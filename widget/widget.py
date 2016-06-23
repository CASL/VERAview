#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget.py					-
#	HISTORY:							-
#		2016-06-23	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-23	leerw@ornl.gov				-
#	  Moved GetSelectedDataSetName() from AxialPlot.
#	  Replaced GetDisplaysMultiDataSets() with GetDataSetDisplayMode().
#		2016-04-20	leerw@ornl.gov				-
#	  Added ToggleDataSetVisible().
#		2016-04-19	leerw@ornl.gov				-
#	  Added GetDisplaysMultiDataSets() and IsDataSetVisible().
#		2016-04-18	leerw@ornl.gov				-
#	  In GetColorTuple() accounting for values above max.
#		2016-04-11	leerw@ornl.gov				-
#	  Changed _CalcFontSize() to make minimum label size 6 instead
#	  of 8.
#		2016-03-16	leerw@ornl.gov				-
#	  Moved _OnFixMaxXxx() methods from RasterWidget.
#		2016-02-19	leerw@ornl.gov				-
#	  Solved black background image copy by forcing a white background
#	  image in _OnCopyImage().
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the widget menu messiness with _CreateMenuDef()
#	  and menuDef defined here and GetPopupMenu() implemented here.
#		2016-01-22	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2016-01-05	leerw@ornl.gov				-
#	  Added GetToolButtonDefs().
#		2015-12-22	leerw@ornl.gov				-
#	  Using Legend2 for a continuous legend.
#		2015-11-18	leerw@ornl.gov				-
#	  Added GetAllow4DDataSets().
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().  Renamed _UpdateState() to
#	  UpdateState() since now called by Animator.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring, generalization.
#		2015-05-11	leerw@ornl.gov				-
#	  New State.axialValue.
#		2015-04-13	leerw@ornl.gov				-
#	  Added GetColor{Contrast,Luminance}().
#		2015-03-19	leerw@ornl.gov				-
#	  Added GetDataSetType().
#		2015-02-11	leerw@ornl.gov				-
# 	  Added GetDarkerColor().
#		2015-02-03	leerw@ornl.gov				-
#	  Replaced CreateMenu() with GetMenuDef().
#		2015-01-30	leerw@ornl.gov				-
# 	  Added CreateMenu().
#		2015-01-05	leerw@ornl.gov				-
#	  Moved _CreateLegendPilImage() here.
#	  Added InvertColorXxx() static methods.
#		2014-12-19	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-25	leerw@ornl.gov				-
#------------------------------------------------------------------------
#import os, sys, threading, traceback
import functools, math, os, sys, threading
import pdb  # set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

from event.state import *
from legend import *
from legend2 import *


BMAP_NAME_green = 'led_green_16x16'
BMAP_NAME_red = 'led_red_16x16'

DEFAULT_BG_COLOR_TUPLE = ( 155, 155, 155, 255 )

#DEFAULT_BG_COLOR = wx.Colour( *DEFAULT_BG_COLOR_TUPLE )


