#!/bin/sh -a

pushd ..

#17
#name=veraview-build-20151125.zip
name=veraview-build-negatives.zip

[ -f ${name} ] && unlink ${name}
zip -r ${name} \
    --exclude='.*.swp' \
    veraview/bean \
    veraview/data \
    veraview/event \
    veraview/res \
    veraview/widget \
    veraview/veraview.py

#    veraview/test \

popd
