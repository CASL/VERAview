#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		test_format.py					-
#	HISTORY:							-
#		2015-12-22	leerw@ornl.gov				-
#		2015-12-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.utils import *


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataUtils.FormatFloat2( 0.00714407 )

  x = [ '1500', '1409.42', '1315.57', '1221.73', '1127.89', '940', '846', '753', '659' ]
  DataUtils.NormalizeValueLabels( x )
  print str( x )

  y = [ '7.65e-05', '6.87e-05', '6.08e-05', '5.3e-05', '4.51e-05', '1.37e-05', '1e-05' ]
  DataUtils.NormalizeValueLabels( y )
  print str( y )

  z = [ '0.0285', '0.0257', '0.0228', '0.02', '0.0172', '0.0143', '0.0115', '0.00867', '0.00584', '0.003' ]
  DataUtils.NormalizeValueLabels( z )
  print str( z )
