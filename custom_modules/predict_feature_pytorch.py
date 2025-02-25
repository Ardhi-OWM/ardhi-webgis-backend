import os
import torch
import numpy as np

import rasterio as rio
from rasterio.transform import Affine
from torchvision import transforms
from PIL import Image


import torch.nn as nn


class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DoubleConv, self).__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.double_conv(x)


class DownBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DownBlock, self).__init__()
        self.double_conv = DoubleConv(in_channels, out_channels)
        self.down_sample = nn.MaxPool2d(2)

    def forward(self, x):
        skip_out = self.double_conv(x)
        down_out = self.down_sample(skip_out)
        return (down_out, skip_out)


class UpBlock(nn.Module):
    def __init__(self, in_channels, out_channels, up_sample_mode):
        super(UpBlock, self).__init__()
        if up_sample_mode == 'conv_transpose':
            self.up_sample = nn.ConvTranspose2d(in_channels-out_channels, in_channels-out_channels, kernel_size=2, stride=2)
        elif up_sample_mode == 'bilinear':
            self.up_sample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        else:
            raise ValueError("Unsupported `up_sample_mode` (can take one of `conv_transpose` or `bilinear`)")
        self.double_conv = DoubleConv(in_channels, out_channels)

    def forward(self, down_input, skip_input):
        x = self.up_sample(down_input)
        x = torch.cat([x, skip_input], dim=1)
        return self.double_conv(x)




class UNet(nn.Module):
    def __init__(self, out_classes=2, up_sample_mode='conv_transpose'):
        super(UNet, self).__init__()
        self.up_sample_mode = up_sample_mode
        # Downsampling Path
        self.down_conv1 = DownBlock(3, 64)
        self.down_conv2 = DownBlock(64, 128)
        self.down_conv3 = DownBlock(128, 256)
        self.down_conv4 = DownBlock(256, 512)
        # Bottleneck
        self.double_conv = DoubleConv(512, 1024)
        # Upsampling Path
        self.up_conv4 = UpBlock(512 + 1024, 512, self.up_sample_mode)
        self.up_conv3 = UpBlock(256 + 512, 256, self.up_sample_mode)
        self.up_conv2 = UpBlock(128 + 256, 128, self.up_sample_mode)
        self.up_conv1 = UpBlock(128 + 64, 64, self.up_sample_mode)
        # Final Convolution
        self.conv_last = nn.Conv2d(64, out_classes, kernel_size=1)

    def forward(self, x):
        x, skip1_out = self.down_conv1(x)
        x, skip2_out = self.down_conv2(x)
        x, skip3_out = self.down_conv3(x)
        x, skip4_out = self.down_conv4(x)
        x = self.double_conv(x)
        x = self.up_conv4(x, skip4_out)
        x = self.up_conv3(x, skip3_out)
        x = self.up_conv2(x, skip2_out)
        x = self.up_conv1(x, skip1_out)
        x = self.conv_last(x)
        return x





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


    # Set device: `cuda` or `cpu`
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load the trained PyTorch model

    # Get UNet model
    model = UNet()
    #model.load_state_dict(torch.load(unet_model_file, DEVICE))

    model = torch.load(unet_model_file, DEVICE)
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
#unet_model_file = r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\model_weights\building_segmentation_model.pth"


##unet_model_file = r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\model_weights\best_model.pth"
##input_raster_folder =r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\output_patches'
##
##output_mask_folder = r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mask'
##predict_masks(input_raster_folder, output_mask_folder, unet_model_file)