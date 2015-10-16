#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		averager.py					-
#	HISTORY:							-
#		2015-10-05	leerw@ornl.gov				-
#		2015-10-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, traceback
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
			or any object with properties: 'coreSym',
			'nass', 'nax', 'npinx', 'npiny'
@return			np.ndarray with shape ( npiny, npinx, nax, nass ) or
			None if any of the properties are 0
"""
    factors = None
    if core != None and core.coreSym > 0 and \
        core.nass > 0 and core.nax > 0 and \
	core.npinx > 0 and core.npiny > 0:
      factors = np.ndarray(
          ( core.npiny, core.npinx, core.nax, core.nass ),
	  np.float32
	  )
      factors.fill( 1.0 )
      factors[ 0, :, :, : ] = 1.0 / core.coreSym
      factors[ :, 0, :, : ] = 1.0 / core.coreSym
      factors[ 0, 0, :, : ] /= core.coreSym
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
