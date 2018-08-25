#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget.py					-
#	HISTORY:							-
#		2018-06-25	leerw@ornl.gov				-
#	  Fixed _ResolveDataRange() to account for min ge max.
#		2018-03-14	leerw@ornl.gov				-
#	  Added for_drag param to SaveProps().
#		2017-12-16	leerw@ornl.gov				-
#	  Adding in-current-assembly find min/max option.
#		2017-11-13	leerw@ornl.gov				-
#	  Added static CalcPointSize() method.
#		2017-11-03	leerw@ornl.gov				-
# 	  Added static CopyFont() method.
#		2017-10-24	leerw@ornl.gov				-
#	  Switching to wx.Bitmap instead of PIL.Image.
#		2017-05-13	leerw@ornl.gov				-
#	  Removed GetDataSetPropertyNames(), added Is3D().
#	  Added title param to _CreateLegendPilImage().
#		2017-05-05	leerw@ornl.gov				-
# 	  Modified HandleStateChange() to call State.ResolveLocks()
#	  on init.
#		2017-05-02	leerw@ornl.gov				-
#	  Fixed bug in _OnFindMinMaxPin() passing self.stateIndex instead
#	  of self.timeValue for with-in state max/min.
#		2017-04-01	leerw@ornl.gov				-
#	  Added apply_custom_range param to _ResolveDataRange().
#		2017-03-10	leerw@ornl.gov				-
#	  Digits and mode for precision.
#		2017-03-04	leerw@ornl.gov				-
#	  Added self.precision with processing in _OnCustomScale().
#		2017-02-03	leerw@ornl.gov				-
#	  Adding white background image save option.
#		2017-01-14	leerw@ornl.gov				-
#	  Added isLoading attribute for LoadProps() signal to not call
#	  LoadDataModelValues().  Was isLoaded in {Plot,Raster}Widget,
#	  so generalizing here.
#		2016-12-13	leerw@ornl.gov				-
#	  Move (de)serialization of curDataSet property here.
#		2016-12-09	leerw@ornl.gov				-
#		2016-12-08	leerw@ornl.gov				-
#	  Migrating to new DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Added customDataRange and dataRangeDialog attributes, with
#	  (de)serialization in {Load,Save}Props().
#	  Added _ResolveDataRange().
#		2016-10-20	leerw@ornl.gov				-
#		2016-10-19	leerw@ornl.gov				-
#	  Resolve issue of widgets not initializing correctly for derived
#	  datasets by changing HandleStateChange() to specify
#	  STATE_CHANGE_ALL and call UpdateState() when
#	  STATE_CHANGE_{dataModel,init} are received.
#		2016-08-23	leerw@ornl.gov				-
#	  Added CheckSingleMenuItem() and ClearMenu().
#	  Setting state in __init__().
#		2016-08-17	leerw@ornl.gov				-
#	  Added _FindFirstDataSet().
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-23	leerw@ornl.gov				-
#	  Redefined menu definitions with dictionaries.
#		2016-06-27	leerw@ornl.gov				-
#	  Implementing SaveProps().
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
import functools, logging, math, os, sys, threading
import pdb  # set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

try:
  from matplotlib import cm, colors
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

from data.config import *
from event.state import *
#from legend import *
#from legend2 import *
from legend3 import *
from bean.data_range_bean import *
import colormaps


BMAP_NAME_green = 'led_green_16x16'
BMAP_NAME_red = 'led_red_16x16'

DEFAULT_BG_COLOR_TUPLE = ( 155, 155, 155, 255 )

#DEFAULT_BG_COLOR = wx.Colour( *DEFAULT_BG_COLOR_TUPLE )

PI_OVER_2 = math.pi / 2.0
TWO_PI = 2.0 * math.pi

