#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_axial_plot.py				-
#	HISTORY:							-
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-05-01	leerw@ornl.gov				-
#	  Using data.core.detectorAxialMesh, detector and detector_operable.
#		2015-04-27	leerw@ornl.gov				-
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
#	CLASS:		DetectorAxialPlot				-
#------------------------------------------------------------------------
class DetectorAxialPlot( Widget ):
  """Pin axial plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):

    self.ax = None
    #self.axialLevel = -1
    self.axialLine = None
    self.axialValue = ( 0.0, -1, -1 )
    self.axialValues = []
    self.canvas = None
    self.cursor = None
    self.data = None
    #self.dataSetName = kwargs.get( 'dataset', 'detector_response' )
    self.dataSetName = 'detector_response'
    self.dataSetValues = []
    self.detectorIndex = ( -1, -1, -1 )
    self.fig = None

    self.lx = None
    #self.ly = None
    self.stateIndex = -1
    self.titleFontSize = 16

    super( DetectorAxialPlot, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreateImage()					-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    result = None

    if self.fig != None:
      if self.axialLine != None:
        self.axialLine.set_visible( False )

      self.fig.savefig(
          file_path, dpi = 144, format = 'png', orientation = 'landscape'
	  )
      result = file_path

      if self.axialLine != None:
        self.axialLine.set_visible( True )
    #end if

    return  result
  #end CreateImage


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValue()				-
  #----------------------------------------------------------------------
  def _FindDataSetValue( self, axial_cm ):
    """Find matching dataset value for the axial.
@param  axial_cm	axial value
@return			dataset value or None if no match
"""

    value = None
    if len( self.axialValues ) == len( self.dataSetValues ):
      ndx = self.data.FindListIndex( self.axialValues, axial_cm )
      if ndx >= 0:
        value = self.dataSetValues[ ndx ]
    #end if array lengths match

    return  value
  #end _FindDataSetValue


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialLevel()					-
  #----------------------------------------------------------------------
#  def GetAxialLevel( self ):
#    """@return		0-based index
#"""
#    return  self.axialLevel
#  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetType()				-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'detector'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_axialValue, STATE_CHANGE_detectorIndex,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detector Axial Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, '[DetectorAxialPlot.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      update_args = {}
      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
          update_args[ 'axial_value' ] = self.state.axialValue
      #end if

      if (reason & STATE_CHANGE_detectorDataSet) > 0:
        if self.state.detectorDataSet != self.dataSetName:
          update_args[ 'detector_dataset' ] = self.state.detectorDataSet
      #end if

      if (reason & STATE_CHANGE_detectorIndex) > 0:
        if self.state.detectorIndex != self.detectorIndex:
          update_args[ 'detector_ndx' ] = self.state.detectorIndex
      #end if

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  update_args[ 'state_ndx' ] = self.state.stateIndex
          #wx.CallAfter( self._UpdateState, state_ndx = self.state.stateIndex )
      #end if

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        update_args[ 'replot' ] = True

      if len( update_args ) > 0:
        wx.CallAfter( self._UpdateState, **update_args )
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
#    if delay > 0:
#      time.sleep( delay )

    print >> sys.stderr, '[DetectorAxialPlot._LoadDataModel]'

    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.core != None and \
	self.data.core.ndetax > 0 and self.data.core.detectorMap != None and \
        self.data.states != None and len( self.data.states ) > 0:

      self.axialValues = \
	  self.data.core.detectorMeshCenters \
	  if self.data.core.detectorMeshCenters != None else \
          range( self.data.core.ndetax, 0, -1 )

      self.dataSetValues = [ 0.0 ] * self.data.core.nax

      det_ndx = self.data.NormalizeDetectorIndex( self.state.detectorIndex )

      update_args = \
        {
	'axial_value': self.state.axialValue,
	'detector_ndx': det_ndx,
	'state_ndx': max( 0, self.state.stateIndex )
	}
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
      if self.lx != None:
        self.lx.set_visible( False )
        self.canvas.draw()
      self.canvas.SetToolTipString( '' )

    elif ev.inaxes == self.ax:
      if self.lx == None:
        self.lx = self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 )

      self.cursor = ( ev.xdata, ev.ydata )
      self.lx.set_ydata( ev.ydata )
      self.lx.set_visible( True )
      self.canvas.draw()

      tip_str = ''
      ds_value = self._FindDataSetValue( ev.ydata )
      if ds_value != None:
        tip_str = \
	    'Axial=%.3g\n%s=%.3g' % \
	    ( ev.ydata, self.dataSetName, ds_value )
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
      axial_value = self.data.CreateAxialValue( value = self.cursor[ 1 ] )
      self._UpdateState( axial_value = axial_value )
      self.FireStateChange( axial_value = axial_value )
    #end if
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    ev.Skip()
    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[DetectorAxialPlot._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None:
      self._UpdateState( replot = True )
#      axial_level = self.axialLevel
#      self.axialLevel = -1
#      self._UpdateState( axial_level = axial_level, replot = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    wx.CallAfter( self._UpdateState, detector_dataset = ds_name )
    self.FireStateChange( detector_dataset = ds_name )
  #end SetDataSet


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
    if self.ax != None and self.data != None:
      self.axialLine = None
      self.lx = None
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
	  'Axial vs %s\nDetector %d %s, %s %.3g' % \
	  ( self.dataSetName, self.detectorIndex[ 0 ] + 1,
	    self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ),
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    ),
	  fontsize = self.titleFontSize
	  )
