from .base import *

# Initializing the environment Variables
env = environ.Env()
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env.development")
environ.Env.read_env(ENV_FILE_PATH)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DJANGO CORS HEADERS
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

# MEDIA FILES
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

TELEGRAM_BOT_API = env.str("TELEGRAM_BOT_API")