from .base import *  # noqa
from .base import env

DEBUG = False

# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env.str("SECRET_KEY")

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS").split(",")
