#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plots.py					-
#	HISTORY:							-
#		2016-12-26	leerw@ornl.gov				-
#	  Prep for top level data model submenus for ref axis menu.
#		2016-12-13	leerw@ornl.gov				-
#	  Adapting to new DataModelMgr.
#		2016-11-26	leerw@ornl.gov				-
#	  Changing plot_type based on dataset being derived or not.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#	  Fixed _OnMplMouseRelease() not to process if refAxisDataSet
#	  is not the time dataset.
#		2016-10-24	leerw@ornl.gov				-
#	  Using customDataRange.
#		2016-10-18	leerw@ornl.gov				-
#	  Added auxNodeAddrs and nodeAddr attributes.
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-10-06	leerw@ornl.gov				-
#	  Updated for node dataset types.
#		2016-08-23	leerw@ornl.gov				-
#	  Trying to use DataSetMenu.
#		2016-08-20	leerw@ornl.gov				-
#	  Properly naming the X-Axis menu item and methods.
#		2016-08-19	leerw@ornl.gov				-
#	  Add capability for user selection of the X-axis dataset.
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
#		2016-07-06	leerw@ornl.gov				-
#	  Not accepting timeDataSet changes.
#		2016-06-30	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-06-16	leerw@ornl.gov				-
#	  Calling DataModel.ReadDataSetValues2() in _UpdateDataSetValues().
#		2016-06-07	leerw@ornl.gov				-
#	  Implemented _CreateClipboardData().
#		2016-06-04	leerw@ornl.gov				-
#	  Renamed from scalar_plot.py
#		2016-05-31	leerw@ornl.gov				-
#		2016-05-26	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, sys, time, traceback
import numpy as np
import pdb  # pdb.set_trace()

try:
  import wx
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
from bean.dataset_menu import *
from bean.plot_dataset_props import *
from event.state import *

from legend import *
from plot_widget import *
from widget import *
from widgetcontainer import *


LABEL_timeDataSet = 'Time Dataset'


