#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr_tree.py				-
#	HISTORY:							-
#		2018-11-19	leerw@ornl.gov				-
#		2018-11-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, logging, os, six, sys
import StringIO, traceback
import pdb

try:
  import wx
  #x import wx.dataview as dv
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.config import Config
from data.datamodel import *
from data.datamodel_mgr import *
from event.state import *


NDX_unselected = 2
NDX_selected = 3


#------------------------------------------------------------------------
#	CLASS:		DataModelMgrTree                                -
#------------------------------------------------------------------------
class DataModelMgrTree( wx.TreeCtrl ):
  """Tree for representing all the datasets in all open DataModels.
These are intended to be built on demand but can be updated explicitly
via SetSelections().
"""

  #logger_ = logging.getLogger( 'widgetBean' )
  logger_ = logging.getLogger( 'widget_bean' )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, **kwargs ):
    """Initializes.
    Args:
        parent (wx.Window): parent window
        state (event.State): State instance
        kwargs (dict):
            ds_types (list): list of defined allowed types,
                where None means all types in the data model
#            ds_visible_func (callable): func with single parameter
#                qds_name (DataSetName) returning True if the dataset is
#                currently visible
            selections (set): optional set of DataSetName instances to make
                initially selected
            show_core_datasets (bool): True to show a core submenu
            show_selected_dataset (bool): True to add top level
                'Selected Dataset' item
            widget (widget.Widget): optional widget
"""
    self.logger = DataModelMgrTree.logger_
    self.selectedDataSetItem = None
    self.state = state

#    self.dataSetVisibleFunc = None
#    if 'ds_visible_func' in kwargs:
#      func = kwargs.get( 'ds_visible_func' )
#      del kwargs[ 'ds_visible_func' ]
#      if hasattr( func, '__call__'):
#        self.dataSetVisibleFunc = func

    self.dataSetTypesIn = None
    if 'ds_types' in kwargs:
      self.dataSetTypesIn = kwargs.get( 'ds_types' )
      del kwargs[ 'ds_types' ]

    self._selections = set()
    if 'selections' in kwargs:
      value = kwargs.get( 'selections' )
      del kwargs[ 'selections' ]
      if isinstance( value, set ):
        self._selections = value

#    self.showCoreDataSets = False
    if 'show_core_datasets' in kwargs:
#      self.showCoreDataSets = kwargs.get( 'show_core_datasets', False )
      del kwargs[ 'show_core_datasets' ]

    self.showSelectedDataSet = False
    if 'show_selected_dataset' in kwargs:
      self.showSelectedDataSet = kwargs.get( 'show_selected_dataset', False )
      del kwargs[ 'show_selected_dataset' ]

    self.widget = None
    if 'widget' in kwargs:
      self.widget = kwargs.get( 'widget' )
      del kwargs[ 'widget' ]

    style = kwargs.get( 'style', 0 )
    #style |= wx.TR_HIDE_ROOT | wx.TR_MULTIPLE | wx.TR_TWIST_BUTTONS
    #style |= wx.TR_HAS_BUTTONS | wx.TR_MULTIPLE | wx.TR_TWIST_BUTTONS
    style |= wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_TWIST_BUTTONS
    kwargs[ 'style' ] = style

    super( DataModelMgrTree, self ).__init__( parent, **kwargs )
    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._CreateDataSetItem()           -
  #----------------------------------------------------------------------
  def _CreateDataSetItem( self, parent, dmodel, qds_name ):
    """
    Args:
        parent (wx.TreeItem): tree item to which to append
        dmodel (data.datamodel.DataModel): DataModel instance
        qds_name (DataSetName): dataset name
    Returns:
        wx.TreeItem: new item
"""
    display_name = dmodel.GetDataSetTypeDisplayName( qds_name.displayName )
#    item_state = \
#        NDX_unselected  if self.dataSetVisibleFunc is None else \
#        NDX_selected  if self.dataSetVisibleFunc( qds_name ) else \
#        NDX_unselected
    item_state = \
        NDX_selected  if qds_name in self._selections else \
        NDX_unselected

    ds_item = self.AppendItem( parent, display_name )
    self.SetItemPyData( ds_item, qds_name )
    self.SetItemState( ds_item, item_state )
    return  ds_item
  #end _CreateDataSetItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._CreateDataSetTypeItems()      -
  #----------------------------------------------------------------------
  def _CreateDataSetTypeItems( self, parent, dmodel, ds_names ):
    """
    Args:
        parent (wx.TreeItem): tree item to which to append
        dmodel (data.datamodel.DataModel): DataModel instance
        ds_names (list(str)): list of dataset names
"""
    for ds_name in ds_names:
      qds_name = DataSetName( dmodel.name, ds_name )
      self._CreateDataSetItem( parent, dmodel, qds_name )
  #end _CreateDataSetTypeItems


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._CreateModelItems()		       -
  #----------------------------------------------------------------------
  def _CreateModelItems( self, model_item, dmodel ):
    """
    Args:
        model_item (wx.TreeItem): item to which to append items
        dmodel (data.datamodel.DataModel): DataModel instance
"""
    dmgr = self.state.dataModelMgr

