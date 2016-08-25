#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		axial_plot.py					-
#	HISTORY:							-
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-23	leerw@ornl.gov				-
#	  Adding user-selectable scaling mode.
#	  Redefined menu definitions with dictionaries.
#		2016-07-07	leerw@ornl.gov				-
#	  Renaming "vanadium" to "fixed_detector".
#		2016-06-30	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-06-07	leerw@ornl.gov				-
#	  Fixed header in _CreateClipboardData().
#		2016-06-06	leerw@ornl.gov				-
#	  Improved/simplified _CreateClipboardData().
#		2016-05-25	leerw@ornl.gov				-
#	  Plotting vanadium dataset.
#		2016-05-19	leerw@ornl.gov				-
#	  Fixed _CreateToolTipText() and _FindDataSetValues() to handle
#	  the new auxiliary selections.
#	  Creating PlotDataSetPropsDialog instead of DataSetChooserDialog.
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

#from bean.dataset_chooser import *
from bean.plot_dataset_props import *
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
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxSubAddrs = []
    self.ax2 = None
    self.axialValue = DataModel.CreateEmptyAxialValue()
    #self.channelDataSet = 'channel_liquid_temps [C]'
    self.curDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by dataset name or pseudo name
    self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name or pseudo name
    #self.detectorDataSet = 'detector_response'
    #self.detectorIndex = ( -1, -1, -1 )
    #self.fixedDetectorDataSet = 'fixed_detector_response'
    #self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.scaleMode = 'selected'
    self.subAddr = ( -1, -1 )

    super( AxialPlot, self ).__init__( container, id, ref_axis = 'y' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateCsvDataRows()				-
  #----------------------------------------------------------------------
  def _CreateCsvDataRows(
      self, axial_mesh_type, cur_selection_flag, dataset_dict
      ):
    """Creates CSV rows for the specified mesh type and associated
dataset names and ( rc, values ) pairs.
@param  axial_mesh_type	'axial', 'detector', or 'fixed_detector'
@param  cur_selection_flag  True to only show data for the current selection
@param  dataset_dict	dict by dataset name of [ ( rc, values ) ]
@return			CSV text
"""
    csv_text = ''
    core = self.data.GetCore()

#		-- Write header row
#		--
    if axial_mesh_type == 'detector':
      header = 'Detector'
      cur_axial_index = self.axialValue[ 2 ]
      mesh_centers = core.detectorMeshCenters
    elif axial_mesh_type == 'fixed_detector':
      header = 'Fixed Detector'
      cur_axial_index = self.axialValue[ 3 ]
      mesh_centers = core.fixedDetectorMeshCenters
    else:
      header = 'Axial'
      cur_axial_index = self.axialValue[ 1 ]
      mesh_centers = core.axialMeshCenters
    header += ' Mesh Center'

    for name, item in sorted( dataset_dict.iteritems() ):
      for rc in sorted( item.keys() ):
        header += ',"' + name
	if rc:
          header += '@' + DataModel.ToAddrString( *rc )
        header += '"'
    csv_text += header + '\n'

    if cur_selection_flag:
      j_range = ( cur_axial_index, )
    else:
      j_range = range( len( mesh_centers ) - 1, -1, -1 )

    for j in j_range:
      row = '%.7g' % mesh_centers[ j ]

      for name, item in sorted( dataset_dict.iteritems() ):
        for rc, values in sorted( item.iteritems() ):
	  cur_val = 0
	  if not hasattr( values, '__len__' ):
	    if j == cur_axial_index:
	      cur_val = values
	  elif len( values ) > j:
	    cur_val = values[ j ]

	  if cur_val != 0:
	    row += ',%.7g' % cur_val
	  else:
	    row += ',0'
        #end for rc, values
      #end for name, values

      csv_text += row + '\n'
    #end for j

    csv_text += '\n'
    return  csv_text
  #end _CreateCsvDataRows


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    cur_selection_flag = mode != 'displayed'

#		-- Must be valid state
#		--
    if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
      core = self.data.GetCore()

      title = '%s=%.3g' % (
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )

      title_set = set( [] )
      axial_mesh_datasets = {}
      detector_mesh_datasets = {}
      fixed_detector_mesh_datasets = {}

#		 	-- Collate by mesh type
#		 	--
      for k in self.dataSetValues:
	ds_name = self._GetDataSetName( k )
	ds_rec = self.dataSetSelections[ k ]

        if ds_rec[ 'visible' ] and ds_name is not None:
	  ds_display_name = self.data.GetDataSetDisplayName( ds_name )
	  ds_type = self.data.GetDataSetType( ds_name )

          data_set_item = self.dataSetValues[ k ]
	  if not isinstance( data_set_item, dict ):
	    data_set_item = { '': data_set_item }

	  if ds_type.startswith( 'channel' ):
	    if 'channel' not in title_set:
	      title_set.add( 'channel' )
	      title += '; Channel=(%d,%d)' % ( 
	          self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1
		  )
	    axial_mesh_datasets[ ds_display_name ] = data_set_item

	  elif ds_type.startswith( 'detector' ):
	    if 'detector' not in title_set:
	      title_set.add( 'detector' )
	      title += '; Detector=%d' % ( self.assemblyAddr[ 0 ] + 1 )
	    detector_mesh_datasets[ ds_display_name ] = data_set_item

	  elif ds_type.startswith( 'fixed_detector' ):
	    if 'detector' not in title_set:
	      title_set.add( 'detector' )
	      title += '; Detector=%d' % ( self.assemblyAddr[ 0 ] + 1 )
	    fixed_detector_mesh_datasets[ ds_display_name ] = data_set_item

	  else:
	    if 'pin' not in title_set:
	      title_set.add( 'pin' )
	      title += '; Pin=(%d,%d)' % ( 
	          self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1
		  )
	    axial_mesh_datasets[ ds_display_name ] = data_set_item
          #end if-else type
	#end if visible
      #end for k

#		 	-- Create CSV
#		 	--
      csv_text = '"%s"\n' % title

      if len( axial_mesh_datasets ) > 0:
	csv_text += self._CreateCsvDataRows( 
	    'axial', cur_selection_flag, axial_mesh_datasets
	    )

      if len( detector_mesh_datasets ) > 0:
	csv_text += self._CreateCsvDataRows( 
	    'detector', cur_selection_flag, detector_mesh_datasets
	    )

      if len( fixed_detector_mesh_datasets ) > 0:
	csv_text += self._CreateCsvDataRows( 
	    'fixed_detector', cur_selection_flag, fixed_detector_mesh_datasets
	    )
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

    select_scale_def = \
      [
        {
	'label': 'All Datasets', 'kind': wx.ITEM_RADIO,
	'handler': functools.partial( self._OnSetScaleMode, 'all' )
	},
        {
	'label': LABEL_selectedDataSet, 'kind': wx.ITEM_RADIO, 'checked': True,
	'handler': functools.partial( self._OnSetScaleMode, 'selected' )
	}
      ]

    more_def = \
      [
        { 'label': '-' },
	{
	'label': 'Edit Dataset Properties...',
	'handler': self._OnEditDataSetProps
	},
	{
	'label': 'Select Bottom Axis Scale Mode',
	'submenu': select_scale_def
	}
      ]
#    more_def = \
#      [
#	( '-', None ),
#        ( 'Edit Dataset Properties', self._OnEditDataSetProps )
#        ( 'Select Bottom Axis Scale Mode', select_scale_def )
#        #( 'Select Datasets', self._OnSelectDataSets )
#      ]
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
      for k in sorted( ds_values.keys() ):
#        tip_str += '\n%s=%.3g' % ( k, ds_values[ k ] )
        data_set_item = ds_values[ k ]
	#if not isinstance( data_set_item, dict ):
	  #data_set_item = { '': data_set_item }
	for rc, value in sorted( data_set_item.iteritems() ):
	  cur_label = \
	      k + '@' + DataModel.ToAddrString( *rc ) \
	      if rc else k
	  tip_str += '\n%s=%.3g' % ( cur_label, value )
	#end for rc, value
      #end for k
    #end if ds_values is not None:

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

#    self.fig.suptitle(
#        'Axial Plot',
#	fontsize = 'medium', fontweight = 'bold'
#	)

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
#      bottom_ds_name = top_ds_name = None
#      for k, rec in self.dataSetSelections.iteritems():
#	if rec[ 'visible' ]:
#          if rec[ 'axis' ] == 'bottom':
#	    bottom_ds_name = self._GetDataSetName( k )
#          elif rec[ 'axis' ] == 'top':
#	    top_ds_name = self._GetDataSetName( k )
#          elif bottom_ds_name is None:
#	    bottom_ds_name = self._GetDataSetName( k )
#      #end for
#      if bottom_ds_name is None:
#        bottom_ds_name = top_ds_name
      bottom_ds_name, top_ds_name = self._ResolveDataSetAxes()

#			-- Configure axes
#			--
#				-- Top
      if top_ds_name is not None and self.ax2 is not None:
        self.ax2.set_xlabel( top_ds_name, fontsize = label_font_size )
	ds_range = self.data.GetRange(
	    top_ds_name,
	    self.stateIndex if self.state.scaleMode == 'state' else -1
	    )
	if self.data.IsValidRange( *ds_range ):
          self.ax2.set_xlim( *ds_range )
	  self.ax2.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#				-- Bottom, primary
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      self.ax.set_xlabel( bottom_ds_name, fontsize = label_font_size )
      ds_range = self.data.GetRange(
	  bottom_ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
#					-- Scale over all plotted datasets?
      if self.scaleMode == 'all':
        for k in self.dataSetValues:
	  cur_name = self._GetDataSetName( k )
	  if cur_name != top_ds_name and cur_name != bottom_ds_name:
	    cur_range = self.data.GetRange(
	        cur_name,
	        self.stateIndex if self.state.scaleMode == 'state' else -1
	        )
	    ds_range = (
	        min( ds_range[ 0 ], cur_range[ 0 ] ),
		max( ds_range[ 1 ], cur_range[ 1 ] )
	        )
        #end for k

      if self.data.IsValidRange( *ds_range ):
        self.ax.set_xlim( *ds_range )
        self.ax.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#			-- Set title
#			--
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )

      title_str = 'Assy %d %s, %s %.3g' % \
          ( self.assemblyAddr[ 0 ] + 1, show_assy_addr,
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )

      title_line2 = ''
      chan_flag = 'channel' in self.dataSetTypes
      pin_flag = 'pin' in self.dataSetTypes
      if chan_flag or pin_flag:
	rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
	prefix = \
	    'Chan/Pin'  if chan_flag and pin_flag else \
	    'Chan'  if chan_flag else \
	    'Pin'
        title_line2 += '%s %s' % ( prefix, str( rc ) )

      #if 'detector' in self.dataSetTypes: # and self.assemblyAddr[ 0 ] >= 0
      if 'detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Det %d %s' % \
	    ( self.assemblyAddr[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ) )

#      if 'pin' in self.dataSetTypes or 'other' in self.dataSetTypes:
#        pin_rc = ( self.pinsubAddr[ 0 ] + 1, self.pinsubAddr[ 1 ] + 1 )
#        if len( title_line2 ) > 0: title_line2 += ', '
#	title_line2 += 'Pin %s' % str( pin_rc )

      if 'fixed_detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Van %d %s' % \
	    ( self.assemblyAddr[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ) )

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

	marker_size = None
	ds_type = self.data.GetDataSetType( ds_name )
	axial_values = self.data.core.axialMeshCenters
	if ds_type.startswith( 'detector' ):
	  axial_values = self.data.core.detectorMeshCenters
	  marker_size = 12
	  plot_type = '.'
	elif ds_type.startswith( 'channel' ):
	  plot_type = '--'
	elif ds_type.startswith( 'pin' ):
	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  axial_values = self.data.core.fixedDetectorMeshCenters
	  marker_size = 12
	  plot_type = 'x'
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
	    if cur_axis:
	      if marker_size is not None:
	        cur_axis.plot(
	            cur_values * scale, axial_values, plot_mode,
	            label = cur_label, linewidth = 2,
		    markersize = marker_size
	            )
	      else:
	        cur_axis.plot(
	            cur_values * scale, axial_values, plot_mode,
	            label = cur_label, linewidth = 2
	            )

	    count += 1
	  #end for rc, values
	#end if axial_values is not None:
      #end for k

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

      #xxxplacement orig=0.925, tried=0.975
      self.fig.text(
          0.1, 0.985, title_str,
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
    results = {}
    for k in self.dataSetValues:
      ds_name = self._GetDataSetName( k )

      data_set_item = self.dataSetValues[ k ]
      if not isinstance( data_set_item, dict ):
        data_set_item = { '': data_set_item }

      ndx = -1
      #x call data.CreateAxialValue() here?
      if ds_name in self.data.GetDataSetNames( 'detector' ):
        if self.data.core.detectorMeshCenters is not None:
	  ndx = self.data.FindListIndex( self.data.core.detectorMeshCenters, axial_cm )
      elif ds_name in self.data.GetDataSetNames( 'fixed_detector' ):
        if self.data.core.fixedDetectorMeshCenters is not None:
	  ndx = self.data.FindListIndex( self.data.core.fixedDetectorMeshCenters, axial_cm )
      else:
        ndx = self.data.FindListIndex( self.data.core.axialMeshCenters, axial_cm )

      sample = data_set_item.itervalues().next()
      if ndx >= 0 and len( sample ) > ndx:
	cur_dict = {}
        for rc, values in data_set_item.iteritems():
	  cur_dict[ rc ] = values[ ndx ]

	results[ ds_name ] = cur_dict
      #end if ndx in range
    #end for k

    return  results
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
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index
			  0-based fixed_detector index )
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
        None  if name is None else \
	self.curDataSet  if name == LABEL_selectedDataSet else \
	name

#    return \
#	None  if name is None else \
#	self.channelDataSet  if name == 'Selected channel dataset' else \
#        self.detectorDataSet  if name == 'Selected detector dataset' else \
#        self.pinDataSet  if name == 'Selected pin dataset' else \
#        self.fixedDetectorDataSet  if name == 'Selected fixed_detector dataset' else \
#	name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      [
      'channel', 'detector',
      'pin', 'pin:assembly', 'pin:axial',
      'fixed_detector'
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
	STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_stateIndex
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
    #self.ax = self.fig.add_axes([ 0.1, 0.12, 0.85, 0.68 ])
    #self.ax = self.fig.add_axes([ 0.1, 0.12, 0.8, 0.68 ])
    self.ax = self.fig.add_axes([ 0.12, 0.12, 0.82, 0.7 ])
    self.ax2 = self.ax.twiny() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.InitDataSetSelections()		-
  #----------------------------------------------------------------------
  def InitDataSetSelections( self, ds_types ):
    """Special hook called in VeraViewFrame.LoadDataModel().
"""
    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'bottom', 'scale': 1.0, 'visible': True }
