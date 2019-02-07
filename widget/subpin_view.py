#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		subpin_view.py					-
#	HISTORY:							-
#		2018-03-02	leerw@ornl.gov				-
#	  Migrating to _CreateEmptyBitmapAndDC().
#		2018-02-05	leerw@ornl.gov				-
#	  Moving Linux/GTK/X11 image manipulation to the UI thread.
#		2017-11-25	leerw@ornl.gov				-
#		2017-11-20	leerw@ornl.gov				-
#	  Migrating to wx.Bitmap.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
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

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.utils import DataUtils
from event.state import *

from .raster_widget import *
from .widget import *


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
    font
    fontSize
    labelFont
    labelSize
    legendBitmap
    legendSize
    mapper
    valueFont
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
    if 'scale_type' not in kwargs:
      kwargs[ 'scale_type' ] = self._ResolveScaleType( self.curDataSet )
      #kwargs[ 'scale_type' ] = self.dmgr.GetDataSetScaleType( self.curDataSet )
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_bmap = config[ 'legendBitmap' ]
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
    #xxxxx _CreateBaseDrawConfig() sets
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      #xxxxx revisit font_size, pt bigger than pixel
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] + 2 )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)
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

    assy_region_x = label_size[ 0 ] + 2
    assy_region_y = label_size[ 1 ] + 2
    image_wd = assy_region_x + assy_wd + (font_size << 1) + legend_size[ 0 ]
#    image_ht = max(
#	assy_region_y + assy_ht + (font_size *3 / 2),
#	legend_size[ 1 ]
#	)
    if legend_size[ 1 ] + 2 > assy_region_y + assy_ht:
      image_ht = legend_size[ 1 ] + 2 + (font_size * 3 / 2) + 2
      #image_ht = legend_size[ 1 ] + 2 + (font_size << 1)
    else:
      image_ht = assy_region_y + assy_ht + (font_size * 3 / 2) + 2
      #image_ht = assy_region_y + assy_ht + (font_size << 1)

    xaxis_factor = (pin_wd - 1) / (xaxis[ -1 ] - xaxis[ 0 ])
    yaxis_factor = (pin_wd - 1) / \
        (core.subPinAxialMeshCenters[ -1 ] - core.subPinAxialMeshCenters[ 0 ])

    config[ 'assemblyRegion' ] = \
	[ assy_region_x, assy_region_y, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
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

    bmap = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
	)
    dset_array = None

    if config is None:
      config = self.config
    if config is not None and tuple_valid:
      assy_region = config[ 'assemblyRegion' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
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
	  font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 4
	  #axial_ndx = 3
	  )
    #end if valid config

#		-- Must be valid assy ndx
#		--
    if dset_array is not None and assy_ndx < dset_shape[ 4 ]:
#			-- Create image
#			--
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )

      black_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	  wx.Colour( 0, 0, 0, 0 ), 1, wx.PENSTYLE_SOLID
          ) )
#      nodata_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
#	  wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
#          ) )
      data_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	  wx.Colour( 255, 255, 255, 255 ), wx.BRUSHSTYLE_SOLID
          ) )

      if self.showLabels:
        glabel_font = gc.CreateFont( label_font, wx.BLACK )
	gc.SetFont( glabel_font )

      gc.SetPen( black_pen )
      gc.SetBrush( data_brush )

#			-- Loop on rows
#			--
      item_y = assy_region[ 1 ]
      for item_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels and item_row < core.npiny:
	  label = '%d' % (item_row + 1)
	  label_size = gc.GetFullTextExtent( label )
	  label_y = item_y + ((pin_wd - label_size[ 1 ]) / 2.0)
	  gc.DrawText( label, 1, label_y )
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
	    label_size = gc.GetFullTextExtent( label )
	    label_x = item_x + ((pin_wd - label_size[ 0 ]) / 2.0)
	    gc.DrawText( label, label_x, 1 )
	  #end if self.showLabels and ...

