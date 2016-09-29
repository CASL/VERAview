#------------------------------------------------------------------------
#	NAME:		channel_averages.py				-
#	HISTORY:							-
#		2016-09-29	leerw@ornl.gov				-
#	  Implementing calc_average().
#		2016-09-14	leerw@ornl.gov				-
#	  Building from Bob's directions on #3996.
#------------------------------------------------------------------------
import h5py, os, sys
import numpy as np
import pdb


#------------------------------------------------------------------------
#	CLASS:		Averages					-
#------------------------------------------------------------------------
class Averages( object ):


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, *args ):
    """Calls load() if the arguments are provided.  Otherwise load() must
be called before use.
@param  args		optional args
          core		  datamodel.Core
"""
    if len( args ) > 0:
      self.load( *args )
    else:
      self.core = None
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_average()					-
  #----------------------------------------------------------------------
  def calc_average( self, dset, avg_axis, **errors_args ):
    """
@param  dset		h5py.Dataset object
@param  avg_axis	axis for averaging
@return			calculated average np.ndarray, or None if averages
			cannot be calculated for this dataset
"""
    avg = None
    if dset is not None:
      if errors_args:
        errors_save = np.seterr( **errors_args )
        #errors = np.seterr( invalid = 'ignore' )
      try:
        avg_weights = np.ones( avg_axis, dtype = int )

	if 'factor' in dset.attrs:
          factor_obj = dset.attrs[ 'factor' ]
	  factor_name = \
	      factor_obj[ 0 ] if isinstance( factor_obj, np.ndarray ) else \
	      str( factor_obj )

	  factor_weights = self.core.get( factor_name )
	  if factor_weights is not None and len( factor_weights.shape ) == 4:
            avg_weights = np.sum( factor_weights, axis = avg_axis )
	#end if 'factor'

	avg = np.sum( data * avg_weights, axis = avg_axis ) / avg_weights
	avg = np.nan_to_num( avg )
      finally:
	if errors_args:
          np.seterr( **errors_save )
    #end if

    return  avg
  #end calc_average


  #----------------------------------------------------------------------
  #	METHOD:		calc_channel_assembly_avg()			-
  #----------------------------------------------------------------------
  def calc_channel_assembly_avg( self, dset ):
#    assembly_weights = np.sum( pin_weights, axis = ( 0, 1 ) )
    return  self.calc_average( dset, ( 0, 1 ) )
  #end calc_channel_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_channel_axial_avg()			-
  #----------------------------------------------------------------------
  def calc_channel_axial_avg( self, dset ):
    return  self.calc_average( dset, ( 0, 1, 3 ) )
  #end calc_channel_axial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_channel_core_avg()				-
  #----------------------------------------------------------------------
  def calc_channel_core_avg( self, dset ):
    return  self.calc_average( dset, ( 0, 1, 2, 3 ) )
  #end calc_channel_core_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_channel_radial_assembly_avg()		-
  #----------------------------------------------------------------------
  def calc_channel_radial_assembly_avg( self, dset ):
    return  self.calc_average( dset, ( 0, 1, 2 ) )
  #end calc_channel_radial_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_channel_radial_avg()			-
  #----------------------------------------------------------------------
  def calc_channel_radial_avg( self, dset ):
    return  self.calc_average( dset, 2, invalid = 'ignore' )
  #end calc_channel_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		load()						-
  #----------------------------------------------------------------------
  def load( self, core ):
    """
@param  core		datamodel.Core object with properties
			  axialMesh, axialMeshCenters, coreMap, coreSym,
			  nass, nassx, nassy, nax, npin, pinVolumes
"""
    self.core = core
  #end load

#end Averages
