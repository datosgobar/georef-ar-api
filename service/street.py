"""Módulo 'street' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar calles (recurso
/calles). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de calles.

Notar que la búsqueda de calles (/calles) no es la búsqueda de direcciones
(/direcciones). La búsqueda de direcciones es más compleja ya que implica
interpretar las distintas partes de una dirección, luego buscar una calle que
contenga su altura, y posiblemente georreferenciarla. La búsqueda de calles es
simplemente buscar listados de calles por nombre, ID y otros criterios.
"""

from service import data
from service.query_result import QueryResult
from service import names as N


def run_street_queries(es, params_list, queries, formats):
    """Punto de entrada del módulo 'street.py'. Toma una lista de consultas de
    calles y las ejecuta, devolviendo los resultados QueryResult.

    Args:
        es (Elasticsearch): Conexión a Elasticsearch.
        params_list (list): Lista de ParametersParseResult.
        queries (list): Lista de búsquedas, generadas a partir de
            'params_list'.
        formats (list): Lista de parámetros de formato de cada búsqueda, en
            forma de diccionario.

    Returns:
        list: Lista de QueryResult, una por cada búsqueda.

    """

    searches = []
    for query, fmt in zip(queries, formats):
        processed_query = query.copy()

        if N.FULL_NAME in fmt[N.FIELDS]:
            # La nomenclatura incluye el nombre de la provincia y del depto.,
            # agregar esos campos a la query para luego poder extraer sus
            # nombres.
            processed_query['fields'] += (N.STATE, N.DEPT)

        searches.append(data.StreetsSearch(processed_query))

    data.ElasticsearchSearch.run_searches(es, searches)

    for search, fmt in zip(searches, formats):
        if N.FULL_NAME in fmt[N.FIELDS]:
            # Agregar nomenclatura a cada hit del resultado.
            for hit in search.result.hits:
                full_name = '{}, {}, {}'.format(
                    hit[N.NAME], hit[N.DEPT][N.NAME], hit[N.STATE][N.NAME]
                )
                hit[N.FULL_NAME] = full_name

    return [
        QueryResult.from_entity_list(search.result.hits,
                                     params.received_values(),
                                     search.result.total,
                                     search.result.offset)
        for search, params in zip(searches, params_list)
    ]
