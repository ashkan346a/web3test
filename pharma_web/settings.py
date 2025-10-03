import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', os.getenv('SECRET_KEY', 'django-insecure-pharma-web-demo-secret'))

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'medpharmaweb.shop',
    'www.medpharmaweb.shop',
    'www.medpharmaweb.com',
    'medpharmaweb.com',
    'apppweb.railway.internal',  # Keep for Railway internal
    'pharmaweb.up.railway.app',  # Railway public domain for testing
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
    'testserver',  # For Django test client
]

CSRF_TRUSTED_ORIGINS = [
    'https://medpharmaweb.shop',
    'https://www.medpharmaweb.shop',
    'https://www.medpharmaweb.com',
    'https://medpharmaweb.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    # Remove old Railway domain completely
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'channels',
    'crispy_forms',
    'crispy_bootstrap4',
    'core',
    'chat',
]

MIDDLEWARE = [
    'core.middleware.HealthCheckMiddleware',  # Must be first to prevent redirects
    'core.canonical_middleware.CanonicalDomainMiddleware',  # Force canonical domain
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware_performance.PerformanceMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SEOMiddleware',
    'core.middleware_performance.SEOMiddleware',
]

ROOT_URLCONF = 'pharma_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.crypto_conversions',  # اضافه شده برای نرخ کریپتو
            ],
        },
    },
]

# Add custom context processors
TEMPLATES[0]['OPTIONS'].setdefault('context_processors', [])
if 'core.context_processors.user_has_address' not in TEMPLATES[0]['OPTIONS']['context_processors']:
    TEMPLATES[0]['OPTIONS']['context_processors'].append('core.context_processors.user_has_address')
if 'core.context_processors.seo_settings' not in TEMPLATES[0]['OPTIONS']['context_processors']:
    TEMPLATES[0]['OPTIONS']['context_processors'].append('core.context_processors.seo_settings')
if 'core.context_processors.site_settings' not in TEMPLATES[0]['OPTIONS']['context_processors']:
    TEMPLATES[0]['OPTIONS']['context_processors'].append('core.context_processors.site_settings')

WSGI_APPLICATION = 'pharma_web.wsgi.application'
ASGI_APPLICATION = 'pharma_web.asgi.application'

# Database configuration - PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:ZLmubdSYxLusObtoTBrCrHCwrJJdXEQQ@postgres.railway.internal:5432/railway')



DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# بهینه‌سازی Database Connection Pool - فقط برای PostgreSQL production
if 'postgresql' in DATABASES['default']['ENGINE'] and not DEBUG:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].update({
        'connect_timeout': 10,
        'application_name': 'pharma_web',
    })

# SSL settings for production
if not DEBUG:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 86400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Additional security settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # امنیت پیشرفته
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    SESSION_COOKIE_HTTPONLY = True  # جلوگیری از دسترسی JavaScript به cookie
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',  # تمام فایل‌های static در یک مکان
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # برای collectstatic

# تنظیمات فایل‌های static برای جلوگیری از warnings
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # نیاز برای Django admin
]

# WhiteNoise settings for serving static files in production
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG  # فقط در development
WHITENOISE_STATIC_PREFIX = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# بهینه‌سازی WhiteNoise
WHITENOISE_MAX_AGE = 31536000  # 1 سال cache برای static files
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.CustomUser'

CRISPY_TEMPLATE_PACK = 'bootstrap4'
# allow bootstrap4 pack explicitly
CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap", "bootstrap4", "uni_form")

# 🔑 کیف‌پول‌های پیش‌فرض برای پرداخت
BITCOIN_MAIN_WALLET = os.getenv('BITCOIN_MAIN_WALLET', 'bc1qwc2lqwjxwc29tnxn6p2kstsrqcc0ems5957r5m')
ETHEREUM_MAIN_WALLET = os.getenv('ETHEREUM_MAIN_WALLET', '0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D')
TRON_MAIN_WALLET = os.getenv('TRON_MAIN_WALLET', 'TW88rRvvvoo3dRpippmQJUNmowdmgaCjhE')

WALLETS = {
    'BTC': BITCOIN_MAIN_WALLET,
    'ETH': ETHEREUM_MAIN_WALLET,
    'TRX': TRON_MAIN_WALLET,
    'USDT': TRON_MAIN_WALLET,  # USDT-TRC20 روی TRON
    'BNB': os.getenv('BNB_WALLET', '0xaF99374Dd015dA244cdA1F1Fc2183b423a17A10D'),
    'TON': os.getenv('TON_WALLET', 'UQATaVtLxM93Sms6jNJwrMjQ_UOKTOvR2niXyS6ONIkx2HNc'),
    'SOL': os.getenv('SOL_WALLET', '9nt397D5ruuTaJVf1WcY6HoQtcthSHEHXek6UFxZUzhQ'),
    'DOGE': os.getenv('DOGE_WALLET', 'DPbSdTVxAh2KpzDScG1qtJGwkfGAkBSG1A'),
}

