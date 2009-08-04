#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

PID_FILE=/var/run/openproximity.pid
LOG_DIR=/var/log/aircable
CWD=$(pwd)

. common.sh

if [ -n $REMOTE_SCANNER ]; then
    bash remote_scanner.sh 1>&2 2>$LOG_DIR/remotescanner.log &
fi

if [ -n $PAIR_MANAGER ]; then
    . pair.sh
    echo $! > $PID_FILE
fi

. rpc.sh
echo $! > $PID_FILE
cd $CWD

. server.sh
echo $! >> $PID_FILE
cd $CWD

# wait until rpc is ready
sleep 5

. rpc_scanner.sh
echo $! >> $PID_FILE
cd $CWD

. rpc_uploader.sh
echo $! >> $PID_FILE
cd $CWD

exit 0