#               -- Get list of relevant types
#               --
    ds_types = []
    types_in = \
        self.dataSetTypesIn  if self.dataSetTypesIn else \
        dmodel.GetDataSetNames().keys()
    for k in sorted( types_in ):
      #if k not in [ 'axials', 'core' ]:
      if k not in ( 'axials', ):
        ds_types.append( k )

#    core_ds_names = dmodel.GetDataSetNames( 'core' )
#    if core_ds_names and self.showCoreDataSets:
#      type_item = self.AppendItem( model_item, 'core' )
#      self.SetItemPyData( type_item, 'core' )
#      self.SetItemState( type_item, wx.TREE_ITEMSTATE_NONE )
#      self._CreateDataSetTypeItems( type_item, dmodel, core_ds_names )

    for dtype in ds_types:
#      ds_names = [
#          d for d in dmodel.GetDataSetNames( dtype )
#          if d not in core_ds_names
#          ]
      ds_names = sorted( dmodel.GetDataSetNames( dtype ) )
      if ds_names:
        type_name = dmodel.GetDataSetTypeDisplayName( dtype )
#        type_item = self.AppendItem( model_item, dtype, 0, 1 )
        type_item = self.AppendItem( model_item, type_name )
        self.SetItemPyData( type_item, dtype )
        self.SetItemState( type_item, wx.TREE_ITEMSTATE_NONE )
        self._CreateDataSetTypeItems( type_item, dmodel, ds_names )
    #end for dtype in ds_types
  #end _CreateModelItems


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._FindItem()			-
  #----------------------------------------------------------------------
  def _FindItem( self, qds_name, ds_type = None, tree_item = None ):
    """Finds the wx.TreeItem.
@param  qds_name	DataSetName instance
@return			item or None if not found
"""
    match_item = None
    if tree_item is None:
      tree_item = self.GetRootItem()

    if not ds_type:
      ds_type = self.state.dataModelMgr.GetDataSetType( qds_name )

    cur_item, cookie = self.GetFirstChild( tree_item )
    while match_item is None and cur_item.IsOk():
      item_data = self.GetItemPyData( cur_item )

      if isinstance( item_data, DataSetName ):
        match_item = item_data == qds_name

      #elif item_data.startswith( 'model:' ):
        #if item_data[ 6 : ] == qds_name.modelName:
      elif isinstance( item_data, DataModel ):
        if item_data.name == qds_name.modelName:
          match_item = self._FindItem( qds_name, ds_type, cur_item )

      #elif item_data.startswith( 'type:' ):
        #if item_data[ 5 : ] == ds_type:
      elif isinstance( item_data, str ):
        if item_data == ds_type:
          match_item = self._FindItem( qds_name, ds_type, cur_item )

      else:
        match_item = self._FindItem( qds_name, ds_type, cur_item )

      if match_item is None:
        cur_item, cookie = self.GetNextChild( tree_item, cookie )
    #end while match_item is None and cur_item.IsOk()

    return  match_item
  #end _FindItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree.GetSelections()		-
  #----------------------------------------------------------------------
  def GetSelections( self ):
    """
    Returns:
        set: set of DataSetName instances
"""
    return  self._selections
  #end GetSelections


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._InitUI()		        -
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    dmgr = self.state.dataModelMgr

    image_list = wx.ImageList( 16, 16, initialCount = 4 )
    for n in ( 'unselected', 'selected', 'unselected', 'selected' ):
      name = 'item_{0}_16x16.png'.format( n )
      im = wx.Image( os.path.join( Config.GetResDir(), name ) )
      image_list.Add( im.ConvertToBitmap() )
    self.AssignStateImageList( image_list )

    root_item = self.AddRoot( 'Datasets' )
    #r root_item = self.AddRoot( 'Files' )
    self.SetItemState( root_item, wx.TREE_ITEMSTATE_NONE )

    if self.showSelectedDataSet:
      item = self.AppendItem( root_item, LABEL_selectedDataSet, 0, 1 )
      self.SetItemPyData( item, NAME_selectedDataSet )
      self.selectedDataSetItem = item

#                       -- Each model
#                       --
    if dmgr.GetDataModelCount() == 1:
      dmodel = dmgr.GetFirstDataModel()
      model_item = self.AppendItem( root_item, 'Dataset Types' )
      self.SetItemPyData( model_item, dmodel )
      #r self.SetItemText( root_item, 'Types' )
      self._CreateModelItems( model_item, dmodel )
      self.Expand( model_item )

    elif dmgr.GetDataModelCount() > 1:
      for name in dmgr.GetDataModelNames():
        dmodel = dmgr.GetDataModel( name )
