#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		subpin_view.py					-
#	HISTORY:							-
#		2017-06-12	leerw@ornl.gov				-
#	  Dual-moded.
#		2017-05-31	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, random, sys
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
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.utils import DataUtils
from event.state import *
from raster_widget import *
from widget import *


MIN_PIN_CIRCLE_R = 1
MIN_RADIUS_R = 4


#------------------------------------------------------------------------
#	CLASS:		SubPin2DView					-
#------------------------------------------------------------------------
class SubPin2DView( RasterWidget ):
  """Experimenting with pin-by-pin assembly view across axials and exposure
times or states.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    self.mode = 'r'  # 'r', 'theta'
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    super( SubPin2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardDisplayedData() if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the current assembly selection.
@return			text or None
"""
    csv_text = None
    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the current pin selection(s).
@return			text or None
"""
    csv_text = None
    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Calls _CreateRConfig() or _CreateThetaConfig().
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys needed by _CreateRasterImage().
"""
#    dset = self.data.GetStateDataSet( 0, self.pinDataSet )
#    if dset is not None and dset.shape[ 0 ] == 1 and dset.shape[ 1 ] == 4:
#      kwargs[ 'nodal' ] = True
    return \
	self._CreateThetaConfig( **kwargs ) if self.mode == 'theta' else \
	self._CreateRConfig( **kwargs )
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateRConfig()			-
  #----------------------------------------------------------------------
  def _CreateRConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
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
    assemblyRegion
    imageSize
    lineWidth
    pinGap
    pinWidth
    xaxis
    xaxisFactor
    yaxisFactor
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

#		-- Get these from the DataModel
#		--
    nx = core.nsubr
    xaxis = core.subPinR
    min_pin_wd = max( core.nsubax, nx )

    if len( xaxis ) == 1:
      xaxis = [ xaxis[ 0 ], xaxis[ 0 ] + 0.1 ]
    elif len( xaxis ) == 0:
      xaxis = [ 0.0, 0.1 ]

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / self.cellRange[ -1 ]

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht
      #pin_adv_wd = max( min_wd, pin_adv_wd )

      pin_gap = pin_adv_wd >> 4
      pin_wd = max( min_pin_wd, pin_adv_wd - pin_gap )
      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      pin_wd = max( min_pin_wd, pin_wd )

      pin_gap = pin_wd >> 4
      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    image_wd = \
        label_size[ 0 ] + 2 + assy_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = max(
        label_size[ 1 ] + 2 + assy_ht + (font_size *3 / 2),
	legend_size[ 1 ]
	)

    xaxis_factor = (pin_wd -1) / (xaxis[ -1 ] - xaxis[ 0 ])
    yaxis_factor = (pin_wd - 1) / \
        (core.subPinAxialMeshCenters[ -1 ] - core.subPinAxialMeshCenters[ 0 ])

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    #config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'lineWidth' ] = max( 1, pin_gap >> 2 )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd
    config[ 'xaxis' ] = xaxis
    config[ 'xaxisFactor' ] = xaxis_factor
    config[ 'yaxisFactor' ] = yaxis_factor

    return  config
  #end _CreateRConfig


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateRImage()			-
  #----------------------------------------------------------------------
  def _CreateRImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
	)
    dset_array = None

    if config is None:
      config = self.config
    if config is not None and tuple_valid:
      assy_region = config[ 'assemblyRegion' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]

      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

#      item_factors = None
#      if self.state.weightsMode == 'on':
#        item_factors = self.dmgr.GetFactors( self.curDataSet )

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0, 0 )
      else:
        dset_array = np.array( dset )
        dset_shape = dset.shape

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 4
	  #axial_ndx = 3
	  )
    #end if valid config

#		-- Must be valid assy ndx
#		--
    if dset_array is not None and assy_ndx < dset_shape[ 4 ]:
#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      im_draw = PIL.ImageDraw.Draw( im )

      nodata_pen_color = ( 155, 155, 155, 255 )
      data_brush_color = ( 255, 255, 255, 255 )

