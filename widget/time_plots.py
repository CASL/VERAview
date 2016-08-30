#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plots.py					-
#	HISTORY:							-
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
import math, os, sys, time, traceback
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

    super( TimePlots, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxSubAddrs = []
    self.ax2 = None
    self.axialValue = DataModel.CreateEmptyAxialValue()
    self.curDataSet = kwargs.get( 'dataset', 'pin_powers' )
    #self.channelDataSet = 'channel_liquid_temps [C]'
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by dataset name or pseudo name
    self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name or pseudo name
    #self.detectorDataSet = 'detector_response'
    #self.detectorIndex = ( -1, -1, -1 )
    #self.fixedDetectorDataSet = 'fixed_detector_response'

    self.refAxisDataSet = ''
    self.refAxisMenu = wx.Menu()
    self.refAxisValues = np.empty( 0 )
    #self.refDataSet = 'state'
    #self.scalarDataSet = 'keff'
    self.scaleMode = 'selected'
    self.subAddr = ( -1, -1 )
    #self.timeDataSet = 'state'

    super( TimePlots, self ).__init__( container, id, ref_axis = 'x' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    #csv_text = '"Axial=%.3f"\n' % self.axialValue[ 0 ]
    csv_text = 'Assy %d %s, Axial %.3f\n' % (
        self.assemblyAddr[ 0 ] + 1,
	self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	self.axialValue[ 0 ]
	)
    cur_selection_flag = mode != 'displayed'

#		-- Must be valid state
#		--
    if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):

#		 	-- Create header
#		 	--
      #header = self.state.timeDataSet
      if self.refAxisDataSet:
	header = '"%s@%s"' % \
	    ( self.refAxisDataSet, DataModel.ToAddrString( *self.subAddr ) )
      else:
        header = self.state.timeDataSet

      #for name, item in sorted( self.dataSetValues ):
      for k in sorted( self.dataSetValues.keys() ):
	name = self.data.GetDataSetDisplayName( self._GetDataSetName( k ) )
	item = self.dataSetValues[ k ]
	if not isinstance( item, dict ):
	  item = { '': item }
        for rc in sorted( item.keys() ):
          header += ',"' + name
	  if rc:
            header += '@' + DataModel.ToAddrString( *rc )
          header += '"'
      csv_text += header + '\n'

#			-- Write values
#			--
      if cur_selection_flag:
        i_range = ( self.stateIndex, )
      else:
        i_range = range( self.data.GetStatesCount() )

      for i in i_range:
        row = '%.7g' % self.refAxisValues[ i ]

        #for name, item in sorted( self.dataSetValues ):
        for name in sorted( self.dataSetValues.keys() ):
	  item = self.dataSetValues[ name ]
	  if not isinstance( item, dict ):
	    item = { '': item }

          for rc, values in sorted( item.iteritems() ):
	    cur_val = 0
	    if not hasattr( values, '__len__' ):
	      if i == self.stateIndex:
	        cur_val = values
	    elif len( values ) > i:
	      cur_val = values[ i ]

	    if cur_val != 0:
	      row += ',%.7g' % cur_val
	    else:
	      row += ',0'
          #end for rc, values
        #end for name, values

        csv_text += row + '\n'
      #end for i
    #end if valid state

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( TimePlots, self )._CreateMenuDef( data_model )

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
	#'handler': self._OnShowXAxisDataSetMenu
	}
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
    if self.refAxisDataSet:
      rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
      xaxis_label = '%s: %d %s %s' % (
	  self.refAxisDataSet,
	  self.assemblyAddr[ 0 ] + 1,
          self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  str( rc )
          )
      self.ax.set_xlim(
	  np.amin( self.refAxisValues ),
	  np.amax( self.refAxisValues )
          )
      self.ax.xaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )
#      ref_axis_range = self.data.GetRange(
#          self.refAxisDataSet,
#          self.stateIndex if self.state.scaleMode == 'state' else -1
#	  )
#      self.ax.set_xlim( *ref_axis_range )
    else:
      xaxis_label = self.state.timeDataSet

