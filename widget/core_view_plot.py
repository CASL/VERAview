#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_view_plot.py				-
#	HISTORY:							-
#		2018-08-21	leerw@ornl.gov				-
#	  Added text values for assembly averages.
#		2018-08-20	leerw@ornl.gov				-
#	  Working version.
#		2018-08-18	leerw@ornl.gov				-
#	  Conversion to matplotlib.
#		2018-03-10	leerw@ornl.gov				-
#	  Calling self.mapper.to_rgba() once per assembly.
#		2018-03-02	leerw@ornl.gov				-
#	  Migrating to _CreateEmptyBitmapAndDC().
#		2018-02-10	leerw@ornl.gov				-
#	  Implemented dataset-aware state tuples.
#		2018-02-05	leerw@ornl.gov				-
#	  Moving Linux/GTK/X11 image manipulation to the UI thread.
#		2017-10-24	leerw@ornl.gov				-
#	  Using wx.Bitmap instead of PIL.Image.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-05-05	leerw@ornl.gov				-
#	  Modified LoadDataModelXxx() methods to process the reason param.
#		2017-03-10	leerw@ornl.gov				-
#	  Update to precisionDigits and precisionMode.
#		2017-03-04	leerw@ornl.gov				-
#	  Using self.precision.
#		2017-02-28	leerw@ornl.gov				-
#	  Calculating and setting image size.
#		2017-01-26	leerw@ornl.gov				-
#	  Removed assembly index from titles.
#		2017-01-12	leerw@ornl.gov				-
#	  Integrating channel datasets.
#		2016-12-16	leerw@ornl.gov				-
#	  Setting self.nodalMode in _LoadDataModelValues().
#		2016-12-09	leerw@ornl.gov				-
#		2016-12-08	leerw@ornl.gov				-
#	  Migrating to new DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DataModel.GetRange()
#	  directly.
#		2016-10-22	leerw@ornl.gov				-
#	  Calling DataModel.Core.Get{Col,Row}Label().
#		2016-10-20	leerw@ornl.gov				-
#	  In nodalMode, hiliting assembly in white and node in red.
#	  Calling DataModel.GetFactors().
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#	  Added auxNodeAddrs and nodeAddr attributes.
#		2016-10-14	leerw@ornl.gov				-
#	  Using new _DrawValues() method.
#		2016-10-01	leerw@ornl.gov				-
#	  Better handling with nodalMode attribute.
#		2016-09-30	leerw@ornl.gov				-
#	  Adding support for nodal derived types.
#		2016-09-29	leerw@ornl.gov				-
#	  Trying to prevent overrun of values displayed in cells.
#		2016-09-20	leerw@ornl.gov				-
#	  Fixed bug where brush_color might not have been defined when
#	  writing values.
#		2016-09-19	leerw@ornl.gov				-
#	  Using state.weightsMode to determine use of pinFactors.
#		2016-09-14	leerw@ornl.gov				-
#	  Using DataModel.pinFactors to determine no-value cells.
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-09	leerw@ornl.gov				-
#	  Added assembly label in clipboard headers.
#		2016-06-27	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _OnFindMax().
#		2016-03-07	leerw@ornl.gov				-
#	  Adding numbers for 'asy_' datasets.
#		2016-02-29	leerw@ornl.gov				-
#	  Calling Redraw() instead of _OnSize( None ).
#		2016-02-25	leerw@ornl.gov				-
#	  Modified _CreateToolTipText() to report the value of an
#	  assembly average or derived dataset.
#		2016-02-17	leerw@ornl.gov				-
#	  Added copy selection.
#		2016-02-11	leerw@ornl.gov				-
#	  Supporting pin:assembly datasets by duplicating the last pin
#	  value in each dimension.
#		2016-02-10	leerw@ornl.gov				-
#	  Title template and string creation now inherited from
#	  RasterWidget.
#		2016-02-09	leerw@ornl.gov				-
#	  Start on customizing title based on dataset shape.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2016-01-22	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2015-11-28	leerw@ornl.gov				-
#	  Calling DataModel.IsNoDataValue() instead of checking for
#	  gt value to draw.
#		2015-11-23	leerw@ornl.gov				-
#	  Fixed some bugs.
#		2015-11-19	leerw@ornl.gov				-
#	  Adding support for 'extra' datasets.
#		2015-11-18	leerw@ornl.gov				-
#	  Relaxing to allow any axial and assembly dimensions.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-06-17	leerw@ornl.gov				-
# 	  Extending RasterWidget.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-21	leerw@ornl.gov				-
#	  Showing legend now optional.
#		2015-05-18	leerw@ornl.gov				-
#	  Making the showing of assembly labels an option.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-04-22	leerw@ornl.gov				-
#	  Showing currently selected assembly.
#		2015-04-10	leerw@ornl.gov				-
#	  Minor fixes and removing sliders (now on VeraViewFrame).
#		2015-04-04	leerw@ornl.gov				-
#	  Zoom display to an assembly view.
#		2015-03-25	leerw@ornl.gov				-
#	  Many fixes and additions, most notably the SetDataSet()
#	  capability.  Also fixed some zooming issues and added
#	  the bitmapsLock protocol in _UpdateStateAndAxial().
#		2015-03-19	leerw@ornl.gov				-
#	  Trying per-menu item handler.
#		2015-03-11	leerw@ornl.gov				-
#	  Using ExposureSliderBean.
#		2015-03-06	leerw@ornl.gov				-
#	  New Widget.GetImage() for 'loading' image.
#	  Starting ellipse drawing at pixel (1,1).
#		2015-02-07	leerw@ornl.gov				-
#	  Processing average powers.
#		2015-02-06	leerw@ornl.gov				-
#	  Added tooltip.
#		2015-01-30	leerw@ornl.gov				-
#	  Added CreateMenu().
#		2015-01-28	leerw@ornl.gov				-
#	  Starting cell range and zoom processing.
#		2015-01-24	leerw@ornl.gov				-
#		2015-01-19	leerw@ornl.gov				-
#	  Re-designing
#		2015-01-16	leerw@ornl.gov				-
#		2015-01-07	leerw@ornl.gov				-
#	  Added popup on assembly.
#		2015-01-06	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, six, sys, threading, time, timeit, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
  from matplotlib import cm, colors, patches, transforms
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

