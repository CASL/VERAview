#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_mgr.py					-
#	HISTORY:							-
#		2015-11-12	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
#import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *


#------------------------------------------------------------------------
#	EVENT:		DataSetChoiceEvent, EVT_DATASET_CHOICE		-
#	PROPERTIES:							-
#	  value		same as DataSetChooserBean value property
#------------------------------------------------------------------------
#DataSetChoiceEvent, EVT_DATASET_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		DataSetManagerBean				-
#------------------------------------------------------------------------
class DataSetManagerBean( wx.Panel ):
  """Panel with controls for adding and removing (for now) calculated
average datasets.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, data_model, id = -1 ):
    super( DataSetManagerBean, self ).__init__( container, id )

    self.fDataModel = data_model

    #extra_names = data_model.GetDataSetNames( 'extra' )
    #self.fExtraNames = [] if extra_names == None else extra_names

    self.fButtonPanel = None
    self.fCategoryListBoxes = {}
    self.fCategoryTabs = None
    self.fExtrasList = None
    #self.fTablePanel = None
    #self.fTableSizer = None

    self._InitUI()
    self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean._CreateExtraControls()	-
  #----------------------------------------------------------------------
  def _CreateExtraControls( self, parent, dset ):
    """
@param  parent		parent window
@param  dset		h5py.Dataset object
@return			dict with
			  'delete': delete CheckBox
			  'name': name StaticText
			  'shape': shape StaticText
