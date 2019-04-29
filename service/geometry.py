"""Módulo 'geometry' de georef-ar-api.

Contiene funciones utilizadas para operar con geometrías en formato GeoJSON
utilizando la librería Shapely.
"""

import math
import shapely.geometry
import shapely.ops
from service import names as N

# Radio de la tierra promedio para WGS84
_MEAN_EARTH_RADIUS_KM = 6371.0088


def _street_block_extents(door_nums, number):
    """Dados los datos de alturas de una cuadra, y una altura recibida en una
    consulta, retorna los extremos de la cuadra que contienen la altura. Los
    valores devueltos corresponderán al lado derecho o izquierdo de la cuadra,
    o None.

    Args:
        door_nums (dict): Datos de alturas de la cuadra.
        number (int): Altura recibida en una consulta.

    Raises:
        ValueError: Si la altura no está contenida dentro de ninguna
            combinación de extremos.

    Returns:
        tuple (int, int): Altura inicial y final de la cuadra que contienen la
            altura especificada.

    """
    start_r = door_nums[N.START][N.RIGHT]
    start_l = door_nums[N.START][N.LEFT]
    end_r = door_nums[N.END][N.RIGHT]
    end_l = door_nums[N.END][N.LEFT]

    if start_r <= number <= end_r:
        return start_r, end_r

    if start_l <= number <= end_l:
        return start_l, end_l

    raise ValueError('Street number out of range')


def street_block_number_location(geom, door_numbers, number,
                                 approximate=False):
    """Intenta obtener las coordenadas de una altura dentro de una calle
    (georreferenciación). Para lograr esto, se toma la geometría de la cuadra
    obtenida vía Elasticsearch, y se realiza una interpolación utilizando los
    datos de inicio/fin de alturas de la cuadra.

    En algunos casos, es posible que la operacion falle debido a problemas con
    los datos de la cuadra. Estos casos son:
        - La cuadra está compuesta por dos o más tramos no conectados. Esto
          solo sucede en algunas localidades censales, y es un problema de
          datos que debería corregirse.
        - Los valores de alturas (fin e inicio) de la cuadra son 0, o son
          idénticos.

    Args:
        geom (dict): Geometría de la cuadra en formato GeoJSON.
        door_numbers (dict): Límites de altura de la cuadra.
        number (int or None): Número de puerta o altura.
        approximate (bool): Si es verdadero, devolver un estimado de las
            coordenadas en caso de que la interpolación falle.

    Raises:
        TypeError: Cuando la geometría no es de tipo Point.

    Returns:
        Point: Punto representando la posición de la altura, o 'None'
            si no pudo ser calculada.

    """
    if geom['type'] != 'MultiLineString':
        raise TypeError('GeoJSON type must be MultiLineString')

    shape = shapely.geometry.MultiLineString(geom['coordinates'])
    line = shapely.ops.linemerge(shape)

    if isinstance(line, shapely.geometry.LineString) and number is not None:
        start, end = _street_block_extents(door_numbers, number)

        if start < end:
            # Se cumplen las condiciones:
            #  - La geometría de la cuadra pudo ser combinada en un solo tramo
            #    contínuo (verdadero en el mayor de los casos).
            #  - La altura a buscar no es None (puede ser 0).
            #  - Los extremos inicio y comienzo de la cuadra no son iguales.
            # Con las condiciones dadas, realizar la interpolación y retornar
            # el resultado.
            ip = line.interpolate((number - start) / (end - start),
                                  normalized=True)

            return Point.from_shapely_point(ip)

    if approximate:
        # Si cualquiera de las condiciones falló pero se permiten estimados,
        # retornar el centroide de la cuadra.
        return Point.from_shapely_point(line.centroid)

    return None