#		-- Something to plot?
#		--
    if len( self.dataSetValues ) > 0:
#			-- Determine axis datasets
#			--
      left_ds_name, right_ds_name = self._ResolveDataSetAxes()

#			-- Configure axes
#			--
#				-- Right
      if right_ds_name is not None and self.ax2 is not None:
        self.ax2.set_ylabel( right_ds_name, fontsize = label_font_size )
	ds_range = self.data.GetRange(
	    right_ds_name,
	    self.stateIndex if self.state.scaleMode == 'state' else -1
	    )
	if self.data.IsValidRange( *ds_range ):
          self.ax2.set_ylim( *ds_range )
	  self.ax2.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#				-- Left, primary
      #self.ax.set_xlabel( self.state.timeDataSet, fontsize = label_font_size )
      self.ax.set_xlabel( xaxis_label, fontsize = label_font_size )
      self.ax.set_ylabel( left_ds_name, fontsize = label_font_size )
      ds_range = self.data.GetRange(
	  left_ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
#					-- Scale over all plotted datasets?
      if self.scaleMode == 'all':
        for k in self.dataSetValues:
	  cur_name = self._GetDataSetName( k )
	  if cur_name != right_ds_name and cur_name != left_ds_name:
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
        self.ax.set_ylim( *ds_range )
        self.ax.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#			-- Set title
#			--
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )

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
	title_line2 += 'Det %d %s' % \
	    ( self.assemblyAddr[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ) )

#      if 'pin' in self.dataSetTypes or 'other' in self.dataSetTypes:
#        pin_rc = ( self.pinsubAddr[ 0 ] + 1, self.pinsubAddr[ 1 ] + 1 )
#        if len( title_line2 ) > 0: title_line2 += ', '
#	title_line2 += 'Pin %s' % str( pin_rc )

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
	plot_type = '-'
	ds_type = self.data.GetDataSetType( ds_name )
	if ds_type.startswith( 'detector' ):
	  marker_size = 12
	  plot_type = '.'
	elif ds_type.startswith( 'channel' ):
	  plot_type = '--'
	elif ds_type.startswith( 'pin' ):
	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  marker_size = 12
	  plot_type = 'x'
	  #plot_type = '-.'
	else:
	  plot_type = ':'

	data_set_item = self.dataSetValues[ k ]
	if not isinstance( data_set_item, dict ):
	  data_set_item = { '': data_set_item }

	for rc, values in sorted( data_set_item.iteritems() ):
	  if values.size == self.refAxisValues.size:
	    cur_values = values
	  else:
	    cur_values = \
	        np.ndarray( self.refAxisValues.shape, dtype = np.float64 )
	    cur_values.fill( 0.0 )
	    cur_values[ 0 : values.shape[ 0 ] ] = values

	  cur_label = \
	      legend_label + '@' + DataModel.ToAddrString( *rc ) \
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

#      #xxxplacement orig=0.925, tried=0.975
      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )

#			-- State/time value line
#			--
      self.axline = \
          self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
      if self.stateIndex >= 0 and self.stateIndex < len( self.refAxisValues ):
        self.axline.set_xdata( self.refAxisValues[ self.stateIndex ] )
    #end if we have something to plot
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
    ndx = self.data.FindListIndex( self.refAxisValues, ref_ds_value )
    if ndx >= 0:
      for k in self.dataSetValues:
        ds_name = self._GetDataSetName( k )

        data_set_item = self.dataSetValues[ k ]
        if not isinstance( data_set_item, dict ):
          data_set_item = { '': data_set_item }

        sample = data_set_item.itervalues().next()
        if len( sample ) > ndx:
	  cur_dict = {}
          for rc, values in data_set_item.iteritems():
	    cur_dict[ rc ] = values[ ndx ]

	  results[ ds_name ] = cur_dict
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
#	self.scalarDataSet  if name == 'Selected scalar dataset' else \
#	name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      [
      'channel', 'detector', 'fixed_detector',
      'pin', 'pin:assembly', 'pin:axial', 'pin:core', 'pin:radial',
      'pin:radial_assembly',
      'scalar'
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
  #	METHOD:		InitDataSetSelections()				-
  #----------------------------------------------------------------------
  def InitDataSetSelections( self, ds_types ):
    """Special hook called in VeraViewFrame.LoadDataModel().
"""
    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'left', 'scale': 1.0, 'visible': True }
