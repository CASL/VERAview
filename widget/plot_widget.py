#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		plot_widget.py					-
#	HISTORY:							-
#		2018-08-21	leerw@ornl.gov				-
#	  Added _IsTimeReplot().
#		2018-08-20	leerw@ornl.gov				-
#	  Added _DoUpdateRedraw() hook.
#		2018-08-18	leerw@ornl.gov				-
#	  Added ref_axis2 param and self.cursorLine2.
#		2018-02-17	leerw@ornl.gov				-
#	  Using a wx.Timer to manage resize events to avoid updating for
#	  transient sizes.
#		2017-05-05	leerw@ornl.gov				-
#	  Modified LoadDataModel() to process the reason param.
#		2017-02-03	leerw@ornl.gov				-
#	  Adding white background image save option.
#		2017-01-26	leerw@ornl.gov				-
#	  Added PLOT_MODES.
#	  Hiding cursorLine in CreatePrintImage().
#		2016-12-14	leerw@ornl.gov				-
#	  Processing dataSetSelections in {Load,Save}Props().
#		2016-12-10	leerw@ornl.gov				-
#	  Adapting to new DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-20	leerw@ornl.gov				-
#	  No longer calling UpdateState() in _LoadDataModel() since
#	  Widget.HandleStateChange() now does so.
#		2016-06-30	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2016-01-23	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2015-06-20	leerw@ornl.gov				-
#	  Generalization of the all the plot widgets.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-04-22	leerw@ornl.gov				-
#	  Showing currently selected assembly.
#		2015-04-04	leerw@ornl.gov				-
#		2015-04-02	leerw@ornl.gov				-
#		2015-03-20	leerw@ornl.gov				-
# 	  Added tooltip.
#		2015-02-11	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, sys, tempfile, time, traceback
import numpy as np
#import pdb # pdb.set_trace()

try:
  import wx
#  import wx.lib.delayedresult as wxlibdr
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
#  import matplotlib.pyplot as plt
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

try:
  from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
  from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

from event.state import *

from .widget import *
from .widgetcontainer import *


PLOT_COLORS = [ 'b', 'r', 'g', 'm', 'c' ]
#        b: blue
#        g: green
#        r: red
#        c: cyan
#        m: magenta
#        y: yellow
#        k: black
#        w: white
#	-: solid
#	--: dashed
#	:: dotted
#http://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.plot.html#matplotlib.axes.Axes.plot

PLOT_MODES = (
  'b-', 'r-', 'g-', 'm-', 'c-',
  'b--', 'r--', 'g--', 'm--', 'c--',
  'b:', 'r:', 'g:', 'm:', 'c:'
  )


