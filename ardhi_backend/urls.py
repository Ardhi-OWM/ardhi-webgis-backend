from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InputViewSet, 
    SubscriptionViewSet, 
    ModelDatasetViewSet,
    get_s3_signed_url
)

router = DefaultRouter()
router.register(r'models-datasets', ModelDatasetViewSet, basename='models-datasets')
router.register(r'inputs', InputViewSet, basename='input')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('get-s3-url/', get_s3_signed_url, name='get_s3_url'),
    path('', include(router.urls)),
]