#------------------------------------------------------------------------
#	CLASS:		TimePlots					-
#------------------------------------------------------------------------
class TimePlots( PlotWidget ):
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

    self.dmgr.RemoveListener( 'dataSetAdded', self._UpdateRefAxisMenu )

    super( TimePlots, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    self.ax2 = None
    self.axialValue = DataModel.CreateEmptyAxialValue()
    self.curDataSet = None
    #self.channelDataSet = 'channel_liquid_temps [C]'
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by DataSetName
    self.dataSetTypes = set()

		#-- keyed by DataSetName, dicts with keys 'times', 'data'
    self.dataSetValues = {}

    self.nodeAddr = -1

#		-- DataSetName instance, None means use self.state.timeDataSet
    self.refAxisDataSet = None
    self.refAxisMenu = wx.Menu()
    self.refAxisTimes = None  # None means refAxisValues *are* the times
    self.refAxisValues = np.empty( 0 )
    self.scaleMode = 'selected'
    self.subAddr = ( -1, -1 )

    super( TimePlots, self ).__init__( container, id, ref_axis = 'x' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    core = self.dmgr.GetCore()
    if core:
      header = 'Assy %d %s, Axial %.3f\n' % (
          self.assemblyAddr[ 0 ] + 1,
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ]
	  )
      cur_selection_flag = mode != 'displayed'

      #if self.refAxisDataSet is not None and self.refAxisTimes is not None:
      if self.refAxisTimes is not None:
        csv_text = self.\
	    _CreateClipboardDataNonTimeXAxis( header, cur_selection_flag )
      else:
        csv_text = self.\
	    _CreateClipboardDataTimeXAxis( header, cur_selection_flag )
    #end if core

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardDataNonTimeXAxis()		-
  #----------------------------------------------------------------------
  def _CreateClipboardDataNonTimeXAxis( self, header_in, cur_selection_flag ):
    """Retrieves the data for the time and axial assuming both
self.refAxisDataSet and self.refAxixTimes are not None.
@return			text or None
"""
    csv_text = header_in

#		-- Must be valid state
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    core = self.dmgr.GetCore()
    if core:
#		 	-- Create header
#		 	--
      header = '"%s@%s"' % (
          self.dmgr.GetDataSetDisplayName( self.refAxisDataSet ),
	  DataUtils.ToAddrString( *self.subAddr )
	  )

      for k in sorted( self.dataSetValues.keys() ):
	qds_name = self._GetDataSetName( k )
        data_set_pair = self.dataSetValues[ k ]
	item = data_set_pair[ 'data' ]
	if not isinstance( item, dict ):
	  item = { '': item }
        for rc in sorted( item.keys() ):
          header += ',"' + qds_name.name
	  if rc:
            header += '@' + DataUtils.ToAddrString( *rc )
          header += '"'
      #end for k
      csv_text += header + '\n'

#			-- Write values
#			--
      cur_time_ndx = DataUtils.\
          FindListIndex( self.refAxisTimes, self.timeValue, 'a' )
      if cur_selection_flag:
        i_range = ( cur_time_ndx, )
      else:
	i_range = xrange( len( self.refAxisTimes ) )
      #end if cur_selection_flag

      for i in i_range:
        row = '%.7g' % self.refAxisValues[ i ]
	time_value = self.refAxisTimes[ i ]

        time_ndx_by_model = {}
	for k, data_pair in sorted( self.dataSetValues.iteritems() ):
	  qds_name = self._GetDataSetName( k )
	  item = data_pair[ 'data' ]
	  if not isinstance( item, dict ):
	    item = { '': item }

	  model_time_ndx = time_ndx_by_model.get( qds_name.modelName )
	  if model_time_ndx is None:
	    model_time_ndx = \
	        DataUtils.FindListIndex( data_pair[ 'times' ], time_value, 'a' )
	    time_ndx_by_model[ qds_name.modelName ] = model_time_ndx
	  #end if model_time_ndx

          for rc, values in sorted( item.iteritems() ):
	    cur_val = 0
	    if not hasattr( values, '__len__' ):
	      if i == cur_time_ndx:
	        cur_val = values
	    elif len( values ) > i:
	      cur_val = values[ i ]

	    if cur_val != 0:
	      row += ',%.7g' % cur_val
	    else:
	      row += ',0'
          #end for rc, values
        #end for k, data_pair

        csv_text += row + '\n'
      #end for i
    #end if core

    return  csv_text
  #end _CreateClipboardDataNonTimeXAxis


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardDataTimeXAxis()			-
  #----------------------------------------------------------------------
  def _CreateClipboardDataTimeXAxis( self, header_in, cur_selection_flag ):
    """Retrieves the data for the time and axial assuming both
self.refAxisDataSet and self.refAxixTimes are None.
@return			text or None
"""
    csv_text = header_in

#		-- Must be valid state
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    core = self.dmgr.GetCore()
    if core:
      time_ds_display = self.state.timeDataSet

#		 	-- Collate by model
#		 	--
      datasets_by_model = {}
      times_by_model = {}
      for k in sorted( self.dataSetValues.keys() ):
	qds_name = self._GetDataSetName( k )
	ds_rec = self.dataSetSelections[ k ]
        if ds_rec[ 'visible' ] and qds_name is not None:
	  ds_list = datasets_by_model.get( qds_name.modelName )
	  if ds_list is None:
	    ds_list = []
	    datasets_by_model[ qds_name.modelName ] = ds_list
	  ds_list.append( k )

	  if qds_name.modelName not in times_by_model:
	    data_set_pair = self.dataSetValues[ k ]
	    times_by_model[ qds_name.modelName ] = data_set_pair[ 'times' ]
        #end if ds_rec[ 'visible' ]
      #end for k

#			-- Create per-model blocks
#			--
      for model_name, ds_list in sorted( datasets_by_model.iteritems() ):
	model_times = times_by_model.get( model_name )
	csv_text += model_name + '\n'
#				-- Header line
        header = time_ds_display
	for k in ds_list:
	  qds_name = self._GetDataSetName( k )
	  data_set_pair = self.dataSetValues[ k ]
	  item = data_set_pair[ 'data' ]
	  if not isinstance( item, dict ):
	    item = { '': item }

          for rc in sorted( item.keys() ):
            header += ',"' + qds_name.displayName
	    if rc:
              header += '@' + DataUtils.ToAddrString( *rc )
            header += '"'
	#end for qds_name
        csv_text += header + '\n'

#				-- Time value rows, cols are dataset values
	cur_time_ndx = DataUtils.\
	    FindListIndex( model_times, self.timeValue, 'a' )
        if cur_selection_flag:
          i_range = ( cur_time_ndx, )
        else:
	  i_range = xrange( len( model_times ) )

        for i in i_range:
          row = '%.7g' % model_times[ i ]

	  for qds_name in ds_list:
            data_set_pair = self.dataSetValues[ qds_name ]
	    item = data_set_pair[ 'data' ]
	    if not isinstance( item, dict ):
	      item = { '': item }
            for rc, values in sorted( item.iteritems() ):
	      cur_val = 0
	      if not hasattr( values, '__len__' ):
	        if i == cur_time_index:
	          cur_val = values
	      elif len( values ) > i:
	        cur_val = values[ i ]

	      if cur_val != 0:
	        row += ',%.7g' % cur_val
	      else:
	        row += ',0'
            #end for rc, values
	  #end for qds_name
	  
	  csv_text += row + '\n'
        #end for i
      #end for model_name, ds_list
    #end if core

    return  csv_text
  #end _CreateClipboardDataTimeXAxis


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( TimePlots, self )._CreateMenuDef()

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
	'label': 'Select Left Axis Scale Mode',
	'submenu': select_scale_def
	},
	{
	'label': 'Select X-Axis Dataset...',
	'submenu': self.refAxisMenu
	},
        { 'label': 'Toggle Toolbar', 'handler': self._OnToggleToolBar }
      ]
