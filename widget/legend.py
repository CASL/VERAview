#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		legend.py					-
#	HISTORY:							-
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
#	CLASS:		Legend						-
#------------------------------------------------------------------------
class Legend( object ):
  """Legend PIL image generator
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, values, colors, font_size = 16 ):
    self.image = self._CreateImage( values, colors, font_size )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_CreateImage()					-
  #----------------------------------------------------------------------
  def _CreateImage( self, values, colors, font_size ):
    """Generate the PIL image.
"""
    print >> sys.stderr, '[Legend._CreateImage] enter'
    border = 2
#    text_fmt = '%.3g'
    text_gap = 8
    pen_color = ( 0, 0, 0, 255 )

    #font = PIL.ImageFont.truetype( 'res/Courier New.ttf', font_size )
    font = PIL.ImageFont.truetype(
        #os.path.join( Config.GetRootDir(), 'res/Courier New.ttf' ),
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' ),
	font_size
	)
    text_size = font.getsize( ' -9.99e+99' )
    block_size = text_size[ 1 ] + (text_size[ 1 ] >> 1)
    im_wd = (border << 1) + text_size[ 0 ] + text_gap + block_size
    im_ht = (border << 1) + (block_size * len( colors ))

    pil_im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
    im_draw = PIL.ImageDraw.Draw( pil_im )

    x = im_wd - border - block_size
    y = border
    tick_y = y + (block_size >> 1)

    for i in range( min( len( colors ), len( values ) ) ):
      color = colors[ i ]
      value = values[ i ]

      im_draw.rectangle(
	  [ x, y, x + block_size, y + block_size ],
	  fill = color, outline = pen_color
          )
      im_draw.line(
          [ x - text_gap, tick_y, x, tick_y ],
	  fill = pen_color, width = 1
	  )

#      label_str = text_fmt % value
      label_str = DataUtils.FormatFloat1( value )
      label_size = font.getsize( label_str )
      im_draw.text(
	  ( x - text_gap - label_size[ 0 ], tick_y - (label_size[ 1 ] >> 1) ),
	  label_str, fill = pen_color, font = font
          )

      y += block_size
      tick_y += block_size
    #end for blocks

#    im_draw.rectangle(
#	[ 0, 0, im_wd - 1, im_ht - 1 ],
#	fill = None, outline = ( 255, 0, 0, 255 )
#        )

    del  im_draw
    print >> sys.stderr, '[Legend._CreateImage] exit'

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
  #	METHOD:		DeriveBaseFactor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def DeriveBaseFactor( min_value, max_value, count ):
    base_exp = math.floor( math.log( max_value ) / math.log( 10 ) )
    base = math.pow( 10, base_exp )
    factor = max_value / base
    factor_tenth = int( 10.0 * factor ) % 10
    if factor_tenth > 7:
      base_factor = math.ceil( max_value / base )
    elif factor_tenth > 3:
      base_factor = math.floor( max_value / base ) + 0.5
    else:
      base_factor = math.floor( max_value / base )
    return  base_factor * base
  #end DeriveBaseFactor


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

#end Legend


if __name__ == '__main__':
  Legend.main()
