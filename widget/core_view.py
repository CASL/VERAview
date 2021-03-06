#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_view.py					-
#	HISTORY:							-
#		2018-12-24	leerw@ornl.gov				-
#         Invoking VeraViewApp.DoBusyEventOp() in event handlers.
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
  import wx.lib.delayedresult as wxlibdr
  #from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) is required for this component'

from data.datamodel import *
from event.state import *

from .raster_widget import *
from .widget import *
#from .widget_ops import *


#------------------------------------------------------------------------
#	CLASS:		Core2DView					-
#------------------------------------------------------------------------
class Core2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.avgDataSet = None
    #self.avgValues = {}
    self.channelMode = False

    self.mode = ''  # 'assy', 'core'
    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    super( Core2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateAssyDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateAssyDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
@param  kwargs
    scale	pixels per pin (deprecated)
    scale_type  'linear' or 'log', defaulting to 'linear'
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
    mode = 'assy'
    pinGap
    pinWidth		used for pin or node width, depending on self.nodalMode
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
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

#		-- Must calculate scale?
#		--
    #xxxxx _CreateBaseDrawConfig() sets 
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      #xxxxx revisit font_size, bigger than pixel
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]

      if self.nodalMode:
        pin_adv_wd = region_wd >> 1
      elif self.channelMode:
        pin_adv_wd = region_wd / (core.npin + 1)
      else:
        pin_adv_wd = region_wd / core.npin

      working_ht = max( ht, legend_size[ 1 ] )
      #xxxxx revisit font_size, bigger than pixel
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      if self.nodalMode:
        pin_adv_ht = region_ht >> 1
      elif self.channelMode:
        pin_adv_ht = region_ht / (core.npin + 1)
      else:
        pin_adv_ht = region_ht / core.npin

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      if self.channelMode:
        pin_gap = 0
      else:
        pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      if self.nodalMode:
        assy_wd = assy_ht = (pin_wd + pin_gap) << 1
      elif self.channelMode:
        assy_wd = assy_ht = (core.npin + 1) * (pin_wd + pin_gap)
      else:
        assy_wd = assy_ht = core.npin * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 24
      if self.channelMode:
        pin_gap = 0
      else:
        pin_gap = pin_wd >> 3

      if self.nodalMode:
        pin_wd <<= 4
        assy_wd = assy_ht = (pin_wd + pin_gap) << 1
      elif self.channelMode:
        assy_wd = assy_ht = (core.npin + 1) * (pin_wd + pin_gap)
      else:
        assy_wd = assy_ht = core.npin * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    image_wd = \
        label_size[ 0 ] + 2 + assy_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = \
        max( assy_ht, legend_size[ 1 ] ) + font_size + (font_size << 1)

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, pin_gap >> 2 )
    config[ 'mode' ] = 'assy'
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateAssyDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateAssyImage()			-
  #----------------------------------------------------------------------
  def _CreateAssyImage( self, tuple_in, config ):
    """Called in background task to create the wx.Image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
	axial_level = axial_level
	#state_index = state_ndx
	)

    core = dset = None
    if config is None:
      config = self.config
    if config is not None and tuple_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      if 'assemblyRegion' not in config:
	if 'clientSize' in config:
          config = self._CreateAssyDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateAssyDrawConfig( scale = config[ 'scale' ] )

      assy_region = config[ 'assemblyRegion' ]
      #im_wd, im_ht = config[ 'clientSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]

#		-- "Item" refers to channel or pin
      item_factors = None
      if self.state.weightsMode == 'on':
        item_factors = self.dmgr.GetFactors( self.curDataSet )

      dset_array = np.array( dset )
      dset_shape = dset.shape
      cur_nxpin = 2 if self.nodalMode else min( core.npinx, dset_shape[ 1 ] )
      cur_nypin = 2 if self.nodalMode else min( core.npiny, dset_shape[ 0 ] )

      ds_range = config[ 'dataRange' ]
      #value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )

      node_value_draw_list = []

#			-- Limit axial level
#			--
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      if self.showLabels:
	glabel_font = gc.CreateFont( label_font, wx.BLACK )
        gc.SetFont( glabel_font )

      item_col_limit = cur_nxpin
      if self.channelMode:
        item_col_limit += 1
      item_row_limit = cur_nypin
      if self.channelMode:
        item_row_limit += 1

      node_ndx = 0
      item_y = assy_region[ 1 ]
      for item_row in xrange( item_row_limit ):
#				-- Row label
#				--
	if self.showLabels:
	  label = '%d' % (item_row + 1)
	  text_size = gc.GetFullTextExtent( label )
	  label_size = ( text_size[ 0 ], text_size[ 1 ] )
	  label_y = item_y + ((pin_wd + pin_gap - label_size[ 1 ]) / 2.0)
	  #gc.DrawText( label, 1, label_y, trans_brush )
	  gc.DrawText( label, 1, label_y )

#					-- Loop on col
#					--
	item_x = assy_region[ 0 ]
	for item_col in xrange( item_col_limit ):
#						-- Column label
#						--
	  if item_row == 0 and self.showLabels:
	    label = '%d' % (item_col + 1)
	    text_size = gc.GetFullTextExtent( label )
	    label_size = ( text_size[ 0 ], text_size[ 1 ] )
	    label_x = item_x + ((pin_wd + pin_gap - label_size[ 0 ]) / 2.0)
	    #gc.DrawText( label, label_x, 1, trans_brush )
	    gc.DrawText( label, label_x, 1 )
	  #end if writing column label

#						-- Map to colors
	  cur_array = dset_array[ :, :, axial_level, assy_ndx ]
          colors = mapper.to_rgba( cur_array, bytes = True )
          if item_factors is not None:
	    cur_factors = item_factors[ :, :, axial_level, assy_ndx ]
	    colors[ cur_factors == 0 ] = trans_color_arr
	  colors[ np.isnan( cur_array ) ] = trans_color_arr
	  colors[ np.isinf( cur_array ) ] = trans_color_arr

	  if self.nodalMode:
	    cur_color = colors[ 0, node_ndx ]
	  else:
	    cur_color = colors[ item_row, item_col ]

	  if cur_color[ 3 ] > 0:
	    brush_color = cur_color.tolist()
	    gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	        wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
		) ) )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
		wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
		) ) )

	    if self.nodalMode:
	      gc.DrawRectangle( item_x, item_y, pin_wd + 1, pin_wd + 1 )
	      value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
	      node_value_draw_list.append((
	          self._CreateValueString( value ),
                  Widget.GetContrastColor( *brush_color ),
                  item_x, item_y, pin_wd, pin_wd
                  ))
	    else:
	      gc.DrawEllipse( item_x, item_y, pin_wd, pin_wd )

	  item_x += pin_wd + pin_gap
	  if self.nodalMode:
	    node_ndx += 1
	#end for pin_col

	item_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw pins
#			--
      if self.channelMode:
        brush_color = ( 155, 155, 155, 128 )
	gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
	    wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
	    ) ) )
	pen_color = Widget.GetDarkerColor( brush_color, 128 )
	gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	    wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
	    ) ) )

	pin_draw_wd = pin_wd >> 1
	#pin_draw_wd = max( 1, pin_wd >> 2 )

	pin_y = assy_region[ 1 ] + pin_wd + ((pin_gap - pin_draw_wd) >> 1)
	for pin_row in xrange( core.npiny ):
	  pin_x = assy_region[ 0 ] + pin_wd + ((pin_gap - pin_draw_wd) >> 1)
	  for pin_col in xrange( core.npinx ):
	    gc.DrawEllipse(
	        pin_x, pin_y,
		pin_x + pin_draw_wd, pin_y + pin_draw_wd
		)
	    pin_x += pin_wd + pin_gap
	  #end for pin_col
	  pin_y += pin_wd + pin_gap
	#end for pin_row
      #end if self.channelMode

#			-- Draw values
#			--
      if node_value_draw_list:
        self._DrawValuesWx( node_value_draw_list, gc )

#			-- Draw legend image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    legend_bmap,
	    assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	    assy_region[ 1 ],
	    legend_size[ 0 ], legend_size[ 1 ]
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      item_y = max( item_y, legend_size[ 1 ] )
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
#	  ( title_str, ( 0, 0, 0, 255 ),
#	    core_region[ 0 ], assy_y, core_region[ 2 ] - core_region[ 0 ],
#	    'c' )
	  ( title_str, ( 0, 0, 0, 255 ),
	    assy_region[ 0 ], item_y, assy_region[ 2 ],
	    'c', im_wd - assy_region[ 0 ] )
	  )
      dc.SelectObject( wx.NullBitmap )
    #end if dset is not None and core is not None

    return  bmap  if bmap is not None else self.emptyBitmap
  #end _CreateAssyImage


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateClipboardData()		-
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
  #	METHOD:		Core2DView._CreateClipboardDisplayedData()	-
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
	axial_level = self.axialValue.pinIndex
	#state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = np.array( dset )
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue.pinIndex, dset_shape[ 2 ] - 1 )

      if self.nodalMode:
        clip_shape = ( self.cellRange[ -1 ] << 1, self.cellRange[ -2 ] << 1 )
        clip_data = np.ndarray( clip_shape, dtype = np.float64 )
        clip_data.fill( 0.0 )
	node_row = 0
        for assy_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
	  node_col = 0
	  for assy_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
            assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
	    if assy_ndx >= 0:
	      clip_data[ node_row, node_col ] =  \
	          dset_value[ 0, 0, axial_level, assy_ndx ]
	      clip_data[ node_row, node_col + 1 ] =  \
	          dset_value[ 0, 1, axial_level, assy_ndx ]
	      clip_data[ node_row + 1, node_col ] =  \
	          dset_value[ 0, 2, axial_level, assy_ndx ]
	      clip_data[ node_row + 1, node_col + 1 ] =  \
	          dset_value[ 0, 3, axial_level, assy_ndx ]

            node_col += 2
	  #end for assy_col

	  node_row += 2
        #end for assy_row

      else:
        clip_shape = (
	    dset_shape[ 0 ] * self.cellRange[ -1 ],
            dset_shape[ 1 ] * self.cellRange[ -2 ]
	    )
        clip_data = np.ndarray( clip_shape, dtype = np.float64 )
        clip_data.fill( 0.0 )

        pin_row = 0
        for assy_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
	  pin_row_to = pin_row + dset_shape[ 0 ]

	  pin_col = 0
	  for assy_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	    pin_col_to = pin_col + dset_shape[ 1 ]

            assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
	    if assy_ndx >= 0:
	      clip_data[ pin_row : pin_row_to, pin_col : pin_col_to ] = \
	          dset_value[ :, :, axial_level, assy_ndx ]

	    pin_col = pin_col_to
	  #end for assy_col

	  pin_row = pin_row_to
        #end for assy_row
      #end else not self.nodalMode

      title1 = '"%s: Axial=%.3f; %s=%.3g"' % (
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  self.axialValue.cm,
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
  #	METHOD:		Core2DView._CreateClipboardSelectedData()	-
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
	axial_level = self.axialValue.pinIndex
	#state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = np.array( dset )
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue.pinIndex, dset_shape[ 2 ] - 1 )

      #clip_shape = ( dset_shape[ 0 ], dset_shape[ 1 ] )
      #clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      #clip_data.fill( 0.0 )
      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%s; Axial=%.3f; %s=%.3g"' % (
	  #self.curDataSet.displayName,
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue.cm,
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateCoreDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per pin (deprecated)
    scale_type  'linear' or 'log', defaulting to 'linear'
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
    assemblyAdvance
    assemblyWidth
    coreRegion
    imageSize
    lineWidth
    mode = 'core'
    pinWidth		used for pin or node width, depending on self.nodalMode
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
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

#		-- Must calculate scale?
#		--
    #xxxxx _CreateBaseDrawConfig() sets 
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      assy_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      #xxxxx revisit font_size, bigger than pixel
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)
      assy_ht = region_ht / self.cellRange[ -1 ]

#x      if assy_ht < assy_wd:
#x        assy_wd = assy_ht
      if self.fitMode == 'wd':
        if assy_wd < assy_ht:
          assy_wd = assy_ht
      else:
        if assy_ht < assy_wd:
          assy_wd = assy_ht

      if self.nodalMode:
        pin_wd = max( 1, (assy_wd - 2) >> 1 )
        assy_wd = pin_wd * 2
      elif self.channelMode:
        pin_wd = max( 1, (assy_wd - 2) / (core.npin + 1) )
        assy_wd = pin_wd * (core.npin + 1) + 1
      else:
        pin_wd = max( 1, (assy_wd - 2) / core.npin )
        assy_wd = pin_wd * core.npin + 1
      #x assy_advance = assy_wd
      assy_advance = assy_wd + 1
      core_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = self.cellRange[ -1 ] * assy_advance

    else:  # we don't do this any more
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4

      if self.nodalMode:
        pin_wd <<= 4
        assy_wd = pin_wd << 1
#        if self.logger.isEnabledFor( logging.DEBUG ):
#          self.logger.debug( 'nodalMode=%d, pin_wd=%d', self.nodalMode, pin_wd )
      elif self.channelMode:
        assy_wd = pin_wd * (core.npin + 1) + 1
      else:
        assy_wd = pin_wd * core.npin + 1
      #x assy_advance = assy_wd
      assy_advance = assy_wd + 1

      #font_size = self._CalcFontSize( 768 )

      core_wd = region_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = region_ht = self.cellRange[ -1 ] * assy_advance

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

#               -- For drawing purposes, assy_wd = assy_advance - 1
    #y assy_advance = assy_wd

    region_x = label_size[ 0 ] + 2
    region_y = label_size[ 1 ] + 2
    image_wd = region_x + core_wd + (font_size << 1) + legend_size[ 0 ]
    if legend_size[ 1 ] + 2 > region_y + core_ht:
      #image_ht = legend_size[ 1 ] + 2 + font_size + (font_size >> 1)
      image_ht = legend_size[ 1 ] + 2 + (font_size << 1)
    else:
      image_ht = region_y + core_ht + (font_size << 1) + 2

    config[ 'assemblyAdvance' ] = assy_advance
    config[ 'assemblyWidth' ] = assy_wd
    config[ 'coreRegion' ] = [ region_x, region_y, core_wd, core_ht ]
    config[ 'coreFullRegion' ] = [ region_x, region_y, region_wd, region_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'mode' ] = 'core'
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreImage()			-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, tuple_in, config ):
    try:
      return  self._CreateCoreImageImpl( tuple_in, config )
    except:
      self.logger.exception( "" )
  #end _CreateCoreImag


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreImageImpl()		-
  #----------------------------------------------------------------------
  def _CreateCoreImageImpl( self, tuple_in, config ):
    """Called in background task to create the wx.Bitmap for the state.
