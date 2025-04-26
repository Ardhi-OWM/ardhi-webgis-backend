import os
import asyncio
from dataclasses import dataclass
import requests
from dotenv import load_dotenv
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404


# Import your models
from .models import Chat, ChatThread
from .serializers import ChatSerializer, ChatThreadSerializer, ModelSerializer

load_dotenv()

# Custom exception for model communication errors
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
    tokens: int  # user token count

class ChatViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.MODEL_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        self.BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.MODEL_NAME = os.getenv("LLM_MODEL_NAME", "deepseek-chat")
    
    # Handles sending prompts to AI models
    async def handle_send_message(self, payload: Prompt):
        try:
            headers = {
                "Authorization": f"Bearer {self.MODEL_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.MODEL_NAME,
                "messages": [{"role": "user", "content": payload.message}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = await asyncio.to_thread(
                lambda: requests.post(
                    f"{self.BASE_URL}/v1/chat/completions",
                    headers=headers,
                    json=data
                )
            )
            
            if response.status_code != 200:
                return ModelError(
                    "Failed to get response from LLM API",
                    details=response.text
                )
                
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
            
        except Exception as error:
            error_message = str(error) if hasattr(error, '__str__') else "Unknown error"
            return ModelError(message="Error communicating with LLM", details=error_message)
    
    @action(detail=False, methods=['post'])
    def new_chat(self, request):
        body_data = request.data
        
        try:
            # Validate required fields
            if not body_data.get('user_id'):
                return Response(
                    {"error": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if not body_data.get('message'):
                return Response(
                    {"error": "message is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            prompt = Prompt(
                thread_id=body_data.get('chat_id', ''),  # Using chat_id from your model
                user_id=body_data.get('user_id', ''),
                message=body_data.get('message', ''),
                tokens=body_data.get('tokens', 0)
            )
            
            # Generate a new chat_id if not provided
            chat_id = prompt.thread_id if prompt.thread_id else os.urandom(8).hex()
            
            # Create a new chat record
            chat = Chat.objects.create(
                user_id=prompt.user_id,
                chat_id=chat_id,
                origin=self.MODEL_NAME
            )
            
            # Run the async function to get LLM response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llm_response = loop.run_until_complete(self.handle_send_message(prompt))
            loop.close()
            
            if isinstance(llm_response, ModelError):
                return Response(
                    {"error": str(llm_response)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Save the user message
            user_thread = ChatThread.objects.create(
                user_id=prompt.user_id,
                chat_id=chat_id,
                message=prompt.message,
                owner="user"
            )
            
            # Save the model response
            model_thread = ChatThread.objects.create(
                user_id=prompt.user_id,
                chat_id=chat_id,
                message=llm_response,
                owner="model"
            )
            
            # Return both the user message and model response
            user_serializer = ChatThreadSerializer(user_thread)
            model_serializer = ChatThreadSerializer(model_thread)
            
            return Response({
                "chat_id": chat_id,
                "user_message": user_serializer.data,
                "model_response": model_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def chat_response(self, request):
        body_data = request.data
        
        # Validate required fields
        if not body_data.get('user_id'):
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not body_data.get('message'):
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not body_data.get('chat_id'):
            # If no chat_id is provided, create a new chat
            return self.new_chat(request)
        
        try:
            prompt = Prompt(
                thread_id=body_data.get('chat_id', ''),
                user_id=body_data.get('user_id', ''),
                message=body_data.get('message', ''),
                tokens=body_data.get('tokens', 0)
            )
            
            # Check if the chat exists
            try:
                chat = Chat.objects.get(chat_id=prompt.thread_id)
            except Chat.DoesNotExist:
                return Response(
                    {"error": f"Chat with ID {prompt.thread_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Run the async function to get LLM response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            llm_response = loop.run_until_complete(self.handle_send_message(prompt))
            loop.close()
            
            if isinstance(llm_response, ModelError):
                return Response(
                    {"error": str(llm_response)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Save the user message
            user_thread = ChatThread.objects.create(
                user_id=prompt.user_id,
                chat_id=prompt.thread_id,
                message=prompt.message,
                owner="user"
            )
            
            # Save the model response
            model_thread = ChatThread.objects.create(
                user_id=prompt.user_id,
                chat_id=prompt.thread_id,
                message=llm_response,
                owner="model"
            )
            
            # Return both the user message and model response
            user_serializer = ChatThreadSerializer(user_thread)
            model_serializer = ChatThreadSerializer(model_thread)
            
            return Response({
                "chat_id": prompt.thread_id,
                "user_message": user_serializer.data,
                "model_response": model_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