SPECTRUM_COLORS = \
  [
    ( 0.000000,0.803922,0.560784 ),
    ( 0.000000,0.803922,0.529412 ),
    ( 0.000000,0.803922,0.498039 ),
    ( 0.000000,0.803922,0.466667 ),
    ( 0.000000,0.803922,0.435294 ),
    ( 0.000000,0.803922,0.403922 ),
    ( 0.000000,0.803922,0.372549 ),
    ( 0.000000,0.803922,0.341176 ),
    ( 0.000000,0.803922,0.309804 ),
    ( 0.000000,0.803922,0.278431 ),
    ( 0.000000,0.803922,0.247059 ),
    ( 0.000000,0.803922,0.215686 ),
    ( 0.000000,0.803922,0.184314 ),
    ( 0.000000,0.803922,0.152941 ),
    ( 0.000000,0.803922,0.121569 ),
    ( 0.000000,0.803922,0.090196 ),
    ( 0.000000,0.803922,0.000000 ),
    ( 0.031373,0.803922,0.000000 ),
    ( 0.062745,0.803922,0.000000 ),
    ( 0.094118,0.803922,0.000000 ),
    ( 0.125490,0.803922,0.000000 ),
    ( 0.156863,0.803922,0.000000 ),
    ( 0.188235,0.803922,0.000000 ),
    ( 0.219608,0.803922,0.000000 ),
    ( 0.250980,0.803922,0.000000 ),
    ( 0.282353,0.803922,0.000000 ),
    ( 0.313725,0.803922,0.000000 ),
    ( 0.345098,0.803922,0.000000 ),
    ( 0.376471,0.803922,0.000000 ),
    ( 0.407843,0.803922,0.000000 ),
    ( 0.439216,0.803922,0.000000 ),
    ( 0.470588,0.803922,0.000000 ),
    ( 0.560784,0.803922,0.000000 ),
    ( 0.572549,0.803922,0.000000 ),
    ( 0.584314,0.803922,0.000000 ),
    ( 0.596078,0.803922,0.000000 ),
    ( 0.607843,0.803922,0.000000 ),
    ( 0.619608,0.803922,0.000000 ),
    ( 0.631373,0.803922,0.000000 ),
    ( 0.643137,0.803922,0.000000 ),
    ( 0.654902,0.803922,0.000000 ),
    ( 0.666667,0.803922,0.000000 ),
    ( 0.678431,0.803922,0.000000 ),
    ( 0.690196,0.803922,0.000000 ),
    ( 0.701961,0.803922,0.000000 ),
    ( 0.713725,0.803922,0.000000 ),
    ( 0.725490,0.803922,0.000000 ),
    ( 0.737255,0.803922,0.000000 ),
    ( 0.803922,0.803922,0.000000 ),
    ( 0.803922,0.800000,0.000000 ),
    ( 0.803922,0.796078,0.000000 ),
    ( 0.803922,0.792157,0.000000 ),
    ( 0.803922,0.788235,0.000000 ),
    ( 0.803922,0.784314,0.000000 ),
    ( 0.803922,0.780392,0.000000 ),
    ( 0.803922,0.776471,0.000000 ),
    ( 0.803922,0.772549,0.000000 ),
    ( 0.803922,0.768627,0.000000 ),
    ( 0.803922,0.764706,0.000000 ),
    ( 0.803922,0.760784,0.000000 ),
    ( 0.803922,0.756863,0.000000 ),
    ( 0.803922,0.752941,0.000000 ),
    ( 0.803922,0.749020,0.000000 ),
    ( 0.803922,0.745098,0.000000 ),
    ( 0.803922,0.686275,0.000000 ),
    ( 0.803922,0.682353,0.000000 ),
    ( 0.803922,0.678431,0.000000 ),
    ( 0.803922,0.674510,0.000000 ),
    ( 0.803922,0.670588,0.000000 ),
    ( 0.803922,0.666667,0.000000 ),
    ( 0.803922,0.662745,0.000000 ),
    ( 0.803922,0.658824,0.000000 ),
    ( 0.803922,0.654902,0.000000 ),
    ( 0.803922,0.650980,0.000000 ),
    ( 0.803922,0.647059,0.000000 ),
    ( 0.803922,0.643137,0.000000 ),
    ( 0.803922,0.639216,0.000000 ),
    ( 0.803922,0.635294,0.000000 ),
    ( 0.803922,0.631373,0.000000 ),
    ( 0.803922,0.627451,0.000000 ),
    ( 0.803922,0.560784,0.000000 ),
    ( 0.803922,0.556863,0.000000 ),
    ( 0.803922,0.552941,0.000000 ),
    ( 0.803922,0.549020,0.000000 ),
    ( 0.803922,0.545098,0.000000 ),
    ( 0.803922,0.541176,0.000000 ),
    ( 0.803922,0.537255,0.000000 ),
    ( 0.803922,0.533333,0.000000 ),
    ( 0.803922,0.529412,0.000000 ),
    ( 0.803922,0.525490,0.000000 ),
    ( 0.803922,0.521569,0.000000 ),
    ( 0.803922,0.517647,0.000000 ),
    ( 0.803922,0.513725,0.000000 ),
    ( 0.803922,0.509804,0.000000 ),
    ( 0.803922,0.505882,0.000000 ),
    ( 0.803922,0.501961,0.000000 ),
    ( 0.803922,0.478431,0.000000 ),
    ( 0.803922,0.470588,0.000000 ),
    ( 0.803922,0.462745,0.000000 ),
    ( 0.803922,0.454902,0.000000 ),
    ( 0.803922,0.447059,0.000000 ),
    ( 0.803922,0.439216,0.000000 ),
    ( 0.803922,0.431373,0.000000 ),
    ( 0.803922,0.423529,0.000000 ),
    ( 0.803922,0.415686,0.000000 ),
    ( 0.803922,0.407843,0.000000 ),
    ( 0.803922,0.400000,0.000000 ),
    ( 0.803922,0.392157,0.000000 ),
    ( 0.803922,0.384314,0.000000 ),
    ( 0.803922,0.376471,0.000000 ),
    ( 0.803922,0.368627,0.000000 ),
    ( 0.803922,0.360784,0.000000 ),
    ( 0.803922,0.301961,0.000000 ),
    ( 0.803922,0.286275,0.000000 ),
    ( 0.803922,0.270588,0.000000 ),
    ( 0.803922,0.254902,0.000000 ),
    ( 0.803922,0.239216,0.000000 ),
    ( 0.803922,0.223529,0.000000 ),
    ( 0.803922,0.207843,0.000000 ),
    ( 0.803922,0.192157,0.000000 ),
    ( 0.803922,0.176471,0.000000 ),
    ( 0.803922,0.160784,0.000000 ),
    ( 0.803922,0.145098,0.000000 ),
    ( 0.803922,0.129412,0.000000 ),
    ( 0.803922,0.113725,0.000000 ),
    ( 0.803922,0.098039,0.000000 ),
    ( 0.803922,0.074510,0.000000 ),
    ( 0.803922,0.000000,0.000000 )
  ]

TIMERID_RESIZE = 100


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
field/property) and initialized via a call to Init(), which calls
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

