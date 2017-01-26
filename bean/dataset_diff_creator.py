#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_diff_creator.py				-
#	HISTORY:							-
#		2017-01-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *
from widget.bean.dataset_menu import *


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
  def __init__( self, field ):
    self.fField = field
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		MenuWidget.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    if self.fField is not None:
      self.fField.SetValue( str( qds_name ) if qds_name else '' )

#    base_qds_name = DataSetName( self.fBaseNameField.GetValue() )
#    sub_qds_name = DataSetName( self.fSubNameField.GetValue() )
#    diff_ds_name = self.fDiffNameField.GetValue().replace( ' ', '_' )
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

#		-- mode 'subsingle', widget with FireStateChange( **kwargs )
# FireStateChange( **kwargs )
# GetCurDataSet()
# SetDataSet( qds_name )
    self.fBaseDataSetMenu = None
    self.fBaseMenuButton = None
    self.fBaseNameField = None

    self.fButtonPanel = None
    self.fCreateButton = None
    self.fDiffNameField = None

    self.fSubDataSetMenu = None
    self.fSubMenuButton = None
    self.fSubNameField = None

    self._InitUI()
    #self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetDiffCreatorBean, self ).Enable( flag )

    for obj in ( self.fBaseMenuButton, self.fSubMenuButton ):
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
    name_ht = 32

    grid_wrapper = wx.Panel( self, -1, style = wx.BORDER_THEME )
    gw_sizer = wx.BoxSizer( wx.HORIZONTAL )
    grid_wrapper.SetSizer( gw_sizer )

    grid_panel = wx.Panel( grid_wrapper, -1 )
    grid_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    grid_panel.SetSizer( grid_sizer )

#		-- Base panel
#		--
#    base_panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
#    base_panel_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    base_panel.SetSizer( base_panel_sizer )

    self.fBaseNameField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( 320, name_ht )
        )
    self.fBaseNameField.SetEditable( False )

    self.fBaseDataSetMenu = DataSetsMenu(
	self.fState, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( self.fBaseNameField )
        )

    self.fBaseMenuButton = wx.Button( grid_panel, -1, label = 'Select...' )
    self.fBaseMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnShowMenu, self.fBaseMenuButton, self.fBaseDataSetMenu
	    )
	)

    st = wx.StaticText(
        grid_panel, -1, label = 'Base Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fBaseNameField, 0,
	wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fBaseMenuButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Sub panel
#		--
#    sub_panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
#    sub_panel_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    sub_panel.SetSizer( sub_panel_sizer )

    self.fSubNameField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( 320, name_ht )
        )
    self.fSubNameField.SetEditable( False )

    self.fSubDataSetMenu = DataSetsMenu(
	self.fState, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( self.fSubNameField )
        )

    self.fSubMenuButton = wx.Button( grid_panel, -1, label = 'Select...' )
    self.fSubMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnShowMenu, self.fSubMenuButton, self.fSubDataSetMenu
	    )
	)

    st = wx.StaticText(
        grid_panel, -1, label = 'Subend Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fSubNameField, 0,
	wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fSubMenuButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Diff panel
#		--
    self.fCreateButton = wx.Button( grid_panel, -1, label = 'Create' )
    self.fCreateButton.SetFont( self.fCreateButton.GetFont().Larger() )
    #self.fCreateButton.Enable( False )
    self.fCreateButton.Bind( wx.EVT_BUTTON, self._OnCreateDataSet )
    self.fDiffNameField = wx.TextCtrl(
	grid_panel, -1, 'diff_data',
	size = ( 320, name_ht )
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
    grid_sizer.Add(
        self.fCreateButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Lay self out
#		--
    gw_sizer.Add( grid_panel, 0, wx.ALL, 8 )
    gw_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( grid_wrapper, 0, wx.BOTTOM, 10 )
    sizer.AddStretchSpacer()

    self.Fit()

    self.fBaseDataSetMenu.Init()
    self.fSubDataSetMenu.Init()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnCreateDataSet()	-
  #----------------------------------------------------------------------
  def _OnCreateDataSet( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    base_qds_name = DataSetName( self.fBaseNameField.GetValue() )
    sub_qds_name = DataSetName( self.fSubNameField.GetValue() )
    diff_ds_name = self.fDiffNameField.GetValue().replace( ' ', '_' )

    msg = ''
    if len( base_qds_name.displayName ) == 0:
      msg = 'Please select a base dataset'
    elif len( sub_qds_name.displayName ) == 0:
      msg = 'Please select a subend dataset'
    elif len( diff_ds_name ) == 0:
      msg = 'Please enter a difference (result) dataset name'

    if msg:
      wx.MessageDialog( self, msg, 'Create Difference Dataset' ).\
          ShowWindowModal()
    else:
      try:
        dmgr = self.fState.dataModelMgr
	result = \
	    dmgr.CreateDiffDataSet( base_qds_name, sub_qds_name, diff_ds_name )
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
  #end _OnCreateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorBean._OnShowMenu()		-
  #----------------------------------------------------------------------
  def _OnShowMenu( self, button, menu, ev ):
    """
"""
    ev.Skip()
    button.PopupMenu( menu )
  #end _OnShowMenu

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
