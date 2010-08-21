#!/bin/bash

VERSION=$(python -c "from RemoteControlClient import __version__; print __version__")
CWD=$(pwd)
python setup.py sdist

rm -rf build
rm -rf RemoteControlClient.egg-info
rm -rf tmp
mkdir tmp
cd tmp
gunzip -c ../dist/RemoteControlClient-$VERSION.tar.gz | tar -xv
mv RemoteControlClient-$VERSION remotecontrolclient-$VERSION
cp ../dist/RemoteControlClient-$VERSION.tar.gz remotecontrolclient_$VERSION.orig.tar.gz
cp -r $CWD/debian remotecontrolclient-$VERSION/debian

