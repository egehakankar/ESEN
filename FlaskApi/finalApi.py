from flask import Flask, request, jsonify
from geographiclib.geodesic import Geodesic

import os
import math
import gdal
import json
import numpy as np

#-----Init app-----
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

#-----JSON Encoder-----
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):

            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}

        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()

        elif isinstance(obj, (np.bool_)):
            return bool(obj)

        elif isinstance(obj, (np.void)): 
            return None

        return json.JSONEncoder.default(self, obj)

#-----Route Validation-----
class RouteValidation:
    def __init__(self, filename):
        self.driver = gdal.GetDriverByName('GTiff')
        self.dataset = gdal.Open(filename)
        self.band = self.dataset.GetRasterBand(1)

        self.cols = self.dataset.RasterXSize
        self.rows = self.dataset.RasterYSize

        self.transform = self.dataset.GetGeoTransform()

        self.xOrigin = self.transform[0]
        self.yOrigin = self.transform[3]
        self.pixelWidth = self.transform[1]
        self.pixelHeight = -self.transform[5]

        self.data = self.band.ReadAsArray(0, 0, self.cols, self.rows)
        self.clearness = 50

    def validateRoute(self, routeCoord, groundElevations):
        checker = True

        col = int((routeCoord[0] - self.xOrigin) / self.pixelWidth)
        row = int((self.yOrigin - routeCoord[1]) / self.pixelHeight)
        # print("col,row", row, col)
        groundElevations.append(self.data[row][col])
        # print(row, "|", col, "|", "Ground elevation: " + str(self.data[row][col]),
        #     "| UAV elevation: " + str(coord[2]))

        if routeCoord[2] - self.clearness > self.data[row][col]:
            print("Ok")
        elif routeCoord[2] < self.data[row][col]:
            print("Impact")
            checker = False
        else:
            print("Close rapprochement. " +
                  str(routeCoord[2] - self.data[row][col]) + " meter close.")
            checker = False
        return (checker)

routeCoordinates = []
UAVElevations = []
distances = []
lastDistance = 0

def find_inter_points(lat1, lon1, alt1, lat2, lon2, alt2, interval):
    global lastDistance
    geod = Geodesic(6378388, 1 / 297.0)  # the international ellipsoid
    l = geod.InverseLine(lat1, lon1, lat2, lon2)
    n = int(math.ceil(l.s13 / interval))

    altDif = alt2 - alt1
    for i in range(n + 1):
        s = min(interval * i, l.s13)
        g = l.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        # print("{:.0f} {:.5f} {:.5f} {:.5f}".format(
        #   g['s12'], g['lat2'], g['lon2'], g['azi2']))
        latitude = g['lat2']
        longitude = g['lon2']
        distance = g['s12']
        altitude = alt1 + altDif * distance / l.s13
        routeCoordinates.append((longitude, latitude, altitude))
        UAVElevations.append(altitude)
        distances.append(distance + lastDistance)
    lastDistance = distances[len(distances) - 1]

def mainRout(wayPoints):
    # wayPoints = [(8.10868, 42.32376, 1000), (8.10869, 42.32376, 1100)]
    interval = 30  # meter

    for i in range(len(wayPoints)-1):
        find_inter_points(wayPoints[i][0], wayPoints[i][1], wayPoints[i][2], wayPoints[i+1][0],
                          wayPoints[i+1][1], wayPoints[i+1][2], interval)

    counter = 0
    groundElevations = []
    firstilat = math.floor(routeCoordinates[0][1])
    firstilon = math.floor(routeCoordinates[0][0])

    # print("routeCoordinates", routeCoordinates)
    for routeCoord in routeCoordinates:
        ilat = math.floor(routeCoord[1])
        ilon = math.floor(routeCoord[0])

        north_coord = str(ilat).zfill(2)
        east_coord = str(ilon).zfill(3)

        tiffName = "ASTGTMV003_N" + north_coord + "E" + \
            east_coord + "_dem.tif"  # ASTGTMV003_N39E032_dem.tif
        # print("tiffName", tiffName)

        print(tiffName)
        if counter == 0:
            f = RouteValidation(tiffName)
        if firstilat != ilat or firstilon != ilon:
            firstilat = ilat
            firstilon = ilon
            f = RouteValidation(tiffName)
        isOk = f.validateRoute(routeCoord, groundElevations)
        # print("Validation Result:", isOk)
        counter += 1

    return groundElevations, UAVElevations, distances


#------Route Class/Model-----

#-----Create a route and get the distances, uavelevations, groundelevations-----
@app.route('/product', methods=['POST'])
def add_product():
    wayPoints = request.json['wayPoints']
    groundElevation, UAVElevations, distances = mainRout(wayPoints)

    groundElevation = json.dumps(groundElevation, cls=NpEncoder)
    UAVElevations = json.dumps(UAVElevations)
    distances = json.dumps(distances)

    jsonobj = {'groundElevation':groundElevation,
    'Uav': UAVElevations,
    'distances': distances
    }

    return jsonobj

# Run Server
if __name__ == '__main__':
    app.run(debug=True)
