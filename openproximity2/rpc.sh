#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh
LOG_DIR=/var/log/aircable

export PYTHONPATH

set -e
cd django-web
echo "Starting RPC server"
if [ -z "$DEBUG" ]; then
    exec python rpc.py 2>&1 1>$LOG_DIR/rpc.log &
else
    python rpc.py
fi
