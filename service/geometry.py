"""Módulo 'geometry' de georef-ar-api.

Contiene funciones utilizadas para operar con geometrías, utilizando la
librería Shapely.
"""

import shapely.ops
import shapely.geometry
from service import names as N


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
