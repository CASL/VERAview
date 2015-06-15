#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		all_axial_plot.py				-
#	HISTORY:							-
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-23	leerw@ornl.gov				-
#	  New channel processing.
#		2015-05-12	leerw@ornl.gov				-
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

from bean.dataset_chooser import *
from event.state import *

from legend import *
from widget import *
from widgetcontainer import *


PLOT_COLORS = [ 'b', 'r', 'g', 'm', 'c' ]
#        b: blue
#        g: green
#        r: red
#        c: cyan
#        m: magenta
#        y: yellow
#        k: black
#        w: white


#------------------------------------------------------------------------
#	CLASS:		AllAxialPlot					-
#------------------------------------------------------------------------
class AllAxialPlot( Widget ):
  """Pin axial plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__del__()					-
  #----------------------------------------------------------------------
  def __del__( self ):
    if self.dataSetDialog != None:
      self.dataSetDialog.Destroy()

    super( AllAxialPlot, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.ax = None
    #self.axialLevel = -1
    self.axialLine = None
    self.axialValue = ( 0.0, -1, -1 )
    #self.axialValues = []
    self.canvas = None
    self.channelColRow = ( -1, -1 )
    self.cursor = None
    self.data = None
    self.dataSetDialog = None
    self.dataSetName = kwargs.get( 'dataset', 'pin_powers' )
    self.dataSetSelections = {}
    self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name
    self.detectorIndex = ( -1, -1, -1 )
    self.fig = None

    self.lx = None
    #self.ly = None
    self.menuDefs = [ ( 'Select Datasets', self._OnSelectDataSets ) ]
    self.pinColRow = ( -1, -1 )
    self.stateIndex = -1
    self.titleFontSize = 16

    super( AllAxialPlot, self ).__init__( container, id )
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
#  def _FindDataSetValue( self, axial_cm ):
#    """Find matching dataset value for the axial.
#@param  axial_cm	axial value
#@return			dataset value or None if no match
#"""
#
#    value = None
#    if len( self.axialValues ) == len( self.dataSetValues ):
#      ndx = self.data.FindListIndex( self.axialValues, axial_cm )
#      if ndx >= 0:
#        value = self.dataSetValues[ ndx ]
#    #end if array lengths match
#
#    return  value
#  #end _FindDataSetValue


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, axial_cm ):
    """Find matching dataset values for the axial.
@param  axial_cm	axial value
@return			dict by name of dataset values or None if no matches
"""

    values = {}
    for k in self.dataSetValues:
      ndx = -1

      if k in self.data.GetDataSetNames( 'detector' ):
        if self.data.core.detectorMeshCenters != None:
	  ndx = self.data.FindListIndex( self.data.core.detectorMeshCenters, axial_cm )
      else:
        ndx = self.data.FindListIndex( self.data.core.axialMeshCenters, axial_cm )
      if ndx >= 0:
        values[ k ] = self.dataSetValues[ k ][ ndx ]
    #end for

    return  values
  #end _FindDataSetValues


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
#  def GetDataSetType( self ):
#    return  'pin'
#  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_channelColRow, STATE_CHANGE_detectorIndex,
	STATE_CHANGE_pinColRow, STATE_CHANGE_stateIndex,
	STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetMenuDef()					-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    return  self.menuDefs
  #end GetMenuDef


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
      print >> sys.stderr, '[AllAxialPlot.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      update_args = {}
      if (reason & STATE_CHANGE_assemblyIndex) > 0:
        if self.state.assemblyIndex != self.assemblyIndex:
          update_args[ 'assy_ndx' ] = self.state.assemblyIndex
          #wx.CallAfter( self._UpdateState, assy_ndx = self.state.assemblyIndex )
      #end if

      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
          update_args[ 'axial_value' ] = self.state.axialValue
#      if (reason & STATE_CHANGE_axialLevel) > 0:
#        if self.state.axialLevel != self.axialLevel:
#          update_args[ 'axial_level' ] = self.state.axialLevel
#          #wx.CallAfter( self._UpdateState, axial_level = self.state.axialLevel )
#      #end if

      if (reason & STATE_CHANGE_channelColRow) > 0:
        if self.state.channelColRow != self.channelColRow:
          update_args[ 'channel_colrow' ] = self.state.channelColRow
      #end if

      if (reason & STATE_CHANGE_detectorIndex) > 0:
        if self.state.detectorIndex != self.detectorIndex:
          update_args[ 'detector_ndx' ] = self.state.detectorIndex
      #end if

      if (reason & STATE_CHANGE_pinColRow) > 0:
        if self.state.pinColRow != self.pinColRow:
          update_args[ 'pin_colrow' ] = self.state.pinColRow
          #wx.CallAfter( self._UpdateState, pin_colrow = self.state.pinColRow )
      #end if

      if (reason & STATE_CHANGE_pinDataSet) > 0:
        if self.state.pinDataSet != self.dataSetName:
          update_args[ 'pin_dataset' ] = self.state.pinDataSet
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
#    #self.ax = self.fig.add_subplot( 111 )
    self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
    self.ax2 = None
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

    print >> sys.stderr, '[AllAxialPlot._LoadDataModel]'

    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.core != None and \
	self.data.core.npin > 0 and self.data.core.nax > 0 and \
        self.data.states != None and len( self.data.states ) > 0:

      assy_ndx = self.data.NormalizeAssemblyIndex( self.state.assemblyIndex )
      axial_value = self.data.NormalizeAxialValue( self.state.axialValue )
      chan_colrow = self.data.NormalizeChannelColRow( self.state.channelColRow )
      detector_ndx = self.data.NormalizeDetectorIndex( self.state.detectorIndex )
      pin_colrow = self.data.NormalizePinColRow( self.state.pinColRow )
      state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'assy_index': assy_ndx,
	'axial_value': axial_value,
	'channel_colrow': chan_colrow,