#					-- Check row and col in range
	  if dset_array is None:
	    self.logger.critical( '** A dset_array is None, how did this happen **' )

	  if item_row < dset_shape[ 1 ] and item_col < dset_shape[ 2 ]:
	    values = dset_array[ :, item_row, item_col, :, assy_ndx ]

	    gc.DrawRectangle( item_x, item_y, pin_wd, pin_wd )
	    self._DrawRectPlot( gc, config, core, item_x, item_y, values )
	  #end if 

	  item_x += pin_wd + pin_gap
	#end for item_col

	item_y += pin_wd + pin_gap
      #end for item_row

#			-- Draw Legend Image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    legend_bmap,
	    assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	    2, #assy_region[ 1 ]
	    legend_bmap.GetWidth(), legend_bmap.GetHeight()
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      item_y = max( item_y, legend_size[ 1 ] + 2 )
      item_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  #assembly = assy_ndx,
	  assembly = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  #axial = axial_value.cm,
	  time = self.timeValue
          )
      self._DrawStringsWx(
	  gc, font,
	  ( title_str, ( 0, 0, 0, 255 ),
	    assy_region[ 0 ], item_y,
	    assy_region[ 2 ] - assy_region[ 0 ],
	    'c', im_wd - assy_region[ 0 ] )
          )

#      title_size = pil_font.getsize( title_str )
#      title_x = max(
#	  font_size,
#	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#	  )
#      im_draw.text(
#          ( title_x, item_y ),
#	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
#          )

      dc.SelectObject( wx.NullBitmap )
    #end if valid assy_ndx

    return  bmap  if bmap is not None else  self.emptyBitmap
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
    return  ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue.subPinIndex )
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
    font
    fontSize
    labelFont
    labelSize
    legendBitmap
    legendSize
    mapper
    +
    assemblyRegion
    imageSize
    lineWidth
    pinGap
    pinWidth/gridWidth
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
    legend_bmap = config[ 'legendBitmap' ]
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
    #xxxxx _CreateBaseDrawConfig() sets
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      #xxxxx revisit font_size, pt bigger than pixel
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] + 2 )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)
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

    assy_region_x = label_size[ 0 ] + 2
    assy_region_y = label_size[ 1 ] + 2
    image_wd = assy_region_x + assy_wd + (font_size << 1) + legend_size[ 0 ]
#    image_ht = max(
#	assy_region_y + 2 + assy_ht + (font_size *3 / 2),
#	legend_size[ 1 ]
#	)
    if legend_size[ 1 ] + 2 > assy_region_y + assy_ht:
      image_ht = legend_size[ 1 ] + 2 + (font_size << 1)
      #image_ht = legend_size[ 1 ] + 2 + (font_size * 3 / 2)
    else:
      image_ht = assy_region_y + assy_ht + (font_size << 1)
      #image_ht = assy_region_y + assy_ht + (font_size * 3 / 2)

    config[ 'assemblyRegion' ] = \
        [ assy_region_x, assy_region_y, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, pin_gap >> 2 )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd

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
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]

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
	  font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 4, axial_ndx = 3
	  )
    #end if valid config

#		-- Must be valid assy ndx
#		--
    if dset_array is not None and assy_ndx < dset_shape[ 4 ]:
#			-- Limit axial level
      axial_level = min( axial_level, dset_shape[ 3 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )

      black_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	  wx.Colour( 0, 0, 0, 0 ), 1, wx.PENSTYLE_SOLID
          ) )
      nodata_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	  wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
          ) )
      data_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	  wx.Colour( 255, 255, 255, 255 ), wx.BRUSHSTYLE_SOLID
          ) )

      if self.showLabels:
        glabel_font = gc.CreateFont( label_font, wx.BLACK )
	gc.SetFont( glabel_font )

