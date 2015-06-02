#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		channel_view.py					-
#	HISTORY:							-
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-23	leerw@ornl.gov				-
#		2015-05-21	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, threading, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from event.state import *
from legend import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Channel2DView					-
#------------------------------------------------------------------------
class Channel2DView( Widget ):
  """Channel-by-channel core and assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.avgValues = {}
    self.axialValue = ( 0.0, -1, -1 )
    self.bitmaps = {}  # key is (row,col)
    self.bitmapsLock = threading.RLock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.channelColRow = None
    self.config = None
    self.curSize = None
    self.data = None
    self.dataSetName = kwargs.get( 'dataset', 'channel_liquid_temps [C]' )
    self.dragStartAssembly = None
    self.dragStartPosition = None

    self.menuDefs = \
      [
	( 'Hide Labels', self._OnToggleLabels ),
	( 'Hide Legend', self._OnToggleLegend ),
        ( 'Unzoom', self._OnUnzoom )
      ]
    self.mode = ''  # 'assy', 'core'
    self.showLabels = True
    self.showLegend = True
    self.stateIndex = -1

#    self.axialBean = None
    self.bitmapCtrl = None
    self.bitmapPanel = None
    self.blankBitmap = self.GetBitmap( 'loading' )

    self.overlay = None
    self.pilFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Black.ttf' )
#        os.path.join( Config.GetRootDir(), 'res/Times New Roman Bold.ttf' )
    self.popupMenu = None
    self.valueFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' )

    super( Channel2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._BitmapThreadFinish()		-
  #----------------------------------------------------------------------
  def _BitmapThreadFinish( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
"""
    if result == None:
      cur_pair = pil_im = None
    else:
      cur_pair, pil_im = result.get()
    print >> sys.stderr, \
        '[Channel2DView._BitmapThreadFinish] cur=%s, pil_im=%s' % \
	( cur_pair, pil_im != None )

    if cur_pair != None:
#			-- Create bitmap
#			--
      if pil_im == None:
        bmap = self.blankBitmap

      else:
        wx_im = wx.EmptyImage( *pil_im.size )

        pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
        wx_im.SetData( pil_im_data_str )

        pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
        wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

        bmap = wx.BitmapFromImage( wx_im )

	self.bitmapsLock.acquire()
	try:
	  self.bitmaps[ cur_pair ] = bmap
	finally:
	  self.bitmapsLock.release()
      #end else pil_im not None

      if cur_pair[ 0 ] == self.stateIndex and cur_pair[ 1 ] == self.axialValue[ 1 ]:
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
    #end if cur_pair != None:

    self._BusyEnd()
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._BitmapThreadStart()		-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, next_pair ):
    """Background thread task to create the wx.Bitmap for the next
pair in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateAssyImage() or _CreateCoreImage().
@param  next_pair	( state_ndx, (core) axial_ndx )
"""
#    print >> sys.stderr, \
#        '[Channel2DView._BitmapThreadStart] next=%s' % str( next_pair )
    pil_im = None

    if next_pair != None and self.config != None:
      if self.config.get( 'mode' ) == 'assy':
        pil_im = self._CreateAssyImage(
	    self.config, self.data, self.dataSetName,
	    next_pair + self.assemblyIndex
	    )
      else:
        pil_im = self._CreateCoreImage(
	    self.config, self.data, self.dataSetName, next_pair
	    )
    #end if next_pair exists

    return  ( next_pair, pil_im )
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._ClearBitmaps()			-
  # Must be called from the UI thread.
  # @param  keep_pair	0-based ( state_ndx, axial_level ) to keep, or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_pair = None ):
    self.bitmapsLock.acquire()
    try:
      self.bitmapCtrl.SetBitmap( self.blankBitmap )

      pairs = list( self.bitmaps.keys() )
      for p in pairs:
	if keep_pair == None or keep_pair != p:
          b = self.bitmaps[ p ]
	  del self.bitmaps[ p ]
	  b.Destroy()
      #end for
    finally:
      self.bitmapsLock.release()
  #end _ClearBitmaps


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._Configure()			-
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    wd, ht = self.bitmapPanel.GetClientSize()
    print >> sys.stderr, '[Channel2DView._Configure] %d,%d' % ( wd, ht )

    self.config = None
    if wd > 0 and ht > 0 and self.data and self.data.HasData() and self.cellRange != None:
#      if self.cellRange[ -2 ] == 1 and self.cellRange[ -1 ] == 1:
      if self.mode == 'assy':
        self.config = self._CreateAssyDrawConfig(
	    self.data, self.dataSetName,
	    size = ( wd, ht )
	    )
      else:  # if self.mode == 'core'
        self.config = self._CreateCoreDrawConfig(
            self.data, self.dataSetName, self.cellRange,
	    size = ( wd, ht )
	    )
  #end _Configure


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateAssyDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateAssyDrawConfig( self, data, ds_name, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per channel) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  data		data model
@param  ds_name		dataset name
@param  kwargs
    scale	pixels per channel
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    assemblyWidth
    channelGap
    channelWidth
    clientSize
    fontSize
    labelFont
    legendPilImage
    lineWidth
    mode = 'assy'
    pilFont
