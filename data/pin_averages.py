#------------------------------------------------------------------------
#	NAME:		pin_averages.py					-
#	HISTORY:							-
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
"""
    if len( args ) >= 2:
      self.load( *args )

#    self.core = core
#    self.statept = statept
#
#    self.pinWeights, \
#    self.assemblyWeights, \
#    self.axialWeights, \
#    self.coreWeights, \
#    self.radialWeights = \
#    self.calc_weights( core, statept.GetDataSet( 'pin_powers' ).value )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_average()					-
  #----------------------------------------------------------------------
  def calc_average( self, data, avg_weights, avg_axis, **errors_args ):
    """
@param  data		np.ndarray with dataset values to average
@param  avg_weights	weights to apply as a denominator to the data sum
@param  avg_axis	axes defining shape for resulting average
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
  #	METHOD:		calc_pin_assembly_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_assembly_avg( self, data ):
    return  self.calc_average( data, self.assemblyWeights, ( 0, 1 ) )
  #end calc_pin_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_axial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_axial_avg( self, data ):
    return  self.calc_average( data, self.axialWeights, ( 0, 1, 3 ) )
  #end calc_pin_axial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_core_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_core_avg( self, data ):
    return  self.calc_average( data, self.coreWeights, ( 0, 1, 2, 3 ) )
  #end calc_pin_core_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_assembly_avg()			-
  #----------------------------------------------------------------------
  def calc_pin_radial_assembly_avg( self, data ):
    return  self.calc_average( data, self.radialAssemblyWeights, ( 0, 1, 2 ) )
  #end calc_pin_radial_assembly_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_pin_radial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_avg( self, data ):
    return  self.calc_average( data, self.radialWeights, 2, invalid = 'ignore' )
  #end calc_pin_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		_calc_weights()					-
  #----------------------------------------------------------------------
  def _calc_weights( self, core, ref_pin_powers ):
    """
@param  core		DataModel.Core object
@param  ref_pin_powers	'pin_powers' data as an np.ndarray
@return			( pin_weights, assembly_weights, axial_weights,
			  core_weights, radial_assembly_weights,
			  radial_weights )
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

#		-- Start with zero weights
#		--
    #powers = statept.GetDataSet( 'pin_powers' ).value
    #pin_weights_shape = core.pinVolumes.shape if core.pinVolumes else ref_pin_powers.shape
    #pin_weights = np.zeros( core.pinVolumes.shape, dtype = np.float64 )
    pin_weights = np.zeros( ref_pin_powers.shape, dtype = np.float64 )

#		-- Full core, weight is 1 for non-zero power
#		--
    if core.coreSym <= 1:
      np.place( pin_weights, ref_pin_powers > 0.0, 1.0 )

    else:
#			-- Initialize weights to 1 for non-zero power
#			--
      #npin = core.npin
      npinx = core.npinx
      npiny = core.npiny
      for i in xrange( core.nass ):
	np.place(
            pin_weights[ pylo[ i ] : npiny, pxlo[ i ] : npinx, :, i ],
            ref_pin_powers[ pylo[ i ] : npiny, pxlo[ i ] : npinx, :, i ] > 0.0,
            1.0
	    )
#			-- Cut pin weights by half on line of symmetry
#			--
      for i in xrange( axlo, core.nassx ):
	assy_ndx = core.coreMap[ mass, i ] - 1
	if assy_ndx >= 0:
	  pin_weights[ mpin, :, :, i ] *= 0.5

      for j in xrange( axlo, core.nassy ):
        assy_ndx = core.coreMap[ j, mass ] - 1
	if assy_ndx >= 0:
	  pin_weights[ :, mpin, :, j ] *= 0.5
    #end if-else

#		-- Multiply weights by axial mesh size
#		--
    for k in xrange( core.nax ):
      pin_weights[ :, :, k, : ] *= (core.axialMesh[ k + 1 ] - core.axialMesh[ k ])

    assembly_weights = np.sum( pin_weights, axis = ( 0, 1 ) )
    axial_weights = np.sum( pin_weights, axis = ( 0, 1, 3 ) )
    core_weights = np.sum( pin_weights, axis = ( 0, 1, 2, 3 ) )
    radial_assembly_weights = np.sum( pin_weights, axis = ( 0, 1, 2 ) )
    radial_weights = np.sum( pin_weights, axis = 2 )

    return  \
        pin_weights, assembly_weights, axial_weights, core_weights, \
        radial_assembly_weights, radial_weights
  #end _calc_weights


  #----------------------------------------------------------------------
  #	METHOD:		load()						-
  #----------------------------------------------------------------------
  def load( self, core, ref_pin_powers ):
    """
@param  core		datamodel.Core object with properties
			  axialMesh, axialMeshCenters, coreMap, coreSym,
			  nass, nassx, nassy, nax, npin, pinVolumes
@param  ref_pin_powers	'pin_powers' data as an np.ndarray
#@param  statept		datamodel.State reference object, probably from
#			'STATE_0001', which is assumed to have 'pin_powers'
"""
    self.core = core
    #self.statept = statept


    self.pinWeights, \
    self.assemblyWeights, \
    self.axialWeights, \
    self.coreWeights, \
    self.radialAssemblyWeights, \
    self.radialWeights = \
    self._calc_weights( core, ref_pin_powers )
  #end load

#end Averages
