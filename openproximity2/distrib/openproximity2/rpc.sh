#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

function start_rpc(){
    set -e
    cd django-web
    echo "Starting RPC server"
    python rpc.py &
    PID=$!
    sleep 10

    cd ../serverXR
    echo "Starting RPC Scanner Client"
    python manager.py localhost 8010 scanner &
    # 1>>$LOG_DIR/rpc-scan 2>>$LOG_DIR/rpc-scan.err &
    
    echo "Starting RPC Uploader Client"
    python manager.py localhost 8010 uploader #1>>$LOG_DIR/rpc-up 2>>$LOG_DIR/rpc-up.err
    cd ..
    set +e
    kill -9 $PID
}

start_rpc
