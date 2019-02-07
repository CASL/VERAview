#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		axial_plot.py					-
#	HISTORY:							-
#		2019-01-16	leerw@ornl.gov				-
#         Transition from tally to fluence.
#		2018-11-20	leerw@ornl.gov				-
#         Applying new DataModelMgrTree and visible datasets button.
#		2018-10-31	leerw@ornl.gov				-
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
#		2018-07-26	leerw@ornl.gov				-
#	  Renaming non-derived dataset category/type from 'axial' to
#	  'axials' to disambiguate from ':axial' displayed name.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-03-25	leerw@ornl.gov				-
#	  Removing implicit dataset axis management.
#		2017-02-03	leerw@ornl.gov				-
#	  Set left boundary to 0.15 to make room for Y-axis label.
#		2017-01-26	leerw@ornl.gov				-
#	  Using PLOT_MODES instead of setting plot type based on
#	  derived vs not-derived dataset.
#	  Removed assembly index from titles.
#		2016-12-10	leerw@ornl.gov				-
#	  Adapting to new DataModelMgr.
#		2016-11-26	leerw@ornl.gov				-
#	  Changing plot_type based on dataset being derived or not.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Using customDataRange.
#		2016-10-21	leerw@ornl.gov				-
#	  Added handling of node_addr and aux_node_addrs in 
#	  _UpdateStateValues().
#		2016-10-18	leerw@ornl.gov				-
#	  Added auxNodeAddrs and nodeAddr attributes.
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-10-01	leerw@ornl.gov				-
#	  Supporting :node datasets.
#		2016-09-03	leerw@ornl.gov				-
#	  Fixed references to detectorMeshCenters.  Doh!!
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
import hashlib, logging, math, os, six, sys, time, traceback
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
  #from matplotlib.backends.backend_wx import NavigationToolbar2Wx
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

from event.state import *

from .bean.plot_dataset_props import *
from .plot_widget import *
from .widget import *
from .widgetcontainer import *


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

		#-- keyed by DataSetName, dicts with keys 'mesh', 'data'
    self.dataSetValues = {}

    self.fluenceAddr = FluenceAddress()
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    super( AxialPlot, self ).__init__( container, id, ref_axis = 'y' )
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
      title_suffix = '; {0}={1:.4g}'.\
          format( self.state.timeDataSet, self.state.timeValue )

#      cur_time_ndx = -1
#      if mode != 'displayed':
#        cur_time_ndx = DataUtils.\
#	      FindListIndex( self.refAxisValues, self.axialValue.cm, 'a' )

      ds_types = {}
      for k in self.dataSetValues:
	qds_name = self._GetDataSetName( k )
	ds_type = self.dmgr.GetDataSetType( qds_name )
	ds_label = self.dmgr.GetDataSetDisplayName( qds_name, True )
	ds_types[ ds_label ] = ds_type

      lines = self.ax.lines
      if self.ax2:
        lines += self.ax2.lines

      groups = {}
      for line in lines:
	label = line.get_label()
	if not label.startswith( '_' ):
	  ds_type = None
	  xdata = line.get_xdata()
	  ydata = line.get_ydata()
	  if hasattr( xdata, '__iter__' ) and hasattr( ydata, '__iter__' ):
	    ds_type = None
	    for k in ds_types:
	      if label.startswith( k ):
	        ds_type = ds_types[ k ]
		break
	  #end if hasattr...

	  if ds_type:
	    ndx = -1
	    if mode != 'displayed':
	      ndx = DataUtils.FindListIndex( ydata, self.axialValue.cm, 'a' )
              if ndx >= 0:
	        xdata = xdata[ ndx : ndx + 1 ]
		ydata = ydata[ ndx : ndx + 1 ]

	    group_key = hashlib.sha1( ydata ).hexdigest()
	    group = groups.get( group_key )
	    if group is None:
	      dsets = []
	      group = dict( ydata = ydata, dsets = dsets, ds_type = ds_type )
	      groups[ group_key ] = group
	    else:
	      dsets = group.get( 'dsets' )
	    dsets.append( ( '"' + label + '"', xdata ) )
	  #end if ds_type
	#end if not label.startswith( '_' )
      #end for line in lines

      csv_text = ''
      for group in six.itervalues( groups ):
	ydata = group.get( 'ydata' )
	dsets = group.get( 'dsets' )
	ds_type = group.get( 'ds_type' )
	ds_names = ','.join( [ i[ 0 ] for i in dsets ] )

	if ds_type.startswith( 'channel' ):
	  block = '"Channel=({0:d},{1:d}){2}"\naxial,{3}\n'.format(
	      self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1,
	      title_suffix, ds_names
	      )
	elif ds_type.startswith( 'detector' ) or \
	    ds_type.startswith( 'fixed_detector' ):
	  block = '"Detector={0}{1}\n"axial,{2}\n'.format(
	      core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	      title_suffix, ds_names
	      )
	elif ds_type.startswith( 'fluence' ):
	  th = int(
              core.fluenceMesh.\
              GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' )
              )
	  block = '"Fluence (r={0:.1f},th={2:d}{3}"\naxial,{4}\n'.\
          format(
              core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ),
              th, title_suffix, ds_names
	      )
	else: # elif ds_type.startswith( 'pin' ):
	  block = '"Pin=({0:d},{1:d}){2}"\naxial,{3}\n'.format(
	      self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1,
	      title_suffix, ds_names
	      )

	for i in range( len( xdata ) ):
	  row = '{0:.7g},{1}\n'.format(
	      ydata[ i ],
	      ','.join( [ '{0:.7g}'.format( ds[ 1 ][ i ] ) for ds in dsets ] )
	      )
          block += row
	#end for i in range( len( xdata ) )

        csv_text += block + '\n'
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
    cur_selection_flag = mode != 'displayed'

