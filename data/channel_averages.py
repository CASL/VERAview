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
  def calc_average( self, dset, avg_axis ):
    """
@param  dset		h5py.Dataset object
@param  avg_axis	axis for averaging
@return			calculated average np.ndarray, or None if averages
			cannot be calculated for this dataset
"""
    avg = None
    factor_weights = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
	factor_weights = None
        #avg_weights = np.ones( avg_axis, dtype = int )

	if 'factor' in dset.attrs:
          factor_obj = dset.attrs[ 'factor' ]
	  factor_name = \
	      factor_obj[ 0 ] if isinstance( factor_obj, np.ndarray ) else \
	      str( factor_obj )

	  factor_weights = self.core.group.get( factor_name )
	  if factor_weights is not None and len( factor_weights.shape ) != 4:
	    factor_weights = None
	  #if factor_weights is not None and len( factor_weights.shape ) == 4:
          #  avg_weights = np.sum( factor_weights, axis = avg_axis )
	#end if 'factor'

	if factor_weights is None:
          factor_weights = np.ones(
	      ( self.core.nchany, self.core.nchanx,
	        self.core.nax, self.core.nass ),
	      dtype = np.float64
	      )
	  for x in xrange( 0, self.core.nchanx ):
	    factor_weights[ 0 , x, :, : ] *= 0.5
	    factor_weights[ self.core.nchany - 1, x, :, : ] *= 0.5
	  for y in xrange( 0, self.core.nchany ):
	    factor_weights[ y , 0, :, : ] *= 0.5
	    factor_weights[ y , self.core.nchanx - 1, :, : ] *= 0.5

	  for k in xrange( self.core.nax ):
	    factor_weights[ :, :, k, : ] *= \
	        (self.core.axialMesh[ k + 1 ] - self.core.axialMesh[ k ])
	#end if factor_weights is None

#xxxxx Might need to *NOT* half symmetry line weights when COBRA-TF fixes
	self.fix_weights( self.core, factor_weights )

        avg_weights = np.sum( factor_weights, axis = avg_axis )
	#dset.value is deprecated
	ds_array = np.array( dset )
	avg = np.sum( ds_array * factor_weights, axis = avg_axis ) / avg_weights
	if len( avg.shape ) > 0:
          avg[ avg == np.inf ] = 0.0
	avg = np.nan_to_num( avg )
      finally:
	np.seterr( **errors_save )
    #end if

    return  avg, factor_weights
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
    return  self.calc_average( dset, 2 )
  #end calc_channel_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		fix_weights()					-
  #----------------------------------------------------------------------
  def fix_weights( self, core, wts ):
    """Zero outside the line of symmetry.
"""
    if core.coreSym == 4:
      mass = core.nassx / 2
      mpin = core.nchanx / 2
      odd = core.nchanx % 2 == 1
      pxlo = np.zeros( [ core.nass ], dtype = int )
      pylo = np.zeros( [ core.nass ], dtype = int )
#			-- Assemblies on the line of symmetry start at the
#			-- middle channel
      for i in xrange( mass, core.nassx ):
        pxlo[ core.coreMap[ i, mass ] - 1 ] = mpin
        pylo[ core.coreMap[ mass, i ] - 1 ] = mpin

      for i in xrange( mass, core.nassx ):
	assy_ndx = core.coreMap[ mass, i ] - 1
	if assy_ndx >= 0:
	  wts[ 0 : pylo[ assy_ndx ], 0 : core.nchanx, :, assy_ndx ] = 0.0
	  if odd:
	    wts[ pylo[ assy_ndx ], 0 : core.nchanx, :, assy_ndx ] *= 0.5
      #end for i

      for j in xrange( mass, core.nassy ):
	assy_ndx = core.coreMap[ j, mass ] - 1
	if assy_ndx >= 0:
          wts[ 0 : core.nchany, 0 : pxlo[ assy_ndx ], :, assy_ndx ] = 0.0
	  if odd:
            wts[ 0 : core.nchany, pxlo[ assy_ndx ], :, assy_ndx ] *= 0.5
      #end for j
    #end if core.coreSym
   
    return  wts
  #end fix_weights


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
