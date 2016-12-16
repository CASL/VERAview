#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_menu.py					-
#	HISTORY:							-
#		2016-12-14	leerw@ornl.gov				-
#	  Added DataModelMenu.showSelectedItem attribute and fixed
#	  LABEL_selectedDataSet item placement, adding
#	  _AddSelectedDataSetItem().
#	  Fixed DataModelMenu._OnDataSetMenuItem() to properly handle
#	  LABEL_selectedDataSet items.
#		2016-12-09	leerw@ornl.gov				-
#	  Fixed event handling.
#		2016-12-07	leerw@ornl.gov				-
#	  Modified _CheckSingleItem() to find the top DataSetsMenu
#	  if the menu param is None.
#	  Modified UpdateMenu() to keep track of any checked item if
#	  isSingleSelection and call _CheckSingleItem( None, ... ).
#	  Working version with DataSetMenuITest.
#		2016-12-02	leerw@ornl.gov				-
#	  Trying per-DataModel menus.
#		2016-12-01	leerw@ornl.gov				-
#	  Moving to DataModelMgr.
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-08-24	leerw@ornl.gov				-
#		2016-08-23	leerw@ornl.gov				-
#	  Refinements and bug fixes.
#		2016-08-22	leerw@ornl.gov				-
#	  Reworking for reuse in all and components.
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-07-21	leerw@ornl.gov				-
#		2016-07-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, os, sys
import pdb  #pdb.set_trace()

try:
  import wx
  #import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *
from event.state import *


#------------------------------------------------------------------------
#	CLASS:		DataModelMenu					-
#------------------------------------------------------------------------
class DataModelMenu( wx.Menu ):
  """Menu for managing datasets for a single DataModel instance.
No event listening is done in this class.
"""

  logger_ = logging.getLogger( 'widgetBean' )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self,
      state, binder,
      data_model = None, mode = '',
      ds_listener = None, ds_types = None,
      show_derived_menu = True,
      widget = None
      ):
    """Initializes with an empty menu.
@param  state		State object, required
@param  binder		object from window containing this on which to call
			Bind() for menu events, cannot be None
@param  data_model	DataModel instance
@param  mode		mode value: ('selected' implies 'multi')
    ''			- single selection, flat menu (default)
    'multi'		- multiple selections, flat menu
    'selected'		- multiple selections with "Selected xxx" items,
			  flat menu
    'single'		- single selection, flat menu
    'submulti'		- multiple selections, per-type submenus
    'subselected'	- multiple selections with "Selected xxx" items,
			  per-type submenus (not implemented)
    'subsingle'		- single selection, per-type submenus (only one tested)
@param  ds_listener	for multiple selections, this object will be called
			on methods {Is,Toggle}DataSetVisible();
			for single selections STATE_CHANGE_curDataSet is fired
@param  ds_types	defined allowed types, where None means all types
			in the data model
@param  show_derived_menu  True to show a derived submenu if applicable
@param  widget		widget for use in a widget
"""
    super( DataModelMenu, self ).__init__()

#		-- Assertions
    assert state is not None, '"state" parameter is required'
    assert binder is not None, '"binder" parameter is required'

    self.binder = binder
    self.dataModel = data_model

    self.dataSetListener = ds_listener
    self.dataSetMenuVersion = -1

