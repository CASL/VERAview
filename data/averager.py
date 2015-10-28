#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		averager.py					-
#	HISTORY:							-
#		2015-10-28	leerw@ornl.gov				-
#		2015-10-26	leerw@ornl.gov				-
#	  Added support for coreSym == 8 in CreateCorePinFactors().
#		2015-10-05	leerw@ornl.gov				-
#		2015-10-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, tempfile, traceback
import numpy as np
#import pdb


#------------------------------------------------------------------------
#	CLASS:		Averager					-
#------------------------------------------------------------------------
class Averager( object ):
  """Interface definition and base implementation of routines to calculate
averages over 4D VERAOutput datasets.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Averager.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self ):
    """
"""
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc1DAxialAverage()			-
  #----------------------------------------------------------------------
  def Calc1DAxialAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates 1D radial averages over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nax )
"""
    wts = \
        pin_factors * weights if pin_factors != None and weights != None else \
	pin_factors if pin_factors != None else \
	weights

    avg = np.ndarray( ( core.nax, ), np.float64 )
    avg.fill( 0.0 )

    for k in range( core.nax ):
      avg[ k ] = \
          np.average( data_in[ :, :, k, : ] )  if wts == None else \
          0.0  if np.sum( wts[ :, :, k, : ] ) == 0.0 else \
          np.average( data_in[ :, :, k, : ], weights = wts[ :, :, k, : ] )
    #end for axial levels

    return  avg
  #end Calc1DAxialAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc1DAxialAverage_()			-
  #----------------------------------------------------------------------
  def Calc1DAxialAverage_( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates 1D radial averages over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nax )
