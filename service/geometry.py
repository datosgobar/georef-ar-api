"""Módulo 'geometry' de georef-ar-api.

Contiene funciones utilizadas para operar con geometrías, utilizando la
librería Shapely.
"""

import shapely.ops
import shapely.geometry
from service import names as N


def street_number_location(geom, number, start, end):
    """Obtiene las coordenadas de un punto dentro de un tramo de calle.

    Args:
        geom (str): Geometría de un tramo de calle.
        number (int or None): Número de puerta o altura.
        start (int): Numeración inicial del tramo de calle.
        end (int): Numeración final del tramo de calle.

    Returns:
        dict: Coordenadas del punto.

    """
    if geom['type'] != 'MultiLineString':
        raise TypeError('GeoJSON type must be MultiLineString')

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


def streets_intersection_location(geom_a, geom_b):
    if geom_a['type'] != 'MultiLineString' or \
       geom_b['type'] != 'MultiLineString':
        raise TypeError('GeoJSON type must be MultiLineString')

    shape_a = shapely.geometry.MultiLineString(geom_a['coordinates'])
    shape_b = shapely.geometry.MultiLineString(geom_b['coordinates'])
    lat, lon = None, None

    intersection = shape_a.intersection(shape_b)

    if isinstance(intersection, shapely.geometry.Point):
        lat = intersection.y  # pylint: disable=no-member
        lon = intersection.x  # pylint: disable=no-member
    elif isinstance(intersection, shapely.geometry.MultiPoint):
        # Una o las dos calles tiene más de un tramo, y la intersección no
        # ocurre en un solo punto si no que en varios
        centroid = intersection.centroid
        lat = centroid.y  # pylint: disable=no-member
        lon = centroid.x  # pylint: disable=no-member

    return {
        N.LAT: lat,
        N.LON: lon
    }