@param  tuple_in	0-based ( state_index, axial_level )
"""
    #start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None

    core = dset = None
    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      #xxxxx does this still happen? shouldn't
      if 'coreRegion' not in config:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'coreRegion missing from config, reconfiguring' )
	if 'clientSize' in config:
          config = self._CreateCoreDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateCoreDrawConfig( scale = config[ 'scale' ] )

      assy_advance = config[ 'assemblyAdvance' ]
      assy_wd = config[ 'assemblyWidth' ]
      #im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]

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
      #value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  font, self.curDataSet, dset_shape, self.state.timeDataSet,
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
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      if self.showLabels:
	glabel_font = gc.CreateFont( label_font, wx.BLACK )
        gc.SetFont( glabel_font )

      assy_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
	  ) )
      node_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 100, 100, 100, 255 ), 1, wx.PENSTYLE_SOLID
	  ) )

#			-- Loop on assembly rows
#			--
      assy_y = core_region[ 1 ]
      for assy_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        #xxx check for thread stop
#				-- Row label
#				--
	if self.showLabels:
	  label = core.GetRowLabel( assy_row )
	  label_size = gc.GetFullTextExtent( label )
	  label_y = assy_y + ((assy_wd - label_size[ 1 ]) / 2.0)
	  #gc.DrawText( label, 1, label_y, trans_brush )
	  gc.DrawText( label, 1, label_y )

#				-- Loop on col
#				--
	assy_x = core_region[ 0 ]
	for assy_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  #xxx check for thread stop
	  brush_color = None
#					-- Column label
#					--
	  if assy_row == self.cellRange[ 1 ] and self.showLabels:
	    label = core.GetColLabel( assy_col )
	    text_size = gc.GetFullTextExtent( label )
	    label_size = ( text_size[ 0 ], text_size[ 1 ] )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) / 2.0)
	    #gc.DrawText( label, label_x, 1, trans_brush )
	    gc.DrawText( label, label_x, 1 )
	  #end if writing column label

	  assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

#					-- Assembly exists in the col,row
#					--
	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    item_y = assy_y + 1

#						-- Map to colors
	    cur_array = dset_array[ :, :, axial_level, assy_ndx ]
            colors = mapper.to_rgba( cur_array, bytes = True )
            if item_factors is not None:
	      cur_factors = item_factors[ :, :, axial_level, assy_ndx ]
	      colors[ cur_factors == 0 ] = trans_color_arr
	    colors[ np.isnan( cur_array ) ] = trans_color_arr
	    colors[ np.isinf( cur_array ) ] = trans_color_arr

#						-- Loop on chan/pin rows
	    node_ndx = 0
	    for item_row in xrange( item_row_limit ):
	      item_x = assy_x + 1
#							-- Loop on chan/pin cols
	      cur_item_row = min( item_row, cur_nypin - 1 )
	      if cur_item_row >= 0:
	        for item_col in xrange( item_col_limit ):
	          cur_item_col = min( item_col, cur_nxpin - 1 )
		  if self.nodalMode:
		    cur_color = colors[ 0, node_ndx ]
		  else:
		    cur_color = colors[ cur_item_row, cur_item_col ]

		  if cur_color[ 3 ] > 0:
		    #pen_color = cmap( mapper.norm( value ), bytes = True )
		    #pen_color = mapper.to_rgba( value, bytes = True )
		    pen_color = cur_color.tolist()
	            gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
		        wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
	                ) ) )
	            brush_color = pen_color
	            gc.SetBrush( gc.CreateBrush(
		        wx.TheBrushList.FindOrCreateBrush(
	                    wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
			    )
		        ) )
		    #im_draw.ellipse
	            gc.DrawRectangle( item_x, item_y, pin_wd + 1, pin_wd + 1 )

		    if self.nodalMode:
		      gc.SetBrush( trans_brush )
		      gc.SetPen( node_pen )
	              gc.DrawRectangle( item_x, item_y, pin_wd + 1, pin_wd + 1 )
		      value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
		      node_value_draw_list.append((
			  self._CreateValueString( value ),
                          Widget.GetContrastColor( *brush_color ),
			  item_x, item_y, pin_wd, pin_wd
		          ))
		    #end if nodalMode
	          #end if good value, not hidden by pin_factor

	          item_x += pin_wd
		  if self.nodalMode:
		    node_ndx += 1
	        #end for item_col
	      #end if cur_item_row >= 0

	      item_y += pin_wd
	    #end for item_row

	    gc.SetBrush( trans_brush )
	    gc.SetPen( assy_pen )
	    gc.DrawRectangle( assy_x, assy_y, assy_wd + 1, assy_wd + 1 )
#-- Draw value for cross-pin integration derived datasets
#--
	    if draw_value_flag and brush_color is not None:
	      value = dset_array[ 0, 0, axial_level, assy_ndx ]
	      assy_value_draw_list.append((
	          self._CreateValueString( value ),
                  Widget.GetContrastColor( *brush_color ),
		  assy_x, assy_y, assy_wd, assy_wd
	          ))
	    #end if draw_value_flag
	  #end if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]

	  assy_x += assy_advance
	#end for assy_col

        assy_y += assy_advance
      #end for assy_row

#			-- Draw Values
#			--
      if node_value_draw_list:
        self._DrawValuesWx( node_value_draw_list, gc )

      if assy_value_draw_list:
        self._DrawValuesWx( assy_value_draw_list, gc )

#			-- Draw Legend Image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    #gc.CreateBitmap( legend_bmap ),
	    legend_bmap,
	    core_region[ 0 ] + core_region[ 2 ] + 2 + font_size, 2,
	    legend_bmap.GetWidth(), legend_bmap.GetHeight()
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      #assy_y = max( assy_y, legend_size[ 1 ] + 2 ) + (font_size >> 1)
      if legend_size[ 1 ] + 2 > assy_y:
        assy_y = legend_size[ 1 ] + 2 + (font_size >> 2)
      else:
        assy_y += (font_size >> 1)

      title_str = self._CreateTitleString(
	  title_templ,
	  axial = axial_value.cm,
	  time = self.timeValue
	  #time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      self._DrawStringsWx(
	  gc, font,
#	  ( title_str, ( 0, 0, 0, 255 ),
#	    core_region[ 0 ], assy_y, core_region[ 2 ] - core_region[ 0 ],
#	    'c' )
	  ( title_str, ( 0, 0, 0, 255 ),
	    core_region[ 0 ], assy_y, core_region[ 2 ], 'c',
	    im_wd - core_region[ 0 ] )
	  )

      dc.SelectObject( wx.NullBitmap )
    #end if dset is not None and core is not None

    #elapsed_time = timeit.default_timer() - start_time
    #if self.logger.isEnabledFor( logging.DEBUG ):
      #self.logger.debug( 'time=%.3fs, im-None=%s', elapsed_time, im is None )
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'bmap-None=%s', str( bmap is None ) )

    return  bmap  if bmap is not None else self.emptyBitmap
  #end _CreateCoreImageImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateDrawConfig()			-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys needed by _CreateRasterImage().
"""
#    dset = self.data.GetStateDataSet( 0, self.pinDataSet )
#    if dset is not None and dset.shape[ 0 ] == 1 and dset.shape[ 1 ] == 4:
#      kwargs[ 'nodal' ] = True
    return \
        self._CreateAssyDrawConfig( **kwargs ) if self.mode == 'assy' else \
	self._CreateCoreDrawConfig( **kwargs )
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateRasterImage()			-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config_in = None ):
    """Called in background task to create the wx.Bitmap for the state.
The config and data attributes are good to go.
@param  tuple_in	state tuple
@param  config_in	optional config to use instead of self.config
@return			wx.Bitmap
"""
    return \
        self._CreateAssyImage( tuple_in, config_in ) \
	if self.mode == 'assy' else \
	self._CreateCoreImage( tuple_in, config_in )
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateStateTuple()			-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			mode == 'assy':
			( state_index, assy_ndx, axial_level,
			  assy_col, assy_row )
			mode == 'core':
			( state_index, axial_level )