# 🔑 API keys برای چک کردن تراکنش‌ها و گرفتن نرخ‌ها
BLOCKCYPHER_API_TOKEN = os.getenv('BLOCKCYPHER_API_TOKEN', '0aee4ba7149a4234bc725938176fd58c')
BSCSCAN_API_KEYS = [
    os.getenv('BSCSCAN_API_KEY_1', 'CICNT83I67CTP8A9FWD5J77JH6KPWHRYKW'),
    os.getenv('BSCSCAN_API_KEY_2', 'IAEFHYJC5C2QHJJQQESWMC4WXBDVGNM45N'),
    os.getenv('BSCSCAN_API_KEY_3', 'MN9GH6RFUV96UVTR3B7NWAIDI6TWZ6A516'),
]

TRONGRID_API_KEYS = [
    os.getenv('TRONGRID_API_KEY_1', '231f7199-08ba-43b6-90b4-ee7024f125b4'),
    os.getenv('TRONGRID_API_KEY_2', 'd5b5c7da-8c29-4462-bb08-7d9b1fc2201f'),
    os.getenv('TRONGRID_API_KEY_3', 'c39cf3ad-28a8-4622-8080-b84f438728db'),
]

INFURA_API_KEY = os.getenv('INFURA_API_KEY', '77c2f23f6e6343829fa6647fe49605bc')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', 'CG-L36bK4soP7T2Lb7bH782g5fe')

# 🔑 API keys برای چک کردن تراکنش‌ها و گرفتن نرخ‌ها
BLOCKCYPHER_API_TOKEN = '0aee4ba7149a4234bc725938176fd58c'
BSCSCAN_API_KEYS = [
    'CICNT83I67CTP8A9FWD5J77JH6KPWHRYKW',
    'IAEFHYJC5C2QHJJQQESWMC4WXBDVGNM45N',
    'MN9GH6RFUV96UVTR3B7NWAIDI6TWZ6A516',
]

TRONGRID_API_KEYS = [
    "231f7199-08ba-43b6-90b4-ee7024f125b4",
    "d5b5c7da-8c29-4462-bb08-7d9b1fc2201f",
    "c39cf3ad-28a8-4622-8080-b84f438728db",
]

INFURA_API_KEY = '77c2f23f6e6343829fa6647fe49605bc'

COINGECKO_API_KEY = "CG-L36bK4soP7T2Lb7bH782g5fe"

# واحد پیش‌فرض برای قیمت‌ها
DEFAULT_CURRENCY = 'usd'

# Channels channel layer configuration
# ... بقیه تنظیمات همونطور بمونه

# Channels channel layer configuration
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }

    # Redis cache با بهینه‌سازی‌های پیشرفته
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                    "socket_connect_timeout": 5,
                    "socket_timeout": 5,
                },
                "SERIALIZER": "django_redis.serializers.pickle.PickleSerializer",  # 👈 این مهمه
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "pharma_web",
            "TIMEOUT": 300,
        }
    }


    # استفاده از Redis برای session storage با بهینه‌سازی
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
    SESSION_COOKIE_AGE = 86400  # 24 ساعت
    SESSION_SAVE_EVERY_REQUEST = False  # فقط در صورت تغییر save کن
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False

else:
    # Fallback به in-memory اگر REDIS_URL ست نشده بود
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }

# بهینه‌سازی Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'django.log',
            'maxBytes': 1024*1024*15,  # 15 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'pharma_web': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# SEO Settings
SITE_NAME = os.getenv('SITE_NAME', "PharmaWeb")
SITE_DESCRIPTION = os.getenv('SITE_DESCRIPTION', "فروشگاه آنلاین دارو و تجهیزات پزشکی")
SITE_KEYWORDS = os.getenv('SITE_KEYWORDS', "دارو, تجهیزات پزشکی, فروشگاه آنلاین, بهداشت, سلامت")
# Primary site URL and canonical domain
# .com is the new primary domain; .shop remains active and allowed
SITE_URL = os.getenv('SITE_URL', "https://medpharmaweb.com")
CANONICAL_DOMAIN = os.getenv('CANONICAL_DOMAIN', "medpharmaweb.com")  # Used only to redirect Railway -> canonical

# Google Analytics & Search Console
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
GOOGLE_SITE_VERIFICATION = os.getenv('GOOGLE_SITE_VERIFICATION', '')
BING_SITE_VERIFICATION = os.getenv('BING_SITE_VERIFICATION', '')

# Security Settings for Production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True