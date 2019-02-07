#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		intrapin_edits_plot.py				-
#	HISTORY:							-
#		2018-10-22	leerw@ornl.gov				-
#         Added clipboard copy.
#		2018-08-31	leerw@ornl.gov				-
#	  Rework after conversations with Cole Gentry.
#		2018-08-23	leerw@ornl.gov				-
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
  from matplotlib import cm, colors, patches, transforms
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
#	CLASS:		IntraPinEditsPlot				-
#------------------------------------------------------------------------
class IntraPinEditsPlot( PlotWidget ):
  """
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

    super( IntraPinEditsPlot, self ).__del__()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    #self.auxNodeAddrs = []
    self.auxSubAddrs = []
    #self.ax2 = None
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
    self.curDataSet = None

#		-- dict by dataset name of np.ndarray
    self.dataSetValues = {}

    self.legendAx = None
    self.mapper = None
    self.subAddr = ( -1, -1 )

    super( IntraPinEditsPlot, self ).__init__( container, id, ref_axis = 'y' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateClipboardData()				-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    core = self.dmgr.GetCore()
    csv_text = '"{0}: Assy {1}; Axial {2:.3f}; {3}={4:.4g}"\n'.format(
        self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	self.axialValue.cm,
        self.state.timeDataSet, self.state.timeValue
        )

    radial_mesh = self.dataSetValues.get( 'radial_mesh' )
    values = self.dataSetValues.get( 'values' )
    if radial_mesh is not None and values is not None:
      csv_text += 'radius,value\n'
      for i in range( len( values ) ):
        csv_text += '{0:g},{1:g}\n'.format( radial_mesh[ i + 1 ], values[ i ] )

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		_CreateMenuDef()				-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( IntraPinEditsPlot, self )._CreateMenuDef()

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
configuring the grid, plotting, and creating self.axline.  The
self.dataSetValues dict has been populated with keys 'thetas' (angles
in radians), 'crud' (crud lengths by angle), optionally 'corrosion'
(corrosion length by angle), and other length values with cardinal keys
starting at 2.
"""
#		-- Something to plot?
#		--
    okay = reduce(
	lambda x, y: x and y in self.dataSetValues,
	[ True, 'radial_mesh', 'values' ]
	#[ True, 'pin_radius', 'radial_mesh', 'regions', 'values' ]
        )
    if okay and self.mapper is not None:
      #pin_radius = self.dataSetValues[ 'pin_radius' ]
      radial_mesh = self.dataSetValues[ 'radial_mesh' ]
      #regions = self.dataSetValues[ 'regions' ]
      values = self.dataSetValues[ 'values' ]

      core = self.dmgr.GetCore()
      title_str = '{0}: '.\
          format( self.dmgr.GetDataSetDisplayName( self.curDataSet ) )
      if 'units' in self.dataSetValues:
        title_str += self.dataSetValues[ 'units' ]

      assy_addr_text = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
      title_str += \
          '\nAssy {0}, Pin {1}, Axial {2:.3f}, {3} {4:.4g}'.format(
              assy_addr_text,
              str( ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 ) ),
	      self.axialValue.cm,
	      self.state.timeDataSet,
	      self.timeValue
              )
#      title_str = '%s: Assy %s, Axial %.3f, %s %.4g' % (
#          self.dmgr.GetDataSetDisplayName( self.curDataSet ),
#          assy_addr_text,
#	  self.axialValue.cm,
#	  self.state.timeDataSet,
#	  self.timeValue
#	  )
#      rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
#      title_line2 = 'Pin %s' % str( rc )
#      title_str += '\n' + title_line2

#			-- Create legend
#			--
      if self.mapper:
        self.fig.colorbar( self.mapper, cax = self.legendAx )

#			-- Add patches to axis
#			--
      self.ax.set_ylim( 0.0, radial_mesh[ -1 ] )
      #radial_mesh = self.dmgr.GetRadialMesh( values.shape[ 0 ] )

      #nvalues = min( len( regions ), len( values ) )
      #for i in range( nvalues ):
      for i in range( values.shape[ 0 ] ):
	#region = regions[ i ]
	value = values[ i ]
        from_r = radial_mesh[ i ]
	to_r = radial_mesh[ i + 1 ]

	self.ax.add_patch( patches.Rectangle(
	    ( 0, from_r ), 2.0 * np.pi, to_r - from_r,
	    color = self.mapper.to_rgba( value )
	    ) )
      #end for i in range( nvalues )

# Add base circle representing rod
      #pdb.set_trace()
      self.ax.add_patch( patches.Rectangle(
          ( 0, 0 ), 2.0 * np.pi, radial_mesh[ 0 ],
	  color = 'grey'
	  ) )

      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )
      self.ax.bar( 0, 1 ).remove()
      #self.ax.axis( 'off' )
      self.ax.set_xticks( [] )
      self.ax.set_yticks( radial_mesh[ 1 : ] )
    #end if len( self.dataSetValues ) > 0
  #end _DoUpdatePlot


  #----------------------------------------------------------------------
  #	METHOD:		_FindDataSetValues()				-
  #----------------------------------------------------------------------
  def _FindDataSetValues( self, x_ref_value, y_ref_value):
    """Find matching dataset values for the reference axis value.
@param  ref_ds_value	value in the reference dataset
@return			dict by real dataset name (not pseudo name) of
			dataset values or None if no matches
"""
    results = {}
    rodradius = 500.0
    fuelradius = 0.6 * rodradius
    gapradius = 1.075 * fuelradius
    thetas = self.dataSetValues.get( 'thetas' )
    crud = self.dataSetValues.get( 'crud' )
    corr = self.dataSetValues.get( 'corrosion' ) 
    result = {}

# find theta from x data
    datax = np.floor(x_ref_value/(2*np.pi)*len(thetas))
