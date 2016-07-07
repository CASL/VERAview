#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plots.py					-
#	HISTORY:							-
#		2016-07-07	leerw@ornl.gov				-
#	  Renaming "vanadium" to "fixed_detector".
#		2016-07-06	leerw@ornl.gov				-
#	  Not acception timeDataSet changes.
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
    self.assemblyIndex = ( -1, -1, -1 )
    self.auxChannelColRows = []
    self.auxPinColRows = []
    self.ax2 = None
    self.axialValue = DataModel.CreateEmptyAxialValue()
    self.channelColRow = ( -1, -1 )
    self.channelDataSet = 'channel_liquid_temps [C]'
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by dataset name or pseudo name
    self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name or pseudo name
    self.detectorDataSet = 'detector_response'
    self.detectorIndex = ( -1, -1, -1 )
    self.fixedDetectorDataSet = 'fixed_detector_response'
    self.pinColRow = ( -1, -1 )
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )

    self.refAxisValues = np.empty( 0 )
    #self.refDataSet = 'state'
    self.scalarDataSet = 'keff'
    self.scalarValues = []
    #self.timeDataSet = 'state'

    super( TimePlots, self ).__init__( container, id, ref_axis = 'x' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = '"Axial=%.3f"\n' % self.axialValue[ 0 ]

#		-- Must be valid state
#		--
    if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):

#		 	-- Create header
#		 	--
      header = self.state.timeDataSet
      #for name, item in sorted( self.dataSetValues ):
      for k in sorted( self.dataSetValues.keys() ):
	name = self.data.GetDataSetDisplayName( self._GetDataSetName( k ) )
	item = self.dataSetValues[ k ]
	if not isinstance( item, dict ):
	  item = { '': item }
        for rc in sorted( item.keys() ):
          header += ',' + name
	  if rc:
            header += '@' + DataModel.ToAddrString( *rc )
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
    more_def = \
      [
	( '-', None ),
        ( 'Edit Dataset Properties', self._OnEditDataSetProps )
        #( 'Select Datasets', self._OnSelectDataSets )
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
    ds_values = self._FindDataSetValues( ev.xdata )
    if ds_values is not None:
      tip_str = '%s=%.3g' % ( self.state.timeDataSet, ev.xdata )
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

#		-- Something to plot?
#		--
    if len( self.dataSetValues ) > 0:
#			-- Determine axis datasets
#			--
      left_ds_name, right_ds_name = self._ResolveDataSetAxes()

#			-- Configure axes
#			--
      if right_ds_name is not None and self.ax2 is not None:
        self.ax2.set_ylabel( right_ds_name, fontsize = label_font_size )
	ds_range = self.data.GetRange(
	    right_ds_name,
	    self.stateIndex if self.state.scaleMode == 'state' else -1
	    )
	if self.data.IsValidRange( *ds_range ):
          self.ax2.set_ylim( *ds_range )
	  self.ax2.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

      self.ax.set_ylabel( left_ds_name, fontsize = label_font_size )
      ds_range = self.data.GetRange(
	  left_ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
      self.ax.set_xlabel( self.state.timeDataSet, fontsize = label_font_size )
      if self.data.IsValidRange( *ds_range ):
        self.ax.set_ylim( *ds_range )
        self.ax.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

#			-- Set title
#			--
      show_assy_addr = \
          self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] )

#      title_str = 'Assy %d %s, %s %.3g' % \
#          ( self.assemblyIndex[ 0 ] + 1, show_assy_addr,
#	    self.state.state.timeDataSet,
#	    self.data.GetTimeValue( self.stateIndex, self.state.state.timeDataSet )
#	    )
      title_str = 'Assy %d %s, Axial %.3f' % \
          ( self.assemblyIndex[ 0 ] + 1, show_assy_addr, self.axialValue[ 0 ] )

      title_line2 = ''
      if 'channel' in self.dataSetTypes:
	chan_rc = ( self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1 )
        title_line2 += 'Chan %s' % str( chan_rc )

      if 'detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Det %d %s' % \
	    ( self.detectorIndex[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ) )

      if 'pin' in self.dataSetTypes or 'other' in self.dataSetTypes:
        pin_rc = ( self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1 )
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Pin %s' % str( pin_rc )

      if 'fixed_detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Van %d %s' % \
	    ( self.detectorIndex[ 0 ] + 1,
	      self.data.core.CreateAssyLabel( *self.detectorIndex[ 1 : 3 ] ) )

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

	plot_type = '-'
	ds_type = self.data.GetDataSetType( ds_name )
#	axial_values = self.data.core.axialMeshCenters
	if ds_type.startswith( 'detector' ):
#	  axial_values = self.data.core.detectorMeshCenters
	  plot_type = '.'
	elif ds_type.startswith( 'channel' ):
	  plot_type = '--'
	elif ds_type.startswith( 'pin' ):
	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  plot_type = 'x'