#		-- Types are resolved in _LoadDataModel()
    self.dataSetTypes = []
    self.dataSetTypesIn = ds_types

    self.derivedMenu = None
    self.derivedMenuLabelMap = {}  # keyed by Menu
    self.logger = DataModelMenu.logger_
    self.mode = mode
    self.showDerivedMenu = show_derived_menu
    self.showSelectedItem = False
    self.state = state
    self.widget = widget
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._AddSelectedDataSetItem()		-
  #----------------------------------------------------------------------
  def _AddSelectedDataSetItem( self, menu = None ):
    """Adds a LABEL_selectedDataSet item to the specified menu.
@param  menu		menu to which to add, self if None
"""
    if menu is None:
      menu = self

    item = wx.MenuItem(
        self, wx.ID_ANY, LABEL_selectedDataSet,
	kind = wx.ITEM_CHECK
	)
    menu.AppendItem( item )
    self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
    if self.dataSetListener and \
        self.dataSetListener.IsDataSetVisible( NAME_selectedDataSet ):
      item.Check()
  #end _AddSelectedDataSetItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._CheckSingleItem()		-
  #----------------------------------------------------------------------
  def _CheckSingleItem( self, menu, checked_item ):
    """DFS walk through menus and items, recursively.
@param  menu		menu to check, where None means find the top level
			DataSetsMenu
@param  checked_item	item to check or None to clear all checks
"""
    if menu is None:
      menu = self
      while menu is not None and \
          type( menu ).__name__ != 'DataSetsMenu':
        menu = menu.GetParent()
      #end while

      if menu is None:
        menu = self
    #end if menu

    for i in range( menu.GetMenuItemCount() ):
      item = menu.FindItemByPosition( i )
      sub_menu = item.GetSubMenu()
      if sub_menu is not None:
        self._CheckSingleItem( sub_menu, checked_item )
      elif item.GetKind() == wx.ITEM_CHECK:
	item.Check(
	    checked_item is not None and item.GetId() == checked_item.GetId()
	    )
        #noworky item.Check( item == checked_item )
    #end for
  #end _CheckSingleItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._ClearMenu()			-
  #----------------------------------------------------------------------
  def _ClearMenu( self, menu, excludes = [] ):
    """Recursively removes items.
"""
#    for item in menu.GetMenuItems():
#      if not excludes or item.GetItemLabelText() not in excludes:
#	if item.GetSubMenu() is not None:
#	  self._ClearMenu( item.GetSubMenu(), excludes )
#        menu.DestroyItem( item )
#    #end for

    ndx = 0
    while menu.GetMenuItemCount() > ndx:
      item = menu.FindItemByPosition( ndx )
      if not excludes or item.GetItemLabelText() not in excludes:
        menu.DestroyItem( item )
      else:
        ndx += 1
  #end _ClearMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._FindMenuItem()			-
  #----------------------------------------------------------------------
  def _FindMenuItem( self, ds_type, qds_name, menu = None ):
    """Finds the menu item.
@param  ds_type		dataset category/type
@param  qds_name	DataSetName instance
@return			item or None if not found
"""
    match_item = None
    if menu == None:
      menu = self

    for item in menu.GetMenuItems():
      if item.GetItemLabelText() == qds_name.displayName:
        match_item = item

      else:
        sub = item.GetSubMenu()
	if sub and item.GetItemLabelText() == ds_type:
	  match_item = self._FindMenuItem( ds_type, qds_name, sub )
      #end if-else item.GetItemLabelText()

      if match_item != None: break
    #end for item

    return  match_item
  #end _FindMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.FireStateChange()			-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    if self.widget is not None:
      self.widget.FireStateChange( **kwargs )
    else:
      reason = self.state.Change( None, **kwargs )
      self.state.FireStateChange( reason )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._GetCurDataSet()			-
  #----------------------------------------------------------------------
  def _GetCurDataSet( self ):
    """If self.isSingleSelection and self.widget exists, returns that value,
otherwise returns self.state.curDataSet
"""
    if self.IsSingleSelection() and self.widget is not None:
      qds_name = self.widget.GetCurDataSet()
    else:
      qds_name = self.state.GetCurDataSet()
    return  qds_name
  #end _GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.Init()				-
  #----------------------------------------------------------------------
