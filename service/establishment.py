"""Módulo 'establishment' de georef-ar-api.

Contiene funciones y clases utilizadas para normalizar establecimientos (recurso
/establecimientos-cercanos). Este módulo puede ser considerado una extensión del módulo
'normalizer', con funciones específicas para el procesamiento de establecimientos.
"""

from service import names as N, constants
from service import data
from service.data import TerritoriesSearch
from service.query_result import QueryResult


class NearbyEstablishmentsSearch(TerritoriesSearch):

    def __init__(self, name, query):
        self._query = query
        super().__init__(name, query)
        self._building_type = name

    def _read_query(self, ids=None, name=None, census_locality=None, local_government=None, department=None, state=None,
                    exact=False, geo_shape_geoms=None, lat=None, lon=None, order=None, tipo=None,
                    distance=None, category=None, **kwargs):
        super()._read_query(ids, name, census_locality, local_government, department, state, exact, geo_shape_geoms,
                            **kwargs)

        if distance:

            self._search = self._search.filter('geo_distance', distance=f"{distance}m", **{
                N.CENTROID: {
                    'lat': lat,
                    'lon': lon
                }
            })

            # Calcula la distancia para incorporar el campo en la respuesta.
            self._search = self._search.script_fields(
                distancia={
                    "script": {
                        "source": f"doc['{N.CENTROID}'].arcDistance(params.lat, params.lon)",
                        "params": {"lat": lat, "lon": lon}
                    }
                }
            )


    @property
    def result(self):
        result = super().result

        new_hits = []
        for hit in result.hits:
            # Devolvemos la distancia como float
            hit = hit.copy()
            distancia = hit.get("distancia", None)
            if distancia and isinstance(distancia, list):
                hit["distancia"] = round(distancia[0], 2)

            hit[N.ESTABLISHMENT_TYPE] = self._building_type

            new_hits.append(hit)

        result._hits = new_hits

        return result


class EducationalEstablishmentsSearch(NearbyEstablishmentsSearch):
    """Representa una búsqueda de establecimientos educativos. Utiliza el índice
        'establecimientos_educativos' para buscar datos.

        """

    def __init__(self, query):
        super().__init__(N.EDUCATIONAL_INSTITUTIONS, query)

    def _read_query(self, ids=None, name=None, census_locality=None, local_government=None, department=None, state=None,
                    exact=False, geo_shape_geoms=None, lat=None, lon=None, order=None,
                    administration=None, category=None, **kwargs):
        super()._read_query(ids, name, census_locality, local_government, department, state, exact, geo_shape_geoms, lat, lon,
                            order, **kwargs)


class UniversityEstablishmentsSearch(NearbyEstablishmentsSearch):
    """Representa una búsqueda de establecimientos universitarios. Utiliza el índice
            'instituciones_universitarias' para buscar datos.

            """

    def __init__(self, query):
        """Inicializa un objeto de tipo UniversityEstablishmentsSearch.

                Args:
                    query (dict): Parámetros de la búsqueda. Ver el método
                        '_read_query' para tomar nota de los valores permitidos
                        dentro del diccionario.

                """
        super().__init__(N.UNIVERSITY_INSTITUTIONS, query)

    def _read_query(self, ids=None, name=None, census_locality=None, local_government=None, department=None, state=None,
                    exact=False, geo_shape_geoms=None, lat=None, lon=None, order=None,
                    administration=None, university=None, **kwargs):
        super()._read_query(ids, name, census_locality, local_government, department, state, exact, geo_shape_geoms, lat, lon,
                            order, **kwargs)


ACTIVE_ESTABLISHMENTS_INDEX = {
    N.EDUCATIONS: EducationalEstablishmentsSearch,
    N.UNIVERSITIES: UniversityEstablishmentsSearch,
}


class EstablishmentMultiSearch:

    def __init__(self, query, fmt):
        self._query = query
        self._format = fmt
        self._searches = []

        tipos = query.get(N.TYPE)
        if not tipos:
            tipos = list(ACTIVE_ESTABLISHMENTS_INDEX.keys())
        elif isinstance(tipos, str):
            tipos = [tipos]

        for tipo in tipos:
            search_class = ACTIVE_ESTABLISHMENTS_INDEX.get(tipo)
            if not search_class:
                continue
            self._searches.append(search_class(query))

    def _apply_sort(self, hits):
        """Ordena los resultados de direcciones. El ordenamiento se hace
        localmente ya que en 'planner_steps' se modifican los lados de las
        intersecciones.

        Args:
            hits (list): Lista de resultados de búsqueda de direcciones.

        """
        order = self._query.get('order', None)

        if order is None:
            return

        # Ordenar resultados utilizando la primera calle
        if order == N.ID:
            hits.sort(key=lambda hit: hit[N.ID])
        elif order == N.NAME:
            hits.sort(key=lambda hit: hit[N.NAME])
        elif order == N.DISTANCE:
            hits.sort(key=lambda hit: hit[N.DISTANCE])
        else:
            raise ValueError('Invalid sort field')

    def get_query_results(self, es, params):
        if not self._searches:
            return QueryResult.empty(self._query)

        data.ElasticsearchSearch.run_searches(es, self._searches)

        hits = []
        for search in self._searches:
            hits.extend(search.result.hits)

        # Aplicar ordenamiento local
        self._apply_sort(hits)

        # Aplicar truncado
        total = params.values.get(N.MAX, constants.MAX_RESULT_LEN)
        offset = params.values.get(N.OFFSET, 0)
        hits = hits[offset:offset + total]

        return QueryResult.from_entity_list(hits,
                                            params.values,
                                            total,
                                            offset)


def run_establishment_queries(es, params_list, queries, formats):
    results = []

    for params, query, fmt in zip(params_list, queries, formats):
        searcher = EstablishmentMultiSearch(query, fmt)
        result = searcher.get_query_results(es, params)
        results.append(result)

    return results