#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widgetcontainer.py				-
#	HISTORY:							-
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
import functools, math, os, sys
import pdb  #pdb.set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

from animators import *
from bean.events_chooser import *
from data.config import Config
from event.state import *
import widget


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
    print >> sys.stderr, \
        '[AnimationCallback] %d/%d (%.2f%%) %s' % \
	( i, n, i * 100.0 / n, '' if msg == None else msg )
  #end __call__


  def __init__( self ):
    pass
  #end __init__

#end AnimationCallback


#------------------------------------------------------------------------
#	CLASS:		WidgetContainer					-
#------------------------------------------------------------------------
class WidgetContainer( wx.Panel ):
  """Widget frame.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, parent, widget_classpath, state, **kwargs ):
    super( WidgetContainer, self ).__init__( parent, -1, style = wx.BORDER_SIMPLE | wx.TAB_TRAVERSAL )

    self.animateMenu = None
    self.controlPanel = None
    self.eventCheckBoxes = {}
    #self.axialCheckBox = None
    self.dataSetMenu = None
    self.dataSetMenuButton = None
    self.dataSetMenuVersion = -1
    self.derivedDataSetMenu = None
    #self.exposureCheckBox = None
    self.eventLocks = State.CreateLocks()
    self.eventsChooserDialog = None
    self.eventsMenu = None
    self.eventsMenuButton = None
    self.eventsMenuItems = {}
    self.led = None
    self.parent = parent
    self.state = state
    self.widget = None
    self.widgetClassPath = widget_classpath
    self.widgetMenu = None
    self.widgetMenuButton = None

#		-- Listen for DataModel events
#		--
    data_model = State.FindDataModel( state )
    #if data_model:
      #data_model.GetDataSetChangeEvent().addListener( self._OnDataSetChange )

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
    if not Config.HaveImageMagick():
      wx.MessageBox(
	  'Cannot find ImageMagick tools for animated image creation',
	  'Save Animated Image', wx.OK_DEFAULT, self
	  )
      file_path = None

    elif file_path == None:
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
  #	METHOD:		FireStateChange()				-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    reason = self.state.Change( self.eventLocks, **kwargs )
    if reason != STATE_CHANGE_noop:
      self.state.FireStateChange( reason )
      #self.GetParent().FireStateChange( reason )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		GetDerivedDataSetMenu()				-
  #----------------------------------------------------------------------
  def GetDerivedDataSetMenu( self ):
    return  self.derivedDataSetMenu
  #end GetDerivedDataSetMenu


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
#handled inside RasterWidget extension _UpdateStateValues() methods
#			-- Check dataset changes
#			--
#      data_model = State.FindDataModel( self.state )
#      if data_model != None:
#        ds_types = self.widget.GetDataSetTypes()
#        for pair in (
#            ( STATE_CHANGE_channelDataSet, self.state.channelDataSet ),
#            ( STATE_CHANGE_detectorDataSet, self.state.detectorDataSet ),
#            ( STATE_CHANGE_pinDataSet, self.state.pinDataSet )
#	    ):
#	  if (reason & pair[ 0 ]) > 0:
#	    cur_type = data_model.GetDataSetType( pair[ 1 ] )
#	    if cur_type != None and cur_type not in ds_types:
#	      reasons &= ~pair[ 0 ]
#	  #end if
#        #end for
#      #end if data_model

      self.widget.HandleStateChange( reason )
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self, widget_classpath, **kwargs ):
#    dsize = wx.DisplaySize()
#    wd = min( dsize[ 0 ], 1280 )
#    ht = min( dsize[ 1 ], 800 )
    data_model = State.FindDataModel( self.state )

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
    tool_button_defs = self.widget.GetToolButtonDefs( data_model )
    if tool_button_defs != None:
      for icon, tip, handler in tool_button_defs:
        tool_im = wx.Image(
	    os.path.join( Config.GetResDir(), icon ),
	    wx.BITMAP_TYPE_PNG
	    )
        tool_button = wx.BitmapButton( control_panel, -1, tool_im.ConvertToBitmap() )
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
    for ev_pair in EVENT_ID_NAMES:
      ev_id = ev_pair[ 0 ]
      if ev_id in lock_set:
        item = wx.MenuItem(
            self.eventsMenu, wx.ID_ANY, ev_pair[ 1 ],
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

    menu_im = wx.Image(
        os.path.join( Config.GetResDir(), 'events_icon_16x16.png' ),
	wx.BITMAP_TYPE_PNG
	)
    self.eventsMenuButton = wx.BitmapButton(
        control_panel, -1, menu_im.ConvertToBitmap()
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
    ndx = 0
    while ndx < len( dataset_types ):
      if data_model.HasDataSetType( dataset_types[ ndx ] ):
        ndx += 1
      else:
        del dataset_types[ ndx ]

    #if dataset_type != None and data_model.HasDataSetCategory( dataset_type ):
    if len( dataset_types ) > 0:
      self.dataSetMenu = wx.Menu()

#			-- Derived pullright
#			--
      derived_labels = data_model.GetDerivedLabels( dataset_types[ 0 ] )
      if derived_labels:
        self.derivedDataSetMenu = wx.Menu()
        derived_item = wx.MenuItem(
            self.dataSetMenu, wx.ID_ANY, 'Derived',
	    subMenu = self.derivedDataSetMenu
	    )
        self.dataSetMenu.AppendItem( derived_item )
      #end if

      menu_im = wx.Image(
            os.path.join( Config.GetResDir(), 'data_icon_16x16.png' ),
	    wx.BITMAP_TYPE_PNG
	    )
      self.dataSetMenuButton = \
          wx.BitmapButton( control_panel, -1, menu_im.ConvertToBitmap() )
      self.dataSetMenuButton.SetToolTip( wx.ToolTip( 'Select Dataset to View' ) )
      self.dataSetMenuButton.Bind( wx.EVT_BUTTON, self._OnDataSetMenu )
#     self.dataSetMenuButton.Bind(
#         wx.EVT_BUTTON,
#	  functools.partial(
#	      self._OnPopupMenu,
#	      self.dataSetMenuButton, self.dataSetMenu
#	      )
#	  )
      cp_sizer.Add(
          self.dataSetMenuButton, 0,
	  wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	  )
    #end if dataset_type

#		-- Widget menu
#		--
#			-- Save image
    self.widgetMenu = wx.Menu()
    save_item = wx.MenuItem( self.widgetMenu, wx.ID_ANY, 'Save Image' )
    self.Bind( wx.EVT_MENU, self._OnSave, save_item )
    self.widgetMenu.AppendItem( save_item )

#			-- Save animated image
    anim_indexes = self.widget.GetAnimationIndexes()
    if anim_indexes != None:
      self.animateMenu = wx.Menu()
      anim_indexes = self.widget.GetAnimationIndexes()

      if 'axial:detector' in anim_indexes and \
          data_model.GetCore().ndetax > 1 and \
	  data_model.HasDataSetType( 'detector' ):
        anim_item = wx.MenuItem(
	    self.animateMenu, wx.ID_ANY, 'Detector Axial Levels'
	    )
        self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
        self.animateMenu.AppendItem( anim_item )
      #end 'axial:detector'

      if 'axial:pin' in anim_indexes and \
          data_model.GetCore().nax > 1 and \
	  data_model.HasDataSetType( 'pin' ):
        anim_item = wx.MenuItem(
	    self.animateMenu, wx.ID_ANY, 'Pin Axial Levels'
	    )
        self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
        self.animateMenu.AppendItem( anim_item )
      #end 'axial:detector'

      if 'statepoint' in anim_indexes and len( data_model.GetStates() ) > 1:
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

#			-- Widget-defined items
    widget_menu_def = self.widget.GetMenuDef( data_model )
    if widget_menu_def != None:
      self.widgetMenu.AppendSeparator()
      for label, handler in widget_menu_def:
	if label == '-':
          self.widgetMenu.AppendSeparator()
	else:
          item = wx.MenuItem( self.widgetMenu, wx.ID_ANY, label )
          self.Bind( wx.EVT_MENU, handler, item )
	  self.widgetMenu.AppendItem( item )
      #end for
    #end if widget_menu_def exists

#		-- Widget menu button
#		--
    menu_im = wx.Image(
          os.path.join( Config.GetResDir(), 'menu_icon_16x16.png' ),
	  wx.BITMAP_TYPE_PNG
	  )
    self.widgetMenuButton = \
        wx.BitmapButton( control_panel, -1, menu_im.ConvertToBitmap() )
    self.widgetMenuButton.SetToolTip( wx.ToolTip( 'Widget Functions' ) )
    self.widgetMenuButton.Bind( wx.EVT_BUTTON, self._OnWidgetMenu )
    cp_sizer.Add(
        self.widgetMenuButton, 0,
	wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2
	)

#		-- Close button
#		--
    close_im = wx.Image(
	os.path.join( Config.GetResDir(), 'close_icon_16x16.png' ),
	wx.BITMAP_TYPE_PNG
        )
    close_button = wx.BitmapButton( control_panel, -1, close_im.ConvertToBitmap() )
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
    self.widget.SetState( self.state )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		IsEventLocked()					-
  #----------------------------------------------------------------------
  def IsEventLocked( self, reason ):
    #return  self.IsEventLocked
    return  self.eventLocks[ reason ]
  #end IsEventLocked


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
    if self.state != None and self.widget != None:
      self.state.RemoveListener( self )

    self.Close()
    self.Destroy()
  #end OnClose


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataSetChange()				-
  #----------------------------------------------------------------------
#  def _OnDataSetChange( self, data_model, *args, **kwargs ):
#    """
#"""
#    self._UpdateDerivedDataSetMenu( data_model )
#  #end _OnDataSetChange


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataSetMenu()				-
  #----------------------------------------------------------------------
  def _OnDataSetMenu( self, ev ):
    """
"""
    #self._UpdateDerivedDataSetMenu()
    self._UpdateDataSetMenu()
    self.dataSetMenuButton.PopupMenu( self.dataSetMenu )
  #end _OnDataSetMenu


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataSetMenuExtraItem()			-
  #----------------------------------------------------------------------
  def _OnDataSetMenuExtraItem( self, ev ):
    """
@deprecated
"""
    ev.Skip()

    data_model = State.FindDataModel( self.state )
    if data_model != None:
      matching_ds_names = data_model.GetExtra4DDataSets()

      if len( matching_ds_names ) == 0:
        wx.MessageBox(
	    'No matching extra datasets',
	    'Save Animated Image', wx.OK_DEFAULT, self
	    )
      else:
        dialog = wx.SingleChoiceDialog(
	    self, 'Select', 'Select Extra Dataset',
	    matching_ds_names
	    )
        status = dialog.ShowModal()
	if status == wx.ID_OK:
	  name = dialog.GetStringSelection()
	  if name != None:
	    self.widget.SetDataSet( 'extra:' + dialog.GetStringSelection() )
      #end if-else
    #end if data_model exists
  #end _OnDataSetMenuExtraItem


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataSetMenuItem()				-
  #----------------------------------------------------------------------
  def _OnDataSetMenuItem( self, ev ):
    """
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item != None:
      self.widget._BusyBegin()
      self.widget.SetDataSet( item.GetLabel() )
      self.widget._BusyEnd()
  #end _OnDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		_OnDerivedDataSetMenuItem()			-
  #----------------------------------------------------------------------
  def _OnDerivedDataSetMenuItem( self, ev ):
    """
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item != None:
      self.widget._BusyBegin()

      ds_name = item.GetLabel().replace( ' *', '' )
      ds_menu = item.GetMenu()
      data_model = State.FindDataModel( self.state )
      name = data_model.ResolveDerivedDataSet(
          self.widget.GetDataSetTypes()[ 0 ], ds_menu._derivedLabel, ds_name
	  )
      if name:
        self.widget.SetDataSet( name )
      self.widget._BusyEnd()
  #end _OnDerivedDataSetMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		_OnEventCheckBox()				-
  #----------------------------------------------------------------------
