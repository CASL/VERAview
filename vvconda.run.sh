#!/bin/bash -a

VERAViewDir=$(dirname "$0")

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CanopyUserBinDir variable to point the User/bin subdir
# under that path.
#------------------------------------------------------------------------
CondaBinDir="$HOME/anaconda2/bin"
if [ "$(uname)" = "Darwin" ]; then
  CondaExe="${CondaBinDir}/pythonw"
else
  CondaExe="${CondaBinDir}/python"
fi

if [ -x "${CondaExe}" ]; then
  export ETS_TOOLKIT=wx
  export PYTHONPATH="${VERAViewDir}:${PYTHONPATH}"
  #exec "${CanopyUserBinDir}/python" veraview.py "$@"
  exec "${CondaExe}" "${VERAViewDir}/veraview.py" "$@"

else
  cat <<END >&2
** Anaconda2 installation not found **

Modify this script to set the CondaBinDir environment variable to point
to your Anaconda2 bin directory.
END

fi
