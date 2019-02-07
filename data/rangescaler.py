#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		rangescaler.py					-
#	HISTORY:							-
#		2018-11-15	leerw@ornl.gov				-
#         Added "exponential" mode param value for Format().
#		2018-06-25	leerw@ornl.gov				-
#	  Handling case of min and max value equal, resulting in no steps.
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

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
  #import matplotlib.pyplot as plt
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

try:
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'


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
  #	METHOD:		__del__()					-
  #----------------------------------------------------------------------
  def __del__( self, *args, **kwargs ):
    if self.fig is not None and \
        hasattr( self.fig, 'close' ) and \
	hasattr( getattr( self.fig, 'close' ), '__call__' ):
      self.fig.close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self ):
    #self.fig = Figure( figsize = ( 1024, 768 ) )
    self.fig = Figure()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AlignNumbers()					-
  #----------------------------------------------------------------------
  def AlignNumbers( self, labels ):
    """Aligns a series of number labels by adding trailing zeros if needed.
@param  labels		labels to align
"""
#		-- Determine if some but not all have exponents
#		--
    e_ndxs = []
    for label in labels:
      e_ndxs.append( label.find( 'e' ) )
    e_count = len( [ x for x in e_ndxs if x > 0 ] )
    have_e = e_count > 0
    #all_e = e_count == len( labels )

#		-- Determine max number of decimal places
#		--
    max_dec_count = 0
    for label, e_ndx in zip( labels, e_ndxs ):
      if not have_e or e_ndx > 0:
        dot_ndx = label.find( '.' )
	if dot_ndx >= 0:
	  end_ndx = len( label )  if e_ndx < 0 else  e_ndx
	  max_dec_count = max( max_dec_count, end_ndx - dot_ndx - 1 )
    #end for label, e_ndx in zip( labels, e_ndxs )

#    max_dec_count = -1
#    have_e = False
#    for label in labels:
#      e_ndx = label.find( 'e' )
#      have_e = e_ndx > 0
#      dot_ndx = label.find( '.' )
#      if dot_ndx >= 0:
#        e_ndx = label.find( 'e' )
#	end_ndx = len( label )  if e_ndx < 0 else  e_ndx
#	max_dec_count = max( max_dec_count, end_ndx - dot_ndx - 1 )
#    #end for i

#		-- Align and/or add 'e'
#		--
    for i in xrange( len( labels ) ):
      #e_ndx = labels[ i ].find( 'e' )
      e_ndx = e_ndxs[ i ]

      if have_e and e_ndx < 0:
	fmt = '{0:.%de}' % max_dec_count
        labels[ i ] = fmt.format( float( labels[ i ] ) )
        e_ndxs[ i ] = e_ndx = labels[ i ].find( 'e' )

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
  #	METHOD:		Calc()						-
  #----------------------------------------------------------------------
  def Calc(
      self, min_value, max_value,
      scale_type = 'linear',
      nticks = None,
      cull_outside_range = False
      ):
    """Calculates linear or log tick values for a specified range.
    Args:
        min_value (float): min value for range
        max_value (float): max value for range
	scale_type (str): 'linear', 'log', or 'auto'
	nticks (int,None): number of ticks, where None is default
	cull_outside_range (bool): if True, all tick values outside the
	    specified range are culled
    Returns:
	list(float): list of tick values
"""
    #fig, ax = plt.subplots()  # plt.gca()
    self.fig.clear()
    ax = self.fig.add_subplot( 111 )

#	-- Handle reverse
#	--
    reverse_flag = False
    if min_value > max_value:
      temp = min_value
      min_value = max_value
      max_value = temp
      reverse_flag = True

#	-- Set nticks
    if nticks:
      ax.locator_params( axis = 'x', nticks = nticks )

#	-- Scale
    if scale_type == 'auto':
      scale_type = 'linear'
      if min_value > 0.0 and max_value > 0.0:
        min_scale = math.floor( math.log10( min_value ) )
        max_scale = math.floor( math.log10( max_value ) )
        if max_scale - min_scale > 3:
	  scale_type = 'log'

    if scale_type == 'log':
      ax.set_xscale( 'log', nonposx = 'clip' )
    else:
      ax.set_xscale( 'linear' )

#	-- Set range
    ax.set_xlim( min_value, max_value, auto = True )

