from rest_framework import serializers
from .models import Input, Subscription, APIEndpoint,UploadedImage

class InputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Input
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class APIEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIEndpoint
        fields = '__all__'    

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model= UploadedImage
        fields=['image']
