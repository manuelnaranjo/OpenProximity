#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server
LOG_FILE=/dev/null

PYTHONPATH=$(pwd)/libs
for i in $( find $(pwd)/libs | grep egg ); do
    PYTHONPATH=$PYTHONPATH:$i
done

function syncdb(){
    cd django-web
    set -e
    echo "Initializating DB"
    python manage.py syncdb --noinput
    set +e
    cd ..
}

function createadmin(){
    cd django-web
    set -e
    python createadmin.py
    set +e
    cd ..
}

function work(){
    while [ 1 ]; do
	python "$@" &>$LOG_FILE
    done
}

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

export AIRCABLE_PATH
mkdir -p $AIRCABLE_PATH

if [ ! -f $AIRCABLE_PATH/aircable.db ]; then
    syncdb
    createadmin
fi