#	'dataset_name': self.dataSetName,
	'detector_index': detector_ndx,
	'pin_colrow': pin_colrow,
	'state_index': state_ndx
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

    #elif ev.inaxes == self.ax:
    elif self.ax != None:
      if self.lx == None:
        self.lx = self.ax.axhline( color = 'k', linestyle = '--', linewidth = 1 )

      self.cursor = ( ev.xdata, ev.ydata )
      self.lx.set_ydata( ev.ydata )
      self.lx.set_visible( True )
      self.canvas.draw()

      tip_str = ''
      ds_values = self._FindDataSetValues( ev.ydata )
      if ds_values != None:
        tip_str = 'Axial=%.3g' % ev.ydata
	ds_keys = ds_values.keys()
	ds_keys.sort()
	for k in ds_keys:
	  tip_str += '\n%s=%.3g' % ( k, ds_values[ k ] )
      #end if
#      ds_value = self._FindDataSetValue( ev.ydata )
#      if ds_value != None:
#        tip_str = \
#	    'Axial=%.3g\n%s=%.3g' % \
#	    ( ev.ydata, self.dataSetName, ds_value )
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
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		_OnSelectDataSets()				-
  #----------------------------------------------------------------------
  def _OnSelectDataSets( self, ev ):
    """Must be called from the UI thread.
"""
    if self.dataSetDialog == None:
      if self.data == None:
        wx.MessageBox( self, 'No data model', 'Select Datasets' ).ShowModal()
      else:
        ds_names = self.data.GetDataSetNames( 'axial' )
	self.dataSetDialog = DataSetChooserDialog( self, ds_names = ds_names )
    #end if

    if self.dataSetDialog != None:
      self.dataSetDialog.ShowModal( self.dataSetSelections )
      selections = self.dataSetDialog.GetResult()
      if selections != None:
        self.dataSetSelections = selections
	self._UpdateState( replot = True )
    #end if
  #end _OnSelectDataSets


  #----------------------------------------------------------------------
  #	METHOD:		_OnSize()					-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    ev.Skip()
    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[AllAxialPlot._OnSize] clientSize=%d,%d' % ( wd, ht )

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
    wx.CallAfter( self._UpdateState, pin_dataset = ds_name )
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
    self.axialLine = None
    self.lx = None

    self.fig.clear()
    self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
    #self.ax2 = self.ax.twiny()
    self.ax2 = None
    self.fig.suptitle(
        'Axial Plot',
	fontsize = 'medium', fontweight = 'bold'
	)

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

#		-- Something to plot?
#		--
    if len( self.dataSetValues ) > 0:
#			-- Determine axis datasets
#			--
      bottom_ds_name = top_ds_name = None
      for k in self.dataSetValues:
        rec = self.dataSetSelections[ k ]
        if rec[ 'axis' ] == 'bottom':
	  bottom_ds_name = k
        elif rec[ 'axis' ] == 'top':
	  top_ds_name = k
      #end for
      if bottom_ds_name == None:
        for k in self.dataSetValues:
	  if top_ds_name != k:
	    bottom_ds_name = k
	    break

#			-- Configure axes
#			--
      if top_ds_name != None:
        self.ax2 = self.ax.twiny()
        self.ax2.set_xlabel( top_ds_name, fontsize = label_font_size )
        self.ax2.set_xlim( *self.data.GetRange( top_ds_name ) )
	self.ax2.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

      self.ax.set_xlabel( bottom_ds_name, fontsize = label_font_size )
      self.ax.set_xlim( *self.data.GetRange( bottom_ds_name ) )
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      self.ax.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )
      self.ax.grid(
          True, 'both', 'both',
	  color = '#c8c8c8', linestyle = ':', linewidth = 1
	  )

#			-- Set title
#			--
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] )

      title_str = 'Assy %d %s, %s %.3g' % \
          ( self.assemblyIndex[ 0 ] + 1, show_assy_addr,
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )
#      title_str = 'Assy %d %s, Exp %.3f' % \
#          ( self.assemblyIndex[ 0 ] + 1, show_assy_addr,
#	    self.data.states[ self.stateIndex ].exposure )

      title_line2 = ''
      if 'channel' in self.dataSetTypes:
	chan_rc = ( self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1 )
        title_line2 += 'Chan %s' % str( chan_rc )

      if 'detector' in self.dataSetTypes: # and self.detectorIndex[ 0 ] >= 0
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Det %d %s' % \
	    ( self.detectorIndex[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ) )

      if 'pin' in self.dataSetTypes: # and self.detectorIndex[ 0 ] >= 0
        pin_rc = ( self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1 )
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Pin %s' % str( pin_rc )

      if len( title_line2 ) > 0:
        title_str += '\n' + title_line2

