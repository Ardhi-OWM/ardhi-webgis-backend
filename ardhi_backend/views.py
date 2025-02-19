from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import urlparse
from rest_framework.exceptions import ValidationError
from .models import Input, Subscription, APIEndpoint
from .serializers import InputSerializer, SubscriptionSerializer, APIEndpointSerializer
from rest_framework.decorators import action


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

        # ✅ Extract Cloud Provider
        cloud_provider = self.get_cloud_provider(data_link)

        # ✅ Extract File Type
        file_type = self.get_file_type(data_link)

        # ✅ Save Entry Without Processing
        serializer.save(
            user_id=user_id,
            input_type=input_type,
            data_link=data_link,
            cloud_provider=cloud_provider,
            file_type=file_type.upper() if file_type else None,
        )

        print(f"✅ Successfully stored {input_type} for user {user_id}")
        return Response(serializer.data, status=201)

    def get_cloud_provider(self, url):
        """Detects the cloud provider from the URL."""
        if "amazonaws.com" in url:
            return "AWS"
        elif "storage.googleapis.com" in url:
            return "Google Cloud"
        elif "digitaloceanspaces.com" in url:
            return "DigitalOcean"
        elif "dropbox.com" in url:
            return "Dropbox"
        else:
            return "Unknown"

    def get_file_type(self, url):
        """Extracts file type from the URL."""
        parsed_url = urlparse(url)
        path = parsed_url.path
        file_extension = path.split(".")[-1].lower()

        print(f"🔹 Extracted File Extension: {file_extension}")
        if file_extension in ["json", "geojson", "csv", "xml", "kml", "gpx", "tif", "tiff"]:
            return file_extension
        else:
            print("❌ Unsupported file extension detected!")
            return None

# -----------------------------------
# ✅ API Endpoint Management
# -----------------------------------
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
