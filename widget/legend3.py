#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		legend3.py					-
#	HISTORY:							-
#		2018-06-01	leerw@ornl.gov				-
#	  Updated CreateBitmap() to check data_min and steps[ 0 ] for
#	  0 before calling math.log10() on them.
#		2018-05-25	leerw@ornl.gov				-
#	  Fixed CreateBitmap() bug when data_min == 0.
#		2018-03-01	leerw@ornl.gov				-
#	  Setting image background under Windows to make font rendering
#	  work.
#		2017-11-03	leerw@ornl.gov				-
#	  Using GraphicsContext to work with RGBA bitmaps, b/c DC
#	  noworky with transparency under Windows.
#		2017-10-24	leerw@ornl.gov				-
#	  Migrating from PIL.Image to wx.Bitmap.
#		2017-05-13	leerw@ornl.gov				-
#	  Added title param.
#		2017-04-01	leerw@ornl.gov				-
#	  Showing min/max values.
#		2017-03-28	leerw@ornl.gov				-
#	  Added __call__() and gray param.
#		2017-03-11	leerw@ornl.gov				-
#	  Trying for better numbers displayed using rangescaler.
#		2015-12-22	leerw@ornl.gov				-
#	  A continuous legend display as per Shane Stimpson's request.
#		2015-12-03	leerw@ornl.gov				-
#	  Allowing for negative numbers in the legend.
#		2014-12-18	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-29	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, time, traceback
import pdb

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  from matplotlib import cm, colors, transforms
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw, ImageFont
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.config import Config
from data.rangescaler import *
from data.utils import *


#------------------------------------------------------------------------
#	CLASS:		Legend3						-
#------------------------------------------------------------------------
class Legend3( object ):
  """Legend PIL image generator
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """Calls CreateBitmap().
"""
    return  self.CreateBitmap( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self ):
    """
"""
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CreateBitmap()					-
  #----------------------------------------------------------------------
  def CreateBitmap(
      self, value_range,
      bg_color = None,
      cmap = None,
      font_size = 10,
      mapper = None,
      ntick_values = 10,
      scale_type = 'linear',
      title = None
      ):
    """Generate the wx.Bitmap.
    Args:
	value_range (tuple): range_min, range_max, data_min, data_max
..        scalar_map (matplotlib.cm.ScalarMappable): instance used to map
..	    values to colors and determine the range and scale type
	bg_color (wx.Colour): optional color for Linux/GTK support
	cmap (matplotlib.colors.Colormap): optional colormap to use if
	    mapper is None, defaulting to 'rainbow'
	font_size (int): font point size
	mapper (matplotlib.cm.ScalarMappable): optional pre-built mapper,
	    if None one is created basd on value_range and scale_type; Note
	    the ``norm`` property determines scale_type, overriding the
	    ``scale_type`` parameter if provided
        ntick_values (int): number of values to show as ticks
	scale_type (str): 'linear' or 'log', used if mapper is None
	title (str): optional title under legend
    Returns:
        wx.Bitmap: new bitmap
