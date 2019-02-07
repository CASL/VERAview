#------------------------------------------------------------------------
#	NAME:		generic_averages.py				-
#	HISTORY:							-
#               2019-01-24      leerw@ornl.gov                          -
#         Added calc_{rms,stddev}().
#		2018-12-05	leerw@ornl.gov				-
#		2018-12-03	leerw@ornl.gov				-
#		2018-05-21	leerw@ornl.gov				-
#	  Added calc_{max,min}(), renamed calc_average() to calc_avg() for
#	  naming consistency.
#		2017-02-03	leerw@ornl.gov				-
#	  Worked with Andrew to add fix_weights(), called from
#	  calc_average().
#		2016-09-29	leerw@ornl.gov				-
#	  Implementing calc_average().
#		2016-09-14	leerw@ornl.gov				-
#	  Building from Bob's directions on #3996.
#------------------------------------------------------------------------
import h5py, logging, os, sys
import numpy as np
import pdb

from .utils import *


#------------------------------------------------------------------------
#	CLASS:		Averages					-
#------------------------------------------------------------------------
class Averages( object ):


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, core = None, pin_powers = None, pin_factors = None ):
    """Calls ``load()``.  If the parameters are not provided, ``load()``
must be called with good parameters before this object can be used.
    Args:
        core (data.datamodel.Core): object with properties
            axialMesh, axialMeshCenters, coreMap, coreSym,
            nass, nassx, nassy, nax, npin, pinVolumes
        pin_powers (np.ndarray): "pin_powers" dataset from which to
            calculate pin weights
        pin_factors (np.ndarray): optional default pin weights
"""
    self._logger = logging.getLogger( 'data' )

    self._node_assy_weights = {}
    self._node_weights = {}
    self._weights = {}

    if core is not None:
      self.load( core, pin_powers, pin_factors )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_avg()					-
  #----------------------------------------------------------------------
  def calc_avg( self, dset, avg_axis, use_factors = True ):
    """
    Args:
        #qds_name (data.datamodel.DataSetName): name
        dset (h5py.Dataset): dataset to average
	avg_axis (int or tuple): axis for averaging
	use_factors (bool): True to apply factors/weights
    Returns:
        np.ndarray: calculated average or None if no-can-do for this dataset
"""
    avg = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        factor_weights = self.resolve_dset_weights( dset, use_factors )

