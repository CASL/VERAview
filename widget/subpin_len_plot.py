#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		subpin_len_plot.py				-
#	HISTORY:							-
#		2018-05-04	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, six, sys, time, traceback
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
#	CLASS:		SubPinLengthPlot				-
#------------------------------------------------------------------------
class SubPinLengthPlot( PlotWidget ):
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

    super( SubPinLengthPlot, self ).__del__()
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
#    self.dataSetDialog = None
#    self.dataSetSelections = {}  # keyed by DataSetName
#    self.dataSetTypes = set()

		#-- keyed by DataSetName, dicts with keys 'mesh', 'data'
		#-- keys: 'thetas', 'radii', 'widths'
    self.dataSetValues = {}

    self.legendAx = None
    self.mode = 'r'  # 'r', 'theta'
    #self.nodeAddr = -1
#    self.scaleMode = 'selected'
    self.subAddr = ( -1, -1 )
    #self.tallyAddr = DataModel.CreateEmptyTallyAddress()

    super( SubPinLengthPlot, self ).__init__( container, id, ref_axis = 'y' )
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
    menu_def = super( SubPinLengthPlot, self )._CreateMenuDef()

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

    ds_values = self._FindDataSetValues( ev.xdata, ev.ydata )

    if ds_values[ 0 ] == 0 :
      tip_str = 'crud thickness:\n%.1f microns' % ds_values[ 1 ]
    elif ds_values[ 0 ] == 1 :
      tip_str = 'corrosion thickness:\n%.1f microns' % ds_values[ 1 ]
    else :
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
#		-- We don't want default PlotWidget grid stuff
    #super( SubPinLengthPlot, self )._DoUpdatePlot( wd, ht )
    #self.ax.grid( False )

#    label_font_size = 14
#    tick_font_size = 12
#    self.titleFontSize = 16
#    if 'wxMac' not in wx.PlatformInfo and wd < 800:
#      decr = (800 - wd) / 50.0
#      label_font_size -= decr
#      tick_font_size -= decr
#      self.titleFontSize -= decr

#		-- Something to plot?
#		--
    if len( self.dataSetValues ) > 0:
      core = self.dmgr.GetCore()
      assy_addr_text = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
      title_str = '%s: Assy %s, Axial %.3f, %s %.4g' % (
          self.dmgr.GetDataSetDisplayName( self.curDataSet ),
          assy_addr_text,
	  self.axialValue.cm,
	  self.state.timeDataSet,
	  self.timeValue
	  )
      rc = ( self.subAddr[ 0 ] + 1, self.subAddr[ 1 ] + 1 )
      title_line2 = 'Pin %s' % str( rc )
      title_str += '\n' + title_line2

#			-- Determine data values range
#			--
      ds_range = self._ResolveDataRange(
          self.curDataSet,
	  self.timeValue if self.state.scaleMode == 'state' else -1.0
	  )
      ds_range_all = self._ResolveDataRange(
          self.curDataSet,
	     -1.0
	  )
#xx
# ds_range[ 0 ] and ds_range[ 1 ] are the data range min, max, possibly
# set by the user
#xx
      crud_max_all_time = self.dataSetValues.get( 'crud_max_all_time' )
#      print('ds_range_all is ', ds_range_all[0], ds_range_all[1])
      rodradius = 500.0
      fuelradius = 0.6 * rodradius
      gapradius = 1.075 * fuelradius
#      ds_range[ 1 ] = rodradius + ds_range[ 1 ]

# Make your self.ax.add_patch() calls here, I'm guessing
#xx
      thetas = self.dataSetValues.get( 'thetas' )
      crud = self.dataSetValues.get( 'crud' )
      corr = self.dataSetValues.get( 'corrosion' )

#			-- Add plot to axis
#			--
      self.ax.set_ylim( 0.0, rodradius + ds_range_all[ 1 ]) #crud.max() )

# Add base circle representing rod
      self.ax.add_patch( patches.Rectangle(
	      ( 0, 0 ), 2.0 * np.pi, rodradius,
	      color='grey'
	      ) )

      for th in range( len( thetas ) ):
	th_start = thetas[ th ]
	if th < len( thetas ) - 1:
	  th_wd = thetas[ th + 1 ] - th_start
	else:
	  th_wd = np.pi * 2.0 - th_start

	self.ax.add_patch( patches.Rectangle(
	    ( th_start, rodradius ), th_wd, crud[ th ],
	    color = '#ffaf07', ec='black'
	    ) )
	self.ax.add_patch( patches.Rectangle(
	    ( th_start, rodradius - corr[ th ] ), th_wd, corr[ th ],
	    color = 'silver'
	    ) )
      #end for th in range( len( self.dataSetValues ) )
#xx

# Add gap circle
      self.ax.add_patch(patches.Rectangle(
	      (0,0), 2.0 * np.pi, gapradius,
		  color='white'
		  ) )

