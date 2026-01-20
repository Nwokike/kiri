"""
Django settings for Kiri Research Labs (kiri.ng)
Optimized for Google Cloud 1GB RAM VM deployment.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
DEBUG = os.environ.get("DEBUG", "False") == "True"
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-for-development-only")

if not DEBUG and SECRET_KEY == "django-insecure-dev-key-for-development-only":
    raise ValueError("SECRET_KEY environment variable must be set in production")

# ALLOWED_HOSTS
ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "")
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]
else:
    ALLOWED_HOSTS = ["*"] if DEBUG else ["kiri.ng", "www.kiri.ng"]

CSRF_TRUSTED_ORIGINS = [
    "https://kiri.ng",
    "https://www.kiri.ng",
]

# Application definition
INSTALLED_APPS = [
    "kiri_project.apps.KiriProjectConfig",  # Must be first for SQLite signals
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third Party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.gitlab",
    "allauth.socialaccount.providers.bitbucket_oauth2",
    "users.providers.huggingface",  # Custom Hugging Face provider
    "django_htmx",
    "pwa",
    "huey.contrib.djhuey",  # Task Queue
    "storages",             # S3/R2 Storage
    "turnstile",            # Cloudflare Captcha
    # Local
    "core",
    "users",
    "publications",
    "projects",
    "tools",
    "discussions",
    "activity",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "kiri_project.middleware.SecurityHeadersMiddleware",  # Studio COOP/COEP Headers
    "csp.middleware.CSPMiddleware",  # Content Security Policy
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "kiri_project.wsgi.application"

# Database - SQLite optimized for 1GB RAM production
# NOTE: PRAGMAs are applied via connection signals in kiri_project/apps.py
# (init_command is deprecated in Django 6.0 for SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            "transaction_mode": "IMMEDIATE",  # Better concurrency
        },
    }
}

# Caching - Database Backend (Optimized for 1GB RAM)
# Using DB instead of RAM (LocMemCache) to save memory for Pyodide/App
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "kiri_cache_table",
        "TIMEOUT": 60 * 15,  # 15 minutes default
        "OPTIONS": {
            "MAX_ENTRIES": 2000
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Storage Configuration (Cloudflare R2 for Prod / Media)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.environ.get("R2_BUCKET_NAME"),
            "access_key": os.environ.get("R2_ACCESS_KEY_ID"),
            "secret_key": os.environ.get("R2_SECRET_ACCESS_KEY"),
            "endpoint_url": os.environ.get("R2_ENDPOINT_URL"),
            "region_name": "auto",
            "default_acl": "public-read",
            "querystring_auth": False,
        }
    } if not DEBUG else {
        "BACKEND": "django.core.files.storage.FileSystemStorage"
    },
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# AWS / R2 Settings for Boto3 (Backups)
AWS_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("R2_BACKUP_BUCKET_NAME") or os.environ.get("R2_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.CustomUser"

# Authentication
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth settings
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # Required for code-based verification
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_UNIQUE_EMAIL = True

# Code-based email verification (OTP style)
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_LOGIN_BY_CODE_ENABLED = True  # Magic code login

# Rate limits (replaces deprecated ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN)
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "3/m",  # 3 requests per minute
    "login": "5/m",
    "login_failed": "10/m/ip",
}

# Account linking - prevent duplicate accounts by auto-linking same email
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# OAuth Providers (GitHub, GitLab, Bitbucket, Hugging Face)
SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
            "secret": os.environ.get("GITHUB_SECRET", ""),
        },
        # Full scopes for: profile, email, starring repos, push/create repos
        "SCOPE": ["read:user", "user:email", "public_repo", "repo"],
    },
    "gitlab": {
        "APP": {
            "client_id": os.environ.get("GITLAB_CLIENT_ID", ""),
            "secret": os.environ.get("GITLAB_SECRET", ""),
        },
        # Full scopes for: profile, repos read/write, API access
        "SCOPE": ["read_user", "read_repository", "write_repository", "api", "openid", "email"],
    },
    "bitbucket_oauth2": {
        "APP": {
            "client_id": os.environ.get("BITBUCKET_CLIENT_ID", ""),
            "secret": os.environ.get("BITBUCKET_SECRET", ""),
        },
    },
    # Hugging Face - custom provider
    "huggingface": {
        "APP": {
            "client_id": os.environ.get("HUGGINGFACE_CLIENT_ID", ""),
            "secret": os.environ.get("HUGGINGFACE_SECRET", ""),
        },
        "SCOPE": ["openid", "profile", "email", "read-repos", "write-repos", "inference-api"],
    },
}
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_ADAPTER = 'users.adapter.KiriSocialAccountAdapter'

# Cloudflare Turnstile Settings
TURNSTILE_SITEKEY = os.environ.get("TURNSTILE_SITEKEY", "1x00000000000000000000AA") # Test key
TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET", "1x0000000000000000000000000000000AA") # Test key

# Huey Configuration (Separate SQLite for task queue - reduces lock contention)
HUEY = {
    'huey_class': 'huey.SqliteHuey',
    'name': 'kiri_tasks',
    'results': True,
    'store_none': False,
    'immediate': DEBUG,
    'utc': True,
    'filename': str(BASE_DIR / 'huey.sqlite3'),
}

# Email
if os.environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@kiri.ng")
SITE_URL = os.environ.get("SITE_URL", "https://kiri.ng")

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    
    # Content Security Policy
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = (
        "'self'",
        "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://challenges.cloudflare.com",
        "https://cdnjs.cloudflare.com",
    )
    CSP_STYLE_SRC = (
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
    )
    CSP_FONT_SRC = (
        "'self'",
        "https://fonts.gstatic.com",
        "https://cdnjs.cloudflare.com",
    )
    CSP_IMG_SRC = ("'self'", "data:", "https:")
    CSP_CONNECT_SRC = ("'self'", "https://cdn.jsdelivr.net", "https://huggingface.co")
    
    # Performance
    CONN_MAX_AGE = 60
    DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    
    # Simple in-memory cache for 1GB RAM constraint
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "kiri-cache",
            "OPTIONS": {"MAX_ENTRIES": 5000},  # ~20MB max
        }
    }
    
    # CSRF Cookie settings
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = "Strict"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# PWA Settings
PWA_APP_NAME = 'Kiri Research Labs'
PWA_APP_SHORT_NAME = 'Kiri'
PWA_APP_DESCRIPTION = 'The Post-Compute Research Lab'
PWA_APP_THEME_COLOR = '#2E9A4F'
PWA_APP_BACKGROUND_COLOR = '#0F2F1B'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {'src': '/static/images/icons/icon-192x192.png', 'sizes': '192x192'},
    {'src': '/static/images/icons/icon-512x512.png', 'sizes': '512x512'}
]
# Note: Service worker served via core.views.serviceworker, not static file
# PWA_SERVICE_WORKER_PATH setting is not used with our template-based approach
