# techhub/settings.py
import os
import sentry_sdk
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# ── Sentry Error Monitoring ──
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'csp',

    # Local apps
    'products',
    'cart',
    'orders',
    'users',
    'wishlist',
    'payment_processing',
    'chatbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'techhub.urls'

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
                'cart.context_processors.cart',
                'techhub.context_processors.analytics',
            ],
        },
    },
]

WSGI_APPLICATION = 'techhub.wsgi.application'

# ── Database ──
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Redis Cache / Fallback ──
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')
import redis
try:
    # Quick check if Redis is up without raising a global unhandled exception
    r = redis.Redis.from_url(REDIS_URL, socket_timeout=1)
    r.ping()
    CACHE_BACKEND = 'django.core.cache.backends.redis.RedisCache'
except (redis.ConnectionError, redis.TimeoutError):
    CACHE_BACKEND = 'django.core.cache.backends.locmem.LocMemCache'

CACHES = {
    'default': {
        'BACKEND': CACHE_BACKEND,
        'LOCATION': REDIS_URL if 'redis' in CACHE_BACKEND else 'unique-snowflake',
        'TIMEOUT': 600,  # 10 minutes default TTL
    }
}

# ── Rate Limiting (django-ratelimit) ──
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# ── Password Validation ──
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static / Media ──
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Crispy Forms ──
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ── Auth URLs ──
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ── Stripe ──
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_placeholder')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_placeholder')

# ── Analytics ──
SITE_ID = 1
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')
FACEBOOK_PIXEL_ID = os.environ.get('FACEBOOK_PIXEL_ID', '')
TWITTER_PIXEL_ID = os.environ.get('TWITTER_PIXEL_ID', '')
ANALYTICAL_INTERNAL_IPS = ['127.0.0.1', '::1']
ANALYTICAL_AUTO_IDENTIFY = True
GOOGLE_ANALYTICS_GTAG_PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_GTAG_PROPERTY_ID', '')
FACEBOOK_PIXEL_USE_NOSCRIPT = True
TWITTER_PIXEL_USE_NOSCRIPT = True

# ── Celery ──
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ── Content Security Policy (django-csp v4) ──
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'", "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://www.googletagmanager.com",
            "https://connect.facebook.net",
            "https://static.ads-twitter.com",
        ),
        'style-src': (
            "'self'", "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://fonts.googleapis.com",
        ),
        'font-src': (
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdnjs.cloudflare.com",
        ),
        'img-src': ("'self'", "data:", "https:"),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
    }
}

# ── Security Headers ──
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Production-only security (set these when deploying to HTTPS)
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# ── Logging ──
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'products': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
