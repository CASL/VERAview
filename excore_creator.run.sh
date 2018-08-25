#!/bin/bash -a

VERAViewDir=$(dirname "$0")

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CondaBinDir variable to point the bin subdir
# under that path.
#------------------------------------------------------------------------
CondaBinDir="${VERAViewDir}/miniconda2/bin"

[ ! -d "${CondaBinDir}" ] && CondaBinDir="$HOME/miniconda2/bin"
[ ! -d "${CondaBinDir}" ] && CondaBinDir="$HOME/anaconda2/bin"

CondaExe="${CondaBinDir}/python"

if [ -x "${CondaExe}" ]; then
  export ETS_TOOLKIT=wx
  export PYTHONPATH="${VERAViewDir}:${PYTHONPATH}"
  exec "${CondaExe}" "${VERAViewDir}/data/excore_creator.py" "$@"

else
  cat <<END >&2
** Anaconda2/Miniconda2 installation not found **

Modify this script to set the CondaBinDir environment variable to point
to your Anaconda2 or Miniconda2 bin directory.
END

fi
