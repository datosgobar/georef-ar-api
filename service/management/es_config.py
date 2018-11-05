"""Módulo es_config.py de georef-ar-api

Contiene toda la información necesaria para la creación de documentos e índices
de Elasticsearch para Georef.

Los campos de los documentos están en castellano ya que corresponden con los
datos generados por el ETL.

El excluimiento del campo 'geometria' en _source se debe a que las geometrías
tienden a aumentar significativamente el tamaño de los documentos, por lo que
la performance de la búsqueda por id/nombre/etc se ve disminuida. Para poder
contar con las geometrías originales (para queries GeoShape), se crean
índices adicionales con las geometrías intactas.

Para más información, ver:
https://www.elastic.co/guide/en/elasticsearch/reference/current/general-recommendations.html#maximum-document-size

"""

from elasticsearch_dsl import Document, Index
from elasticsearch_dsl import analyzer, normalizer, token_filter
from elasticsearch_dsl import Object, Float, GeoShape, Keyword, Text, Integer
from elasticsearch_dsl import MetaField

# Tipo de documento utilizado por default en elasticsearch_dsl
DOC_TYPE = 'doc'

# -----------------------------------------------------------------------------
# Analizadores, Filtros, Normalizadores
# -----------------------------------------------------------------------------


spanish_stopwords_filter = token_filter(
    'spanish_stopwords_filter',
    type='stop',
    stopwords=[
        # El filtro de stopwords _spanish_ de Elasticsearch es demasiado
        # abarcativo para los campos de texto utilizados en Georef (nombres de
        # entidades).
        'la', 'las', 'el', 'los', 'de', 'del', 'y', 'e', 'lo', 'al'
    ]
)

name_analyzer = analyzer(
    'name_analyzer',
    tokenizer='standard',
    filter=[
        'lowercase',
        'asciifolding',
        spanish_stopwords_filter
    ]
)


name_analyzer_synonyms = 'name_analyzer_synonyms'
"""El analizador 'name_analyzer_synonyms' no puede ser definido estáticamente,
ya que su definición depende del listado de sinónimos a utilizar. En cambio, se
lo define como un valor string que puede ser utilizado en los mapeos de los
documentos Elasticsearch, ya que los mismos aceptan analizadores (object) o
nombres de analizadores (str).

El analizador en sí se crea utilizando 'gen_name_analyzer_synonyms', si es
necesario.
"""


def gen_name_analyzer_synonyms(synonyms):
    """Crea un analizador para nombres con sinónimos.

    Args:
        synonyms (list): Lista de sinónimos a utilizar, en formato Solr.

    Returns:
        elasticsearch_dsl.analysis.Analyzer: analizador de texto con nombre
            'name_analyzer_synonyms'.

    """
    name_synonyms_filter = token_filter(
        'name_synonyms_filter',
        type='synonym',
        synonyms=synonyms
    )

    return analyzer(
        name_analyzer_synonyms,
        tokenizer='standard',
        filter=[
            'lowercase',
            'asciifolding',
            name_synonyms_filter,
            spanish_stopwords_filter
        ]
    )


lowcase_ascii_normalizer = normalizer(
    'lowcase_ascii_normalizer',
    filter=[
        'lowercase',
        'asciifolding'
    ]
)


# -----------------------------------------------------------------------------
# Campos comunes
# -----------------------------------------------------------------------------


IdField = Keyword()

CentroidField = Object(
    properties={
        'lat': Float(index=False),
        'lon': Float(index=False)
    },
    dynamic='strict'
)

NameField = Text(
    analyzer=name_analyzer_synonyms,
    search_analyzer=name_analyzer,
    fields={
        'exacto': Keyword(
            normalizer=lowcase_ascii_normalizer
        )
    }
)

StateSimpleField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField,
        'interseccion': Float(index=False)
    },
    dynamic='strict'
)

DepartmentSimpleField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField
    },
    dynamic='strict'
)

MunicipalitySimpleField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField
    },
    dynamic='strict'
)

StreetLimitField = Object(
    properties={
        'derecha': Integer(),
        'izquierda': Integer()
    },
    dynamic='strict'
)

StreetNumbersField = Object(
    properties={
        'inicio': StreetLimitField,
        'fin': StreetLimitField
    },
    dynamic='strict'
)


# -----------------------------------------------------------------------------
# Documentos
# -----------------------------------------------------------------------------


class Entity(Document):
    """Clase base para todos los documentos que representan entidades
    geograficas.
    """
    id = IdField


class State(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()

    class Meta:
        source = MetaField(excludes=['geometria'])


class StateGeom(Entity):
    geometria = GeoShape()


class Department(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSimpleField

    class Meta:
        source = MetaField(excludes=['geometria'])


class DepartmentGeom(Entity):
    geometria = GeoShape()


class Municipality(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSimpleField

    class Meta:
        source = MetaField(excludes=['geometria'])


class MunicipalityGeom(Entity):
    geometria = GeoShape()


class Locality(Entity):
    nombre = NameField
    centroide = CentroidField
    tipo = Keyword()
    geometria = GeoShape()
    provincia = StateSimpleField
    departamento = DepartmentSimpleField
    municipio = MunicipalitySimpleField

    class Meta:
        source = MetaField(excludes=['geometria'])


class Street(Entity):
    nombre = NameField
    nomenclatura = Text(index=False)
    tipo = Text(
        analyzer=name_analyzer_synonyms,
        search_analyzer=name_analyzer
    )
    altura = StreetNumbersField
    geometria = Text(index=False)
    provincia = StateSimpleField
    departamento = DepartmentSimpleField


def create_index(es, name, doc_class, synonyms=None):
    """Crea un índice Elasticsearch utilizando un nombre y una clase de
    documento.

    Args:
        es (elasticsearch.Elasticsearch): Cliente Elasticsearch.
        name (str): Nombre del índice a crear.
        doc_class (type): Clase del documento (debe heredar de Document).
        synonyms (list): Lista de sinónimos a utilizar en caso de necesitar el
            analizador 'name_analyzer_synonyms'.

    """
    index = Index(name)

    # Crear el analizador 'name_analyzer_synonyms' solo si se lo pidió
    # explícitamente. Si el documento tipo 'doc_class' utiliza el analizador
    # en algún punto de su mapeo, la lista 'synonyms' debería estar presente.
    if synonyms is not None:
        index.analyzer(gen_name_analyzer_synonyms(synonyms))

    index.document(doc_class)
    index.create(using=es)
