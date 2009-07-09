#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

sh common.sh

sh server.sh &
sh rpc.sh &

sleep 5

while [ 1 ] ; do
    sh client.sh
    sleep 5
done
