#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

PID=$$

export PYTHONPATH

cd remoteScanner
echo "Starting Remote Scanner DBUS Service"
python remotescanner.py
