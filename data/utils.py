#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		utils.py					-
#	HISTORY:							-
#		2017-07-17	leerw@ornl.gov				-
#	  Added DataUtils.ApplyIgnoreExpression().
#		2017-06-07	leerw@ornl.gov				-
#	  Added MergeLists(0.
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
import bisect, copy, logging, math, os, re, sys
import numpy as np
import pdb


NAN = float( 'nan' )

REGEX_WS = re.compile( '[\s,t]+' )


#------------------------------------------------------------------------
#	CLASS:		DataUtils					-
#------------------------------------------------------------------------
class DataUtils( object ):
  """
"""


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ApplyIgnoreExpression()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ApplyIgnoreExpression( arr, ignore_expr ):
    """Returns only the values not in the ignore range.  Useful for finding
min and max.
@param  arr		np.ndarray
@param  ingore_expr	ignore expression to apply to arr
@return			new np.ndarray
"""
    result = arr

    if ignore_expr:
      tokens = REGEX_WS.split( ignore_expr )
      where_str = var_name = None

      if len( tokens ) == 7 and tokens[ 3 ] == 'and':
	one = ' '.join( tokens[ : 3 ] )
	two = ' '.join( tokens[ 4 : ] )
        where_str = '({0:s}) & ({1:s})'.format( one, two )
	var_name = tokens[ 0 ]

      elif len( tokens ) == 3:
        where_str = ' '.join( tokens[ : 3 ] )
	var_name = tokens[ 0 ]

      if where_str and var_name:
	temp_array = arr[ np.logical_not( np.isnan( arr ) ) ]
	temp_array = np.reshape( temp_array, arr.shape )
        where_str = where_str.replace( var_name, 'temp_array' )

	eval_str = 'temp_array[ np.where( {0:s} ) ]'.format( where_str )
	result = eval( eval_str )
    #end if ignore_expr

    return  result
  #end ApplyIgnoreExpression


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
  #	METHOD:		ChangeIgnoreValues()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ChangeIgnoreValues( arr, ignore_expr, new_value = NAN ):
    """
@param  arr		np.ndarray
@param  ingore_expr	ignore expression to apply to data
@param  new_value	new value for values in the ignore range
@return			new np.ndarray
"""
    #result = np.copy( arr )
    result = arr

    if ignore_expr:
      tokens = REGEX_WS.split( ignore_expr )
      mask_str = var_name = None

      if len( tokens ) == 7 and tokens[ 3 ] == 'and':
	one = ' '.join( tokens[ : 3 ] )
	two = ' '.join( tokens[ 4 : ] )
        mask_str = '({0:s}) | ({1:s})'.format( one, two )
	var_name = tokens[ 0 ]

      elif len( tokens ) == 3:
        mask_str = ' '.join( tokens[ : 3 ] )
	var_name = tokens[ 0 ]

      if mask_str and var_name:
        temp_arr = np.copy( arr )
        mask_str = mask_str.replace( var_name, 'temp_arr' )
	eval_str = \
	    'np.logical_and( np.logical_not( np.isnan( temp_arr ) ), {0:s} )'.\
	    format( mask_str )
        temp_mask = eval( eval_str )
	np.place( temp_arr, temp_mask, new_value )
	result = temp_arr
      #end if mask_str and var_name
    #end if ignore_expr

    return  result
  #end ChangeIgnoreValues


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

    if values is not None and hasattr( values, '__iter__' ) and \
        len( values ) > 0:
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
    #result1 = ('%%.%dg' % size) % value
    #result2 = ('%%%dg' % size) % value
    result1 = ('{0:.%dg}' % size).format( value )
    result2 = ('{0:%dg}' % size).format( value )
    return  result2  if len( result2 ) <= len( result1 ) else  result1
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
    #result = ('%%.%dg' % size) % value
    fmt = '{0:.%dg}' % size
    result = fmt.format( value )
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
  #	METHOD:		FormatFloat4()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FormatFloat4( value, digits = 3, mode = 'general' ):
    """Used in raster widgets.
"""
    fmt_char = 'f' if mode and mode.startswith( 'fixed' ) else 'g'
    fmt = '{0:.%d%s}' % ( digits, fmt_char )
    result = fmt.format( value )
    return  result
  #end FormatFloat4


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
  #	METHOD:		DataUtils.MergeList()				-
  #----------------------------------------------------------------------
  @staticmethod
  def MergeList( master, *values ):
    """Updates master with values allowing duplicate values.
Both are assumed to be in ascending order.
@param  master		master list to update, created if necessary
@param  values		values to add
@return			master or new list if master is None
"""
    if values:
      if master is None:
        master = list( values )
      else:
        for v in values:
	  ndx = bisect.bisect_right( master, v )
	  master.insert( ndx, v )
	#end for v
    #end if values

    return  master
  #end MergeList


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.NormalizeNodeAddr()			-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeNodeAddr( ndx ):
    """Here for completeness.
@param  ndx		0-based index
"""
    return  max( 0, min( 3, ndx ) )
  #end NormalizeNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.NormalizeNodeAddrs()			-
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
  #	METHOD:		DataUtils.NormalizeValueLabels()		-
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
