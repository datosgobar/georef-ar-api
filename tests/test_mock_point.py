from service.geometry import Point
from . import GeorefMockTest

POINT_1 = Point(-58.381614, -34.603713)  # Obelisco
POINT_2 = Point(-58.373691, -34.608874)  # Cabildo
POINT_3 = Point(-58.373720, -34.592172)  # Torre Monumental - Retiro

DISTANCES = [
    (POINT_1, POINT_2, 920),
    (POINT_1, POINT_3, 1470),
    (POINT_2, POINT_3, 1855)
]


class PointTest(GeorefMockTest):
    def test_distance_0(self):
        """La distancia entre dos puntos iguales debería ser 0."""
        point = Point(0, 0)
        self.assertAlmostEqual(point.approximate_distance_meters(point), 0)

    def test_distances(self):
        """La distancia entre dos puntos conocidos debe ser correcta."""
        for p1, p2, distance in DISTANCES:
            calculated = p1.approximate_distance_meters(p2)
            self.assertAlmostEqual(distance, calculated, delta=5)

    def test_midpoint(self):
        """El punto medio entre dos puntos debe ser correcto."""
        p1 = Point(0, 0)
        p2 = Point(10, 10)
        midpoint = p1.midpoint(p2)
        self.assertAlmostEqual(midpoint.lat, 5)
        self.assertAlmostEqual(midpoint.lon, 5)
