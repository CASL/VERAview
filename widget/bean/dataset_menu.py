#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_menu.py					-
#	HISTORY:							-
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
import os, sys
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
#	CLASS:		DataSetMenu					-
#------------------------------------------------------------------------
class DataSetMenu( wx.Menu ):
  """Common dataset menu implementation.  There are two modes: State-based
and Widget-based.  For the former, this will listen to State and DataModel
events, self-update based on those events, and fire events through the
State object.  In the latter, all updates are performed to the Widget,
and the WidgetContainer or Widget is responsible for calling UpdateMenu().
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self,
      state, binder,
      mode = '',
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
    super( DataSetMenu, self ).__init__()

#		-- Assertions
    assert state is not None, '"state" parameter is required'
    assert binder is not None, '"binder" parameter is required'

    self.binder = binder
    self.dataSetListener = ds_listener
    self.dataSetMenuVersion = -1

#		-- Types are resolved in _LoadDataModel()
    self.dataSetTypes = []
    self.dataSetTypesIn = ds_types

    self.derivedMenu = None
    self.derivedMenuLabelMap = {}
    self.mode = mode
    self.showDerivedMenu = show_derived_menu
    self.state = state
    self.widget = widget

    #if state is not None:
    if widget is None:
      state.AddListener( self )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._CheckSingleItem()			-
  #----------------------------------------------------------------------
  def _CheckSingleItem( self, menu, checked_item ):
    """DFS walk through menus and items, recursively.
@param  menu		menu to check, where None means self
@param  checked_item	item to check or None to clear all checks
"""
    if menu is None:
      menu = self
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
  #	METHOD:		DataSetMenu._ClearMenu()			-
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
  #	METHOD:		DataSetMenu._FindMenuItem()			-
  #----------------------------------------------------------------------
  def _FindMenuItem( self, ds_type, ds_name, menu = None ):
    """Finds the menu item.
@param  ds_type		dataset category/type
@param  ds_name		dataset name
@return			item or None if not found
"""
    match_item = None
    if menu == None:
      menu = self

    for item in menu.GetMenuItems():
      if item.GetItemLabelText() == ds_name:
        match_item = item

      else:
        sub = item.GetSubMenu()
	if sub and item.GetItemLabelText() == ds_type:
	  match_item = self._FindMenuItem( ds_type, ds_name, sub )
      #end if-else item.GetItemLabelText()

      if match_item != None: break
    #end for item

    return  match_item
  #end _FindMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.FireStateChange()			-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    if self.widget is not None:
      self.widget.FireStateChange( **kwargs )
    else:
      reason = self.state.Change( None, **kwargs )
      self.state.FireStateChange( reason )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._GetCurDataSet()			-
  #----------------------------------------------------------------------
  def _GetCurDataSet( self ):
    """If self.isSingleSelection and self.widget exists, returns that value,
otherwise returns self.state.curDataSet
"""
    if self.IsSingleSelection() and self.widget is not None:
      ds_name = self.widget.GetCurDataSet()
    else:
      ds_name = self.state.GetCurDataSet()
    return  ds_name
  #end _GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.HandleStateChange()			-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    """Handler for State-mode events.
