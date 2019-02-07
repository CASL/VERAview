#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_range_bean.py				-
#	HISTORY:							-
#		2018-11-16	leerw@ornl.gov				-
#         Added DataRangeValues.customRange.
#		2018-11-15	leerw@ornl.gov				-
#         Added "Exponential" Precision Mode option.
#         Definition and use of DataRangeValues.
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
import copy, math, os, sys, webbrowser
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  from wx.lib.agw.hyperlink import HyperLinkCtrl
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


CUSTOM_FORMAT_URL = 'https://docs.python.org/2/library/string.html#format-specification-mini-language'

DEFAULT_colormap = 'jet'
DEFAULT_precisionDigits = 3
DEFAULT_precisionMode = 'general'
DEFAULT_scaleType = '(dataset default)'


EMPTY_RANGE = ( np.nan, np.nan )

MODE_OPTIONS = \
  [ 'Custom', 'Exponential', 'Fixed', DEFAULT_precisionMode.title() ]

SCALE_TYPES = [ DEFAULT_scaleType.title(), 'Linear', 'Log' ]


#------------------------------------------------------------------------
#	CLASS:		DataRangeBean					-
#------------------------------------------------------------------------
class DataRangeBean( wx.Panel ):
  """Panel with controls for setting the range, colormap, and scale type.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__(
      self, container, id = -1,
      bitmap_func = None,
      values = None,
#      range_in = EMPTY_RANGE,
#      digits_in = DEFAULT_precisionDigits,
#      mode_in = DEFAULT_precisionMode,
#      colormap_in = DEFAULT_colormap,
#      scale_type_in = DEFAULT_scaleType,
      use_scale_and_cmap = True
      ):
    """
"""
    super( DataRangeBean, self ).__init__( container, id )

    self.fBitmapFunc = bitmap_func
#    self.fRange = EMPTY_RANGE
    self.fValues = DataRangeValues()
    self.fUseScaleAndCmap = use_scale_and_cmap

    self.fColormapBitmap = \
    self.fColormapButton = \
    self.fColormapMenu = \
    self.fCustomFormatField = \
    self.fCustomFormatLabel = \
    self.fPanelSizer = \
    self.fPrecisionModeCtrl = \
    self.fPrecisionDigitsCtrl = \
    self.fPrecisionDigitsLabel = \
    self.fScaleTypeCtrl = None
    self.fRangeFields = []

    self.GetRange = self.GetDataRange
    self.SetRange = self.SetDataRange

    #if range_in:
      #self.SetRange( range_in, False )


    self._InitUI( use_scale_and_cmap )
#    self.SetColormap( colormap_in )
#    self.SetPrecisionDigits( digits_in )
#    self.SetPrecisionMode( mode_in )
#    self.SetScaleType( scale_type_in )
#    self._UpdateRangeControls()
    if values is not None:
      self.SetValues( values )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.Check()				-
  #----------------------------------------------------------------------
  def Check( self ):
    """
"""
#    if (self.fRange[ 0 ] < 0.0 or self.fRange[ 1 ] < 0.0) and \
#        self.GetScaleType() == 'log':
    data_range = self.GetDataRange()
    if (data_range[ 0 ] < 0.0 or data_range[ 0 ] < 0.0) and \
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

    custom = 'custom' == self.GetPrecisionMode()

    for item in self.fRangeFields:
      item.Enable( flag )
    self.fCustomFormatField.Enable( custom )
    self.fCustomFormatLabel.Enable( custom )
    self.fPrecisionModeCtrl.Enable( not custom )
    self.fPrecisionDigitsCtrl.Enable( not custom )

    if self.IsUseScaleAndCmap():
      self.fColormapButton.Enable( flag )
      self.fScaleTypeCtrl.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetColormap()			-
  #----------------------------------------------------------------------
  def GetColormap( self ):
    #return  self.fColormapButton.GetLabel()
    return  self.fValues.colormap
  #end GetColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetCustomFormat()			-
  #----------------------------------------------------------------------
  def GetCustomFormat( self ):
    #return  self.fRange
    return  self.fValues.customFormat
  #end GetCustomFormat


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetDataRange()			-
  #----------------------------------------------------------------------
  def GetDataRange( self ):
    #return  self.fRange
    return  self.fValues.dataRange
  #end GetDataRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetPrecisionDigits()		-
  #----------------------------------------------------------------------
  def GetPrecisionDigits( self ):
    #return  self.fPrecisionDigitsCtrl.GetValue()
    return  self.fValues.precisionDigits
  #end GetPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetPrecisionMode()		-
  #----------------------------------------------------------------------
  def GetPrecisionMode( self ):
    #return  str( self.fPrecisionModeCtrl.GetValue() ).lower()
    return  self.fValues.precisionMode
  #end GetPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetScaleType()			-
  #----------------------------------------------------------------------
  def GetScaleType( self ):
    #return  str( self.fScaleTypeCtrl.GetValue() ).lower()
    return  self.fValues.scaleType
  #end GetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.GetValues()			-
  #----------------------------------------------------------------------
  def GetValues( self ):
    return  copy.copy( self.fValues )
  #end GetValues


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self, use_scale_and_cmap = True ):
    """Builds this panel.