# np.average() will not ignore divide by zero
#        avg = np.average( dset[ : ], axis = avg_axis, weights = factor_weights )
#	avg = np.nan_to_num( avg )
        data = np.nan_to_num( dset[ : ] )
        avg = \
            np.sum( data * factor_weights, axis = avg_axis ) / \
            np.sum( factor_weights, axis = avg_axis )

      finally:
	np.seterr( **errors_save )
    #end if

    return  avg
  #end calc_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_node_avg()					-
  #----------------------------------------------------------------------
  def calc_node_avg( self, dset, avg_axis = None ):
    """
    Args:
        dset (h5py.Dataset): dataset with shape ( npiny, npinx, nax, nass )
        avg_axis (tuple or int): optional additional axes over which to average,
            in addition to ( 0, 1 )
    Returns:
        np.ndarray: calculated average with shape ( 1, 4, nax or 1, nass or 1 )
"""
    avg = np.zeros(
        ( 1, 4, dset.shape[ 2 ], dset.shape[ 3 ] ),
	dtype = np.float64
	)

    node_assy_wts = self._calc_node_assembly_weights( *dset.shape[ : 2 ] )
    factor_wts = self.resolve_dset_weights( dset )
    node_wts = self._calc_node_weights( node_assy_wts, factor_wts )

    errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
    try:
      for l in range( dset.shape[ 3 ] ):
        for k in range( dset.shape[ 2 ] ):
          avg[ 0, :, k, l ] = self._calc_node_sum(
              dset.shape[ 0 ], dset.shape[ 1 ], node_assy_wts,
	      dset[ :, :, k, l ] * factor_wts[ :, :, k, l ]
              )

      avg = self._fix_node_factors( avg )
      avg /= node_wts
      avg[ avg == np.inf ] = 0.0
      avg = np.nan_to_num( avg )

      if avg_axis:
        if not has_attr( avg_axis, '__iter__' ):
          avg_axis = tuple([ avg_axis ])

        if avg_axis == ( 2, 3 ):
          temp_avg = \
              np.sum( avg * node_wts, axis = 2 ) / np.sum( node_wts, axis = 1 )
          avg = temp_avg.reshape( ( 0, 4, 1, 1 ) )
        elif 2 in avg_axis:
          temp_avg = \
              np.sum( avg * node_wts, axis = 1 ) / np.sum( node_wts, axis = 1 )
          avg = temp_avg.reshape( ( 0, 4, 1, dset.shape[ 3 ] ) )
        elif 3 in avg_axis:
          temp_avg = \
              np.sum( avg * node_wts, axis = 2 ) / np.sum( node_wts, axis = 2 )
          avg = temp_avg.reshape( ( 0, 4, dset.shape[ 2 ], 1 ) )
      #end if avg_axis

    finally:
      np.seterr( **errors_save )

    return  avg
  #end calc_node_avg


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_sum()				-
  #----------------------------------------------------------------------
  def _calc_node_sum( self, npiny, npinx, node_assy_weights, data ):
    """
    Args:
        npiny (int): number of vertical pins
        npinx (int): number of horizontal pins
        node_assy_weights (np.ndarray): weights for each pin,
            shape (4, npiny, npinx )
        data (np.ndarray): shape ( npiny, npinx )
    Returns:
        np.ndarray: node sums, [ s0, s1, s2, s3 ]
"""
    values = \
        [ np.sum( data * node_assy_weights[ i, :, : ] ) for i in range( 4 ) ]
    return  np.array( values, dtype = np.float64 )
  #end _calc_node_sum


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_weights()				-
  #----------------------------------------------------------------------
  def _calc_node_weights( self, node_assy_weights, pin_weights ):
    """
    Args:
        npiny (int): number of vertical pins
        npinx (int): number of horizontal pins
        node_assy_weights (np.ndarray): weights for each pin,
            shape (4, npiny, npinx )
        pin_weights (np.ndarray): shape ( npiny, npinx, nax, nass )
    Returns:
        np.ndarray: node weights with shape [ 4, core.nax, core.nass ]
"""
#		-- Node factors
#		--
    fshape = pin_weights.shape
    node_factors_shape = ( 1, 4 ) + fshape[ 2 : ]
    node_factors = np.zeros( node_factors_shape, dtype = np.float64 )
        #np.zeros( ( 1, 4, fshape[ 2 ], fshape[ 3 ] ), dtype = np.float64 )
    for l in xrange( node_factors.shape[ 2 ] ):
      for k in xrange( node_factors.shape[ 1 ] ):
        node_factors[ 0, :, k, l ] = self._calc_node_sum(
            fshape[ 0 ], fshape[ 1 ],
            node_assy_weights,
	    pin_weights[ :, :, k, l ]
	    )
  
    #if quarter symmetry and odd assem
        #fshape[ 3 ] == self.core.nass
    if self.core.coreSym == 4 and \
        self.core.nassx % 2 == 1 and self.core.nassy == self.core.nassx and \
        fshape[ 0 ] % 2 == 1 and fshape[ 1 ] == fshape[ 0 ]:
      mid_ass = self.core.nassy >> 1
      for j in range( mid_ass, self.core.nassx ):
        l = self.core.coreMap[ mid_ass, j ] - 1
        if l >= 0:
          node_factors[0,2,:,l] += node_factors[0,0,:,l]
          node_factors[0,3,:,l] += node_factors[0,1,:,l]
          node_factors[0,0,:,l] = 0
          node_factors[0,1,:,l] = 0

        l = self.core.coreMap[ j, mid_ass ] - 1
        if l >= 0:
          node_factors[0,1,:,l] += node_factors[0,0,:,l]
          node_factors[0,3,:,l] += node_factors[0,2,:,l]
          node_factors[0,0,:,l] = 0
          node_factors[0,2,:,l] = 0
        
    node_factors = np.nan_to_num( node_factors )
    return  node_factors
  #end _calc_node_weights


  #----------------------------------------------------------------------
  #	METHOD:		_calc_node_weights_1()				-
  #----------------------------------------------------------------------
  def _calc_node_weights_1( self, node_assy_weights, pin_weights ):
    """
    Args:
        npiny (int): number of vertical pins
        npinx (int): number of horizontal pins
        node_assy_weights (np.ndarray): weights for each pin,
            shape (4, npiny, npinx )
        pin_weights (np.ndarray): shape [ npiny, npinx, nax, nass ]
    Returns:
        list(np.ndarray): two arrays:
            node weights with shape [ 4, core.nax, core.nass ],
            radial node weights with shape [ 1, core.nax, core.nass ]
"""
#		-- Node factors
#		--
    node_factors = \
        np.zeros( ( 4, self.core.nax, self.core.nass ), dtype = np.float64 )
    for l in xrange( self.core.nass ):
      for k in xrange( self.core.nax ):
        node_factors[ :, k, l ] = self._calc_node_sum(
	    self.core.npiny, self.core.npinx, node_assy_weights,
	    pin_weights[ :, :, k, l ]
	    )
  
    #if quarter symmetry and odd assem
    if self.core.coreSym == 4 and \
        self.core.nassx % 2 == 1 and self.core.nassy == self.core.nassx and \
        self.core.npinx % 2 == 1 and self.core.npiny == self.core.npinx:
      mid_ass = self.core.nassy >> 1
      #mid_ass_x = core.nassx >> 1
      #mid_ass_y = core.nassy >> 1
      for j in range( mid_ass, self.core.nassx ):
        l = self.core.coreMap[ mid_ass, j ] - 1
        if l >= 0:
          node_factors[2,:,l] += node_factors[0,:,l]
          node_factors[3,:,l] += node_factors[1,:,l]
          node_factors[0,:,l] = 0
          node_factors[1,:,l] = 0

        l = self.core.coreMap[ j, mid_ass ] - 1
        if l >= 0:
          node_factors[1,:,l] += node_factors[0,:,l]
          node_factors[3,:,l] += node_factors[2,:,l]
          node_factors[0,:,l] = 0
          node_factors[2,:,l] = 0
        
    node_factors = np.nan_to_num( node_factors )
    radial_node_factors = np.sum( node_factors, axis = 1 )
    return  node_factors, radial_node_factors
  #end _calc_node_weights_1


  #----------------------------------------------------------------------
  #	METHOD:		calc_rms()					-
  #----------------------------------------------------------------------
  def calc_rms( self, dset, avg_axis, use_factors = True ):
    """
    Args:
        #qds_name (data.datamodel.DataSetName): name
        dset (h5py.Dataset): dataset to average
	avg_axis (int or tuple): axis for averaging
	use_factors (bool): True to apply factors/weights
    Returns:
        np.ndarray: calculated average or None if no-can-do for this dataset
"""
    rms = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        factor_weights = self.resolve_dset_weights( dset, use_factors )
        data = np.nan_to_num( dset[ : ] )
        rms = np.sqrt(
            np.sum( (data ** 2) * factor_weights, axis = avg_axis ) /
            np.sum( factor_weights, axis = avg_axis )
            )

      finally:
	np.seterr( **errors_save )
    #end if

    return  rms
  #end calc_rms


  #----------------------------------------------------------------------
  #	METHOD:		calc_stddev()					-
  #----------------------------------------------------------------------
  def calc_stddev( self, dset, avg_axis, use_factors = True ):
    """
    Args:
        #qds_name (data.datamodel.DataSetName): name
        dset (h5py.Dataset): dataset to average
	avg_axis (int or tuple): axis for averaging
	use_factors (bool): True to apply factors/weights
    Returns:
        np.ndarray: calculated average or None if no-can-do for this dataset
"""
    stddev = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        factor_weights = self.resolve_dset_weights( dset, use_factors )
        data = np.nan_to_num( dset[ : ] )
        mean = np.sum( data * factor_weights ) / np.sum( factor_weights )
        a = np.sum( ((data - mean) ** 2) * factor_weights, axis = avg_axis )
        b = np.sum( factor_weights, axis = avg_axis )
        stddev = np.sqrt( a / b )

      finally:
	np.seterr( **errors_save )
    #end if

    return  stddev
  #end calc_stddev


  #----------------------------------------------------------------------
  #	METHOD:		_calc_weights()					-
  #----------------------------------------------------------------------
  def _calc_weights( self, pin_powers ):
    """Updates self.fDict.
    Args:
	pin_powers (np.ndarray): "pin_powers" as an array
    Returns:
        np.ndarray: default pin weights
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
#hmid=(ax_mesh[0]+ax_mesh[-1])*0.5       # midpoint of the fuel for AO
#if sym==4:                              # for quarter symmetry
#    axlo=mass                           # start in the middle of the core
#    for i in xrange(axlo,nasx):
#        pxlo[map[i,mass]-1]=mpin        # in the assemblies on the line of 
#        pylo[map[mass,i]-1]=mpin        # symmetry, start at the middle pin

    core = self.core
    assy_col_start = assy_row_start = 0

#		-- Start with zero weights
#		--
    pin_weights = np.zeros( pin_powers.shape, dtype = np.float64 )
    pin_powers[ np.isnan( pin_powers ) ] = 0.0

#               -- Full core, weight is 1 for non-zero power
#		--
    if core.coreSym <= 1:
      np.place( pin_weights, pin_powers > 0.0, 1.0 )

    else:
#		        -- Quarter symmetry, start in the middle of the core
#                       --
      if core.coreSym == 4:
        #x mass = massx = core.nassx >> 1
        mid_assy_ndx = \
        mid_assy_col = core.nassx >> 1
        mid_assy_row = core.nassy >> 1
#        mpin = mpinx = core.npinx >> 1
#        mpiny = core.npiny >> 1
        #x mpin = mpinx = 0 if core.nassx % 2 == 0  else core.npinx >> 1
        mid_pin_ndx = \
        mid_pin_col = 0  if core.nassx % 2 == 0 else  core.npinx >> 1
        mid_pin_row = 0  if core.nassy % 2 == 0 else  core.npiny >> 1
        pin_col_start = np.zeros( [ core.nass ], dtype = int )
        pin_row_start = np.zeros( [ core.nass ], dtype = int )
#			        -- Assemblies on the line of symmetry start
#                               -- at the middle pin
        for j in range( mid_assy_row, core.nassy ):
          pin_col_start[ core.coreMap[ j, mid_assy_col ] - 1 ] = mid_pin_col
        for i in range( mid_assy_col, core.nassx ):
          pin_row_start[ core.coreMap[ mid_assy_row, i ] - 1 ] = mid_pin_row
#			        -- Start in the middle of the core
        assy_col_start = mid_assy_col
        assy_row_start = mid_assy_row

#		        -- Eighth symmetry, start at the core quadrant
#		        -- Note this has yet to be implemented
      elif core.coreSym == 8:
        #x mass = mid_assy_col = core.nassx >> 2
        mid_assy_ndx = \
        mid_assy_col = core.nassx >> 2
        mid_assy_row = core.nassy >> 2
        mid_pin_ndx = mid_pin_col = core.npinx >> 2
        mid_pin_row = core.npiny >> 2
        pin_col_start = np.zeros( [ core.nass ], dtype = int )
        pin_row_start = np.zeros( [ core.nass ], dtype = int )
#		        	-- Assemblies on the line of symmetry start
#                               -- at the -- fourth-way pin
        for j in xrange( mid_assy_row, core.nassy ):
          pin_col_start[ core.coreMap[ j, mid_assy_col ] - 1 ] = mid_pin_col
        for i in xrange( mid_assy_col, core.nassx ):
          pin_row_start[ core.coreMap[ mid_assy_row, i ] - 1 ] = mid_pin_row
        assy_col_start = mid_assy_col
        assy_row_start = mid_assy_row
      #end if-elif core.coreSym

#			-- Initialize weights to 1 for non-zero power
#			--
      #npin = core.npin
      npinx = core.npinx
      npiny = core.npiny
      for j in range( core.nassy ):
        for i in range( core.nassx ):
          assy_ndx = core.coreMap[ j, i ] - 1
          pin_i = pin_col_start[ assy_ndx ]
          pin_j = pin_row_start[ assy_ndx ]
          np.place(
              pin_weights[ pin_j : npiny, pin_i : npinx, :, assy_ndx ],
              pin_powers[ pin_j : npiny, pin_i : npinx, :, assy_ndx ] > 0.0,
              1.0
              )
#                       -- Cut pin weights by half on line of symmetry
#                       --
      for i in range( assy_col_start, core.nassx ):
	assy_ndx = core.coreMap[ mid_assy_row, i ] - 1
	if assy_ndx >= 0:
	  pin_weights[ mid_pin_row, :, :, assy_ndx ] *= 0.5

      for j in range( assy_row_start, core.nassy ):
        assy_ndx = core.coreMap[ j, mid_assy_col ] - 1
	if assy_ndx >= 0:
	  pin_weights[ :, mid_pin_col, :, assy_ndx ] *= 0.5
    #end if core.coreSym <= 1

#			-- Multiply weights by axial mesh size
#			--
    for k in range( core.nax ):
      pin_weights[ :, :, k, : ] *= \
          (core.axialMesh[ k + 1 ] - core.axialMesh[ k ])

    return  pin_weights
  #end _calc_weights


  #----------------------------------------------------------------------
  #	METHOD:		_fix_node_factors()				-
  #----------------------------------------------------------------------
  def _fix_node_factors( self, avg ):
    """Applies Andrew's quarter symmetry, odd assemblies node averaging fix.
    Args:
        avg (np.ndarray): input factors
    Returns:
        np.ndarray: updated factors
