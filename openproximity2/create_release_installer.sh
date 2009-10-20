#!/bin/bash

source prepare_installer.sh
tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity2-$(cat $CWD/latest-version).tar.gz openproximity2
