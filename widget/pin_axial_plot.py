#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		pin_axial_plot.py				-
#	HISTORY:							-
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
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
#	CLASS:		PinAxialPlot					-
#------------------------------------------------------------------------
class PinAxialPlot( Widget ):
  """Pin axial plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):

    self.assemblyIndex = ( -1, -1, -1 )
    self.ax = None
    #self.axialLevel = -1
    self.axialLine = None
    self.axialValue = ( 0.0, -1, -1 )
    self.axialValues = []
    self.canvas = None
    self.cursor = None
    self.data = None
    self.dataSetValues = []
    self.fig = None
    self.pinDataSet = kwargs.get( 'pin_dataset', 'pin_powers' )

    self.lx = None
    #self.ly = None
    self.pinColRow = ( -1, -1 )
    self.stateIndex = -1
    self.titleFontSize = 16

    super( PinAxialPlot, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreatePrintImage()				-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
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
  #end CreatePrintImage


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
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


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
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Pin Axial Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange_()				-
  #----------------------------------------------------------------------
  def HandleStateChange_( self, reason ):
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, '[PinAxialPlot.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      update_args = {}
      if (reason & STATE_CHANGE_assemblyIndex) > 0:
        if self.state.assemblyIndex != self.assemblyIndex:
          update_args[ 'assy_ndx' ] = self.state.assemblyIndex
      #end if

      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
          update_args[ 'axial_value' ] = self.state.axialValue

      if (reason & STATE_CHANGE_pinColRow) > 0:
        if self.state.pinColRow != self.pinColRow:
          update_args[ 'pin_colrow' ] = self.state.pinColRow
      #end if

      if (reason & STATE_CHANGE_pinDataSet) > 0:
        if self.state.pinDataSet != self.pinDataSet:
          update_args[ 'pin_dataset' ] = self.state.pinDataSet
      #end if

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  update_args[ 'state_ndx' ] = self.state.stateIndex
      #end if

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        update_args[ 'replot' ] = True

      if len( update_args ) > 0:
        wx.CallAfter( self.UpdateState, **update_args )
    #end else not a data model load
  #end HandleStateChange_


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

    print >> sys.stderr, '[PinAxialPlot._LoadDataModel]'

    self.data = State.FindDataModel( self.state )
    if self.data != None and self.data.core != None and \
	self.data.core.npin > 0 and self.data.core.nax > 0 and \
        self.data.states != None and len( self.data.states ) > 0:

#      self.axialValues = range( self.data.core.nax, 0, -1 )
      self.axialValues = \
	  self.data.core.axialMeshCenters \
	  if self.data.core.axialMeshCenters != None else \
          range( self.data.core.nax, 0, -1 )

      self.dataSetValues = [ 0.0 ] * self.data.core.nax

      assy_ndx = self.data.NormalizeAssemblyIndex( self.state.assemblyIndex )
      pin_colrow = self.data.NormalizePinColRow( self.state.pinColRow )
      update_args = \
        {
	'assembly_index': assy_ndx,
	'axial_value': self.state.axialValue,
	'pin_dataset': self.pinDataSet,
	'pin_colrow': pin_colrow,
	'state_index': max( 0, self.state.stateIndex )
	}
      wx.CallAfter( self.UpdateState, **update_args )
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
	    ( ev.ydata, self.pinDataSet, ds_value )
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
      self.UpdateState( axial_value = axial_value )
      self.FireStateChange( axial_value = axial_value )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    ev.Skip()
    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[PinAxialPlot._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None:
      self.UpdateState( replot = True )
#      axial_level = self.axialLevel
#      self.axialLevel = -1
#      self.UpdateState( axial_level = axial_level, replot = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
    self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


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
      pin_rc = ( self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1 )
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] )
      self.ax.set_title(
	  'Axial vs %s\nAssy %d %s, Pin %s, %s %.3g' % \
	  ( self.pinDataSet,
	    self.assemblyIndex[ 0 ] + 1, show_assy_addr, str( pin_rc ),
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    ),
	  fontsize = self.titleFontSize
	  )
#      self.ax.set_title(
#	  'Axial vs %s\nAssy %d %s, Pin %s, Exposure %.3f' % \
#	  ( self.pinDataSet,
#	    self.assemblyIndex[ 0 ] + 1, show_assy_addr, str( pin_rc ),
#	    self.data.states[ self.stateIndex ].exposure
#	    ),
#	  fontsize = self.titleFontSize
#	  )
      self.ax.set_xlabel( self.pinDataSet, fontsize = label_font_size )
      self.ax.set_xlim( *self.data.GetRange( self.pinDataSet ) )
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      self.ax.tick_params( axis = 'both', which = 'major', labelsize = tick_font_size )

      if len( self.axialValues ) == len( self.dataSetValues ):
        self.ax.plot(
	    self.dataSetValues, self.axialValues, 'b-',  # b.
	    label = self.pinDataSet, linewidth = 2
	    )

        self.axialLine = \
            self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
        #self.axialLine.set_ydata( self.axialValues[ self.axialValue[ 1 ] ] )
        self.axialLine.set_ydata( self.axialValue[ 0 ] )
      #end if data match

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
    replot = kwargs[ 'replot' ] if 'replot' in kwargs  else False
    redraw = kwargs[ 'redraw' ] if 'redraw' in kwargs  else False

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      replot = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]
    #end if

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      replot = True
      self.pinColRow = kwargs[ 'pin_colrow' ]
    #end if

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      replot = True
      self.pinDataSet = kwargs[ 'pin_dataset' ]
    #end if

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      replot = True
      self.stateIndex = kwargs[ 'state_index' ]
    #end if

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      self.axialValue = kwargs[ 'axial_value' ]
      if not replot:
        redraw = True
        if self.axialLine == None:
	  self.axialLine = \
	      self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
        self.axialLine.set_ydata( self.axialValue[ 0 ] )
      #end if
    #end if

    if replot:
      self.dataSetValues = []
      if self.stateIndex >= 0 and self.stateIndex < len( self.data.states ) and \
	  self.assemblyIndex[ 0 ] >= 0 and self.assemblyIndex[ 0 ] < self.data.core.nass and \
	  self.pinColRow[ 0 ] >= 0 and self.pinColRow[ 0 ] < self.data.core.npin and \
	  self.pinColRow[ 1 ] >= 0 and self.pinColRow[ 1 ] < self.data.core.npin and \
	  self.pinDataSet in self.data.states[ self.stateIndex ].group:

	ds = self.data.states[ self.stateIndex ].group[ self.pinDataSet ]
	del self.dataSetValues[ : ]
	for i in range( self.data.core.nax ):
	  self.dataSetValues.append(
	      ds[ self.pinColRow[ 1 ], self.pinColRow[ 0 ], i, self.assemblyIndex[ 0 ] ]
	      )
	#end for
      #end if

      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end UpdateState

#end PinAxialPlot
