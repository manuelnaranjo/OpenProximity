#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PID_FILE=/var/run/openproximity.pid
LOG_DIR=/var/log/aircable
CWD=$(pwd)

echo "Starting RPC $1 Client"

if [ -z "$DEBUG" ]; then
    LOG_FILE=$LOG_DIR/$1.log
    export LOG_FILE
    ( cd serverXR && work manager.py localhost 8010 $1 ) &
else
    export DEBUG
    ( cd serverXR && python manager.py localhost 8010 $1 ) &
fi

