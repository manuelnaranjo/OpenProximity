#!/bin/bash

# you can use this script to run any django manage thing
# the script will setup the needed paths

source common.sh

LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/manager.log

export PYTHONPATH
export LOG_FILE

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
python manage.py $@
