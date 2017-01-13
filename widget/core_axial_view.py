#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_axial_view.py				-
#	HISTORY:							-
#		2017-01-13	leerw@ornl.gov				-
#	  Integrating channel datasets.
#		2016-12-20	leerw@ornl.gov				-
#	  Migrating to new DataModelMgr.
#		2016-11-23	leerw@ornl.gov				-
#	  Fixed _CreateDrawConfig() in scale mode where axial mesh was
#	  not adequately rendered.
#		2016-10-31	leerw@ornl.gov				-
#	  Added nodeAddr attribute, selection of node_addr in
#	  _FindPinNodal(), and firing of node_addr changes.
#		2016-10-30	leerw@ornl.gov				-
#	  Drawing node boundary lines and forcing value size to fit in
#	  all axial mesh vertical sizes.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DatModel.GetRange()
#	  directly.
#		2016-10-22	leerw@ornl.gov				-
#	  Calling DataModel.Core.Get{Col,Row}Label().
#		2016-10-21	leerw@ornl.gov				-
#	  Attempting to draw node values.
#		2016-10-20	leerw@ornl.gov				-
#	  Calling DataModel.GetFactors().
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-10-06	leerw@ornl.gov				-
#	  Updated to call DataModel.IsNodalType() and thus support
#	  pin:radial_node datasets.
#		2016-10-01	leerw@ornl.gov				-
#	  Adding support for nodal derived types.
#		2016-09-19	leerw@ornl.gov				-
#	  Using state.weightsMode to determine use of pinFactors.
#		2016-09-14	leerw@ornl.gov				-
#	  Redrawing on changed pin selection
#	  Using DataModel.pinFactors to determine no-value cells.
#		2016-08-16	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-11	leerw@ornl.gov				-
#	  Handling 'mode' correctly in LoadProps().
#		2016-07-01	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-20	leerw@ornl.gov				-
#	  GetDataSetTypes() changed so pin:assembly is the only derived
#	  type.
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _OnFindMax().
#		2016-03-05	leerw@ornl.gov				-
#	  Single widget with tool button for toggling slice axis.
#		2016-03-04	leerw@ornl.gov				-
#	  Not redrawing on changes to the slice assembly or pin col/row.
#		2016-03-02	leerw@ornl.gov				-
#	  Scaling correctly.  Just lacking clipboard data copy.
#		2016-02-29	leerw@ornl.gov				-
#	  Starting with core_view.py.
#------------------------------------------------------------------------
import logging, math, os, sys, threading, time, timeit, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  #from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) is required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.datamodel import *
from event.state import *
from legend import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		CoreAxial2DView					-
#------------------------------------------------------------------------
class CoreAxial2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    #self.avgDataSet = None
    #self.avgValues = {}
    self.channelMode = False

