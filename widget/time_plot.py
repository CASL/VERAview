#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plot.py					-
#	HISTORY:							-
#		2015-05-25	leerw@ornl.gov				-
#	  Copied from exposure_plot.py to use new timeDataSet state
#	  mask and value.
#		2015-05-06	leerw@ornl.gov				-
#	  Calling DataModel.GetScalarValue() to build scalarValues.
#		2015-04-03	leerw@ornl.gov				-
#	  More checks in _LoadDataModel() and _UpdateState() for existence
#	  of data in each state.
#		2015-03-20	leerw@ornl.gov				-
#	  Added tooltip.
#		2015-03-19	leerw@ornl.gov				-
#	  Added GetDataSetType().
#		2015-03-18	leerw@ornl.gov				-
#	  Got this working and tested.
#		2015-03-13	leerw@ornl.gov				-
#	  Starting from core_keff.py.
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
#	CLASS:		TimePlot					-
#------------------------------------------------------------------------
class TimePlot( Widget ):
  """Per-time core-level plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):

    self.ax = None
    self.canvas = None
    self.cursor = None
    self.data = None
    self.fig = None

#x    self.fontSizeLabels = 14
#x    self.fontSizeTicks = 12
#x    self.fontSizeTitle = 16

    self.scalarName = 'keff'
    self.scalarValues = []
    #self.lx = None
    self.ly = None
    self.stateIndex = -1
    self.timeLine = None
    self.timeValues = []
    self.titleFontSize = 16

    super( TimePlot, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreateImage()					-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    result = None

    if self.fig != None:
      if self.timeLine != None:
        self.timeLine.set_visible( False )

      self.fig.savefig(
          file_path, dpi = 144, format = 'png', orientation = 'landscape'
	  )
      result = file_path

      if self.timeLine != None:
        self.timeLine.set_visible( True )
    #end if

    return  result
  #end CreateImage


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetType()				-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'scalar'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_scalarDataSet, STATE_CHANGE_stateIndex,
	STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetStateIndex()					-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Time Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, '[TimePlot.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      state_args = {}

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  state_args[ 'state_ndx' ] = self.state.stateIndex
          #wx.CallAfter( self._UpdateState, state_ndx = self.state.stateIndex )

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        state_args[ 'time_dataset' ] = self.state.timeDataSet

      if len( state_args ) > 0:
        wx.CallAfter( self._UpdateState, **state_args )
    #end else not a data model load
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    dpis = wx.ScreenDC().GetPPI()
    size = ( WIDGET_PREF_SIZE[ 0 ] / dpis[ 0 ], WIDGET_PREF_SIZE[ 1 ] / dpis[ 0 ] )
    self.fig = Figure( figsize = size, dpi = dpis[ 0 ] )
    self.ax = self.fig.add_subplot( 111 )
    #ax2 = ax1.twinx()
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

    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.states != None and len( self.data.states ) > 0:
      update_args = \
        {
	'scalar_dataset': self.scalarName,
	'state_ndx': max( 0, self.state.stateIndex ),
	'time_dataset': self.state.timeDataSet
	}
      wx.CallAfter( self._UpdateState, **update_args )

#      self.exposureValues = []
#      for st in self.data.states:
#	if st.exposure >= 0.0:
#          self.exposureValues.append( st.exposure )
#      #end for
#
#      update_args = \
#        {
#	'scalar_dataset': self.scalarName,
#	'state_ndx': max( 0, self.state.stateIndex )
#	}
#      self.scalarName = ''
#      self.stateIndex = -1
#      wx.CallAfter( self._UpdateState, **update_args )
    #end if
  #end _LoadDataModel


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
    if ev.inaxes is None:
      self.cursor = None
      if self.ly != None:
        self.ly.set_visible( False )
        self.canvas.draw()
      self.canvas.SetToolTipString( '' )

    elif ev.inaxes == self.ax:
      if self.ly == None:
        self.ly = self.ax.axvline( color = 'k', linestyle = '--', linewidth = 1 )

      self.cursor = ( ev.xdata, ev.ydata )
      self.ly.set_xdata( ev.xdata )
      self.ly.set_visible( True )
      self.canvas.draw()

      tip_str = ''
      state_ndx = self.data.FindListIndex( self.timeValues, ev.xdata )
      if state_ndx >= 0 and len( self.scalarValues ) >= state_ndx:
        if self.state.timeDataSet == 'state':
	  tip_str = 'State=%d' % (state_ndx + 1)
        else:
	  tip_str = '%s=%.3g' % ( self.state.timeDataSet, ev.xdata )

        tip_str += '\n%s=%.3g' % \
	    ( self.scalarName, self.scalarValues[ state_ndx ] )
      self.canvas.SetToolTipString( tip_str )
    #end elif
  #end _OnMplMouseMotion


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    button = ev.button or 1
    if button == 1 and self.cursor != None:
      state_ndx = self.data.FindListIndex( self.timeValues, self.cursor[ 0 ] )
      if state_ndx >= 0:
        self._UpdateState( state_ndx = state_ndx )
	    #exposure_value = self.cursor[ 0 ],
	self.FireStateChange( state_index = state_ndx )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    ev.Skip()
    wd, ht = self.GetClientSize()

    if wd > 0 and ht > 0 and self.stateIndex >= 0:
      state_ndx = self.stateIndex
      self.stateIndex = -1
#      self._UpdateState( state_ndx = state_ndx )
      self._UpdateState( replot = True, state_ndx = state_ndx )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    wx.CallAfter( self._UpdateState, scalar_dataset = ds_name )
    self.FireStateChange( scalar_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_UpdatePlot()					-
  #----------------------------------------------------------------------
  def _UpdatePlot( self ):
    """
