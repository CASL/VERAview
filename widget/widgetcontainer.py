#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widgetcontainer.py				-
#	HISTORY:							-
#		2016-12-08	leerw@ornl.gov				-
#	  Migrating to new DataModelMgr.
#		2016-11-19	leerw@ornl.gov				-
#	  Added Show in New Window item and Reparent().
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-09-14	leerw@ornl.gov				-
#	  Fixed bug where a created menu in a menu definition cannot be
#	  twice-parented and used in the popup menu.
#		2016-08-15	leerw@ornl.gov				-
#	  Using DataSetMenu.
#		2016-08-15	leerw@ornl.gov				-
#	  New State and event names.
#		2016-07-23	leerw@ornl.gov				-
#	  Redefined menu definitions with dictionaries.
#	  Added FindMenuItem().
#		2016-04-23	leerw@ornl.gov				-
#		2016-04-20	leerw@ornl.gov				-
#		2016-04-19	leerw@ornl.gov				-
#	  Starting to support multiple dataset display.
#		2016-03-16	leerw@ornl.gov				-
#	  New animations based on gifsicle.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _CreateMenuFromDef() for recursive menu definition.
#		2016-03-06	leerw@ornl.gov				-
#	  Using Widget.GetBitmap() for all icon images.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed Widget.GetDataSetType() to GetDataSetTypes().
#		2016-02-05	leerw@ornl.gov				-
#	  Dynamically creating the dataset menu when out-of-date.
#		2016-02-02	leerw@ornl.gov				-
#	  Trying to add derivedDataSetMenu.
#		2016-01-25	leerw@ornl.gov				-
#	  Added GetWidgetMenu() and GetWidgetMenuButton().
#		2016-01-22	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2016-01-05	leerw@ornl.gov				-
#		2015-12-08	leerw@ornl.gov				-
# 	  State changes managed by the State object.
#		2015-11-18	leerw@ornl.gov				-
# 	  Adding 'other' datasets to the dataset menu if the widget
#	  GetAllow4DDataSets() returns True.
#		2015-08-31	leerw@ornl.gov				-
#	  Fixed _OnSaveAnimated() and SaveWidgetAnimatedImage().
#		2015-08-29	leerw@ornl.gov				-
#	  Adding capability to save animated gif.
#		2015-06-15	leerw@ornl.gov				-
#	  Calling Widget.CreatePrintImage().
#		2015-05-11	leerw@ornl.gov				-
#	  New State.axialValue.
#		2015-04-27	leerw@ornl.gov				-
#	  New STATE_CHANGE_detectorIndex.
#		2015-04-11	leerw@ornl.gov				-
#	  Passing ds_default to constructor.
#		2015-04-04	leerw@ornl.gov				-
#	  STATE_CHANGE_pinRowCol changed to STATE_CHANGE_pinColRow.
#		2015-02-11	leerw@ornl.gov				-
#	  Added STATE_CHANGE_pinRowCol to EVENT_LOCK_PAIRS.
#		2015-01-31	leerw@ornl.gov				-
#	  Switching to Widget.GetMenuDef() since we learned we cannot
#	  handle event generated here in another class.
#		2015-01-30	leerw@ornl.gov				-
#	  Adding close and menu buttons.
#		2015-01-16	leerw@ornl.gov				-
#	  No longer a frame.
#		2015-01-10	leerw@ornl.gov				-
#		2015-01-02	leerw@ornl.gov				-
#	  Event lock UI based on Widget.GetEventLockSet().
#		2014-12-18	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-25	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, logging, math, os, sys
import pdb  #pdb.set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

from animators import *
from bean.dataset_menu import *
from bean.events_chooser import *
from data.config import Config
from event.state import *
import widget
from widget_config import *


