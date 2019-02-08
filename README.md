# CASL VERAView

VERAView is a GUI for visualization and engineering analyses of output data
from VERA (Virtual Environment for Reactor Applications).  Implemented in
Python, it provides instantaneous 2D and 3D images, 1D plots, and alpha-numeric
data from VERA multi-physics simulations.

VERAView is under rapid development, and significant changes in the software
are expected.  However, the snapshots in the repository represent comparatively
stable versions intended for use.  Bugs and feature requests can be entered
using the *Issues* tab on this page or reported via email to

    casl-vri-infrastructure@casl.gov


## Installer Download Links

There are two primary ways to access and install VERAView: running an
application installer, and updating from the repository.  Installers for the
latest stable (relatively speaking) version are available for download as
follows:

* [Windows application installer](https://newton.ornl.gov/casl/VERAView-2.4.1-Windows-x86_64.exe)
* [Mac OS X application disk image](https://newton.ornl.gov/casl/VERAView-2.4.1-MacOSX.dmg)
* [Linux application installer script](https://newton.ornl.gov/casl/VERAView-2.4.1-Linux-x86_64.sh)

Note installers will not be updated as frequently as the repository.  So, if
you want to track development versions, you'll need to install from the
repository.

How to get VERAView from the repository and set it up for execution are
described below.

### Windows

The executable (link above) is an installer that does *not* require elevated
privileges.  By default it will install in your home folder, but you can
install to any folder in which you have permissions.  Execute the installer and
follow the prompts.

### Mac OS X

The link above is for a disk image that can be mounted by opening the file in
Finder.  The resulting mount window will have an Applications folder as well
as the VERAView application icon.  Install VERAView by dragging the icon onto
the Applications folder icon.

If you are a Admin user, VERAView will be installed in the root `/Applications`
folder.  Otherwise, it will be installed in the `$HOME/Applications`.


### Linux

Linked above is a shell script that must be executed as follows:

    $ bash VERAView-2.4.1-Linux-x86_64.sh

You can execute as root for a system wide install to any location.  Otherwise,
the default is to install in your home directory.


## Fast Path to Tracking the Repository

The easiest path for tracking repository updates is to install the
pre-built Miniconda2 environment for your platform and extracting it in you
home directory/folder.  The launcher script files will look for Python
there.

### Windows

Download the Miniconda2 environment
[zip file](https://newton.ornl.gov/casl/Miniconda2-win64.zip).  Extract it in
your folder using File Explorer.  Clone or pull from this repository to obtain
the latest VERAView version.  Launch using the batch file `vvconda.run.bat` in
the root VERAView folder.

### Mac OS X

Download the Miniconda2 environment
[gzipped tarball](https://newton.ornl.gov/casl/miniconda2-mac.tgz).  Extract it
in your home directory:

    $ tar xvfz miniconda2-mac.tgz

Clone or pull from this repository to obtain the latest VERAView version.
Launch using the script file `vvconda.run.sh` in the root VERAView directory.

### Linux

Download the Miniconda2 environment
[gzipped tarball](https://newton.ornl.gov/casl/miniconda2-linux.tgz).  Extract
it in your home directory:

    $ tar xvfz miniconda2-linux.tgz

Clone or pull from this repository to obtain the latest VERAView version.
Launch using the script file `vvconda.run.sh` in the root VERAView directory.


## Installation to an Existing Anaconda2 or Miniconda2 Environment

You must have the following packages required by VERAView (minimum version
numbers in parens):

* numpy (1.9.3)
* hp5y (2.5.0)
* scipy (0.16.0)
* matplotlib (1.4.3)
* pillow
* wxPython (3.0)
* mayavi (4.4.0)

Use the Conda command-line package manager or the Anaconda Navigator to install
any missing packages.  For Windows, `conda.exe` is in the `scripts\` subfolder
under your Anaconda2 or Miniconda2 installation.  For Mac and Linux it is the
`conda` script in the `bin/` subdir.  The following command illustrates
installation of all required packages via the command line (Command Prompt for Windows)

    conda install -y numpy=1.9.3 h5py=2.5.0 scipy=0.16.0 matplotlib pillow wxpython=3.0 mayavi=4.4.0

If you have installed Anaconda2 or Miniconda2 to a custom location, it might be
necessary to edit the VERAView launcher script.  This is described in
platform-specific sections below.


## Windows Installation

If you have already installed Anaconda2 or Miniconda2 and want to use that
Python environment, refer to the *Installation to an Existing Anaconda2 or
Miniconda2 Environment* section above.  Otherwise, you can choose to use the
single-click application installer or download a pre-built Miniconda2
environment containing all packages needed by VERAView.


### Windows Application Installer

A Windows application installer that will install VERAView and the required
Python environment (Continuum's Miniconda2) is available
[here](https://newton.ornl.gov/casl/VERAView-2.3.0-Windows-x86_64.exe).
The installer does not require elevated privileges and will install by default
in a `VERAView` subfolder in your home folder.

With this option no other steps are required to install VERAView.  After
completing the installation, you launch VERAView by executing (i.e.,
double-clicking in File Explorer or Windows Explorer) the file
`vvconda.run.exe` in the `VERAView` folder.  Also, Windows 10 users should see
a *CASL VERAView* Start menu folder containing a *VERAView* launcher shortcut.


### Windows Installation from the Repository

If you prefer not to use the application installer or plan on frequently
updating VERAView from the repository, you will save time by using an existing
Anaconda2 or Miniconda2 environment or installing one.


#### Windows Pre-Built Miniconda2 Environment

A zip file containing the Miniconda2 environment with packages required by
VERAView can be downloaded from
[here](https://newton.ornl.gov/casl/Miniconda2-win64.zip).  Extract it in your
home folder (usually `c:\Users\username` but determined by the `%userprofile%`
environment variable).  This should result in a `Miniconda2\` subfolder in your
home folder.  If you extract it to a location other than your home folder, it
will be necessary to edit the launch script as described in *Launch VERAView*
below.


#### Clone the Repository

Click the green *Clone or download* button above to see the `git` command
that will clone the VERAView repostory.  This should be run in a Command Prompt
window and will create a `VERAView\` subfolder in the current folder.

Alternatively, download the zip file and extract it in a folder of choice,
renaming the `VERAView-master` subfolder to `VERAView`.


#### Launch VERAView

A `vvconda.run.bat` script is provided in the `VERAView\` folder for launching
VERAView.  If you installed Anaconda or Miniconda in a non-default location you
will need to edit `vvconda.run.bat` to change the line

    set CondaDir=%VERAViewDir%Miniconda2

to point to your Anaconda2 or Miniconda2 installation.


## Mac OS X Installation

If you have already installed Anaconda2 or Miniconda2 and want to use that
Python environment, refer to the *Installation to an Existing Anaconda2 or
Miniconda2 Environment* section above.  Otherwise, you can choose to use an
application disk image or download a pre-built Miniconda2 environment
containing all packages required by VERAView.


### Mac OS X Application Disk Image

An application disk image containing VERAView with the required Python
environment is available
[here](https://newton.ornl.gov/casl/VERAView-2.3.0-MacOSX.dmg).
Once the image is mounted, you may copy the `VERAView.app` file to
`$HOME/Applications`, or if you are an administrator you may copy it to
`/Applications.`

With this option no other steps are required to install VERAView.  After
completing the installation, you launch VERAView by double-clicking `VERAView`
under Applications in Finder or by executing the `VERAView` script under
`VERAView.app/Contents/MacOS` in the applications directory.


### Mac OS X Installation from the Repository

If you prefer not to use the application disk image or plan on frequently
updating VERAView from the repository, you will save time by using an existing
Anaconda2 or Miniconda2 environment or installing one.


#### Mac OS X Pre-Built Miniconda2 Environment

A gzipped tar file containing the Miniconda2 environment with packages required
by VERAView can be downloaded from
[here](https://newton.ornl.gov/casl/miniconda2-mac.tgz).  Extract it in your
home directory (usually `/Users/username` but determined by the `$HOME`
environment variable).  This should result in a `miniconda2/` subdir in your
home directory.  If you extract it to a location other than your home
directory, it will be necessary to edit the launch script as described in
*Launch VERAView* below.


#### Clone the Repository

Click the green *Clone or download* button above to see the `git` command
needed to clone from the repostory.  This should be run in a Bash shell
and will create the `VERAView/` subdir in the current directory.

Alternatively, download the zip file and extract it in a directory of choice,
renaming the `VERAView-master` subdir to `VERAView`.


#### Launch VERAView

A script is provided in the `VERAView/` subdir for launching VERAView,
`vvconda.run.sh`.  If you installed Anaconda or Miniconda in a non-default
location you will need to edit `vvconda.run.sh` to change the line

    CondaBinDir="${VERAViewDir}/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation.


## Linux Installation

If you have already installed Anaconda2 or Miniconda2 and want to use that
Python environment, refer to the *Installation to an Existing Anaconda2 or
Miniconda2 Environment* section above.  Otherwise, you can choose to use an
application installer script or download a pre-built Miniconda2 environment
containing all packages required by VERAView.


### Linux Application Installer

An installer script containing VERAView with the required Python
environment is available
[here](https://newton.ornl.gov/casl/VERAView-2.3.0-Linux-x86_64.sh).
The installer does not require root privileges but can be installed as root.
When run as root, the default installation path is `/usr/local/veraview-2.3.0`.
Otherwise the default install path is `$HOME/veraview-2.3.0`.  Execute the
installer with

    $ bash VERAView-2.3.0-Linux-x86_64.sh

With this option no other steps are required to install VERAView.  After
completing the installation and depending on you desktop environment, VERAView
might appear in your desktop `Applications` menu (usually in the `Other`
folder), in which case you can launch by choosing it from the menu.
Alternatively, execute the `vvconda.run.sh` script in the `veraview-2.3.0`
installation folder.


### Linux Installation from the Repository

If you prefer not to use the application installer script or plan on frequently
updating VERAView from the repository, you will save time by using an existing
Anaconda2 or Miniconda2 environment or installing one.


#### Linux Pre-Built Miniconda2 Environment

A gzipped tar file containing the Miniconda2 environment with packages required
by VERAView can be downloaded from
[here](https://newton.ornl.gov/casl/miniconda2-linux.tgz).  Extract it in your
home directory (usually `/home/username` but determined by the `$HOME`
environment variable).  This should result in a `miniconda2/` subdir in your
home directory.  If you extract it to a location other than your home
directory, it will be necessary to edit the launch script as described in
*Launch VERAView* below.


#### Clone the Repository

Click the green *Clone or download* button above to see the `git` command
needed to clone from the repostory.  This should be run in a Bash shell
and will create the `VERAView/` subdir in the current directory.

Alternatively, download the zip file and extract it in a directory of choice,
renaming the `VERAView-master` subdir to `VERAView`.


#### Launch VERAView

A script is provided in the `VERAView/` subdir for launching VERAView,
`vvconda.run.sh`.  If you installed Anaconda or Miniconda in a non-default
location you will need to edit `vvconda.run.sh` to change the line

    CondaBinDir="${VERAViewDir}/miniconda2/bin"

to point to your Anaconda2 or Miniconda2 installation.


## Updating from the Repository

### After an Initial Clone

After an initial clone from the repository, execute

    git pull

in your VERAView repository directory to update with the latest changes.


### After a Zip Download

If you chose to download a zip file, you will need re-download the latest zip
file and extract it.  Before renaming the extracted `VERAView-master`
subdir/subfolder to `VERAView`, either delete your existing `VERAView` folder
or rename it in order to preserve it.


## After Using an Application Installer

The easiest way to migrate to using the repository after an installer is
to follow these steps after downloading a zip.

1. Move the `Miniconda2` subfolder or `miniconda2` subdir in your installation to your home folder or directory.

  Windows: The `Miniconda2` subfolder is in the root of the VERAView
  installation directory.

  Mac: The `miniconda2` subdir is in the `VERAView.app/Contents/MacOS`
  directory in the applications directory where VERAView is installed, which
  usually will be either `/Applications` or `$HOME/Applications`.

  Linux: The `miniconda2` subdir is the in the root of the VERAView
  installation.

2. Extract the zip file.

  Windows: Extract in the folder above (containing) your VERAView installation
  directory.

  Mac: Extract in the `VERAView.app/Contents` directory in the applications
  directory where VERAView is installed.   Either rename or remove your
  existing `MacOS` directory.  Rename the extracted `veraview` subdirectory to
  `MacOS`.

  Linux: Extract in the directory above (containing) your VERAView installation
  directory.

3. Copy files.

  Windows: Copy all the files in the extracted `VERAView-master` folder into
  your installed `VERAView` folder.  You can do this with File Explorer or
  with the `robocopy` in a Command Prompt window:

    > robocopy VERAView-master VERAView * /e

  Mac:  Since application files are in the `MacOS` subdir under
  `VERAView.app/Contents` the files in the newly extracted `VERAView-master`
  subdirectory must copied into `MacOS`.  For example:

    $ cd .../VERAView.app/Contents/VERAView-master
    $ cp -r * ../MacOS

  Linux: Copy all the files in the extracted `VERAView-master` directory into
  your installed `veraview` folder.  For example:

    $ cd .../VERAView-master
    $ cp -r * ../veraview


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

VERAView expects a Python-2.7 runtime environment with packages h5py,
matplotlib, mayavi, numpy, pillow, scipy, and wxPython.  Although it is
possible to install each of these packages in a custom Python environment,
VERAView is developed and tested with the Anaconda Python-2 environment.  Our
experience is that Anaconda provides a consistent environment on the three
platforms, thus Anaconda is our recommended runtime environment, and we only
provide instructions for it.  The
[Anaconda2](https://www.anaconda.com/download/) or
[Miniconda2](https://conda.io/miniconda.html)
environment provides all the necessary requirements as pre-built packages,
but packages required by VERAView must be installed.
