#!/bin/bash

IP=$(ifconfig  | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}')
echo "Starting Web server, you can manage me at http://$IP"

cd django-web

exec python manage.py runcpserver $@