GetCurDataSet()
  If GetDataSetDisplayMode() returns '' (not 'selected' or 'multi') this
  method returns the name of the current dataset

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

GetSpecialDataSetTypes()
  Extensions must override to provide a list of special categories/types
  of datasets that can be displayed.  Right now this is limited to
  'bank' and 'tally'.

GetTitle()
  Must be overridden by extensions to provide a nice label for the widget.

GetToolButtonDefs()
  Can be overridden by extensions to define additional buttons to appear
  on the WidgetContainer toolbar.  The return value is a list of
  ( icon_name, tip_text, handler ) triples.  Refer to the section on
  Icons below for an explanation of icon names.

GetUsesScaleAndCmap()
  Must be overridden by extensions to specify whether not the widget
  uses user-assigned scale and cmap on the DataRangeDialog.

_InitUI()
  Must be implemented by extensions to create any necessary UI components.
  Failure to implement this method results in an exception.

_LoadDataModel()
  Must be implemented by extensions to initialize local fields and properties
  once the DataModel has been established.  When this method is called from
  HandleStateChange(), the *state* field has been populated.  The preferred
  means of obtaining the DataModel object is State.FindDataModel( self.state ).

_OnFindMinMax()
  This is a placeholder event handling method for widgets that define
  "Find Maximum" and "Find Minimum" pullright menus for the widget menu.  The
  implementation here is a noop, but extensions can override to call one of the
  support methods _OnFindMinMax{Channel,MultiDataSet,Pin}().

_OnSize()
  Event handler for a window resize.

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

_CreateLegendBitmap()
  Provides a legend wx.Bitmap using a Legend3 instance.

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

_OnFindMinMaxChannel()
  Handles 'channel' dataset mininum/maximum processing.  Calls
  self.data.FindChannelMinMaxValue() and FireStateChange().

_OnFindMinMaxMultiDataSets()
  Handles 'detector' multiple datasets minimum/maximum processing.  Calls
  self.data.FindMultiDataSetMinMaxValue() and FireStateChange().

_OnFindMinMaxPin()
  Handles 'pin' dataset minimum/maximum processing.  Calls
  self.data.FindPinMinMaxValue() and FireStateChange().

_OnFindMinMaxTally()
  Handles 'tally' dataset minimum/maximum processing.  Calls
  self.data.FindTallyMinMaxValue() and FireStateChange().

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

  logger_ = logging.getLogger( 'widget' )


#		-- Class Initialization
#		--

#  cm.register_cmap(
#      'spectrum',
#       colors.LinearSegmentedColormap.
#           from_list( 'spectrum', SPECTRUM_COLORS )
#           #from_list( SPECTRUM_COLORS, N = len( SPECTRUM_COLORS ) )
#       )
  colormaps.register_colormaps()


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
    """
"""
#		-- Assert on container.state, container.state.dataModelMgr
#		--
    assert \
        container is not None and hasattr( container, 'state' ) and \
	getattr( container, 'state' ) is not None, \
	'Widget container.state is not a valid State instance'
    assert container.state.GetDataModelMgr() is not None, \
        'State.dataModelMgr is not have a valid DataModelMgr instance'

#		-- Plow on
    super( Widget, self ).__init__( container, id )

    self.busy = False
    self.busyLock = threading.RLock()
    #self.busyCursor = None
    self.colormapName = DEFAULT_colormap
    self.container = container
    self.customDataRange = None
    self.dmgr = container.state.GetDataModelMgr()
    self.isLoading = False
    self.logger = Widget.logger_
    self.precisionDigits = DEFAULT_precisionDigits
    self.precisionMode = DEFAULT_precisionMode
    self.scaleType = DEFAULT_scaleType
    self.state = container.state

    self.dataRangeDialog = None
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
    self.busyLock.acquire()
    try:
      if not self.busy:
        self.busy = True
        self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
        self.container.led.Update()
    finally:
      self.busyLock.release()
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
    self.busyLock.acquire()
    try:
      if self.busy:
        self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
        self.container.led.Update()
        self.busy = False
    finally:
      self.busyLock.release()
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
    #limits = ( 280, 6, 1280, 32 )
##    limits = ( 280, 6, 1280, 32, 2560, 64, 3000, 92 )
##    if display_wd >= limits[ 6 ]:
##      size = limits[ 7 ]
##    elif display_wd >= limits[ 4 ]:
##      size = limits[ 5 ]
    limits = ( 280, 6, 3840, 96 )
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
    return  size
  #end _CalcFontSize


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateClipboardData()			-
  #----------------------------------------------------------------------
#  def _CreateClipboardData( self, cur_selection_flag = False, all_states = False ):
#    """Method that should be overridden by subclasses to create a text
#representation of the data displayed.  This implementation returns None.
#Note what determines the selection is up to the subclass.
#
#@param  cur_selection_flag  if True, only the current selection is copied
#@return			text to copy to the clipboard
#"""
#    return  None
#  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateClipboardData()			-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Method that should be overridden by subclasses to create a text
representation of the data displayed.  This implementation returns None.
Note what determines the selection is up to the subclass.