"""
    if self.ax != None:
      self.timeLine = None
      self.ly = None
      self.ax.clear()

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

      self.ax.grid(
          True, 'both', 'both',
	  color = '#c8c8c8', linestyle = ':', linewidth = 1
	  )
      self.ax.set_title(
	  self.scalarName + ' vs Time',
	  fontsize = self.titleFontSize
	  )
      #self.ax.set_xlabel( 'Exposure (GWD/MT(HM))', fontsize = label_font_size )
      self.ax.set_xlabel( self.state.timeDataSet, fontsize = label_font_size )
      self.ax.set_ylabel( self.scalarName, fontsize = label_font_size )
      self.ax.tick_params( axis = 'both', which = 'major', labelsize = tick_font_size )

      if len( self.timeValues ) == len( self.scalarValues ):
        self.ax.plot(
            self.timeValues, self.scalarValues, 'b-',
	    label = self.scalarName, linewidth = 2
	    )

        self.timeLine = \
            self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
	if self.stateIndex >= 0 and self.stateIndex < len( self.timeValues ):
          self.timeLine.set_xdata( self.timeValues[ self.stateIndex ] )
      #end if data match

      self.canvas.draw()
    #end if
  #end _UpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateState()					-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    replot = kwargs[ 'replot' ] if 'replot' in kwargs  else False
    redraw = kwargs[ 'redraw' ] if 'redraw' in kwargs  else False

    if 'time_dataset' in kwargs:
      replot = True

    if 'scalar_dataset' in kwargs:
      if kwargs[ 'scalar_dataset' ] != self.scalarName:
        replot = True
	self.scalarName = kwargs[ 'scalar_dataset' ]
    #end if

    if 'state_ndx' in kwargs and kwargs[ 'state_ndx' ] != self.stateIndex:
      redraw = True
      self.stateIndex = kwargs[ 'state_ndx' ]
      if not replot and self.data.IsValid( state_index = self.stateIndex ):
        if self.timeLine == None:
          self.timeLine = \
	      self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
	self.timeLine.set_xdata( self.timeValues[ self.stateIndex ] )
      #end if not replotting
    #end if

    if replot:
      del self.scalarValues[ : ]
      del self.timeValues[ : ]

      if self.data != None and self.data.states != None:
#          self.stateIndex >= 0 and self.stateIndex < len( self.data.states ):
        for st in self.data.states:
          time_value = \
	      self.data.GetScalarValue( st.group[ self.state.timeDataSet ] ) \
	      if self.state.timeDataSet in st.group else \
	      float( st.index + 1 )
	  self.timeValues.append( time_value )

	  scalar_value = \
	      self.data.GetScalarValue( st.group[ self.scalarName ] ) \
	      if self.scalarName in st.group else \
	      0.0
	  self.scalarValues.append( scalar_value )
        #end for
      #end if

      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end _UpdateState

#end TimePlot