#------------------------------------------------------------------------
#	CLASS:		PlotWidget					-
#------------------------------------------------------------------------
class PlotWidget( Widget ):
  """Base class for plot widgets based on matplotlib.

Widget Framework
================

Fields/Properties
-----------------

ax
  primary matplotlib.axes.Axes instance

axline
  horizontal or vertical matplotlib.lines.Line2D instance used to indicate
  the current event state

canvas
  FigureCanvas (FigureCanvasWxAgg) instance in which the *fig* is rendered

cursor
  ( x, y ) plot location following the mouse

cursorLine
  horizontal or vertical matplotlib.lines.Line2D instance following the mouse

cursorLine2
  horizontal or vertical matplotlib.lines.Line2D instance following the mouse
  for the non-primary axis

data
  DataModel reference, getter is GetData()

fig
  matplotlib.figure.Figure instance

refAxis
  reference or non-magnitude axis, either 'y' (default) or 'x'

#stateIndex
  #0-based state point index, getter is GetStateIndex()

timeValue
  value of current time dataset

Framework Methods
-----------------

_CreateToolTipText()
  Should be implemented by extensions to create a tool tip based on the plot
  location returned in the event, ev.xdata when *refAxis* == 'x' and ev.ydata
  when *refAxis* == 'y'.

_DoUpdatePlot()
  Called from _UpdatePlotImpl(), the implementation here creates a grid on
  *ax*, but extensions must override, calling super._DoUpdatePlot() to
  configure axes with labels and limits, create plots, add a legend, add a
  title, and/or set *axline*.

_InitAxes()
  Called from _InitUI(), this default implementation creates a single axis, the
  *ax* property.  Extensions should override to create axes and layout the plot
  as desired, calling Figure methods add_axes() or add_subplot().

_InitUI()
  Widget framework method implementation that creates the Figure (*fig*),
  calls _InitAxes(), creates the Canvas (*canvas*), and binds matplotlib
  and wxPython event handlers.

_IsTimeReplot()
  True to replot on time change, False to redraw

_LoadDataModel()
  Widget framework method implementation that calls _LoadDataModelValues() and
  then UpdateState(), the latter on the event UI thread.

_LoadDataModelValues()
  Must be overridden by extensions to update event state properties and return
  the changes.

_OnMplMouseRelease()
  Matplotlib event handler that checks for the right button (ev.button == 3) to
  pass onto wxPython event handling for the context menu.  Extensions should
  override this method calling super._OnMplMouseRelease() and processing left
  button (ev.button == 1) events to update local event state properties by
  calling UpdateState() and firing state changes via FireStateChange().

_UpdateDataSetValues()
  Must be overridden by extensions to rebuild plot data arrays after a
  change in dataset selections

UpdateState()
  Implements this Widget framework method by calling _UpdateStateValues().  A
  'redraw' condition (currently does not occur) means the *canvas* must be
  redrawn via self.canvas.redraw().  A 'replot' condition means
  _UpdateDataSetValues() and _UpdatePlot() must be called.

_UpdateStateValues()
  The implementation here handles 'state_index' changes, but extensions should
  override to handle widget-specific event state values, being sure to call
  super._UpdateStateValues().

Support Methods
---------------

"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    """
@param  kwargs
    ref_axis		reference axis 'x' or 'y', defaults to 'y'
    ref_axis2		2nd reference axis 'x' or 'y', defaults to None
    show_cursor		toggle for showing cursor lines, defaults to True
"""

    self.ax = None
    self.axline = None  # axis line representing state
    self.canvas = None
    self.curSize = None
    self.cursor = None
    self.cursorLine = None  # axis line following the cursor
    self.cursorLine2 = None  # axis line following the cursor
    self.fig = None
    self.timer = None
    self.toolbar = None

    self.callbackIds = {}
    #self.isLoaded = False
    self.refAxis = kwargs.get( 'ref_axis', 'y' )
    self.refAxis2 = kwargs.get( 'ref_axis2' )
    self.showCursor = kwargs.get( 'show_cursor', True )
    #self.stateIndex = -1
    self.timeValue = -1.0
    self.titleFontSize = 16

    super( PlotWidget, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardImage()				-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return			bitmap or None
"""
    bmap = None

    fd, name = tempfile.mkstemp( '.png' )
    try:
      os.close( fd )
      if self.CreatePrintImage( name ):
        bmap = wx.Image( name, wx.BITMAP_TYPE_PNG ).ConvertToBitmap()
    finally:
      os.remove( name )

    return  bmap
  #end _CreateClipboardImage


  #----------------------------------------------------------------------
  #	METHOD:		CreatePrintImage()				-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path, bgcolor = None, hilite = False ):
    """
"""
    result = None

    if self.fig is not None:
      #if wx.IsMainThread():
      if not hilite:
        if self.cursorLine is not None:
          self.cursorLine.set_visible( False )
        if self.cursorLine2 is not None:
          self.cursorLine2.set_visible( False )
        if self.axline is not None:
          self.axline.set_visible( False )
        self._DoUpdateRedraw( False )
	self.canvas.draw()

      if bgcolor and hasattr( bgcolor, '__iter__' ) and len( bgcolor ) >= 3:
	fc = tuple( [ bgcolor[ i ] / 255.0 for i in xrange( 3 ) ] )
      else:
        fc = self.fig.get_facecolor()

