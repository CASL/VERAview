#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		rangescaler.py					-
#	HISTORY:							-
#		2017-07-15	leerw@ornl.gov				-
#	  Added ForceSigDigits(), called in Format() for 'g' formatting.
#		2017-06-16	leerw@ornl.gov				-
#	  Fixed CreateLinearLabels() to check for excessively long
#	  labels.
#		2017-06-06	leerw@ornl.gov				-
#	  Fixed critical bug in CalcLinear() in loop to bring step_incr
#	  below max_value; the latter must be tested as abs( max_value ).
#		2017-04-01	leerw@ornl.gov				-
#	  Added AlignNumbers() and Format().
#		2017-03-11	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys
from decimal import *
import pdb


#------------------------------------------------------------------------
#	CLASS:		RangeScaler					-
#------------------------------------------------------------------------
class RangeScaler( object ):
  """
"""
#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    return  self.Calc( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self ):
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AlignNumbers()					-
  #----------------------------------------------------------------------
  def AlignNumbers( self, labels ):
    """Aligns a series of number labels by adding trailing zeros if needed.
@param  labels		labels to align
"""
    max_dec_count = -1
    for label in labels:
      dot_ndx = label.find( '.' )
      if dot_ndx >= 0:
        e_ndx = label.find( 'e' )
	end_ndx = len( label )  if e_ndx < 0 else  e_ndx
	max_dec_count = max( max_dec_count, end_ndx - dot_ndx - 1 )
    #end for i

    for i in xrange( len( labels ) ):
      e_ndx = labels[ i ].find( 'e' )
      end_ndx = len( labels[ i ] )  if e_ndx < 0 else  e_ndx

      dot_ndx = labels[ i ].find( '.' )
      dec_count = end_ndx - dot_ndx - 1  if dot_ndx >= 0 else  0

      if dec_count < max_dec_count:
        new_str = labels[ i ][ 0 : end_ndx ]
	if dot_ndx < 0:
	  new_str += '.'
        new_str += '0' * (max_dec_count - dec_count)
	if e_ndx >= 0:
	  new_str += labels[ i ][ e_ndx : ]
        labels[ i ] = new_str
    #end for i
  #end AlignNumbers


  #----------------------------------------------------------------------
  #	METHOD:		AlignNumbers_works()				-
  #----------------------------------------------------------------------
  def AlignNumbers_works( self, labels ):
    """Aligns a series of number labels by adding trailing zeros if needed.
@param  labels		labels to align
"""
    max_dec_count = -1
    for label in labels:
      dot_ndx = label.find( '.' )
      if dot_ndx >= 0:
        e_ndx = label.find( 'e' )
	end_ndx = len( label )  if e_ndx < 0 else  e_ndx
	max_dec_count = max( max_dec_count, end_ndx - dot_ndx - 1 )
    #end for i

    for i in xrange( len( labels ) ):
      dot_ndx = labels[ i ].find( '.' )
      e_ndx = labels[ i ].find( 'e' )
      if dot_ndx >= 0:
	end_ndx = len( labels[ i ] )  if e_ndx < 0 else  e_ndx
	dec_count = end_ndx - dot_ndx - 1
	if dec_count < max_dec_count:
	  new_str = \
	      labels[ i ][ 0 : end_ndx ] + '0' * (max_dec_count - dec_count)
	  if e_ndx >= 0:
	    new_str += labels[ i ][ e_ndx : ]
          labels[ i ] = new_str
      else:
	end_ndx = len( labels[ i ] )  if e_ndx < 0 else  e_ndx
	dec_count = 0
	if dec_count < max_dec_count:
	  new_str = \
	      labels[ i ][ 0 : end_ndx ] + '.' + \
	      '0' * (max_dec_count - dec_count)
	  if e_ndx >= 0:
	    new_str += labels[ i ][ e_ndx : ]
          labels[ i ] = new_str
      #end if-else dot_ndx
    #end for i
  #end AlignNumbers_works


  #----------------------------------------------------------------------
  #	METHOD:		Calc()						-
  #----------------------------------------------------------------------
  def Calc(
      self, min_value, max_value,
      max_steps = 8,
      cull_outside_range = False
      ):
    """Chooses to call CalcLinear() or CalcLog() based on value range.
@param  min_value	min value in range
@param  max_value	max value in range
@param  max_steps	maximum number of steps, result may be less
@param  cull_outside_range  if True, all steps outside the range are culled
"""
    log_flag = False
    if min_value > 0.0 and max_value > 0.0:
      min_scale = math.floor( math.log10( min_value ) )
      max_scale = math.floor( math.log10( max_value ) )
      log_flag = (max_scale - min_scale) > 3

    if log_flag:
      steps = self.\
          CalcLog( min_value, max_value, max_steps, cull_outside_range )
    else:
      steps = self.\
          CalcLinear( min_value, max_value, max_steps, cull_outside_range )

    return  steps
  #end Calc


  #----------------------------------------------------------------------
  #	METHOD:		CalcLinear()					-
  #----------------------------------------------------------------------
  def CalcLinear(
      self, min_value, max_value,
      max_steps = 8,
      cull_outside_range = False
      ):
    """Calculates a linear range.
@param  min_value	min value in range
@param  max_value	max value in range
@param  max_steps	maximum number of steps, result may be less
@param  cull_outside_range  if True, all steps outside the range are culled
@return		list of steps
"""
    if min_value > max_value:
      min_value = max_value
    steps = [ min_value ]
    max_steps = max( 2, max_steps )
    value_range = max_value - min_value
    value_incr = value_range / (max_steps - 1)
    value_incr_log = \
	0  if value_incr <= 0.0 else \
        math.floor( math.log10( value_incr ) )
    value_incr_base = math.pow( 10.0, value_incr_log )

    #factor = value_incr / value_incr_base
    factor = int( value_incr / value_incr_base + 0.5 )
    if factor > 5.0:
      factor = 10.0
    elif factor > 2.0:
      factor = 5.0
    elif factor > 1.0:
      factor = 2.0
    step_incr = factor * value_incr_base
    while step_incr > abs( max_value ):
      step_incr /= 2.0

    if step_incr > 0.0:
      step_count = max_steps + 1
      while step_count > max_steps:
        min_step = math.floor( min_value / step_incr ) * step_incr
        max_step = math.floor( max_value / step_incr ) * step_incr
        step_count = int( math.ceil( (max_step - min_step) / step_incr ) ) + 1
        if step_count > max_steps:
          step_incr *= 2.0

      steps = [ min_step + (i * step_incr) for i in xrange( step_count ) ]
      if cull_outside_range:
        steps = self.CullOutside( steps, min_value, max_value )
    #end if step_incr > 0.0

    return  steps
  #end CalcLinear


  #----------------------------------------------------------------------
  #	METHOD:		CalcLog()					-
  #----------------------------------------------------------------------
  def CalcLog(
      self, min_value, max_value,
      max_steps = 8,
      cull_outside_range = False
      ):
    """Calculates a logarithmic range.   Works for positive numbers only.
@param  min_value	min value in range, forced to 1 if le 0
@param  max_value	max value in range
@param  max_steps	maximum number of steps, result may be less
@param  cull_outside_range  if True, all steps outside the range are culled
@return		list of steps
"""
    max_steps = max( 2, max_steps )
    if min_value <= 0:
      min_value = 1.0
    min_scale = \
	0  if min_value <= 0.0 else \
        math.floor( math.log10( min_value ) )
    max_scale = \
	0  if max_scale <= 0.0 else \
        math.floor( math.log10( max_value ) )

    log_range = max_scale - min_scale
    if log_range == 0.0:
      steps = [ math.pow( 10.0, min_scale ) ]

    else:
      log_incr = math.ceil( log_range / (max_steps - 1) )
      step_count = int( math.floor( log_range / log_incr ) ) + 1
      step_power = math.pow( 10.0, log_incr )
      base_min = math.pow( 10.0, min_scale )
      steps = [ base_min ]
      for i in xrange( step_count - 1 ):
        base_min *= step_power
        steps.append( base_min )

      if cull_outside_range:
        steps = self.CullOutside( steps, min_value, max_value )
    #end if-else log_range

    return  steps
  #end CalcLog


  #----------------------------------------------------------------------
  #	METHOD:		CreateLinearLabels()				-
  #----------------------------------------------------------------------
  def CreateLinearLabels( self, steps ):
    """Creates labels for the step values.
@param  steps		steps for which labels are desire
@return			list of formatted string labels
"""
    min_value_scale = \
        0  if steps[ 0 ] <= 0.0 else \
        int( math.floor( math.log10( steps[ 0 ] ) ) )
    max_value_scale = \
        0  if steps[ -1 ] <= 0.0 else \
        int( math.floor( math.log10( steps[ -1 ] ) ) )
    min_scale = min( min_value_scale, max_value_scale )
    max_scale = max( min_value_scale, max_value_scale )

    pre_step = steps[ -2 ]  if len( steps ) > 2 else  steps[ 0 ]
    step_delta = steps[ -1 ] - pre_step
    delta_scale = \
	0  if step_delta <= 0.0 else \
        int( math.floor( math.log10( step_delta ) ) )