#			-- Plot each selected dataset
#			--
      count = 0
      for k in self.dataSetValues:
	rec = self.dataSetSelections[ k ]
	scale = rec[ 'scale' ] if rec[ 'axis' ] == '' else 1.0
	legend_label = k
	if scale != 1.0:
	  legend_label += '*%.3g' % scale

	if k in self.data.GetDataSetNames( 'detector' ):
	  axial_values = self.data.core.detectorMeshCenters
	  plot_type = '.'
	else:
	  axial_values = self.data.core.axialMeshCenters
	  plot_type = '-'

	plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	cur_axis = self.ax2 if rec[ 'axis' ] == 'top' else self.ax
	cur_axis.plot(
	    self.dataSetValues[ k ] * scale, axial_values, plot_mode,
	    label = legend_label, linewidth = 2
	    )

	count += 1
      #end for

#			-- Create legend
#			--
      handles, labels = self.ax.get_legend_handles_labels()
      if self.ax2 != None:
        handles2, labels2 = self.ax2.get_legend_handles_labels()
	handles += handles2
	labels += labels2

      self.fig.legend(
          handles, labels,
	  loc = 'upper right',
	  prop = { 'size': 'small' }
	  )
#      self.ax.legend(
#	  handles, labels,
#	  bbox_to_anchor = ( 1.05, 1 ), borderaxespad = 0., loc = 2
#	  )

      self.fig.text(
          0.1, 0.925, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )

#			-- Axial value line
#			--
      self.axialLine = \
          self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
      self.axialLine.set_ydata( self.axialValue[ 0 ] )
    #end if we have something to plot

    self.canvas.draw()
  #end _UpdatePlotImpl


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateState()					-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
#    replot = False
#    redraw = False
    replot = kwargs[ 'replot' ] if 'replot' in kwargs  else False
    redraw = kwargs[ 'redraw' ] if 'redraw' in kwargs  else False

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      replot = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]
    #end if

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] != self.channelColRow:
      replot = True
      self.channelColRow = kwargs[ 'channel_colrow' ]
    #end if

    if 'detector_index' in kwargs and kwargs[ 'detector_index' ] != self.detectorIndex:
      replot = True
      self.detectorIndex = kwargs[ 'detector_index' ]
    #end if

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      replot = True
      self.pinColRow = kwargs[ 'pin_colrow' ]
    #end if

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.dataSetName:
      replot = True
      self.dataSetName = kwargs[ 'pin_dataset' ]
    #end if

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      replot = True
      self.stateIndex = kwargs[ 'state_index' ]
    #end if

    if 'time_dataset' in kwargs:
      replot = True

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
      self.dataSetTypes.clear()
      self.dataSetValues.clear()
      if self.data != None and \
          self.data.IsValid( state_index = self.stateIndex ):
        state_group = self.data.states[ self.stateIndex ].group

        for k in self.dataSetSelections:
	  ds_rec = self.dataSetSelections[ k ]
	  if ds_rec[ 'visible' ] and k in state_group:
	    ds = state_group[ k ]

	    if k in self.data.GetDataSetNames( 'channel' ):
	      valid = self.data.IsValid(
		  assembly_index = self.assemblyIndex,
		  channel_colrow = self.channelColRow
	          )
	      if valid:
		new_values = []
	        for i in range( self.data.core.nax ):
		  new_values.append(
		      ds[ self.channelColRow[ 0 ], self.channelColRow[ 1 ],
			  i, self.assemblyIndex[ 0 ] ]
		      )
	        self.dataSetValues[ k ] = np.array( new_values )
		self.dataSetTypes.add( 'channel' )

	    elif k in self.data.GetDataSetNames( 'detector' ):
	      if self.data.IsValid( detector_index = self.detectorIndex[ 0 ] ):
	        self.dataSetValues[ k ] = ds[ :, self.detectorIndex[ 0 ] ]
		self.dataSetTypes.add( 'detector' )

	    elif k in self.data.GetDataSetNames( 'pin' ):
	      valid = self.data.IsValid(
		  assembly_index = self.assemblyIndex,
		  pin_colrow = self.pinColRow
	          )
	      if valid:
		new_values = []
	        for i in range( self.data.core.nax ):
		  new_values.append(
		      ds[ self.pinColRow[ 0 ], self.pinColRow[ 1 ],
		          i, self.assemblyIndex[ 0 ] ]
		      )
	        self.dataSetValues[ k ] = np.array( new_values )
		self.dataSetTypes.add( 'pin' )
	    #end if category match
	  #end if visible
        #end for each dataset
      #end if valid state

      self._UpdatePlot()
    #end if replot

    elif redraw:
      self.canvas.draw()
  #end _UpdateState

#end AllAxialPlot
