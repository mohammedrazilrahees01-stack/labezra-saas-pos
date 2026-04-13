from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================================
# SECURITY
# =====================================================

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'labezra-pos-saas-#8x$k2p!q@w3e4r5t6y7u8i9o0p-change-in-production'
)

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,0.0.0.0,*'
).split(',')

# =====================================================
# APPLICATIONS
# =====================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'accounts',
    'company',
    'inventory',
    'pos',
    'customers',
    'employees',
    'expenses',
    'notifications',
    'payroll',
    'activity',
    'accounting',
    'projects',
]


# =====================================================
# MIDDLEWARE
# =====================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SAAS PLAN PROTECTION
    'company.middleware.SubscriptionMiddleware',
    'accounts.middleware.RoleRedirectMiddleware',
    'core.middleware.MaintenanceModeMiddleware',
]


ROOT_URLCONF = 'core.urls'


# =====================================================
# TEMPLATES
# =====================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications',
                'company.context_processors.business_type',
            ],
        },
    },
]


WSGI_APPLICATION = 'core.wsgi.application'


# =====================================================
# DATABASE
# =====================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        }
    }
}


# =====================================================
# PASSWORD VALIDATION
# =====================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =====================================================
# INTERNATIONALIZATION
# =====================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dubai'
USE_I18N = True
USE_TZ = True


# =====================================================
# STATIC FILES
# =====================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# =====================================================
# MEDIA FILES
# =====================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

    
# =====================================================
# AUTHENTICATION
# =====================================================

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"


# =====================================================
# DEFAULT PRIMARY KEY
# =====================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =====================================================
# SESSION
# =====================================================

SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True


# =====================================================
# MESSAGES
# =====================================================

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


# =====================================================
# MAINTENANCE MODE
# =====================================================

MAINTENANCE_MODE = False


# =====================================================
# VAT SETTINGS (UAE / KSA)
# =====================================================

VAT_RATE = 5  # 5% UAE VAT


# =====================================================
# COMPANY DEFAULTS
# =====================================================

DEFAULT_CURRENCY = 'AED'
DEFAULT_COUNTRY = 'UAE'


# =====================================================
# FILE UPLOAD LIMITS
# =====================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB


# =====================================================
# PRODUCTION SECURITY (enabled when DEBUG=False)
# =====================================================

if not DEBUG:
    # Render handles SSL termination — use proxy header instead of SSL redirect
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Do NOT set SECURE_SSL_REDIRECT=True on Render — it causes redirect loops
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# =====================================================
# CSRF TRUSTED ORIGINS (required for Render/production)
# =====================================================

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.onrender.com,https://*.labezra.com,http://localhost:8000'
).split(',')


# =====================================================
# DATABASE (supports PostgreSQL via DATABASE_URL env var)
# =====================================================

import dj_database_url as _dj_db_url

_db_url = os.environ.get('DATABASE_URL', '')
if _db_url:
    DATABASES['default'] = _dj_db_url.config(
        default=_db_url,
        conn_max_age=600,
        ssl_require=True,
    )


# ──────────────────────────────
# EMAIL CONFIGURATION
# ──────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@labezra.com'
# Production SMTP (uncomment and configure):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
