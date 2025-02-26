from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionViewSet, 
    ModelDatasetViewSet,
    # upload_image,
    get_s3_signed_url_view 
)

router = DefaultRouter()
router.register(r'models-datasets', ModelDatasetViewSet, basename='models-datasets')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('get-s3-url/', get_s3_signed_url_view, name='get_s3_url'),  
    path('', include(router.urls)),
]