#		-- Must be valid state
#		--
    core = self.dmgr.GetCore()
    if core:
      title = '%s=%.4g' % (
	  self.state.timeDataSet,
	  self.state.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )

      title_set = set( [] )
      axial_mesh_datasets = {}
      detector_mesh_datasets = {}
      fixed_detector_mesh_datasets = {}
      fluence_mesh_datasets = {}

#		 	-- Collate by model and mesh type
#		 	--
      model_mesh_datasets = {}
      for k in self.dataSetValues:
	qds_name = self._GetDataSetName( k )
	ds_rec = self.dataSetSelections[ k ]
        if ds_rec[ 'visible' ] and qds_name is not None:
	  if qds_name.modelName in model_mesh_datasets:
	    model_dict = model_mesh_datasets[ qds_name.modelName ]
	  else:
	    model_dict = { 'Axial': {}, 'Detector': {}, 'Fixed Detector': {}, 'Fluence': {} }
	    model_mesh_datasets[ qds_name.modelName ] = model_dict

	  ds_type = self.dmgr.GetDataSetType( qds_name )
          data_set_pair = self.dataSetValues[ k ]

	  if ds_type.startswith( 'channel' ):
	    if 'channel' not in title_set:
	      title_set.add( 'channel' )
	      title += '; Channel=(%d,%d)' % ( 
	          self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1
		  )
	    #axial_mesh_datasets[ qds_name ] = data_set_item
	    model_dict[ 'Axial' ][ qds_name ] = data_set_pair

	  elif ds_type.startswith( 'detector' ):
	    if 'detector' not in title_set:
	      title_set.add( 'detector' )
	      #title += '; Detector=%d' % ( self.assemblyAddr[ 0 ] + 1 )
	      title += '; Detector=%s' % \
	          core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    model_dict[ 'Detector' ][ qds_name ] = data_set_pair

	  elif ds_type.startswith( 'fixed_detector' ):
	    if 'detector' not in title_set:
	      title_set.add( 'detector' )
	      #title += '; Detector=%d' % ( self.assemblyAddr[ 0 ] + 1 )
	      title += '; Detector=%s' % \
	          core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    model_dict[ 'Fixed Detector' ][ qds_name ] = data_set_pair

	  elif ds_type.startswith( 'fluence' ):
	    if 'fluence' not in title_set:
	      title_set.add( 'fluence' )
              th = \
int( core.fluenceMesh.GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' ) )
	      title += '; Fluence r=%.1f,th=%d' % \
( core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ), th )
	    model_dict[ 'Fluence' ][ qds_name ] = data_set_pair

	  else:
	    if 'pin' not in title_set:
	      title_set.add( 'pin' )
	      title += '; Pin=(%d,%d)' % ( 
	          self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1
		  )
	    #axial_mesh_datasets[ qds_name ] = data_set_item
	    model_dict[ 'Axial' ][ qds_name ] = data_set_pair
          #end if-else type
	#end if visible
      #end for k