#		-- 'xz' is x-plane view of selected y-plane
#		-- 'yz' is y-plane view of selected x-plane
    self.mode = kwargs.get( 'mode', 'xz' )  # 'xz' and 'yz'
    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    self.toolButtonDefs = [ ( 'X_16x16', 'Toggle Slice Axis', self._OnMode ) ]

    super( CoreAxial2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardDisplayedData()  if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
#        self._CreateClipboardSelectionData() \
#        if cur_selection_flag else \
#        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None

    core = dset = None
    is_valid = self.dmgr.IsValid(
        self.curDataSet,
	axial_level = self.axialValue[ 1 ]
	#state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = np.array( dset )
      dset_shape = dset_value.shape
      #axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      node_addr = self.dmgr.GetNodeAddr( self.subAddr )

      if self.mode == 'xz':
	assy_row = self.assemblyAddr[ 2 ]
	pin_row = self.subAddr[ 1 ]
	#pin_count = 4  if self.nodalMode else  dset_shape[ 0 ]
	if self.nodalMode:
	  pin_shape_count = 2
	  pin_count = 4
          node_cells = ( 0, 1 ) if node_addr in ( 0, 1 ) else ( 2, 3 )
	else:
	  pin_count = pin_shape_count = dset_shape[ 0 ]
      else:
	assy_col = self.assemblyAddr[ 1 ]
	pin_col = self.subAddr[ 0 ]
	#pin_count = 4  if self.nodalMode else  dset_shape[ 1 ]
	if self.nodalMode:
	  pin_shape_count = 2
	  pin_count = 4
          node_cells = ( 0, 2 ) if node_addr in ( 0, 2 ) else ( 1, 3 )
	else:
	  pin_count = pin_shape_count = dset_shape[ 1 ]

      clip_shape = (
          self.cellRange[ -1 ],
	  (pin_shape_count * self.cellRange[ -2 ]) + 1
	  )
      clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      clip_data.fill( 0.0 )

      #for ax in range( self.cellRange[ -1 ] ):
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
	ax_offset = self.cellRange[ 3 ] - 1 - ax
	#clip_data[ ax_offset, 0 ] = self.data.core.axialMeshCenters[ ax ]
	cur_axial_value = \
	    self.dmgr.GetAxialValue( self.curDataSet, core_ndx = ax )
	clip_data[ ax_offset, 0 ] = cur_axial_value[ 0 ]

	pin_cell = 1
        for assy_cell in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  pin_cell_to = pin_cell + pin_count
	  if self.mode == 'xz':
	    assy_ndx = core.coreMap[ assy_row, assy_cell ] - 1
	    if assy_ndx >= 0:
	      if self.nodalMode:
		for k in xrange( len( node_cells ) ):
	          clip_data[ ax_offset, pin_cell + k ] = \
		    dset_value[ 0, node_cells[ k ], ax, assy_ndx ]
	      else:
	        clip_data[ ax_offset, pin_cell : pin_cell_to ] = \
	            dset_value[ pin_row, :, ax, assy_ndx ]
	      #end if-else self.nodalMode

	  else:
	    assy_ndx = core.coreMap[ assy_cell, assy_col ] - 1
	    if assy_ndx >= 0:
	      if self.nodalMode:
		for k in xrange( len( node_cells ) ):
	          clip_data[ ax_offset, pin_cell + k ] = \
		    dset_value[ 0, node_cells[ k ], ax, assy_ndx ]
	      else:
	        clip_data[ ax_offset, pin_cell : pin_cell_to ] = \
	            dset_value[ :, pin_col, ax, assy_ndx ]
	      #end if-else self.nodalMode
	  #end if-else self.mode

	  pin_cell = pin_cell_to
        #end for assy_cel
      #end for axials

      item_label = 'Chan'  if self.channelMode else  'Pin'
      nodes_str = ''
      if self.nodalMode:
	nodes_str = 'Nodes=%d,%d; ' % \
	    ( node_cells[ 0 ] + 1, node_cells[ 1 ] + 1 )

      if self.mode == 'xz':
        title1 = '"%s: Assy Row=%s; %s Row=%d; %s%s=%.3g"' % (
	    self.dmgr.GetDataSetDisplayName( self.curDataSet ),
            core.GetRowLabel( assy_row ),
	    item_label, pin_row + 1, nodes_str,
	    self.state.timeDataSet, self.timeValue
	    #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )
	col_labels = \
	    core.GetColLabel( self.cellRange[ 0 ], self.cellRange[ 2 ] )
        title2 = '"Axial; Cols=%s"' % ':'.join( col_labels )

      else:
        title1 = '"%s: Assy Col=%s; %s Col=%d; %s%s=%.3g"' % (
	    self.dmgr.GetDataSetDisplayName( self.curDataSet ),
            core.GetColLabel( assy_col ),
	    item_label, pin_col + 1, nodes_str,
	    self.state.timeDataSet, self.timeValue
	    #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )
	row_labels = \
	    core.GetRowLabel( self.cellRange[ 0 ], self.cellRange[ 2 ] )
        title2 = '"Axial; Rows=%s"' % ':'.join( row_labels )
      #end if-else

#		-- Write with axial mesh centers
#		--
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )
    #end if dset is not None and core is not None

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return			text or None
"""
    csv_text = None

    core = dset = None
    is_valid = self.dmgr.IsValid(
        self.curDataSet,
	axial_level = self.axialValue[ 1 ]
	#state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = np.array( dset )
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      node_addr = self.dmgr.GetNodeAddr( self.subAddr )
      item_label = 'Chan'  if self.channelMode else  'Pin'

      if self.mode == 'xz':
	pin_row = self.subAddr[ 1 ]
	if self.nodalMode:
          node_cells = ( 0, 1 ) if node_addr in ( 0, 1 ) else ( 2, 3 )
	  clip_data = np.zeros( 2, dtype = np.float64 )
	  for k in xrange( len( node_cells ) ):
	    clip_data[ k ] = \
	        dset_value[ 0, node_cells[ k ], axial_level, assy_ndx ]
	else:
	  clip_data = dset_value[ pin_row, :, axial_level, assy_ndx ]
	pin_title = '%s Row=%d' % (item_label, pin_row + 1)

      else:
	pin_col = self.subAddr[ 0 ]
	if self.nodalMode:
          node_cells = ( 0, 2 ) if node_addr in ( 0, 2 ) else ( 1, 3 )
	  clip_data = np.zeros( 2, dtype = np.float64 )
	  for k in xrange( len( node_cells ) ):
	    clip_data[ k ] = \
	        dset_value[ 0, node_cells[ k ], axial_level, assy_ndx ]
	else:
	  clip_data = dset_value[ :, pin_col, axial_level, assy_ndx ]
	pin_title = '%s Col=%d' % (item_label, pin_col + 1)

      nodes_str = ''
      if self.nodalMode:
	nodes_str = 'Nodes=%d,%d; ' % \
	    ( node_cells[ 0 ] + 1, node_cells[ 1 ] + 1 )

      title = '"%s: Assembly=%d %s; %s; %sAxial=%.3f; %s=%.3g"' % (
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  assy_ndx + 1,
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  pin_title, nodes_str, self.axialValue[ 0 ],
	  self.state.timeDataSet, self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per cm
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    dataRange
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
    +
    assemblyWidth
    axialLevelsDy	list of pixel offsets in y dimension
    axialLevelsDyMin
    axialPixPerCm	used?
    coreRegion
    lineWidth
    nodeWidth		if self.nodalMode
    pinWidth
    valueFont
    valueFontSize
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

    #axial_mesh = core.axialMesh
    axial_mesh = self.dmgr.GetAxialMesh( self.curDataSet )
    axial_range_cm = \
        axial_mesh[ self.cellRange[ 3 ] - 1 ] - \
	axial_mesh[ self.cellRange[ 1 ] ]
        #axial_mesh[ self.cellRange[ 3 ] ] -
    npin = core.npinx  if self.mode == 'xz' else  core.npiny

    # pin equivalents in the axial range
    cm_per_pin = core.GetAssemblyPitch() / npin
    axial_pin_equivs = axial_range_cm / cm_per_pin
    core_aspect_ratio = \
        core.GetAssemblyPitch() * self.cellRange[ -2 ] / \
	axial_range_cm

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

#			-- Determine drawable region in image
#			--
      # l2r, label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      # t2b, core : title
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)

      region_aspect_ratio = float( region_wd ) / float( region_ht )

#				-- Limited by height
      if region_aspect_ratio > core_aspect_ratio:
	pin_wd = max( 1, int( math.floor( region_ht / axial_pin_equivs ) ) )
	if self.nodalMode:
	  node_count = self.cellRange[ -2 ] << 1
	  node_wd = max( 1, int( math.floor( region_ht / node_count ) ) )

#				-- Limited by width
      else:
        assy_wd = region_wd / self.cellRange[ -2 ]
	if self.channelMode:
          pin_wd = max( 1, (assy_wd - 2) / (npin + 1) )
	else:
          pin_wd = max( 1, (assy_wd - 2) / npin )
	if self.nodalMode:
	  node_wd = max( 1, (assy_wd - 2) >> 1 )

      if self.nodalMode:
        assy_wd = (node_wd << 1) + 1
      elif self.channelMode:
        assy_wd = pin_wd * (npin + 1) + 1
      else:
        assy_wd = pin_wd * npin + 1

      axial_pix_per_cm = pin_wd / cm_per_pin

      if self.logger.isEnabledFor( logging.DEBUG ):
        if self.nodalMode:
          self.logger.debug(
	      'assy_wd=%d, node_wd=%d, pin_wd=%d, axial_pix_per_cm=%f',
	      assy_wd, node_wd, pin_wd, axial_pix_per_cm
	      )
        else:
          self.logger.debug(
	      'assy_wd=%d, pin_wd=%d, axial_pix_per_cm=%f',
	      assy_wd, pin_wd, axial_pix_per_cm
	      )

#			-- Calc sizes
#			--
      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

#		-- Or, scale set explicitly
#		--
    else:
      pin_wd = kwargs.get( 'scale', 4 )
      axial_pix_per_cm = pin_wd / cm_per_pin

      if len( axial_mesh ) > 1:
        if (axial_range_cm * axial_pix_per_cm) / (len( axial_mesh ) - 1) < 2.0:
	  axial_pix_per_cm = 2.0 * (len( axial_mesh) - 1) / axial_range_cm
	  pin_wd = int( math.ceil( axial_pix_per_cm * cm_per_pin ) )

      if self.nodalMode:
        node_wd = pin_wd << 2
        assy_wd = (node_wd << 1) + 1
      elif self.channelMode:
        assy_wd = pin_wd * (npin + 1) + 1
      else:
        assy_wd = pin_wd * npin + 1

      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

      font_size = self._CalcFontSize( 768 )

      # l2r, label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    axials_dy_min = sys.float_info.max
    axials_dy = []
    for ax in range( self.cellRange[ 3 ] - 2, self.cellRange[ 1 ] - 1, -1 ):
      ax_cm = axial_mesh[ ax + 1 ] - axial_mesh[ ax ]
      dy = max( 1, int( math.floor( axial_pix_per_cm * ax_cm ) ) )
      axials_dy.insert( 0, dy )
      axials_dy_min = min( axials_dy_min, dy )
    #end for

    value_font_size = assy_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    config[ 'assemblyWidth' ] = assy_wd
    config[ 'axialLevelsDy' ] = axials_dy
    config[ 'axialLevelsDyMin' ] = axials_dy_min
    config[ 'axialPixPerCm' ] = axial_pix_per_cm
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'pinWidth' ] = pin_wd
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size

    if self.nodalMode:
      config[ 'nodeWidth' ] = node_wd

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_col_or_row, pin_col_or_row )
@param  config		optional config to use instead of self.config
"""
    #start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    node_addr = self.dmgr.GetNodeAddr( self.subAddr )
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      assy_wd = config[ 'assemblyWidth' ]
      axial_levels_dy = config[ 'axialLevelsDy' ]
      axial_levels_dy_min = config[ 'axialLevelsDyMin' ]
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_wd = config[ 'pinWidth' ]

      if self.nodalMode:
        node_wd = config[ 'nodeWidth' ]

      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()
      pin_factors = None
      if self.state.weightsMode == 'on':
        pin_factors = self.dmgr.GetFactors( self.curDataSet )

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = np.array( dset )
        dset_shape = dset.shape

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      if self.mode == 'xz':
	if self.nodalMode:
          node_cells = ( 0, 1 ) if node_addr in ( 0, 1 ) else ( 2, 3 )
	  addresses = 'Assy Row %s, Nodes %d,%d' % ( 
	      core.GetRowLabel( tuple_in[ 1 ] ),
	      node_cells[ 0 ] + 1, node_cells[ 1 ] + 1
	      )
	else:
	  pin_cell = min( tuple_in[ 2 ], dset_shape[ 0 ] - 1 )
	  if self.channelMode:
	    cur_npin = min( core.npinx + 1, dset_shape[ 1 ] )
	    pin_range = xrange( core.npinx + 1 )
	    item_label = 'Chan'
	  else:
	    cur_npin = min( core.npinx, dset_shape[ 1 ] )
	    pin_range = xrange( core.npinx )
	    item_label = 'Pin'
	  addresses = 'Assy Row %s, %s Row %d' % \
	      ( core.GetRowLabel( tuple_in[ 1 ] ), item_label, pin_cell + 1 )

        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	    additional = addresses
	    )

      else: # 'yz'
	if self.nodalMode:
          node_cells = ( 0, 2 ) if node_addr in ( 0, 2 ) else ( 1, 3 )
	  addresses = 'Assy Col %s, Nodes %d,%d' % (
	      core.GetColLabel( tuple_in[ 1 ] ),
	      node_cells[ 0 ] + 1, node_cells[ 1 ] + 1
	      )
	else:
	  pin_cell = min( tuple_in[ 2 ], dset_shape[ 1 ] - 1 )
	  if self.channelMode:
	    cur_npin = min( core.npiny + 1, dset_shape[ 0 ] )
	    pin_range = range( core.npiny + 1 )
	    item_label = 'Chan'
	  else:
	    cur_npin = min( core.npiny, dset_shape[ 0 ] )
	    pin_range = range( core.npiny )
	    item_label = 'Pin'
	  addresses = 'Assy Col %s, %s Col %d' % \
	      ( core.GetColLabel( tuple_in[ 1 ] ), item_label, pin_cell + 1 )

        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	    additional = addresses
	    )
      #end if-else self.mode

      node_value_draw_list = []

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )
      node_pen = ( 100, 100, 100, 255 )

