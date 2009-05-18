#!/bin/bash

MAKESELF_PATH=$(pwd)/makeself/
MAKESELF=${MAKESELF_PATH}/makeself.sh
OP2=$(pwd)/distrib/
LIB_TARGET=${OP2}/openproximity2/libs
CWD=$(pwd)

rm -rf $OP2
mkdir -p $OP2/openproximity2
mkdir -p $LIB_TARGET

cd $OP2/openproximity2
ln -s $CWD/serverXR .
ln -s $CWD/django-web .
ln -s $CWD/latest-version .
ln -s $CWD/rpc.sh
ln -s $CWD/run.sh
ln -s $CWD/shell.sh
ln -s $CWD/server.sh

cd $OP2
mkdir tmp
cd tmp

echo "extracting rpyc"
gunzip -c $CWD/libs/rpyc-3.0.6.tar.gz | tar -x
cd rpyc-3.0.6
cp -r rpyc $LIB_TARGET
cd ..

echo "extracting django"
gunzip -c $CWD/libs/Django-1.0.2-final.tar.gz | tar -x
cd Django-1.0.2-final
cp -r django $LIB_TARGET
cd ..

cd $OP2
rm -rf tmp
tar --numeric-owner -h --group=0 --owner=0 -czf $CWD/openproximity2.tar.gz openproximity2
