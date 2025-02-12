from django.contrib import admin
from .models import Input, Subscription, APIEndpoint

admin.site.register(Input)
admin.site.register(Subscription)
admin.site.register(APIEndpoint)

