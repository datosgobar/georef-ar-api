import download

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_params import DEFAULT_SETTINGS
from elasticsearch_mappings import MAP_STATE, MAP_STATE_GEOM
from elasticsearch_mappings import MAP_DEPT, MAP_DEPT_GEOM
from elasticsearch_mappings import MAP_MUNI, MAP_MUNI_GEOM
from elasticsearch_mappings import MAP_SETTLEMENT, MAP_SETTLEMENT_GEOM
from elasticsearch_mappings import MAP_STREET
import psycopg2

from flask import Flask
import argparse
import os
import urllib.parse
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger.addHandler(handler)

# Versión de archivos del ETL compatibles con ésta versión de API.
# Modificar su valor cuando se haya actualizdo el código para tomar
# nuevas versiones de los archivos.
FILE_VERSION = '1.0.0'

SEPARATOR_WIDTH = 60
ACTIONS = ['index', 'index_stats', 'run_sql']


def print_log_separator(l, message):
    l.info("=" * SEPARATOR_WIDTH)
    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + message.center(SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")
    l.info("=" * SEPARATOR_WIDTH)


class GeorefIndex:
    def __init__(self, alias, filepath, backup_filepath, mapping,
                 excludes=None, docs_key='entidades'):
        self.alias = alias
        self.docs_key = docs_key
        self.filepath = filepath
        self.backup_filepath = backup_filepath
        self.mapping = mapping
        self.excludes = excludes or []

    def fetch_data(self, filepath, files_cache):
        if filepath in files_cache:
            logger.info('Utilizando versión cacheada de:')
            logger.info(' + {}'.format(filepath))
            logger.info('')
            return files_cache[filepath]

        if urllib.parse.urlparse(filepath).scheme in ['http', 'https']:
            logger.info('Descargando archivo:')
            logger.info(' + {}'.format(filepath))
            logger.info('')

            try:
                content = download.download(filepath)
                data = json.loads(content.decode())
            except Exception:
                logger.warning('No se pudo descargar el archivo.')
                logger.warning('')
                return None
        else:
            logger.info('Accediendo al archivo:')
            logger.info(' + {}'.format(filepath))
            logger.info('')

            try:
                with open(filepath) as f:
                    data = json.load(f)
            except Exception:
                logger.warning('No se pudo acceder al archivo JSON.')
                logger.warning('')
                return None

        files_cache[filepath] = data
        return data

    def create_or_reindex(self, es, files_cache, forced=False):
        print_log_separator(logger,
                            'Creando/reindexando {}'.format(self.alias))
        logger.info('')

        data = self.fetch_data(self.filepath, files_cache)
        ok = self.create_or_reindex_with_data(es, data,
                                              check_timestamp=not forced)

        if forced and not ok:
            logger.warning('No se pudo indexar utilizando fuente primaria.')
            logger.warning('Intentando nuevamente con backup...')
            logger.warning('')

            data = self.fetch_data(self.backup_filepath, files_cache)
            ok = self.create_or_reindex_with_data(es, data,
                                                  check_timestamp=False)

            if not ok:
                # TODO: Agregar manejo de errores adicional
                logger.fatal('No se pudo indexar utilizando backups.')
                logger.fatal('')

        if ok:
            self.write_backup(data, files_cache)

    def create_or_reindex_with_data(self, es, data, check_timestamp=True):
        if not data:
            logger.warning('No existen datos a indexar.')
            return False

        timestamp = data['timestamp']
        version = data['version']
        docs = data[self.docs_key]

        logger.info('Versión de API:   {}'.format(FILE_VERSION))
        logger.info('Versión de Datos: {}'.format(version))
        logger.info('')

        if version.split('.')[0] != FILE_VERSION.split('.')[0]:
            logger.warning('Salteando creación de nuevo índice:')
            logger.warning('Versiones de datos no compatibles.')
            logger.info('')
            return False

        new_index = '{}-{}-{}'.format(self.alias,
                                      uuid.uuid4().hex[:8], timestamp)
        old_index = self.get_old_index(es)

        if check_timestamp:
            if not self.check_index_newer(new_index, old_index):
                logger.warning(
                    'Salteando creación de índice {}'.format(new_index))
                logger.warning(
                    (' + El índice {} ya existente es idéntico o más' +
                     ' reciente').format(old_index))
                logger.info('')
                return False
        else:
            logger.info('Omitiendo chequeo de timestamp.')
            logger.info('')

        self.create_index(es, new_index)
        self.insert_documents(es, new_index, docs)

        self.update_aliases(es, new_index, old_index)
        if old_index:
            self.delete_index(es, old_index)

        return True

    def write_backup(self, data, files_cache):
        if self.backup_filepath in files_cache:
            logger.info(
                'Omitiendo creación de backup (ya fue creado anteriormente).')
            logger.info('')
            return

        logger.info('Creando archivo de backup...')
        with open(self.backup_filepath, 'w') as f:
            json.dump(data, f)
        logger.info('Archivo creado.')
        logger.info('')

        files_cache[self.backup_filepath] = data

    def create_index(self, es, index):
        logger.info('Creando nuevo índice: {}...'.format(index))
        logger.info('')
        es.indices.create(index=index, body={
            'settings': DEFAULT_SETTINGS,
            'mappings': self.mapping
        })

    def insert_documents(self, es, index, docs):
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

                logger.warning(
                    'Error al procesar el documento ID {}:'.format(identifier))
                logger.warning(json.dumps(error, indent=4, ensure_ascii=False))
                logger.warning('')

        logger.info('Resumen:')
        logger.info(' + Documentos procesados: {}'.format(len(docs)))
        logger.info(' + Documentos creados: {}'.format(creations))
        logger.info(' + Errores: {}'.format(errors))
        logger.info('')

    def delete_index(self, es, old_index):
        logger.info('Eliminando índice anterior ({})...'.format(old_index))
        es.indices.delete(old_index)
        logger.info('Índice eliminado.')
        logger.info('')

    def update_aliases(self, es, index, old_index):
        logger.info('Actualizando aliases...')

        alias_ops = []
        if old_index:
            alias_ops.append({
                'remove': {
                    'index': old_index,
                    'alias': self.alias
                }
            })

        alias_ops.append({
            'add': {
                'index': index,
                'alias': self.alias
            }
        })

        logger.info('Existen {} operaciones de alias.'.format(len(alias_ops)))

        for op in alias_ops:
            if 'add' in op:
                logger.info(' + Agregar {} como alias de {}'.format(
                    op['add']['alias'], op['add']['index']))
            else:
                logger.info(' + Remover {} como alias de {}'.format(
                    op['remove']['alias'], op['remove']['index']))

        es.indices.update_aliases({'actions': alias_ops})

        logger.info('')
        logger.info('Aliases actualizados.')
        logger.info('')

    def check_index_newer(self, new_index, old_index):
        if not old_index:
            return True

        new_date = datetime.fromtimestamp(int(new_index.split('-')[-1]))
        old_date = datetime.fromtimestamp(int(old_index.split('-')[-1]))

        return new_date > old_date

    def get_old_index(self, es):
        if not es.indices.exists_alias(name=self.alias):
            return None
        return list(es.indices.get_alias(name=self.alias).keys())[0]

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


def run_index(app, es, forced):
    backups_dir = app.config['BACKUPS_DIR']
    os.makedirs(backups_dir, exist_ok=True)

    indices = [
        GeorefIndex('provincias',
                    app.config['STATES_FILE'],
                    os.path.join(backups_dir, 'provincias.json'),
                    MAP_STATE,
                    ['geometria']),
        GeorefIndex('provincias-geometria',
                    app.config['STATES_FILE'],
                    os.path.join(backups_dir, 'provincias.json'),
                    MAP_STATE_GEOM),
        GeorefIndex('departamentos',
                    app.config['DEPARTMENTS_FILE'],
                    os.path.join(backups_dir, 'departamentos.json'),
                    MAP_DEPT,
                    ['geometria']),
        GeorefIndex('departamentos-geometria',
                    app.config['DEPARTMENTS_FILE'],
                    os.path.join(backups_dir, 'departamentos.json'),
                    MAP_DEPT_GEOM),
        GeorefIndex('municipios',
                    app.config['MUNICIPALITIES_FILE'],
                    os.path.join(backups_dir, 'municipios.json'),
                    MAP_MUNI,
                    ['geometria']),
        GeorefIndex('municipios-geometria',
                    app.config['MUNICIPALITIES_FILE'],
                    os.path.join(backups_dir, 'municipios.json'),
                    MAP_MUNI_GEOM),
        GeorefIndex('bahra',
                    app.config['LOCALITIES_FILE'],
                    os.path.join(backups_dir, 'bahra.json'),
                    MAP_SETTLEMENT,
                    ['geometria']),
        GeorefIndex('bahra-geometria',
                    app.config['LOCALITIES_FILE'],
                    os.path.join(backups_dir, 'bahra.json'),
                    MAP_SETTLEMENT_GEOM),
        GeorefIndex('calles',
                    app.config['STREETS_FILE'],
                    os.path.join(backups_dir, 'calles.json'),
                    MAP_STREET,
                    ['codigo_postal'],
                    docs_key='vias')
    ]

    files_cache = {}

    for index in indices:
        try:
            index.create_or_reindex(es, files_cache, forced)
        except Exception as e:
            logger.error('Ocurrió un error al indexar:')
            logger.error('')
            logger.error(e)
            logger.error('')

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
    parser.add_argument('-f', '--forced', action='store_true')
    parser.add_argument('-i', '--info', action='store_true',
                        help='Mostrar información de índices y salir.')
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
            run_index(app, es, args.forced)
        else:
            run_info(es)

    elif args.mode == 'run_sql':
        run_sql(app, args.script)


if __name__ == '__main__':
    main()