"""
#		-- Panel
#		--
    panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    self.fPanelSizer = panel_sizer = wx.FlexGridSizer( 8, 2, 6, 4 )
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

    self.fCustomFormatLabel = wx.StaticText(
        panel, wx.ID_ANY, label = 'Custom Format:',
	style = wx.ALIGN_RIGHT
	)
    self.fCustomFormatField = wx.TextCtrl(
        panel, wx.ID_ANY, value = 'g'
        #size = ( 200, -1 )
        )
    self.fCustomFormatField.Bind( wx.EVT_KILL_FOCUS, self._OnCustomFocusOut )
    self.fCustomFormatField.Bind( wx.EVT_SET_FOCUS, self._OnFocusIn )
    panel_sizer.Add(
        self.fCustomFormatLabel, 0,
        wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0
        )
    panel_sizer.Add(
        self.fCustomFormatField, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)

    self.fPrecisionDigitsLabel = wx.StaticText(
        panel, wx.ID_ANY, label = 'Precision Digits:',
	style = wx.ALIGN_RIGHT
	)
    self.fPrecisionDigitsCtrl = wx.SpinCtrl(
	panel, wx.ID_ANY,
	min = 1, max = 4, initial = DEFAULT_precisionDigits,
	style = wx.SP_ARROW_KEYS
        );
    self.fPrecisionDigitsCtrl.Bind( wx.EVT_SPINCTRL, self._OnPrecisionDigits )
    panel_sizer.Add(
        self.fPrecisionDigitsLabel, 0,
        wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0
        )
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
    self.fPrecisionModeCtrl.Bind( wx.EVT_COMBOBOX, self._OnPrecisionMode )
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
    self.fScaleTypeCtrl.Bind( wx.EVT_COMBOBOX, self._OnScaleType )
    panel_sizer.Add( label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0 )
    panel_sizer.Add(
        self.fScaleTypeCtrl, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)
    if not use_scale_and_cmap:
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
    if not use_scale_and_cmap:
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

#               -- Help message with link
#               --
    help_sizer = wx.BoxSizer( wx.HORIZONTAL )
    help_message = wx.StaticText(
        self, wx.ID_ANY,
        'Custom formats are described at ',
	style = wx.ALIGN_LEFT
        )
    help_sizer.Add( help_message, 0, wx.ALIGN_LEFT | wx.LEFT, 6 )
    link = HyperLinkCtrl(
        self, wx.ID_ANY,
        label = 'at this link', URL = CUSTOM_FORMAT_URL
        )
    link.SetFont( link.GetFont().Bold() )
    help_sizer.Add( link, 0, wx.ALIGN_LEFT, 0 )

#			-- Lay out
#			--
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( panel, 1, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6 )
    sizer.Add(
        message, 0,
	wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6
	)
    sizer.Add(
        help_sizer, 0,
	wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_TOP | wx.EXPAND, 0
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
  #	METHOD:		DataRangeBean._OnCustomFocusOut()               -
  #----------------------------------------------------------------------
  def _OnCustomFocusOut( self, ev ):
    """
"""
    ev.Skip()

    new_value = ev.GetEventObject().GetValue()
    if not new_value:
      new_value = 'g'
      ev.GetEventObject().SetValue( new_value )

    self.fValues.customFormat = new_value
  #end _OnCustomFocusOut


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
  #	METHOD:		DataRangeBean._OnPrecisionDigits()		-
  #----------------------------------------------------------------------
  def _OnPrecisionDigits( self, ev ):
    """
"""
    ev.Skip()
    self.fValues.precisionDigits = ev.GetEventObject().GetValue()
  #end _OnPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnPrecisionMode()		-
  #----------------------------------------------------------------------
  def _OnPrecisionMode( self, ev ):
    """
"""
    ev.Skip()
    self.fValues.precisionMode = str( ev.GetEventObject().GetValue() ).lower()
    self._UpdateModeControls()
  #end _OnPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnReset()			-
  #----------------------------------------------------------------------
  def _OnReset( self, ev ):
    """
"""
    ev.Skip()
#    self.SetColormap( DEFAULT_colormap )
#    self.SetPrecisionDigits( DEFAULT_precisionDigits )
#    self.SetPrecisionMode( DEFAULT_precisionMode )
#    self.SetRange( EMPTY_RANGE )
#    self.SetScaleType( DEFAULT_scaleType )
    self.SetValues( DataRangeValues() )
  #end _OnReset


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._OnScaleType()		        -
  #----------------------------------------------------------------------
  def _OnScaleType( self, ev ):
    """
