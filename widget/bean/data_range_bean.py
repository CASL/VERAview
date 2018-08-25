#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_range_bean.py				-
#	HISTORY:							-
#		2018-06-22	leerw@ornl.gov				-
#	  Disallowing "inf" in range fields.
#		2018-06-19	leerw@ornl.gov				-
#	  Added DataRangeBean.Check().
#		2018-03-31	leerw@ornl.gov				-
#		2018-03-30	leerw@ornl.gov				-
#	  Adding Scale Type and Colormap.
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-03-30	leerw@ornl.gov				-
#	  Fixed focus bug.
#		2017-03-10	leerw@ornl.gov				-
#	  Added fixed/general choice.
#		2017-03-04	leerw@ornl.gov				-
#	  Added precision to dialog.
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
from widget.colormaps import *


#------------------------------------------------------------------------
#	EVENT:		DataRangeEvent, EVT_DATA_RANGE			-
#	PROPERTIES:							-
#	  value		( min, max )
#------------------------------------------------------------------------
#DataRangeEvent, EVT_DATA_RANGE = wx.lib.newevent.NewEvent()


DEFAULT_colormap = 'jet'
DEFAULT_precisionDigits = 3
DEFAULT_precisionMode = 'general'
DEFAULT_scaleType = '(dataset default)'


EMPTY_RANGE = ( float( 'NaN' ), float( 'NaN' ) )

MODE_OPTIONS = [ 'Fixed', DEFAULT_precisionMode.title() ]

SCALE_TYPES = [ DEFAULT_scaleType.title(), 'Linear', 'Log' ]


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
  def __init__(
      self, container, id = -1,
      bitmap_func = None,
      range_in = EMPTY_RANGE,
      digits_in = DEFAULT_precisionDigits,
      mode_in = DEFAULT_precisionMode,
      colormap_in = DEFAULT_colormap,
      scale_type_in = DEFAULT_scaleType,
      enable_scale_and_cmap = True
      ):
    """
"""
    super( DataRangeBean, self ).__init__( container, id )

    self.fBitmapFunc = bitmap_func
    self.fRange = EMPTY_RANGE

    self.fColormapBitmap = \
    self.fColormapButton = \
    self.fColormapMenu = \
    self.fPrecisionModeCtrl = \
    self.fPrecisionDigitsCtrl = \
    self.fScaleTypeCtrl = None
    self.fRangeFields = []

    if range_in:
      self.SetRange( range_in, False )

    self._InitUI( enable_scale_and_cmap )
    self.SetColormap( colormap_in )
    self.SetPrecisionDigits( digits_in )
    self.SetPrecisionMode( mode_in )
    self.SetScaleType( scale_type_in )
    self._UpdateRangeControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.Check()				-
  #----------------------------------------------------------------------
  def Check( self ):
    """
"""
    if (self.fRange[ 0 ] < 0.0 or self.fRange[ 1 ] < 0.0) and \
        self.GetScaleType() == 'log':
      self.SetScaleType( 'linear' )
      wx.MessageBox(
          'Cannot use "log" scale with negative values',
	  'Set Data Range and Scale', wx.OK, None
	  )
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._CreateMenu()			-
  #----------------------------------------------------------------------
  def _CreateMenu( self, options ):
    """
    Args:
        options (dict): dictionary of pullrights and colormap names
"""
    menu = wx.Menu()

    for label, names in sorted( options.iteritems() ):
      submenu = wx.Menu()

      for name in names:
        if name == '-':
	  submenu.AppendSeparator()
        else:
	  item = wx.MenuItem( submenu, wx.ID_ANY, name )
	  if self.fBitmapFunc:
	    item.SetBitmap( self.fBitmapFunc( 'cmap_' + name ) )
	  self.Bind( wx.EVT_MENU, self._OnColormap, item )
	  submenu.AppendItem( item )
      #end for name in names

      subitem = wx.MenuItem( menu, wx.ID_ANY, label, subMenu = submenu )
      menu.AppendItem( subitem )
    #end for label, names in sorted( options.iteritems() )

    return  menu
  #end _CreateMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.Enable()				-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataRangeBean, self ).Enable( flag )

    for item in self.fRangeFields:
      item.Enable( flag )
    self.fPrecisionModeCtrl.Enable( flag )
    self.fPrecisionDigitsCtrl.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetColormap()			-
  #----------------------------------------------------------------------
  def GetColormap( self ):
