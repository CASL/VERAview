#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		interpolator_itest.py				-
#	HISTORY:							-
#		2017-02-07	leerw@ornl.gov				-
#		2017-01-24	leerw@ornl.gov				-
#	  Adapting to DataModelMgr					-
#		2016-10-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, traceback
import numpy as np
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.datamodel_mgr import *
#from data.datamodel import *
from data.interpolator import *


#------------------------------------------------------------------------
#	CLASS:		InterpolatorITest				-
#------------------------------------------------------------------------
class InterpolatorITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, dmgr, ref_model, comp_model ):
    """
@param  dmgr		DataModelMgr
@param  ref_model	reference DataModel
@param  comp_model	comparison DataModel
"""
    self.compModel = comp_model
    self.dmgr = dmgr
    self.refModel = ref_model

    self.interpolator = Interpolator(
        dmgr.GetAxialMeshCenters( ref_model.name ),
	dmgr.GetAxialmesh( comp_model.name ),
	self._OnInterplator
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest._OnInterpolator()		-
  #----------------------------------------------------------------------
  def _OnInterpolator( self, current, total ):
    pct = (current * 100.0) / total
    print >> sys.stderr, '[interpolator_itest] %6d / %d (%.2f%%)' % \
        ( current, total, pct )
  #end _OnInterpolator


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.Interpolate()			-
  #----------------------------------------------------------------------
  def Interpolate( self, ds_name, time_value ):
    result = None

    #ref_state_ndx = dmgr.GetTimeValueIndex( ref_model.name )
    #dset = self.fDataModel.GetStateDataSet( ref_state_ndx, ds_name )
    dset = dmgr.GetH5DataSet( DataSetName( ref_model.name, ds_name ), time_value )

    if dset is not None:
      result = self.interpolator.interpolate( dset )

    return  result
  #end Interpolate


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      #parser = argparse.ArgumentParser( description = '', epilog = EPILOG )
      parser = argparse.ArgumentParser()
      parser.add_argument(
	  '-d', '--datasets',
	  default = [ 'pin_powers' ], nargs = '+',
	  help = 'dataset-name ...'
          )
#      parser.add_argument(
#	  '-e', '--exposure',
#	  default = 0.0,
#	  help = 'exposure value',
#	  type = float
#          )
      parser.add_argument(
	  '-f', '--files',
	  default = None, nargs = 2,
	  help = 'input HDF5 files'
          )
      parser.add_argument(
	  '-t', '--time',
	  default = 'exposure=0.0',
	  help = 'dataset=value',
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      #if args.dataset is None or args.file is None:
      if args.files is None or not args.datasets:
	parser.print_help()

      else:
#			-- Parse time and value
#			--
	tokens = args.time.split( '=' )
	time_ds_name = tokens[ 0 ]
	time_value = float( tokens[ 1 ] ) if len( tokens ) > 1 else 0.0

#			-- Must have valid data
#			--
	dmgr = DataModelMgr()
	ref_model = dmgr.OpenModel( args.files[ 0 ] )
	comp_model = dmgr.OpenModel( args.files[ 1 ] )
	dmgr.SetTimeDataSet( time_ds_name )

	test = InterpolatorITest( dmgr, ref_model, comp_model )

	for ds_name in args.dataset:
	  print '\n[%s, %s=%f]' % ( ds_name, time_ds_name, time_value )
	  result = test.Interpolate( ds_name, time_value )
	  print repr( result )
	#end for
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

#end InterpolatorITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  InterpolatorITest.main()
