from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
import requests
import boto3
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
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        email = serializer.validated_data["email"]
        if Subscription.objects.filter(email=email).exists():
            return Response({"error": "Email already subscribed"}, status=400)

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
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        serializer.save(user_id=user_id)


def home(request):
    return JsonResponse({"message": "Welcome to Ardhi WebGIS API"})
