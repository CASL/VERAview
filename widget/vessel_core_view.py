#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		vessel_core_view.py				-
#	HISTORY:							-
#		2017-02-27	leerw@ornl.gov				-
#	  To scale.
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
from data.utils import *
from event.state import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		VesselCore2DView				-
#------------------------------------------------------------------------
class VesselCore2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.avgDataSet = None
    #self.avgValues = {}
    self.channelMode = False

    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    self.vesselFlag = True
			# -- offsets in cm to edge given current cellRange
    self.vesselOffset = [ 0, 0 ]

    super( VesselCore2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._CreateClipboardData()		-
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
  #	METHOD:	VesselCore2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None

    core = None
    dset = None
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
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      clip_shape = (
	  dset_shape[ 0 ] * self.cellRange[ -1 ],
          dset_shape[ 1 ] * self.cellRange[ -2 ]
	  )
      clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      clip_data.fill( 0.0 )

      pin_row = 0
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
	#pin_row_to = pin_row + self.core.npiny
	pin_row_to = pin_row + dset_shape[ 0 ]

	pin_col = 0
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  #pin_col_to = pin_col + self.core.npinx
	  pin_col_to = pin_col + dset_shape[ 1 ]

          assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
	  if assy_ndx >= 0:
	    clip_data[ pin_row : pin_row_to, pin_col : pin_col_to ] = \
	        dset_value[ :, :, axial_level, assy_ndx ]

	  pin_col = pin_col_to
	#end for assy cols

	pin_row = pin_row_to
      #end for assy rows

      title1 = '"%s: Axial=%.3f; %s=%.3g"' % (
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      col_labels = core.GetColLabel( self.cellRange[ 0 ], self.cellRange[ 2 ] )
      row_labels = core.GetRowLabel( self.cellRange[ 1 ], self.cellRange[ 3 ] )
      title2 = '"Cols=%s; Rows=%s"' % (
	  ':'.join( col_labels ),
	  ':'.join( row_labels )
          )
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return			text or None
"""
    csv_text = None

    core = None
    dset = None
    is_valid = self.dmgr.IsValid(
        self.curDataSet,
        assembly_addr = self.assemblyAddr[ 0 ],
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

      #clip_shape = ( dset_shape[ 0 ], dset_shape[ 1 ] )
      #clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      #clip_data.fill( 0.0 )
      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%s; Axial=%.3f; %s=%.3g"' % (
	  #self.curDataSet.displayName,
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
The technique is to determine the number of pixels per pin, with a minimum
of 1, meaning a forced scale might be necessary.
@param  kwargs
    scale	pixels per pin
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
    coreRegion
    imageSize
    lineWidth
    pinWidth		used for pin or node width, depending on self.nodalMode
    pixPerCm
    valueFont
    valueFontSize
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

    core = self.dmgr.GetCore()
    vessel_tally = core.vesselTallyMesh

#		-- We want an integral number of pixels per pin
#		--
    npin = max( core.npinx, core.npiny )

    if self.nodalMode:
      cm_per_pin = core.apitch / 2.0
      #cm_per_pin_x = core.apitch / 2.0
      #cm_per_pin_y = core.apitch / 2.0
    elif self.channelMode:
      cm_per_pin = float( core.apitch ) / (npin + 1)
      #cm_per_pin_x = float( core.apitch ) / (core.npinx + 1)
      #cm_per_pin_y = float( core.apitch ) / (core.npiny + 1)
    else:
      cm_per_pin = float( core.apitch ) / npin
      #cm_per_pin_x = float( core.apitch ) / core.npinx
      #cm_per_pin_y = float( core.apitch ) / core.npiny

    vessel_wd_cm = self.cellRange[ -2 ] * core.apitch
    vessel_ht_cm = self.cellRange[ -1 ] * core.apitch

    if vessel_tally is not None:
      vessel_wd_cm = max( vessel_wd_cm, vessel_tally.r[ -1 ] )
      vessel_ht_cm = max( vessel_ht_cm, vessel_tally.r[ -1 ] )

    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)

      pix_per_cm_x = float( region_wd ) / vessel_wd_cm
      pix_per_cm_y = float( region_ht ) / vessel_ht_cm
      pix_per_pin = math.floor( min( pix_per_cm_x, pix_per_cm_y ) * cm_per_pin )
      pix_per_pin = max( 1, int( pix_per_pin ) )

    else:
      pix_per_pin = int( kwargs[ 'scale' ] ) if 'scale' in kwargs else 4
      font_size = self._CalcFontSize( 768 )

    pix_per_cm = pix_per_pin / cm_per_pin

    if self.nodalMode:
      pin_wd = int( pix_per_pin ) << 4
      assy_wd = pin_wd << 1
    elif self.channelMode:
      pin_wd = pix_per_pin
      assy_wd = pin_wd * (npin + 1)
    else:
      pin_wd = pix_per_pin
      assy_wd = pin_wd * npin

    region_wd = int( math.ceil( vessel_wd_cm * pix_per_cm ) )
    region_ht = int( math.ceil( vessel_ht_cm * pix_per_cm ) )

    image_wd = \
        label_size[ 0 ] + 2 + region_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = max(
        label_size[ 1 ] + 2 + region_ht + (font_size << 1),
	legend_size[ 1 ]
	)

    value_font_size = assy_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    config[ 'assemblyWidth' ] = assy_wd
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, region_wd, region_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'pinWidth' ] = pin_wd
    config[ 'pixPerCm' ] = pix_per_cm
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level )
"""
    #start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    core = dset = None
    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

      #vessel_tally_group = \
          #self.dmgr.GetVesselTallyData( self.curDataSet, self.timeValue )

    if dset is not None and core is not None:
      if 'coreRegion' not in config:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'coreRegion missing from config, reconfiguring' )
	if 'clientSize' in config:
          config = self._CreateDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateDrawConfig( scale = config[ 'scale' ] )

      assy_wd = config[ 'assemblyWidth' ]
      #im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_wd = config[ 'pinWidth' ]
      pix_per_cm = config[ 'pixPerCm' ]
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]

      vessel_tally_mesh = core.vesselTallyMesh