#    return  str( self.fColormapCtrl.GetValue() ).lower()
    return  self.fColormapButton.GetLabel()
  #end GetColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetPrecisionDigits()		-
  #----------------------------------------------------------------------
  def GetPrecisionDigits( self ):
    return  self.fPrecisionDigitsCtrl.GetValue()
  #end GetPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetPrecisionMode()		-
  #----------------------------------------------------------------------
  def GetPrecisionMode( self ):
    return  str( self.fPrecisionModeCtrl.GetValue() ).lower()
  #end GetPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetRange()			-
  #----------------------------------------------------------------------
  def GetRange( self ):
    return  self.fRange
  #end GetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetScaleType()			-
  #----------------------------------------------------------------------
  def GetScaleType( self ):
    return  str( self.fScaleTypeCtrl.GetValue() ).lower()
  #end GetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self, enable_scale_and_cmap = True ):
    """Builds this panel.
"""
#		-- Panel
#		--
    panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    panel_sizer = wx.FlexGridSizer( 7, 2, 6, 4 )
    panel_sizer.SetFlexibleDirection( wx.HORIZONTAL )
    panel.SetSizer( panel_sizer )

    self.fRangeFields = []
    for name in ( 'Minimum Value:', 'Maximum Value:' ):
      label = wx.StaticText(
          panel, wx.ID_ANY, label = name,
	  style = wx.ALIGN_RIGHT
	  )
      field = wx.TextCtrl( panel, wx.ID_ANY, value = 'NaN', size = ( 200, -1 ) )
      field.Bind( wx.EVT_KILL_FOCUS, self._OnFocusOut )
      field.Bind( wx.EVT_SET_FOCUS, self._OnFocusIn )
      self.fRangeFields.append( field )

      panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
      panel_sizer.Add(
          field, 0,
	  wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	  )
    #end for name

    label = wx.StaticText(
        panel, wx.ID_ANY, label = 'Precision Digits:',
	style = wx.ALIGN_RIGHT
	)
    self.fPrecisionDigitsCtrl = wx.SpinCtrl(
	panel, wx.ID_ANY,
	min = 1, max = 4, initial = DEFAULT_precisionDigits,
	style = wx.SP_ARROW_KEYS
        );
    panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
    panel_sizer.Add(
        self.fPrecisionDigitsCtrl, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)

    label = wx.StaticText(
        panel, wx.ID_ANY, label = 'Precision Mode:',
	style = wx.ALIGN_RIGHT
	)
    self.fPrecisionModeCtrl = wx.ComboBox(
	panel, wx.ID_ANY, DEFAULT_precisionMode,
	choices = MODE_OPTIONS,
	style = wx.CB_READONLY
        );
    panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
    panel_sizer.Add(
        self.fPrecisionModeCtrl, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)

    label = wx.StaticText(
	panel, wx.ID_ANY, label = 'Scale Type:',
	style = wx.ALIGN_RIGHT
        )
    self.fScaleTypeCtrl = wx.ComboBox(
	panel, wx.ID_ANY, DEFAULT_scaleType,
	choices = SCALE_TYPES,
	style = wx.CB_READONLY
        )
    panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
    panel_sizer.Add(
        self.fScaleTypeCtrl, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)
    if not enable_scale_and_cmap:
      self.fScaleTypeCtrl.Enable( False )

#		-- Colormap is embedded in second column
    cmap_sizer = wx.BoxSizer( wx.HORIZONTAL )
    self.fColormapButton = wx.Button( panel, label = 'X' * 16 )
    self.fColormapButton.Bind( wx.EVT_BUTTON, self._OnColormapButton )

    cmap_bitmap = \
        self.fBitmapFunc( 'cmap_' + DEFAULT_colormap ) \
	if self.fBitmapFunc else \
	wx.EmptyBitmap( 8 ,8 )
    self.fColormapBitmap = wx.StaticBitmap( panel, bitmap = cmap_bitmap )
    cmap_sizer.Add(
	self.fColormapButton, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, 4
        )
    cmap_sizer.Add(
        self.fColormapBitmap, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0
	)

    label = wx.StaticText(
	panel, wx.ID_ANY, label = 'Colormap:',
	style = wx.ALIGN_RIGHT
        )
    panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
    panel_sizer.Add(
        cmap_sizer, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)
    if not enable_scale_and_cmap:
      self.fColormapButton.Enable( False )

#		-- Panel button
#		--
    reset_button = wx.Button( panel, label = '&Reset' )
    reset_button.Bind( wx.EVT_BUTTON, self._OnReset )

    panel_sizer.Add(
	wx.StaticText( panel, wx.ID_ANY, label = '' ), 0,
	wx.ALIGN_RIGHT, 0
        )
    panel_sizer.Add( reset_button, 0, wx.ALIGN_CENTER, 0 )

#		-- Info message
#		--
    message = wx.StaticText(
	self, wx.ID_ANY,
	'Non-numeric values are interpreted as "NaN".\n' +
	'"NaN" specifies that the calculated range value should be used.',
	style = wx.ALIGN_LEFT
        )