#find which dataset cursor is in for y
    if y_ref_value > rodradius and y_ref_value < rodradius + crud[datax] :
      datay = 0
      results[ 0 ] = datay
      results[ 1 ] = crud[ datax ] 
    elif y_ref_value < rodradius and y_ref_value > rodradius - corr[datax] :
      datay = 1
      results[ 0 ] = datay 
      results[ 1 ] = corr[ datax ] 
    else :
      results[ 0 ] = 2 

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
    return  ( 'axial:pin', 'statepoint' )
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
  #	METHOD:		GetDataSetTypes()				-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'intrapin_edits' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetDisplayMode()				-
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
    return  'Intrapin Edits Plot'
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
        [ 0.05, 0.01, 0.8, 0.8 ],
	projection = 'polar'
	)
    self.ax.set_theta_direction( -1 )
    self.ax.set_theta_zero_location( 'N' )

#can do here if you want
#    self.ax.bar( 0, 1 ).remove()
#    self.ax.set_xticks( [] )

    self.legendAx = self.fig.add_axes( [ 0.86, 0.01, 0.03, 0.8 ] )
  #end _InitAxes


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModelValues()				-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assume self.dmgr is valid.
@return			dict to be passed to UpdateState()
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

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		LoadProps()					-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxSubAddrs', 'subAddr', 'timeValue' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( IntraPinEditsPlot, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    super( IntraPinEditsPlot, self )._OnMplMouseRelease( ev )

#    button = ev.button or 1
#    if button == 1 and self.cursor is not None:
#      axial_value = self.dmgr.GetAxialValue( None, cm = self.cursor[ 1 ] )
#      self.UpdateState( axial_value = axial_value )
#      self.FireStateChange( axial_value = axial_value )
  #end _OnMplMouseRelease


  #----------------------------------------------------------------------
  #	METHOD:		SaveProps()					-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    # dataSetSelections now handled in PlotWidget
    super( IntraPinEditsPlot, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'assemblyAddr', 'auxSubAddrs', 'subAddr', 'timeValue' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
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
    """Rebuild dataset arrays to plot.  Upon return, self.dataSetValues
will have at least two, usually three keys: 'thetas', 'crud', and optionally
'corrosion'.  It is assumed that a length-based 'subpin' dataset will use the
radial dataset dimension to store crud and corrosion lengths, respectively.
An additional lengths will be added with cardinal order keys starting at 2.

Note all of this could be done in _DoUpdatePlot(), but this follows the pattern
of other PlotWidget extensions, where data fetching is done here, and
_DoUpdatePlot() takes care of (when necessary) recreating the plot when data
selections have not changed.
"""
    self.dataSetValues.clear()
    #self.dataSetValues = None

#		-- Must have data
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    dset = start_dset = count_dset = None
    if self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      if dset is not None and \
          dset.attrs and 'PinFirstRegionIndexArray' in dset.attrs and \
          'PinNumRegionsArray' in dset.attrs:
	start_name = DataSetName(
	    self.curDataSet.modelName,
	    DataUtils.ToString( dset.attrs[ 'PinFirstRegionIndexArray' ] )
	    )
        start_dset = self.dmgr.GetH5DataSet( start_name, self.timeValue )
	count_name = DataSetName(
	    self.curDataSet.modelName,
	    DataUtils.ToString( dset.attrs[ 'PinNumRegionsArray' ] )
	    )
        count_dset = self.dmgr.GetH5DataSet( count_name, self.timeValue )
        if 'units' in dset.attrs:
          self.dataSetValues[ 'units' ] = \
              DataUtils.ToString( dset.attrs[ 'units' ] )

    if dset is not None and start_dset is not None and count_dset is not None:
      core = self.dmgr.GetCore()
#      nradials = np.nanmax( count_dset )
#      self.dataSetValues[ 'radial_mesh' ] = radial_mesh = \
#      self.dmgr.\
#          GetRadialMesh( self.curDataSet, 'intrapin_edits_mesh', nradials )
      #xxxxx use pin_volumes for this pin
#      self.dataSetValues[ 'pin_radius' ] = \
#          self.dmgr.GetCore().GetPinDiameter() / 2.0

      assy_ndx = min( self.assemblyAddr[ 0 ], start_dset.shape[ 3 ] - 1 )
      pin_col = min( self.subAddr[ 0 ], start_dset.shape[ 1 ] - 1 )
      pin_row = min( self.subAddr[ 1 ], start_dset.shape[ 0 ] - 1 )
      axial_level = min( self.axialValue.pinIndex, start_dset.shape[ 2 ] - 1 )
      region_start = start_dset[ pin_row, pin_col, axial_level, assy_ndx ]
      region_count = count_dset[ pin_row, pin_col, axial_level, assy_ndx ]

      if region_count > 0:
	start_ndx = max( 0, region_start )
	stop_ndx = min( region_start + region_count, dset.shape[ 0 ] )
#	self.dataSetValues[ 'regions' ] = \
#	    [ x % nradials for x in range( start_ndx, stop_ndx ) ]
	self.dataSetValues[ 'values' ] = dset[ start_ndx : stop_ndx ]
	self.dataSetValues[ 'radial_mesh' ] = self.dmgr.CalcRadialMesh(
	    self.curDataSet, pin_col, pin_row, axial_level, assy_ndx,
            region_count
	    )

#			-- Create mapper
#			--
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
      self.mapper.set_array( np.array( dset ) )
    #end if dset is not None and start_dset is not None ...
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
    kwargs = super( IntraPinEditsPlot, self )._UpdateStateValues( **kwargs )
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
      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        replot = True
        self.curDataSet = kwargs[ 'cur_dataset' ]
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

#end IntraPinEditsPlot