"""

    ds_range = data.GetRange( ds_name )

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[Assembly2DView._CreateDrawConfig] size=%d,%d' % ( wd, ht )

      font_size = self._CalcFontSize( wd )
#      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
      if self.showLegend:
        legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
	legend_size = legend_pil_im.size
      else:
        legend_pil_im = None
	legend_size = ( 0, 0 )

      label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
#      label_size = label_font.getsize( '99' )
      label_size = \
          label_font.getsize( '99' ) \
	  if self.showLabels else \
	  ( 0, 0 )

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      chan_adv_wd = region_wd / (data.core.npin + 1)

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      chan_adv_ht = region_ht / (data.core.npin + 1)

      if chan_adv_ht < chan_adv_wd:
        chan_adv_wd = chan_adv_ht

      #chan_gap = chan_adv_wd >> 3
      chan_gap = 0
      chan_wd = max( 1, chan_adv_wd - chan_gap )

      assy_wd = assy_ht = (data.core.npin + 1) * (chan_wd + chan_gap)

    else:
      chan_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 24
      print >> sys.stderr, '[Assembly2DView._CreateDrawConfig] chan_wd=%d' % chan_wd

      #chan_gap = chan_wd >> 3
      chan_gap = 0
      assy_wd = assy_ht = (data.core.npin + 1) * (chan_wd + chan_gap)

      font_size = self._CalcFontSize( 512 )
#      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
      if self.showLegend:
        legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
	legend_size = legend_pil_im.size
      else:
        legend_pil_im = None
	legend_size = ( 0, 0 )

      label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
      label_size = \
          label_font.getsize( '99' ) \
	  if self.showLabels else \
	  ( 0, 0 )

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size
    #end if-else

    print >> sys.stderr, \
        '[Assembly2DView._CreateDrawConfig] font_size=%d, legend_size=%s, chan_wd=%d, chan_gap=%d, wd=%d, ht=%d' % \
	  ( font_size, str( legend_size ), chan_wd, chan_gap, wd, ht )

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    config = \
      {
      'assemblyRegion': [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ],
      'channelGap': chan_gap,
      'channelWidth': chan_wd,
      'clientSize': ( wd, ht ),
      'fontSize': font_size,
      'labelFont': label_font,
      'legendPilImage': legend_pil_im,
      'lineWidth': max( 1, chan_gap ),
      'mode': 'assy',
      'pilFont': pil_font
      }

    return  config
  #end _CreateAssyDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateAssyImage()		-
  #----------------------------------------------------------------------
  def _CreateAssyImage( self, config, data, ds_name, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  tuple_in	0-based
			( state_index, axial_level, assy_ndx, assy_col, assy_row )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    assy_ndx = tuple_in[ 2 ]
    print >> sys.stderr, \
        '[Channel2DView._CreateAssyImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = data.IsValid(
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    if config != None and tuple_valid:
#			-- Draw channel "cells"
#			--
      assy_region = config[ 'assemblyRegion' ]
      chan_gap = config[ 'channelGap' ]
      chan_wd = config[ 'channelWidth' ]
      im_wd, im_ht = config[ 'clientSize' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]

      title_fmt = '%s: Assembly %%d, Axial %%.3f, %s %%.3g' % \
          ( ds_name, self.state.timeDataSet )
      #title_fmt = '%s: Assembly %%d, Axial %%.3f, Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % ( 99, 99.999, 99.999 ) )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      chan_y = assy_region[ 1 ]
      for chan_row in range( data.core.npin + 1 ):
#				-- Row label
#				--
	if self.showLabels and chan_row < data.core.npin:
	  label = '%d' % (chan_row + 1)
	  label_size = label_font.getsize( label )
	  #label_y = chan_y + ((chan_wd - label_size[ 1 ]) >> 1)
	  label_y = chan_y + chan_wd + ((chan_gap - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )

#				-- Loop on col
#				--
	chan_x = assy_region[ 0 ]
	for chan_col in range( data.core.npin + 1 ):
#					-- Column label
#					--
	  if chan_row == 0 and self.showLabels and chan_col < data.core.npin:
	    label = '%d' % (chan_col + 1)
	    label_size = label_font.getsize( label )
	    #label_x = chan_x + ((chan_wd - label_size[ 0 ]) >> 1)
	    label_x = chan_x + chan_wd + ((chan_gap - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ), label,
		fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  value = 0.0
	  if ds_value != None:
#	    value = ds_value[ chan_col, chan_row, axial_level, assy_ndx ]
	    value = ds_value[ chan_row, chan_col, axial_level, assy_ndx ]
	  if value > 0.0:
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    #ellipse
	    im_draw.rectangle(
	        [ chan_x, chan_y, chan_x + chan_wd, chan_y + chan_wd ],
	        fill = brush_color, outline = pen_color
	        )
	  #end if value > 0

	  chan_x += chan_wd + chan_gap
	#end for chan_col

	chan_y += chan_wd + chan_gap
      #end for chan_row

#			-- Draw pins
#			--
      brush_color = ( 155, 155, 155, 128 )
      pen_color = Widget.GetDarkerColor( brush_color, 128 )
      pin_draw_wd = chan_wd >> 1

      pin_y = assy_region[ 1 ] + chan_wd + ((chan_gap - pin_draw_wd) >> 1)
      for pin_row in range( data.core.npin ):
	pin_x = assy_region[ 0 ] + chan_wd + ((chan_gap - pin_draw_wd) >> 1)
	for pin_col in range( data.core.npin ):
	  im_draw.ellipse(
	      [ pin_x, pin_y, pin_x + pin_draw_wd, pin_y + pin_draw_wd ],
	      fill = brush_color, outline = pen_color
	      )

	  pin_x += chan_wd + chan_gap
	#end for pin_col

	pin_y += chan_wd + chan_gap
      #end for pin_row

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( assy_wd + font_size, 1 ) )
      if legend_pil_im != None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 2 ] + 2 + font_size, assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      chan_y = max( chan_y, legend_size[ 1 ] )
      chan_y += font_size >> 2

      title_str = title_fmt % ( \
	  assy_ndx + 1,
	  data.core.axialMeshCenters[ axial_level ],
	  data.GetTimeValue( state_ndx, self.state.timeDataSet )
#	  data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, chan_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    return  im
  #end _CreateAssyImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateCoreDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateCoreDrawConfig( self, data, ds_name, cell_range, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per channel) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  data		data model
@param  ds_name		dataset name
@param  cell_range	cell range to display
@param  kwargs
    scale	pixels per channel
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    assemblyAdvance
    assemblyWidth
    channelWidth
    clientSize
    coreRegion
    fontSize
    labelFont
    legendPilImage
    lineWidth
    mode = 'core'
    pilFont
"""

    ds_range = data.GetRange( ds_name )

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[Channel2DView._CreateCoreDrawConfig] size=%d,%d' % ( wd, ht )

      font_size = self._CalcFontSize( wd )
