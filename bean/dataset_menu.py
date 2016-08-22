#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_menu.py					-
#	HISTORY:							-
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

from event.state import *


#------------------------------------------------------------------------
#	CLASS:		DataSetMenu					-
#------------------------------------------------------------------------
class DataSetMenu( wx.Menu ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self,
      state, binder, mode = '',
      #mode = '', item_bind = None,
      ds_callback = None, ds_types = None
      ):
    """Initializes with an empty menu.
@param  state		State object, required
@param  binder		object from window containingg this on which to call
			Bind() for menu events
@param  mode		mode value:
    ''			- single selection, flat menu (default)
    'multi'		- multiple selections, flat menu
    'selected'		- multiple selections with "Selected xxx" items,
			  flat menu
    'single'		- single selection, flat menu
    'submulti'		- multiple selections, per-type submenus
    'subselected'	- multiple selections with "Selected xxx" items,
			  per-type submenus (not implemented)
    'subsingle'		- single selection, per-type submenus (only one tested)
@param  ds_callback	for multiple selections, this item will be called
			with methods {Is,Toggle}DataSetVisible()
@param  ds_types	defined allowed types, where None means all types
			in the data model
"""
    super( DataSetMenu, self ).__init__()

    self.binder = binder
    self.dataSetCallback = ds_callback
    self.dataSetMenuVersion = -1
    self.dataSetTypes = []
    self.dataSetTypesIn = ds_types
    self.derivedMenu = None
    self.derivedMenuLabelMap = {}
    self.mode = mode
    self.state = state

    state.AddListener( self )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._CheckSingleItem()			-
  #----------------------------------------------------------------------
  def _CheckSingleItem( self, menu, checked_item ):
    """DFS walk through menus and items.
"""
    for i in range( menu.GetMenuItemCount() ):
      item = menu.FindItemByPosition( i )
      sub_menu = item.GetSubMenu()
      if sub_menu is not None:
        self._CheckSingleItem( sub_menu, checked_item )
      elif item.GetKind() == wx.ITEM_CHECK:
        item.Check( item.GetId() == checked_item.GetId() )
        #item.Check( item == checked_item )
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
  #end if _ClearMenu


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
  #	METHOD:		DataSetMenu.HandleStateChange()			-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    """
"""
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      self._LoadDataModel()

    elif (reason & STATE_CHANGE_curDataSet) > 0:
      data = self.state.GetDataModel()
      ds_name = self.state.GetCurDataSet()
      ds_type = data.GetDataSetType( ds_name ) if ds_name else None
      if ds_type:
        item = self._FindMenuItem( ds_type, ds_name )
	if item and item.GetItemLabelText() == ds_name:
	  if self.IsSingleSelection():
	    self._CheckSingleItem( self, item )
	  else:
	    item.Check()
#        if item and item.GetKind() == wx.ITEM_RADIO and \
#	    item.GetItemLabelText() == ds_name:
#          item.Check()

#    else:
#      changes = self.state.GetDataSetChanges( reason )
#      if changes:
#        for ds_type, ds_name in changes.iteritems():
#          item = self._FindMenuItem( ds_type, ds_name )
#          if item and item.GetKind() == wx.ITEM_RADIO and \
#	      item.GetItemLabelText() == self.state.GetDataSetByType( ds_type ):
#            item.Check()
#        #end for ds_type, ds_name
#      #end if changes
    #if-else
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.Init()				-
  #----------------------------------------------------------------------
  def Init( self ):
    """Convenience method to call HandleStateChange( STATE_CHANGE_init )
"""
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
#		-- Remove existing items
#		--
    while self.GetMenuItemCount() > 0:
      self.DestroyItem( self.FindItemByPosition( 0 ) )
    self.derivedMenu = None

#		-- Process datamodel
#		--
    data_model = State.FindDataModel( self.state )
    if data_model is not None:
      have_derived_flag = False

      types_in = \
          self.dataSetTypesIn if self.dataSetTypesIn is not None else \
	  data_model.GetDataSetNames().keys()
	  #data_model.GetDataSetDefs().keys()
      del self.dataSetTypes[ : ]
      for k in sorted( types_in ):
        if k != 'axial' and k.find( ':' ) < 0 and \
	    data_model.HasDataSetType( k ):
          self.dataSetTypes.append( k )
	  if data_model.GetDerivedLabels( k ):
	    have_derived_flag = True
      #end for k

      if have_derived_flag:
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
        if self.dataSetCallback:
	  self.dataSetCallback.ToggleDataSetVisible( ds_name )
      else:
	self._CheckSingleItem( self, item )
	reason = self.state.Change( None, cur_dataset = ds_name )
        self.state.FireStateChange( reason )
#        data_model = self.state.GetDataModel()
#	ds_type = data_model.GetDataSetType( ds_name ) \
#	    if data_model is not None else None
#	if ds_type:
#	  reason = self.state.SetDataSetByType( ds_type, ds_name )
#	  if reason != STATE_CHANGE_noop:
#	    self.state.FireStateChange( reason )
	#end if data_model is not None
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
      if item is not None:
        der_ds_name = None
	ds_name = item.GetItemLabelText().replace( ' *', '' )
	ds_menu = item.GetMenu()

	data_model = self.state.GetDataModel()
	ds_category = data_model.GetDataSetType( ds_name )
	der_label = self.derivedMenuLabelMap.get( ds_menu )
	if ds_category and der_label:
	  der_ds_name = data_model.ResolveDerivedDataSet(
	      ds_category, der_label, ds_name
	      )

	if der_ds_name:
	  if item.GetKind() == wx.ITEM_CHECK:
            if self.dataSetCallback:
	      self.dataSetCallback.ToggleDataSetVisible( der_ds_name )
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
  #end _OnDerivedDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.SetState()				-
  #----------------------------------------------------------------------
  def SetState( self, state ):
    """
