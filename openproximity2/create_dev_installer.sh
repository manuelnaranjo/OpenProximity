#!/bin/bash

source prepare_installer.sh

VERSION="devel-$(date +%Y%m%d%H%M%S)"

cd $OP2
echo $VERSION > openproximity2/latest-version
echo $VERSION > ../devel-version
echo "version='$VERSION'" >> openproximity2/django-web/openproximity/__init__.py
mv openproximity2 openproximity2-$VERSION
tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity2-$VERSION.tar.gz openproximity2-$VERSION
echo "openproximity2-$VERSION.tar.gz created"
