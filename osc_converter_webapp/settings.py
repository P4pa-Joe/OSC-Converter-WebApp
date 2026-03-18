"""
Django settings for osc_converter_webapp project.
"""
import os
from pathlib import Path

# Developer Info
DEVELOPER_NAME = 'PAVAGEAU Sébastien'
DEVELOPER_EMAIL = 'seb.pav@wanadoo.fr'
DEVELOPER_GITHUB = 'https://github.com/P4pa-Joe/OSC-Converter-WebApp'

# App Version
APP_VERSION = '26.318'

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-osc-converter-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'osc_converter_webapp.main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'osc_converter_webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'osc_converter_webapp' / 'main' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'osc_converter_webapp.main.context_processors.app_version',
            ],
        },
    },
]

WSGI_APPLICATION = 'osc_converter_webapp.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'osc_converter_webapp' / 'main' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OSC Config
OSC_LOG_FILE = os.path.join(BASE_DIR, 'osc-converter.log')
