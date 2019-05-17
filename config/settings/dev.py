from .base import *  # noqa
from .base import env

DEBUG = True

SECRET_KEY = env.str("SECRET_KEY", "dev_secret_key")

ENV_HOSTS = [host for host in env.str("ALLOWED_HOSTS", "").split(",") if host]
ALLOWED_HOSTS = ENV_HOSTS + ["localhost", ".localhost", "127.0.0.1", "0.0.0.0"]
