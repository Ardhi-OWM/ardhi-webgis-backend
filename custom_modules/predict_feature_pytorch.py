#-------------------------------------------------------------------------------
# Name:        predict_feature_pytorch
# Purpose:
#
# Author:      caleb/translated to pytorch by deepseek
#
# Created:     19/01/2025
# Copyright:   (c) caleb 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import torch
import numpy as np
import rasterio as rio
from rasterio.transform import Affine
from torchvision import transforms
from PIL import Image

def predict_masks(input_raster_folder, output_mask_folder, unet_model_file, feature_type='bounds'):
    # To hold data crucial for georeferencing and writing the patches to file
    coord_sys_list = []
    pixel_size_xy_list = []
    upper_coords_xy_list = []

    # To hold the raster arrays
    raster_array_list = []

    input_raster_path_list = [image_file for image_file in os.listdir(input_raster_folder) if image_file.endswith('.tif')]

    for i in range(len(input_raster_path_list)):
        input_raster_path = os.path.join(input_raster_folder, input_raster_path_list[i])
        print(input_raster_path)
        image = rio.open(input_raster_path)
        red_array = image.read(1)
        blue_array = image.read(2)
        green_array = image.read(3)

        rgb_array = np.dstack((red_array, blue_array, green_array))
        coord_system = image.crs
        upper_left_coord = [image.bounds.left, image.bounds.top]
        pixel_res = [image.res[0], image.res[1]]

        coord_sys_list.append(coord_system)
        pixel_size_xy_list.append(pixel_res)
        upper_coords_xy_list.append(upper_left_coord)
        raster_array_list.append(rgb_array)

    # Convert the raster list into one general array
    raster_array = np.array(raster_array_list)

    # Load the trained PyTorch model
    model = torch.load(unet_model_file)
    model.eval()

    # Convert numpy array to PyTorch tensor
    raster_tensor = torch.from_numpy(raster_array).float()
    raster_tensor = raster_tensor.permute(0, 3, 1, 2)  # Change from NHWC to NCHW format

    # Use the trained model to predict masks
    with torch.no_grad():
        y_pred = model(raster_tensor)
        y_pred_argmax = torch.argmax(y_pred, dim=1).numpy()  # Get mask values

    print(len(y_pred))

    # Write predicted masks to a folder
    for k in range(len(y_pred)):
        # Create an affine transform file
        transform_file = Affine(pixel_size_xy_list[k][0], 0, upper_coords_xy_list[k][0], 0, -pixel_size_xy_list[k][1], upper_coords_xy_list[k][1])

        with rio.open(os.path.join(output_mask_folder, '{}_{}_mask.tif'.format(input_raster_path_list[k].rstrip('.tif'), feature_type)), 'w', driver='GTIFF', height=raster_array_list[k].shape[0], width=raster_array_list[k].shape[1], count=1, dtype=raster_array_list[k].dtype, crs=coord_sys_list[k], transform=transform_file) as dst:
            predicted_masks = y_pred_argmax[k].astype('uint8')
            dst.write(predicted_masks, 1)  # Reshape into a 2D file. It will be the 1st band.

# Example usage
# unet_model_file = r''
# input_raster_folder = r''
# output_mask_folder = r''
# predict_masks(input_raster_folder, output_mask_folder, unet_model_file)