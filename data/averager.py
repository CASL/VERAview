#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		averager.py					-
#	HISTORY:							-
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
  #	METHOD:		Averager.CalcScalarAverage()			-
  #----------------------------------------------------------------------
  def CalcScalarAverage( self, core, data_in, pin_factors = None, weights = None ):
    """Calculates a scalar average over a 4D dataset
@param  core		datamodel.Core object, cannot be None
			or any object with properties: 'nass', 'nax', 'npin'
@param  data_in		dataset (numpy.ndarray) to average, cannot be None
@param  pin_factors	optional pin factors (numpy.ndarray) to apply
@param  weights		optional weights (numpy.ndarray) to apply
"""
    avg = 0.0

    sum_weights = 0.0
    for i in range( core.nass ):
      for j in range( core.nax ):
        for y in range( core.npin ):
	  for x in range( core.npin ):
	    local_wt = pin_factors[ y, x, j, i ] if pin_factors != None else 1.0
	    if weights != None:
	      local_wt *= weights[ y, x, j, i ]

	    avg += data_in[ y, x, j, i ] * local_wt
	    sum_weights += local_wt
	  #end for columns
        #end for rows
      #end for axial levels
    #end for assemblies

    if sum_weights > 0.0:
      avg /= sum_weights

    return  avg
  #end CalcScalarAverage


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
