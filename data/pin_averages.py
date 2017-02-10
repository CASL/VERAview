#------------------------------------------------------------------------
#	NAME:		pin_averages.py					-
#	HISTORY:							-
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
import h5py, os, sys
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
      self.radialNodeWeights = \
      self.radialWeights = \
      None
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_average()					-
  #----------------------------------------------------------------------
  def calc_average( self, dset, avg_weights, avg_axis ):
    """
@param  dset		h5py.Dataset object
@param  avg_weights	weights to apply as a denominator to the data sum
@param  avg_axis	axes defining shape for resulting average
@return			np.ndarray
"""
    #errors_args = { 'divide': 'ignore', 'invalid': 'ignore' }
    avg = None
    if dset is not None:
      errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
      try:
	data = np.array( dset )
	avg = np.sum( data * self.pinWeights, axis = avg_axis ) / avg_weights
	if len( avg.shape ) > 0:
          avg[ avg == np.inf ] = 0.0
	avg = np.nan_to_num( avg )
      finally:
	np.seterr( **errors_save )
    #end if

    return  avg
  #end calc_average


  #----------------------------------------------------------------------
  #	METHOD:		calc_average_old()				-
  #----------------------------------------------------------------------
  def calc_average_old( self, data, avg_weights, avg_axis, **errors_args ):
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
  #end calc_average_old


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
  
    if core.coreSym==4 and core.nassx%2==1 and core.npinx%2==1:     # if quarter symmetry and odd assem
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
    return  self.calc_average( dset, self.assemblyWeights, ( 0, 1 ) )
    #return  self.calc_average( dset.value, self.assemblyWeights, ( 0, 1 ) )
  #end calc_pin_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_avg( self, dset ):
    return  self.calc_average( dset, self.axialWeights, ( 0, 1, 3 ) )
    #return  self.calc_average( dset.value, self.axialWeights, ( 0, 1, 3 ) )
  #end calc_pin_axial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_core_avg( self, dset ):
    return  self.calc_average( dset, self.coreWeights, ( 0, 1, 2, 3 ) )
    #return  self.calc_average( dset.value, self.coreWeights, ( 0, 1, 2, 3 ) )
  #end calc_pin_core_avg


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
  #	METHOD:		calc_pin_radial_assembly_avg()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_avg( self, dset ):
    return  self.calc_average( dset, self.radialAssemblyWeights, ( 0, 1, 2 ) )
    #self.calc_average( dset.value, self.radialAssemblyWeights, ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_avg( self, dset ):
    return  self.calc_average( dset, self.radialWeights, 2 )
    #self.calc_average( dset.value, self.radialWeights, 2 )
  #end calc_pin_radial_avg


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
  #	METHOD:		calc_pin_radial_node_avg_wrong()		-
  #----------------------------------------------------------------------
  def calc_pin_radial_node_avg_wrong( self, dset ):
    avg = np.zeros( ( 1, 4, 1, self.core.nass ), dtype = np.float64 )

    errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
    try:
      for l in xrange( self.core.nass ):
        for k in xrange( self.core.nax ):
	  node_sum = self._calc_node_sum(
	      self.core, self.assemblyNodeWeights,
	      dset[ :, :, k, l ] * self.pinWeights[ :, :, k, l]
	      )
          for n in xrange( 4 ):
	    avg[ 0, :, 0, l ] += node_sum[ n ]

      avg = self._fix_node_factors( avg )
      for n in xrange( 4 ):
        avg[ 0, n, 0, : ] /= self.radialNodeWeights[ n, : ]

      avg[ avg == np.inf ] = 0.0
      avg = np.nan_to_num( avg )
    finally:
      np.seterr( **errors_save )

    return  avg
  #end calc_pin_radial_node_avg_wrong


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
			  radial_weights, assy_node_weights,
			  node_weights, radial_node_weights )
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
      mpin = mpinx = core.npinx >> 1
      mpiny = core.npiny >> 1
      pxlo = np.zeros( [ core.nass ], dtype = int )
      pylo = np.zeros( [ core.nass ], dtype = int )
#			-- Assemblies on the line of symmetry start at the
#			-- middle pin
#x      for i in xrange( mass, core.nassx ):
#x        pxlo[ core.coreMap[ i, mass ] - 1 ] = mpin
#x        pylo[ core.coreMap[ mass, i ] - 1 ] = mpin
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
    #end else must calculate pin_weights

    assembly_weights = np.sum( pin_weights, axis = ( 0, 1 ) )
    axial_weights = np.sum( pin_weights, axis = ( 0, 1, 3 ) )
    core_weights = np.sum( pin_weights, axis = ( 0, 1, 2, 3 ) )
    radial_assembly_weights = np.sum( pin_weights, axis = ( 0, 1, 2 ) )
    radial_weights = np.sum( pin_weights, axis = 2 )

#			-- Calculate node weights
#			--
    assy_node_weights = self._calc_node_assembly_weights( core )
    node_weights, radial_node_weights = \
        self._calc_node_weights( core, assy_node_weights, pin_weights )

    return  \
        pin_weights, assembly_weights, axial_weights, core_weights, \
        radial_assembly_weights, radial_weights, assy_node_weights, \
	node_weights, radial_node_weights
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
    if self.core.coreSym==4 and self.core.nassx%2==1 and self.core.npinx%2==1:
      mass = self.core.nassx / 2
      for i in xrange(mass,self.core.nassx):
        l=self.core.coreMap[mass,i]-1
        if l>=0:
          avg[ 0, 2,:,l]+=avg[ 0, 0,:,l]
          avg[ 0, 3,:,l]+=avg[ 0, 1,:,l]
          avg[ 0, 0,:,l]=0
          avg[ 0, 1,:,l]=0

        l=self.core.coreMap[i,mass]-1
        if l>=0:
          avg[ 0, 1,:,l]+=avg[ 0, 0,:,l]
          avg[ 0, 3,:,l]+=avg[ 0, 2,:,l]
          avg[ 0, 0,:,l]=0
          avg[ 0, 2,:,l]=0

    return  avg
  #end _fix_node_factors


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
    self.nodeWeights, \
    self.radialNodeWeights = \
    self._calc_weights( core, ref_pin_powers, pin_factors )
  #end load

#end Averages
