from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
import requests
import boto3
from rest_framework.exceptions import ValidationError
from .models import Input, Subscription, APIEndpoint
from .serializers import InputSerializer, SubscriptionSerializer, APIEndpointSerializer
from rest_framework.decorators import action
from rest_framework import status

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from django.core.files.storage import default_storage
from .serializers import ImageUploadSerializer



from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile

from custom_modules.mosaic import process_mosaic
from custom_modules.predict_feature_pytorch import predict_masks
from custom_modules.tiling import generate_tiles,generate_image_patches
from custom_modules.vectorize import raster_vector

import os
import json






@csrf_exempt
def upload_and_process_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Save the uploaded image
        uploaded_file = request.FILES['image']
        file_name = default_storage.save(uploaded_file.name, ContentFile(uploaded_file.read()))
        file_path = default_storage.path(file_name)

        # Process the image using the custom module
        try:
            # Step 1: Tile the image
            
            ### Generating image patches
            tiles = generate_tiles(file_path, settings.INPUT_RASTER_FOLDER, "grid", size=256)
            generate_image_patches(tiles, file_path, "image_tiled", output_folder=settings.INPUT_RASTER_FOLDER, size=256)

            # Step 2: Predict features using PyTorch
            predict_masks(settings.INPUT_RASTER_FOLDER, settings.OUTPUT_MASK_FOLDER, settings.UNET_MODEL_FILE)

            # Step 3: Create a mosaic
            process_mosaic(settings.OUTPUT_MASK_FOLDER, settings.OUTPUT_MOSAIC_FILE)

            # Step 4: Vectorize the mosaic to GeoJSON
            raster_vector(settings.OUTPUT_MOSAIC_FILE, settings.OUTPUT_VECTOR_FILE)

            # Read the generated GeoJSON file
            with open(settings.OUTPUT_VECTOR_FILE, 'r') as f:
                geojson_data = json.load(f)

            # Save the GeoJSON to a file (optional)
            geojson_file_path = file_path.replace('.tif', '.geojson')
            with open(geojson_file_path, 'w') as f:
                json.dump(geojson_data, f)

            # Return the GeoJSON as a response
            return JsonResponse({'status': 'success', 'geojson': geojson_data})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'No image uploaded'})

"""
@csrf_exempt
def upload_and_process_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Save the uploaded image
        uploaded_file = request.FILES['image']
        file_name = default_storage.save(uploaded_file.name, ContentFile(uploaded_file.read()))
        file_path = default_storage.path(file_name)

        # Process the image using the custom module
        try:
            # Step 1: Tile the image
            tiled_images = process_tile(file_path)
            ###generating image patches
            tiles = generate_tiles(input_file, output_grid_files, "grid", size=256)
            generate_image_patches(tiles,input_file,"image_tiled",output_folder=output_tif_folder,size=256)


            # Step 2: Predict features using PyTorch
            #predicted_features = predict_features(tiled_images)

            unet_model_file = r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\model_weights\best_model.pth"
            input_raster_folder =r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\output_patches'
            ##
            output_mask_folder = r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mask'
            predict_masks(input_raster_folder, output_mask_folder, unet_model_file)

            # Step 3: Create a mosaic
            #mosaic_image = create_mosaic(predicted_features)

            #example
            input_mask_folder=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mask"
            output_mosaic_file=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mosaic_mask\mosaic_mask.tif"
            ##
            process_mosaic(input_mask_folder,output_mosaic_file)

            # Step 4: Vectorize the mosaic to GeoJSON
            #geojson_data = vectorize_to_geojson(mosaic_image)

            ## #location of the raster to be vectorised
            input_file_path=r"C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\mosaic_mask\mosaic_mask.tif"
            ## # name of the vector to be created
            geojson_data=r'C:\Users\caleb\OneDrive\Desktop\private\projects\ardhi\example_backend\data\output\inferenced\vector\vector_inference.geojson'
            
            raster_vector(input_file_path,geojson_data)

            # Save the GeoJSON to a file (optional)
            geojson_file_path = file_path.replace('.tif', '.geojson')
            with open(geojson_file_path, 'w') as f:
                json.dump(geojson_data, f)

            # Return the GeoJSON as a response
            return JsonResponse({'status': 'success', 'geojson': geojson_data})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'No image uploaded'})
"""







@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    serializer = ImageUploadSerializer(data=request.data)
    if serializer.is_valid():
        uploaded_image = serializer.save()
        image_path = uploaded_image.image.path

        # Step 1: Process with your custom modules
        processed_image = process_mosaic(image_path)
        prediction_result = process_prediction(processed_image)
        tiled_data = process_tiling(prediction_result)
        geojson_result = process_vectorization(tiled_data)

        return Response({"geojson": geojson_result})
    return Response(serializer.errors, status=400)


def get_s3_signed_url(request):
    """
    Generate a presigned URL for frontend access to a file stored in S3.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    file_key = request.GET.get("file", "default-model.geojson")

    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": file_key},
            ExpiresIn=3600  # Link expires in 1 hour
        )

        return JsonResponse({"success": True, "url": presigned_url}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


class InputViewSet(viewsets.ModelViewSet):
    serializer_class = InputSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Input.objects.filter(user_id=user_id)
        return Input.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        serializer.save(user_id=user_id)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Subscription.objects.filter(user_id=user_id)
        return Subscription.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        email = self.request.data.get("email")

        if not user_id:
            raise ValidationError({"error": "user_id is required"})

        if Subscription.objects.filter(email=email).exists():
            raise ValidationError({"error": "This email is already subscribed."})

        serializer.save(user_id=user_id)

class APIEndpointViewSet(viewsets.ModelViewSet):
    serializer_class = APIEndpointSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return APIEndpoint.objects.filter(user_id=user_id)
        return APIEndpoint.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        api_url = self.request.data.get("api_url")

        if not user_id:
            raise ValidationError({"error": "user_id is required"})

        # Check for duplicate API URL per user
        if APIEndpoint.objects.filter(api_url=api_url, user_id=user_id).exists():
            raise ValidationError({"detail": "This API URL already exists for this user."})

        serializer.save(user_id=user_id)


    @action(detail=False, methods=['delete'])
    def delete_by_api_url(self, request):
        api_url = request.data.get("api_url")
        if not api_url:
            return Response({"error": "api_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = APIEndpoint.objects.get(api_url=api_url)
            instance.delete()
            return Response({"message": "API Endpoint deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except APIEndpoint.DoesNotExist:
            return Response({"error": "API Endpoint not found"}, status=status.HTTP_404_NOT_FOUND)

def home(request):
    return JsonResponse({"message": "Welcome to Ardhi WebGIS API"})