#        model_item = self.AppendItem( root_item, name, 0, 1 )
        model_item = self.AppendItem( root_item, name )
        self.SetItemPyData( model_item, dmodel )
        self._CreateModelItems( model_item, dmodel )

    #self.Bind( wx.EVT_TREE_SEL_CHANGED, self._OnSelectionChanged )
    self.Bind( wx.EVT_TREE_KEY_DOWN, self._OnKeyDown )
    self.Bind( wx.EVT_TREE_STATE_IMAGE_CLICK, self._OnItemClick )
    #r self.Expand( root_item )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._OnItemClick()		        -
  #----------------------------------------------------------------------
  def _OnItemClick( self, ev ):
    """
"""
    ev.Skip()
    self._ToggleItem( ev.GetItem() )
  #end _OnItemClick


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._OnKeyDown()		        -
  #----------------------------------------------------------------------
  def _OnKeyDown( self, ev ):
    """
"""
    ev.Skip()
    if ev.GetKeyCode() == 32:
      item = self.GetSelection()
      if item.IsOk():
        self._ToggleItem( item )
  #end _OnKeyDown


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._OnSelectionChanged()		-
  #----------------------------------------------------------------------
##  def _OnSelectionChanged( self, ev ):
##    """
##"""
##    item = ev.GetItem()
##    item_data = self.GetItemPyData( item )
##
##    if isinstance( item_data, DataSetName ) and self.IsSelected( item ):
##      if item_data in self._selections:
##        self._selections.remove( item_data )
##        self.SetItemState( item, NDX_unselected )
##      else:
##        self._selections.add( item_data )
##        self.SetItemState( item, NDX_selected )
##  #end _OnSelectionChanged


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree.SetSelections()		-
  #----------------------------------------------------------------------
  def SetSelections( self, selections ):
    """
    Args:
        selections(set(DataSetName)): new selections
"""
    self._selections.clear()
    self._selections |= selections
    self._UpdateSelections( self.GetRootItem() )
  #end SetSelections


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._ToggleItem()		        -
  #----------------------------------------------------------------------
  def _ToggleItem( self, item ):
    """
"""
    item_data = self.GetItemPyData( item )

    if isinstance( item_data, DataSetName ):
      if self.GetItemState( item ) > 2:
        self.SetItemState( item, NDX_unselected )
        if item_data in self._selections:
          self._selections.remove( item_data )
      else:
        self.SetItemState( item, NDX_selected )
        self._selections.add( item_data )
  #end _ToggleItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTree._UpdateSelections()		-
  #----------------------------------------------------------------------
  def _UpdateSelections( self, item ):
    """
"""
    if item is not None and item.IsOk():
      item_data = self.GetItemPyData( item )

      if isinstance( item_data, DataSetName ):
        self.SetItemState(
            item,
            NDX_selected if item_data in self._selections else NDX_unselected
            )
      else:
        ds_item, cookie = self.GetFirstChild( item )
        while ds_item.IsOk():
          self._UpdateSelections( ds_item )
          ds_item, cookie = self.GetNextChild( item, cookie )
  #end _UpdateSelections


#               -- Property Definitions
#               --

  selections = property( GetSelections, SetSelections )

#end DataModelMgrTree


#------------------------------------------------------------------------
#	CLASS:		DataModelMgrTreeDialog				-
#------------------------------------------------------------------------
class DataModelMgrTreeDialog( wx.Dialog ):
  """
Properties:
  bean			DataModelMgrTree reference
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog.__init__()               -
  #----------------------------------------------------------------------
  def __init__( self, parent, state, **kwargs ):
    """
"""
    tree_kwargs = {}
    for name in (
        'ds_types', 'selections', 'show_core_datasets',
        'show_selected_dataset', 'widget'
        ):
      if name in kwargs:
        tree_kwargs[ name ] = kwargs[ name ]
        del kwargs[ name ]

    super( DataModelMgrTreeDialog, self ).__init__( parent, -1, **kwargs )

    self._tree = None
    self._InitUI( state, tree_kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog.GetSelections()          -
  #----------------------------------------------------------------------
  def GetSelections( self ):
    return  self._tree.selections
  #end GetSelections


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog.GetTree()                -
  #----------------------------------------------------------------------
  def GetTree( self ):
    return  self._tree
  #end GetTree


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog._InitUI()                -
  #----------------------------------------------------------------------
  def _InitUI( self, state, tree_kwargs ):
    tree_kwargs[ 'size' ] = ( 400, 400 )
    self._tree = DataModelMgrTree( self, state, **tree_kwargs )

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
	self._tree, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetAutoLayout( True )
    self.SetSizer( sizer )
    self.SetTitle( 'Set Visible Datasets' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog._OnButton()              -
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = wx.ID_CANCEL if obj.GetLabel() == 'Cancel' else  wx.ID_OK

    #if obj.GetLabel() != 'Cancel':
      #self.fResult = self.fBean.GetRange()

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrTreeDialog._OnCharHook()            -
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
  #	METHOD:		DataModelMgrTreeDialog.ShowModal()              -
  #----------------------------------------------------------------------
  def ShowModal( self, selections = None ):
    if selections is not None:
      self._tree.selections = selections
    return  super( DataModelMgrTreeDialog, self ).ShowModal()
  #end ShowModal


#		-- Property Definitions
#		--

  selections = property( GetSelections )

  tree = property( GetTree )

#end DataModelMgrTreeDialog
