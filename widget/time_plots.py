#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		time_plots.py					-
#	HISTORY:							-
#		2019-01-16	leerw@ornl.gov				-
#         Transition from tally to fluence.
#		2018-11-20	leerw@ornl.gov				-
#         Applying new DataModelMgrTree and visible datasets button.
#		2018-11-09	leerw@ornl.gov				-
#         Added support for radial_detector datasets in numbers mode.
#		2018-11-02	leerw@ornl.gov				-
#         Adding support for intrapin_edits datasets.
#		2018-10-20	leerw@ornl.gov				-
#         Added quotes around column label in _CreateClipboardData().
#		2018-10-03	leerw@ornl.gov				-
#	  Passing self.state.weightsMode == 'on' as use_factors param to
#	  DataModelMgr.GetRangeAll() in _DoUpdatePlot().
#		2018-09-12	leerw@ornl.gov				-
#	  Tracking dataset selection order.
#		2018-09-07	leerw@ornl.gov				-
#	  Simplified _CreateClipboardData() to use data stored in self.ax.
#		2018-09-06	leerw@ornl.gov				-
#	  Fixed resolution of different time values and optional reference
#	  axis values.
#		2018-08-21	leerw@ornl.gov				-
#	  Added _IsTimeReplot().
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-05-13	leerw@ornl.gov				-
#	  Removed GetDataSetPropertyNames().
#		2017-03-25	leerw@ornl.gov				-
#	  Removing implicit dataset axis management.
#		2017-01-26	leerw@ornl.gov				-
#	  Using PLOT_MODES instead of setting plot type based on
#	  derived vs not-derived dataset.
#	  Removed assembly index from titles.
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
import hashlib, logging, math, os, six, sys, time, traceback
import numpy as np
from scipy import interpolate
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

from event.state import *

from .bean.plot_dataset_props import *
from .plot_widget import *
from .widget import *
from .widgetcontainer import *


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
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
    self.curDataSet = None
    self.dataSetDialog = None
    self.dataSetOrder = []  # list of DataSetName
    self.dataSetSelections = {}  # keyed by DataSetName
    self.dataSetTypes = set()

		#-- keyed by DataSetName, dicts with keys 'times', 'data'
    self.dataSetValues = {}

    self.fluenceAddr = FluenceAddress()
    self.nodeAddr = -1

#		-- DataSetName instance, None means use self.state.timeDataSet
    self.refAxisDataSet = None
    self.refAxisMenu = wx.Menu()
    self.refAxisTimes = None  # None means refAxisValues *are* the times
    self.refAxisValues = np.empty( 0 )
    #self.scaleMode = 'selected'
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
      csv_text = 'Assy %s; Axial %.3f\n' % (
          #self.assemblyAddr[ 0 ] + 1,
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue.cm
	  )
#      cur_time_ndx = -1

      if self.refAxisTimes is not None:
#        if mode != 'displayed':
#          cur_time_ndx = DataUtils.\
#              FindListIndex( self.refAxisTimes, self.timeValue, 'a' )
        xaxis_dataset = self.dmgr.GetDataSetDisplayName( self.refAxisDataSet )
      else:
#        if mode != 'displayed':
#	  cur_time_ndx = DataUtils.\
#	      FindListIndex( self.refAxisValues, self.timeValue, 'a' )
        xaxis_dataset = self.state.timeDataSet

      groups = {}

      lines = self.ax.lines
      if self.ax2:
        lines += self.ax2.lines

      for line in lines:
	label = line.get_label()
	if not label.startswith( '_' ):
          label = '"' + label + '"'
	  xdata = line.get_xdata()
	  ydata = line.get_ydata()
	  if hasattr( xdata, '__iter__' ) and hasattr( ydata, '__iter__' ):
#	      len( xdata ) > max( 0, cur_time_ndx ) and \
#	      len( ydata ) > max( 0, cur_time_ndx ):
	    if mode != 'displayed':
	      ndx = DataUtils.FindListIndex( xdata, self.timeValue, 'a' )
	      if ndx >= 0:
	        xdata = xdata[ ndx : ndx + 1 ]
		ydata = ydata[ ndx : ndx + 1 ]
