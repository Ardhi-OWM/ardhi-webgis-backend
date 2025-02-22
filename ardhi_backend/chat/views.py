from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import urlparse
from rest_framework.exceptions import ValidationError
from .models import Chat, ChatThread
from .serializers import ChatSerializer, ChatThreadSerializer


class ChatViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

class ChatThreadViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChatThreadSerializer
    queryset = ChatThread.objects.all()
