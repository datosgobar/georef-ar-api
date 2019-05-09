"""Script 'indexer' de georef-ar-api

Contiene funciones de utilidad para descargar e indexar datos.
"""

import argparse
import os
import shutil
import sys
import urllib.parse
import json
import smtplib
import logging
import uuid
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from io import StringIO

from elasticsearch import helpers
import requests
import tqdm

from .. import app
from .. import normalizer
from .. import names as N
from . import es_config


logger_stream = StringIO()
"""StringIO: Buffer donde se almacenan los logs generados como strings.
"""

logger = logging.getLogger(__name__)
"""Logger: logger global para almacenar información sobre acciones ejecutadas.
"""

# Versión de archivos del ETL compatibles con ésta versión de API.
# Modificar su valor cuando se haya actualizado el código para tomar
# nuevas versiones de los archivos.
ETL_FILE_VERSION = '12.0.0'

LOGS_DIR = 'logs'
CACHE_DIR = 'cache'

SEPARATOR_WIDTH = 60
SMTP_TIMEOUT = 30
CHUNK_SIZE = 8192
ACTIONS = ['index', 'index_stats']
INDEX_NAMES = [
    N.STATES,
    es_config.geom_index_for(N.STATES),
    N.DEPARTMENTS,
    es_config.geom_index_for(N.DEPARTMENTS),
    N.MUNICIPALITIES,
    es_config.geom_index_for(N.MUNICIPALITIES),
    N.CENSUS_LOCALITIES,
    N.SETTLEMENTS,
    N.LOCALITIES,
    N.STREETS,
    N.INTERSECTIONS,
    N.STREET_BLOCKS,
    'all'
]
ES_TIMEOUT = 720
DEFAULT_SHARDS = 1
DEFAULT_REPLICAS = 2


def setup_logger(l, stream):
    """Configura un objeto Logger para imprimir eventos de nivel INFO o
    superiores. Los eventos se envían a sys.stdout, a un archivo en el
    directorio de logs, y a un buffer de tipo 'StringIO'.

    Args:
        l (Logger): Objeto logger a configurar.
        stream (StringIO): Buffer donde almacenar adicionalmente los eventos
            enviados a 'l'.

    """
    l.setLevel(logging.INFO)

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)

    str_handler = logging.StreamHandler(stream)
    str_handler.setLevel(logging.INFO)

    os.makedirs(LOGS_DIR, exist_ok=True)
    filename = time.strftime('georef-index-%Y.%m.%d-%H.%M.%S.log')
    file_handler = logging.FileHandler(os.path.join(LOGS_DIR, filename))
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    stdout_handler.setFormatter(formatter)
    str_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    l.addHandler(stdout_handler)
    l.addHandler(str_handler)
    l.addHandler(file_handler)


def send_email(host, user, password, subject, message, recipients,
               attachments=None, ssl=True, port=0, timeout=SMTP_TIMEOUT):
    """Envía un mail a un listado de destinatarios.

    Args:
        host (str): Hostname de servidor SMTP.
        user (str): Usuario del servidor SMTP.
        password (str): Contraseña para el usuario.
        subject (str): Asunto a utilizar en el mail enviado.
        message (str): Contenido del mail a enviar.
        recipients (list): Lista de destinatarios.
        attachments (dict): Diccionario de contenidos <str, str> a adjuntar en
            el mail. Las claves representan los nombres de los contenidos y los
            valores representan los contenidos en sí.
        ssl (bool): Verdadero si la conexión inicial debería utilizar SSL/TLS.
        port (int): Puerto a utilizar (0 para utilizar el default).
        timeout (int): Tiempo máximo a esperar en segundos para establecer la
            conexión al servidor SMTP.

    """
    client_class = smtplib.SMTP_SSL if ssl else smtplib.SMTP
    with client_class(host, timeout=timeout, port=port) as smtp:
        if not ssl:
            smtp.starttls()
            smtp.ehlo()

        smtp.login(user, password)

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg["From"] = user
        msg["To"] = ",".join(recipients)
        msg.attach(MIMEText(message))

        for name, contents in (attachments or {}).items():
            attachment = MIMEText(contents)
            attachment['Content-Disposition'] = \
                'attachment; filename="{}"'.format(name)
            msg.attach(attachment)

        smtp.send_message(msg)


