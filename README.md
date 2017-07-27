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


## Download Links

Installers are available for download as follows:

* [Windows application installer](https://newton.ornl.gov/casl/VERAView-2.1b1-Windows-x86_64.exe)
* [Mac OS X application disk image](https://newton.ornl.gov/casl/VERAView-2.1b1-MacOSX.dmg)
* [Linux application installer script](https://newton.ornl.gov/casl/VERAView-2.1b1-Linux-x86_64.sh)


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
  and is supported on Windows, Mac OSX, and Linux.


## System Requirements

VERAView expects a Python-2.7 runtime environment with packages h5py,
matplotlib, mayavi, numpy, pillow, scipy, and wxPython.
The
[Anaconda2](https://www.continuum.io/downloads) and
[Miniconda2](https://conda.io/miniconda.html)
environments provide all the necessary requirements as pre-built packages.  Our
experience is that Anaconda2 and Miniconda2 run on all three platforms
(Windows, Mac OSX, Linux).  Consequently, VERAView is developed and tested with
Anaconda2.  It is very possible to run VERAView with another Python environment
such as Canopy or an environment built with Linux distribution packages.
However, we only provide instructions for Anaconda2 or Miniconda2.


## Windows Installation

If you have already installed Anaconda2 or Miniconda2, skip to the section
below titled "Install Anaconda2/Miniconda2 Packages".

If you have not already installed a Python environment, you have a choice of an
application installer installer or manual installation of the required Python
components followed by clicking the green *Clone or download* button above.


### Application Installer

A Windows application installer that will install VERAView and the required
Python environment (Continuum's Miniconda2) is available
[here](https://newton.ornl.gov/casl/VERAView-2.1b1-Windows-x86_64.exe).
Note this file includes everything you need.  The installer does not
require elevated privileges and will install by default in a `VERAView`
subfolder in your home folder.

Note that with this option no other steps are required to install VERAView.
After completing the installation, you launch VERAView by executing (i.e.,
double-clicking in File Explorer or Windows Explorer) the file
`vvconda.run.exe` in the `VERAView` folder.


### Manual Install

#### Install Miniconda2

For a manual install of the required Python environment, go to the Continuum
Miniconda [download page](https://conda.io/miniconda.html) and click the
*64-bit (exe installer)* link in the *Windows* column and *Python 2.7* row.
The link should be something like the following:

    https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe

After downloading the file, execute it to install the Miniconda2 environment.
If possible, accept the defaults when prompted, including:

* Install for current user, not all users
* Install location

The install location should be `Miniconda2` or
`AppData\Local\Continuum\Miniconda2` under your home folder.  *Note, if you
choose a different install location, you will have to update the*
`vvconda.run.bat` *file as noted below.*


#### Install Anaconda2/Miniconda2 Packages

You must install the following packages needed by VERAView:

* numpy (1.9.3)
* hp5y (2.5.0)
* scipy (0.16.0)
* matplotlib (1.4.3)
* pillow
* wxPython (3.0)
* mayavi (4.4.0)

If during the install you chose to allow Anaconda2 or Miniconda2 to be your
default Python, the `conda.exe` package manager should be in your path.
Otherwise, you must add the `scripts` folder (.e.g,
`%userprofile%\Miniconda2\scripts`) to your path.  Execute the following from a
Command Prompt:

    > conda install -y numpy=1.9.3 h5py=2.5.0 scipy=0.16.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

Alternatively, the VERAView repo includes the batch file
`files/conda-install-packages.bat` which will run this command, assuming
Anaconda2 or Miniconda2 is installed in the default location.  Download the
file by clicking the *files* folder in the file list above.  Execute the
command from a Command Prompt.

    > conda-install-packages.bat


#### Install VERAView

You must follow a manual Python environment install with a download of the
VERAView Python source files.  Click the green *Clone or download* button above
and choose *Download ZIP*.  Extract the downloaded file in your home folder to
create a `VERAView` subdir.  (Note the zip file can be extracted anywhere
permissions allow, but it will be convenient to keep it in your home folder.)


#### Launch VERAView

A script is provided in the `VERAView` folder for launching VERAView,
`vvconda.run.bat`.  If you installed Anaconda or Miniconda in a non-default
location you will need to modify `vvconda.run.bat` to edit the first line

    set CondaDir=%userprofile%\AppData\Local\Continuum\Miniconda2

to point to your Anaconda2 or Miniconda2 installation.  If you are using Canopy
or an alternate environment, modify the script as needed to launch in your
environment.


## Mac Users

If you have already installed Anaconda2 or Miniconda2, skip to the section
below titled "Install Anaconda2/Miniconda2 Packages".

If you have not already installed a Python environment, you have a choice of a
VERAView Mac OS X application disk image or manual installation of the required
Python components followed by clicking the green *Clone or download* button
above.


### Application Disk Image

An application diskimage containing VERAView with the required Python
environment (Continuum's Miniconda2) is available
[here](https://newton.ornl.gov/casl/VERAView-2.1b1-MacOSX.dmg).
Note this file includes everything you need.  Once the image is mounted,
you may copy the `VERAView.app` file to `$HOME/Applications`, or if you are an
administrator you may copy it to `/Applications.`

Note that with this option no other steps are required to install VERAView.
After completing the installation, you launch VERAView by double-clicking
`VERAView` under Applications in Finder or by executing the `VERAView` script
under `Contents/MacOS` in the app installation directory.


### Manual Install

#### Install Miniconda2

For a manual install of the required Python environment, go to the Continuum
Miniconda [download page](https://conda.io/miniconda.html) and click the
*64-bit (bash installer)* link in the *Mac OS X* column and *Python 2.7* row.
The link should be something like the following:

    https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh

After downloading the file, execute it to install the Miniconda2 environment
with

    $ bash Miniconda2-latest-Linux-x86_64.sh

If possible, accept the defaults when prompted, including:

* Install for current user, not all users
* Install location


### Install Anaconda2/Miniconda2 Packages

You must install the following packages needed by VERAView:

* numpy (1.9.3)
* hp5y (2.5.0)
* scipy (0.16.0)
* matplotlib (1.4.3)
* pillow
* wxPython (3.0)
* mayavi (4.4.0)

If during the install you chose to allow Anaconda2 or Miniconda2 to be your
default Python, the `conda` package manager should be in your path.  Otherwise,
you must add the Anaconda2/Miniconda2 `bin` folder (.e.g, `~/miniconda2/bin`)
to your path.  Execute the following from a bash shell:

    $ conda install -y numpy=1.9.3 h5py=2.5.0 scipy=0.16.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

Alternatively, the VERAView repo includes the script file
`files/conda-install-packages.sh` which will run this command, assuming
Anaconda2 or Miniconda2 is installed in the default location.  Download the
file by clicking the *files* folder in the file list above.  Execute the
command from a bash shell.

    $ bash files/conda-install-packages.sh


#### Install VERAView

You must follow a manual Python environment install with a download of the
VERAView Python source files.  Click the green *Clone or download* button above
and choose *Download ZIP*.  Extract the downloaded file in your home folder to
create a `VERAView` subdir.  (Note the zip file can be extracted anywhere
permissions allow, but it will be convenient to keep it in your home folder.)


#### Launch VERAView

A script is provided in the `VERAView` folder for launching VERAView,
`vvconda.run.sh`.  If you installed Anaconda or Miniconda in a non-default
location you will need to modify `vvconda.run.sh` to edit the first line

    CondaBinDir="${VERAViewDir}/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation.  If you are using Canopy
or an alternate environment, modify the script as needed to launch in your
environment.


## Linux Users

If you have already installed Anaconda2 or Miniconda2, skip to the section
below titled "Install Anaconda2/Miniconda2 Packages".

If you have not already installed a Python environment, you have a choice of an
application installer script or manual installation of the required Python
components followed by clicking the green *Clone or download* button above.


### Application Installater Script

An application installer that will install VERAView and the required Python
environment (Continuum's Miniconda2) is available
[here](https://newton.ornl.gov/casl/VERAView-2.1b1-Linux-x86_64.sh).
Note this large file includes everything you need.  The installer does not
require root but can be installed as root.  When run as root, the default
installation path is `/usr/local/veraview-2.1b1`.  Otherwise the default
install path is `$HOME/veraview-2.1b1`.  Execute the installer with

    $ bash VERAView-2.1b1-Linux-x86_64.sh

Note that with this option no other steps are required to install VERAView.
After completing the installation, you launch VERAView by double-clicking
`VERAView` under Applications in Finder or by executing the `VERAView` script
under `Contents/MacOS` in the app installation directory.


### Manual Install

#### Install Miniconda2

For a manual install of the required Python environment, go to the Continuum
Miniconda [download page](https://conda.io/miniconda.html) and click the
*64-bit (bash installer)* link in the *Linux* column and *Python 2.7* row.
The link should be something like the following:

    https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh

After downloading the file, execute it to install the Miniconda2 environment
with

    $ bash Miniconda2-latest-Linux-x86_64.sh

If possible, accept the defaults when prompted, including:

* Install for current user, not all users
* Install location


### Install Anaconda2/Miniconda2 Packages

You must install the following packages needed by VERAView:

* numpy (1.9.3)
* hp5y (2.5.0)
* scipy (0.16.0)
* matplotlib (1.4.3)
* pillow
* wxPython (3.0)
* mayavi (4.4.0)
* libgfortran (1.0)

Note due to some package version incompatibilities (blas, scipy), it is
necessary to **downgrade** libgfortran to version 1.

If during the install you chose to allow Anaconda2 or Miniconda2 to be your
default Python, the `conda` package manager should be in your path.  Otherwise,
you must add the Anaconda2/Miniconda2 `bin` folder (.e.g, `~/miniconda2/bin`)
to your path.  Execute the following from a bash shell:

    $ conda install -y numpy=1.9.3 h5py=2.5.0 scipy=0.16.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0 libgfortran=1

Alternatively, the VERAView repo includes the script file
`files/conda-install-packages.linux.sh` which will run this command, assuming
Anaconda2 or Miniconda2 is installed in the default location.  Download the
file by clicking the *files* folder in the file list above.  Execute the
command from a bash shell.

    $ bash files/conda-install-packages.linux.sh


#### Install VERAView

You must follow a manual Python environment install with a download of the
VERAView Python source files.  Click the green *Clone or download* button above
and choose *Download ZIP*.  Extract the downloaded file in your home folder to
create a `VERAView` subdir.  (Note the zip file can be extracted anywhere
permissions allow, but it will be convenient to keep it in your home folder.)


#### Launch VERAView

A script is provided in the `VERAView` folder for launching VERAView,
`vvconda.run.sh`.  If you installed Anaconda or Miniconda in a non-default
location you will need to modify `vvconda.run.sh` to edit the first line

    CondaBinDir="${VERAViewDir}/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation.  If you are using Canopy
or an alternate environment, modify the script as needed to launch in your
environment.