"""
    # if quarter symmetry and odd assem
    if self.core.coreSym == 4 and \
        avg.shape[ 3 ] == self.core.nass and \
        core.nassx % 2 == 1 and core.nassy == core.nassx:
      mid_ass = self.core.nassy >> 1
      for j in range( mid_ass, self.core.nassx ):
        l = self.core.coreMap[ mid_ass, j ] - 1
        if l >= 0:
          avg[ 0, 2, :, l ] += avg[ 0, 0, :, l ]
          avg[ 0, 3, :, l ] += avg[ 0, 1, :, l ]
          avg[ 0, 0, :, l ] = 0
          avg[ 0, 1, :, l ] = 0

        l = self.core.coreMap[ j, mid_ass ] - 1
        if l >= 0:
          avg[ 0, 1, :, l ] += avg[ 0, 0, :, l ]
          avg[ 0, 3, :, l ] += avg[ 0, 2, :, l ]
          avg[ 0, 0, :, l ] = 0
          avg[ 0, 2, :, l ] = 0

    return  avg
  #end _fix_node_factors


  #----------------------------------------------------------------------
  #	METHOD:		get_node_assembly_weights()			-
  #----------------------------------------------------------------------
  def get_node_assembly_weights( self, npiny, npinx ):
    """
    Args:
        npiny (int): number of vertical pins
        npinx (int): number of horizontal pins
    Returns:
        np.ndarray: weights with shape ( 4, npiny, npinx )
