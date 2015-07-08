#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		plot_widget.py					-
#	HISTORY:							-
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
import math, os, sys, time, traceback
import numpy as np
import pdb  # pdb.set_trace()

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
#  import matplotlib.pyplot as plt
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

try:
  from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
  from matplotlib.backends.backend_wx import NavigationToolbar2Wx
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

try:
  import wx
#  import wx.lib.delayedresult as wxlibdr
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

from event.state import *
from legend import *
from widget import *
from widgetcontainer import *


#------------------------------------------------------------------------
#	CLASS:		PlotWidget					-
#------------------------------------------------------------------------
class PlotWidget( Widget ):
  """Base class for plot widgets.

Properties:
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
"""

    self.ax = None
    self.axline = None  # axis line representing state
    self.canvas = None
    self.cursor = None
    self.cursorLine = None  # axis line following the cursor
    self.data = None
    self.fig = None

    self.refAxis = kwargs.get( 'ref_axis', 'y' )
    self.refAxisValues = []
    self.stateIndex = -1
    self.titleFontSize = 16

    super( PlotWidget, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreatePrintImage()				-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    result = None

    if self.fig != None:
      if self.axline != None:
        self.axline.set_visible( False )

      self.fig.savefig(
          file_path, dpi = 144, format = 'png', orientation = 'landscape'
	  )
      result = file_path

      if self.axline != None:
        self.axline.set_visible( True )
      self.canvas.draw()
    #end if

    return  result
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		_CreateToolTipText()				-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		mouse motion event
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
  #	METHOD:		_FindAxialDataSetValue()			-
  #----------------------------------------------------------------------
  def _FindAxialDataSetValue( self, axial_cm, axial_values, ds_values ):
    """Find matching dataset value for the axial.
are axial values.
@param  axial_cm	axial value
@param  axial_values	axial values in which to find axial level index
@param  ds_values	dataset values indexed by axial level index
@return			dataset value or None if no match
"""

    value = None
    if len( axial_values ) == len( ds_values ):
      ndx = self.data.FindListIndex( axial_values, axial_cm )
      if ndx >= 0:
        value = ds_values[ ndx ]
    #end if array lengths match

    return  value
  #end _FindAxialDataSetValue


  #----------------------------------------------------------------------
  #	METHOD:		GetStateIndex()					-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


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
    self.fig = Figure( figsize = size, dpi = dpis[ 0 ] )

    self._InitAxes()
#    if two_axes:
#      self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
#      self.ax2 = self.ax.twiny()
#    else:
#      self.ax = self.fig.add_subplot( 111 )
    self.canvas = FigureCanvas( self, -1, self.fig )

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.canvas, 1, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND )
    self.SetSizer( sizer )

    self.canvas.mpl_connect( 'button_release_event', self._OnMplMouseRelease )
    self.canvas.mpl_connect( 'motion_notify_event', self._OnMplMouseMotion )

    self.Bind( wx.EVT_CLOSE, self._OnClose )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModel()				-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.
"""
    print >> sys.stderr, '[PlotWidget._LoadDataModel]'

    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      update_args = self._LoadDataModelValues()
      wx.CallAfter( self._UpdateState, **update_args )
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to _UpdateState().  Assume self.data is valid.
@return			dict to be passed to _UpdateState()
"""
    return  {}
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		_OnClose()					-
  #----------------------------------------------------------------------
  def _OnClose( self, ev ):
    """
"""
    if self.fig != None:
      self.fig.close()
  #end _OnClose


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseMotion()				-
  #----------------------------------------------------------------------
  def _OnMplMouseMotion( self, ev ):
    tip_str = ''

    if ev.inaxes is None:
      self.cursor = None
      if self.cursorLine != None:
        self.cursorLine.set_visible( False )
        self.canvas.draw()
      #self.canvas.SetToolTipString( '' )

    elif self.ax != None:
      if self.cursorLine == None:
        self.cursorLine = \
	    self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 ) \
	    if self.refAxis == 'y' else \
	    self.ax.axvline( color = 'k', linestyle = '--', linewidth = 1 ) \

      self.cursor = ( ev.xdata, ev.ydata )
      if self.refAxis == 'y':
        self.cursorLine.set_ydata( ev.ydata )
      else:
        self.cursorLine.set_xdata( ev.xdata )
      self.cursorLine.set_visible( True )
      self.canvas.draw()

      tip_str = self._CreateToolTipText( ev )
      #self.canvas.SetToolTipString( tip_str )
    #end elif

    self.canvas.SetToolTipString( tip_str )
  #end _OnMplMouseMotion


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseMotion_old()				-
  #----------------------------------------------------------------------
  def _OnMplMouseMotion_old( self, ev ):
    tip_str = ''

    if ev.inaxes is None:
      self.cursor = None
      if self.cursorLine != None:
        self.cursorLine.set_visible( False )
        self.canvas.draw()
      #self.canvas.SetToolTipString( '' )

    elif ev.inaxes == self.ax:
      if self.cursorLine == None:
        self.cursorLine = \
	    self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 ) \
	    if self.refAxis == 'y' else \
	    self.ax.axvline( color = 'k', linestyle = '--', linewidth = 1 ) \

      self.cursor = ( ev.xdata, ev.ydata )
      if self.refAxis == 'y':
        self.cursorLine.set_ydata( ev.ydata )
      else:
        self.cursorLine.set_xdata( ev.xdata )
      self.cursorLine.set_visible( True )
      self.canvas.draw()

      tip_str = self._CreateToolTipText( ev )
      #self.canvas.SetToolTipString( tip_str )
    #end elif

    self.canvas.SetToolTipString( tip_str )
  #end _OnMplMouseMotion_old


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """Handle click to set the state value.
This noop version must be overridden by subclasses.
"""
    pass
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    ev.Skip()
    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[PlotWidget._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None:
      self._UpdateState( replot = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot.
This noop version must be overridden by subclasses.
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
#    try:
#      wait = wx.BusyCursor()
#      self._UpdatePlotImpl()
#    finally:
#      del wait
  #end _UpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_UpdatePlotImpl()				-
  #----------------------------------------------------------------------
  def _UpdatePlotImpl( self ):
    """
Must be called from the UI thread.
"""
    if self.ax != None and self.data != None:
      self.axline = None
      self.cursorLine = None

#      self.ax.clear()
#      if hasattr( self, 'ax2' ) and self.ax2 != None:
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
      self.canvas.draw()
    #end if
  #end _UpdatePlotImpl


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateState()					-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    kwargs = self._UpdateStateValues( **kwargs )
    redraw = kwargs.get( 'redraw', False )
    replot = kwargs.get( 'replot', False )

    if replot:
      self._UpdateDataSetValues()
      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end _UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateStateValues()				-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
@return			kwargs with 'redraw' and/or 'replot'
"""
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      replot = True
      self.stateIndex = kwargs[ 'state_index' ]
    #end if

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end PlotWidget