#      self.ax.set_title(
#	  'Axial vs %s\nDetector %d %s, Exposure %.3f' % \
#	  ( self.dataSetName, self.detectorIndex[ 0 ] + 1,
#	    self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ),
#	    self.data.states[ self.stateIndex ].exposure
#	    ),
#	  fontsize = self.titleFontSize
#	  )
      self.ax.set_xlabel( self.dataSetName, fontsize = label_font_size )
      self.ax.set_xlim( *self.data.GetRange( self.dataSetName ) )
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      self.ax.tick_params( axis = 'both', which = 'major', labelsize = tick_font_size )

      if len( self.axialValues) == len( self.dataSetValues ):
        self.ax.plot(
	    self.dataSetValues, self.axialValues, 'b.',  # b-
	    label = self.dataSetName, linewidth = 2
	    )

        self.axialLine = \
            self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
        self.axialLine.set_ydata( self.axialValue[ 0 ] )
        #self.axialLine.set_ydata( self.axialValues[ self.axialLevel ] )
      #end if data match

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
    replot = kwargs[ 'replot' ] if 'replot' in kwargs  else False
    redraw = kwargs[ 'redraw' ] if 'redraw' in kwargs  else False

    if 'detector_dataset' in kwargs:
      if kwargs[ 'detector_dataset' ] != self.dataSetName:
        replot = True
	self.dataSetName = kwargs[ 'detector_dataset' ]
    #end if

    if 'detector_ndx' in kwargs:
      if kwargs[ 'detector_ndx' ] != self.detectorIndex:
	replot = True
        self.detectorIndex = kwargs[ 'detector_ndx' ]
    #end if

    if 'state_ndx' in kwargs:
      if kwargs[ 'state_ndx' ] != self.stateIndex:
	replot = True
        self.stateIndex = kwargs[ 'state_ndx' ]
    #end if

    if 'axial_value' in kwargs:
      if kwargs[ 'axial_value' ] != self.axialValue:
	self.axialValue = kwargs[ 'axial_value' ]
	if not replot:
          redraw = True
	  if self.axialLine == None:
	    self.axialLine = \
	        self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
	  self.axialLine.set_ydata( self.axialValue[ 0 ] )
      #end if value changed
    #end if

    if replot:
      self.dataSetValues = []
      if self.stateIndex >= 0 and self.stateIndex < len( self.data.states ) and \
	  self.detectorIndex[ 0 ] >= 0 and self.detectorIndex[ 0 ] < self.data.core.ndet and \
	  self.dataSetName in self.data.states[ self.stateIndex ].group:

	ds = self.data.states[ self.stateIndex ].group[ self.dataSetName ]
	self.dataSetValues = ds[ :, self.detectorIndex[ 0 ] ]
      #end if

      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end _UpdateState

#end DetectorAxialPlot
