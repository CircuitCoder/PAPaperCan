#!/bin/sh
set -e

export PYTHONPATH=.:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=web.settings

django-admin migrate
django-admin runserver
