#!/bin/bash -a

#------------------------------------------------------------------------
# If you changed the path for your per-user environment setup,
# set the value of the CondaBinDir variable to point the bin subdir
# under that path.
#------------------------------------------------------------------------
CondaBinDir="$HOME/miniconda2/bin"
[ ! -d "${CondaBinDir}" ] && CondaBinDir="$HOME/anaconda2/bin"
Conda="${CondaBinDir}/conda"

if [ -x "${Conda}" ]; then
  exec "${Conda}" install -y numpy=1.9.3 h5py=2.5.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

else
  cat <<END >&2
** Anaconda2/Miniconda2 installation not found **

Modify this script to set the CondaBinDir environment variable to point
to your Anaconda2 or Miniconda2 bin directory.
END

fi
