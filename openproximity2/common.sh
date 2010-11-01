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

AIRCABLE_PATH="/tmp"
TIMEOUT="20"
MEDIA_ROOT=/tmp/aircable/media

if [ -f /etc/openproximity2.conf ]; then
    source /etc/openproximity2.conf
fi

export AIRCABLE_PATH
mkdir -p $AIRCABLE_PATH

if [ -z "$MEDIA_ROOT" ]; then
    MEDIA_ROOT=$AIRCABLE_PATH/media
fi
export MEDIA_ROOT
