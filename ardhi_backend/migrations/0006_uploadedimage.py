# Generated by Django 3.2.25 on 2025-02-16 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ardhi_backend', '0005_rename_apiurl_apiendpoint_api_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='uploads/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