"""
    if (reason & STATE_CHANGE_init) > 0:
      self._LoadDataModel()
      reason |= STATE_CHANGE_dataModel

    if (reason & STATE_CHANGE_dataModel) > 0:
      self.UpdateMenu()

    if (reason & STATE_CHANGE_curDataSet) > 0:
      if self.IsSingleSelection():
        #data = self.state.GetDataModel()
	dmgr = self.state.GetDataModelMgr()
        qds_name = self.state.GetCurDataSet()
	dmodel = dmgr.GetDataModel( qds_name = qds_name )
        ds_type = \
	    dmodel.GetDataSetType( qds_name ) if dmodel and qds_name else None
	item = self._FindMenuItem( ds_type, ds_name ) if ds_type else None
	if item and item.GetItemLabelText() == ds_name and \
	    not item.IsChecked():
	  self._CheckSingleItem( self, item )

#_        if item and item.GetKind() == wx.ITEM_RADIO and \
#_	    item.GetItemLabelText() == ds_name:
#_          item.Check()

#_    else:
#_      changes = self.state.GetDataSetChanges( reason )
#_      if changes:
#_        for ds_type, ds_name in changes.iteritems():
#_          item = self._FindMenuItem( ds_type, ds_name )
#_          if item and item.GetKind() == wx.ITEM_RADIO and \
#_	      item.GetItemLabelText() == self.state.GetDataSetByType( ds_type ):
#_            item.Check()
#_        #end for ds_type, ds_name
#_      #end if changes
    #if-else
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.Init()				-
  #----------------------------------------------------------------------
  def Init( self, new_state = None ):
    """Convenience method to call HandleStateChange( STATE_CHANGE_init )
