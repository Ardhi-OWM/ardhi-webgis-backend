# from django.urls import path
# from .views import InputListCreateView, InputDetailView

# urlpatterns = [
#     path('inputs/', InputListCreateView.as_view(), name='input-list-create'),
#     path('inputs/<int:pk>/', InputDetailView.as_view(), name='input-detail'),
# ]


from django.urls import path
from .views import (InputListCreateView, InputDetailView, SubscriptionListCreateView, SubscriptionDeleteView, fetch_external_data)

urlpatterns = [
    path('inputs/', InputListCreateView.as_view(), name='input-list-create'),
    path('inputs/<int:pk>/', InputDetailView.as_view(), name='input-detail'),
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('subscriptions/<int:pk>/', SubscriptionDeleteView.as_view(), name='subscription-delete'),
    path('fetch-data/', fetch_external_data, name='fetch_data'),
]
