"""Módulo es_config.py de georef-ar-api

Contiene toda la información necesaria para la creación de documentos e índices
de Elasticsearch para Georef.

Los campos de los documentos están en castellano ya que corresponden con los
datos generados por el ETL.

El excluimiento del campo 'geometria' en _source se debe a que las geometrías
tienden a aumentar significativamente el tamaño de los documentos, por lo que
la performance de la búsqueda por id/nombre/etc se ve disminuida. Para poder
contar con las geometrías originales (para queries GeoShape y para poder
utilizarlas como valores de respuesta), se crean índices adicionales con las
geometrías intactas. Notar que este cambio solo se aplica a entidades que
tienen geometrías de gran tamaño (provincias, municipios y departamentos).

Para más información, ver:
https://www.elastic.co/guide/en/elasticsearch/reference/current/general-recommendations.html#maximum-document-size

"""

from elasticsearch_dsl import Document, Index
from elasticsearch_dsl import analyzer, normalizer, token_filter
from elasticsearch_dsl import Object, Float, GeoShape, Keyword, Text, Integer
from elasticsearch_dsl import MetaField
from .. import names as N

GEOM_INDEX_SUFFIX = '{}-geometria'
GEOMETRYLESS_INDICES = {N.STATES, N.DEPARTMENTS, N.MUNICIPALITIES}

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

