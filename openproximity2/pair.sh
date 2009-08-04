#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

echo "Starting Pairing manager"
exec python pair.py 1>&2 2>$LOG_DIR/pair.log &