"""
    core = self.core
#               -- Already have it?
#               --
    t = ( npiny, npinx )
    assy_node_factors = self._node_assy_weights.get( t )

#		-- Must calculate
#		--
    if assy_node_factors is None:
      assy_node_factors = np.zeros( ( 4, npiny, npinx ) )
#x    mid = core.npin >> 1
      midy = core.npiny >> 1
      midx = core.npinx >> 1

      y = midy + 1  if core.npiny % 2 == 1  else midy
      x = midx + 1  if core.npinx % 2 == 1  else midx

      assy_node_factors[ 0,     0 : y         ,     0 : x          ] = 1
      assy_node_factors[ 1,     0 : y         ,  midx : core.npinx ] = 1
      assy_node_factors[ 2,  midy : core.npiny,     0 : x          ] = 1
      assy_node_factors[ 3,  midy : core.npiny,  midx : core.npinx ] = 1

      assy_node_factors[ :,     0 : core.npiny,  midx           ] *= 0.5
      assy_node_factors[ :,  midy             ,  0 : core.npinx ] *= 0.5
    #end if assy_node_factors is None

    return  assy_node_factors
  #end get_node_assembly_weights


  #----------------------------------------------------------------------
  #	METHOD:		get_node_weights()                              -
  #----------------------------------------------------------------------
  def get_node_weights( self, npiny, npinx ):
    """
