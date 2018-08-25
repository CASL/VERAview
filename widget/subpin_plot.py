#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		subpin_plot.py					-
#	HISTORY:							-
#		2018-04-26	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, sys, time, traceback
import numpy as np
import pdb  # pdb.set_trace()

try:
  import wx
#  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
  from matplotlib import cm, colors, transforms
#  import matplotlib.pyplot as plt
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

try:
  from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
  #from matplotlib.backends.backend_wx import NavigationToolbar2Wx
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

#from bean.dataset_chooser import *
from bean.plot_dataset_props import *
from event.state import *

from plot_widget import *
from widget import *
from widgetcontainer import *


#------------------------------------------------------------------------
#	CLASS:		SubPinPlot					-
#------------------------------------------------------------------------
class SubPinPlot( PlotWidget ):
  """Subpin axial plot.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__del__()					-
  #----------------------------------------------------------------------
  def __del__( self ):
#    if self.dataSetDialog is not None:
#      self.dataSetDialog.Destroy()

    super( SubPinPlot, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    #self.auxNodeAddrs = []
    self.auxSubAddrs = []
    #self.ax2 = None
    self.axialValue = DataModel.CreateEmptyAxialValueObject()
    self.curDataSet = None
#    self.dataSetDialog = None
#    self.dataSetSelections = {}  # keyed by DataSetName
#    self.dataSetTypes = set()

		#-- keyed by DataSetName, dicts with keys 'mesh', 'data'
		#-- keys: 'thetas', 'radii', 'widths'
    self.dataSetValues = {}

    self.legendAx = None
    self.mode = 'theta'  # 'r', 'theta'
    #self.nodeAddr = -1
#    self.scaleMode = 'selected'
    self.subAddr = ( -1, -1 )
    #self.tallyAddr = DataModel.CreateEmptyTallyAddress()

    super( SubPinPlot, self ).__init__( container, id, ref_axis = 'y' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( SubPinPlot, self )._CreateMenuDef()

    more_def = \
      [
        { 'label': '-' },
#	{
#	'label': 'Edit Dataset Properties...',
#	'handler': self._OnEditDataSetProps
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
    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		_DoUpdatePlot()					-
  #----------------------------------------------------------------------
  def _DoUpdatePlot( self, wd, ht ):
    """Do the work of creating the plot, setting titles and labels,
