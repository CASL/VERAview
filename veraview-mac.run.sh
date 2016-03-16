#!/bin/bash -a

VERAViewDir=$(dirname "$0")

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CanopyUserBinDir variable to point the User/bin subdir
# under that path.
#------------------------------------------------------------------------
CanopyUserBinDir="$HOME/Library/Enthought/Canopy_64bit/User/bin"

if [ -x "${CanopyUserBinDir}/python" ]; then
  export ETS_TOOLKIT=wx
#  export DYLD_LIBRARY_PATH="${VERAViewDir}/ImageMagick/macos/lib:${DYLD_LIBRARY_PATH}"
#  export PATH="${VERAViewDir}/ImageMagick/macos:${PATH}"
  export PYTHONPATH="${VERAViewDir}:${PYTHONPATH}"
  #exec "${CanopyUserBinDir}/python" veraview.py "$@"
  exec "${CanopyUserBinDir}/python" "${VERAViewDir}/veraview.py" "$@"

else
  cat <<END >&2
** Canopy installation not found **

Modify this script to set the CanopyUserBinDir environment variable to point
to your Canopy User/bin directory.
END

fi
