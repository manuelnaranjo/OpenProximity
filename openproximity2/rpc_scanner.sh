#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/scanner.log

export PYTHONPATH
export LOG_FILE

cd serverXR
echo "Starting RPC Scanner Client"
if [ -z "$DEBUG" ]; then
    exec python manager.py localhost 8010 scanner 2>&1 &
else
    exec python manager.py localhost 8010 scanner
fi
