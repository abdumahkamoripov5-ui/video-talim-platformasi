import os
from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
IS_VERCEL = os.environ.get('VERCEL') == '1'
DEBUG = config('DEBUG', default=not IS_VERCEL, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    # Local apps
    'users',
    'courses',
    'videos',
    'payments',
    'interactions',
    'quizzes',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': config('SQLITE_PATH', default=str(BASE_DIR / 'db.sqlite3')),
        'OPTIONS': {'timeout': 20},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.DeviceJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('REFRESH_TOKEN_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

MAX_DEVICES = config('MAX_DEVICES', default=2, cast=int)
SIGNED_URL_EXPIRY = config('SIGNED_URL_EXPIRY', default=1800, cast=int)

SPECTACULAR_SETTINGS = {
    'TITLE': "Video Ta'lim Platformasi API",
    'DESCRIPTION': "Online ta'lim platformasi uchun REST API",
    'VERSION': '1.0.0',
}

# Email
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@eduplatform.uz')

# Telegram
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')

# Deployment configuration. Keep frontend and API on the same origin for native HLS cookies.
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173').rstrip('/')
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:5173,http://127.0.0.1:5173').split(',')
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
PAYME_MERCHANT_ID = config('PAYME_MERCHANT_ID', default='')
PAYME_SECRET = config('PAYME_SECRET', default='')
CLICK_SERVICE_ID = config('CLICK_SERVICE_ID', default='')
CLICK_MERCHANT_ID = config('CLICK_MERCHANT_ID', default='')
CLICK_SECRET = config('CLICK_SECRET', default='')
UZUM_SERVICE_ID = config('UZUM_SERVICE_ID', default='')
UZUM_LOGIN = config('UZUM_LOGIN', default='')
UZUM_PASSWORD = config('UZUM_PASSWORD', default='')
UZUM_CHECKOUT_URL = config('UZUM_CHECKOUT_URL', default='')
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=DEBUG, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
if not DEBUG:
    if SECRET_KEY == 'django-insecure-change-this-in-production':
        raise ValueError('Production SECRET_KEY is required')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
if config('POSTGRES_DB', default=''):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql', 'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'), 'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='db'), 'PORT': config('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': 60, 'CONN_HEALTH_CHECKS': True,
    }
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle']
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'anon': '120/minute', 'user': '600/minute', 'auth': '10/minute'}
if config('CACHE_REDIS_URL', default=''):
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': config('CACHE_REDIS_URL')}}

MAX_VIDEO_UPLOAD_BYTES = config('MAX_VIDEO_UPLOAD_BYTES', default=5 * 1024**3, cast=int)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
if config('TRUST_PROXY', default=False, cast=bool):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Vercel uses stateless functions; persistent data must live in PostgreSQL.
from config.database import database_from_url

DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES['default'] = database_from_url(DATABASE_URL)

if IS_VERCEL:
    if DEBUG:
        raise ValueError('Vercelda DEBUG=False bo‘lishi kerak')
    if not DATABASE_URL:
        raise ValueError('Vercel uchun PostgreSQL DATABASE_URL majburiy')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Only trust this project’s domains, including its current preview URL.
    for variable in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL'):
        host = os.environ.get(variable, '').strip()
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
        if host and 'https://' + host not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append('https://' + host)
    FILE_UPLOAD_TEMP_DIR = '/tmp'
    MEDIA_ROOT = Path('/tmp/edu-media')
    MIDDLEWARE.insert(1, 'config.middleware.VercelUploadGuard')
    # No Redis connection or synchronous FFmpeg work during HTTP requests.
    CELERY_TASK_ALWAYS_EAGER = False

# A single Django deployment owns public routing; Vercel serves collected assets.
if IS_VERCEL:
    STATICFILES_DIRS = [BASE_DIR / 'frontend' / 'dist']

# Enable only after a private bucket and its server-side credentials are configured.
OBJECT_STORAGE_ENABLED = config('OBJECT_STORAGE_ENABLED', default=False, cast=bool)
AWS_ENDPOINT_URL_S3 = config('AWS_ENDPOINT_URL_S3', default='')
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_REGION = config('AWS_REGION', default='us-east-2')
MEDIA_BUCKET = config('MEDIA_BUCKET', default='edu-media')
DIRECT_VIDEO_MAX_BYTES = config('DIRECT_VIDEO_MAX_BYTES', default=1024**3, cast=int)
DIRECT_ATTACHMENT_MAX_BYTES = config('DIRECT_ATTACHMENT_MAX_BYTES', default=100 * 1024**2, cast=int)
if OBJECT_STORAGE_ENABLED:
    if not all((AWS_ENDPOINT_URL_S3.startswith('https://'), AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, MEDIA_BUCKET)):
        raise ValueError('Object storage endpoint, bucket and credentials are required')
    STORAGES = {
        'default': {'BACKEND': 'videos.object_storage.PrivateObjectStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
