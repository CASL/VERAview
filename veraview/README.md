# CASL VERAView

VERAView is a GUI for visualization and engineering analyses of output data
from VERA (Virtual Environment for Reactor Applications).  Implemented in
Python, it provides instantaneous 2D and 3D images, 1D plots, and alpha-numeric
data from VERA multi-physics simulations.

VERAView is under rapid development, and significant changes in the software
are expected.  However, the snapshots in the repository represent comparatively
stable versions intended for use.  Bugs and feature requests should be reported
to

  veraview-bugs@casl-dev.ornl.gov


## Design Philosophy

VERAView is specifically designed to interpret the output data from VERA codes.
The VERAOut specification specifies how reactor data is structured in an HDF5
file.  Understanding this structure, VERAView implicitly displays the data in
the form of simplified pressurized water reactor (PWR) geometry.

* Though VERAView can only process files in the VERAOut format, it is *not*
  connected directly to VERA codes and does not require any specific data from
  the physics software.  It is currently limited to common physical geometries
  such as fuel rods, coolant channels, fuel assemblies, etc., and does not
  display any more specific information (though this may be an option in the
  future).  The result is that data from *any* reactor methods can be displayed
  by first converting the data to the VERAOut format.  Numerous converting
  codes have been created for this purpose.

* VERAView is designed to be used with nearly no experience or training.  While
  applications such as ParaView and VisIt are powerful, general-purpose data
  analysis and visualization tools, setting up data sources and rendering
  pipelines requires a fair amount of expertise and can be complex. VERAView
  provides an alternative, simplified interaction for engineers and students
  that is designed from the beginning for reactor analysis.

* VERAView is to be a true multi-physics analysis tool, specifically for the
  simultaneous visualization of neutronics, thermal-hydraulics, and fuel
  performance data.  Generally the fidelity of the displayed data is in the
  form of fuel rod or coolant channel quantities, but VERAView can also provide
  coarser quantities derived from rods and channels (such as assemblies or
  axial distributions), and can also display in-core detector data as well.
  Currently VERAView does not support methods-specific geometries, meshes, or
  intra-pin distributions, though these features could be added in the future.

* The purpose of VERAView is to go beyond visualization and provide numeric
  data for engineering analyses.  Features such as labels, plots, tool tips,
  image extraction, and comma separated values (CSV) file export allow VERAView
  to be extremely useful for interactions with Microsoft Excel and PowerPoint.
  Functions such as finding the maximum values have already been implemented,
  and there is an initial capability for displaying differences between files.

* VERAView allows inspection of data in multiple dimensions, and visualization
  by the user in different perspectives, to accommodate various types of
  reactor data and quantities.  It also incorporates time (or exposure) as a
  fourth dimension into this philosophy in a seamless manner, so that the user
  can discover critical aspects of data as a function of space and/or time,
  quickly able to observe trends and distributions.

* The analysis capabilities are designed to be extensible to new codes,
  features, or data as needed.  This is accomplished through the use of the
  custom widgets, which could be added by developers or even implemented and
  integrated by users.

* VERAView is intended to be executed locally on the user’s personal computer,
  and is supported on Windows, Mac OS X, and Linux.


## System Requirements