@param  mode		one of the following or anything a widget wishes
			to define
    'displayed'            - all data displayed
    'selected'             - current selection
    'selected_all_axials'  - current selection across all axials
    'selected_all_states'  - current selection across all states
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
  #	METHOD:		Widget._CreateLegendBitmap()			-
  #----------------------------------------------------------------------
  def _CreateLegendBitmap(
      self, value_range,
      font_size = 10,
      mapper = None,
      ntick_values = 10,
      scale_type = 'linear',
      title = None
      ):
    """Instantiates ``widget.Legend3`` to create a wx.Bitmap.
    Args:
	value_range (tuple): range_min, range_max, data_min, data_max
        scalar_map (matplotlib.cm.ScalarMappable): instance used to map
	    values to colors and determine the range and scale type
	mapper (matplotlib.cm.ScalarMappable): optional pre-built mapper,
	    if None one is created basd on value_range and scale_type; Note
	    the ``norm`` property determines scale_type, overriding the
	    ``scale_type`` parameter if provided
        ntick_values (int): number of values to show as ticks
	font_size (int): font point size
	title (str): optional title under legend
	scale_type (str): 'linear' or 'log'
"""
    bg_color = self.GetBackgroundColour() \
        if Config.GetOSName() == 'linux' else None

    return  \
    Legend3()(
        value_range,
	bg_color = bg_color,
	font_size = font_size,
	mapper = mapper,
	ntick_values = ntick_values,
	scale_type = scale_type,
	title = title
	)
  #end _CreateLegendBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateLegendBitmap_1()			-
  #----------------------------------------------------------------------
  def _CreateLegendBitmap_1(
      self, value_range,
      font_size = 16, gray = False, scale_type = 'linear', title = None
      ):
    """Instantiates ``widget.Legend3`` to create a wx.Bitmap.
    Args:
        value_range (tuple): min, max
    Keyword Args:
	font_size (int): font point size
	gray (boolean): True to convert to gray scale
	scale_type (str): 'linear', 'log'
	title (str): title string
"""
    bg_color = self.GetBackgroundColour() \
        if Config.GetOSName() == 'linux' else None

    return \
    Legend3()(
        Widget.GetColorTuple, value_range, 10, font_size,
	gray, title, bg_color
	)
  #end _CreateLegendBitmap_1


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateLegendPilImage()			-
  #----------------------------------------------------------------------
#  def _CreateLegendPilImage(
#      self, value_range,
#      font_size = 16, gray = False, title = None
#      ):
#    """For now this is linear only.
#@param  value_range	( min, max )
#"""
#    return \
#    Legend3()( Widget.GetColorTuple, value_range, 10, font_size, gray, title )
#  #end _CreateLegendPilImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """List of (label, handler) pairs to present in a menu.
This implementation creates the Copy Data and Copy Image items, so
subclasses must override this calling super._CreateMenuDef() to insert
or append items.
@return			[ ( label, handler ), ... ]
"""
    return \
      [
	{ 'label': 'Copy Displayed Data',
	  'handler':functools.partial( self._OnCopyData, 'displayed' ) },
	{ 'label': 'Copy Selected Data',
	  'handler': functools.partial( self._OnCopyData, 'selected' ) },
        { 'label': 'Copy Image', 'handler': self._OnCopyImage },
	{ 'label': '-' },
        { 'label': 'Edit Data Scale...', 'handler': self._OnCustomScale },
      ]
#    return \
#      [
#	( 'Copy Displayed Data', functools.partial( self._OnCopyData, False ) ),
#	( 'Copy Selected Data', functools.partial( self._OnCopyData, True ) ),
#        ( 'Copy Image', self._OnCopyImage )
#      ]
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         Widget._CreatePopupMenu()			-
  #----------------------------------------------------------------------
  def _CreatePopupMenu( self ):
    """Populates self.popupMenu from self.GetMenuDef().
Must be called from the UI thread.
"""
    return  self.container._CreateMenuFromDef( None, self.GetMenuDef() )
  #end _CreatePopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		Widget.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path, bgcolor = None, hilite = False ):
    """
Placeholder for widget implementations to create a PNG image.
The default implementation returns None.
@param  file_path	path to file if the widget creates the image
@param  bgcolor		background color tupe ( r, g, b, a ), where None
			means transparent
@return			file_path or None if not processed
"""
    #return  wx.EmptyImage( 400, 300 )
    return  None
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		Widget._FindFirstDataSet()			-
  #----------------------------------------------------------------------
  def _FindFirstDataSet( self, qds_name_in = None ):
    """Finds the first dataset available from the types supported by this.
@param  qds_name_in	optional dataset name (DataSetName instance) to try
			first for a match against supported types
@return			DataSetName instance or None
"""
    qds_name = None
    if self.dmgr.HasData():
      ds_types = self.GetDataSetTypes()
      if qds_name_in and self.dmgr.GetDataSetType( qds_name_in ) in ds_types:
        qds_name = qds_name_in
      else:
        for t in ds_types:
	  qds_name_in = self.dmgr.GetFirstDataSet( t )
	  if qds_name_in:
	    qds_name = qds_name_in
	    break
	#end for
      #end if-else ds_name_in in ds_types
    #end if self.dmgr

    return  qds_name
  #end _FindFirstDataSet


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
  #	METHOD:		Widget._GetCurAssemblyIndex()			-
  #----------------------------------------------------------------------
  def _GetCurAssemblyIndex( self ):
    """Retrieves the property value 'assemblyAddr' or 'detectorAddr',
returning -1 if neither found.
@return			'assemblyAddr' or 'detectorAddr' value or -1
"""
    ndx = \
        self.assemblyAddr[ 0 ]  if hasattr( self, 'assemblyAddr' ) else \
	self.detectorAddr[ 0 ]  if hasattr( self, 'detectorAddr' ) else \
	-1
    return  ndx
  #end _GetCurAssemblyIndex


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetCurDataSet()				-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """This implementation tries to infer the name from an attribute
named 'curDataSet', 'channelDataSet', or 'pinDataSet', in that order,
only if GetDataSetDisplayMode is ''.  Otherwise, None is returned.
Subclasses should override as needed.
@return		current dataset name (DataSetName instance)
		if dataSetDisplayMode is ''