#Back to single selection
#    axis = 'bottom'
#    for dtype in sorted( list( ds_types ) ):
#      if self.data.HasDataSetType( dtype ):
#        self.dataSetSelections[ self.GetSelectedDataSetName( dtype ) ] = \
#          { 'axis': axis, 'scale': 1.0, 'visible': True }
#        axis = 'top' if axis == 'bottom' else ''
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
    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'bottom', 'scale': 1.0, 'visible': True }
    self.dataSetDialog = None

    if self.data is not None and self.data.HasData():
      assy_addr = self.data.NormalizeAssemblyAddr( self.state.assemblyAddr )
      aux_sub_addrs = self.data.\
          NormalizeSubAddrs( self.state.auxSubAddrs, mode = 'channel' )
      axial_value = self.data.NormalizeAxialValue( self.state.axialValue )
      sub_addr = \
          self.data.NormalizeSubAddr( self.state.subAddr, mode = 'channel' )
      #detector_ndx = self.data.NormalizeDetectorIndex( self.state.assemblyAddr )
      state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'assembly_addr': assy_addr,
	'aux_sub_addrs': aux_sub_addrs,
	'axial_value': axial_value,
	'cur_dataset': self.state.curDataSet,
	'state_index': state_ndx,
	'sub_addr': sub_addr,
	'time_dataset': self.state.timeDataSet
	}

    else:
      update_args = {}

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in (
	'assemblyAddr', 'auxSubAddrs', 'axialValue',
	'curDataSet', 'dataSetSelections', 'scaleMode', 'subAddr'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( AxialPlot, self ).LoadProps( props_dict )

#		-- Update scale mode radio menu item
#		--
    labels = [
        'Select Bottom Axis Scale Mode',
	'All Datasets' if self.scaleMode == 'all' else LABEL_selectedDataSet
	]
    select_item = \
        self.container.FindMenuItem( self.container.GetWidgetMenu(), *labels )
    if select_item:
      select_item.Check()

    wx.CallAfter( self.UpdateState, replot = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnEditDataSetProps()				-
  #----------------------------------------------------------------------
  def _OnEditDataSetProps( self, ev ):
    """Must be called from the UI thread.
"""
    if self.dataSetDialog is None:
      self.dataSetDialog = PlotDataSetPropsDialog( self )

    if self.dataSetDialog is not None:
      #axial_ds_names = self.data.GetDataSetNames( 'axial' )
      self.dataSetDialog.ShowModal( self.dataSetSelections )
      selections = self.dataSetDialog.GetProps()
      if selections:
        for name in self.dataSetSelections:
	  if name in selections:
	    ds_rec = self.dataSetSelections[ name ]
	    sel_rec = selections[ name ]
	    ds_rec[ 'axis' ] = sel_rec[ 'axis' ]
	    ds_rec[ 'scale' ] = sel_rec[ 'scale' ]
	#end for

	self.UpdateState( replot = True )
    #end if
  #end _OnEditDataSetProps


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
  #	METHOD:		AxialPlot._OnSetScaleMode()			-
  #----------------------------------------------------------------------
  def _OnSetScaleMode( self, mode, ev ):
    """Must be called from the UI thread.
@param  mode		'all' or 'selected', defaulting to 'selected'
"""
    if mode != self.scaleMode:
      self.scaleMode = mode
      self.UpdateState( replot = True )
    #end if mode changed
  #end _OnSetScaleMode


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot._ResolveDataSetAxes()			-
  #----------------------------------------------------------------------
  def _ResolveDataSetAxes( self ):
    """Allocates top and bottom axis if they are not assigned.
@return			( bottom, top )
"""
    bottom = bottom_name = None
    top = top_name = None
    visible_names = []
    for k, rec in self.dataSetSelections.iteritems():
      if rec[ 'visible' ]:
	visible_names.append( k )
	if rec[ 'axis' ] == 'bottom':
	  bottom = rec
	  bottom_name = k
        elif rec[ 'axis' ] == 'top':
	  top = rec
	  top_name = k
      #end if visible
    #end for

    if bottom is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'top':
	  rec[ 'axis' ] = 'bottom'
	  bottom_name = name
	  bottom = rec
	  break
    #end if

    if top is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'bottom':
	  rec[ 'axis' ] = 'top'
	  top_name = name
	  top = rec
	  break
    #end if

#		-- Special case, only top, must make it bottom
#		--
    if bottom is None and top is not None:
      top[ 'axis' ] = 'bottom'
      bottom_name = top_name
      top_name = None

    return  \
      ( self._GetDataSetName( bottom_name ), self._GetDataSetName( top_name ) )
  #end _ResolveDataSetAxes


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( AxialPlot, self ).SaveProps( props_dict )

    for k in (
	'assemblyAddr', 'auxSubAddrs', 'axialValue',
	'dataSetSelections', 'scaleMode', 'subAddr'
	):
      props_dict[ k ] = getattr( self, k )

    if self.data is not None:
      for k in ( 'curDataSet', ):
	props_dict[ k ] = self.data.RevertIfDerivedDataSet( getattr( self, k ) )
  #end SaveProps


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
      if rec[ 'visible' ]:
        rec[ 'axis' ] = ''
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
    #if self.data is not None and self.data.IsValid( state_index = self.stateIndex ):
    if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
      axial_ds_names = self.data.GetDataSetNames( 'axial' )

      sub_addr_list = None

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

#				-- Must be visible and an "axial" dataset
#				--
        if ds_rec[ 'visible' ] and ds_name is not None and \
	    ds_name in axial_ds_names:
	  ds_values = None
	  ds_type = self.data.GetDataSetType( ds_name )

	  if ds_name in self.dataSetValues:
	    ds_values = self.dataSetValues[ ds_name ]

#					-- Channel
	  elif ds_type.startswith( 'channel' ):
#						-- Lazy creation
	    if sub_addr_list is None:
              sub_addr_list = list( self.auxSubAddrs )
              sub_addr_list.insert( 0, self.subAddr )

	    ds_values = self.data.ReadDataSetAxialValues(
	        ds_name,
		assembly_index = self.assemblyAddr[ 0 ],
		sub_addrs = sub_addr_list,
		state_index = self.stateIndex
		)
            self.dataSetTypes.add( 'channel' )

#					-- Detector
	  elif ds_type.startswith( 'detector' ):
	    ds_values = self.data.ReadDataSetAxialValues(
	        ds_name,
		detector_index = self.assemblyAddr[ 0 ],
		state_index = self.stateIndex
		)
            self.dataSetTypes.add( 'detector' )

#					-- Pin
	  elif ds_type.startswith( 'pin' ):
#						-- Lazy creation
	    if sub_addr_list is None:
              sub_addr_list = list( self.auxSubAddrs )
              sub_addr_list.insert( 0, self.subAddr )

	    ds_values = self.data.ReadDataSetAxialValues(
	        ds_name,
		assembly_index = self.assemblyAddr[ 0 ],
		sub_addrs = sub_addr_list,
		state_index = self.stateIndex
		)
            self.dataSetTypes.add( 'pin' )

#					-- Fixed detector
	  elif ds_type.startswith( 'fixed_detector' ):
	    ds_values = self.data.ReadDataSetAxialValues(
	        ds_name,
		detector_index = self.assemblyAddr[ 0 ],
		state_index = self.stateIndex
		)
            self.dataSetTypes.add( 'fixed_detector' )
	  #end if ds_type match

	  if ds_values is not None:
	    self.dataSetValues[ k ] = ds_values
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

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      replot = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
    #end if

    if 'aux_sub_addrs' in kwargs and kwargs[ 'aux_sub_addrs' ] != self.auxSubAddrs:
      replot = True
      self.auxSubAddrs = \
          self.data.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      replot = True
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )
    #end if

    if 'cur_dataset' in kwargs and \
        kwargs[ 'cur_dataset' ] != self.curDataSet and \
	kwargs[ 'cur_dataset' ] in self.data.GetDataSetNames( 'axial' ):
      self.curDataSet = kwargs[ 'cur_dataset' ]
      #select_name = self.GetSelectedDataSetName( 'channel' )
      select_name = self.GetSelectedDataSetName()
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] != self.subAddr:
      replot = True
      self.subAddr = kwargs[ 'sub_addr' ]
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