#    more_def = \
#      [
#	( '-', None ),
#        ( 'Edit Dataset Properties', self._OnEditDataSetProps )
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
    ds_values = self._FindDataSetValues( ev.xdata )
    if ds_values is not None:
      #tip_str = '%s=%.3g' % ( self.state.timeDataSet, ev.xdata )
      tip_str = 'x=%.3g' % ev.xdata
      for k in sorted( ds_values.keys() ):
        data_set_item = ds_values[ k ]
	for rc, value in sorted( data_set_item.iteritems() ):
	  cur_label = \
	      k.name + '@' + DataUtils.ToAddrString( *rc ) \
	      if rc else k.name
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
    super( TimePlots, self )._DoUpdatePlot( wd, ht )

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

#		-- Set title
#		--
#    self.ax.set_title(
#	'Versus ' + self.state.timeDataSet,
#	fontsize = self.titleFontSize
#	)

#		-- Must have valid core and something to plot
#		--
    core = self.dmgr.GetCore()
    if core is not None and len( self.dataSetValues ) > 0:
      if self.refAxisDataSet is not None:
        xaxis_label = '%s: %d %s' % (
	    self.dmgr.GetDataSetDisplayName( self.refAxisDataSet ),
	    self.assemblyAddr[ 0 ] + 1,
            core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
            )
	if self.dmgr.GetDataSetHasSubAddr( self.refAxisDataSet ):
          rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
	  extra = ' %s' % str( rc )
	  xaxis_label += extra

        self.ax.set_xlim(
	    np.amin( self.refAxisValues ),
	    np.amax( self.refAxisValues )
            )
        self.ax.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )
      else:
	xaxis_label = self.state.timeDataSet
      #end if-else self.refAxisDataSet

#			-- Determine axis datasets
#			--
      left_qds_name, right_qds_name = self._ResolveDataSetAxes()

#			-- Configure axes
#			--
#				-- Right
      if right_qds_name is not None and self.ax2 is not None:
        self.ax2.set_ylabel( right_qds_name, fontsize = label_font_size )
	ds_range = self.dmgr.GetRange(
	    right_qds_name,
	    self.timeValue if self.state.scaleMode == 'state' else -1.0
	    )
        if DataUtils.IsValidRange( *ds_range ):
          self.ax2.set_ylim( *ds_range )
	  self.ax2.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )
	  #self.ax2.yaxis.get_major_formatter().set_scientific( True )

#				-- Left, primary
      self.ax.set_xlabel( xaxis_label, fontsize = label_font_size )
      self.ax.set_ylabel(
	  self.dmgr.GetDataSetDisplayName( left_qds_name ),
	  fontsize = label_font_size
	  )

      ds_range = list( self.customDataRange ) \
          if self.customDataRange is not None else \
	  [ NAN, NAN ]
      if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] ):
        calc_range = self.dmgr.GetRange(
	    left_qds_name,
	    self.timeValue if self.state.scaleMode == 'state' else -1.0
	    )
#				-- Scale over all plotted datasets?
        if self.scaleMode == 'all':
          for k in self.dataSetValues:
	    cur_qname = self._GetDataSetName( k )
	    if cur_qname != right_qds_name and cur_qname != left_qds_name:
	      cur_range = self.dmgr.GetRange(
	          cur_qname,
	          self.timeValue if self.state.scaleMode == 'state' else -1.0
	          )
	      calc_range = (
	          min( calc_range[ 0 ], cur_range[ 0 ] ),
		  max( calc_range[ 1 ], cur_range[ 1 ] )
	          )
          #end for k

        for i in xrange( len( ds_range ) ):
	  if math.isnan( ds_range[ i ] ):
	    ds_range[ i ] = calc_range[ i ]
      #end if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] )

      if DataUtils.IsValidRange( *ds_range ):
        self.ax.set_ylim( *ds_range )
        self.ax.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )
	#self.ax.yaxis.get_major_formatter().set_scientific( True )