try:
  from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
  #from matplotlib.backends.backend_wx import NavigationToolbar2Wx
  from matplotlib.figure import Figure
except Exception:
  raise ImportError, 'The wxPython matplotlib backend modules are required for this component'

from data.datamodel import *
from event.state import *

from .plot_widget import *
from .widget import *


#------------------------------------------------------------------------
#	CLASS:		Core2DPlot					-
#------------------------------------------------------------------------
class Core2DPlot( PlotWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.channelMode = False
    self.curDataSet = None

#		-- np.ndarray row x column
    self.dataSetValues = None
    self.imageData = None

    self.legendAx = None
    self.mapper = None

    self.mode = ''  # 'assy', 'core'
    self.nodalMode = False
    self.nodeAddr = -1
    self.npinx = \
    self.npiny = 0
    self.selectedPatches = []
    self.subAddr = ( -1, -1 )
    self.textDrawItems = []
    self.textDrawList = []
    self.textDrawSize = ( -1, -1 )
    self.titleText = None

    self.xtickLabels = \
    self.xtickLocs = \
    self.ytickLabels = \
    self.ytickLocs = None

    super( Core2DPlot, self ).__init__(
        container, id,
	ref_axis = 'y', ref_axis2 = 'x', show_cursor = False
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._CreateMenuDef()			-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( Core2DPlot, self )._CreateMenuDef()

    all_assy_max_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'max', True, True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'max', False, True )
	}
      ]
    all_assy_min_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'min', True, True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'min', False, True )
	}
      ]

    cur_assy_max_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'max', True, False )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'max', False, False )
	}
      ]
    cur_assy_min_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'min', True, False )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'min', False, False )
	}
      ]

    find_max_def = \
      [
	{ 'label': 'All Assemblies', 'submenu': all_assy_max_def },
	{ 'label': 'Current Assembly', 'submenu': cur_assy_max_def }
      ]
    find_min_def = \
      [
	{ 'label': 'All Assemblies', 'submenu': all_assy_min_def },
	{ 'label': 'Current Assembly', 'submenu': cur_assy_min_def }
      ]

    more_def = \
      [
	{ 'label': '-' },
	{ 'label': 'Find Maximum', 'submenu': find_max_def },
	{ 'label': 'Find Minimum', 'submenu': find_min_def },
#	{ 'label': '-' },
#	{ 'label': 'Hide Labels', 'handler': self._OnToggleLabels },
#	{ 'label': 'Hide Legend', 'handler': self._OnToggleLegend },
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
  #	METHOD:		Core2DPlot._CreateToolTipText()			-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, ev ):
    """Create a tool tip.  This implementation returns a blank string.
@param  ev		mouse motion event
"""
    core = None

    # assy_col, assy_row, pin_col, pin_row, value
    ds_values = None
    if ev is not None:
      ds_values = self._FindDataSetValues( ev.xdata, ev.ydata )
    if ds_values and len( ds_values ) >= 5:
      core = self.dmgr.GetCore()
      assy_addr_text = core.CreateAssyLabel( ds_values[ 0 ], ds_values[ 1 ] )
      tip_str = 'Assy=' + assy_addr_text
      if self.nodalMode:
	node_addr = self.dmgr.GetPinNodeAddr( *ds_values[ 2 : 4 ] )
        tip_str += ', Node={0:d}'.format( node_addr )
      else:
        tip_str += ', Pin={0:d},{1:d}'.format( *ds_values[ 2 : 4 ] )
      tip_str += ': {0:.3g}'.format( ds_values[ 4 ] )
    else:
      tip_str = ''

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._DoUpdatePlot()			-
  #----------------------------------------------------------------------
  def _DoUpdatePlot( self, wd, ht ):
    """Do the work of creating the plot, setting titles and labels,
configuring the grid, plotting, and creating self.axline.
"""
#		-- Something to plot?
#		--
    if self.imageData is not None:
      core = self.dmgr.GetCore()

      max_col = self.cellRange[ 4 ] * self.npinx
      max_row = self.cellRange[ 5 ] * self.npiny
      self.ax.imshow(
	  self.imageData,
	  #aspect = 'auto', # 'equal',
	  extent = [ 0, max_col, max_row, 0 ],
	  #interpolation = 'bilinear',
	  #interpolation = 'nearest'
	  interpolation = 'none'
	  #origin = 'upper'
          )
      if self.xtickLocs and self.xtickLabels:
        self.ax.set_xticks( self.xtickLocs )
        self.ax.set_xticklabels( self.xtickLabels )
      if self.ytickLocs and self.ytickLabels:
        self.ax.set_yticks( self.ytickLocs )
        self.ax.set_yticklabels( self.ytickLabels )

#		-- Create title
#		--
#      assy_addr_text = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
#      title_str = '%s: Assy %s, Axial %.3f, %s %.4g' % (
#          self.dmgr.GetDataSetDisplayName( self.curDataSet ),
#          assy_addr_text,
#	  self.axialValue.cm,
#	  self.state.timeDataSet,
#	  self.timeValue
#	  )
      title_str = '%s: Axial %.3f, %s %.4g' % (
          self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  self.axialValue.cm,
	  self.state.timeDataSet, self.timeValue
	  )

      if self.titleText is not None:
        self.titleText.remove()
      self.titleText = self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left',
	  size = 12,
	  verticalalignment = 'top'
	  )

