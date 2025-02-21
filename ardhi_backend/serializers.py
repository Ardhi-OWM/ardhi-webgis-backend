from rest_framework import serializers
from .models import Input, Subscription, ModelDataset

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