#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_diff_creator.py				-
#	HISTORY:							-
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
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *
from data.differences import *
from widget.bean.dataset_menu import *


DIFF_OPTIONS = [ 'Delta', 'Pct Difference' ]

INTERP_OPTIONS = [ 'Cubic', 'Quadratic', 'Linear' ]


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
  #	METHOD:		DataSetDiffCreatorBean.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, id = -1 ):
    super( DataSetDiffCreatorBean, self ).__init__( parent, id )

    self.fState = state
    #self.fDataMgr = state.dataModelMgr

    self.fButtonPanel = None
    self.fCreateButton = None

    self.fCompDataSetMenu = None
    self.fCompMenuButton = None
    self.fCompNameField = None

    self.fDiffComboBox = None
    self.fDiffNameField = None
    self.fGridSizer = None
    self.fInterpComboBox = None

    self.fProgressField = None
    self.fProgressSizer = None

    self.fRefDataSetMenu = None
    self.fRefMenuButton = None
    self.fRefNameField = None

    self.fSelectionBox = None

    self.fWorkerIsCanceled = False

    self._InitUI()
    #self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._CreateDataSetBegin()	-
  #----------------------------------------------------------------------
  def _CreateDataSetBegin(
      self, ref_qname, comp_qname, diff_ds_name,
      diff_mode, interp_mode
      ):
    try:
      #dmgr = self.fState.dataModelMgr
      #result = dmgr.CreateDiffDataSet

      result = Differences( self.fState.dataModelMgr )(
          ref_qname, comp_qname, diff_ds_name,
	  diff_mode = diff_mode, interp_mode = interp_mode,
	  listener = self.OnDataSetProgress
	  )
    except Exception, ex:
      result = ex
    return  result
  #end _CreateDataSetBegin


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._CreateDataSetEnd()	-
  #----------------------------------------------------------------------
  def _CreateDataSetEnd( self, result ):
    error_message = None
    new_qname = None

    try:
      result_obj = None
      if result is None:
        error_message = 'Dataset creation failed'
      else:
        result_obj = result.get()

      if result_obj is None:
        error_message = 'Dataset creation failed'

      elif isinstance( result_obj, DataSetName ):
	new_qname = result_obj
        if self.fSelectBox.GetValue():
	  reason = self.fState.Change( None, cur_dataset = new_qname )
          self.fState.FireStateChange( reason )

      else:
        error_message = 'Dataset creation failed'
	if isinstance( result_obj, Exception ):
	  error_message += ':\n' + str( result_obj )
      #end if-else on result_obj

    except Exception, ex:
      error_message = 'Dataset creation failed:\n' + str( ex )

    finally:
      self.fCreateButton.Enable()
      self.fProgressGauge.Hide()
      self.fProgressGauge.SetValue( 0 )
      label = ('Created %s' % new_qname) if new_qname else ''
      self.fProgressField.SetLabel( label )
      self.Layout()

    if error_message:
      wx.MessageDialog( self, error_message, 'Create Difference Dataset' ).\
          ShowWindowModal()
  #end _CreateDataSetEnd


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetDiffCreatorBean, self ).Enable( flag )

    for obj in ( self.fRefMenuButton, self.fCompMenuButton ):
      if obj is not None:
        obj.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    all_types = DATASET_DEFS.keys()
    name_ht = 28
    name_wd = 320

    grid_wrapper = wx.Panel( self, -1, style = wx.BORDER_THEME )
    gw_sizer = wx.BoxSizer( wx.HORIZONTAL )
    grid_wrapper.SetSizer( gw_sizer )

    grid_panel = wx.Panel( grid_wrapper, -1 )
    self.fGridSizer = \
    grid_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    grid_panel.SetSizer( grid_sizer )