#	  axial_values = self.data.core.fixedDetectorMeshCenters
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
	self.channelDataSet  if name == 'Selected channel dataset' else \
        self.detectorDataSet  if name == 'Selected detector dataset' else \
        self.pinDataSet  if name == 'Selected pin dataset' else \
        self.fixedDetectorDataSet  if name == 'Selected fixed_detector dataset' else \
	self.scalarDataSet  if name == 'Selected scalar dataset' else \
	name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      [
      'channel', 'detector',
      'pin', 'pin:assembly', 'pin:axial', 'pin:core',
      'scalar', 'fixed_detector'
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
        STATE_CHANGE_assemblyIndex,
        STATE_CHANGE_auxChannelColRows, STATE_CHANGE_auxPinColRows,
	STATE_CHANGE_axialValue,
	STATE_CHANGE_channelColRow, STATE_CHANGE_channelDataSet,
	STATE_CHANGE_detectorIndex, STATE_CHANGE_detectorDataSet,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_scalarDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet,
	STATE_CHANGE_fixedDetectorDataSet
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
    self.ax = self.fig.add_axes([ 0.15, 0.12, 0.75, 0.65 ])
    self.ax2 = self.ax.twinx() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		InitDataSetSelections()				-
  #----------------------------------------------------------------------
  def InitDataSetSelections( self, ds_types ):
    """Special hook called in VeraViewFrame.LoadDataModel().
"""
    axis = 'left'
    for dtype in sorted( list( ds_types ) ):
      self.dataSetSelections[ self.GetSelectedDataSetName( dtype ) ] = \
        { 'axis': axis, 'scale': 1.0, 'visible': True }
      axis = 'right' if axis == 'left' else ''
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
	'aux_channel_colrows': self.state.auxChannelColRows,
	'aux_pin_colrows': self.state.auxPinColRows,
	'axial_value': axial_value,
	'channel_colrow': chan_colrow,
	'channel_dataset': self.state.channelDataSet,
	'detector_dataset': self.state.detectorDataSet,
	'detector_index': detector_ndx,
	'pin_colrow': pin_colrow,
	'pin_dataset': self.state.pinDataSet,
	'scalar_dataset': self.state.scalarDataSet,
	'state_index': state_ndx,
	'time_dataset': self.state.timeDataSet
	}

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
	'assemblyIndex', 'auxChannelColRows', 'auxPinColRows',
	'axialValue', 'channelColRow', 'channelDataSet',
	'dataSetSelections', 'detectorDataSet',
	'pinColRow', 'pinDataSet',
	'scalarDataSet', 'fixedDetectorDataSet'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( TimePlots, self ).LoadProps( props_dict )
    wx.CallAfter( self.UpdateState, replot = True )
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
	'assemblyIndex', 'auxChannelColRows', 'auxPinColRows',
	'axialValue', 'channelColRow', 'channelDataSet',
	'dataSetSelections', 'detectorDataSet',
	'pinColRow', 'pinDataSet',
	'scalarDataSet', 'fixedDetectorDataSet'
	):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """Noop since this displays multiple datasets.
"""
#    wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
#    self.FireStateChange( pin_dataset = ds_name )
    pass
  #end SetDataSet


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
Once aux{Channel,Pin}ColRows include the assembly and axial indexes,
compare each new dataset with what's in self.dataSetValues and only load
new ones in new_ds_values, copying from self.dataSetValues for ones
already read.
"""
    #del self.refAxisValues[ : ]
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

    #x new_ds_types = set()
    #x new_ds_values = {}

#		-- Must have data
#		--
    if DataModel.IsValidObj( self.data, axial_level = self.axialValue[ 1 ] ):
      chan_colrow_list = None
      pin_colrow_list = None

#			-- Construct read specs
#			--
      specs = []
      specs.append( { 'ds_name': self.state.timeDataSet} )

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

#				-- Must be visible
        if ds_rec[ 'visible' ] and ds_name is not None:
	  ds_type = self.data.GetDataSetType( ds_name )
	  spec = { 'ds_name': ds_name }

	  if ds_type is None:
	    pass

#					-- Channel
	  elif ds_type.startswith( 'channel' ):
#						-- Lazy creation
	    if chan_colrow_list is None:
              chan_colrow_list = list( self.auxChannelColRows )
              chan_colrow_list.insert( 0, self.channelColRow )

	    spec[ 'assembly_index' ] = self.assemblyIndex[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    spec[ 'channel_colrows' ] = chan_colrow_list
	    specs.append( spec )
            self.dataSetTypes.add( 'channel' )

#					-- Detector
	  elif ds_type.startswith( 'detector' ):
	    spec[ 'detector_index' ] = self.detectorIndex[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    specs.append( spec )
            self.dataSetTypes.add( 'detector' )

#					-- Pin
	  elif ds_type.startswith( 'pin' ):
#						-- Lazy creation
	    if pin_colrow_list is None:
              pin_colrow_list = list( self.auxPinColRows )
              pin_colrow_list.insert( 0, self.pinColRow )

	    spec[ 'assembly_index' ] = self.assemblyIndex[ 0 ]
	    spec[ 'axial_cm' ] = self.axialValue[ 0 ]
	    spec[ 'pin_colrows' ] = pin_colrow_list
	    specs.append( spec )
            self.dataSetTypes.add( 'pin' )

#					-- Fixed detector
	  elif ds_type.startswith( 'fixed_detector' ):
	    spec[ 'detector_index' ] = self.detectorIndex[ 0 ]
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

      self.refAxisValues = results[ self.state.timeDataSet ]

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )
        if ds_rec[ 'visible' ] and ds_name is not None:
	  self.dataSetValues[ k ] = results[ ds_name ]
      #end for k
    #end if valid state
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues_slow()			-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues_slow( self ):
    """Rebuild dataset arrays to plot.
