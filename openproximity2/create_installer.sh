#!/bin/bash

echo "Creating installer for version" $(cat latest-version)

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
ln -s $CWD/remoteScanner .
ln -s $CWD/op_lib/net $LIB_TARGET/net
ln -s $CWD/common.sh
ln -s $CWD/rpc.sh
ln -s $CWD/run.sh
ln -s $CWD/shell.sh
ln -s $CWD/server.sh
ln -s $CWD/rpc_scanner.sh
ln -s $CWD/rpc_uploader.sh
ln -s $CWD/remote_scanner.sh
ln -s $CWD/clean.sh
ln -s $CWD/syncdb.sh
ln -s $CWD/manager.sh

cd $OP2
mkdir tmp
cd tmp

if [ ! -f $CWD/libs/rpyc-3.0.6.tar.gz ]; then
    wget -O $CWD/libs/rpyc-3.0.6.tar.gz http://ufpr.dl.sourceforge.net/sourceforge/rpyc/rpyc-3.0.6.tar.gz
fi

echo "extracting rpyc"
gunzip -c $CWD/libs/rpyc-3.0.6.tar.gz | tar -x
cd rpyc-3.0.6
cp -r rpyc $LIB_TARGET
cd ..

if [ ! -f $CWD/libs/Django-1.1.tar.gz ]; then
    wget -O $CWD/libs/Django-1.1.tar.gz http://media.djangoproject.com/releases/1.1/Django-1.1.tar.gz
fi


echo "extracting django"
gunzip -c $CWD/libs/Django-1.1.tar.gz | tar -x
cd Django-1.1
cp -r django $LIB_TARGET
cd ..

cd $OP2
rm -rf tmp
rm -f $(find . | grep "\.pyc$")
rm -f $(find . | grep "\.pyo$")
tar --numeric-owner -h --group=0 --exclude=\*svn --owner=0 -czf $CWD/openproximity2-$(cat $CWD/latest-version).tar.gz openproximity2
