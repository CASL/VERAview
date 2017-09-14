#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		legend3.py					-
#	HISTORY:							-
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
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw, ImageFont
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

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
  def __call__(
      self, get_color, value_range, value_count,
      font_size = 16, gray = False, title = None
      ):
    """Calls CreateImage().
@param  get_color	function( value_offset, max_value_offset, alpha, gray )
@param  value_range	value range ( min, max )
@param  value_count	number of values to display on bar, max to min
@param  font_size	size of font for drawing
@param  gray		True to convert to grayscale
@param  title		optional title under legend
@return			PIL.Image instance
"""
    return  \
    self.CreateImage(
        get_color, value_range, value_count, font_size,
	gray, title
	)
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
  #	METHOD:		CreateImage()					-
  #----------------------------------------------------------------------
  def CreateImage(
      self, get_color, value_range, value_count, font_size,
      gray = False, title = None
      ):
    """Generate the PIL image.
@param  get_color	function( value_offset, max_value_offset, alpha, gray )
@param  value_range	value range ( min, max, data_min?, data_max? )
@param  value_count	number of values to display on bar, max to min
@param  font_size	size of font for drawing
@param  gray		True to convert to grayscale
@param  title		optional title under legend
@return			PIL.Image instance
"""
    value_count = max( 2, value_count )

#		-- Pre-step, format values
#		--
    scaler = RangeScaler()
    steps = scaler.\
        CalcLinear( value_range[ 0 ], value_range[ 1 ], value_count, True )
    labels = scaler.CreateLinearLabels( steps )
    widest_label = None
    for l in labels:
      if widest_label is None or len( l ) > len( widest_label ):
        widest_label = l

#		-- Calc sizes
#		--
    border = 2
    text_gap = 8  # line drawn from text to color block
    pen_color = ( 0, 0, 0, 255 )

    font = PIL.ImageFont.truetype(
        #os.path.join( Config.GetRootDir(), 'res/Courier New.ttf' ),
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' ),
	font_size
	)
    #text_size = font.getsize( '-9.999e+99' )
    text_size = font.getsize( '99' + widest_label )
    if title:
      title_size = font.getsize( title )
      if title_size[ 0 ] > text_size[ 0 ]:
        text_size = ( title_size[ 0 ], text_size[ 1 ] )

    block_size = text_size[ 1 ] << 1
    im_wd = border + text_size[ 0 ] + text_gap + block_size + border
    color_band_ht = block_size * value_count
    ##im_ht = (border << 1) + color_band_ht + block_size
    #im_ht = (border << 1) + color_band_ht + (block_size << 1)
    #x im_ht = border + block_size + color_band_ht + block_size
    im_ht = border + block_size + color_band_ht + block_size + text_size[ 1 ] + border
    if title:
      im_ht += block_size + text_size[ 1 ]

    pil_im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
    im_draw = PIL.ImageDraw.Draw( pil_im )

    # x,y is UL position of the contour color block
    x = im_wd - border - block_size
    # do this if not drawing max value
    #y = border + (text_size[ 1 ] >> 1)
    y = border

#		-- Write max value
#		--
    data_max = value_range[ 3 ] if len( value_range ) > 3 else value_range[ 1 ]
    #cur_label = scaler.Format( value_range[ 1 ], 3, 'auto' )
    cur_label = scaler.Format( data_max, 3 )
    label_size = font.getsize( cur_label )
    im_draw.text(
	#( x + block_size - label_size[ 0 ], y - (text_size[ 1 ] >> 1) ),
	( x + block_size - label_size[ 0 ], y ),
	cur_label, fill = pen_color, font = font
        )
    y += text_size[ 1 ] + (text_size[ 1 ] >> 1)

#		-- Draw color band
#		--
    value_delta = value_range[ 1 ] - value_range[ 0 ]
    cur_value_incr = value_delta / color_band_ht
    cur_value = value_range[ 1 ]
    for j in xrange( color_band_ht ):
      color = get_color(
          cur_value - value_range[ 0 ], value_delta, 255,
	  gray = gray
	  )
      im_draw.rectangle(
	  [ x, y + j, x + block_size, y + j ],
	  fill = color, outline = color
          )
      cur_value -= cur_value_incr
    #end for

    im_draw.rectangle(
	[ x, y, x + block_size, y + color_band_ht ],
	fill = None, outline = pen_color
        )

#		-- Draw contour values and lines
#		--
    for j in xrange( len( steps ) ):
      cur_value = steps[ j ]
      cur_label = labels[ j ]
      tick_y = (value_range[ 1 ] - cur_value) / value_delta * color_band_ht + y
      im_draw.line(
          [ x - text_gap, tick_y, x, tick_y ],
	  fill = pen_color, width = 1
	  )

      label_size = font.getsize( cur_label )
      im_draw.text(
          #( x - text_gap - label_size[ 0 ], tick_y - (label_size[ 1 ] >> 1) ),
          ( x - text_gap - label_size[ 0 ], tick_y - (label_size[ 1 ] >> 1) - 1 ),
	  cur_label, fill = pen_color, font = font
          )
    #end for j
    y += color_band_ht

#		-- Write min value
#		--
    data_min = value_range[ 2 ] if len( value_range ) > 3 else value_range[ 0 ]
    #cur_label = scaler.Format( value_range[ 0 ], 3, 'auto' )
    cur_label = scaler.Format( data_min, 3 )
    label_size = font.getsize( cur_label )
    im_draw.text(
	( x + block_size - label_size[ 0 ], y + (text_size[ 1 ] >> 1) ),
	cur_label, fill = pen_color, font = font
        )

    if title:
      y += block_size
      #tx = (im_wd - title_size[ 0 ]) >> 1
      tx = im_wd - title_size[ 0 ]
      im_draw.text(
	  ( tx, y ),
	  title, fill = pen_color, font = font
          )
    #end if title

    del  im_draw

    return  pil_im
  #end CreateImage


  #----------------------------------------------------------------------
  #	METHOD:		GetImage()					-
  #----------------------------------------------------------------------
#  def GetImage( self ):
#    return  self.image
#  #end GetImage


  #----------------------------------------------------------------------
  #	METHOD:		GetWxBitmap()					-
  #----------------------------------------------------------------------
#  def GetWxBitmap( self ):
#    """Must be called from the UI thread."""
#    wx_im = self.GetWxImage()
#    if wx_im is not None:
#      bmap = wx.BitmapFromImage( wx_im )
#    else:
#      bmap = None
#
#    return  bmap
#  #end GetWxBitmap


  #----------------------------------------------------------------------
  #	METHOD:		GetWxImage()					-
  #----------------------------------------------------------------------
#  def GetWxImage( self ):
#    """Must be called from the UI thread."""
#    wx_im = None
#    if self.image is not None:
#      wx_im = wx.EmptyImage( *self.image.size )
#      im_data_str = self.image.convert( 'RGB' ).tostring()
#      wx_im.SetData( im_data_str )
#
#      im_data_str = self.image.convert( 'RGBA' ).tostring()
#      wx_im.SetAlphaData( im_data_str[ 3 : : 4 ] )
#    #end if
#
#    return  wx_im
#  #end GetWxImage

#end Legend3
