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




# -----------------------------------
# ✅ Generate Signed URL for Cloud Storage Access
# -----------------------------------
def get_s3_signed_url(bucket_name, file_key):
    """
    Generate a presigned URL for frontend access to a file stored in S3-compatible storage.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return presigned_url
    except Exception as e:
        return str(e)


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
