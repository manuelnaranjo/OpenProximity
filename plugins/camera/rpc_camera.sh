#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/camera.log

source common.sh

export PYTHONPATH
export LOG_FILE

cd serverXR
echo "Starting RPC Camera Client"
if [ -z "$DEBUG" ]; then
    do_work manager.py localhost 8010 camera &
else
    exec python manager.py localhost 8010 camera
fi
