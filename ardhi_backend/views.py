# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework import generics
# from .models import Input
# from .serializers import InputSerializer

# class InputListCreateView(generics.ListCreateAPIView):
#     queryset = Input.objects.all()
#     serializer_class = InputSerializer
    # permission_classes = [AllowAny] 

# class InputDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Input.objects.all()
#     serializer_class = InputSerializer

from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.response import Response
from .models import Input, Subscription
from .serializers import InputSerializer, SubscriptionSerializer
import requests
from django.http import JsonResponse
from django.conf import settings

import requests
from django.http import JsonResponse
from django.conf import settings
import requests
import boto3
from django.http import JsonResponse
from django.conf import settings

# def fetch_external_data(request):
#     """Fetch data from an external API (AWS S3 or another service)."""
#     url = settings.API_BASE_URL.rstrip("/") + "/endpoint/"
#     headers = {
#         "Authorization": f"Bearer {settings.API_KEY}",  
#         "x-api-key": settings.API_KEY,  
#         "Content-Type": "application/json",
#     }

#     try:
#         response = requests.get(url, headers=headers)
#         response.raise_for_status()  
#         data = response.json()
#         return JsonResponse({"success": True, "data": data}, status=200)

#     except requests.exceptions.HTTPError as e:
#         return JsonResponse({"success": False, "error": f"HTTP Error: {e}"}, status=response.status_code)
#     except requests.exceptions.RequestException as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)


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

    file_key = request.GET.get("file", "default-model.geojson")  # Get file from frontend request

    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": file_key},
            ExpiresIn=3600  # Link expires in 1 hour
        )

        return JsonResponse({"success": True, "url": presigned_url}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)



# def fetch_model_from_do(request):
#     """Fetch a model file from DigitalOcean Spaces"""
#     s3 = boto3.client(
#         "s3",
#         aws_access_key_id=settings.DO_SPACES_KEY,
#         aws_secret_access_key=settings.DO_SPACES_SECRET,
#         region_name=settings.DO_SPACES_REGION,
#         endpoint_url=f"https://{settings.DO_SPACES_REGION}.digitaloceanspaces.com",
#     )

#     file_key = "model/model.pkl"

#     try:
#         response = s3.get_object(Bucket=settings.DO_SPACES_BUCKET, Key=file_key)
#         model_data = response['Body'].read()
#         return JsonResponse({"success": True, "message": "Model retrieved successfully"}, status=200)
#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)


class InputListCreateView(generics.ListCreateAPIView):
    serializer_class = InputSerializer
    permission_classes = [AllowAny]  # Allow requests without authentication

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")  # Get user_id from query params
        if user_id:
            return Input.objects.filter(user_id=user_id)
        return Input.objects.all()  # Return all if no user_id provided

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")  # Get from request body
        if not user_id:  # Ensure user_id is not None
            return Response({"error": "user_id is required"}, status=400)

        serializer.save(user_id=user_id)

class InputDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InputSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Input.objects.filter(user_id=user_id)
        return Input.objects.all()

class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Subscription.objects.filter(user_id=user_id)
        return Subscription.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")  # Get from request body
        if not user_id:
            return Response({"error": "user_id is required"}, status=400)

        email = serializer.validated_data["email"]
        if Subscription.objects.filter(email=email).exists():
            return Response({"error": "Email already subscribed"}, status=400)

        serializer.save(user_id=user_id)

class SubscriptionDeleteView(generics.DestroyAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Subscription.objects.filter(user_id=user_id)
        return Subscription.objects.all()


def home(request):
    return JsonResponse({"message": "Welcome to Ardhi WebGIS API"})