# Sleep needed when animating to prevent matplotlib errors generating
# tick marks on Mac.  Some day we must figure out why.  It seems to have
# to do with wxPython and the MainThread.
      time.sleep( 0.5 )
      self.fig.savefig(
          file_path, dpi = 216, format = 'png', orientation = 'landscape',
	  facecolor = fc
	  )
          # dpi = 144
      result = file_path

      #if wx.IsMainThread():
      if not hilite:
        if self.axline is not None:
          self.axline.set_visible( True )
        if self.cursorLine is not None:
          self.cursorLine.set_visible( True )
        if self.cursorLine2 is not None:
          self.cursorLine2.set_visible( True )
        self._DoUpdateRedraw()
        self.canvas.draw()
    #end if

    return  result
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		_CreateToolTipText()				-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		matplotlib mouse motion event
"""
    return  ''
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		_DoUpdatePlot()					-
  #----------------------------------------------------------------------
  def _DoUpdatePlot( self, wd, ht ):
    """Do the work of creating the plot, setting titles and labels,
configuring the grid, plotting, and creating self.axline.  This implementation
calls self.ax.grid() and can be called by subclasses.
"""
    self.ax.grid(
        True, 'both', 'both',
	color = '#c8c8c8', linestyle = ':', linewidth = 1
	)
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_DoUpdateRedraw()				-
  #----------------------------------------------------------------------
  def _DoUpdateRedraw( self, hilite = True ):
    """Update for a redraw only.
"""
    pass
  #end _DoUpdateRedraw


  #----------------------------------------------------------------------
  #	METHOD:		GetStateIndex()					-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		GetTimeValue()					-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """@return		0-based state/time index
"""
    return  self.timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		PlotWidget.GetUsesScaleAndCmap()		-
  #----------------------------------------------------------------------
  def GetUsesScaleAndCmap( self ):
    """
    Returns:
        boolean: False
"""
    return  False
  #end GetUsesScaleAndCmap


  #----------------------------------------------------------------------
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes.  By default creates a single axis 'ax'.
"""
    self.ax = self.fig.add_subplot( 111 )
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self, two_axes = False ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    dpis = wx.ScreenDC().GetPPI()
    size = ( WIDGET_PREF_SIZE[ 0 ] / dpis[ 0 ], WIDGET_PREF_SIZE[ 1 ] / dpis[ 0 ] )
    self.fig = Figure( facecolor = '#ececec', figsize = size, dpi = dpis[ 0 ] )

    self._InitAxes()
