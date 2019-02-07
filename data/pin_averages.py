#------------------------------------------------------------------------
#	NAME:		pin_averages.py					-
#	HISTORY:							-
#		2018-08-17	godfreyat@ornl.gov			-
#	  Unsuccessful experimentation with calc_max().
#		2018-05-25	godfreyat@ornl.gov			-
#	  Fixed calc_axial_offset() to survive all zero weights.
#		2018-05-21	godfreyat@ornl.gov			-
#		2018-05-20	godfreyat@ornl.gov			-
#	  Added calc_{max,min}(), renamed calc_average() to calc_avg() for
#	  naming consistency.
#		2018-02-10	godfreyat@ornl.gov			-
#	  Beginning migration to multiple functions in addition to average,
#	  max, min, stddev, abs max, sum, weighted sum, rms, index
#	  (all but max, min, sum weighted)
#		2017-08-21	godfreyat@ornl.gov			-
# 	  Fixing _calc_weights() to make the middle (line of symmetry)
#	  pin index 0 for an even number of assemblies (lines 453-4).
#		2017-03-07	godfreyat@ornl.gov			-
#	  Checking "factor" attribute, defaulting to self.pinWeights in
#	  calc_average().
#		2016-11-23	godfreyat@ornl.gov			-
#	  New calc_pin_radial_node_avg() implementation.
#		2016-10-04	leerw@ornl.gov				-
#	  Adding radialNodeWeights and and calc_pin_radial_node_avg()
#	  to pin_averages.py.
#		2016-10-01	godfreyat@ornl.gov			-
#	  Fixed _calc_node_weights() and calc_pin_node_avg().
#		2016-09-30	leerw@ornl.gov				-
#	  Revised _calc_weights() as per Andrew's guidance.
#	  Added assemblyNodeWeights, nodeWeights, and _calc_node_weights().
#		2016-09-14	leerw@ornl.gov				-
#	  Passing pin_factors params to load() and _calc_weights().
#	  Passing dataset as parameter to calc methods instead of
#	  dataset.value.
#		2016-08-30	leerw@ornl.gov				-
#	  In calc_average(), added np.nan_to_num() call to avoid having
#	  NaN values.
#	  Renamed what was "core" to "radial assembly" as per Andrew's
#	  instructions, added "core" with shape ( 1, ).
#		2016-02-15	leerw@ornl.gov				-
#	  Re-fitting to use VERAView DataModel.
#		2016-01-28	godfreyam@ornl.gov			-
#------------------------------------------------------------------------
import bisect, h5py, os, six, sys
import numpy as np
import pdb


#------------------------------------------------------------------------
#	CLASS:		Averages					-
#------------------------------------------------------------------------
class Averages( object ):
  """
      pin    channel
         \     /
          node -> radial, axial
	    |
         assembly -> assembly-radial,...
	    |
          core

For channel: have attribute or defaults
For pin: have attribute, or pin_factors, or defaults
Final step is dz weighting
"""


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, *args ):
    """Calls load() if the arguments are provided.  Otherwise load() must
be called before use.
@param  args		optional args
          core		  datamodel.Core
	  pin_powers	  reference pin_powers np.ndarray
	  pin_factors	  optional already-computed factors
"""
    self.fDict = {}
    if len( args ) >= 2:
      self.load( *args )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_aggregate()				-
  #----------------------------------------------------------------------
  def calc_aggregate( self, dset, dset_factors, agg_axis, agg_weights, func ):
    """Applies an aggregation function (e.g., avg, sum, stddev) after
retrieving or if necessary calculating factor weights.  The ``agg_weights``
are to be the denominator for weighted aggregations.  The ``func`` param
is a function returning the resulting array that is passed the dataset
np.ndarray, the factor_weights np.ndarray, the axis int or tuple, and
``agg_weights``.

    Args:
        dset (h5py.Dataset): Dataset being aggregated.
	dset_factors (np.ndarray): If agg_weights is not None, factors to
	    apply to ``dset`` before
	    averaging, None to default to "pinWeights".  Note a "factor"
	    attribute on ``dset`` overrides this parameter.
	agg_axis (int or tuple): Axis across which the aggregation is to occur.
	agg_weights (np.ndarray): Applied as the normalizing denominator,
	    so it must be of the correct shape to apply after aggregating
	    across ``agg_axis``.
	func (callable):
	    np.ndarray
	    func(
	        data : np.ndarray,
		factors : np.ndarray,
		axis : int or tuple,
		agg_weights : np.ndarray
		)
    Returns:
        (np.ndarray): Array resulting from the aggregation operation.
"""
    result = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
	factors = None
	if isinstance( dset, h5py.Dataset ) and \
	    dset.attrs and 'factor' in dset.attrs:
          factor_obj = dset.attrs[ 'factor' ]
	  factor_name = \
	      factor_obj[ 0 ] if isinstance( factor_obj, np.ndarray ) else \
	      str( factor_obj )

	  if self.core is not None:
	    factors = self.core.group.get( factor_name )
	  if factors is not None and len( factors.shape ) != 4:
	    factors = None
	#end if 'factor'

	if factors is None:
	  factors = self.pinWeights

	if dset_factors is not None:
	  factors = factors * dset_factors
	  agg_weights = agg_weights * np.sum( dset_factors, axis = agg_axis )

	data = np.array( dset )
	#result = np.sum( data * factor_weights, axis = agg_axis ) / agg_weights
	result = func( data, factors, agg_axis, agg_weights )

	#if len( result.shape ) > 0:
        #  result[ result == np.inf ] = 0.0
	result = np.nan_to_num( result )
      finally:
	np.seterr( **errors_save )
    #end if

    return  result
  #end calc_aggregate


  #----------------------------------------------------------------------
  #	METHOD:		calc_avg()					-
  #----------------------------------------------------------------------
  def calc_avg( self, dset, weights_name, avg_axis ):
    """Calls ``pin_averages.Averages.calc_aggregate()`` with a weighted
averaging function.
    Args:
        dset (h5py.Dataset): Dataset instance.
	weights_name (str): name of normal weights to apply.
	avg_axis (int or tuple): axes across which to calc the average
    Returns:
        np.ndarray: average dataset
    Raises:
        AssertionError: if ``weights_name`` is not found

Not quite:
  \\frac
    { sum{ x_y * x_factors * x_initial_mass } }
    { sum{ x_factors * x_initial_mass } }
"""
    weights = self.fDict.get( weights_name )
    assert weights is not None, 'Weights not found: ' + weights_name

