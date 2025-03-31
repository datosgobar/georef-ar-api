import math

import shapely
import shapely.ops

from service.geometry import offset_block_street
from . import GeorefLiveTest


class Test(GeorefLiveTest):

    def test_offset_block_street(self):

        long_deg, lat_deg = -57.005, -34.005
        delta_long_deg, delta_lat_deg = .001, .001
        delta_long, delta_lat = 91, 111

        offset_deg = 0.0001
        offset_long, offset_lat = .1 * delta_long, .1 * delta_lat

        point_n = [long_deg, lat_deg + delta_lat_deg]
        point_w, point_e = [long_deg - delta_long_deg, lat_deg], [long_deg + delta_lat_deg, lat_deg]
        point_s = [long_deg, lat_deg - delta_lat_deg]

        # Una calle de sur a norte
        shape = shapely.geometry.MultiLineString([[point_s, point_n]])
        line = shapely.ops.linemerge(shape)

        line_l = offset_block_street(line, "left", distance=offset_long)
        self.assertTrue(math.isclose(line_l.coords[0][1], line.coords[0][1], abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[1][1], line.coords[1][1], abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[0][0], line.coords[0][0] - offset_deg, abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[1][0], line.coords[1][0] - offset_deg, abs_tol=.00001))

        line_r = offset_block_street(line, "right", distance=offset_long)
        self.assertTrue(math.isclose(line_r.coords[0][1], line.coords[0][1], abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[1][1], line.coords[1][1], abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[0][0], line.coords[0][0] + offset_deg, abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[1][0], line.coords[1][0] + offset_deg, abs_tol=.00001))

        # Una calle de oeste a este
        shape = shapely.geometry.MultiLineString([[point_w, point_e]])
        line = shapely.ops.linemerge(shape)

        line_l = offset_block_street(line, "left", distance=offset_lat)
        self.assertTrue(math.isclose(line_l.coords[0][0], line.coords[0][0], abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[1][0], line.coords[1][0], abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[0][1], line.coords[0][1] + offset_deg, abs_tol=.00001))
        self.assertTrue(math.isclose(line_l.coords[1][1], line.coords[1][1] + offset_deg, abs_tol=.00001))

        line_r = offset_block_street(line, "right", distance=offset_lat)
        self.assertTrue(math.isclose(line_r.coords[0][0], line.coords[0][0], abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[1][0], line.coords[1][0], abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[0][1], line.coords[0][1] - offset_deg, abs_tol=.00001))
        self.assertTrue(math.isclose(line_r.coords[1][1], line.coords[1][1] - offset_deg, abs_tol=.00001))