#!/bin/bash

# this script will start django shell for OpenProximity 2.0

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

cd django-web
python manage.py shell