#	-- Let matplotlib gives us the tick "locations"
    xaxis = ax.get_xaxis()
    xaxis.reset_ticks()
    steps = xaxis.get_ticklocs().tolist()

#	-- Clean up
    #plt.close( fig )

#	-- Cull?
    if cull_outside_range and scale_type != 'log':
      tsteps = steps
      steps = [ x for x in tsteps if x >= min_value and x <= max_value ]
      if len( steps ) == 0:
        steps = [ min_value ]

#	-- Reverse?
    if reverse_flag:
      steps = steps[ :: -1 ]
    return  steps
  #end Calc


  #----------------------------------------------------------------------
  #	METHOD:		CreateLabels()					-
  #----------------------------------------------------------------------
  def CreateLabels( self, steps, mode = 'auto' ):
    """
"""
    if mode == 'auto':
      mode = 'linear'
      if len( steps ) > 2:
        d1 = steps[ 1 ] - steps[ 0 ]
        d2 = steps[ 2 ] - steps[ 1 ]
        err = abs( (d1 - d2) / ((d1 + d2) / 2.0) )
        if err > 1.0e-3:
          mode = 'log'
    #end if mode == 'auto'

    return  \
        self.CreateLogLabels( steps )  if mode == 'log' else \
	self.CreateLinearLabels( steps )
  #end CreateLabels


  #----------------------------------------------------------------------
  #	METHOD:		CreateLinearLabels()				-
  #----------------------------------------------------------------------
  def CreateLinearLabels( self, steps ):
    """Creates labels for the step values.
@param  steps		steps for which labels are desired
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
  #	METHOD:		CreateLogLabels()				-
  #----------------------------------------------------------------------
  def CreateLogLabels( self, steps ):
    """Creates labels for the step values.
@param  steps		steps for which labels are desired
@return			list of formatted string labels
"""

    labels = [ '{0:.3g}'.format( k ) for k in steps ]
    self.AlignNumbers( labels )

    return  labels
  #end CreateLogLabels


  #----------------------------------------------------------------------
  #	METHOD:		ForceSigDigits()				-
  #----------------------------------------------------------------------
  def ForceSigDigits( self, value_str, prec_digits ):
    """Right fills with zeros and a decimal point if necessary.
Accounts for 'g' format not right-filling with zeros.
    Args:
        value_str (str): value string, assumed to have been formatted with
			'.ng' with any trailing exponent removed
        prec_digits (int): of digits to display
"""
    if prec_digits > 1:
      value_str = value_str.lower()

      has_decimal = False
      has_exp = False
      has_sig_number = False
      sig_count = st_ndx = 0
      while st_ndx < len( value_str ) and not has_exp:
	ch = value_str[ st_ndx ]
        if ch == 'e':
	  value_str = value_str[ : st_ndx ]
          has_exp = True
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
    Args:
        value (float): floating point value to format
        prec_digits (int): number of signficant figures ("general", "exp" modes)
            or decimal places ("fixed" mode)
        mode (str): 'general', 'exp', 'fixed', or 'auto',
            defaulting to 'general'
"""
    if not mode:
      mode = 'general'

    if mode == 'auto':
      scale = int( math.floor( math.log10( value ) ) )
      fmt_char = 'g'  if scale < -2 or scale > 3 else  'f'
    else:
      fmt_char = \
          'f'  if mode.startswith( 'fixed' ) else \
          'e'  if mode.startswith( 'exp' ) else \
          'g'

    fmt = '{0:.%d%s}' % ( prec_digits, fmt_char )
    #return  fmt.format( value )

    value_str = fmt.format( value )
    if fmt_char == 'g':
      value_str = self.ForceSigDigits( value_str, prec_digits )
    return  value_str
  #end Format


#		-- Class Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		main()						-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    if len( sys.argv ) < 5:
      print >> sys.stderr, 'Usage: rangescaler min max mode nticks [ cull ]'
    else:
      m = float( sys.argv[ 1 ] )
      n = float( sys.argv[ 2 ] )
      mode = sys.argv[ 3 ]
      nticks = int( sys.argv[ 4 ] )
      cull = len( sys.argv ) >= 5

      obj = RangeScaler()
      steps = obj.Calc( m, n, mode, nticks, cull )
      labels = obj.CreateLabels( steps )

      print 'steps=', str( steps )
      print 'labels=', ', '.join( labels )
    #end if-else
  #end main

#end RangeScaler


if __name__ == '__main__':
  RangeScaler.main()
