#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_menu_item.py				-
#	HISTORY:							-
#		2016-07-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, os, sys, time, traceback
#import numpy as np
#import pdb  #pdb.set_trace()

try:
  import wx
  #import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from event.state import *


#------------------------------------------------------------------------
#	CLASS:		DataSetMenu					-
#------------------------------------------------------------------------
class DataSetMenu( wx.MenuItem ):
  """Task manager.
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self,
      parent_menu, mode = '',
      ds_callback = None, ds_types = None,
      state = None
      ):
    """Initializes with an empty menu.
@param  parent_menu	parent menu for this item
@param  mode		mode value:
    ''			- single selection, flat menu (default)
    'multi'		- multiple selections, flat menu
    'selected'		- multiple selections with "Selected xxx" items,
			  flat menu
    'single'		- single selection, flat menu
    'submulti'		- multiple selections, per-type submenus
    'subselected'	- multiple selections with "Selected xxx" items,
			  per-type submenus
    'subsingle'		- single selection, per-type submenus
@param  ds_callback	for multiple selections, this item will be called
			with methods {Is,Toggle}DataSetVisible()
@param  ds_types	defined allowed types, where None means all types
			in the data model
@param  state		if not None, SetState()
"""
    super( DataSetMenu, this ).__init__(
        parent_menu, wx.ID_ANY, 'Select Dataset',
	subMenu = wx.Menu()
	)

    self.dataSetCallback = ds_callback
    self.dataSetMenuVersion = -1
    self.dataSetTypes = []
    self.dataSetTypesIn = ds_types
    self.derivedMenu = None
    self.derivedMenuLabelMap = {}
    self.mode = mode
    self.state = None

    self.Bind( wx.EVT_MENU_OPEN, self._UpdateMenu )

    if state is not None:
      self.SetState( state )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._ClearMenu()			-
  #----------------------------------------------------------------------
  def _ClearMenu( self, menu, excludes = [] ):
    """Recursively removes items.
"""
#    for item in menu.GetMenuItems():
#      if not excludes or item.GetLabelText() not in excludes:
#	if item.GetSubMenu() is not None:
#	  self._ClearMenu( item.GetSubMenu(), excludes )
#        menu.DestroyItem( item )
#    #end for

    ndx = 0
    while menu.GetMenuItemCount() > ndx:
      item = menu.FindItemByPosition( ndx )
      if not excludes or item.GetLabelText() not in excludes:
        menu.DestroyItem( item )
      else:
        ndx += 1
  #end if _ClearMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.HandleStateChange()			-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    """
"""
    pass
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu._OnDataSetMenuItem()		-
  #----------------------------------------------------------------------
  def _OnDataSetMenuItem( self, ev ):
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      ds_name = item.GetLabelText()
      if item.GetKind() == wx.ITEM_CHECK:
        if self.dataSetCallback:
	  self.dataSetCallback.ToggleDataSetVisible( ds_name )
      else:
        data_model = self.state.GetDataModel()
	ds_type = data_model.GetDataSetType( ds_name ) \
	    if data_model is not None else None
	if ds_type:
	  reason = self.state.SetDataSetByType( ds_type, ds_name )
	  if reason != STATE_CHANGE_noop:
	    self.state.FireStateChange( reason )
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
	ds_name = item.GetLabelText().replace( ' *', '' )
	ds_menu = item.GetMenu()

	data_model = self.state.GetDataModel()
	ds_category = data_model.GetDataSetType( ds_name )
	label = self.derivedMenuLabelMap.get( ds_menu )
	if ds_category and label:
	  der_ds_name = data_model.ResolveDerivedDataSet(
	      ds_category, label, ds_name
	      )

	if der_ds_name:
	  if item.GetKind() == wx.ITEM_CHECK:
            if self.dataSetCallback:
	      self.dataSetCallback.ToggleDataSetVisible( der_ds_name )
	  else:
	    ds_type = data_model.GetDataSetType( der_ds_name ) \
	        if data_model is not None else None
	    if ds_type:
	      reason = self.state.SetDataSetByType( ds_type, der_ds_name )
	      if reason != STATE_CHANGE_noop:
	        self.state.FireStateChange( reason )
          #end if-else item.GetKind()
	#end if der_ds_name
      #end if item is not None

    except Exception, ex:
      wx.MessageBox(
          str( ex ), 'Calculate Derived Dataset',
          wx.OK_DEFAULT, self
          )
  #end _OnDerivedDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenu.SetState()				-
  #----------------------------------------------------------------------
  def SetState( self, state ):
    """
