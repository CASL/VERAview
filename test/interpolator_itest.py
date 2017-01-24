#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		interpolator_itest.py				-
#	HISTORY:							-
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
  def __init__( self, data_model ):
    core = data_model.GetCore()
    src_shape = ( core.npiny, core.npinx, core.nax, core.nass )

    pitch = core.GetAssemblyPitch()
    src_axial_mesh = core.axialMesh

    mesh_min = src_axial_mesh[ 0 ] + 10.0
    mesh_max = max( src_axial_mesh[ -1 ] - 10.0, mesh_min + 10.0 )
    dst_axial_mesh = np.linspace(
	mesh_min, mesh_max,
	src_axial_mesh.shape[ 0 ] >> 1
        )
    dst_shape = (
	core.npiny, core.npinx,
	dst_axial_mesh.shape[ 0 ] - 1,
	core.nass
        )

    self.fDataModel = data_model
    self.fInterpolator = Interpolator(
        src_shape, pitch, src_axial_mesh,
	dst_shape, pitch, dst_axial_mesh,
	core.nass, self._Callback
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest._Callback()			-
  #----------------------------------------------------------------------
  def _Callback( self, message, progress ):
    print >> sys.stderr, '[interpolator_itest]', message
  #end _Callback


  #----------------------------------------------------------------------
  #	METHOD:		InterpolatorITest.Interpolate()			-
  #----------------------------------------------------------------------
  def Interpolate( self, ds_name ):
    result = None
    dset = self.fDataModel.GetStateDataSet( 0, ds_name )
    if dset is not None:
      result = self.fInterpolator.interpolate( np.array( dset ), ds_name )

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
      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input HDF5 file'
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      #if args.dataset is None or args.file is None:
      if args.file is None or not args.datasets:
	parser.print_help()

      else:
#			-- Must have valid data
#			--
        data_model = DataModel( args.file )
	test = InterpolatorITest( data_model )

	for ds_name in args.dataset:
	  print '\n[' + ds_name + ']'
	  result = test.Interpolate( ds_name )
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
