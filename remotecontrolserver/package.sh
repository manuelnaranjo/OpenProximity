#!/bin/bash

VERSION=$(python -c "from RemoteControlServer import __version__; print __version__")
CWD=$(pwd)
python setup.py sdist

rm -rf build
rm -rf RemoteControlServer.egg-info
rm -rf tmp
mkdir tmp
cd tmp
gunzip -c ../dist/RemoteControlServer-$VERSION.tar.gz | tar -xv
mv RemoteControlServer-$VERSION remotecontrolserver-$VERSION
cp ../dist/RemoteControlServer-$VERSION.tar.gz remotecontrolserver_$VERSION.orig.tar.gz
cp -r $CWD/debian remotecontrolserver-$VERSION/debian

