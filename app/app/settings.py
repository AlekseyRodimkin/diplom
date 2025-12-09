import os
from pathlib import Path
import logging.config
from django.urls import reverse_lazy
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = [
                    "0.0.0.0",
                    "127.0.0.1",
                ] + os.getenv(
    "DJANGO_ALLOWED_HOSTS", ""
).split(",")

INTERNAL_IPS = ["127.0.0.1"]

DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

if DEBUG:
    import socket

    try:
        hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
        INTERNAL_IPS.append("10.0.2.2")
        INTERNAL_IPS.extend([ip[: ip.rfind(".")] + ".1" for ip in ips])
    except socket.gaierror:
        pass

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "accounts.apps.AccountConfig",
    "warehouse.apps.WarehouseConfig",
    "structure.apps.StructureConfig",
    "staff.apps.StaffConfig",
    "bound.apps.BoundConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

##### Конфигурация 'django-allauth' #####
# AUTHENTICATION_BACKENDS - бэкенды аутентификации
#       ModelBackend - стандартный бэкенд Django
#       AuthenticationBackend - бэкенд allauth
# ACCOUNT_SIGNUP_FIELDS - поля для формы регистрации (* - обязательное поле)
# ACCOUNT_EMAIL_VERIFICATION - верификация email
#       mandatory - пользователь не сможет войти, пока не подтвердит email
# ACCOUNT_LOGIN_METHODS - разрешённые методы входа
#       email — вход только по email (логин по username отключён)
# ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION - автоматический логин после подтверждения email по ссылке
# ACCOUNT_CONFIRM_EMAIL_ON_GET - переход по ссылке из письма сразу подтверждает email
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", '0') == "1"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")
####################################################
LOGIN_REDIRECT_URL = reverse_lazy("warehouse:main")
LOGIN_URL = "/account/login/"

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

##### Конфигурация Базы данных #####
# База данных Posgresql в контейнере
# DEFAULT_AUTO_FIELD - настройка исправляющая переполнение первичного ключа
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
####################################################


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

LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

##### Конфигурация файлов #####
# Настройки продакшен папки для статических файлов
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

# Настройки DEBUG папки для статических файлов
STATICFILES_DIRS = [
    BASE_DIR / "static_debug",
    # BASE_DIR / 'app_name/static',
]

# допустимые типы загружаемых файлов
ALLOWED_MIME_TYPES = []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "uploads"
MEDIA_ROOT.mkdir(exist_ok=True)
####################################################


##### Конфигурация сессии #####
# Хранение сессии 8 часов
# Окончание сессии при закрытии браузера отключено
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
####################################################


##### Конфигурация логирования #####
# Логирование в файл и в консоль
# Ротация файлов: 5 по 5mb
# Уровень логирования Debug
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGFILE_PATH = LOG_DIR / "app.log"
LOGFILE_SIZE = 1024 * 1024 * 5  # 5 mb
LOGFILE_COUNT = 5

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGFILE_PATH,
            "maxBytes": LOGFILE_SIZE,
            "backupCount": LOGFILE_COUNT,
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "logfile"], "level": "DEBUG"},
}
####################################################