#    axis = 'left'
#    for dtype in sorted( list( ds_types ) ):
#      if self.data.HasDataSetType( dtype ):
#        self.dataSetSelections[ self.GetSelectedDataSetName( dtype ) ] = \
#          { 'axis': axis, 'scale': 1.0, 'visible': True }
#        axis = 'right' if axis == 'left' else ''
  #end InitDataSetSelections


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.IsDataSetVisible()			-
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
    """Assume self.data is valid.
@return			dict to be passed to UpdateState()
"""
    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'left', 'scale': 1.0, 'visible': True }
    self.dataSetDialog = None
    if self.data is not None and self.data.HasData():
      assy_addr = self.data.NormalizeAssemblyAddr( self.state.assemblyAddr )
      axial_value = self.data.NormalizeAxialValue( self.state.axialValue )
      sub_addr = self.data.NormalizeSubAddr( self.state.subAddr )
      #detector_ndx = self.data.NormalizeDetectorIndex( self.state.assemblyAddr )
      state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'assembly_addr': assy_addr,
	'aux_sub_addrs': self.state.auxSubAddrs,
	'axial_value': axial_value,
	'cur_dataset': self.state.curDataSet,
	'state_index': state_ndx,
	'sub_addr': sub_addr,
	'time_dataset': self.state.timeDataSet
	}

      self.data.AddListener( 'newDataSet', self._UpdateRefAxisMenu )
      wx.CallAfter( self._UpdateRefAxisMenu )

    else:
      update_args = {}

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
    for k in (
	'assemblyAddr', 'auxSubAddrs', 'axialValue',
	'curDataSet', 'dataSetSelections', 'refAxisDataSet',
	'scaleMode', 'subAddr'
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

    button = ev.button or 1
    if button == 1 and self.cursor is not None:
      ndx = self.data.FindListIndex( self.refAxisValues, self.cursor[ 0 ] )
      if ndx >= 0:
        self.UpdateState( state_index = ndx )
        self.FireStateChange( state_index = ndx )
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
      new_value = '' if label == 'Time Dataset' else label
      if new_value != self.refAxisDataSet:
	Widget.CheckSingleMenuItem( self.refAxisMenu, item )
        self.refAxisDataSet = new_value
	self.UpdateState( replot = True )
    #end if
  #end _OnSelectRefAxisDataSet


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._OnSelectXAxisDataSet()		-
  #----------------------------------------------------------------------
  def _OnSelectXAxisDataSet( self, ev ):
    """Must be called from the UI thread.
@deprecated
"""
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None:
      label = item.GetItemLabelText()

      new_value = '' if label == 'Time Dataset' else label
      if new_value != self.refAxisDataSet:
        self.refAxisDataSet = new_value
	self.UpdateState( replot = True )
    #end if
  #end _OnSelectXAxisDataSet


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
  #	METHOD:		TimePlots._OnShowXAxisDataSetMenu()		-
  #----------------------------------------------------------------------
  def _OnShowXAxisDataSetMenu( self, ev ):
    """Must be called from the UI thread.
@deprecated  now a pullright
"""
    ev.Skip()

    if self.data is None:
      wx.MessageBox(
	  'No data are loaded', 'Select X-Axis Dataset',
	  wx.ICON_WARNING | wx.OK_DEFAULT, None
          )

    else:
      menu_types = []
#      ds_types = self.GetDataSetTypes()
#      if 'channel' in ds_types:
#        menu_types.append( 'channel' )
#      if 'pin' in ds_types:
#        menu_types.append( 'pin' )
      menu_types = self.GetDataSetTypes()

#			-- Create pullrights
#			--
      menu = wx.Menu()
      for ty in menu_types:
	ds_names = self.data.GetDataSetNames( ty )
	if ds_names:
	  type_menu = wx.Menu()
	  for ds_name in ds_names:
	    item = wx.MenuItem(
	        type_menu, wx.ID_ANY, ds_name,
		kind = wx.ITEM_CHECK
		)
	    self.container.Bind( wx.EVT_MENU, self._OnSelectXAxisDataSet, item )
	    type_menu.AppendItem( item )
	    if ds_name == self.refAxisDataSet:
	      item.Check()
	  #end for ds_name

          type_item = wx.MenuItem( menu, wx.ID_ANY, ty, subMenu = type_menu )
	  menu.AppendItem( type_item )
	#end if ds_names
      #end for ty

      item = \
          wx.MenuItem( menu, wx.ID_ANY, 'Time Dataset', kind = wx.ITEM_CHECK )
      self.container.Bind( wx.EVT_MENU, self._OnSelectXAxisDataSet, item )
      menu.AppendItem( item )
      if not self.refAxisDataSet:
        item.Check()

      self.container.widgetMenuButton.PopupMenu( menu )
    #end if-else self.data
  #end _OnShowXAxisDataSetMenu


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

    for k in (
	'assemblyAddr', 'auxSubAddrs', 'axialValue',
	'curDataSet', 'dataSetSelections',
	'scaleMode', 'subAddr'
	):
      props_dict[ k ] = getattr( self, k )

    if self.data is not None:
      for k in ( 'refAxisDataSet', ):
	cur_name = getattr( self, k )
	rev_name = self.data.RevertIfDerivedDataSet( cur_name )
	if cur_name == rev_name:
          props_dict[ k ] = cur_name
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.ToggleDataSetVisible()		-
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
    if DataModel.IsValidObj( self.data, axial_level = self.axialValue[ 1 ] ):
      sub_addr_list = None

#			-- Construct read specs
#			--
      specs = []
      spec_names = set()
      if self.refAxisDataSet:
        specs.append({
	    'assembly_index': self.assemblyAddr[ 0 ],
	    'axial_cm': self.axialValue[ 0 ],
	    'ds_name': '*' + self.refAxisDataSet,
	    'sub_addrs': [ self.subAddr ]
	    })
      else:
        specs.append( { 'ds_name': self.state.timeDataSet} )

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

#				-- Must be visible
        if ds_rec[ 'visible' ] and ds_name is not None and \
	    ds_name not in spec_names:
	  ds_type = self.data.GetDataSetType( ds_name )
	  spec = { 'ds_name': ds_name }
	  spec_names.add( ds_name )

	  if ds_type is None:
	    pass

#					-- Channel
	  elif ds_type.startswith( 'channel' ):
#						-- Lazy creation
	    if sub_addr_list is None:
              sub_addr_list = list( self.auxSubAddrs )
              sub_addr_list.insert( 0, self.subAddr )

	    spec[ 'assembly_index' ] = self.assemblyAddr[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    spec[ 'sub_addrs' ] = sub_addr_list
	    specs.append( spec )
            self.dataSetTypes.add( 'channel' )

#					-- Detector
	  elif ds_type.startswith( 'detector' ):
	    spec[ 'detector_index' ] = self.assemblyAddr[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    specs.append( spec )
            self.dataSetTypes.add( 'detector' )

#					-- Pin
	  elif ds_type.startswith( 'pin' ):
#						-- Lazy creation
	    if sub_addr_list is None:
              sub_addr_list = list( self.auxSubAddrs )
              sub_addr_list.insert( 0, self.subAddr )

	    spec[ 'assembly_index' ] = self.assemblyAddr[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    spec[ 'sub_addrs' ] = sub_addr_list
	    specs.append( spec )
            self.dataSetTypes.add( 'pin' )

#					-- Fixed detector
	  elif ds_type.startswith( 'fixed_detector' ):
	    spec[ 'detector_index' ] = self.assemblyAddr[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    specs.append( spec )
            self.dataSetTypes.add( 'fixed_detector' )

#					-- Scalar
	  else:
	    specs.append( spec )
            self.dataSetTypes.add( 'scalar' )
	  #end if-else ds_type match
        #end if visible
      #end for k

#			-- Read and extract
#			--
      results = self.data.ReadDataSetValues2( *specs )

      #self.refAxisValues = results[ self.state.timeDataSet ]
      if self.refAxisDataSet:
	#values_dict = results[ '*' + self.refAxisDataSet ]
	#self.refAxisValues = values_dict.itervalues().next()
	values_item = results[ '*' + self.refAxisDataSet ]
	if isinstance( values_item, dict ):
	  self.refAxisValues = values_item.itervalues().next()
	else:
	  self.refAxisValues = values_item
      else:
        self.refAxisValues = results[ self.state.timeDataSet ]

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )
        if ds_rec[ 'visible' ] and ds_name is not None and \
	    ds_name in results:
	  self.dataSetValues[ k ] = results[ ds_name ]
      #end for k
    #end if valid state
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._UpdateRefAxisMenu()			-
  #----------------------------------------------------------------------
  def _UpdateRefAxisMenu( self, *args, **kwargs ):
    """Must be called from the UI thread.
"""
    if self.data is not None:
      Widget.ClearMenu( self.refAxisMenu )

      menu_types = []
      menu_types = self.GetDataSetTypes()

#			-- Map dataset names to base category/type
#			--
      names_by_type = {}
      for dtype in menu_types:
        dataset_names = self.data.GetDataSetNames( dtype )
	if dataset_names:
	  ndx = dtype.find( ':' )
	  if ndx >= 0:
	    dtype = dtype[ 0 : ndx ]

	  if dtype in names_by_type:
	    names_by_type[ dtype ] += dataset_names
	  else:
	    names_by_type[ dtype ] = list( dataset_names )
	#end if dataset_names
      #end for dtype

#			-- Create pullrights
#			--
      for dtype, ds_names in sorted( names_by_type.iteritems() ):
        if ds_names:
	  type_menu = wx.Menu()
	  for ds_name in sorted( ds_names ):
	    item = wx.MenuItem(
	        type_menu, wx.ID_ANY, ds_name,
		kind = wx.ITEM_CHECK
		)
	    self.container.Bind( wx.EVT_MENU, self._OnSelectRefAxisDataSet, item )
	    type_menu.AppendItem( item )
	    if ds_name == self.refAxisDataSet:
	      item.Check()
	  #end for ds_name

          type_item = wx.MenuItem(
	      self.refAxisMenu, wx.ID_ANY, dtype,
	      subMenu = type_menu
	      )
	  self.refAxisMenu.AppendItem( type_item )
        #end if ds_names
      #end for dtype, ds_names

      item = wx.MenuItem(
          self.refAxisMenu, wx.ID_ANY, 'Time Dataset',
	  kind = wx.ITEM_CHECK
	  )
      self.container.Bind( wx.EVT_MENU, self._OnSelectRefAxisDataSet, item )
      self.refAxisMenu.AppendItem( item )
      if not self.refAxisDataSet:
        item.Check()
    #end if-else self.data
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

    if 'aux_sub_addrs' in kwargs and \
        kwargs[ 'aux_sub_addrs' ] != self.auxSubAddrs:
      replot = True
      self.auxSubAddrs = \
          self.data.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      replot = True
      self.axialValue = kwargs[ 'axial_value' ]
    #end if

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
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

#end TimePlots
