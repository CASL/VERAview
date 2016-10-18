#!/bin/sh -a

pushd ..

#1.0 == build-35
name=veraview-build-69.zip

[ -f ${name} ] && unlink ${name}
zip -r ${name} \
    --exclude='.*.swp' \
    --exclude='*.[12]' \
    --exclude='*.py_' \
    --exclude='*.pyc' \
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