#		-- General
    #if min_scale < -2 or max_scale > 3:
    if delta_scale < -2 or delta_scale > 3:
      if delta_scale < 0:
        digits = max( 1, int( min_scale - delta_scale ) )
      else:
        digits = max( 1, int( max_scale - delta_scale ) )
      alt_fmt = fmt = '{0:.%dg}' % (digits + 1)
#		-- Fixed
    else:
      if delta_scale >= 0 and max_scale >= delta_scale:
        digits = 0
      else:
        digits = int( abs( delta_scale ) )
      fmt = '{0:.%df}' % digits
      alt_fmt = '{0:.%dg}' % (digits + 1)
    #end if-else min_scale, max_scale

    #labels = [ fmt.format( k ) for k in steps ]
    labels = []
    for k in steps:
      l = fmt.format( k )
      if len( l ) > digits + 6:
        l = alt_fmt.format( k )
      labels.append( l )
    #end for k
    self.AlignNumbers( labels )

    return  labels
  #end CreateLinearLabels


  #----------------------------------------------------------------------
  #	METHOD:		CullOutside()					-
  #----------------------------------------------------------------------
  def CullOutside( self, steps_in, min_value, max_value ):
    """
"""
    min_value *= 0.999999
    max_value *= 1.000001
    steps = []
    for x in steps_in:
      if x >= min_value and x <= max_value:
        steps.append( x )

    return  steps
  #end CullOutside


  #----------------------------------------------------------------------
  #	METHOD:		ForceSigDigits()				-
  #----------------------------------------------------------------------
  def ForceSigDigits( self, value_str, prec_digits ):
    """Right fills with zeros and a decimal point if necessary.
Accounts for 'g' format not right-filling with zeros.
@param  value_str	value string, assumed to have been formatted with
			'.ng' with any trailing exponent removed
@param  prec_digits	number of digits to display
"""
    if prec_digits > 1:
      value_str = value_str.lower()

      has_decimal = False
      has_sig_number = False
      sig_count = st_ndx = 0
      while st_ndx < len( value_str ):
	ch = value_str[ st_ndx ]
        if ch == 'e':
	  value_str = value_str[ : st_ndx ]
	  break
	elif ch == '.':
	  has_decimal = True
	elif ch >= '1' and ch <= '9':
	  has_sig_number = True
	  sig_count += 1
	elif ch == '0':
	  if has_decimal or has_sig_number:
	    sig_count += 1

        st_ndx += 1
      #end while st_ndx < len( value_str )

      if sig_count < prec_digits:
        if not has_decimal:
	  value_str += '.'
	value_str += '0' * (prec_digits - sig_count)
    #end if prec_digits > 1

    return  value_str
  #end ForceSigDigits


  #----------------------------------------------------------------------
  #	METHOD:		Format()					-
  #----------------------------------------------------------------------
  def Format( self, value, prec_digits = 3, mode = 'general' ):
    """Formats a floating point value.
(Replacement for DataUtils.FormatFloat4()).
@param  value		floating point value to format
@param  prec_digits	precision (general) or number of decimal places (fixed)
@param  mode		'general', 'fixed', or 'auto', defaulting to 'general'
"""
    #fmt_char = 'f'  if mode and mode.startswith( 'fixed' ) else  'g'
    if mode == 'auto':
      scale = int( math.floor( math.log10( value ) ) )
      fmt_char = 'g'  if scale < -2 or scale > 3 else  'f'
    else:
      fmt_char = 'f'  if mode and mode.startswith( 'fixed' ) else  'g'

    fmt = '{0:.%d%s}' % ( prec_digits, fmt_char )
    #return  fmt.format( value )

    value_str = fmt.format( value )
    if fmt_char == 'g':
      value_str = self.ForceSigDigits( value_str, prec_digits )
    return  value_str
  #end Format


  #----------------------------------------------------------------------
  #	METHOD:		Format_not_quite()				-
  #----------------------------------------------------------------------
  def Format_not_quite( self, value, prec_digits = 3, mode = 'general' ):
    """Formats a floating point value.
(Replacement for DataUtils.FormatFloat4()).
@param  value		floating point value to format
@param  prec_digits	precision (general) or number of decimal places (fixed)
@param  mode		'general' or 'fixed', defaulting to the former
"""
    if mode == 'fixed':
      dec = Decimal( '0.' + ('0' * (prec_digits - 1)) + '1' )
      dec = Decimal( value ).quantize( dec, rounding = ROUND_HALF_UP )
      result = str( dec )

    else:
      fmt = '{0:.%dg}' % prec_digits
      result = fmt.format( value )