#		-- Comparison panel
#		--
    self.fCompNameField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd, name_ht )
        )
    self.fCompNameField.SetEditable( False )

    self.fCompDataSetMenu = DataSetsMenu(
	self.fState, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( self.fCompNameField, self.OnNameUpdate )
        )

    self.fCompMenuButton = wx.Button( grid_panel, -1, label = 'Select...' )
    self.fCompMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnShowMenu, self.fCompMenuButton, self.fCompDataSetMenu
	    )
	)

    st = wx.StaticText(
        grid_panel, -1, label = 'Comparison Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fCompNameField, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fCompMenuButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Reference panel
#		--
    self.fRefNameField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd, name_ht )
        )
    self.fRefNameField.SetEditable( False )

    self.fRefDataSetMenu = DataSetsMenu(
	self.fState, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( self.fRefNameField, self.OnNameUpdate )
        )

    self.fRefMenuButton = wx.Button( grid_panel, -1, label = 'Select...' )
    self.fRefMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnShowMenu, self.fRefMenuButton, self.fRefDataSetMenu
	    )
	)

    st = wx.StaticText(
        grid_panel, -1, label = 'Reference Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fRefNameField, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fRefMenuButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Diff panel
#		--
    self.fDiffNameField = wx.TextCtrl(
	grid_panel, -1, 'diff_data',
	size = ( name_wd, name_ht )
        )

    st = wx.StaticText(
        grid_panel, -1, label = 'Difference Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fDiffNameField, 0,
	wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.AddSpacer( 0 )

#		-- Combo boxes
#		--
    self.fDiffComboBox = wx.ComboBox(
        grid_panel, -1, DIFF_OPTIONS[ 0 ],
	choices = DIFF_OPTIONS
	)
    self.fInterpComboBox = wx.ComboBox(
        grid_panel, -1, INTERP_OPTIONS[ 0 ],
	choices = INTERP_OPTIONS
	)

    combos_sizer = wx.BoxSizer( wx.HORIZONTAL )
    st = wx.StaticText(
        grid_panel, -1, label = 'Difference:',
	style = wx.ALIGN_RIGHT
	)
    combos_sizer.Add(
        st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 4
	)
    combos_sizer.Add(
	self.fDiffComboBox, 0,
	wx.ALIGN_LEFT | wx.ALL, 0
        )
    combos_sizer.AddSpacer( 16 )
    st = wx.StaticText(
        grid_panel, -1, label = 'Interpolation:',
	style = wx.ALIGN_RIGHT
	)
    combos_sizer.Add(
        st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 4
	)
    combos_sizer.Add(
	self.fInterpComboBox, 0,
	wx.ALIGN_LEFT | wx.ALL, 0
        )

    grid_sizer.AddSpacer( 0 )
    grid_sizer.Add( combos_sizer, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    grid_sizer.AddSpacer( 0 )

#		-- Create row
#		--
    self.fCreateButton = wx.Button( grid_panel, -1, label = 'Create', size = ( -1, 28 ) )
    self.fCreateButton.SetFont( self.fCreateButton.GetFont().Larger() )
    self.fCreateButton.Bind( wx.EVT_BUTTON, self._OnCreateDataSet )

    self.fSelectBox = wx.CheckBox( grid_panel, wx.ID_ANY, "Select New Dataset" )

    create_sizer = wx.BoxSizer( wx.HORIZONTAL )
    create_sizer.Add(
	self.fCreateButton, 0,
	wx.ALIGN_CENTRE | wx.ALL, 0
        )
    create_sizer.AddSpacer( 16 )
    create_sizer.Add( self.fSelectBox, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    self.fSelectBox.SetValue( True )

    grid_sizer.AddSpacer( 0 )
    grid_sizer.Add( create_sizer, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    grid_sizer.AddSpacer( 0 )

#		-- Progress
#		--
    self.fProgressField = \
        wx.StaticText( self, -1, label = '', style = wx.ALIGN_LEFT )
    self.fProgressGauge = wx.Gauge( self, wx.ID_ANY, size = ( 40, 24 ) )
    self.fProgressGauge.SetValue( 0 )

#		-- Lay self out
#		--
    gw_sizer.Add( grid_panel, 0, wx.ALL, 8 )
    gw_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( grid_wrapper, 0, wx.BOTTOM, 10 )
    sizer.Add(
        self.fProgressField, 0,
	wx.ALIGN_LEFT | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT,
	10
	)
    sizer.Add(
        self.fProgressGauge, 0,
	wx.ALIGN_LEFT | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT,
	10
	)
    sizer.AddStretchSpacer()

    self.Fit()

    self.fRefDataSetMenu.Init()
    self.fCompDataSetMenu.Init()
    #self.fProgressGauge.Hide()
    wx.CallAfter( self.fProgressGauge.Hide )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnCreateDataSet()	-
  #----------------------------------------------------------------------
  def _OnCreateDataSet( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    ref_qds_name = DataSetName( self.fRefNameField.GetValue() )
    comp_qds_name = DataSetName( self.fCompNameField.GetValue() )
    diff_ds_name = self.fDiffNameField.GetValue().replace( ' ', '_' )

    msg = ''
    if len( ref_qds_name.displayName ) == 0:
      msg = 'Please select a reference dataset'
    elif len( comp_qds_name.displayName ) == 0:
      msg = 'Please select a comparison dataset'
    elif len( diff_ds_name ) == 0:
      msg = 'Please enter a difference (result) dataset name'

    if msg:
      wx.MessageDialog( self, msg, 'Create Difference Dataset' ).\
          ShowWindowModal()
    else:
      self.fCreateButton.Disable()
      self.fProgressGauge.SetValue( 0 )
      self.fProgressGauge.Show()

      diff_mode = self.fDiffComboBox.GetStringSelection().lower()
      interp_mode = self.fInterpComboBox.GetStringSelection().lower()

      self.fWorkerIsCanceled = False
      wargs = [
          ref_qds_name, comp_qds_name, diff_ds_name, diff_mode, interp_mode
	  ]
      th = wxlibdr.startWorker(
          self._CreateDataSetEnd,
          self._CreateDataSetBegin,
	  wargs = wargs
	  )
    #end if-else msg
  #end _OnCreateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnCreateDataSet_orig()	-
  #----------------------------------------------------------------------
  def _OnCreateDataSet_orig( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    ref_qds_name = DataSetName( self.fRefNameField.GetValue() )
    comp_qds_name = DataSetName( self.fCompNameField.GetValue() )
    diff_ds_name = self.fDiffNameField.GetValue().replace( ' ', '_' )

    msg = ''
    if len( ref_qds_name.displayName ) == 0:
      msg = 'Please select a reference dataset'
    elif len( comp_qds_name.displayName ) == 0:
      msg = 'Please select a comparison dataset'
    elif len( diff_ds_name ) == 0:
      msg = 'Please enter a difference (result) dataset name'

    if msg:
      wx.MessageDialog( self, msg, 'Create Difference Dataset' ).\
          ShowWindowModal()
    else:
      try:
	#xxx Progress dialog
        dmgr = self.fState.dataModelMgr
	result = \
	    dmgr.CreateDiffDataSet( ref_qds_name, comp_qds_name, diff_ds_name )
        wx.MessageDialog(
	    self,
	    'Dataset "%s" created' % str( result ),
	    'Create Difference Dataset'
	    ).\
	    ShowWindowModal()
      except Exception, ex:
        wx.MessageDialog(
	    self, str( ex ),
	    'Error Creating Difference Dataset'
	    ).\
	    ShowWindowModal()
    #end if-else msg
  #end _OnCreateDataSet_orig


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.OnDataSetProgress()	-
  #----------------------------------------------------------------------
  def OnDataSetProgress( self, message, cur_step, step_count ):
    """Not called on the UI thread.
"""
    wx.CallAfter( self._UpdateProgress, message, cur_step, step_count )
    return  not self.fWorkerIsCanceled
  #end OnDataSetProgress


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.OnNameUpdate()		-
  #----------------------------------------------------------------------
  def OnNameUpdate( self, *args, **kwargs ):
    """
"""
    ref_qds_name = DataSetName( self.fRefNameField.GetValue() )
    comp_qds_name = DataSetName( self.fCompNameField.GetValue() )

    if ref_qds_name and ref_qds_name.displayName == comp_qds_name.displayName:
      self.fDiffNameField.SetValue( 'diff_' + ref_qds_name.displayName )
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
  #	METHOD:		DataSetDiffCreatorBean._UpdateProgress()	-
  #----------------------------------------------------------------------
  def _UpdateProgress( self, message, cur_step, step_count ):
    """Must be called on the UI thread.
"""
    if step_count != self.fProgressGauge.GetRange():
      self.fProgressGauge.SetRange( step_count )

    self.fProgressGauge.SetValue( cur_step )

    if message != self.fProgressField.GetLabel():
      self.fProgressField.SetLabel( message )

    self.Layout()
  #end _UpdateProgress

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


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetDiffCreatorDialog.bean			-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'state' parameter.
"""
#		-- Assert
#		--
    if 'state' not in kwargs:
      raise  Exception( 'state argument required' )

    state = kwargs.get( 'state' )
    del kwargs[ 'state' ]

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetDiffCreatorDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    #self.fResult = None

    self._InitUI( state )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.GetResult()		-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self, state ):
    self.fBean = DataSetDiffCreatorBean( self, state, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
    close_button.SetDefault()

    button_sizer.AddStretchSpacer()
    button_sizer.Add( close_button, 0, wx.ALL | wx.EXPAND, 6 );
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
    self.SetTitle( 'Difference Dataset Creation' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    super( DataSetDiffCreatorDialog, self ).ShowModal()
  #end ShowModal

#end DataSetDiffCreatorDialog
