#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('ardhi_user', 'info@ardhi.de', 'ochwuma') if not User.objects.filter(username='ardhi_user').exists() else None" | python3 manage.py shell
gunicorn ardhi_webgis.wsgi:application --bind 0.0.0.0:$PORT


