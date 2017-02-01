#!/bin/bash -a

VERAViewDir=$(dirname "$0")

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CanopyUserBinDir variable to point the User/bin subdir
# under that path.
#------------------------------------------------------------------------
if [ "$(uname)" = "Darwin" ]; then
  CanopyUserBinDir="$HOME/Library/Enthought/Canopy_64bit/User/bin"
else
  CanopyUserBinDir=$HOME/Enthought/Canopy_64bit/User/bin
fi

if [ -x "${CanopyUserBinDir}/python" ]; then
  export ETS_TOOLKIT=wx
  export PYTHONPATH="${VERAViewDir}:${PYTHONPATH}"
  exec "${CanopyUserBinDir}/python" "${VERAViewDir}/veraview.py" "$@"

else
  cat <<END >&2
** Canopy installation not found **

Modify this script to set the CanopyUserBinDir environment variable to point
to your Canopy User/bin directory.
END

fi