"""
    qds_name = None
    if not self.GetDataSetDisplayMode():
      for attr in ( 'curDataSet', 'channelDataSet', 'pinDataSet' ):
        if hasattr( self, attr ):
          qds_name = getattr( self, attr )
	  break
      #end for attr
    #end if not

    return  qds_name
  #end GetCurDataSet


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


#  #----------------------------------------------------------------------
#  #	METHOD:		Widget.GetDataSetPropertyNames()		-
#  #----------------------------------------------------------------------
#  def GetDataSetPropertyNames( self ):
#    """Default list of dataset property names, to be overridden by subclasses
#to append to what's returned here.
#@return			list of property names, [ 'curDataSet' ] defined
#			here
#"""
#    return  [ 'curDataSet' ]
#  #end GetDataSetPropertyNames


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
  #	METHOD:		Widget.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, assemblyIndex, axialValue, and timeValue changes are
captured.
"""
    locks = set([
        STATE_CHANGE_assemblyIndex,
        STATE_CHANGE_axialValue,
        STATE_CHANGE_scale,
        STATE_CHANGE_timeValue
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
  def GetMenuDef( self ):
    """List of (label, handler) pairs to present in a menu.
Lazily created here via a call to _CreateMenuDef(), which should be overridden 
by subclasses.
@return			[ ( label, handler ), ... ]
"""
    if self.menuDef is None:
      self.menuDef = self._CreateMenuDef()
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
  def GetSelectedDataSetName( self, ds_type = None ):
    """
@param  ds_type		dataset type/category
"""
    return \
        'Selected ' + ds_type + ' dataset'  if ds_type else \
	NAME_selectedDataSet
    #return  'Selected ' + ds_type + ' dataset'
  #end GetSelectedDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetSpecialDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetSpecialDataSetTypes( self ):
    """Accessor specifying the types of special datasets which can be
processed in this widget.  For now this is limited to 'bank' and 'tally'.
This implementation returns an empty list.

@return			list of dataset types, cannot be None
"""
    return  []
  #end GetSpecialDataSetTypes


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
  def GetToolButtonDefs( self ):
    """List of (icon_name, tip, handler) triples from which to build tool bar
buttons.
Returning None means no tool buttons, which is the default implemented here.
@return			[ ( icon_name, tip, handler ), ... ]
"""
    return  None
  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetUsesScaleAndCmap()			-
  #----------------------------------------------------------------------
  def GetUsesScaleAndCmap( self ):
    """Specifies whether or not this widget uses scale and colormap
settings in the DataRangeDialog.  Extensions should override to return False
if appropriate.
    Returns:
        boolean: True
"""
    return  True
  #end GetUsesScaleAndCmap


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
 
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModelMgr
    if (reason & load_mask) > 0:
      reason = self.state.\
          ResolveLocks( STATE_CHANGE_ALL, self.container.eventLocks )
      self.logger.debug( 'calling _LoadDataModel()' )
      self._LoadDataModel( reason )

    update_args = self.state.CreateUpdateArgs( reason )

    if len( update_args ) > 0:
      wx.CallAfter( self.UpdateState, **update_args )
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		Widget.Init()					-
  #----------------------------------------------------------------------
  def Init( self, new_state = None ):
    if new_state is not None:
      self.state = new_state

    self.HandleStateChange( STATE_CHANGE_init )
  #end Init


  #----------------------------------------------------------------------
  #	METHOD:		Widget._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Implementation classes must override.
"""
    raise  Exception( "subclasses must implement" )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Widget.Is3D()					-
  #----------------------------------------------------------------------
  def Is3D( self ):
    """
@return			False
"""
    return  False
  #end Is3D


  #----------------------------------------------------------------------
  #	METHOD:		Widget.IsBusy()					-
  #----------------------------------------------------------------------
  def IsBusy( self ):
    #return  self.busy
    st = False
    self.busyLock.acquire()
    try:
      st = self.busy
    finally:
      self.busyLock.release()
    return  st
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
  def _LoadDataModel( self, reason ):
    """Must be implemented by extensions.
"""
    #self.dmgr = State.FindDataModelMgr( self.state )
    pass
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Widget.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  Subclasses should override calling this
method via super.SaveProps() at the end.
@param  props_dict	dict object from which to deserialize properties
"""
    self.isLoading = True
    try:
      for k in (
	  'colormapName',
          'customDataRange', 'precisionDigits', 'precisionMode',
	  'scaleType'
	  ):
        if k in props_dict:
          setattr( self, k, props_dict[ k ] )

      for k in ( 'axialValue', 'curDataSet', 'tallyAddr' ):
        if k in props_dict and hasattr( self, k ):
          setattr( self, k, props_dict[ k ] )

      if 'eventLocks' in props_dict:
#		-- Must convert keys to ints
        locks_in = props_dict[ 'eventLocks' ]
        locks_out = {}
        for k in locks_in:
          i = int( k )
	  locks_out[ i ] = locks_in[ k ]
        #end for

        self.container.SetEventLocks( locks_out )

    finally:
      self.isLoading = False
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
  def _OnCopyData( self, mode, ev ):
    """Handler for a Copy Data action.  Calls _CreateClipboardData() to get
