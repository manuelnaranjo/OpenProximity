#!/bin/bash

VERSION=$(cat $CWD/latest-version)
source prepare_installer.sh
cd $OP2
mv openproximity2 openproximity2-$VERSION
tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity2-$VERSION.tar.gz openproximity2-$VERSION
