from django.db import models

'''
Ardhi chat neeeded models.
    - chat hitory
'''
class Chat(models.Model):
    user_id = models.CharField(max_length=255)
    chat_id = models.CharField(max_length=255)
    # this will be the source of the model we are using for the chat.
    origin = models.CharField(max_length=255) # in a case where we will allowing users to use multiple models for the same chat.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chat_id} - {self.user_id}"

class ChatThread(models.Model):
    user_id = models.CharField(max_length=255)
    chat_id = models.CharField(max_length=255)
    message = models.TextField()
    owner = models.CharField(max_length=255) # this will be the user who created the thread. (model/user)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message} - {self.user_id}"
