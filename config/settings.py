"""
Django settings for Community Free-Food Discovery Platform.
"""

from pathlib import Path
import os
import sys
from urllib.parse import urlsplit
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

IS_VERCEL = bool(os.getenv('VERCEL') or os.getenv('VERCEL_ENV'))
PUBLIC_APP_URL = os.getenv(
    'PUBLIC_APP_URL',
    'https://dona-com-kappa.vercel.app' if IS_VERCEL else '',
)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if IS_VERCEL:
        raise ImproperlyConfigured('SECRET_KEY must be set in Vercel environment variables.')
    SECRET_KEY = 'django-insecure-default-change-me-in-production'

DEBUG = os.getenv('DEBUG', 'False' if IS_VERCEL else 'True').lower() in ('true', '1', 't')

def _host_from_value(value):
    """Return a hostname from a host or URL environment value."""
    value = value.strip()
    if not value:
        return None
    parsed = urlsplit(value if '://' in value else f'//{value}')
    return parsed.hostname


def _origin_from_value(value):
    """Return an origin suitable for Django's CSRF trusted-origin setting."""
    value = value.strip().rstrip('/')
    if not value:
        return None
    if '://' not in value:
        value = f'https://{value}'
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return None
    return f'{parsed.scheme}://{parsed.netloc}'


def _env_values(name):
    return [value.strip() for value in os.getenv(name, '').split(',') if value.strip()]


configured_hosts = [
    _host_from_value(value)
    for value in _env_values('ALLOWED_HOSTS')
]
vercel_hosts = [
    _host_from_value(os.getenv(name, ''))
    for name in ('VERCEL_URL', 'VERCEL_BRANCH_URL', 'VERCEL_PROJECT_PRODUCTION_URL')
]
ALLOWED_HOSTS = list(dict.fromkeys(
    host for host in (configured_hosts + vercel_hosts + [_host_from_value(PUBLIC_APP_URL), 'localhost', '127.0.0.1', 'testserver'])
    if host
))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'accounts',
    'food',
    'moderation',
    'locations',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'config.context_processors.platform_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration - TiDB Database Exclusively
# TiDB is MySQL wire-compatible and connects via django.db.backends.mysql with SSL/TLS
import certifi

TIDB_HOST = os.getenv('TIDB_HOST', os.getenv('DATABASE_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'))
TIDB_PORT = int(os.getenv('TIDB_PORT', os.getenv('DATABASE_PORT', 4000)))
TIDB_USER = os.getenv('TIDB_USER', os.getenv('DATABASE_USER', 'root'))
TIDB_PASSWORD = os.getenv('TIDB_PASSWORD', os.getenv('DATABASE_PASSWORD', ''))
TIDB_NAME = os.getenv('TIDB_DATABASE', os.getenv('DATABASE_NAME', 'test'))
TIDB_CA_PATH = os.getenv('TIDB_CA_PATH') or certifi.where()

# SSL is required for TiDB Cloud (remote hosts)
# For local development (localhost / 127.0.0.1), SSL can be toggled via TIDB_ENABLE_SSL
is_remote_tidb = TIDB_HOST not in ('localhost', '127.0.0.1')
enable_ssl = os.getenv('TIDB_ENABLE_SSL', str(is_remote_tidb)).lower() in ('true', '1', 't')

db_options = {
    'charset': 'utf8mb4',
    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
}

if enable_ssl:
    db_options['ssl'] = {
        'ca': TIDB_CA_PATH,
    }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': TIDB_NAME,
        'USER': TIDB_USER,
        'PASSWORD': TIDB_PASSWORD,
        'HOST': TIDB_HOST,
        'PORT': TIDB_PORT,
        'OPTIONS': db_options,
        'CONN_MAX_AGE': int(os.getenv('CONN_MAX_AGE', 300)),
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        }
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media files (User uploads, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Platform & Service Configuration
PLATFORM_NAME = os.getenv('PLATFORM_NAME', 'Dona.Com')
MAP_PROVIDER = os.getenv('MAP_PROVIDER', 'leaflet')
MAP_API_KEY = os.getenv('MAP_API_KEY', '')

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email Configuration (Supports Gmail/SendGrid SMTP or console fallback)

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    DEFAULT_FROM_EMAIL = f'"Dona.Com" <{EMAIL_HOST_USER}>'
else:
    EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    DEFAULT_FROM_EMAIL = '"Dona.Com" <no-reply@dona.com>'




# CSRF & Security settings
configured_origins = [
    _origin_from_value(value)
    for value in _env_values('CSRF_TRUSTED_ORIGINS')
]
vercel_origins = [
    _origin_from_value(os.getenv(name, ''))
    for name in ('VERCEL_URL', 'VERCEL_BRANCH_URL', 'VERCEL_PROJECT_PRODUCTION_URL')
]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(
    origin for origin in (configured_origins + vercel_origins + [_origin_from_value(PUBLIC_APP_URL), 'http://localhost:8000', 'http://127.0.0.1:8000'])
    if origin
))

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
