#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server
LOG_FILE=/dev/null
PYTHONPATH=$(pwd)/libs:/usr/lib/openproximity:~/.openproximity2
LOG_DIR=/var/log/aircable
export PYTHONPATH

for i in $( find $(pwd)/libs | grep egg ); do
    PYTHONPATH=$PYTHONPATH:$i
done

function work(){
    while [ 1 ]; do
	python "$@" &>/dev/null
	sleep 5 # 5 seconds out
    done
}


if [ -f /etc/timezone ]; then
    export TZ=$(cat /etc/timezone)
fi

if [ ! -d $LOG_DIR ]; then
    mkdir -p $LOG_DIR
fi

