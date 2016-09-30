#------------------------------------------------------------------------
#	NAME:		pin_averages.py					-
#	HISTORY:							-
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
	  pin_powers	  reference pin_powers np.ndarray
	  pin_factors	  optional already-computed factors
"""
    if len( args ) >= 2:
      self.load( *args )

    else:
      self.core = \
      self.assemblyWeights = \
      self.assemblyNodeWeights = \
      self.axialWeights = \
      self.coreWeights = \
      self.nodeWeights = \
      self.pinWeights = \
      self.radialAssemblyWeights = \
      self.radialWeights = \
      None
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_average()					-
  #----------------------------------------------------------------------
  def calc_average( self, data, avg_weights, avg_axis, **errors_args ):
    """
@param  data		np.ndarray with dataset values to average
@param  avg_weights	weights to apply as a denominator to the data sum
@param  avg_axis	axes defining shape for resulting average
@return			np.ndarray
"""
    avg = None
    if data is not None:
      if errors_args:
        errors_save = np.seterr( **errors_args )
        #errors = np.seterr( invalid = 'ignore' )
      try:
	avg = np.sum( data * self.pinWeights, axis = avg_axis ) / avg_weights
	avg = np.nan_to_num( avg )
      finally:
	if errors_args:
          np.seterr( **errors_save )
    #end if

    return  avg
  #end calc_average


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
    result = np.zeros( ( 1, 4, core.nax, core.nass ), dtype = np.float64 )
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
			( 4, core.nax, core.ass )
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

    return  np.nan_to_num( node_factors )
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
    return  self.calc_average( dset.value, self.assemblyWeights, ( 0, 1 ) )
  #end calc_pin_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_avg( self, dset ):
    return  self.calc_average( dset.value, self.axialWeights, ( 0, 1, 3 ) )
  #end calc_pin_axial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_core_avg( self, dset ):
    return  self.calc_average( dset.value, self.coreWeights, ( 0, 1, 2, 3 ) )
  #end calc_pin_core_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_node_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_node_avg( self, dset ):
    avg = np.zeros(
        ( 1, 4, self.core.nax, self.core.nass ),
	dtype = np.float64
	)

    errors_save = np.seterr( invalid = 'ignore' )
    try:
      for l in xrange( self.core.nass ):
        for k in xrange( self.core.nax ):
	  avg[ 0, :, k, l ] = self._calc_node_sum(
	      self.core, self.assemblyNodeWeights,
	      dset[ :, :, k, l ]
	      )

      avg /= self.nodeWeights
    finally:
      np.seterr( **errors_save )

    return  avg
  #end calc_pin_node_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_assembly_avg()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_avg( self, dset ):
    return  \
    self.calc_average( dset.value, self.radialAssemblyWeights, ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_avg( self, dset ):
    return  \
    self.calc_average( dset.value, self.radialWeights, 2, invalid = 'ignore' )
  #end calc_pin_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		_calc_weights()					-
  #----------------------------------------------------------------------
  def _calc_weights( self, core, ref_pin_powers, pin_factors = None ):
    """
@param  core		DataModel.Core object
@param  ref_pin_powers	'pin_powers' data as an np.ndarray
@param  pin_factors	optional factors to use for pinWeights
@return			( pin_weights, assembly_weights, axial_weights,
			  core_weights, radial_assembly_weights,
			  radial_weights, assy_node_weights, node_weights )
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
    axlo = 0
#hmid=(ax_mesh[0]+ax_mesh[-1])*0.5       # midpoint of the fuel for AO
#if sym==4:                              # for quarter symmetry
#    axlo=mass                           # start in the middle of the core
#    for i in xrange(axlo,nasx):
#        pxlo[map[i,mass]-1]=mpin        # in the assemblies on the line of 
#        pylo[map[mass,i]-1]=mpin        # symmetry, start at the middle pin
#		-- Quarter symmetry, start in the middle of the core
#		--
    if core.coreSym == 4:
      mass = core.nassx / 2
      mpin = core.npinx / 2
      pxlo = np.zeros( [ core.nass ], dtype = int )
      pylo = np.zeros( [ core.nass ], dtype = int )
#			-- Assemblies on the line of symmetry start at the
#			-- middle pin
      for i in xrange( mass, core.nassx ):
        pxlo[ core.coreMap[ i, mass ] - 1 ] = mpin
        pylo[ core.coreMap[ mass, i ] - 1 ] = mpin
#			-- Start in the middle of the core
      axlo = mass

#		-- Eighth symmetry, start at the core quadrant
#		--
    elif core.coreSym == 8:
      mass = core.nassx / 4
      mpin = core.npinx / 4
      pxlo = np.zeros( [ core.nass ], dtype = int )
      pylo = np.zeros( [ core.nass ], dtype = int )
#			-- Assemblies on the line of symmetry start at the
#			-- fourth-way pin
      for i in xrange( mass, core.nassx ):
        pxlo[ core.coreMap[ i, mass ] - 1 ] = mpin
        pylo[ core.coreMap[ mass, i ] - 1 ] = mpin
      axlo = mass

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
	  assy_ndx = core.coreMap[ mass, i ] - 1
	  if assy_ndx >= 0:
	    pin_weights[ mpin, :, :, assy_ndx ] *= 0.5

        for j in xrange( axlo, core.nassy ):
          assy_ndx = core.coreMap[ j, mass ] - 1
	  if assy_ndx >= 0:
	    pin_weights[ :, mpin, :, assy_ndx ] *= 0.5
      #end if-else coreSym

#			-- Multiply weights by axial mesh size
#			--
      for k in xrange( core.nax ):
        pin_weights[ :, :, k, : ] *= \
	    (core.axialMesh[ k + 1 ] - core.axialMesh[ k ])
    #end else must calculate pin_weights

    assembly_weights = np.sum( pin_weights, axis = ( 0, 1 ) )
    axial_weights = np.sum( pin_weights, axis = ( 0, 1, 3 ) )
    core_weights = np.sum( pin_weights, axis = ( 0, 1, 2, 3 ) )
    radial_assembly_weights = np.sum( pin_weights, axis = ( 0, 1, 2 ) )
    radial_weights = np.sum( pin_weights, axis = 2 )

#			-- Calculate node weights
#			--
    assy_node_weights = self._calc_node_assembly_weights( core )
    node_weights = \
        self._calc_node_weights( core, assy_node_weights, pin_weights )

    return  \
        pin_weights, assembly_weights, axial_weights, core_weights, \
        radial_assembly_weights, radial_weights, assy_node_weights, node_weights
  #end _calc_weights


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
    #self.statept = statept

    self.pinWeights, \
    self.assemblyWeights, \
    self.axialWeights, \
    self.coreWeights, \
    self.radialAssemblyWeights, \
    self.radialWeights, \
    self.assemblyNodeWeights, \
    self.nodeWeights = \
    self._calc_weights( core, ref_pin_powers, pin_factors )
  #end load

#end Averages
