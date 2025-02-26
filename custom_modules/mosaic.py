import rasterio as rio
import numpy as np
from rasterio.merge import merge
import os




def process_mosaic(input_mask_folder:str,output_mosaic_file:str):
    mask_files=[x for x in os.listdir(input_mask_folder) if x.endswith('.tif')]
    mask_rasters=[]
    for i in range(len(mask_files)):
        src=rio.open(os.path.join(input_mask_folder,mask_files[i]))
        mask_rasters.append(src)

    mosaic, out_transform=merge(mask_rasters,)

    #copy the meta of one src file and use it to define mosaic meta

    meta=mask_rasters[0].meta.copy()
    meta.update({ "height":mosaic.shape[1],"width":mosaic.shape[2],"transform":out_transform})

    with rio.open(output_mosaic_file,"w",**meta)as dst:
        dst.write(mosaic)

    return output_mosaic_file

#example
##input_mask_folder=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mask"
##output_mosaic_file=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mosaic_mask\mosaic_mask.tif"
##
##process_mosaic(input_mask_folder,output_mosaic_file)