#      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
      if self.showLegend:
        legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
	legend_size = legend_pil_im.size
      else:
        legend_pil_im = None
	legend_size = ( 0, 0 )

      label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
#      label_size = label_font.getsize( '99' )
      label_size = \
          label_font.getsize( '99' ) \
	  if self.showLabels else \
	  ( 0, 0 )

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      assy_wd = region_wd / cell_range[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      assy_ht = region_ht / cell_range[ -1 ]

      if assy_ht < assy_wd:
        assy_wd = assy_ht

      chan_wd = max( 1, (assy_wd - 2) / (data.core.npin + 1) )
      assy_wd = chan_wd * (data.core.npin + 1) + 1
      assy_advance = assy_wd
      core_wd = cell_range[ -2 ] * assy_advance
      core_ht = cell_range[ -1 ] * assy_advance

    else:
      chan_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4
      print >> sys.stderr, '[Channel2DView._CreateCoreDrawConfig] chan_wd=%d' % chan_wd
      assy_wd = chan_wd * (data.core.npin + 1) + 1
      assy_advance = assy_wd

      font_size = self._CalcFontSize( 768 )
      #legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
      if self.showLegend:
        legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
	legend_size = legend_pil_im.size
      else:
        legend_pil_im = None
	legend_size = ( 0, 0 )

      core_wd = cell_range[ -2 ] * assy_advance
      core_ht = cell_range[ -1 ] * assy_advance

      label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
#      label_size = label_font.getsize( '99' )
      label_size = \
          label_font.getsize( '99' ) \
	  if self.showLabels else \
	  ( 0, 0 )

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size
    #end if-else

    print >> sys.stderr, \
        '[Channel2DView._CreateCoreDrawConfig] font_size=%d, legend_size=%s, assy_wd=%d, core_wd=%d, wd=%d, ht=%d' % \
	  ( font_size, str( legend_size ), assy_wd, core_wd, wd, ht )

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    config = \
      {
      'assemblyAdvance': assy_advance,
      'assemblyWidth': assy_wd,
      'channelWidth': chan_wd,
      'clientSize': ( wd, ht ),
      'coreRegion': [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ],
      'fontSize': font_size,
      'labelFont': label_font,
      'legendPilImage': legend_pil_im,
      'lineWidth': max( 1, min( 10, int( assy_wd / 20.0 ) ) ),
      'mode': 'core',
      'pilFont': pil_font
      }

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, config, data, ds_name, pair ):
    """Called in background task to create the PIL image for the state.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  pair		0-based ( state_index, axial_level )
"""
    state_ndx = pair[ 0 ]
    axial_level = pair[ 1 ]
    print >> sys.stderr, \
        '[Channel2DView._CreateCoreImage] pair=%d,%d' % \
	( state_ndx, axial_level )
    im = None

    if config != None:
      assy_advance = config[ 'assemblyAdvance' ]
      assy_wd = config[ 'assemblyWidth' ]
      chan_wd = config[ 'channelWidth' ]
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]

      title_fmt = '%s: Axial %%.3f, %s %%.3g' % \
          ( ds_name, self.state.timeDataSet )
      #title_fmt = '%s: Axial %%.3f, Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % ( 99, 99.999 ) )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )

#			-- Loop on assembly rows
#			--
      assy_y = core_region[ 1 ]
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        core_data_row = data.core.coreMap[ assy_row, : ]

#				-- Row label
#				--
	if self.showLabels:
	  label = data.core.coreLabels[ 1 ][ assy_row ]
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
#					-- Column label
#					--
	  if assy_row == self.cellRange[ 1 ] and self.showLabels:
	    label = data.core.coreLabels[ 0 ][ assy_col ]
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  assy_ndx = core_data_row[ assy_col ] - 1

	  if assy_ndx >= 0:
	    chan_y = assy_y + 1
	    for chan_row in range( data.core.npin + 1 ):
	      chan_x = assy_x + 1
	      for chan_col in range( data.core.npin + 1 ):
		value = 0.0
	        if ds_value != None:
		  value = ds_value[ chan_row, chan_col, axial_level, assy_ndx ]
		if value > 0.0:
	          pen_color = Widget.GetColorTuple(
	              value - ds_range[ 0 ], value_delta, 255
	              )
	          brush_color = \
		      ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
		  #im_draw.ellipse
	          im_draw.rectangle(
		      [ chan_x, chan_y, chan_x + chan_wd, chan_y + chan_wd ],
		      fill = brush_color, outline = pen_color
		      )
		#end if value gt 0
	        chan_x += chan_wd
	      #end for chan cols

	      chan_y += chan_wd
	    #end for chan rows

	    im_draw.rectangle(
		[ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
		fill = None, outline = assy_pen
	        )
	  #end if assembly referenced

	  assy_x += assy_advance
	#end for assy_col

        assy_y += assy_advance
      #end for assy_row

#			-- Draw Legend Image
#			--
      if legend_pil_im != None:
        im.paste(
	    legend_pil_im,
	    ( core_region[ 2 ] + 2 + font_size, core_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      assy_y = max( assy_y, legend_size[ 1 ] )
      assy_y += font_size >> 2

      title_str = title_fmt % ( \
	  data.core.axialMeshCenters[ axial_level ],
	  data.GetTimeValue( state_ndx, self.state.timeDataSet )
#	  data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (core_region[ 3 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, assy_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    return  im
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.CreateImage()			-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    wx_im = None

    if self.mode == 'assy':
      config = self._CreateAssyDrawConfig(
	  self.data, self.dataSetName,
	  scale = 24
          )
      pil_im = self._CreateAssyImage(
          config, self.data, self.dataSetName,
	  ( self.stateIndex, self.axialValue[ 1 ] ) + self.assemblyIndex
#	  ( self.stateIndex, self.axialLevel ) + self.assemblyIndex
	  )
    else:  # if self.mode == 'core':
      config = self._CreateCoreDrawConfig(
          self.data, self.dataSetName, self.cellRange,
	  scale = 4
	  )
      pil_im = self._CreateCoreImage(
          config, self.data, self.dataSetName,
	  ( self.stateIndex, self.axialValue[ 1 ] )
#	  ( self.stateIndex, self.axialLevel )
	  )
    #end if-else

    wx_im = wx.EmptyImage( *pil_im.size )

    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
    wx_im.SetData( pil_im_data_str )

    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

    return  wx_im
  #end CreateImage


  #----------------------------------------------------------------------
  #     METHOD:         Channel2DView.CreatePopupMenu()			-
  #----------------------------------------------------------------------
  def CreatePopupMenu( self ):
    """Lazily creates.  Must be called from the UI thread.
"""
    if self.popupMenu == None:
      self.popupMenu = wx.Menu()

      for label, handler in self.menuDefs:
        item = wx.MenuItem( self.popupMenu, wx.ID_ANY, label )
        self.Bind( wx.EVT_MENU, handler, item )
        self.popupMenu.AppendItem( item )
      #end for

      self._UpdateVisibilityMenuItems(
          self.popupMenu,
	  'Labels', self.showLabels,
	  'Legend', self.showLegend
	  )
    #end if must create menu

    return  self.popupMenu
  #end CreatePopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row, chan_col, chan_row )
"""
    result = None

    if self.config != None and self.data != None and \
        self.data.core != None and self.data.core.coreMap != None:
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

	assy_ndx = self.data.core.coreMap[ cell_y, cell_x ] - 1

	chan_wd = self.config[ 'channelWidth' ]
	chan_col = int( (off_x % assy_advance) / chan_wd )
	if chan_col > self.data.core.npin: chan_col = -1
	chan_row = int( (off_y % assy_advance) / chan_wd )
	if chan_row > self.data.core.npin: chan_row = -1

	result = ( assy_ndx, cell_x, cell_y, chan_col, chan_row )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.FindChannel()			-
  #----------------------------------------------------------------------
  def FindChannel( self, ev_x, ev_y ):
    """Finds the channel index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    if self.config != None and self.data != None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        chan_size = self.config[ 'channelWidth' ] + self.config[ 'channelGap' ]
        cell_x = min(
	    int( (ev_x - assy_region[ 0 ]) / chan_size ),
	    self.data.core.npin
	    )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / chan_size ),
	    self.data.core.npin
	    )

	result = ( cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindChannel


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetAxialLevel()			-
  #----------------------------------------------------------------------
#  def GetAxialLevel( self ):
#    """@return		0-based axial level
#"""
#    return  self.axialLevel
#  #end GetAxialLevel


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'channel'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_channelColRow, STATE_CHANGE_channelDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
#    return  Channel2DView.MENU_DEFS
    return  self.menuDefs
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.HandleMenuItem()			-
  #----------------------------------------------------------------------
#  def HandleMenuItem( self, id ):
#    """
#"""
#    if id == Channel2DView.MENU_ID_unzoom:
#      self._OnUnzoom( None )
#  #end HandleMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.HandleStateChange()		-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    print >> sys.stderr, \
        '[Channel2DView.HandleStateChange] reason=%d' % reason
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[Channel2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      state_args = {}
      if (reason & STATE_CHANGE_assemblyIndex) > 0:
        if self.state.assemblyIndex != self.assemblyIndex:
	  state_args[ 'assembly_index' ] = self.state.assemblyIndex
#	  wx.CallAfter(
#	      self._UpdateState,
#	      assembly_index = self.state.assemblyIndex
#	      )

      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
	  state_args[ 'axial_value' ] = self.state.axialValue
#      if (reason & STATE_CHANGE_axialLevel) > 0:
#        if self.state.axialLevel != self.axialLevel:
#	  state_args[ 'axial_level' ] = self.state.axialLevel
##          wx.CallAfter( self._UpdateState, axial_level = self.state.axialLevel )

      if (reason & STATE_CHANGE_channelColRow) > 0:
        if self.state.channelColRow != self.channelColRow:
	  state_args[ 'channel_colrow' ] = self.state.channelColRow

      if (reason & STATE_CHANGE_channelDataSet) > 0:
        if self.state.channelDataSet != self.dataSetName:
	  state_args[ 'channel_dataset' ] = self.state.channelDataSet

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  state_args[ 'state_index' ] = self.state.stateIndex

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        state_args[ 'resized' ] = True

      if len( state_args ) > 0:
        wx.CallAfter( self._UpdateState, **state_args )
    #end else not a data model load
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config != None:
      line_wd = -1
      rect = None

      if self.cellRange[ -2 ] == 1 and self.cellRange[ -1 ] == 1:
        pass

#			-- Core mode
#			--
      elif self.config[ 'mode' ] == 'core':
        rel_col = self.assemblyIndex[ 1 ] - self.cellRange[ 0 ]
        rel_row = self.assemblyIndex[ 2 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
          assy_adv = self.config[ 'assemblyAdvance' ]
	  assy_wd = self.config[ 'assemblyWidth' ]
	  core_region = self.config[ 'coreRegion' ]
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      rel_col * assy_adv + core_region[ 0 ],
	      rel_row * assy_adv + core_region[ 1 ],
	      assy_wd, assy_wd
	    ]
        #end if cell in drawing range

#			-- Assy mode
#			--
      else:  # 'assy'
	if self.channelColRow[ 0 ] >= 0 and self.channelColRow[ 1 ] >= 0 and \
	    self.channelColRow[ 0 ] < self.data.core.npin and \
	    self.channelColRow[ 1 ] < self.data.core.npin:
          assy_region = self.config[ 'assemblyRegion' ]
	  chan_gap = self.config[ 'channelGap' ]
	  chan_wd = self.config[ 'channelWidth' ]
	  chan_adv = chan_wd + chan_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.channelColRow[ 0 ] * chan_adv + assy_region[ 0 ],
	      self.channelColRow[ 1 ] * chan_adv + assy_region[ 1 ],
	      chan_adv, chan_adv
	    ]
        #end if cell in drawing range
      #end if-else on mode

#			-- Draw?
#			--
      if rect != None:
        block = chr( 0 ) * bmap.GetWidth() * bmap.GetHeight() * 4
        bmap.CopyToBuffer( block, wx.BitmapBufferFormat_RGBA )
	#new_bmap = wx.Bitmap.FromBufferRGBA( bmap.GetWidth(), bmap.GetHeight(),block )
        new_bmap = wx.EmptyBitmapRGBA( bmap.GetWidth(), bmap.GetHeight() )
        new_bmap.CopyFromBuffer( block, wx.BitmapBufferFormat_RGBA )

        dc = wx.MemoryDC( new_bmap )
	gc = wx.GraphicsContext.Create( dc )
	gc.SetPen(
	    wx.ThePenList.FindOrCreatePen(
	        wx.Colour( 255, 255, 255, 255 ), line_wd, wx.PENSTYLE_SOLID
		)
	    )
	path = gc.CreatePath()
	path.AddRectangle( *rect )
	gc.StrokePath( path )
# This doesn't work on MSWIN
#	dc.SetBrush( wx.TRANSPARENT_BRUSH )
#        dc.SetPen(
#	    wx.ThePenList.FindOrCreatePen(
#	        wx.Colour( 255, 0, 0 ), line_wd, wx.PENSTYLE_SOLID
#		)
#	    )
#        dc.DrawRectangle( *rect )
	dc.SelectObject( wx.NullBitmap )

	result = new_bmap
      #end if rect
    #end if self.config != None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    self.overlay = wx.Overlay()
#    inside_panel = wx.Panel( self )

#		-- Axial slider
#		--
#    self.axialBean = AxialSliderBean( inside_panel )
#    self.axialBean.Bind( EVT_AXIAL_LEVEL, self._OnAxial )
#    self.axialBean.Enable()

#		-- Bitmap panel
#		--
#    self.bitmapPanel = wx.lib.scrolledpanel.ScrolledPanel(
#        inside_panel, -1,
#	size = ( 640, 600 ),
#	style = wx.SIMPLE_BORDER
#	)
#    self.bitmapPanel.SetupScrolling()
#    self.bitmapPanel.SetBackgroundColour( wx.Colour( *DEFAULT_BG_COLOR_TUPLE ) )
    self.bitmapPanel = wx.Panel( self )
    self.bitmapCtrl = wx.StaticBitmap( self.bitmapPanel, bitmap = self.blankBitmap )
#    #self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnClick )
#    self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnDragStart )
#    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnDragEnd )
#    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnDragMove )
    self.bitmapCtrl.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    self._SetMode( 'core' )

#		-- Lay out
#		--
#    inside_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    inside_sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
#    inside_sizer.Add( self.axialBean, 0, wx.ALL | wx.EXPAND, 1 )
#    inside_panel.SetSizer( inside_sizer )

    sizer = wx.BoxSizer( wx.VERTICAL )
#    sizer.Add( inside_panel, 1, wx.ALL | wx.EXPAND )
    sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.  Sets properties:
  assemblyIndex
  axialValue
  channelColRow
  cellRange
  data
  dataSetName
  stateIndex
"""
    print >> sys.stderr, '[Channel2DView._LoadDataModel]'
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[Channel2DView._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      self.avgValues.clear()
      self.cellRange = list( self.data.ExtractSymmetryExtent() )
      del self.cellRangeStack[ : ]

      self.assemblyIndex = self.state.assemblyIndex
      self.axialValue = self.state.axialValue
      self.channelColRow = self.state.channelColRow
      self.dataSetName = self.state.channelDataSet
      self.stateIndex = self.state.stateIndex
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._LoadDataModelUI()		-
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self ):
    """Must be called on the UI thread.
"""
#    self.axialBean.SetRange( 1, self.data.core.nax )
#    self.axialBean.axialLevel = 0
#    self.exposureBean.SetRange( 1, len( self.data.states ) )
#    self.exposureBean.stateIndex = 0
    self._OnSize( None )
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindAssembly( x, y )
    if cell_info != None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_ndx = cell_info[ 0 : 3 ]
      if assy_ndx != self.assemblyIndex:
	state_args[ 'assembly_index' ] = assy_ndx

      chan_addr = cell_info[ 3 : 5 ]
      if chan_addr != self.channelColRow:
	state_args[ 'channel_colrow' ] = chan_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnContextMenu()			-
  #----------------------------------------------------------------------
  def _OnContextMenu( self, ev ):
    """
"""
    pos = ev.GetPosition()
    pos = self.bitmapCtrl.ScreenToClient( pos )

    menu = self.CreatePopupMenu()
    self.bitmapCtrl.PopupMenu( menu, pos )
  #end _OnContextMenu


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnDragEndCore()			-
  #----------------------------------------------------------------------
  def _OnDragEndCore( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[Channel2DView._OnDragEndCore] enter'
    zoom_flag = False

    if self.HasCapture():
      self.ReleaseMouse()

    rect = None
    if self.dragStartPosition != None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    #elif self.dragStartPosition == ev.GetPosition():
    if rect == None or rect.width <= 5 or rect.height <= 5:
      self._OnClick( ev )

    else:
      x = ev.GetX()
      y = ev.GetY()
      assy = self.FindAssembly( x, y )

      if assy != None:
        left = min( self.dragStartAssembly[ 1 ], assy[ 1 ] )
        right = max( self.dragStartAssembly[ 1 ], assy[ 1 ] ) + 1
	top = min( self.dragStartAssembly[ 2 ], assy[ 2 ] )
	bottom = max( self.dragStartAssembly[ 2 ], assy[ 2 ] ) + 1

	self.cellRangeStack.append( self.cellRange )
	self.cellRange = [ left, top, right, bottom, right - left, bottom - top ]
	zoom_flag = True
	if right - left == 1 and bottom - top == 1:
#	  self.assemblyIndex = self.dragStartAssembly[ 0 ]
	  self.assemblyIndex = self.dragStartAssembly
          self.FireStateChange( assembly_index = self.assemblyIndex )
	  self._SetMode( 'assy' )
	else:
	  self._SetMode( 'core' )
      #end if assy found
    #end else dragging

    self.dragStartAssembly = None
    self.dragStartPosition = None

    self.overlay.Reset()
    self.Refresh()

    if zoom_flag:
      self._OnSize( None )
  #end _OnDragEndCore


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnDragMoveCore()			-
  #----------------------------------------------------------------------
  def _OnDragMoveCore( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition == None:
      tip_str = ''
      assy = self.FindAssembly( *ev.GetPosition() )

      if assy != None and assy[ 0 ] >= 0:
#	if self.stateIndex in self.avgValues:
#	  avg_value = self.avgValues[ self.stateIndex ][ self.axialValue[ 1 ], assy[ 0 ] ]
#	else:
#	  avg_value = 0.0
	avg_value = 0.0

	show_assy_addr = self.data.core.CreateAssyLabel( *assy[ 1 : 3 ] )
	tip_str = 'Assy: %d %s\n%s %s: %.3g' % \
	    ( assy[ 0 ] + 1, show_assy_addr, 'Avg', self.dataSetName, avg_value )
      #end if

#      else:
#	avg_value = 0.0
#	if self.stateIndex in self.avgValues:
#	  avg_value = self.avgValues[ self.stateIndex ][ self.axialValue[ 1 ], assy[ 0 ] ]
#	show_assy_addr = self.data.core.CreateAssyLabel( *assy[ 1 : 3 ] )
#	tip_str = \
#	    'Assy: %d %s\nAvg: %.3g' % ( assy[ 0 ], show_assy_addr, avg_value )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      print >> sys.stderr, '[Channel2DView._OnDragMoveCore]', str( rect )

      if rect.width > 5 and rect.height > 5:
        dc = wx.ClientDC( self.bitmapCtrl )
        odc = wx.DCOverlay( self.overlay, dc )
        odc.Clear()

        if 'wxMac' in wx.PlatformInfo:
          dc.SetPen( wx.Pen( 'black', 2 ) )
          dc.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          dc.DrawRectangle( *rect )
        else:
          ctx = wx.GraphicsContext_Create( dc )
          ctx.SetPen( wx.GREY_PEN )
          ctx.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          ctx.DrawRectangle( *rect )
        del odc
      #end if moved sufficiently
    #end else dragging
  #end _OnDragMoveCore


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnDragStartCore()		-
  #----------------------------------------------------------------------
  def _OnDragStartCore( self, ev ):
    """
"""
    self.bitmapCtrl.SetToolTipString( '' )
    assy = self.FindAssembly( *ev.GetPosition() )
#    if assy != None and assy[ 0 ] > 0:
    if assy != None:
      self.dragStartAssembly = assy
      self.dragStartPosition = ev.GetPosition()
  #end _OnDragStartCore


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseMotionAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''
    chan_addr = self.FindChannel( *ev.GetPosition() )
    if chan_addr != None:
      state_ndx = self.stateIndex
      ds_name = self.dataSetName
      chan_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	chan_value = ds_value[
	    chan_addr[ 0 ], chan_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if chan_value > 0:
	chan_rc = ( chan_addr[ 0 ] + 1, chan_addr[ 1 ] + 1 )
        tip_str = 'Channel: %s\n%s: %g' % ( str( chan_rc ), ds_name, chan_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    chan_addr = self.FindChannel( *ev.GetPosition() )
    if chan_addr != None and chan_addr != self.channelColRow:
      state_ndx = self.stateIndex
      ds_name = self.dataSetName
      chan_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	chan_value = ds_value[
	    chan_addr[ 0 ], chan_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if chan_value > 0.0:
	self.FireStateChange( channel_colrow = chan_addr )
    #end if chan_addr changed
  #end _OnMouseUpAssy


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnSize()				-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev == None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[Channel2DView._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None and \
        (self.curSize == None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
      self._BusyBegin()
      self.curSize = ( wd, ht )
      #wx.CallAfter( self._Configure )
      wx.CallAfter( self._UpdateState, resized = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnToggleLabels()			-
  #----------------------------------------------------------------------
  def _OnToggleLabels( self, ev ):
    """Must be called on the UI thread.
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    label = item.GetItemLabel()

#		-- Change Label for Toggle Items
#		--
    if label.startswith( 'Show' ):
      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )
      self.showLabels = True
    else:
      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
      self.showLabels = False

#		-- Change Toggle Labels for Other Menu
#		--
    other_menu = \
        self.popupMenu \
	if menu == self.container.widgetMenu else \
	self.container.widgetMenu
    if other_menu != None:
      self._UpdateVisibilityMenuItems(
          other_menu,
	  'Labels', self.showLabels
	  )

#		-- Redraw
#		--
    self._UpdateState( resized = True )
  #end _OnToggleLabels


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnToggleLegend()			-
  #----------------------------------------------------------------------
  def _OnToggleLegend( self, ev ):
    """Must be called on the UI thread.
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    label = item.GetItemLabel()

#		-- Change Label for Toggle Items
#		--
    if label.startswith( 'Show' ):
      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )
      self.showLegend = True
    else:
      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
      self.showLegend = False

#		-- Change Toggle Labels for Other Menu
#		--
    other_menu = \
        self.popupMenu \
	if menu == self.container.widgetMenu else \
	self.container.widgetMenu
    if other_menu != None:
      self._UpdateVisibilityMenuItems(
          other_menu,
	  'Legend', self.showLegend
	  )

#		-- Redraw
#		--
    self._UpdateState( resized = True )
  #end _OnToggleLegend


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._SetMode( 'core' )
      self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.dataSetName:
#      self.avgValues.clear()
#      self.dataSetName = ds_name
#      wx.CallAfter( self._OnSize, None )
      wx.CallAfter( self._UpdateState, channel_dataset = ds_name )
      self.FireStateChange( channel_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._SetMode()			-
  #----------------------------------------------------------------------
  def _SetMode( self, mode ):
    """Must be called from the UI thread.
"""
    if mode != self.mode:
      if mode == 'assy':
	#if self.mode == 'core':
        self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, None )
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnMouseUpAssy )
        self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotionAssy )

      else:  # if mode == 'core':
	#if self.mode == 'assy':
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

        self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnDragStartCore )
        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnDragEndCore )
        self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnDragMoveCore )
      #end if-else

      self.mode = mode
    #end if different mode
  #end _SetMode


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._UpdateState()			-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateState( self, **kwargs ):
    """Called to update the components on a new state property.
Must be called from the UI thread.
@param  kwargs		'resized', 'changed'
"""
    self._BusyBegin()
    changed = kwargs[ 'changed' ] if 'changed' in kwargs  else False
    resized = kwargs[ 'resized' ] if 'resized' in kwargs  else False

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      changed = True
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )

    if 'channel_colrow' in kwargs and \
        kwargs[ 'channel_colrow' ] != self.channelColRow:
      changed = True
      self.channelColRow = self.data.NormalizeChannelColRow( kwargs[ 'channel_colrow' ] )

    if 'channel_dataset' in kwargs and \
        kwargs[ 'channel_dataset' ] != self.dataSetName:
      resized = True
      self.dataSetName = kwargs[ 'channel_dataset' ]
      self.avgValues.clear()

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      #self._CalcAvgValues( self.data, self.stateIndex )
      pair = ( self.stateIndex, self.axialValue[ 1 ] )

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if pair in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self._HiliteBitmap( self.bitmaps[ pair ] ) )
	  must_create_image = False
      finally:
        self.bitmapsLock.release()

      if must_create_image:
        print >> sys.stderr, '[Channel2DView._UpdateState] starting worker'
        wxlibdr.startWorker(
	    self._BitmapThreadFinish,
	    self._BitmapThreadStart,
	    wargs = [ pair ]
	    )
      else:
        self._BusyEnd()
    #end if
    print >> sys.stderr, '[Channel2DView._UpdateState] exit'
  #end _UpdateState

#end Channel2DView
