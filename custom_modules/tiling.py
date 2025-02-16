

#-------------------------------------------------------------------------------
# Name:        gridding
# Purpose:      grids raster or vector data into patches
#
# Author:      caleb
# Additional
# source:
# Copyright:   (c) caleb 2024
# Licence:     <ardhi>
#-------------------------------------------------------------------------------
import pandas as pd
import geopandas as gpd

import rasterio as rio
from rasterio.plot import show
import rasterio.mask


from rasterio import windows
from shapely.geometry import box,Polygon

from matplotlib import pyplot as plt


def generate_tiles(image_file, output_folder, area_str, size=256):
    """Generates 256 x 256 polygon tiles. however can be changed """

    def get_window_polygon(src_file, window):
      src = rio.open(src_file)
      bbox = windows.bounds(window, src.transform)
      src.close()
      return box(*bbox)

    raster = rio.open(image_file)
    coord_system=raster.crs
    width, height = raster.shape

    geo_dict = {
        'id' : [],
        'geometry' : []

    }

    index = 0


    for w in range(0, width, size):
        for h in range(0, height, size):
          window = windows.Window(h, w, size, size)
          bbox = get_window_polygon(image_file, window)

          uid = '{}-{}'.format(area_str.lower().replace(' ', '_'), index)#add an attribute
          geo_dict['id'].append(uid)
          geo_dict['geometry'].append(bbox)
          index += 1



    results = gpd.GeoDataFrame(pd.DataFrame(geo_dict))
    results.crs = {'init' :coord_system}
    #results.to_file(output_folder+'/tiles.geojson', driver="GeoJSON") #Geojson does not allow other crs apart from 4326
    results.to_file(output_folder+'/tiles.shp') #save as shapefile
    raster.close()

    return results




def generate_image_patches(tiles,image,image_name,output_folder,size):
    try:
        tiles=gpd.read_file(tiles) #incase one is importing a shp or geojson from local disc
    except:
        tiles=tiles #incase the tiles exist as as a gpd within the code

    for i in range(len(tiles)):

        with rio.open(image) as src:
            out_image, out_transform = rio.mask.mask(src, [tiles.iloc[i]['geometry']], crop=True)
            out_meta=src.meta

            out_meta.update({"driver":"GTiff","height":out_image.shape[1],"width":out_image.shape[2],"transform":out_transform})

            if out_image.shape[1]==size and out_image.shape[2]==size:



                with rio.open(output_folder + "\{}_{}.tif".format(image_name,i),"w",**out_meta) as dest:

                    dest.write(out_image)

####Example
###specify data folder
input_file=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\input\image_001.tif"
output_grid_files=r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\output_grid'
output_tif_folder=r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\output_patches'


###generating image patches
tiles = generate_tiles(input_file, output_grid_files, "grid", size=256)
generate_image_patches(tiles,input_file,"image_tiled",output_folder=output_tif_folder,size=256)