#  def Init( self, new_state = None ):
#    """Convenience method to call ProcessStateChange( STATE_CHANGE_init )
#"""
##	-- Should be unneeded
#    if new_state is not None:
#      self.state = new_state
#      new_state.AddListener( self )
#
#    self.ProcessStateChange( STATE_CHANGE_init )
#  #end Init


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.IsPullright()			-
  #----------------------------------------------------------------------
  def IsPullright( self ):
    return  self.mode.startswith( 'sub' ) and len( self.dataSetTypes ) > 1
  #end IsPullright


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.IsSingleSelection()		-
  #----------------------------------------------------------------------
  def IsSingleSelection( self ):
    return  self.mode == '' or self.mode.find( 'single' ) >= 0
  #end IsSingleSelection


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Here we determine the available dataset types and create the
derivedMenu if requested in the constructor.
"""
    self.dataSetMenuVersion = -1

#		-- Remove existing items
#		--
#    while self.GetMenuItemCount() > 0:
#      self.DestroyItem( self.FindItemByPosition( 0 ) )
    self._ClearMenu( self )
    self.derivedMenu = None

#		-- Process datamodel to determine if there are derive-ables
#		--
    if self.dataModel:
      have_derived_flag = False

      types_in = \
          self.dataSetTypesIn if self.dataSetTypesIn is not None else \
	  self.dataModel.GetDataSetNames().keys()
      del self.dataSetTypes[ : ]
      for k in sorted( types_in ):
	if k != 'axial':
	  self.dataSetTypes.append( k )
	  if k.find( ':' ) >= 0:
	    have_derived_flag = True
      #end for k

      if self.showDerivedMenu and have_derived_flag:
	self.derivedMenu = wx.Menu()
	derived_item = wx.MenuItem(
	    self, wx.ID_ANY, 'Derived',
	    subMenu = self.derivedMenu
	    )
	self.AppendItem( derived_item )
    #end if self.dataModel
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._OnDataSetMenuItem()		-
  #----------------------------------------------------------------------
  def _OnDataSetMenuItem( self, ev ):
    ev.Skip()

    qds_name = None
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      ds_display_name = item.GetItemLabelText()
      if ds_display_name == LABEL_selectedDataSet:
        qds_name = NAME_selectedDataSet
      elif self.dataModel is not None:
        qds_name = DataSetName( self.dataModel.GetName(), ds_display_name )

    if qds_name:
      if not self.IsSingleSelection():
        if self.dataSetListener and \
	    hasattr( self.dataSetListener, 'ToggleDataSetVisible' ):
	  self.dataSetListener.ToggleDataSetVisible( qds_name )
      else:
	self._CheckSingleItem( None, item )
	#this should not happen, 'selected' implies 'multi' and dataSetListener
	if qds_name == NAME_selectedDataSet:
	  qds_name = self.state.GetCurDataSet()

	if self.widget is not None:
	  self.widget.SetDataSet( qds_name )
	else:
	  reason = self.state.Change( None, cur_dataset = qds_name )
          self.state.FireStateChange( reason )
	#end if-else self.widget
      #end if-else item.GetKind()
    #end if item is not None
  #end _OnDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._OnDerivedDataSetMenuItem()	-
  #----------------------------------------------------------------------
  def _OnDerivedDataSetMenuItem( self, ev ):
    ev.Skip()

    try:
      menu = ev.GetEventObject()
      item = menu.FindItemById( ev.GetId() )

      if item is not None and self.dataModel is not None:
        der_ds_name = None
	item_text = item.GetItemLabelText().replace( ' *', '' )
	der_label_menu = item.GetMenu()

	ds_category = self.dataModel.GetDataSetType( item_text )
	der_label = self.derivedMenuLabelMap.get( der_label_menu )
	if ds_category and der_label:
	  der_ds_name = self.dataModel.\
	      ResolveDerivedDataSet( ds_category, der_label, item_text )

	if der_ds_name:
	  der_qds_name = DataSetName( self.dataModel.GetName(), der_ds_name )
	  #if item.GetKind() == wx.ITEM_CHECK:
	  if not self.IsSingleSelection():
            if self.dataSetListener and \
	        hasattr( self.dataSetListener, 'ToggleDataSetVisible' ):
	      self.dataSetListener.ToggleDataSetVisible( der_qds_name )
	  elif self.widget is not None:
	    self.widget.SetDataSet( der_qds_name )
	  else:
	    reason = self.state.Change( None, cur_dataset = der_qds_name )
	    self.state.FireStateChange( reason )
          #end if-else item.GetKind()
	#end if der_ds_name
      #end if item is not None

    except Exception, ex:
      wx.MessageBox(
          str( ex ), 'Calculate Derived Dataset',
          wx.OK_DEFAULT, self.GetWindow()
          )
  #end _OnDerivedDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.ProcessStateChange()		-
  #----------------------------------------------------------------------
  def ProcessStateChange( self, reason ):
    """Handler for State-mode events.