"""
    ds_name = dset.name.replace( '/', '' )

    sizer = parent.GetSizer()

    delete_field = wx.CheckBox( parent, -1, label = '' )
#    delete_field.Bind(
#        wx.EVT_CHECKBOX,
#	functools.partial( self._OnDelete, ds_name )
#	)
    sizer.Add( delete_field, 0, wx.ALL | wx.ALIGN_CENTER, 0 )

    name_field = wx.StaticText(
        parent, -1, label = ds_name,
	style = wx.ALIGN_LEFT
	)
    sizer.Add( name_field, 0, wx.ALL | wx.EXPAND, 0 )

    shape_field = wx.StaticText(
	parent, -1, label = str( dset.shape ),
	style = wx.ALIGN_LEFT
        )
    sizer.Add( shape_field, 0, wx.ALL | wx.ALIGN_LEFT, 0 )

    rec = \
      {
      'delete': delete_field,
      'name': name_field,
      'shape': shape_field
      }
    return  rec
  #end _CreateExtraControls


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetManagerBean, self ).Enable( flag )

    for panel in ( self.fButtonPanel, self.fTablePanel ):
      if panel != None:
        for child in panel.GetChildren():
          if isinstance( child, wx.Window ):
	    child.Enable( flag )
        #end for
      #end if panel exists
    #end for panels

    self._UpdateControls()
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""

#		-- Current extras Grid
#		--
    self.fExtrasList = wx.ListCtrl(
	self, wx.ID_ANY,
	style = wx.LC_REPORT | wx.LC_VRULES
        )
    self.fExtrasList.InsertColumn( 0, 'Name' )
    self.fExtrasList.InsertColumn( 1, 'Shape' )

    self.fExtrasList.InsertStringItem( 0, 'X' * 64 )
    self.fExtrasList.SetStringItem( 0, 1, '(99, 99, 99, 99)' )
    for i in range( self.fExtrasList.GetColumnCount() ):
      self.fExtrasList.SetColumnWidth( i, -1 )
    self.fExtrasList.Fit()

#		-- NoteBook for dataset category lists
#		--
    self.fCategoryTabs = wx.Notebook( self, -1, style = wx.NB_TOP )
    self.fCategoryTabs.SetBackgroundColour( wx.Colour( 255, 255, 0 ) )

    for category in ( 'channel', 'pin' ):
      names = self.fDataModel.GetDataSetNames( category )
      if len( names ) > 0:
        label = category[ 0 ].upper() + category[ 1 : ]
        lb = wx.ListBox(
	    self.fCategoryTabs, -1,
	    choices = names,
	    #size = ( 320, 100 ),
	    style = wx.LB_ALWAYS_SB | wx.LB_SINGLE | wx.LB_SORT
	    )
        self.fCategoryTabs.AddPage( lb, label )
        self.fCategoryListBoxes[ category ] = lb
      #end if
    #end for

    if self.fCategoryTabs.GetPageCount() > 0:
      self.fCategoryTabs.ChangeSelection( 0 )

#		-- Buttons
#		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
    self.fButtonPanel = wx.Panel( self, -1, style = wx.BORDER_NONE )

    create_button = wx.Button( self.fButtonPanel, -1, label = 'Create Extra Dataset' )
    #create_button.SetToolTipString( 'Create/calculate a dataset' )
    create_button.Bind( wx.EVT_BUTTON, self._OnCreate )

    delete_button = wx.Button( self.fButtonPanel, -1, label = 'Delete Extra Datasets' )
    #delete_button.SetToolTipString( 'Delete the selected extra datasets' )
    delete_button.Bind( wx.EVT_BUTTON, self._OnDelete )

    button_sizer = wx.BoxSizer( wx.VERTICAL )
    self.fButtonPanel.SetSizer( button_sizer )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( create_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddSpacer( 8 )
    button_sizer.Add( delete_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddStretchSpacer()

#		-- Lay Out
#		--
    lower_sizer = wx.BoxSizer( wx.HORIZONTAL )
    lower_sizer.Add( self.fCategoryTabs, 1, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 0 )
    lower_sizer.Add( self.fButtonPanel, 0, wx.ALL | wx.ALIGN_TOP | wx.EXPAND, 0 )
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add(
	wx.StaticText(
	    self, -1,
	    label = 'Extra Datasets', style = wx.ALIGN_LEFT
	    ),
	0, wx.LEFT | wx.TOP, 4
        )
    sizer.Add( self.fExtrasList, 1, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 4 )
    sizer.AddSpacer( 10 )
    sizer.Add(
	wx.StaticText(
	    self, -1, 
	    label = 'Source Datasets', style = wx.ALIGN_LEFT
	    ),
	0, wx.LEFT, 4
        )
    sizer.Add( lower_sizer, 0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 4 )

    self.Fit()
    #self.Layout()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean._OnCreate()			-
  #----------------------------------------------------------------------
  def _OnCreate( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()
  #end _OnCreate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean._OnDelete()			-
  #----------------------------------------------------------------------
  def _OnDelete( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()
  #end _OnDelete


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerBean._UpdateControls()		-
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    """
"""
    self.fExtrasList.DeleteAllItems()

    #extra_names = self.fDataModel.GetDataSetNames( 'extra' )
    extra_states = self.fDataModel.GetExtraStates()
    if extra_states != None and len( extra_states ) > 0:
      st = self.fDataModel.GetExtraState( 0 )

      ndx = 0
      for name in sorted( st.GetGroup().keys() ):
	ds = st.GetDataSet( name )
	self.fExtrasList.InsertStringItem( ndx, name )
	self.fExtrasList.SetStringItem( ndx, 1, str( ds.shape ) )
      #end for
    #end if

#    for i in range( self.fExtrasList.GetColumnCount() ):
#      self.fExtrasList.SetColumnWidth( i, -1 )
#    self.fExtrasList.Fit()
  #end _UpdateControls
#end DataSetManagerBean


#------------------------------------------------------------------------
#	CLASS:		DataSetManagerDialog				-
#------------------------------------------------------------------------
class DataSetManagerDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetManagerBean reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetManagerDialog.bean			-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'data_model' parameter.
"""
#		-- Assert
#		--
    if 'data_model' not in kwargs:
      raise  Exception( 'data_model argument required' )

    data_model = kwargs.get( 'data_model' )
    del kwargs[ 'data_model' ]

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetManagerDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    #self.fResult = None

    self._InitUI( data_model )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialog.GetResult()		-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, data_model ):
    self.fBean = DataSetManagerBean( self, data_model, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

#    ok_button = wx.Button( self, label = '&OK' )
#    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
#    cancel_button = wx.Button( self, label = 'Cancel' )
#    cancel_button.Bind( wx.EVT_BUTTON, self._OnButton )

#    button_sizer.AddStretchSpacer()
#    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 );
#    button_sizer.AddSpacer( 10 )
#    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 );
#    button_sizer.AddStretchSpacer()

    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
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
    self.SetTitle( 'DataSet Manager' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    super( DataSetManagerDialog, self ).ShowModal()
  #end ShowModal

#end DataSetManagerDialog
