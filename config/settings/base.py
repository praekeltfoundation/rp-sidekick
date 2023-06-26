"""
Django settings for rp_sidekick project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
import os
from os.path import join

import dj_database_url
import environ
import sentry_sdk
from celery.schedules import crontab
from kombu import Exchange, Queue
from sentry_sdk.integrations.django import DjangoIntegration

root = environ.Path(__file__) - 3
env = environ.Env(DEBUG=(bool, False))

ROOT_DIR = root()
environ.Env.read_env(join(ROOT_DIR, ".env"))

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_extensions",
    "django_prometheus",
    "sidekick",
    "rp_transferto",
    "rp_recruit",
    "rp_gpconnect",
    "rp_interceptors",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "RP_SIDEKICK_DATABASE", "postgres://postgres@localhost/rp_sidekick"
        ),
        engine="django_prometheus.db.backends.postgresql",
    )
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
)

STATIC_ROOT = join(ROOT_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
COMPRESS_ENABLED = True

MEDIA_ROOT = join(ROOT_DIR, "media")
MEDIA_URL = "/media/"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": env.bool("DEBUG", False),
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

REST_FRAMEWORK = {
    "PAGE_SIZE": 1000,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}

GP_CONNECT_FILE_DIR = env.str("GP_CONNECT_FILE_DIR", "")
GP_CONNECT_ORG_NAME = env.str("GP_CONNECT_ORG_NAME", "")
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", "")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", "")

BROKER_URL = env.str("BROKER_URL", "redis://localhost:6379/0")

CELERY_DEFAULT_QUEUE = "rp_sidekick"
CELERY_QUEUES = (
    Queue("rp_sidekick", Exchange("rp_sidekick"), routing_key="rp_sidekick"),
)

CELERY_ALWAYS_EAGER = False

# Tell Celery where to find the tasks
CELERY_IMPORTS = ("rp_transferto.tasks",)

CELERY_CREATE_MISSING_QUEUES = True
CELERY_ROUTES = {"celery.backend_cleanup": {"queue": "mediumpriority"}}

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

CELERYBEAT_SCHEDULE = {}

if GP_CONNECT_FILE_DIR:
    CELERYBEAT_SCHEDULE["rp_gpconnect_find_new_import_file"] = {
        "task": "rp_gpconnect.tasks.pull_new_import_file",
        "schedule": crontab(minute="0", hour="*"),
        "kwargs": {"upload_dir": GP_CONNECT_FILE_DIR, "org_name": GP_CONNECT_ORG_NAME},
    }

TRANSFERTO_LOGIN = env.str("TRANSFERTO_LOGIN", "")
TRANSFERTO_TOKEN = env.str("TRANSFERTO_TOKEN", "")
TRANSFERTO_APIKEY = env.str("TRANSFERTO_APIKEY", "")
TRANSFERTO_APISECRET = env.str("TRANSFERTO_APISECRET", "")

RAPIDPRO_URL = env.str("RAPIDPRO_URL", "")
RAPIDPRO_TOKEN = env.str("RAPIDPRO_TOKEN", "")

ASOS_ADMIN_GROUP_ID = env.str("ASOS_ADMIN_GROUP_ID", "27825487140-1557840182")

EMAIL_HOST = env.str("EMAIL_HOST", "localhost")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "")
EMAIL_PORT = env.int("EMAIL_PORT", 25)
EMAIL_SUBJECT_PREFIX = env.str("EMAIL_SUBJECT_PREFIX", "[Django]")

RABBITMQ_MANAGEMENT_INTERFACE = env.str("RABBITMQ_MANAGEMENT_INTERFACE", "")

PROMETHEUS_EXPORT_MIGRATIONS = env.bool("PROMETHEUS_EXPORT_MIGRATIONS", False)
SENTRY_DSN = env.str("SENTRY_DSN", env.str("RAVEN_DSN", ""))
TRACES_SAMPLE_RATE = env.float("TRACES_SAMPLE_RATE", 1.0)

sentry_sdk.init(
    dsn=SENTRY_DSN if SENTRY_DSN else {},
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=os.environ.get("TRACES_SAMPLE_RATE"),
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
    # By default the SDK will try to use the SENTRY_RELEASE
    # environment variable, or infer a git commit
    # SHA as release, however you may want to set
    # something more human-readable.
    # release="myapp@1.0.0",
)