"""
    ev.Skip()
    self.fValues.scaleType = str( ev.GetEventObject().GetValue() ).lower()
  #end _OnScaleType


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

    self.fValues.colormap = cmap_in
  #end SetColormap


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetCustomFormat()			-
  #----------------------------------------------------------------------
  def SetCustomFormat( self, value_in ):
    if not value_in:
      value_in = 'g'
    self.fCustomFormatField.SetValue( value_in )
    self.fValues.customFormat = value_in
  #end SetCustomFormat


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetDataRange()			-
  #----------------------------------------------------------------------
  def SetDataRange( self, value_in ):
    if value_in is not None and \
        hasattr( value_in, '__iter__' ) and len( value_in ) >= 2:
      cur_values = []
      for i in xrange( 2 ):
        try:
	  x = float( value_in[ i ] )
        except:
	  x = np.nan
        cur_values.append( x )
      #end for
      self.fValues.dataRange = tuple( cur_values )

    else:
      self.fValues.dataRange = EMPTY_RANGE
    #end if

    self._UpdateRangeControls()
  #end SetDataRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetPrecisionDigits()		-
  #----------------------------------------------------------------------
  def SetPrecisionDigits( self, prec_in ):
    prec_in = max( 1, min( 4, prec_in ) )
    self.fPrecisionDigitsCtrl.SetValue( prec_in )
    self.fPrecisionDigitsCtrl.Update()

    self.fValues.precisionDigits = prec_in
  #end SetPrecisionDigits


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetPrecisionMode()		-
  #----------------------------------------------------------------------
  def SetPrecisionMode( self, mode_in ):
    tmode_in = mode_in.title()
    if tmode_in not in MODE_OPTIONS:
      mode_in = DEFAULT_precisionMode
    self.fPrecisionModeCtrl.SetValue( tmode_in )
    self.fPrecisionModeCtrl.Update()

    self.fValues.precisionMode = mode_in
    self._UpdateModeControls()
  #end SetPrecisionMode


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetScaleType()			-
  #----------------------------------------------------------------------
  def SetScaleType( self, type_in ):
    ttype_in = type_in.title()
    if ttype_in not in SCALE_TYPES:
      type_in = DEFAULT_scaleType
    self.fScaleTypeCtrl.SetValue( ttype_in )
    self.fScaleTypeCtrl.Update()

    self.fValues.scaleType = type_in
  #end SetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean.SetValues()			-
  #----------------------------------------------------------------------
  def SetValues( self, values ):
    self.SetColormap( values.colormap )
    self.SetCustomFormat( values.customFormat )
    self.SetDataRange( values.dataRange )
    self.SetPrecisionDigits( values.precisionDigits )
    self.SetPrecisionMode( values.precisionMode )
    self.SetScaleType( values.scaleType )
  #end SetValues


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateRange()			-
  #----------------------------------------------------------------------
  def _UpdateRange( self ):
    new_value = []
    for i in range( len( self.fValues.dataRange ) ):
      try:
        #cur_value = float( self.fRangeFields[ i ].GetValue() )
	cur_str = self.fRangeFields[ i ].GetValue()
	if cur_str and cur_str.lower().find( 'inf' ) >= 0:
	  cur_value = np.nan  # float( 'NaN' )
	  self.fRangeFields[ i ].SetValue( 'NaN' )
        else:
          cur_value = float( self.fRangeFields[ i ].GetValue() )
      except:
        cur_value = np.nan  # float( 'NaN' )
	self.fRangeFields[ i ].SetValue( 'NaN' )
      new_value.append( cur_value )
    #end for i

    self.fValues.dataRange = tuple( new_value )
  #end _UpdateRange


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateModeControls()		-
  #----------------------------------------------------------------------
  def _UpdateModeControls( self ):
    custom = 'custom' == self.GetPrecisionMode()
    self.fCustomFormatField.Show( custom )
    self.fCustomFormatLabel.Show( custom )
    self.fPrecisionDigitsCtrl.Show( not custom )
    self.fPrecisionDigitsLabel.Show( not custom )
    self.fPanelSizer.Layout()
  #end _UpdateModeControls


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeBean._UpdateRangeControls()		-
  #----------------------------------------------------------------------
  def _UpdateRangeControls( self ):
    data_range = self.GetDataRange()
    for i in range( len( data_range ) ):
      self.fRangeFields[ i ].SetValue(
	  'NaN' if np.isnan( data_range[ i ] ) else
	  '%.8g' % data_range[ i ]
          )
    #end for i
  #end _UpdateRangeControls


#		-- Property Definitions
#		--

  colormap = property( GetColormap, SetColormap )

  customFormat = property( GetCustomFormat, SetCustomFormat )

  dataRange = property( GetDataRange, SetDataRange )

  precisionDigits = property( GetPrecisionDigits, SetPrecisionDigits )

  precisionMode = property( GetPrecisionMode, SetPrecisionMode )

  scaleType = property( GetScaleType, SetScaleType )

  values = property( GetValues, SetValues )

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

    use_scale_and_cmap = kwargs.get(
        'use_scale_and_cmap',
        kwargs.get( 'enable_scale_and_cmap', True )
        )
    if 'enable_scale_and_cmap' in kwargs:
      del kwargs[ 'enable_scale_and_cmap' ]
    if 'use_scale_and_cmap' in kwargs:
      del kwargs[ 'use_scale_and_cmap' ]

    super( DataRangeDialog, self ).__init__( *args, **kwargs )

    self.GetRange = self.GetDataRange

    self.fBean = None
    self._InitUI(
        bitmap_func = bitmap_func,
	use_scale_and_cmap = use_scale_and_cmap
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
  #	METHOD:		DataRangeDialog.GetCustomFormat()               -
  #----------------------------------------------------------------------
  def GetCustomFormat( self ):
    return  self.fBean.GetCustomFormat()
  #end GetCustomFormat


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog.GetDataRange()			-
  #----------------------------------------------------------------------
  def GetDataRange( self ):
    return  self.fBean.GetDataRange()
  #end GetDataRange


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
  #	METHOD:		DataRangeDialog.GetScaleType()			-
  #----------------------------------------------------------------------
  def GetScaleType( self ):
    return  self.fBean.GetScaleType()
  #end GetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self,
      bitmap_func = None,
      values = None,
#      range_in = None,
#      digits_in = DEFAULT_precisionDigits,
#      mode_in = DEFAULT_precisionMode,
#      scale_type_in = DEFAULT_scaleType,
#      colormap_in = DEFAULT_colormap,
      use_scale_and_cmap = True
      ):
    self.fBean = DataRangeBean(
        self, -1, bitmap_func,
#        range_in = range_in,
#        digits_in = DEFAULT_precisionDigits,
#        mode_in = DEFAULT_precisionMode,
#        scale_type_in = DEFAULT_scaleType,
#        colormap_in = DEFAULT_colormap,
        values = values,
        use_scale_and_cmap = use_scale_and_cmap
	)

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    ok_button = wx.Button( self, wx.ID_OK, label = '&OK' )
    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
    cancel_button = wx.Button( self, wx.ID_CANCEL, label = 'Cancel' )
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
    retcode = wx.ID_CANCEL if obj.GetLabel() == 'Cancel' else  wx.ID_OK

    if obj.GetLabel() != 'Cancel':
      self.fBean.Check()
      #self.fResult = self.fBean.GetRange()

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      #self.fResult = self.fBean.GetRange()
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
  def ShowModal( self, values_in = None ):
    if values_in is None:
      values_in = DataRangeValues()
    self.fBean.SetValues( values_in )
    super( DataRangeDialog, self ).ShowModal()
  #end ShowModal


#		-- Property Definitions
#		--

  bean = property( GetBean )

  colormap = property( GetColormap )

  customFormat = property( GetCustomFormat )

  dataRange = property( GetDataRange )

  precisionDigits = property( GetPrecisionDigits )

  precisionMode = property( GetPrecisionMode )

  scaleType = property( GetScaleType )

  values = property( lambda x: x.fBean.values )

#end DataRangeDialog


#------------------------------------------------------------------------
#	CLASS:		DataRangeValues					-
#------------------------------------------------------------------------
class DataRangeValues( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeValues.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self,
      custom_format = None,
      data_range = EMPTY_RANGE,
      precision_digits = DEFAULT_precisionDigits,
      precision_mode = DEFAULT_precisionMode,
      colormap = DEFAULT_colormap,
      scale_type = DEFAULT_scaleType
      ):
    """
"""
    self.customFormat = custom_format
    self.dataRange = data_range
    self.precisionDigits = precision_digits
    self.precisionMode = precision_mode
    self.colormap = colormap
    self.scaleType = scale_type
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeValues.EqualRange()			-
  #----------------------------------------------------------------------
  def EqualRange( self, that ):
    """
"""
    eq = False
    one = self.dataRange
    if np.isnan( one[ 0 ] ) and np.isnan( that[ 0 ] ) and \
        np.isnan( one[ 1 ] ) and np.isnan( that[ 1 ] ):
      eq = True
    else:
      eq = one == that
    return  eq
  #end EqualRange

#end DataRangeValues