#------------------------------------------------------------------------
#	CLASS:		Widget						-
#------------------------------------------------------------------------
class Widget( wx.Panel ):
  """Abstract base class and interface definition for widgets.

Widget Framework
================

Widget instances are driven by the WidgetContainer in which they live.
Refer to the WidgetContainer documentation.

Construction and Initialization
-------------------------------

Widget instances are created by the WidgetContainer (*container*
field/property) and initialized via a call to SetState(), which calls
HandleStateChange( STATE_CHANGE_init ), which in turn calls _LoadDataModel().

Widget UI components must be created in _InitUI() independent of the State
(*state* field) which holds the DataModel (*state.dataModel*).  All extensions
must implement _InitUI().

Event Propagation
-----------------

State change events are passed to HandleStateChange().  For anything other than
the STATE_CHANGE_init or STATE_CHANGE_dataModel "reason", the UpdateState()
method is called, another method which extension must implement.

Fields/Properties
-----------------

container
  WidgetContainer instance, getter is GetContainer()

state
  State instance, getter is GetState()

Framework Methods
-----------------

Refer to documentation for individual methods for more details.

_CreateClipboardData()
  Must be implemented by extensions to provide a textual (CSV) representation
  of the data displayed.

_CreateClipboardImage()
  Must be implemented by extensions to provide a bitmap capture of the
  current widget contents.  Returns a Bitmap.

_CreateMenuDef()
  Returns a description of the widget-specific menu as a list of
  ( label, handler ) pairs.  A default menu is created in this class that
  can be used in extensions by not overriding this method or augmented
  by overriding and calling super._CreateMenuDef().

CreatePrintImage()
  Must be implemented by extensions to store a bitmap capture of the
  current widget contents to a file.  Obviously, this is only slightly
  different from _CreateClipboardImage().

GetAnimationIndexes()
  Extensions must override if they can support animation across one or
  more indexes.
  Must be implemented by extensions to store a bitmap capture of the

GetDataSetDisplayMode()
  Extensions that support "selected" datasets from a type and/or display
  multiple datasets at a time must override to indicate the dataset
  handling mode.  The default is no special handling.  If anything but
  the default is specified, both IsDataSetVisible() and
  ToggleDataSetVisible() must be overridden as well.

GetDataSetTypes()
  Extensions must override to provide a list of categories/types of datasets
  that can be displayed.  Type names are the keys of the DATASET_DEFS dict
  defined in data/datamodel.py, e.g., 'channel', 'detector', 'pin',
  'pin:assembly'.

GetEventLockSet()
  Extensions must override to define the events than can be handled and/or
  produced.  Unless the "reason" mask value is returned in the set, events of
  that type are never propagated to the widget.

GetTitle()
  Must be overridden by extensions to provide a nice label for the widget.

GetToolButtonDefs()
  Can be overridden by extensions to define additional buttons to appear
  on the WidgetContainer toolbar.  The return value is a list of
  ( icon_name, tip_text, handler ) triples.  Refer to the section on
  Icons below for an explanation of icon names.

_InitUI()
  Must be implemented by extensions to create any necessary UI components.
  Failure to implement this method results in an exception.

_LoadDataModel()
  Must be implemented by extensions to initialize local fields and properties
  once the DataModel has been established.  When this method is called from
  HandleStateChange(), the *state* field has been populated.  The preferred
  means of obtaining the DataModel object is State.FindDataModel( self.state ).

_OnFindMax()
  This is a placeholder event handling method for widgets that define a
  "Find Maximum" pullright menu for the widget menu.  The implementation
  here is a noop, but extensions can override to call one of the support
  methods _OnFindMax{Channel,Detector,Pin}().

SetDataSet()
  Called when a dataset is selected on the dataset menu.  Must be implemented
  by extensions.

ToggleDataSetVisible()
  If the dataset display mode [GetDataSetDisplayMode()] is 'select' or 'multi'
  extensions must override this method to handle the toggling of visibility.

UpdateState()
  Must be implemented by extensions.  This method is called by
  HandleStateChange() for any "reason" other than STATE_CHANGE_init or
  STATE_CHANGE_dataModel.  This is the widget's opportunity to update its state
  and UI when changes are initiated from other widgets.  The widget should only
  act upon a state change that differs from its internally-managed state.

Support Methods
---------------

Refer to documentation for individual methods for more details.

This class provides a lot of methods intended to be used by extensions to
accomplish common tasks and operations.

_BusyBegin(), _BusyEnd()
  Turns the LED "working" indicator on and off for long operations.

_CalcFontSize()
  Determines an optimal font size for a specified display width in pixels.

_CreateLegendPilImage()
  Provides a legend PIL image using a Legend2 instance.

FireStateChange()
  Calls *container*.FireStateChange() on a widget-initiated change to the
  event state.

GetSelectedDataSetName()
  Convenience just to standardize how the selected dataset from a type is
  represented in menu labels and such.

_OnContextMenu()
  Handles wx.EVT_CONTEXT_MENU events by showing the popupup menu.  In cases
  where special handling is necessary (e.g., matplotlib), this method should be
  overridden for that processing.

_OnFindMaxChannel()
  Handles 'channel' dataset maximum processing.  Calls
  self.data.FindChannelMaxValue() and FireStateChange().

_OnFindMaxDetector()
  Handles 'detector' dataset maximum processing.  Calls
  self.data.FindDetectorMaxValue() and FireStateChange().

_OnFindMaxPin()
  Handles 'pin' dataset maximum processing.  Calls
  self.data.FindPinMaxValue() and FireStateChange().

_UpdateVisibilityMenuItems()
  Widgets may define menu items for toggling state, in which case the label
  must be changed from "Show ..." to "Hide ... "and vice versa.  This method
  handles that for the ( item, flag ) pairs that are passed.

Icons
-----

In order to improve performance, icons used for menus and buttons should be
loaded only once.  This class has a dict class field, *bitmaps_* that is a
cache of all images loaded.  The static method GetBitmap() takes care of
looking up an icon by filename and creating it if it has not been cached.

There are a couple of simplifying assumptions behind this.  First, it is
assumed that all icons are PNG with a ".png" extension for the filename.
Second, the icon file must exist in the ``res/`` (resources) subdir.

Widget Class Hierarchy
======================
::

  Widget <--+- PlotWidget    <---- AxialPlot
  .         |
  .         +- RasterWidget  <--+- Assembly2DView
  .         |                   |
  .         |                   +- Channel2DView
  .         |                   |
  .         |                   +- ChannelAssembly2DView
  .         |                   |
  .         |                   +- ChannelAxial2DView
  .         |                   |
  .         |                   +- Core2DView
  .         |                   |
  .         |                   +- CoreAxial2DView
  .         |                   |
  .         |                   +- Detector2DView
  .         |
  .         +--------------------- Slicer3DView
  .         |
  .         +--------------------- Volume3DView
"""


