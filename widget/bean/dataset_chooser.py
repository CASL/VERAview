#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_chooser.py				-
#	HISTORY:							-
#		2015-05-28	leerw@ornl.gov				-
#	  Added scrolled panel.
#		2015-05-12	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )


#------------------------------------------------------------------------
#	EVENT:		DataSetChoiceEvent, EVT_DATASET_CHOICE		-
#	PROPERTIES:							-
#	  value		same as DataSetChooserBean value property
#------------------------------------------------------------------------
#DataSetChoiceEvent, EVT_DATASET_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		DataSetChooserBean				-
#------------------------------------------------------------------------
class DataSetChooserBean( wx.Panel ):
  """Panel containing a table of inputs, one row per available dataset
with columns for visibility (checkbox), axis (checkbox, only two of
which are allowed to be checked), and scale (float).

Attributes/properties:
  value			dict keyed by dataset name of:
			  'axis': 'top', 'bottom', or ''
			  'scale': float
			  'visible': boolean
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetChooserBean.value			-
  #----------------------------------------------------------------------
  @property
  def value( self ):
    """@return		dict reference"""
    return  self.fValue
  #end value.getter


#  @value.deleter
#  def value( self ):
#    pass
#  #end value.deleter


  @value.setter
  def value( self, value_in ):
    """@param  value_in	dict from which to copy"""
    if value_in is not None:
      #self.fValue.clear()
      for k in self.fValue:
        if k in value_in:
	  value_rec = self.fValue[ k ]
	  in_rec = value_in[ k ]
	  for y in value_rec:
	    if y in in_rec:
	      value_rec[ y ] = in_rec[ y ]
      #end for

      self._UpdateControls()
    #end if
  #end value.setter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, ds_names = None ):
    super( DataSetChooserBean, self ).__init__( container, id )

    self.fDataSetNames = [] if ds_names is None else ds_names
    self.fValue = {}
    for name in ds_names:
      self.fValue[ name ] = { 'axis': '', 'scale': 1.0, 'visible': False }

    self.fButtonPanel = None
    self.fDataSetControls = {}
    self.fTablePanel = None
    self.fTableSizer = None

    self._InitUI( self.fDataSetNames )
    self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetChooserBean, self ).Enable( flag )

    for panel in ( self.fButtonPanel, self.fTablePanel ):
      if panel is not None:
        for child in panel.GetChildren():
          if isinstance( child, wx.Window ):
	    child.Enable( flag )
        #end for
      #end if panel exists
    #end for panels

    self._UpdateControls()
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._CreateDataSetControls()	-
  #----------------------------------------------------------------------
  def _CreateDataSetControls( self, parent, ds_name ):
    """
@param  parent		parent window
@param  ds_name		dataset name
@return			dict with
			  'bottom': bottom axis RadioButton
			  'name': name StaticText
			  'scale': scale TextCtrl
			  'top': top axis RadioButton
			  'visible': visibility CheckBox
"""
    sizer = parent.GetSizer()

    name = wx.StaticText(
        parent, -1, label = ds_name,
	style = wx.ALIGN_CENTRE_HORIZONTAL
	)
    sizer.Add( name, 0, wx.ALL | wx.ALIGN_CENTER, 0 )

    visible = wx.CheckBox( parent, -1, label = '' )
    visible.Bind(
        wx.EVT_CHECKBOX,
	functools.partial( self._OnVisible, ds_name )
	)
    sizer.Add( visible, 0, wx.ALL | wx.ALIGN_CENTER, 0 )

    #bottom = wx.RadioButton( parent, -1, label = '', style = wx.RB_SINGLE )
    bottom = wx.CheckBox( parent, -1, label = '' )
    bottom.Bind(
        #wx.EVT_RADIOBUTTON,
        wx.EVT_CHECKBOX,
	functools.partial( self._OnAxis, ds_name, 'bottom' )
	)
    sizer.Add( bottom, 0, wx.ALL | wx.ALIGN_CENTER, 0 )

    #top = wx.RadioButton( parent, -1, label = '', style = wx.RB_SINGLE )
    top = wx.CheckBox( parent, -1, label = '' )
    top.Bind(
        #wx.EVT_RADIOBUTTON,
        wx.EVT_CHECKBOX,
	functools.partial( self._OnAxis, ds_name, 'top' )
	)
    sizer.Add( top, 0, wx.ALL | wx.ALIGN_CENTER, 0 )

    scale = wx.TextCtrl( parent, -1, value = '1.0', size = wx.Size( 16, -1 ) )
    scale.Bind( wx.EVT_KILL_FOCUS, self._OnScaleFocus )
    sizer.Add( scale, 0, wx.ALL | wx.EXPAND, 0 )

    rec = \
      {
      'bottom': bottom,
      'name': name,
      'scale': scale,
      'top': top,
      'visible': visible
      }
    return  rec
  #end _CreateDataSetControls


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, ds_names ):
    """Builds this UI component frame with everything but the items for
