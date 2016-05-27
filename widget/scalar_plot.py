#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		scalar_plot.py					-
#	HISTORY:							-
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
#	CLASS:		ScalarPlot					-
#------------------------------------------------------------------------
class ScalarPlot( PlotWidget ):
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

    super( ScalarPlot, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.ax2 = None
    self.dataSetDialog = None
    self.dataSetSelections = {}  # keyed by dataset name or pseudo name
    #self.dataSetTypes = set()
    self.dataSetValues = {}  # keyed by dataset name or pseudo name

    self.refAxisValues = []
    #self.refDataSet = 'state'
    self.scalarDataSet = 'state'
    self.scalarValues = []
    self.timeDataSet = 'state'

    super( ScalarPlot, self ).__init__( container, id, ref_axis = 'x' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
#x    csv_text = None
#x
#x    if DataModel.IsValidObj( self.data ):
#x      core = self.data.GetCore()
#x
#x      title = '%s=%.3g' % (
#x	  self.state.timeDataSet,
#x	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
#x          )
#x
#x      title_set = set( [] )
#x      axial_mesh_datasets = []
#x      detector_mesh_datasets = []
#x      detector_mesh_header = 'Detector Mesh Center'
#x
#x      for k in self.dataSetSelections:
#x        ds_rec = self.dataSetSelections[ k ]
#x	ds_name = self._GetDataSetName( k )
#x
#x        if ds_rec[ 'visible' ] and ds_name is not None:
#x	  ds_display_name = self.data.GetDataSetDisplayName( ds_name )
#x	  ds_type = self.data.GetDataSetType( ds_name )
#x	  dset = self.data.GetStateDataSet( self.stateIndex, ds_name )
#x	  dset_array = dset.value if dset is not None else None
#x	  if dset_array is None:
#x	    pass
#x
#x	  #elif ds_display_name in self.data.GetDataSetNames( 'channel' ):
#x	  elif ds_type.startswith( 'channel' ):
#x	    valid = self.data.IsValid(
#x	        assembly_index = self.assemblyIndex,
#x		axial_level = self.axialValue[ 1 ],
#x		channel_colrow = self.channelColRow
#x	        )
#x	    if valid:
#x	      if 'channel' not in title_set:
#x	        title_set.add( 'channel' )
#x		title += '; Channel=(%d,%d)' % ( 
#x		    self.channelColRow[ 0 ] + 1, self.channelColRow[ 1 ] + 1
#x		    )
#x	      if cur_selection_flag:
#x	        values = dset_array[
#x		    self.channelColRow[ 1 ], self.channelColRow[ 0 ],
#x		    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
#x		    ]
#x	      else:
#x	        values = dset_array[
#x		    self.channelColRow[ 1 ], self.channelColRow[ 0 ],
#x		    :, self.assemblyIndex[ 0 ]
#x	            ]
#x	      axial_mesh_datasets.append( ( ds_display_name, values ) )
#x
#x	  #elif ds_display_name in self.data.GetDataSetNames( 'detector' ):
#x	  elif ds_type.startswith( 'detector' ):
#x	    valid = self.data.IsValid(
#x		axial_level = self.axialValue[ 1 ],
#x	        detector_index = self.detectorIndex[ 0 ]
#x		)
#x	    if valid:
#x	      if 'detector' not in title_set:
#x	        title_set.add( 'detector' )
#x		title += '; Detector=%d' % ( self.detectorIndex[ 0 ] + 1 )
#x
#x	      if cur_selection_flag:
#x	        values = \
#x		    dset_array[ self.axialValue[ 1 ], self.detectorIndex[ 0 ] ]
#x	      else:
#x	        values = dset_array[ :, self.detectorIndex[ 0 ] ]
#x	      detector_mesh_datasets.append( ( ds_display_name, values ) )
#x
#x	  # deprecated
#x	  elif ds_name in self.data.GetDataSetNames( 'derived' ) or \
#x	      ds_display_name in self.data.GetDataSetNames( 'extra' ) or \
#x	      ds_display_name in self.data.GetDataSetNames( 'other' ):
#x	    valid = self.data.IsValidForShape(
#x		dset.shape,
#x		assembly_index = self.assemblyIndex[ 0 ],
#x		pin_colrow = self.pinColRow
#x	        )
#x	    if valid:
#x	      assy_ndx = min( self.assemblyIndex[ 0 ], dset.shape[ 3 ] - 1 )
#x	      temp_nax = min( self.data.core.nax, dset.shape[ 2 ] )
#x	      values = dset_array[
#x		  self.pinColRow[ 1 ], self.pinColRow[ 0 ],
#x		  0 : temp_nax, assy_ndx
#x	          ]
#x	      axial_mesh_datasets.append( ( ds_display_name, values ) )
#x
#x	  #elif ds_display_name in self.data.GetDataSetNames( 'pin' ):
#x	  elif ds_type.startswith( 'pin' ):
#x	    valid = self.data.IsValid(
#x	        assembly_index = self.assemblyIndex,
#x		axial_level = self.axialValue[ 1 ],
#x		pin_colrow = self.pinColRow
#x	        )
#x	    if valid:
#x	      if 'pin' not in title_set:
#x	        title_set.add( 'pin' )
#x		title += '; Pin=(%d,%d)' % ( 
#x		    self.pinColRow[ 0 ] + 1, self.pinColRow[ 1 ] + 1
#x		    )
#x
#x	      if cur_selection_flag:
#x	        values = dset_array[
#x		    self.pinColRow[ 1 ], self.pinColRow[ 0 ],
#x		    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
#x		    ]
#x	      else:
#x	        values = dset_array[
#x		    self.pinColRow[ 1 ], self.pinColRow[ 0 ],
#x		    :, self.assemblyIndex[ 0 ]
#x	            ]
#x	      axial_mesh_datasets.append( ( ds_display_name, values ) )
#x	  #end if category match
#x        #end if visible
#x      #end for each dataset
#x
#x      #csv_text = '#"%s"\n' % title
#x      csv_text = '"%s"\n' % title
#x
#x      if len( axial_mesh_datasets ) > 0:
#x        header = 'Axial Mesh Center'
#x        for name, values in axial_mesh_datasets:
#x	  header += ',' + name
#x        csv_text += header + '\n'
#x
#x	if cur_selection_flag:
#x	  j_range = ( self.axialValue[ 1 ], )
#x	else:
#x	  j_range = range( len( core.axialMeshCenters ) - 1, -1, -1 )
#x	for j in j_range:
#x	  row = '%.7g' % core.axialMeshCenters[ j ]
#x          for name, values in axial_mesh_datasets:
#x	    cur_val = 0
#x	    if not hasattr( values, '__len__' ):
#x	      if j == self.axialValue[ 1 ]:
#x	        cur_val = values
#x	    elif len( values ) > j:
#x	      cur_val = values[ j ]
#x
#x	    if cur_val != 0:
#x	      row += ',%.7g' % cur_val
#x	    else:
#x	      row += ',0'
#x          #end for name, values
#x
#x          csv_text += row + '\n'
#x	#end for j
#x
#x	csv_text += '\n'
#x      #end if
#x
#x      if len( detector_mesh_datasets ) > 0:
#x        header = 'Detector Mesh Center'
#x        for name, values in detector_mesh_datasets:
#x	  header += ',' + name
#x        csv_text += header + '\n'
#x
#x	if cur_selection_flag:
#x	  j_range = ( self.axialValue[ 2 ], )
#x	else:
#x	  j_range = range( len( core.detectorMeshCenters ) - 1, -1, -1 )
#x	for j in j_range:
#x	  row = '%.7g' % core.detectorMeshCenters[ j ]
#x          for name, values in detector_mesh_datasets:
#x	    cur_val = 0
#x	    if not hasattr( values, '__len__' ):
#x	      if j == self.axialValue[ 2 ]:
#x	        cur_val = values
#x	    elif len( values ) > j:
#x	      cur_val = values[ j ]
#x
#x	    if cur_val != 0:
#x	      row += ',%.7g' % cur_val
#x	    else:
#x	      row += ',0'
#x          #end for name, values
#x
#x          csv_text += row + '\n'
#x	#end for j
#x      #end if
#x    #end if valid state
#x
#x    return  csv_text
    return  None
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( ScalarPlot, self )._CreateMenuDef( data_model )
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
      tip_str = '%s=%.3g' % ( self.timeDataSet, ev.xdata )
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
    super( ScalarPlot, self )._DoUpdatePlot( wd, ht )

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
    self.ax.set_title(
	'Versus ' + self.timeDataSet,
	fontsize = self.titleFontSize
	)

#		-- Something to plot?
#		--
    if len( self.dataSetValues ) > 0:
#			-- Determine axis datasets
#			--
#      left_ds_name = right_ds_name = None
#      for k, rec in self.dataSetSelections.iteritems():
#	if rec[ 'visible' ]:
#          if rec[ 'axis' ] == 'left':
#	    left_ds_name = self._GetDataSetName( k )
#          elif rec[ 'axis' ] == 'right':
#	    right_ds_name = self._GetDataSetName( k )
#          elif left_ds_name is None:
#	    left_ds_name = self._GetDataSetName( k )
#      #end for
#      if left_ds_name is None:
#        left_ds_name = right_ds_name
      left_ds_name, right_ds_name = self._ResolveDataSetAxes()

#			-- Configure axes
#			--
      if right_ds_name is not None and self.ax2 is not None:
        self.ax2.set_ylabel( right_ds_name, fontsize = label_font_size )
	ds_range = self.data.GetRange(
	    right_ds_name,
	    self.stateIndex if self.state.scaleMode == 'state' else -1
	    )
        self.ax2.set_ylim( *ds_range )
	self.ax2.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

      self.ax.set_ylabel( left_ds_name, fontsize = label_font_size )
      ds_range = self.data.GetRange(
	  left_ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
      self.ax.set_ylim( *ds_range )
      self.ax.set_xlabel( self.timeDataSet, fontsize = label_font_size )
      self.ax.yaxis.get_major_formatter().set_powerlimits( ( -3, 3 ) )

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
#	ds_type = self.data.GetDataSetType( ds_name )
#	axial_values = self.data.core.axialMeshCenters
#	if ds_type.startswith( 'detector' ):
#	  axial_values = self.data.core.detectorMeshCenters
#	  plot_type = '.'
#	elif ds_type.startswith( 'channel' ):
#	  plot_type = '--'
#	elif ds_type.startswith( 'pin' ):
#	  plot_type = '-'
#	elif ds_type.startswith( 'vanadium' ):
#	  axial_values = self.data.core.vanadiumMeshCenters
#	  plot_type = '-.'
#	else:
#	  plot_type = ':'

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

#	  cur_label = \
#	      legend_label + '@' + DataModel.ToAddrString( *rc ) \
#	      if rc else legend_label

	  plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	  cur_axis = self.ax2 if rec[ 'axis' ] == 'right' else self.ax
	  cur_axis.plot(
		self.refAxisValues, cur_values * scale, plot_mode,
	        label = legend_label, linewidth = 2
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
#      self.fig.text(
#          0.1, 0.985, title_str,
#	  horizontalalignment = 'left', verticalalignment = 'top'
#	  )

#			-- Axial value line
#			--
      self.axline = \
          self.ax.avhline( color = 'r', linestyle = '-', linewidth = 1 )
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
        len( sample ) > ndx:
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
    return  ( 'statepoint', )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		_GetDataSetName()				-
  #----------------------------------------------------------------------
  def _GetDataSetName( self, name ):
    """Determines actual dataset name if a pseudo name is provided.
"""
    return \
	None  if name is None else \
	self.scalarDataSet  if name == 'Selected scalar dataset' else \
	self.timeDataSet  if name == 'Selected time dataset' else \
	name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		ScalarPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'scalar', 'pin:core' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		ScalarPlot.GetDataSetDisplayMode()		-
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
        STATE_CHANGE_scalarDataSet, STATE_CHANGE_stateIndex,
	STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Scalar Plots'
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
    self.ax = self.fig.add_axes([ 0.1, 0.12, 0.85, 0.7 ])
    self.ax2 = self.ax.twinx() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		InitDataSetSelections()				-
  #----------------------------------------------------------------------
#  def InitDataSetSelections( self, ds_types ):
#    """Special hook called in VeraViewFrame.LoadDataModel().
#"""
#    axis = 'left'
#    for dtype in sorted( list( ds_types ) ):
#      self.dataSetSelections[ self.GetSelectedDataSetName( dtype ) ] = \
#        { 'axis': axis, 'scale': 1.0, 'visible': True }
#      axis = 'right' if axis == 'left' else ''
#  #end InitDataSetSelections


  #----------------------------------------------------------------------
  #	METHOD:		ScalarPlot.IsDataSetVisible()			-
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
      state_ndx = self.data.NormalizeStateIndex( self.state.stateIndex )
      update_args = \
        {
	'state_index': state_ndx,
	'time_dataset': self.state.timeDataSet
	}

    else:
      update_args = {}

    return  update_args
  #end _LoadDataModelValues


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
    super( ScalarPlot, self )._OnMplMouseRelease( ev )

    button = ev.button or 1
    if button == 1 and self.cursor is not None:
      ndx = self.data.FindListIndex( self.refAxisValues, self.cursor[ 0 ] )
      if ndx >= 0:
        self.UpdateState( state_index = ndx )
        self.FireStateChange( state_index = ndx )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		ScalarPlot._ResolveDataSetAxes()		-
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
	  break
    #end if

    if right is None:
      for name in visible_names:
        rec = self.dataSetSelections[ name ]
	if rec[ 'axis' ] != 'left':
	  rec[ 'axis' ] = 'right'
	  right_name = name
	  break
    #end if

    return\
      ( self._GetDataSetName( left_name ), self._GetDataSetName( right_name ) )
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
  #	METHOD:		ScalarPlot.ToggleDataSetVisible()		-
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
    #xxxxx
    if self.data is not None and self.data.IsValid( state_index = self.stateIndex ):
      axial_ds_names = self.data.GetDataSetNames( 'axial' )

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

#					-- Vanadium
	  elif ds_type.startswith( 'vanadium' ):
	    det_ndx = min( self.detectorIndex[ 0 ], dset_array.shape[ 1 ] )
	    self.dataSetValues[ k ] = dset_array[ :, det_ndx ]
            self.dataSetTypes.add( 'vanadium' )

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
    kwargs = super( ScalarPlot, self )._UpdateStateValues( **kwargs )
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

    if 'vanadium_dataset' in kwargs and kwargs[ 'vanadium_dataset' ] != self.vanadiumDataSet:
      self.vanadiumDataSet = kwargs[ 'vanadium_dataset' ]
      select_name = self.GetSelectedDataSetName( 'vanadium' )
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

#end ScalarPlot