"""
#		-- Only process if state differs
#		--
    if self.state is not None and self.state != state:
      self.state.RemoveListener( this )
      self.state = state
      state.AddListener( self )

#			-- Remove existing items
#			--
      sub = self.GetSubMenu()
      if sub is None:
        sub = wx.Menu()
	self.SetSubMenu( sub )
      else:
        while sub.GetMenuItemCount() > 0:
	  sub.DestroyItem( sub.FindItemByPosition( 0 ) )
        self.derivedMenu = None

#			-- Process datamodel
#			--
      data_model = state.GetDataModel()
      if data_model is not None:
        have_derived_flag = False

	types_in = \
	    self.dataSetTypesIn if self.dataSetTypesIn is not None else \
	    data_model.GetDataSetNames().keys()
        del self.dataSetTypes[ : ]
	for ds_type in sorted( types_in ):
	  if data_model.HasDataSetType( k ):
	    self.dataSetTypes.append( k )
	    if data_model.GetDerivedLabels( k ):
	      have_derived_flag = True
	#end for k

	if have_derived_flag:
	  self.derivedMenu = wx.Menu()
	  derived_item = wx.MenuItem(
	      sub, wx.ID_ANY, 'Derived',
	      subMenu = self.derivedMenu
	      )
	  sub.AppendItem( derived_item )
      #end if data_model
    #end if new state
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

#		-- Populate derived labels
#		--
    label_cat_ds_names_map = {}
    for ds_type in self.dataSetTypes:
      ndx = ds_type.find( ':' )
      if ndx > 0:
        category = ds_type[ 0 : ndx ]
	der_label = ds_type[ ndx + 1 ]

	if der_label in data_model.GetDerivedLabels( category ):
	  cat_names_map = label_cat_ds_names_map.get( der_label )
	  if cat_names_map is None:
	    cat_names_map = {}
	    label_cat_ds_names_map[ der_label ] = cat_names_map

	  cat_names = cat_names_map.get( category )
	  if cat_names is None:
	    cat_names = []
	    cat_names_map[ category ] = cat_names
	  cat_names += data_model.GetDataSetNames( category )
	#end if der_label
      #end if ndx > 0
    #end for ds_type

    if label_cat_ds_names_map:
      single_flag = self.mode == '' or self.mode.find( 'single' ) >= 0
      item_kind = wx.ITEM_RADIO if single_flag else wx.ITEM_CHECK

      for label, cat_names_map in sorted( label_cat_ds_names_map.iteritems() ):
        ds_menu = wx.Menu()
	#ds_menu._derivedLabel = label
        self.derivedMenuLabelMap[ ds_menu ] = label
	
	for cat, names in cat_names_map.iteritems():
	  for name in sorted( names ):
	    item_label = name
	    if data_model.HasDerivedDataSet( cat, label, name ):
	      item_label += ' *'
	    item = wx.MenuItem( ds_menu, wx.ID_ANY, item_label, kind = item_kind )
	    self.Bind( wx.EVT_MENU, self._OnDerivedDataSetMenuItem, item )
	    ds_menu.AppendItem( item )

	    if item_kind == wx.ITEM_CHECK:
	      der_names = data_model._CreateDerivedNames( cat, label, name )
	      if self.dataSetCallback is None:
	        pass
	      elif self.dataSetCallback.IsDataSetVisible( der_names[ 1 ] ) or \
	          self.dataSetCallback.IsDataSetVisible( der_names[ 2 ] ):
                item.Check()
	    #end if item_kind
	  #end for name
	#end for cat, names

	label_item = wx.MenuItem(
	    self.derivedMenu, wx.ID_ANY, label,
	    subMenu = ds_menu
	    )
        self.derivedMenu.AppendItem( label_item )
      #end for label, cat_names_map
    #end if label_cat_ds_names_map
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
      single_flag = self.mode == '' or self.mode.find( 'single' ) >= 0

#			-- Remove existing items
#			--
      sub = self.GetSubMenu()
      self._ClearMenu( sub, [ 'Derived' ] )

#			-- Process if we have something
#			--
      if self.dataSetTypes:
        pullright_flag = \
	    self.mode.startswith( 'sub' ) and len( self.dataSetTypes ) > 1
	selected_flag = self.mode.find( 'selected' ) >= 0
	kind = wx.ITEM_RADIO if single_flag else wx.ITEM_CHECK

#				-- Pullrights
	if pullright_flag:
	  ndx = 0
	  for dtype in self.dataSetTypes:
	    cur_selection = self.state.GetDataSetByType( dtype )
	    dataset_names = data_model.GetDataSetNames( dtype )
	    dtype_menu = wx.Menu()
	    for name in dataset_names:
	      if single_flag:
	        check = name == cur_selection
	      elif self.dataSetCallback:
	        check = self.dataSetCallback.IsDataSetVisible( name )

	      item = wx.MenuItem( dtype_menu, wx.ID_ANY, name, kind = kind )
	      item.Check( check )
	      self.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    #end for name

	    dtype_item = wx.Item( sub, wx.ID_ANY, dtype, subMenu = dtype_menu )
	    sub.InsertItem( ndx, dtype_item )
	    ndx += 1
	  #end for dtype

#				-- Flat
	else:
          dataset_names = []
	  selected_ds_names = []
	  cur_selection = None
	  for dtype in self.dataSetTypes:
	    if cur_selection is None:
	      cur_selection = self.state.GetDataSetByType( dtype )
	    dataset_names += data_model.GetDataSetNames( dtype )
	    if selected_flag and dtype.find( ':' ) < 0:
	      selected_ds_names.append( 'Selected ' + dtype + ' dataset' )
	  #end for dtype

	  dataset_names.sort()
	  if selected_ds_names:
	    selected_ds_names.sort()
	    dataset_names += selected_ds_names

	  ndx = 0
	  for name in dataset_names:
	    if single_flag:
	      check = name == cur_selection
	    elif self.dataSetCallback:
	      check = self.dataSetCallback.IsDataSetVisible( name )

	    item = wx.MenuItem( sub, wx.ID_ANY, name, kind = kind )
	    item.Check( check )
	    self.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	    sub.InsertItem( ndx, item )
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
