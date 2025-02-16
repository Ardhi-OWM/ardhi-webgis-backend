from django.db import models

class Input(models.Model):
    user_id = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50)
    data_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.input_type} - {self.user_id}"

    def __str__(self):
        return f"{self.input_type} - {self.user_id}"

class Subscription(models.Model):
    user_id = models.CharField(max_length=255)  
    email = models.EmailField(unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription - {self.email}"

class APIEndpoint(models.Model):
    user_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    api_url = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user_id}"

class UploadedImage(models.Model):
    image=models.ImageField(upload_to='uploads/')
    uploaded_at=models.DateTimeField(auto_now_add=True)