# Add fuel pellet circle
      self.ax.add_patch(patches.Rectangle(
	      (0,0), 2.0 * np.pi, fuelradius,
		  color='orange'
		  ) )

      self.fig.text(
          0.1, 0.985, title_str,
	  horizontalalignment = 'left', verticalalignment = 'top'
	  )
      self.ax.bar(0,1).remove()
      self.ax.axis('off')
      self.ax.set_xticks(thetas[0: -1])
    #end if len( self.dataSetValues ) > 0
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
  #	METHOD:		GetDataSetTypes()				-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'subpin_cc' ]
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
    return  'Subpin Length Plot'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		_InitAxes()					-
  #----------------------------------------------------------------------
  def _InitAxes( self ):
    """Initialize axes, 'ax', and 'ax2'.
XXX size according to how many datasets selected?
"""
#xx
# Assuming no need for a legend colorbar
    self.ax = self.fig.add_axes(
        [ 0.05, 0.05, 0.9, 0.85 ],
	projection = 'polar'
	)
    self.ax.set_theta_direction( -1 )
    self.ax.set_theta_zero_location( 'N' )

#    self.ax = self.fig.add_axes(
#        [ 0.05, 0.05, 0.8, 0.85 ],
#	projection = 'polar' if self.mode == 'theta' else 'rectilinear'
#	)
#    self.legendAx = self.fig.add_axes(
#	[ 0.9, 0.05, 0.05, 0.85 ]
#        )
#xx
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

    super( SubPinLengthPlot, self ).LoadProps( props_dict )
# In PlotWidget
#    wx.CallAfter( self.UpdateState, replot = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		_OnMplMouseRelease()				-
  #----------------------------------------------------------------------
  def _OnMplMouseRelease( self, ev ):
    """
"""
    super( SubPinLengthPlot, self )._OnMplMouseRelease( ev )

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
    super( SubPinLengthPlot, self ).SaveProps( props_dict, for_drag = for_drag )

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
#    self.dataSetTypes.clear()
    self.dataSetValues.clear()

#		-- Must have data
#		--
    #if DataModel.IsValidObj( self.data, state_index = self.stateIndex ):
    if self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      core = self.dmgr.GetCore()

      self.dataSetValues[ 'thetas' ] = core.subPinTheta

      assy_ndx = min( self.assemblyAddr[ 0 ], dset.shape[ 5 ] - 1 )
      pin_col = min( self.subAddr[ 0 ], dset.shape[ 3 ] - 1 )
      pin_row = min( self.subAddr[ 1 ], dset.shape[ 2 ] - 1 )
      axial_level = min( self.axialValue.subPinIndex, dset.shape[ 4 ] - 1 )
      dset_values = dset[ :, :, pin_row, pin_col, axial_level, assy_ndx ]

      self.dataSetValues[ 'crud' ] = \
          dset[ 0, :, pin_row, pin_col, axial_level, assy_ndx ]
      #if dset.shape[ 0 ] > 1:
      self.dataSetValues[ 'corrosion' ] = \
          dset[ 1, :, pin_row, pin_col, axial_level, assy_ndx ]
      crud_max_all_time = max(dset[ 0, :, pin_row, pin_col, axial_level, assy_ndx ])
      corr_max_all_time = max(dset[ 1, :, pin_row, pin_col, axial_level, assy_ndx ])
#      print('crudmaxalltime is ',crud_max_all_time)
      self.dataSetValues[ 'crud_max_all_time' ] = max(dset[ 0, :, pin_row, pin_col, axial_level, assy_ndx ])
	  #			-- Other lengths?
      for i in range( 2, dset.shape[ 0 ] ):
        self.dataSetValues[ 0 ] = \
            dset[ i, :, pin_row, pin_col, axial_level, assy_ndx ]
    #end if dset is not None
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
    kwargs = super( SubPinLengthPlot, self )._UpdateStateValues( **kwargs )
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
    datax = int( np.floor(x_ref_value/(2*np.pi)*len(thetas)) )
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

###    if ndx >= 0:
###      for k in self.dataSetValues:
###        qds_name = self._GetDataSetName( k )
###
###        data_pair = self.dataSetValues[ k ]
###        time_values = data_pair[ 'times' ]
###        data_set_item = data_pair[ 'data' ]
###
###        #data_set_item = self.dataSetValues[ k ]
###        if not isinstance( data_set_item, dict ):
###          data_set_item = { '': data_set_item }
###
###        sample = data_set_item.itervalues().next()
###        if len( sample ) > ndx:
###	  cur_dict = {}
###          for rc, values in data_set_item.iteritems():
###	    cur_dict[ rc ] = values[ ndx ]
###
###	  results[ qds_name ] = cur_dict
###        #end if ndx in range
###      #end for k
###    #end if ndx

    return  results
  #end _FindDataSetValues



#end SubPinLengthPlot