#			-- Loop on axial levels
#			--
      last_axial_label_y = 0;
      axial_y = core_region[ 1 ]
      for ax in range( len( axial_levels_dy ) - 1, -1, -1 ):
        cur_dy = axial_levels_dy[ ax ]
	axial_level = ax + self.cellRange[ 1 ]

#				-- Row label
#				--
	if self.showLabels:
	  label = '%02d' % (axial_level + 1)
	  label_size = pil_font.getsize( label )
	  label_y = axial_y + ((cur_dy - label_size[ 1 ]) >> 1)
	  if last_axial_label_y + label_size[ 1 ] < axial_y + cur_dy:
	    im_draw.text(
	        ( 1, label_y ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	    last_axial_label_y = label_y

#				-- Loop on col
#				--
	assy_x = core_region[ 0 ]
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if ax == len( axial_levels_dy ) - 1 and self.showLabels:
	    label_ndx = 0 if self.mode == 'xz' else 1
	    label = core.GetCoreLabel( label_ndx, assy_col )
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if

	  if self.mode == 'xz':
	    assy_ndx = core.coreMap[ tuple_in[ 1 ], assy_col ] - 1
	  else:
	    assy_ndx = core.coreMap[ assy_col, tuple_in[ 1 ] ] - 1

#					-- Assembly referenced?
#					--
	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    if self.nodalMode:
	      node_x = assy_x + 1

	      for node_ndx in node_cells:
	        value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
	        if pin_factors is None:
	          pin_factor = 1
	        else:
	          pin_factor = pin_factors[ 0, node_ndx, axial_level, assy_ndx ]

	        if not ( pin_factor == 0 or self.dmgr.IsBadValue( value ) ):
	          pen_color = Widget.GetColorTuple(
	              value - ds_range[ 0 ], value_delta, 255
	              )
	          brush_color = \
		      ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
	          im_draw.rectangle(
		      [ node_x, axial_y,
		        node_x + node_wd + 1, axial_y + cur_dy + 1 ],
		      fill = brush_color, outline = node_pen
		      #fill = brush_color, outline = pen_color
		      )
		  node_value_draw_list.append((
		      self._CreateValueString( value, 3 ),
                      Widget.GetContrastColor( *brush_color ),
                      node_x, axial_y, node_wd, cur_dy
		      ))
	        #end if valid value
	        node_x += node_wd
	      #end for node cells

	    else: # not self.nodalMode:
	      pin_x = assy_x + 1

	      for pin_col in pin_range:
	        cur_pin_col = min( pin_col, cur_npin - 1 )
	        if self.mode == 'xz':
	          value = \
		      dset_array[ pin_cell, cur_pin_col, axial_level, assy_ndx ]
	          if pin_factors is None:
	            pin_factor = 1
		  else:
	            pin_factor = \
		     pin_factors[ pin_cell, cur_pin_col, axial_level, assy_ndx ]
	        else:
	          value = \
		      dset_array[ cur_pin_col, pin_cell, axial_level, assy_ndx ]
	          if pin_factors is None:
	            pin_factor = 1
		  else:
	            pin_factor = \
		     pin_factors[ cur_pin_col, pin_cell, axial_level, assy_ndx ]

	        if not ( pin_factor == 0 or self.dmgr.IsBadValue( value ) ):
	          pen_color = Widget.GetColorTuple(
	              value - ds_range[ 0 ], value_delta, 255
	              )
	          brush_color = \
		      ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
	          im_draw.rectangle(
		      [ pin_x, axial_y,
		        pin_x + pin_wd + 1, axial_y + cur_dy + 1 ],
		      fill = brush_color, outline = pen_color
		      )
	        #end if valid value
	        pin_x += pin_wd
	      #end for pin cols
	    #end if-else self.nodalMode

	    im_draw.rectangle(
		[ assy_x, axial_y, assy_x + assy_wd, axial_y + cur_dy ],
		fill = None, outline = assy_pen
	        )
	  #end if assembly referenced

	  assy_x += assy_wd
	#end for assy_col

	axial_y += cur_dy
      #end for assy_row

#			-- Draw Values
#			--
      if node_value_draw_list:
        self._DrawValues( node_value_draw_list, im_draw )

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( core_region[ 0 ] + core_region[ 2 ] + 2 + font_size,
	      core_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      axial_y = max( axial_y, legend_size[ 1 ] )
      axial_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  time = self.timeValue
	  #time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
#(core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, axial_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists
    #elapsed_time = timeit.default_timer() - start_time
    #if self.logger.isEnabledFor( logging.DEBUG ):
      #self.logger.debug( 'time=%.3fs, im-None=%s', elapsed_time, im is None )

    return  im  if im is not None else  self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return  ( state_index, assy_col_or_row, pin_col_or_row )
"""
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyAddr[ 2 ], self.subAddr[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyAddr[ 1 ], self.subAddr[ 0 ] )
    return  t
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
			( assy_ndx, assy_col_or_row, axial_level,
			  pin_col_or_row, node_addr )
"""
    tip_str = ''
    valid = False
    if cell_info is not None:
      valid = self.dmgr.IsValid(
	  self.curDataSet,
          assembly_index = cell_info[ 0 ],
	  axial_level = cell_info[ 2 ]
          )

    dset = None
    if valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      assy_ndx = cell_info[ 0 ]
    if dset is not None and assy_ndx < dset.shape[ 3 ]:
      core = self.dmgr.GetCore()
      if self.mode == 'xz':
        assy_addr = ( cell_info[ 1 ], self.assemblyAddr[ 2 ] )
      else:
        assy_addr = ( self.assemblyAddr[ 1 ], cell_info[ 1 ] )

      show_assy_addr = core.CreateAssyLabel( *assy_addr )
      tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )

      if cell_info[ 2 ] >= 0:
	axial_value = self.dmgr.\
	    GetAxialValue( self.curDataSet, core_ndx = cell_info[ 2 ] )
	tip_str += ', Axial: %.2f' % axial_value[ 0 ]
      #end if cell_info[ 2 ] >= 0
    #end if dset is not None and assy_ndx < dset.shape[ 3 ]

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return  ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is not None and core.coreMap is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axials_dy = self.config[ 'axialLevelsDy' ]
      core_region = self.config[ 'coreRegion' ]
      node_addr = -1
      #pin_wd = self.config[ 'pinWidth' ]

      off_x = ev_x - core_region[ 0 ]
      off_y = ev_y - core_region[ 1 ]

      if self.mode == 'xz':
	assy_row = self.assemblyAddr[ 2 ]
        assy_col = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        assy_col = max( self.cellRange[ 0 ], assy_col )
	assy_col_or_row = assy_col

	pin_offset = off_x % assy_wd
	if self.nodalMode:
	  pin_col_or_row, node_addr = self._FindPinNodal( pin_offset )
	else:
	  pin_col_or_row = self._FindPinNonNodal( pin_offset )
	if pin_col_or_row >= core.npinx: pin_col_or_row = -1

      else:
        assy_col = self.assemblyAddr[ 1 ]
	assy_row = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	assy_row = max( self.cellRange[ 0 ], assy_row )
	assy_col_or_row = assy_row

	pin_offset = off_x % assy_wd
	if self.nodalMode:
	  pin_col_or_row, node_addr = self._FindPinNodal( pin_offset )
	else:
	  pin_col_or_row = self._FindPinNonNodal( pin_offset )
	if pin_col_or_row >= core.npiny: pin_col_or_row = -1
      #end if-else

      axial_level = 0
      ax_y = 0
      for ax in range( len( axials_dy ) - 1, -1, -1 ):
        ax_y += axials_dy[ ax ]
	if off_y <= ax_y:
	  axial_level = ax + self.cellRange[ 1 ]
	  break
      #end for

      assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
      result = \
          ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row, node_addr )
    #end if core is not None and core.coreMap is not None

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._FindPinNodal()			-
  #----------------------------------------------------------------------
  def _FindPinNodal( self, pin_offset ):
    """
@return  0-based pin_col_or_row, node_addr
"""
    pin_col_or_row = -1
    node_wd = self.config.get( 'nodeWidth', -1 )

    node_base_ndx = self.dmgr.GetNodeAddr( self.subAddr )
    node_col_or_row = min( 1, pin_offset / node_wd )  if node_wd > 0 else  0

    if self.mode == 'xz':
      node_pair = ( 0, 1 ) if node_base_ndx in ( 0, 1 ) else ( 2, 3 )
      node_addr = node_pair[ node_col_or_row ]
      sub_addr = self.dmgr.GetSubAddrFromNode( node_addr )
      pin_col_or_row = sub_addr[ 0 ]

    else:
      node_pair = ( 0, 2 ) if node_base_ndx in ( 0, 2 ) else ( 1, 3 )
      node_addr = node_pair[ node_col_or_row ]
      sub_addr = self.dmgr.GetSubAddrFromNode( node_addr )
      pin_col_or_row = sub_addr[ 1 ]

    return  pin_col_or_row, node_addr
  #end _FindPinNodal


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._FindPinNonNodal()		-
  #----------------------------------------------------------------------
  def _FindPinNonNodal( self, pin_offset ):
    """
@return  0-based pin_col_or_row
"""
    pin_wd = self.config[ 'pinWidth' ]
    return  pin_offset / pin_wd
  #end _FindPinNonNodal


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'channel', 'pin', ':assembly', ':node' ]
    #return  [ 'pin', ':assembly', ':node' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetEventLockSet()		-
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
  #	METHOD:		CoreAxial2DView.GetInitialCellRange()		-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """Creates the range using y for the axial.