#		-- "Item" refers to channel or pin
      item_factors = None
      if self.state.weightsMode == 'on':
        item_factors = self.dmgr.GetFactors( self.curDataSet )

      dset_array = np.array( dset )
      dset_shape = dset.shape
      if self.nodalMode:
        cur_nxpin = cur_nypin = item_col_limit = item_row_limit = 2
      else:
        if self.channelMode:
	  item_col_limit = core.npinx + 1
	  item_row_limit = core.npiny + 1
        else:
	  item_col_limit = core.npinx
	  item_row_limit = core.npiny
	cur_nxpin = min( item_col_limit, dset_shape[ 1 ] )
	cur_nypin = min( item_row_limit, dset_shape[ 0 ] )
      #end if-else self.nodalMode

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  axial_ndx = 2
	  )

      draw_value_flag = \
          self.curDataSet is not None and \
	  dset_shape[ 0 ] == 1 and dset_shape[ 1 ] == 1
          #value_font is not None
      node_value_draw_list = []
      assy_value_draw_list = []

#			-- Limit axial level
#			--
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )
      node_pen = ( 100, 100, 100, 255 )

#			-- Loop on assembly rows
#			--
      assy_y = core_region[ 1 ]
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels:
	  label = core.GetRowLabel( assy_row )
	  label_size = pil_font.getsize( label )
	  label_y = assy_y + ((assy_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )
#				-- Loop on col
#				--
	assy_x = core_region[ 0 ]
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  brush_color = None
#					-- Column label
#					--
	  if assy_row == self.cellRange[ 1 ] and self.showLabels:
	    label = core.GetColLabel( assy_col )
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    #item_y = assy_y + 1
	    item_y = assy_y

#						-- Loop on chan/pin rows
	    node_ndx = 0
	    for item_row in xrange( item_row_limit ):
	      #item_x = assy_x + 1
	      item_x = assy_x
#							-- Loop on chan/pin cols
	      cur_item_row = min( item_row, cur_nypin - 1 )
	      if cur_item_row >= 0:
	        for item_col in range( item_col_limit ):
	          cur_item_col = min( item_col, cur_nxpin - 1 )
#-- Resolve value, apply pin factors
		  value = 0.0
		  item_factor = 0
	          if dset_array is None:
	            self.logger.critical( '** B.2 dset_array is None, how did this happen **' )
		  if cur_item_col >= 0:
		    if self.nodalMode:
		      value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
		      if item_factors is None:
		        item_factor = 1
		      else:
	                item_factor = \
		            item_factors[ 0, node_ndx, axial_level, assy_ndx ]
		      node_ndx += 1
		    else:
		      value = dset_array[
		          cur_item_row, cur_item_col, axial_level, assy_ndx
		          ]
	              if item_factors is None:
	                item_factor = 1
		      else:
	                item_factor = item_factors[
		            cur_item_row, cur_item_col, axial_level, assy_ndx
		            ]
		    #end if-else self.nodalMode
		  #end if cur_item_col

#-- Check value and pin_factor
#--
	          if not ( item_factor == 0 or self.dmgr.IsBadValue( value ) ):
	            pen_color = Widget.GetColorTuple(
	                value - ds_range[ 0 ], value_delta, 255
	                )
	            brush_color = \
		        ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
		    #im_draw.ellipse
	            im_draw.rectangle(
		        [ item_x, item_y, item_x + pin_wd, item_y + pin_wd ],
		        fill = brush_color, outline = pen_color
		        )

		    if self.nodalMode:
	              im_draw.rectangle(
		          [ item_x, item_y, item_x + pin_wd, item_y + pin_wd ],
		          fill = None, outline = node_pen
		          )
		      node_value_draw_list.append((
			  self._CreateValueString( value, 3 ),
                          Widget.GetContrastColor( *brush_color ),
			  item_x, item_y, pin_wd, pin_wd
		          ))
		    #end if nodalMode
	          #end if good value, not hidden by pin_factor

	          item_x += pin_wd
	        #end for item_col
	      #end if cur_item_row >= 0

	      item_y += pin_wd
	    #end for item_row

#	    im_draw.rectangle(
#		[ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
#		fill = None, outline = assy_pen
#	        )
#-- Draw value for cross-pin integration derived datasets
#--
	    if dset_array is None:
	      self.logger.critical( '** B.3 dset_array is None, how did this happen **' )
	    if draw_value_flag and brush_color is not None:
	      value = dset_array[ 0, 0, axial_level, assy_ndx ]
	      assy_value_draw_list.append((
	          self._CreateValueString( value, 3 ),
                  Widget.GetContrastColor( *brush_color ),
		  assy_x, assy_y, assy_wd, assy_wd
	          ))
	    #end if draw_value_flag
	  #end if assembly referenced
	  else:  # if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    im_draw.rectangle(
		[ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
		fill = None, outline = assy_pen
	        )

	  assy_x += assy_wd
	#end for assy_col

        assy_y += assy_wd
      #end for assy_row

#			-- Draw Values
#			--
      if node_value_draw_list:
        self._DrawValues( node_value_draw_list, im_draw )

      if assy_value_draw_list:
        self._DrawValues( assy_value_draw_list, im_draw )

      if vessel_tally_mesh is not None:
	# barrel ring
	bottom_col, bottom_row = \
	    core.FindBottomRightAssemblyCell( self.cellRange )
	w = bottom_col - self.cellRange[ 0 ] + 0.5
	h = bottom_row - self.cellRange[ 1 ] + 0.5
	barrel_r = int( math.ceil( assy_wd * math.sqrt( (w * w) + (h * h) ) ) )

#        bottom_col, right_row = core.FindCornerAssemblyAddrs( self.cellRange )
#	d1 = right_row - self.cellRange[ 1 ] + 1
#	d2 = bottom_col - self.cellRange[ 0 ] + 1
#	if d1 > d2:
#	  w = self.cellRange[ -2 ]
#	  r = int( math.ceil( assy_wd * math.sqrt( (w * w) + (d1 * d1) ) ) )
#	else:
#	  h = self.cellRange[ -1 ]
#	  r = int( math.ceil( assy_wd * math.sqrt( (d2 * d2) + (h * h) ) ) )
#	barrel_r = r

	barrel_ring_rect = [
	    core_region[ 0 ] - barrel_r, core_region[ 1 ] - barrel_r,
	    core_region[ 0 ] + barrel_r, core_region[ 1 ] + barrel_r,
	    ]
        im_draw.arc(
	    barrel_ring_rect,
	    0, 90, ( 0, 0, 200, 255 )
	    )

	# vessel ring
	vessel_ring_rect = [
	    core_region[ 0 ] - core_region[ 2 ],
	    core_region[ 1 ] - core_region[ 3 ],
	    core_region[ 0 ] + core_region[ 2 ],
	    core_region[ 1 ] + core_region[ 3 ]
	    ]
        im_draw.arc(
	    vessel_ring_rect,
	    0, 90, ( 0, 0, 200, 255 )
	    )

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
      #assy_y = max( assy_y, legend_size[ 1 ] )
      assy_y = max( core_region[ 1 ] + core_region[ 3 ], legend_size[ 1 ] )
      assy_y += font_size >> 1

      title_str = self._CreateTitleString(
	  title_templ,
	  axial = axial_value[ 0 ],
	  time = self.timeValue
	  #time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
#0,
#(core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, assy_y ),
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
  #	METHOD:		VesselCore2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			mode == 'assy':
			( state_index, assy_ndx, axial_level,
			  assy_col, assy_row )
			mode == 'core':
			( state_index, axial_level )
"""
    return  self.stateIndex, self.axialValue[ 1 ]
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    if cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      #if dset is not None and assy_ndx < dset.shape[ 3 ]:
      if dset is not None:
        core = self.dmgr.GetCore()
        assy_ndx = min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
        axial_level = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 ),
        assy_addr_display = core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
	value = None

	if self.nodalMode:
	  node_addr = cell_info[ 5 ]  if len( cell_info ) > 5 else  -1
	  if self.dmgr.IsValid( self.curDataSet, node_addr = node_addr ):
	    tip_str = 'Assy: %s, Node %d' % \
	        ( assy_addr_display, node_addr + 1 )
	    value = dset[ 0, node_addr, axial_level, assy_ndx ]
	else:
          tip_str = 'Assy: %s' % assy_addr_display
	  if dset.shape[ 0 ] == 1 or dset.shape[ 1 ] == 1:
	    value = dset[ 0, 0, axial_level, assy_ndx ]
	#end if self.nodalMode

	if not self.dmgr.IsBadValue( value ):
	  tip_str += ': %g' % value
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row,
			  pin_col, pin_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is not None and core.coreMap is not None:
      if ev_x >= 0 and ev_y >= 0:
	assy_wd = self.config[ 'assemblyWidth' ]
	core_region = self.config[ 'coreRegion' ]
	off_x = ev_x - core_region[ 0 ]
	off_y = ev_y - core_region[ 1 ]
        cell_x = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
	    int( off_y / assy_wd ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	cell_y = max( self.cellRange[ 1 ], cell_y )

	assy_ndx = core.coreMap[ cell_y, cell_x ] - 1

	pin_wd = self.config[ 'pinWidth' ]
	if self.nodalMode:
	  node_col = int( (off_x % assy_wd) / pin_wd )
	  node_row = int( (off_y % assy_wd) / pin_wd )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  pin_col, pin_row = self.dmgr.GetSubAddrFromNode(
	      node_addr,
	      'channel' if self.channelMode else 'pin'
	      )
	else:
	  pin_col = int( (off_x % assy_wd) / pin_wd )
	  if pin_col >= core.npinx: pin_col = -1
	  pin_row = int( (off_y % assy_wd) / pin_wd )
	  if pin_row >= core.npiny: pin_row = -1
	  node_addr = self.dmgr.GetNodeAddr(
	      ( pin_col, pin_row ),
	      'channel' if self.channelMode else 'pin'
	      )

	result = ( assy_ndx, cell_x, cell_y, pin_col, pin_row, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindAssembly().
"""
    return  self.FindAssembly( ev_x, ev_y )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [
	'channel', 'pin',
	':assembly', ':chan_radial', ':node',
	':radial', ':radial_assembly', ':radial_node'
	]
#        'pin', ':assembly', ':node',
#	':radial', ':radial_assembly', ':radial_node'
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.GetEventLockSet()		-
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
  #	METHOD:		VesselCore2DView.GetPrintScale()		-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		4
"""
    return  4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Vessel Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._HiliteBitmap()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    core = self.dmgr.GetCore()
    if self.config is not None and core is not None:
      line_wd = self.config[ 'lineWidth' ]
      half_line_wd = line_wd >> 1
      draw_list = []  # ( rect, pen )

      if self.nodalMode:
        node_addr_list = list( self.auxNodeAddrs )
        #node_addr_list.insert( 0, self.nodeAddr )
        node_addr_list.append( self.nodeAddr )
        select_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 255, 255, 255, 255 ),
	    half_line_wd, wx.PENSTYLE_SOLID
	    )
        primary_pen = wx.ThePenList.FindOrCreatePen(
#	    wx.Colour( 255, 255, 255, 255 ),
	    wx.Colour( 255, 0, 0, 255 ),
	    #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
	    line_wd, wx.PENSTYLE_SOLID
	    )
        secondary_pen = wx.ThePenList.FindOrCreatePen(
	    wx.Colour( 255, 255, 0, 255 ),
	    #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
	    line_wd, wx.PENSTYLE_SOLID
	    )
      else:
        select_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 255, 0, 0, 255 ),
	    line_wd, wx.PENSTYLE_SOLID
	    )
      #end if-else self.nodalMode

#			-- Core mode
#			--
      rel_col = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
      rel_row = self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	assy_wd = self.config[ 'assemblyWidth' ]
	core_region = self.config[ 'coreRegion' ]

	rect = [
	    rel_col * assy_wd + core_region[ 0 ],
	    rel_row * assy_wd + core_region[ 1 ],
	    assy_wd, assy_wd
	    ]
	draw_list.append( ( rect, select_pen ) )

#				-- Core nodal
	if self.nodalMode:
	  node_wd = self.config[ 'pinWidth' ]
          for i in range( len( node_addr_list ) ):
	    node_addr = node_addr_list[ i ]
	    if node_addr >= 0:
	      rel_x = node_wd if node_addr in ( 1, 3 ) else half_line_wd
	      rel_y = node_wd if node_addr in ( 2, 3 ) else half_line_wd
	      node_rect = [
	          rect[ 0 ] + rel_x, rect[ 1 ] + rel_y,
		  node_wd - half_line_wd, node_wd - half_line_wd
		  ]
	      pen = \
	          secondary_pen if i < len( node_addr_list ) - 1 else \
		  primary_pen
	      draw_list.append( ( node_rect, pen ) )
	    #end if valid node addr
          #end for i
	#end if nodalMode
      #end if cell in drawing range

#			-- Draw?
#			--
      if draw_list:
	new_bmap = self._CopyBitmap( bmap )

        dc = wx.MemoryDC( new_bmap )
	gc = wx.GraphicsContext.Create( dc )

	for draw_item in draw_list:
	  gc.SetPen( draw_item[ 1 ] )
	  path = gc.CreatePath()
	  path.AddRectangle( *draw_item[ 0 ] )
	  gc.StrokePath( path )
	#end for draw_item

	dc.SelectObject( wx.NullBitmap )
	result = new_bmap
      #end if draw_list
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._InitEventHandlers()		-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    #self._SetMode( 'core' )

    self.bitmapCtrl.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    #self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnLeftDown )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnLeftUp )
    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotion )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = \
        tpl is not None and len( tpl ) >= 2 and \
        tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.axialValue[ 1 ]

    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    #self.avgValues.clear()
    self.assemblyAddr = self.state.assemblyAddr
    self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )
    self.subAddr = self.state.subAddr

    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    #no self.channelMode = ds_type == 'channel'
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( VesselCore2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindAssembly( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_addr = cell_info[ 0 : 3 ]
      if assy_addr != self.assemblyAddr:
	state_args[ 'assembly_addr' ] = assy_addr

      if self.nodalMode:
        node_addr = cell_info[ 5 ]
        is_aux = self.IsAuxiliaryEvent( ev )
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
	elif ev.GetClickCount() > 1:
	  sub_addr = self.dmgr.GetSubAddrFromNode(
	      node_addr,
	      'channel' if self.channelMode else 'pin'
	      )
	  if sub_addr != self.subAddr:
	    state_args[ 'sub_addr' ] = sub_addr
	#end if-elif is_aux

      #if ev.GetClickCount() > 1:
      elif ev.GetClickCount() > 1:
        pin_addr = cell_info[ 3 : 5 ]
        if pin_addr != self.subAddr:
	  state_args[ 'sub_addr' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._OnDragFinished()		-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    pass
#    if right - left == 1 and bottom - top == 1:
#      self.assemblyAddr = self.dragStartCell
#      self._SetMode( 'assy' )
#      self.FireStateChange( assembly_addr = self.assemblyAddr )
#    else:
#      self._SetMode( 'core' )
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._OnFindMinMax()		-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    #if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
    if self.curDataSet:
      if self.channelMode:
        self._OnFindMinMaxChannel( mode, self.curDataSet, all_states_flag )
      else:
        self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      #self._SetMode( 'core' )
      self.Redraw()  # self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( VesselCore2DView, self ).SaveProps( props_dict )

    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._UpdateDataSetStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type ):
    """
@param  ds_type		dataset category/type
Updates the nodalMode property.
"""
    #no self.channelMode = ds_type == 'channel'
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #	METHOD:		VesselCore2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( VesselCore2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.dmgr.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
        changed = True
	self.auxNodeAddrs = aux_node_addrs

# Now handled in RasterWidget
#    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
#      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#	self.nodalMode = self.dmgr.IsNodalType( ds_type )
#        self.curDataSet = kwargs[ 'cur_dataset' ]
#	self._UpdateAxialValue()
#	self.container.GetDataSetMenu().Reset()

    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        changed = True
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr(
          kwargs[ 'sub_addr' ],
	  'channel' if self.channelMode else 'pin'
	  )
      if sub_addr != self.subAddr:
        changed = True
        self.subAddr = sub_addr
    #end if 'sub_addr'

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end VesselCore2DView