#		-- Class Attributes
#		--

  bitmaps_ = {}


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Widget.__eq__()					-
  #----------------------------------------------------------------------
  def __eq__( self, other ):
    """Equality must be the very same object instance.
"""
    return  self is other
  #end __eq__


  #----------------------------------------------------------------------
  #	METHOD:		Widget.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( Widget, self ).__init__( container, id )

    self.busy = False
    #self.busyCursor = None
    self.container = container
    self.state = None

    #self.derivedLabels = None
    self.menuDef = None
    self.popupMenu = None

    Widget.GetBitmap( BMAP_NAME_green )
    Widget.GetBitmap( BMAP_NAME_red )

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyBegin()				-
  #----------------------------------------------------------------------
  def _BusyBegin( self ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
"""
    if not self.busy:
      self.busy = True
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
  #end _BusyBegin


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyBegin_cursor()			-
  #----------------------------------------------------------------------
  def _BusyBegin_cursor( self ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
Not being used.
"""
    if self.busyCursor is None:
      self.busyCursor = wx.BusyCursor()
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
  #end _BusyBegin_cursor


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyBeginOp()				-
  #----------------------------------------------------------------------
  def _BusyBeginOp( self, func, *args ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
"""
    if not self.busy:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
      wx.CallAfter( func, *args )
  #end _BusyBeginOp


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyDoOp()				-
  #----------------------------------------------------------------------
  def _BusyDoOp( self, func, *args ):
    """Show some indication of being busy, make the call, then restore from
the busy indicator.
Must be called from the UI thread.
"""

    self._BusyBegin()
    try:
      func( *args )
#      wx.CallAfter( func, *args )
    finally:
      self._BusyEnd()
  #end _BusyDoOp


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyEnd()				-
  #----------------------------------------------------------------------
  def _BusyEnd( self ):
    """End indication of being busy.
Must be called from the UI thread.
"""
    if self.busy:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      self.busy = False
  #end _BusyEnd


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyEnd_cursor()			-
  #----------------------------------------------------------------------
  def _BusyEnd_cursor( self ):
    """End indication of being busy.
Must be called from the UI thread.
Not being used.
"""
    if self.busyCursor is not None:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      del self.busyCursor
      self.busyCursor = None
  #end _BusyEnd_cursor


  #----------------------------------------------------------------------
  #	METHOD:		Widget._BusyEndOp()				-
  #----------------------------------------------------------------------
  def _BusyEndOp( self, func, *args ):
    """End indication of being busy.
Must be called from the UI thread.
"""
    if self.busyCursor is not None:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      del self.busyCursor
      self.busyCursor = None
      wx.CallAfter( func, *args )
  #end _BusyEndOp


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CalcFontSize()				-
  #----------------------------------------------------------------------
  def _CalcFontSize( self, display_wd ):
    #limits = ( 280, 8, 1280, 28 )
    #limits = ( 280, 8, 1280, 32 )
    limits = ( 280, 6, 1280, 32 )
    if display_wd >= limits[ 2 ]:
      size = limits[ 3 ]
    elif display_wd < limits[ 0 ]:
      size = limits[ 1 ]
    else:
      size = limits[ 1 ] + int( math.floor(
          float( display_wd - limits[ 0 ] ) /
	  float( limits[ 2 ] - limits[ 0 ] ) *
	  float( limits[ 3 ] - limits[ 1 ] )
          ) )
    #size = max( size, 6 )
    return  size
  #end _CalcFontSize


  #----------------------------------------------------------------------
  #	METHOD:		Widget.CreateAnimateImages()			-
  #----------------------------------------------------------------------
#  def CreateAnimateImages( self, temp_dir, over = 'axial' ):
#    """
#"""
#    return  False
#  #end CreateAnimateImages


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateClipboardData()			-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
    """Method that should be overridden by subclasses to create a text
representation of the data displayed.  This implementation returns None.
Note what determines the selection is up to the subclass.

@param  cur_selection_flag  if True, only the current selection is copied
@return			text to copy to the clipboard
"""
    return  None
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateClipboardImage()			-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Method that should be overridden by subclasses to create a bitmap
ready for a clipboard copy.  This implementation returns None.

@return			bitmap to copy to the clipboard
"""
    return  None
  #end _CreateClipboardImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateLegendPilImage()			-
  #----------------------------------------------------------------------
  def _CreateLegendPilImage( self, value_range, font_size = 16 ):
    """For now this is linear only.
@param  value_range	( min, max )
"""
    #was 10
    legend = Legend2( Widget.GetColorTuple, value_range, 8, font_size )
    return  legend.image
  #end _CreateLegendPilImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateLegendPilImage_0()		-
  #----------------------------------------------------------------------
  def _CreateLegendPilImage_0( self, value_range, font_size = 16 ):
    """For now this is linear only.
@param  value_range	( min, max )
"""
    count = 10
    value_delta = value_range[ 1 ] - value_range[ 0 ]
    value_incr = value_delta / count

    colors = []
    values = []

    cur_value = value_range[ 1 ]
    values.append( cur_value )
    for i in range( count ):
      cur_value -= value_incr

      values.append( cur_value )
      colors.append(
          Widget.GetColorTuple( cur_value - value_range[ 0 ], value_delta, 255 )
	  )
#      cur_value -= value_incr
    #end for

    legend = Legend( values, colors, font_size )
    return  legend.image
  #end _CreateLegendPilImage_0


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """List of (label, handler) pairs to present in a menu.
This implementation creates the Copy Data and Copy Image items, so
subclasses must override this calling super._CreateMenuDef() to insert
or append items.
@param  data_model	loaded data model, might be None
@return			[ ( label, handler ), ... ]
"""
    return \
      [
	( 'Copy Displayed Data', functools.partial( self._OnCopyData, False ) ),
	( 'Copy Selected Data', functools.partial( self._OnCopyData, True ) ),
        ( 'Copy Image', self._OnCopyImage )
      ]
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         Widget._CreatePopupMenu()			-
  #----------------------------------------------------------------------
  def _CreatePopupMenu( self ):
    """Populates self.popupMenu from self.GetMenuDef().
Must be called from the UI thread.
"""
    return  self.container._CreateMenuFromDef( None, self.GetMenuDef( None ) )
  #end _CreatePopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		Widget.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    """
Placeholder for widget implementations to create a PNG image.
The default implementation returns None.
@param  file_path	path to file if the widget creates the image
@return			file_path or None if not processed
"""
    #return  wx.EmptyImage( 400, 300 )
    return  None
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._FindListIndex()				-
  #----------------------------------------------------------------------
#  def _FindListIndex( self, values, value ):
#    """Values in the list are assumed in ascending order.
#@param  values		list of values in ascending order
#@param  value		value to find
#@return			0-based index N, where
#			(values[ N ] le value lt values[ N + 1 ]), or
#			-1 if all items are gt value
#@deprecated	Use DataModel.FindListIndex()
#"""
#    match_ndx = -1
#
#    if len( values ) > 0 and value >= values[ 0 ]:
#      for i in range( len( values ) - 1, -1, -1 ):
#        if value >= values[ i ]:
#	  match_ndx = i
#	  break
#      #end for
#    #end if
#
#    return  match_ndx
#  #end _FindListIndex


  #----------------------------------------------------------------------
  #	METHOD:		Widget.FireStateChange()			-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    self.container.FireStateChange( **kwargs )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetAllow4DDataSets()			-
  #----------------------------------------------------------------------
  def GetAllow4DDataSets( self ):
    """Accessor specifying if the widget can visualize any dataset with a
4-tuple shape.  Extensions must override as necessary.
@return			None
@deprecated
"""
    return  None
  #end GetAllow4DDataSets


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetAnimationIndexes()			-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  None
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetContainer()				-
  #----------------------------------------------------------------------
  def GetContainer( self ):
    return  self.container
  #end GetContainer


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetDataSetDisplayMode()			-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Accessor specifying the dataset display mode.
This implementation returns '', but subclasses should override as necessary.
If not '', the subclass should implement IsDataSetVisible() and
ToggleDataSetVisible().
@return			mode
  'selected'	displays multiple datasets and the "selected" datasets for
		the base types/categories
  'multi'	displays multiple datasets
  ''		displays one dataset at a time
"""
    return  ''
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    """Accessor specifying the types of datasets which can be single-selected
for this widget, including derived types.  The types are defined in
datamodel.DATASET_DEFS and include primary types 'channel', 'detector', 'pin',
and 'scalar' as well as derived types such as 'pin:assembly'.  Derived
labels (e.g., 'assembly') that can be produced by this widget will be
determined from this value.  This implementation returns an empty list and must
be overridden by subclasses.

@return			list of dataset types, cannot be None
"""
    return  []
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetDerivedLabels()			-
  #----------------------------------------------------------------------
#  def GetDerivedLabels( self ):
#    """Lazily creates the list of derived labels supported by this
#widget from the types returned by GetDataSetTypes().
#
#@return			set of derived labels, possibly empty, not None
#"""
#    if self.derivedLabels is None:
#      self.derivedLabels = set()
#      for t in self.GetDataSetTypes():
#        ndx = t.find( ':' )
#	if ndx >= 0:
#	  self.derivedLabels.add( t[ ndx + 1 : ] )
#      #end for
#    #end if
#
#    return  self.derivedLabels
#  #end GetDerivedLabels


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetDisplaysMultiDataSets()		-
  #----------------------------------------------------------------------
#  def GetDisplaysMultiDataSets( self ):
#    """Accessor specifying if the widget displays multiple datasets.
#This implementation returns False, but
#subclasses should override as necessary.  If True is returned, a subclass
#should also override IsDataSetVisible() and ToggleDataSetVisible().
#@return			False
#"""
#    return  False
#  #end GetDisplaysMultiDataSets


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, assemblyIndex, axialValue, and stateIndex changes are
captured.
"""
    locks = set([
        STATE_CHANGE_assemblyIndex,
        STATE_CHANGE_axialValue,
#        STATE_CHANGE_axialLevel,
        STATE_CHANGE_scale,
        STATE_CHANGE_stateIndex
        ])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetInitialSize()				-
  #----------------------------------------------------------------------
  def GetInitialSize( self ):
    """Returns None.
"""
    return  wx.Size( 640, 480 )
  #end GetInitialSize


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetMenuDef()				-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """List of (label, handler) pairs to present in a menu.
Lazily created here via a call to _CreateMenuDef(), which should be overridden 
by subclasses.
@param  data_model	loaded data model, might be None
@return			[ ( label, handler ), ... ]
"""
    if self.menuDef is None:
      self.menuDef = self._CreateMenuDef( data_model )
    return  self.menuDef
  #end GetMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         Widget.GetPopupMenu()				-
  #----------------------------------------------------------------------
  def GetPopupMenu( self ):
    """Lazily creates calling _CreatePopupMenu().
Must be called from the UI thread.
"""
    if self.popupMenu is None:
      self.popupMenu = self._CreatePopupMenu()
    return  self.popupMenu
  #end GetPopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetSelectedDataSetName()			-
  #----------------------------------------------------------------------
  def GetSelectedDataSetName( self, ds_type ):
    """
@param  ds_type		dataset type/category
"""
    return  'Selected ' + ds_type + ' dataset'
  #end GetSelectedDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetState()				-
  #----------------------------------------------------------------------
  def GetState( self ):
    return  self.state
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'unnamed'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetToolButtonDefs()			-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self, data_model ):
    """List of (icon_name, tip, handler) triples from which to build tool bar
buttons.
Returning None means no tool buttons, which is the default implemented here.
@param  data_model	loaded data model, might be None
@return			[ ( icon_name, tip, handler ), ... ]
"""
    return  None
  #end GetToolButtonDefs


#  #----------------------------------------------------------------------
#  #	METHOD:		Widget.HandleMenuItem()				-
#  #----------------------------------------------------------------------
#  def HandleMenuItem( self, id ):
#    """Menu handler.  Noop implemented here
#@param  id		menu item id as specified in GetMenuDef().
#"""
#    pass
#  #end HandleMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		Widget.HandleStateChange()			-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    """Note value difference checks must occur in UpdateState()
"""
#    ct = threading.current_thread()
#    print >> sys.stderr, \
#        '[Widget.HandleStateChange] reason=%d, thread=%s/%d' % \
#        ( reason, ct.name, -1 if ct.ident is None else ct.ident )

    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[Core2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      update_args = self.state.CreateUpdateArgs( reason )

      if len( update_args ) > 0:
#			-- Block extra if not supported
#	if 'pin_dataset' in update_args and \
#	    DataModel.IsExtra( update_args[ 'pin_dataset' ] ) and \
#	    not self.GetAllow4DDataSets():
#	  update_args = dict( update_args )
#	  del update_args[ 'pin_dataset' ]
        wx.CallAfter( self.UpdateState, **update_args )
      #end if
    #end else not a data model load
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		Widget._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Implementation classes must override.
"""
    raise  Exception( "subclasses must implement" )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Widget.IsBusy()					-
  #----------------------------------------------------------------------
  def IsBusy( self ):
    return  self.busy
  #end IsBusy


  #----------------------------------------------------------------------
  #	METHOD:		Widget.IsAuxiliaryEvent()			-
  #----------------------------------------------------------------------
  def IsAuxiliaryEvent( self, ev ):
    """Assumes ev implements KeyboardState and checks for Control/Cmd(Meta)
modifiers.
@param  ev		mouse event
@return			True if auxiliary keys are pressed, False otherwise
"""
    mask = ev.GetModifiers() & (wx.MOD_CONTROL | wx.MOD_META)
    return  mask > 0
  #end IsAuxiliaryEvent


  #----------------------------------------------------------------------
  #	METHOD:		Widget.IsDataSetVisible()			-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, ds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
This is meant for subclasses that override GetDisplaysMultiDataSets() to
return True, in which case ToggleDataSetVisible() should also be overridden.
@param  ds_name		dataset name
@return			False
"""
    return  False
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		Widget._LoadDataModel()				-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Must be implemented by extensions.  This is a noop implementation
"""
    pass
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Widget.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    pass
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnContextMenu()				-
  #----------------------------------------------------------------------
  def _OnContextMenu( self, ev ):
    """
"""
    pos = ev.GetPosition()
    pos = self.ScreenToClient( pos )

    menu = self.GetPopupMenu()
    self.PopupMenu( menu, pos )
  #end _OnContextMenu


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnCopyData()				-
  #----------------------------------------------------------------------
  def _OnCopyData( self, selection_flag, ev ):
    """Handler for a Copy Data action.  Calls _CreateClipboardData() to get
the data as text.  If the text is not None or empty, this method copies it to
the clipboard.
"""
    ev.Skip()

    data_text = self._CreateClipboardData( selection_flag )
    if data_text is not None and len( data_text ) > 0:
      if not wx.TheClipboard.Open():
        wx.MessageBox(
	    'Could not open the clipboard', 'Copy Data',
	    wx.ICON_WARNING | wx.OK_DEFAULT
	    )

      else:
        try:
	  wx.TheClipboard.SetData( wx.TextDataObject( data_text ) )

	except Exception, ex:
          wx.MessageBox(
	      'Clipboard copy error', 'Copy Data',
	      wx.ICON_WARNING | wx.OK_DEFAULT
	      )

	finally:
	  wx.TheClipboard.Close()
      #end if-else
    #end if data exist
  #end _OnCopyData


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnCopyImage()				-
  #----------------------------------------------------------------------
  def _OnCopyImage( self, ev ):
    """Handler for a Copy Image action.  Calls _CreateClipboardImage() to get
the image as a bitmap.  If the bitmap is not None or empty, this method copies
it to the clipboard.
"""
    ev.Skip()

    bitmap = self._CreateClipboardImage()
    if bitmap is not None:
      if not wx.TheClipboard.Open():
        wx.MessageBox(
	    'Could not open the clipboard', 'Copy Image',
	    wx.ICON_WARNING | wx.OK_DEFAULT
	    )

      else:
#				-- Force white background for Windoze
#				--
        white_bmap = wx.EmptyBitmapRGBA(
            bitmap.GetWidth(), bitmap.GetHeight(),
	    255, 255, 255, 255
	    )
        img_dc = wx.MemoryDC()
        img_dc.SelectObject( white_bmap )
	try:
          img_dc.DrawBitmap( bitmap, 0, 0 )
	finally:
          img_dc.SelectObject( wx.NullBitmap )
#				--
        try:
	  wx.TheClipboard.SetData( wx.BitmapDataObject( white_bmap ) )

	except Exception, ex:
          wx.MessageBox(
	      'Clipboard copy error', 'Copy Image',
	      wx.ICON_WARNING | wx.OK_DEFAULT
	      )
	finally:
	  wx.TheClipboard.Close()
      #end if-else
    #end if data exist
  #end _OnCopyImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMax()				-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Placeholder event handling method for widgets that define a "Find
"Maximum" pullright for the widget menu.  This implementation is a noop.
Subclasses can override to call _OnFindMaxChannel(), _OnFindMaxDetector(),
or _OnFindMaxPin().
@param  all_states_flag	True for all states, False for current state
@param  ev		menu event
"""
    pass
  #end _OnFindMax


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMaxChannel()			-
  #----------------------------------------------------------------------
  def _OnFindMaxChannel( self, ds_name, all_states_flag ):
    """Handles 'channel' dataset maximum processing, resulting in a call to
FireStateChange() with assembly_index, channel_colrow, and/or
state_index changes.
@param  ds_name		name of dataset
@param  all_states_flag	True for all states, False for current state
"""
    update_args = {}

    if self.data is not None and ds_name:
      update_args = self.data.FindChannelMaxValue(
          ds_name,
	  -1 if all_states_flag else self.stateIndex,
	  self
	  )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMaxChannel


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMaxDetector()			-
  #----------------------------------------------------------------------
  def _OnFindMaxDetector( self, ds_name, all_states_flag ):
    """Handles 'channel' dataset maximum processing, resulting in a call to
FireStateChange() with assembly_index, channel_colrow, and/or
state_index changes.
@param  all_states_flag	True for all states, False for current state
@param  ds_name		name of dataset
"""
    update_args = {}

    if self.data is not None and ds_name:
      update_args = self.data.FindDetectorMaxValue(
          ds_name,
	  -1 if all_states_flag else self.stateIndex,
	  self
	  )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMaxDetector


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMaxPin()				-
  #----------------------------------------------------------------------
  def _OnFindMaxPin( self, ds_name, all_states_flag ):
    """Handles 'pin' dataset maximum processing, resulting in a call to
FireStateChange() with assembly_index, pin_colrow, and/or
state_index changes.
@param  all_states_flag	True for all states, False for current state
@param  ds_name		name of dataset
"""
    update_args = {}

    if self.data is not None and ds_name:
      update_args = self.data.FindPinMaxValue(
	  ds_name,
	  -1 if all_states_flag else self.stateIndex,
	  self
          )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMaxPin


  #----------------------------------------------------------------------
  #	METHOD:		Widget.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object to which to serialize properties
"""
    pass
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Widget.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """Called when a dataset is selected on the dataset menu.  This
implementation is a noop.
"""
    pass
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Widget.SetState()				-
  #----------------------------------------------------------------------
  def SetState( self, state ):
    self.state = state
    self.HandleStateChange( STATE_CHANGE_init )
  #end SetState


  #----------------------------------------------------------------------
  #	METHOD:		Widget.ToggleDataSetVisible()			-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, ds_name ):
    """Toggle the visibility of the named dataset if this supports
multi dataset display.
This implementation is a noop, but subclasses should override if
GetDisplaysMultiDataSets() returns True.
@param  ds_name		dataset name
"""
    pass
  #end ToggleDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		Widget.UpdateState()				-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """Must be implemented by extensions.  This is a noop implementation
"""
    pass
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		Widget._UpdateVisibilityMenuItems()		-
  #----------------------------------------------------------------------
  def _UpdateVisibilityMenuItems( self, menu, *suffixes_and_flags ):
    """Must be called on the UI event thread.
@param  menu		menu to process
@param  suffixes_and_flags  ( suffix, flag, ... ) where suffix appears
			after "Show" or "Hide" in the menu item and
			flag is the current visibility state
"""
    if menu is not None and \
        suffixes_and_flags is not None and len( suffixes_and_flags ) >= 2:
      for item in menu.GetMenuItems():
        label = item.GetItemLabel()

	for i in range( 0, len( suffixes_and_flags ), 2 ):
	  suffix = suffixes_and_flags[ i ]
	  flag = suffixes_and_flags[ i + 1 ]

	  if label.startswith( 'Show ' + suffix ):
	    if flag:
	      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )

	  elif label.startswith( 'Hide ' + suffix ):
	    if not flag:
	      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
	#end for
      #end for
  #end _UpdateVisibilityMenuItems


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetBitmap()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetBitmap( name ):
    """Lazily creates and caches.
"""
    if name in Widget.bitmaps_:
      bmap = Widget.bitmaps_[ name ]
    else:
      image_path = os.path.join( Config.GetResDir(), name + '.png' )
      if os.path.exists( image_path ):
        bmap = wx.Image( image_path, wx.BITMAP_TYPE_PNG ).ConvertToBitmap()
      else:
        bmap = wx.EmptyBitmap( 16, 16 )
      Widget.bitmaps_[ name ] = bmap

    return  bmap
  #end GetBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColor( value, max_value, alpha = 255 ):
    """Calls GetColorTuple().
"""
    return  wx.Colour( *Widget.GetColorTuple( value, max_value, alpha ) )
  #end GetColor


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetColorLuminance()			-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColorLuminance( r, g, b ):
    value = \
        0.2126 * (r / 255.0) + \
	0.7151 * (g / 255.0) + \
	0.0721 * (b / 255.0)
    return  value
  #end GetColorLuminance


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetColorTuple()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColorTuple( value, max_value, alpha = 255, debug = False ):
    """
http://www.particleincell.com/blog/2014/colormap/
@return			( red, green, blue, alpha )
"""
    if debug:
      print >> sys.stderr, \
      '[Widget.GetColorTuple] value=%f, max_value=%f' % \
      ( value, max_value )

    use_value = min( value, max_value )
    f = float( use_value ) / max_value  if max_value != 0.0  else 0.0
    a = (1.0 - f) / 0.25
    x = int( math.floor( a ) )
    y = int( math.floor( 255 * (a - x) ) )

    if x == 0:
      red = 255
      green = y
      blue = 0

    elif x == 1:
      red = 255 - y
      green = 255
      blue = 0

    elif x == 2:
      red = 0
      green = 255
      blue = y

    elif x == 3:
      red = 0
      green = 255 - y
      blue = 200

    else:
      red = 0
      green = 0
      blue = 100

    if debug:
      print >> sys.stderr, \
      '[Widget.GetColorTuple] f=%f, a=%f, x=%f, y=%f, rgb=(%d,%d,%d)' % \
      ( f, a, x, y, red, green, blue )

    return  ( red, green, blue, alpha )
  #end GetColorTuple


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetContrastColor()			-
  #----------------------------------------------------------------------
  @staticmethod
  def GetContrastColor( r, g, b, alpha = 255 ):
    if Widget.GetColorLuminance( r, g, b ) < 0.5:
      color = ( 255, 255, 255, alpha )
    else:
      color = ( 0, 0, 0, alpha )
    return  color
  #end GetContrastColor


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetContrastRedColor()			-
  #----------------------------------------------------------------------
  @staticmethod
  def GetContrastRedColor( r, g, b, alpha = 255 ):
    if Widget.GetColorLuminance( r, g, b ) < 0.5:
      color = ( 255, 0, 0, alpha )
    else:
      color = ( 100, 0, 0, alpha )
    return  color
  #end GetContrastRedColor


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetDarkerColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetDarkerColor( tuple_in, alpha = 255 ):
    """Adjusts each component by a factor of .5.
"""
    result = ( tuple_in[ 0 ] >> 1, tuple_in[ 1 ] >> 1, tuple_in[ 2 ] >> 1, alpha )
    return  result
  #end GetDarkerColor


  #----------------------------------------------------------------------
  #	METHOD:		Widget.InvertColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def InvertColor( color ):
    result = wx.Colour(
        *Widget.InvertColorTuple( color.Red(), color.Green(), color.Blue() )
	)
    return  result
  #end InvertColor


  #----------------------------------------------------------------------
  #	METHOD:		Widget.InvertColorTuple()			-
  #----------------------------------------------------------------------
  @staticmethod
  def InvertColorTuple( r, g, b ):
    return  ( 255 - r, 255 - g, 255 - b )
  #end InvertColorTuple
#end Widget
