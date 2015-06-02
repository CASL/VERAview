#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		exposure_plot.py				-
#	HISTORY:							-
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
#	CLASS:		ExposurePlot					-
#------------------------------------------------------------------------
class ExposurePlot( Widget ):
  """Per-exposure core-level plot.

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
    self.exposureLine = None
    self.exposureValues = []
    self.fig = None

#x    self.fontSizeLabels = 14
#x    self.fontSizeTicks = 12
#x    self.fontSizeTitle = 16

    self.scalarName = 'keff'
    self.scalarValues = []
    #self.lx = None
    self.ly = None
    self.stateIndex = -1
    self.titleFontSize = 16

    super( ExposurePlot, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreateImage()					-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    result = None

    if self.fig != None:
      if self.exposureLine != None:
        self.exposureLine.set_visible( False )

      self.fig.savefig(
          file_path, dpi = 144, format = 'png', orientation = 'landscape'
	  )
      result = file_path

      if self.exposureLine != None:
        self.exposureLine.set_visible( True )
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
    locks = set([ STATE_CHANGE_scalarDataSet, STATE_CHANGE_stateIndex ])
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
    return  'Exposure Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, '[ExposurePlot.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

#		-- Remember, multiple reasons possible
    elif (reason & STATE_CHANGE_stateIndex) > 0:
      print >> sys.stderr, '[ExposurePlot.HandleStateChange] state.stateIndex=%d, self.stateIndex=%d' % ( self.state.stateIndex, self.stateIndex )
      if self.state.stateIndex != self.stateIndex:
        wx.CallAfter( self._UpdateState, state_ndx = self.state.stateIndex )
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
#    if delay > 0:
#      time.sleep( delay )

    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.states != None and len( self.data.states ) > 0:
      self.exposureValues = []
      for st in self.data.states:
	if st.exposure >= 0.0:
          self.exposureValues.append( st.exposure )
      #end for

      update_args = \
        {
	'scalar_dataset': self.scalarName,
	'state_ndx': max( 0, self.state.stateIndex )
	}
      self.scalarName = ''
      self.stateIndex = -1
      wx.CallAfter( self._UpdateState, **update_args )
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
      state_ndx = self.data.FindListIndex( self.exposureValues, ev.xdata )
      if state_ndx >= 0 and len( self.scalarValues ) >= state_ndx:
        tip_str = \
            'Exposure=%.3g\n%s=%.3g' % \
	    ( ev.xdata, self.scalarName, self.scalarValues[ state_ndx ] )
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
      state_ndx = self.data.FindListIndex( self.exposureValues, self.cursor[ 0 ] )
      if state_ndx >= 0:
        self._UpdateState(
	    exposure_value = self.cursor[ 0 ],
	    state_ndx = state_ndx
	    )
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

    if wd > 0 and ht > 0:
#      self._UpdatePlot()

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
      self.exposureLine = None
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
	  self.scalarName + ' vs Exposure',
	  fontsize = self.titleFontSize
	  )
      self.ax.set_xlabel( 'Exposure (GWD/MT(HM))', fontsize = label_font_size )
      self.ax.set_ylabel( self.scalarName, fontsize = label_font_size )
      self.ax.tick_params( axis = 'both', which = 'major', labelsize = tick_font_size )

      if len( self.exposureValues ) == len( self.scalarValues ):
        self.ax.plot(
            self.exposureValues, self.scalarValues, 'b-',
	    label = self.scalarName, linewidth = 2
	    )

        self.exposureLine = \
            self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
        self.exposureLine.set_xdata( self.exposureValues[ self.stateIndex ] )
      #end if data match

      self.canvas.draw()
    #end if
  #end _UpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateState()					-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  #def _UpdateState( self, state_ndx, exposure_value = None ):
  def _UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    replot = kwargs[ 'replot' ] if 'replot' in kwargs  else False
    redraw = kwargs[ 'redraw' ] if 'redraw' in kwargs  else False
#    redraw = False

    exposure_value = -1.0
    new_state_ndx = -1
    if 'exposure_value' in kwargs:
      exposure_value = kwargs[ 'exposure_value' ]
      if 'state_ndx' in kwargs:
        new_state_idx = kwargs[ 'state_ndx' ]
      else:
        new_state_ndx = self.data.FindListIndex( self.exposureValues, exposure_value )

    elif 'state_ndx' in kwargs:
      new_state_ndx = kwargs[ 'state_ndx' ]

    if new_state_ndx >= 0 and new_state_ndx != self.stateIndex:
      redraw = True
      self.stateIndex = new_state_ndx
      if exposure_value < 0.0:
        exposure_value = self.exposureValues[ new_state_ndx ]

      if self.exposureLine == None:
        self.exposureLine = \
            self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
      self.exposureLine.set_xdata( exposure_value )
    #end if

    if 'scalar_dataset' in kwargs:
      if kwargs[ 'scalar_dataset' ] != self.scalarName:
        replot = True
	self.scalarName = kwargs[ 'scalar_dataset' ]
    #end if

    if replot:
      self.scalarValues = []
      if self.data != None and self.data.states != None and \
          self.stateIndex >= 0 and self.stateIndex < len( self.data.states ):

        for st in self.data.states:
	  if st.exposure >= 0.0 and self.scalarName in st.group:
	    self.scalarValues.append(
		self.data.GetScalarValue( st.group[ self.scalarName ] )
	        )
#            self.scalarValues.\
#	        append( st.group[ self.scalarName ].value.item() )
        #end for
      #end if

      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end _UpdateState

#end ExposurePlot
