#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		axial_plot.py					-
#	HISTORY:							-
#		2016-05-04	leerw@ornl.gov				-
#	  Supporting auxChannelColRows.
#		2016-04-28	leerw@ornl.gov				-
#	  Supporting auxPinColRows.
#		2016-04-23	leerw@ornl.gov				-
#	  Adding 'Selected ' dataset support.  Moved
#	  _GetSelectedDataSetName() to Widget.
#		2016-04-20	leerw@ornl.gov				-
#		2016-02-19	leerw@ornl.gov				-
#	  Added copy selection.
#		2016-02-11	leerw@ornl.gov				-
#	  Refitting _UpdateDataSetValues() to allow all the new ds_types.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
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
#	CLASS:		AxialPlot					-
#------------------------------------------------------------------------
class AxialPlot( PlotWidget ):
  """Pin axial plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__del__()					-
  #----------------------------------------------------------------------
  def __del__( self ):
    if self.dataSetDialog is not None:
      self.dataSetDialog.Destroy()

    super( AxialPlot, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.auxChannelColRows = []
    self.auxPinColRows = []
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

    super( AxialPlot, self ).__init__( container, id, ref_axis = 'y' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
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

        if ds_rec[ 'visible' ] and ds_name is not None:
	  ds_display_name = self.data.GetDataSetDisplayName( ds_name )
	  ds_type = self.data.GetDataSetType( ds_name )
	  dset = self.data.GetStateDataSet( self.stateIndex, ds_name )
	  dset_array = dset.value if dset is not None else None
	  if dset_array is None:
	    pass

	  #elif ds_display_name in self.data.GetDataSetNames( 'channel' ):
	  elif ds_type.startswith( 'channel' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		axial_level = self.axialValue[ 1 ],
		channel_colrow = self.channelColRow
	        )
	    if valid:
	      if 'channel' not in title_set:
	        title_set.add( 'channel' )
		title += '; Channel=(%d,%d)' % ( 
		    self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1
		    )
	      if cur_selection_flag:
	        values = dset_array[
		    self.channelColRow[ 1 ], self.channelColRow[ 0 ],
		    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
		    ]
	      else:
	        values = dset_array[
		    self.channelColRow[ 1 ], self.channelColRow[ 0 ],
		    :, self.assemblyIndex[ 0 ]
	            ]
	      axial_mesh_datasets.append( ( ds_display_name, values ) )

	  #elif ds_display_name in self.data.GetDataSetNames( 'detector' ):
	  elif ds_type.startswith( 'detector' ):
	    valid = self.data.IsValid(
		axial_level = self.axialValue[ 1 ],
	        detector_index = self.detectorIndex[ 0 ]
		)
	    if valid:
	      if 'detector' not in title_set:
	        title_set.add( 'detector' )
		title += '; Detector=%d' % ( self.detectorIndex[ 0 ] + 1 )

	      if cur_selection_flag:
	        values = \
		    dset_array[ self.axialValue[ 1 ], self.detectorIndex[ 0 ] ]
	      else:
	        values = dset_array[ :, self.detectorIndex[ 0 ] ]
	      detector_mesh_datasets.append( ( ds_display_name, values ) )

	  # deprecated
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

	  #elif ds_display_name in self.data.GetDataSetNames( 'pin' ):
	  elif ds_type.startswith( 'pin' ):
	    valid = self.data.IsValid(
	        assembly_index = self.assemblyIndex,
		axial_level = self.axialValue[ 1 ],
		pin_colrow = self.pinColRow
	        )
	    if valid:
	      if 'pin' not in title_set:
	        title_set.add( 'pin' )
		title += '; Pin=(%d,%d)' % ( 
		    self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1
		    )

	      if cur_selection_flag:
	        values = dset_array[
		    self.pinColRow[ 1 ], self.pinColRow[ 0 ],
		    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
		    ]
	      else:
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

	if cur_selection_flag:
	  j_range = ( self.axialValue[ 1 ], )
	else:
	  j_range = range( len( core.axialMeshCenters ) - 1, -1, -1 )
	for j in j_range:
	  row = '%.7g' % core.axialMeshCenters[ j ]
          for name, values in axial_mesh_datasets:
	    cur_val = 0
	    if not hasattr( values, '__len__' ):
	      if j == self.axialValue[ 1 ]:
	        cur_val = values
	    elif len( values ) > j:
	      cur_val = values[ j ]

	    if cur_val != 0:
	      row += ',%.7g' % cur_val
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

	if cur_selection_flag:
	  j_range = ( self.axialValue[ 2 ], )
	else:
	  j_range = range( len( core.detectorMeshCenters ) - 1, -1, -1 )
	for j in j_range:
	  row = '%.7g' % core.detectorMeshCenters[ j ]
          for name, values in detector_mesh_datasets:
	    cur_val = 0
	    if not hasattr( values, '__len__' ):
	      if j == self.axialValue[ 2 ]:
	        cur_val = values
	    elif len( values ) > j:
	      cur_val = values[ j ]

	    if cur_val != 0:
	      row += ',%.7g' % cur_val
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
    menu_def = super( AxialPlot, self )._CreateMenuDef( data_model )
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
    if ds_values is not None:
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
configuring the grid, plotting, and creating self.axline.
"""
    super( AxialPlot, self )._DoUpdatePlot( wd, ht )

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
          elif bottom_ds_name is None:
	    bottom_ds_name = self._GetDataSetName( k )
      #end for
      if bottom_ds_name is None:
        bottom_ds_name = top_ds_name
	top_ds_name = None

