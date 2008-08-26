#!/bin/bash

PKGNAM=openproximity
VERSION=${VERSION:-0.1.2}

CWD=$(pwd)

PKG=$TMP/$PKGNAM-$VERSION
rm -rf $PKG
mkdir -p $PKG

cd $PKG
cp -r $CWD/* .

for i in $( find -type d -iname .svn ); do
    rm -rf $i
done

cd src
wget http://www.babytux.org/gallery/images/coketux.gif
cd ..

cd ..

tar cvf $PKGNAM-$VERSION.tar $PKGNAM-$VERSION
gzip $PKGNAM-$VERSION.tar

mv $PKGNAM-$VERSION.tar.gz $CWD

rm -rf $PKG
