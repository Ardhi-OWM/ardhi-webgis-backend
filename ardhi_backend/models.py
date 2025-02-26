from django.db import models
class Subscription(models.Model):
    user_id = models.CharField(max_length=255)  
    email = models.EmailField(unique=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription - {self.email}"

from django.db import models

class ModelDataset(models.Model):
    user_id = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=[("model", "Model"), ("dataset", "Dataset")])
    provider = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    linkName = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user_id}"

# class UploadedImage(models.Model):
#     image=models.ImageField(upload_to='uploads/')
#     uploaded_at=models.DateTimeField(auto_now_add=True)        