#		-- Create legend
#		--
      if self.mapper:
        self.fig.colorbar( self.mapper, cax = self.legendAx )

      #x self.ax.axis('off')

#		-- Draw assembly boundaries if nodal mode
#		--
      if self.nodalMode:
	assy_y = 0
        for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ] ):
	  assy_x = 0
          for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ] ):
	    self.ax.add_patch( patches.Rectangle(
		( assy_x, assy_y ), self.npinx, self.npiny,
		color = 'lightgray', fill = False, linewidth = 1
	        ) )
	    assy_x += self.npinx
	  assy_y += self.npiny
      #end if self.nodalMode

#		-- Draw text values
#		--
#x      for s, c, x, y in self.textDrawList:
#x        self.ax.text(
#x	    x, y, s,
#x	    color = c,
#x	    family = 'sans-serif',
#x	    horizontalalignment = 'center',
#x	    size = 'small', # 10
#x	    verticalalignment = 'center'
#x	    )
      #end for d in self.textDrawList
    #end if self.dataSetValues is not None
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._DoUpdateRedraw()			-
  #----------------------------------------------------------------------
  def _DoUpdateRedraw( self, hilite = True ):
    """
"""
    for p in self.selectedPatches:
      p.remove()
    del self.selectedPatches[ : ]

#		-- Something to plot?
#		--
    if self.imageData is not None and hilite:
