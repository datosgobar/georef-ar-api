"""Módulo 'geometry' de georef-ar-api.

Contiene funciones utilizadas para operar con geometrías, utilizando la
librería Shapely.
"""

import math
import shapely.geometry
import shapely.ops
from service import names as N

MEAN_EARTH_RADIUS_KM = 6371


def street_extents(door_nums, number):
    """Dados los datos de alturas de una calle, y una altura recibida en una
    consulta, retorna los extremos de la calle que contienen la altura.
    Idealmente, se utilizaría siempre start_r y end_l, pero al contar a veces
    con datos incompletos, se flexibiliza la elección de extremos para poder
    geolocalizar más direcciones.

    Args:
        door_nums (dict): Datos de alturas de la calle.
        number (int): Altura recibida en una consulta.

    Returns:
        tuple (int, int): Altura inicial y final de la calle que contienen la
            altura especificada.

    Raises:
        ValueError: Si la altura no está contenida dentro de ninguna
            combinación de extremos.

    """
    start_r = door_nums[N.START][N.RIGHT]
    start_l = door_nums[N.START][N.LEFT]
    end_r = door_nums[N.END][N.RIGHT]
    end_l = door_nums[N.END][N.LEFT]

    combinations = [(start_r, end_l), (start_l, end_r), (start_r, end_r),
                    (start_l, end_l)]

    for start, end in combinations:
        if start <= number <= end:
            return start, end

    raise ValueError('Street number out of range')


def street_number_location(street, number):
    """Obtiene las coordenadas de una altura dentro de una calle.

    Args:
        street (dict): Datos de la calle (doc de Elasticsearch).
        number (int or None): Número de puerta o altura.

    Returns:
        dict: Coordenadas del punto.

    """
    geom = street[N.GEOM]
    if geom['type'] != 'MultiLineString':
        raise TypeError('GeoJSON type must be MultiLineString')

    start, end = street_extents(street[N.DOOR_NUM], number)
    shape = shapely.geometry.MultiLineString(geom['coordinates'])
    line = shapely.ops.linemerge(shape)
    lat, lon = None, None

    if isinstance(line, shapely.geometry.LineString):
        # Si la geometría de la calle pudo ser combinada para formar un único
        # tramo, encontrar la ubicación interpolando la altura con el inicio y
        # fin de altura de la calle.
        ip = line.interpolate((number - start) / (end - start),
                              normalized=True)
        # TODO:
        # line.interpolate retorna un shapely Point pero pylint solo mira
        # los atributos de BaseGeometry.
        lat = ip.y  # pylint: disable=no-member
        lon = ip.x  # pylint: disable=no-member

    return {
        N.LAT: lat,
        N.LON: lon
    }


def geojson_point_to_location(geom):
    if geom['type'] != 'Point':
        raise TypeError('GeoJSON type must be Point')

    return {
        N.LON: geom['coordinates'][0],
        N.LAT: geom['coordinates'][1]
    }


def build_circle_geometry(location, radius_meters):
    return {
        'type': 'circle',
        'radius': '{}m'.format(radius_meters),
        'coordinates': [location[N.LON], location[N.LAT]]
    }


def geojson_points_centroid(point_a, point_b):
    point_a = shapely.geometry.Point(point_a['coordinates'])
    point_b = shapely.geometry.Point(point_b['coordinates'])

    centroid = shapely.geometry.MultiPoint([point_a, point_b]).centroid
    return {
        N.LON: centroid.x,  # pylint: disable=no-member
        N.LAT: centroid.y   # pylint: disable=no-member
    }


def approximate_distance_meters(loc_a, loc_b):
    # https://en.wikipedia.org/wiki/Haversine_formula
    lat_a = math.radians(loc_a[N.LAT])
    lat_b = math.radians(loc_b[N.LAT])
    diff_lat = math.radians(loc_b[N.LAT] - loc_a[N.LAT])
    diff_lon = math.radians(loc_b[N.LON] - loc_a[N.LON])

    a = math.sin(diff_lat / 2) ** 2
    b = math.cos(lat_a) * math.cos(lat_b) * (math.sin(diff_lon / 2) ** 2)

    kms = 2 * MEAN_EARTH_RADIUS_KM * math.asin(math.sqrt(a + b))
    return kms * 1000