#  def _OnEventCheckBox( self, state_change_id, ev ):
#    """Handles events from an event lock checkbox
#"""
#    ev.Skip()
#
#    obj = ev.GetEventObject()
#    self.eventLocks[ state_change_id ] = obj.IsChecked()
#
#    if obj.IsChecked():
#      self.widget.HandleStateChange( state_change_id )
#
#    print >> sys.stderr, '[WidgetContainer._OnEventCheckBox] event_id=%d, checked=%d' % ( state_change_id, obj.IsChecked() )
#  #end _OnEventCheckBox


  #----------------------------------------------------------------------
  #	METHOD:		_OnEventMenuItem()				-
  #----------------------------------------------------------------------
  def _OnEventMenuItem( self, ev_id, ev ):
    """
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item != None:
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

    if self.eventsChooserDialog == None:
      self.eventsChooserDialog = EventsChooserDialog(
          self, wx.ID_ANY,
	  event_set = self.widget.GetEventLockSet()
	  )

    self.eventsChooserDialog.ShowModal( self.eventLocks )
    new_events = self.eventsChooserDialog.GetResult()
    if new_events != None:
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
  #	METHOD:		_OnExposureCheckBox()				-
  #----------------------------------------------------------------------
  def _OnExposureCheckBox( self, ev ):
    """Handles events from the event lock check box.