#			-- Draw text
#			--
      if self.textDrawList:
        wd, ht = self.GetClientSize()
	if ( wd, ht ) != self.textDrawSize:
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug( 'new size=%d,%d', wd, ht )
	  self.textDrawSize = ( wd, ht )
	  for i in self.textDrawItems:
	    try:
	      i.remove()
	    except:
	      pass
	  cell_size = \
              float( min( wd, ht ) ) / \
	      max( self.imageData.shape[ 0 ], self.imageData.shape[ 1 ] )
          font_size = min( 20, int( cell_size * 0.8 / 3.0 ) )
	  if font_size >= 5:
            for s, c, x, y in self.textDrawList:
              item = self.ax.text(
	          x, y, s,
	          color = c,
	          family = 'sans-serif',
	          horizontalalignment = 'center',
	          size = font_size,
	          verticalalignment = 'center'
	          )
              self.textDrawItems.append( item )
      #end if self.textDrawList

#			-- Highlight selected assembly
#			--
      if self.nodalMode:
        npinx = npiny = 2
      else:
        npinx = self.npinx
	npiny = self.npiny
      x = (self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]) * npinx
      y = (self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]) * npiny

      assy_patch = patches.Rectangle(
	  ( x, y ), npinx, npiny,
	  color = 'white', fill = False, linewidth = 2
          )
      self.ax.add_patch( assy_patch )
      self.selectedPatches.append( assy_patch )

#			-- Highlight selected node
#			--
      if self.nodalMode:
        if self.nodeAddr == 3:
	  x += 1
	  y += 1
        elif self.nodeAddr == 2:
	  y += 1
        elif self.nodeAddr == 1:
	  x += 1
        node_patch = patches.Rectangle(
	    ( x, y ), 1, 1,
	    color = 'yellow', fill = False, linewidth = 1
	    )
        self.ax.add_patch( node_patch )
	self.selectedPatches.append( node_patch )
    #end if self.dataSetValues is not None
  #end _DoUpdateRedraw


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._FindDataSetValues()			-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, x_ref_value, y_ref_value ):
    """Find matching dataset values for the reference axis value.
    Args:
        x_ref_value (float): x-axis event location
	y_ref_value (float): y-axis event location
    Returns:
        tuple: ( assy_col, assy_row, pin_col, pin_row, value )
"""
    result = None
    if self.dataSetValues is not None and x_ref_value and y_ref_value:
      f, i = math.modf( x_ref_value / self.npinx )
      assy_col = self.cellRange[ 0 ] + int( i )
      pin_col = int( f * self.npinx )

      f, i = math.modf( y_ref_value / self.npiny )
      assy_row = self.cellRange[ 1 ] + int( i )
      pin_row = int( f * self.npiny )

      value = self.dataSetValues[ int( y_ref_value ), int( x_ref_value ) ]
      result = ( assy_col, assy_row, pin_col, pin_row, value )

    return  result
  #end _FindDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [
	'channel', 'pin',
	':assembly', ':chan_radial', ':node',
	':radial', ':radial_assembly', ':radial_node'
	]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.GetDataSetDisplayMode()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns ''.
"""
    return  ''
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_timeValue
	])
#	STATE_CHANGE_stateIndex
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._InitAxes()				-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes 'ax'.
"""
    del self.selectedPatches[ : ]
    self.titleText = None
    # [ left, bottom, wd, ht ]
    #self.ax = self.fig.add_axes( [ 0.05, 0.05, 0.9, 0.85 ] )
    self.ax = self.fig.add_axes( [ 0.05, 0.01, 0.8, 0.8 ] )
    self.ax.get_xaxis().set_ticks_position( 'top' )
    #self.legendAx = self.fig.add_axes( [ 0.9, 0.05, 0.05, 0.85 ] )
    self.legendAx = self.fig.add_axes( [ 0.851, 0.01, 0.05, 0.8 ] )
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """
"""
    update_args = {}
    if (reason & STATE_CHANGE_coordinates) > 0:
      update_args[ 'assembly_addr' ] = \
          self.dmgr.NormalizeAssemblyAddr( self.state.assemblyAddr )
      update_args[ 'sub_addr' ] = \
          self.dmgr.NormalizeSubAddr( self.state.subAddr )

    if (reason & STATE_CHANGE_curDataSet) > 0:
      update_args[ 'cur_dataset' ] = \
          self._FindFirstDataSet( self.state.curDataSet )

    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
    self.cellRange = self.dmgr.ExtractSymmetryExtent()

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Core2DPlot, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    #if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
    if self.curDataSet:
      if self.channelMode:
        self._OnFindMinMaxChannel(
	    mode, self.curDataSet, all_states_flag, all_assy_flag
	    )
      else:
        self._OnFindMinMaxPin(
	    mode, self.curDataSet, all_states_flag, all_assy_flag
	    )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._OnMplMouseRelease()			-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    super( Core2DPlot, self )._OnMplMouseRelease( ev )
