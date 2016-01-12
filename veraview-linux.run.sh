#!/bin/bash -a

VERAViewDir=$(dirname "$0")

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CanopyUserBinDir variable to point the User/bin subdir
# under that path.
#------------------------------------------------------------------------
CanopyUserBinDir=$HOME/Enthought/Canopy_64bit/User/bin

if [ -x "${CanopyUserBinDir}/python" ]; then
  export ETS_TOOLKIT=wx
  exec ${CanopyUserBinDir}/python "${VERAViewDir}/veraview.py" "$@"

else
  cat <<END >&2
** Canopy installation not found. **

Edit this script to set the CanopyUserBinDir variable.
END
fi
