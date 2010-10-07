#!/bin/bash

PKGNAM=OpenProximity
VERSION=${VERSION:-0.1.2}

CWD=$(pwd)

PKG=$TMP/package-${PKGNAM}
rm -rf $PKG
mkdir -p $PKG

cd $PKG
cp -r $CWD/* .

for i in $( find -type d -iname .svn ); do
    rm -rf $i
done

wget http://www.babytux.org/gallery/images/coketux.gif

tar cvf $PKGNAM-$VERSION.tar .
gzip $PKGNAM-$VERSION.tar

mv $PKGNAM-$VERSION.tar.gz $CWD

rm -rf $PKG
