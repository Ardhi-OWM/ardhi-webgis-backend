
# from django.urls import path
# from .views import (InputListCreateView, InputDetailView, SubscriptionListCreateView, SubscriptionDeleteView, get_s3_signed_url, APIEndpointViewSet)

# urlpatterns = [
#     path('inputs/', InputListCreateView.as_view(), name='input-list-create'),
#     path('inputs/<int:pk>/', InputDetailView.as_view(), name='input-detail'),
#     path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
#     path('subscriptions/<int:pk>/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
#     # path('fetch-data/', fetch_external_data, name='fetch_data'),
#     path('get-s3-url/', get_s3_signed_url, name='get_s3_url'),

    
# ]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    InputViewSet, 
    SubscriptionViewSet, 
    APIEndpointViewSet,
    upload_and_process_image,
    upload_image,
    get_s3_signed_url
)

router = DefaultRouter()
router.register(r'api-endpoints', APIEndpointViewSet, basename='api-endpoint')
router.register(r'inputs', InputViewSet, basename='input')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('get-s3-url/', get_s3_signed_url, name='get_s3_url'),
    path('', include(router.urls)),
    path('upload-image/', upload_and_process_image, name='upload_image'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