#    button = ev.button or 1
#    if button == 1 and not self.toolbar.IsShown():

    #if ev.guiEvent.GetClickCount() > 0:
    if ev is not None:
      self.xlim = self.ax.get_xlim()
      self.ylim = self.ax.get_ylim()

      state_args = {}
      ds_values = self._FindDataSetValues( ev.xdata, ev.ydata )
      if ds_values and ds_values[ 0 : 2 ] != self.assemblyAddr[ 1 : 3 ]:
        assy_addr = self.dmgr.CreateAssemblyAddr( *ds_values[ 0 : 2 ] )
        if assy_addr >= 0:
          state_args[ 'assembly_addr' ] = assy_addr

      if self.nodalMode:
        node_addr = self.dmgr.GetPinNodeAddr( *ds_values[ 2 : 4 ] )
        is_aux = self.IsAuxiliaryEvent( ev.guiEvent )
        if is_aux:
          addrs = list( self.auxNodeAddrs )
	  if node_addr in addrs:
	    addrs.remove( node_addr )
	  else:
	    addrs.append( node_addr )
          if addrs != self.auxNodeAddrs:
	    state_args[ 'aux_node_addrs' ] = addrs
        elif node_addr != self.nodeAddr:
          state_args[ 'node_addr' ] = node_addr
          state_args[ 'aux_node_addrs' ] = []

      elif ev.guiEvent.GetClickCount() > 1:
        if ds_values[ 2 : 4 ] != self.subAddr:
          state_args[ 'sub_addr' ] = ds_values[ 2 : 4 ]

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if ev.guiEvent.GetClickCount() > 0
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Core2DPlot, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._UpdateDataSetValues()		-
  #----------------------------------------------------------------------
  def _UpdateDataSetValues( self ):
    """
"""
    self.dataSetValues = None
    self.imageData = None
    self.npinx = self.npiny = 0

    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )

#	-- Must have data
#	--
    core = dset = None
    if self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
#		-- "Item" refers to channel or pin
#		--
      item_factors = None
      if self.state.weightsMode == 'on':
        item_factors = self.dmgr.GetFactors( self.curDataSet )
     
      dset_array = np.array( dset )
      dset_shape = dset.shape
##      if self.nodalMode:
##        #self.npinx = self.npiny = item_col_limit = item_row_limit = 2
##        self.npinx = self.npiny = 2
##      else:
##	item_col_limit = core.npinx
##	item_row_limit = core.npiny
##        if self.channelMode:
##	  item_col_limit += 1
##	  item_row_limit += 1
##        self.npinx = min( item_col_limit, dset_shape[ 1 ] )
##        self.npiny = min( item_row_limit, dset_shape[ 0 ] )
      if self.nodalMode:
        self.npinx = self.npiny = 2
      else:
	self.npinx = dset_shape[ 1 ]
	self.npiny = dset_shape[ 0 ]

      draw_value_flag = \
          self.curDataSet is not None and \
	  dset_shape[ 0 ] == 1 and dset_shape[ 1 ] == 1
      node_value_draw_list = []
      #assy_value_draw_list = []
      del self.textDrawList[ : ]

      axial_level = min( self.axialValue.pinIndex, dset_shape[ 2 ] - 1 )
      axial_value = \
          self.dmgr.GetAxialValue( self.curDataSet, core_ndx = axial_level )

      self.cellRange = self.dmgr.ExtractSymmetryExtent()
      im_wd = self.cellRange[ 4 ] * self.npinx
      im_ht = self.cellRange[ 5 ] * self.npiny

      self.dataSetValues = np.empty( ( im_wd, im_ht ), dtype = np.float64 )
      self.dataSetValues[ : ] = np.nan
      self.imageData = np.zeros( ( im_wd, im_ht, 4 ), dtype = np.uint8 )

#		-- Create mapper
#		--
      ds_range = self._ResolveDataRange(
          self.curDataSet,
	  self.timeValue if self.state.scaleMode == 'state' else -1.0
	  )
      if self.scaleType == 'log':
        norm = colors.LogNorm(
	    vmin = max( ds_range[ 0 ], 1.0e-16 ),
	    vmax = max( ds_range[ 1 ], 1.0e-16 ),
	    clip = True
	    )
      else:
        norm = colors.Normalize(
	    vmin = ds_range[ 0 ], vmax = ds_range[ 1 ], clip = True
	    )
      self.mapper = cm.ScalarMappable(
	  norm = norm,
	  cmap = cm.get_cmap( self.colormapName )
          )
      self.mapper.set_array( dset_array )
      #trans_color_arr = np.array( [ 200, 200, 200, 255 ], dtype = np.uint8 )
      fc = np.array( self.fig.get_facecolor() ) * 255.0
      trans_color_arr = fc.astype( np.uint8 )

