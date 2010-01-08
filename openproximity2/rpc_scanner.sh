#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh
LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/scanner.log

export PYTHONPATH
export LOG_FILE

cd serverXR
echo "Starting RPC Scanner Client"
if [ -z "$DEBUG" ]; then
    work manager.py localhost 8010 scanner &
else
    export DEBUG
    exec python manager.py localhost 8010 scanner
fi
