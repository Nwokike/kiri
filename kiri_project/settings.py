"""
Django settings for Kiri Labs (kiri.ng)
Optimized for Google Cloud 1GB RAM VM deployment.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
DEBUG = os.environ.get("DEBUG", "False") == "True"
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-development-only")

if not DEBUG and SECRET_KEY == "django-insecure-dev-key-for-development-only":
    raise ValueError("SECRET_KEY environment variable must be set in production")

ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "")
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]
else:
    ALLOWED_HOSTS = ["*"] if DEBUG else ["kiri.ng", "www.kiri.ng"]

CSRF_TRUSTED_ORIGINS = [
    "https://kiri.ng",
    "https://www.kiri.ng",
]

CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "hello@kiri.ng")

# Core Application Definition
INSTALLED_APPS = [
    "kiri_project.apps.KiriProjectConfig",  # Must be first for SQLite signals
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "users.providers.huggingface",
    "django_htmx",
    "pwa",
    "core",
    "users",
    "projects",
    "tools",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware", 
    "core.middleware.ExceptionLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "kiri_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "kiri_project.context_processors.kiri_settings",
                "kiri_project.context_processors.ecosystem_platforms",
            ],
        },
    },
]

WSGI_APPLICATION = "kiri_project.wsgi.application"

# Database - SQLite optimized for 1GB RAM
# PRAGMAs applied via connection signals in kiri_project/apps.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",
        },
    }
}

# Caching - Database Backend to save RAM
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "kiri_cache_table",
        "TIMEOUT": 60 * 15,
        "OPTIONS": {
            "MAX_ENTRIES": 2000
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static & Media Files with WhiteNoise Optimization
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

WHITENOISE_CUSTOM_HEADERS = [
    (r'.*', {
        'Cross-Origin-Resource-Policy': 'cross-origin',
        'Access-Control-Allow-Origin': '*',
    }),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'suppress_disallowed_host': {
            '()': 'core.logging.DisallowedHostFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['suppress_disallowed_host'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.CustomUser"

# Authentication & Allauth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Staff-Only Signup Configuration
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
ACCOUNT_LOGOUT_ON_GET = True
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_ADAPTER = 'users.adapter.KiriSocialAccountAdapter'
ACCOUNT_ADAPTER = 'users.adapter.KiriAccountAdapter'

ACCOUNT_RATE_LIMITS = {
    "login": "5/m",
    "login_failed": "10/m/ip",
}

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
            "secret": os.environ.get("GITHUB_SECRET", ""),
        },
        "SCOPE": ["read:user", "user:email", "public_repo", "repo"],
    },
    "huggingface": {
        "APP": {
            "client_id": os.environ.get("HUGGINGFACE_CLIENT_ID", ""),
            "secret": os.environ.get("HUGGINGFACE_SECRET", ""),
        },
        "SCOPE": ["openid", "profile", "email", "read-repos", "write-repos", "inference-api"],
    },
}

# Tasks Configuration
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    },
}

# General & Security
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SITE_URL = os.environ.get("SITE_URL", "https://kiri.ng")

IS_TESTING = 'test' in sys.argv

if not DEBUG or IS_TESTING:
    SECURE_SSL_REDIRECT = not IS_TESTING
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    SECURE_CSP_REPORT_ONLY = {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'", 
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://www.googletagmanager.com",
            "https://pagead2.googlesyndication.com",
            "https://static.cloudflareinsights.com",
            "https://adservice.google.com",
            "https://unpkg.com",
            "blob:",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://cdnjs.cloudflare.com",
        ],
        "font-src": [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdnjs.cloudflare.com",
        ],
        "img-src": ["'self'", "data:", "https:", "https://unpkg.com", "blob:"],
        "connect-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://huggingface.co",
            "https://www.google-analytics.com",
            "https://region1.google-analytics.com",
            "https://stats.g.doubleclick.net",
            "https://unpkg.com",
            "blob:",
        ],
        "frame-src": ["'self'", "https://www.youtube-nocookie.com"],
        "object-src": ["'none'"],
    }

    CONN_MAX_AGE = 60
    DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    CSRF_COOKIE_SAMESITE = "Strict"

# PWA Settings
PWA_APP_NAME = "Kiri"
PWA_APP_SHORT_NAME = "Kiri"
PWA_APP_DESCRIPTION = "Software & AI tools, developer utilities, and project showcases by Kiri Labs. Built lightweight and efficient."
PWA_APP_THEME_COLOR = '#2E9A4F'
PWA_APP_BACKGROUND_COLOR = '#0F2F1B'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {'src': '/static/images/icons/icon-192x192.png', 'sizes': '192x192', 'type': 'image/png'},
    {'src': '/static/images/icons/icon-512x512.png', 'sizes': '512x512', 'type': 'image/png'}
]