"""
    dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if self.mode == 'assy':
      assy_ndx = self.assemblyAddr[ 0 ]
      assy_col = self.assemblyAddr[ 1 ]
      assy_row = self.assemblyAddr[ 2 ]
      axial_level = self.axialValue.pinIndex
      if dset is not None:
        if dset.shape[ 2 ] == 1:
          axial_level = 0
        if dset.shape[ 3 ] == 1:
	  assy_ndx = assy_col = assy_row = 0
      #end if dset is not None
      result = ( self.stateIndex, assy_ndx, axial_level, assy_col, assy_row )

    else:
      axial_level = self.axialValue.pinIndex
      if dset is not None:
        if dset.shape[ 2 ] == 1:
          axial_level = 0
      #end if dset is not None
      result = ( self.stateIndex, axial_level )

    return  result
#    return \
#        ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue.pinIndex,
#	  self.assemblyAddr[ 1 ], self.assemblyAddr[ 2 ] ) \
#        if self.mode == 'assy' else \
#        ( self.stateIndex, self.axialValue.pinIndex )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateToolTipText()			-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    if self.mode == 'core' and cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      #if dset is not None and assy_ndx < dset.shape[ 3 ]:
      if dset is not None:
        core = self.dmgr.GetCore()
        assy_ndx = min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
        axial_level = min( self.axialValue.pinIndex, dset.shape[ 2 ] - 1 ),
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
  #	METHOD:		Core2DView.FindAssembly()			-
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
	assy_advance = self.config[ 'assemblyAdvance' ]
	core_region = self.config[ 'coreRegion' ]
	off_x = ev_x - core_region[ 0 ]
	off_y = ev_y - core_region[ 1 ]
        cell_x = min(
	    int( off_x / assy_advance ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
	    int( off_y / assy_advance ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	cell_y = max( self.cellRange[ 1 ], cell_y )

	assy_ndx = core.coreMap[ cell_y, cell_x ] - 1

	pin_wd = self.config[ 'pinWidth' ]
	if self.nodalMode:
	  node_col = int( (off_x % assy_advance) / pin_wd )
	  node_row = int( (off_y % assy_advance) / pin_wd )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  pin_col, pin_row = self.dmgr.GetSubAddrFromNode(
	      node_addr,
	      'channel' if self.channelMode else 'pin'
	      )
	else:
	  pin_col = int( (off_x % assy_advance) / pin_wd )
	  if pin_col >= core.npinx: pin_col = -1
	  pin_row = int( (off_y % assy_advance) / pin_wd )
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
  #	METHOD:		Core2DView.FindCell()				-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() in 'assy' mode or FindAssembly() in 'core' mode.
"""
    result = None
    if self.mode == 'assy':
      pin = self.FindPin( ev_x, ev_y )
      if pin is not None:
	result = ( -1, ) + pin
        #result = ( -1, pin[ 0 ], pin[ 1 ] )
    else:
      result = self.FindAssembly( ev_x, ev_y )

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.FindPin()				-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.  Must be in 'assy' mode.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and 'assemblyRegion' in self.config:
      core = self.dmgr.GetCore()

    if core and ev_x >= 0 and ev_y >= 0:
      assy_region = self.config[ 'assemblyRegion' ]
      pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
	
      if self.nodalMode:
        node_col = min( int( (ev_x - assy_region[ 0 ]) / pin_size ), 1 )
	node_row = min( int( (ev_y - assy_region[ 1 ]) / pin_size ), 1 )