## Now using events_chooser
#EVENT_LOCK_PAIRS = \
#  [
#    ( STATE_CHANGE_assemblyIndex, 'Assy' ),
#    ( STATE_CHANGE_axialValue, 'Axial' ),
#    ( STATE_CHANGE_channelColRow, 'Channel' ),
#    ( STATE_CHANGE_channelDataSet, 'Channel Data' ),
#    ( STATE_CHANGE_detectorIndex, 'Detector' ),
#    ( STATE_CHANGE_detectorDataSet, 'Detector Data' ),
#    ( STATE_CHANGE_pinColRow, 'Pin' ),
#    ( STATE_CHANGE_pinDataSet, 'Pin Data' ),
#    ( STATE_CHANGE_scalarDataSet, 'Scalar Data' ),
#    ( STATE_CHANGE_stateIndex, 'State' )
#  ]


###WIDGET_PREF_SIZE = ( 648, 405 )  # 1.6
##WIDGET_PREF_SIZE = ( 600, 450 )  # 1.333
##WIDGET_PREF_SIZE = ( 520, 390 )  # 1.333
#WIDGET_PREF_SIZE = ( 540, 405 )  # 1.333  <--
#WIDGET_PREF_SIZE = ( 486, 405 )  # 1.2
#WIDGET_PREF_SIZE = ( 576, 480 )  # 1.2
#WIDGET_PREF_SIZE = ( 1024, 768 )  # 1.333
#WIDGET_PREF_SIZE = ( 960, 800 )  # 1.2
#WIDGET_PREF_SIZE = ( 480, 400 )  # 1.2

#WIDGET_PREF_SIZE = ( 800, 600 )  # 1.2
#WIDGET_PREF_RATIO = float( WIDGET_PREF_SIZE[ 0 ] ) / float( WIDGET_PREF_SIZE[ 1 ] )

WIDGET_PREF_RATIO = 1.2
WIDGET_PREF_SIZE = ( 480, 400 )


#------------------------------------------------------------------------
#	CLASS:		AnimationCallback				-
#------------------------------------------------------------------------
class AnimationCallback( object ):


  def __call__( self, i, n, msg = None ):
    n = max( n, 1 )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          '%d/%d (%.2f%%) %s',
	  i, n, i * 100.0 / n, '' if msg is None else msg
	  )
  #end __call__


  def __init__( self ):
    self.logger = logging.getLogger( 'widget' )
  #end __init__

#end AnimationCallback


#------------------------------------------------------------------------
#	CLASS:		WidgetContainer					-
#------------------------------------------------------------------------
class WidgetContainer( wx.Panel ):
  """Widget frame.  Refer to the Widget documentation for an explanation
of the widget framework.

WidgetContainer instances are constructed with a full "classpath" to the Widget
extension to dynamically create and a State object.  The latter contains a
DataModel.  The heavy lifting begins in the _InitUI() method.  The
WidgetContainer takes care of building menus (the dataset menu is created
dynamically immediately before display) and frequently consults Widget
properties throughout operation.

The Widget is initialized via a call to SetState().

Events passed to the HandleStateChange() method are handed to the
widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__del__()					-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.state.RemoveListener( self )
    if self.dataSetMenu is not None:
      self.dataSetMenu.Dispose()
#      self.state.RemoveListener( self.dataSetMenu )

    super( WidgetContainer, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, parent, widget_classpath, state, **kwargs ):
    """
@param  parent		parent window
@param  widget_claspath	full module.classpath
@param  state		State instance, cannot be None
@param  kwargs		additional params for widget constructor
"""
    super( WidgetContainer, self ).__init__( parent, -1, style = wx.BORDER_SIMPLE | wx.TAB_TRAVERSAL )

    self.animateMenu = None
    self.controlPanel = None
    self.eventCheckBoxes = {}
    #self.axialCheckBox = None
    self.dataSetMenu = None
    self.dataSetMenuButton = None
    self.dataSetMenuVersion = -1
    #deprecated self.derivedDataSetMenu = None
    #self.exposureCheckBox = None
    self.eventLocks = State.CreateLocks()
    self.eventsChooserDialog = None
    self.eventsMenu = None
    self.eventsMenuButton = None
    self.eventsMenuItems = {}
    self.led = None
    self.logger = widget.Widget.logger_
    self.parent = parent
    self.state = state
    self.widget = None
    self.widgetClassPath = widget_classpath
    self.widgetMenu = None
    self.widgetMenuButton = None

    self._InitUI( widget_classpath, **kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CheckAndPromptForAnimatedImage()		-
  #----------------------------------------------------------------------
  def _CheckAndPromptForAnimatedImage( self, file_path ):
    """
