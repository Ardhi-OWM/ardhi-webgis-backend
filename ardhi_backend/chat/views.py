import os
from dataclasses import dataclass

import requests
from dotenv import load_dotenv
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

load_dotenv()

# INFO: THIS CUSTOM HANDLE WILL HELP WHEN WE WILL BE HANDLING MULTIPLE MODLES (Gemini, Deepseek ..)
class ModelError(Exception):
    def __init__(self, message="An error communicating with the model", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


@dataclass
class Prompt:
    thread_id: str
    user_id: str
    message: str
    tokens: int # user token count


class ChatViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

    def __init__(self):
        self.MODEL_API_KEY = ""
        self.BASE_URL = "https://api.deepseek.com" # basic deep seek URL -> will and should be dynamic


    # INFO: THIS HANDLES SENDING PROMPTS TO AI MODELS
    async def handle_send_message(self, payload: Prompt):
        try:
            response = await requests.get()
        except Exception as error:
            return ModelError(error.message)
        finally:


    @action(detail=True, methods=['post'])
    def new_chat(self, request):

        body: Prompt = request.data

        if !body.thread_id:


        return

    @action(detail=True, methods=['post'])
    def chat_response(self, request):
        body: Prompt = request.data

        # this would automatically create a new chat thread if the thread ID is not present
        if !body.thread_id:
            return self.new_chat(request)

        return
