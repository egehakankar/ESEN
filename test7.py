import gdal
from geographiclib.geodesic import Geodesic
import math

def find_inter_points(lat1, lon1, lat2, lon2, interval):
    geod = Geodesic(6378388, 1 / 297.0)  # the international ellipsoid
    l = geod.InverseLine(lat1, lon1, lat2, lon2)
    ds = interval
    n = int(math.ceil(l.s13 / interval))
    for i in range(n + 1):
        if i == 0:
            print("distance latitude longitude azimuth")
        s = min(ds * i, l.s13)
        g = l.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        print("{:.0f} {:.5f} {:.5f} {:.5f}".format(
            g['s12'], g['lat2'], g['lon2'], g['azi2']))

lat1 = 39.129694
lon1 = 33.310130
lat2 = 39.8124
lon2 = 33.7361
interval = 5000

find_inter_points(lat1, lon1, lat2, lon2, interval)