Must be called on the UI thread.
@param  file_path	input file path, None to prompt
@return			file path if selected, None if canceled or
			animated images cannot be created
"""
    if not Config.HaveGifsicle():
      wx.MessageBox(
	  'Cannot find "gifsicle" for animated image creation',
	  'Save Animated Image', wx.OK_DEFAULT, self
	  )
      file_path = None

    elif file_path is None:
      dialog = wx.FileDialog(
          self, 'Save Widget Animated Image', '', '',
	  'GIF files (*.gif)|*.gif',
	  wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	  )
      if dialog.ShowModal() != wx.ID_CANCEL:
        file_path = dialog.GetPath()

    return  file_path
  #end _CheckAndPromptForAnimatedImage


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuFromDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuFromDef( self, menu_in, item_defs ):
    """Given a menu definition, creates the menu with any necessary
pullrights.  Can be called recursively.  A menu definition is a list
of tuples defining entries.  A tuple has two entries, the first of which
is the name.  The special name '-' specifies a separator.  The second
entry in the tuple can be a handle function for an item or another
definition array for a pullright.

@param  menu_in		wxMenu to populate or None to create one
@param  item_defs	list of menu item definitions
@return			menu or created menu
"""
    if item_defs is not None:
      menu = wx.Menu() if menu_in is None else menu_in
      #if menu is None:
        #menu = wx.Menu()

      for item_def in item_defs:
        label = item_def.get( 'label', '-' )
	if label == '-':
	  menu.AppendSeparator()

	elif 'submenu' in item_def:
	  if isinstance( item_def[ 'submenu' ], wx.Menu ):
	    submenu = item_def[ 'submenu' ]
	    if submenu.GetParent() is not None:
	      submenu = None
	  else:
	    submenu = self._CreateMenuFromDef( None, item_def[ 'submenu' ] )
	  if submenu is not None:
	    item = wx.MenuItem( menu, wx.ID_ANY, label, subMenu = submenu )
	    menu.AppendItem( item )

        elif 'handler' in item_def:
	  item_kind = item_def.get( 'kind', wx.ITEM_NORMAL )
          item = wx.MenuItem( menu, wx.ID_ANY, label, kind = item_kind )
	  self.Bind( wx.EVT_MENU, item_def[ 'handler' ], item )
	  menu.AppendItem( item )
	  if 'checked' in item_def:
	    item.Check()
        #end if-elif
      #end for item_def
    #end if menu_def not None

    return  menu
  #end _CreateMenuFromDef


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuFromDef1()				-
  #----------------------------------------------------------------------
  def _CreateMenuFromDef1( self, menu, menu_def ):
    """Given a menu definition, creates the menu with any necessary
pullrights.  Can be called recursively.  A menu definition is a list
of tuples defining entries.  A tuple has two entries, the first of which
is the name.  The special name '-' specifies a separator.  The second
entry in the tuple can be a handle function for an item or another
definition array for a pullright.

@param  menu		wxMenu to populate or None to create one
@param  menu_def	menu definition list
@return			menu or created menu
"""
    if menu_def is not None:
      if menu is None:
        menu = wx.Menu()

      for label, handler_or_def in menu_def:
        if label == '-':
	  menu.AppendSeparator()

        elif isinstance( handler_or_def, list ):
	  pullright = self._CreateMenuFromDef( None, handler_or_def )
	  item = wx.MenuItem( menu, wx.ID_ANY, label, subMenu = pullright )
	  menu.AppendItem( item )

        else:
          item = wx.MenuItem( menu, wx.ID_ANY, label )
          self.Bind( wx.EVT_MENU, handler_or_def, item )
	  menu.AppendItem( item )
      #end for
    #end if menu_def not None

    return  menu
  #end _CreateMenuFromDef1


  #----------------------------------------------------------------------
  #	METHOD:		FindMenuItem()					-
  #----------------------------------------------------------------------
  def FindMenuItem( self, menu, *labels ):
    """Locates the menu item in the menu hierarchy
