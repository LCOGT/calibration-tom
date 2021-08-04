"""
Django settings for your TOM project.

Originally generated by 'django-admin startproject' using Django 2.1.1.
Generated by ./manage.py tom_setup on Aug. 30, 2019, 9:50 p.m.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import logging.config
import tempfile

from lcogt_logging import LCOGTFormatter

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'uuly7s#w(7xm-h+%7jc@ej-lag5=1&amp;2-9m_185&amp;#(od0ih-!9r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', True)

ALLOWED_HOSTS = ['*', ]


# Application definition

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django_extensions',
    'guardian',
    'tom_common',
    'django_comments',
    'bootstrap4',
    'crispy_forms',
    'django_filters',
    'django_gravatar',
    'rest_framework',
    'tom_targets',
    'tom_alerts',
    'tom_catalogs',
    'tom_observations',
    'tom_dataproducts',
    'nres_calibrations',
    'imager_calibrations',
    'calibrations',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tom_common.middleware.Raise403Middleware',
    'tom_common.middleware.ExternalServiceMiddleware',
    'tom_common.middleware.AuthStrategyMiddleware',
]

ROOT_URLCONF = 'calibration_tom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

WSGI_APPLICATION = 'calibration_tom.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
   'default': {
       'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
       'NAME': os.getenv('DB_NAME', 'calibration-tom'),
       'USER': os.getenv('DB_USER', 'postgres'),
       'PASSWORD': os.getenv('DB_PASS', ''),
       'HOST': os.getenv('DB_HOST', '127.0.0.1'),
       'PORT': os.getenv('DB_PORT', '5432'),
   },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'  # for Django 3.2

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = True

DATETIME_FORMAT = 'Y-m-d H:m:s'
DATE_FORMAT = 'Y-m-d'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '_static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_ROOT = os.path.join(BASE_DIR, 'data')
MEDIA_URL = '/data/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': LCOGTFormatter
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO'
        },
    }
}
logging.config.dictConfig(LOGGING)

# Caching
# https://docs.djangoproject.com/en/dev/topics/cache/#filesystem-caching

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': tempfile.gettempdir()
    }
}


# AWS S3 Data Storage configuration

# the helm-chart value*.yaml file will set the value of djangoDebug (and thus DEBUG).
# For local development and dev namespace deployment, do NOT use the AWS S3 buckets.
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_S3_BUCKET', 'calibration-tom-lco-global')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-west-2')
    AWS_DEFAULT_ACL = None


# TOM Specific configuration
HINTS_ENABLED = False
HINT_LEVEL = 20
TARGET_TYPE = 'SIDEREAL'

FACILITIES = {
    'LCO': {
        'portal_url': os.getenv('OBSERVATION_PORTAL_URL', 'http://observation-portal-dev.lco.gtn'),
        'api_key': os.getenv('OBSERVATION_PORTAL_API_KEY', 'not_set'),
    }
}

# Define the valid data product types for your TOM. Be careful when removing items, as previously valid types will no
# longer be valid, and may cause issues unless the offending records are modified.
DATA_PRODUCT_TYPES = {
    'nres_rv': ('nres_rv', 'NRES RV'),
    'photometry': ('photometry', 'Photometry'),
    'fits_file': ('fits_file', 'FITS File'),
    'spectroscopy': ('spectroscopy', 'Spectroscopy'),
    'image_file': ('image_file', 'Image File')
}

DATA_PROCESSORS = {
    'nres_rv': 'calibrations.processors.NRESRVDataProcessor',
    'photometry': 'tom_dataproducts.processors.photometry_processor.PhotometryProcessor',
    'spectroscopy': 'tom_dataproducts.processors.spectroscopy_processor.SpectroscopyProcessor',
}

TOM_FACILITY_CLASSES = [
    'calibrations.facilities.imager_calibration_facility.ImagerCalibrationFacility',
    'calibrations.facilities.lco_calibration_facility.LCOCalibrationFacility'
]

TOM_ALERT_CLASSES = []

TOM_CADENCE_STRATEGIES = [
    'calibrations.cadences.nres_cadence.NRESCadenceStrategy',
    'calibrations.cadences.imager_cadence.ImagerCadenceStrategy'
]

BROKER_CREDENTIALS = {}

# Define extra target fields here. Types can be any of "number", "string", "boolean" or "datetime"
# See https://tomtoolkit.github.io/docs/target_fields for documentation on this feature
# For example:
# EXTRA_FIELDS = [
#     {'name': 'redshift', 'type': 'number'},
#     {'name': 'discoverer', 'type': 'string'}
#     {'name': 'eligible', 'type': 'boolean'},
#     {'name': 'dicovery_date', 'type': 'datetime'}
# ]
EXTRA_FIELDS = [
    # {'name': 'site', 'type': 'string'},  # for FLOYDS targets
    {'name': 'seasonal_start', 'type': 'number'},  # First of this month number the target becomes visible
    {'name': 'seasonal_end', 'type': 'number'},  # Last of this month number the target ceases to be visible
    # {'name': 'v_mag', 'type': 'number'},
    {'name': 'exp_time', 'type': 'number'},
    {'name': 'exp_count', 'type': 'number'},
    {'name': 'observing_frequency', 'type': 'number', 'default': 5},
    {'name': 'observing_period', 'type': 'number', 'default': 3},
    {'name': 'nres_active_target', 'type': 'boolean', 'default': None},
    {'name': 'cadence_expiration_date', 'type': 'datetime'},  # The date the target is no longer valid for a cadence
    {'name': 'expected_rv', 'type': 'number'},
    {'name': 'standard_type', 'type': 'string'},  # Either FLUX or RV
    {'name': 'min_lunar_distance', 'type': 'number'},  # Min lunar distance value for obs portal submission
    {'name': 'calibration_type', 'type': 'string', 'default': None}
]

# Authentication strategy can either be LOCKED (required login for all views)
# or READ_ONLY (read only access to views)
AUTH_STRATEGY = 'READ_ONLY'

TARGET_PERMISSIONS_ONLY = True

# URLs that should be allowed access even with AUTH_STRATEGY = LOCKED
# for example: OPEN_URLS = ['/', '/about']
OPEN_URLS = []

HOOKS = {
    'target_post_save': 'tom_common.hooks.target_post_save',
    # 'observation_change_state': 'tom_common.hooks.observation_change_state',
    'observation_change_state': 'calibrations.hooks.observation_change_state',
    'data_product_post_upload': 'tom_dataproducts.hooks.data_product_post_upload',
}

AUTO_THUMBNAILS = False

THUMBNAIL_MAX_SIZE = (0, 0)

THUMBNAIL_DEFAULT_SIZE = (200, 200)

CONFIGDB_URL = os.getenv('CONFIGDB_URL', 'http://configdb-dev.lco.gtn')

NRES_SITES = ('cpt', 'tlv', 'lsc', 'elp')
NRES_INSTRUMENT_TYPE = '1M0-NRES-SCICAM'

CALIBRATION_TYPES = ('NRES', 'IMAGER', 'FLOYDS')

try:
    from local_settings import *  # noqa
except ImportError:
    pass