"""
    return  self._node_weights.get( ( npiny, npinx ) )
  #end get_node_weights


  #----------------------------------------------------------------------
  #	METHOD:		get_weights()					-
  #----------------------------------------------------------------------
  def get_weights( self, shape ):
    """
"""
    result = self._weights.get( shape )
    if result is None:
      result = self._calc_weights( self._pin_powers )
    return  result
  #end get_weights


  #----------------------------------------------------------------------
  #	METHOD:		load()						-
  #----------------------------------------------------------------------
  def load( self, core, pin_powers, pin_factors ):
    """Uses ``pin_factors`` as pin_weights if provided
``pin_powers`` are provided.  Otherwise ``load()`` must be called before use.
    Args:
        core (data.datamodel.Core): object with properties
            axialMesh, axialMeshCenters, coreMap, coreSym,
            nass, nassx, nassy, nax, npin, pinVolumes
        pin_powers (np.ndarray): "pin_powers" dataset from which to
            calculate pin weights, cannot be None
        pin_factors (np.ndarray): optional default pin weights
"""
    self._node_assy_weights.clear()
    self._node_weights.clear()
    self._weights.clear()

    self._core = core
    self._pin_powers = pin_powers
    if pin_factors is not None and pin_factors.shape == pin_powers.shape:
      self._weights[ pin_powers.shape ] = pin_factors
    else:
      self._weights[ pin_powers.shape ] = self._calc_weights( pin_powers )
  #end load


  #----------------------------------------------------------------------
  #	METHOD:		resolve_dset_node_weights()                     -
  #----------------------------------------------------------------------
  def resolve_dset_node_weights( self, dset, use_factors = True ):
    """
    Args:
        dset (h5py.Dataset or np.ndarray): 4D dataset to average, if not
           a Dataset no attributes lookup is performed
	use_factors (bool): True to apply factors/weights
    Returns:
        np.ndarray: retrieved or calculated node weights