"""
    ev.Skip()

    obj = ev.GetEventObject()
    self.eventLocks[ STATE_CHANGE_exposureIndex ] = obj.IsChecked()
  #end _OnExposureCheckBox


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

    if item != None and self.widget.GetState() != None:
      try:
        animator = None

        label = item.GetLabel().lower()
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

        if animator != None:
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
  #	METHOD:		SaveWidgetAnimatedImage()			-
  #----------------------------------------------------------------------
  def SaveWidgetAnimatedImage( self, animator, file_path = None ):
    """
Must be called from the UI event thread
"""
    file_path = self._CheckAndPromptForAnimatedImage( file_path )

    if file_path != None:
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
    if file_path == None:
      dialog = wx.FileDialog(
          self, 'Save Widget Image', '', '',
	  'PNG files (*.png)|*.png',
	  wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	  )
      if dialog.ShowModal() != wx.ID_CANCEL:
        file_path = dialog.GetPath()
    #end if

    if file_path != None:
      try:
	result = self.widget.CreatePrintImage( file_path )
	if result == None:
	  raise Exception( 'No image created' )
	elif isinstance( result, wx.Image ):
	  result.SaveFile( file_path, wx.BITMAP_TYPE_PNG )
      except Exception, ex :
	msg = 'Error saving image:' + os.linesep + str( ex )
	wx.CallAfter( wx.MessageBox, msg, 'Save Error', wx.OK_DEFAULT, self )
  #end SaveWidgetImage


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetMenu()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetMenu( self ):
    """Handles (re)creation of the dataset menu.