#	node_addr = 2 if node_row > 0 else 0
#	if node_col > 0:
#	  node_addr += 1
	node_addr = DataUtils.GetNodeAddr( node_col, node_row )
	cell_x, cell_y = self.dmgr.GetSubAddrFromNode(
	    node_addr,
	    'channel' if self.channelMode else 'pin'
	    )

      else:
	cell_x = int( (ev_x - assy_region[ 0 ]) / pin_size )
        cell_y = int( (ev_y - assy_region[ 1 ]) / pin_size )
	if self.channelMode:
	  cell_x = min( cell_x, core.npinx )
	  cell_y = min( cell_y, core.npiny )
	else:
	  cell_x = min( cell_x, core.npinx - 1 )
	  cell_y = min( cell_y, core.npiny - 1 )

        node_addr = self.dmgr.GetNodeAddr(
	    ( cell_x, cell_y ),
	    'channel' if self.channelMode else 'pin'
	    )
	result = ( cell_x, cell_y, node_addr )
    #end if core and ev_x >= 0 and ev_y >= 0

    return  result
  #end FindPin


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetDataSetTypes()			-
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
  #	METHOD:		Core2DView.GetEventLockSet()			-
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
  #	METHOD:		Core2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
#  def GetPrintScale( self ):
#    """
#@return		24 in 'assy' mode, 4 in 'core' mode
#"""
#    #return  24 if self.mode == 'assy' else 4
#    return  24 if self.mode == 'assy' else 100
#  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None:
      line_wd = config[ 'lineWidth' ]
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
            HILITE_COLOR_primary,
	    line_wd, wx.PENSTYLE_SOLID
	    )
        secondary_pen = wx.ThePenList.FindOrCreatePen(
	    HILITE_COLOR_secondary,
	    line_wd, wx.PENSTYLE_SOLID
	    )
      else:
        select_pen = wx.ThePenList.FindOrCreatePen(
            HILITE_COLOR_primary,
	    line_wd, wx.PENSTYLE_SOLID
	    )
      #end if-else self.nodalMode