"""
    node_weights = None

    if dset is not None and len( dset.shape ) == 4:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        if use_factors:
          if hasattr( dset, 'attrs' ) and dset.attrs and self.core is not None:
            factor_obj = None
            for attr_name in ( 'node_factor', 'node_factors' ):
              if attr_name in dset.attrs:
                factor_obj = dset.attrs[ attr_name ]
                break
            if factor_obj is not None:
	      factor_name = DataUtils.ToString( factor_obj )
              if factor_name.lower() in ( 'none', 'null', '' ):
                use_factors = False
              else:
                node_weights = self.core.group.get( factor_name )
          #end if dset.attrs and self.core is not None
        #end if use_factors

        if use_factors:
          if node_weights is not None:
            match_shape = ( 1, 4 ) + dset.shape[ 2 : ]
            if node_weights.shape == match_shape[ 1 : ]:
              node_weights = node_weights.reshape( match_shape )
            elif node_weights.shape != match_shape:
              self._logger.warning(
                  'dset "%s" shape=%s, "node_factors" attribute shape=%s"',
                  dset.name, str( dset.shape ), str( node_weights.shape )
                  )
              node_weights = None

	  if node_weights is None:
            node_weights = self._node_weights.get( dset.shape )
        #end if use_factors

	if node_weights is None:
          node_assy_wts = self.get_node_assembly_weights( *dset.shape[ : 2 ] )
          pin_wts = self.resolve_dset_weights( dset )
          node_weights = self._calc_node_weights( node_assy_wts, pin_wts )

          if use_factors:
            self._node_weights[ dset.shape ] = node_weights
	#end if node_weights is None

      finally:
	np.seterr( **errors_save )
    #end if dset is not None

    return  node_weights
  #end resolve_dset_node_weights


  #----------------------------------------------------------------------
  #	METHOD:		resolve_dset_weights()                          -
  #----------------------------------------------------------------------
  def resolve_dset_weights( self, dset, use_factors = True ):
    """
    Args:
        dset (h5py.Dataset or np.ndarray): 4D dataset to average, if not
           a Dataset no attributes lookup is performed
	use_factors (bool): True to apply factors/weights
    Returns:
        np.ndarray: retrieved or calculated weights