"""
#	-- Should be unneeded
    if new_state is not None:
      self.state = new_state
      new_state.AddListener( self )

    self.HandleStateChange( STATE_CHANGE_init )
  #end Init


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.IsPullright()			-
  #----------------------------------------------------------------------
  def IsPullright( self ):
    return  self.mode.startswith( 'sub' ) and len( self.dataSetTypes ) > 1
  #end IsPullright


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.IsSingleSelection()			-
  #----------------------------------------------------------------------
  def IsSingleSelection( self ):
    return  self.mode == '' or self.mode.find( 'single' ) >= 0
  #end IsSingleSelection


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """
"""
    self.dataSetMenuVersion = -1

#		-- Remove existing items
#		--
    while self.GetMenuItemCount() > 0:
      self.DestroyItem( self.FindItemByPosition( 0 ) )
    self.derivedMenu = None

#		-- Process datamodel to determine if there are derive-ables
#		--
    data_model = State.FindDataModel( self.state )
    if data_model is not None:
      data_model.AddListener( 'newDataSet', self._OnNewDataSet )
      have_derived_flag = False

      types_in = \
          self.dataSetTypesIn if self.dataSetTypesIn is not None else \
	  data_model.GetDataSetNames().keys()
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
    #end if data_model
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._OnDataSetMenuItem()		-
  #----------------------------------------------------------------------
  def _OnDataSetMenuItem( self, ev ):
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      ds_name = item.GetItemLabelText()
      #if item.GetKind() == wx.ITEM_CHECK:
      if not self.IsSingleSelection():
        if self.dataSetListener and \
	    hasattr( self.dataSetListener, 'ToggleDataSetVisible' ):
	  self.dataSetListener.ToggleDataSetVisible( ds_name )
      else:
	self._CheckSingleItem( self, item )
	#this should not happen, 'selected' implies 'multi'
	if ds_name == LABEL_selectedDataSet:
	  ds_name = self.state.GetCurDataSet()

	if self.widget is not None:
	  self.widget.SetDataSet( ds_name )
	else:
	  reason = self.state.Change( None, cur_dataset = ds_name )
          self.state.FireStateChange( reason )
#_        data_model = self.state.GetDataModel()
#_	  ds_type = data_model.GetDataSetType( ds_name ) \
#_	      if data_model is not None else None
#_	  if ds_type:
#_	    reason = self.state.SetDataSetByType( ds_type, ds_name )
#_	    if reason != STATE_CHANGE_noop:
#_	      self.state.FireStateChange( reason )
	#end if-else self.widget
      #end if-else item.GetKind()
    #end if item is not None
  #end _OnDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._OnDerivedDataSetMenuItem()		-
  #----------------------------------------------------------------------
  def _OnDerivedDataSetMenuItem( self, ev ):
    ev.Skip()

    try:
      menu = ev.GetEventObject()
      item = menu.FindItemById( ev.GetId() )
      data_model = State.FindDataModel( self.state )

      if item is not None and data_model is not None:
        der_ds_name = None
	ds_name = item.GetItemLabelText().replace( ' *', '' )
	der_label_menu = item.GetMenu()

	ds_category = data_model.GetDataSetType( ds_name )
	der_label = self.derivedMenuLabelMap.get( der_label_menu )
	if ds_category and der_label:
	  der_ds_name = data_model.\
	      ResolveDerivedDataSet( ds_category, der_label, ds_name )

	if der_ds_name:
	  #if item.GetKind() == wx.ITEM_CHECK:
	  if not self.IsSingleSelection():
            if self.dataSetListener and \
	        hasattr( self.dataSetListener, 'ToggleDataSetVisible' ):
	      self.dataSetListener.ToggleDataSetVisible( der_ds_name )
	  elif self.widget is not None:
	    self.widget.SetDataSet( der_ds_name )
	  else:
	    reason = self.state.Change( None, cur_dataset = der_ds_name )
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
  #	METHOD:		DataSetMenu._OnDerivedDataSetMenuItem_old()	-
  #----------------------------------------------------------------------
  def _OnDerivedDataSetMenuItem_old( self, ev ):
    ev.Skip()

    try:
      menu = ev.GetEventObject()
      item = menu.FindItemById( ev.GetId() )
      if item is not None:
        der_ds_name = None
	ds_name = item.GetItemLabelText().replace( ' *', '' )
	ds_menu = item.GetMenu()

	data_model = self.state.GetDataModel()
	ds_category = data_model.GetDataSetType( ds_name )
	der_label = self.derivedMenuLabelMap.get( ds_menu )
	if ds_category and der_label:
	  der_ds_name = data_model.\
	      ResolveDerivedDataSet( ds_category, der_label, ds_name )

	if der_ds_name:
	  #if item.GetKind() == wx.ITEM_CHECK:
	  if not self.IsSingleSelection():
            if self.dataSetListener and \
	        hasattr( self.dataSetListener, 'ToggleDataSetVisible' ):
	      self.dataSetListener.ToggleDataSetVisible( der_ds_name )
	  elif self.widget is not None:
	    self.widget.SetDataSet( der_ds_name )
	  else:
	    reason = self.state.Change( None, cur_dataset = der_ds_name )
	    self.state.FireStateChange( reason )

#Back to one selected dataset
#	    ds_type = data_model.GetDataSetType( der_ds_name ) \
#	        if data_model is not None else None
#	    if ds_type:
#	      reason = self.state.SetDataSetByType( ds_type, der_ds_name )
#	      if reason != STATE_CHANGE_noop:
#	        self.state.FireStateChange( reason )
          #end if-else item.GetKind()
	#end if der_ds_name
      #end if item is not None

    except Exception, ex:
      wx.MessageBox(
          str( ex ), 'Calculate Derived Dataset',
          wx.OK_DEFAULT, self.GetWindow()
          )
  #end _OnDerivedDataSetMenuItem_old


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._OnNewDataSet()			-
  #----------------------------------------------------------------------
  def _OnNewDataSet( self, *args, **kwargs ):
    wx.CallAfter( self.UpdateMenu )
  #end _OnNewDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.Reset()				-
  #----------------------------------------------------------------------
  def Reset( self ):
    """Reverts dataSetMenuVersion.
"""
    self.dataSetMenuVersion = -1
  #end Reset


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._UpdateDerivedMenu()		-
  #----------------------------------------------------------------------
  def _UpdateDerivedMenu( self, data_model ):
    """
