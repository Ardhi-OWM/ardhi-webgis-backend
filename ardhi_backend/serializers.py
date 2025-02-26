from rest_framework import serializers
from .models import Input, Subscription, ModelDataset, UploadedImage

class InputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Input
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class ModelDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelDataset
        fields = '__all__'    

class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model= UploadedImage
        fields=['image']            