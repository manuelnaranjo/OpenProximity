#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

cd serverXR
echo "Starting RPC Scanner Client"
python manager.py localhost 8010 scanner &
# 1>>$LOG_DIR/rpc-scan 2>>$LOG_DIR/rpc-scan.err &
    
echo "Starting RPC Uploader Client"
python manager.py localhost 8010 uploader #1>>$LOG_DIR/rpc-up 2>>$LOG_DIR/rpc-up.err