the data as text.  If the text is not None or empty, this method copies it to
the clipboard.
"""
    ev.Skip()

    data_text = self._CreateClipboardData( mode )
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
  #	METHOD:		Widget._OnCustomScale()				-
  #----------------------------------------------------------------------
  def _OnCustomScale( self, ev ):
    """Handler for a setting the custom scale.
Must be called from the UI thread.
"""
    ev.Skip()

    if self.dataRangeDialog is None:
      self.dataRangeDialog = DataRangeDialog(
          self, wx.ID_ANY,
	  bitmap_func = Widget.GetBitmap,
	  enable_scale_and_cmap = self.GetUsesScaleAndCmap()
	  )

    changed = False
    self.dataRangeDialog.ShowModal(
        range_in = self.customDataRange,
	digits_in = self.precisionDigits,
	mode_in = self.precisionMode,
	scale_type_in = self.scaleType,
	colormap_in = self.colormapName
	)

    new_colormap = self.dataRangeDialog.GetColormap()
    if new_colormap != self.colormapName:
      self.colormapName = new_colormap
      changed = True

    new_range = self.dataRangeDialog.GetRange()
    if new_range[ 0 ] > new_range[ 1 ]:
      wx.MessageBox(
          'Minimum cannot be greater than maximum', 'Set Data Scale',
	  wx.ICON_ERROR | wx.OK_DEFAULT
	  )
    elif new_range != self.customDataRange:
      self.customDataRange = new_range
      changed = True

    new_digits = self.dataRangeDialog.GetPrecisionDigits()
    if new_digits != self.precisionDigits:
      self.precisionDigits = new_digits
      changed = True

    new_mode = self.dataRangeDialog.GetPrecisionMode()
    if new_mode != self.precisionMode:
      self.precisionMode = new_mode
      changed = True

    new_scale_type = self.dataRangeDialog.GetScaleType()
    if new_scale_type != self.scaleType:
      self.scaleType = new_scale_type
      changed = True

    if changed:
      self.Redraw()
  #end _OnCustomScale


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMinMax()				-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Placeholder event handling method for widgets that define a "Find
"Maximum" or "Find Minimum" pullright for the widget menu.
This implementation is a noop.
Subclasses should override to call _OnFindMinMaxChannel(),
_OnFindMinMaxMultiDataSets(), _OnFindMinMaxPin(), or _OnFindMinMaxTally().
@param  mode		'min' or 'max', defaulting to the latter
@param  all_states_flag	True for all states, False for current state
@param  all_assy_flag	True to search all assemblies, False for current
@param  ev		menu event
"""
    pass
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMinMaxChannel()			-
  #----------------------------------------------------------------------
  def _OnFindMinMaxChannel(
      self, mode, qds_name,
      all_states_flag = True, all_assy_flag = True
      ):
    """Handles 'channel' dataset min/max processing, resulting in a call to
FireStateChange() with assembly_addr, axial_value, state_index, and/or
sub_addr changes.
Note: if all_states_flag is false, self must have a 'timeValue' attribute.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  all_states_flag	True for all states, False for current state
@param  all_assy_flag	True to search all assemblies, False for current
"""
    update_args = {}

    if qds_name:
      update_args = self.dmgr.FindChannelMinMaxValue(
	  mode, qds_name,
	  -1 if all_states_flag else self.timeValue,
	  -1 if all_assy_flag else self._GetCurAssemblyIndex(),
	  self, self.state.weightsMode == 'on'
          )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMinMaxChannel


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMinMaxMultiDataSets()		-
  #----------------------------------------------------------------------
  def _OnFindMinMaxMultiDataSets(
      self, mode, all_states_flag, all_assy_flag,
      *qds_names
      ):
    """Handles multi-dataset dataset maximum processing, resulting in a call to
FireStateChange() with assembly_addr, axial_value, state_index,
and/or sub_addr changes.
Note: if all_states_flag is false, self must have a 'timeValue' attribute.
@param  mode		'min' or 'max', defaulting to the latter
@param  all_states_flag	True for all states, False for current state
@param  all_assy_flag	True to search all assemblies, False for current
@param  qds_names	dataset names to search, DataSetName instances
"""
    update_args = {}

    if qds_names:
      update_args = self.dmgr.FindMultiDataSetMinMaxValue(
	  mode,
	  -1 if all_states_flag else self.timeValue,
	  -1 if all_assy_flag else self._GetCurAssemblyIndex(),
	  self, *qds_names
	  )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMinMaxMultiDataSets


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMinMaxPin()			-
  #----------------------------------------------------------------------
  def _OnFindMinMaxPin(
      self, mode, qds_name, all_states_flag = True, all_assy_flag = True
      ):
    """Handles 'pin' dataset min/max processing, resulting in a call to
FireStateChange() with assembly_addr, axial_value, state_index, and/or
sub_addr changes.
Note: if all_states_flag is false, self must have a 'timeValue' attribute.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  all_states_flag	True for all states, False for current state
@param  all_assy_flag	True to search all assemblies, False for current
"""
    update_args = {}

    if qds_name:
      update_args = self.dmgr.FindPinMinMaxValue(
	  mode, qds_name,
	  -1 if all_states_flag else self.timeValue,
	  -1 if all_assy_flag else self._GetCurAssemblyIndex(),
	  self, self.state.weightsMode == 'on'
          )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMinMaxPin


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnFindMinMaxTally()			-
  #----------------------------------------------------------------------
  def _OnFindMinMaxTally(
      self, mode, tally_addr = True, all_states_flag = True,
      ds_expr = None, radius_start_ndx = 0
      ):
    """Handles 'tally' dataset min/max processing, resulting in a call to
FireStateChange() with axial_value, state_index, and/or tally_addr changes.
Note: if all_states_flag is false, self must have a 'timeValue' attribute.
@param  mode		'min' or 'max', defaulting to the latter
@param  tally_addr	TallyAddress instance
@param  all_states_flag	True for all states, False for current state
@param  ds_expr		expression to apply to dataset min/max search,
			if None, tally_addr.multIndex and .statIndex will
			be applied in DataModel.FindTallyMinMaxValueAddr()
@param  radius_start_ndx  starting index of range range of validity
"""
    update_args = {}

    if tally_addr:
      update_args = self.dmgr.FindTallyMinMaxValue(
	  mode, tally_addr,
	  -1 if all_states_flag else self.timeValue,
	  self, ds_expr, radius_start_ndx
          )

    if update_args:
      self.FireStateChange( **update_args )
  #end _OnFindMinMaxTally


  #----------------------------------------------------------------------
  #	METHOD:		Widget._OnSize()				-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """Noop.
