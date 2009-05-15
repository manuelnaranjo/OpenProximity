#!/bin/bash

MAKESELF_PATH=$(pwd)/makeself/
MAKESELF=${MAKESELF_PATH}/makeself.sh
OP2=$(pwd)/distrib/
LIB_TARGET=${OP2}/openproximity2/libs
CWD=$(pwd)

rm -rf $OP2
mkdir -p $OP2/openproximity2

cd $OP2/openproximity2
ln -s $CWD/serverXR
ln -s $CWD/django-web
ln -s $CWD/latest-version

cd $OP2
mkdir tmp
cd tmp

gunzip -c $CWD/libs/rpyc-3.0.6.tar.gz | tar -xv
cd rpyc-3.0.6
mv rpyc $LIB_TARGET/
cd ..

gunzip -c $CWD/libs/Django-1.0.2-final.tar.gz | tar -xv
cd Django-1.0.2-final
mv django $LIB_TARGET/
cd ..

cd $OP2
rm -rf tmp
tar --numeric-owner -h --group=0 --owner=0 -czvf $CWD/openproximity2.tar.gz openproximity2

