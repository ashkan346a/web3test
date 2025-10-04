# Local SQLite settings for development
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_local.sqlite3',
    }
}

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
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

ROOT_URLCONF = 'pharma_web.urls'
WSGI_APPLICATION = 'pharma_web.wsgi.application'

# 🔑 Wallet configurations for local development
WALLETS = {
    'BTC': 'bc1qwc2lqwjxwc29tnxn6p2kstsrqcc0ems5957r5m',
    'ETH': '0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D',
    'TRX': 'TW88rRvvvoo3dRpippmQJUNmowdmgaCjhE',
    'USDT': 'TW88rRvvvoo3dRpippmQJUNmowdmgaCjhE',
    'BNB': '0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D',
    'TON': 'UQATaVtLxM93Sms6jNJwrMjQ_UOKTOvR2niXyS6ONIkx2HNc',
    'SOL': '9nt397D5ruuTaJVf1WcY6HoQtcthSHEHXek6UFxZUzhQ',
    'DOGE': 'DPbSdTVxAh2KpzDScG1qtJGwkfGAkBSG1A',
}

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration  
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Additional configurations needed
LANGUAGE_CODE = 'fa'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# Security settings for development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_USER_MODEL = 'core.CustomUser'

USE_TZ = True