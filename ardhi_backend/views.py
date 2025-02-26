from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import urlparse
from rest_framework.exceptions import ValidationError
from .models import Input, Subscription, ModelDataset
from .serializers import InputSerializer, SubscriptionSerializer, ModelDatasetSerializer
from rest_framework.decorators import action, api_view
import logging

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from django.core.files.storage import default_storage
from .serializers import ImageUploadSerializer
from custom_modules.mosaic import process_mosaic
from custom_modules.predict_feature_pytorch import process_prediction
from custom_modules.tiling import process_tiling
from custom_modules.vectorize import process_vectorization



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




# -----------------------------------
# ✅ Generate Signed URL for Cloud Storage Access
# -----------------------------------

logger = logging.getLogger(__name__)

def get_s3_signed_url(bucket_name, file_key):
    """
    Generate a presigned URL for frontend access to a file stored in S3-compatible storage.
    """
    if not bucket_name or not file_key:
        logger.error("Missing required parameters: bucket_name or file_key")
        return None  

    try:
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
        )

        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600  
        )

        return presigned_url

    except Exception as e:
        logger.error(f"Error generating S3 presigned URL: {str(e)}", exc_info=True)
        return None


def get_s3_signed_url_view(request):
    """
    Django view to handle requests for S3 presigned URLs.
    """
    file_key = request.GET.get("file_key")  
    bucket_name = settings.S3_BUCKET_NAME 

    if not file_key:
        return JsonResponse({"error": "Missing file_key parameter"}, status=400)

    presigned_url = get_s3_signed_url(bucket_name, file_key)

    if not presigned_url:
        return JsonResponse({"error": "Failed to generate S3 presigned URL"}, status=500)

    return JsonResponse({"success": True, "url": presigned_url}, status=200)


# -----------------------------------
# ✅ Handle Input Data Storage
# -----------------------------------
class InputViewSet(viewsets.ModelViewSet):
    serializer_class = InputSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Retrieve inputs for a specific user."""
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Input.objects.filter(user_id=user_id)
        return Input.objects.all()

    def perform_create(self, serializer):
        """Stores the uploaded model URL without processing."""
        user_id = self.request.data.get("user_id")
        input_type = self.request.data.get("input_type")
        data_link = self.request.data.get("data_link")

        if not user_id or not data_link:
            return Response({"error": "user_id and data_link are required"}, status=400)

        if Input.objects.filter(user_id=user_id, input_type=input_type, data_link=data_link).exists():
            raise ValidationError({"detail": "This model/API/dataset already exists for this user."})

        # ✅ Save Entry Without Processing
        serializer.save(user_id=user_id, input_type=input_type, data_link=data_link)

        print(f"✅ Successfully stored {input_type} for user {user_id}")
        return Response(serializer.data, status=201)


# -----------------------------------
# ✅ Model and Dataset Management
# -----------------------------------
class ModelDatasetViewSet(viewsets.ModelViewSet):
    serializer_class = ModelDatasetSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return ModelDataset.objects.filter(user_id=user_id)
        return ModelDataset.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        link = self.request.data.get("link")
        dataset_type = self.request.data.get("type")

        if not user_id:
            raise ValidationError({"error": "user_id is required"})

        if not dataset_type or dataset_type not in ["model", "dataset"]:
            raise ValidationError({"error": "type must be either 'model' or 'dataset'"})

        if ModelDataset.objects.filter(link=link, user_id=user_id).exists():
            raise ValidationError({"detail": f"This {dataset_type} link already exists for this user."})

        serializer.save(user_id=user_id)

    @api_view(['GET'])
    def check_duplicate(request):
        link = request.GET.get('link', None)
        if link and ModelDataset.objects.filter(link=link).exists():
            return Response({"exists": True})
        return Response({"exists": False})
    
    @action(detail=False, methods=['delete'])
    def delete_by_id(self, request):
        model_id = request.data.get("id")
        if not model_id:
            return Response({"error": "ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = ModelDataset.objects.get(id=model_id)
            instance.delete()
            return Response({"message": "Model/Dataset deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ModelDataset.DoesNotExist:
            return Response({"error": "Model/Dataset not found"}, status=status.HTTP_404_NOT_FOUND)


# -----------------------------------
# ✅ Subscription Management
# -----------------------------------
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

# -----------------------------------
# ✅ Home API Endpoint
# -----------------------------------
def home(request):
    return JsonResponse({"message": "Welcome to Ardhi WebGIS API"})