"""
#		-- Check need for update
#		--
    data_model = State.FindDataModel( self.state )
    if data_model != None and \
        self.dataSetMenuVersion < data_model.GetDataSetNamesVersion():

      print >> sys.stderr, \
          '[WidgetContainer._UpdateDataSetMenu] version from=%d, to=%d' % \
	  ( self.dataSetMenuVersion, data_model.GetDataSetNamesVersion() )

#			-- Remove existing items
#			--
      rlist = []
      for item in self.dataSetMenu.GetMenuItems():
        if item.GetLabel() not in ( 'Derived', 'Other' ):
	  rlist.append( item )
      for item in rlist:
        self.dataSetMenu.DestroyItem( item )
#      while self.dataSetMenu.GetMenuItemCount() > 0:
#	item = self.dataSetMenu.FindItemByPosition( 0 )
#	if item.GetLabel() not in ( 'Derived', 'Other' ):
#	  self.dataSetMenu.DestroyItem( item )
#      #end while

#			-- Must have datasets
#			--
#      dataset_type = self.widget.GetDataSetType()
#      if dataset_type != None and data_model.HasDataSetCategory( dataset_type ):
#        dataset_names = data_model.GetDataSetNames( dataset_type )
      dataset_names = []
      if self.widget.GetDataSetTypes() != None:
        for dtype in self.widget.GetDataSetTypes():
	  dataset_names = dataset_names + data_model.GetDataSetNames( dtype )

#				-- Populate dataset items
#				--
      if len( dataset_names ) > 0:
	dataset_names.sort()

	ndx = 0
        for name in dataset_names:
          item = wx.MenuItem( self.dataSetMenu, wx.ID_ANY, name )
          self.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
	  #self.dataSetMenu.AppendItem( item )
	  self.dataSetMenu.InsertItem( ndx, item )
	  ndx += 1
        #end for

#				-- Other 4-tuple shapes?
#				--
#        if self.widget.GetAllow4DDataSets():
#          if data_model.HasDataSetCategory( 'other' ):
#	    self.dataSetMenu.AppendSeparator()
#	    for name in data_model.GetDataSetNames( 'other' ):
#	      item = wx.MenuItem( self.dataSetMenu, wx.ID_ANY, name )
#	      self.Bind( wx.EVT_MENU, self._OnDataSetMenuItem, item )
#	      #self.dataSetMenu.AppendItem( item )
#	      self.dataSetMenu.InsertItem( 0, item )
#	  #end if other datasets exists
#        #end if 4d datasets allowed

        #item = wx.MenuItem( self.dataSetMenu, wx.ID_ANY, 'Extra...' )
	#self.Bind( wx.EVT_MENU, self._OnDataSetMenuExtraItem, item )
	#self.dataSetMenu.AppendItem( item )

#				-- Derived pullright
#				--
	if self.derivedDataSetMenu != None:
	  self._UpdateDerivedDataSetMenu( data_model )
      #end if dataset names

      self.dataSetMenuVersion = data_model.GetDataSetNamesVersion()
    #end if must update
  #end _UpdateDataSetMenu


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDerivedDataSetMenu()			-
  #----------------------------------------------------------------------
  def _UpdateDerivedDataSetMenu( self, data_model = None ):
    """
