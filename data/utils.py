#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		utils.py					-
#	HISTORY:							-
#		2018-10-19	leerw@ornl.gov				-
#	  Fixed CalcEqualAreaRadii().
#		2018-10-18	leerw@ornl.gov				-
#	  Moved FixDuplicates() from DataModel.
#		2018-08-24	leerw@ornl.gov				-
#	  Added CalcEqualAreaRadii().
#		2018-08-21	leerw@ornl.gov				-
#	  Added ToString().
#		2018-05-21	leerw@ornl.gov				-
#	  Added CreatedDerivedMethodName().
#		2018-02-26	leerw@ornl.gov				-
#	  Added GetNodeAddr() for documentation purposes.
#		2017-12-15	leerw@ornl.gov				-
# 	  Added CreateDataSetExpr().
#		2017-10-25	leerw@ornl.gov				-
#	  Fixed bug in MergeLists() not handling duplicate values.
#		2017-07-17	leerw@ornl.gov				-
#	  Added DataUtils.ApplyIgnoreExpression().
#		2017-06-07	leerw@ornl.gov				-
#	  Added MergeLists().
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

NODE_INDEXES = ( ( 0, 1 ), ( 2, 3 ) )

PI_OVER_2 = math.pi / 2.0

RADS_PER_DEG = math.pi / 180.0

REGEX_WS = re.compile( '[\s,]+' )

TWO_PI = math.pi * 2.0


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
  #	METHOD:		CreateDataSetExpr()				-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateDataSetExpr( ds_shape, *ndx_value_pairs ):
    """
"""
    expr_items = [ ':' for i in xrange( len( ds_shape ) ) ]
    if ndx_value_pairs:
      for pair in ndx_value_pairs:
        if pair[ 0 ] >= 0 and pair[ 0 ] < len( ds_shape ):
	  expr_items[ pair[ 0 ] ] = str( pair[ 1 ] )
    #end if ndx_value_pairs

    expr = '[' + ','.join( expr_items ) + ']'
    return  expr
  #end CreateDataSetExpr


  #----------------------------------------------------------------------
  #	METHOD:		CalcEqualAreaRadii()				-
  #----------------------------------------------------------------------
  @staticmethod
  def CalcEqualAreaRadii( diameter, nrings ):
    """Assumes the radii start at zero.
    Args:
        diameter (float): total diameter of area for radii
	nrings (int): number of rings
    Returns:
        list(float): nrings + 1 values from inside to outside (low to high)
"""
    total_area = math.pi * math.pow( diameter / 2.0, 2.0 )
    bin_area = total_area / nrings  if nrings > 0 else  total_area
    term = bin_area / math.pi
    r = math.sqrt( term )
    radii = [ 0.0, r ]
    for i in range( nrings - 1 ):
      r = math.sqrt( term + (r * r) )
      radii.append( r )
    return  radii
  #end CalcEqualAreaRadii


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
	    len( values ) - bisect.bisect_left( sorted( values ), value )
	    #len( values ) - 1 - bisect.bisect_left( sorted( values ), value )
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
  #	METHOD:		FixDuplicates()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FixDuplicates( values, order = 'a' ):
    """Creates a new list with no duplicate values.  Duplicate values in
sequence are changed, either to a higher value if order is 'a' or a lower
value if order is 'd'.  The values are such that order is preserved, and
the changes are as insignificant as feasible.
    Args:
        values (iterable): list or iterable of values to dedup
	order (char): 'a' for ascending, 'd' for descending
    Returns:
        list: values dedup'd
"""
#		-- Assert on iterable
#		--
    assert hasattr( values, '__iter__' ), 'Values must be iterable'

    values_list = values  if isinstance( values, list ) else  list( values )
    result = []

    pivot_ndx = -1
    pivot_value = dedup_value = None
    for i in xrange( len( values_list ) ):
      cur_value = values_list[ i ]

      if pivot_ndx < 0 or cur_value != pivot_value:
        pivot_ndx = i
	pivot_value = dedup_value = cur_value
      else:
        #base_value = dedup_value * 1.000000001
	base_value = \
            0.000000001  if dedup_value == 0.0 else \
	    dedup_value * 1.000000001
	if i < len( values_list ) - 1 and \
	    values_list[ i + 1 ] != pivot_value and \
	    base_value >= values_list[ i + 1 ]:
	  base_value = (dedup_value + values_list[ i + 1 ]) / 2.0
        cur_value = dedup_value = base_value

      result.append( cur_value )
    #end for i

    return  result
  #end FixDuplicates


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
  #	METHOD:		DataUtils.CreateDerivedMethodName()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateDerivedMethodName( ds_category, derived_label, agg_name = 'avg' ):
    """Creates the method name from the parameters with format
"calc_[ds_category]_[derived_label]_[agg_name]"
    Args:
        ds_category (str): dataset category, e.g., 'channel', 'pin'
	derived_label (str): derived label, e.g., 'assembly', 'axial', 'core',
	    'radial'
        agg_name (str): name of aggration function, e.g., 'avg', 'max', 'min'
    Returns:
        str:  method name
"""
    name = '{0:s}_{1:s}_{2:s}_{3:s}'.\
        format( ds_category, derived_label, agg_name )
    return  name
  #end CreateDerivedMethodName


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
#    if ds_type:
#      ds_type = ds_type[ ds_type.find( ':' ) + 1 : ]

#		-- Safer version
    if ds_type and ds_type[ 0 ] == ':':
      ds_type = ds_type[ 1 : ]
    return  ds_type
  #end GetDataSetTypeDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.GetNodeAddr()				-
  #----------------------------------------------------------------------
  def GetNodeAddr( self, col, row ):
    """Returns the index in range [0,3] for the node col and row.
    Args:
      col (int): 0-based node column
      row (int): 0-based node row
    Returns:
      int: index in range [0,3]
"""
    col = max( 0, min( col, 1 ) )
    row = max( 0, min( row, 1 ) )
    return  NODE_INDEXES[ row ][ col ]
  #end GetNodeAddr


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
	  if ndx < 1 or master[ ndx - 1 ] != v:
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
  def ToAddrString( *args ):
    """Convenience method to convert from 0-based indices to Fortran
1-based indices.
    Args:
        args (int list): list of indexes
    Returns:
        str: tuple representation
"""
    cur_list = [ i + 1 for i in args if i >= 0 ]
    result = str( tuple( cur_list ) )
    return  result.replace( ' ', '' )
  #end ToAddrString


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.ToAddrString1()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ToAddrString1( col, row ):
    """Convenience method to convert from 0-based indices to Fortran
1-based indices.
@param  col		0-based column index
@param  row		0-based row index
@return			"( col + 1, row + 1 )"
"""
    return  \
        '(%d,%d)' % ( col + 1, row + 1 )  if row >= 0 else \
        '(%d)' % (col + 1)
  #end ToAddrString1


  #----------------------------------------------------------------------
  #	METHOD:		DataUtils.ToString()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ToString( value ):
    """Convenience method to extract a string value.
    Args:
        value (?): scalar, array, or object
    Returns:
        str: string value, the first value if ``value`` is an array
"""
#    return \
#        str( value[ 0 ] )  if isinstance( value, np.ndarray ) else \
#	str( value[ 0 ] )  if hasattr( value, '__iter__' ) else \
#	str( value )
    result = ''

    if isinstance( value, np.ndarray ):
      result = value[ () ]  if len( value.shape ) == 0 else  value[ 0 ]
    elif hasattr( value, '__iter__' ):
      result = str( value[ 0 ] )
    else:
      result = str( value )

    return  result
  #end ToString

#end DataUtils