@param  menu		menu to search
@param  labels		list of items representing item labels in the
			pullright hierarchy
@return			menu item if found or None
"""
    match = None
    if menu and labels:
      for item in menu.GetMenuItems():
        if labels[ 0 ] == item.GetItemLabelText():
	  if len( labels ) == 1:
	    match = item
	    break
	  else:
	    sub = item.GetSubMenu()
	    if sub:
	      match = self.FindMenuItem( sub, *labels[ 1 : ] )
	  #end if-else
	#end if labels match
      #end for item

    return  match
  #end FindMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		FireStateChange()				-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    reason = self.state.Change( self.eventLocks, **kwargs )
    if reason != STATE_CHANGE_noop:
      self.state.FireStateChange( reason )
      #self.GetParent().FireStateChange( reason )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		GetControlPanel()				-
  #----------------------------------------------------------------------
  def GetControlPanel( self ):
    return  self.controlPanel
  #end GetControlPanel


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetMenu()				-
  #----------------------------------------------------------------------
  def GetDataSetMenu( self ):
    """
@return			DataSetsMenu instance
"""
    return  self.dataSetMenu
  #end GetDataSetMenu


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLocks()					-
  #----------------------------------------------------------------------
  def GetEventLocks( self ):
    """
@return			copy of locks dict
"""
    return  dict( self.eventLocks )
  #end GetEventLocks


  #----------------------------------------------------------------------
  #	METHOD:		GetState()					-
  #----------------------------------------------------------------------
  def GetState( self ):
    return  self.state
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		GetWidgetMenu()					-
  #----------------------------------------------------------------------
  def GetWidgetMenu( self ):
    return  self.widgetMenu
  #end GetWidgetMenu


  #----------------------------------------------------------------------
  #	METHOD:		GetWidgetMenuButton()				-
  #----------------------------------------------------------------------
  def GetWidgetMenuButton( self ):
    return  self.widgetMenuButton
  #end GetWidgetMenuButton


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    reason = self.state.ResolveLocks( reason, self.eventLocks )
    if reason != STATE_CHANGE_noop:
      self.widget.HandleStateChange( reason )
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self, widget_classpath, **kwargs ):
    #dmgr = State.FindDataModelMgr( self.state )
    dmgr = self.state.GetDataModelMgr()

#		-- Instantiate Widget
#		--
    module_path, class_name = widget_classpath.rsplit( '.', 1 )
    try:
      module = __import__( module_path, fromlist = [ class_name ] )
    except ImportError:
      raise ValueError( 'Module "%s" could not be imported' % module_path )
    try:
      cls = getattr( module, class_name )
    except AttributeError:
      raise ValueError( 'Class "%s" not found in module "%s"' % (class_name, module_path ) )

    self.widget = cls( self, -1, **kwargs )
    #self.widget.SetMinClientSize( ( 300, 240 ) )

#		-- Create Control Panel
#		--
    control_panel = wx.Panel( self )
    self.controlPanel = control_panel

    cp_sizer = wx.BoxSizer( wx.HORIZONTAL )
    control_panel.SetSizer( cp_sizer )

    cp_sizer.AddSpacer( 4 )

#		-- Widget Title
#		--
    widget_title = wx.StaticText(
        control_panel, -1,
	label = self.widget.GetTitle(), size = ( -1, 22 )
	)
    if Config.CanDragNDrop():
      widget_title.Bind( wx.EVT_LEFT_DOWN, self._OnLeftDown )
    widget_title.SetFont( widget_title.GetFont().Italic() )
    cp_sizer.Add(
        widget_title, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2
	)

    cp_sizer.AddStretchSpacer( 1 )

#		-- LED
#		--
    self.led = wx.StaticBitmap( control_panel, -1, size = wx.Size( 16, 16 ) )
    self.led.SetBitmap( widget.Widget.GetBitmap( widget.BMAP_NAME_green ) )
    cp_sizer.Add(
        self.led, 0,
	wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2
	)

#		-- Widget-defined toolbar buttons
#		--
    tool_button_defs = self.widget.GetToolButtonDefs()
    if tool_button_defs is not None:
      for icon, tip, handler in tool_button_defs:
#        tool_im = wx.Image(
#	    os.path.join( Config.GetResDir(), icon ),
#	    wx.BITMAP_TYPE_PNG
#	    )
#        tool_button = wx.BitmapButton( control_panel, -1, tool_im.ConvertToBitmap() )
        tool_button = wx.BitmapButton(
	    control_panel, -1, widget.Widget.GetBitmap( icon )
	    )
        tool_button.SetToolTip( wx.ToolTip( tip ) )
        tool_button.Bind( wx.EVT_BUTTON, handler )
	cp_sizer.Add(
	    tool_button, 0,
	    wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	    )
      #end for
    #end if tool_button_defs

#		-- Events menu
#		--
    lock_set = self.widget.GetEventLockSet()
    self.eventsMenu = wx.Menu()
    for ev_id, ev_name in LOCKABLE_STATES:
      if ev_id in lock_set:
        item = wx.MenuItem(
            self.eventsMenu, wx.ID_ANY, ev_name,
	    kind = wx.ITEM_CHECK
	    )
        self.Bind(
            wx.EVT_MENU,
	    functools.partial( self._OnEventMenuItem, ev_id ),
	    item
	    )
	self.eventsMenu.AppendItem( item )
        item.Check( True )
	self.eventsMenuItems[ ev_id ] = item

      else:
        self.eventLocks[ ev_id ] = False
    #end for
    item = wx.MenuItem( self.eventsMenu, wx.ID_ANY, 'Edit...' )
    self.Bind( wx.EVT_MENU, self._OnEventsEdit, item )
    self.eventsMenu.AppendItem( item )

#    menu_im = wx.Image(
#        os.path.join( Config.GetResDir(), 'events_icon_16x16.png' ),
#	wx.BITMAP_TYPE_PNG
#	)
#    self.eventsMenuButton = wx.BitmapButton(
#        control_panel, -1, menu_im.ConvertToBitmap()
#	)
    self.eventsMenuButton = wx.BitmapButton(
        control_panel, -1, widget.Widget.GetBitmap( 'events_icon_16x16' )
	)
    self.eventsMenuButton.SetToolTip( wx.ToolTip( 'Control Events' ) )
    self.eventsMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnPopupMenu,
	    self.eventsMenuButton, self.eventsMenu
	    )
	)
    cp_sizer.Add(
        self.eventsMenuButton, 0,
	wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	)

#		-- Dataset menu button
#		--
    dataset_types = list( self.widget.GetDataSetTypes() )
    if len( dataset_types ) > 0:
      display_mode = self.widget.GetDataSetDisplayMode()
      ds_menu_mode = \
          'subselected' if display_mode == 'selected' else \
	  'submulti' if display_mode == 'multi' else \
	  'subsingle'
      self.dataSetMenu = DataSetsMenu(
	  self.state, binder = self, mode = ds_menu_mode,
	  ds_listener = self.widget, ds_types = dataset_types,
	  widget = self.widget
          )

      menu_bmap = widget.Widget.GetBitmap( 'data_icon_16x16' )
      self.dataSetMenuButton = wx.BitmapButton( control_panel, -1, menu_bmap )

      self.dataSetMenuButton.SetToolTip( wx.ToolTip( 'Select Dataset to View' ) )
      self.dataSetMenuButton.Bind( wx.EVT_BUTTON, self._OnDataSetMenu )
      cp_sizer.Add(
          self.dataSetMenuButton, 0,
	  wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	  )
    #end if dataset_types

#		-- Widget menu
#		--
#			-- Save image
    self.widgetMenu = wx.Menu()
    save_item = wx.MenuItem( self.widgetMenu, wx.ID_ANY, 'Save Image' )
    self.Bind( wx.EVT_MENU, self._OnSave, save_item )
    self.widgetMenu.AppendItem( save_item )

#			-- Save animated image
    anim_indexes = self.widget.GetAnimationIndexes()
    if anim_indexes is not None:
      self.animateMenu = wx.Menu()

      #xxxxx 'axial:all'
      if 'axial:detector' in anim_indexes and \
          dmgr.GetCore().ndetax > 1 and \
	  dmgr.HasDataSetType( 'detector' ):
        anim_item = wx.MenuItem(
	    self.animateMenu, wx.ID_ANY, 'Detector Axial Levels'
	    )
        self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
        self.animateMenu.AppendItem( anim_item )
      #end 'axial:detector'

      if 'axial:pin' in anim_indexes and \
          dmgr.GetCore().nax > 1 and \
	  dmgr.HasDataSetType( 'pin' ):
        anim_item = wx.MenuItem(
	    self.animateMenu, wx.ID_ANY, 'Pin Axial Levels'
	    )
        self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
        self.animateMenu.AppendItem( anim_item )
      #end 'axial:detector'

      #if 'statepoint' in anim_indexes and len( data_model.GetStates() ) > 1:
      if 'statepoint' in anim_indexes and len( dmgr.GetTimeValues() ) > 1:
        anim_item = wx.MenuItem(
	    self.animateMenu, wx.ID_ANY, 'State Points'
	    )
        self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
        self.animateMenu.AppendItem( anim_item )
      #end 'axial:detector'

      self.widgetMenu.AppendMenu(
          wx.ID_ANY, 'Save Animated Image', self.animateMenu
	  )
    #end if anim_indexes for this widget

#			-- Save image
    if Config.CanDragNDrop():
      show_item = \
          wx.MenuItem( self.widgetMenu, wx.ID_ANY, 'Show in New Window' )
      self.Bind( wx.EVT_MENU, self._OnShowInNewWindow, show_item )
      self.widgetMenu.AppendItem( show_item )

#			-- Widget-defined items
    widget_menu_def = self.widget.GetMenuDef()
    if widget_menu_def is not None:
      self.widgetMenu.AppendSeparator()
      self._CreateMenuFromDef( self.widgetMenu, widget_menu_def )

#		-- Widget menu button
#		--
    self.widgetMenuButton = wx.BitmapButton(
        control_panel, -1,
	widget.Widget.GetBitmap( 'menu_icon_16x16' )
	)

    self.widgetMenuButton.SetToolTip( wx.ToolTip( 'Widget Functions' ) )
    self.widgetMenuButton.Bind( wx.EVT_BUTTON, self._OnWidgetMenu )
    cp_sizer.Add(
        self.widgetMenuButton, 0,
	wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	)

#		-- Close button
#		--
    close_button = wx.BitmapButton(
        control_panel, -1,
	widget.Widget.GetBitmap( 'close_icon_16x16' )
	)
    close_button.SetToolTip( wx.ToolTip( 'Close This Widget' ) )
    close_button.Bind( wx.EVT_BUTTON, self.OnClose )
    cp_sizer.Add(
        close_button, 0,
	wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	)

#		-- Add Components to this Container
#		--
    vbox = wx.BoxSizer( wx.VERTICAL )
    vbox.Add( control_panel, 0, border = 2, flag = wx.EXPAND )
    vbox.Add( self.widget, 1, border = 2, flag = wx.EXPAND )
    self.SetSizer( vbox )

    #xxxxx get preferred size from widget
    ##self.SetSize( wx.Size( 640, 480 ) )
    #self.SetSize( self.widget.GetInitialSize() )
    #self.SetTitle( self.widget.GetTitle() )
    vbox.Layout()

    self.state.AddListener( self )
    self.widget.Init()
    self.dataSetMenu.Init()
    #self.widget.SetState( self.state )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		IsEventLocked()					-
  #----------------------------------------------------------------------
  def IsEventLocked( self, reason ):
    #return  self.IsEventLocked
    return  self.eventLocks[ reason ]
  #end IsEventLocked


  #----------------------------------------------------------------------
  #	METHOD:		WidgetContainer.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Calls self.widget.LoadProps() and reinitializes dataSetMenu.
@param  props_dict	dict object from which to deserialize properties
"""
    self.widget.LoadProps( props_dict )
    self.dataSetMenu.Init()
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnAxialCheckBox()				-
  #----------------------------------------------------------------------
