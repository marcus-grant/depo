"""
Django settings for depo project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Init environment variables
env = environ.Env(DEBUG=(bool, False))

# Read the env file if it exists
env_file = BASE_DIR / "depo.env"
if env_file.exists():
    environ.Env.read_env(env_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-e&szy9e=gx0-6&whzj0ermdtnn1at#n#0y*zbnp!ci@2d+juuh"
_defaultkey = "django-insecure-e&szy9e=gx0-6&whzj0ermdtnn1at#n#0y*zbnp!ci@2d+juuh"
SECRET_KEY = env("DEPO_SECRET_KEY", default=_defaultkey)  # type: ignore

# SECURITY WARNING: don't run with debug turned on in production!
# NOTE: Should we be doing this below as well?
DEBUG = env("DEBUG", default=True)

# DEBUG = True
# DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# Application definition

# Custom Vars
# Superuser info
SUPERUSER_NAME = env("DEPO_SUPERUSER_NAME", default="admin")  # type: ignore
SUPERUSER_EMAIL = env("DEPO_SUPERUSER_EMAIL", default="admin@example.com")  # type: ignore
SUPERUSER_PASS = env("DEPO_SUPERUSER_PASS", default="adminpass")  # type: ignore
# Uploads
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE = 100 * 10**6  # Default to 100MB
# Default Django Auth
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "core": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Default Django Vars
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # If using DRF for API endpoints:
    # 'rest_framework',
    # 'rest_framework.authtoken',
    # Add your apps here
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# NOTE: Use for Django REST Framework
# Optionally, if using Django Rest Framework for API endpoints
# REST_FRAMEWORK = {
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',
#         'rest_framework.authentication.TokenAuthentication',
#     ],
# }

ROOT_URLCONF = "depo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "depo.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    # You can add more directories here if needed
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
