#!/bin/bash

# echo all commands if debug is enabled
if [ -n "$DEBUG" ]; then
    set -x
fi

# exit script if we try to use an uninitialised variable
set -u

# exit if we get an error
set -e

function download_and_uncompress(){
    PACKAGE=$1
    VERSION=$2
    FOLDER=$3
    URL=$4

    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.tar.gz ]; then
        echo "Downloading"
        wget -P "$CWD"/libs $URL/$PACKAGE-$VERSION.tar.gz
    fi
    
    echo "extracting $PACKAGE"
    gunzip -c "$CWD"/libs/$PACKAGE-$VERSION.tar.gz | tar -x
    cd $PACKAGE-$VERSION; cp -r $FOLDER $LIB_TARGET
}

function download_jstree(){
    PACKAGE=$1
    VERSION=$2
    URL=$3
    URL_P=$4

    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE.$VERSION.zip ]; then
        echo "Downloading"
        wget -O "$CWD"/libs/$PACKAGE.$VERSION.zip $URL/$URL_P.$VERSION.zip
    fi
    
    echo "extracting $PACKAGE"
    mkdir jstree_tmp
    cd jstree_tmp
    mkdir orig
    cd orig ; unzip "$CWD"/libs/$PACKAGE.$VERSION.zip ; cd ..
    mkdir out
    cd out
    cp ../orig/jquery.tree.js .
    mkdir lib && cp ../orig/lib/jquery.js lib/
    mkdir plugins && cp ../orig/plugins/jquery.tree.contextmenu.js plugins/
    mkdir themes && cp -r ../orig/themes/default themes/
    cp -r * $OP2/openproximity2/django-web/media/
}


function download_egg(){
    PACKAGE=$1
    VERSION=$2
    URL=$3

    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.egg ]; then
        echo "Downloading"
        wget -P "$CWD"/libs $URL/$PACKAGE-$VERSION.egg
    fi
    cp "$CWD"/libs/$PACKAGE-$VERSION.egg $LIB_TARGET
}

function git_download(){
    PACKAGE=$1
    VERSION=$2
    GIT=$3
    COMMIT=$4
    
    echo "processing $PACKAGE"

    if [ ! -d "$CWD"/libs/$PACKAGE-$VERSION ]; then
        echo "Downloading"
        pushd "$CWD"/libs
        git clone $GIT $PACKAGE
        cd $PACKAGE
        git checkout $COMMIT
        popd
        mv "$CWD"/libs/$PACKAGE "$CWD"/libs/$PACKAGE-$VERSION
    fi
    cp -r "$CWD"/libs/$PACKAGE-$VERSION/$PACKAGE "$LIB_TARGET"
}

function git_egg(){
    PACKAGE=$1
    VERSION=$2
    GIT=$3
    COMMIT=$4
    
    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.egg ]; then
        echo "Downloading"
        pushd "$CWD"/libs
        git clone $GIT $PACKAGE
        cd "$PACKAGE"
        git checkout $COMMIT
        python setup.py bdist_egg
        mv dist/$PACKAGE-$VERSION.egg "$CWD"/libs/$PACKAGE-$VERSION.egg
        cd ..
        rm -rf "$PACKAGE".temp
        popd
    fi
    cp "$CWD"/libs/$PACKAGE-$VERSION.egg "$LIB_TARGET"
}

function tinymce(){
    # we need this function because tinymce has been badly packaged
    if [ ! -f "$CWD"/libs/tinymce_3_2_7.zip ]; then
	wget -P "$CWD"/libs http://ufpr.dl.sourceforge.net/project/tinymce/TinyMCE/3.2.7/tinymce_3_2_7.zip
    fi
    
    echo "extracting tinymce"
    unzip "$CWD"/libs/tinymce_3_2_7.zip
    mkdir -p $OP2/openproximity2/django-web/media/js
    cp -r tinymce/jscripts/tiny_mce/* $OP2/openproximity2/django-web/media/js/
    rm -rf tinymce
}
echo "Creating installer for version" `cat latest-version`

OP2=`pwd`/distrib
LIB_TARGET="${OP2}"/openproximity2/libs
CWD=`pwd`

rm -rf "$OP2"
mkdir -p "$OP2"/openproximity2
mkdir -p "$LIB_TARGET"

cd "$OP2"/openproximity2
cp "$CWD"/client.sh .
cp "$CWD"/common.sh .
cp -r "$CWD"/django-web .
cp "$CWD"/latest-version .
cp "$CWD"/LICENSE .
cp "$CWD"/manager.sh .
cp -r "$CWD"/op_lib/net "$LIB_TARGET"
cp -r "$CWD"/op_lib/plugins "$LIB_TARGET"
cp "$CWD"/pair.sh .
cp -r "$CWD"/remoteScanner .
cp "$CWD"/remote_scanner.sh .
cp "$CWD"/rpc.sh .
cp "$CWD"/run.sh .
cp "$CWD"/run_rpc.sh .
cp "$CWD"/server.sh .
cp -r "$CWD"/serverXR .
cp "$CWD"/shell.sh .
cp "$CWD"/syncdb.sh .
cp "$CWD"/syncagent.sh .
rm -rf $(find . -name .svn)
rm -rf $(find . -name *~)

cd "$OP2"
mkdir tmp
cd tmp

download_and_uncompress rpyc 3.0.6 rpyc http://ufpr.dl.sourceforge.net/sourceforge/rpyc
download_and_uncompress Django 1.1 django http://media.djangoproject.com/releases/1.1
git_download django_cpserver 19739be git://github.com/lincolnloop/django-cpserver.git 19739be
download_and_uncompress django-rosetta 0.4.7 rosetta http://django-rosetta.googlecode.com/files
download_and_uncompress wadofstuff-django-serializers 1.0.0 wadofstuff http://wadofstuff.googlecode.com/files
download_and_uncompress poster 0.4 poster http://pypi.python.org/packages/source/p/poster/
download_and_uncompress PyOFC2 0.1.1dev pyofc2 http://pypi.python.org/packages/source/P/PyOFC2
download_and_uncompress django-notification 0.1.5 notification http://pypi.python.org/packages/source/d/django-notification/
download_and_uncompress django-mailer 0.1.0 mailer http://pypi.python.org/packages/source/d/django-mailer/
download_jstree jstree v.0.9.9a2 http://jstree.googlecode.com/files jsTree
#some ideas on a WYSIWYG template editor
#download_and_uncompress django-tinymce 1.5 tinymce http://django-tinymce.googlecode.com/files/
#tinymce

cd $OP2

for i in `ls "$CWD"/patches/*.patch`; do
    cd "$LIB_TARGET"; patch -p0 < $i
done

rm -rf "$OP2"/tmp

PYTHONPATH=$OP2/openproximity2/libs
export PYTHONPATH
#update messages
cd "$OP2/openproximity2/django-web"; NO_SYNC="true" python manage.py makemessages -a

#copy messages back to original code
cp -r "$OP2/openproximity2/django-web/locale" "$CWD/django-web/"
rm -f `find $CWD/django-web/locale | grep "\.mo$"`

#now compile messages
cd "$OP2/openproximity2/django-web"; NO_SYNC="true" python manage.py makemessages -a

#clean up compiled python files
rm -f `find . | grep "\.pyc$"`
rm -f `find . | grep "\.pyo$"`
