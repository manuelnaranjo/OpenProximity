#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh

LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/server.log
export LOG_FILE

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
IP=$(ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}')
echo "Starting Web server, you can manage me at http://$IP"

if [ -z "$DEBUG" ]; then
    exec python manage.py runcpserver --traceback -v 2 $@ 2>&1 1>$LOG_DIR/server.log
else
    export DEBUG
    exec python manage.py runcpserver --django_debug=True --cherrypy_cp_daemonize=False --traceback -v 2 $@
fi;
