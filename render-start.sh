#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn ardhi_backend.wsgi:application --bind 0.0.0.0:$PORT
