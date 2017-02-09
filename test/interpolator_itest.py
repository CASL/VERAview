#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		interpolator_itest.py				-
#	HISTORY:							-
#		2017-02-09	leerw@ornl.gov				-
#		2017-02-07	leerw@ornl.gov				-
#		2017-01-24	leerw@ornl.gov				-
#	  Adapting to DataModelMgr					-
#		2016-10-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, timeit, traceback
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
	dmgr.GetAxialMeshCenters( comp_model.name ),
	self._OnInterpolator
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
    dset = self.dmgr.\
        GetH5DataSet( DataSetName( self.refModel.name, ds_name ), time_value )

    if dset is not None:
      result = self.interpolator.interpolate( dset, skip_assertions = True )

    return  result
  #end Interpolate


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.InterpolateAndDiff()		-
  #----------------------------------------------------------------------
  def InterpolateAndDiff( self, ds_name, time_value ):
    result = None
    diff = None

    #ref_state_ndx = dmgr.GetTimeValueIndex( ref_model.name )
    #dset = self.fDataModel.GetStateDataSet( ref_state_ndx, ds_name )
    dset = self.dmgr.\
        GetH5DataSet( DataSetName( self.refModel.name, ds_name ), time_value )

    if dset is not None:
      result = self.interpolator.interpolate( dset, skip_assertions = True )
      diff = dset - result

    return  result, diff
  #end InterpolateAndDiff


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    """
linear
  0.456
  0.47827
  0.47234
  0.47961
  0.466418

slinear
  64.4356
  65.153

quadratic

cubic
  68.8685
  64.141
"""
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
#      parser.add_argument(
#	  '-t', '--time',
#	  default = 'exposure=0.0',
#	  help = 'dataset=value',
#          )
      parser.add_argument(
	  '-t', '--time',
	  default = 'exposure',
	  help = 'time dataset name'
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
#	tokens = args.time.split( '=' )
#	time_ds_name = tokens[ 0 ]
#	time_value = float( tokens[ 1 ] ) if len( tokens ) > 1 else 0.0

#			-- Must have valid data
#			--
	dmgr = DataModelMgr()
	ref_model = dmgr.OpenModel( args.files[ 0 ] )
	comp_model = dmgr.OpenModel( args.files[ 1 ] )

	dmgr.SetTimeDataSet( args.time )
	time_values = dmgr.GetTimeValues( comp_model.name )

	test = InterpolatorITest( dmgr, ref_model, comp_model )
	results = []

        start_time = timeit.default_timer()
	for tv in time_values:
	  cur_results = {}
	  for ds_name in args.datasets:
	    inter, diff = test.InterpolateAndDiff( ds_name, tv )
	    cur_results[ ds_name ] = ( inter, diff )
	  #end for ds_name
	  results.append( cur_results )
	#end for tv
        elapsed_time = timeit.default_timer() - start_time
        print 'calculation time=%.6gs' % elapsed_time

	ndx = 0
	for tv in time_values:
	  print '\n[%s=%.3f]' % ( args.time, tv )
	  cur_results = results[ ndx ]
	  ndx += 1

	  for ds_name, pair in sorted( cur_results.iteritems() ):
	    print '\n[%s, %s=%.3f]' % ( ds_name, args.time, tv )
	    print '  [interpolation]\n', str( pair[ 0 ] )
	    print '\n  [diff]\n', str( pair[ 1 ] )
	  #end for ds_name, pair
	#end for tv
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
