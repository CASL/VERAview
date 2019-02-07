#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_diff_creator.py				-
#	HISTORY:							-
#		2019-01-25	leerw@ornl.gov				-
#         Mimic'ing the layout of DataSetCreatorBean.
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-03-31	leerw@ornl.gov				-
#	  Added EVT_CHAR_HOOK
#		2017-02-24	leerw@ornl.gov				-
#		2017-02-16	leerw@ornl.gov				-
#	  Added diff and interp mode comboboxes.
#		2017-02-15	leerw@ornl.gov				-
#	  New approach from Andrew.
#		2017-01-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.agw.toasterbox as wxtb
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *
from data.differences import *
from widget.bean.dataset_menu import *


DIFF_OPTIONS = [ 'Delta', 'Pct Difference' ]

ID_CREATE = wx.NewId()
ID_CREATE_CLOSE = wx.NewId()

INTERP_OPTIONS = [ 'Cubic', 'Quadratic', 'Linear' ]

NAME_FIELD_SIZE = ( 320, 24 )


#------------------------------------------------------------------------
#	CLASS:		MenuWidget					-
#------------------------------------------------------------------------
class MenuWidget( BaseDataModelMenuWidget ):
  """Dummy DataSetModelMenu widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		MenuWidget.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, field, callback = None ):
    self.fCallback = \
        callback  if callback and hasattr( callback, '__call__' ) else  None
    self.fField = field
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		MenuWidget.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    if self.fField is not None:
      self.fField.SetValue( str( qds_name ) if qds_name else '' )

      if self.fCallback:
        self.fCallback()
  #end SetDataSet

#end MenuWidget


#------------------------------------------------------------------------
#	CLASS:		DataSetDiffCreatorBean				-
#------------------------------------------------------------------------
class DataSetDiffCreatorBean( wx.Panel ):
  """Panel with controls for selecting two datasets for calculation and
