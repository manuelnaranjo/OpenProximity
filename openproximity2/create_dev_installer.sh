#!/bin/bash

source prepare_installer.sh

VERSION="devel-$(date +%m%d%Y%H%M%S)"

echo $VERSION > openproximity2/latest-version

tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity2-$VERSION.tar.gz openproximity2
