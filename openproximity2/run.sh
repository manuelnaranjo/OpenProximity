#!/bin/bash

# this script will launch all the needed parts for an OpenProximity2.0 stand
# alone server

source common.sh

bash server.sh &
sleep 5

while [ 1 ] ; do
    bash rpc.sh
    sleep 5
done