creating a difference dataset.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.__del__()		-
  #----------------------------------------------------------------------
  def __del__( self ):
    if self.fCompDataSetMenu is not None:
      self.fCompDataSetMenu.Dispose()
    if self.fRefDataSetMenu is not None:
      self.fRefDataSetMenu.Dispose()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, id = -1, show_create_button = True ):
    super( DataSetDiffCreatorBean, self ).__init__( parent, id )

    self._state = state

    self._createButton = None

    self._compDataSetMenu = \
    self._compMenuButton = \
    self._compNameField = None

    self._diffChoice = None
    self._diffNameField = None
    self._interpChoice = None

    self._progressGauge = None

    self._refDataSetMenu = None
    self._refMenuButton = None
    self._refNameField = None

    self._selectCheck = None
    self._workerIsCanceled = False

    self._InitUI( show_create_button )
    #self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._CreateDataSetBegin()	-
  #----------------------------------------------------------------------
  def _CreateDataSetBegin( self,
      ref_qname, comp_qname, diff_ds_name,
      diff_mode, interp_mode,
      do_toast = True, after_callback = None
      ):
    try:
      qds_name = Differences( self._state.dataModelMgr )(
          ref_qname, comp_qname, diff_ds_name,
	  diff_mode = diff_mode, interp_mode = interp_mode,
	  listener = self.OnDataSetProgress
	  )
      result = dict(
          callback = after_callback,
          do_toast = do_toast,
          qds_name = qds_name
          )
    except Exception, ex:
      result = ex

    return  result
  #end _CreateDataSetBegin


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._CreateDataSetEnd()	-
  #----------------------------------------------------------------------
  def _CreateDataSetEnd( self, result ):
    #error_message = None
    error_message = 'Dataset creation failed'
    do_toast = True
    callback = \
    qds_name = None

    try:
      result_obj = None
      if result is not None:
        result_obj = result.get()

      if result_obj is not None:
        if isinstance( result_obj, dict ):
          callback = result_obj.get( 'callback' )
          do_toast = result_obj.get( 'do_toast' )
          qds_name = result_obj.get( 'qds_name' )

	elif isinstance( result_obj, Exception ):
	  error_message += ':\n' + str( result_obj )
      #end if result_obj is not None

      if qds_name is not None:
        error_message = None
        if self._selectCheck.GetValue():
          reason = self._state.Change( None, cur_dataset = qds_name )
          self._state.FireStateChange( reason )
        if do_toast:
          self.\
            ToastMessage( 'Dataset "' + qds_name.displayName + '" was created' )
      #end if qds_name is not None

    except Exception, ex:
      error_message = 'Dataset creation failed:\n' + str( ex )

    finally:
      if self._createButton:
        self._createButton.Enable()
      self._compDataSetMenu.UpdateAllMenus()
      self._refDataSetMenu.UpdateAllMenus()
      #self._progressGauge.Hide()
      self._progressGauge.SetValue( 0 )
      self.Layout()

      if callback and hasattr( callback, '__call__' ):
        callback()
    #end finally

    if error_message:
      wx.MessageDialog( self, error_message, 'Create Difference Dataset' ).\
          ShowWindowModal()
  #end _CreateDataSetEnd


  #----------------------------------------------------------------------
  #	METHOD: DataSetDiffCreatorBean._CreateDiffDataSetGroup()        -
  #----------------------------------------------------------------------
  def _CreateDiffDataSetGroup( self, show_create_button ):
    """
    Returns:
        dict: dict of controls created with keys
            ``group_panel``, ``diff_field``, ``select_check``, and
            optionally ``create_button``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = \
        wx.StaticBox( group_panel, -1, "3. Enter Difference Dataset Name" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    names_panel = wx.Panel( group_box, -1 )
    names_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    names_panel.SetSizer( names_sizer )

#               -- New line
#               --
    diff_label = wx.StaticText(
        names_panel, -1,
	label = 'Difference Name:',
	style = wx.ALIGN_LEFT
	)

    inner_sizer = wx.BoxSizer( wx.HORIZONTAL )
    diff_field = \
        wx.TextCtrl( names_panel, -1, 'diff_data', size = NAME_FIELD_SIZE )
    select_check = wx.CheckBox( names_panel, wx.ID_ANY, "Select Dataset" )
    select_check.SetValue( True )

    inner_sizer.AddMany([
        ( diff_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND, 0 ),
        ( select_check, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.LEFT | wx.RIGHT, 10 ),
        ])

    names_sizer.AddMany([
        ( diff_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( inner_sizer, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND, 0 )
        ])

    if show_create_button:
#		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
      create_button = \
          wx.Button( names_panel, -1, label = 'C&reate' )
      create_button.\
          SetToolTipString( 'Calculate and create difference dataset' )
      create_button.Bind( wx.EVT_BUTTON, self._OnCreate )
      create_button.Enable( False )
      names_sizer.Add(
          create_button, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT, 10
          )

#               -- Layout
#               --
    #group_sizer.Add( names_panel, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 0 )
    group_sizer.Add(
        names_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        diff_field = diff_field,
        group_panel = group_panel,
        select_check = select_check
        )
    if show_create_button:
      items[ 'create_button' ] = create_button
    return  items
  #end _CreateDiffDataSetGroup


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetDiffCreatorBean._CreateMethodGroup()     -
  #----------------------------------------------------------------------
  def _CreateMethodGroup( self ):
    """
    Returns:
        dict: dict of controls created with keys
            ``group_panel``, ``diff_choice``, ``interp_choice``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = \
        wx.StaticBox( group_panel, -1, "2. Select Methods" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    outer_panel = wx.Panel( group_box, -1, style = wx.BORDER_NONE )
    outer_sizer = wx.BoxSizer( wx.HORIZONTAL )
    outer_panel.SetSizer( outer_sizer )

#               -- Difference
#               --
    diff_sizer = wx.BoxSizer( wx.HORIZONTAL )
    #preset_panel.SetSizer( preset_sizer )
    diff_label = wx.StaticText(
        outer_panel, -1, label = 'Difference:',
        style = wx.ALIGN_RIGHT
        )
    diff_choice = wx.Choice( outer_panel, -1, choices = DIFF_OPTIONS )
    diff_choice.SetSelection( 0 )
    diff_sizer.AddMany([
        ( diff_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 8 ),
        ( diff_choice, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT, 0 )
        ])

#               -- Interpolation
#               --
    interp_sizer = wx.BoxSizer( wx.HORIZONTAL )
    #preset_panel.SetSizer( preset_sizer )
    interp_label = wx.StaticText(
        outer_panel, -1, label = 'Interpolation:',
        style = wx.ALIGN_RIGHT
        )
    interp_choice = wx.Choice( outer_panel, -1, choices = INTERP_OPTIONS )
    interp_choice.SetSelection( 0 )
    interp_sizer.AddMany([
        ( interp_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 8 ),
        ( interp_choice, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT, 0 )
        ])

#               -- Layout outer_panel
#               --
    outer_sizer.AddSpacer( 10 )
    outer_sizer.Add(
        diff_sizer, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    outer_sizer.AddSpacer( 10 )
    outer_sizer.Add(
        interp_sizer, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    outer_sizer.AddStretchSpacer()

#               -- Layout group_panel
#               --
    group_sizer.Add(
        outer_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        diff_choice = diff_choice,
        interp_choice = interp_choice,
        group_panel = group_panel
        )
    return  items
  #end _CreateMethodGroup


  #----------------------------------------------------------------------
  #	METHOD: DataSetDiffCreatorBean._CreateSelectDataSetsGroup()     -
  #----------------------------------------------------------------------
  def _CreateSelectDataSetsGroup( self ):
    """
    Returns:
        dict: dict of controls created with keys
            ``group_panel``, ``comp_button``, ``comp_field``, ``comp_menu``,
            ``ref_button``, ``ref_field``, ``ref_menu``
"""
    all_types = DATASET_DEFS.keys()

    group_panel = wx.Panel( self, -1 )
    group_box = wx.StaticBox( group_panel, -1, "1. Select Datasets" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    names_panel = wx.Panel( group_box, -1 )
    names_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    names_panel.SetSizer( names_sizer )

#               -- Comparison line
#               --
    comp_label = wx.StaticText(
        names_panel, -1,
        label = 'Comparison Dataset:',
	style = wx.ALIGN_RIGHT
        )
    comp_field = wx.TextCtrl( names_panel, -1, '', size = NAME_FIELD_SIZE )
    comp_field.SetEditable( False )

    comp_menu = DataSetsMenu(
	self._state, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( comp_field, self.OnNameUpdate )
        )
    comp_button = wx.Button( names_panel, -1, label = 'Select...' )
    comp_button.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnShowMenu, comp_button, comp_menu )
	)

#               -- Reference line
#               --
    ref_label = wx.StaticText(
        names_panel, -1,
        label = 'Reference Dataset:',
	style = wx.ALIGN_RIGHT
        )
    ref_field = wx.TextCtrl( names_panel, -1, '', size = NAME_FIELD_SIZE )
    ref_field.SetEditable( False )

    ref_menu = DataSetsMenu(
	self._state, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( ref_field, self.OnNameUpdate )
        )
    ref_button = wx.Button( names_panel, -1, label = 'Select...' )
    ref_button.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnShowMenu, ref_button, ref_menu )
	)