"""
#    if (reason & STATE_CHANGE_init) > 0:
#      self._LoadDataModel()
#      reason |= STATE_CHANGE_dataModelMgr
#
#    if (reason & STATE_CHANGE_dataModelMgr) > 0:
#      self.UpdateMenu()

    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModelMgr
    if (reason & load_mask) > 0:
      self._LoadDataModel()
      self.UpdateMenu()

    if (reason & STATE_CHANGE_curDataSet) > 0:
      if self.IsSingleSelection() and self.dataModel:
        #data = self.state.GetDataModel()
        qds_name = self.state.GetCurDataSet()
        ds_type = \
	    self.dataModel.GetDataSetType( qds_name.displayName ) \
	    if qds_name else None

	item = None
	if ds_type:
	  item = self._FindMenuItem(
	      self.dataModel.GetDataSetTypeDisplayName( ds_type ), qds_name
	      )
	if item and not item.IsChecked():
	  self._CheckSingleItem( None, item )
      #end if single selection
    #end if curDataSet
  #end ProcessStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.Reset()				-
  #----------------------------------------------------------------------
  def Reset( self ):
    """Rests dataSetMenuVersion to -1.
"""
    self.dataSetMenuVersion = -1
  #end Reset


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu._UpdateDerivedMenu()		-
  #----------------------------------------------------------------------
  def _UpdateDerivedMenu( self ):
    """
"""
#		-- Clear existing items
#		--
    self._ClearMenu( self.derivedMenu )
    self.derivedMenuLabelMap.clear()

#		-- Build map by derived label of maps by category/type
#		-- of derivable datasets
    derived_names_map = {}
    for ds_type in self.dataSetTypes:
      if self.dataModel.IsDerivedType( ds_type ):
        der_label = self.dataModel.GetDataSetTypeDisplayName( ds_type )
	ds_names = derived_names_map.get( der_label )
	if ds_names is None:
	  ds_names = []
	  derived_names_map[ der_label ] = ds_names

	for base_type in self.dataModel.GetDerivableTypes( der_label ):
	  base_ds_names = self.dataModel.GetDataSetNames( base_type )
	  ds_names += base_ds_names
      #end if ds_type is derived
    #end for ds_type

#		-- Create derived submenus
#		--
    if derived_names_map:
      single_flag = self.IsSingleSelection()
      pullright_flag = self.IsPullright()
      #item_kind = wx.ITEM_NORMAL if single_flag else wx.ITEM_CHECK
      item_kind = wx.ITEM_NORMAL

      for der_label, ds_names in sorted( derived_names_map.iteritems() ):
	if len( ds_names ) > 0:
          der_label_menu = wx.Menu()
	  self.derivedMenuLabelMap[ der_label_menu ] = der_label
	  for ds_name in sorted( ds_names ):
	    ds_type = self.dataModel.GetDataSetType( ds_name )
	    item_label = ds_name
	    if self.dataModel.HasDerivedDataSet( ds_type, der_label, ds_name ):
	      item_label += ' *'
	    item = wx.MenuItem(
		der_label_menu, wx.ID_ANY, item_label,
		kind = item_kind
	        )
	    self.binder.\
	        Bind( wx.EVT_MENU, self._OnDerivedDataSetMenuItem, item )
	    der_label_menu.AppendItem( item )

          der_label_item = wx.MenuItem(
	      self.derivedMenu, wx.ID_ANY, der_label,
	      subMenu = der_label_menu
	      )
	  self.derivedMenu.AppendItem( der_label_item )
        #if there are derivables
      #end for der_label, ds_names
    #end if derived_names_map
  #end _UpdateDerivedMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMenu.UpdateMenu()			-
  #----------------------------------------------------------------------
  def UpdateMenu( self ):
    """