#    if two_axes:
#      self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
#      self.ax2 = self.ax.twiny()
#    else:
#      self.ax = self.fig.add_subplot( 111 )
    self.canvas = FigureCanvas( self, -1, self.fig )
    self.canvas.SetMinClientSize( wx.Size( 200, 200 ) )
    self.toolbar = NavigationToolbar( self.canvas )
    #self.toolbar.Realize()
    self.toolbar.SetBackgroundColour( wx.Colour( 236, 236, 236, 255 ) )
    self.toolbar.Show( False )

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.toolbar, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND, 1 )
    sizer.Add( self.canvas, 1, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND, 1 )
    self.SetSizer( sizer )

    self.callbackIds[ 'button_release_event' ] = \
      self.canvas.mpl_connect( 'button_release_event', self._OnMplMouseRelease )
    self.callbackIds[ 'motion_notify_event' ] = \
      self.canvas.mpl_connect( 'motion_notify_event', self._OnMplMouseMotion )

    self.Bind( wx.EVT_CLOSE, self._OnClose )
    self.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    self.Bind( wx.EVT_SIZE, self._OnSize )

    self.timer = wx.Timer( self, TIMERID_RESIZE )
    self.Bind( wx.EVT_TIMER, self._OnTimer )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		IsDataSetScaleCapable()			        -
  #----------------------------------------------------------------------
  def IsDataSetScaleCapable( self ):
    """Returns false.
    Returns:
        bool: False
"""
    return  False
  #end IsDataSetScaleCapable


  #----------------------------------------------------------------------
  #	METHOD:		_IsTimeReplot()					-
  #----------------------------------------------------------------------
  def _IsTimeReplot( self ):
    """Returns True if the widget replots on a time change, False it it
merely redraws.  Defaults to True.  Should be overridden as necessary.
"""
    return  True
  #end _IsTimeReplot


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModel()				-
  #----------------------------------------------------------------------
  def _LoadDataModel( self, reason ):
    """Updates the components for the current model.
xxx need loaded flag set when LoadProps() is called so you don't call
_LoadDataModelValues()
"""
    if not self.isLoading:
      update_args = self._LoadDataModelValues( reason )
      if 'replot' in update_args:
        wx.CallAfter( self.UpdateState, replot = True )
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assume self.dmgr is valid.
@return			dict to be passed to UpdateState()
"""
    return  {}
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		PlotWidget.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation takes care of
'dataSetSelections' and 'timeValue', but subclasses must override for
all other properties.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'timeValue', ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    for k in ( 'dataSetSelections', ):
      if k in props_dict:
        cur_attr = props_dict[ k ]
	for name in cur_attr.keys():
	  cur_value = cur_attr[ name ]
	  del cur_attr[ name ]
	  cur_attr[ DataSetName( name ) ] = cur_value
	#end for name

        setattr( self, k, cur_attr )
      #end if k in props_dict
    #end for k

    super( PlotWidget, self ).LoadProps( props_dict )
    self.container.dataSetMenu.UpdateAllMenus()
    wx.CallAfter( self.UpdateState, replot = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnClose()					-
  #----------------------------------------------------------------------
  def _OnClose( self, ev ):
    """
"""
    if self.fig is not None:
      if self.logger.isEnabledFor( logging.INFO ):
        self.logger.debug( '%s: closing figure', self.GetTitle() )
      self.fig.close()
  #end _OnClose


  #----------------------------------------------------------------------
  #	METHOD:		_OnContextMenu()				-
  #----------------------------------------------------------------------
  def _OnContextMenu( self, ev ):
    """