#  def _OnAxialCheckBox( self, ev ):
#    """Handles events from the event lock check box.
#"""
#    ev.Skip()
#
#    obj = ev.GetEventObject()
#    self.eventLocks[ STATE_CHANGE_axialLevel ] = obj.IsChecked()
#  #end _OnAxialCheckBox


  #----------------------------------------------------------------------
  #	METHOD:		OnClose()					-
  #----------------------------------------------------------------------
  def OnClose( self, ev ):
    """
"""
    if self.state is not None and self.widget is not None:
      self.state.RemoveListener( self )
      if self.dataSetMenu is not None:
        self.dataSetMenu.Dispose()

#    self.Close()
    self.Destroy()
  #end OnClose


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataSetMenu()				-
  #----------------------------------------------------------------------
  def _OnDataSetMenu( self, ev ):
    """
"""
    # Using DataModelMgr and State events instead
    #self.dataSetMenu.UpdateAllMenus()
    self.dataSetMenuButton.PopupMenu( self.dataSetMenu )
  #end _OnDataSetMenu


  #----------------------------------------------------------------------
  #	METHOD:		_OnEventMenuItem()				-
  #----------------------------------------------------------------------
  def _OnEventMenuItem( self, ev_id, ev ):
    """
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      self.eventLocks[ ev_id ] = item.IsChecked()
      if item.IsChecked():
        self.widget.HandleStateChange( ev_id )
  #end _OnEventMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		_OnEventsEdit()					-
  #----------------------------------------------------------------------
  def _OnEventsEdit( self, ev ):
    """
