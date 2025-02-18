from django.db import models

class Input(models.Model):
    user_id = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, choices=[("API", "API"), ("Model", "Model"), ("Dataset", "Dataset")])
    data_link = models.URLField()
    cloud_provider = models.CharField(max_length=100, null=True, blank=True)  # AWS, GCP, etc.
    file_type = models.CharField(max_length=20, null=True, blank=True)  # GEOJSON, KML, CSV, etc.
    processed_data = models.JSONField(null=True, blank=True)  # Store processed JSON data
    signed_url = models.URLField(null=True, blank=True)  # Secure access URL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.input_type} - {self.user_id}"

    def get_processed_data(self):
        return json.loads(self.processed_data) if self.processed_data else None
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