"""
    ev_obj = ev.GetEventObject()
    if ev_obj.HasCapture():
      ev_obj.ReleaseMouse()

    pos = ev.GetPosition()
    pos = self.ScreenToClient( pos )

    menu = self.GetPopupMenu()
    self.PopupMenu( menu, pos )
  #end _OnContextMenu


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseMotion()				-
  #----------------------------------------------------------------------
  def _OnMplMouseMotion( self, ev ):
    tip_str = ''

    if ev.inaxes is None:
      self.cursor = None
      if self.cursorLine is not None:
        self.cursorLine.set_visible( False )
	if self.cursorLine2 is not None:
	  self.cursorLine2.set_visible( False )
        self.canvas.draw()
      #self.canvas.SetToolTipString( '' )

    elif self.ax is not None:
      if self.cursorLine is None and self.showCursor:
        self.cursorLine = \
	    self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 ) \
	    if self.refAxis == 'y' else \
	    self.ax.axvline( color = 'k', linestyle = '--', linewidth = 1 ) \

      if self.refAxis2 and self.cursorLine2 is None and self.showCursor:
        self.cursorLine2 = \
	    self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 ) \
	    if self.refAxis2 == 'y' else \
	    self.ax.axvline( color = 'k', linestyle = '--', linewidth = 1 ) \

      self.cursor = ( ev.xdata, ev.ydata )
      if self.showCursor:
        if self.refAxis == 'y':
          self.cursorLine.set_ydata( ev.ydata )
        else:
          self.cursorLine.set_xdata( ev.xdata )
        if self.refAxis2 == 'y':
          self.cursorLine2.set_ydata( ev.ydata )
        elif self.refAxis2 == 'x':
          self.cursorLine2.set_xdata( ev.xdata )

        self.cursorLine.set_visible( True )
        if self.cursorLine2:
          self.cursorLine2.set_visible( True )
      #end if self.showCursor
      self.canvas.draw()

      tip_str = self._CreateToolTipText( ev )
      #self.canvas.SetToolTipString( tip_str )
    #end elif

    self.canvas.SetToolTipString( tip_str )
  #end _OnMplMouseMotion


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """Handle click to set the state value.
This implementation checks for a right-click and calls Skip() to pass
the event to the wxPython window.  Subclasses should call this method
with super.
"""
    if ev.button == 3:
      ev.guiEvent.Skip()
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev is None:
      self.curSize = None
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( '%s: forced replot', self.GetTitle() )
      wx.CallAfter( self.UpdateState, replot = True )

    else:
      ev.Skip()

      wd, ht = self.GetClientSize()
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( '%s: clientSize=%d,%d', self.GetTitle(), wd, ht )

      if wd > 0 and ht > 0:
        if self.curSize is None or \
            wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
          self.curSize = ( wd, ht )
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug( '%s: starting timer', self.GetTitle() )
	  self.timer.Start( 500, wx.TIMER_ONE_SHOT )

#      wd, ht = self.GetClientSize()
#      if wd > 0 and ht > 0:
#        if self.curSize is None or \
#            wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
#          self.curSize = ( wd, ht )
#          if self.logger.isEnabledFor( logging.DEBUG ):
#            self.logger.debug( '%s: starting timer', self.GetTitle() )
#	  self.timer.Start( 500, wx.TIMER_ONE_SHOT )
    #end else ev is not None
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize_0()					-
  #----------------------------------------------------------------------
##  def _OnSize_0( self, ev ):
##    """
##"""
##    if ev is not None:
##      ev.Skip()
##
##    wd, ht = self.GetClientSize()
##
##    if wd > 0 and ht > 0:
##      self.UpdateState( replot = True )
##  #end _OnSize_0


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize_1()					-
  #----------------------------------------------------------------------
##  def _OnSize_1( self, ev ):
##    """
##"""
##    if ev is None:
##      # call wx.CallAfter( self.UpdateState, replot = True ) here?
##      self.curSize = None
##    else:
##      ev.Skip()
##
##    wd, ht = self.GetClientSize()
##
##    if wd > 0 and ht > 0:
##      if self.curSize is None or \
##          wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
##        self.curSize = ( wd, ht )
##        if self.logger.isEnabledFor( logging.DEBUG ):
##          self.logger.debug( '%s: calling timer', self.GetTitle() )
##	self.timer.Start( 500, wx.TIMER_ONE_SHOT )
##  #end _OnSize_1


  #----------------------------------------------------------------------
  #	METHOD:		PlotWidget._OnTimer()				-
  #----------------------------------------------------------------------
  def _OnTimer( self, ev ):
    """
"""
    if ev.Timer.Id == TIMERID_RESIZE:
      #wd, ht = self.GetClientSize()
      if self.curSize is not None:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( '%s: calling UpdateState redraw', self.GetTitle() )
        wx.CallAfter( self.UpdateState, redraw = True ) # replot = true
    #end if ev.Timer.Id == TIMERID_RESIZE
  #end _OnTimer


  #----------------------------------------------------------------------
  #	METHOD:		_OnToggleToolBar()				-
  #----------------------------------------------------------------------
  def _OnToggleToolBar( self, ev ):
    """
"""
    ev.Skip()

    if self.toolbar.IsShown():
      self.toolbar.home( False )
      self.toolbar.Show( False )
      self.callbackIds[ 'button_release_event' ] = self.\
          canvas.mpl_connect( 'button_release_event', self._OnMplMouseRelease )
      self.callbackIds[ 'motion_notify_event' ] = self.\
          canvas.mpl_connect( 'motion_notify_event', self._OnMplMouseMotion )

    else:
#      for k, id in self.callbackIds.iteritems():
#        self.canvas.mpl_disconnect( id )
      self.toolbar.Show( True )

    self.GetSizer().Layout()
  #end _OnToggleToolBar


  #----------------------------------------------------------------------
  #	METHOD:		PlotWidget.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to load properties.  This implementation takes care of
'dataSetSelections' and 'timeValue', but subclasses must override for
all other properties.
@param  props_dict	dict object to which to serialize properties
"""
    super( PlotWidget, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'timeValue', ):
      props_dict[ k ] = getattr( self, k )

    for k in ( 'dataSetSelections', ):
      if hasattr( self, k ):
        cur_attr = getattr( self, k )
	if isinstance( cur_attr, dict ):
	  for name in cur_attr.keys():
	    if isinstance( name, DataSetName ):
	      cur_value = cur_attr[ name ]
	      del cur_attr[ name ]
	      cur_attr[ name.name ] = cur_value
	  #end for name
	#end if isinstance( cur_value, dict )

	props_dict[ k ] = cur_attr
      #end if hasattr( self, k )
    #end for k
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """This noop version must be overridden by subclasses.
"""
    pass
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		_UpdatePlot()					-
  #----------------------------------------------------------------------
  def _UpdatePlot( self ):
    """
Must be called from the UI thread.
"""
    self._BusyDoOp( self._UpdatePlotImpl )
  #end _UpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_UpdatePlotImpl()				-
  #----------------------------------------------------------------------
  def _UpdatePlotImpl( self ):
    """
Must be called from the UI thread.
"""
    if self.ax is not None:
      self.axline = None
      self.cursorLine = \
      self.cursorLine2 = None

#      self.ax.clear()
#      if hasattr( self, 'ax2' ) and self.ax2 is not None:
#        self.ax2.clear()
      self.fig.clear()
      self._InitAxes()

#		-- Scale fonts
#		--
      wd, ht = self.GetClientSize()
      label_font_size = 14
      tick_font_size = 12
      self.titleFontSize = 16
      if 'wxMac' not in wx.PlatformInfo and wd < 800:
	decr = (800 - wd) / 50.0
	label_font_size -= decr
	tick_font_size -= decr
	self.titleFontSize -= decr

#      self.ax.grid(
#          True, 'both', 'both',
#	  color = '#c8c8c8', linestyle = ':', linewidth = 1
#	  )
      self._DoUpdatePlot( wd, ht )
      self._DoUpdateRedraw()
      self.canvas.draw()
    #end if
  #end _UpdatePlotImpl


  #----------------------------------------------------------------------
  #	METHOD:		UpdateState()					-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    if bool( self ):
      if 'scale_mode' in kwargs:
        kwargs[ 'replot' ] = True

      kwargs = self._UpdateStateValues( **kwargs )
      redraw = kwargs.get( 'redraw', False )
      replot = kwargs.get( 'replot', False )

      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
            '%s: redraw=%s, replot=%s',
	    self.GetTitle(), str( redraw ), str( replot )
	    )

      if replot:
        self._UpdateDataSetValues()
        self._UpdatePlot()

      elif redraw:
        self._DoUpdateRedraw()
        self.canvas.draw()
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateStateValues()				-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
@return			kwargs with 'redraw' and/or 'replot'
"""
    #replot = kwargs.get( 'replot', False )
    #redraw = kwargs.get( 'redraw', kwargs.get( 'force_redraw', False ) )
    replot = kwargs.get( 'replot', kwargs.get( 'force_redraw', False ) )
    redraw = kwargs.get( 'redraw', False )

    if 'data_model_mgr' in kwargs:
      replot = True

    if 'dataset_added' in kwargs:
      wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

    if 'time_value' in kwargs and kwargs[ 'time_value' ] != self.timeValue:
      if self._IsTimeReplot():
        replot = True
      else:
        redraw = True
      self.timeValue = kwargs[ 'time_value' ]

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end PlotWidget
