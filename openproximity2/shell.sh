#!/bin/bash

# this script will start django shell for OpenProximity 2.0

source common.sh

cd django-web
DEBUG=yes python manage.py shell
