#!/bin/bash

CWD=$(pwd)
source prepare_installer.sh

VERSION=$(cat $CWD/latest-version)
cd $OP2
cp "$CWD"/py-base openproximity2/django-web/openproximity/__init__.py
echo "version='$VERSION'" >> openproximity2/django-web/openproximity/__init__.py

mv openproximity2 openproximity-$VERSION

echo "creating official release $VERSION" 

tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity-$VERSION.tar.gz openproximity-$VERSION