"""
    pass
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		Widget.Redraw()					-
  #----------------------------------------------------------------------
  def Redraw( self ):
    """Calls _OnSize( None )
"""
    self._OnSize( None )
  #end Redraw


  #----------------------------------------------------------------------
  #	METHOD:		Widget._ResolveDataRange()			-
  #----------------------------------------------------------------------
  def _ResolveDataRange(
      self, qds_name, time_value,
      ds_expr = None,
      apply_custom_range = True
      ):
    """Calls self.dmgr.GetRange() if necessary to replace NaN values in
customDataRange.
@param  qds_name	name of dataset, DataSetName instance
#@param  state_ndx	explicit state index or -1 for all states
@param  time_value	explicit time value or -1 for all statepoints
@param  ds_expr		optional reference expression to apply to the dataset
@param  apply_custom_range  True to apply self.customDataRange if it is defined
@return			( range_min, range_max, data_min, data_max )
"""
#    ds_range = [ NAN, NAN ] \
#        if self.customDataRange is None else \
#	list( self.customDataRange )
    ds_range = \
        list( self.customDataRange ) \
	if apply_custom_range and self.customDataRange is not None else \
	[ NAN, NAN ]
    calc_range = self.dmgr.GetRange( qds_name, time_value, ds_expr )
    if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] ):
      #calc_range = self.dmgr.GetRange( qds_name, time_value, ds_expr )
      if calc_range:
        for i in xrange( len( calc_range ) ):
          if math.isnan( ds_range[ i ] ):
            ds_range[ i ] = calc_range[ i ]

    if math.isnan( ds_range[ 1 ] ):
      ds_range[ 1 ] = 10.0
    if math.isnan( ds_range[ 0 ] ):
      ds_range[ 0 ] = -10.0

    if calc_range:
      ds_range.append( calc_range[ 0 ] )
      ds_range.append( calc_range[ 1 ] )
    else:
      ds_range.append( -10.0 )
      ds_range.append( 10.0 )

    if ds_range[ 0 ] >= ds_range[ 1 ]:
      span = abs( ds_range[ 0 ] ) * 0.1
      ds_range[ 1 ] = ds_range[ 0 ] + span
      ds_range[ 0 ] -= span

    return  tuple( ds_range )
  #end _ResolveDataRange


  #----------------------------------------------------------------------
  #	METHOD:		Widget._ResolveScaleType()			-
  #----------------------------------------------------------------------
  def _ResolveScaleType( self, qds_name ):
    """
"""
    return \
        self.scaleType  if self.scaleType != DEFAULT_scaleType else \
	'linear'  if qds_name is None else \
        self.dmgr.GetDataSetScaleType( qds_name )
  #end _ResolveScaleType


  #----------------------------------------------------------------------
  #	METHOD:		Widget.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    for k in (
	'colormapName',
        'customDataRange', 'precisionDigits', 'precisionMode',
	'scaleType'
	):
      props_dict[ k ] = getattr( self, k )

    for k in ( 'axialValue', 'tallyAddr' ):
      if hasattr( self, k ):
        props_dict[ k ] = getattr( self, k )

    for k in ( 'curDataSet', ):
      if hasattr( self, k ):
	if for_drag:
          qds_name = getattr( self, k )
	else:
          qds_name = self.dmgr.RevertIfDerivedDataSet( getattr( self, k ) )
#t        props_dict[ k ] = qds_name.name  if qds_name is not None else  ''
	if qds_name:
	  props_dict[ k ] = qds_name.tojson()

    props_dict[ 'eventLocks' ] = self.container.GetEventLocks()
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
  def SetState( self, state = None ):
    """
@deprecated  call Init()
"""
    self.Init( state )
    #self.state = state
    #self.HandleStateChange( STATE_CHANGE_init )
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
  #	METHOD:		Widget.CalcPointSize()				-
  #----------------------------------------------------------------------
  @staticmethod
  def CalcPointSize( gc, pixel_size ):
    """
