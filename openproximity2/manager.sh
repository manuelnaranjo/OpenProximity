#!/bin/bash

# you can use this script to run any django manage thing
# the script will setup the needed paths

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
python manage.py $@
