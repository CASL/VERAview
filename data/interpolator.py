#------------------------------------------------------------------------
#	NAME:		interpolator.py					-
#	HISTORY:							-
#		2016-11-04	leerw@ornl.gov				-
#		2016-10-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys, timeit
import numpy as np
from scipy.interpolate import griddata
import pdb


#------------------------------------------------------------------------
#	CLASS:		Interpolator					-
#------------------------------------------------------------------------
class Interpolator( object ):


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, src_data, name = '' ):
    return  self.interpolate( src_data, name )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self,
      src_shape, src_pitch, src_axial_mesh_centers,
      dst_shape, dst_pitch, dst_axial_mesh_centers,
      nass, listener = None
      ):
    """Sets up the interpolation grid for future calls to the
Interpolate() method.  For now we only do 4D shapes and assume identical
core_maps.

others are TBD.  It is
assumed that none of the parameters are None.  Otherwise you will get an
exception.

@param  src_shape	source dataset shape
@param  src_pitch	source assembly pitch
@param  src_axial_mesh_centers  source axial mesh np.ndarray
@param  dst_shape	destination dataset shape
			(must have the same size for axis == 3 as src_shape
@param  dst_pitch	destination assembly pitch
@param  dst_axial_mesh_centers  destination axial mesh np.ndarray
@param  nass		number of assemblys for src and dst
@param  listener	optional callable to invoke with progress, prototype
			callback( message, progress_value ), where
			progress_value is [0,100]
"""
#		-- Assertions
#		--
    assert len( src_shape ) == 4 and len( dst_shape ) == 4, \
        'only 4D shapes are supported'
    assert src_shape[ 3 ] == dst_shape[ 3 ], \
        'shapes must match size on axis == 3'

    assert 0 not in src_shape, 'src_shape has 0-sized dimension'
    assert 0 not in dst_shape, 'dst_shape has 0-sized dimension'

    self.listeners = []
    if listener:
      self.listeners.append( listener )

#		-- Plow on
#		--
    self.srcShape = src_shape
    self.dstShape = dst_shape

#		-- X- and Y-axis grids
#		--
    src_pitch = float( src_pitch )
    src_x = np.linspace( 0.0, src_pitch, src_shape[ 1 ], False )
    src_y = np.linspace( 0.0, src_pitch, src_shape[ 0 ], False )

    dst_pitch = float( dst_pitch )
    dst_x = np.linspace( 0.0, dst_pitch, dst_shape[ 1 ], False )
    dst_y = np.linspace( 0.0, dst_pitch, dst_shape[ 0 ], False )

#		-- Axial mesh centers
#		--
#    t = np.copy( src_axial_mesh )
#    t2 = np.r_[ t, np.roll( t, -1 ) ]
#    src_ax = np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]
#
#    t = np.copy( dst_axial_mesh )
#    t2 = np.r_[ t, np.roll( t, -1 ) ]
#    dst_ax = np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]

#		-- Build interpolation coordinates
#		--
    self.srcCoords = []
    for y in src_y:
      for x in src_x:
        for z in src_axial_mesh_centers:
	  self.srcCoords.append( [ y, x, z ] )
#	  for i in xrange( nass ):
#	    self.srcCoords.append( [ y, x, z, i ] )

    self.dstCoords = []
    for y in dst_y:
      for x in dst_x:
        for z in dst_axial_mesh_centers:
	  self.dstCoords.append( [ y, x, z ] )
#	  for i in xrange( nass ):
#	    self.dstCoords.append( [ y, x, z, i ] )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		add_listeners()					-
  #----------------------------------------------------------------------
  def add_listeners( self, *listeners ):
    """Adds listeners/callbacks.  Listeners are callables invoked with
prototype callback( message, progress_value ), where progress_value is
in range [0,100], 100 indicating completion.
@param  listeners	one or more listeners to add
"""
    if listeners:
      for l in listeners:
        if l and hasattr( l, '__callable__' ) and l not in self.listeners:
	  self.listeners.append( l )
      #end for
    #end if
  #end add_listeners


  #----------------------------------------------------------------------
  #	METHOD:		interpolate()					-
  #----------------------------------------------------------------------
  def interpolate( self, src_data, name = '' ):
    """
@param  src_data	np.ndarray of self.srcShape
@param  name		optional name to use in callback messages
@return			interpolated np.ndarray of self.dstShape
"""
    start_time = timeit.default_timer()

    nass = self.srcShape[ 3 ]
    progress = 0
    result = np.zeros( self.dstShape, dtype = np.float64 )

    for assy_ndx in xrange( nass ):
      progress = int( 100 * assy_ndx / nass )
      message = 'Processing %s (%d%%)' % ( name, progress )
      self.notify_listeners( message, progress )

      src_data_slice = src_data[ :, :, :, assy_ndx ]
      src_data_flat = src_data_slice.flatten()
      result_data = \
          griddata( self.srcCoords, src_data_flat, self.dstCoords, 'linear' )
      result_data_shaped = result_data.reshape( *self.dstShape[ 0 : 3 ] )
      result[ :, :, :, assy_ndx ] = result_data_shaped
    #end for assy_ndx

    message = 'Processing %s complete (100%%)' % name
    self.notify_listeners( message, 100 )
    elapsed_time = timeit.default_timer() - start_time
    print >> sys.stderr, '[interpolate] time=%.3fs' % elapsed_time

    return  result
  #end interpolate


  #----------------------------------------------------------------------
  #	METHOD:		notify_listeners()				-
  #----------------------------------------------------------------------
  def notify_listeners( self, message, progress ):
    """Invokes listener.
"""
    for l in self.listeners:
      l( message, progress )
  #end notify_listeners


  #----------------------------------------------------------------------
  #	METHOD:		remove_listeners()				-
  #----------------------------------------------------------------------
  def remove_listeners( self, *listeners ):
    """Removes listeners/callbacks.
@param  listeners	one or more listeners to remove
"""
    if listeners:
      for l in listeners:
        if l and l in self.listeners:
	  self.listeners.remove( l )
      #end for
    #end if
  #end remove_listeners

#end Interpolator