@param  data_model	assumed not None
"""
#		-- Clear existing items
#		--
    self._ClearMenu( self.derivedMenu )
    self.derivedMenuLabelMap.clear()

#		-- Build map by derived label of maps by category/type
#		-- of derivable datasets
    derived_names_map = {}
    for ds_type in self.dataSetTypes:
      if data_model.IsDerivedType( ds_type ):
        der_label = data_model.GetDataSetTypeDisplayName( ds_type )
	ds_names = derived_names_map.get( der_label )
	if ds_names is None:
	  ds_names = []
	  derived_names_map[ der_label ] = ds_names

	for base_type in data_model.GetDerivableTypes( der_label ):
	  base_ds_names = data_model.GetDataSetNames( base_type )
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
	    ds_type = data_model.GetDataSetType( ds_name )
	    item_label = ds_name
	    if data_model.HasDerivedDataSet( ds_type, der_label, ds_name ):
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
  #	METHOD:		DataSetMenu._UpdateDerivedMenu_old()		-
  #----------------------------------------------------------------------
  def _UpdateDerivedMenu_old( self, data_model ):
    """Old, nest by primary type approach.
@param  data_model	assumed not None
"""
#		-- Clear existing items
#		--
    self._ClearMenu( self.derivedMenu )
    self.derivedMenuLabelMap.clear()

#		-- Build map by derived label of maps by category/type
#		-- of derivable datasets
    derived_category_names_map = {}
    for ds_type in self.dataSetTypes:
      ndx = ds_type.find( ':' )
      if ndx >= 0:
        base_type = ds_type[ 0 : ndx ]
	der_label = ds_type[ ndx + 1 : ]
	category_ds_names = data_model.GetDataSetNames( base_type )

	cat_names_map = derived_category_names_map.get( der_label )
	if cat_names_map is None:
	  cat_names_map = {}
	  derived_category_names_map[ der_label ] = cat_names_map

        cat_names = cat_names_map.get( base_type )
	if cat_names is None:
	  cat_names = []
	  cat_names_map[ base_type ] = cat_names
        cat_names += category_ds_names
      #end if ds_type is derived
    #end for ds_type

#		-- Create derived submenus
#		--
    if derived_category_names_map:
      single_flag = self.IsSingleSelection()
      pullright_flag = self.IsPullright()
      #item_kind = wx.ITEM_NORMAL if single_flag else wx.ITEM_CHECK
      item_kind = wx.ITEM_NORMAL

      for der_label, cat_names_map in \
          sorted( derived_category_names_map.iteritems() ):
	der_label_menu = wx.Menu()

	#if pullright_flag:
	if pullright_flag and len( cat_names_map ) > 1:
	  for cat, names in sorted( cat_names_map.iteritems() ):
	    cat_menu = wx.Menu()
	    self.derivedMenuLabelMap[ cat_menu ] = der_label
	    for name in sorted( names ):
	      item_label = name
	      if data_model.HasDerivedDataSet( cat, der_label, name ):
	        item_label += ' *'
	      item = wx.MenuItem(
	          cat_menu, wx.ID_ANY, item_label,
		  kind = item_kind
		  )
	      self.binder.\
	          Bind( wx.EVT_MENU, self._OnDerivedDataSetMenuItem, item )
	      cat_menu.AppendItem( item )
	    #end for name

	    cat_menu_item = \
	      wx.MenuItem( der_label_menu, wx.ID_ANY, cat, subMenu = cat_menu )
	    der_label_menu.AppendItem( cat_menu_item )
	  #end for cat, names

	else:  # flat
	  #der_label_menu._derivedLabel = der_label
          self.derivedMenuLabelMap[ der_label_menu ] = der_label
	  names = []
	  for cat, cat_names in cat_names_map.iteritems():
	    names += cat_names

	  for name in sorted( names ):
	    item_label = name
	    if data_model.HasDerivedDataSet( cat, der_label, name ):
	      item_label += ' *'
	    item = wx.MenuItem(
	        der_label_menu, wx.ID_ANY, item_label,
		kind = item_kind
		)
	    self.binder.\
	        Bind( wx.EVT_MENU, self._OnDerivedDataSetMenuItem, item )
	    der_label_menu.AppendItem( item )
	  #end for name
	#end if-else pullright_flag

	der_label_item = wx.MenuItem(
	    self.derivedMenu, wx.ID_ANY, der_label,
	    subMenu = der_label_menu
	    )
	self.derivedMenu.AppendItem( der_label_item )
      #end for der_label, cat_names_map
    #end if derived_category_names_map
  #end _UpdateDerivedMenu_old


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.UpdateMenu()			-
  #----------------------------------------------------------------------
  def UpdateMenu( self ):
    """
