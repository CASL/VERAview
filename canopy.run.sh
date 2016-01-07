#!/bin/bash -a

CanopyBinDir=$HOME/Library/Enthought/Canopy_64bit/User/bin
#WxPythonLibDir=$HOME/Library/Enthought/Canopy_64bit/User/lib/wxPython/lib

#export DYLD_LIBRARY_PATH=${WxPythonLibDir}:${DYLD_LIBRARY_PATH}
export ETS_TOOLKIT=wx
#export PYTHONHOME=${WxPythonLibDir}/python2.7/site-packages/wx-3.0-osx_cocoa:${PYTHONHOME}


exec ${CanopyBinDir}/python "$@"
