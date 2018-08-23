from .base import *  # flake8: noqa

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "TESTSEKRET"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = False  # To test error handling
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = "memory"
CELERY_RESULT_BACKEND = "djcelery.backends.database:DatabaseBackend"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]