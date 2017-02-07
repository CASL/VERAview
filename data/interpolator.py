#------------------------------------------------------------------------
#	NAME:		interpolator.py					-
#	HISTORY:							-
#		2017-02-06	leerw@ornl.gov				-
#	  New approach from Andrew and Ben.
#		2016-11-04	leerw@ornl.gov				-
#		2016-10-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys, timeit
import numpy as np
from scipy.interpolate import interp1d
from scipy import array, integrate
import pdb


#------------------------------------------------------------------------
#	CLASS:		Interpolator					-
#------------------------------------------------------------------------
class Interpolator( object ):
  """
"""


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, src_data, name = '' ):
    return  self.interpolate( src_data, name )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, src_mesh_centers, dst_mesh, listener = None ):
    """Sets up to interpolate within a single state point.
It is assumed that none of the parameters are None.  Otherwise you will get an
exception.

@param  src_mesh_centers  axial mesh centers (np.ndarray)
@param  dst_mesh	result mesh, not centers (np.ndarray)
@param  listener	optional callable to invoke with progress, prototype
			callback( message, progress_value ), where
			progress_value is [0,100]
"""
#		-- Assertions
#		--
    assert src_mesh_centers is None or len( src_mesh_centers ) == 0, \
        'src_mesh_centers cannot be empty'
    assert dst_mesh is None or len( dst_mesh ) < 2, \
        'dst_mesh must have length ge 2'

    self.listeners = []
    if listener:
      self.listeners.append( listener )

#		-- Plow on
#		--
    self.srcMeshCenters = src_axial_mesh_centers
    self.dstMesh = dst_axial_mesh

    if isinstance( src_data, h5py.Dataset ):
      src.srcData = np.array( src_data )
    else:
      src.srcData = src_data

    dst_shape = list( src_dset.shape )
    dst_shape[ axial_axis ] = len( dst_axial_mesh ) - 1

    #self.dstData = np.ndarray( dst_shape, dtype = np.float64 )
    self.dstData = np.zeros( dst_shape, dtype = np.float64 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		add_listeners()					-
  #----------------------------------------------------------------------
  def add_listeners( self, *listeners ):
    """Adds listeners/callbacks.  Listeners are callables invoked with
parameters ( cur_step, total_steps ).
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
  #	METHOD:		create_interpolator()				-
  #----------------------------------------------------------------------
  def create_interpolator( self, xs, ys ):
    f_s = interp1d( xs, ys, 'cubic' )

    def get_y( x ):
      if x < xs[ 0 ]:
	if len( xs ) < 2 or len( ys ) < 2:
	  y = ys[ 0 ]
	else:
	  y = ys[ 0 ] + \
	      (x - xs[ 0 ]) * (ys[ 1 ] - ys[ 0 ]) / (xs[ 1 ] - xs[ 0 ])
      elif x > x_values[ -1 ]:
        if len( xs ) < 2 or len( ys ) < 2:
	  y = ys[ 0 ]
        else:
	  y = ys[ -1 ] + \
	      (x - xs[ -1 ]) * (ys[ -1 ] - ys[ -2 ]) / (xs[ -1 ] - xs[ -2 ])
      else:
        y = f_s( x )
      return  y
    #end extrap_pt

    def interp_ys( xs_in ):
      return  array( [ get_y( i ) for i in xs_in ] )

    return  interp_ys
  #end create_interpolator


  #----------------------------------------------------------------------
  #	METHOD:		interpolate()					-
  #----------------------------------------------------------------------
  def interpolate( self, src_data ):
    """
@param  src_data	source dataset (h5py.Dataset or np.ndarray instance)
@return			interpolated np.ndarray with len( self.dstMesh ) -1
			axial levels
"""
#		-- Assertions
#		--
    assert src_data is not None and len( src_data.shape ) == 4, \
        'only 4D shapes are supported'

#    assert isinstance( src_data, h5py.Dataset ) or \
#        isinstance( src_data, np.ndarray ), \
#        'src_data must be a Dataset or ndarray'
    if isinstance( src_data, h5py.Dataset ):
      src_data = np.array( src_data )
    else:
      assert isintance( src_data, np.ndarray ), \
          'src_data must be a Dataset or ndarray'

    assert \
        src_data.shape[ 2 ] == len( self.srcMeshCenters ), \
        'src_data has incompatible shapes'


    start_time = timeit.default_timer()

    dst_shape = list( src_dset.shape )
    dst_shape[ 2 ] = len( self.dstMesh ) - 1

    #dst_data = np.ndarray( dst_shape, dtype = np.float64 )
    dst_data = np.zeros( dst_shape, dtype = np.float64 )

    step_count = reduce( (lambda x, y : x * y), dst_shape )
    step = 1

    for assy_ndx in xrange( dst_shape.shape[ 3 ] ):
      for pin_row in xrange( dst_shape.shape[ 0 ] ):
        for pin_col in xrange( dst_shape.shape[ 1 ] ):
          #progress = int( 100 * assy_ndx / nass )
          self.notify_listeners( step, step_count )
	  self.interpolate_slice(
	      dst_data, self.dstMesh,
	      src_data, self.srcMeshCenters,
	      assy_ndx, pin_col, pin_row
	      )
	  step += 1
        #end for x
      #end for y
    #end for assy_ndx

    elapsed_time = timeit.default_timer() - start_time
    print >> sys.stderr, '[interpolator] time=%.3fs' % elapsed_time

    return  dst_data
  #end interpolate


  #----------------------------------------------------------------------
  #	METHOD:		interpolate_slice()				-
  #----------------------------------------------------------------------
  def interpolate_slice( self,
      dst_data, dst_mesh, src_data, src_mesh_centers,
      assy_ndx, pin_col, pin_row
      ):
    """Interpolates a single slice.
"""
    f_e = self.create_interpolator(
        src_mesh_centers,
	src_data[ pin_row, pin_col, :, assy_ndx ]
	)

    for k in xrange( len( dst_mesh ) - 1 ):
      a = dst_mesh[ k ]
      b = dst_mesh[ k + 1 ]
      dst_data[ pin_row, pin_col, k, assy_ndx ] = \
          integrate.quadrature( f_e, a, b )
    #end for k

    return  dst_data
  #end interpolate_slice


  #----------------------------------------------------------------------
  #	METHOD:		notify_listeners()				-
  #----------------------------------------------------------------------
  def notify_listeners( self, current, total ):
    """Invokes listener.
"""
    for l in self.listeners:
      l( current, total )
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
