#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh 
LOG_DIR=/var/log/aircable

export PYTHONPATH

echo "Starting Pairing manager"
if [ -z $DEBUG ]; then
    LOG_FILE=$LOG_DIR/pair.log
    export LOG_FILE
    (cd serverXR && work pair.py) &
else
    export DEBUG
    (cd serverXR && python pair.py)
fi