#		-- Map data values to colors
#		--
      im_row = 0
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ] ):
	im_row_to = im_row + self.npiny
	im_col = 0

        for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ] ):
	  im_col_to = im_col + self.npinx
	  assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

	  if assy_ndx < 0 or assy_ndx >= dset_shape[ 3 ]:
	    self.imageData[ im_row : im_row_to, im_col : im_col_to ] = \
	        trans_color_arr

	  else: # if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    cur_array = dset_array[ :, :, axial_level, assy_ndx ]
	    cur_colors = self.mapper.to_rgba( cur_array, bytes = True )
	    if item_factors is not None:
	      cur_factors = item_factors[ :, :, axial_level, assy_ndx ]
	      cur_colors[ cur_factors == 0 ] = trans_color_arr
	      cur_colors[ np.isnan( cur_array ) ] = trans_color_arr
	      cur_colors[ np.isinf( cur_array ) ] = trans_color_arr

	    if self.nodalMode:
	      cur_array = cur_array.reshape( ( 2, 2 ) )
	      cur_colors = cur_colors.reshape( ( 2, 2, 4 ) )
	    self.dataSetValues[ im_row : im_row_to, im_col : im_col_to ] = \
	        cur_array
	    self.imageData[ im_row : im_row_to, im_col : im_col_to ] = \
		cur_colors
	  #end else assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]

	  im_col = im_col_to
        #end for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )

	im_row = im_row_to
      #end for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ] )

      if draw_value_flag:
        for r in range( im_ht ):
	  for c in range( im_wd ):
	    if not np.array_equal( self.imageData[ r, c ], trans_color_arr ):
	      clr = Widget.GetContrastColor( *self.imageData[ r, c ] )
	      self.textDrawList.append((
		  self._CreateValueString( self.dataSetValues[ r, c ] ),
		  np.array( clr ) / 255.0, c + 0.5, r + 0.5
	          ))
      #end if draw_value_flag

      tickbase = self.npiny / 2.0
      self.ytickLocs = [
          (i * self.npiny) + tickbase
	  for i in range( self.cellRange[ 5 ] )
	  ]
      self.ytickLabels = [
          core.GetRowLabel( i )
	  for i in range( self.cellRange[ 1 ], self.cellRange[ 3 ] )
          ]

      tickbase = self.npinx / 2.0
      self.xtickLocs = [
          (i * self.npinx) + tickbase
	  for i in range( self.cellRange[ 4 ] )
	  ]
      self.xtickLabels = [
          core.GetColLabel( i )
	  for i in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )
          ]
    #end if dset is not None and core is not None
  #end _UpdateDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DPlot._UpdateStateValues()			-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Core2DPlot, self )._UpdateStateValues( **kwargs )
    replot = kwargs.get( 'replot', False )
    redraw = kwargs.get( 'redraw', False )

#    kwargs = super( Core2DPlot, self )._UpdateStateValues( **kwargs )
#    changed = kwargs.get( 'changed', False )
#    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      redraw = True  # replot = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.dmgr.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
        redraw = True
	self.auxNodeAddrs = aux_node_addrs

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      replot = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        replot = True
        self.curDataSet = kwargs[ 'cur_dataset' ]
	self.nodalMode = self.dmgr.IsNodalType( ds_type )
      elif self.curDataSet is None:
        replot = True
        self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

      if replot:
        self.container.GetDataSetMenu().Reset()
        wx.CallAfter( self.container.GetDataSetMenu().UpdateMenu )
        self.axialValue = \
            self.dmgr.GetAxialValue( self.curDataSet, cm = self.axialValue.cm )
        self.stateIndex = max(
            0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet )
	    )
    #end if 'cur_dataset'

    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        redraw = True
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr(
          kwargs[ 'sub_addr' ],
	  'channel' if self.channelMode else 'pin'
	  )
      if sub_addr != self.subAddr:
        redraw = True
        self.subAddr = sub_addr
    #end if 'sub_addr'

    if 'time_dataset' in kwargs:
      replot = True

    if 'weights_mode' in kwargs:
      kwargs[ 'replot' ] = True

    if redraw:
      kwargs[ 'redraw' ] = True
    if replot:
      kwargs[ 'replot' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Core2DPlot
