#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		all_axial_plot.py				-
#	HISTORY:							-
#		2016-02-03	leerw@ornl.gov				-
#	  Fixed handling of derived data in _UpdateDataSetValues().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#	  Added _CreateClipboardData().
#		2016-01-23	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2015-11-20	leerw@ornl.gov				-
#	  Added graceful handling of extra and other datasets.
#		2015-11-19	leerw@ornl.gov				-
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-08-20	leerw@ornl.gov				-
#	  Adding special references for selected datasets.
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-07-08	leerw@ornl.gov				-
#	  Extending PlotWidget.
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

from bean.dataset_chooser import *
from event.state import *

from legend import *
from plot_widget import *
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
class AllAxialPlot( PlotWidget ):
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
    self.axialValue = ( 0.0, -1, -1 )
    self.channelColRow = ( -1, -1 )
    self.channelDataSet = 'channel_liquid_temps [C]'
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by dataset name or pseudo name
    self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name or pseudo name
    self.detectorDataSet = 'detector_respose'
    self.detectorIndex = ( -1, -1, -1 )

#Old Way
#    self.menuDef = \
#      [
#	( 'Copy Data', self._OnCopyData ),
#	( 'Copy Image', self._OnCopyImage ),
#	( '-', None ),
#        ( 'Select Datasets', self._OnSelectDataSets )
#      ]
    self.pinColRow = ( -1, -1 )
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )

    super( AllAxialPlot, self ).__init__( container, id, ref_axis = 'y' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None

    if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
      core = self.data.GetCore()

      title = '%s=%.3g' % (
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )

      title_set = set( [] )
      axial_mesh_datasets = []
      detector_mesh_datasets = []
      detector_mesh_header = 'Detector Mesh Center'

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

        if ds_rec[ 'visible' ] and ds_name != None:
	  ds_display_name = self.data.GetDataSetDisplayName( ds_name )
	  dset = self.data.GetStateDataSet( self.stateIndex, ds_name )
	  dset_array = dset.value if dset != None else None
	  if dset_array == None:
	    pass

	  elif ds_display_name in self.data.GetDataSetNames( 'channel' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		channel_colrow = self.channelColRow
	        )
	    if valid:
	      if 'channel' not in title_set:
	        title_set.add( 'channel' )
		title += '; Channel=(%d,%d)' % ( 
		    self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1
		    )
	      values = dset_array[
		  self.channelColRow[ 1 ], self.channelColRow[ 0 ],
		  :, self.assemblyIndex[ 0 ]
	          ]
	      axial_mesh_datasets.append( ( ds_display_name, values ) )

	  elif ds_display_name in self.data.GetDataSetNames( 'detector' ):
	    if self.data.IsValid( detector_index = self.detectorIndex[ 0 ] ):
	      if 'detector' not in title_set:
	        title_set.add( 'detector' )
		title += '; Detector=%d' % ( self.detectorIndex[ 0 ] + 1 )

	      detector_mesh_datasets.append(
		  ( ds_display_name, dset_array[ :, self.detectorIndex[ 0 ] ] )
	          )

	  elif ds_name in self.data.GetDataSetNames( 'derived' ) or \
	      ds_display_name in self.data.GetDataSetNames( 'extra' ) or \
	      ds_display_name in self.data.GetDataSetNames( 'other' ):
	    valid = self.data.IsValidForShape(
		dset.shape,
		assembly_index = self.assemblyIndex[ 0 ],
		pin_colrow = self.pinColRow
	        )
	    if valid:
	      assy_ndx = min( self.assemblyIndex[ 0 ], dset.shape[ 3 ] - 1 )
	      temp_nax = min( self.data.core.nax, dset.shape[ 2 ] )
	      values = dset_array[
		  self.pinColRow[ 1 ], self.pinColRow[ 0 ],
		  0 : temp_nax, assy_ndx
	          ]
	      axial_mesh_datasets.append( ( ds_display_name, values ) )

	  elif ds_display_name in self.data.GetDataSetNames( 'pin' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		pin_colrow = self.pinColRow
	        )
	    if valid:
	      if 'pin' not in title_set:
	        title_set.add( 'pin' )
		title += '; Pin=(%d,%d)' % ( 
		    self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1
		    )

	      values = dset_array[
		  self.pinColRow[ 1 ], self.pinColRow[ 0 ],
		  :, self.assemblyIndex[ 0 ]
	          ]
	      axial_mesh_datasets.append( ( ds_display_name, values ) )
	  #end if category match
        #end if visible
      #end for each dataset

      #csv_text = '#"%s"\n' % title
      csv_text = '"%s"\n' % title

      if len( axial_mesh_datasets ) > 0:
        header = 'Axial Mesh Center'
        for name, values in axial_mesh_datasets:
	  header += ',' + name
        csv_text += header + '\n'

	for j in range( len( core.axialMeshCenters ) - 1, -1, -1 ):
	  row = '%.7g' % core.axialMeshCenters[ j ]
          for name, values in axial_mesh_datasets:
	    if len( values ) > j:
	      row += ',%.7g' % values[ j ]
	    else:
	      row += ',0'
          #end for name, values

          csv_text += row + '\n'
	#end for j

	csv_text += '\n'
      #end if

      if len( detector_mesh_datasets ) > 0:
        header = 'Detector Mesh Center'
        for name, values in detector_mesh_datasets:
	  header += ',' + name
        csv_text += header + '\n'

	for j in range( len( core.detectorMeshCenters ) - 1, -1, -1 ):
	  row = '%.7g' % core.detectorMeshCenters[ j ]
          for name, values in detector_mesh_datasets:
	    if len( values ) >= j:
	      row += ',%.7g' % values[ j ]
	    else:
	      row += ',0'
          #end for name, values

          csv_text += row + '\n'
	#end for j
      #end if
    #end if valid state

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( AllAxialPlot, self )._CreateMenuDef( data_model )
    more_def = \
      [
	( '-', None ),
        ( 'Select Datasets', self._OnSelectDataSets )
      ]
    return  menu_def + more_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		_CreateToolTipText()				-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		mouse motion event
"""
    tip_str = ''
    ds_values = self._FindDataSetValues( ev.ydata )
    if ds_values != None:
      tip_str = 'Axial=%.3g' % ev.ydata
#      ds_keys = ds_values.keys()
#      ds_keys.sort()
#      for k in ds_keys:
      for k in sorted( ds_values.keys() ):
        tip_str += '\n%s=%.3g' % ( k, ds_values[ k ] )

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
    super( AllAxialPlot, self )._DoUpdatePlot( wd, ht )

    self.fig.suptitle(
        'Axial Plot',
	fontsize = 'medium', fontweight = 'bold'
	)

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
      for k, rec in self.dataSetSelections.iteritems():
	if rec[ 'visible' ]:
          if rec[ 'axis' ] == 'bottom':
	    bottom_ds_name = self._GetDataSetName( k )
          elif rec[ 'axis' ] == 'top':
	    top_ds_name = self._GetDataSetName( k )
          elif bottom_ds_name == None:
	    bottom_ds_name = self._GetDataSetName( k )
      #end for
      if bottom_ds_name == None:
        bottom_ds_name = top_ds_name
	top_ds_name = None

#			-- Configure axes
#			--
      if top_ds_name != None and self.ax2 != None:
        self.ax2.set_xlabel( top_ds_name, fontsize = label_font_size )
        self.ax2.set_xlim( *self.data.GetRange( top_ds_name ) )
	self.ax2.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

      self.ax.set_xlabel( bottom_ds_name, fontsize = label_font_size )
      self.ax.set_xlim( *self.data.GetRange( bottom_ds_name ) )
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      self.ax.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#			-- Set title
#			--
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] )

      title_str = 'Assy %d %s, %s %.3g' % \
          ( self.assemblyIndex[ 0 ] + 1, show_assy_addr,
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )

      title_line2 = ''
      if 'channel' in self.dataSetTypes:
	chan_rc = ( self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1 )
        title_line2 += 'Chan %s' % str( chan_rc )

      if 'detector' in self.dataSetTypes: # and self.detectorIndex[ 0 ] >= 0
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Det %d %s' % \
	    ( self.detectorIndex[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ) )

      #if 'pin' in self.dataSetTypes: # and self.detectorIndex[ 0 ] >= 0
      if 'pin' in self.dataSetTypes or 'other' in self.dataSetTypes:
        pin_rc = ( self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1 )
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Pin %s' % str( pin_rc )

      if len( title_line2 ) > 0:
        title_str += '\n' + title_line2

#			-- Plot each selected dataset
#			--
      count = 0
      for k in self.dataSetValues:
	ds_name = self.data.GetDataSetDisplayName( self._GetDataSetName( k ) )
	rec = self.dataSetSelections[ k ]
	scale = rec[ 'scale' ] if rec[ 'axis' ] == '' else 1.0
	legend_label = ds_name
	if scale != 1.0:
	  legend_label += '*%.3g' % scale

	if ds_name in self.data.GetDataSetNames( 'detector' ):
	  axial_values = self.data.core.detectorMeshCenters
	  plot_type = '.'
#	elif self.dataSetValues[ k ].size != self.data.core.axialMeshCenters.size:
#	  axial_values = None
	else:
	  axial_values = self.data.core.axialMeshCenters
	  plot_type = '-'

	if axial_values != None:
	  if self.dataSetValues[ k ].size == axial_values.size:
	    cur_values = self.dataSetValues[ k ]
	  else:
	    cur_values = np.ndarray( axial_values.shape, dtype = np.float64 )
	    cur_values.fill( 0.0 )
	    cur_values[ 0 : self.dataSetValues[ k ].shape[ 0 ] ] = \
	        self.dataSetValues[ k ]

	  plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	  cur_axis = self.ax2 if rec[ 'axis' ] == 'top' else self.ax
	  cur_axis.plot(
	      cur_values * scale, axial_values, plot_mode,
	      label = legend_label, linewidth = 2
	      )
	#end if axial_values != None:

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
      self.axline = \
          self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
      self.axline.set_ydata( self.axialValue[ 0 ] )
    #end if we have something to plot
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, axial_cm ):
    """Find matching dataset values for the axial.
@param  axial_cm	axial value
@return			dict by real dataset name (not pseudo name) of
			dataset values or None if no matches
"""

    values = {}
    for k in self.dataSetValues:
      ndx = -1
      ds_name = self._GetDataSetName( k )

      if ds_name in self.data.GetDataSetNames( 'detector' ):
        if self.data.core.detectorMeshCenters != None:
	  ndx = self.data.FindListIndex( self.data.core.detectorMeshCenters, axial_cm )
      else:
        ndx = self.data.FindListIndex( self.data.core.axialMeshCenters, axial_cm )
      if ndx >= 0 and len( self.dataSetValues[ k ] ) > ndx:
        values[ ds_name ] = self.dataSetValues[ k ][ ndx ]
    #end for

    return  values
  #end _FindDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint', )
    #return  ( 'axial:detector', 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		_GetDataSetName()				-
  #----------------------------------------------------------------------
  def _GetDataSetName( self, name ):
    """Determines actual dataset name if a pseudo name is provided.
"""
    return \
	self.channelDataSet  if name == 'Selected channel dataset' else \
        self.detectorDataSet  if name == 'Selected detector dataset' else \
        self.pinDataSet  if name == 'Selected pin dataset' else \
	name
#    return \
#	self.channelDataSet  if name == '_channelDataSet_' else \
#	self.detectorDataSet  if name == '_detectorDataSet_' else \
#        self.pinDataSet  if name == '_pinDataSet_' else \
#	name
  #end _GetDataSetName


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
	STATE_CHANGE_channelColRow, STATE_CHANGE_channelDataSet,
	STATE_CHANGE_detectorIndex, STATE_CHANGE_detectorDataSet,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		_GetSelectedDataSetName()			-
  #----------------------------------------------------------------------
  def _GetSelectedDataSetName( self, dtype ):
    """
@param  dtype		dataset type/category
"""
    return  'Selected ' + dtype + ' dataset'
  #end _GetSelectedDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Axial Plots'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes, 'ax', and 'ax2'.
XXX size according to how many datasets selected?
"""
    self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
    self.ax2 = self.ax.twiny() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		InitDataSetSelections()				-
  #----------------------------------------------------------------------
  def InitDataSetSelections( self, ds_types ):
    """
"""
    axis = 'bottom'
    for dtype in sorted( list( ds_types ) ):
      self.dataSetSelections[ self._GetSelectedDataSetName( dtype ) ] = \
        { 'axis': axis, 'scale': 1.0, 'visible': True }
      axis = 'top' if axis == 'bottom' else ''
  #end InitDataSetSelections


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assume self.data is valid.
@return			dict to be passed to UpdateState()
"""
    self.dataSetDialog = None
    if self.data != None and self.data.HasData():
      assy_ndx = self.data.NormalizeAssemblyIndex( self.state.assemblyIndex )
      axial_value = self.data.NormalizeAxialValue( self.state.axialValue )
      chan_colrow = self.data.NormalizeChannelColRow( self.state.channelColRow )
      detector_ndx = self.data.NormalizeDetectorIndex( self.state.detectorIndex )
      pin_colrow = self.data.NormalizePinColRow( self.state.pinColRow )
      state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'assembly_index': assy_ndx,
	'axial_value': axial_value,
	'channel_colrow': chan_colrow,
	'channel_dataset': self.state.channelDataSet,
	'detector_dataset': self.state.detectorDataSet,
	'detector_index': detector_ndx,
	'pin_colrow': pin_colrow,
	'pin_dataset': self.state.pinDataSet,
	'state_index': state_ndx,
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
    super( AllAxialPlot, self )._OnMplMouseRelease( ev )

    button = ev.button or 1
    if button == 1 and self.cursor != None:
      axial_value = self.data.CreateAxialValue( value = self.cursor[ 1 ] )
      self.UpdateState( axial_value = axial_value )
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
	for dtype in ( 'channel', 'detector', 'pin' ):
	  if len( self.data.GetDataSetNames( dtype ) ) > 0:
	    ds_names.append( self._GetSelectedDataSetName( dtype ) )
	    #ds_names.append( '_' + dtype + 'DataSet_' )
	#end for
	self.dataSetDialog = DataSetChooserDialog( self, ds_names = ds_names )
    #end if

    if self.dataSetDialog != None:
      self.dataSetDialog.ShowModal( self.dataSetSelections )
      selections = self.dataSetDialog.GetResult()
      if selections != None:
        self.dataSetSelections = selections
	self.UpdateState( replot = True )
    #end if
  #end _OnSelectDataSets


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
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot.
"""
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

    if self.data != None and self.data.IsValid( state_index = self.stateIndex ):
      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

        if ds_rec[ 'visible' ] and ds_name != None:
	  ds_display_name = self.data.GetDataSetDisplayName( ds_name )
	  dset = self.data.GetStateDataSet( self.stateIndex, ds_name )
	  dset_array = dset.value if dset != None else None
	  if dset_array == None:
	    pass

	  elif ds_display_name in self.data.GetDataSetNames( 'channel' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		channel_colrow = self.channelColRow
	        )
	    if valid:
              self.dataSetValues[ k ] = dset_array[
	          self.channelColRow[ 1 ], self.channelColRow[ 0 ],
		  :, self.assemblyIndex[ 0 ]
	          ]
              self.dataSetTypes.add( 'channel' )

	  elif ds_display_name in self.data.GetDataSetNames( 'detector' ):
	    if self.data.IsValid( detector_index = self.detectorIndex[ 0 ] ):
	      self.dataSetValues[ k ] = dset_array[ :, self.detectorIndex[ 0 ] ]
              self.dataSetTypes.add( 'detector' )

	  elif ds_name in self.data.GetDataSetNames( 'derived' ) or \
	      ds_display_name in self.data.GetDataSetNames( 'extra' ) or \
	      ds_display_name in self.data.GetDataSetNames( 'other' ):
	    valid = self.data.IsValidForShape(
		dset.shape,
		assembly_index = self.assemblyIndex[ 0 ],
		pin_colrow = self.pinColRow
	        )
	    if valid:
	      assy_ndx = min( self.assemblyIndex[ 0 ], dset.shape[ 3 ] - 1 )
	      temp_nax = min( self.data.core.nax, dset.shape[ 2 ] )
	      self.dataSetValues[ k ] = dset_array[
	          self.pinColRow[ 1 ], self.pinColRow[ 0 ],
	          0 : temp_nax, assy_ndx
	          ]
              self.dataSetTypes.add( 'other' )

	  elif ds_display_name in self.data.GetDataSetNames( 'pin' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		pin_colrow = self.pinColRow
	        )
	    if valid:
	      self.dataSetValues[ k ] = dset_array[
	          self.pinColRow[ 1 ], self.pinColRow[ 0 ],
		  :, self.assemblyIndex[ 0 ]
	          ]
              self.dataSetTypes.add( 'pin' )
	  #end if category match
        #end if visible
      #end for each dataset
    #end if valid state
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
    kwargs = super( AllAxialPlot, self )._UpdateStateValues( **kwargs )
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      replot = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]
    #end if

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      replot = True
      self.axialValue = kwargs[ 'axial_value' ]
    #end if

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] != self.channelColRow:
      replot = True
      self.channelColRow = kwargs[ 'channel_colrow' ]
    #end if

    if 'channel_dataset' in kwargs and kwargs[ 'channel_dataset' ] != self.channelDataSet:
      self.channelDataSet = kwargs[ 'channel_dataset' ]
      select_name = self._GetSelectedDataSetName( 'channel' )
      #if '_channelDataSet_' in self.dataSetSelections:
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.detectorDataSet:
      self.detectorDataSet = kwargs[ 'detector_dataset' ]
      select_name = self._GetSelectedDataSetName( 'detector' )
      #if '_detectorDataSet_' in self.dataSetSelections:
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'detector_index' in kwargs and kwargs[ 'detector_index' ] != self.detectorIndex:
      replot = True
      self.detectorIndex = kwargs[ 'detector_index' ]
    #end if

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      replot = True
      self.pinColRow = kwargs[ 'pin_colrow' ]
    #end if

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      self.pinDataSet = kwargs[ 'pin_dataset' ]
      select_name = self._GetSelectedDataSetName( 'pin' )
      #if '_pinDataSet_' in self.dataSetSelections:
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'time_dataset' in kwargs:
      replot = True

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end AllAxialPlot
