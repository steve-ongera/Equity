import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-dxqe2c1h@aspljw3hti)j(00x1pp!5(v+_c2ppkn#wytre$h7f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


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
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap4',
    'phonenumber_field',
    'import_export',
    'django_extensions',
    'channels',
    'django.contrib.humanize',

    'banking_system',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

#     'banking_system.middleware.AuditMiddleware',  # Custom audit middleware
#     'banking_system.middleware.SecurityMiddleware',  # Custom security middleware
 ]

ROOT_URLCONF = 'Equity.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Equity.wsgi.application'
#ASGI_APPLICATION = 'Equity.asgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'banking_system.User'



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'banking_system.authentication.BankingTokenAuthentication',  # Custom authentication
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/min',
        'transaction': '50/min',
    }
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com",
]

CORS_ALLOW_CREDENTIALS = True

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session settings
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@equitybank.co.ke')

# SMS settings (using Africa's Talking or similar)
SMS_BACKEND = 'banking.sms.AfricasTalkingSMSBackend'
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')

# # Banking specific settings
# BANKING_SETTINGS = {
#     # Default account settings
#     'DEFAULT_ACCOUNT_TYPE': 'SAV',
#     'MIN_ACCOUNT_BALANCE': 100.00,
#     'DEFAULT_DAILY_WITHDRAWAL_LIMIT': 40000.00,
#     'DEFAULT_MONTHLY_WITHDRAWAL_LIMIT': 1000000.00,
    
#     # ATM settings
#     'ATM_SESSION_TIMEOUT': 120,  # seconds
#     'MAX_PIN_ATTEMPTS': 3,
#     'ATM_RECEIPT_FOOTER': 'Thank you for banking with Equity Bank',
    
#     # Agent settings
#     'AGENT_DAILY_LIMIT': 500000.00,
#     'AGENT_MONTHLY_LIMIT': 10000000.00,
#     'AGENT_COMMISSION_RATE': 0.01,  # 1%
    
#     # Loan settings
#     'MIN_LOAN_AMOUNT': 1000.00,
#     'MAX_LOAN_AMOUNT': 5000000.00,
#     'DEFAULT_LOAN_INTEREST_RATE': 0.15,  # 15% per annum
#     'INSTANT_LOAN_LIMIT': 50000.00,
    
#     # Security settings
#     'REQUIRE_OTP_FOR_TRANSFERS': True,
#     'MAX_DAILY_TRANSACTION_AMOUNT': 1000000.00,
#     'SUSPICIOUS_TRANSACTION_THRESHOLD': 500000.00,
    
#     # Notification settings
#     'SEND_SMS_NOTIFICATIONS': True,
#     'SEND_EMAIL_NOTIFICATIONS': True,
#     'TRANSACTION_ALERT_THRESHOLD': 1000.00,
    
#     # Interest calculation
#     'INTEREST_CALCULATION_METHOD': 'daily_balance',
#     'SAVINGS_INTEREST_RATE': 0.07,  # 7% per annum
#     'CURRENT_ACCOUNT_INTEREST_RATE': 0.03,  # 3% per annum
    
#     # Currency settings
#     'DEFAULT_CURRENCY': 'KES',
#     'SUPPORTED_CURRENCIES': ['KES', 'USD', 'EUR', 'GBP'],
    
#     # API settings
#     'MPESA_CONSUMER_KEY': config('MPESA_CONSUMER_KEY', default=''),
#     'MPESA_CONSUMER_SECRET': config('MPESA_CONSUMER_SECRET', default=''),
#     'MPESA_SHORTCODE': config('MPESA_SHORTCODE', default=''),
#     'MPESA_PASSKEY': config('MPESA_PASSKEY', default=''),
    
#     # External services
#     'CREDIT_BUREAU_API_URL': config('CREDIT_BUREAU_API_URL', default=''),
#     'CREDIT_BUREAU_API_KEY': config('CREDIT_BUREAU_API_KEY', default=''),
#     'KRA_API_URL': config('KRA_API_URL', default=''),
#     'KRA_API_KEY': config('KRA_API_KEY', default=''),
# }

# # Celery Configuration (for background tasks)
# CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_BEAT_SCHEDULE = {
#     'calculate-daily-interest': {
#         'task': 'banking.tasks.calculate_daily_interest',
#         'schedule': 86400.0,  # Run daily
#     },
#     'update-loan-statuses': {
#         'task': 'banking.tasks.update_loan_statuses',
#         'schedule': 3600.0,  # Run hourly
#     },
#     'generate-monthly-statements': {
#         'task': 'banking.tasks.generate_monthly_statements',
#         'schedule': 86400.0,  # Run daily, but check if month-end
#     },
#     'process-standing-orders': {
#         'task': 'banking.tasks.process_standing_orders',
#         'schedule': 3600.0,  # Run hourly
#     },
#     'cleanup-expired-sessions': {
#         'task': 'banking.tasks.cleanup_expired_sessions',
#         'schedule': 1800.0,  # Run every 30 minutes
#     },
# }

