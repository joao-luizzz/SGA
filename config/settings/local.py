import os
from .base import *

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

DB_ENGINE = os.getenv("DB_ENGINE", "django.db.backends.postgresql")
DB_NAME = os.getenv("DB_NAME", "sga_db")
DB_USER = os.getenv("DB_USER", "sga_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "sga_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Database Configuration
if os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "t"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
        }
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {'recovery_secrets': {'()': 'accounts.logging.RecoveryLogFilter'}},
    'formatters': {
        'server': {'()': 'django.utils.log.ServerFormatter',
                   'format': '[{server_time}] {message}', 'style': '{'},
    },
    'handlers': {
        'server': {'class': 'logging.StreamHandler', 'formatter': 'server'},
    },
    'loggers': {
        'django.server': {'handlers': ['server'], 'level': 'INFO',
                          'propagate': False, 'filters': ['recovery_secrets']},
        'django.request': {'filters': ['recovery_secrets']},
    },
}
