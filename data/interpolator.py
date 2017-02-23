#------------------------------------------------------------------------
#	NAME:		interpolator.py					-
#	HISTORY:							-
#		2017-02-16	leerw@ornl.gov				-
#	  Added mode param.
#		2017-02-09	leerw@ornl.gov				-
#	  New, simple approach.
#		2017-02-06	leerw@ornl.gov				-
#	  New approach from Andrew and Ben.
#		2016-11-04	leerw@ornl.gov				-
#		2016-10-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys, time
import numpy as np
#from scipy import array, griddata, integrate, interpolate
#from scipy.interpolate import griddata, interp1d
from scipy import interpolate
import pdb


#------------------------------------------------------------------------
#	CLASS:		Interpolator					-
#------------------------------------------------------------------------
class Interpolator( object ):
  """Instances interpolate a dataset in a single state point.
"""


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    return  self.interpolate( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, src_mesh_centers, dst_mesh_centers, listener = None ):
    """Sets up for interpolation.
@param  src_mesh_centers  axial mesh centers (np.ndarray)
@param  dst_mesh_centers  result mesh centers (np.ndarray)
@param  listener	optional callable to invoke with progress, prototype
			callback( message, progress_value ), where
			progress_value is [0,100]
"""
#		-- Assertions
#		--
    assert \
        src_mesh_centers is not None and len( src_mesh_centers ) > 0 and \
        dst_mesh_centers is not None and len( dst_mesh_centers ) > 0, \
        'mesh centers cannot be empty'

#		-- Plow on
#		--
    self.listeners = []
    if listener:
      self.listeners.append( listener )

    self.srcMeshCenters = src_mesh_centers
    self.dstMeshCenters = dst_mesh_centers
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
  #	METHOD:		_create_inner_interpolator()			-
  #----------------------------------------------------------------------
  def _create_inner_interpolator(
      self, src_data, src_mesh_centers, mode = 'linear'
      ):
    """
@return		interpolator function
"""
    #print >> sys.stderr, '[create_inner_interpolator] mode=', mode

    if mode.startswith( 'cubic' ):
      #print >> sys.stderr, '[create_interpolator] CUBIC'
      f = interpolate.interp1d(
          src_mesh_centers, src_data,
	  assume_sorted = True, axis = 2,
	  bounds_error = False,
	  kind = 'cubic'
	  )

    elif mode.startswith( 'quad' ):
      #print >> sys.stderr, '[create_inner_interpolator] QUAD'
      f = interpolate.interp1d(
          src_mesh_centers, src_data,
	  assume_sorted = True, axis = 2,
	  bounds_error = False,
	  kind = 'quadratic'
	  )

    else:
      #print >> sys.stderr, '[create_inner_interpolator] LINEAR'
      f = interpolate.interp1d(
          src_mesh_centers, src_data,
	  assume_sorted = True, axis = 2
	  )

    return  f
  #end _create_inner_interpolator


  #----------------------------------------------------------------------
  #	METHOD:		create_interpolator()				-
  #----------------------------------------------------------------------
  def create_interpolator( self, src_data, src_mesh_centers, mode = 'linear' ):
    """
@return		interpolator function
"""
    f = self._create_inner_interpolator( src_data, src_mesh_centers, mode )
    x = f.x
    y = f.y

    def extrapolate( x ):
      if x < f.x[ 0 ]:
	y = \
	    (x - f.x[ 0 ]) / (f.x[ 1 ] - f.x[ 0 ]) * \
            (f.y[ :, :, 1, : ] - f.y[ :, :, 0, : ]) + \
	    f.y[ :, :, 0, : ]
      elif x > f.x[ -1 ]:
	y = \
	    (x - f.x[ -2 ]) / (f.x[ -1 ] - f.x[ -2 ]) * \
            (f.y[ :, :, -1, : ] - f.y[ :, :, -2, : ]) + \
	    f.y[ :, :, -2, : ]
      else:
        y = f( x )
      return  y
    #end extrapolate

    return  extrapolate
  #end create_interpolator


  #----------------------------------------------------------------------
  #	METHOD:		interpolate()					-
  #----------------------------------------------------------------------
  def interpolate(
      self,
      src_data,
      f = None,
      mode = 'linear',
      skip_assertions = False
      ):
    """Interpolates by finding the value on the interpolation function.
@param  src_data	source dataset (h5py.Dataset or np.ndarray instance)
@param  f		interpolator function, will be created if None
@return			interpolated np.ndarray with len( self.dstMeshCenters )
			axial levels
"""
#		-- Assertions
#		--
    if not skip_assertions:
      assert src_data is not None and len( src_data.shape ) == 4, \
          'only 4D shapes are supported'

