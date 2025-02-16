#-------------------------------------------------------------------------------
# Name:        raster to vector converter
# Purpose:
#
# Author:      caleb
# Additional
# source:      [https://github.com/rasterio/rasterio/blob/main/rasterio/features.py#L77], https://gis.stackexchange.com/questions/187877/how-to-polygonize-raster-to-shapely-polygons/437855#437855
# Created:     09/08/2022
# Copyright:   (c) caleb 2024
# Licence:     <ardhi>
#-------------------------------------------------------------------------------

import rasterio as rio
from rasterio import features
from rasterio.features import shapes
from rasterio.enums import Resampling

import geopandas as gpd
from matplotlib import pyplot as plt


def raster_vector(input_raster,output_vector):

    #raster to vector operation

    #downsample from gdal
    ##ds=gdal.Open(input_file)
    ##array1=ds.GetRasterBand(1).ReadAsArray()
    ##dsRes = gdal.Warp(dir+"/lowRes.tif", ds, xRes = 10, yRes = 10,  resampleAlg = "bilinear")

    ##downsample from rasterio:
##    upscale_factor=1/20
##    with rio.open(input_raster) as dataset:
##        #resample to new shape
##        print(dataset.shape)
##        print(dataset.height,dataset.width)
##        data=dataset.read(out_shape=(dataset.count,int(dataset.height*upscale_factor),int(dataset.width*upscale_factor)),resampling=Resampling.bilinear)
##
##        print(data.shape)
##        #scale image transform
##        transform=dataset.transform.scale((dataset.width / data.shape[-1]),(dataset.height / data.shape[-2]))



    input_imagery=rio.open(input_raster)
    input_crs=input_imagery.crs
    input_transform=input_imagery.transform
    #raster to vector operation
    mask=None
    with rio.Env():
        with rio.open(input_raster) as depth_image:
            depth_array=depth_image.read(1).astype(int)

            result=({'properties': {'raster_val':v},'geometry':s}

             for i, (s,v)
             in enumerate(shapes(depth_array,mask=mask,transform=input_transform)))

    raster_polygon_values=list(result) # contains all the data, including No datavalues

    raster_polygon_values_minus_no_data=[] # to hold only values conatining the raster. No Data values not included


    # removing nodata values. Are encoded as -ve values
    for i in range(len(raster_polygon_values)):
        if raster_polygon_values[i]['properties']['raster_val'] > 0:
            raster_polygon_values_minus_no_data.append(raster_polygon_values[i])


    # export the vector to file. Can take quite some time e.g > 30 min for this case
    new_gpd=gpd.GeoDataFrame.from_features(raster_polygon_values_minus_no_data)
    new_gpd=new_gpd.set_crs(input_crs)
    new_gpd.to_file(output_vector)
    ##new_gpd.plot()
    ##plt.show()


# try todownsample the data first
###Specify input and output data

 #location of the raster to be vectorised
input_file_path=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mask\binary_inference_001.tif"
 # name of the vector to be created
output_file_path=r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\vector\vector_inference_001.shp'

raster_vector(input_file_path,output_file_path)