#			-- Lay out
#			--
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( panel, 1, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6 )
    sizer.Add(
        message, 0,
	wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6
	)
    #sizer.AddStretchSpacer()
    self.Fit()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnColormap()			-
  #----------------------------------------------------------------------
  def _OnColormap( self, ev ):
    """
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item:
      self.SetColormap( item.GetItemLabelText() )
  #end _OnColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnColormapButton()		-
  #----------------------------------------------------------------------
  def _OnColormapButton( self, ev ):
    """
"""
    ev.Skip()
    if self.fColormapMenu is None:
      self.fColormapMenu = self._CreateMenu( COLORMAP_DEFS )

    ev.GetEventObject().PopupMenu( self.fColormapMenu, ( 0, 0 ) )
  #end _OnColormapButton


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnFocusIn()			-
  #----------------------------------------------------------------------
  def _OnFocusIn( self, ev ):
    """
"""
    obj = ev.GetEventObject()
    obj.SelectAll()
    ev.Skip()
  #end _OnFocusIn


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnFocusOut()			-
  #----------------------------------------------------------------------
  def _OnFocusOut( self, ev ):
    """
"""
    self._UpdateRange()
    ev.Skip()
  #end _OnFocusOut


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnReset()			-
  #----------------------------------------------------------------------
  def _OnReset( self, ev ):
    """