#      assert isinstance( src_data, h5py.Dataset ) or \
#          isinstance( src_data, np.ndarray ), \
#          'src_data must be a Dataset or ndarray'
      if isinstance( src_data, h5py.Dataset ):
        src_data = np.array( src_data )
      else:
        assert isintance( src_data, np.ndarray ), \
          'src_data must be a Dataset or ndarray'

      assert \
          src_data.shape[ 2 ] == len( self.srcMeshCenters ), \
          'src_data has incompatible shape'
    #end if not skip_assertions:

    dst_shape = list( src_data.shape )
    dst_shape[ 2 ] = len( self.dstMeshCenters )

    dst_data = np.zeros( dst_shape, dtype = np.float64 )

    #step_count = reduce( (lambda x, y : x * y), dst_shape )
    #step_count = dst_shape[ 3 ]
    #step = 1

    if f is None:
      f = self.create_interpolator( src_data, self.srcMeshCenters, mode )

    for k in xrange( dst_shape[ 2 ] ):
      dst_data[ :, :, k, : ] = f( self.dstMeshCenters[ k ] )

    return  dst_data
  #end interpolate


  #----------------------------------------------------------------------
  #	METHOD:		interpolate_integral()				-
  #----------------------------------------------------------------------
  def interpolate_integral(
      self,
      src_data,
      f = None,
      mode = 'linear',
      skip_assertions = False
      ):
    """Interpolates by integrating over the interpolation function.
@param  src_data	source dataset (h5py.Dataset or np.ndarray instance)
@param  f		interpolator function, will be created if None
@return			interpolated np.ndarray with len( self.dstMeshCenters )
			axial levels
"""
#		-- Assertions
#		--
    if not skip_assertions:
      assert src_data is not None and len( src_data.shape ) == 4, \
          'only 4D shapes are supported'

#      assert isinstance( src_data, h5py.Dataset ) or \
#          isinstance( src_data, np.ndarray ), \
#          'src_data must be a Dataset or ndarray'
      if isinstance( src_data, h5py.Dataset ):
        src_data = np.array( src_data )
      else:
        assert isintance( src_data, np.ndarray ), \
          'src_data must be a Dataset or ndarray'

      assert \
          src_data.shape[ 2 ] == len( self.srcMeshCenters ), \
          'src_data has incompatible shape'
    #end if not skip_assertions:

    dst_shape = list( src_data.shape )
    dst_shape[ 2 ] = len( self.dstMeshCenters )

    dst_data = np.zeros( dst_shape, dtype = np.float64 )

    #step_count = reduce( (lambda x, y : x * y), dst_shape )
    #step_count = dst_shape[ 3 ]
    #step = 1

    if f is None:
      f = self.create_interpolator( src_data, self.srcMeshCenters, mode )

#    for k in xrange( dst_shape[ 2 ] ):
#      dst_data[ :, :, k, : ] = f( self.dstMeshCenters[ k ] )
    left_ndx = 0
    for k in xrange( dst_shape[ 2 ] ):
      dst_z = self.dstMeshCenters[ k ]
      while left_ndx < len( self.srcMeshCenters ) - 1 and \
          self.srcMeshCenters[ left_ndx + 1 ] <= dst_z:
        left_ndx += 1

      left = self.srcMeshCenters[ left_ndx ]

      avg_dist = abs( left - dst_z ) / ((left + dst_z) / 2.0)
      #if left == dst_z:
      if avg_dist < 0.01:
        dst_data[ :, :, k, : ] = src_data[ :, :, left_ndx, : ]

      elif left > dst_z or left_ndx == len( self.srcMeshCenters ) - 1:
        dst_data[ :, :, k, : ] = f( dst_z )

      else:
	f_dst_z = f( dst_z )
	right_ndx = left_ndx + 1
	right = self.srcMeshCenters[ right_ndx ]
	d1 = dst_z - left
	d2 = right - dst_z
	term1 = (d1 / 2.0) * (f_dst_z - src_data[ :, :, left_ndx, : ])
	term2 = (d2 / 2.0) * (src_data[ :, :, right_ndx, : ] - f_dst_z)
	#dst_data[ :, :, k, : ] = ((d1 * term1) + (d2 * term2)) / (d1 + d2)
	w1 = d1 / (d1 + d2)
	w2 = d2 / (d1 + d2)
	dst_data[ :, :, k, : ] = (w1 * term1) + (w2 * term2)
    #end for k

    return  dst_data
  #end interpolate_integral


  #----------------------------------------------------------------------
  #	METHOD:		interpolate_no1()				-
  #----------------------------------------------------------------------
  def interpolate_no1(
      self,
      src_data,
      f = None,
      mode = 'linear',
      skip_assertions = False
      ):
    """Interpolates by integrating over the interpolation function.
@param  src_data	source dataset (h5py.Dataset or np.ndarray instance)
@param  f		interpolator function, will be created if None
@return			interpolated np.ndarray with len( self.dstMeshCenters )
			axial levels
"""
#		-- Assertions
#		--
    if not skip_assertions:
      assert src_data is not None and len( src_data.shape ) == 4, \
          'only 4D shapes are supported'

