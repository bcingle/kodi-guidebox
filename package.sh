#!/bin/sh

PACKAGE=plugin.video.guideboxkodi

dir="$PWD/$PACKAGE"
zip="$PWD/$PACKAGE.zip"

if [[ ! -d "$dir" ]]
then
    echo "Package directory doesn't exist: $dir" >2
    exit 1
fi

if [[ -f "$zip" ]]
then
    echo "Zip file already exists, deleting it..."
    rm -f "$zip"
fi

zip -r "$zip" $PACKAGE

cp "$zip" ../sigo-kodi-repository/dist/