#	    if cur_time_ndx >= 0:
#	      xdata = xdata[ cur_time_ndx : cur_time_ndx + 1 ]
#	      ydata = ydata[ cur_time_ndx : cur_time_ndx + 1 ]

	    group_key = hashlib.sha1( xdata ).hexdigest()
	    group = groups.get( group_key )
	    if group is None:
	      dsets = []
	      group = dict( xdata = xdata, dsets = dsets )
	      groups[ group_key ] = group
	    else:
	      dsets = group.get( 'dsets' )
	    dsets.append( ( label, ydata ) )
	  #end if hasattr...
	#end if not label.startswith( '_' )
      #end for line in lines

      for group in six.itervalues( groups ):
	xdata = group.get( 'xdata' )
	dsets = group.get( 'dsets' )
	block = '\n{0},{1}\n'.format(
	    xaxis_dataset,
	    ','.join( [ i[ 0 ] for i in dsets ] )
	    )
	for i in range( len( xdata ) ):
	  row = '{0:.7g},{1}\n'.format(
	      xdata[ i ],
	      ','.join( [ '{0:.7g}'.format( ds[ 1 ][ i ] ) for ds in dsets ] )
	      )
          block += row
	#end for i in range( len( xdata ) )

        csv_text += block
      #end for group in six.itervalues( groups )

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData_1()			-
  #----------------------------------------------------------------------
  def _CreateClipboardData_1( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    core = self.dmgr.GetCore()
    if core:
      csv_text = 'Assy %s, Axial %.3f\n' % (
          #self.assemblyAddr[ 0 ] + 1,
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue.cm
	  )
      cur_time_ndx = -1

      if self.refAxisTimes is not None:
        if mode != 'displayed':
          cur_time_ndx = DataUtils.\
              FindListIndex( self.refAxisTimes, self.timeValue, 'a' )
        xaxis_dataset = self.dmgr.GetDataSetDisplayName( self.refAxisDataSet )
      else:
        if mode != 'displayed':
	  cur_time_ndx = DataUtils.\
	      FindListIndex( self.refAxisValues, self.timeValue, 'a' )
        xaxis_dataset = self.state.timeDataSet

      model_groups = {}

      lines = self.ax.lines
      if self.ax2:
        lines += self.ax2.lines

      for line in lines:
	label = line.get_label()
	ndx = label.find( '|' )
	model_name = label[ 0 : ndx ]  if ndx >= 0 else  'default'
	if not label.startswith( '_' ):
	  xdata = line.get_xdata()
	  ydata = line.get_ydata()
	  if hasattr( xdata, '__iter__' ) and \
	      len( xdata ) > max( 0, cur_time_ndx ) and \
	      hasattr( ydata, '__iter__' ) and \
	      len( ydata ) > max( 0, cur_time_ndx ):
	    if cur_time_ndx >= 0:
	      xdata = xdata[ cur_time_ndx : cur_time_ndx + 1 ]
	      ydata = ydata[ cur_time_ndx : cur_time_ndx + 1 ]

	    model_group = model_groups.get( model_name )
	    if model_group is None:
	      dsets = []
	      model_group = dict( xdata = xdata, dsets = dsets )
	      model_groups[ model_name ] = model_group
	    else:
	      dsets = model_group.get( 'dsets' )
	    dsets.append( ( label, ydata ) )
	  #end if hasattr...
	#end if not label.startswith( '_' )
      #end for line in lines

      for model_group in six.itervalues( model_groups ):
	xdata = model_group.get( 'xdata' )
	dsets = model_group.get( 'dsets' )
	block = '\n{0},{1}\n'.format(
	    xaxis_dataset,
	    ','.join( [ i[ 0 ] for i in dsets ] )
	    )
	for i in range( len( xdata ) ):
	  row = '{0:.7g},{1}\n'.format(
	      xdata[ i ],
	      ','.join( [ '{0:.7g}'.format( ds[ 1 ][ i ] ) for ds in dsets ] )
	      )
          block += row
	#end for i in range( len( xdata ) )

        csv_text += block
      #end for model_group in six.itervalues( model_groups )

    return  csv_text
  #end _CreateClipboardData_1


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( TimePlots, self )._CreateMenuDef()

#    select_scale_def = \
#      [
#        {
#	'label': 'All Datasets', 'kind': wx.ITEM_RADIO,
#	'handler': functools.partial( self._OnSetScaleMode, 'all' )
#	},
#        {
#	'label': LABEL_selectedDataSet, 'kind': wx.ITEM_RADIO, 'checked': True,
#	'handler': functools.partial( self._OnSetScaleMode, 'selected' )
#	}
#      ]
    more_def = \
      [
	{ 'label': '-' },
        {
	'label': 'Edit Dataset Properties...',
	'handler': self._OnEditDataSetProps
	},
#	{
#	'label': 'Select Left Axis Scale Mode',
#	'submenu': select_scale_def
#	},
	{
	'label': 'Select X-Axis Dataset...',
	'submenu': self.refAxisMenu
	},
        { 'label': 'Toggle Toolbar', 'handler': self._OnToggleToolBar }
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
      if self.refAxisTimes is not None:
        xaxis_name = self.dmgr.GetDataSetDisplayName( self.refAxisDataSet )
      else:
        xaxis_name = self.state.timeDataSet
      #tip_str = 'x=%.3g' % ev.xdata
      tip_str = '{0}={1:.3f}'.format( xaxis_name, ds_values[ '_refaxis_' ] )
      del ds_values[ '_refaxis_' ]

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

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'enter' )

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
        xaxis_label = '%s: %s' % (
	    self.dmgr.GetDataSetDisplayName( self.refAxisDataSet ),
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
        self.ax.xaxis.get_major_formatter().set_powerlimits( ( -2, 3 ) )
      else:
	xaxis_label = self.state.timeDataSet
      #end if-else self.refAxisDataSet

#			-- Determine axis datasets
#			--
      left_list, right_list = self._ListVisibleDataSets()

#			-- Configure x-axis
#			--
#				-- Right
      if len( right_list ) > 0 and self.ax2 is not None:
	label = self.dmgr.GetDataSetDisplayName( right_list[ 0 ] )
	if len( right_list ) > 1:
	  label += ',...'
        self.ax2.set_ylabel( label, fontsize = label_font_size )
	ds_range = self.dmgr.GetRangeAll(
	    self.timeValue if self.state.scaleMode == 'state' else -1.0,
	    self.state.weightsMode == 'on',
	    *right_list
	    )
	#scale_type = self.dmgr.GetDataSetScaleTypeAll( 'all', *right_list )
	scale_type = \
	    self.dmgr.GetDataSetScaleTypeAll( 'all', *right_list ) \
	    if self.scaleType == DEFAULT_scaleType else \
	    self.scaleType

        if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] ):
	  if scale_type == 'log':
	    self.ax2.set_yscale( 'log', nonposy = 'clip' )
	    self.ax2.set_ylim(
	        max( 1.0e-30, ds_range[ 0 ] ),
	        max( 1.0e-30, ds_range[ 1 ] )
	        )
	  else:
	    self.ax2.set_xscale( 'linear' )
            self.ax2.set_ylim( *ds_range[ 0 : 2 ] )
	    self.ax2.yaxis.get_major_formatter().set_powerlimits( ( -2, 3 ) )
	  #self.ax2.yaxis.get_major_formatter().set_scientific( True )