"""
    ev.Skip()
    self.SetColormap( DEFAULT_colormap )
    self.SetPrecisionDigits( DEFAULT_precisionDigits )
    self.SetPrecisionMode( DEFAULT_precisionMode )
    self.SetRange( EMPTY_RANGE )
    self.SetScaleType( DEFAULT_scaleType )
  #end _OnReset


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetColormap()			-
  #----------------------------------------------------------------------
  def SetColormap( self, cmap_in ):
    #self.fColormapCtrl.SetValue( cmap_in )
    #self.fColormapCtrl.Update()
    self.fColormapButton.SetLabel( cmap_in )
    self.fColormapButton.Update()

    if self.fBitmapFunc:
      self.fColormapBitmap.SetBitmap( self.fBitmapFunc( 'cmap_' + cmap_in ) )
      self.fColormapBitmap.Update()
  #end SetColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetPrecisionDigits()		-
  #----------------------------------------------------------------------
  def SetPrecisionDigits( self, prec_in ):
    self.fPrecisionDigitsCtrl.SetValue( max( 1, min( 4, prec_in ) ) )
    self.fPrecisionDigitsCtrl.Update()
  #end SetPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetPrecisionMode()		-
  #----------------------------------------------------------------------
  def SetPrecisionMode( self, mode_in ):
    mode_in = mode_in.title()
    if mode_in not in MODE_OPTIONS:
      mode_in = DEFAULT_precisionMode
    self.fPrecisionModeCtrl.SetValue( mode_in )
    self.fPrecisionModeCtrl.Update()
  #end SetPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetRange()			-
  #----------------------------------------------------------------------
  def SetRange( self, value_in, update_controls = True ):
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
      self.fRange = tuple( cur_values )

    else:
      self.fRange = EMPTY_RANGE
    #end if

    if update_controls:
      self._UpdateRangeControls()
  #end SetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetScaleType()			-
  #----------------------------------------------------------------------
  def SetScaleType( self, type_in ):
    type_in = type_in.title()
    if type_in not in SCALE_TYPES:
      type_in = DEFAULT_scaleType
    self.fScaleTypeCtrl.SetValue( type_in )
    self.fScaleTypeCtrl.Update()
  #end SetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateRange()			-
  #----------------------------------------------------------------------
  def _UpdateRange( self ):
    new_value = []
    for i in range( len( self.fRange ) ):
      try:
        #cur_value = float( self.fRangeFields[ i ].GetValue() )
	cur_str = self.fRangeFields[ i ].GetValue()
	if cur_str and cur_str.lower().find( 'inf' ) >= 0:
	  cur_value = float( 'NaN' )
	  self.fRangeFields[ i ].SetValue( 'NaN' )
        else:
          cur_value = float( self.fRangeFields[ i ].GetValue() )
      except:
        cur_value = float( 'NaN' )
	self.fRangeFields[ i ].SetValue( 'NaN' )
      new_value.append( cur_value )
    #end for i

    self.fRange = tuple( new_value )
  #end _UpdateRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateRangeControls()		-
  #----------------------------------------------------------------------
  def _UpdateRangeControls( self ):
    for i in range( len( self.fRange ) ):
      self.fRangeFields[ i ].SetValue(
	  'NaN' if math.isnan( self.fRange[ i ] ) else
	  '%.8g' % self.fRange[ i ]
          )
    #end for i
  #end _UpdateRangeControls

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
#  @property
#  def bean( self ):
#    """reference to bean, read-only"""
#    return  self.fBean
#  #end bean.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.colormap			-
  #----------------------------------------------------------------------
#  @property
#  def colormap( self ):
#    """colormap name, read-only"""
#    return  self.fBean.GetColormap()
#  #end colormap.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.digits				-
  #----------------------------------------------------------------------
#  @property
#  def digits( self ):
#    """precision digits, read-only"""
#    return  self.fBean.GetPrecisionDigits()
#  #end digits.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.mode				-
  #----------------------------------------------------------------------
#  @property
#  def mode( self ):
#    """precision mode, read-only"""
#    return  self.fBean.GetPrecisionMode()
#  #end mode.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.range				-
  #----------------------------------------------------------------------
#  @property
#  def range( self ):
#    """range value, read-only"""
#    return  self.fBean.GetRange()
#  #end range.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataRangeDialog.scaletype			-
  #----------------------------------------------------------------------
#  @property
#  def scaletype( self ):
#    """scaletype, read-only"""
#    return  self.fBean.GetScaleType()
#  #end scaletype.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
@param  'range' or 'value'  ( min_value, max_value ) tuple
"""
#    value_in = None
#    for n in ( 'range', 'value' ):
#      if n in kwargs:
#        value_in = kwargs[ n ]
#        del kwargs[ n ]
#    #end for n
#
#    if value_in is not None:
#      if not (hasattr( value_in, '__iter__' ) and len( value_in ) >= 2):
#        value_in = None
#    #end if
#
#    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
#    style |= wx.RESIZE_BORDER
#    kwargs[ 'style' ] = style

    bitmap_func = kwargs.get( 'bitmap_func' )
    if not hasattr( bitmap_func, '__call__' ):
      bitmap_func = None

    if 'bitmap_func' in kwargs:
      del kwargs[ 'bitmap_func' ]
    if 'enable_scale_and_cmap' in kwargs:
      enable_scale_and_cmap = kwargs[ 'enable_scale_and_cmap' ]
      del kwargs[ 'enable_scale_and_cmap' ]

    super( DataRangeDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self._InitUI(
        bitmap_func = bitmap_func,
	enable_scale_and_cmap = enable_scale_and_cmap
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetBean()			-
  #----------------------------------------------------------------------
  def GetBean( self ):
    return  self.fBean
  #end GetBean


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetColormap()			-
  #----------------------------------------------------------------------
  def GetColormap( self ):
    return  self.fBean.GetColormap()
  #end GetColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetPrecisionDigits()		-
  #----------------------------------------------------------------------
  def GetPrecisionDigits( self ):
    return  self.fBean.GetPrecisionDigits()
  #end GetPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetPrecisionMode()		-
  #----------------------------------------------------------------------
  def GetPrecisionMode( self ):
    return  self.fBean.GetPrecisionMode()
  #end GetPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetRange()			-
  #----------------------------------------------------------------------
  def GetRange( self ):
    return  self.fBean.GetRange()
  #end GetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetScaleType()			-
  #----------------------------------------------------------------------
  def GetScaleType( self ):
    return  self.fBean.GetScaleType()
  #end GetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI(
      self,
      bitmap_func = None,
      range_in = None,
      digits_in = DEFAULT_precisionDigits,
      mode_in = DEFAULT_precisionMode,
      scale_type_in = DEFAULT_scaleType,
      colormap_in = DEFAULT_colormap,
      enable_scale_and_cmap = True
      ):
    self.fBean = DataRangeBean(
        self, -1, bitmap_func,
        range_in = range_in,
        digits_in = DEFAULT_precisionDigits,
        mode_in = DEFAULT_precisionMode,
        scale_type_in = DEFAULT_scaleType,
        colormap_in = DEFAULT_colormap,
        enable_scale_and_cmap = enable_scale_and_cmap
	)

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

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetSizer( sizer )
    self.SetTitle( 'Edit Custom Data Scale' )
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
      self.fBean.Check()
      self.fResult = self.fBean.GetRange()

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.fResult = self.fBean.GetRange()
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal(
      self,
      range_in = None,
      digits_in = DEFAULT_precisionDigits,
      mode_in = None,
      scale_type_in = DEFAULT_scaleType,
      colormap_in = DEFAULT_colormap
      ):
#    self.fResult = range_in
#    if range_in is not None:
#      self.fBean.SetRange( range_in )
    self.fBean.SetColormap( colormap_in )
    self.fBean.SetPrecisionDigits( digits_in )
    self.fBean.SetPrecisionMode( mode_in )
    self.fBean.SetRange( range_in )
    self.fBean.SetScaleType( scale_type_in )
    super( DataRangeDialog, self ).ShowModal()
  #end ShowModal


#		-- Property Definitions
#		--

  bean = property( GetBean )

  colormap = property( GetColormap )

  digits = property( GetPrecisionDigits )

  mode = property( GetPrecisionMode )

  range = property( GetRange )

  scaletype = property( GetScaleType )

#end DataRangeDialog