@return			( xy-left, z-bottom, xy-right+1, z-top+1, d-xy, dz )
"""
    core = None
    if self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is None:
      result = ( 0, 0, 0, 0, 0, 0 )

    else:
      result = list( self.dmgr.ExtractSymmetryExtent() )
      if self.mode == 'yz':
        result[ 0 ] = result[ 1 ]
	result[ 2 ] = result[ 3 ]
	result[ 4 ] = result[ 5 ]

      result[ 1 ] = 0
      #result[ 3 ] = result[ 5 ] = core.nax
      mesh = self.dmgr.GetAxialMesh( self.curDataSet )
      result[ 3 ] = result[ 5 ] = len( mesh )

    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetMode()			-
  #----------------------------------------------------------------------
  def GetMode( self ):
    """
"""
    return  self.mode
  #end GetMode


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		8
"""
    return  4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self ):
    """
"""
    return  self.toolButtonDefs
  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core Axial 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    #return  bmap
    result = bmap

    core = self.dmgr.GetCore()
    if self.config is not None and core is not None:
      line_wd = -1
      rect = None

      rel_axial = self.axialValue[ 1 ] - self.cellRange[ 1 ]

      if self.mode == 'xz':
        rel_cell = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
      else:
        rel_cell = self.assemblyAddr[ 2 ] - self.cellRange[ 0 ]

      if rel_cell >= 0 and rel_cell < self.cellRange[ -2 ] and \
          rel_axial >= 0 and rel_axial < self.cellRange[ -1 ]:
        assy_wd = self.config[ 'assemblyWidth' ]
        axial_levels_dy = self.config[ 'axialLevelsDy' ]
	core_region = self.config[ 'coreRegion' ]
	line_wd = self.config[ 'lineWidth' ]
        #pin_wd = self.config[ 'pinWidth' ]

        axial_y = core_region[ 1 ]
        for ax in range( len( axial_levels_dy ) - 1, rel_axial, -1 ):
	  axial_y += axial_levels_dy[ ax ]

	rect = [
	    rel_cell * assy_wd + core_region[ 0 ], axial_y,
	    assy_wd, axial_levels_dy[ rel_axial ]
	    ]
      #end if selection w/in image

