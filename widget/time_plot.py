#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plot.py					-
#	HISTORY:							-
#		2015-07-03	leerw@ornl.gov				-
#	  Migrating to a PlotWidget extension.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
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
  from matplotlib.backends.backend_wx import NavigationToolbar2Wx
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

from event.state import *
from legend import *
from plot_widget import *
from widget import *
from widgetcontainer import *


#------------------------------------------------------------------------
#	CLASS:		TimePlot					-
#------------------------------------------------------------------------
class TimePlot( PlotWidget ):
  """Per-time core-level plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.menuDef = \
      [
	( 'Copy Data', self._OnCopyData ),
	( 'Copy Image', self._OnCopyImage )
      ]

    self.scalarDataSet = 'keff'
    self.scalarValues = []
    self.timeDataSet = 'state'

    super( TimePlot, self ).__init__( container, id, ref_axis = 'x' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateToolTipText()				-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		mouse motion event
"""
    tip_str = ''
    state_ndx = self.data.FindListIndex( self.refAxisValues, ev.xdata )
    if state_ndx >= 0 and len( self.scalarValues ) >= state_ndx:
      if self.state.timeDataSet == 'state':
        tip_str = 'State=%d' % (state_ndx + 1)
      else:
        tip_str = '%s=%.3g' % ( self.state.timeDataSet, ev.xdata )

      tip_str += '\n%s=%.3g' % \
          ( self.scalarDataSet, self.scalarValues[ state_ndx ] )

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		_DoUpdatePlot()					-
  #----------------------------------------------------------------------
  def _DoUpdatePlot( self, wd, ht ):
    """Do the work of creating the plot, setting titles and labels,
configuring the grid, plotting, and creating self.axline.  This implementation
calls self.ax.grid() and can be called by subclasses.
"""
    super( TimePlot, self )._DoUpdatePlot( wd, ht )

    label_font_size = 14
    tick_font_size = 12
    self.titleFontSize = 16
    if 'wxMac' not in wx.PlatformInfo and wd < 800:
      decr = (800 - wd) / 50.0
      label_font_size -= decr
      tick_font_size -= decr
      self.titleFontSize -= decr

    self.ax.set_title(
        self.scalarDataSet + ' vs Time',
	fontsize = self.titleFontSize
	)
    #self.ax.set_xlabel( 'Exposure (GWD/MT(HM))', fontsize = label_font_size )
    self.ax.set_xlabel( self.state.timeDataSet, fontsize = label_font_size )
    self.ax.set_ylabel( self.scalarDataSet, fontsize = label_font_size )
    self.ax.tick_params( axis = 'both', which = 'major', labelsize = tick_font_size )

    if len( self.refAxisValues ) == len( self.scalarValues ):
      self.ax.plot(
          self.refAxisValues, self.scalarValues, 'b-',
	  label = self.scalarDataSet, linewidth = 2
	  )

    self.axline = self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
    if self.stateIndex >= 0 and self.stateIndex < len( self.refAxisValues ):
      self.axline.set_xdata( self.refAxisValues[ self.stateIndex ] )
    #end if data match
  #end _DoUpdatePlot


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
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assume self.data is valid.
@return			dict to be passed to UpdateState()
"""
    if self.data != None and self.data.HasData():
      update_args = \
        {
	'scalar_dataset': self.scalarDataSet,
	'state_index': max( 0, self.state.stateIndex ),
	'time_dataset': self.state.timeDataSet
	}
    else:
      update_args = {}

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    button = ev.button or 1
    if button == 1 and self.cursor != None:
      state_ndx = self.data.FindListIndex( self.refAxisValues, self.cursor[ 0 ] )
      if state_ndx >= 0:
        self.UpdateState( state_index = state_ndx )
	self.FireStateChange( state_index = state_ndx )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    wx.CallAfter( self.UpdateState, scalar_dataset = ds_name )
    self.FireStateChange( scalar_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot and set self.axline.
This noop version must be overridden by subclasses.
"""
    del self.refAxisValues[ : ]
    del self.scalarValues[ : ]

    if self.data != None and self.data.HasData():
      for st in self.data.states:
        time_value = \
	    self.data.GetScalarValue( st.group[ self.state.timeDataSet ] ) \
	    if self.state.timeDataSet in st.group else \
	    float( st.index + 1 )
        self.refAxisValues.append( time_value )

        scalar_value = \
	    self.data.GetScalarValue( st.group[ self.scalarDataSet ] ) \
	    if self.scalarDataSet in st.group else \
	    0.0
        self.scalarValues.append( scalar_value )
      #end for
    #end if
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateStateValues()				-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
@return			kwargs with 'redraw' and/or 'replot'
"""
    kwargs = super( TimePlot, self )._UpdateStateValues( **kwargs )
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

    if 'scalar_dataset' in kwargs and kwargs[ 'scalar_dataset' ] != self.scalarDataSet:
      replot = True
      self.scalarDataSet = kwargs[ 'scalar_dataset' ]
    #end if

    if 'time_dataset' in kwargs:
      replot = True

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end TimePlot