manipulating dataset.  That is done with _CreateDataSetUI().
"""
    scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(
        self, -1,
	size = ( 680, 320 ), style = wx.SIMPLE_BORDER
	)
    scroll_panel.SetupScrolling()
    scroll_sizer = wx.BoxSizer( wx.VERTICAL )
    scroll_panel.SetSizer( scroll_sizer )
    #scroll_panel.SetBackgroundColour( wx.Colour( *DEFAULT_BG_COLOR_TUPLE ) )

#		-- Table
#		--
#    self.fTablePanel = wx.Panel( self, -1 )
    self.fTablePanel = wx.Panel( scroll_panel, -1 )

#			-- (rows) cols, vgap, hgap
    table_sizer = wx.GridSizer( len( ds_names ) + 1, 5, 6, 10 )
    self.fTablePanel.SetSizer( table_sizer )

    header_font = self.fTablePanel.GetFont().Bold()
    for header in ( 'DataSet', 'Visible', 'Bottom Axis', 'Top Axis', 'Scale' ):
      item = wx.StaticText(
          self.fTablePanel, -1, label = header,
	  style = wx.ALIGN_CENTRE_HORIZONTAL
	  )
      item.SetFont( header_font )
      table_sizer.Add( item, 0, wx.ALL | wx.EXPAND, 4 )
    #end for

    for ds_name in ds_names:
      controls = self._CreateDataSetControls( self.fTablePanel, ds_name )
      self.fDataSetControls[ ds_name ] = controls
    #end for

    self.fTablePanel.Fit()
    scroll_sizer.Add( self.fTablePanel, 1, wx.EXPAND, 0 )
    scroll_panel.FitInside()

#		-- Buttons
#		--  SUNKEN, RAISED, SIMPLE
    self.fButtonPanel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    load_button = wx.Button( self.fButtonPanel, -1, label = 'Load...' )
    load_button.Bind( wx.EVT_BUTTON, self._OnLoad )
    save_button = wx.Button( self.fButtonPanel, -1, label = 'Save...' )
    save_button.Bind( wx.EVT_BUTTON, self._OnSave )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    self.fButtonPanel.SetSizer( button_sizer )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( load_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddSpacer( 10 )
    button_sizer.Add( save_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddStretchSpacer()

#		-- Lay Out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

#    sizer.Add( self.fTablePanel, 0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 4 )
    sizer.Add( scroll_panel, 1, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 4 )
    sizer.Add( self.fButtonPanel, 0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 4 )

    self.Layout()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean.LoadFile()			-
  #----------------------------------------------------------------------
  def LoadFile( self, path ):
    """May be called from any thread.
"""
    fp = None

    try:
      fp = file( path )
      value_in = json.loads( fp.read() )
      wx.CallAfter( self._LoadFileImpl, value_in )

    except Exception, ex:
      wx.MessageDialog(
	  self, 'Error reading file "%s":\n' + str( ex ),
	  'Load File'
          ).ShowModal()

    finally:
      if fp is not None:
        fp.close()
  #end LoadFile


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._LoadFileImpl()		-
  #----------------------------------------------------------------------
  def _LoadFileImpl( self, value_in ):
    """Must be called from the UI thread.
"""
    self.value = value_in
  #end _LoadFileImpl


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._OnAxis()			-
  #----------------------------------------------------------------------
  def _OnAxis( self, ds_name, axis_name, ev ):
    """Handles events from axis radio buttons.  Called on the UI thread.
"""
    ev.Skip()

    if ev.IsChecked():
      other_axis = 'top' if axis_name == 'bottom' else 'bottom'

      other_radio = self.fDataSetControls[ ds_name ][ other_axis ]
      if other_radio.GetValue():
        other_radio.SetValue( False )

      for k in self.fDataSetControls:
        if k != ds_name:
	  controls = self.fDataSetControls[ k ]
	  if controls[ axis_name ].GetValue():
	    controls[ axis_name ].SetValue( False )
      #end for
    #end if

    self._UpdateValue()
  #end _OnAxis


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._OnLoad()			-
  #----------------------------------------------------------------------
  def _OnLoad( self, ev ):
    """Called on the UI thread.
"""
    ev.Skip()
#    obj = ev.GetEventObject()
#    obj.GetLabel()

    file_dialog = wx.FileDialog(
	self, 'Open Selections File', '', '',
	'JSON files (*.json)|*.json',
	wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
	#wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
        )
    if file_dialog.ShowModal() != wx.ID_CANCEL:
      path = file_dialog.GetPath()
      file_dialog.Destroy()
      self.LoadFile( path )
  #end _OnLoad


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._OnSave()			-
  #----------------------------------------------------------------------
  def _OnSave( self, ev ):
    """Called on the UI thread.
