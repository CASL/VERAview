#!/bin/bash -a

CanopyBinDir=$HOME/Library/Enthought/Canopy_64bit/User/bin
WxPythonLibDir=$HOME/src/veraview-anaconda-macos/lib/wxPython-3.0.2.0/lib

export DYLD_LIBRARY_PATH=${WxPythonLibDir}:${DYLD_LIBRARY_PATH}

exec ${CanopyBinDir}/python "$@"