#				-- Set title
#				--
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )

      title_str = 'Assy %d %s, Axial %.3f' % \
          ( self.assemblyAddr[ 0 ] + 1, show_assy_addr, self.axialValue[ 0 ] )

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

      if 'detector' in self.dataSetTypes or \
          'fixed_detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Det %d %s' % (
	    self.assemblyAddr[ 0 ] + 1,
	    core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    )

      if len( title_line2 ) > 0:
        title_str += '\n' + title_line2

#				-- Plot each selected dataset
#				--
      count = 0
      time_indices_by_model = {}
      for k in self.dataSetValues:
        data_pair = self.dataSetValues[ k ]
	qds_name = self._GetDataSetName( k )
	model_time_indices = None
#					-- Match refAxisTimes to model times
#					--
	if self.refAxisTimes is not None:
	  model_time_indices = time_indices_by_model.get( qds_name.modelName )
	  if model_time_indices is None:
	    model_time_indices = []
	    model_time_values = self.dmgr.GetTimeValues( qds_name.modelName )
	    for t in self.refAxisTimes:
	      model_time_indices.append(
	          DataUtils.FindListIndex( model_time_values, t, 'a' )
		  )
	    time_indices_by_model[ qds_name.modelName ] = model_time_indices
	  #end if qds_name.modelName
	#end if self.refAxisTimes

	rec = self.dataSetSelections[ k ]
	scale = rec[ 'scale' ] if rec[ 'axis' ] == '' else 1.0
	legend_label = self.dmgr.GetDataSetDisplayName( qds_name )
	if scale != 1.0:
	  legend_label += '*%.3g' % scale

	marker_size = None
	plot_type = '--' if self.dmgr.IsDerivedDataSet( qds_name ) else '-'
	ds_type = self.dmgr.GetDataSetType( qds_name )
	if ds_type.startswith( 'detector' ):
	  marker_size = 12
#	  plot_type = '.'
#	elif ds_type.startswith( 'channel' ):
#	  plot_type = '--'
#	elif ds_type.startswith( 'pin' ):
#	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  marker_size = 12
	  plot_type = 'x'
	  #plot_type = '-.'
#	else:
#	  plot_type = ':'

	#data_set_item = self.dataSetValues[ k ]
	data_set_item = data_pair[ 'data' ]
	if not isinstance( data_set_item, dict ):
	  data_set_item = { '': data_set_item }

	for rc, values in sorted( data_set_item.iteritems() ):
	  if self.refAxisTimes is not None and model_time_indices is not None:
	    cur_values = values[ model_time_indices ]
	  else:
	    if values.size == self.refAxisValues.size:
	      cur_values = values
	    else:
	      cur_values = \
	          np.ndarray( self.refAxisValues.shape, dtype = np.float64 )
	      cur_values.fill( 0.0 )
	      cur_values[ 0 : values.shape[ 0 ] ] = values
	  #end if-else self.refAxisTimes

	  cur_label = \
	      legend_label + '@' + DataUtils.ToAddrString( *rc ) \
	      if rc else legend_label

	  plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	  cur_axis = self.ax2 if rec[ 'axis' ] == 'right' else self.ax
	  if marker_size is not None:
	    cur_axis.plot(
	        self.refAxisValues, cur_values * scale, plot_mode,
	        label = cur_label, linewidth = 2,
		markersize = marker_size
	        )
	  else:
	    cur_axis.plot(
	        self.refAxisValues, cur_values * scale, plot_mode,
	        label = cur_label, linewidth = 2
	        )

	  count += 1
	#end for rc, values
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

#     #xxxplacement orig=0.925, tried=0.975
      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )

#				-- Time value line
#				--
      self.axline = \
          self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
      if self.refAxisTimes is not None:
	ndx = DataUtils.FindListIndex( self.refAxisTimes, self.timeValue )
	self.axline.set_xdata( self.refAxisValues[ ndx ] )
      else:
        self.axline.set_xdata( self.timeValue )
    #end if core is not None and len( self.dataSetValues ) > 0
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, ref_ds_value ):
    """Find matching dataset values for the axial.
@param  ref_ds_value	value in the reference dataset
@return			dict by real dataset name (not pseudo name) of
			dataset values or None if no matches
"""
    results = {}
    ndx = DataUtils.FindListIndex( self.refAxisValues, ref_ds_value, 'a' )
    if ndx >= 0:
      for k in self.dataSetValues:
        qds_name = self._GetDataSetName( k )

        data_pair = self.dataSetValues[ k ]
        time_values = data_pair[ 'times' ]
        data_set_item = data_pair[ 'data' ]

        #data_set_item = self.dataSetValues[ k ]
        if not isinstance( data_set_item, dict ):
          data_set_item = { '': data_set_item }

        sample = data_set_item.itervalues().next()
        if len( sample ) > ndx:
	  cur_dict = {}
          for rc, values in data_set_item.iteritems():
	    cur_dict[ rc ] = values[ ndx ]

	  results[ qds_name ] = cur_dict
        #end if ndx in range
      #end for k
    #end if ndx

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
    return  ( 'axial:detector', 'axial:pin' )
    #xxxxx ( 'axial:all' )
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
  #	METHOD:		TimePlots.GetCurDataSet()			-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """Returns the visible dataset.
@return		current dataset name (DataSetName instance) or None
"""
    qds_name = None
    if len( self.dataSetValues ) > 0:
      qds_name = self._GetDataSetName( self.dataSetValues.iterkeys().next() )

    return  qds_name
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_GetDataSetName()				-
  #----------------------------------------------------------------------
  def _GetDataSetName( self, name ):
    """Determines actual dataset name if a pseudo name is provided.
