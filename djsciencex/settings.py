"""
Django settings for djsciencex project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TEMPLATE_DIRS = (
    BASE_DIR + "/templates/",
    BASE_DIR + "/main/templates/",
    BASE_DIR + "/main/templates/main/",
    BASE_DIR + "/polls/templates/",
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yn63o9^fe%vmxsuivx_hv=h9s^lzhferg2u6j!v(fvb@+g1=$0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True #

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'polls',
    'main',
    'core',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'djsciencex.urls'

WSGI_APPLICATION = 'djsciencex.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE':'django.db.backends.mysql',
        'NAME': 'sciencex',
        'USER': 'linkingpilot',
        'PASSWORD': '881209',
        'HOST': '54.200.209.54',
        'PORT': '3306',
    }
}

STATICFILES_DIRS = (
    BASE_DIR + '/templates/static/',
    BASE_DIR + '/main/static/',
    )
# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

FULLTEXT_DIR =  '/Users/binchen1/Documents/code/sciencex/web_data/companydb/'
#FULLTEXT_DIR = '/home/ubuntu/proj/sciencex/web_data/data/companydb/'
