#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh 
LOG_DIR=/var/log/aircable

export PYTHONPATH
LOG_FILE=$LOG_DIR/pair.log
export LOG_FILE

echo "Starting Pairing manager"
if [ -z $DEBUG ]; then
    work pair.py &
else
    python pair.py
fi

