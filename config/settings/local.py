from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'playto_db',
        'USER': 'postgres',
        'PASSWORD': 'admin123',  
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

STATIC_URL = '/static/'