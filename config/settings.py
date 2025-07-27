from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()

# detect production vs. dev via an ENV var (e.g. DJANGO_ENV)
ENV = os.environ.get("DJANGO_ENV", "dev")

env.read_env(os.path.join(BASE_DIR, f".env.{ENV}"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG")

# --- START DEBUG TROUBLESHOOTING PRINT ---
import sys

print(
    f"*** SETTINGS.PY LOADED - DJANGO_ENV: {ENV}, DEBUG_FROM_ENV: {env.bool('DEBUG')}, FINAL_DEBUG_BEFORE_OVERRIDE: {DEBUG} ***",
    file=sys.stderr,
)
# --- END DEBUG TROUBLESHOOTING PRINT ---

# Force DEBUG=False in production environment regardless of .env file configuration
if ENV == "prod":
    DEBUG = False

# Safety check: Fail fast if DEBUG is somehow still True in production
if ENV == "prod" and DEBUG:
    import sys

    print("CRITICAL ERROR: DEBUG is True in production environment!", file=sys.stderr)
    print(
        "This is a security risk and the application will not start.", file=sys.stderr
    )
    print(f"Current DJANGO_ENV: {ENV}", file=sys.stderr)
    print(f"Current DEBUG: {DEBUG}", file=sys.stderr)
    sys.exit(1)

# Configure ALLOWED_HOSTS based on environment
if ENV == "prod":
    ALLOWED_HOSTS = env.list("ALLOWED_HOSTS_PROD", default=["organisize.com"])
else:
    # Development and other environments - include localhost and development hosts
    ALLOWED_HOSTS = ["3.128.45.219", "organisize.com", "127.0.0.1", "localhost", "*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "planner",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if ENV == "prod":
    # Production: MySQL database configuration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT"),
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "charset": "utf8mb4",
            },
        }
    }
else:
    # Development: SQLite database configuration
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Static files (CSS, JavaScript, Images)
# During development, serve static files from the app directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "planner", "static"),
]


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth settings
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "vacation_list"  # or another view name like "home"
LOGOUT_REDIRECT_URL = "login"

# Email settings - configured via environment variables with django-environ
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@organisize.com")
