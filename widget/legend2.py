#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		legend2.py					-
#	HISTORY:							-
#		2015-12-22	leerw@ornl.gov				-
#	  A continuous legend display as per Shane Stimpson's request.
#		2015-12-03	leerw@ornl.gov				-
#	  Allowing for negative numbers in the legend.
#		2014-12-18	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-29	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, time, traceback
#import numpy as np

try:
  import wx
#  import wx.lib.delayedresult as wxlibdr
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw, ImageFont
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.config import Config
from data.utils import DataUtils


#------------------------------------------------------------------------
#	CLASS:		Legend2						-
#------------------------------------------------------------------------
class Legend2( object ):
  """Legend PIL image generator
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, get_color, value_range, value_count, font_size = 16 ):
    self.image = \
        self._CreateImage( get_color, value_range, value_count, font_size )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateImage()					-
  #----------------------------------------------------------------------
  def _CreateImage( self, get_color, value_range, value_count, font_size ):
    """Generate the PIL image.
@param  get_color	function( value, max_value, alpha )
@param  value_range	value range ( min, max )
@param  value_count	number of values to display on bar, max to min
@param  font_size	size of font for drawing
@return			PIL.Image instance
"""
    print >> sys.stderr, '[Legend2._CreateImage] enter'

    value_count = max( 2, value_count )

    border = 2
    text_gap = 8  # line drawn from text to color block
    pen_color = ( 0, 0, 0, 255 )

    #font = PIL.ImageFont.truetype( 'res/Courier New.ttf', font_size )
    font = PIL.ImageFont.truetype(
        #os.path.join( Config.GetRootDir(), 'res/Courier New.ttf' ),
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' ),
	font_size
	)
    text_size = font.getsize( ' -9.99e+99' )
    block_size = text_size[ 1 ] << 1
    im_wd = (border << 1) + text_size[ 0 ] + text_gap + block_size
    #xbug color_band_ht = block_size * (value_count - 1)
    color_band_ht = block_size * value_count
    #im_ht = (border << 1) + color_band_ht + text_size[ 1 ]
    im_ht = (border << 1) + color_band_ht + block_size

    pil_im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
    im_draw = PIL.ImageDraw.Draw( pil_im )

    #x,y is UL position of the contour color block
    x = im_wd - border - block_size
    #y = border
    #tick_y = y + (block_size >> 1)
    y = border + (text_size[ 1 ] >> 1)

#		-- Draw color band
#		--
    value_delta = value_range[ 1 ] - value_range[ 0 ]
    cur_value_incr = value_delta / color_band_ht
    cur_value = value_range[ 1 ]
    for j in range( color_band_ht ):
      color = get_color( cur_value - value_range[ 0 ], value_delta, 255 )
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

#		-- Pre-step, format values
#		--
    labels = []
    cur_value = value_range[ 1 ]
    cur_value_incr = value_delta / value_count
    for i in range( value_count ):
      labels.append( DataUtils.FormatFloat1( cur_value ) )
      cur_value -= cur_value_incr
    labels.append( DataUtils.FormatFloat1( cur_value ) )

    DataUtils.NormalizeValueLabels( labels )

#		-- Draw contour values and lines
#		--
    #cur_value = value_range[ 1 ]
    #cur_value_incr = value_delta / value_count
    tick_y = y
    #for i in range( value_count ):
    for label_str in labels:
      im_draw.line(
          [ x - text_gap, tick_y, x, tick_y ],
	  fill = pen_color, width = 1
	  )

      #label_str = DataUtils.FormatFloat1( cur_value )
      label_size = font.getsize( label_str )
      im_draw.text(
          ( x - text_gap - label_size[ 0 ], tick_y - (label_size[ 1 ] >> 1) ),
	  label_str, fill = pen_color, font = font
          )

      #cur_value -= cur_value_incr
      y += block_size
      tick_y += block_size
    #end for blocks

#		-- Write minimum value
#		--
#    im_draw.line(
#        [ x - text_gap, tick_y, x, tick_y ],
#	fill = pen_color, width = 1
#	)
#    label_str = DataUtils.FormatFloat1( value_range[ 0 ] )
#    label_size = font.getsize( label_str )
#    im_draw.text(
#        ( x - text_gap - label_size[ 0 ], tick_y - (label_size[ 1 ] >> 1) ),
#	label_str, fill = pen_color, font = font
#        )

    del  im_draw
    print >> sys.stderr, '[Legend2._CreateImage] exit'

    return  pil_im
  #end _CreateImage


  #----------------------------------------------------------------------
  #	METHOD:		GetImage()					-
  #----------------------------------------------------------------------
  def GetImage( self ):
    return  self.image
  #end GetImage


  #----------------------------------------------------------------------
  #	METHOD:		GetWxBitmap()					-
  #----------------------------------------------------------------------
  def GetWxBitmap( self ):
    """Must be called from the UI thread."""
    wx_im = self.GetWxImage()
    if wx_im != None:
      bmap = wx.BitmapFromImage( wx_im )
    else:
      bmap = None

    return  bmap
  #end GetWxBitmap


  #----------------------------------------------------------------------
  #	METHOD:		GetWxImage()					-
  #----------------------------------------------------------------------
  def GetWxImage( self ):
    """Must be called from the UI thread."""
    wx_im = None
    if self.image != None:
      wx_im = wx.EmptyImage( *self.image.size )
      im_data_str = self.image.convert( 'RGB' ).tostring()
      wx_im.SetData( im_data_str )

      im_data_str = self.image.convert( 'RGBA' ).tostring()
      wx_im.SetAlphaData( im_data_str[ 3 : : 4 ] )
    #end if

    return  wx_im
  #end GetWxImage


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		main()						-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      colors = \
        (
	  ( 0, 0, 255, 255 ),
	  ( 0, 255, 0, 255 ),
	  ( 0, 255, 255, 255 ),
	  ( 255, 0, 0, 255 ),
	  ( 255, 0, 255, 255 ),
	  ( 255, 255, 0, 255 ),
	  ( 255, 255, 255, 255 )
	)
      values = ( 1.0e10, 1.0e9, 1.0e8, 1.0e7, 1.0e6, 1.0e5, 1.0e4 )

      legend = Legend( values, colors, 16 )
      legend.image.save( 'test.png', 'PNG' )

    except Exception, ex:
      print >> sys.stderr, str( ex )
      et, ev, tb = sys.exc_info()
      while tb:
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
  #end main

#end Legend2


if __name__ == '__main__':
  Legend2.main()
