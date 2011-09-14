#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh

cd django-web
echo "Starting RPyC server"

if [ -z "$DEBUG" ]; then
    exec python manage.py rpc --django_debug=True --rpyc_rpc_daemonize=True --traceback -v 2
else
    export DEBUG
    exec python manage.py rpc --django_debug=True --rpyc_rpc_daemonize=False --traceback -v 2 $@
fi;
