#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		averager_itest.py				-
#	HISTORY:							-
#		2015-10-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.averager import *
from data.datamodel import *


EPILOG = """
Tests:
  scalar	--dataset [ --pin-factors ] [ --weights | --weights-file ]
"""


#------------------------------------------------------------------------
#	CLASS:		AveragerITest					-
#------------------------------------------------------------------------
class AveragerITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AveragerITest.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, fname ):
    self.fData = DataModel( fname )
    self.fAverager = Averager()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AveragerITest.CalcScalarAverage()		-
  #----------------------------------------------------------------------
  def CalcScalarAverage( self, ds_name, pin_factors_name = None, weights = None ):
    avg = self.fAverager.CalcScalarAverage(
        self.fData.GetCore(), data_in,
	pin_factors, weights
	)
    return  avg
  #end CalcScalarAverage


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AveragerITest.main()				-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser( description = '', epilog = EPILOG )

      parser.add_argument( 'test', help = 'one of "scalar"' )

      parser.add_argument(
	  '-d', '--dataset',
	  default = None,
	  help = 'name of dataset to average'
          )
      parser.add_argument(
	  '-p', '--pin-factors',
	  default = None,
	  help = 'optional pin factors dataset'
          )
      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input HDF5 file'
          )
      parser.add_argument(
	  '-s', '--state-pt',
	  default = 0,
	  help = '0-based state point index',
	  type = int
          )
      parser.add_argument(
	  '-w', '--weights',
	  default = None,
	  help = 'optional weights dataset'
          )
      parser.add_argument(
	  '--weights-file',
	  default = None,
	  help = 'file from which to read weights'
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      if args.dataset is None or args.file is None or args.test is None:
	parser.print_help()

      else:
	averager = Averager()

#			-- Must have valid data
#			--
        data = DataModel( args.file )
	messages = data.Check()
	st = data.GetState( args.state_pt )
	ds_in_nd = st.GetDataSet( args.dataset ) if st is not None else None

	if len( messages ) > 0:
	  print sys.stderr, '\n'.join( messages )
	elif ds_in_nd is None:
	  parser.print_help()

	else:
#				-- Process args
#				--
	  ds_in = ds_in_nd.value
	  pin_factors_nd = st.GetDataSet( args.pin_factors )
	  pin_factors = pin_factors_nd.value if pin_factors_nd is not None else None

	  weights = None
	  if args.weights_file is not None:
	    fp = file( args.weights_file )
	    try:
	      content = fp.read( -1 )
	      weights = np.array( list( eval( content ) ), np.float64 )
	    finally:
	      fp.close()
	  elif args.weights is not None:
	    weights_nd = st.GetDataSet( args.weights )
	    weights = weights_nd.value if weights_nd is not None else None

#				-- Check test
#				--
	  if args.test == 'scalar':
	    avg = averager.CalcScalarAverage(
		data.GetCore(), ds_in,
		pin_factors, weights
	        )
	    print 'Average = %.6g' % avg

	  #elif args.test == 'assy2d':

	  #elif args.test == 'assy3d':

	  #elif args.test == 'pin2d':

	  #elif args.test == 'radial1d':

	  else:
	    parser.print_help()
	#end else required data exist
      #end required arguments specified

    except Exception, ex:
      print >> sys.stderr, str( ex )
      et, ev, tb = sys.exc_info()
      while tb:
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
  #end main

#end AveragerITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  AveragerITest.main()