#			-- Loop on rows
#			--
      item_y = assy_region[ 1 ]
      for item_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels and item_row < core.npiny:
	  label = '%d' % (item_row + 1)
	  label_size = gc.GetFullTextExtent( label )
	  label_y = item_y + ((pin_wd - label_size[ 1 ]) / 2.0)
	  gc.DrawText( label, 1, label_y )
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
	    label_size = gc.GetFullTextExtent( label )
	    label_x = item_x + ((pin_wd - label_size[ 0 ]) / 2.0)
	    gc.DrawText( label, label_x, 1 )
	  #end if self.showLabels and ...

#					-- Check row and col in range
	  if item_row < dset_shape[ 1 ] and item_col < dset_shape[ 2 ]:
	    values = dset_array[ :, item_row, item_col, axial_level, assy_ndx ]
	    #rtheta = np.ndarray( ( 1, dset_shape[ 0 ] ), dtype = np.float64 )
	    #rtheta[ 0 ] = values
	    rtheta = values.reshape( ( 1, dset_shape[ 0 ] ) )
            gc.SetPen( black_pen )
            gc.SetBrush( data_brush )

	    gc.DrawRectangle( item_x, item_y, pin_wd, pin_wd )
	    self._DrawRadialPlot( gc, config, item_x, item_y, rtheta )

	  else:
            gc.SetPen( nodata_pen )
            gc.SetBrush( trans_brush )
	    gc.DrawRectangle( item_x, item_y, pin_wd, pin_wd )
	  #if-else good value, not hidden by item_factor

	  item_x += pin_wd + pin_gap
	#end for item_col

	item_y += pin_wd + pin_gap
      #end for item_row

#			-- Draw Legend Image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    legend_bmap,
	    assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	    2, #assy_region[ 1 ]
	    legend_bmap.GetWidth(), legend_bmap.GetHeight()
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      item_y = max( item_y, legend_size[ 1 ] + 2 )
      item_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  #assembly = assy_ndx,
	  assembly = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  axial = axial_value.cm,
	  time = self.timeValue
          )
      self._DrawStringsWx(
	  gc, font,
	  ( title_str, ( 0, 0, 0, 255 ),
	    assy_region[ 0 ], item_y,
	    assy_region[ 2 ] - assy_region[ 0 ],
	    'c', im_wd - assy_region[ 0 ] )
          )

#      title_size = pil_font.getsize( title_str )
#      title_x = max(
#	  font_size,
#	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#	  )
#
#      im_draw.text(
#          ( title_x, item_y ),
#	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
#          )

      dc.SelectObject( wx.NullBitmap )
    #end if valid assy_ndx

    return  bmap  if bmap is not None else  self.emptyBitmap
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
	  axial_level = self.axialValue.pinIndex,
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
	    min( self.axialValue.pinIndex, dset_shape[ 2 ] - 1 ),
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
  def _DrawRadialPlot( self, gc, config, x, y, rt_values ):
    """Handles drawing the grid
@param  gc		wx.GraphicsContext instance
@param  config		draw configuration dict with keys 'circleR', 'ds_range',
			'gridWidth', 'radiusCount', 'radiusR', 'thetaCount'
@param  x		left pixel
@param  y		top pixel
@param  rt_values	ndarray with shape ( radius_count, theta_count )
"""
    amode = gc.GetAntialiasMode()
    cmode = gc.GetCompositionMode()
    gc.SetAntialiasMode( wx.ANTIALIAS_NONE )
    gc.SetCompositionMode( wx.COMPOSITION_SOURCE )

    circle_r = config[ 'circleR' ]
    ds_range = config[ 'dataRange' ]
    value_delta = ds_range[ 1 ] - ds_range[ 0 ]
    grid_wd = config[ 'gridWidth' ]
    mapper = config[ 'mapper' ]
    radius_count = config[ 'radiusCount' ]
    radius_r = config[ 'radiusR' ]
    theta_count = config[ 'thetaCount' ]

    origin = ( x + (grid_wd >> 1), y + (grid_wd >> 1) )
    #dtheta = (2.0 * math.pi) / theta_count
    dtheta = TWO_PI
    if theta_count > 1:
      dtheta /= theta_count
    radius_wd = max( 1, int( radius_r ) )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
