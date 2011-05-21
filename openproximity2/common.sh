#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server
LOG_FILE=/dev/null
LOG_DIR=/var/log/aircable

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

