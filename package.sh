#!/bin/sh -a

pushd ..

#name=veraview-1.0.zip
#1.0 == build-35
name=veraview-build-40.zip

[ -f ${name} ] && unlink ${name}
zip -r ${name} \
    --exclude='.*.swp' \
    --exclude='*.[12]' \
    --exclude='canopy.run.sh' \
    veraview/bean \
    veraview/bin \
    veraview/data \
    veraview/event \
    veraview/res \
    veraview/view3d \
    veraview/widget \
    veraview/README.txt \
    veraview/veraview.py \
    veraview/veraview.run.bat \
    veraview/veraview-linux.run.sh \
    veraview/veraview-mac.run.sh

#    veraview/test \

popd