#    dset_factors = None
#    if dset.name.endswith( '_exposures' ):
#      exp_name = self._get_exposure_name( weights_name )
#      exp_weights = self.fDict.get( exp_name )
#      dset_factors = self.fDict.get( 'initialMass' )
#      if exp_weights is not None and dset_factors is not None:
#        weights = exp_weights
    weights, dset_factors = \
        self._resolve_weights_and_factors( dset, weights_name )

    return \
    self.calc_aggregate(
        dset, dset_factors, avg_axis, weights,
	lambda d, f, a, w: np.sum( d * f, axis = a ) / w
	)
  #end calc_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_axial_offset()				-
  #----------------------------------------------------------------------
  def calc_axial_offset( self, pin_powers_dset ):
    """
"""
    axial_mesh = self.core.axialMesh
    if len( axial_mesh ) <= 2:
      result = 0.0

    else:
      weights = self.fDict.get( 'pinWeights' )
      pin_data = np.array( pin_powers_dset )
      inside_shape = list( pin_data.shape )
      inside_shape[ 2 ] = len( axial_mesh ) - 1

      power_top = power_bot = 0.0
      axial_middle = (axial_mesh[ 0 ] + axial_mesh[ -1 ]) / 2.0
      kmid = bisect.bisect_left( axial_mesh, axial_middle )
      for k in range( len( axial_mesh ) - 1 ):
        cur_weights = weights[ :, :, k, : ]
        cur_sum = np.sum( pin_data[ :, :, k, : ] * cur_weights )
        if axial_mesh[ k + 1 ] <= axial_middle:
          power_bot += cur_sum
        elif axial_mesh[ k ] < axial_middle:
          bottom_fraction = \
              (axial_middle - axial_mesh[ k ]) / \
              (axial_mesh[ k + 1 ] - axial_mesh[ k ] )
          power_bot += cur_sum * bottom_fraction
          power_top += cur_sum * (1.0 - bottom_fraction)
        else:
          power_top += cur_sum

      total_sum = np.sum( pin_data[:] * weights )
      result = (power_top - power_bot) / (power_top + power_bot) * 100.0
    #end else

    return  result
  #end calc_axial_offset


  #----------------------------------------------------------------------
  #	METHOD:		calc_axial_offset_orig()                        -
  #----------------------------------------------------------------------
  def calc_axial_offset_orig( self, pin_powers_dset ):
    """
"""
    axial_mesh = self.core.axialMesh
    weights = self.fDict.get( 'pinWeights' )
    pin_data = np.array( pin_powers_dset )
    inside_shape = list( pin_data.shape )
    inside_shape[ 2 ] = len( axial_mesh ) - 1

    axial_powers = []
    for k in range( len( axial_mesh ) - 1 ):  # pin_data.shape[ 2 ]
      cur_weights = weights[ :, :, k, : ]
      cur_weights_sum = cur_weights.sum()
      if cur_weights_sum == 0.0:
	cur_powers = np.zeros( inside_shape )
        axial_powers.append( 0.0 )
      else:
	cur_powers = \
	    np.sum( pin_data[ :, :, k, : ] * cur_weights ) / cur_weights_sum
      axial_powers.append( cur_powers )

    #xxxx account for 0s at top and bottom, ignore them
    if len( axial_mesh ) <= 2:
      result = axial_powers[ 0 ] * (axial_mesh[ 1 ] - axial_mesh[ 0 ])

    else:
      axial_middle = (axial_mesh[ 0 ] + axial_mesh[ -1 ]) / 2.0
      kmid = bisect.bisect_left( axial_mesh, axial_middle )

      if axial_middle == axial_mesh[ kmid ]:
        bot_en = top_st = kmid
      else:
        bot_en = kmid - 1
        top_st = kmid + 1

      power_top = power_bot = 0.0
      for k in range( bot_en ):
        #print k, axial_powers[ k ], axial_mesh[ k ], axial_mesh[ k + 1 ]
        power_bot += axial_powers[ k ] * (axial_mesh[ k + 1 ] - axial_mesh[ k ])

      for k in range( top_st, len( axial_mesh ) - 1 ):
        power_top += \
	    axial_powers[ k ] * (axial_mesh[ k + 1 ] - axial_mesh[ k ] )

      if top_st != bot_en:
        power_bot += axial_powers[ kmid ] * (axial_middle - axial_mesh[ kmid ])
        power_top += \
	    axial_powers[ kmid ] * (axial_mesh[ top_st ] - axial_middle)

      result =  (power_top - power_bot) / (power_top + power_bot) * 100.0
    #end else not len( axial_mesh ) <= 2

    return  result
  #end calc_axial_offset_orig


  #----------------------------------------------------------------------
  #	METHOD:		calc_core_exposure()				-
  #----------------------------------------------------------------------
  def calc_core_exposure( self, pin_exposures_dset ):
    """
"""
    result = 0.0
    if 'initialMass' in self.fDict:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        weights = self.fDict[ 'pinWeights' ] * self.fDict[ 'initialMass' ]
        result = np.sum( pin_exposures_dset * weights ) / np.sum( weights )
      finally:
        np.seterr( **errors_save )

    return  result
  #end calc_core_exposure


  #----------------------------------------------------------------------
  #	METHOD:		calc_max()					-
  #----------------------------------------------------------------------
  def calc_max( self, dset, weights_name, max_axis ):
    """Calls ``pin_averages.Averages.calc_aggregate()`` with a weighted
averaging function in max values across ``max_axis``.
    Args:
        dset (h5py.Dataset): Dataset instance.
	weights_name (str): name of normal weights to apply.
	max_axis (int or tuple): axes across which to take the max
        dset (h5py.Dataset): Dataset instance.
    Returns:
        np.ndarray: max values dataset
"""
    result = np.nanmax( dset, axis = max_axis )
    return  np.nan_to_num( result )
  #end calc_max


  #----------------------------------------------------------------------
  #	METHOD:		_calc_max_no()					-
  #----------------------------------------------------------------------
  def _calc_max_no( self, dset, weights_name, max_axis ):
    """Calls ``pin_averages.Averages.calc_aggregate()`` with a weighted
averaging function in max values across ``max_axis``.
    Args:
        dset (h5py.Dataset): Dataset instance.
	weights_name (str): name of normal weights to apply.
	max_axis (int or tuple): axes across which to take the max
        dset (h5py.Dataset): Dataset instance.
    Returns:
        np.ndarray: max values dataset
"""
    weights = self.fDict.get( weights_name )
    assert weights is not None, 'Weights not found: ' + weights_name

    weights, dset_factors = \
        self._resolve_weights_and_factors( dset, weights_name )

    return \
    self.calc_aggregate(
        dset, dset_factors, max_axis, weights,
	lambda d, f, a, w: np.nanmax( d, axis = a )
#	lambda d, f, a, w: np.nanmax( d * f, axis = a ) / w
	)
  #end _calc_max_no


  #----------------------------------------------------------------------
  #	METHOD:		calc_min()					-
  #----------------------------------------------------------------------
  def calc_min( self, dset, weights_name, min_axis ):
    """Calls ``pin_averages.Averages.calc_aggregate()`` with a min function.
    Args:
        dset (h5py.Dataset): Dataset instance.
	weights_name (str): name of normal weights to apply.
	min_axis (int or tuple): axes across which to take the min
    Returns:
        np.ndarray: min values dataset
"""
    d = np.copy( dset )
    d[ d == 0.0 ] = np.nan
    result = np.nanmin( d, axis = min_axis )
    return  np.nan_to_num( result )
  #end calc_min


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_assembly_weights()			-
  #----------------------------------------------------------------------
  def _calc_node_assembly_weights( self, core ):
    """
@param  core		DataModel.Core object
@return			asy_node_factors as a np.ndarray with shape
			( 4, core.npiny, core.npinx )
"""
#		-- Calculate asy node factors
#		--
    asy_node_factors = np.zeros( ( 4, core.npiny, core.npinx ) )
    mid = core.npin >> 1

