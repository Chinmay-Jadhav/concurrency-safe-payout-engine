from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = ['*']  # tighten after deployment

SECRET_KEY = os.environ['SECRET_KEY']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['PGDATABASE'],
        'USER': os.environ['PGUSER'],
        'PASSWORD': os.environ['PGPASSWORD'],
        'HOST': os.environ['PGHOST'],
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}

CELERY_BROKER_URL = os.environ['REDIS_URL']
CELERY_RESULT_BACKEND = os.environ['REDIS_URL']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
CORS_ALLOW_ALL_ORIGINS = True