"""
    if data_model == None:
      data_model = State.FindDataModel( self.state )

    if data_model and self.derivedDataSetMenu:
#		-- Clear existing items
#		--
      while self.derivedDataSetMenu.GetMenuItemCount() > 0:
	item = self.derivedDataSetMenu.FindItemByPosition( 0 )
	self.derivedDataSetMenu.DestroyItem( item )

#		-- Populate derived label submenus
#		--
      ds_category = self.widget.GetDataSetTypes()[ 0 ]
      labels = data_model.GetDerivedLabels( ds_category )
      names = data_model.GetDataSetNames( ds_category )

      if labels and names:
        for label in labels:
	  ds_type = ds_category + ':' + label
	  ds_menu = wx.Menu()
	  ds_menu._derivedLabel = label

	  for name in names:
	    if data_model.HasDerivedDataSet( ds_category, label, name ):
	      name += ' *'

	    item = wx.MenuItem( ds_menu, wx.ID_ANY, name )
	    self.Bind( wx.EVT_MENU, self._OnDerivedDataSetMenuItem, item )
	    ds_menu.AppendItem( item )
	  #end for

	  label_item = wx.MenuItem(
            self.derivedDataSetMenu, wx.ID_ANY, label,
	    subMenu = ds_menu
	    )
	  self.derivedDataSetMenu.AppendItem( label_item )
	#end for label
      #end if we have labels and names
    #end if we have a derived submenu
  #end _UpdateDerivedDataSetMenu

#end WidgetContainer