def read_text_file(filepath):
    """Retorna los contenidos de un archivo de texto.

    Args:
        filepath (str): Ruta local al archivo.

    Returns:
        str: Contenidos del archivo.

    """
    with open(filepath) as f:
        return f.read()


def read_ndjson_file(filepath):
    """Retorna los contenidos de un archivo NDJSON (http://ndjson.org/) en
    forma de un iterador de objetos.

    Args:
        filepath (str): Ruta local al archivo.

    Yields:
        dict: Objeto JSON en cada línea del archivo.

    """
    with open(filepath) as f:
        for line in f:
            yield json.loads(line)


def download(url, filepath, timeout=30):
    """
    Descarga un archivo a través del protocolo HTTP.

    Args:
        url (str): URL (schema HTTP) del archivo a descargar.
        filepath (str): Ruta del archivo a donde almacenar los datos.
        timeout (int): Timeout a utilizar en segundos.

    Raises:
        requests.exceptions.RequestException, requests.exceptions.HTTPError: en
            caso de ocurrir un error durante la descarga.

    """
    with requests.get(url, stream=True, timeout=timeout) as req:
        req.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in req.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)


def print_log_separator(l, message):
    """Imprime un separador de logs con forma de rectángulo con texto.

    Args:
        l (Logger): Objeto Logger sobre el cual imprimir el separador.
        message (str): Mensaje a utilizar como separador.

    """
    l.info("=" * SEPARATOR_WIDTH)
    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + message.center(SEPARATOR_WIDTH - 2) + "|")

    l.info("|" + " " * (SEPARATOR_WIDTH - 2) + "|")
    l.info("=" * SEPARATOR_WIDTH)