#				-- Left, primary
      self.ax.set_xlabel( xaxis_label, fontsize = label_font_size )
      label = self.dmgr.GetDataSetDisplayName( left_list[ 0 ] )
      if len( left_list ) > 1:
        label += ',...'
      self.ax.set_ylabel( label, fontsize = label_font_size )

#			-- Configure y-axis
#			--
      ds_range = list( self.customDataRange ) \
          if self.customDataRange is not None else \
	  [ NAN, NAN ]
      if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] ):
        calc_range = self.dmgr.GetRangeAll(
	    self.timeValue if self.state.scaleMode == 'state' else -1.0,
	    self.state.weightsMode == 'on',
	    *left_list
	    )
#				-- Scale over all plotted datasets?
#        if self.scaleMode == 'all':
#          for k in self.dataSetValues:
#	    cur_qname = self._GetDataSetName( k )
#	    if cur_qname != right_qds_name and cur_qname != left_qds_name:
#	      cur_range = self.dmgr.GetRange(
#	          cur_qname,
#	          self.timeValue if self.state.scaleMode == 'state' else -1.0
#	          )
#	      if calc_range is None:
#	        calc_range = tuple( cur_range )
#	      else:
#	        calc_range = (
#	            min( calc_range[ 0 ], cur_range[ 0 ] ),
#		    max( calc_range[ 1 ], cur_range[ 1 ] )
#	            )
#          #end for k

	if calc_range is None:
	  calc_range = ( 0.0, 10.0 )
        for i in xrange( min( len( ds_range ), len( calc_range ) ) ):
	  if math.isnan( ds_range[ i ] ):
	    ds_range[ i ] = calc_range[ i ]
      #end if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] )

      if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] ):
        #scale_type = self.dmgr.GetDataSetScaleTypeAll( 'all', *left_list )
	scale_type = \
	    self.dmgr.GetDataSetScaleTypeAll( 'all', *left_list ) \
	    if self.scaleType == DEFAULT_scaleType else \
	    self.scaleType
	if scale_type == 'log':
	  self.ax.set_yscale( 'log', nonposy = 'clip' )
	  self.ax.set_ylim(
	      max( 1.0e-30, ds_range[ 0 ] ),
	      max( 1.0e-30, ds_range[ 1 ] )
	      )
	else:
	  self.ax.set_yscale( 'linear' )
          self.ax.set_ylim( *ds_range[ 0 : 2 ] )
          self.ax.yaxis.get_major_formatter().set_powerlimits( ( -2, 3 ) )
	#self.ax.yaxis.get_major_formatter().set_scientific( True )