VERAView expects a Python-2.7 runtime environment with packages h5py, numpy,
matplotlib, wxPython, and mayavi.  The
[Anaconda2](https://www.continuum.io/downloads),
[Miniconda2](https://conda.io/miniconda.html), and
[Canopy](https://store.enthought.com/downloads/#default) environments provide
all the necessary requirements as pre-built packages.  Our experience is that
Anaconda2 and Miniconda2 run on all three platforms (Windows, Mac OSX, Linux),
but the Mac OSX wxPython implementation has some known bugs that prevent
certain VERAView features from working.  Therefore, we suggest Canopy for Mac
users.  Canopy is difficult to install on some Linux versions but is generally
usable for Windows as well.


## Windows Installation

Anaconda2 or Miniconda2 is preferred, but if you have already installed Canopy,
instructions for installing the necessary packages are below in the section
"Installing Canopy Packages".  If you have already installed Anaconda2 or
Miniconda2, skip to the section titled "Installing Anaconda2 Packages".


### Install Miniconda2

Go to the Continuum Miniconda [download page](https://conda.io/miniconda.html)
and click the *64-bit (exe installer)* link in the *Windows* column and
*Python 2.7* row.  The link should be something like the following:

  https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe

After downloading the file, execute it to install the Miniconda2 environment.
If possible, accept the defaults when prompted, including:

* Install for current user, not all users
* Install location

The default install location will be `AppData\Local\Continuum\Miniconda2` in
your home folder.  *Note, if you choose another install location, you will have
to update the *`vvconda.run.bat`* file as noted below.*


### Install Anaconda2/Miniconda2 Packages

You must install the following packages needed by VERAView:

* numpy (1.9.3)
* hp5y (2.5.0
* matplotlib
* pillow
* wxPython (3.0)
* mayavi (4.4.0)

If during the install you chose to allow Anaconda2 or Miniconda2 to be your
default Python, the `conda.exe` package manager should be in your path.
Otherwise, you must add the scripts folder (.e.g,
`%userprofile%\AppData\Local\Continuum\Miniconda2\scripts`) to your path.
Execute the following from a Command Prompt:

  > conda install -y numpy=1.9.3 hy5py=2.5.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

Alternatively, the VERAView repo includes the batch file
`files/conda-install-packages.bat` which will run this command, assuming
Anaconda2 or Miniconda2 is installed in the default location.

  > cd .....\VERAView
  > files\conda-install-packages.bat


### Install Canopy Packages

Refer to the file `files/canopy-install.pdf` in the VERAView directory for
instructions on installing Canopy and adding the packages required by VERAView.


### Launch VERAView

Two batch scripts are provided in the VERAView directory for launching
VERAView, `vvconda.run.bat` and `veraview.run.bat`, for Anaconda/Miniconda and
Canopy, respectively.  If you installed Anaconda or Miniconda in a non-default
location you will need to modify `vvconda.run.bat` to edit the first line

  set CondaDir=%userprofile%\AppData\Local\Continuum\Miniconda2

to point to your Anaconda2 or Miniconda2 installation.

Similarly, if you are using Canopy but installed in a non-default location,
edit the file `veraview.run.bat` to change the line

  set CanopyUserDir=%userprofile%\AppData\Local\Enthought\Canopy\User

to point to the property Canopy user folder.


## Mac Users

If you have already installed Anaconda or Miniconda2, you can use it for
VERAView, but the multiwindow features will be disabled.  Otherwise, we suggest
you install Canopy according to the directions specified in the file
`files/canopy-install.pdf` in the VERAView directory.


### Launch VERAView

Two scripts are provided in the VERAView directory for launching VERAView,
`vvconda.run.sh` and `veraview.run.sh`, for launching under
Anaconda2/Miniconda2 and Canopy, respectively.  If you installed Anaconda2 or
Miniconda2 in a non-default location you will need to modify `vvconda.run.sh`
to edit the line

  CondaBinDir="$HOME/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation.

Similarly, if you are using Canopy but installed in a non-default location,
edit the file `veraview.run.sh` to uncomment and change the line

  #CanopyUserBinDir=custom path/Canopy_64bit/User/bin

to point to the property Canopy user directory.


## Linux Users

Anaconda2 or Miniconda2 is preferred, but if you have managed to get Canopy
installed with version 3.0 of the wxPython package, you can give it a try.  If
you are using Canopy, follow the instructions in the file
`files/canopy-install.pdf` in the VERAView directory.

instructions for installing the necessary packages are below in the section
"Installing Canopy Packages".  If you have already installed Anaconda2 or
Miniconda2, skip to the section titled "Installing Anaconda2 Packages".


### Install Miniconda2

Go to the Continuum Miniconda [download page](https://conda.io/miniconda.html)
and click the *64-bit (bash installer)* link in the *Linux* column and
*Python 2.7* row.  The link should be something like the following:

  https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh

After downloading the file, execute it to install the Miniconda2 environment.

  $ bash Miniconda2-latest-Linux-x86_64.sh

If possible, accept the defaults when prompted, including:

* Install for current user, not all users
* Install location

The default install location will be `~/miniconda2'.  *Note, if you choose
another install location, you will have to update the *`vvconda.run.sh`* file
as noted below.*


### Install Anaconda2/Miniconda2 Packages

You must install the following packages needed by VERAView:

* numpy (1.9.3)
* hp5y (2.5.0
* matplotlib
* pillow
* wxPython (3.0)
* mayavi (4.4.0)

If during the install you chose to allow Anaconda2 or Miniconda2 to be your
default Python, the `conda` package manager should be in your path.  Otherwise,
you must add the bin folder (.e.g, `~/miniconda2/bin`) to your path.  Execute
the following from a bash shell:

  $ conda install -y numpy=1.9.3 hy5py=2.5.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

Alternatively, the VERAView repo includes the script file
`files/conda-install-packages.sh` which will run this command, assuming
Anaconda2 or Miniconda2 is installed in the default location.

  $ cd ...../VERAView
  $ bash files/conda-install-packages.sh


### Launch VERAView

Two scripts are provided in the VERAView directory for launching VERAView,
`vvconda.run.sh` and `veraview.run.sh`, for Anaconda/Miniconda and Canopy,
respectively.  If you installed Anaconda or Miniconda in a non-default location
you will need to modify `vvconda.run.sh` to edit the first line

  CondaBinDir="$HOME/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation bin directory.

Similarly, if you are using Canopy but installed in a non-default location,
edit the file `veraview.run.sh` to uncomment and change the line

  #CanopyUserBinDir=custom path/Canopy_64bit/User/bin

to point to the property Canopy user folder.
