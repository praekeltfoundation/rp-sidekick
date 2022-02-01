from .base import *  # noqa

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "TESTSEKRET"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

CELERY_EAGER_PROPAGATES_EXCEPTIONS = False  # To test error handling
CELERY_ALWAYS_EAGER = True
BROKER_BACKEND = "memory"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]

TRANSFERTO_LOGIN = ("fake_transferto_login",)
TRANSFERTO_TOKEN = ("fake_transferto_token",)
TRANSFERTO_APIKEY = ("fake_transferto_apikey",)
TRANSFERTO_APISECRET = ("fake_transferto_apisecret",)

RABBITMQ_MANAGEMENT_INTERFACE = "http://user:pass@rabbitmq:15672/api/queues//my_vhost/"