#			-- Configure axes
#			--
      if top_ds_name is not None and self.ax2 is not None:
        self.ax2.set_xlabel( top_ds_name, fontsize = label_font_size )
        #self.ax2.set_xlim( *self.data.GetRange( top_ds_name ) )
	ds_range = self.data.GetRange(
	    top_ds_name,
	    self.stateIndex if self.state.scaleMode == 'state' else -1
	    )
        self.ax2.set_xlim( *ds_range )
	self.ax2.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

      self.ax.set_xlabel( bottom_ds_name, fontsize = label_font_size )
      #self.ax.set_xlim( *self.data.GetRange( bottom_ds_name ) )
      ds_range = self.data.GetRange(
	  bottom_ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
      self.ax.set_xlim( *ds_range )
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

	#ds_def = self.data.GetDataSetDefByName( ds_name )
	#ds_type = ds_def[ 'type' ] if ds_def else ''
	ds_type = self.data.GetDataSetType( ds_name )
	axial_values = self.data.core.axialMeshCenters
	#if ds_name in self.data.GetDataSetNames( 'detector' ):
	if ds_type.startswith( 'detector' ):
	  axial_values = self.data.core.detectorMeshCenters
	  plot_type = '.'
	#elif ds_name in self.data.GetDataSetNames( 'channel' ):
	elif ds_type.startswith( 'channel' ):
	  plot_type = '--'
	elif ds_type.startswith( 'pin' ):
	  plot_type = '-'
	else:
	  plot_type = ':'

	if axial_values is not None:
	  data_set_item = self.dataSetValues[ k ]
	  if not isinstance( data_set_item, dict ):
	    data_set_item = { '': data_set_item }

	  for rc, values in sorted( data_set_item.iteritems() ):
	    if values.size == axial_values.size:
	      cur_values = values
	    else:
	      cur_values = np.ndarray( axial_values.shape, dtype = np.float64 )
	      cur_values.fill( 0.0 )
	      cur_values[ 0 : values.shape[ 0 ] ] = values

	    cur_label = \
	        legend_label + '@' + DataModel.ToAddrString( *rc ) \
	        if rc else legend_label

	    plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	    cur_axis = self.ax2 if rec[ 'axis' ] == 'top' else self.ax
	    cur_axis.plot(
	        cur_values * scale, axial_values, plot_mode,
	        label = cur_label, linewidth = 2
	        )

	    count += 1
	  #end for rc, values
	#end if axial_values is not None:

#o	if axial_values is not None:
#o	  if self.dataSetValues[ k ].size == axial_values.size:
#o	    cur_values = self.dataSetValues[ k ]
#o	  else:
#o	    cur_values = np.ndarray( axial_values.shape, dtype = np.float64 )
#o	    cur_values.fill( 0.0 )
#o	    cur_values[ 0 : self.dataSetValues[ k ].shape[ 0 ] ] = \
#o	        self.dataSetValues[ k ]
#o
#o	  plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
#o	  cur_axis = self.ax2 if rec[ 'axis' ] == 'top' else self.ax
#o	  cur_axis.plot(
#o	      cur_values * scale, axial_values, plot_mode,
#o	      label = legend_label, linewidth = 2
#o	      )
#o
#o	  count += 1
#o	#end if axial_values is not None:
      #end for

#			-- Create legend
#			--
      handles, labels = self.ax.get_legend_handles_labels()
      if self.ax2 is not None:
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
        if self.data.core.detectorMeshCenters is not None:
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
  #	METHOD:		AxialPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      [
      'channel', 'detector',
      'pin', 'pin:assembly', 'pin:axial'
      ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.GetDataSetDisplayMode()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns 'selected'
@return			'selected'
"""
    return  'selected'
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_assemblyIndex,
        STATE_CHANGE_auxChannelColRows, STATE_CHANGE_auxPinColRows,
	STATE_CHANGE_axialValue,
	STATE_CHANGE_channelColRow, STATE_CHANGE_channelDataSet,
	STATE_CHANGE_detectorIndex, STATE_CHANGE_detectorDataSet,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


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
    """Special hook called in VeraViewFrame.LoadDataModel().
"""
    axis = 'bottom'
    for dtype in sorted( list( ds_types ) ):
      self.dataSetSelections[ self.GetSelectedDataSetName( dtype ) ] = \
        { 'axis': axis, 'scale': 1.0, 'visible': True }
      axis = 'top' if axis == 'bottom' else ''
  #end InitDataSetSelections


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.IsDataSetVisible()			-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, ds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  ds_name		dataset name
@return			True if visible, else False
"""
    visible = \
        ds_name in self.dataSetSelections and \
        self.dataSetSelections[ ds_name ][ 'visible' ]
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assume self.data is valid.
@return			dict to be passed to UpdateState()
"""
    self.dataSetDialog = None
    if self.data is not None and self.data.HasData():
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
    super( AxialPlot, self )._OnMplMouseRelease( ev )

    button = ev.button or 1
    if button == 1 and self.cursor is not None:
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
    if self.dataSetDialog is None:
      if self.data is None:
        wx.MessageBox( self, 'No data model', 'Select Datasets' ).ShowModal()
      else:
        ds_names = self.data.GetDataSetNames( 'axial' )
	for dtype in ( 'channel', 'detector', 'pin' ):
	  if len( self.data.GetDataSetNames( dtype ) ) > 0:
	    ds_names.append( self.GetSelectedDataSetName( dtype ) )
	    #ds_names.append( '_' + dtype + 'DataSet_' )
	#end for
	self.dataSetDialog = DataSetChooserDialog( self, ds_names = ds_names )
    #end if

    if self.dataSetDialog is not None:
      self.dataSetDialog.ShowModal( self.dataSetSelections )
      selections = self.dataSetDialog.GetResult()
      if selections is not None:
        self.dataSetSelections = selections
	self.UpdateState( replot = True )
    #end if
  #end _OnSelectDataSets


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot._ResolveDataSetAxes()			-
  #----------------------------------------------------------------------
  def _ResolveDataSetAxes( self ):
    """Allocates top and bottom axis if they are not assigned.
"""
    bottom = None
    top = None
    visible_names = []
    for k, rec in self.dataSetSelections.iteritems():
      if rec[ 'visible' ]:
	visible_names.append( k )
	if rec[ 'axis' ] == 'bottom':
	  bottom = rec
        elif rec[ 'axis' ] == 'top':
	  top = rec
      #end if visible
    #end for

    if bottom is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'top':
	  rec[ 'axis' ] = 'bottom'
	  break
    #end if

    if top is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'bottom':
	  rec[ 'axis' ] = 'top'
	  break
    #end if
  #end _ResolveDataSetAxes


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
#    wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
#    self.FireStateChange( pin_dataset = ds_name )
    pass
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.ToggleDataSetVisible()		-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, ds_name ):
    """Toggles the visibility of the named dataset.
Must be called from the event thread.
@param  ds_name		dataset name, possibly with 'Selected ' prefix
"""
    if ds_name in self.dataSetSelections:
      rec = self.dataSetSelections[ ds_name ]
      rec[ 'visible' ] = not rec[ 'visible' ]

    else:
      self.dataSetSelections[ ds_name ] = \
        { 'axis': '', 'scale': 1.0, 'visible': True }

    self._ResolveDataSetAxes()
    self.UpdateState( replot = True )
  #end ToggleDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot.
"""
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

#		-- Must have data
#		--
    if self.data is not None and self.data.IsValid( state_index = self.stateIndex ):
      axial_ds_names = self.data.GetDataSetNames( 'axial' )

      #chan_colrow_list = list( self.auxChannelColRows )
      #chan_colrow_list.insert( 0, self.channelColRow )
      #pin_colrow_list = list( self.auxPinColRows )
      #pin_colrow_list.insert( 0, self.pinColRow )
      chan_colrow_list = None
      pin_colrow_list = None

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

#				-- Must be visible and an "axial" dataset
#				--
        if ds_rec[ 'visible' ] and ds_name is not None and \
	    ds_name in axial_ds_names:
	  #ds_display_name = self.data.GetDataSetDisplayName( ds_name )
	  ds_type = self.data.GetDataSetType( ds_name )
	  dset = self.data.GetStateDataSet( self.stateIndex, ds_name )
	  dset_array = dset.value \
	      if dset is not None and ds_type is not None  else None

	  if dset_array is None:
	    pass

#					-- Channel
	  elif ds_type.startswith( 'channel' ):
	    assy_ndx = min( self.assemblyIndex[ 0 ], dset_array.shape[ 3 ] - 1 )
#o	    chan_col = min( self.channelColRow[ 0 ], dset_array.shape[ 1 ] - 1 )
#o	    chan_row = min( self.channelColRow[ 1 ], dset_array.shape[ 0 ] - 1 )
#o	    self.dataSetValues[ k ] = \
#o	        dset_array[ chan_row, chan_col, :, assy_ndx ]
#o            self.dataSetTypes.add( 'channel' )
#						-- Lazy creation
	    if chan_colrow_list is None:
              chan_colrow_list = list( self.auxChannelColRows )
              chan_colrow_list.insert( 0, self.channelColRow )

	    chan_colrow_set = set()
	    for colrow in chan_colrow_list:
	      col = min( colrow[ 0 ], dset_array.shape[ 1 ] - 1 )
	      row = min( colrow[ 1 ], dset_array.shape[ 0 ] - 1 )
	      chan_colrow_set.add( ( col, row ) )
              #valid = self.data.IsValidForShape(
	          #dset_array.shape, pin_colrow = self.pinColRow
		  #)
	    #end for
	    ds_values_dict = {}
	    for colrow in sorted( chan_colrow_set ):
	      ds_values_dict[ colrow ] = \
	          dset_array[ colrow[ 1 ], colrow[ 0 ], :, assy_ndx ]

	    self.dataSetValues[ k ] = ds_values_dict
            self.dataSetTypes.add( 'channel' )

#	  elif ds_display_name in self.data.GetDataSetNames( 'channel' ):
#	    valid = self.data.IsValid(
#	        assembly_index = self.assemblyIndex,
#		channel_colrow = self.channelColRow
#	        )
#	    if valid:
#              self.dataSetValues[ k ] = dset_array[
#	          self.channelColRow[ 1 ], self.channelColRow[ 0 ],
#		  :, self.assemblyIndex[ 0 ]
#	          ]
#              self.dataSetTypes.add( 'channel' )

#					-- Detector
	  elif ds_type.startswith( 'detector' ):
	    det_ndx = min( self.detectorIndex[ 0 ], dset_array.shape[ 1 ] )
	    self.dataSetValues[ k ] = dset_array[ :, det_ndx ]
            self.dataSetTypes.add( 'detector' )

#					-- Pin
	  elif ds_type.startswith( 'pin' ):
	    assy_ndx = min( self.assemblyIndex[ 0 ], dset_array.shape[ 3 ] - 1 )
#						-- Lazy creation
	    if pin_colrow_list is None:
              pin_colrow_list = list( self.auxPinColRows )
              pin_colrow_list.insert( 0, self.pinColRow )

	    pin_colrow_set = set()
	    for colrow in pin_colrow_list:
	      col = min( colrow[ 0 ], dset_array.shape[ 1 ] - 1 )
	      row = min( colrow[ 1 ], dset_array.shape[ 0 ] - 1 )
	      pin_colrow_set.add( ( col, row ) )
              #valid = self.data.IsValidForShape(
	          #dset_array.shape, pin_colrow = self.pinColRow
		  #)
	    #end for
	    ds_values_dict = {}
	    for colrow in sorted( pin_colrow_set ):
	      ds_values_dict[ colrow ] = \
	          dset_array[ colrow[ 1 ], colrow[ 0 ], :, assy_ndx ]

	    self.dataSetValues[ k ] = ds_values_dict
            self.dataSetTypes.add( 'pin' )

#	  elif ds_display_name in self.data.GetDataSetNames( 'pin' ):
#	    valid = self.data.IsValid(
#	        assembly_index = self.assemblyIndex,
#		pin_colrow = self.pinColRow
#	        )
#	    if valid:
#	      self.dataSetValues[ k ] = dset_array[
#	          self.pinColRow[ 1 ], self.pinColRow[ 0 ],
#		  :, self.assemblyIndex[ 0 ]
#	          ]
#              self.dataSetTypes.add( 'pin' )
	  #end if ds_type match
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
    kwargs = super( AxialPlot, self )._UpdateStateValues( **kwargs )
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      replot = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]
    #end if

    if 'aux_channel_colrows' in kwargs and \
        kwargs[ 'aux_channel_colrows' ] != self.auxChannelColRows:
      replot = True
      self.auxChannelColRows = self.data.\
          NormalizeChannelColRows( kwargs[ 'aux_channel_colrows' ] )

    if 'aux_pin_colrows' in kwargs and \
        kwargs[ 'aux_pin_colrows' ] != self.auxPinColRows:
      replot = True
      self.auxPinColRows = self.data.\
          NormalizePinColRows( kwargs[ 'aux_pin_colrows' ] )

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
      select_name = self.GetSelectedDataSetName( 'channel' )
      #if '_channelDataSet_' in self.dataSetSelections:
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.detectorDataSet:
      self.detectorDataSet = kwargs[ 'detector_dataset' ]
      select_name = self.GetSelectedDataSetName( 'detector' )
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
      select_name = self.GetSelectedDataSetName( 'pin' )
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

#end AxialPlot
