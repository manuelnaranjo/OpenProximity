#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

if [ -f /var/op2.pids ]; then
    kill -9 $(cat /var/op2.pids)
fi

if [ ! -f /tmp/aircable.db ]; then
    cd django-web
    set -e
    echo "Initializating DB"
    python manage.py syncdb
    set +e
    cd ..
fi

if [ ! -d $LOG_DIR ]; then
    mkdir -p $LOG_DIR
fi

sh server.sh &
sleep 5

while [ 1 ] ; do
    sh rpc.sh
    sleep 5
done
