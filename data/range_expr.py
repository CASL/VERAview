#------------------------------------------------------------------------
#	NAME:		range_expr.py					-
#	HISTORY:							-
#		2017-07-18	godfreyat@ornl.gov			-
#------------------------------------------------------------------------
import math, os, sys, threading
import numpy as np
import pyparsing as pp
import pdb


NAN = float( 'nan' )


#------------------------------------------------------------------------
#	CLASS:		RangeExpression					-
#------------------------------------------------------------------------
class RangeExpression( object ):
  """Encapsulation of everything needed to process range expressions.
"""


#		-- Class Attributes
#		--

  fParser_ = None

  fParserLock_ = threading.RLock()


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """Calls Parse().
"""
    self.Parse( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, expr = None ):
    """Initializes with an optional expression.
@param  expr		string with one or more op-value pairs
@exception		on error parsing expr
"""
    self.fDisplayExpr = ''
    self.fNumpyExpr = ''
    self.fTerms = {}

    if expr:
      self.Parse( expr )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		__repr__()					-
  #----------------------------------------------------------------------
  def __repr__( self ):
    return  \
        'range_expression.RangeExpression({0:s})'.format( self.fDisplayExpr )
  #end __repr__


  #----------------------------------------------------------------------
  #	METHOD:		__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    return  self.fDisplayExpr
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		ApplyThreshold()				-
  #----------------------------------------------------------------------
  def ApplyThreshold( self, arr, invalid_value = NAN ):
    """Applies this expression as a threshold to the specified array
@param  arr		np.ndarray instance, arr on no change or a new
			np.ndarray instance if applied
@param  invalid_value	value with which to fill values outside the
			range specified by this expression
"""
    result = arr
    if self.fNumpyExpr:
      x = np.copy( arr )
      #mask_str = self.fNumpyExpr.replace( 'x', 'arr' )
      eval_str = \
          'np.logical_not( np.logical_or( np.isnan( x ), {0:s} ) )'.\
	  format( self.fNumpyExpr )
      mask = eval( eval_str )
      np.place( x, mask, invalid_value )
      result = x
    #end if self.fNumpyExpr

    return  result
  #end ApplyThreshold


  #----------------------------------------------------------------------
  #	METHOD:		_DoParse()					-
  #----------------------------------------------------------------------
  def _DoParse( self, parser, expr ):
    """Parses the expression.
@param  parser		pp.ParserElement instance
@param  expr		string with one or more op-value pairs
@exception		on error parsing expr
"""
    try:
      result = parser.parseString( expr )
      #tokens = result[ 0 ]

      self.fTerms.clear()
      self.fDisplayExpr = ''
      self.fNumpyExpr = ''

      for i in xrange( 0, len( result ) - 1, 2 ):
	op = result[ i ]
	value = float( result[ i + 1 ] )

	if op in ( '>', '>=', '!=' ):
	  self.fTerms[ 'aboveop' ] = op
	  self.fTerms[ 'abovevalue' ] = value
	else:
	  self.fTerms[ 'belowop' ] = op
	  self.fTerms[ 'belowvalue' ] = value

	term = 'x {0:s} {1:.6g}'.format( op, value )

        if self.fDisplayExpr:
	  self.fDisplayExpr += ' and '
        self.fDisplayExpr += term

        if self.fNumpyExpr:
	  self.fNumpyExpr += ' & '
        self.fNumpyExpr += '({0:s})'.format( term )
      #end for i

    except pp.ParseException, ex:
      raise  Exception( str( ex ) )
  #end _DoParse


  #----------------------------------------------------------------------
  #	METHOD:		GetDisplayExpr()				-
  #----------------------------------------------------------------------
  def GetDisplayExpr( self ):
    """
@return			expression suitable for display
"""
    return  self.fDisplayExpr
  #end GetDisplayExpr


  #----------------------------------------------------------------------
  #	METHOD:		GetNumpyExpr()					-
  #----------------------------------------------------------------------
  def GetNumpyExpr( self ):
    """
@return			numpy mask or where expression
"""
    return  self.fNumpyExpr
  #end GetNumpyExpr


  #----------------------------------------------------------------------
  #	METHOD:		GetTerms()					-
  #----------------------------------------------------------------------
  def GetTerms( self ):
    """
@return			dict of terms with keys 'aboveop', 'abovevalue',
			'belowop', and/or 'belowvalue'
"""
    return  self.fTerms
  #end GetTerms


  #----------------------------------------------------------------------
  #	METHOD:		Parse()						-
  #----------------------------------------------------------------------
  def Parse( self, expr ):
    """Parses the expression.
@param  expr		string with one or more op-value pairs
@exception		on error parsing expr
"""
    RangeExpression.WithParser( self._DoParse, expr )
  #end Parse


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WithParser()					-
  #----------------------------------------------------------------------
  @staticmethod
  def WithParser( callback, *args ):
    """Lazily creates the parser, calls callback with the pp.ParserElement
instance as the sole argument.
@param  callback	callable( parser, *args )
"""
    RangeExpression.fParserLock_.acquire()
    try:
#		-- Create parser if necessary
#		--
      if RangeExpression.fParser_ is None:
	logical_op = pp.CaselessLiteral( 'and' ) ^ pp.Literal( '&&' )
	word = pp.Word( pp.alphas )
        op = pp.oneOf( '!= <= < >= >' )
	number = pp.Word( pp.nums + '.Ee+-' )
	expr = pp.Optional( word ).suppress() + op + number
	#expr = pp.ZeroOrMore( word ).suppress() + op + number
	RangeExpression.fParser_ = \
	    expr + pp.Optional( logical_op ).suppress() + pp.Optional( expr )
      #end if

      callback( RangeExpression.fParser_, *args )

    finally:
      RangeExpression.fParserLock_.release()
  #end WithParser


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	displayExpr					-
  #----------------------------------------------------------------------
  displayExpr = property( GetDisplayExpr )


  #----------------------------------------------------------------------
  #	PROPERTY:	numpyExpr					-
  #----------------------------------------------------------------------
  numpyExpr = property( GetNumpyExpr )


  #----------------------------------------------------------------------
  #	PROPERTY:	terms						-
  #----------------------------------------------------------------------
  terms = property( GetTerms )

#end RangeExpression
