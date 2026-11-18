import os
from pathlib import Path
from dotenv import load_dotenv
from .base import *

# Load environment variables from .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

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

# Padrão seguro: não registrar mensagens/links de recuperação no console.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.locmem.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'SGA <nao-responda@sga.local>')
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', '3600'))
PASSWORD_RESET_DOMAIN = os.getenv('PASSWORD_RESET_DOMAIN', 'localhost:8000')
PASSWORD_RESET_USE_HTTPS = os.getenv('PASSWORD_RESET_USE_HTTPS', 'False').lower() == 'true'
PASSWORD_RESET_EMAIL_COOLDOWN = int(os.getenv('PASSWORD_RESET_EMAIL_COOLDOWN', '60'))
PASSWORD_RESET_IP_COOLDOWN = int(os.getenv('PASSWORD_RESET_IP_COOLDOWN', '10'))

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