#		 	-- Create CSV
#		 	--
      csv_text = '"%s"\n' % title
      for model_name in sorted( model_mesh_datasets.keys() ):
        model_dict = model_mesh_datasets[ model_name ]
	for axial_type in ( 'Axial', 'Detector', 'Fixed Detector', 'Fluence' ):
	  if len( model_dict[ axial_type ] ) > 0:
	    csv_text += self._CreateCsvDataRows(
		model_name, model_dict[ axial_type ],
		axial_type, cur_selection_flag
	        )
	#endfor axial_type
      #end for model_name
    #end if core

    return  csv_text
  #end _CreateClipboardData_1


  #----------------------------------------------------------------------
  #	METHOD:		_CreateCsvDataRows()				-
  #----------------------------------------------------------------------
  def _CreateCsvDataRows(
      self, model_name, data_dict, axial_mesh_type, cur_selection_flag
      ):
    """Creates CSV rows for the specified mesh type and associated
dataset names and ( rc, values ) pairs.
@param  model_name	name of DataModel instance
@param  data_dict	dict by qds_name of
			{ 'mesh': xxx, 'data': [ ( rc, values ) ] }
@param  axial_mesh_type	'Axial', 'Detector', 'Fixed Detector', or 'Fluence'
@param  cur_selection_flag  True to only show data for the current selection
@return			CSV text
"""
    csv_text = model_name + '\n'

    core = self.dmgr.GetCore()
    if core:
      header = axial_mesh_type
      if axial_mesh_type == 'Detector':
        header += ' Mesh'
      else:
        header += ' Mesh Centers'

      mesh_values = None
      for qds_name, data_pair in sorted( six.iteritems( data_dict ) ):
	if mesh_values is None:
	  mesh_values = data_pair[ 'mesh' ]
	item = data_pair[ 'data' ]
	if isinstance( item, dict ):
          for rc in sorted( item.keys() ):
            header += ',"' + qds_name.displayName
	    if rc:
              header += '@' + DataUtils.ToAddrString( *rc )
            header += '"'
	else:
	  header += ',"' + qds_name.displayName
	#end if-else dict
      #end for qds_name, data_pair

      csv_text += header + '\n'