"""
    single_checked_item = None

    if self.dataModel is not None and \
        self.dataSetMenuVersion < self.dataModel.GetDataSetNamesVersion():
      single_flag = self.IsSingleSelection()

#			-- Remove existing items
#			--
      self._ClearMenu( self, [ 'Derived' ] )

#			-- Process if we have something
#			--
      if self.dataSetTypes:
        pullright_flag = self.IsPullright()
	selected_flag = self.mode.find( 'selected' ) >= 0
#No radio if we don't have a selected dataset for each category
#	kind = wx.ITEM_RADIO if single_flag else wx.ITEM_CHECK
	kind = wx.ITEM_CHECK

#				-- Pullrights
	if pullright_flag:
#					-- Collate names by base category
	  names_by_type = {}
	  for dtype in self.dataSetTypes:
	    dataset_names = self.dataModel.GetDataSetNames( dtype )
	    if dataset_names:
	      dtype = self.dataModel.GetDataSetTypeDisplayName( dtype )
	      if dtype in names_by_type:
	        names_by_type[ dtype ] += dataset_names
	      else:
	        names_by_type[ dtype ] = list( dataset_names )
	    #end if dataset_names
	  #end for dtype
#					-- Create per-type menus
	  item_ndx = 0
	  cur_selection = self.state.GetCurDataSet()
	  for dtype, dataset_names in sorted( names_by_type.iteritems() ):
	    dtype_menu = wx.Menu()
	    for name in sorted( dataset_names ):
	      qds_name = DataSetName( self.dataModel.GetName(), name )
	      check = False
	      if single_flag:
		check = qds_name == cur_selection
	      elif self.dataSetListener:
	        check = self.dataSetListener.IsDataSetVisible( qds_name )

	      item = wx.MenuItem( dtype_menu, wx.ID_ANY, name, kind = kind )
	      dtype_menu.AppendItem( item )
	      item.Check( check )
	      self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )

	      if single_flag and check:
	        single_checked_item = item
	    #end for name

	    dtype_item = \
	        wx.MenuItem( self, wx.ID_ANY, dtype, subMenu = dtype_menu )
	    self.InsertItem( item_ndx, dtype_item )
	    item_ndx += 1
	  #end for dtype
	  
	  if selected_flag and self.showSelectedItem:
	    self._AddSelectedDataSetItem()
#	    item = wx.MenuItem(
#	        self, wx.ID_ANY, LABEL_selectedDataSet,
#		kind = kind
#		)
#	    self.AppendItem( item )
#	    self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
#	    if self.dataSetListener and \
#	        self.dataSetListener.IsDataSetVisible( NAME_selectedDataSet ):
#	      item.Check()
	  #end if selected_flag

#				-- Flat
	else:
          dataset_names = []
	  selected_ds_names = []
#	  cur_selection = None
	  for dtype in self.dataSetTypes:
	    dataset_names += self.dataModel.GetDataSetNames( dtype )
#	    if cur_selection is None:
#	      cur_selection = self.state.GetDataSetByType( dtype )
#	    if selected_flag and dtype.find( ':' ) < 0:
#	      selected_ds_names.append( 'Selected ' + dtype + ' dataset' )
	  #end for dtype
	  if selected_flag and self.showSelectedItem:
	    selected_ds_names = [ LABEL_selectedDataSet ]
	  #cur_selection = self.state.GetCurDataSet()
	  cur_selection = self._GetCurDataSet()

	  dataset_names.sort()
	  if selected_ds_names:
	    selected_ds_names.sort()
	    dataset_names += selected_ds_names

	  #xxxxx why not just call AppendItem()?
	  ndx = 0
	  for name in dataset_names:
	    qds_name = DataSetName( self.dataModel.GetName(), name )
	    check = False
	    if single_flag:
	      check = qds_name == cur_selection
	    elif self.dataSetListener:
	      check = self.dataSetListener.IsDataSetVisible( qds_name )

	    item = wx.MenuItem( self, wx.ID_ANY, name, kind = kind )
	    self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    self.InsertItem( ndx, item )
	    item.Check( check )

	    if single_flag and check:
	      single_checked_item = item

	    ndx += 1
	  #end for name
	#end if-else pullright_flag

	if self.derivedMenu is not None:
	  self._UpdateDerivedMenu()
      #end if self.dataSetTypes

      if single_flag:
        self.dataSetMenuVersion = self.dataModel.GetDataSetNamesVersion()
	if single_checked_item is not None:
	  self._CheckSingleItem( None, single_checked_item )
    #end if self.dataModel
  #end UpdateMenu

#end DataModelMenu


#------------------------------------------------------------------------
#	CLASS:		DataSetsMenu					-
#------------------------------------------------------------------------
class DataSetsMenu( DataModelMenu ):
  """Common dataset menu implementation.  There are two uses: State-based
