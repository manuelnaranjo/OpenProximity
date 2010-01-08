#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh
LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/rpc.log

export PYTHONPATH

set -e
cd django-web
echo "Starting RPC server"
if [ -z "$DEBUG" ]; then
    work rpc.py &
else
    export DEBUG
    python rpc.py
fi
