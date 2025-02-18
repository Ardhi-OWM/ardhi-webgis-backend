# Generated by Django 5.1.5 on 2025-02-18 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ardhi_backend', '0005_rename_apiurl_apiendpoint_api_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='input',
            name='cloud_provider',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='input',
            name='file_type',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='input',
            name='processed_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='input',
            name='signed_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='input',
            name='input_type',
            field=models.CharField(choices=[('API', 'API'), ('Model', 'Model'), ('Dataset', 'Dataset')], max_length=50),
        ),
    ]