synonyms_only_filter = token_filter(
    'synonyms_only_filter',
    type='keep_types',
    types=['SYNONYM']
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

name_analyzer_excluding_terms = 'name_analyzer_excluding_terms'
"""El analizador 'name_analyzer_excluding_terms' sigue el mismo proceso de
construcción que 'name_analyzer_synonyms', ya que su definición también depende
de un listado de términos excluyentes externo.
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


def gen_name_analyzer_excluding_terms(excluding_terms):
    """Crea un analizador para nombres que sólo retorna TE (términos
    excluyentes).

    Por ejemplo, si el archivo de configuración de TE contiene las siguientes
    reglas:

    santa, salta, santo
    caba, cba

    Entonces, aplicar el analizador a la búsqueda 'salta' debería retornar
    'santa' y 'santo', mientras que buscar 'caba' debería retornar 'cba'.

    El analizador se utiliza para excluir resultados de búsquedas específicas.

    Args:
        excluding_terms (list): Lista de TE a utilizar especificados como
            sinónimos Solr.

    Returns:
        elasticsearch_dsl.analysis.Analyzer: analizador de texto con nombre
            'name_analyzer_excluding_terms'.

    """
    name_excluding_terms_filter = token_filter(
        'name_excluding_terms_filter',
        type='synonym',
        synonyms=excluding_terms
    )

    return analyzer(
        name_analyzer_excluding_terms,
        tokenizer='standard',
        filter=[
            'lowercase',
            'asciifolding',
            name_excluding_terms_filter,
            synonyms_only_filter,
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

UnindexedTextField = Text(index=False)

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

StateSubField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField,
        'interseccion': Float(index=False)
    },
    dynamic='strict'
)

DepartmentSubField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField
    },
    dynamic='strict'
)

MunicipalitySubField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField
    },
    dynamic='strict'
)

CensusLocalitySubField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField
    },
    dynamic='strict'
)

StreetSubField = Object(
    properties={
        'id': Keyword(),
        'nombre': NameField,
        'provincia': StateSubField,
        'departamento': DepartmentSubField,
        'localidad_censal': CensusLocalitySubField,
        'categoria': UnindexedTextField,
        'fuente': UnindexedTextField
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
    geográficas.

    """

    id = IdField


class State(Entity):
    nombre = NameField
    nombre_completo = UnindexedTextField
    iso_id = UnindexedTextField
    iso_nombre = UnindexedTextField
    centroide = CentroidField
    geometria = GeoShape()
    categoria = UnindexedTextField
    fuente = UnindexedTextField

    class Meta:
        source = MetaField(excludes=['geometria'])


class StateGeom(Entity):
    geometria = GeoShape()


class Department(Entity):
    nombre = NameField
    nombre_completo = Text(index=False)
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSubField
    categoria = UnindexedTextField
    fuente = UnindexedTextField

    class Meta:
        source = MetaField(excludes=['geometria'])


class DepartmentGeom(Entity):
    geometria = GeoShape()


class Municipality(Entity):
    nombre = NameField
    nombre_completo = UnindexedTextField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSubField
    categoria = UnindexedTextField
    fuente = UnindexedTextField

    class Meta:
        source = MetaField(excludes=['geometria'])


class MunicipalityGeom(Entity):
    geometria = GeoShape()


class CensusLocality(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSubField
    departamento = DepartmentSubField
    municipio = MunicipalitySubField
    categoria = UnindexedTextField
    funcion = UnindexedTextField
    fuente = UnindexedTextField


class Settlement(Entity):
    nombre = NameField
    centroide = CentroidField
    geometria = GeoShape()
    provincia = StateSubField
    departamento = DepartmentSubField
    municipio = MunicipalitySubField
    localidad_censal = CensusLocalitySubField
    categoria = UnindexedTextField
    fuente = UnindexedTextField


class Locality(Settlement):
    # Las localidades tienen estructura idéntica a los asentamientos
    pass


class Street(Entity):
    nombre = NameField
    altura = StreetNumbersField
    geometria = GeoShape()
    provincia = StateSubField
    departamento = DepartmentSubField
    localidad_censal = CensusLocalitySubField
    # Indexar las categorías de calles ya que se puede filtrar por las mismas
    categoria = Text(
        analyzer=name_analyzer_synonyms,
        search_analyzer=name_analyzer
    )
    fuente = UnindexedTextField


class Intersection(Entity):
    calle_a = StreetSubField
    calle_b = StreetSubField
    geometria = GeoShape()


class StreetBlock(Entity):
    calle = StreetSubField
    altura = StreetNumbersField
    geometria = GeoShape()


def create_index(es, name, doc_class, shards, replicas, synonyms=None,
                 excluding_terms=None):
    """Crea un índice Elasticsearch utilizando un nombre y una clase de
    documento.

    Args:
        es (elasticsearch.Elasticsearch): Cliente Elasticsearch.
        name (str): Nombre del índice a crear.
        doc_class (type): Clase del documento (debe heredar de Document).
        shards (int): Cantidad de "shards" a utilizar para el índice.
        replicas (int): Cantidad de réplicas por "shard".
        synonyms (list): Lista de sinónimos a utilizar en caso de necesitar el
            analizador 'name_analyzer_synonyms'.
        excluding_terms (list): Lista de términos excluyentes a utilizar en
            caso de necesitar el analizador 'name_analyzer_excluding_terms'.

    """
    index = Index(name)

    # Crear el analizador 'name_analyzer_synonyms' solo si se lo pidió
    # explícitamente. Si el documento tipo 'doc_class' utiliza el analizador
    # en algún punto de su mapeo, la lista 'synonyms' debería estar presente.
    if synonyms is not None:
        index.analyzer(gen_name_analyzer_synonyms(synonyms))

    # Mismo razonamiento que con 'name_analyzer_synonyms'.
    if excluding_terms is not None:
        index.analyzer(gen_name_analyzer_excluding_terms(excluding_terms))

    index.document(doc_class)
    index.settings(number_of_shards=shards, number_of_replicas=replicas)
    index.create(using=es)


def geom_index_for(index):
    """Dado un nombre de índice, retorna su índice correspondiente que contenga
    las geometrías de la entidad.

    Args:
        index (str): Nombre del índice conteniendo entidades de las cuales se
            desea obtener las geometrías.

    Returns:
        str: Nombre de índice conteniendo las geometrías de las entidades
            almacenadas en 'index'.

    """
    if index in GEOMETRYLESS_INDICES:
        return GEOM_INDEX_SUFFIX.format(index)

    return index