"""
    factor_weights = None

    if dset is not None:
      base_weights = None

      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
        #avg_weights = np.ones( avg_axis, dtype = int )

        if use_factors:
          if hasattr( dset, 'attrs' ) and dset.attrs and self.core is not None:
            factor_obj = None
            for attr_name in ( 'factor', 'factors' ):
              if attr_name in dset.attrs:
                factor_obj = dset.attrs[ attr_name ]
                break
            if factor_obj is not None:
	      factor_name = DataUtils.ToString( factor_obj )
              if factor_name.lower() in ( 'none', 'null', '' ):
                use_factors = False
              else:
                factor_weights = self.core.group.get( factor_name )
          #end if dset.attrs and self.core is not None
        #end if use_factors

        if use_factors:
          if factor_weights is not None and factor_weights.shape != dset.shape:
            self._logger.warning(
                'dset "%s" shape=%s, "factors" attribute shape=%s"',
                dset.name, str( dset.shape ), str( factor_weights.shape )
                )
            factor_weights = None

	  if factor_weights is None:
            factor_weights = self._weights.get( dset.shape )
            if factor_weights is None:
              base_weights = self._weights.get( self._pin_powers.shape )
        #end if use_factors

	if factor_weights is None:
          #base_weights = self._weights.get( self._pin_powers.shape )
          if base_weights is None:
            base_weights = np.ones( self._pin_powers.shape, dtype = np.float64 )

          sum_axis = \
              [ i for i in range( len( dset.shape ) ) if dset.shape[ i ] == 1 ]
          sum_axis = tuple( sum_axis )
          factor_weights = np.sum( base_weights, axis = sum_axis )
          if factor_weights.shape != dset.shape:
            factor_weights = factor_weights.reshape( dset.shape )

          if use_factors:
            self._weights[ dset.shape ] = factor_weights
	#end if factor_weights is None

      finally:
	np.seterr( **errors_save )
    #end if dset is not None

    return  factor_weights
  #end resolve_dset_weights


#               -- Properties
#               --

  core = property( lambda x: x._core )

  pin_powers = property( lambda x: x._pin_powers )

#end Averages