@param  gc		wx.GraphicsContext instance
@param  pixel_size	pixel size
@return			point size for the given number of pixels
"""
    if isinstance( gc, wx.GraphicsContext ):
      pts_per_pixel = 72.0 / gc.GetDPI()[ 0 ]
    else:
      pts_per_pixel = 72.0 / gc.GetPPI()[ 0 ]
    return  int( pts_per_pixel * pixel_size )
  #end CalcPointSize


  #----------------------------------------------------------------------
  #	METHOD:		Widget.CheckSingleMenuItem()			-
  #----------------------------------------------------------------------
  @staticmethod
  def CheckSingleMenuItem( menu, checked_item ):
    """Calls recursively with DFS walk through menus and items.
"""
#    if checked_item is not None:
#      checked_id = checked_item.GetId()
#      checked_label = checked_item.GetItemLabelText()
#    else:
#      checked_id = -1
#      checked_label = ''

    for i in range( menu.GetMenuItemCount() ):
      item = menu.FindItemByPosition( i )
      sub_menu = item.GetSubMenu()
      if sub_menu is not None:
        Widget.CheckSingleMenuItem( sub_menu, checked_item )
      elif item.GetKind() == wx.ITEM_CHECK:
	if item.GetId() != checked_item.GetId():
	  item.Check( False )
	elif not item.IsChecked():
	  item.Check( True )
    #end for
  #end CheckSingleMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		Widget.ClearMenu()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ClearMenu( menu, excludes = [] ):
    """Removes all items, relying on wx.Menu.DestroyItem() on removing
submenus.
"""
    ndx = 0
    while menu.GetMenuItemCount() > ndx:
      item = menu.FindItemByPosition( ndx )
      if not excludes or item.GetItemLabelText() not in excludes:
        menu.DestroyItem( item )
      else:
        ndx += 1
  #end ClearMenu


  #----------------------------------------------------------------------
  #	METHOD:		Widget.CopyFont()				-
  #----------------------------------------------------------------------
  @staticmethod
  def CopyFont(
      font,
      family = None, pt_size = None, style = None, weight = None
      ):
    """Makes a copy of the font.
@param  font		wx.Font instance
@param  family		optional wx.FontFamily, None uses font.GetFamily()
@param  pt_size		optional point size, None uses font.GetPointSize()
@param  style		optional wx.FontStyle, None uses font.GetStyle()
@param  weight		optional wx.FontWeight, None uses font.GetStyle()
@return			new wx.Font instance
"""
    new_font = wx.Font(
	pt_size  if pt_size is not None else  font.GetPointSize(),
	family  if family is not None else  font.GetFamily(),
	style  if style is not None else  font.GetStyle(),
	weight  if weight is not None else  font.GetWeight()
        )
    return  new_font
  #end CopyFont


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
  def GetColorTuple( value, max_value, alpha = 255, debug = False, gray = False ):
    """
http://www.particleincell.com/blog/2014/colormap/
@param  value		value offset
@param  max_value	max value offset
@param  alpha		alpha value [0,255]
@param  gray		make grayscale
@return			( red, green, blue, alpha )
"""
    if debug and Widget.logger_.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'value=%f, max_value=%f', value, max_value )

    use_value = min( value, max_value )

    if gray:
      if max_value <= 0.0:
        incr = 0
      else:
        incr = min( 200, int( math.floor( 200.0 * use_value / max_value ) ) )
      f = 55 + incr
      color = ( f, f, f, alpha )

    else:
      f = float( use_value ) / max_value  if max_value > 0.0  else 0.0
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

      if debug and Widget.logger_.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
            'f=%f, a=%f, x=%f, y=%f, rgb=(%d,%d,%d)',
	    f, a, x, y, red, green, blue
	    )

      color = ( red, green, blue, alpha )
    #end if-else gray

    return  color
  #end GetColorTuple


  #----------------------------------------------------------------------
  #	METHOD:		Widget.GetColorTuple_1()			-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColorTuple_1( value, max_value, alpha = 255, debug = False, gray = False ):
    """
http://www.particleincell.com/blog/2014/colormap/
@param  value		value offset
@param  max_value	max value offset
@param  alpha		alpha value [0,255]
@param  gray		make grayscale
@return			( red, green, blue, alpha )
"""
    if debug and Widget.logger_.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'value=%f, max_value=%f', value, max_value )

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

    if debug and Widget.logger_.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          'f=%f, a=%f, x=%f, y=%f, rgb=(%d,%d,%d)',
	  f, a, x, y, red, green, blue
	  )

    color = ( red, green, blue, alpha )
    if gray:
      color = Widget.ToGray( *color )
    return  color
  #end GetColorTuple_1


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


  #----------------------------------------------------------------------
  #	METHOD:		Widget.IsMainThread()				-
  #----------------------------------------------------------------------
  @staticmethod
  def IsMainThread():
    return  threading.current_thread().name == 'MainThread'
  #end IsMainThread


  #----------------------------------------------------------------------
  #	METHOD:		Widget.NormalizeAngle()				-
  #----------------------------------------------------------------------
  @staticmethod
  def NormalizeAngle( angle_rad ):
    """Normalizes angle to range (-180,180].
"""
    return  angle_rad - TWO_PI  if angle_rad > math.pi else  angle_rad
  #end NormalizeAngle


  #----------------------------------------------------------------------
  #	METHOD:		Widget.ToGray()					-
  #----------------------------------------------------------------------
  @staticmethod
  def ToGray( r, g, b, alpha = 255 ):
    """Returns a grayscale equivalent of the color.
"""
    gray = int( math.ceil( (r * 0.2989) + (g * 0.5870) + (b * 0.1140) ) )
    return  ( gray, gray, gray, alpha )
  #end ToGray
#end Widget
