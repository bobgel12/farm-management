"""
Django settings for chicken_management project.
"""

from pathlib import Path
from decouple import config
import os
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'farms',
    'houses',
    'tasks',
    'authentication',
    'health',
    'integrations',  # New integration service
    'rotem_scraper',
    'organizations',  # Multi-tenancy support
    'reporting',  # Advanced reporting
    'analytics',  # Business Intelligence
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chicken_management.urls'

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

WSGI_APPLICATION = 'chicken_management.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='chicken_management'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# For development, use SQLite
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

CORS_ALLOW_CREDENTIALS = True

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

# Email settings - Using Resend
# Resend SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = config('RESEND_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@chickenmanagement.com')

# Email timeout settings
EMAIL_TIMEOUT = 30

# Frontend URL for password reset links and invite emails
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3002')

# Configure logger
logger = logging.getLogger(__name__)

# Email logging for debugging
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    logger.info("Using console email backend for development (no Resend API key)")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    logger.info(f"Using Resend SMTP backend: {EMAIL_HOST}:{EMAIL_PORT}")
    logger.info(f"Resend API Key: {'configured' if EMAIL_HOST_PASSWORD else 'Not set'}")

# Logging configuration
import os
from pathlib import Path

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'detailed': {
            'format': '{levelname} {asctime} {name} {module} {funcName} {lineno} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOGS_DIR / 'django_errors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'debug_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tasks.email_service': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'rotem_scraper': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'integrations': {
            'handlers': ['file', 'console', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'farms': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'houses': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Authentication settings
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Fixed admin credentials
ADMIN_USERNAME = config('ADMIN_USERNAME', default='admin')
ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='admin123')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@chickenmanagement.com')

# Integration Settings
INTEGRATION_SETTINGS = {
    'ROTEM': {
        'ENABLED': True,
        'DEFAULT_SYNC_INTERVAL': 300,  # 5 minutes
        'MAX_RETRY_ATTEMPTS': 3,
        'CONNECTION_TIMEOUT': 30,
    },
    'FUTURE_SYSTEMS': {
        'ENABLED': False,
    }
}

# Rotem Scraper Settings
ROTEM_USERNAME = config('ROTEM_USERNAME', default='')
ROTEM_PASSWORD = config('ROTEM_PASSWORD', default='')

# Celery settings
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    # Legacy Rotem scraper tasks (for existing farms)
    'scrape-rotem-data-every-5-minutes': {
        'task': 'rotem_scraper.tasks.scrape_rotem_data',
        'schedule': 300.0,  # Every 5 minutes (300 seconds)
    },
    'analyze-data-every-hour': {
        'task': 'rotem_scraper.tasks.analyze_data',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    'train-ml-models-daily': {
        'task': 'rotem_scraper.tasks.train_ml_models',
        'schedule': 86400.0,  # Every day (86400 seconds)
    },
    'cleanup-old-predictions-weekly': {
        'task': 'rotem_scraper.tasks.cleanup_old_predictions',
        'schedule': 604800.0,  # Every week (604800 seconds)
    },
    
    # New integration tasks
    'sync-integrated-farms-every-5-minutes': {
        'task': 'integrations.tasks.sync_farm_data',
        'schedule': 300.0,  # Every 5 minutes (300 seconds)
    },
    'test-integration-connections-every-hour': {
        'task': 'integrations.tasks.test_integration_connections',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    'update-integration-health-every-hour': {
        'task': 'integrations.tasks.update_integration_health_metrics',
        'schedule': 3600.0,  # Every hour (3600 seconds)
    },
    'cleanup-integration-logs-daily': {
        'task': 'integrations.tasks.cleanup_old_integration_logs',
        'schedule': 86400.0,  # Every day (86400 seconds)
    },
    
    # Enhanced ML Analysis tasks
    'run-ml-analysis-every-15-minutes': {
        'task': 'integrations.tasks.run_ml_analysis',
        'schedule': 900.0,  # Every 15 minutes (900 seconds)
    },
    'cleanup-old-predictions-daily': {
        'task': 'integrations.tasks.cleanup_old_predictions',
        'schedule': 86400.0,  # Every day (86400 seconds)
    },
    'generate-daily-report': {
        'task': 'integrations.tasks.generate_daily_report',
        'schedule': 86400.0,  # Every day at midnight (86400 seconds)
    },
}

# ML Models Directory
ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')