class Point:
    """Representa un punto en el plano cartesiano (x, y - lon, lat). Sirve como
    intermediario entre distintas formas de representar puntos: shapely.Point,
    GeoJSON 'Point' y {'lon': X, 'lat': Y}.

    Attributes:
        _lon (float): Longitud.
        _lat (float): Latitud.

    """

    __slots__ = ['_lon', '_lat']

    def __init__(self, lon, lat):
        """Inicializa un objeto de tipo 'Point'.

        Args:
            lon (float): Longitud (x).
            lat (float): Latitud (y).

        """
        self._lon = lon
        self._lat = lat

    @classmethod
    def from_shapely_point(cls, point):
        """Construye un objeto 'Point' desde un punto de Shapely.

        Args:
            point (shapely.geometry.Point): Punto a copiar.

        Returns:
            Point: Punto creado.

        """
        return cls(point.x, point.y)

    @classmethod
    def from_geojson_point(cls, geom):
        """Construye un objeto 'Point' desde un punto GeoJSON.

        Raises:
            TypeError: Cuando el argumento no tiene tipo Point.

        Args:
            geom (dict): Punto GeoJSON a copiar.

        Returns:
            Point: Punto creado.

        """
        if geom['type'] != 'Point':
            raise TypeError('Geometry type must be Point')

        return cls(*geom['coordinates'])

    @classmethod
    def from_json_location(cls, loc):
        """Construye un objeto 'Point' desde una ubicación.

        Args:
            loc (dict): Ubicación a copiar.

        Returns:
            Point: Punto creado.

        """
        return cls(loc[N.LON], loc[N.LAT])

    @property
    def lon(self):
        return self._lon

    @property
    def lat(self):
        return self._lat

    def to_geojson(self):
        """Retorna una representación GeoJSON de la instancia de Point.

        Returns:
            dict: Valor GeoJSON de la instancia de Point.

        """
        return {
            'type': 'Point',
            'coordinates': [self._lon, self._lat]
        }

    def to_geojson_circle(self, radius_meters):
        """Retorna una representación GeoJSON de un círculo centrado en la
        instancia de Point.

        Args:
            radius_meters (int): Radio del círculo en metros.

        Returns:
            dict: Valor GeoJSON del círculo (tipo GeoJSON: "polygon").

        """
        point = self.to_shapely_point()

        # Queremos crear un círculo GeoJSON centrado en self, con un radio de
        # 'radius_meters'.
        #
        # Para lograr esto, transformamos self a un punto Shapely. Luego,
        # utilizamos el método .buffer() para crear una geometría
        # cuasi-circular centrada en ese punto. El método requiere una variable
        # 'distance' que representa el radio del círculo a crear, en grados.
        #
        # Para obtener los grados necesarios, imaginamos que el radio de
        # nuestro círculo a crear es en realidad un arco sobre la superficie de
        # la tierra. Conocemos la longitud de este arco en metros
        # ('radius_meters'), y conocemos el radio de la tierra
        # ('_MEAN_EARTH_RADIUS_KM'), por lo que podemos usar la ecuación:
        #
        #     ángulo de arco = largo del arco / radio
        #
        # para calcular el ángulo que el arco representa sobre la superficie de
        # la tierra.

        distance_angle = math.degrees(radius_meters /
                                      (1000 * _MEAN_EARTH_RADIUS_KM))

        # Con 'resolution=3', obtenemos un polígono de 13 vértices (3 vértices
        # por cuarto de círculo, mas uno para cerrar) con forma cuasi-circular.
        circle = point.buffer(distance_angle, resolution=3)

        return {
            'type': 'polygon',
            'coordinates': [list(circle.exterior.coords)]
        }

    def to_json_location(self):
        """Retorna una representación como ubicación de la instancia de Point.
        La ubicación es un diccionario con valores 'lat' y 'lon'.

        Returns:
            dict: Ubicación creada a partir de la instancia de Point.

        """
        return {
            N.LON: self._lon,
            N.LAT: self._lat
        }

    def to_shapely_point(self):
        """Retorna una representación shapely.Point de la instancia de Point.

        Returns:
            shapely.geometry.Point: Valor shapely.Point de la instancia de
                Point.

        """
        return shapely.geometry.Point([self._lon, self._lat])

    def midpoint(self, other):
        """Calcula el punto intermedio entre esta instancia de Point y otra.

        Args:
            other (Point): Punto hacia el cual calcular el punto medio.

        Returns:
            Point: Punto medio entre este Point y 'other'.

        """
        points = [self.to_shapely_point(), other.to_shapely_point()]

        centroid = shapely.geometry.MultiPoint(points).centroid
        return Point.from_shapely_point(centroid)

    def approximate_distance_meters(self, other):
        """Retorna la distancia aproximada, en metros, entre esta instancia de
        Point y otro punto.

        La distancia se calcula utilizando la fórmula de Haversine
        (https://es.wikipedia.org/wiki/F%C3%B3rmula_del_haversine) y no debería
        ser aplicada en casos donde se necesiten altos grados de precisión.

        Args:
            other (Point): Punto hacia el cual calcular la distancia.

        Returns:
            float: Distancia aproximada en metros desde esta instancia de Point
                y 'other'.

        """
        lon_a = math.radians(self._lon)
        lat_a = math.radians(self._lat)
        lon_b = math.radians(other.lon)
        lat_b = math.radians(other.lat)
        diff_lat = lat_b - lat_a
        diff_lon = lon_b - lon_a

        a = math.sin(diff_lat / 2) ** 2
        b = math.cos(lat_a) * math.cos(lat_b) * (math.sin(diff_lon / 2) ** 2)

        kms = 2 * _MEAN_EARTH_RADIUS_KM * math.asin(math.sqrt(a + b))
        return kms * 1000