"""
    #del self.refAxisValues[ : ]
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

    #x new_ds_types = set()
    #x new_ds_values = {}

#		-- Must have data
#		--
    if DataModel.IsValidObj( self.data, axial_level = self.axialValue[ 1 ] ):
      chan_colrow_list = None
      pin_colrow_list = None

#			-- Build reference axis values
#			--
      self.refAxisValues = self.data.ReadDataSetValues( self.state.timeDataSet )

#			-- Build dict of arrays for selected datasets
#			--
      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	ds_name = self._GetDataSetName( k )

#				-- Must be visible
#				--
        if ds_rec[ 'visible' ] and ds_name is not None:
	  ds_values = None
	  ds_type = self.data.GetDataSetType( ds_name )

#					-- Channel
	  if ds_type.startswith( 'channel' ):
#						-- Lazy creation
	    if chan_colrow_list is None:
              chan_colrow_list = list( self.auxChannelColRows )
              chan_colrow_list.insert( 0, self.channelColRow )

	    ds_values = self.data.ReadDataSetValues(
	        ds_name,
		assembly_index = self.assemblyIndex[ 0 ],
		axial_value = self.axialValue[ 0 ],
		channel_colrows = chan_colrow_list
		)
            self.dataSetTypes.add( 'channel' )

#					-- Detector
	  elif ds_type.startswith( 'detector' ):
	    ds_values = self.data.ReadDataSetValues(
	        ds_name,
		detector_index = self.detectorIndex[ 0 ],
		axial_value = self.axialValue[ 0 ]
		)
            self.dataSetTypes.add( 'detector' )

#					-- Pin
	  elif ds_type.startswith( 'pin' ):
#						-- Lazy creation
	    if pin_colrow_list is None:
              pin_colrow_list = list( self.auxPinColRows )
              pin_colrow_list.insert( 0, self.pinColRow )

	    ds_values = self.data.ReadDataSetValues(
	        ds_name,
		assembly_index = self.assemblyIndex[ 0 ],
		axial_value = self.axialValue[ 0 ],
		pin_colrows = pin_colrow_list
		)
            self.dataSetTypes.add( 'pin' )

#					-- Fixed detector
	  elif ds_type.startswith( 'fixed_detector' ):
	    ds_values = self.data.ReadDataSetValues(
	        ds_name,
		detector_index = self.detectorIndex[ 0 ],
		axial_value = self.axialValue[ 0 ]
		)
            self.dataSetTypes.add( 'fixed_detector' )

#					-- Scalar
	  else:
	    ds_values = self.data.ReadDataSetValues( ds_name )
            self.dataSetTypes.add( 'scalar' )

	  #end if ds_type match

	  if ds_values is not None:
	    self.dataSetValues[ k ] = ds_values
        #end if visible
      #end for each dataset
    #end if valid state
  #end _UpdateDataSetValues_slow


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
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.detectorDataSet:
      self.detectorDataSet = kwargs[ 'detector_dataset' ]
      select_name = self.GetSelectedDataSetName( 'detector' )
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
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'scalar_dataset' in kwargs and \
        kwargs[ 'scalar_dataset' ] != self.scalarDataSet:
      self.scalarDataSet = kwargs[ 'scalar_dataset' ]
      select_name = self.GetSelectedDataSetName( 'scalar' )
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if 'time_dataset' in kwargs:
      replot = True

    if 'fixed_detector_dataset' in kwargs and kwargs[ 'fixed_detector_dataset' ] != self.fixedDetectorDataSet:
      self.fixedDetectorDataSet = kwargs[ 'fixed_detector_dataset' ]
      select_name = self.GetSelectedDataSetName( 'fixed_detector' )
      if select_name in self.dataSetSelections and \
          self.dataSetSelections[ select_name ][ 'visible' ]:
        replot = True
    #end if

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end TimePlots