"""
    ev.Skip()

    if self.eventsChooserDialog is None:
      self.eventsChooserDialog = EventsChooserDialog(
          self, wx.ID_ANY,
	  event_set = self.widget.GetEventLockSet()
	  )

    self.eventsChooserDialog.ShowModal( self.eventLocks )
    new_events = self.eventsChooserDialog.GetResult()
    if new_events is not None:
      for k in new_events:
        if k in self.eventsMenuItems:
	  on = new_events[ k ]
          self.eventsMenuItems[ k ].Check( on )
	  self.eventLocks[ k ] = on
	  if on:
            self.widget.HandleStateChange( k )
      #end for
    #end if
  #end _OnEventsEdit


  #----------------------------------------------------------------------
  #	METHOD:		_OnLeftDown()					-
  #----------------------------------------------------------------------
  def _OnLeftDown( self, ev ):
    """
"""
    widget_props = WidgetConfig.CreateWidgetProps( self.widget )
    widget_json = WidgetConfig.Encode( widget_props )

    drag_source = wx.DropSource( ev.GetEventObject() )
    drag_data = wx.TextDataObject( widget_json )
    drag_source.SetData( drag_data )

    result = drag_source.DoDragDrop()
    if result == wx.DragCopy:
      wx.CallAfter( self.OnClose, None )
  #end _OnLeftDown


  #----------------------------------------------------------------------
  #	METHOD:		_OnPopupMenu()					-
  #----------------------------------------------------------------------
  def _OnPopupMenu( self, button, menu, ev ):
    """
