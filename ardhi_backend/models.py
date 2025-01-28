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
    user_id = models.CharField(max_length=255)  # Clerk User ID
    email = models.EmailField(unique=True)  # Ensure uniqueness for subscribers
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Subscription - {self.email}"