import glob
from setuptools import find_packages, setup

PACKAGE = 'veraview'
VERSION = '2.3.19'

setup(
    name = PACKAGE,
    version = VERSION,
    description = 'VERAOut file viewer and browser',
    license = '3-Clause BSD',
    url = 'https://github.com/CASL/VERAview/',
    #py_modules = [ 'src/veraview/veraview' ],
#    packages =
#      [
#        'bean', 'data', 'event',
#	'view3d', 'widget', 'widget.bean'
#      ],
    packages = find_packages( 'src' ),
#    package_data = { '': [ '*.conf', '*.pbs', '*.json', '*.sh' ] },
    package_dir = { '': 'src' },
    data_files =
      [
        ( 'bin/linux64', [ 'bin/linux64/gifsicle' ] ),
        ( 'bin/macos', [ 'bin/macos/gifsicle' ] ),
        ( 'bin/win32', [ 'bin/win32/gifsicle.exe' ] ),
        ( 'bin/win64', [ 'bin/win64/gifsicle.exe' ] ),
	( 'res', glob.glob( 'res/*.conf' ) + glob.glob( 'res/*.png' ) )
      ],
    install_requires =
      [
	#'argparse >= 1.1',
        'h5py >= 2.5.0',
	'six',
	'wx >= 3.0',
	#'logging', 'os', 'sys', 'threading', 'time', 'traceback'
      ],
    scripts = [ 'bin/veraview', 'bin/veraview.bat' ],
    zip_safe = False
    )
