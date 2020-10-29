import gdal

ds = gdal.Open("C:/Users/Hakan/Desktop/esen/ASTGTMV003_N39E033_dem.tif")
width = ds.RasterXSize
height = ds.RasterYSize
gt = ds.GetGeoTransform()
minx = gt[0]
miny = gt[3] + width*gt[4] + height*gt[5] 
maxx = gt[0] + width*gt[1] + height*gt[2]
maxy = gt[3]

print(minx, maxy)