and Widget-based.  For the former, this will listen to State events,
self-update based on those events, and fire events through the State object.
In the latter, all updates are performed to the Widget, and the WidgetContainer
or Widget is responsible for calling UpdateMenu().
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.__del__()				-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.state.RemoveListener( self )

    dmgr = self.state.dataModelMgr
    if dmgr is not None:
      dmgr.RemoveListener( 'dataSetAdded', self._OnDataSetAdded )
      dmgr.RemoveListener( 'modelAdded', self._OnModelAdded )
      dmgr.RemoveListener( 'modelRemoved', self._OnModelRemoved )

    super( DataSetsMenu, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self,
      state, binder, mode = '',
      ds_listener = None, ds_types = None,
      show_derived_menu = True,
      widget = None
      ):
    """Initializes with an empty menu.
@param  state		State object, required
@param  binder		object from window containing this on which to call
			Bind() for menu events
@param  mode		mode value: ('selected' implies 'multi')
    ''			- single selection, flat menu (default)
    'multi'		- multiple selections, flat menu
    'selected'		- multiple selections with "Selected xxx" items,
			  flat menu
    'single'		- single selection, flat menu
    'submulti'		- multiple selections, per-type submenus
    'subselected'	- multiple selections with "Selected xxx" items,
			  per-type submenus (not implemented)
    'subsingle'		- single selection, per-type submenus (only one tested)
@param  ds_listener	for multiple selections, this object will be called
			on methods {Is,Toggle}DataSetVisible();
			for single selections STATE_CHANGE_curDataSet is fired
@param  ds_types	defined allowed types, where None means all types
			in the data model
@param  show_derived_menu  True to show a derived submenu if applicable
@param  widget		widget for use in a widget
"""
    super( DataSetsMenu, self ).__init__(
        state, binder,
	None, mode,
        ds_listener, ds_types,
        show_derived_menu, widget
        )
    self.modelSubMenus = {}  # keyed by model name or 'self'

    #added in Init()
    #if widget is None:
    #  state.AddListener( self )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.Init()				-
  #----------------------------------------------------------------------
  def Init( self ):
    """Convenience method to call OnStateChange( STATE_CHANGE_init )
"""
    self.logger.debug( 'initializing' )
    self.state.AddListener( self )
    self.OnStateChange( STATE_CHANGE_init )
  #end Init


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu._LoadDataModelMgr()		-
  #----------------------------------------------------------------------
  def _LoadDataModelMgr( self ):
    """Here we determine the available dataset types, create model
submenu (DataSetMenus), and create the derivedMenu if
requested in the constructor and there is only one DataModel.
"""
    #dmgr = State.FindDataModelMgr( self.state )
    dmgr = self.state.dataModelMgr
    if dmgr is not None:
      dmgr.AddListener( 'dataSetAdded', self._OnDataSetAdded )
      dmgr.AddListener( 'modelAdded', self._OnModelAdded )
      dmgr.AddListener( 'modelRemoved', self._OnModelRemoved )
      self.UpdateAllMenus( dmgr )
    #end if dmgr
  #end _LoadDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu._OnDataSetAdded()			-
  #----------------------------------------------------------------------
  def _OnDataSetAdded( self, dmgr, dmodel, ds_display_name ):
    """Event handler for new dataset in a DataModel instance.
"""
    ds_menu = None

    if dmodel and ds_display_name:
      if 'self' in self.modelSubMenus:
        ds_menu = self.modelSubMenus[ 'self' ]
      elif dmodel.GetName() in self.modelSubMenus:
        ds_menu = self.modelSubMenus[ dmodel.GetName() ]
    #end if dmodel, display_name

    if ds_menu:
      wx.CallAfter( ds_menu.UpdateMenu )