class GeorefIndex:
    """La clase GeorefIndex representa un índice Elasticsearch a ser utilizado
    por la API. Actualmente se utilizan los siguientes índices:

    - provincias
    - provincias-geometria
    - departamentos
    - departamentos-geometria
    - municipios
    - municipios-geometria
    - localidades
    - calles
    - intersecciones

    La clase GeorefIndex existe para simplificar la creación y actualización de
    los datos de los índices. La clase también permite crear respaldos
    (backups) de los datos siendo utilizados.

    El flujo de creación de los índices es el siguiente:

        1) Creación inicial del índice y su alias
        2) Se crea un respaldo de los datos utilizados

    El flujo de actualización del los índices es el siguiente:

        1) Se crea un nuevo índice con los datos actualizados
        2) Se modifica el alias para que referencie a la nueva versión
        3) Se elimina el índice antiguo
        4) Se crea un respaldo de los datos utilizados

    Attributes:
        _alias (str): Alias a utilizar para el índice (por ejemplo, 'calles').
        _doc_class (type): Tipo del documento Elasticsearch, debe heredar de
            elasticsearch_dsl.Document.
        _filepath (str): Path o URL de archivo de datos a utilizar como datos.
        _synonyms_filepath (str): Path o URL de archivo de sinónimos.
        _excluding_terms_filepath (str): Path o URL de archivo de términos
            excluyentes.
        _backup_filepath (str): Path donde colocar un respaldo de los últimos
            datos indexados.
        _includes  (list): Lista de atributos a incluir cuando se leen los
            documentos del archivo de datos. Si no se especifica, se incluyen
            todos los campos.

    """

    def __init__(self, alias, doc_class, filepath, synonyms_filepath=None,
                 excluding_terms_filepath=None, backup_filepath=None,
                 includes=None):
        """Inicializa un nuevo objeto de tipo GeorefIndex.

        Args:
            alias (str): Ver el atributo '_alias'.
            doc_class (str): Ver el atributo '_doc_class'.
            filepath (str): Ver el atributo '_filepath'.
            synonyms_filepath (str): Ver el atributo '_synonyms_filepath'.
            excluding_terms_filepath (str): Ver el atributo
                '_excluding_terms_filepath'.
            backup_filepath (str): Ver el atributo '_backup_filepath'.
            includes (list): Ver el atributo '_includes'.

        """
        self._alias = alias
        self._doc_class = doc_class
        self._filepath = filepath
        self._synonyms_filepath = synonyms_filepath
        self._excluding_terms_filepath = excluding_terms_filepath
        self._backup_filepath = backup_filepath
        self._includes = includes

    @property
    def alias(self):
        return self._alias

    def _fetch_data(self, filepath, files_cache, fmt='ndjson'):
        """Retorna los contenidos de un archivo.

        Args:
            filepath (str): Path o URL HTTP/HTTPS donde leer el archivo.
            files_cache (dict): Cache de archivos descargados/leídos
                anteriormente durante el proceso de indexación actual.
            fmt (str): Formato de los contenidos del archivo.

        Returns:
            Iterator[dict], str: Contenido del archivo.

        """
        data = None
        if fmt == 'ndjson':
            loadfn = read_ndjson_file
        elif fmt == 'txt':
            loadfn = read_text_file
        else:
            raise ValueError('Invalid format: {}'.format(fmt))

        if filepath in files_cache:
            logger.info('Utilizando archivo cacheado para:')
            logger.info(' + {}'.format(filepath))
            logger.info('')
            return loadfn(files_cache[filepath])

        if urllib.parse.urlparse(filepath).scheme in ['http', 'https']:
            logger.info('Descargando archivo remoto:')
            logger.info(' + {}'.format(filepath))

            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                url_path = urllib.parse.urlparse(filepath).path
                filename = url_path.rsplit('/', 1)[-1]
                download_path = os.path.join(CACHE_DIR, filename)

                logger.info(' + Destino: {}'.format(download_path))
                logger.info('')

                download(filepath, download_path)

                data = loadfn(download_path)
                files_cache[filepath] = download_path
            except requests.exceptions.RequestException as e:
                logger.warning('No se pudo descargar el archivo:')
                logger.warning(e)
                logger.warning('')
            except ValueError as e:
                logger.warning('No se pudo leer los contenidos del archivo:')
                logger.warning(e)
                logger.warning('')
        else:
            logger.info('Accediendo al archivo local:')
            logger.info(' + {}'.format(filepath))
            logger.info('')

            try:
                data = loadfn(filepath)
            except OSError as e:
                logger.warning('No se pudo acceder al archivo local:')
                logger.warning(e)
                logger.warning('')
            except ValueError as e:
                logger.warning('No se pudo leer los contenidos del archivo:')
                logger.warning(e)
                logger.warning('')

        return data

    def _parse_elasticsearch_synonyms(self, contents):
        """Interpreta los contenidos de un archivo de sinónimos utilizado por
        Elasticsearch (formato Solr).

        Args:
            contents (str): Contenido de un archivo de sinónimos.

        Returns:
            list: Lista de sinónimos apta para ser utilizada para construir
                filtros de tokens.

        """
        if not contents:
            return []

        lines = [line.strip() for line in contents.splitlines()]
        return [
            line for line in lines
            if line and not line.startswith('#')
        ]

    def create_or_reindex(self, es, files_cache, forced=False, verbose=False):
        """Punto de entrada de la clase GeorefIndex. Permite crear o actualizar
        el índice.

        El índice se crea/actualiza siguiendo el flujo de pasos mencionados en
        la documentación principal de la clase GeorefIndex.

        Al momento de actualizar, se comprueba que los datos nuevos a utilizar
        sean más recientes (en fecha de creación) que los datos ya existentes
        e indexados. En caso de no serlos, se saltea la actualización. Este
        comportamiento se puede desactivar utilizando el parámetro 'forced' con
        valor True. Si el índice se está creando por primera vez, el valor del
        parámetro 'forced' no tiene relevancia.

        Si se está actualizando, y el valor de 'forced' es True, y por alguna
        razón no es posible acceder al archivo de datos a utilizar, se intenta
        utilizar un archivo de respaldo creado anteriormente. Si no se puede
        utilizar el archivo de respaldo, se cancela la actualización.

        La versión de los datos a utilizar para indexar debe ser idéntica a la
        versión utilizada por la API, especificada en la variable
        'FILE_VERSION'. En caso de no serlo, la indexación falla, sin importar
        el valor de 'forced'.

        Luego de una actualización/creación exitosa, se crea un respaldo de los
        datos utilizado.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            files_cache (dict): Cache de archivos descargados/leídos
                anteriormente durante el proceso de indexación actual.
            forced (bool): Activa modo de actualización forzada (se ignoran los
                timestamps).
            verbose (bool): Mostrar más información en pantalla.

        """
        print_log_separator(logger,
                            'Creando/reindexando {}'.format(self._alias))
        logger.info('')

        data = self._fetch_data(self._filepath, files_cache)

        synonyms = None
        if self._synonyms_filepath:
            synonyms_str = self._fetch_data(self._synonyms_filepath,
                                            files_cache, fmt='txt')
            synonyms = self._parse_elasticsearch_synonyms(synonyms_str)

            if not synonyms:
                logger.warning('Lista de sinónimos vacía.')
                logger.warning('')

        excluding_terms = None
        if self._excluding_terms_filepath:
            ex_terms_str = self._fetch_data(self._excluding_terms_filepath,
                                            files_cache, fmt='txt')
            excluding_terms = self._parse_elasticsearch_synonyms(ex_terms_str)

            if not excluding_terms:
                logger.warning('Lista de términos excluyentes vacía.')
                logger.warning('')

        ok = self._create_or_reindex_with_data(es, data, synonyms,
                                               excluding_terms,
                                               check_timestamp=not forced,
                                               verbose=verbose)

        if not self._backup_filepath:
            if not ok:
                log_fn = logger.error if forced else logger.warning
                log_fn('No se pudo indexar utilizando fuente primaria.')
                log_fn('')

            return

        if ok:
            self._write_backup(files_cache)
        elif forced:
            logger.warning('No se pudo indexar utilizando fuente primaria.')
            logger.warning('Intentando nuevamente con backup...')
            logger.warning('')

            data = self._fetch_data(self._backup_filepath, files_cache)
            ok = self._create_or_reindex_with_data(es, data, synonyms,
                                                   excluding_terms,
                                                   check_timestamp=False,
                                                   verbose=verbose)

            if not ok:
                logger.error('No se pudo indexar utilizando backups.')
                logger.error('')

    def _create_or_reindex_with_data(self, es, data, synonyms, excluding_terms,
                                     check_timestamp, verbose=False):
        """Crea o actualiza el índice. Ver la documentación de
        'create_or_reindex' para más detalles del flujo de creación y
        actualización de índices.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            data (Iterator[dict]): Iterador de datos a indexar (diccionarios).
            synonyms (list): Lista de sinónimos a utilizar en la configuración
                de Elasticsearch.
            excluding_terms (list): Lista de términos excluyentes a utilizar en
                la configuración de Elasticsearch.
            check_timestamp (bool): Cuando es falso, permite indexar datos con
                timestamp anterior a los que ya están almacenados.
            verbose (bool): Mostrar más información en pantalla.

        Returns:
            bool: Verdadero si la creación/actualización se ejecutó
                correctamente.

        """
        if not data:
            logger.warning('No existen datos a indexar.')
            logger.warning('')
            return False

        # El primer objeto del NDJSON son los metadatos
        metadata = next(data)
        timestamp = metadata['timestamp']
        date = metadata['fecha_creacion']
        version = metadata['version']
        count = metadata['cantidad']

        # El resto de los objetos son entidades a indexar
        docs = data

        logger.info('Fecha de creación de datos: {}'.format(date))
        logger.info('Versión de datos API: {}'.format(ETL_FILE_VERSION))
        logger.info('Versión de datos ETL: {}'.format(version))
        logger.info('')

        if version.split('.')[0] != ETL_FILE_VERSION.split('.')[0]:
            logger.warning('Salteando creación de nuevo índice:')
            logger.warning('Versiones de datos no compatibles.')
            logger.info('')
            return False

        # El nombre real del índice (no su alias) está compuesto de tres
        # componentes: el alias, un número al azar, y el timestamp de los
        # datos que contiene. Por ejemplo: provincias-965d5f6b-1538377538.
        #
        # La primera parte identifica el propósito del índice, la tercera
        # describe la fecha de creación de los datos que contiene, y la segunda
        # se utiliza para distinguir entre índices de una misma entidad que
        # contienen los mismos datos (este caso se puede dar en casos de
        # utilizar forced=True).

        new_index = '{}-{}-{}'.format(self._alias,
                                      uuid.uuid4().hex[:8], timestamp)
        old_index = self._get_old_index(es)

        if check_timestamp:
            if not self._check_index_newer(new_index, old_index):
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

        self._create_index(es, new_index, synonyms, excluding_terms)
        self._insert_documents(es, new_index, docs, count, verbose)

        self._update_aliases(es, new_index, old_index)
        if old_index:
            self._delete_index(es, old_index)

        logger.info('Indexado completo.')
        logger.info('')
        return True

    def _write_backup(self, files_cache):
        """Crea un archivo de respaldo situado en el path
        'self._backup_filepath' a partir de 'self._filepath'.

        Args:
            files_cache (dict): Cache de archivos descargados/leídos
                anteriormente durante el proceso de indexación actual.

        """
        logger.info('Creando archivo de backup...')
        if urllib.parse.urlparse(self._filepath).scheme in ['http', 'https']:
            # self._filepath es una URL, utilizar el archivo ya descargado en
            # el cache.
            source = files_cache[self._filepath]
        else:
            # self._filepath es un archivo local, tomar su ruta
            source = self._filepath

        shutil.copy(source, self._backup_filepath)

        logger.info('Archivo creado.')
        logger.info('')

    def _create_index(self, es, index, synonyms, excluding_terms):
        """Crea un índice Elasticsearch con settings default y
        mapeos establecidos por 'self._doc_class'.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            index (str): Nombre del índice a crear. Notar que el nombre no es
                igual al alias del índice.
            synonyms (list): Lista de sinónimos a utilizar en la configuración
                de Elasticsearch.
            excluding_terms (list): Lista de términos excluyentes a utilizar en
                la configuración de Elasticsearch.

        """
        logger.info('Creando nuevo índice: {}...'.format(index))
        logger.info('')

        es_config.create_index(es, index, self._doc_class, DEFAULT_SHARDS,
                               DEFAULT_REPLICAS, synonyms, excluding_terms)

    def _insert_documents(self, es, index, docs, count, verbose=False):
        """Inserta documentos dentro de un índice.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            index (str): Nombre de índice.
            docs (Iterator[dict]): Iterator de documentos a insertar.
            count (int): Cantidad de documentos a insertar.
            verbose (bool): Mostrar más información en pantalla.

        """
        operations = self._bulk_update_generator(docs, index)
        creations, errors = 0, 0

        logger.info('Insertando documentos...')

        iterator = helpers.streaming_bulk(es, operations, raise_on_error=False,
                                          request_timeout=ES_TIMEOUT)

        if verbose:
            iterator = tqdm.tqdm(iterator, total=count, file=sys.stderr)

        for ok, response in iterator:
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
        logger.info(' + Documentos procesados: {}'.format(count))
        logger.info(' + Documentos creados: {}'.format(creations))
        logger.info(' + Errores: {}'.format(errors))
        logger.info('')

    def _delete_index(self, es, old_index):
        """Borra un índice.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            old_index (str): Nombre de índice.

        """
        logger.info('Eliminando índice anterior ({})...'.format(old_index))
        es.indices.delete(old_index)
        logger.info('Índice eliminado.')
        logger.info('')

    def _update_aliases(self, es, index, old_index):
        """Transfiere el alias 'self._alias' de un índice a otro.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.
            index (str): Nombre de índice al que self._alias debe referenciar.
            old_index (list): Nombre de índice al que self._alias referencia
                actualmente.

        """
        logger.info('Actualizando aliases...')

        alias_ops = []
        if old_index:
            alias_ops.append({
                'remove': {
                    'index': old_index,
                    'alias': self._alias
                }
            })

        alias_ops.append({
            'add': {
                'index': index,
                'alias': self._alias
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

    def _check_index_newer(self, new_index, old_index):
        """Comprueba si un índice es mas reciente que otro.

        Args:
            new_index (str): Nombre del nuevo índice.
            old_index (str): Nombre del índice antiguo.

        Returns:
            bool: Verdadero si new_index es más reciente que old_index.

        """
        if not old_index:
            return True

        new_date = datetime.fromtimestamp(int(new_index.split('-')[-1]))
        old_date = datetime.fromtimestamp(int(old_index.split('-')[-1]))

        return new_date > old_date

    def _get_old_index(self, es):
        """Retorna el índice al que 'self._alias' apunta actualmente.

        Args:
            es (Elasticsearch): Cliente Elasticsearch.

        Returns:
            str: Nombre del índice apuntado por self._alias.

        """
        if not es.indices.exists_alias(name=self._alias):
            return None

        return list(es.indices.get_alias(name=self._alias).keys())[0]

    def _bulk_update_generator(self, docs, index):
        """Crea un generador de operaciones 'create' para Elasticsearch a
        partir de una lista de documentos a indexar.

        Args:
            docs (list): Documentos a indexar.
            index (str): Nombre del índice.

        Yields:
            dict: Acción a ejecutar en un índice Elasticsearch.

        """
        for doc in docs:
            if self._includes:
                doc = {key: doc[key]
                       for key in doc
                       if key in self._includes}

            action = {
                '_op_type': 'create',
                '_id': doc['id'],
                '_index': index,
                '_source': doc
            }

            yield action


def send_index_email(config, forced, env, log):
    """Envía los contenidos de los logs generados por mail, utilizando la
    configuración de Flask para leer los parámetros.

    Args:
        config (flask.Config): Configuración Flask de la API.
        forced (bool): Verdadero si se activó el modo de re-indexación forzada.
        env (str): Ambiente actual (dev/stg/prod).
        log (str): Contenidos de los logs generados.

    """
    lines = log.splitlines()
    warnings = len([line for line in lines if 'WARNING' in line])
    errors = len([line for line in lines if 'ERROR' in line])

    subject = 'Georef API [{}] Index - Errores: {} - Warnings: {}'.format(
        env,
        errors,
        warnings
    )
    msg = 'Indexación de datos para Georef API. Modo forzado: {}'.format(
        forced)

    send_email(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        subject=subject,
        message=msg,
        recipients=config['recipients'],
        attachments={'log.txt': log},
        ssl=config['ssl'],
        port=config['port']
    )


def run_index(es, forced, name='all', verbose=False):
    """Ejecuta la rutina de creación/actualización de los índices utilizados
    por Georef API.

    Args:
        es (Elasticsearch): Cliente Elasticsearch.
        forced (bool): Verdadero si se especificó el modo de re-indexación
            forzada.
        name (str): Nombre del índice a crear/actualizar. Si se utiliza el
            valor 'all', se crean/actualizan todos los índices.
        verbose (bool): Mostrar más información en pantalla.

    """
    backups_dir = app.config['BACKUPS_DIR']
    os.makedirs(backups_dir, exist_ok=True)

    env = app.config['GEOREF_ENV']
    logger.info('Comenzando (re)indexación en Georef API [{}]'.format(env))
    logger.info('')

    logger.info('Índice(s) seleccionado(s): {}'.format(name))
    logger.info('Modo forzado: {}'.format(forced))
    logger.info('')

    indices = [
        GeorefIndex(alias=N.STATES,
                    doc_class=es_config.State,
                    filepath=app.config['STATES_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'provincias.ndjson')),
        GeorefIndex(alias=es_config.geom_index_for(N.STATES),
                    doc_class=es_config.StateGeom,
                    filepath=app.config['STATES_FILE'],
                    includes=[N.ID, N.GEOM]),
        GeorefIndex(alias=N.DEPARTMENTS,
                    doc_class=es_config.Department,
                    filepath=app.config['DEPARTMENTS_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'departamentos.ndjson')),
        GeorefIndex(alias=es_config.geom_index_for(N.DEPARTMENTS),
                    doc_class=es_config.DepartmentGeom,
                    filepath=app.config['DEPARTMENTS_FILE'],
                    includes=[N.ID, N.GEOM]),
        GeorefIndex(alias=N.MUNICIPALITIES,
                    doc_class=es_config.Municipality,
                    filepath=app.config['MUNICIPALITIES_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'municipios.ndjson')),
        GeorefIndex(alias=es_config.geom_index_for(N.MUNICIPALITIES),
                    doc_class=es_config.MunicipalityGeom,
                    filepath=app.config['MUNICIPALITIES_FILE'],
                    includes=[N.ID, N.GEOM]),
        GeorefIndex(alias=N.CENSUS_LOCALITIES,
                    doc_class=es_config.CensusLocality,
                    filepath=app.config['CENSUS_LOCALITIES_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(
                        backups_dir, 'localidades-censales.ndjson')),
        GeorefIndex(alias=N.SETTLEMENTS,
                    doc_class=es_config.Settlement,
                    filepath=app.config['SETTLEMENTS_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'asentamientos.ndjson')),
        GeorefIndex(alias=N.LOCALITIES,
                    doc_class=es_config.Locality,
                    filepath=app.config['LOCALITIES_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'localidades.ndjson')),
        GeorefIndex(alias=N.STREETS,
                    doc_class=es_config.Street,
                    filepath=app.config['STREETS_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'calles.ndjson')),
        GeorefIndex(alias=N.INTERSECTIONS,
                    doc_class=es_config.Intersection,
                    filepath=app.config['INTERSECTIONS_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(
                        backups_dir, 'calles_intersecciones.ndjson')),
        GeorefIndex(alias=N.STREET_BLOCKS,
                    doc_class=es_config.StreetBlock,
                    filepath=app.config['STREET_BLOCKS_FILE'],
                    synonyms_filepath=app.config['SYNONYMS_FILE'],
                    excluding_terms_filepath=app.config[
                        'EXCLUDING_TERMS_FILE'],
                    backup_filepath=os.path.join(backups_dir,
                                                 'cuadras.ndjson'))
    ]

    files_cache = {}

    for index in indices:
        if name in ['all', index.alias]:
            try:
                index.create_or_reindex(es, files_cache, forced, verbose)
            except Exception:  # pylint: disable=broad-except
                logger.error('')
                logger.exception('Ocurrió un error al indexar:')
                logger.error('')

    logger.info('')

    mail_config = app.config.get_namespace('EMAIL_')
    if mail_config['enabled']:
        logger.info('Enviando mail...')

        send_index_email(mail_config, forced, env, logger_stream.getvalue())
        logger.info('Mail enviado.')
        logger.info('')

    logger.info('Script finalizado.')


def run_info(es):
    """Imprime en pantalla información sobre el estado del cluster
    Elasticsearch.

    Args:
        es (Elasticsearch): Cliente Elasticsearch.

    """
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


def main():
    """Punto de entrada para indexer.py

    Utilizar 'python indexer.py -h' para información sobre el uso de éste
    archivo en la línea de comandos. Se recomienda utilizar el Makefile
    incluido en la raíz del proyecto en lugar de ejecutar indexer.py
    directamente.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', metavar='<action>', required=True,
                        choices=ACTIONS, help='Acción a ejecutar.')
    parser.add_argument('-n', '--name', metavar='<index name>',
                        choices=INDEX_NAMES, default='all',
                        help='Nombre del índice (o "all").')
    parser.add_argument('-f', '--forced', action='store_true',
                        help='Omitir chequeo de timestamp.')
    parser.add_argument('-i', '--info', action='store_true',
                        help='Mostrar información de índices y salir.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Imprimir información adicional.')
    args = parser.parse_args()

    setup_logger(logger, logger_stream)

    try:
        with app.app_context():
            es = normalizer.get_elasticsearch()

            if args.mode == 'index':
                run_index(es, args.forced, args.name, args.verbose)
            elif args.mode == 'index_stats':
                run_info(es)
            else:
                raise ValueError('Invalid operation')
    except Exception:  # pylint: disable=broad-except
        logger.exception(
            'Ocurrió un error al realizar la operación: {}'.format(args.mode))

    logging.shutdown()


if __name__ == '__main__':
    main()