#      assert isinstance( src_data, h5py.Dataset ) or \
#          isinstance( src_data, np.ndarray ), \
#          'src_data must be a Dataset or ndarray'
      if isinstance( src_data, h5py.Dataset ):
        src_data = np.array( src_data )
      else:
        assert isintance( src_data, np.ndarray ), \
          'src_data must be a Dataset or ndarray'

      assert \
          src_data.shape[ 2 ] == len( self.srcMeshCenters ), \
          'src_data has incompatible shape'
    #end if not skip_assertions:

    dst_shape = list( src_data.shape )
    dst_shape[ 2 ] = len( self.dstMeshCenters )

    dst_data = np.zeros( dst_shape, dtype = np.float64 )

    #step_count = reduce( (lambda x, y : x * y), dst_shape )
    #step_count = dst_shape[ 3 ]
    #step = 1

    if f is None:
      f = self.create_interpolator( src_data, self.srcMeshCenters, mode )

#    for k in xrange( dst_shape[ 2 ] ):
#      dst_data[ :, :, k, : ] = f( self.dstMeshCenters[ k ] )
    left_ndx = 0
    for k in xrange( dst_shape[ 2 ] ):
      dst_z = self.dstMeshCenters[ k ]
      while left_ndx < len( self.srcMeshCenters ) - 1 and \
          self.srcMeshCenters[ left_ndx + 1 ] <= dst_z:
        left_ndx += 1

      left = self.srcMeshCenters[ left_ndx ]
      right = None

      avg_dist = abs( left - dst_z ) / ((left + dst_z) / 2.0)
      #if left == dst_z:
      if avg_dist < 0.01:
        pass

      elif left > dst_z:
	if left_ndx < len( self.srcMeshCenters ) - 1:
	  next_x = self.srcMeshCenters[ left_ndx + 1 ]
	  temp = left - (next_x - left)
	  right = left
	  left = temp

      elif left_ndx == len( self.srcMeshCenters ) - 1:
        if left_ndx > 0:
	  prev_x = self.srcMeshCenters[ left_ndx - 1 ]
	  right = left + left - prev_x

      else:
        right = self.srcMeshCenters[ left_ndx + 1 ]

      if right is None:
        dst_data[ :, :, k, : ] = f( left )

      else:
	#result = integrate.quadrature( f, left, right )
        #dst_data[ :, :, k, : ] = result[ 0 ] / (right - left)
	# Gaussian quadrature integration, f is the approximating polynomial
	# w_i are relative distances
	d1 = dst_z - left
	d2 = right - dst_z
	w1 = d1 / (d1 + d2)
	w2 = d2 / (d1 + d2)
	h = (right - left) / 2.0
	f_dst_z = f( dst_z )
	term1 = d1 * (f_dst_z + f( left )) / (d1 + d2)
	term2 = d2 * (f( right ) + f_dst_z ) / (d1 + d2)
	dst_data[ :, :, k, : ] = term1 + term2
    #end for k

    return  dst_data
  #end interpolate_no1


  #----------------------------------------------------------------------
  #	METHOD:		interpolate_no2()				-
  #----------------------------------------------------------------------
  def interpolate_no2(
      self,
      src_data,
      f = None,
      mode = 'linear',
      skip_assertions = False
      ):
    """Interpolates by integrating over the interpolation function.
@param  src_data	source dataset (h5py.Dataset or np.ndarray instance)
@param  f		interpolator function, will be created if None
@return			interpolated np.ndarray with len( self.dstMeshCenters )
			axial levels
"""
#		-- Assertions
#		--
    if not skip_assertions:
      assert src_data is not None and len( src_data.shape ) == 4, \
          'only 4D shapes are supported'

#      assert isinstance( src_data, h5py.Dataset ) or \
#          isinstance( src_data, np.ndarray ), \
#          'src_data must be a Dataset or ndarray'
      if isinstance( src_data, h5py.Dataset ):
        src_data = np.array( src_data )
      else:
        assert isintance( src_data, np.ndarray ), \
          'src_data must be a Dataset or ndarray'

      assert \
          src_data.shape[ 2 ] == len( self.srcMeshCenters ), \
          'src_data has incompatible shape'
    #end if not skip_assertions:

    dst_shape = list( src_data.shape )
    dst_shape[ 2 ] = len( self.dstMeshCenters )
    dst_data = np.zeros( dst_shape, dtype = np.float64 )

#    points = self.srcMeshCenters
#    values = np.array( src_data )
#    xi = self.dstMeshCenters
#    dst_data = griddata( points, values, xi, method = mode )

    return  dst_data
  #end interpolate_no2


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