#		-- Add trailing 0s if necessary
#		--
      dot_ndx = result.find( '.' )
      e_ndx = result.find( 'e' )
      if dot_ndx >= 0:
        end_ndx = len( result )  if e_ndx < 0 else  e_ndx
        dec_count = end_ndx - dot_ndx - 1

	if dec_count < prec_digits - 1:
	  new_str = result[ 0 : end_ndx ] + '0' * (prec_digits - 1 - dec_count)
	  if e_ndx >= 0:
	    new_str += result[ e_ndx : ]
	  result = new_str

      elif e_ndx > 0:
	new_str = result[ 0 : e_ndx ] + '.' + '0' * (prec_digits - 1)
	new_str += result[ e_ndx : ]
	result = new_str
    #end else not 'fixed'

    return  result
  #end Format_not_quite


#		-- Class Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		main()						-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    if len( sys.argv ) < 4:
      print >> sys.stderr, 'Usage: rangescaler min max count [ cull ]'
    else:
      m = float( sys.argv[ 1 ] )
      n = float( sys.argv[ 2 ] )
      c = int( sys.argv[ 3 ] )
      cull = len( sys.argv ) >= 4

      obj = RangeScaler()
      linear_steps = obj.CalcLinear( m, n, c, cull )
      linear_str = [ '{0:.6g}'.format( i ) for i in linear_steps ]
      print 'linear=', linear_str
      print 'labels=', obj.CreateLinearLabels( linear_steps )

      log_steps = obj.CalcLog( m, n, c, cull )
      log_str = [ '{0:.6g}'.format( i ) for i in log_steps ]
      print 'log=', log_str

      steps = obj.Calc( m, n, c, cull )
      msg = [ '{0:.6g}'.format( i ) for i in steps ]
      print '\nanswer=', msg
    #end if-else
  #end main

#end RangeScaler


if __name__ == '__main__':
  RangeScaler.main()