# # Cache configuration
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# # Logging configuration
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'filters': {
#         'require_debug_true': {
#             '()': 'django.utils.log.RequireDebugTrue',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'INFO',
#             'filters': ['require_debug_true'],
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple'
#         },
#         'file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'logs' / 'django.log',
#             'formatter': 'verbose',
#         },
#         'transaction_file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'logs' / 'transactions.log',
#             'formatter': 'verbose',
#         },
#         'security_file': {
#             'level': 'WARNING',
#             'class': 'logging.FileHandler',
#             'filename': BASE_DIR / 'logs' / 'security.log',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'file'],
#             'level': 'INFO',
#         },
#         'banking.transactions': {
#             'handlers': ['transaction_file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         'banking.security': {
#             'handlers': ['security_file'],
#             'level': 'WARNING',
#             'propagate': False,
#         },
#         'banking': {
#             'handlers': ['console', 'file'],
#             'level': 'DEBUG' if DEBUG else 'INFO',
#         },
#     },
# }

# # Create logs directory
# LOGS_DIR = BASE_DIR / 'logs'
# LOGS_DIR.mkdir(exist_ok=True)

# # Channels configuration for WebSocket support
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [config('REDIS_URL', default='redis://localhost:6379/2')],
#         },
#     },
# }

# # File upload settings
# FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
# DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
# FILE_UPLOAD_PERMISSIONS = 0o644

# # Crispy Forms
# CRISPY_TEMPLATE_PACK = 'bootstrap4'

# # Phone number field
# PHONENUMBER_DEFAULT_REGION = 'KE'

# # Django Extensions
# GRAPH_MODELS = {
#     'all_applications': True,
#     'group_models': True,
# }

# # Custom settings for banking operations
# TRANSACTION_PROCESSING = {
#     'ENABLE_REAL_TIME_PROCESSING': True,
#     'BATCH_SIZE': 1000,
#     'RETRY_ATTEMPTS': 3,
#     'TIMEOUT_SECONDS': 30,
# }

# # Fraud detection settings
# FRAUD_DETECTION = {
#     'ENABLED': True,
#     'MAX_TRANSACTION_VELOCITY': 5,  # Max transactions per minute
#     'UNUSUAL_AMOUNT_THRESHOLD': 100000.00,
#     'GEOGRAPHIC_VALIDATION': True,
#     'DEVICE_FINGERPRINTING': True,
# }

# # Third-party integrations
# INTEGRATIONS = {
#     'MPESA': {
#         'ENABLED': config('MPESA_ENABLED', default=False, cast=bool),
#         'CONSUMER_KEY': config('MPESA_CONSUMER_KEY', default=''),
#         'CONSUMER_SECRET': config('MPESA_CONSUMER_SECRET', default=''),
#         'SHORTCODE': config('MPESA_SHORTCODE', default=''),
#         'PASSKEY': config('MPESA_PASSKEY', default=''),
#         'ENVIRONMENT': config('MPESA_ENVIRONMENT', default='sandbox'),
#     },
#     'PESALINK': {
#         'ENABLED': config('PESALINK_ENABLED', default=False, cast=bool),
#         'API_URL': config('PESALINK_API_URL', default=''),
#         'API_KEY': config('PESALINK_API_KEY', default=''),
#     },
#     'SWIFT': {
#         'ENABLED': config('SWIFT_ENABLED', default=False, cast=bool),
#         'BIC': config('SWIFT_BIC', default=''),
#         'API_URL': config('SWIFT_API_URL', default=''),
#         'API_KEY': config('SWIFT_API_KEY', default=''),
#     },
#     'KRA': {
#         'ENABLED': config('KRA_ENABLED', default=False, cast=bool),
#         'API_URL': config('KRA_API_URL', default=''),
#         'API_KEY': config('KRA_API_KEY', default=''),
#     },
#     'CREDIT_BUREAU': {
#         'ENABLED': config('CREDIT_BUREAU_ENABLED', default=False, cast=bool),
#         'API_URL': config('CREDIT_BUREAU_API_URL', default=''),
#         'API_KEY': config('CREDIT_BUREAU_API_KEY', default=''),
#     }
# }

# # Monitoring and Analytics
# MONITORING = {
#     'SENTRY_DSN': config('SENTRY_DSN', default=''),
#     'GOOGLE_ANALYTICS_ID': config('GOOGLE_ANALYTICS_ID', default=''),
#     'HOTJAR_ID': config('HOTJAR_ID', default=''),
#     'ENABLE_PERFORMANCE_MONITORING': config('ENABLE_PERFORMANCE_MONITORING', default=False, cast=bool),
# }

# # Import/Export settings
# IMPORT_EXPORT_USE_TRANSACTIONS = True

# # Development settings
# if DEBUG:
#     INSTALLED_APPS += [
#         'debug_toolbar',
#         'django_seed',
#     ]
    
#     MIDDLEWARE = [
#         'debug_toolbar.middleware.DebugToolbarMiddleware',
#     ] + MIDDLEWARE
    
#     DEBUG_TOOLBAR_CONFIG = {
#         'DISABLE_PANELS': [
#             'debug_toolbar.panels.redirects.RedirectsPanel',
#         ],
#         'SHOW_TEMPLATE_CONTEXT': True,
#     }
    
#     INTERNAL_IPS = [
#         '127.0.0.1',
#         'localhost',
#     ]

# # Production settings
# else:
#     # SSL/HTTPS settings
#     SECURE_SSL_REDIRECT = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
#     # Additional security headers
#     SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
#     # Database connection pooling for production
#     DATABASES['default']['CONN_MAX_AGE'] = 600
    
#     # Static files compression
#     STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
#     # Error reporting
#     ADMINS = [
#         ('Bank Admin', config('ADMIN_EMAIL', default='admin@equitybank.co.ke')),
#     ]
    
#     MANAGERS = ADMINS
    
#     # Email error reports
#     EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#     SERVER_EMAIL = config('SERVER_EMAIL', default='server@equitybank.co.ke')



# # Custom validators
# AUTH_PASSWORD_VALIDATORS += [
#     {
#         'NAME': 'banking.validators.BankingPasswordValidator',
#         'OPTIONS': {
#             'min_length': 8,
#             'require_uppercase': True,
#             'require_lowercase': True,
#             'require_numeric': True,
#             'require_special': True,
#             'max_similarity': 0.7,
#         }
#     },
# ]

# # Data retention policies
# DATA_RETENTION = {
#     'TRANSACTION_RECORDS_YEARS': 7,
#     'AUDIT_LOGS_YEARS': 5,
#     'SESSION_LOGS_DAYS': 90,
#     'NOTIFICATION_LOGS_DAYS': 30,
# }

# # Backup settings
# BACKUP_SETTINGS = {
#     'ENABLED': config('BACKUP_ENABLED', default=False, cast=bool),
#     'STORAGE_BACKEND': config('BACKUP_STORAGE', default='local'),
#     'AWS_S3_BUCKET': config('BACKUP_S3_BUCKET', default=''),
#     'SCHEDULE': '0 2 * * *',  # Daily at 2 AM
#     'RETENTION_DAYS': 30,
# }

# # API versioning
# API_VERSION = 'v1'


# # Locale settings
# LOCALE_PATHS = [
#     BASE_DIR / 'locale',
# ]

# LANGUAGES = [
#     ('en', 'English'),
#     ('sw', 'Swahili'),
# ]



# # WebSocket settings for real-time updates
# WEBSOCKET_SETTINGS = {
#     'ENABLED': config('WEBSOCKET_ENABLED', default=True, cast=bool),
#     'HEARTBEAT_INTERVAL': 30,
#     'CONNECTION_TIMEOUT': 300,
# }

# # Mobile app settings
# MOBILE_APP_SETTINGS = {
#     'VERSION_CHECK_ENABLED': True,
#     'MIN_SUPPORTED_VERSION': '2.0.0',
#     'FORCE_UPDATE_VERSION': '1.0.0',
#     'APP_STORE_URL': config('APP_STORE_URL', default=''),
#     'PLAY_STORE_URL': config('PLAY_STORE_URL', default=''),
# }

# # Compliance and regulatory settings
# COMPLIANCE = {
#     'KYC_REQUIRED': True,
#     'AML_SCREENING': True,
#     'CBK_REPORTING': config('CBK_REPORTING_ENABLED', default=False, cast=bool),
#     'FATCA_COMPLIANCE': config('FATCA_ENABLED', default=False, cast=bool),
#     'GDPR_COMPLIANCE': True,
# }

# # Performance settings
# PERFORMANCE = {
#     'ENABLE_QUERY_OPTIMIZATION': True,
#     'DATABASE_QUERY_TIMEOUT': 30,
#     'API_RESPONSE_TIMEOUT': 30,
#     'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
# }

# # Notification templates
# NOTIFICATION_TEMPLATES = {
#     'TRANSACTION_SUCCESS_SMS': 'Dear {customer_name}, your transaction of KES {amount} has been successful. Ref: {reference}. Balance: KES {balance}. Thank you for banking with Equity.',
#     'TRANSACTION_SUCCESS_EMAIL': 'Your transaction has been processed successfully.',
#     'LOGIN_ALERT_SMS': 'Dear {customer_name}, your account was accessed on {timestamp}. If this was not you, please contact us immediately.',
#     'LOW_BALANCE_SMS': 'Dear {customer_name}, your account balance is KES {balance}. Please deposit to continue enjoying our services.',
# }

# # Feature flags
# FEATURE_FLAGS = {
#     'BIOMETRIC_AUTHENTICATION': config('ENABLE_BIOMETRIC_AUTH', default=False, cast=bool),
#     'CRYPTOCURRENCY_SUPPORT': config('ENABLE_CRYPTO', default=False, cast=bool),
#     'AI_FRAUD_DETECTION': config('ENABLE_AI_FRAUD', default=False, cast=bool),
#     'REAL_TIME_NOTIFICATIONS': config('ENABLE_REALTIME_NOTIFICATIONS', default=True, cast=bool),
#     'ADVANCED_ANALYTICS': config('ENABLE_ANALYTICS', default=False, cast=bool),
# }

