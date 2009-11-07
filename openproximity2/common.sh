#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
for i in $(pwd)/libs/*.egg; do
    PYTHONPATH=$PYTHONPATH:$i
done

LOG_DIR=/var/log/aircable

export PYTHONPATH
if [ -f /etc/timezone ]; then
    export TZ=$(cat /etc/timezone)
fi

if [ ! -d $LOG_DIR ]; then
    mkdir -p $LOG_DIR
fi

AIRCABLE_PATH="/tmp"

if [ -f /etc/openproximity2.conf ]; then
    source /etc/openproximity2.conf
fi

mkdir -p $AIRCABLE_PATH

if [ ! -f $AIRCABLE_PATH/aircable.db ]; then
    cd django-web
    set -e
    echo "Initializating DB"
    python manage.py syncdb --noinput
    python createadmin.py
    set +e
    cd ..
fi
