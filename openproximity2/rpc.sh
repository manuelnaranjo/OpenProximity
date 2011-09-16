#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh

cd django-web
echo "Starting RPyC server"

exec python manage.py rpc --django_debug=True $@