#               -- Layout names_panel
#               --
    names_sizer.AddMany([
        ( comp_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( comp_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0 ),
        ( comp_button, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT, 10 ),
        ( ref_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( ref_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0 ),
        ( ref_button, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT, 10 )
        ])

#               -- Layout group_panel
#               --
    #group_sizer.Add( names_panel, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 0 )
    group_sizer.Add(
        names_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        group_panel = group_panel,
        comp_button = comp_button,
        comp_field = comp_field,
        comp_menu = comp_menu,
        ref_button = ref_button,
        ref_field = ref_field,
        ref_menu = ref_menu
        )
    return  items
  #end _CreateSelectDataSetsGroup


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.DoCreate()               -
  #----------------------------------------------------------------------
  def DoCreate( self, do_toast = True, after_callback = None ):
    """Must be called on MainThread.
"""
    comp_qds_name = DataSetName( self._compNameField.GetValue() )
    ref_qds_name = DataSetName( self._refNameField.GetValue() )
    diff_ds_name = self._diffNameField.GetValue().replace( ' ', '_' )

    msg = ''
    if len( ref_qds_name.displayName ) == 0:
      msg = 'Please select a reference dataset'
    elif len( comp_qds_name.displayName ) == 0:
      msg = 'Please select a comparison dataset'
    elif len( diff_ds_name ) == 0:
      msg = 'Please enter a difference (result) dataset name'

#		-- Difference name already exists?
    if msg == '':
      diff_qds_name = DataSetName( comp_qds_name.modelName, diff_ds_name )
      if self._state.dataModelMgr.GetDataSetType( diff_qds_name ):
        msg = 'Difference Name "' + diff_ds_name + '" already exists'

    if msg:
      wx.MessageDialog( self, msg, 'Create Difference Dataset' ).\
          ShowWindowModal()
    else:
      if self._createButton:
        self._createButton.Disable()
      self._progressGauge.SetValue( 0 )
      #self._progressGauge.Show()

      diff_ndx = max( self._diffChoice.GetSelection(), 0 )
      diff_mode = self._diffChoice.GetString( diff_ndx ).lower()
      interp_ndx = max( self._interpChoice.GetSelection(), 0 )
      interp_mode = self._interpChoice.GetString( interp_ndx ).lower()

      self._workerIsCanceled = False
      wargs = [
          ref_qds_name, comp_qds_name, diff_ds_name, diff_mode, interp_mode,
          do_toast, after_callback
	  ]
      th = wxlibdr.startWorker(
          self._CreateDataSetEnd,
          self._CreateDataSetBegin,
	  wargs = wargs
	  )
    #end else not: msg
  #end DoCreate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetDiffCreatorBean, self ).Enable( flag )

    for obj in (
        self._refMenuButton, self._compMenuButton, self._createButton
        ):
      if obj is not None:
        obj.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self, show_create_button ):
    """
"""
    ds_items = self._CreateSelectDataSetsGroup()
    self._compDataSetMenu = ds_items.get( 'comp_menu' )
    self._compMenuButton = ds_items.get( 'comp_button' )
    self._compNameField = ds_items.get( 'comp_field' )
    self._refDataSetMenu = ds_items.get( 'ref_menu' )
    self._refMenuButton = ds_items.get( 'ref_button' )
    self._refNameField = ds_items.get( 'ref_field' )

    method_items = self._CreateMethodGroup()
    self._diffChoice = method_items.get( 'diff_choice' )
    self._interpChoice = method_items.get( 'interp_choice' )

    diff_items = self._CreateDiffDataSetGroup( show_create_button )
    self._createButton = diff_items.get( 'create_button' )
    self._diffNameField = diff_items.get( 'diff_field' )
    self._selectCheck = diff_items.get( 'select_check' )

    self._progressGauge = wx.Gauge( self, -1, style = wx.GA_HORIZONTAL )

#               -- Layout
#               --
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetAutoLayout( True )
    self.SetSizer( sizer )

    sizer.AddMany([
        ( ds_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( method_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( diff_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( self._progressGauge, 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 )
        ])
    sizer.AddStretchSpacer()

    self.Fit()
    self._compDataSetMenu.Init()
    self._refDataSetMenu.Init()
    #wx.CallAfter( self._progressGauge.Hide )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnCreate()              -
  #----------------------------------------------------------------------
  def _OnCreate( self, ev ):
    """Must be called on MainThread.  Calls ``DoCreate()``.
"""
    if ev:
      ev.Skip()
    self.DoCreate()
  #end _OnCreate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.OnDataSetProgress()	-
  #----------------------------------------------------------------------
  def OnDataSetProgress( self, message, cur_step, step_count ):
    """Not called on the UI thread.
"""
    wx.CallAfter( self._UpdateProgress, message, cur_step, step_count )
    return  not self._workerIsCanceled
  #end OnDataSetProgress


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.OnNameUpdate()		-
  #----------------------------------------------------------------------
  def OnNameUpdate( self, *args, **kwargs ):
    """
"""
    ref_qds_name = DataSetName( self._refNameField.GetValue() )
    comp_qds_name = DataSetName( self._compNameField.GetValue() )

    if ref_qds_name and comp_qds_name and \
        ref_qds_name.displayName == comp_qds_name.displayName:
      self._diffNameField.SetValue( 'diff_' + ref_qds_name.displayName )
  #end OnNameUpdate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnShowMenu()		-
  #----------------------------------------------------------------------
  def _OnShowMenu( self, button, menu, ev ):
    """
"""
    ev.Skip()
    button.PopupMenu( menu )
  #end _OnShowMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.ToastMessage()           -
  #----------------------------------------------------------------------
  def ToastMessage( self, msg ):
    """
"""
    font = self._diffChoice.GetFont()
    font_size = font.GetPixelSize()
    gauge_pos = self._progressGauge.ClientToScreen( wx.Point( 0, 0 ) )
    gauge_size = self._progressGauge.GetSize()
    info_size = wx.Size( gauge_size.width, font_size.height << 1 )

    info_box = wxtb.ToasterBox( self, tbstyle = wxtb.TB_SIMPLE )
    info_box.SetPopupBackgroundColour( wx.Colour( 176, 196, 222 ) )
    info_box.SetPopupPauseTime( 2000 )
    info_box.SetPopupPosition( gauge_pos )
    info_box.SetPopupSize( info_size )
    info_box.SetPopupTextFont( font )

    info_box.SetPopupText( msg )
    info_box.Play()
  #end ToastMessage


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._UpdateProgress()	-
  #----------------------------------------------------------------------
  def _UpdateProgress( self, message, cur_step, step_count ):
    """Must be called on the UI thread.
"""
    if step_count != self._progressGauge.GetRange():
      self._progressGauge.SetRange( step_count )

    self._progressGauge.SetValue( cur_step )
    #if message != self._progressField.GetLabel():
      #self._progressField.SetLabel( message )

    self.Layout()
  #end _UpdateProgress


#		-- Properties
#		--

  createButton = property( lambda x : x._createButton )

  compDataSetMenu = property( lambda x: x._compDataSetMenu )
  compMenuButton = property( lambda x: x._compMenuButton )
  compNameField = property( lambda x: x._compNameField )

  diffChoice = property( lambda x: x._diffChoice )
  diffNameField = property( lambda x: x._diffNameField )
  interpChoice = property( lambda x: x._interpChoice )

  progressGauge = property( lambda x: x._progressGauge )

  refDataSetMenu = property( lambda x: x._refDataSetMenu )
  refMenuButton = property( lambda x: x._refMenuButton )
  refNameField = property( lambda x: x._refNameField )

  selectCheck = property( lambda x: x._selectCheck )

  state = property( lambda x: x._state )

#end DataSetDiffCreatorBean


#------------------------------------------------------------------------
#	CLASS:		DataSetDiffCreatorDialog			-
#------------------------------------------------------------------------
class DataSetDiffCreatorDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetDiffCreatorBean reference
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.__init__()		-
  #----------------------------------------------------------------------
  #def __init__( self, *args, **kwargs ):
  def __init__( self, parent, state, **kwargs ):
    """
"""
    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetDiffCreatorDialog, self ).__init__( parent, -1, **kwargs )

    self._bean = None
    self._InitUI( state )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.GetApp()               -
  #----------------------------------------------------------------------
  def GetApp( self ):
    """Not sure why this is necessary, but ``wx.App.Get()`` called in
DataModelMenu returns a ``wx.App`` instance, not a ``VeraViewApp`` instance.
"""
    return  wx.App.Get()
  #end GetApp


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self, state ):
    self._bean = \
        DataSetDiffCreatorBean( self, state, show_create_button = False )

    create_button = wx.Button( self, ID_CREATE, label = 'C&reate' )
    create_button.Bind( wx.EVT_BUTTON, self._OnButton )

    create_close_button = \
        wx.Button( self, ID_CREATE_CLOSE, label = 'Cre&ate and Close' )
    create_close_button.Bind( wx.EVT_BUTTON, self._OnButton )

    close_button = wx.Button( self, wx.ID_CLOSE, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
    close_button.SetDefault()

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    button_sizer.AddStretchSpacer()
    button_sizer.AddMany([
        ( create_button, 0, wx.ALL | wx.EXPAND, 6 ),
        ( create_close_button, 0, wx.ALL | wx.EXPAND, 6 ),
        ( close_button, 0, wx.ALL | wx.EXPAND, 6 )
        ])
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
	self._bean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )
    self.SetAutoLayout( True )
    self.SetSizer( sizer )
    self.SetTitle( 'Difference Dataset Creation' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

    button = ev.GetEventObject()
    button_id = ev.GetEventObject().GetId()

    if button_id == ID_CREATE:
      self._bean.DoCreate()
    elif button_id == ID_CREATE_CLOSE:
      self._bean.DoCreate( False, lambda : self.EndModal( button_id ) )
    else:
      self.EndModal( button_id )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog._OnCharHook()          -
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
#    if code == wx.WXK_RETURN:
#      self.EndModal( wx.ID_OK )
#    elif code == wx.WXK_ESCAPE:
#      self.EndModal( wx.ID_CANCEL )
    if code == wx.WXK_RETURN or code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CLOSE )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    return  super( DataSetDiffCreatorDialog, self ).ShowModal()
  #end ShowModal


#		-- Properties
#		--

  bean = property( lambda x : x._bean )

#end DataSetDiffCreatorDialog
