#!/bin/bash -a
#------------------------------------------------------------------------
#	NAME:		sync_from_code_ornl_gov.sh			-
#	HISTORY:							-
#		2016-03-08	leerw@ornl.gov				-
#------------------------------------------------------------------------
Here=$(dirname "$0")
if [ "${Here}" = "." ]; then
  Here="$PWD"
fi
HereName=$(basename "${Here}")

#Parent=$(dirname "${Here}")
#ParentName=$(basename "${Parent}")
#if [ "${HereName}" != "veraview" -o "${ParentName}" != "VERAView" ]; then
#  echo "Error: Must be run in the VERAView/veraview repo directory" >&2

if [ "${HereName}" != "VERAView" ]; then
  echo "Error: Must be run in the VERAView directory" >&2

elif [ ! -d "${Here}/veraview" ]; then
  echo "Error: "veraview" subdirectory not found" >&2

elif [ ! -d "${Here}/veraview-tests" ]; then
  echo "Error: "veraview-tests" subdirectory not found" >&2

else
# This directory must have veraview and veraview-tests subdirs prepared
# with
#   veraview: $ git clone git@code.ornl.gov:re7/veraview.git
#   veraview-tests: $ git clone git@code.ornl.gov:re7/veraview-tests.git
  SYNC_DIR=/localhome/re7/sync_veraview
  if [ $# -gt 0 ]; then
    SYNC_DIR="$1"
    shift
  fi

  if [ ! -d "${SYNC_DIR}/veraview" ]; then
    echo "Error: "${SYNC_DIR}/veraview" not found" >&2
  elif [ ! -d "${SYNC_DIR}/veraview-tests" ]; then
    echo "Error: "${SYNC_DIR}/veraview-tests" not found" >&2

  else
    pushd "${SYNC_DIR}/veraview"
    git checkout master
    git reset --hard origin/master
    git pull origin master
    popd

    rsync \
        -avzu --delete \
        --exclude=.git --exclude=3d --exclude=doc --exclude=test \
	--exclude=\*.py_ \
        --exclude=canopy.run.sh
        "${SYNC_DIR}/veraview" .

    pushd "${SYNC_DIR}/veraview-tests"
    git checkout master
    git reset --hard origin/master
    git pull origin master
    popd

    rsync \
        -avzu --delete \
        --exclude=.git \
        "${SYNC_DIR}/veraview-tests" .

    git add -A
    git commit -a -m "Sync from code.ornl.gov"
    git push
  fi
fi