#      ds_menu.ProcessDataSetAdded(
#          dmodel,
#	  DataSetName( dmodel.GetName(), ds_display_name )
#	  )
  #end _OnDataSetAdded


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu._OnModelAdded()			-
  #----------------------------------------------------------------------
  def _OnModelAdded( self, dmgr, model_name ):
    """Event handler for new DataModel instance.  We try to be smart and
only recreate all the menus when necessary.
"""
    if dmgr and model_name:
      if 'self' in self.modelSubMenus:
        self.UpdateAllMenus()
      else:
        dmodel = dmgr.GetDataModel( model_name )
        ds_menu = DataModelMenu(
	    self.state, self.binder,
	    dmodel, self.mode,
	    self.dataSetListener, self.dataSetTypesIn,
	    self.showDerivedMenu, self.widget
	    )
        sub_item = wx.MenuItem( self, wx.ID_ANY, model_name, subMenu = ds_menu )
	self.AppendItem( sub_item )

	self.modelSubMenus[ model_name ] = ds_menu
	ds_menu.ProcessStateChange( STATE_CHANGE_init )
      #end if-else
    #end if dmgr and model_name
  #end _OnModelAdded


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu._OnModelRemoved()			-
  #----------------------------------------------------------------------
  def _OnModelRemoved( self, dmgr, model_name ):
    """Event handler for removed DataModel instance.  We try to be smart and
only recreate all the menus when necessary.
"""
    if dmgr and model_name:
      if dmgr.GetDataModelCount() == 1 and 'self' not in self.modelSubMenus:
        self.UpdateAllMenus()
      elif model_name in self.modelSubMenus:
        menu_item_id = self.FindItem( model_name )
	if menu_item_id != wx.NOT_FOUND:
	  self.DestroyItem( menu_item_id )
        del self.modelSubMenus[ model_name ]
      #end if-else
    #end if dmgr and model_name
  #end _OnModelRemoved


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.OnStateChange()			-
  #----------------------------------------------------------------------
  def OnStateChange( self, reason ):
    """Handler for State-mode events.
"""
    if (reason & STATE_CHANGE_init) > 0:
      #self._LoadDataModelMgr()
      reason |= STATE_CHANGE_dataModelMgr

    if (reason & STATE_CHANGE_dataModelMgr) > 0:
      self._LoadDataModelMgr()

    if (reason & STATE_CHANGE_curDataSet) > 0:
      qds_name = self.state.GetCurDataSet()
      if 'self' in self.modelSubMenus:
        self.ProcessStateChange( STATE_CHANGE_curDataSet )
      #elif qds_name.modelName:
      else:
        for ds_menu in self.modelSubMenus.values():
	  ds_menu.ProcessStateChange( STATE_CHANGE_curDataSet )
    #end if curDataSet
  #end OnStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.Reset()				-
  #----------------------------------------------------------------------
  def Reset( self ):
    """If this is the sole menu, calls super.Reset(), otherwise calls
Reset() on all the model submenus.
"""
    if 'self' in self.modelSubMenus:
      super( DataSetsMenu, self ).Reset()
    else:
      for ds_menu in self.modelSubMenus.values():
        ds_menu.Reset()
  #end Reset


  #----------------------------------------------------------------------
  #	METHOD:		DataSetsMenu.UpdateAllMenus()			-
  #----------------------------------------------------------------------
  def UpdateAllMenus( self, dmgr = None ):
    """
@param  dmgr		DataModelMgr instance or None to grab it from self.state
"""
    self._ClearMenu( self )
    self.modelSubMenus = {}

    if dmgr is None:
      dmgr = State.FindDataModelMgr( self.state )
    if dmgr is not None:
      if dmgr.GetDataModelCount() == 1:
        self.modelSubMenus[ 'self' ] = self
	self.dataModel = dmgr.GetFirstDataModel()
	self.showSelectedItem = True
	self.ProcessStateChange( STATE_CHANGE_init )

      elif dmgr.GetDataModelCount() > 1:
	selected_flag = self.mode.find( 'selected' ) >= 0
	if selected_flag:
	  self._AddSelectedDataSetItem()
        for name in dmgr.GetDataModelNames():
	  dmodel = dmgr.GetDataModel( name )
	  ds_menu = DataModelMenu(
	      self.state, self.binder,
	      dmodel, self.mode,
	      self.dataSetListener, self.dataSetTypesIn,
	      self.showDerivedMenu, self.widget
	      )
	  sub_item = wx.MenuItem( self, wx.ID_ANY, name, subMenu = ds_menu )
	  self.AppendItem( sub_item )

	  self.modelSubMenus[ name ] = ds_menu
	  ds_menu.ProcessStateChange( STATE_CHANGE_init )
	#end for name
      #end if-elif modelCount
    #end if dmgr
  #end UpdateAllMenus

#end DataSetsMenu
