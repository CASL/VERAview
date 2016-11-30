#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		utils.py					-
#	HISTORY:							-
#		2016-11-30	leerw@ornl.gov				-
#	  Moved FindListIndex() here from DataModel.
#		2016-09-19	leerw@ornl.gov				-
#	  Fixed FormatFloat{23}() to never call math.log() on zero.
#		2015-12-22	leerw@ornl.gov				-
#	  Added NormalizeValueLabels().
#		2015-04-11	leerw@ornl.gov				-
#	  Added defaultDataSetName property.
#		2014-12-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, math, os, sys
import pdb


#------------------------------------------------------------------------
#	CLASS:		DataUtils					-
#------------------------------------------------------------------------
class DataUtils( object ):
  """
"""


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		FindListIndex()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FindListIndex( values, value ):
    """Values in the list are assumed to be in order, either ascending or
descending.  Note bisect only does ascending.
@param  values		list of values
@param  value		value to search
@return			0-based index N, values[ N ]
			'a': values[ N ] <= value < values[ N + 1 ]
			'd': values[ N ] >= value > values[ N + 1 ]
"""
    match_ndx = -1

    if values is not None and len( values ) > 0:
#			-- Descending
      if values[ 0 ] > values[ -1 ]:
        match_ndx = \
	    len( values ) - 1 - bisect.bisect_left( sorted( values ), value )
        match_ndx = max( 0, min( match_ndx, len( values ) - 1 ) )
#        lo = 0
#	hi = len( values )
#        while lo < hi:
#	  mid = ( lo + hi ) // 2
#          if value > values[ mid ]:  hi = mid
#          else:  lo = mid + 1
#        match_ndx = min( lo, len( values ) - 1 )

#			-- Ascending
      else:
	match_ndx = bisect.bisect_right( values, value ) - 1
	match_ndx = max( 0, min( match_ndx, len( values ) - 1 ) )
#        match_ndx = min(
#            bisect.bisect_left( values, value ),
#	    len( values ) - 1
#	    )
    #end if not empty list

    return  match_ndx
  #end FindListIndex


  #----------------------------------------------------------------------
  #	METHOD:		FormatFloat1()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FormatFloat1( value, size = 3 ):
    result1 = ('%%.%dg' % size) % value
    result2 = ('%%%dg' % size) % value
    return  result2 if len( result2 ) <= len( result1 ) else result1
  #end FormatFloat1


  #----------------------------------------------------------------------
  #	METHOD:		FormatFloat2()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FormatFloat2( value, size = 3 ):
    if value < 0.0:
      neg_flag = True
      value = abs( value )
    else:
      neg_flag = False

    size = max( 1, size )
    fexp = \
        0.0  if value == 0.0 else \
        math.log( value ) / math.log( 10 )
    exp = int( fexp )
    if fexp < 0.0:
      exp -= 1

    basis = math.pow( 10.0, exp )
    shift_exp = size - 2 if neg_flag else size - 1
    shift = math.pow( 10.0, shift_exp )

    ivalue = int( value / basis * shift * 10.0 )
    ones = ivalue % 10
    ivalue /= 10
    if ones >= 5:
      ivalue += 1

    value = ivalue / shift * basis
    result = ('%%.%dg' % size) % value
    if result.startswith( '0.' ):
      result = result[ 1 : ]

    if neg_flag:
      result = '-' + result
    return  result
  #end FormatFloat2


  #----------------------------------------------------------------------
  #	METHOD:		FormatFloat3()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FormatFloat3( value, size = 3 ):
    if value < 0.0:
      neg_flag = True
      value = abs( value )
    else:
      neg_flag = False

    size = max( 1, size )
    fexp = \
        0.0  if value == 0.0 else \
        math.log( value ) / math.log( 10 )
    exp = int( fexp )
    if fexp < 0.0:
      exp -= 1

    basis = math.pow( 10.0, exp )
    shift_exp = size - 2 if neg_flag else size - 1
    shift = math.pow( 10.0, shift_exp )

    ivalue = int( value / basis * shift * 10.0 )
    ones = ivalue % 10
    ivalue /= 10
    if ones >= 5:
      ivalue += 1

    value = ivalue / shift * basis
    result = ('%%.%dg' % size) % value
    if result.startswith( '0.' ):
      result = result[ : -1 ]

    if neg_flag:
      result = '-' + result
    return  result
  #end FormatFloat3


  #----------------------------------------------------------------------
  #	METHOD:		NormalizeValueLabels()				-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeValueLabels( labels ):
    """Reformats labels to have a consisten size and number of decimal places.
@param  labels		list of labels, updated in-line
@return			labels parameter
"""
#		-- Noop if no labels
#		--
    if labels is not None and len( labels ) > 0:
#			-- Find longest, count labels with exponents
#			--
      longest = None
      for label in labels:
        if longest is None or len( label ) > len( longest ):
          longest = label
      #end for
#			-- Exponent?
#			--
      #pdb.set_trace()
      e_ndx = longest.find( 'e' )
      if e_ndx >= 0:
        longest = longest[ : e_ndx ]

#			-- Determine number of decimals
#			--
      dot_ndx = longest.find( '.' )
      decimals = len( longest ) - 1 - dot_ndx  if dot_ndx >= 0  else 0

#			-- Fix labels
#			--
      for i in range( len( labels ) ):
        cur_label = labels[ i ]
	e_ndx = cur_label.find( 'e' )
	mantissa = cur_label[ : e_ndx ]  if e_ndx >= 0  else cur_label

        dot_ndx = mantissa.find( '.' )
	cur_decimals = len( mantissa ) - 1 - dot_ndx  if dot_ndx >= 0  else 0

	if cur_decimals < decimals:
	  new_label = \
	      cur_label[ : e_ndx ]  if e_ndx >= 0  else \
	      cur_label
	  if dot_ndx < 0:
	    new_label += '.'

          new_label += '0' * (decimals - cur_decimals)

	  if e_ndx >= 0:
            new_label += cur_label[ e_ndx : ]

          labels[ i ] = new_label
        #end if adding decimals
      #end for
    #end if we have labels
  #end NormalizeValueLabels

#end DataUtils
