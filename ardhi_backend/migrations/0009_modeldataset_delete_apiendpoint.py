# Generated by Django 5.1.5 on 2025-02-21 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ardhi_backend', '0008_remove_input_cloud_provider_remove_input_file_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelDataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('model', 'Model'), ('dataset', 'Dataset')], max_length=10)),
                ('provider', models.CharField(blank=True, max_length=255, null=True)),
                ('region', models.CharField(blank=True, max_length=100, null=True)),
                ('link', models.URLField(unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='APIEndpoint',
        ),
    ]