"""
    ev.Skip()
#    obj = ev.GetEventObject()
#    obj.GetLabel()

    file_dialog = wx.FileDialog(
	self, 'Save Selections File', '', '',
	'JSON files (*.json)|*.json',
	wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
	#wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
        )
    if file_dialog.ShowModal() != wx.ID_CANCEL:
      path = file_dialog.GetPath()
      file_dialog.Destroy()
      self.SaveFile( path )
  #end _OnSave


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._OnScaleFocus()		-
  #----------------------------------------------------------------------
  def _OnScaleFocus( self, ev ):
    """Handles focus loss from the scale textctrl.  Called on the UI thread.
"""
    ev.Skip()
    self._UpdateValue()
  #end _OnScaleFocus


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._OnVisible()			-
  #----------------------------------------------------------------------
  def _OnVisible( self, ds_name, ev ):
    """Handles events from the visibility checkbox.  Called on the UI thread.
"""
    ev.Skip()

    rec = self.fDataSetControls[ ds_name ]

    if not ev.IsChecked():
      for k in ( 'bottom', 'top' ):
        rec[ k ].SetValue( False )

    for k in ( 'bottom', 'top', 'scale' ):
      rec[ k ].Enable( ev.IsChecked() )

    self._UpdateValue()
  #end _OnVisible


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean.SaveFile()			-
  #----------------------------------------------------------------------
  def SaveFile( self, path ):
    """May be called from any thread.
"""
    fp = None

    try:
      fp = file( path, 'w' )
      fp.write( json.dumps( self.value ) )

    except Exception, ex:
      wx.MessageDialog(
	  self, 'Error writing file "%s":\n' + str( ex ),
	  'Save File'
          ).ShowModal()

    finally:
      if fp is not None:
        fp.close()
  #end SaveFile


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._UpdateControls()		-
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    """
"""
    for k in self.fValue:
      if k in self.fDataSetControls:
	value_rec = self.fValue[ k ]
        controls = self.fDataSetControls[ k ]

	controls[ 'bottom' ].SetValue( value_rec[ 'axis' ] == 'bottom' )
	controls[ 'top' ].SetValue( value_rec[ 'axis' ] == 'top' )
	controls[ 'scale' ].SetValue( str( value_rec[ 'scale' ] ) )

	visible = value_rec[ 'visible' ]
	controls[ 'visible' ].SetValue( visible )
	for name in ( 'bottom', 'top', 'scale' ):
	  controls[ name ].Enable( visible )
      #end if
    #end for
  #end _UpdateControls


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserBean._UpdateValue()		-
  #----------------------------------------------------------------------
  def _UpdateValue( self ):
    """
"""
    for k in self.fValue:
      if k in self.fDataSetControls:
	value_rec = self.fValue[ k ]
        controls = self.fDataSetControls[ k ]

	value_rec[ 'axis' ] = \
            'top' if controls[ 'top' ].GetValue() else \
	    'bottom' if controls[ 'bottom' ].GetValue() else \
	    ''
        try:
          value_rec[ 'scale' ] = float( controls[ 'scale' ].GetValue() )
        except Exception, ex:
          value_rec[ 'scale' ] = 1.0

        value_rec[ 'visible' ] = controls[ 'visible' ].IsChecked()
      #end if
    #end for
  #end _UpdateValue
#end DataSetChooserBean


#------------------------------------------------------------------------
#	CLASS:		DataSetChooserDialog				-
#------------------------------------------------------------------------
class DataSetChooserDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetChooserBean reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetChooserDialog.bean			-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetChooserDialog.result			-
  #----------------------------------------------------------------------
  @property
  def result( self ):
    """bean value, read-only"""
    return  self.fResult
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'ds_names' parameter.
"""
    if 'ds_names' in kwargs:
      ds_names = kwargs[ 'ds_names' ]
      del kwargs[ 'ds_names' ]
    else:
      ds_names = None

    style = kwargs.get( 'style' )
    if style is None:
      style = wx.DEFAULT_DIALOG_STYLE
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetChooserDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fResult = None

    self._InitUI( ds_names )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialog.GetResult()		-
  #----------------------------------------------------------------------
  def GetResult( self ):
    return  self.fResult
  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, ds_names ):
    self.fBean = DataSetChooserBean( self, -1, ds_names )

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
    self.SetTitle( 'DataSet Chooser' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    if obj.GetLabel() != 'Cancel':
      self.fResult = self.fBean.value

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self, bean_value = None ):
    self.fResult = None
    if bean_value is not None:
      self.fBean.value = bean_value
    super( DataSetChooserDialog, self ).ShowModal()
  #end ShowModal

#end DataSetChooserDialog