'  ds_range=%s' +
'%s  circle_r=%d, x=%d, y=%d' +
'%s  grid_wd=%d, radius_count=%d, radius_r=%d, theta_count=%d' +
'%s  origin=%s, dtheta=%f/%f',
	  str( ds_range ),
	  os.linesep, circle_r, x, y,
	  os.linesep, grid_wd, radius_count, radius_r, theta_count,
	  os.linesep, str( origin ), dtheta, dtheta * 180.0 / math.pi
          )

#	-- Outer loop is radius
#	--
    #cur_r = circle_r + ((radius_count - 1) * radius_r)
    cur_r = circle_r + ((radius_count - 1) * radius_r) - (radius_wd >> 1)
    for ri in xrange( radius_count - 1, -1, -1 ):
#		-- Inner loop is theta
#		--
      #cur_theta = 0.0
      cur_theta = -PI_OVER_2
      for ti in xrange( theta_count ):
        #angle_st = Widget.NormalizeAngle( cur_theta - PI_OVER_2 )
	end_theta = Widget.NormalizeAngle( cur_theta + (dtheta * 2) )

        value = rt_values[ ri, ti ]
	if not self.dmgr.IsBadValue( value ):
#	  pen_color = Widget.\
#	      GetColorTuple( value - ds_range[ 0 ], value_delta, 155 )
	  pen_color = mapper.to_rgba( value, bytes = True )

	  cur_pen = wx.ThePenList.FindOrCreatePen(
	      wx.Colour( *pen_color ), radius_wd, wx.PENSTYLE_SOLID
	      )
	  cur_pen.SetCap( wx.CAP_BUTT )
	  gc.SetPen( gc.CreatePen( cur_pen ) )
#	  gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
#	      wx.Colour( *fill_color ), wx.BRUSHSTYLE_SOLID
#	      ) ) )

          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
'  ri=%d, ti=%d, cur_r=%f, radius_wd=%d, color=%s' +
'%s  cur_theta=%f, end_theta=%f',
		ri, ti, cur_r, radius_wd, str( pen_color ),
		os.linesep, cur_theta, end_theta
		)

	  path = gc.CreatePath()
	  path.AddArc(
	      origin[ 0 ], origin[ 1 ], circle_r + cur_r,
	      #cur_theta, cur_theta + dtheta
	      cur_theta, end_theta
	      )
	  gc.StrokePath( path )
	#end if good value

        #cur_theta += dtheta
	cur_theta = Widget.NormalizeAngle( cur_theta + dtheta )
      #end for ti

      cur_r -= radius_r
    #end for ri

