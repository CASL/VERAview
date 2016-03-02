#!/bin/sh -a

pushd ..

#17
#name=veraview-build-20151125.zip
name=veraview-build-29.zip

[ -f ${name} ] && unlink ${name}
zip -r ${name} \
    --exclude='.*.swp' \
    --exclude='canopy.run.sh' \
    veraview/bean \
    veraview/data \
    veraview/event \
    veraview/res \
    veraview/view3d \
    veraview/widget \
    veraview/veraview.py \
    veraview/veraview.run.bat \
    veraview/veraview-linux.run.sh \
    veraview/veraview-mac.run.sh

#    veraview/test \

popd
