from .base import *  # noqa
from .base import env


DEBUG = False

# Raises ImproperlyConfigured exception if SECRET_KEY not in os.environ
SECRET_KEY = env.str("SECRET_KEY")

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS").split(",")

# Configure Sentry Logging
INSTALLED_APPS += ("raven.contrib.django.raven_compat",)
RAVEN_DSN = env.str("RAVEN_DSN", False)
RAVEN_CONFIG = {"dsn": RAVEN_DSN} if RAVEN_DSN else {}