"""
    avg = np.ndarray( ( core.nax, ), np.float64 )
    avg.fill( 0.0 )

    for k in range( core.nax ):
      sum_weights = 0.0

      for i in range( core.nass ):
        for x in range( core.npin ):
          for y in range( core.npin ):
	    local_wt = pin_factors[ y, x, k, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, k, i ]

	    avg[ k ] += data_in[ y, x, k, i ] * local_wt
	    sum_weights += local_wt
          #end for rows
        #end for cols
      #end for assemblies

      if sum_weights > 0.0:
        avg[ k ] /= sum_weights
      else:
        avg[ k ] = 0.0
    #end for axial levels

    return  avg
  #end Calc1DAxialAverage_


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc2DAssyAverage()			-
  #----------------------------------------------------------------------
  def Calc2DAssyAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 2D axially averaged assembly values over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nass )
"""
    wts = \
        pin_factors * weights if pin_factors != None and weights != None else \
	pin_factors if pin_factors != None else \
	weights

    avg = np.ndarray( ( core.nass, ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      avg[ i ] = \
          np.average( data_in[ :, :, :, i ] )  if wts == None else \
          0.0  if np.sum( wts[ :, :, :, i ] ) == 0.0 else \
          np.average( data_in[ :, :, :, i ], weights = wts[ :, :, :, i ] )
    #end for assemblies

    return  avg
  #end Calc2DAssyAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc2DAssyAverage_()			-
  #----------------------------------------------------------------------
  def Calc2DAssyAverage_( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 2D axially averaged assembly values over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nass )
"""
    avg = np.ndarray( ( core.nass, ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      sum_weights = 0.0

      for x in range( core.npin ):
        for y in range( core.npin ):
          for k in range( core.nax ):
	    local_wt = pin_factors[ y, x, k, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, k, i ]

	    avg[ i ] += data_in[ y, x, k, i ] * local_wt
	    sum_weights += local_wt
          #end for axial levels
        #end for rows
      #end for cols

      if sum_weights > 0.0:
        avg[ i ] /= sum_weights
      else:
        avg[ i ] = 0.0
    #end for assemblies

    return  avg
  #end Calc2DAssyAverage_


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc2DPinAverage()			-
  #----------------------------------------------------------------------
  def Calc2DPinAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 2D pin axial averages over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( npiny, npinx, nass )
"""
    wts = \
        pin_factors * weights if pin_factors != None and weights != None else \
	pin_factors if pin_factors != None else \
	weights

    avg = np.ndarray( ( core.npiny, core.npinx, core.nass ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      for x in range( core.npin ):
        for y in range( core.npin ):
          avg[ y, x, i ] = \
	      np.average( data_in[ y, x, :, i ] )  if wts == None else \
	      0.0  if np.sum( wts[ y, x, :, i ] ) == 0.0 else \
	      np.average( data_in[ y, x, :, i ], weights = wts[ y, x, :, i ] )
        #end for rows
      #end for cols
    #end for assemblies

    return  avg
  #end Calc2DPinAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc2DPinAverage_()			-
  #----------------------------------------------------------------------
  def Calc2DPinAverage_( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 2D pin axial averages over a 4D dataset
@param  core		datamodel.Core object or any object with properties:
			'nass', 'nax', 'npinx', 'npiny'
			cannot be None
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nax, nass )
"""
    avg = np.ndarray( ( core.npiny, core.npinx, core.nass ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      for x in range( core.npin ):
        for y in range( core.npin ):
          sum_weights = 0.0

          for k in range( core.nax ):
	    local_wt = pin_factors[ y, x, k, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, k, i ]

	    avg[ y, x, i ] += data_in[ y, x, k, i ] * local_wt
	    sum_weights += local_wt
          #end for axial levels

	  if sum_weights > 0.0:
	    avg[ y, x, i ] /= sum_weights
          else:
	    avg[ y, x, i ] = 0.0
        #end for rows
      #end for cols
    #end for assemblies

    return  avg
  #end Calc2DPinAverage_


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc3DAssyAverage()			-
  #----------------------------------------------------------------------
  def Calc3DAssyAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 3D assembly average over a 4D dataset
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'nass', 'nax', 'npin'
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nax, nass )
"""
    wts = \
        pin_factors * weights if pin_factors != None and weights != None else \
	pin_factors if pin_factors != None else \
	weights

    avg = np.ndarray( ( core.nax, core.nass ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      for k in range( core.nax ):
        avg[ k, i ] = \
	    np.average( data_in[ :, :, k, i ] )  if wts == None else \
	    0.0  if np.sum( wts[ :, :, k, i ] ) == 0.0 else \
	    np.average( data_in[ :, :, k, i ], weights = wts[ :, :, k, i ] )
      #end for axial levels
    #edd for assemblies

    return  avg
  #end Calc3DAssyAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.Calc3DAssyAverage_()			-
  #----------------------------------------------------------------------
  def Calc3DAssyAverage_( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a 3D assembly average over a 4D dataset
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'nass', 'nax', 'npin'
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			numpy.ndarray with shape ( nax, nass )
"""
    avg = np.ndarray( ( core.nax, core.nass ), np.float64 )
    avg.fill( 0.0 )

    for i in range( core.nass ):
      for k in range( core.nax ):
        sum_weights = 0.0

	for x in range( core.npin ):
	  for y in range( core.npin ):
	    local_wt = pin_factors[ y, x, k, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, k, i ]

	    avg[ k, i ] += data_in[ y, x, k, i ] * local_wt
	    sum_weights += local_wt
          #end for rows
        #end for cols

	if sum_weights > 0.0:
	  avg[ k, i ] /= sum_weights
        else:
	  avg[ k, i ] = 0.0
      #end for axial levels
    #edd for assemblies

    return  avg
  #end Calc3DAssyAverage_


  #----------------------------------------------------------------------
  #	METHOD:		Averager.CalcGeneralAverage()			-
  #----------------------------------------------------------------------
  def CalcGeneralAverage( self, data_in, avg_shape, factors = None, weights = None ):
    """Calculates any average, preserving the original dimensionality of
data_in.
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  avg_shape	tuple defining the shape of the result, with 1 for
			the axes across which averages will be computed,
			must be of the same length of data_in.shape with
			no zeros, cannot be None
@param  factors		optional factors (numpy.ndarray) to apply, must have
			the same shape as data_in
@param  weights		optional weights (numpy.ndarray) to apply, must have
			the same shape as data_in
@return			numpy.ndarray of shape avg_shape with averaged values
@exception		if any of the shape/size assertions fail
"""
#	-- Assertions
#	--
    if len( avg_shape ) != len( data_in.shape ):
      raise Exception( 'Average shape must have same length as data shape' )

    if np.count_nonzero( avg_shape ) != len( avg_shape ):
      raise Exception( 'Average shape cannot have zeros' )

    if factors != None and factors.shape != data_in.shape:
      raise Exception( 'Factors must have same shape as data' )

    if weights != None and weights.shape != data_in.shape:
      raise Exception( 'Weights must have same shape as data' )

#	-- Resolve factors and weights
#	--
    wts = \
        factors * weights if factors != None and weights != None else \
	factors if factors != None else \
	weights

    avg = np.ndarray( avg_shape, np.float64 )
    avg.fill( 0.0 )

#	-- Determine flattened axes
#	--
    flat_indexes = filter(
        lambda x: avg_shape[ x ] == 1,
	range( len( avg_shape ) )
	)

    indent = ''
    exec_str = ''
    data_expr = '['
    for axis_ndx in range( len( avg_shape ) ):
      if axis_ndx > 0:
        data_expr += ','

      if avg_shape[ axis_ndx ] == 1:
        data_expr += ':'
      else:
	var = 'i' + str(axis_ndx)
        data_expr += var
	s = '%sfor %s in range( data_in.shape[ %d ] ):\n' % \
	    ( indent, var, axis_ndx )
        exec_str += s
        indent += '  '
      #end if-else
    #for axis_ndx

    data_expr += ']'
    avg_expr = data_expr.replace( ':', '0' )

    s = """%savg%s = \\
    np.average( data_in%s )  if wts == None else \\
    0.0  if np.sum( wts%s ) == 0.0 else \\
    np.average( data_in%s, weights = wts%s )
"""
    exec_str += \
        s % ( indent, avg_expr, data_expr, data_expr, data_expr, data_expr )

    fd, name = tempfile.mkstemp( '.avg' )
    try:
      fp = os.fdopen( fd, 'w' )
      try:
        fp.write( exec_str )
      finally:
        fp.close()

      execfile( name )

    finally:
      os.remove( name )

    return  avg
  #end CalcGeneralAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.CalcScalarAverage()			-
  #----------------------------------------------------------------------
  def CalcScalarAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a scalar average over a 4D dataset
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'nass', 'nax', 'npin'
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			scalar weighted average
"""

    wts = \
        pin_factors * weights if pin_factors != None and weights != None else \
	pin_factors if pin_factors != None else \
	weights
    avg = \
	np.average( data_in )  if wts == None else \
	0.0  if np.sum( wts ) == 0.0 else \
        np.average( data_in, weights = wts )
    return  avg
  #end CalcScalarAverage


  #----------------------------------------------------------------------
  #	METHOD:		Averager.CalcScalarAverage_()			-
  #----------------------------------------------------------------------
  def CalcScalarAverage_( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a scalar average over a 4D dataset
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'nass', 'nax', 'npin'
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
@return			scalar weighted average
"""
    avg = 0.0

    sum_weights = 0.0
    for i in range( core.nass ):
      for k in range( core.nax ):
        for y in range( core.npin ):
	  for x in range( core.npin ):
	    local_wt = pin_factors[ y, x, k, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, k, i ]

	    avg += data_in[ y, x, k, i ] * local_wt
	    sum_weights += local_wt
	  #end for columns
        #end for rows
      #end for axial levels
    #end for assemblies

    if sum_weights > 0.0:
      avg /= sum_weights
    else:
      avg = 0.0

    return  avg
  #end CalcScalarAverage_


  #----------------------------------------------------------------------
  #	METHOD:		Averager.CreateCorePinFactors()			-
  #----------------------------------------------------------------------
  def CreateCorePinFactors( self, core ):
    """Creates a pin factors np.ndarray for the current config properties:
coreSym, npiny, npinx, nax, and nass.
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'axialMesh',
			'coreMap', 'coreSym', 'nass', 'nassx', 'nassy',
			'nax', 'npinx', 'npiny'
@return			np.ndarray with shape ( npiny, npinx, nax, nass ) or
			None if any of the properties are 0
"""
    factors = None
    if core != None and core.coreSym > 0 and \
        core.nass > 0 and core.nax > 0 and \
	core.npinx > 0 and core.npiny > 0 and \
	core.axialMesh != None and core.axialMesh.shape[ 0 ] == core.nax + 1:
      factors = np.ndarray(
          ( core.npiny, core.npinx, core.nax, core.nass ),
	  np.float32
	  )
      factors.fill( 0.0 )

      for k in range( core.nax ):
        factors[ :, :, k, : ] = core.axialMesh[ k + 1 ] - core.axialMesh[ k ]

#		-- Quarter core symmetry
#		--
      if core.coreSym == 4:
#			-- Account for odd number of assemblies and pins in
#			-- Y dimension
        if (core.nassy % 2) == 1 and (core.npiny % 2) == 1:
	  mid_pin_row = (core.npiny - 1) / 2
	  mid_assy_row = (core.nassy - 1) / 2
          #mid_pin_row = (core.npiny + 1) / 2 - 1
	  #mid_assy_row = (core.nassy + 1) / 2 - 1

#				-- Loop over top row of SE quadrant
	  xstart = (core.nassx + (core.nassx % 2)) / 2 - 1
          for i in range( xstart, core.nassx ):
	    assy_ndx = core.coreMap[ mid_assy_row, i ] - 1

	    factors[ mid_pin_row, 0 : core.npinx, 0 : core.nax, assy_ndx ] /= 2.0
#	    for k in range( core.nax ):
#	      for x in range( core.npinx ):
#	        factors[ mid_pin_row, x, k, assy_ndx ] /= 2.0
#	      #for pin columns
#	    #end for axial
	  #end for assembly quadrant columns
        #end if

        if (core.nassx % 2) == 1 and (core.npinx % 2) == 1:
          mid_pin_col = (core.npinx - 1) / 2
	  mid_assy_col = (core.nassx - 1) / 2
          #mid_pin_col = (core.npinx + 1) / 2 - 1
	  #mid_assy_col = (core.nassx + 1) / 2 - 1

#				-- Loop over left col of SE quadrant
	  ystart = (core.nassy + (core.nassy % 2)) / 2 - 1
          for j in range( ystart, core.nassy ):
	    assy_ndx = core.coreMap[ mid_assy_col, j ] - 1

	    factors[ 0 : core.npiny, mid_pin_col, 0 : core.nax, assy_ndx ] /= 2.0
#	    for k in range( core.nax ):
#	      for y in range( core.npiny ):
#	        factors[ y, mid_pin_col, k, assy_ndx ] /= 2.0
#	      #for pin rows
#	    #end for axial
	  #end for assembly quadrant rows
        #end if

#		-- Eighth core symmetry
#		--
      elif core.coreSym == 8:
#			-- Account for odd number of assemblies and pins in
#			-- Y dimension
        if (core.nassy % 4) == 3 and (core.npiny % 4) == 3:
	  pin_row_offset = (core.npiny - 1) / 4
	  mid_pin_row = core.npiny - 1 - pin_row_offset
	  assy_row_offset = (core.nassy - 1) / 4
	  mid_assy_row = core.nassy - 1 - assy_row_offset

#				-- Loop over top row of SE quadrant
	  xstart = (core.nassx + (core.nassx % 4)) / 4 - 1
          for i in range( xstart, core.nassx ):
	    assy_ndx = core.coreMap[ mid_assy_row, i ] - 1

	    factors[ mid_pin_row, 0 : core.npinx, 0 : core.nax, assy_ndx ] /= 2.0
	  #end for assembly quadrant columns
        #endif

        if (core.nassx % 4) == 3 and (core.npinx % 4) == 3:
	  pin_col_offset = (core.npinx - 1) / 4
          mid_pin_col = core.npinx - 1 - pin_col_offset
	  assy_col_offset = (core.nassx - 1) / 4
	  mid_assy_col = core.nassx - 1 - assy_col_offset

#				-- Loop over left col of SE quadrant
	  ystart = (core.nassy + (core.nassy % 4)) / 4 - 1
          for j in range( ystart, core.nassy ):
	    assy_ndx = core.coreMap[ mid_assy_col, j ] - 1

	    factors[ 0 : core.npiny, mid_pin_col, 0 : core.nax, assy_ndx ] /= 2.0
	  #end for assembly quadrant rows
	#endif
      #end if-else core.coreSym

#      factors.fill( 1.0 )
#      factors[ 0, :, :, : ] = 1.0 / core.coreSym
#      factors[ :, 0, :, : ] = 1.0 / core.coreSym
#      factors[ 0, 0, :, : ] /= core.coreSym
    #end if

    return  factors
  #end CreateCorePinFactors


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Averager.main()					-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      if len( sys.argv ) < 2:
        print >> sys.stderr, 'Usage: datamodel.py casl-output-fname'

      else:
        data = DataModel( sys.argv[ 1 ] )
	print str( data )
      #end if-else

    except Exception, ex:
      print >> sys.stderr, str( ex )
      et, ev, tb = sys.exc_info()
      while tb:
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
  #end main
#end Averager


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  Averager.main()