#				-- Build title
#				--
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )

      title_str = 'Assy %s, Axial %.3f' % \
          ( show_assy_addr, self.axialValue.cm )
          #( self.assemblyAddr[ 0 ] + 1, show_assy_addr, self.axialValue.cm )

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
	title_line2 += 'Det %s' % (
	    #self.assemblyAddr[ 0 ] + 1,
	    core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    )

      if 'fluence' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
        th =  \
int( core.fluenceMesh.GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' ) )
	title_line2 += 'Fluence r=%.1f,th=%d' % \
            ( core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ), th )

      if len( title_line2 ) > 0:
        title_str += '\n' + title_line2

#				-- Plot each selected dataset
#				--
      count = 0
      time_values_by_model = {}

      if self.refAxisTimes is not None:
        ifunc = interpolate.interp1d(
	    self.refAxisTimes, self.refAxisValues,
	    kind = 'linear', fill_value = 'extrapolate',
	    assume_sorted = True
	    )

      #for k in self.dataSetValues:
      for k in self.dataSetOrder:
        data_pair = self.dataSetValues[ k ]
	qds_name = self._GetDataSetName( k )
#					-- Determine x-axis values
#					--
	if self.refAxisTimes is None:
	  model_times = data_pair[ 'times' ]
	else:
	  model_times = time_values_by_model.get( qds_name.modelName )
	  if model_times is None:
	    model_times = [ ifunc( t ) for t in data_pair[ 'times' ] ]
	    time_values_by_model[ qds_name.modelName ] = model_times
	#end else not self.refAxisTimes is None

#					-- Scale and label
#					--
	rec = self.dataSetSelections[ k ]
	#scale = rec[ 'scale' ] if rec[ 'axis' ] == '' else 1.0
	scale = rec.get( 'scale', 1.0 )
	legend_label = self.dmgr.GetDataSetDisplayName( qds_name, True )
	if scale != 1.0:
	  legend_label += '*%.3g' % scale

