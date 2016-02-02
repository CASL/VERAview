#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		deriveddata_itest.py				-
#	HISTORY:							-
#		2016-02-02	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

#from data.averager import *
from data.datamodel import *
from data.deriveddata import *


#------------------------------------------------------------------------
#	CLASS:		DerivedDataITest				-
#------------------------------------------------------------------------
class DerivedDataITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, fname ):
    self.fData = DataModel( fname )
    self.fAverager = Averager()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataITest.CalcScalarAverage()		-
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
  #	METHOD:		DerivedDataITest.main()				-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      #parser = argparse.ArgumentParser( description = '', epilog = EPILOG )
      parser = argparse.ArgumentParser()
      parser.add_argument(
	  '-d', '--dataset',
	  default = None, nargs = '+',
	  help = 'dataset-name derived-label ...'
          )
      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input HDF5 file'
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      if args.dataset == None or args.file == None:
	parser.print_help()

      else:
#			-- Must have valid data
#			--
        data = DataModel( args.file )
	dmgr = data.GetDerivedDataMgr()

	pdb.set_trace()
	for j in range( 0, len( args.dataset ) - 1, 2 ):
	  name = dmgr.\
	      CreateDataSet( 'pin', args.dataset[ j + 1 ], args.dataset[ j ] )

	  for i in range( data.GetStatesCount() ):
	    dset = data.GetStateDataSet( i, name )
	    print '\n[%s, state=%d]' % ( name, i + 1 )
	    print dset.value
	#end for tests


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

#end DerivedDataITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DerivedDataITest.main()
