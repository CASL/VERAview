#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_range_bean.py				-
#	HISTORY:							-
#		2016-10-22	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from event.state import *


#------------------------------------------------------------------------
#	EVENT:		DataRangeEvent, EVT_DATA_RANGE			-
#	PROPERTIES:							-
#	  value		( min, max )
#------------------------------------------------------------------------
#DataRangeEvent, EVT_DATA_RANGE = wx.lib.newevent.NewEvent()


EMPTY_RANGE = ( float( 'NaN' ), float( 'NaN' ) )


#------------------------------------------------------------------------
#	CLASS:		DataRangeBean					-
#------------------------------------------------------------------------
class DataRangeBean( wx.Panel ):
  """Panel containing a list of checkboxes.

Attributes/properties:
  events		dict keyed by state change IDs of True/False values
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, value_in = EMPTY_RANGE ):
    """
@param  value		initial value
"""
    super( DataRangeBean, self ).__init__( container, id )

    self.fFields = []
    self.fValue = EMPTY_RANGE

    if value_in:
      self.SetValue( value_in, False )

    self._InitUI()
    self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.Enable()				-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataRangeBean, self ).Enable( flag )

    for item in ( self.fMaxField, self.fMinField ):
      item.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetValue()			-
  #----------------------------------------------------------------------
  def GetValue( self ):
    return  self.fValue
  #end GetValue


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this panel.
"""

    panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    panel_sizer = wx.FlexGridSizer( 2, 2, 6, 4 )
    panel_sizer.SetFlexibleDirection( wx.HORIZONTAL )
    panel.SetSizer( panel_sizer )

    self.fFields = []
    for name in ( 'Minimum Value:', 'Maximum Value:' ):
      label = wx.StaticText(
          panel, wx.ID_ANY, label = name,
	  style = wx.ALIGN_RIGHT
	  )
      field = wx.TextCtrl( panel, wx.ID_ANY, value = 'NaN', size = ( 200, -1 ) )
      field.Bind( wx.EVT_KILL_FOCUS, self._OnFocusOut )
      field.Bind( wx.EVT_SET_FOCUS, self._OnFocusIn )
      self.fFields.append( field )

      panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
      panel_sizer.Add(
          field, 0,
	  wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
	  0
	  )
    #end for name

#			-- Lay Out
#			--
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( panel, 1, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6 )
    sizer.AddStretchSpacer()
    self.Fit()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnFocusIn()			-
  #----------------------------------------------------------------------
  def _OnFocusIn( self, ev ):
    """
"""
    #ev.Skip()
    obj = ev.GetEventObject()
    obj.SetSelection( -1, -1 )
  #end _OnFocusIn


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnFocusOut()			-
  #----------------------------------------------------------------------
  def _OnFocusOut( self, ev ):
    """
"""
    #ev.Skip()
    self._UpdateValue()
  #end _OnFocusOut


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetValue()			-
  #----------------------------------------------------------------------
  def SetValue( self, value_in, update_controls = True ):
    if value_in is not None and \
        hasattr( value_in, '__iter__' ) and len( value_in ) >= 2:
      cur_values = []
      for i in xrange( 2 ):
        try:
	  x = float( value_in[ i ] )
        except:
	  x = float( 'NaN' )
        cur_values.append( x )
      #end for
      self.fValue = tuple( cur_values )

    else:
      self.fValue = EMPTY_RANGE
    #end if

    if update_controls:
      self._UpdateControls()
  #end SetValue


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateControls()			-
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    for i in range( len( self.fValue ) ):
      self.fFields[ i ].SetValue(
	  'NaN' if math.isnan( self.fValue[ i ] ) else
	  '%.8g' % self.fValue[ i ]
          )
    #end for i
  #end _UpdateControls


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateValue()			-
  #----------------------------------------------------------------------
  def _UpdateValue( self ):
    new_value = []
    for i in range( len( self.fValue ) ):
      try:
        cur_value = float( self.fFields[ i ].GetValue() )
      except:
        cur_value = float( 'NaN' )
	self.fFields[ i ].SetValue( 'NaN' )
      new_value.append( cur_value )
    #end for i

    self.fValue = tuple( new_value )
  #end _UpdateValue

#end DataRangeBean


#------------------------------------------------------------------------
#	CLASS:		DataRangeDialog					-
#------------------------------------------------------------------------
class DataRangeDialog( wx.Dialog ):
  """
Properties:
  bean			DataRangeBean reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.bean				-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.result				-
  #----------------------------------------------------------------------
  @property
  def result( self ):
    """bean value, read-only"""
    return  self.fResult
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
@param  'range' or 'value'  ( min_value, max_value ) tuple
"""
    value_in = None
    for n in ( 'range', 'value' ):
      if n in kwargs:
        value_in = kwargs[ n ]
        del kwargs[ n ]
    #end for n

    if value_in is not None:
      if not (hasattr( value_in, '__iter__' ) and len( value_in ) >= 2):
        value_in = None
    #end if

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataRangeDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fResult = None

    self._InitUI( value_in )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetResult()			-
  #----------------------------------------------------------------------
  def GetResult( self ):
    return  self.fResult
  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, value_in ):
    self.fBean = DataRangeBean( self, -1, value_in )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    ok_button = wx.Button( self, label = '&OK' )
    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
    cancel_button = wx.Button( self, label = 'Cancel' )
    cancel_button.Bind( wx.EVT_BUTTON, self._OnButton )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddSpacer( 10 )
    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )

    sizer.Add(
	self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.SetSizer( sizer )
    self.SetTitle( 'Edit Custom Range' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    if obj.GetLabel() != 'Cancel':
      self.fResult = self.fBean.GetValue()

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self, value_in = None ):
    self.fResult = None
    if value_in is not None:
      self.fBean.SetValue( value_in )
    super( DataRangeDialog, self ).ShowModal()
  #end ShowModal

#end DataRangeDialog