#					-- Marker
#					--
	marker_size = None
#x	plot_type = '--' if self.dmgr.IsDerivedDataSet( qds_name ) else '-'
	plot_type = None
	ds_type = self.dmgr.GetDataSetType( qds_name )
	if ds_type.startswith( 'detector' ):
	  marker_size = 12
	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  marker_size = 12
	  plot_type = 'x'
#	else:
#	  plot_type = ':'

	data_set_item = data_pair[ 'data' ]
#	if not isinstance( data_set_item, dict ):
#	  data_set_item = { '': data_set_item }
	if isinstance( data_set_item, dict ):
	  rc_keys = \
	      sorted( six.iterkeys( data_set_item ), Widget.CompareAuxAddrs )
	else:
	  data_set_item = { '': data_set_item }
	  rc_keys = [ '' ]

	cur_axis = self.ax2 if rec[ 'axis' ] == 'right' else self.ax
	if cur_axis:
	  #for rc, values in sorted( data_set_item.iteritems() ):
	  for rc in rc_keys:
	    values = data_set_item[ rc ]
	    if not isinstance( values, np.ndarray ):
	      values = np.array( values )

	    cur_label = \
	        legend_label + '@' + DataUtils.ToAddrString( *rc ) \
	        if rc else legend_label

#	    plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	    if marker_size is not None:
	      if not plot_type:  plot_type = '-'
	      plot_mode = PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	      cur_axis.plot(
#	          self.refAxisValues, cur_values * scale, plot_mode,
	          model_times, values * scale, plot_mode,
	          label = cur_label, linewidth = 2,
		  markersize = marker_size
	          )
	    else:
	      plot_mode = PLOT_MODES[ count % len( PLOT_MODES ) ]
	      cur_axis.plot(
#	          self.refAxisValues, cur_values * scale, plot_mode,
	          model_times, values * scale, plot_mode,
	          label = cur_label, linewidth = 2
	          )

	    count += 1
	  #end for rc, values
	#end if cur_axis
      #end for k

#			-- Create legend and title
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

#     #xxx placement orig=0.925, tried=0.975
      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )

#				-- Time value line
#				--
      self._DoUpdateRedraw()
#      self.axline = \
#          self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
#      if self.refAxisTimes is not None:
#	ndx = DataUtils.FindListIndex( self.refAxisTimes, self.timeValue )
#	self.axline.set_xdata( self.refAxisValues[ ndx ] )
#      else:
#        self.axline.set_xdata( self.timeValue )
    #end if core is not None and len( self.dataSetValues ) > 0

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'exit' )
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._DoUpdateRedraw()			-
  #----------------------------------------------------------------------
  def _DoUpdateRedraw( self, hilite = True ):
    """
"""
    if len( self.dataSetValues ) > 0:
