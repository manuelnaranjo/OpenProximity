#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh
LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/remote_scanner.log

export LOG_FILE

cd remoteScanner
echo "Starting Remote Scanner DBUS Service"
if [ -z "$DEBUG" ] ; then
    python remotescanner.py &
else
    export DEBUG
    python remotescanner.py
fi