#			-- Write data rows
#			--
      cur_axial_index = \
          DataUtils.FindListIndex( mesh_values, self.axialValue.cm, 'a' )
      if cur_selection_flag:
        j_range = ( cur_axial_index, )
      else:
        j_range = range( len( mesh_values ) - 1, -1, -1 )

      for j in j_range:
        row = '%.7g' % mesh_values[ j ]

        for qds_name, data_pair in sorted( six.iteritems( data_dict ) ):
	  item = data_pair[ 'data' ]
	  if not isinstance( item, dict ):
	    item = { '': item }
          for rc, values in sorted( six.iteritems( item ) ):
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
    #end if core

    return  csv_text
  #end _CreateCsvDataRows


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( AxialPlot, self )._CreateMenuDef()

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
#	'label': 'Select Bottom Axis Scale Mode',
#	'submenu': select_scale_def
#	},
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
    ds_values = self._FindDataSetValues( ev.ydata )

    if ds_values is not None:
      mesh_values_dict = {}

      for k in sorted( ds_values.keys() ):
        data_set_item = ds_values[ k ]
        mesh_value = data_set_item[ '_mesh_' ]
        del data_set_item[ '_mesh_' ]

        if mesh_value in mesh_values_dict:
          mesh_list = mesh_values_dict[ mesh_value ]
        else:
          mesh_list = []
          mesh_values_dict[ mesh_value ] = mesh_list
	for rc, value in sorted( six.iteritems( data_set_item ) ):
	  cur_label = \
	      k.name + '@' + DataUtils.ToAddrString( *rc ) \
	      if rc else k.name
          mesh_list.append( '{0}={1:.3g}'.format( cur_label, value ) )
      #end for k

      for mesh_value in sorted( mesh_values_dict.keys() ):
        if len( tip_str ) > 0:
          tip_str += '\n'
        tip_str += 'Axial={0:.3f}\n'.format( mesh_value )
        tip_str += '\n'.join( mesh_values_dict.get( mesh_value ) )
      #end for mesh_value in sorted( mesh_values_dict.keys() )
    #end if ds_values is not None:

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		_CreateToolTipText_orig()                       -
  #----------------------------------------------------------------------
  def _CreateToolTipText_orig( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		mouse motion event
"""
    tip_str = ''
    ds_values = self._FindDataSetValues( ev.ydata )
    if ds_values is not None:
      #tip_str = 'Axial=%.3g' % ev.ydata
      for k in sorted( ds_values.keys() ):
        data_set_item = ds_values[ k ]
	#if not isinstance( data_set_item, dict ):
	  #data_set_item = { '': data_set_item }
        if len( tip_str ) > 0:
          tip_str += '\n'
        tip_str += 'Axial=%.3f' % data_set_item[ '_mesh_' ]
        del data_set_item[ '_mesh_' ]
	for rc, value in sorted( six.iteritems( data_set_item ) ):
	  cur_label = \
	      k.name + '@' + DataUtils.ToAddrString( *rc ) \
	      if rc else k.name
	  tip_str += ' %s=%.3g' % ( cur_label, value )
	#end for rc, value
      #end for k
    #end if ds_values is not None:

    return  tip_str
  #end _CreateToolTipText_orig


  #----------------------------------------------------------------------
  #	METHOD:		_DoUpdatePlot()					-
  #----------------------------------------------------------------------
  def _DoUpdatePlot( self, wd, ht ):
    """Do the work of creating the plot, setting titles and labels,
configuring the grid, plotting, and creating self.axline.
"""
    super( AxialPlot, self )._DoUpdatePlot( wd, ht )

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

#		-- Something to plot?
#		--
    core = self.dmgr.GetCore()
    if core is not None and len( self.dataSetValues ) > 0:
#			-- Determine axis datasets
#			--
      bottom_list, top_list = self._ListVisibleDataSets()

#			-- Configure axes
#			--
#				-- Top
      if len( top_list ) > 0 and self.ax2 is not None:
	label = self.dmgr.GetDataSetDisplayName( top_list[ 0 ] )
	if len( top_list ) > 1:
	  label += ',...'
        self.ax2.set_xlabel( label, fontsize = label_font_size )
	ds_range = self.dmgr.GetRangeAll(
	    self.timeValue if self.state.scaleMode == 'state' else -1.0,
	    self.state.weightsMode == 'on',
	    *top_list
	    )
	#scale_type = self.dmgr.GetDataSetScaleTypeAll( 'all', *top_list )
	scale_type = \
	    self.dmgr.GetDataSetScaleTypeAll( 'all', *top_list ) \
	    if self.scaleType == DEFAULT_scaleType else \
	    self.scaleType
	if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] ):
	  if scale_type == 'log':
	    self.ax2.set_xscale( 'log', nonposx = 'clip' )
            self.logger.debug(
	        'calling set_xlim: log, %s', str( ds_range[ 0 : 2 ] )
	        )
	    self.ax2.set_xlim(
		max( 1.0e-30, ds_range[ 0 ] ),
		max( 1.0e-30, ds_range[ 1 ] )
	        )
	  else:
	    self.ax2.set_xscale( 'linear' )
            self.logger.debug(
	        'calling set_xlim: linear, %s', str( ds_range[ 0 : 2 ] )
	        )
            self.ax2.set_xlim( *ds_range[ 0 : 2 ] )
	    self.ax2.xaxis.get_major_formatter().set_powerlimits( ( -2, 3 ) )

#				-- Bottom, primary
      self.ax.set_ylabel( 'Axial (cm)', fontsize = label_font_size )
      label = self.dmgr.GetDataSetDisplayName( bottom_list[ 0 ] )
      if len( bottom_list ) > 1:
        label += ',...'
      self.ax.set_xlabel( label, fontsize = label_font_size )

      ds_range = list( self.customDataRange ) \
          if self.customDataRange is not None else \
	  [ NAN, NAN ]
      if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] ):
        calc_range = self.dmgr.GetRangeAll(
	    self.timeValue if self.state.scaleMode == 'state' else -1.0,
	    self.state.weightsMode == 'on',
	    *bottom_list
	    )
#					-- Scale over all plotted datasets?
#        if self.scaleMode == 'all':
#          for k in self.dataSetValues:
#	    cur_qname = self._GetDataSetName( k )
#	    if cur_qname != top_qds_name and cur_qname != bottom_qds_name:
#	      cur_range = self.dmgr.GetRange(
#	          cur_qname,
#	          self.timeValue if self.state.scaleMode == 'state' else -1.0
#	          )
#	      calc_range = (
#	          min( calc_range[ 0 ], cur_range[ 0 ] ),
#		  max( calc_range[ 1 ], cur_range[ 1 ] )
#	          )
#          #end for k

	if calc_range is None:
	  calc_range = ( 0.0, 10.0 )
        for i in xrange( min( len( ds_range ), len( calc_range ) ) ):
	  if math.isnan( ds_range[ i ] ):
	    ds_range[ i ] = calc_range[ i ]
      #end if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] )

      if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] ):
	scale_type = \
	    self.dmgr.GetDataSetScaleTypeAll( 'all', *bottom_list ) \
	    if self.scaleType == DEFAULT_scaleType else \
	    self.scaleType
	if scale_type == 'log':
	  self.ax.set_xscale( 'log', nonposx = 'clip' )
          self.logger.debug(
	      'calling set_xlim: log, %s', str( ds_range[ 0 : 2 ] )
	      )
	  self.ax.set_xlim(
	      max( 1.0e-30, ds_range[ 0 ] ),
	      max( 1.0e-30, ds_range[ 1 ] )
	      )
	else:
	  self.ax.set_xscale( 'linear' )
          self.logger.debug(
	      'calling set_xlim: linear, %s', str( ds_range[ 0 : 2 ] )
	      )
          self.ax.set_xlim( *ds_range[ 0 : 2 ] )
          self.ax.xaxis.get_major_formatter().set_powerlimits( ( -2, 3 ) )

#			-- Set title
#			--
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )

      title_str = 'Assy %s, %s %.4g' % (
          show_assy_addr,
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
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
	title_line2 += 'Det %s' % (
	    #self.assemblyAddr[ 0 ] + 1,
	    core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    )

      if 'fixed_detector' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
	title_line2 += 'Van %s' % (
	    #self.assemblyAddr[ 0 ] + 1,
	    core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
	    )

      if 'fluence' in self.dataSetTypes:
        if len( title_line2 ) > 0: title_line2 += ', '
        th = \
int( core.fluenceMesh.GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' ) )
	title_line2 += 'Fluence r=%.1f,th=%d' % \
            ( core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ), th )

      if len( title_line2 ) > 0:
        title_str += '\n' + title_line2

#			-- Plot each selected dataset
#			--
      count = 0
      #for k in self.dataSetValues:
      for k in self.dataSetOrder:
	data_pair = self.dataSetValues[ k ]
	qds_name = self._GetDataSetName( k )
	rec = self.dataSetSelections[ k ]
	#scale = rec[ 'scale' ] if rec[ 'axis' ] == '' else 1.0
	scale = rec.get( 'scale', 1.0 )
	legend_label = self.dmgr.GetDataSetDisplayName( qds_name, True )
	if scale != 1.0:
	  legend_label += '*%.3g' % scale

	ds_type = self.dmgr.GetDataSetType( qds_name )
	axial_values = data_pair[ 'mesh' ]
	marker_size = None
	plot_type = None
	if ds_type.startswith( 'detector' ):
	  marker_size = 12
	  plot_type = '-'
	elif ds_type.startswith( 'fixed_detector' ):
	  marker_size = 12
	  plot_type = 'x'
#	else:
#	  plot_type = ':'

	cur_axis = self.ax2 if rec[ 'axis' ] == 'top' else self.ax
	if cur_axis and axial_values is not None:
	  data_set_item = data_pair[ 'data' ]
#	  if not isinstance( data_set_item, dict ):
#	    data_set_item = { '': data_set_item }
	  if isinstance( data_set_item, dict ):
	    rc_keys = \
	        sorted( six.iterkeys( data_set_item ), Widget.CompareAuxAddrs )
	  else:
	    data_set_item = { '': data_set_item }
	    rc_keys = [ '' ]

	  #for rc, values in sorted( six.iteritems( data_set_item ) ):
	  for rc in rc_keys:
	    values = data_set_item[ rc ]
	    if not isinstance( values, np.ndarray ):
	      values = np.array( values )

            if len( values ) == len( axial_values ):
	      cur_label = \
	          legend_label + '@' + DataUtils.ToAddrString( *rc ) \
	          if rc else legend_label

	      if marker_size is not None:
	        if not plot_type:  plot_type = '-'
	        plot_mode = \
                    PLOT_COLORS[ count % len( PLOT_COLORS ) ] + plot_type
	        cur_axis.plot(
	            values * scale, axial_values, plot_mode,
	            label = cur_label, linewidth = 2,
		    markersize = marker_size
	            )
	      else:
	        plot_mode = PLOT_MODES[ count % len( PLOT_MODES ) ]
	        cur_axis.plot(
	            values * scale, axial_values, plot_mode,
	            label = cur_label, linewidth = 2
	            )
	      count += 1
            #end if len( values ) == len( axial_values )
	  #end for rc, values
	#end if axial_values
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

      #xxxplacement orig=0.925, tried=0.975
      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )

#			-- Axial value line
#			--
#x      self.axline = \
#x          self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
#x      self.axline.set_ydata( self.axialValue.cm )
    #end if core and len( self.dataSetValues ) > 0, we have something to plot

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'exit' )
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot._DoUpdateRedraw()			-
  #----------------------------------------------------------------------
  def _DoUpdateRedraw( self, hilite = True ):
    """
"""
#			-- Axial value line
#			--
    if len( self.dataSetValues ) > 0:
      if self.axline is None:
        self.axline = \
	    self.ax.axhline( color = 'r', linestyle = '-', linewidth = 1 )
      self.axline.set_ydata( self.axialValue.cm )
  #end _DoUpdateRedraw


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, axial_cm ):
    """Find matching dataset values for the axial.
@param  axial_cm	axial value
@return			dict by real qdataset name (not pseudo name) of
			dataset values or None if no matches
"""
    results = {}
    for k in self.dataSetValues:
      qds_name = self._GetDataSetName( k )

      data_pair = self.dataSetValues[ k ]
      mesh_values = data_pair[ 'mesh' ]
      data_set_item = data_pair[ 'data' ]
      if not isinstance( data_set_item, dict ):
        data_set_item = { '': data_set_item }

      ndx = DataUtils.FindListIndex( mesh_values, axial_cm, 'a' )
      sample = data_set_item.itervalues().next()
      #if ndx >= 0 and len( sample ) > ndx:
      if hasattr( sample, '__iter__' ) and ndx >= 0 and len( sample ) > ndx:
	#cur_dict = {}
	cur_dict = { '_mesh_': mesh_values[ ndx ] }
        for rc, values in six.iteritems( data_set_item ):
	  cur_dict[ rc ] = values[ ndx ]

	results[ qds_name ] = cur_dict
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
    """@return		AxialValue instance
( cm value, 0-based core index, 0-based detector index
			  0-based fixed_detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.GetCurDataSet()			-
  #----------------------------------------------------------------------
  def GetCurDataSet( self, ds_type = None ):
    """Returns the first visible dataset.
@return		dataset name (DataSetName instance) or None
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
  def _GetDataSetName( self, qds_name ):
    """Determines actual dataset name if a pseudo name is provided.
@param  name		DataSetName instance
@return			name to use, None if qds_name is None
"""
    return \
        None  if qds_name is None else \
	self.curDataSet  if qds_name == NAME_selectedDataSet else \
	qds_name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      (
      'channel', 'detector', 'fixed_detector', 'intrapin_edits', 'pin',
      'subpin_cc', 'fluence',
      ':assembly', ':axial', ':node'
      )
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
	STATE_CHANGE_fluenceAddr,
	STATE_CHANGE_timeValue
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
  #	METHOD:		AxialPlot.GetVisibleDataSets()			-
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
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes, 'ax', and 'ax2'.
XXX size according to how many datasets selected?
"""
    self.axline = None
    ##self.ax = self.fig.add_axes([ 0.1, 0.12, 0.85, 0.68 ])
    ##self.ax = self.fig.add_axes([ 0.1, 0.12, 0.8, 0.68 ])
    #self.ax = self.fig.add_axes([ 0.12, 0.12, 0.82, 0.7 ])
    self.ax = self.fig.add_axes([ 0.15, 0.12, 0.82, 0.7 ])
    self.ax2 = self.ax.twiny() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.IsDataSetVisible()			-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, qds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  qds_name	dataset name, DataSetName instance
@return			True if visible, else False
"""
    visible = \
        qds_name in self.dataSetSelections and \
        self.dataSetSelections[ qds_name ].get( 'visible', False )
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assumes self.dmgr is valid.
@return			dict to be passed to UpdateState()
"""
    update_args = {}

    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'bottom', 'draworder': 1, 'scale': 1.0, 'visible': True }
    self.dataSetDialog = None

    #if self.data is not None and self.data.HasData():
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
  #	METHOD:		AxialPlot.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    # dataSetSelections now handled in PlotWidget
    for k in (
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'dataSetOrder', 'nodeAddr', 'subAddr', 'timeValue'
#	'scaleMode'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

# Handled in Widget
#    for k in ( 'axialValue', ):
#      if k in props_dict and hasattr( self, k ):
#        setattr( self, k, AxialValue( props_dict[ k ] ) )

    super( AxialPlot, self ).LoadProps( props_dict )
# In PlotWidget
#    wx.CallAfter( self.UpdateState, replot = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot._ListVisibleDataSets()		-
  #----------------------------------------------------------------------
  def _ListVisibleDataSets( self ):
    """Lists visible datasets by bottom (primary) and top axes.
@return			( bottom_list, top_list )
"""
    bottom_list = []
    top_list = []

    selection_list = \
        [ ( k, rec ) for k, rec in six.iteritems( self.dataSetSelections ) ]
    selection_list.sort( self.SortSelectionRecs )

    #for k, rec in six.iteritems( self.dataSetSelections ):
    for k, rec in selection_list:
      if rec[ 'visible' ]:
        if rec[ 'axis' ] == 'top':
	  top_list.append( k )
        else:
	  bottom_list.append( k )
    #end for

#		-- Must have at least one bottom/primary
#		--
    if len( bottom_list ) == 0 and len( top_list ) > 0:
      first_top = top_list.pop( 0 )
      bottom_list.append( first_top )
      rec = self.dataSetSelections[ first_top ]
      rec[ 'axis' ] = 'bottom'

    bottom_list = \
        [ self._GetDataSetName( i ) for i in bottom_list if i is not None ]
    #bottom_list = [ i for i in bottom_list if i is not None ]
    top_list = \
        [ self._GetDataSetName( i ) for i in top_list if i is not None ]
    #top_list = [ i for i in top_list if i is not None ]

    return  bottom_list, top_list
  #end _ListVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		_OnEditDataSetProps()				-
  #----------------------------------------------------------------------
  def _OnEditDataSetProps( self, ev ):
    """Must be called from the UI thread.
"""
    if self.dataSetDialog is None:
      self.dataSetDialog = PlotDataSetPropsDialog( self )

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
      #end if selections
    #end if self.dataSetDialog is not None
  #end _OnEditDataSetProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    super( AxialPlot, self )._OnMplMouseRelease( ev )

    #if ev.guiEvent.GetClickCount() > 0:
    button = ev.button or 1
    if button == 1 and self.cursor is not None:
      axial_value = self.dmgr.GetAxialValue( None, cm = self.cursor[ 1 ] )
      self.UpdateState( axial_value = axial_value )
      self.FireStateChange( axial_value = axial_value )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot._OnSetScaleMode()			-
  #----------------------------------------------------------------------
#  def _OnSetScaleMode( self, mode, ev ):
#    """Must be called from the UI thread.
#@param  mode		'all' or 'selected', defaulting to 'selected'
#"""
#    if mode != self.scaleMode:
#      self.scaleMode = mode
#      self.UpdateState( replot = True )
#    #end if mode changed
#  #end _OnSetScaleMode


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    # dataSetSelections now handled in PlotWidget
    super( AxialPlot, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in (
#t	'axialValue',
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'dataSetOrder', 'nodeAddr', 'subAddr', 'timeValue'
#	'scaleMode'
	):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.SetVisibleDataSets()			-
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

    axial_qds_names = self.dmgr.GetDataSetQNames( None, 'axials' )
    max_order = max(
        map(
            lambda x: x.get( 'draworder', 1 ),
	    six.itervalues( self.dataSetSelections )
	    )
        )

#               -- Now visible
#               --
    for k in qds_names:
      qds_name = self._GetDataSetName( k )
      if qds_name in axial_qds_names:
        if k in self.dataSetSelections:
          self.dataSetSelections[ k ][ 'visible' ] = True
        else:
          self.dataSetSelections[ k ] = \
            {
	    'axis': 'bottom',
	    'draworder': max_order + 1,
	    'scale': 1.0,
	    'visible': True
	    }
          max_order += 1
      #end if qds_name in axial_qds_names
    #end for qds_name in qds_names
  #end SetVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		AxialPlot.SortSelectionRecs()                   -
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
  #	METHOD:		AxialPlot.ToggleDataSetVisible()		-
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
	'axis': 'bottom',
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
"""
    del self.dataSetOrder[ : ]
    self.dataSetTypes.clear()
    self.dataSetValues.clear()

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'enter' )

#		-- Must have data
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    if self.dmgr.HasData():
      axial_qds_names = self.dmgr.GetDataSetQNames( None, 'axials' )

      node_addr_list = None
      sub_addr_list = None

      for k in self.dataSetSelections:
        ds_rec = self.dataSetSelections[ k ]
	qds_name = self._GetDataSetName( k )

        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'qds_name=%s, ds_rec=%s', qds_name, str( ds_rec ) )

#				-- Must be visible and an "axial" dataset
#				--
        if ds_rec[ 'visible' ] and qds_name is not None and \
	    qds_name in axial_qds_names:
	  data_pair = None
	  ds_type = self.dmgr.GetDataSetType( qds_name )

	  if qds_name in self.dataSetValues:
	    data_pair = self.dataSetValues[ qds_name ]

#					-- Detector, fixed detector
	  if ds_type == 'detector' or ds_type == 'fixed_detector':
	    data_pair = self.dmgr.ReadDataSetAxialValues(
	        qds_name,
		detector_index = self.assemblyAddr[ 0 ],
		time_value = self.timeValue
		)
            self.dataSetTypes.add( ds_type )

#					-- Fluence
	  elif ds_type == 'fluence':
	    data_pair = self.dmgr.ReadDataSetAxialValues(
	        qds_name,
		fluence_addr = self.fluenceAddr,
		time_value = self.timeValue
		)
            self.dataSetTypes.add( ds_type )

#					-- Not scalar
	  elif ds_type != 'scalar':
#						-- Lazy creation
	    if node_addr_list is None:
	      node_addr_list = list( self.auxNodeAddrs )
	      node_addr_list.insert( 0, self.nodeAddr )
	    if sub_addr_list is None:
              sub_addr_list = list( self.auxSubAddrs )
              sub_addr_list.insert( 0, self.subAddr )

	    data_pair = self.dmgr.ReadDataSetAxialValues(
	        qds_name,
		assembly_index = self.assemblyAddr[ 0 ],
		node_addrs = node_addr_list,
		sub_addrs = sub_addr_list,
		time_value = self.timeValue
		)
            self.dataSetTypes.add( ds_type )
	  #end if ds_type match

	  if data_pair is not None:
	    self.dataSetValues[ k ] = data_pair
        #end if visible
      #end for each dataset

      order_list = [
          ( k, self.dataSetSelections[ k ] )
	  for k in six.iterkeys( self.dataSetValues )
	  if k in self.dataSetSelections
	  ]
#      order_list = []
#      for k in self.dataSetValues:
#	rec = self.dataSetSelections.get( k )
#	if rec:
#	  order_list.append( ( k, rec ) )
      order_list.sort( PlotDataSetPropsBean.CompareRecs )
      self.dataSetOrder = map( lambda x: x[ 0 ], order_list )
    #end if self.dmgr.HasData()

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'exit' )
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

    if 'aux_node_addrs' in kwargs and \
        kwargs[ 'aux_node_addrs' ] != self.auxNodeAddrs:
      replot = True
      self.auxNodeAddrs = \
          DataUtils.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )

    if 'aux_sub_addrs' in kwargs and kwargs[ 'aux_sub_addrs' ] != self.auxSubAddrs:
      replot = True
      self.auxSubAddrs = \
          self.dmgr.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      redraw = True  # replot = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

    if 'cur_dataset' in kwargs and \
        kwargs[ 'cur_dataset' ] != self.curDataSet and \
	kwargs[ 'cur_dataset' ].displayName in \
	  self.dmgr.\
	  GetDataModelDataSetNames( kwargs[ 'cur_dataset' ], 'axials' ):
      self.curDataSet = kwargs[ 'cur_dataset' ]
      #select_name = self.GetSelectedDataSetName( 'channel' )
      select_name = self.GetSelectedDataSetName()  # NAME_selectedDataSet
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

#end AxialPlot
