#!/bin/bash

# echo all commands if debug is enabled
if [ -n "$DEBUG" ]; then
    set -x
fi

UPDATE_LOCALES=$UPDATE_LOCALES

# exit script if we try to use an uninitialised variable
set -u

# exit if we get an error
set -e

function download(){
    PACKAGE=$1
    VERSION=$2
    URL=$3
    EXTENSION=$4
    DESTINATION=$5

    echo "processing $PACKAGE"

    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.$EXTENSION ]; then
        echo "Downloading"
        wget -P "$CWD"/libs $URL/$PACKAGE-$VERSION.$EXTENSION
    fi

    cp "$CWD"/libs/$PACKAGE-$VERSION.$EXTENSION $OP2/$DESTINATION/$PACKAGE-$VERSION.$EXTENSION
}

function download2(){
    PACKAGE=$1
    URL=$2
    EXTENSION=$3
    DESTINATION=$4

    echo "processing $PACKAGE"

    if [ ! -f "$CWD"/libs/$PACKAGE.$EXTENSION ]; then
        echo "Downloading"
        wget -P "$CWD"/libs $URL/$PACKAGE.$EXTENSION
    fi

    cp "$CWD"/libs/$PACKAGE.$EXTENSION $OP2/$DESTINATION/$PACKAGE.$EXTENSION
}


function download_jqueryui(){
    PACKAGE="jquery-ui"
    VERSION=$1
    URL=$2
    THEME=$3
    POST_DATA="t-name=${THEME}&ui-version=${VERSION}&download=true&theme="\
"?ffDefault=Lucida Grande%2C Lucida Sans%2C Arial%2C sans-serif&"\
"fwDefault=bold&fsDefault=1.1em&cornerRadius=6px&"\
"bgColorHeader=deedf7&bgTextureHeader=03_highlight_soft.png&"\
"bgImgOpacityHeader=100&borderColorHeader=aed0ea&fcHeader=222222&"\
"iconColorHeader=72a7cf&bgColorContent=f2f5f7&"\
"bgTextureContent=04_highlight_hard.png&bgImgOpacityContent=100&"\
"borderColorContent=dddddd&fcContent=362b36&iconColorContent=72a7cf&"\
"bgColorDefault=d7ebf9&bgTextureDefault=02_glass.png&"\
"bgImgOpacityDefault=80&borderColorDefault=aed0ea&fcDefault=2779aa&"\
"iconColorDefault=3d80b3&bgColorHover=e4f1fb&bgTextureHover=02_glass.png&"\
"bgImgOpacityHover=100&borderColorHover=74b2e2&fcHover=0070a3&"\
"iconColorHover=2694e8&bgColorActive=3baae3&bgTextureActive=02_glass.png&"\
"bgImgOpacityActive=50&borderColorActive=2694e8&fcActive=ffffff&"\
"iconColorActive=ffffff&bgColorHighlight=ffef8f&"\
"bgTextureHighlight=03_highlight_soft.png&bgImgOpacityHighlight=25&"\
"borderColorHighlight=f9dd34&fcHighlight=363636&iconColorHighlight=2e83ff&"\
"bgColorError=cd0a0a&bgTextureError=01_flat.png&bgImgOpacityError=15&"\
"borderColorError=cd0a0a&fcError=ffffff&iconColorError=ffffff&"\
"bgColorOverlay=eeeeee&bgTextureOverlay=08_diagonals_thick.png&"\
"bgImgOpacityOverlay=90&opacityOverlay=80&bgColorShadow=000000&"\
"bgTextureShadow=04_highlight_hard.png&bgImgOpacityShadow=70&"\
"opacityShadow=30&thicknessShadow=7px&offsetTopShadow=-7px&"\
"offsetLeftShadow=-7px&cornerRadiusShadow=8px"

    echo "processing $PACKAGE"

    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.min.js ]; then
        echo "Downloading jquery ui from CDN"
        wget -P "$CWD"/libs $URL/$VERSION/$PACKAGE.min.js
        mv "$CWD"/libs/$PACKAGE.min.js "$CWD"/libs/$PACKAGE-$VERSION.min.js 
    fi
    
    if [ ! -f "$CWD"/libs/$PACKAGE-$THEME-$VERSION.zip ]; then
        echo "Downloading theme"
        
        wget --post-data "${POST_DATA}" -O $PACKAGE-$THEME-$VERSION.zip http://jqueryui.com/download
        mv $PACKAGE-$THEME-$VERSION.zip "$CWD"/libs/
    fi

    cp "$CWD"/libs/$PACKAGE-$VERSION.min.js $OP2/openproximity2/django-web/openproximity/static/js
    
    mkdir $PACKAGE-$THEME-$VERSION
    pushd $PACKAGE-$THEME-$VERSION
    unzip "$CWD"/libs/$PACKAGE-$THEME-$VERSION.zip
    cp -r css/$THEME $OP2/openproximity2/django-web/openproximity/static/css
    popd
}


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
    if [ -d $PACKAGE-$VERSION ]; then
        cd $PACKAGE-$VERSION; cp -r $FOLDER $LIB_TARGET
    else
        cd $PACKAGE; cp -r $FOLDER $LIB_TARGET
    fi
}

