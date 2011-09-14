#!/bin/bash

# this script will start django shell for OpenProximity 2.0

cd django-web
python manage.py send_agent_data send_agent_data=True
