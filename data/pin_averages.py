#------------------------------------------------------------------------
#	NAME:		pin_averages.py					-
#	HISTORY:							-
#		2016-02-15	leerw@ornl.gov				-
#	  Re-fitting to use VERAView DataModel.
#		2016-01-28	godfreyam@ornl.gov			-
#------------------------------------------------------------------------
import h5py, os, sys
import numpy as np


#------------------------------------------------------------------------
#	CLASS:		Averages					-
#------------------------------------------------------------------------
class Averages( object ):


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, core, statept ):
    """
@param  core		datamodel.Core object with properties
			  axialMesh, axialMeshCenters, coreMap, coreSym,
			  nass, nassx, nassy, nax, npin, pinVolumes
@param  statept		datamodel.State reference object, probably from
			'STATE_0001', which is assumed to have 'pin_powers'
"""
    self.core = core
    self.statept = statept

# Get the geometry information ----------------------------------------
#map=f['CORE']['core_map']               # get core map
#ax_mesh=f['CORE']['axial_mesh']         # get axial mesh
#sym=f['CORE']['core_sym'][0]            # symmetry option
#pows=f['STATE_0001']['pin_powers']      # get sample pin powers
#nass=pows.shape[3]                      # total number of assembles
#nasx=len(map)                           # number of assemblies across the core
#mass=int(nasx/2)                        # middle assembly (assume odd)
    self.mass = core.nassx / 2
#npin=pows.shape[0]                      # number of fuel pins
#mpin=int(npin/2)                        # middle fuel pin (assume odd)
    self.mpin = core.npinx / 2
#nax=len(ax_mesh)-1                      # number of axial planes
#pxlo=numpy.empty([nass],dtype=int)      # create arrays for loop bounds
#pylo=numpy.empty([nass],dtype=int)      # in case of quarter symmetry
    self.pxlo = np.empty( [ core.nass ], dtype = int )
    self.pxlo.fill( 0 )
    self.pylo = np.empty( [ core.nass ], dtype = int )
    self.pylo.fill( 0 )
#axlo=0                                  # initialize loop bounds for 
#hmid=(ax_mesh[0]+ax_mesh[-1])*0.5       # midpoint of the fuel for AO
    self.axlo = 0
    self.hmid = (core.axialMesh[ 0 ] + core.axialMesh[ -1 ]) * 0.5

    self.assemblyWeights, \
    self.axialWeights, \
    self.pinWeights, \
    self.radialWeights = \
    self.calc_weights( core, statept.GetDataSet( 'pin_powers' ).value )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc_average()					-
  #----------------------------------------------------------------------
  def calc_average( self, data, avg_weights, avg_axis ):
    """
@param  data		np.ndarray with dataset values to average
@param  avg_weights	weights to apply as a denominator to the data sum
@param  avg_axis	axes defining shape for resulting average
"""
    avg = None
    if data is not None:
      errors = np.seterr( invalid = 'ignore' )
      try:
	avg = np.sum( data * self.pinWeights, axis = avg_axis ) / avg_weights
      finally:
        np.seterr( **errors )
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
  #	METHOD:		calc_pin_radial_avg()				-
  #----------------------------------------------------------------------
  def calc_pin_radial_avg( self, data ):
    return  self.calc_average( data, self.radialWeights, 2 )
  #end calc_pin_radial_avg


  #----------------------------------------------------------------------
  #	METHOD:		calc_weights()					-
  #----------------------------------------------------------------------
  def calc_weights( self, core, pin_powers ):
    axlo = 0

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
    weights = np.zeros( core.pinVolumes.shape, dtype = np.float64 )
    #powers = statept.GetDataSet( 'pin_powers' ).value

#		-- Full core, weight is 1 for non-zero power
#		--
    if core.coreSym == 0:
      np.place( weights, pin_powers > 0.0, 1.0 )

    else:
#			-- Initialize weights to 1 for non-zero power
#			--
      npin = core.npin
      for i in xrange( core.nass ):
	np.place(
            weights[ pylo[ i ] : npin, pxlo[ i ] : npin, :, i ],
            pin_powers[ pylo[ i ] : npin, pxlo[ i ] : npin, :, i ] > 0.0,
            1.0
	    )
#			-- Cut pin weights by half on line of symmetry
#			--
      for i in xrange( axlo, core.nassx ):
	assy_ndx = core.coreMap[ mass, i ] - 1
	if assy_ndx >= 0:
	  weights[ mpin, :, :, i ] *= 0.5

      for j in xrange( axlo, core.nassy ):
        assy_ndx = core.coreMap[ j, mass ] - 1
	if assy_ndx >= 0:
	  weights[ :, mpin, :, j ] *= 0.5
    #end if-else

#		-- Multiply weights by axial mesh size
#		--
    for k in xrange( core.nax ):
      weights[ :, :, k, : ] *= (core.axialMesh[ k + 1 ] - core.axialMesh[ k ])

    assembly_weights = np.sum( weights, axis = ( 0, 1 ) )
    axial_weights = np.sum( weights, axis = ( 0, 1, 3 ) )
    radial_weights = np.sum( weights, axis = 2 )

    return  assembly_weights, axial_weights, weights, radial_weights
  #end calc_weights

#end Averages
