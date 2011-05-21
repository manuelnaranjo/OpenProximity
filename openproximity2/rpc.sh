#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh

LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/rpyc.log
export LOG_FILE

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
echo "Starting RPyC server"

if [ -z "$DEBUG" ]; then
    exec python manage.py rpc --django_debug=True --rpyc_rpc_daemonize=True --traceback -v 2
else
    export DEBUG
    exec python manage.py rpc --django_debug=True --rpyc_rpc_daemonize=False --traceback -v 2 $@
fi;
