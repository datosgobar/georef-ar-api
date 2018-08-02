from elasticsearch import Elasticsearch
from elasticsearch import helpers, ElasticsearchException
from elasticsearch_params import DEFAULT_SETTINGS
from elasticsearch_mappings import MAP_STATE, MAP_STATE_GEOM
from elasticsearch_mappings import MAP_DEPT, MAP_DEPT_GEOM
from elasticsearch_mappings import MAP_MUNI, MAP_MUNI_GEOM
from elasticsearch_mappings import MAP_SETTLEMENT, MAP_SETTLEMENT_GEOM
from elasticsearch_mappings import MAP_STREET
import psycopg2

from flask import Flask
import argparse
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger.addHandler(handler)

SEPARATOR_WIDTH = 60
ACTIONS = ['index', 'index_stats', 'run_sql']


def print_log_separator(l, message):
    l.info("=" * SEPARATOR_WIDTH)
    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + message.center(SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")
    l.info("=" * SEPARATOR_WIDTH)


class GeorefIndex:
    def __init__(self, alias, filepath, mapping, excludes=None,
                 docs_key='entidades'):
        self.alias = alias
        self.docs_key = docs_key
        self.filepath = filepath
        self.mapping = mapping
        self.excludes = excludes or []

    def create_or_reindex(self, es):
        print_log_separator(logger,
                            'Creando/reindexando {}'.format(self.alias))
        logger.info('')
        logger.info('Leyendo archivo JSON...')
        logger.info(' - Path: {}'.format(self.filepath))
        logger.info('')

        with open(self.filepath) as f:
            data = json.load(f)

        timestamp = data['timestamp']
        docs = data[self.docs_key]

        index = '{}-{}'.format(self.alias, timestamp)
        old_index = self.get_old_index(es)

        if not self.check_index_newer(index, old_index):
            logger.warning('Salteando creación de índice {}'.format(index))
            logger.warning(
                (' - El índice {} ya existente es idéntico o más' +
                 ' reciente').format(old_index))
            logger.info('')

            return [], []

        logger.info('Creando nuevo índice: {}...'.format(index))
        logger.info('')
        es.indices.create(index=index, body={
            'settings': DEFAULT_SETTINGS,
            'mappings': self.mapping
        })

        operations = self.bulk_update_generator(docs, index)
        creations, errors = 0, 0

        logger.info('Insertando documentos...')

        for ok, response in helpers.streaming_bulk(es, operations,
                                                   raise_on_error=False):
            if ok and response['create']['result'] == 'created':
                creations += 1
            else:
                errors += 1
                identifier = response['create']['_id']
                error = response['create']['error']

                logger.error(
                    'Error al procesar el documento ID {}:'.format(identifier))
                logger.error(json.dumps(error, indent=4, ensure_ascii=False))
                logger.error('')

        logger.info('Resumen:')
        logger.info(' - Documentos procesados: {}'.format(len(docs)))
        logger.info(' - Documentos creados: {}'.format(creations))
        logger.info(' - Errores: {}'.format(errors))
        logger.info('')

        return self.gen_swap_alias_operation(es, index, old_index)

    def check_index_newer(self, index, old_index):
        if not old_index:
            return True

        new_date = datetime.fromtimestamp(int(index.split('-')[-1]))
        old_date = datetime.fromtimestamp(int(old_index.split('-')[-1]))

        return new_date > old_date

    def get_old_index(self, es):
        if not es.indices.exists_alias(name=self.alias):
            return None
        return list(es.indices.get_alias(name=self.alias).keys())[0]

    def gen_swap_alias_operation(self, es, index, old_index):
        if not old_index:
            return [
                {
                    'add': {
                        'index': index,
                        'alias': self.alias
                    }
                }
            ], []

        return [
            {
                'remove': {
                    'index': old_index,
                    'alias': self.alias
                }
            },
            {
                'add': {
                    'index': index,
                    'alias': self.alias
                }
            }
        ], [old_index]

    def bulk_update_generator(self, docs, index):
        """Crea un generador de operaciones 'create' para Elasticsearch a
        partir de una lista de documentos a indexar.

        Args:
            docs (list): Documentos a indexar.
            index (str): Nombre del índice.

        """
        for original_doc in docs:
            doc = {
                key: original_doc[key]
                for key in original_doc
                if key not in self.excludes
            }

            action = {
                '_op_type': 'create',
                '_type': '_doc',
                '_id': doc['id'],
                '_index': index,
                '_source': doc
            }

            yield action


def update_aliases(es, alias_ops):
    print_log_separator(logger, 'Cambio de alias')
    logger.info('')

    if not alias_ops:
        logger.info('No hay operaciones de alias a realizar.')
        logger.info('')
        return

    logger.info('Existen {} operaciones de alias'.format(len(alias_ops)))

    for op in alias_ops:
        if 'add' in op:
            logger.info(' - Agregar {} como alias de {}'.format(
                op['add']['alias'], op['add']['index']))
        else:
            logger.info(' - Remover {} como alias de {}'.format(
                op['remove']['alias'], op['remove']['index']))

    es.indices.update_aliases({'actions': alias_ops})

    logger.info('')
    logger.info('Aliases actualizados.')
    logger.info('')


def delete_indices(es, indices):
    print_log_separator(logger, 'Borrado de índices antiguos')
    logger.info('')

    if not indices:
        logger.info('No hay índices a eliminar.')
        return

    logger.info('Índices a eliminar:')
    for index in indices:
        logger.info(' - {}'.format(index))

    es.indices.delete(','.join(indices))

    logger.info('')
    logger.info('Los índices fueron eliminados exitosamente.')


def run_index(app, es):
    indices = [
        GeorefIndex('provincias', app.config['STATES_FILE'], MAP_STATE,
                    ['geometria']),
        GeorefIndex('provincias-geometria', app.config['STATES_FILE'],
                    MAP_STATE_GEOM),
        GeorefIndex('departamentos', app.config['DEPARTMENTS_FILE'], MAP_DEPT,
                    ['geometria']),
        GeorefIndex('departamentos-geometria', app.config['DEPARTMENTS_FILE'],
                    MAP_DEPT_GEOM),
        GeorefIndex('municipios', app.config['MUNICIPALITIES_FILE'], MAP_MUNI,
                    ['geometria']),
        GeorefIndex('municipios-geometria', app.config['MUNICIPALITIES_FILE'],
                    MAP_MUNI_GEOM),
        GeorefIndex('bahra', app.config['LOCALITIES_FILE'], MAP_SETTLEMENT,
                    ['geometria']),
        GeorefIndex('bahra-geometria', app.config['LOCALITIES_FILE'],
                    MAP_SETTLEMENT_GEOM),
        GeorefIndex('calles', app.config['STREETS_FILE'], MAP_STREET,
                    ['codigo_postal'], docs_key='vias')
    ]

    alias_ops = []
    old_indices = []

    for index in indices:
        try:
            ops, old = index.create_or_reindex(es)
            alias_ops.extend(ops)
            old_indices.extend(old)
        except (ElasticsearchException,
                FileNotFoundError,
                json.decoder.JSONDecodeError) as e:
            logger.error('Ocurrió un error al indexar:')
            logger.error('')
            logger.error(e)
            logger.error('')

    update_aliases(es, alias_ops)
    delete_indices(es, old_indices)
    logger.info('')


def run_info(es):
    logger.info('INDICES:')
    for line in es.cat.indices(v=True).splitlines():
        logger.info(line)
    logger.info('')

    logger.info('ALIASES:')
    for line in es.cat.aliases(v=True).splitlines():
        logger.info(line)
    logger.info('')

    logger.info('NODES:')
    for line in es.cat.nodes(v=True).splitlines():
        logger.info(line)


def run_sql(app, script):
    try:
        conn = psycopg2.connect(host=app.config['SQL_DB_HOST'],
                                dbname=app.config['SQL_DB_NAME'],
                                user=app.config['SQL_DB_USER'],
                                password=app.config['SQL_DB_PASS'])

        sql = script.read()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)

        conn.close()
        logger.info('El script SQL fue ejecutado correctamente.')
    except psycopg2.Error as e:
        logger.error('Ocurrió un error al ejecutar el script SQL:')
        logger.error(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', metavar='<action>', required=True,
                        choices=ACTIONS)
    parser.add_argument('-t', '--timeout', metavar='<seconds>', default=300,
                        type=int,
                        help='Tiempo de espera para transfer. Elasticsearch.')
    parser.add_argument('-c', '--config', metavar='<path>', required=True)
    parser.add_argument('-s', '--script', metavar='<path>',
                        type=argparse.FileType())
    parser.add_argument('-i', '--info', action='store_true')
    args = parser.parse_args()

    app = Flask(__name__)
    app.config.from_pyfile(args.config, silent=False)

    if args.mode in ['index', 'index_stats']:
        options = {
            'hosts': app.config['ES_HOSTS'],
            'timeout': args.timeout
        }

        if app.config['ES_SNIFF']:
            options['sniff_on_start'] = True
            options['sniff_on_connection_fail'] = True
            options['sniffer_timeout'] = app.config['ES_SNIFFER_TIMEOUT']

        es = Elasticsearch(**options)

        if args.mode == 'index':
            run_index(app, es)
        else:
            run_info(es)

    elif args.mode == 'run_sql':
        run_sql(app, args.script)


if __name__ == '__main__':
    main()
