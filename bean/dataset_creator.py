#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		dataset_creator.py				-
#	HISTORY:							-
#		2019-01-11	leerw@ornl.gov				-
#         Fixed bugginess.
#		2018-11-27	leerw@ornl.gov				-
#		2018-11-24	leerw@ornl.gov				-
#         New 'axis_names' tuple in dataset definition.
#		2018-11-09	leerw@ornl.gov				-
#         Resurrected to use in new derived data scheme.
#		2016-10-26	leerw@ornl.gov				-
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2015-11-14	leerw@ornl.gov				-
#		2015-11-13	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, logging, json, math, os, six, sys, time, traceback
import numpy as np
#import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.agw.toasterbox as wxtb
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *

from widget.bean.dataset_menu import *


ID_CREATE = wx.NewId()
ID_CREATE_CLOSE = wx.NewId()

DERIVATION_METHODS = \
  [
    ( 'Average', 'avg' ),
    ( 'Root Mean Square', 'rms' ),
    ( 'Standard Deviation', 'stddev' )
  ]
#METHOD_NAMES = \
#  {
#  'Average': 'avg',
#  'Root Mean Squre': 'rms',
#  'Standard Deviation': 'stddev'
#  }

NAME_FIELD_SIZE = ( 320, 24 )

## Defined in data.datamodel
## AXIS_PRESET_DEFS = \
##   {
##   'assembly': ( 'assembly', 'axial' ),
##   'axial': ( 'axial', ),
##   #'chan_node': ( 'channel', ),
##   'chan_radial': ( 'assembly', 'channel' ),
##   'core': (),
##   #'node': ( 'pin', ),
##   'radial': ( 'assembly', 'pin' ),
##   'radial_assembly': ( 'assembly', ),
##   #'radial_node': ( 'assembly', 'node' )
##   }


#------------------------------------------------------------------------
#	EVENT:		DataSetChoiceEvent, EVT_DATASET_CHOICE		-
#	PROPERTIES:							-
#	  value		same as DataSetChooserBean value property
#------------------------------------------------------------------------
#DataSetChoiceEvent, EVT_DATASET_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorBean				-
#------------------------------------------------------------------------
class DataSetCreatorBean( wx.Panel ):
  """Panel with controls for specifying what axes of the dataset over
which to average.
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.__del__()                    -
  #----------------------------------------------------------------------
  def __del__( self ):
    if self._sourceDataSetMenu is not None:
      self._sourceDataSetMenu.Dispose()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, state, id = -1, show_create_button = True ):
    super( DataSetCreatorBean, self ).__init__( container, id )

    self._state = state

    self._axisNames = None
    self._dataSetDef = None
    self._shape = None

    self._axisCheckBoxes = []
    self._axisPanel = \
    self._createButton = \
    self._factorsCheckBox = \
    self._factorsField = \
    self._methodChoice = \
    self._newNameField = \
    self._presetChoice = \
    self._progressGauge = None
    #self._statusField = None

    self._sourceDataSetMenu = \
    self._sourceMenuButton = \
    self._sourceNameField = None

    self._InitUI( show_create_button )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.ApplyPreset()                -
  #----------------------------------------------------------------------
  def ApplyPreset( self, preset ):
    """
