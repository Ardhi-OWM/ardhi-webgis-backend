from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse
from django.conf import settings
import requests
import boto3
from rest_framework.exceptions import ValidationError
from .models import Input, Subscription, APIEndpoint
from .serializers import InputSerializer, SubscriptionSerializer, APIEndpointSerializer

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
        input_type = self.request.data.get("input_type")
        data_link = self.request.data.get("data_link")

        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        if Input.objects.filter(user_id=user_id, input_type=input_type, data_link=data_link).exists():
            raise ValidationError({"detail": "This model/API/dataset already exists for this user."})

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