#			-- Loop on rows
#			--
      item_y = assy_region[ 1 ]
      for item_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels and item_row < core.npiny:
	  label = '%d' % (item_row + 1)
	  label_size = label_font.getsize( label )
	  label_y = item_y + ((pin_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )
	#end if self.showLabels and item_row < core.npiny

#				-- Loop on col
#				--
	item_x = assy_region[ 0 ]
	for item_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if self.showLabels and \
	      item_row == self.cellRange[ 1 ] and item_col < core.npinx:
	    label = '%d' % (item_col + 1)
	    label_size = label_font.getsize( label )
	    label_x = item_x + ((pin_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if self.showLabels and ...

#					-- Check row and col in range
	  if dset_array is None:
	    self.logger.critical( '** A dset_array is None, how did this happen **' )

	  if item_row < dset_shape[ 1 ] and item_col < dset_shape[ 2 ]:
	    values = dset_array[ :, item_row, item_col, :, assy_ndx ]

#	    brush_color = Widget.GetColorTuple(
#	        value - ds_range[ 0 ], value_delta, 255
#	        )
#	    pen_color = Widget.GetDarkerColor( brush_color, 255 )

	    im_draw.rectangle(
	        [ item_x, item_y, item_x + pin_wd, item_y + pin_wd ],
	        fill = ( 255, 255, 255, 255 ), outline = ( 0, 0, 0, 255 )
#	        fill = brush_color, outline = pen_color
	        )
	    self._DrawRectPlot( im_draw, config, core, item_x, item_y, values )
	  #end if 

	  item_x += pin_wd + pin_gap
	#end for item_col

	item_y += pin_wd + pin_gap
      #end for item_row

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	      assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      item_y = max( item_y, legend_size[ 1 ] )
      item_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  assembly = assy_ndx,
	  #axial = axial_value[ 0 ],
	  time = self.timeValue
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#(assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, item_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if valid assy_ndx

    return  im  if im is not None else  self.emptyPilImage
  #end _CreateRImage


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateRasterImage()			-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config_in = None ):
    """Calls _CreateRImage() or _CreateThetaImage().
@param  tuple_in	state tuple
@param  config_in	optional config to use instead of self.config
@return			PIL image
"""
    return \
	self._CreateThetaImage( tuple_in, config_in ) \
	if self.mode == 'theta' else \
	self._CreateRImage( tuple_in, config_in )
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, assy_ndx, axial_level )
"""
    return  ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue[ 1 ] )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateThetaConfig()		-
  #----------------------------------------------------------------------
  def _CreateThetaConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
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
    assemblyRegion
    imageSize
    lineWidth
    pinGap
    pinWidth/gridWidth
#    valueFont
#    valueFontSize
    +
    circleR  (pixels)
    radiusCount
    radiusR  (pixels)
    thetaCount
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

#		-- Get these from the DataModel
#		--
    radius_count = 1
    theta_count = core.nsubtheta
    min_wd = (MIN_PIN_CIRCLE_R << 1) + (radius_count * (MIN_RADIUS_R << 1))
    # given pin_gap = pin_adv_wd >> 4
    min_wd = int( math.ceil( min_wd * 17.0/16.0 ) )

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / self.cellRange[ -1 ]

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht
      pin_adv_wd = max( min_wd, pin_adv_wd )

      pin_gap = pin_adv_wd >> 4
      pin_wd = pin_adv_wd - pin_gap  # max( N, pin_adv_wd - pin_gap )
      assy_wd = self.cellRange[ -2 ] * pin_adv_wd
      assy_ht = self.cellRange[ -1 ] * pin_adv_wd

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      pin_wd = max( min_wd, pin_wd )

      pin_gap = pin_wd >> 4
      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    image_wd = \
        label_size[ 0 ] + 2 + assy_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = max(
        label_size[ 1 ] + 2 + assy_ht + (font_size *3 / 2),
	legend_size[ 1 ]
	)

#    value_font_size = pin_wd >> 1
#    value_font = \
#        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
#	if value_font_size >= 6 else None

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, pin_gap >> 2 )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd
#    config[ 'valueFont' ] = value_font
#    config[ 'valueFontSize' ] = value_font_size
##    config[ 'valueFontSmaller' ] = value_font_smaller

    pin_circle_r = max( MIN_PIN_CIRCLE_R, pin_wd >> 3 )
    radius_r = (pin_wd - (pin_circle_r << 1)) / ((radius_count + 1) << 1)

    config[ 'circleR' ] = pin_circle_r
    config[ 'gridWidth' ] = pin_wd
    config[ 'radiusCount' ] = radius_count
    config[ 'radiusR' ] = radius_r
    config[ 'thetaCount' ] = theta_count

    return  config
  #end _CreateThetaConfig


  #----------------------------------------------------------------------
  #	METHOD:		SubPinRadial2DView._CreateThetaImage()		-
  #----------------------------------------------------------------------
  def _CreateThetaImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level, assy_ndx )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
	axial_level = axial_level
	)

    dset_array = None

    if config is None:
      config = self.config
    if config is not None and tuple_valid:
      assy_region = config[ 'assemblyRegion' ]
      #im_wd, im_ht = config[ 'clientSize' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
#      value_font = config[ 'valueFont' ]
#      value_font_size = config[ 'valueFontSize' ]

      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

#		-- "Item" is chan or pin
#      item_factors = None
#      if self.state.weightsMode == 'on':
#        item_factors = self.dmgr.GetFactors( self.curDataSet )

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = np.array( dset )
        dset_shape = dset.shape

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 4, axial_ndx = 3
	  )
    #end if valid config

#		-- Must be valid assy ndx
#		--
    if dset_array is not None and assy_ndx < dset_shape[ 4 ]:
#			-- Limit axial level
      axial_level = min( axial_level, dset_shape[ 3 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue2( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      nodata_pen_color = ( 155, 155, 155, 255 )
      data_brush_color = ( 255, 255, 255, 255 )

#			-- Loop on rows
#			--
      item_y = assy_region[ 1 ]
      for item_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels and item_row < core.npiny:
	  label = '%d' % (item_row + 1)
	  label_size = label_font.getsize( label )
	  label_y = item_y + ((pin_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )
	#end if self.showLabels and item_row < core.npiny

#				-- Loop on col
#				--
	item_x = assy_region[ 0 ]
	for item_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if self.showLabels and \
	      item_row == self.cellRange[ 1 ] and item_col < core.npinx:
	    label = '%d' % (item_col + 1)
	    label_size = label_font.getsize( label )
	    label_x = item_x + ((pin_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if self.showLabels and ...

#					-- Check row and col in range
	  if dset_array is None:
	    self.logger.critical( '** A dset_array is None, how did this happen **' )
	  if item_row < dset_shape[ 1 ] and item_col < dset_shape[ 2 ]:
	    values = dset_array[ :, item_row, item_col, axial_level, assy_ndx ]
	    #rtheta = np.ndarray( ( 1, dset_shape[ 0 ] ), dtype = np.float64 )
	    #rtheta[ 0 ] = values
	    rtheta = values.reshape( ( 1, dset_shape[ 0 ] ) )

	    im_draw.rectangle(
	        [ item_x, item_y, item_x + pin_wd, item_y + pin_wd ],
	        fill = ( 255, 255, 255, 255 ), outline = ( 0, 0, 0, 255 )
#	        fill = brush_color, outline = pen_color
	        )
	    self._DrawRadialPlot( im_draw, config, item_x, item_y, rtheta )

	  else:
	    im_draw.rectangle(
	        [ item_x, item_y, item_x + pin_wd, item_y + pin_wd ],
	        fill = None, outline = nodata_pen_color
	        )
	  #if-else good value, not hidden by item_factor

	  item_x += pin_wd + pin_gap
	#end for item_col

	item_y += pin_wd + pin_gap
      #end for item_row

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	      assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      item_y = max( item_y, legend_size[ 1 ] )
      item_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  assembly = assy_ndx,
	  axial = axial_value[ 0 ],
	  time = self.timeValue
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#(assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, item_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if valid assy_ndx

    return  im  if im is not None else  self.emptyPilImage
  #end _CreateThetaImage


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = False
    if cell_info is not None:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr = self.assemblyAddr,
	  axial_level = self.axialValue[ 1 ],
	  sub_addr = cell_info[ 1 : 3 ],
	  sub_addr_mode = 'pin'
          )

    dset = None
    if valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      dset_shape = dset.shape
      value = None
      if cell_info[ 2 ] < dset_shape[ 0 ] and cell_info[ 1 ] < dset_shape[ 1 ]:
        value = dset[
            cell_info[ 2 ], cell_info[ 1 ],
	    min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 ),
	    min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
	    ]

      if not self.dmgr.IsBadValue( value ):
        show_pin_addr = ( cell_info[ 1 ] + 1, cell_info[ 2 ] + 1 )
	tip_str = 'Pin: %s\n%s: %g' % (
	    str( show_pin_addr ),
	    self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	    value
	    )
    #end if dset

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._DrawRadialPlot()			-
  #----------------------------------------------------------------------
  def _DrawRadialPlot( self, im_draw, config, x, y, rt_values ):
    """Handles drawing the grid
@param  im_draw		PIL.ImageDraw instance
@param  config		draw configuration dict with keys 'circleR', 'ds_range',
			'gridWidth', 'radiusCount', 'radiusR', 'thetaCount'
@param  x		left pixel
@param  y		top pixel
@param  rt_values	ndarray with shape ( radius_count, theta_count )
"""
    circle_r = config[ 'circleR' ]
    ds_range = config[ 'dataRange' ]
    value_delta = ds_range[ 1 ] - ds_range[ 0 ]
    grid_wd = config[ 'gridWidth' ]
    radius_count = config[ 'radiusCount' ]
    radius_r = config[ 'radiusR' ]
    theta_count = config[ 'thetaCount' ]

    origin = ( x + (grid_wd >> 1), y + (grid_wd >> 1) )
    dtheta = (2.0 * math.pi) / theta_count
    dtheta_deg = 360.0 / theta_count

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
'ds_range=%s, circle_r=%d, x=%d, y=%d' +
'%sgrid_wd=%d, radius_count=%d, theta_count=%d' +
'%sradius_r=%s' +
'%sorigin=%s, dtheta=%f/%f',
	  str( ds_range ), circle_r, x, y,
	  os.linesep, grid_wd, radius_count, theta_count,
	  os.linesep, str( radius_r ),
	  os.linesep, str( origin ), dtheta, dtheta_deg
          )

#	-- Outer loop is radius
#	--
    cur_r = circle_r + ((radius_count - 1) * radius_r)
    for ri in xrange( radius_count - 1, -1, -1 ):
#      ring_rect_inner = [
#	  origin[ 0 ] - cur_r, origin[ 1 ] - cur_r,
#	  origin[ 0 ] + cur_r, origin[ 1 ] + cur_r
#          ]
      ring_rect_outer = [
	  origin[ 0 ] - (cur_r + radius_r), origin[ 1 ] - (cur_r + radius_r),
	  origin[ 0 ] + (cur_r + radius_r), origin[ 1 ] + (cur_r + radius_r)
          ]

#		-- Inner loop is theta
#		--
      cur_theta = cur_theta_deg = 0.0
      for ti in xrange( theta_count ):
        value = rt_values[ ri, ti ]
	if not self.dmgr.IsBadValue( value ):
	  pen_color = Widget.\
	      GetColorTuple( value - ds_range[ 0 ], value_delta, 155 )
	  fill_color = pen_color

          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
		'ri=%d, ti=%d, rect=%s',
		ri, ti, str( ring_rect_outer )
	        )
          im_draw.pieslice(
	      ring_rect_outer,
	      cur_theta_deg, cur_theta_deg + dtheta_deg,
	      fill = fill_color,
	      outline = None
	      #outline = ( 0, 0, 100, 255 )
	      )
	#end if good value

        cur_theta += dtheta
        cur_theta_deg += dtheta_deg
      #end for ti

      cur_r -= radius_r
    #end for ri

#	-- Draw pin
#	--
    ring_rect = [
	origin[ 0 ] - circle_r, origin[ 1 ] - circle_r,
	origin[ 0 ] + circle_r, origin[ 1 ] + circle_r
        ]
    im_draw.ellipse(
	ring_rect,
	fill = ( 155, 155, 155, 255 ),
	outline = ( 100, 100, 100, 255 )
	)
  #end _DrawRadialPlot


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._DrawRectPlot()			-
  #----------------------------------------------------------------------
  def _DrawRectPlot( self, im_draw, config, core, x, y, values ):
    """Handles drawing the plot for a single pin
@param  im_draw		PIL.ImageDraw instance
@param  config		draw configuration dict
@param  x		left pixel
@param  y		top pixel
@param  values		nparray ( x, y )
"""
    ds_range = config[ 'dataRange' ]
    value_delta = ds_range[ 1 ] - ds_range[ 0 ]
    pin_wd = config[ 'pinWidth' ]
    xaxis = config[ 'xaxis' ]
    xaxis_factor = config[ 'xaxisFactor' ]
    yaxis_factor = config[ 'yaxisFactor' ]

    im_draw.rectangle(
	[ x, y, x + pin_wd, y + pin_wd ],
	fill = ( 0, 0, 0, 0 )
        )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
'ds_range=%s, pin_wd=%d, x=%d, y=%d' +
'%sxaxis_factor=%f, yaxis_factor=%f' +
'%sxaxis=%s%svalues.shape=%s',
	  str( ds_range ), pin_wd, x, y,
	  os.linesep, xaxis_factor, yaxis_factor,
	  os.linesep, str( xaxis ),
	  os.linesep, str( values.shape )
          )

    if values is not None:
      #last_y = y
      y1 = y + core.subPinAxialMesh[ -1 ] * yaxis_factor
      for j in xrange( core.nsubax - 1, -1, -1 ):
	y2 = y + core.subPinAxialMesh[ j ] * yaxis_factor
        if self.logger.isEnabledFor( logging.DEBUG ):
	  self.logger.debug( 'j=%d, y1=%f, y2=%f', j, y1, y2 )

	last_x = x
        for i in xrange( xaxis.shape[ 0 ] ):
	  if i == xaxis.shape[ 0 ] - 1:
	    dx = pin_wd
	  else:
	    dx = (xaxis[ i + 1 ] - xaxis[ 0 ]) / 2.0 * xaxis_factor
	  cur_x = x + dx
	  rect = [ last_x, y1, cur_x, y2 ]
	  cur_value = values[ i, j ]
	  if self.dmgr.IsBadValue( cur_value ):
	    fill_color = ( 0, 0, 0, 0 )
	  else:
	    fill_color = Widget.\
	        GetColorTuple( cur_value - ds_range[ 0 ], value_delta, 255 )

          if self.logger.isEnabledFor( logging.DEBUG ):
	    self.logger.debug( 
	       'i=%d, cur_x=%f, cur_value=%f, color=%s%srect=%s',
	       i, cur_x, cur_value, str( fill_color ),
	       os.linesep, str( rect )
	       )
	  im_draw.rectangle( rect, fill = fill_color, outline = fill_color )
	  last_x = cur_x
	#end for i

	y1 = y2
      #end for j
    #end if values is not None
  #end _DrawRectPlot


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.FindCell()				-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() and prepends -1 for an index value for drag processing.
@return			None if no match, otherwise tuple of
			( -1, 0-based cell_col, cell_row )
"""
    pin_addr = self.FindPin( ev_x, ev_y )
    return \
        None if pin_addr is None else \
	( -1, pin_addr[ 0 ], pin_addr[ 1 ] )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.FindPin()				-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin col and row.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    core = None
    if self.config is not None and 'assemblyRegion' in self.config:
      core = self.dmgr.GetCore()

    if core and ev_x >= 0 and ev_y >= 0:
      assy_region = self.config[ 'assemblyRegion' ]
      pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
      off_x = ev_x - assy_region[ 0 ]
      off_y = ev_y - assy_region[ 1 ]
      cell_x = min(
          int( off_x / pin_size ) + self.cellRange[ 0 ],
	  self.cellRange[ 2 ] - 1
	  )
      cell_x = max( self.cellRange[ 0 ], cell_x )
      cell_y = min(
	  int( off_y / pin_size ) + self.cellRange[ 1 ],
	  self.cellRange[ 3 ] - 1
	  )
      cell_y = max( self.cellRange[ 1 ], cell_y )
      result = ( cell_x, cell_y )
      #end if event within display
    #end if core and ev_x >= 0 and ev_y >= 0

    return  result
  #end FindPin


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
  #	METHOD:		SubPin2DView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'subpin_r', 'subpin_theta' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.GetEventLockSet()			-
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
  #	METHOD:		SubPin2DView.GetInitialCellRange()		-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.dmgr.ExtractSymmetryExtent().
Subclasses should override as needed.
@return			initial range of raster cells
			( left, top, right, bottom, dx, dy )
"""
    result = None
    core = self.dmgr.GetCore()
    if core is not None:
      maxx = core.npinx
      maxy = core.npiny
      result = ( 0, 0, maxx, maxy, maxx, maxy )

    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
"""
    pin_count = max( self.cellRange[ -2 ], self.cellRange[ -1 ] )
    return  max( 32, 1024 / pin_count )
#    return \
#	512  if pin_count <= 1 else \
#	256  if pin_count <= 2 else \
#	128  if pin_count <= 3 else \
#	96  if pin_count <= 5 else \
#        64  if pin_count <= 10 else \
#	40  if pin_count <= 15 else \
#	32
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Sub Pin 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    core = self.dmgr.GetCore()
    if self.config is not None and core is not None:
      addr_list = list( self.auxSubAddrs )
      addr_list.insert( 0, self.subAddr )

      new_bmap = None
      dc = None
      secondary_pen = None

      assy_region = self.config[ 'assemblyRegion' ]
      pin_gap = self.config[ 'pinGap' ]
      pin_wd = self.config[ 'pinWidth' ]
      pin_adv = pin_gap + pin_wd
      line_wd = self.config[ 'lineWidth' ]

      for i in range( len( addr_list ) ):
	addr = addr_list[ i ]
        rel_col = addr[ 0 ] - self.cellRange[ 0 ]
        rel_row = addr[ 1 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	  if new_bmap is None:
	    new_bmap = self._CopyBitmap( bmap )
            dc = wx.MemoryDC( new_bmap )
	    gc = wx.GraphicsContext.Create( dc )

	  if i == 0:
	    gc.SetPen(
	        wx.ThePenList.FindOrCreatePen(
	            wx.Colour( 255, 0, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
		    )
	        )
	  elif secondary_pen is None:
	    secondary_pen = wx.ThePenList.FindOrCreatePen(
	        wx.Colour( 255, 255, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
	        )
	    gc.SetPen( secondary_pen )

	  rect = [
	      rel_col * pin_adv + assy_region[ 0 ],
	      rel_row * pin_adv + assy_region[ 1 ],
	      pin_wd + 1, pin_wd + 1
	      ]
	  path = gc.CreatePath()
	  path.AddRectangle( *rect )
	  gc.StrokePath( path )
        #end if addr within range
      #end for i

      if dc is not None:
        dc.SelectObject( wx.NullBitmap )
      if new_bmap is not None:
        result = new_bmap
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = \
        tpl is not None and len( tpl ) >= 2 and \
	tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.assemblyAddr[ 0 ]
    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._LoadDataModelValues()		-
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
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxSubAddrs', 'mode', 'subAddr' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( SubPin2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._OnClick()				-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    #ev.Skip()
    is_aux = self.IsAuxiliaryEvent( ev )

#		-- Validate
#		--
    valid = False
    pin_addr = self.FindPin( *ev.GetPosition() )

    if pin_addr is not None and pin_addr != self.subAddr:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr = self.assemblyAddr[ 0 ],
	  axial_level = self.axialValue[ 1 ],
	  sub_addr = pin_addr,
	  sub_addr_mode = 'pin'
	  )

    if valid:
      if is_aux:
	addrs = list( self.auxSubAddrs )
	if pin_addr in addrs:
	  addrs.remove( pin_addr )
	else:
	  addrs.append( pin_addr )
	#self.FireStateChange( aux_sub_addrs = addrs )
	node_addrs = self.dmgr.NormalizeNodeAddrs(
	    self.auxNodeAddrs + self.dmgr.GetNodeAddrs( addrs )
	    )
	self.FireStateChange(
	    aux_node_addrs = node_addrs,
	    aux_sub_addrs = addrs
	    )

      else:
        #self.FireStateChange( sub_addr = pin_addr, aux_sub_addrs = [] )
        #state_args = { 'aux_sub_addrs': [] 'sub_addr': pin_addr }
	state_args = dict(
	    aux_node_addrs = [],
	    aux_sub_addrs = [],
	    sub_addr = pin_addr
	    )
	node_addr = self.dmgr.GetNodeAddr( pin_addr )
	if node_addr >= 0:
	  state_args[ 'node_addr' ] = node_addr
        self.FireStateChange( **state_args )
      #end if-else is_aux
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    pass
#    if self.curDataSet:
#      self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( SubPin2DView, self ).SaveProps( props_dict )

    for k in ( 'assemblyAddr', 'auxSubAddrs', 'mode', 'subAddr' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._UpdateDataSetStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type ):
    """
@param  ds_type		dataset category/type
Updates the nodalMode property.
"""
    self.mode = 'theta'  if ds_type == 'subpin_theta' else  'r'
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( SubPin2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_sub_addrs' in kwargs:
      aux_sub_addrs = \
          self.dmgr.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'pin' )
      if aux_sub_addrs != self.auxSubAddrs:
        changed = True
	self.auxSubAddrs = aux_sub_addrs

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr( kwargs[ 'sub_addr' ], 'pin' )
      if sub_addr != self.subAddr:
        changed = True
	self.subAddr = sub_addr

#    if 'weights_mode' in kwargs:
#      kwargs[ 'resized' ] = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end SubPin2DView