@deprecated
"""
#xx    self.state = state
#xx    self.HandleStateChange( STATE_CHANGE_init )
#		-- Only process if state differs
#		--
    if state is not None:
      if state != self.state:
        state.AddListener( self )
	if self.state is not None:
          self.state.RemoveListener( this )
        self.state = state
      #end if state != self.state

      self.HandleStateChange( STATE_CHANGE_init )
    #end if new state

## #			-- Remove existing items
## #			--
##       while self.GetMenuItemCount() > 0:
##         self.DestroyItem( self.FindItemByPosition( 0 ) )
##       self.derivedMenu = None
## 
## #			-- Process datamodel
## #			--
##       data_model = state.GetDataModel()
##       if data_model is not None:
##         have_derived_flag = False
## 
## 	types_in = \
## 	    self.dataSetTypesIn if self.dataSetTypesIn is not None else \
## 	    data_model.GetDataSetNames().keys()
## 	    #data_model.GetDataSetDefs().keys()
##         del self.dataSetTypes[ : ]
## 	for k in sorted( types_in ):
## 	  if k != 'axial' and k.find( ':' ) < 0 and \
## 	      data_model.HasDataSetType( k ):
## 	    self.dataSetTypes.append( k )
## 	    if data_model.GetDerivedLabels( k ):
## 	      have_derived_flag = True
## 	#end for k
## 
## 	if have_derived_flag:
## 	  self.derivedMenu = wx.Menu()
## 	  derived_item = wx.MenuItem(
## 	      self, wx.ID_ANY, 'Derived',
## 	      subMenu = self.derivedMenu
## 	      )
## 	  self.AppendItem( derived_item )
##       #end if data_model
  #end SetState


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
    derived_category_names_map = {}
    for ds_type in self.dataSetTypes:
      der_labels = data_model.GetDerivedLabels( ds_type )
      if der_labels:
        category_ds_names = data_model.GetDataSetNames( ds_type )

	for der_label in der_labels:
	  cat_names_map = derived_category_names_map.get( der_label )
	  if cat_names_map is None:
	    cat_names_map = {}
	    derived_category_names_map[ der_label ] = cat_names_map

	  cat_names = cat_names_map.get( ds_type )
	  if cat_names is None:
	    cat_names = []
	    cat_names_map[ ds_type ] = cat_names
	  cat_names += category_ds_names
	#end for der_label
      #end if der_labels
    #end for ds_type

#		-- Create derived submenus
#		--
    if derived_category_names_map:
      single_flag = self.IsSingleSelection()
      pullright_flag = self.IsPullright()
      item_kind = wx.ITEM_NORMAL if single_flag else wx.ITEM_CHECK

      for der_label, cat_names_map in \
          sorted( derived_category_names_map.iteritems() ):
	der_label_menu = wx.Menu()

	if pullright_flag:
	  for cat, names in cat_names_map.iteritems():
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
  #end _UpdateDerivedMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._UpdateMenu()			-
  #----------------------------------------------------------------------
  def _UpdateMenu( self, ev ):
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
	  ndx = 0
	  cur_selection = self.state.GetCurDataSet()
	  for dtype in self.dataSetTypes:
	    #cur_selection = self.state.GetDataSetByType( dtype )
	    dataset_names = data_model.GetDataSetNames( dtype )
	    dtype_menu = wx.Menu()
	    for name in dataset_names:
	      check = \
	          name == cur_selection if single_flag else \
	          self.dataSetCallback.IsDataSetVisible( name ) \
		    if self.dataSetCallback else \
		  False

	      item = wx.MenuItem( dtype_menu, wx.ID_ANY, name, kind = kind )
	      dtype_menu.AppendItem( item )
	      item.Check( check )
	      self.binder.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    #end for name

	    dtype_item = \
	        wx.MenuItem( self, wx.ID_ANY, dtype, subMenu = dtype_menu )
	    self.InsertItem( ndx, dtype_item )
	    ndx += 1
	  #end for dtype

#				-- Flat
	else:
          dataset_names = []
	  selected_ds_names = []
	  cur_selection = None
	  for dtype in self.dataSetTypes:
	    dataset_names += data_model.GetDataSetNames( dtype )
#	    if cur_selection is None:
#	      cur_selection = self.state.GetDataSetByType( dtype )
#	    if selected_flag and dtype.find( ':' ) < 0:
#	      selected_ds_names.append( 'Selected ' + dtype + ' dataset' )
	  #end for dtype
	  if selected_flag:
	    selected_ds_names = [ 'Selected dataset' ]
	  cur_selection = self.state.GetCurDataSet()

	  dataset_names.sort()
	  if selected_ds_names:
	    selected_ds_names.sort()
	    dataset_names += selected_ds_names

	  ndx = 0
	  for name in dataset_names:
	    check = \
	        name == cur_selection if single_flag else \
	        self.dataSetCallback.IsDataSetVisible( name ) \
		  if self.dataSetCallback else \
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
  #end _UpdateMenu

#end DataSetMenu