#			-- Draw?
#			--
      if rect is not None:
	new_bmap = self._CopyBitmap( bmap )

        dc = wx.MemoryDC( new_bmap )
	gc = wx.GraphicsContext.Create( dc )
	gc.SetPen(
	    wx.ThePenList.FindOrCreatePen(
	        wx.Colour( 255, 0, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
		)
	    )
	path = gc.CreatePath()
	path.AddRectangle( *rect )
	gc.StrokePath( path )

	dc.SelectObject( wx.NullBitmap )
	result = new_bmap
      #end if rect
    #end if self.config

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyAddr[ 2 ], self.subAddr[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyAddr[ 1 ], self.subAddr[ 0 ] )
    return  tpl == t
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    #self.avgValues.clear()
    self.assemblyAddr = self.state.assemblyAddr
    self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )
    self.subAddr = self.state.subAddr

    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'subAddr' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    for p, m in ( ( 'mode', 'SetMode' ), ):
      if p in props_dict:
        method = getattr( self, m )
	method( props_dict[ p ] )

    super( CoreAxial2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindCell( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}

      if self.mode == 'xz':
	assy_ndx = ( cell_info[ 0 ], cell_info[ 1 ], self.assemblyAddr[ 2 ] )
	pin_addr = ( cell_info[ 3 ], self.subAddr[ 1 ] )
      else:
	assy_ndx = ( cell_info[ 0 ], self.assemblyAddr[ 1 ], cell_info[ 1 ] )
	pin_addr = ( self.subAddr[ 0 ], cell_info[ 3 ] )

      if assy_ndx != self.assemblyAddr:
	state_args[ 'assembly_addr' ] = assy_ndx

      node_addr = cell_info[ 4 ]
      if node_addr != self.nodeAddr:
	state_args[ 'node_addr' ] = node_addr

      if pin_addr != self.subAddr:
	state_args[ 'sub_addr' ] = pin_addr

      axial_level = cell_info[ 2 ]
      axial_value = \
          self.dmgr.GetAxialValue( self.curDataSet, core_ndx = axial_level )
      if axial_value[ 0 ] != self.axialValue[ 0 ]:
        state_args[ 'axial_value' ] = axial_value

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    if self.curDataSet:
      if self.channelMode:
        self._OnFindMinMaxChannel( mode, self.curDataSet, all_states_flag )
      else:
        self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnMode()			-
  #----------------------------------------------------------------------
  def _OnMode( self, ev ):
    """Must be called from the event thread.
"""
    new_mode = 'xz' if self.mode == 'yz' else 'yz'
    button = ev.GetEventObject()
    self.SetMode( new_mode, button )
  #end _OnMode


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self.Redraw()
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( CoreAxial2DView, self ).SaveProps( props_dict )

    for k in ( 'assemblyAddr', 'mode', 'subAddr' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.SetMode()			-
  #----------------------------------------------------------------------
  def SetMode( self, mode, button = None ):
    """May be called from any thread.
@param  mode		either 'xz' or 'yz', defaulting to the former on
			any other value
@param  button		optional button to update
"""
    if mode != self.mode:
      self.mode = 'yz' if mode == 'yz' else 'xz'
      self.cellRange = list( self.GetInitialCellRange() )
      del self.cellRangeStack[ : ]

      wx.CallAfter( self._SetModeImpl, button )
  #end SetMode


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._SetModeImpl()			-
  #----------------------------------------------------------------------
  def _SetModeImpl( self, button = None ):
    """Must be called from the event thread.
@param  mode		mode, already setjdd
			any other value
@param  button		optional button to update
"""
    if button is None:
      for ch in self.GetParent().GetControlPanel().GetChildren():
        if isinstance( ch, wx.BitmapButton ) and \
	    ch.GetToolTip().GetTip().find( 'Toggle Slice Axis' ) >= 0:
          button = ch
	  break
    #end if

    if button is not None:
      if self.mode == 'yz':
        bmap = Widget.GetBitmap( 'Y_16x16' )
      else:
        bmap = Widget.GetBitmap( 'X_16x16' )
      button.SetBitmapLabel( bmap )
      button.Update()
      self.GetParent().GetControlPanel().Layout()
    #end if

    self.Redraw()
  #end _SetModeImpl


#   #----------------------------------------------------------------------
#   #	METHOD:		CoreAxial2DView._UpdateAvgValues()		-
#   #----------------------------------------------------------------------
#   def _UpdateAvgValues( self, state_ndx, force = False ):
#     dset = None
#     if self.avgDataSet is not None and \
#         (force or (state_ndx not in self.avgValues)):
#       dset = self.data.GetStateDataSet( state_ndx, self.avgDataSet )
# 
#     if dset is not None:
#       dset_array = dset.value
#       dset_shape = dset_array.shape
# 
# #			-- Axial
#       #if dset_shape[ 0 ] == 1 and dset_shape[ 3 ] == 1
#       if dset_shape[ 3 ] == 1:
#         t_nax = min( self.data.core.nax, dset_shape[ 2 ] )
#         avg_values = np.zeros( shape = ( t_nax, ) )
# 	for ax in range( t_nax ):
# 	  avg_values[ ax ] = np.mean( dset_array[ :, :, ax, : ] )
# 
# #			-- Assembly
#       else:
#         t_nax = min( self.data.core.nax, dset_shape[ 2 ] )
#         t_nass = min( self.data.core.nass, dset_shape[ 3 ] )
# 	for ax in range( t_nax ):
# 	  for assy in range( t_nass ):
# 	    avg_values[ ax, assy ] = np.mean( dset_array[ :, :, ax, assy ] )
# 
#       self.avgValues[ state_ndx ] = avg_values
#     #end if
#   #end _UpdateAvgValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._UpdateDataSetStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type ):
    """
@param  ds_type		dataset category/type
Updates the nodalMode property.
"""
    self.cellRange = list( self.GetInitialCellRange() )
    del self.cellRangeStack[ : ]

    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( CoreAxial2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    core = self.dmgr.GetCore()

    new_pin_index_flag = False
    if self.mode == 'xz':
      assy_ndx = 2  # row
      pin_ndx = 1  # row
      npin = core.npiny  if core is not None else  0
    else:
      assy_ndx = 1  # col
      pin_ndx = 0  # col
      npin = core.npinx  if core is not None else  0

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      if kwargs[ 'assembly_addr' ][ assy_ndx ] != self.assemblyAddr[ assy_ndx ]:
        resized = True
	new_pin_index_flag = True
      else:
        changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

#    if 'avg_dataset' in kwargs and kwargs[ 'avg_dataset' ] != self.avgDataSet:
#      changed = True
#      self.avgDataSet = kwargs[ 'avg_dataset' ]
#      if self.avgDataSet == '':
#        self.avgDataSet = None
#      self.avgValues.clear()

# Now handled in RasterWidget
#    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.pinDataSet:
#      ds_type = self.data.GetDataSetType( kwargs[ 'cur_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#	self.nodalMode = self.data.IsNodalType( ds_type )
#        self.pinDataSet = kwargs[ 'cur_dataset' ]
#        #self.avgValues.clear()
#	self.container.GetDataSetMenu().Reset()

    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] != self.subAddr:
      if kwargs[ 'sub_addr' ][ pin_ndx ] != self.subAddr[ pin_ndx ]:
        resized = True
      else:
        changed = True
      self.subAddr = self.dmgr.NormalizeSubAddr( kwargs[ 'sub_addr' ], 'pin' )

#x    if new_pin_index_flag:
#x      self.pinOffset = \
#x          self.assemblyAddr[ assy_ndx ] * npin + self.subAddr[ pin_ndx ]
#x    #end if new_pin_index_flag

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

#    if (changed or resized) and self.config is not None:
#      self._UpdateAvgValues( self.stateIndex )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end CoreAxial2DView


#------------------------------------------------------------------------
#	CLASS:		CoreXZView					-
#------------------------------------------------------------------------
class CoreXZView( CoreAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( CoreXZView, self ).__init__( container, id, mode = 'xz' )
  #end __init__
#end CoreXZView


#------------------------------------------------------------------------
#	CLASS:		CoreYZView					-
#------------------------------------------------------------------------
class CoreYZView( CoreAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( CoreYZView, self ).__init__( container, id, mode = 'yz' )
  #end __init__
#end CoreYZView