"""
    preset_axes = AXIS_PRESET_DEFS.get( preset )
    if preset_axes is not None and self._axisNames:
      for i in range( len( self._axisNames ) ):
        axis_pair = self._axisNames[ i ]
        checked = axis_pair[ 1 ] not in preset_axes
        self._axisCheckBoxes[ i ].SetValue( checked )

      qds_name = DataSetName( self._sourceNameField.GetValue() )
      self._newNameField.SetValue( preset + '_' + qds_name.displayName )
    #end if preset_def and self._axisNames
  #end ApplyPreset


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetCreatorBean._CreateAxisGroup()           -
  #----------------------------------------------------------------------
  def _CreateAxisGroup( self ):
    """
    Returns:
        dict: dict of controls created with keys
            ``axis_panel``, ``group_panel``, ``preset_choice``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = \
        wx.StaticBox( group_panel, -1, "2. Select Axes Over Which to Derive" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    outer_panel = wx.Panel( group_box, -1, style = wx.BORDER_NONE )
    outer_sizer = wx.BoxSizer( wx.HORIZONTAL )
    outer_panel.SetSizer( outer_sizer )

    dc = wx.WindowDC( self )
    extent = dc.GetFullTextExtent( 'Assembly' )
    axis_panel = wx.Panel(
        outer_panel, -1,
        size = ( extent[ 0 ] * 5, extent[ 1 ] * 6 ), style = wx.BORDER_THEME
        )

    right_panel = wx.Panel( outer_panel, -1, style = wx.BORDER_NONE )
    right_sizer = wx.BoxSizer( wx.VERTICAL )
    right_panel.SetSizer( right_sizer )

    #preset_panel = wx.Panel( button_panel, -1, style = wx.BORDER_NONE )
    preset_sizer = wx.BoxSizer( wx.HORIZONTAL )
    #preset_panel.SetSizer( preset_sizer )
    preset_label = wx.StaticText(
        right_panel, -1, label = 'Preset:',
        style = wx.ALIGN_RIGHT
        )
    preset_choice = wx.Choice( right_panel, -1 )
    preset_choice.Bind( wx.EVT_CHOICE, self._OnPreset )
    preset_sizer.AddMany([
        ( preset_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 8 ),
        ( preset_choice, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT, 0 )
        ])


##		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
#    create_button = \
#        wx.Button( right_panel, -1, label = 'C&reate Derived Dataset' )
#    #create_button.SetToolTipString( 'Create/calculate a dataset' )
#    create_button.Bind( wx.EVT_BUTTON, self._OnCreate )
#    create_button.Enable( False )

    right_sizer.Add( preset_sizer, 0, wx.BOTTOM | wx.EXPAND, 6 )
    right_sizer.AddStretchSpacer()
#    right_sizer.Add( create_button, 0, wx.EXPAND | wx.TOP, 6 )

    outer_sizer.AddMany([
        ( axis_panel, 1,
          wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6 ),
        ( right_panel, 0,
          wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6 )
        ])


#               -- Layout
#               --
    group_sizer.Add(
        outer_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        axis_panel = axis_panel,
        #create_button = create_button,
        group_panel = group_panel,
        preset_choice = preset_choice
        )
    return  items
  #end _CreateAxisGroup


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetCreatorBean._CreateDataSetGroup_()       -
  #----------------------------------------------------------------------
  def _CreateDataSetGroup_( self ):
    """
    Returns:
        dict: dict of controls created with keys
            factors_checkbox, group_box, new_field
            src_button, src_field, src_menu
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = wx.StaticBox( group_panel, -1, "Dataset Selection" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    names_panel = wx.Panel( group_box, -1 )
    names_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    names_panel.SetSizer( names_sizer )

#               -- Source line
#               --
    src_label = wx.StaticText(
        names_panel, -1,
        label = 'Source Dataset:',
	style = wx.ALIGN_RIGHT
        )
    src_field = wx.TextCtrl( names_panel, -1, '', size = NAME_FIELD_SIZE )
    src_field.SetEditable( False )
    src_button = wx.Button( names_panel, -1, label = 'Select...' )

    ds_types = [
        v.get( 'type' )
        for v in six.itervalues( DATASET_DEFS )
        if v.get( 'axis_names' ) and
            v.get( 'copy_shape_expr', v.get( 'shape_expr' ) ).count( ',' ) == 3
        ]
    src_menu = DataSetsMenu(
        self._state, binder = self, mode = 'subsingle',
	ds_types = ds_types,
	widget = DataSetCreatorMenuWidget( src_field, self._OnNameUpdate )
        )
    src_button.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnShowMenu, src_button, src_menu )
	)

    names_sizer.AddMany([
        ( src_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( src_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0 ),
        ( src_button, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT, 10 )
        ])

#               -- New line
#               --
    new_label = wx.StaticText(
        names_panel, -1,
	label = 'New Dataset:',
	style = wx.ALIGN_LEFT
	)
    new_field = \
        wx.TextCtrl( names_panel, -1, 'unnamed', size = NAME_FIELD_SIZE )
    names_sizer.AddMany([
        ( new_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( new_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND, 0 ),
        ( wx.StaticText( names_panel, -1, '' ), 0, wx.EXPAND, 0 )
        ])

#               -- Factors line
#               --
#    factors_label = wx.StaticText(
#        names_panel, -1,
#	label = 'Use Factors:',
#	style = wx.ALIGN_LEFT
#	)
    factors_checkbox = wx.CheckBox( names_panel, -1, 'Use Factors' )
    factors_checkbox.SetValue( True )

    names_sizer.AddMany([
        ( factors_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.BOTTOM, 8 ),
        ( factors_checkbox, 1,
          #wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT,
          wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.RIGHT,
          4 ),
        ( wx.StaticText( names_panel, -1, '' ), 0, wx.EXPAND, 0 )
        ])

#               -- Layout
#               --
    group_sizer.Add( names_panel, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 0 )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        factors_checkbox = factors_checkbox,
        group_panel = group_panel,
        new_field = new_field,
        src_button = src_button,
        src_field = src_field,
        src_menu = src_menu
        )
    return  items
  #end _CreateDataSetGroup_


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetCreatorBean._CreateMethodGroup()         -
  #----------------------------------------------------------------------
  def _CreateMethodGroup( self ):
    """
    Returns:
        dict: dict of controls created with keys
            ``factors_checkbox``, ``group_panel``, ``method_choice``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = \
        wx.StaticBox( group_panel, -1, "3. Select Derivation Method" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    outer_panel = wx.Panel( group_box, -1, style = wx.BORDER_NONE )
    outer_sizer = wx.BoxSizer( wx.HORIZONTAL )
    outer_panel.SetSizer( outer_sizer )

    method_sizer = wx.BoxSizer( wx.HORIZONTAL )
    #preset_panel.SetSizer( preset_sizer )
    method_label = wx.StaticText(
        outer_panel, -1, label = 'Method:',
        style = wx.ALIGN_RIGHT
        )
    #methods = [ 'Average', 'Max', 'Axial Offset' ]
    methods = [ x[ 0 ] for x in DERIVATION_METHODS ]
    method_choice = wx.Choice( outer_panel, -1, choices = methods  )
    method_choice.SetSelection( 0 )
    method_sizer.AddMany([
        ( method_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 8 ),
        ( method_choice, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT, 0 )
        ])

    right_panel = wx.Panel( outer_panel, -1, style = wx.BORDER_NONE )
    right_sizer = wx.BoxSizer( wx.VERTICAL )
    right_panel.SetSizer( right_sizer )

#    factors_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    factors_label = wx.StaticText(
#        right_panel, -1,
#	label = 'Use Factors:',
#	style = wx.ALIGN_LEFT
#	)
    factors_checkbox = wx.CheckBox( right_panel, -1, 'Use Factors' )
    factors_checkbox.SetValue( True )
#    factors_sizer.AddMany([
#        ( factors_label, 0,
#          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT, 8 ),
#        ( factors_checkbox, 0,
#          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT, 0 )
#        ])

#    right_sizer.Add( factors_sizer, 0, wx.ALIGN_RIGHT | wx.BOTTOM, 6 )
    right_sizer.Add(
        factors_checkbox, 0,
        wx.ALIGN_RIGHT | wx.LEFT, 10
        )
    right_sizer.AddStretchSpacer()

    outer_sizer.AddMany([
        ( method_sizer, 1,
          wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6 ),
        ( right_panel, 0,
          wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6 )
        ])
    outer_sizer.AddStretchSpacer()

#               -- Layout
#               --
    group_sizer.Add(
        outer_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict(
        factors_checkbox = factors_checkbox,
        method_choice = method_choice,
        group_panel = group_panel
        )
    return  items
  #end _CreateMethodGroup


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetCreatorBean._CreateNewDataSetGroup()     -
  #----------------------------------------------------------------------
  def _CreateNewDataSetGroup( self, show_create_button ):
    """
    Returns:
        dict: dict of controls created with keys
            ``group_panel``, ``new_field`` and optionally ``create_button``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = wx.StaticBox( group_panel, -1, "4. Enter New Dataset Name" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    names_panel = wx.Panel( group_box, -1 )
    names_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    names_panel.SetSizer( names_sizer )

#               -- New line
#               --
    new_label = wx.StaticText(
        names_panel, -1,
	label = 'New Dataset:',
	style = wx.ALIGN_LEFT
	)
    new_field = \
        wx.TextCtrl( names_panel, -1, 'unnamed', size = NAME_FIELD_SIZE )
    names_sizer.AddMany([
        ( new_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( new_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND, 0 )
        ])

    if show_create_button:
#		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
      create_button = \
          wx.Button( names_panel, -1, label = 'C&reate Derived Dataset' )
      create_button.SetToolTipString( 'Create/calculate a dataset' )
      create_button.Bind( wx.EVT_BUTTON, self._OnCreate )
      create_button.Enable( False )
      names_sizer.Add( create_button, 0, wx.EXPAND, 0 )

#               -- Layout
#               --
    #group_sizer.Add( names_panel, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 0 )
    group_sizer.Add(
        names_panel, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 6
        )
    group_panel.SetSizer( group_sizer )
    group_panel.Fit()

    items = dict( group_panel = group_panel, new_field = new_field )
    if show_create_button:
      items[ 'create_button' ] = create_button
    return  items
  #end _CreateNewDataSetGroup


  #----------------------------------------------------------------------
  #	METHOD:	        DataSetCreatorBean._CreateSelectDataSetGroup()  -
  #----------------------------------------------------------------------
  def _CreateSelectDataSetGroup( self ):
    """
    Returns:
        dict: dict of controls created with keys
            ``group_panel``, ``src_button``, ``src_field``, ``src_menu``
"""
    group_panel = wx.Panel( self, -1 )
    #group_sizer = wx.StaticBoxSizer( wx.VERTICAL, self, "Dataset Selection" )
    group_box = wx.StaticBox( group_panel, -1, "1. Select Dataset" )
    group_sizer = wx.StaticBoxSizer( group_box, wx.VERTICAL )

    names_panel = wx.Panel( group_box, -1 )
    names_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    names_panel.SetSizer( names_sizer )

#               -- Source line
#               --
    src_label = wx.StaticText(
        names_panel, -1,
        label = 'Source Dataset:',
	style = wx.ALIGN_RIGHT
        )
    src_field = wx.TextCtrl( names_panel, -1, '', size = NAME_FIELD_SIZE )
    src_field.SetEditable( False )
    src_button = wx.Button( names_panel, -1, label = 'Select...' )

    ds_types = [
        v.get( 'type' )
        for v in six.itervalues( DATASET_DEFS )
        if v.get( 'axis_names' ) and
            v.get( 'copy_shape_expr', v.get( 'shape_expr' ) ).count( ',' ) == 3
        ]
    src_menu = DataSetsMenu(
        self._state, binder = self, mode = 'subsingle',
	ds_types = ds_types,
	widget = DataSetCreatorMenuWidget( src_field, self._OnNameUpdate )
        )
    src_button.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnShowMenu, src_button, src_menu )
	)

    names_sizer.AddMany([
        ( src_label, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0 ),
        ( src_field, 1,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0 ),
        ( src_button, 0,
          wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.RIGHT, 10 )
        ])

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
        group_panel = group_panel,
        src_button = src_button,
        src_field = src_field,
        src_menu = src_menu
        )
    return  items
  #end _CreateSelectDataSetGroup


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.DoCreate()			-
  #----------------------------------------------------------------------
  def DoCreate( self, do_toast = True, after_callback = None ):
    """Must be called on MainThread.
"""
    dm = None
    src_qds_name = DataSetName( self._sourceNameField.GetValue() )
    result_ds_name = self._newNameField.GetValue().replace( ' ', '_' )

    msg = ''
    if len( src_qds_name.displayName ) == 0:
      msg = 'Please select a source dataset'
    elif len( result_ds_name ) == 0:
      msg = 'Please enter a result dataset name'

    else:
      dm = self._state.dataModelMgr.GetDataModel( src_qds_name )
      if dm is None:
        msg = 'Dataset read error'

      elif dm.GetDataSetType( result_ds_name ):
        msg = 'A dataset named "{0}" already exists'.format( result_ds_name )

      else:
        #self._statusField.SetValue( 'Creating ' + result_ds_name + '...' )
        #self._statusField.Update()

        derive_axis_names = [
            self._axisNames[ i ]
            for i in range( len( self._axisCheckBoxes ) )
            if self._axisCheckBoxes[ i ].GetValue()
            ]
        if len( derive_axis_names ) == 0:
          msg = 'Please select one or more dataset axes'

    if msg:
      wx.MessageDialog( self, msg, 'Derive Dataset' ).ShowWindowModal()
    else:
      avg_axis = set()
      for axis_pair in derive_axis_names:
        if hasattr( axis_pair[ 0 ], '__iter__' ):
          avg_axis |= set( axis_pair[ 0 ] )
        else:
          avg_axis.add( axis_pair[ 0 ] )
      avg_axis = tuple( sorted( avg_axis ) )

      if self._createButton:
        self._createButton.Disable()
      self._progressGauge.SetRange( dm.GetStatesCount() )

      der_method = 'avg'
      der_method_ndx = max( self._methodChoice.GetSelection(), 0 )
      der_method = DERIVATION_METHODS[ der_method_ndx ][ 1 ]

      creator = DataSetCreatorTask(
          dm, src_qds_name.displayName,
          avg_axis, result_ds_name,
          der_method = der_method,
          use_factors = self._factorsCheckBox.GetValue(),
          progress_callback = self._OnProgress,
          finished_callback = lambda x: \
            wx.CallAfter( self._OnCreateFinished, x, do_toast, after_callback )
	  )
      wx.CallAfter( creator.Run )
    #end if-else
  #end DoCreate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    """
"""
    super( DataSetCreatorBean, self ).Enable( flag )

    if self._createButton:
      self._createButton.Enable( flag and self._axisNames )

    for cb in self._axisCheckBoxes:
      cb.Enable( flag )

    self._presetChoice.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.InferPresets()               -
  #----------------------------------------------------------------------
  def InferPresets( self ):
    """
"""
    #core = self.state.dataModelMgr.GetCore()
    presets = [ '(custom)' ]

    if self._axisNames:
      axis_names = set( map( lambda x: x[ 1 ], self._axisNames ) )

      for preset_name, axis_list in six.iteritems( AXIS_PRESET_DEFS ):
        matched = True
        for axis in axis_list:
          matched &= axis in axis_names

        #if matched:
        if matched and len( axis_list ) < len( self._axisNames ):
          presets.append( preset_name )
      #end for name, sets in six.iteritems( AXIS_PRESET_DEFS )
    #end if self._axisNames

    return  sorted( presets )
  #end InferPresets


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, show_create_button = True ):
    """
"""
    ds_items = self._CreateSelectDataSetGroup()
    self._sourceDataSetMenu = ds_items.get( 'src_menu' )
    self._sourceMenuButton = ds_items.get( 'src_button' )
    self._sourceNameField = ds_items.get( 'src_field' )

    axis_items = self._CreateAxisGroup()
    self._axisPanel = axis_items.get( 'axis_panel' )
    self._presetChoice = axis_items.get( 'preset_choice' )

    method_items = self._CreateMethodGroup()
    self._factorsCheckBox = method_items.get( 'factors_checkbox' )
    self._methodChoice = method_items.get( 'method_choice' )

    new_items = self._CreateNewDataSetGroup( show_create_button )
    self._createButton = new_items.get( 'create_button' )
    self._newNameField = new_items.get( 'new_field' )

    self._progressGauge = wx.Gauge( self, -1, style = wx.GA_HORIZONTAL )

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetAutoLayout( True )
    self.SetSizer( sizer )

    sizer.AddMany((
        ( ds_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( axis_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( method_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( new_items.get( 'group_panel' ), 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 ),
        ( self._progressGauge, 0,
          wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 )
        ))
    sizer.AddStretchSpacer()
    #sizer.Layout()

    self.Fit()
    self._sourceDataSetMenu.Init()
    self._UpdateAxisPanel()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnCreate()			-
  #----------------------------------------------------------------------
  def _OnCreate( self, ev ):
    """Must be called on MainThread.  Calls ``DoCreate()``.
"""
    if ev:
      ev.Skip()
    self.DoCreate()
  #end _OnCreate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnCreateFinished()          -
  #----------------------------------------------------------------------
  def _OnCreateFinished( self, ds_name, do_toast = True, callback = None ):
    """
"""
    if self._createButton:
      self._createButton.Enable()
    self._sourceDataSetMenu.UpdateAllMenus()
    self._progressGauge.SetValue( 0 )

    if callback:
      if hasattr( callback, '__call__' ):
        callback()
    elif do_toast:
      self.ToastMessage( 'Dataset "' + ds_name + '" was created' )
  #end _OnCreateFinished


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnNameUpdate()		-
  #----------------------------------------------------------------------
  def _OnNameUpdate( self, *args, **kwargs ):
    """
"""
    src_qds_name = DataSetName( self._sourceNameField.GetValue() )
    result_ds_name = self._newNameField.GetValue()

    if src_qds_name: # and src_qds_name.displayName == result_ds_name:
      self._newNameField.SetValue( 'derived_' + result_ds_name )

    ds_def = None
    if src_qds_name:
      ds_def = self._state.dataModelMgr.GetDataSetDefByQName( src_qds_name )
    self._dataSetDef = ds_def

    if ds_def:
      if self._createButton:
        self._createButton.Enable( True )
      self._axisNames = ds_def.get( 'axis_names', () )
      self._shape = ds_def.get( 'copy_shape', ds_def.get( 'shape' ) )
    else:
      if self._createButton:
        self._createButton.Enable( False )
      self._axisNames = \
      self._shape = None
    self._UpdateAxisPanel()
  #end _OnNameUpdate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnPreset()                  -
  #----------------------------------------------------------------------
  def _OnPreset( self, ev ):
    """
"""
    ev.Skip()
    choice = ev.GetEventObject()

    sel_ndx = choice.GetSelection()
    #if sel_ndx >= 0:
    if sel_ndx > 0:
      preset = choice.GetString( sel_ndx )
      self.ApplyPreset( preset )
  #end _OnPreset


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnProgress()                -
  #----------------------------------------------------------------------
  def _OnProgress( self, state_ndx ):
    """
"""
    wx.CallAfter( self._progressGauge.SetValue, state_ndx )
  #end _OnProgress


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnShowMenu()		-
  #----------------------------------------------------------------------
  def _OnShowMenu( self, button, menu, ev ):
    """
"""
    ev.Skip()
    button.PopupMenu( menu )
  #end _OnShowMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.ToastMessage()               -
  #----------------------------------------------------------------------
  def ToastMessage( self, msg ):
    """
"""
    font = self._methodChoice.GetFont()
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
  #	METHOD:		DataSetCreatorBean._UpdateAxisPanel()           -
  #----------------------------------------------------------------------
  def _UpdateAxisPanel( self ):
    """
"""
#               -- Axis panel
#               --
    del self._axisCheckBoxes[ : ]

    self._axisPanel.DestroyChildren()
    ncols = len( self._axisNames )  if self._axisNames else  1
    sizer = wx.FlexGridSizer( cols = ncols, rows = 3, vgap = 6, hgap = 8 )
    for i in range( ncols ):
      sizer.AddGrowableCol( i, 1 )
    self._axisPanel.SetSizer( sizer )

    if self._axisNames:
#                       -- First row is axis names
      for ndx, name in self._axisNames:
        sizer.Add(
            wx.StaticText(
                self._axisPanel, -1,
                name.capitalize(), style = wx.ALIGN_CENTER
                ),
            1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, wx.EXPAND, 0
            )

#                       -- Second row is axis dimensions
      for ndx, name in self._axisNames:
        if hasattr( ndx, '__iter__' ):
          addr = [ str( self._shape[ i ] ) for i in ndx ]
          size_str = ','.join( addr )
        else:
          size_str = str( self._shape[ ndx ] )

        size_label = wx.StaticText(
            self._axisPanel, -1, size_str,
            style = wx.ALIGN_CENTER
            )
        sizer.Add(
            size_label, 1,
            wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, wx.EXPAND, 0
            )
      #end for ndx, name in self._axisNames

#                       -- Third row is checkboxes
      for i in range( len( self._axisNames ) ):
        cb = wx.CheckBox( self._axisPanel, -1, '', style = wx.ALIGN_RIGHT )
        self._axisCheckBoxes.append( cb )
        sizer.Add(
            cb, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP | wx.LEFT,
            cb.GetFont().GetPixelSize()[ 0 ] >> 1
            )
      #end for i in range( len( self._axisNames ) )

      self._presetChoice.SetItems( self.InferPresets() )

    else:
      label = wx.StaticText(
          self._axisPanel, -1,
          label = 'Select a dataset', style = wx.ALIGN_CENTER
          )
      sizer.Add(
          label, 0,
          wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_TOP | wx.BOTTOM | wx.TOP, 8
          )
      sizer.Add( wx.StaticText( self._axisPanel, -1, '' ), 0, 0, 0 )

      self._presetChoice.SetItems( [] )
    #end else not self._axisNames

#               -- Layout
#               --
    #self.Layout()
    self._axisPanel.Layout()
    top_win = self.GetParent()
    while not( top_win is None or isinstance( top_win, wx.TopLevelWindow ) ):
      top_win = top_win.GetParent()
    if top_win is None:
      self.Layout()
    else:
      top_win.Layout()
  #end _UpdateAxisPanel


#		-- Properties
#		--

  axisCheckBoxes = property( lambda x : x._axisCheckBoxes )

  axisPanel = property( lambda x : x._axisPanel )

  createButton = property( lambda x : x._createButton )

  factorsCheckBox = property( lambda x : x._factorsCheckBox )

  factorsField = property( lambda x : x._factorsField )

  methodChoice = property( lambda x : x._methodChoice )

  newNameField = property( lambda x : x._newNameField )

  presetChoice = property( lambda x : x._presetChoice )

  progressGauge = property( lambda x : x._progressGauge )

  sourceDataSetMenu = property( lambda x : x._sourceDataSetMenu )

  sourceMenuButton = property( lambda x : x._sourceMenuButton )

  sourceNameField = property( lambda x : x._sourceNameField )

  state = property( lambda x : x._state )

#end DataSetCreatorBean


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorDialog				-
#------------------------------------------------------------------------
class DataSetCreatorDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetCreatorBean reference
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, **kwargs ):
    """
Must pass the 'state' parameter.
"""

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetCreatorDialog, self ).__init__( parent, -1, **kwargs )

    self._bean = None
    self._InitUI( state )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog.GetApp()                   -
  #----------------------------------------------------------------------
  def GetApp( self ):
    """Not sure why this is necessary, but ``wx.App.Get()`` called in
DataModelMenu returns a ``wx.App`` instance, not a ``VeraViewApp`` instance.
"""
    return  wx.App.Get()
  #end GetApp


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, state ):
    #self.fBean = DataSetCreatorBean( self, data_model, ds_name, -1 )
    self._bean = DataSetCreatorBean( self, state, show_create_button = False )

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
    self.SetTitle( 'Create Derived Datasets' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

    button = ev.GetEventObject()
    button_id = ev.GetEventObject().GetId()

#    if button_id == ID_CREATE or button_id == ID_CREATE_CLOSE:
#      self._bean.DoCreate( button_id == ID_CREATE )
#
#    if button_id == wx.ID_CLOSE or button_id == ID_CREATE_CLOSE:
#      self.EndModal( button_id )

    if button_id == ID_CREATE:
      self._bean.DoCreate()
    elif button_id == ID_CREATE_CLOSE:
      self._bean.DoCreate( False, lambda : self.EndModal( button_id ) )
    else:
      self.EndModal( button_id )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog._OnCharHook()              -
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
  #	METHOD:		DataSetCreatorDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    return  super( DataSetCreatorDialog, self ).ShowModal()
  #end ShowModal


#		-- Properties
#		--

  bean = property( lambda x : x._bean )

#end DataSetCreatorDialog


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorMenuWidget                        -
#------------------------------------------------------------------------
class DataSetCreatorMenuWidget( BaseDataModelMenuWidget ):
  """Dummy DataSetModelMenu widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorMenuWidget.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, field, callback = None ):
    self._callback = \
        callback  if callback and hasattr( callback, '__call__' ) else  None
    self._field = field
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorMenuWidget.SetDataSet()		-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    if self._field is not None:
      self._field.SetValue( str( qds_name ) if qds_name else '' )

      if self._callback:
        self._callback()
  #end SetDataSet

#end DataSetCreatorMenuWidget


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorTask                              -
#------------------------------------------------------------------------
class DataSetCreatorTask( object ):
  """Task manager.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorTask.__init__()			-
  #----------------------------------------------------------------------
  def __init__(
      self, data_model, src_ds_name, avg_axis, result_ds_name,
      der_method = 'avg',
      use_factors = True,
      progress_callback = None,
      finished_callback = None
      ):
    """Starts average calculation for each state point in data_model
    Args:
        data_model (DataModel): DataModel instance
        src_ds_name (str): source dataset name
        avg_axis (tuple): average axes
        result_ds_name (str): result dataset name
        der_method (str): derivation function ('avg', 'rms', 'stddev')
        use_factors (bool): True to apply factors
        progress_callback (callable): optional, called with each statepoint,
            prototype func( state_ndx )
        finished_callback (callable): optional, called when the derivation is
            complete with the result ds_name passed as a parameter
"""
    self._dataModel = data_model
    self._srcDsName = src_ds_name
    self._resultDsName = result_ds_name
    self._avgAxis = avg_axis
    self._derMethod = der_method
    self._useFactors = use_factors
    self._progressCallback = progress_callback
    self._finishedCallback = finished_callback

    #self._dialog = None

    self.logger = logging.getLogger( 'widget_bean' )

    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info(
          'data_model=%s, src_ds_name=%s, result_ds_name=%s, avg_axis=%s',
          data_model.name, src_ds_name, result_ds_name, str( avg_axis )
	  )
  #end __init__


#  #----------------------------------------------------------------------
#  #	METHOD:		DataSetCreatorTask.DoUpdate()                   -
#  #----------------------------------------------------------------------
#  def DoUpdate( self, state_ndx ):
#    """
#"""
#    wx.CallAfter(
#        self._dialog.Update, state_ndx,
#        'Calculating for statepoint {0:3d}/{1:d}'.
#            format( state_ndx, len( self._dataModel.GetStates() ) )
#        )
#  #end DoUpdate


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorTask.Run()                        -
  #----------------------------------------------------------------------
  def Run( self ):
    """Launches averages calculation for each state point.
Must be called in the UI thread.
"""
#    self._dialog = wx.ProgressDialog(
#        'Calculating Derived Dataset', 'Initializing...',
#	len( self._dataModel.GetStates() )
#	)
#    self._dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBegin,
	wargs = []
	#wargs = [ self._dialog ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorTask._RunBegin()			-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog = None ):
    """
"""
    status = { 'dialog': dialog }

    try:
      self._dataModel.CreateDerivedDataSet2(
          self._srcDsName, self._avgAxis,
          self._resultDsName,
          der_method = self._derMethod,
          use_factors = self._useFactors,
          callback = self._progressCallback
          )

    except Exception, ex:
      status[ 'messages' ] = \
          [ 'Error calculating average dataset:' + os.linesep + str( ex ) ]

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorTask._RunEnd()			-
  #----------------------------------------------------------------------
  def _RunEnd( self, result ):
    """Called in the UI thread.
"""
    status = result.get()
    if status is not None:
      dialog = status.get( 'dialog' )
      if dialog is not None:
        dialog.Destroy()

      messages = status.get( 'messages' )
      if messages is not None and len( messages ) > 0:
        msg = \
	    'Averages not calculated:' + os.linesep + \
	    os.linesep.join( messages )
        wx.MessageBox( msg, 'Calculating Averages', wx.ICON_ERROR | wx.OK_DEFAULT )
        #wx.MessageDialog( self, msg, 'Calculating Averages' ).ShowWindowModal()
      #end if
    #end if

    if self._finishedCallback:
      self._finishedCallback( self._resultDsName )
  #end _RunEnd

#end DataSetCreatorTask
