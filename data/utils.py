#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		utils.py					-
#	HISTORY:							-
#		2017-01-12	leerw@ornl.gov				-
#	  Marginal improvement in NormalizeValueLabels() to account for
#	  exponential and non-exponential labels.
#		2016-12-28	leerw@ornl.gov				-
#	  Added DeepCopy().
#		2016-12-13	leerw@ornl.gov				-
#	  Added GetDataSetTypeDisplayName().
#	  Added mode param to FindListIndex().
#		2016-12-12	leerw@ornl.gov				-
#	  Moved IsValidRange(), ToAddrString() here from DataModel.
#	  Added NormalizeNodeAddr{s}().
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
import bisect, copy, logging, math, os, sys
import numpy as np
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
  #	METHOD:		CalcDistance()					-
  #----------------------------------------------------------------------
  @staticmethod
  def CalcDistance( x1, y1, x2, y2 ):
    """
"""
    dx = x2 - x1
    dy = y2 - y1
    return  math.sqrt( (dx * dx ) + (dy * dy) )
  #end CalcDistance


  #----------------------------------------------------------------------
  #	METHOD:		DeepCopy()					-
  #----------------------------------------------------------------------
  @staticmethod
  def DeepCopy( obj ):
    """Performs a deep copy calling copy.deepcopy() and np.copy(), checking
for items in obj.__dict__ that are of type np.ndarray.
"""
    new_obj = obj.__class__()

    for name, value in obj.__dict__.iteritems():
      if isinstance( value, np.ndarray ):
        new_value = np.copy( value )
      else:
        new_value = copy.deepcopy( value )
      setattr( new_obj, name, new_value )
    #end for

    return  new_obj
  #end DeepCopy


  #----------------------------------------------------------------------
  #	METHOD:		FindListIndex()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FindListIndex( values, value, mode = None ):
    """Values in the list are assumed to be in order, either ascending or
descending.  Note bisect only does ascending.
@param  values		list of values
@param  value		value to search
@param  mode		'a' for ascending, 'd' for descending, None if unknown
@return			0-based index N, where
			'a': values[ N ] <= value < values[ N + 1 ]
			'd': values[ N ] >= value > values[ N + 1 ]
"""
    match_ndx = -1

    if values is not None and len( values ) > 0:
      if not mode:
        mode = 'd' if values[ 0 ] > values[ -1 ] else 'a'

#			-- Descending
      #if values[ 0 ] > values[ -1 ]:
      if mode == 'd':
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
  #	METHOD:		DataUtils.CreateDerivedTypeName()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateDerivedTypeName( derived_label ):
    """Compliment to GetDataSetTypeDisplayName() to create a derived type.
@param  derived_label	derived type label/name
@return			type name
"""
    return  ':' + derived_label
  #end CreateDerivedTypeName


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.GetDataSetTypeDisplayName()		-
  #----------------------------------------------------------------------
  @staticmethod
  def GetDataSetTypeDisplayName( ds_type ):
    """Strips any derived prefix.  Best to encapsulate this here.  Note this
must match how _CreateDerivedNames() builds the derived type name.
@param  ds_type		category/type
@return			type name sans any derived marking
"""
#    if ds_type and ds_type.find( ':' ) == 0:
#      ds_type = ds_type[ 1 : ]
#		-- Safer version
    if ds_type:
      ndx = ds_type.find( ':' )
      if ndx >= 0:
        ds_type = ds_type[ ndx + 1 : ]
    return  ds_type
  #end GetDataSetTypeDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.IsValidRange()			-
  #----------------------------------------------------------------------
  @staticmethod
  def IsValidRange( min_value, max_value ):
    """Companion to GetDataRange() to check for a valid range as not
[-sys.float_info.max or sys.float_info.max] and min_value ne max_value.
@param  min_value	minimum value in range
@param  max_value	maximum value in range
@return			True if valid, False otherwise
"""
    return  \
        min_value != -sys.float_info.max and \
	max_value != sys.float_info.max and \
	min_value != max_value
  #end IsValidRange


  #----------------------------------------------------------------------
  #	METHOD:		NormalizeNodeAddr()				-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeNodeAddr( ndx ):
    """Here for completeness.
@param  ndx		0-based index
"""
    return  max( 0, min( 3, ndx ) )
  #end NormalizeNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		NormalizeNodeAddrs()				-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeNodeAddrs( addr_list ):
    """Normalizes each index in the list.
@param  addr_list	list of 0-based indexes
"""
    result = []
    for addr in addr_list:
      result.append( max( 0, min( 3, addr ) ) )

    return  list( set( result ) )
  #end NormalizeNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		NormalizeValueLabels()				-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeValueLabels( labels ):
    """Reformats labels to have a consistent size and number of decimal places.
@param  labels		list of labels, updated in-line
@return			labels parameter
"""
#		-- Noop if no labels
#		--
    if labels is not None and len( labels ) > 0:
#			-- Find longest, count labels with exponents
#			--
      longest_e = longest_noe = None
      for label in labels:
        e_ndx = label.find( 'e' )
	if e_ndx >= 0:
	  if longest_e is None or len( label ) > len( longest_e ):
	    longest_e = label
	elif longest_noe is None or len( label ) > len( longest_noe ):
	  longest_noe = label
      #end for label
#			-- Determine number of decimals
#			--
      decimals_e = 0
      if longest_e:
        e_ndx = longest_e.find( 'e' )
	longest_e = longest_e[ : e_ndx ]
        dot_ndx = longest_e.find( '.' )
	if dot_ndx >= 0:
	  decimals_e = len( longest_e ) - 1 - dot_ndx

      decimals_noe = 0
      if longest_noe:
        dot_ndx = longest_noe.find( '.' )
	if dot_ndx >= 0:
	  decimals_noe = len( longest_noe ) - 1 - dot_ndx

#			-- Fix labels
#			--
      for i in range( len( labels ) ):
        cur_label = labels[ i ]
	e_ndx = cur_label.find( 'e' )

	if e_ndx >= 0:
	  mantissa = cur_label[ : e_ndx ]
	  decimals = decimals_e
	  e_suffix = cur_label[ e_ndx : ]
	else:
	  mantissa = cur_label
	  decimals = decimals_noe
	  e_suffix = ''

        dot_ndx = mantissa.find( '.' )
	cur_decimals = len( mantissa ) - 1 - dot_ndx  if dot_ndx >= 0  else 0

	if cur_decimals < decimals:
	  new_label = mantissa
	  if dot_ndx < 0:
	    new_label += '.'

          new_label += '0' * (decimals - cur_decimals)
	  new_label += e_suffix

          labels[ i ] = new_label
        #end if adding decimals
      #end for
    #end if we have labels
  #end NormalizeValueLabels


  #----------------------------------------------------------------------
  #	METHOD:		NormalizeValueLabels_0()			-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeValueLabels_0( labels ):
    """Reformats labels to have a consistent size and number of decimal places.
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
      long_e_ndx = longest.find( 'e' )
      if long_e_ndx >= 0:
        longest = longest[ : long_e_ndx ]

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
  #end NormalizeValueLabels_0


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.ToAddrString()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ToAddrString( col, row ):
    """Convenience method to convert from 0-based indices to Fortran
1-based indices.
@param  col		0-based column index
@param  row		0-based row index
@return			"( col + 1, row + 1 )"
"""
    #return  '(%d,%d)' % ( col + 1, row + 1 )
    return  \
        '(%d,%d)' % ( col + 1, row + 1 )  if row >= 0 else \
        '(%d)' % (col + 1)
  #end ToAddrString

#end DataUtils