configuring the grid, plotting, and creating self.axline.
"""
    #super( SubPinPlot, self )._DoUpdatePlot( wd, ht )
    #self.ax.grid( False )

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
    dset_values = None
    core = self.dmgr.GetCore()
    if core is not None and len( self.dataSetValues ) > 0:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
#			-- For both theta and r
#      assy_ndx = self.assemblyAddr[ 0 ]
#      if assy_ndx < dset.shape[ 4 ]:
#        dset_array = np.array( dset )
      assy_ndx = min( self.assemblyAddr[ 0 ], dset.shape[ 4 ] - 1 )
      pin_col = min( self.subAddr[ 0 ], dset.shape[ 2 ] - 1 )
      pin_row = min( self.subAddr[ 1 ], dset.shape[ 1 ] - 1 )
      axial_level = min( self.axialValue.subPinIndex, dset.shape[ 3 ] - 1 )
      dset_values = dset[ :, pin_row, pin_col, axial_level, assy_ndx ]

    if dset_values is not None:
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
      title_str = '%s: Assy %s, Axial %.3f, %s %.4g' % (
          self.dmgr.GetDataSetDisplayName( self.curDataSet ),
          show_assy_addr,
	  self.axialValue.cm,
	  self.state.timeDataSet,
	  self.timeValue
	  )
      rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
      title_line2 = 'Pin %s' % str( rc )
      title_str += '\n' + title_line2

#			-- Configure axes
#			--
      ds_range = list( self.customDataRange ) \
          if self.customDataRange is not None else \
	  [ NAN, NAN ]
      if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] ):
        calc_range = self.dmgr.GetRange(
	    self.curDataSet,
	    self.timeValue if self.state.scaleMode == 'state' else -1.0
	    )

	if calc_range is None:
	  calc_range = ( 0.0, 10.0 )
        for i in xrange( min( len( ds_range ), len( calc_range ) ) ):
	  if math.isnan( ds_range[ i ] ):
	    ds_range[ i ] = calc_range[ i ]
      #end if math.isnan( ds_range[ 0 ] ) or math.isnan( ds_range[ 1 ] )

      if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] ):
        #scale_type = self.dmgr.GetDataSetScaleTypeAll( 'all', *bottom_list )
	scale_type = \
	    self.dmgr.GetDataSetScaleTypeAll( self.curDataSet ) \
	    if self.scaleType == DEFAULT_scaleType else \
	    self.scaleType
        if scale_type == 'log':
	  norm = colors.LogNorm(
	      vmin = max( ds_range[ 0 ], 1.0e-16 ),
	      vmax = max( ds_range[ 1 ], 1.0e-16 ),
	      clip = True
	      )
	else:
	  norm = colors.\
	    Normalize( vmin = ds_range[ 0 ], vmax = ds_range[ 1 ], clip = True )

        mapper = cm.\
	  ScalarMappable( norm = norm, cmap = cm.get_cmap( self.colormapName ) )

        if self.mode == 'theta':
	  radii = self.dataSetValues.get( 'radii' )
	  thetas = self.dataSetValues.get( 'thetas' )
	  self.ax.set_rgrids( [] )
	  self.ax.set_thetagrids(
	      np.linspace( 0.0, 360.0, 12, endpoint = False )
	      #color = ( 0.25, 0.25, 0.25, 0.25 )
	      )
	  self.ax.set_theta_direction( -1 )
	  self.ax.set_theta_zero_location( 'N' )

	  bar_colors = mapper.to_rgba( dset_values )
          bars = self.ax.bar(
	      thetas, radii,
	      width = self.dataSetValues.get( 'widths' ),
	      bottom = 2.0,
	      color = bar_colors,
	      edgecolor = bar_colors
              )
	  mapper.set_array( dset_values )
	  #self.fig.colorbar( mapper, ax = [ self.ax ] )
	  self.fig.colorbar( mapper, cax = self.legendAx )

        else:
          pass
        #end else self.mode != 'theta'
      #end if ds_range and DataUtils.IsValidRange( *ds_range[ 0 : 2 ] )

      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )
    #end if dset_values is not None
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:subpin', 'statepoint', )
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
  #	METHOD:		SubPinPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'subpin_theta' ]
    #return  [ 'subpin_r', 'subpin_theta' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		SubPinPlot.GetDataSetDisplayMode()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns ''.
"""
    return  ''
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
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_timeValue
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Subpin Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes, 'ax', and 'ax2'.
XXX size according to how many datasets selected?
"""
    self.ax = self.fig.add_axes(
        #[ 0.05, 0.05, 0.9, 0.85 ],
        [ 0.05, 0.05, 0.8, 0.85 ],
	projection = 'polar' if self.mode == 'theta' else 'rectilinear'
	)
    self.legendAx = self.fig.add_axes(
	[ 0.9, 0.05, 0.05, 0.85 ]
        )
    #self.ax2 = self.ax.twiny() if len( self.dataSetValues ) > 1 else None
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    if (reason & STATE_CHANGE_coordinates) > 0:
      self.assemblyAddr = self.state.assemblyAddr
      self.subAddr = self.state.subAddr
    if (reason & STATE_CHANGE_curDataSet) > 0:
      self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

    return  {}
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		SubPinPlot.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxSubAddrs', 'subAddr', 'timeValue' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( SubPinPlot, self ).LoadProps( props_dict )
# In PlotWidget
#    wx.CallAfter( self.UpdateState, replot = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    super( SubPinPlot, self )._OnMplMouseRelease( ev )

#    button = ev.button or 1
#    if button == 1 and self.cursor is not None:
#      axial_value = self.dmgr.GetAxialValue( None, cm = self.cursor[ 1 ] )
#      self.UpdateState( axial_value = axial_value )
#      self.FireStateChange( axial_value = axial_value )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		SubPinPlot.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    # dataSetSelections now handled in PlotWidget
    super( SubPinPlot, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'assemblyAddr', 'auxSubAddrs', 'subAddr', 'timeValue' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		SubPinPlot.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateDataSetValues()				-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """Rebuild dataset arrays to plot.
"""
    self.dataSetValues.clear()

#		-- Must have data
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    if self.dmgr.HasData():
      core = self.dmgr.GetCore()

      if self.mode == 'theta':
	# get from dataset?
        theta_count = max( 1, core.nsubtheta )
        thetas = np.linspace( 0.0, 2.0 * np.pi, theta_count, endpoint = False )
	radii = np.full( theta_count, 10.0, dtype = np.float32 )

	arc_wd = 2.0 * np.pi / theta_count
	widths = np.full( theta_count, arc_wd, dtype = np.float32 )

	self.dataSetValues[ 'thetas' ] = thetas
	self.dataSetValues[ 'radii' ] = radii
	self.dataSetValues[ 'widths' ] = widths

      else:
        pass
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
    kwargs = super( SubPinPlot, self )._UpdateStateValues( **kwargs )
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
          self.dmgr.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      replot = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      replot = True
      self.curDataSet = kwargs[ 'cur_dataset' ]
      ds_type = self.dmgr.GetDataSetType( self.curDataSet )
      self.mode = 'theta'  if ds_type == 'subpin_theta' else  'r'
      self.container.GetDataSetMenu().Reset()
      wx.CallAfter( self.container.GetDataSetMenu().UpdateMenu )

      self.axialValue = \
          self.dmgr.GetAxialValue( self.curDataSet, cm = self.axialValue.cm )
      self.stateIndex = max(
          0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet )
	  )
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

#end SubPinPlot
