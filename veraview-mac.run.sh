#!/bin/bash -a

CanopyUserDir="$HOME/Library/Enthought/Canopy_64bit/User/bin"

if [ -x "${CanopyUserDir}/python" ]; then
  exec "${CanopyUserDir}/python" veraview.py "$@"

else
  cat <<END >&2
** Canopy installation not found **

Modify this script to set the CanopyUserDir environment variable to point
to your Canopy User/bin directory.
END

fi
