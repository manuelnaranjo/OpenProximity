#!/bin/bash

# you can use this script to run any django manage thing
# the script will setup the needed paths

source common.sh

LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/manager.log

export LOG_FILE

cd django-web
exec python manage.py $@
