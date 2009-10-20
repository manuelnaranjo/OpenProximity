#!/bin/bash

# this script will start django shell for OpenProximity 2.0

PYTHONPATH=$(pwd)/libs
LOG_DIR=/var/log/aircable

export PYTHONPATH

OP2_VERSION=$(cat latest-version)
export OP2_VERSION

cd django-web
python manage.py send_agent_data send_agent_data=True