"""
    return \
        None  if name is None else \
	self.curDataSet  if name == NAME_selectedDataSet else \
	name

#    return \
#	None  if name is None else \
#	self.channelDataSet  if name == 'Selected channel dataset' else \
#        self.detectorDataSet  if name == 'Selected detector dataset' else \
#        self.pinDataSet  if name == 'Selected pin dataset' else \
#        self.fixedDetectorDataSet  if name == 'Selected fixed_detector dataset' else \
#	self.scalarDataSet  if name == 'Selected scalar dataset' else \
#	name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      [
      'channel', 'detector', 'fixed_detector', 'pin', 'scalar',
      ':assembly', ':axial', ':chan_radial', ':core', ':node',
      ':radial', ':radial_assembly', ':radial_node'
      ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetDataSetDisplayMode()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns 'selected'
@return			'selected'
"""
    return  'selected'
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetDataSetPropertyNames()		-
  #----------------------------------------------------------------------
  def GetDataSetPropertyNames( self ):
    """Overrides to append 'refAxisDataSet' to the list
@return			[ 'curDataSet', 'refAxisDataSet' ]
"""
    result = super( TimePlots, self ).GetDataSetPropertyNames()
    return  result + [ 'refAxisDataSet' ]
  #end GetDataSetPropertyNames


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
	STATE_CHANGE_timeValue
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Time Plots'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes, 'ax', and 'ax2'.
XXX size according to how many datasets selected?
"""
    #xxxplacement
    #self.ax = self.fig.add_axes([ 0.1, 0.1, 0.85, 0.65 ])
    #self.ax = self.fig.add_axes([ 0.1, 0.12, 0.85, 0.68 ])
    #self.ax = self.fig.add_axes([ 0.15, 0.12, 0.75, 0.65 ])
    self.ax = self.fig.add_axes([ 0.15, 0.12, 0.68, 0.65 ])
    self.ax2 = self.ax.twinx() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.IsDataSetVisible()			-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, qds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  qds_name	dataset name, DataSetName instance
@return			True if visible, else False
"""
    visible = \
        qds_name in self.dataSetSelections and \
        self.dataSetSelections[ qds_name ][ 'visible' ]
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """Assume self.dmgr is valid.
@return			dict to be passed to UpdateState()
"""
    update_args = {}

    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'left', 'scale': 1.0, 'visible': True }
    self.dataSetDialog = None

    if self.dmgr.HasData():
      assy_addr = self.dmgr.NormalizeAssemblyAddr( self.state.assemblyAddr )
      aux_node_addrs = self.dmgr.NormalizeNodeAddrs( self.state.auxNodeAddrs )
      aux_sub_addrs = self.dmgr.\
          NormalizeSubAddrs( self.state.auxSubAddrs, mode = 'channel' )
      axial_value = self.dmgr.NormalizeAxialValue( None, self.state.axialValue )
      node_addr = self.dmgr.NormalizeNodeAddr( self.state.nodeAddr )
      sub_addr = self.dmgr.NormalizeSubAddr( self.state.subAddr )
      #detector_ndx = self.data.NormalizeDetectorIndex( self.state.assemblyAddr )
      #state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'assembly_addr': assy_addr,
	'aux_node_addrs': aux_node_addrs,
	'aux_sub_addrs': aux_sub_addrs,
	'axial_value': axial_value,
	'cur_dataset': self.state.curDataSet,
	'node_addr': node_addr,
	'sub_addr': sub_addr,
	'time_dataset': self.state.timeDataSet,
	'time_value': self.state.timeValue
	}

      self.dmgr.AddListener( 'dataSetAdded', self._UpdateRefAxisMenu )
      wx.CallAfter( self._UpdateRefAxisMenu )
    #end if self.dmgr.HasData()

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    # dataSetSelections now handled in PlotWidget
    for k in (
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs', 'axialValue',
	'nodeAddr', 'scaleMode', 'subAddr'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( TimePlots, self ).LoadProps( props_dict )

#		-- Update scale mode radio menu item
#		--
    labels = [
        'Select Left Axis Scale Mode',
	'All Datasets' if self.scaleMode == 'all' else LABEL_selectedDataSet
	]
    select_item = \
        self.container.FindMenuItem( self.container.GetWidgetMenu(), *labels )
    if select_item:
      select_item.Check()

    wx.CallAfter( self.UpdateState, replot = True )
    wx.CallAfter( self._UpdateRefAxisMenu )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnEditDataSetProps()				-
  #----------------------------------------------------------------------
  def _OnEditDataSetProps( self, ev ):
    """Must be called from the UI thread.
"""
    if self.dataSetDialog is None:
      self.dataSetDialog = \
          PlotDataSetPropsDialog( self, axis1 = 'left', axis2 = 'right' )

    if self.dataSetDialog is not None:
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
    super( TimePlots, self )._OnMplMouseRelease( ev )

    if self.refAxisDataSet is None:
      button = ev.button or 1
      if button == 1 and self.cursor is not None:
        ndx = DataUtils.\
	    FindListIndex( self.refAxisValues, self.cursor[ 0 ], 'a' )
        if ndx >= 0:
	  self.UpdateState( time_value = self.refAxisValues[ ndx ] )
	  self.FireStateChange( time_value = self.refAxisValues[ ndx ] )
          #self.UpdateState( state_index = ndx )
          #self.FireStateChange( state_index = ndx )
    #end if self.refAxisDataSet
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._OnSelectRefAxisDataSet()		-
  #----------------------------------------------------------------------
  def _OnSelectRefAxisDataSet( self, ev ):
    """Must be called from the UI thread.
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      label = item.GetItemLabelText()
      #x new_value = None if label == LABEL_timeDataSet else self.refAxisMenuItemMap.get( item )
      new_value = None if label == LABEL_timeDataSet else DataSetName( label )
      if new_value != self.refAxisDataSet:
	Widget.CheckSingleMenuItem( self.refAxisMenu, item )
        self.refAxisDataSet = new_value
	self.UpdateState( replot = True )
    #end if
  #end _OnSelectRefAxisDataSet


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._OnSetScaleMode()			-
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
  #	METHOD:		TimePlots._ResolveDataSetAxes()			-
  #----------------------------------------------------------------------
  def _ResolveDataSetAxes( self ):
    """Allocates right and left axis if they are not assigned.
"""
    left = left_name = None
    right = right_name = None
    visible_names = []
    for k, rec in self.dataSetSelections.iteritems():
      if rec[ 'visible' ]:
	visible_names.append( k )
	if rec[ 'axis' ] == 'left':
	  left = rec
	  left_name = k
        elif rec[ 'axis' ] == 'right':
	  right = rec
	  right_name = k
      #end if visible
    #end for

    if left is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'right':
	  rec[ 'axis' ] = 'left'
	  left_name = name
	  left = rec
	  break
    #end if

    if right is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'left':
	  rec[ 'axis' ] = 'right'
	  right_name = name
	  right = rec
	  break
    #end if

#		-- Special case, only right, must make it left
#		--
    if left is None and right is not None:
      right[ 'axis' ] = 'left'
      left_name = right_name
      right_name = None

    return\
      ( self._GetDataSetName( left_name ), self._GetDataSetName( right_name ) )
  #end _ResolveDataSetAxes


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( TimePlots, self ).SaveProps( props_dict )

    # dataSetSelections now handled in PlotWidget
    for k in (
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs', 'axialValue',
	'nodeAddr', 'scaleMode', 'subAddr'
	):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.ToggleDataSetVisible()		-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, qds_name ):
    """Toggles the visibility of the named dataset.
Must be called from the event thread.
@param  qds_name	dataset name, DataSetName instance
"""
    if qds_name in self.dataSetSelections:
      rec = self.dataSetSelections[ qds_name ]
      if rec[ 'visible' ]:
        rec[ 'axis' ] = ''
      rec[ 'visible' ] = not rec[ 'visible' ]

    else:
      self.dataSetSelections[ qds_name ] = \
        { 'axis': '', 'scale': 1.0, 'visible': True }

    self._ResolveDataSetAxes()
    self.UpdateState( replot = True )
  #end ToggleDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot.
Performance enhancement
=======================
Once auxSubAddrs include the assembly and axial indexes,
compare each new dataset with what's in self.dataSetValues and only load
new ones in new_ds_values, copying from self.dataSetValues for ones
already read.
"""
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

#		-- Must have data
#		--
    #if DataModel.IsValidObj( self.data, axial_level = self.axialValue[ 1 ] ):
    if self.dmgr.HasData() and self.curDataSet:
      node_addr_list = None
      sub_addr_list = None
      ref_axis_qds_name = None

#			-- Construct read specs
#			--
      time_values = None
      specs = []
      spec_names = set()
      if self.refAxisDataSet is not None:
	ref_axis_qds_name = DataSetName(
	    self.refAxisDataSet.modelName,
	    '*' + self.refAxisDataSet.displayName
	    )
        specs.append({
	    'assembly_index': self.assemblyAddr[ 0 ],
	    'axial_cm': self.axialValue[ 0 ],
	    'qds_name': ref_axis_qds_name,
	    'sub_addrs': [ self.subAddr ]
	    })
      else:
	time_values = np.array( self.dmgr.GetTimeValues() )
        #specs.append( { 'qds_name': self.state.timeDataSet} )

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	qds_name = self._GetDataSetName( k )

#				-- Must be visible
        if ds_rec[ 'visible' ] and qds_name is not None and \
	    qds_name not in spec_names:
	  ds_type = self.dmgr.GetDataSetType( qds_name )
	  if ds_type:
	    spec = { 'qds_name': qds_name }
	    spec_names.add( qds_name )

#						-- Detector, fixed detector
	    if ds_type == 'detector' or ds_type == 'fixed_detector':
	      spec[ 'detector_index' ] = self.assemblyAddr[ 0 ]
	      spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	      specs.append( spec )
              self.dataSetTypes.add( ds_type )

#						-- Scalar
	    elif ds_type == 'scalar':
	      specs.append( spec )
              self.dataSetTypes.add( 'scalar' )

#						-- Everything else
	    else:
#							-- Lazy creation
	      if node_addr_list is None:
	        node_addr_list = list( self.auxNodeAddrs )
		node_addr_list.insert( 0, self.nodeAddr )
	      if sub_addr_list is None:
                sub_addr_list = list( self.auxSubAddrs )
                sub_addr_list.insert( 0, self.subAddr )

	      spec[ 'assembly_index' ] = self.assemblyAddr[ 0 ]
	      spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	      spec[ 'node_addrs' ] = node_addr_list
	      spec[ 'sub_addrs' ] = sub_addr_list
	      specs.append( spec )
              self.dataSetTypes.add( ds_type )
	    #end if-else ds_type match
	  #end if ds_type exists
        #end if visible
      #end for k

#			-- Read and extract
#			--
      results = self.dmgr.ReadDataSetTimeValues( *specs )

      #if self.refAxisDataSet is not None:
      if ref_axis_qds_name is not None:
	#values_item = results[ '*' + self.refAxisDataSet ]
	ref_axis_pair = results[ ref_axis_qds_name ]
	values_item = ref_axis_pair[ 'data' ]
	self.refAxisTimes = ref_axis_pair[ 'times' ]
	if isinstance( values_item, dict ):
	  self.refAxisValues = values_item.itervalues().next()
	else:
	  self.refAxisValues = values_item
      else:
	#ref_axis_pair = results[ self.state.timeDataSet ]
        #self.refAxisValues = ref_axis_pair[ 'data' ]
	self.refAxisValues = time_values
	self.refAxisTimes = None

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	qds_name = self._GetDataSetName( k )
        if ds_rec[ 'visible' ] and qds_name is not None and \
	    qds_name in results:
	  self.dataSetValues[ k ] = results[ qds_name ]
      #end for k
    #end if valid state
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._UpdateRefAxisMenu()			-
  #----------------------------------------------------------------------
  def _UpdateRefAxisMenu( self, *args, **kwargs ):
    """Must be called from the UI thread.
"""
    #xxxxx Create model submenus at first level with types submenus
    #xxxxx _OnSelectRefAxisDataSet() must check parent menu to see
    #if self.data is not None:
    if self.dmgr.HasData():
      Widget.ClearMenu( self.refAxisMenu )
      #x self.refAxisMenuItemMap.clear()

      menu_types = []
      menu_types = self.GetDataSetTypes()

#			-- Map dataset names to base category/type
#			--
      #x if self.dmgr.GetDataModelCount() < 2:
      #x for model_name in self.dmgr.GetDataModelNames():
      #x   if self.dmgr.GetDataModelCount() > 1:
      #x     model_menu = wx.Menu()
      #x     model_menu_item = wx.MenuItem( self.refAxisMenu, wx.ID_ANY, model_name, subMenu = model_menu )
      #x     self.refAxisMenu.AppendItem( model_menu )
      #x   else:
      #x     model_menu = self.refAxisMenu

      qds_names_by_type = {}
      for dtype in menu_types:
        qds_names = self.dmgr.GetDataSetQNames( None, dtype )
	if qds_names:
	  dtype = DataUtils.GetDataSetTypeDisplayName( dtype )
	  if dtype in qds_names_by_type:
	    qds_names_by_type[ dtype ] += qds_names
	  else:
	    qds_names_by_type[ dtype ] = list( qds_names )
	#end if qds_names
      #end for dtype

#			-- Create pullrights
#			--
      for dtype, qds_names in sorted( qds_names_by_type.iteritems() ):
        if qds_names:
	  type_menu = wx.Menu()
	  for qds_name in sorted( qds_names ):
	    item = wx.MenuItem(
		#x qds_name.displayName
	        type_menu, wx.ID_ANY, qds_name.name,
		kind = wx.ITEM_CHECK
		)
	    self.container.Bind( wx.EVT_MENU, self._OnSelectRefAxisDataSet, item )
	    type_menu.AppendItem( item )
	    if qds_name == self.refAxisDataSet:
	      item.Check()
            #x self.refAxisMenuItemMap[ item ] = qds_name
	  #end for qds_name

          type_item = wx.MenuItem(
	      self.refAxisMenu, wx.ID_ANY, dtype,
	      subMenu = type_menu
	      )
          #x model_menu.AppendItem( type_item )
	  self.refAxisMenu.AppendItem( type_item )
        #end if qds_names
      #end for dtype, ds_names

      item = wx.MenuItem(
          self.refAxisMenu, wx.ID_ANY, LABEL_timeDataSet,
	  kind = wx.ITEM_CHECK
	  )
      self.container.Bind( wx.EVT_MENU, self._OnSelectRefAxisDataSet, item )
      self.refAxisMenu.AppendItem( item )
      if self.refAxisDataSet is None:
        item.Check()

      #x end for model_name
    #end if self.dmgr.HasData()
  #end _UpdateRefAxisMenu


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateStateValues()				-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
@return			kwargs with 'redraw' and/or 'replot'
"""
    kwargs = super( TimePlots, self )._UpdateStateValues( **kwargs )
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

    if 'assembly_addr' in kwargs and \
       kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      replot = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
    #end if

    if 'aux_node_addrs' in kwargs and \
        kwargs[ 'aux_node_addrs' ] != self.auxNodeAddrs:
      replot = True
      self.auxNodeAddrs = \
          DataUtils.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )

    if 'aux_sub_addrs' in kwargs and \
        kwargs[ 'aux_sub_addrs' ] != self.auxSubAddrs:
      replot = True
      self.auxSubAddrs = \
          self.dmgr.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ][ 0 ] != self.axialValue[ 0 ]:
      replot = True
      self.axialValue = \
          self.dmgr.GetAxialValue( cm = kwargs[ 'axial_value' ][ 0 ] )
    #end if

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      self.curDataSet = kwargs[ 'cur_dataset' ]
      #select_name = self.GetSelectedDataSetName( 'channel' )
      select_name = self.GetSelectedDataSetName()
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'node_addr' in kwargs and kwargs[ 'node_addr' ] != self.nodeAddr:
      replot = True
      self.nodeAddr = DataUtils.NormalizeNodeAddr( kwargs[ 'node_addr' ] )

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

#end TimePlots