"""
    button.PopupMenu( menu )
  #end _OnPopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		_OnSave()					-
  #----------------------------------------------------------------------
  def _OnSave( self, ev ):
    """
"""
    self.SaveWidgetImage()
  #end _OnSave


  #----------------------------------------------------------------------
  #	METHOD:		_OnSaveAnimated()				-
  #----------------------------------------------------------------------
  def _OnSaveAnimated( self, ev ):
    """
"""
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item is not None and self.widget.GetState() is not None:
      try:
        animator = None

        label = item.GetLabel().lower()
	#xxxxx 'all axial'
	if label.find( 'detector axial' ) >= 0:
	  animator = DetectorAxialAnimator(
              self.widget, callback = AnimationCallback()
	      )

	elif label.find( 'pin axial' ) >= 0:
	  animator = PinAxialAnimator(
              self.widget, callback = AnimationCallback()
	      )

	elif label.find( 'state' ) >= 0:
	  animator = StatePointAnimator(
              self.widget, callback = AnimationCallback()
	      )

        if animator is not None:
          self.SaveWidgetAnimatedImage( animator )
      #end try

      except Exception, ex:
        wx.MessageBox(
	    'Cannot animate the widget, data missing:\n' + str( ex ),
	    'Save Animated Image', wx.OK_DEFAULT, self
	    )
    #end if item found
  #end _OnSaveAnimated


  #----------------------------------------------------------------------
  #	METHOD:		_OnShowInNewWindow()				-
  #----------------------------------------------------------------------
  def _OnShowInNewWindow( self, ev ):
    """