#				-- Time value line
#				--
      if self.axline is None:
        self.axline = \
            self.ax.axvline( color = 'r', linestyle = '-', linewidth = 1 )
      if self.refAxisTimes is not None:
	ndx = DataUtils.FindListIndex( self.refAxisTimes, self.timeValue )
	self.axline.set_xdata( self.refAxisValues[ ndx ] )
      else:
        self.axline.set_xdata( self.timeValue )
  #end _DoUpdateRedraw


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, ref_ds_value ):
    """Find matching dataset values for the reference axis value.
@param  ref_ds_value	value in the reference dataset
@return			dict by real dataset name (not pseudo name) of
			dataset values or None if no matches
"""
    results = {}
    ndx = DataUtils.FindListIndex( self.refAxisValues, ref_ds_value, 'a' )
    if ndx >= 0:
      results[ '_refaxis_' ] = self.refAxisValues[ ndx ]
      for k in self.dataSetValues:
        qds_name = self._GetDataSetName( k )

        data_pair = self.dataSetValues[ k ]
        time_values = data_pair[ 'times' ]
        data_set_item = data_pair[ 'data' ]

        #data_set_item = self.dataSetValues[ k ]
        if not isinstance( data_set_item, dict ):
          data_set_item = { '': data_set_item }

        if len( data_set_item ) > 0:
          sample = data_set_item.itervalues().next()
          if len( sample ) > ndx:
	    cur_dict = {}
            for rc, values in data_set_item.iteritems():
	      cur_dict[ rc ] = values[ ndx ]
	    results[ qds_name ] = cur_dict
          #end if ndx in range
        #end if len( data_set_item ) > 0
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
    #return  ( 'axial:detector', 'axial:pin' )
    return  ( 'axial:detector', 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		AxialValue instance
( value, 0-based core index, 0-based detector index
			  0-based fixed_detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetVisibleDataSets()			-
  #----------------------------------------------------------------------
  def GetVisibleDataSets( self ):
    """Returns a set of DataSetName instances for visible datasets.
    Returns:
        set(DataSetName): visible DataSetNames
"""
    visibles = [
        k for k in self.dataSetSelections
        if self.dataSetSelections[ k ].get( 'visible', False )
        ]
    return  set( visibles )
  #end GetVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.GetCurDataSet()			-
  #----------------------------------------------------------------------
  def GetCurDataSet( self, ds_type = None ):
    """Returns the visible dataset.
@return		current dataset name (DataSetName instance) or None
"""
    qds_name = None
#    if len( self.dataSetValues ) > 0:
    if len( self.dataSetValues ) == 1:
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
      'channel', 'detector', 'fixed_detector', 'fluence', 'intrapin_edits',
      'pin', 'radial_detector', 'scalar', 'subpin_cc',
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


#  #----------------------------------------------------------------------
#  #	METHOD:		TimePlots.GetDataSetPropertyNames()		-
#  #----------------------------------------------------------------------
#  def GetDataSetPropertyNames( self ):
#    """Overrides to append 'refAxisDataSet' to the list
#@return			[ 'curDataSet', 'refAxisDataSet' ]
#"""
#    result = super( TimePlots, self ).GetDataSetPropertyNames()
#    return  result + [ 'refAxisDataSet' ]
#  #end GetDataSetPropertyNames


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
	STATE_CHANGE_fluenceAddr,
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
    self.axline = None
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
        self.dataSetSelections[ qds_name ].get( 'visible', False )
        #self.dataSetSelections[ qds_name ][ 'visible' ]
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_IsTimeReplot()					-
  #----------------------------------------------------------------------
  def _IsTimeReplot( self ):
    """Returns True if the widget replots on a time change, False it it
merely redraws.  Defaults to True.  Should be overridden as necessary.
"""
    return  False
  #end _IsTimeReplot


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """Assume self.dmgr is valid.
@return			dict to be passed to UpdateState()
"""
    update_args = {}

    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'left', 'draworder': 1, 'scale': 1.0, 'visible': True }
    self.dataSetDialog = None

    if self.dmgr.HasData():
      if (reason & STATE_CHANGE_axialValue) > 0:
	update_args[ 'axial_value' ] = self.state.axialValue
	    #self.dmgr.NormalizeAxialValue( None, self.state.axialValue )

      if (reason & STATE_CHANGE_coordinates) > 0:
	update_args[ 'assembly_addr' ] = self.dmgr.\
	    NormalizeAssemblyAddr( self.state.assemblyAddr )
	update_args[ 'aux_node_addrs' ] = self.dmgr.\
	    NormalizeNodeAddrs( self.state.auxNodeAddrs )
	update_args[ 'aux_sub_addrs' ] = self.dmgr.\
	    NormalizeSubAddrs( self.state.auxSubAddrs, mode = 'channel' )
	update_args[ 'node_addr' ] = self.dmgr.\
	    NormalizeNodeAddr( self.state.nodeAddr )
	update_args[ 'sub_addr' ] = self.dmgr.\
            NormalizeSubAddr( self.state.subAddr, mode = 'channel' )

      if (reason & STATE_CHANGE_curDataSet) > 0:
	update_args[ 'cur_dataset' ] = self.state.curDataSet

      if (reason & STATE_CHANGE_timeDataSet) > 0:
	update_args[ 'time_dataset' ] = self.state.timeDataSet

      if (reason & STATE_CHANGE_timeValue) > 0:
	update_args[ 'time_value' ] = self.state.timeValue

      self.dmgr.AddListener( 'dataSetAdded', self._UpdateRefAxisMenu )
      wx.CallAfter( self._UpdateRefAxisMenu )
    #end if self.dmgr.HasData()

    for k in self.dataSetValues:
      qds_name = self._GetDataSetName( k )
      if self.dmgr.GetDataModel( qds_name ) is None:
        update_args[ 'replot' ] = True
	if qds_name in self.dataSetSelections:
	  del self.dataSetSelections[ qds_name ]
      #end if qds_name no longer exists
    #end for k

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
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'dataSetOrder', 'nodeAddr', 'subAddr'
#	'scaleMode'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

# Handled in Widget
#    for k in ( 'axialValue', ):
#      if k in props_dict and hasattr( self, k ):
#        setattr( self, k, AxialValue( props_dict[ k ] ) )

    super( TimePlots, self ).LoadProps( props_dict )

# In PlotWidget
#    wx.CallAfter( self.UpdateState, replot = True )
    wx.CallAfter( self._UpdateRefAxisMenu )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots._ListVisibleDataSets()		-
  #----------------------------------------------------------------------
  def _ListVisibleDataSets( self ):
    """Lists visible datasets by left (primary) and right axes.
@return			( left_list, right_list )
"""
    left_list = []
    right_list = []

    selection_list = \
        [ ( k, rec ) for k, rec in six.iteritems( self.dataSetSelections ) ]
    selection_list.sort( self.SortSelectionRecs )

    #for k, rec in self.dataSetSelections.iteritems():
    for k, rec in selection_list:
      if rec[ 'visible' ]:
        if rec[ 'axis' ] == 'right':
	  right_list.append( k )
        else:
	  left_list.append( k )
    #end for

#		-- Must have at least one left/primary
#		--
    if len( left_list ) == 0 and len( right_list ) > 0:
      first_right = right_list.pop( 0 )
      left_list.append( first_right )
      rec = self.dataSetSelections[ first_right ]
      rec[ 'axis' ] = 'left'

    left_list = \
        [ self._GetDataSetName( i ) for i in left_list if i is not None ]
    #left_list = [ i for i in left_list if i is not None ]
    right_list = \
        [ self._GetDataSetName( i ) for i in right_list if i is not None ]
    #right_list = [ i for i in right_list if i is not None ]

    return  left_list, right_list
  #end _ListVisibleDataSets


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
	    ds_rec[ 'draworder' ] = sel_rec[ 'draworder' ]
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

    #if ev.guiEvent.GetClickCount() > 0 and self.refAxisDataSet is None:
# Can't work b/c refAxisValues not in sorted order
#    button = ev.button or 1
#    if button == 1 and self.cursor is not None:
#      xvalues = \
#          self.refAxisTimes  if self.refAxisTimes is not None  else \
#          self.refAxisValues
#      ndx = DataUtils.FindListIndex( xvalues, self.cursor[ 0 ], 'a' )
#      if ndx >= 0:
#        self.UpdateState( time_value = self.refAxisValues[ ndx ] )
#	self.FireStateChange( time_value = self.refAxisValues[ ndx ] )

    if self.refAxisDataSet is None:
      button = ev.button or 1
      if button == 1 and self.cursor is not None:
        ndx = DataUtils.\
	    FindListIndex( self.refAxisValues, self.cursor[ 0 ], 'a' )
        if ndx >= 0:
	  self.UpdateState( time_value = self.refAxisValues[ ndx ] )
	  self.FireStateChange( time_value = self.refAxisValues[ ndx ] )
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
  #	METHOD:		TimePlots.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( TimePlots, self ).SaveProps( props_dict, for_drag = for_drag )

    # dataSetSelections now handled in PlotWidget
    for k in (
#t	'axialValue',
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'dataSetOrder', 'nodeAddr', 'subAddr'
#	'scaleMode'
	):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.SetVisibleDataSets()			-
  #----------------------------------------------------------------------
  def SetVisibleDataSets( self, qds_names ):
    """Applys the set of visible DataSetName instances.
    Args:
        qds_names (set(DataSetName)): set of all visible DataSetNames
"""
#               -- Now invisible
#               --
    for k, rec in six.iteritems( self.dataSetSelections ):
      if rec.get( 'visible', False ) and k not in qds_names:
        rec[ 'visible' ] = False

    max_order = max(
        map(
            lambda x: x.get( 'draworder', 1 ),
	    six.itervalues( self.dataSetSelections )
	    )
        )

#               -- Now visible
#               --
    for k in qds_names:
      #qds_name = self._GetDataSetName( k )
      if k in self.dataSetSelections:
        self.dataSetSelections[ k ][ 'visible' ] = True
      else:
        self.dataSetSelections[ k ] = \
          {
	  'axis': 'left',
	  'draworder': max_order + 1,
	  'scale': 1.0,
	  'visible': True
	  }
        max_order += 1
    #end for qds_name in qds_names
  #end SetVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		TimePlots.SortSelectionRecs()                   -
  #----------------------------------------------------------------------
  def SortSelectionRecs( self, a, b ):
    """
"""
    aorder = a[ 1 ].get( 'draworder', 1 )
    border = b[ 1 ].get( 'draworder', 1 )
    value = -1 if aorder < border else  1 if aorder > border else  0

    if value == 0:
      aname = self._GetDataSetName( a[ 0 ] )
      bname = self._GetDataSetName( b[ 0 ] )
      value = -1 if aname < bname else  1 if aname > bname else  0

    return  value
  #end SortSelectionRecs


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
#      if rec[ 'visible' ]:
#        rec[ 'axis' ] = ''
      rec[ 'visible' ] = not rec[ 'visible' ]

    else:
      max_order = max(
          map(
	      lambda x: x.get( 'draworder', 1 ),
	      six.itervalues( self.dataSetSelections )
	      )
          )
      self.dataSetSelections[ qds_name ] = \
        {
	'axis': 'left',
	'draworder': max_order + 1,
	'scale': 1.0,
	'visible': True
	}

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
    del self.dataSetOrder[ : ]
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

#		-- Must have data
#		--
    #if self.dmgr.HasData() and self.curDataSet:
    if self.dmgr.HasData():
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
	    'axial_cm': self.axialValue.cm,
	    'fluence_addr': self.fluenceAddr,
	    'qds_name': ref_axis_qds_name,
	    'sub_addrs': [ self.subAddr ]
	    })
      else:
	time_values = np.array( self.dmgr.GetTimeValues() )
        #specs.append( { 'qds_name': self.state.timeDataSet} )

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	qds_name = self._GetDataSetName( k )

        #pdb.set_trace()

        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'qds_name=%s, ds_rec=%s', qds_name, str( ds_rec ) )

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
	      spec[ 'axial_cm' ] = self.axialValue.cm
	      specs.append( spec )
              self.dataSetTypes.add( ds_type )

#						-- Fluence
	    elif ds_type == 'fluence':
	      spec[ 'axial_cm' ] = self.axialValue.cm
	      spec[ 'fluence_addr' ] = self.fluenceAddr
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
	      spec[ 'axial_cm' ] = self.axialValue.cm
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

      order_list = [
          ( k, self.dataSetSelections[ k ] )
	  for k in six.iterkeys( self.dataSetValues )
	  if k in self.dataSetSelections
	  ]
      order_list.sort( PlotDataSetPropsBean.CompareRecs )
      self.dataSetOrder = map( lambda x: x[ 0 ], order_list )
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
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      replot = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
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

    if 'fluence_addr' in kwargs and \
        kwargs[ 'fluence_addr' ] != self.fluenceAddr:
      replot = True
      self.fluenceAddr = self.state.fluenceAddr.copy()
    #end if 'fluence_addr'

    if 'time_dataset' in kwargs:
      replot = True

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end TimePlots