#			-- Core mode
#			--
      if config[ 'mode' ] == 'core':
        rel_col = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
        rel_row = self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
          assy_adv = config[ 'assemblyAdvance' ]
	  assy_wd = config[ 'assemblyWidth' ]
	  core_region = config[ 'coreRegion' ]

	  rect = \
	    [
	      rel_col * assy_adv + core_region[ 0 ],
	      rel_row * assy_adv + core_region[ 1 ],
	      assy_wd, assy_wd
	    ]
	  draw_list.append( ( rect, select_pen ) )

#					-- Core nodal
	  if self.nodalMode:
	    node_wd = config[ 'pinWidth' ]
            for i in xrange( len( node_addr_list ) ):
	      node_addr = node_addr_list[ i ]
	      if node_addr >= 0:
	        rel_x = node_wd if node_addr in ( 1, 3 ) else half_line_wd
	        rel_y = node_wd if node_addr in ( 2, 3 ) else half_line_wd
	        node_rect = [
	            rect[ 0 ] + rel_x, rect[ 1 ] + rel_y,
		    node_wd - half_line_wd, node_wd - half_line_wd
		    ]
		#pen = primary_pen if i == 0 else secondary_pen
		pen = \
		    secondary_pen if i < len( node_addr_list ) - 1 else \
		    primary_pen
	        draw_list.append( ( node_rect, pen ) )
	      #end if valid node addr
	    #end for i
	  #end if nodalMode
        #end if cell in drawing range