"""
    #self.GetTopLevelParent().CreateWindow( self )
    widget_props = WidgetConfig.CreateWidgetProps( self.widget )
    self.GetTopLevelParent().CreateWindow( widget_props )
    wx.CallAfter( self.OnClose, None )
  #end _OnShowInNewWindow


  #----------------------------------------------------------------------
  #	METHOD:		_OnWidgetMenu()					-
  #----------------------------------------------------------------------
  def _OnWidgetMenu( self, ev ):
    """
"""
    # Only for EVT_CONTEXT_MENU
    #pos = ev.GetPosition()
    #pos = self.widgetMenuButton.ScreenToClient( pos )
    #self.widgetMenuButton.PopupMenu( self.widgetMenu, pos )

    self.widgetMenuButton.PopupMenu( self.widgetMenu )
  #end _OnWidgetMenu


  #----------------------------------------------------------------------
  #	METHOD:		Reparent()					-
  #----------------------------------------------------------------------
  def Reparent( self, parent ):
    self.parent = parent
    super( WidgetContainer, self ).Reparent( parent )
  #end Reparent


  #----------------------------------------------------------------------
  #	METHOD:		SaveWidgetAnimatedImage()			-
  #----------------------------------------------------------------------
  def SaveWidgetAnimatedImage( self, animator, file_path = None ):
    """
Must be called from the UI event thread
"""
    file_path = self._CheckAndPromptForAnimatedImage( file_path )

    if file_path is not None:
      animator.Run( file_path )
      #animator.Start( file_path )
    #end if we have a destination file path
  #end SaveWidgetAnimatedImage


  #----------------------------------------------------------------------
  #	METHOD:		SaveWidgetImage()				-
  #----------------------------------------------------------------------
  def SaveWidgetImage( self, file_path = None ):
    """
"""
    if file_path is None:
      dialog = wx.FileDialog(
          self, 'Save Widget Image', '', '',
	  'PNG files (*.png)|*.png',
	  wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	  )
      if dialog.ShowModal() != wx.ID_CANCEL:
        file_path = dialog.GetPath()
    #end if

    if file_path is not None:
      try:
	result = self.widget.CreatePrintImage( file_path )
	if result is None:
	  raise Exception( 'No image created' )
	elif isinstance( result, wx.Image ):
	  result.SaveFile( file_path, wx.BITMAP_TYPE_PNG )
      except Exception, ex :
	msg = 'Error saving image:' + os.linesep + str( ex )
	wx.CallAfter( wx.MessageBox, msg, 'Save Error', wx.OK_DEFAULT, self )
  #end SaveWidgetImage


  #----------------------------------------------------------------------
  #	METHOD:		SetEventLocks()					-
  #----------------------------------------------------------------------
  def SetEventLocks( self, locks ):
    """
@param  locks		dict to copy
"""
    for k in locks:
      if k in self.eventLocks:
        self.eventLocks[ k ] = locks[ k ]

	if k in self.eventsMenuItems:
	  self.eventsMenuItems[ k ].Check( locks[ k ] )
      #end if k
    #end for k
  #end SetEventLocks

#end WidgetContainer