"""
    ntick_values = max( 2, ntick_values )
    data_max = value_range[ 3 ] if len( value_range ) > 3 else value_range[ 1 ]
    data_min = value_range[ 2 ] if len( value_range ) > 2 else value_range[ 0 ]

    if isinstance( mapper, cm.ScalarMappable ):
      norm = mapper.norm
      is_log_scale = isinstance( norm, colors.LogNorm )
    else:
      is_log_scale = scale_type == 'log'
      if is_log_scale:
        norm = colors.LogNorm(
	    #vmin = value_range[ 0 ], vmax = value_range[ 1 ], clip = True
	    vmin = max( data_min, 1.0e-16 ),
	    vmax = max( data_max, 1.0e-16 ),
	    clip = True
	    )
      else:
        norm = colors.Normalize(
	    #vmin = value_range[ 0 ], vmax = value_range[ 1 ], clip = True
	    vmin = data_min, vmax = data_max, clip = True
	    )
      if cmap is None:
        cmap = cm.get_cmap( Config.defaultCmapName_ ) #'rainbow'
      mapper = cm.ScalarMappable( norm = norm, cmap = cmap )
	  #cmap = cm.get_cmap( 'rainbow' )
    #norm = scalar_map.norm
    #is_log_scale = isinstance( norm, colors.LogNorm )

#		-- Pre-step, format values
#		--
    scaler = RangeScaler()
    steps = scaler.Calc(
        norm.vmin, norm.vmax,
	scale_type = 'log' if is_log_scale else 'linear',
	nticks = ntick_values,
	cull_outside_range = True
	)
    labels_mode = 'log' if is_log_scale else 'linear'
    labels = scaler.CreateLabels( steps, labels_mode )

    widest_label = None
    for l in labels:
      if widest_label is None or len( l ) > len( widest_label ):
        widest_label = l

#		-- Calc sizes
#		--
    border = 2
    text_gap = 8  # line drawn from text to color block
    pen_color = ( 0, 0, 0, 255 )

    dc = wx.MemoryDC()
    dc.SelectObject( wx.EmptyBitmapRGBA( 64, 64 ) )

#    if Config.GetOSName() == 'windows':
#      font_size = int( font_size * 0.8 )

    font_params = \
      {
      'pointSize': font_size,
      'family': wx.FONTFAMILY_SWISS,
      'style': wx.FONTSTYLE_NORMAL,
      'weight': wx.FONTWEIGHT_NORMAL
      }
    if Config.GetOSName() == 'windows':
      font_params[ 'faceName' ] = 'Lucida Sans' # 'Arial'
      font_params[ 'weight' ] = wx.FONTWEIGHT_BOLD
    cur_font = wx.Font( **font_params )
    dc.SetFont( cur_font )
    text_size = dc.GetTextExtent( '99' + widest_label )
    if title:
      tsize = dc.GetTextExtent( title )
      if tsize[ 0 ] > text_size[ 0 ]:
        text_size = ( tsize[ 0 ], tsize[ 1 ] )

    if Config.GetOSName() == 'darwin':
      block_size = text_size[ 1 ] << 1
    else:
      block_size = int( text_size[ 1 ] * 1.5 )

    im_wd = border + text_size[ 0 ] + text_gap + block_size + border
    color_band_ht = block_size * ntick_values
    im_ht = \
	border + (text_size[ 1 ] << 1) + color_band_ht + \
        (text_size[ 1 ] >> 1) + 2 + \
        text_size[ 1 ] + (text_size[ 1 ] >> 1)
#        border + block_size + color_band_ht +
#	text_size[ 1 ] + border
    if title:
      im_ht += block_size + text_size[ 1 ]

    #this is drawn empty in Windows
    if bg_color is not None:
      bmap = wx.EmptyBitmapRGBA(
          im_wd, im_ht,
	  bg_color.red, bg_color.green, bg_color.blue, bg_color.alpha
	  )
    else:
      bmap = wx.EmptyBitmapRGBA( im_wd, im_ht )

    dc.SelectObject( bmap )
    if bg_color is None:
      if Config.GetOSName() == 'windows':
        dc.SetBackground( wx.TheBrushList.FindOrCreateBrush(
	      wx.WHITE, wx.BRUSHSTYLE_SOLID
	      #wx.Colour( 225, 225, 225, 255 ), wx.BRUSHSTYLE_SOLID
	      ) )
        dc.Clear()
      else:
        dc.SetBackground( wx.TheBrushList.FindOrCreateBrush(
            wx.WHITE, wx.TRANSPARENT
	    ) )
    #end if bg_color is None
    gc = wx.GraphicsContext.Create( dc )

    trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
        wx.WHITE, wx.TRANSPARENT
	) )
    black_pen = gc.CreatePen( wx.Pen( wx.BLACK, 1 ) )
    gfont = gc.CreateFont( cur_font, wx.BLACK )
    gc.SetAntialiasMode( wx.ANTIALIAS_DEFAULT )  # wx.ANTIALIAS_NONE
    gc.SetBrush( trans_brush )
    gc.SetFont( gfont )
    gc.SetInterpolationQuality( wx.INTERPOLATION_BEST )
    gc.SetPen( black_pen )


    # x,y is UL position of the contour color block
    x = im_wd - border - block_size
    # do this if not drawing max value
    #y = border + (text_size[ 1 ] >> 1)
    y = border

#		-- Write max value
#		--
    data_max_log = int( math.log10( data_max ) ) if data_max > 0.0 else 0
    steps_max_log = int( math.log10( steps[ -1 ] ) ) if steps[ -1 ] > 0.0 else 0

    #cur_label = scaler.Format( data_max, 3 )
    cur_label = \
        scaler.Format( data_max, 3 )  if data_max_log == steps_max_log else \
	'{0:.3g}'.format( data_max )
    label_size = gc.GetFullTextExtent( cur_label )
    gc.DrawText(
        cur_label, x + block_size - label_size[ 0 ], y + label_size[ 2 ]
	)

    #x y += text_size[ 1 ] + (text_size[ 1 ] >> 1)
    y += text_size[ 1 ] << 1

#		-- Draw color band
#		--
    max_value = max( norm.vmax, steps[ -1 ] )
    min_value = min( norm.vmin, steps[ 0 ] )

    if is_log_scale:
#      log_delta = \
#          0  if norm.vmin == 0.0 else  math.log10( max_value / min_value )
      log_delta = \
          0  if norm.vmin == 0.0 else \
	  0  if max_value <= 0.0 or  min_value <= 0.0 else \
	  math.log10( max_value / min_value )
      log_b = log_delta / color_band_ht
      log_factor = math.pow( 10.0, log_b )
      #log_a = value_range[ 1 ] / math.pow( 10.0, log_factor * color_band_ht )
      #                           this is 1
    else:
      #value_delta = norm.vmax - norm.vmin
      value_delta = max_value - min_value
      value_incr = value_delta / (color_band_ht - 1)

    #cur_value = value_range[ 1 ]
    cur_value = max_value
    for j in xrange( color_band_ht ):
#      if is_log_scale:
#        cur_value = value_range[ 1 ] / math.pow( 10.0, log_b * j )

      #color = cmap( norm( cur_value ), bytes = True )
      color = mapper.to_rgba( cur_value, bytes = True )
      gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
          wx.Colour( *color ), wx.BRUSHSTYLE_SOLID
          ) ) )
      gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( *color ), 1, wx.PENSTYLE_SOLID
          ) ) )
      gc.DrawRectangle( x, y + j, block_size, 1 )
      if is_log_scale:
        cur_value /= log_factor
      else:
        cur_value -= value_incr
    #end for

    gc.SetBrush( trans_brush )
    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
        wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
        ) ) )
    gc.DrawRectangle( x, y, block_size, color_band_ht )

#		-- Draw contour values and lines
#		--
    for j in xrange( len( steps ) ):
      cur_value = steps[ j ]
      cur_label = labels[ j ]
      if is_log_scale:
	tick_delta = math.log10( max_value / cur_value ) / log_b
      else:
        tick_delta = (max_value - cur_value) / value_delta * color_band_ht
      tick_y = y + tick_delta
      gc.DrawLines( ( ( x - text_gap, tick_y ), ( x, tick_y ) ) )

      label_size = gc.GetFullTextExtent( cur_label )
      gc.DrawText(
          cur_label,
	  x - text_gap - label_size[ 0 ] - 1,
	  tick_y - (label_size[ 1 ] / 2.0)
	  )
    #end for j
    y += color_band_ht

#		-- Write min value
#		--
    if data_min == 0.0 or steps[ 0 ] == 0.0:
      data_min_log = steps_min_log = 0
    else:
      data_min_log = int( math.log10( abs( data_min ) ) )
      steps_min_log = int( math.log10( abs( steps[ 0 ] ) ) )

    #cur_label = scaler.Format( data_min, 3 )
    cur_label = \
        scaler.Format( data_min, 3 )  if data_min_log == steps_min_log else \
	'{0:.3g}'.format( data_min )
    label_size = gc.GetFullTextExtent( cur_label )
    #x gc.DrawText( cur_label, x + block_size - label_size[ 0 ], y + 2 )
    y += (text_size[ 1 ] >> 1) + 2
    gc.DrawText( cur_label, x + block_size - label_size[ 0 ], y )

    if title:
      #x y += block_size
      y += text_size[ 1 ] + (text_size[ 1 ] >> 1)
      title_size = gc.GetFullTextExtent( title )
      tx = im_wd - title_size[ 0 ]
      gc.DrawText( title, tx, y )
    #end if title

    dc.SelectObject( wx.NullBitmap )

    return  bmap
  #end CreateBitmap

#end Legend3