"""
    data_model = State.FindDataModel( self.state )
    if data_model is not None and \
        self.dataSetMenuVersion < data_model.GetDataSetNamesVersion():
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
	    dataset_names = data_model.GetDataSetNames( dtype )
	    if dataset_names:
	      dtype = data_model.GetDataSetTypeDisplayName( dtype )
	      #colon_ndx = dtype.find( ':' )
	      #if colon_ndx >= 0:
	      #  dtype = dtype[ 0 : colon_ndx ]

	      if dtype in names_by_type:
	        names_by_type[ dtype ] += dataset_names
	      else:
	        names_by_type[ dtype ] = list( dataset_names )
	    #end if dataset_names
	  #end for dtype
#					-- Create per-type menus
	  item_ndx = 0
	  #cur_selection = self.state.GetCurDataSet()
	  cur_selection = self._GetCurDataSet()
	  for dtype, dataset_names in sorted( names_by_type.iteritems() ):
	    dtype_menu = wx.Menu()
	    for name in sorted( dataset_names ):
	      check = \
	          name == cur_selection if single_flag else \
	          self.dataSetListener.IsDataSetVisible( name ) \
		    if self.dataSetListener else \
		  False
	      item = wx.MenuItem( dtype_menu, wx.ID_ANY, name, kind = kind )
	      dtype_menu.AppendItem( item )
	      item.Check( check )
	      self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    #end for name

	    dtype_item = \
	        wx.MenuItem( self, wx.ID_ANY, dtype, subMenu = dtype_menu )
	    self.InsertItem( item_ndx, dtype_item )
	    item_ndx += 1
	  #end for dtype
	  
	  if selected_flag:
	    item = \
	      wx.MenuItem( self, wx.ID_ANY, LABEL_selectedDataSet, kind = kind )
	    self.AppendItem( item )
	    self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    if self.dataSetListener and \
	        self.dataSetListener.IsDataSetVisible( LABEL_selectedDataSet ):
	      item.Check()
	  #end if selected_flag

#				-- Flat
	else:
          dataset_names = []
	  selected_ds_names = []
#	  cur_selection = None
	  for dtype in self.dataSetTypes:
	    dataset_names += data_model.GetDataSetNames( dtype )
#	    if cur_selection is None:
#	      cur_selection = self.state.GetDataSetByType( dtype )
#	    if selected_flag and dtype.find( ':' ) < 0:
#	      selected_ds_names.append( 'Selected ' + dtype + ' dataset' )
	  #end for dtype
	  if selected_flag:
	    selected_ds_names = [ LABEL_selectedDataSet ]
	  #cur_selection = self.state.GetCurDataSet()
	  cur_selection = self._GetCurDataSet()

	  dataset_names.sort()
	  if selected_ds_names:
	    selected_ds_names.sort()
	    dataset_names += selected_ds_names

	  ndx = 0
	  for name in dataset_names:
	    check = \
	        name == cur_selection if single_flag else \
	        self.dataSetListener.IsDataSetVisible( name ) \
		  if self.dataSetListener else \
		False

	    item = wx.MenuItem( self, wx.ID_ANY, name, kind = kind )
	    self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    self.InsertItem( ndx, item )
	    item.Check( check )
	    ndx += 1
	  #end for name
	#end if-else pullright_flag

	if self.derivedMenu is not None:
	  self._UpdateDerivedMenu( data_model )
      #end if self.dataSetTypes

      if single_flag:
        self.dataSetMenuVersion = data_model.GetDataSetNamesVersion()
    #end if data_model
  #end UpdateMenu

#end DataSetMenu
