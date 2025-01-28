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
