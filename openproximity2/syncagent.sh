#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh
LOG_DIR=/var/log/aircable
LOG_FILE=$LOG_DIR/syncagent.log

export LOG_FILE

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
python manage.py send_agent_data send_agent_data=True
