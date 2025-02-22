
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
from .views import (
    InputViewSet,
    SubscriptionViewSet,
    APIEndpointViewSet,
    get_s3_signed_url
)
from .chat.views import ChatViewSet, ChatThreadViewSet

router = DefaultRouter()
router.register(r'models-datasets', ModelDatasetViewSet, basename='models-datasets')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

# INFO: base read only views
router.register(r'chat', ChatViewSet, basename='chat')
router.register(r'chat-thread', ChatThreadViewSet, basename='chat-thread')

urlpatterns = [
    path('get-s3-url/', get_s3_signed_url_view, name='get_s3_url'),  
    path('', include(router.urls)),
]
