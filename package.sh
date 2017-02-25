#!/bin/bash -a

pushd ..

#1.0 == build-35
name=veraview-build-85.zip

[ -f ${name} ] && unlink ${name}
zip -r ${name} \
    --exclude='.*.swp' \
    --exclude='*.[12]' \
    --exclude='*.py_' \
    --exclude='*.pyc' \
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
    veraview/veraview.run.sh \
    veraview/vvconda.run.bat \
    veraview/vvconda.run.sh

#    --exclude='canopy.run.sh'
#    --exclude='package.sh'
#    --exclude='sync-save.sh'
#    --exclude='vera_sync_from_code_ornl_gov.sh'
#    --exclude='veraview-linux.run.sh'
#    --exclude='veraview-mac.run.sh'

#    veraview/veraview-linux.run.sh
#    veraview/veraview-mac.run.sh

#    veraview/test

popd