function download_and_uncompress_bitbucket(){
    PACKAGE=$1
    VERSION=$2
    FOLDER=$3
    URL=$4

    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE-$VERSION.tar.gz ]; then
        echo "Downloading"
        wget -O test.tar.gz $URL/$VERSION.tar.gz
        mv test.tar.gz "$CWD"/libs/$PACKAGE-$VERSION.tar.gz
    fi
    
    echo "extracting $PACKAGE"
    gunzip -c "$CWD"/libs/$PACKAGE-$VERSION.tar.gz | tar -x
    if [ -d $PACKAGE-$VERSION ]; then
        cd $PACKAGE-$VERSION; cp -r $FOLDER $LIB_TARGET
    else
        cd $PACKAGE; cp -r $FOLDER $LIB_TARGET
    fi
}


function download_jstree(){
    PACKAGE=$1
    VERSION=$2
    URL=$3
    URL_P=$4

    echo "processing $PACKAGE"
    
    if [ ! -f "$CWD"/libs/$PACKAGE.$VERSION.zip ]; then
        echo "Downloading"
        wget -O "$CWD"/libs/$PACKAGE.$VERSION.zip $URL/${URL_P}_${VERSION}.zip
    fi
    
    echo "extracting $PACKAGE"
    mkdir jstree_tmp
    cd jstree_tmp
    mkdir orig
    cd orig ; unzip "$CWD"/libs/$PACKAGE.$VERSION.zip ; cd ..
    mkdir out
    cd out
    mkdir -p js && cp ../orig/jquery.jstree.js js/
#    mkdir -p js/plugins && cp ../orig/plugins/jquery.tree.contextmenu.js js/plugins/
    mkdir -p js/themes && cp -r ../orig/themes/default js/themes/
    cp -r * $OP2/openproximity2/django-web/openproximity/static/
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

function svn_download(){
    PACKAGE=$1
    VERSION=$2
    SVN=$3
    COMMIT=$4

    echo "processing $PACKAGE"

    if [ ! -d "$CWD"/libs/$PACKAGE-$VERSION ]; then
        echo "Downloading"
        pushd "$CWD"/libs
        svn checkout -r $COMMIT $SVN $PACKAGE
        svn export $PACKAGE $PACKAGE-$VERSION
        rm -rf $PACKAGE
        popd
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
    mkdir -p $OP2/openproximity2/django-web/openproximity/static/js
    cp -r tinymce/jscripts/tiny_mce/* $OP2/openproximity2/django-web/openproximity/static/js/
    rm -rf tinymce
}

function mark_emptyfiles(){
    pushd $OP2
    for i in $( find . -size 0 ); do
        echo "#empty file" > $i;
    done
    popd
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
cp -r "$CWD"/op_lib/django_restapi "$LIB_TARGET"
cp "$CWD"/pair.sh .
cp -r "$CWD"/remoteScanner .
cp "$CWD"/django-web/setpaths.py remoteScanner/
cp "$CWD"/remote_scanner.sh .
cp "$CWD"/rpc.sh .
cp "$CWD"/run.sh .
cp "$CWD"/run_rpc.sh .
cp "$CWD"/server.sh .
cp -r "$CWD"/serverXR .
cp "$CWD"/django-web/setpaths.py serverXR/
cp "$CWD"/shell.sh .
cp "$CWD"/syncdb.sh .
cp "$CWD"/syncagent.sh .
rm -rf $(find . -name .svn)
rm -rf $(find . -name *~)

cd "$OP2"
mkdir tmp
cd tmp

download_and_uncompress rpyc 3.0.6 rpyc http://ufpr.dl.sourceforge.net/sourceforge/rpyc
download_and_uncompress Django 1.3 django http://media.djangoproject.com/releases/1.3
download_and_uncompress django-rosetta 0.4.7 rosetta http://django-rosetta.googlecode.com/files
download_and_uncompress wadofstuff-django-serializers 1.0.0 wadofstuff http://wadofstuff.googlecode.com/files
download_and_uncompress poster 0.4 poster http://pypi.python.org/packages/source/p/poster/
download_and_uncompress PyOFC2 0.1.1dev pyofc2 http://pypi.python.org/packages/source/P/PyOFC2
download_and_uncompress django-notification 0.1.5 notification http://pypi.python.org/packages/source/d/django-notification/
download_and_uncompress django-mailer 0.1.0 mailer http://pypi.python.org/packages/source/d/django-mailer/
download_jstree jstree pre1.0_fix_1 https://github.com/downloads/vakata/jstree jstree
#svn_download django_restapi 81 http://django-rest-interface.googlecode.com/svn/trunk/ 81
git_download timezones 2b903a38 git://github.com/brosner/django-timezones.git 2b903a38da1ff9df4b2aba8e4f5429d967f73881
download_and_uncompress south 0.7.3 south http://www.aeracode.org/releases/south/
download jquery 1.6.2.min code.jquery.com js openproximity2/django-web/openproximity/static/js
download_jqueryui 1.8.16 https://ajax.googleapis.com/ajax/libs/jqueryui/ cupertino
download2 jquery.corner https://raw.github.com/malsup/corner/master/ js openproximity2/django-web/openproximity/static/js
download2 jquery.tweet https://raw.github.com/seaofclouds/tweet/master/tweet/ js openproximity2/django-web/openproximity/static/js
download2 DateTime https://raw.github.com/mochi/mochikit/master/MochiKit/ js openproximity2/django-web/openproximity/static/js
download2 Base https://raw.github.com/mochi/mochikit/master/MochiKit/ js openproximity2/django-web/openproximity/static/js
#some ideas on a WYSIWYG template editor
#download_and_uncompress django-tinymce 1.5 tinymce http://django-tinymce.googlecode.com/files/
#tinymce

cd $OP2

for i in `ls "$CWD"/patches/*.patch`; do
    cd "$LIB_TARGET"; patch -p0 < $i
done

rm -rf "$OP2"/tmp

DEBUG="yes"
export DEBUG
#update messages
cd "$OP2/openproximity2/django-web"; NO_SYNC="true" python manage.py  makemessages --traceback -a

#copy messages back to original code
if [ -n "$UPDATE_LOCALES" ]; then
    cp -r "$OP2/openproximity2/django-web/locale" "$CWD/django-web/"
    rm -f `find $CWD/django-web/locale | grep "\.mo$"`
fi

#now compile messages
cd "$OP2/openproximity2/django-web"; NO_SYNC="true" python manage.py  makemessages --traceback -a

#clean up compiled python files
rm -f `find . | grep "\.pyc$"`
rm -f `find . | grep "\.pyo$"`

mark_emptyfiles

