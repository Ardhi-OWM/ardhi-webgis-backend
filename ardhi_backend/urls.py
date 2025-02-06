
from django.urls import path
from .views import (InputListCreateView, InputDetailView, SubscriptionListCreateView, SubscriptionDeleteView, get_s3_signed_url)

urlpatterns = [
    path('inputs/', InputListCreateView.as_view(), name='input-list-create'),
    path('inputs/<int:pk>/', InputDetailView.as_view(), name='input-detail'),
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('subscriptions/<int:pk>/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
    # path('fetch-data/', fetch_external_data, name='fetch_data'),
    path('get-s3-url/', get_s3_signed_url, name='get_s3_url'),
    
]