#	-- Draw pin
#	--
    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
        ) ) )
    gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	wx.Colour( 100, 100, 100, 255 ), wx.BRUSHSTYLE_SOLID
        ) ) )
    gc.DrawEllipse(
	origin[ 0 ] - circle_r, origin[ 1 ] - circle_r,
	circle_r << 1, circle_r << 1
        )

    gc.SetAntialiasMode( amode )
    gc.SetCompositionMode( cmode )
  #end _DrawRadialPlot


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._DrawRectPlot()			-
  #----------------------------------------------------------------------
  def _DrawRectPlot( self, gc, config, core, x, y, values ):
    """Handles drawing the plot for a single pin
@param  gc		wx.GraphicsContext instance
@param  config		draw configuration dict
@param  x		left pixel
@param  y		top pixel
@param  values		nparray ( x, y )
"""
    ds_range = config[ 'dataRange' ]
    value_delta = ds_range[ 1 ] - ds_range[ 0 ]
    mapper = config[ 'mapper' ]
    pin_gap = config[ 'pinGap' ]
    pin_wd = config[ 'pinWidth' ]
    xaxis = config[ 'xaxis' ]
    xaxis_factor = config[ 'xaxisFactor' ]
    yaxis_factor = config[ 'yaxisFactor' ]

    trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	wx.WHITE, wx.TRANSPARENT
        ) )
    trans_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	wx.WHITE, 0, wx.TRANSPARENT
        ) )

    gc.SetPen( trans_pen )
    gc.SetBrush( trans_brush )
    gc.DrawRectangle( x, y, pin_wd, pin_wd )

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
      half_gap = pin_gap >> 1
      #last_y = y
      #y1 = y + core.subPinAxialMesh[ -1 ] * yaxis_factor
      ydelta = \
          core.subPinAxialMeshCenters[ -1 ] - core.subPinAxialMeshCenters[ 0 ]
      y1 = y + (ydelta * yaxis_factor)
      for j in xrange( core.nsubax - 1, -1, -1 ):
	y2 = y + core.subPinAxialMesh[ j ] * yaxis_factor
        if self.logger.isEnabledFor( logging.DEBUG ):
	  self.logger.debug( 'j=%d, y1=%f, y2=%f', j, y1, y2 )

	cur_x = x
        for i in xrange( xaxis.shape[ 0 ] ):
	  if i == xaxis.shape[ 0 ] - 1:
	    #dx = pin_wd - cur_x
	    dx = pin_wd + half_gap - cur_x
	  else:
	    dx = (xaxis[ i + 1 ] - xaxis[ 0 ]) / 2.0 * xaxis_factor
	  cur_value = values[ i, j ]

	  if self.dmgr.IsBadValue( cur_value ):
	    gc.SetPen( trans_pen )
	    gc.SetBrush( trans_brush )
	  else:
#	    fill_color = Widget.\
#	        GetColorTuple( cur_value - ds_range[ 0 ], value_delta, 255 )
	    fill_color = mapper.to_rgba( cur_value, bytes = True )
	    fill_colour = wx.Colour( *fill_color )
	    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
		fill_colour, 1, wx.PENSTYLE_SOLID
	        ) ) )
	    gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
		fill_colour, wx.BRUSHSTYLE_SOLID
	        ) ) )

          if self.logger.isEnabledFor( logging.DEBUG ):
	    self.logger.debug( 
	       'i=%d, cur_x=%f, cur_value=%f',
	       i, cur_x, cur_value
	       )
	  gc.DrawRectangle( cur_x, y1, dx, y1 - y2 )
	  cur_x += dx
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
    return  ( 'axial:subpin', 'statepoint' )
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
#  def GetPrintScale( self ):
#    """
#"""
#    pin_count = max( self.cellRange[ -2 ], self.cellRange[ -1 ] )
#    return  max( 32, 1024 / pin_count )
#  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Subpin 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None:
      addr_list = list( self.auxSubAddrs )
      addr_list.insert( 0, self.subAddr )

      new_bmap = None
      dc = None
      secondary_pen = None

      assy_region = config[ 'assemblyRegion' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      pin_adv = pin_gap + pin_wd
      line_wd = config[ 'lineWidth' ]

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

#	  rect = [
#	      rel_col * pin_adv + assy_region[ 0 ],
#	      rel_row * pin_adv + assy_region[ 1 ],
#	      pin_wd + 1, pin_wd + 1
#	      ]
	  rect = [
	      rel_col * pin_adv + assy_region[ 0 ],
	      rel_row * pin_adv + assy_region[ 1 ],
	      pin_wd + line_wd, pin_wd + line_wd
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
    #end if config is not None:

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
	  axial_level = self.axialValue.pinIndex,
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
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    pass
#    if self.curDataSet:
#      self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		SubPin2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( SubPin2DView, self ).SaveProps( props_dict, for_drag = for_drag )

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
  def _UpdateDataSetStateValues( self, ds_type, clear_zoom_stack = False ):
    """Updates the mode.
    Args:
        ds_type (str): dataset category/type
	clear_zoom_stack (boolean): True to clear in zoom stack
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