#			-- Odd
    if core.npin % 2 == 1:
      asy_node_factors[ 0, 0   : mid + 1,   0   : mid + 1   ] = 1
      asy_node_factors[ 1, 0   : mid + 1,   mid : core.npin ] = 1
      asy_node_factors[ 2, mid : core.npin, 0   : mid + 1   ] = 1
      asy_node_factors[ 3, mid : core.npin, mid : core.npin ] = 1

      asy_node_factors[ :, 0 : core.npin,   mid             ] *= 0.5
      asy_node_factors[ :, mid,             0 : core.npin   ] *= 0.5

#			-- Even
    else:
      asy_node_factors[ 0, 0 : mid,         0 : mid         ] = 1
      asy_node_factors[ 1, 0 : mid,         mid : core.npin ] = 1
      asy_node_factors[ 2, mid : core.npin, 0 : mid         ] = 1
      asy_node_factors[ 3, mid : core.npin, mid : core.npin ] = 1
    #end if-else

    return  asy_node_factors
  #end _calc_node_assembly_weights


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_sum()				-
  #----------------------------------------------------------------------
  def _calc_node_sum( self, core, assy_node_weights, data ):
    """
@param  core		DataModel.Core object
@param  assy_node_weights  np.ndarray with shape ( 4, core.npiny, core.npinx )
@param  data		np.ndarray with shape ( core.nax, core.nass )
@return			np.ndarray([ w, x, y, z ])
"""
    values = \
        [ np.sum( data * assy_node_weights[ i, :, : ] ) for i in range( 4 ) ]
    return  np.array( values, dtype = np.float64 )
  #end _calc_node_sum


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_weights()				-
  #----------------------------------------------------------------------
  def _calc_node_weights( self, core, assy_node_weights, pin_weights ):
    """
@param  core		DataModel.Core object
@param  assy_node_weights  np.ndarray with shape ( 4, core.npiny, core.npinx )
@param  pin_weights	pin weights np.ndarray
@return			node weights as np.ndarray with shape
			( 4, core.nax, core.ass ) and radial node weights with
			shape ( 1, core.nax, core.nass )
"""
#		-- Node factors
#		--
    node_factors = np.zeros( ( 4, core.nax, core.nass ), dtype = np.float64 )
    for l in xrange( core.nass ):
      for k in xrange( core.nax ):
        node_factors[ :, k, l ] = self._calc_node_sum(
	    core, assy_node_weights,
	    pin_weights[ :, :, k, l ]
	    )
  
    #if quarter symmetry and odd assem
    if core.coreSym==4 and core.nassx%2==1 and core.npinx%2==1:
      mass = core.nassx / 2
      for i in xrange(mass,core.nassx):
        l=self.core.coreMap[mass,i]-1
        if l>=0:
          node_factors[2,:,l]+=node_factors[0,:,l]
          node_factors[3,:,l]+=node_factors[1,:,l]
          node_factors[0,:,l]=0
          node_factors[1,:,l]=0

        l=self.core.coreMap[i,mass]-1
        if l>=0:
          node_factors[1,:,l]+=node_factors[0,:,l]
          node_factors[3,:,l]+=node_factors[2,:,l]
          node_factors[0,:,l]=0
          node_factors[2,:,l]=0
        
    node_factors = np.nan_to_num( node_factors )
    radial_node_factors = np.sum( node_factors, axis = 1 )
    return  node_factors, radial_node_factors
  #end _calc_node_weights


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_weights2()				-
  #----------------------------------------------------------------------
  def _calc_node_weights2( self, core, pin_weights ):
    """Ignore this for now
@param  core		DataModel.Core object
@param  pin_weights	pin weights np.ndarray
@return			node weights as a np.ndarray
"""
#		-- Calculate asy node factors
#		--
    asy_node_factors = np.zeros( ( 4, core.npinx, core.npiny ) )
    mid_x = core.npinx >> 1
    mid_y = core.npiny >> 1

    if core.npinx % 2 == 1 and core.npiny % 2 == 1:
      asy_node_factors[ 0, 0 : mid_y + 1,      0 : mid_x + 1      ] = 1
      asy_node_factors[ 1, 0 : mid_y + 1,      mid_x : core.npinx ] = 1
      asy_node_factors[ 2, mid_y : core.npiny, 0 : mid_x + 1      ] = 1
      asy_node_factors[ 3, mid_y : core.npiny, mid_x : core.npinx ] = 1
      asy_node_factors[ :, 0 : core.npiny,     mid_x              ] *= 0.5
      asy_node_factors[ :, mid_y,              0 : core.npinx     ] *= 0.5

    elif core.npinx % 2 == 1:
      asy_node_factors[ 0, 0 : mid_y,          0 : mid_x + 1      ] = 1
      asy_node_factors[ 1, 0 : mid_y,          mid_x : core.npinx ] = 1
      asy_node_factors[ 2, mid_y : core.npiny, 0 : mid_x          ] = 1
      asy_node_factors[ 3, mid_y : core.npiny, mid_x : core.npinx ] = 1

    elif core.npiny % 2 == 1:
      asy_node_factors[ 0, 0 : mid_y + 1,      0 : mid_x          ] = 1
      asy_node_factors[ 1, 0 : mid_y + 1,      mid_x : core.npinx ] = 1
      asy_node_factors[ 2, mid_y : core.npiny, 0 : mid_x          ] = 1
      asy_node_factors[ 3, mid_y : core.npiny, mid_x : core.npinx ] = 1
  #end _calc_node_weights2


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_assembly_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_assembly_avg( self, dset ):
    return  self.calc_avg( dset, 'assemblyWeights', ( 0, 1 ) )
  #end calc_pin_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_assembly_max()				-
  #----------------------------------------------------------------------
  def calc_pin_assembly_max( self, dset ):
    return  self.calc_max( dset, 'assemblyWeights', ( 0, 1 ) )
  #end calc_pin_assembly_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_assembly_min()				-
  #----------------------------------------------------------------------
  def calc_pin_assembly_min( self, dset ):
    return  self.calc_min( dset, ( 0, 1 ) )
  #end calc_pin_assembly_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_avg( self, dset ):
    return  self.calc_avg( dset, 'axialWeights', ( 0, 1, 3 ) )
  #end calc_pin_axial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_max()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_max( self, dset ):
    return  self.calc_max( dset, 'axialWeights', ( 0, 1, 3 ) )
  #end calc_pin_axial_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_min()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_min( self, dset ):
    return  self.calc_min( dset, ( 0, 1, 3 ) )
  #end calc_pin_axial_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_core_avg( self, dset ):
    #return  np.average( dset, axis = None, weights = self.pinWeights )
    return  self.calc_avg( dset, 'coreWeights', ( 0, 1, 2, 3 ) )
    #return  self.calc_avg( dset, self.coreWeights, ( 0, 1, 2, 3 ) )
  #end calc_pin_core_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_max()				-
  #----------------------------------------------------------------------
  def calc_pin_core_max( self, dset ):
    return  self.calc_max( dset, 'coreWeights', ( 0, 1, 2, 3 ) )
  #end calc_pin_core_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_min()				-
  #----------------------------------------------------------------------
  def calc_pin_core_min( self, dset ):
    return  self.calc_min( dset, ( 0, 1, 2, 3 ) )
  #end calc_pin_core_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_node_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_node_avg( self, dset ):
    avg = np.zeros(
        ( 1, 4, self.core.nax, self.core.nass ),
	dtype = np.float64
	)

    errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
    try:
      for l in xrange( self.core.nass ):
        for k in xrange( self.core.nax ):
	  avg[ 0, :, k, l ] = self._calc_node_sum(
	      self.core, self.assemblyNodeWeights,
	      dset[ :, :, k, l ] * self.pinWeights[ :, :, k, l]
	      )

      avg = self._fix_node_factors( avg )
      avg /= self.nodeWeights
      avg[ avg == np.inf ] = 0.0
      avg = np.nan_to_num( avg )
    finally:
      np.seterr( **errors_save )

    return  avg
  #end calc_pin_node_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_node_max()				-
  #----------------------------------------------------------------------
  def calc_pin_node_max( self, dset ):
    result = np.nanmax( dset, axis = ( 2, 3 ) )
    return  result
  #end calc_pin_node_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_node_min()				-
  #----------------------------------------------------------------------
  def calc_pin_node_min( self, dset ):
    d = np.copy( dset )
    d[ d == 0.0 ] = np.nan
    result = np.nanmin( d, axis = ( 2, 3 ) )
    return  result
  #end calc_pin_node_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_assembly_avg()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_avg( self, dset ):
    return  self.calc_avg( dset, 'radialAssemblyWeights', ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_assembly_max()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_max( self, dset ):
    return  self.calc_max( dset, 'radialAssemblyWeights', ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_assembly_min()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_min( self, dset ):
    return  self.calc_min( dset, ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_avg( self, dset ):
    return  self.calc_avg( dset, 'radialWeights', 2 )
    #return  self.calc_avg( dset, self.radialWeights, 2 )
  #end calc_pin_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_max()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_max( self, dset ):
    return  self.calc_max( dset, 'radialWeights', 2 )
  #end calc_pin_radial_max


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_min()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_min( self, dset ):
    return  self.calc_min( dset, 2 )
  #end calc_pin_radial_min


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_node_avg()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_node_avg( self, dset ):
    errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )

    try:
      node = self.calc_pin_node_avg( dset )
      avg = np.sum( node * self.nodeWeights, axis = 2 ) / self.radialNodeWeights

      avg[ avg == np.inf ] = 0.0
      avg = np.nan_to_num( avg )
    finally:
      np.seterr( **errors_save )

    return  avg
  #end calc_pin_radial_node_avg


  #----------------------------------------------------------------------
  #	METHOD:		_calc_weights()					-
  #----------------------------------------------------------------------
  def _calc_weights( self, core, ref_pin_powers, pin_factors = None ):
    """Updates self.fDict.
    Args:
        core (DataModel.Core): Core instance.
	ref_pin_powers (np.ndarray): "pin_powers" as an array
	pin_factors (np.ndarray): optional factors to use for "pinWeights"
    Returns:
        dict: self.fDict
"""
# Get the geometry information ----------------------------------------
#map=f['CORE']['core_map']               # get core map
#ax_mesh=f['CORE']['axial_mesh']         # get axial mesh
#sym=f['CORE']['core_sym'][0]            # symmetry option
#pows=f['STATE_0001']['pin_powers']      # get sample pin powers
#nass=pows.shape[3]                      # total number of assembles
#nasx=len(map)                           # number of assemblies across the core
#mass=int(nasx/2)                        # middle assembly (assume odd)
#npin=pows.shape[0]                      # number of fuel pins
#mpin=int(npin/2)                        # middle fuel pin (assume odd)
#nax=len(ax_mesh)-1                      # number of axial planes
#pxlo=numpy.empty([nass],dtype=int)      # create arrays for loop bounds
#pylo=numpy.empty([nass],dtype=int)      # in case of quarter symmetry
#axlo=0                                  # initialize loop bounds for 
    axlo = aylo = 0
#hmid=(ax_mesh[0]+ax_mesh[-1])*0.5       # midpoint of the fuel for AO
#if sym==4:                              # for quarter symmetry
#    axlo=mass                           # start in the middle of the core
#    for i in xrange(axlo,nasx):
#        pxlo[map[i,mass]-1]=mpin        # in the assemblies on the line of 
#        pylo[map[mass,i]-1]=mpin        # symmetry, start at the middle pin
#		-- Quarter symmetry, start in the middle of the core
#		--
    if core.coreSym == 4:
      mass = massx = core.nassx >> 1
      massy = core.nassy >> 1
#      mpin = mpinx = core.npinx >> 1
#      mpiny = core.npiny >> 1
      mpin = mpinx = 0 if core.nassx % 2 == 0  else core.npinx >> 1
      mpiny = 0 if core.nassy % 2 == 0  else core.npiny >> 1
      pxlo = np.zeros( [ core.nass ], dtype = int )  # core.nassy?
      pylo = np.zeros( [ core.nass ], dtype = int )  # core.nassx?
#			-- Assemblies on the line of symmetry start at the
#			-- middle pin
      for j in xrange( massy, core.nassy ):
        pxlo[ core.coreMap[ j, massx ] - 1 ] = mpinx
      for i in xrange( massx, core.nassx ):
        pylo[ core.coreMap[ massy, i ] - 1 ] = mpiny
#			-- Start in the middle of the core
      axlo = massx
      aylo = massy

#		-- Eighth symmetry, start at the core quadrant
#		--
    elif core.coreSym == 8:
      mass = massx = core.nassx >> 2
      massy = core.nassy >> 2
      mpin = mpinx = core.npinx >> 2
      mpiny = core.npiny >> 2
      pxlo = np.zeros( [ core.nass ], dtype = int )
      pylo = np.zeros( [ core.nass ], dtype = int )
#			-- Assemblies on the line of symmetry start at the
#			-- fourth-way pin
      for j in xrange( massy, core.nassy ):
        pxlo[ core.coreMap[ j, massx ] - 1 ] = mpinx
      for i in xrange( massx, core.nassx ):
        pylo[ core.coreMap[ massy, i ] - 1 ] = mpiny
      axlo = massx
      aylo = massy

#		-- Weights provided?
#		--
    if pin_factors is not None:
      pin_weights = pin_factors

#		-- Must calculate weights
#		--
    else:
#			-- Start with zero weights
#			--
      pin_weights = np.zeros( ref_pin_powers.shape, dtype = np.float64 )
      ref_pin_powers[ np.isnan( ref_pin_powers ) ] = 0.0

#			-- Full core, weight is 1 for non-zero power
#			--
      if core.coreSym <= 1:
        np.place( pin_weights, ref_pin_powers > 0.0, 1.0 )

      else:
#				-- Initialize weights to 1 for non-zero power
#				--
        #npin = core.npin
        npinx = core.npinx
        npiny = core.npiny
        for i in xrange( core.nass ):
	  np.place(
              pin_weights[ pylo[ i ] : npiny, pxlo[ i ] : npinx, :, i ],
              ref_pin_powers[ pylo[ i ] : npiny, pxlo[ i ] : npinx, :, i ] > 0.0,
              1.0
	      )
#				-- Cut pin weights by half on line of symmetry
#				--
        for i in xrange( axlo, core.nassx ):
	  assy_ndx = core.coreMap[ massy, i ] - 1
	  if assy_ndx >= 0:
	    pin_weights[ mpiny, :, :, assy_ndx ] *= 0.5

        for j in xrange( aylo, core.nassy ):
          assy_ndx = core.coreMap[ j, massx ] - 1
	  if assy_ndx >= 0:
	    pin_weights[ :, mpiny, :, assy_ndx ] *= 0.5
      #end if-else coreSym

#			-- Multiply weights by axial mesh size
#			--
      for k in xrange( core.nax ):
        pin_weights[ :, :, k, : ] *= \
	    (core.axialMesh[ k + 1 ] - core.axialMesh[ k ])
    #end else pin_factors is None

    self.fDict[ 'pinWeights' ] = pin_weights

#			-- "Normal" averaging weights
#			--
    self.fDict[ 'assemblyWeights' ] = np.sum( pin_weights, axis = ( 0, 1 ) )
    self.fDict[ 'axialWeights' ] = np.sum( pin_weights, axis = ( 0, 1, 3 ) )
    self.fDict[ 'coreWeights' ] = np.sum( pin_weights, axis = ( 0, 1, 2, 3 ) )
    self.fDict[ 'radialAssemblyWeights' ] = \
        np.sum( pin_weights, axis = ( 0, 1, 2 ) )
    self.fDict[ 'radialWeights' ] = np.sum( pin_weights, axis = 2 )

#			-- Calculate node weights
#			--
    self.fDict[ 'assemblyNodeWeights' ] = assy_node_weights = \
        self._calc_node_assembly_weights( core )
    self.fDict[ 'nodeWeights' ], \
    self.fDict[ 'radialNodeWeights' ] = \
        self._calc_node_weights( core, assy_node_weights, pin_weights )

#			-- Special exposure weights?
#			--
    initial_mass = None
    for n in ( 'initial_mass', 'pin_initial_mass' ):
      if n in core.group:
	self.fDict[ 'initialMass' ] = initial_mass = \
	    np.array( core.group[ n ] )
	break
    #xxx assume 'factor' attribute is initial_maass for _exposure datasets
    #xxx do this on-the-fly in _calc_aggregate()
    if initial_mass is not None:
      self.fDict[ 'exposurePinWeights' ] = exp_pin_weights = \
          pin_weights * initial_mass
      self.fDict[ 'exposureAssemblyWeights' ] = \
          np.sum( exp_pin_weights, axis = ( 0, 1 ) )
      self.fDict[ 'exposureAxialWeights' ] = \
          np.sum( exp_pin_weights, axis = ( 0, 1, 3 ) )
      self.fDict[ 'exposureCoreWeights' ] = \
          np.sum( exp_pin_weights, axis = ( 0, 1, 2, 3 ) )
      self.fDict[ 'exposureRadialAssemblyWeights' ] = \
          np.sum( exp_pin_weights, axis = ( 0, 1, 2 ) )
      self.fDict[ 'exposureRadialWeights' ] = \
          np.sum( exp_pin_weights, axis = 2 )
    #end if initial_mass is not None

    return  self.fDict
  #end _calc_weights


  #----------------------------------------------------------------------
  #	METHOD:		_fix_node_factors()				-
  #----------------------------------------------------------------------
  def _fix_node_factors( self, avg ):
    """Applies Andrew's quarter symmetry, odd assemblies node averaging fix.
@param  avg		input factors, np.ndarray
@return			same factors, updated
"""
    # if quarter symmetry and odd assem
    if self.core.coreSym == 4 and self.core.nassx % 2 == 1 and \
        self.core.npinx % 2 == 1:
      mass = self.core.nassx / 2
      for i in xrange( mass, self.core.nassx ):
        l=self.core.coreMap[mass,i]-1
        if l>=0:
          avg[ 0, 2, :, l ] += avg[ 0, 0, :, l ]
          avg[ 0, 3, :, l ] += avg[ 0, 1, :, l ]
          avg[ 0, 0, :, l ] = 0
          avg[ 0, 1, :, l ] = 0

        l=self.core.coreMap[i,mass]-1
        if l>=0:
          avg[ 0, 1, :, l ] += avg[ 0, 0, :, l ]
          avg[ 0, 3, :, l ] += avg[ 0, 2, :, l ]
          avg[ 0, 0, :, l ] = 0
          avg[ 0, 2, :, l ] = 0

    return  avg
  #end _fix_node_factors


  #----------------------------------------------------------------------
  #	METHOD:		get_dataset_basename()				-
  #----------------------------------------------------------------------
  def get_dataset_basename( self, dset ):
    """Returns the base name sans parents.
"""
    name = None
    if dset is not None:
      ndx = dset.name.rfind( '/' )
      name = dset.name  if ndx < 0 else  dset.name[ ndx + 1 : ]
    return  name
  #end get_dataset_basename


  #----------------------------------------------------------------------
  #	METHOD:		_get_exposure_name()				-
  #----------------------------------------------------------------------
  def _get_exposure_name( self, name ):
    """Converts the weights name to an exposure equivalent, e.g.
'assemblyWeights' becomes 'exposureAssemblyWeights'.
"""
    if name:
      name = 'exposure' + name[ 0 ].upper() + name[ 1 : ]
    return  name
  #end _get_exposure_name


  #----------------------------------------------------------------------
  #	METHOD:		load()						-
  #----------------------------------------------------------------------
  def load( self, core, ref_pin_powers, pin_factors = None ):
    """
@param  core		datamodel.Core object with properties
			  axialMesh, axialMeshCenters, coreMap, coreSym,
			  nass, nassx, nassy, nax, npin, pinVolumes
@param  ref_pin_powers	'pin_powers' data as an np.ndarray
@param  pin_factors	optional factors to use for pinWeights
"""
    self.core = core
    self._calc_weights( core, ref_pin_powers, pin_factors )
  #end load


  #----------------------------------------------------------------------
  #	METHOD:		_resolve_weights_and_factors()			-
  #----------------------------------------------------------------------
  def _resolve_weights_and_factors( self, dset, weights_name ):
    """Checks for "_exposures" dataset, 'initialMass' from CORE, and
exposures factors.
    Args:
        dset (h5py.Dataset): Dataset instance.
	weights_name (str): name of normal weights to apply.
    Returns:
	tuple: weights, optional factors
"""
    weights = self.fDict.get( weights_name )

    factors = None
    if dset.name.endswith( '_exposures' ):
      exp_name = self._get_exposure_name( weights_name )
      exp_weights = self.fDict.get( exp_name )
      factors = self.fDict.get( 'initialMass' )
      if exp_weights is not None and factors is not None:
        weights = exp_weights

    return  weights, factors
  #end _resolve_weights_and_factors


  #----------------------------------------------------------------------
  #	PROPERTIES							-
  #----------------------------------------------------------------------
  assemblyNodeWeights = \
      property( lambda self: self.fDict.get( 'assemblyNodeWeights' ) )
  assemblyWeights = \
      property( lambda self: self.fDict.get( 'assemblyWeights' ) )
  axialWeights = \
      property( lambda self: self.fDict.get( 'axialWeights' ) )
  coreWeights = \
      property( lambda self: self.fDict.get( 'coreWeights' ) )
  exposureAssemblyWeights = \
      property( lambda self: self.fDict.get( 'exposureAssemblyWeights' ) )
  exposureAxialWeights = \
      property( lambda self: self.fDict.get( 'exposureAxialWeights' ) )
  exposureCoreWeights = \
      property( lambda self: self.fDict.get( 'exposureCoreWeights' ) )
  exposurePinWeights = \
      property( lambda self: self.fDict.get( 'exposurePinWeights' ) )
  exposureRadialAssemblyWeights = \
      property( lambda self: self.fDict.get( 'exposureRadialAssemblyWeights' ) )
  exposureRadialWeights = \
      property( lambda self: self.fDict.get( 'exposureRadialWeights' ) )
  initialMass = \
      property( lambda self: self.fDict.get( 'initialMass' ) )
  nodeWeights = \
      property( lambda self: self.fDict.get( 'nodeWeights' ) )
  pinWeights = \
      property( lambda self: self.fDict.get( 'pinWeights' ) )
  radialAssemblyWeights = \
      property( lambda self: self.fDict.get( 'radialAssemblyWeights' ) )
  radialNodeWeights = \
      property( lambda self: self.fDict.get( 'radialNodeWeights' ) )
  radialWeights = \
      property( lambda self: self.fDict.get( 'radialWeights' ) )

#end Averages