#			-- Assy nodal mode
#			--
      elif self.nodalMode:
        assy_region = config[ 'assemblyRegion' ]
        pin_gap = config[ 'pinGap' ]
	pin_wd = config[ 'pinWidth' ]
	pin_adv = pin_wd + pin_gap

	for i in xrange( len( node_addr_list ) ):
	  node_addr = node_addr_list[ i ]
	  if node_addr >= 0:
	    rel_x = pin_adv if node_addr in ( 1, 3 ) else 0
	    rel_y = pin_adv if node_addr in ( 2, 3 ) else 0
	    node_rect = [
		assy_region[ 0 ] + rel_x,
		assy_region[ 1 ] + rel_y,
		pin_wd, pin_wd
		]
	    #pen = primary_pen if i == 0 else secondary_pen
	    pen = \
	        secondary_pen if i < len( node_addr_list ) - 1 else primary_pen
	    draw_list.append( ( node_rect, pen ) )
	  #end if valid node addr
	#end for i

#			-- Assy not nodal mode
#			--
      else:  # 'assy'
	if self.subAddr[ 0 ] >= 0 and self.subAddr[ 1 ] >= 0 and \
	    self.subAddr[ 0 ] < core.npinx and \
	    self.subAddr[ 1 ] < core.npiny:
          assy_region = config[ 'assemblyRegion' ]
	  pin_gap = config[ 'pinGap' ]
	  pin_wd = config[ 'pinWidth' ]
	  pin_adv = pin_wd + pin_gap
	  rect = \
	    [
	      self.subAddr[ 0 ] * pin_adv + assy_region[ 0 ],
	      self.subAddr[ 1 ] * pin_adv + assy_region[ 1 ],
	      pin_adv, pin_adv
	    ]
	  draw_list.append( ( rect, select_pen ) )
        #end if cell in drawing range
      #end if-else on mode

