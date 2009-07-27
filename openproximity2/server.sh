#!/bin/bash

# this script will start django shell for OpenProximity 2.0

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
IP=$(ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}')
echo "Starting Web server, you can manage me at http://$IP"

if [ -z "$DEBUG" ]; then
    exec python manage.py runserver $@ 0.0.0.0:80 2>&1 1>$LOG_DIR/server.log &
else
    exec python manage.py runserver $@ 0.0.0.0:80 
fi;