#			-- Draw?
#			--
      #if rect is not None:
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
    #end if config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._InitEventHandlers()			-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    self._SetMode( 'core' )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = False

    dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if self.mode == 'assy':
      assy_ndx = self.assemblyAddr[ 0 ]
      assy_col = self.assemblyAddr[ 1 ]
      assy_row = self.assemblyAddr[ 2 ]
      axial_level = self.axialValue.pinIndex
      if dset is not None:
        if dset.shape[ 2 ] == 1:
          axial_level = 0
        if dset.shape[ 3 ] == 1:
	  assy_ndx = assy_col = assy_row = 0
      #end if dset is not None

      result = \
          tpl is not None and len( tpl ) >= 5 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == assy_ndx and \
	  tpl[ 2 ] == axial_level and \
	  tpl[ 3 ] == assy_col and \
	  tpl[ 4 ] == assy_row

    else:
      axial_level = self.axialValue.pinIndex
      if dset is not None:
        if dset.shape[ 2 ] == 1:
          axial_level = 0
      #end if dset is not None

      result = \
          tpl is not None and len( tpl ) >= 2 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == axial_level

    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.IsTupleCurrent_1()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent_1( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = False

    if self.mode == 'assy':
      result = \
          tpl is not None and len( tpl ) >= 5 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == self.assemblyAddr[ 0 ] and \
	  tpl[ 2 ] == self.axialValue.pinIndex and \
	  tpl[ 3 ] == self.assemblyAddr[ 1 ] and \
	  tpl[ 4 ] == self.assemblyAddr[ 2 ]

    else:
      result = \
          tpl is not None and len( tpl ) >= 2 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == self.axialValue.pinIndex

    return  result
  #end IsTupleCurrent_1


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """
"""
    if (reason & STATE_CHANGE_coordinates) > 0:
      self.assemblyAddr = self.state.assemblyAddr
      self.subAddr = self.state.subAddr
    if (reason & STATE_CHANGE_curDataSet) > 0:
      self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Core2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnClick()				-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()
    is_aux = self.IsAuxiliaryEvent( ev )
    click_count = ev.GetClickCount()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnClickImpl, x, y, is_aux, click_count )
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnClickImpl()                       -
  #----------------------------------------------------------------------
  def _OnClickImpl( self, x, y, is_aux, click_count ):
    """
"""
    cell_info = self.FindAssembly( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_addr = cell_info[ 0 : 3 ]
      if assy_addr != self.assemblyAddr:
	state_args[ 'assembly_addr' ] = assy_addr

      if self.nodalMode:
        node_addr = cell_info[ 5 ]
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
	elif click_count > 1:
	  sub_addr = self.dmgr.GetSubAddrFromNode(
	      node_addr,
	      'channel' if self.channelMode else 'pin'
	      )
	  if sub_addr != self.subAddr:
	    state_args[ 'sub_addr' ] = sub_addr
	#end if-elif is_aux

      elif click_count > 1:
        pin_addr = cell_info[ 3 : 5 ]
        if pin_addr != self.subAddr:
	  state_args[ 'sub_addr' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClickImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnDragFinished()			-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    if right - left == 1 and bottom - top == 1:
      self.assemblyAddr = self.dragStartCell
      self._SetMode( 'assy' )
      self.FireStateChange( assembly_addr = self.assemblyAddr )
    else:
      self._SetMode( 'core' )
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    self.GetTopLevelParent().GetApp().DoBusyEventOp(
        self._OnFindMinMaxImpl, mode, all_states_flag, all_assy_flag
        )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnFindMinMaxImpl()			-
  #----------------------------------------------------------------------
  def _OnFindMinMaxImpl( self, mode, all_states_flag, all_assy_flag ):
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
  #end _OnFindMinMaxImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseMotionAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''

    dset = None
    pin_info = self.FindPin( *ev.GetPosition() )
    if pin_info is not None:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      axial_level = min( self.axialValue.pinIndex, dset.shape[ 2 ] - 1 )
      assy_ndx = self.assemblyAddr[ 0 ]
      pin_factors = None

      if self.nodalMode:
        if self.state.weightsMode == 'on':
          pin_factors = self.dmgr.GetFactors( self.curDataSet )
        node_addr = pin_info[ 2 ]
	if node_addr < dset.shape[ 1 ] and assy_ndx < dset.shape[ 3 ]:
	  pin_factor = 1
	  if pin_factors is not None:
	    pin_factor = pin_factors[ 0, node_addr, axial_level, assy_ndx ]
          pin_value = dset[ 0, node_addr, axial_level, assy_ndx ]
	  if not ( pin_factor == 0 or self.dmgr.IsBadValue( pin_value ) ):
            tip_str = 'Node: %d\n%s: %g' % (
	        node_addr + 1,
	        self.dmgr.GetDataSetDisplayName( self.curDataSet ),
		pin_value
		)
	#end if node_addr and assy_ndx valid

      else:
        if self.state.weightsMode == 'on':
          pin_factors = self.dmgr.GetFactors( self.curDataSet )
        pin_addr = pin_info[ 0 : 2 ]
        if pin_addr[ 1 ] < dset.shape[ 0 ] and \
	    pin_addr[ 0 ] < dset.shape[ 1 ] and \
	    assy_ndx < dset.shape[ 3 ]:
	  pin_factor = 1
	  if pin_factors is not None:
	    pin_factor = pin_factors[
	        pin_addr[ 1 ], pin_addr[ 0 ],
		axial_level, assy_ndx
		]
          pin_value = \
	      dset[ pin_addr[ 1 ], pin_addr[ 0 ], axial_level, assy_ndx ]
	  if not ( pin_factor == 0 or self.dmgr.IsBadValue( pin_value ) ):
	    pin_rc = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
            tip_str = 'Pin: %s\n%s: %g' % (
	        str( pin_rc ),
	        self.dmgr.GetDataSetDisplayName( self.curDataSet ),
		pin_value
		)
      #end if-else nodalMode
    #end if dset

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    pos = ev.GetPosition()
    is_aux = self.IsAuxiliaryEvent( ev )
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnMouseUpAssyImpl, pos, is_aux )
  #end _OnMouseUpAssy


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseUpAssyImpl()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssyImpl( self, pos, is_aux ):
    """
"""
    pin_info = self.FindPin( *pos )
    if pin_info is None:
      pass

    elif self.nodalMode:
      node_addr = pin_info[ 2 ]
      valid = self.dmgr.IsValid( self.curDataSet, node_addr = node_addr )
      if valid:
	if is_aux:
	  addrs = list( self.auxNodeAddrs )
	  if node_addr in addrs:
	    addrs.remove( node_addr )
	  else:
	    addrs.append( node_addr )
	  self.FireStateChange( aux_node_addrs = addrs )
	else:
          self.FireStateChange( node_addr = node_addr, aux_node_addrs = [] )
      #end if valid

    else:
      pin_addr = pin_info[ 0 : 2 ]
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      if dset is not None:
        if pin_addr[ 1 ] < dset.shape[ 0 ] and \
	    pin_addr[ 0 ] < dset.shape[ 1 ] and \
	    self.assemblyAddr[ 0 ] < dset.shape[ 3 ]:
          pin_value = dset[
	      pin_addr[ 1 ], pin_addr[ 0 ],
	      min( self.axialValue.pinIndex, dset.shape[ 2 ] - 1 ),
	      self.assemblyAddr[ 0 ]
	      ]
	  if not self.dmgr.IsBadValue( pin_value ):
	    self.FireStateChange( sub_addr = pin_addr )
      #end if dset
    #end if-else
  #end _OnMouseUpAssyImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnUnzoom()				-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._SetMode( 'core' )
      #self.Redraw()  # self._OnSize( None )
      self.GetTopLevelParent().GetApp().DoBusyEventOp( self.Redraw )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Core2DView, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._SetMode()				-
  #----------------------------------------------------------------------
  def _SetMode( self, mode ):
    """Must be called from the UI thread.
"""
    if mode != self.mode:
      if mode == 'assy':
        self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, None )
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnMouseUpAssy )
        self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotionAssy )

      else:  # if mode == 'core':
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

	super( Core2DView, self )._InitEventHandlers()
      #end if-else

      self.mode = mode
    #end if different mode
  #end _SetMode


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._UpdateDataSetStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type, clear_zoom_stack = False ):
    """Updates the nodalMode property.
    Args:
        ds_type (str): dataset category/type
	clear_zoom_stack (boolean): True to clear in zoom stack
"""
    #no self.channelMode = ds_type == 'channel'
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._UpdateStateValues()			-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Core2DView, self )._UpdateStateValues( **kwargs )
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

#end Core2DView
