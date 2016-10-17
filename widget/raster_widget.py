#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		raster_widget.py				-
#	HISTORY:							-
#		2016-10-14	leerw@ornl.gov				-
#	  Added _DrawValues() method.
#		2016-09-29	leerw@ornl.gov				-
#	  Modified _CreateValue{Display,String}() in an effort to
#	  prevent overrun of values displayed in cells.
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-06-30	leerw@ornl.gov				-
#	  Added isLoaded with check in _LoadDataModel() against call to
#	  _LoadDataModelValues().
#		2016-06-23	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-03-16	leerw@ornl.gov				-
#	  Moving find-max calcs to DataModel and methods to Widget.
#		2016-03-14	leerw@ornl.gov				-
#	  Added menu options to find maximum values.
#		2016-02-29	leerw@ornl.gov				-
#	  Added Redraw() to call _OnSize( None ).
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2016-01-22	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2016-01-15	leerw@ornl.gov				-
#	  Fixed bug in UpdateState() where _BusyEnd() was not called if
#	  no state changes.
#		2015-12-03	leerw@ornl.gov				-
#	  Added _CreateValueString().
#		2015-11-28	leerw@ornl.gov				-
#	  Added 'dataRange' to returned config rec in _CreateBaseDrawConfig().
#		2015-11-23	leerw@ornl.gov				-
#	  Added self.bitmapThreadArgs = tpl + self.curSize to help
#	  eliminate unnecessary threads.
#		2015-11-18	leerw@ornl.gov				-
# 	  Added GetData().
#		2015-08-20	leerw@ornl.gov				-
#	  Added workaround for MacOS DCOverlay bug in _OnMouseMotion().
#		2015-06-17	leerw@ornl.gov				-
#	  Generalization of the 2D raster view widgets.
#------------------------------------------------------------------------
import functools, math, os, string, sys, threading
import numpy as np
import pdb  #pdb.set_trace()
#import time, traceback

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

from event.state import *
from legend import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		RasterWidget					-
#------------------------------------------------------------------------
class RasterWidget( Widget ):
  """Base class for raster or image widgets with a legend.

Widget Framework
================

Fields/Properties
-----------------

axialValue
  local axial value state, getter is GetAxialValue()

bitmapCtrl
  wx.StaticBitmap used to display the raster image and as the event source

bitmapPanel
  wx.Panel holding *bitmapCtrl*

bitmapThreadArgs
  arguments in current bitmap creation thread, used to avoid duplicate
  threads to create the same bitmap

bitmaps
  dict caching bitmaps created, keyed by event state tuple, which is defined
  by extensions

bitmapsLock
  threading.RLock() to manage access to *bitmaps*

cellRange
  currently displayed zoom range

cellRangeStack
  zoom stack

config
  drawing configuration

curSize
  current widget size in pixels

data
  DataModel reference, getter is GetData()

stateIndex
  0-based state point index, getter is GetStateIndex()

Framework Methods
-----------------

_CreateDrawConfig()
  Must be implemented by extensions to build the drawing configuration based
  on widget size or a specified scale factor.

_CreateRasterImage()
  Must be implemented by extensions to create the raster image based on
  the event state tuple and a configuration created by _CreateDrawConfig().

_CreateStateTuple()
  Must be implemented by extensions to define the event state tuple used
  to create raster images.

_CreateToolTipText()
  Should be implemented by extensions to create a tool tip based on the
  cell returned from FindCell().

FindCell()
  Returns the event state tuple for the specified x- and y-pixel position
  within the raster image.

GetInitialCellRange()
  Implementation here returns self.data.ExtractSymmetryExtent(), but extensions
  may override as appropriate to define the range of assembly columns/rows, or
  channel/pin columns/rows to display initially.

GetPrintScale()
  Configuration scale factor to apply for creating raster images for printing.
  The default here is 28, but this should be overridden by extensions.

_HiliteBitmap()
  Extensions should override to "hilite" a raster image by drawing primary
  and/or secondary cell selection indicators.

_InitEventHandlers()
  Registers/binds handlers for wxPython events.  Extensions that override
  should call super._InitEventHandlers() to get events consistent across all
  raster widgets.

_InitUI()
  Implements common processing for all raster widgets by creating the
  *bitmapPanel* and *bitmapCtrl* objects.

IsTupleCurrent()
  Must be implemented by extensions to indicate if the specified event state
  tuple represents the current selection.

_LoadDataModel()
  Implements this Widget framework method by populating properties
  *axialValue*, *cellRange*, *cellRangeStack*, *data*, and *stateIndex*.  It
  then calls _LoadDataModelValues() and _LoadDataModelUI(), the latter on the
  UI thread.

_LoadDataModelUI()
  The method defined here calls Redraw(), but extensions can override this
  for any special UI processing needed after _LoadDataModelValues() has been
  called.

_LoadDataModelValues()
  Should be implemented by extensions to initialize fields/properties
  defined in those classes.

_OnClick( self, ev ):
  Should be implemented by extensions to handle clicks.  Normally, this means
  determine what "cell" has been selected and calling FireStateChange() with
  the event state change that results.

_OnDragFinished()
  The noop implementation here can be overridden by extensions to do anything
  needed after a successful zoom.

UpdateState()
  Implements this Widget framework method by calling _UpdateStateValues() and
  managing bitmaps appropriately.  On a 'resize', the bitmap cache is cleared.
  On a 'change' in event state selection, the appropriate bitmap is retrieved
  from the cache or created if necessary.

_UpdateStateValues()
  The implementation here handles 'axial_value', 'state_index', and
  'time_dataset' changes, but extensions should override to handle
  widget-specific event state values, being sure to call
  super._UpdateStateValues().

Support Methods
---------------

_CreateBaseDrawConfig()
  Creates common draw configuration values needed by most rasters.  Should be
  called from subclass _CreateDrawConfig() methods.

_CreateTitleString()
  General purpose method to create a title string.

_CreateTitleTemplate()
  Creates a title string template and a default title string to be used for
  sizing.

_CreateTitleTemplate2()
  Like _CreateTitleTemplate() but allows additional title items.

_CreateValueDisplay()
  Creates a string representation of a value that fits in a requested width for
  a specified font.

_CreateValueString()
  Creates minimal length value string.

"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.axialValue = DataModel.CreateEmptyAxialValue()
    #self.axialValue = ( 0.0, -1, -1 )
    self.bitmapThreadArgs = None
    self.bitmaps = {}  # key is (row,col)
    self.bitmapsLock = threading.RLock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.config = None
    self.curSize = None
    self.dragStartCell = None
    self.dragStartPosition = None
    self.isLoaded = False

    self._imcount = 0

#old way
#    self.menuDef = \
#      [
#	( 'Copy Data', self._OnCopyData ),
#	( 'Copy Image', self._OnCopyImage ),
#	( '-', None ),
#	( 'Hide Labels', self._OnToggleLabels ),
#	( 'Hide Legend', self._OnToggleLegend ),
#        ( 'Unzoom', self._OnUnzoom )
#      ]

    self.showLabels = True
    self.showLegend = True
    self.stateIndex = -1

    self.bitmapCtrl = None
    self.bitmapPanel = None
    self.blankBitmap = self.GetBitmap( 'loading' )
    self.emptyPilImage = PIL.Image.new( "RGBA", ( 16, 16 ) )

    self.overlay = None
    self.pilFont2Path = \
        os.path.join( Config.GetRootDir(), 'res/Arial Black.ttf' )
#        os.path.join( Config.GetRootDir(), 'res/Times New Roman Bold.ttf' )
    self.pilFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Verdana Bold.ttf' )
    self.valueFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' )

    super( RasterWidget, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadFinish_0()		-
  #----------------------------------------------------------------------
  def _BitmapThreadFinish_0( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
"""
    if result is None:
      cur_tuple = pil_im = None
      try_count = 0
    else:
      cur_tuple, pil_im, try_count = result.get()

    if cur_tuple is None:
      print >> sys.stderr, \
          '[RasterWidget._BitmapThreadFinish] xxx cur_tuple is None xxx'
    if pil_im is None:
      print >> sys.stderr, \
          '[RasterWidget._BitmapThreadFinish] xxx pil_im is None xxx'

    if cur_tuple is not None:
#			-- Create bitmap
#			--
      if pil_im is None:
	if try_count < 2:
          print >> sys.stderr, \
'[RasterWidget._BitmapThreadFinish] retrying image thread, try_count=', \
try_count
	  th = wxlibdr.startWorker(
	      self._BitmapThreadFinish,
	      self._BitmapThreadStart,
	      wargs = [ cur_tuple, try_count + 1 ]
	      )
	else:
          bmap = self.blankBitmap

      else:
        wx_im = wx.EmptyImage( *pil_im.size )

        pil_im_data_str = pil_im.convert( 'RGB' ).tobytes()
        wx_im.SetData( pil_im_data_str )

        pil_im_data_str = pil_im.convert( 'RGBA' ).tobytes()
        wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

        bmap = wx.BitmapFromImage( wx_im )

#	with self.bitmapsLock:
#	  self.bitmaps[ cur_tuple ] = bmap
	self.bitmapsLock.acquire()
	try:
	  self.bitmaps[ cur_tuple ] = bmap
	  self.bitmapThreadArgs = None
	finally:
	  self.bitmapsLock.release()
      #end else pil_im not None

      if self.IsTupleCurrent( cur_tuple ):
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
        self.bitmapCtrl.Update()
    #end if cur_pair is not None:

    self._BusyEnd()
  #end _BitmapThreadFinish_0


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadFinish()		-
  #----------------------------------------------------------------------
  def _BitmapThreadFinish( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
"""
    if result is None:
      cur_tuple = pil_im = None
      try_count = 0
    else:
      cur_tuple, pil_im, try_count = result.get()

#		-- Log these conditions
#		--
    if cur_tuple is None:
      print >> sys.stderr, \
          '[RasterWidget._BitmapThreadFinish] XXX cur_tuple is None XXX'
    if pil_im is None:
      print >> sys.stderr, \
          '[RasterWidget._BitmapThreadFinish] XXX pil_im is None XXX'

#		-- Retry image creation thread?
#		--
    if cur_tuple is not None and pil_im is None and try_count < 2:
      print >> sys.stderr, \
'[RasterWidget._BitmapThreadFinish] retrying image thread, try_count=', \
try_count
      th = wxlibdr.startWorker(
          self._BitmapThreadFinish,
	  self._BitmapThreadStart,
	  wargs = [ cur_tuple, try_count + 1 ]
	  )

#		-- No, normal processing
#		--
    else:
      self._BitmapThreadFinishImpl( cur_tuple, pil_im )
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadFinishImpl()		-
  #----------------------------------------------------------------------
  def _BitmapThreadFinishImpl( self, cur_tuple, pil_im ):
    """Called from _BitmapThreadFinish().
"""
#		-- No tuple, give up
#		--
    if cur_tuple is not None:
      if pil_im is None:
        bmap = self.blankBitmap

#			-- Create bitmap
#			--
      else:
        wx_im = wx.EmptyImage( *pil_im.size )

        pil_im_data_str = pil_im.convert( 'RGB' ).tobytes()
        wx_im.SetData( pil_im_data_str )

        pil_im_data_str = pil_im.convert( 'RGBA' ).tobytes()
        wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

        bmap = wx.BitmapFromImage( wx_im )

#	with self.bitmapsLock:
#	  self.bitmaps[ cur_tuple ] = bmap
	self.bitmapsLock.acquire()
	try:
	  self.bitmaps[ cur_tuple ] = bmap
	  self.bitmapThreadArgs = None
	finally:
	  self.bitmapsLock.release()
      #end else pil_im not None

      if self.IsTupleCurrent( cur_tuple ):
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
        self.bitmapCtrl.Update()
    #end if cur_pair is not None:

    self._BusyEnd()
  #end _BitmapThreadFinishImpl


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadStart()		-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, next_tuple, try_count = 0 ):
    """Background thread task to create the wx.Bitmap for the next
tuple in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateRasterImage().
@return			( next_tuple, PIL_image )
"""
    pil_im = None

    if next_tuple is not None and self.config is not None:
      pil_im = self._CreateRasterImage( next_tuple )

      if pil_im is None:
        print >> sys.stderr, \
            '[RasterWidget._BitmapThreadStart] XXX pil_im is None XXX'

    return  ( next_tuple, pil_im, try_count )
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._ClearBitmaps()			-
  # Must be called from the UI thread.
  # @param  keep_tuple	tuple to keep, or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_tuple = None ):
    self.bitmapsLock.acquire()
    try:
      self.bitmapCtrl.SetBitmap( self.blankBitmap )

      tuples = list( self.bitmaps.keys() )
      for t in tuples:
	if keep_tuple is None or keep_tuple != t:
          b = self.bitmaps[ t ]
	  del self.bitmaps[ t ]
	  b.Destroy()
      #end for
    finally:
      self.bitmapsLock.release()
  #end _ClearBitmaps


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._Configure()			-
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    wd, ht = self.bitmapPanel.GetClientSize()
    print >> sys.stderr, '[RasterWidget._Configure] %d,%d' % ( wd, ht )

    self.config = None
    if wd > 0 and ht > 0 and self.data is not None and \
        self.data.HasData() and self.cellRange is not None:
      self.config = self._CreateDrawConfig( size = ( wd, ht ) )
  #end _Configure


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CopyBitmap()			-
  #----------------------------------------------------------------------
  def _CopyBitmap( self, bmap ):
    """Makes a copy of the bitmap, which is assumed to be in RGBA format.
@param  bmap		bitmap to copy
@return			copy of bitmap
"""
    new_bmap = None

    if bmap is not None:
      block = chr( 0 ) * bmap.GetWidth() * bmap.GetHeight() * 4
      bmap.CopyToBuffer( block, wx.BitmapBufferFormat_RGBA )
	#new_bmap = wx.Bitmap.FromBufferRGBA( bmap.GetWidth(), bmap.GetHeight(),block )
      new_bmap = wx.EmptyBitmapRGBA( bmap.GetWidth(), bmap.GetHeight() )
      new_bmap.CopyFromBuffer( block, wx.BitmapBufferFormat_RGBA )

    return  new_bmap
  #end _CopyBitmap


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateBaseDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateBaseDrawConfig( self, ds_range, **kwargs ):
    """Creates common config values needed by most rasters.  Should be
called from subclass _CreateDrawConfig() methods.
@param  ds_range	current dataset value range
@param  kwargs
    scale	pixels per smallest drawing unit
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize      (if size specified)
    dataRange
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
    pilFontSmall
"""

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[RasterWidget._CreateBaseDrawConfig] size=%d,%d' % ( wd, ht )
      font_size = self._CalcFontSize( wd )

    else:
#      scale = kwargs.get( 'scale', 8 )
#      print >> sys.stderr, \
#          '[RasterWidget._CreateBaseDrawConfig] scale=%d' % scale
      font_size = self._CalcFontSize( 512 )

    if self.showLegend:
      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
      legend_size = legend_pil_im.size
    else:
      legend_pil_im = None
      legend_size = ( 0, 0 )

    label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
    label_size = \
        label_font.getsize( '99' ) if self.showLabels else ( 0, 0 )

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )
    pil_font_small = PIL.ImageFont.truetype( self.pilFontPath, font_size - 2 )
    pil_font2 = PIL.ImageFont.truetype( self.pilFont2Path, font_size )

    config = \
      {
      'dataRange': ds_range,
      'fontSize': font_size,
      'labelFont': label_font,
      'labelSize': label_size,
      'legendPilImage': legend_pil_im,
      'legendSize': legend_size,
      'pilFont': pil_font,
      'pilFont2': pil_font2,
      'pilFontSmall': pil_font_small
      }
    if 'size' in kwargs:
      config[ 'clientSize' ] = kwargs[ 'size' ]

    return  config
  #end _CreateBaseDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateClipboardImage()		-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return			bitmap or None
"""
    bmap = None
    cur_tuple = self._CreateStateTuple()
    if cur_tuple in self.bitmaps:
      bmap = self.bitmaps[ cur_tuple ]
    elif self.bitmapCtrl is not None:
      bmap = self.bitmapCtrl.GetBitmap()

    return  bmap
    #return  self.bitmapCtrl.GetBitmap() if self.bitmapCtrl is not None else None
  #end _CreateClipboardImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Noop version which must be overridden by subclasses, calling this
first.
Either size or scale should be specified as arguments.  If neither are
specified, a default scale value of 8 is used.
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys needed by _CreateRasterImage().
"""
    return  {}
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateEmptyPilImage()		-
  #----------------------------------------------------------------------
  def _CreateEmptyPilImage( self, size = ( 16, 16 ) ):
    return  PIL.Image.new( "RGBA", size )
  #end _CreateEmptyPilImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateMenuDef()			-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( RasterWidget, self )._CreateMenuDef( data_model )

    find_max_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'max', True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'max', False )
	}
      ]

    find_min_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'min', True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'min', False )
	}
      ]

    raster_def = \
      [
	{ 'label': '-' },
	{ 'label': 'Find Maximum', 'submenu': find_max_def },
	{ 'label': 'Find Minimum', 'submenu': find_min_def },
	{ 'label': '-' },
	{ 'label': 'Hide Labels', 'handler': self._OnToggleLabels },
	{ 'label': 'Hide Legend', 'handler': self._OnToggleLegend },
        { 'label': 'Unzoom', 'handler': self._OnUnzoom }
      ]
#    raster_def = \
#      [
#	( '-', None ),
#	( 'Find Maximum', find_max_def ),
#	( '-', None ),
#	( 'Hide Labels', self._OnToggleLabels ),
#	( 'Hide Legend', self._OnToggleLegend ),
#        ( 'Unzoom', self._OnUnzoom )
#      ]
    return  menu_def + raster_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreatePopupMenu()			-
  #----------------------------------------------------------------------
  def _CreatePopupMenu( self ):
    """Calls _UpdateVisibilityMenuItems().
Must be called from the UI thread.
"""
    popup_menu = super( RasterWidget, self )._CreatePopupMenu()

    if popup_menu is not None:
      self._UpdateVisibilityMenuItems(
          popup_menu,
          'Labels', self.showLabels,
          'Legend', self.showLegend
          )

    return  popup_menu
  #end _CreatePopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    config = self._CreateDrawConfig( scale = self.GetPrintScale() )
    pil_im = self._CreateRasterImage( self._CreateStateTuple(), config )

    if pil_im is not None:
      pil_im.save( file_path, 'PNG' )
#      pil_im2 = PIL.Image.new( "RGBA", pil_im.size, ( 236, 236, 236, 255 ) )
#      pil_im2.paste( pil_im, ( 0, 0 ), pil_im )
#      pil_im2.save( file_path.replace( '.png', '.gif' ), 'GIF' )
    return  file_path
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config_in = None ):
    """Called in background task to create the PIL image for the state.
The config and data attributes are good to go.
This implementation returns None and must be overridden by subclasses.
@param  tuple_in	state tuple
@param  config_in	optional config to use instead of self.config
@return			PIL image
"""
    return  None
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateStateBitmapArgs()		-
  #----------------------------------------------------------------------
#  def _CreateStateBitmapArgs( self ):
#    """Concatenates the results of _CreateRasterImage(), curSize, and
#cellRange.
#"""
#    return  self._CreateStateTuple() + self.curSize + self.cellRange
#  #end _CreateStateBitmapArgs


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """Should be overridden by subclasses to create the tuple passed to
_CreateRasterImage().
"""
    return  ()
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateTitleFormat()		-
  #----------------------------------------------------------------------
  def _CreateTitleFormat(
      self, pil_font, ds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1
      ):
    """Creates the title format and default string for sizing.
@param  pil_font	PIL font to use for sizing
@param  ds_name		dataset name
@param  ds_shape	dataset shape
@param  time_ds_name	optional time dataset name
@param  assembly_ndx	shape index for Assembly, or -1 if Assembly should not				be displayed
@param  axial_ndx	shape index for Axial, or -1 if Axial should not be
			displayed
@return			( format-string, size-tuple )
"""
    title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    comma_flag = False
    size_args = []

    if assembly_ndx >= 0 and ds_shape[ assembly_ndx ] > 1:
      title_fmt += 'Assembly %%d'
      size_args.append( 99 )
      comma_flag = True

    if axial_ndx >= 0 and ds_shape[ axial_ndx ] > 1:
      if comma_flag:
        title_fmt += ', '
      title_fmt += 'Axial %%.3f'
      size_args.append( 99.999 )
      comma_flag = True

    if time_ds_name:
      if comma_flag:
        title_fmt += ', '
      title_fmt += '%s %%.3g' % time_ds_name
      size_args.append( 99.999 )

    title_size = pil_font.getsize( title_fmt % tuple( size_args ) )

    return  title_fmt, title_size
  #end _CreateTitleFormat


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateTitleString()		-
  #----------------------------------------------------------------------
  def _CreateTitleString( self, title_templ, **kwargs ):
    """Creates the title template and default string for sizing.
@param  title_templ	template created with _CreateTitleTemplate()
@param  kwargs		keyword arguments
		'assembly'	0-based assembly index
		'axial'		axial value in cm
		'time'		time dataset value
@return			title string
"""
    targs = {}
    if 'assembly' in kwargs:
      targs[ 'assembly' ] = '%d' % (kwargs[ 'assembly' ] + 1)
    if 'axial' in kwargs:
      targs[ 'axial' ] = '%.3f' % kwargs[ 'axial' ]
    if 'time' in kwargs:
      targs[ 'time' ] = '%.4g' % kwargs[ 'time' ]
      
    return  title_templ.substitute( targs )
  #end _CreateTitleString


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateTitleTemplate()		-
  #----------------------------------------------------------------------
  def _CreateTitleTemplate(
      self, pil_font, ds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1
      ):
    """Creates the title template and default string for sizing.
@param  pil_font	PIL font to use for sizing
@param  ds_name		dataset name
@param  ds_shape	dataset shape
@param  time_ds_name	optional time dataset name
@param  assembly_ndx	shape index for Assembly, or -1 if Assembly should not				be displayed
@param  axial_ndx	shape index for Axial, or -1 if Axial should not be
			displayed
@return			( string.Template, size-tuple )
"""
    title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    comma_flag = False
    size_values = {}

    if assembly_ndx >= 0 and ds_shape[ assembly_ndx ] > 1:
      title_fmt += 'Assembly ${assembly}'
      size_values[ 'assembly' ] = '99'
      comma_flag = True

    if axial_ndx >= 0 and ds_shape[ axial_ndx ] > 1:
      if comma_flag:
        title_fmt += ', '
      title_fmt += 'Axial ${axial}'
      size_values[ 'axial' ] = '999.999'
      comma_flag = True

    if time_ds_name:
      if comma_flag:
        title_fmt += ', '
      title_fmt += '%s ${time}' % time_ds_name
      size_values[ 'time' ] = '9.99e+99'

    title_templ = string.Template( title_fmt )
    title_size = pil_font.getsize( title_templ.substitute( size_values ) )

    return  title_templ, title_size
  #end _CreateTitleTemplate


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateTitleTemplate2()		-
  #----------------------------------------------------------------------
  def _CreateTitleTemplate2(
      self, pil_font, ds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1, additional = None
      ):
    """Creates the title template and default string for sizing.
@param  pil_font	PIL font to use for sizing
@param  ds_name		dataset name
@param  ds_shape	dataset shape
@param  time_ds_name	optional time dataset name
@param  assembly_ndx	shape index for Assembly, or -1 if Assembly should not				be displayed
@param  axial_ndx	shape index for Axial, or -1 if Axial should not be
			displayed
@param  additional	single or tuple of items to add
@return			( string.Template, size-tuple )
"""
    title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    comma_flag = False
    size_values = {}

    if assembly_ndx >= 0 and ds_shape[ assembly_ndx ] > 1:
      title_fmt += 'Assembly ${assembly}'
      size_values[ 'assembly' ] = '99'
      comma_flag = True

    if axial_ndx >= 0 and ds_shape[ axial_ndx ] > 1:
      if comma_flag:
        title_fmt += ', '
      title_fmt += 'Axial ${axial}'
      size_values[ 'axial' ] = '999.999'
      comma_flag = True

    if additional is not None:
      if not hasattr( additional, '__iter__' ):
        additional = [ additional ]
      for item in additional:
        if comma_flag:
	  title_fmt += ', '
        title_fmt += item
	comma_flag = True
    #end if

    if time_ds_name:
      if comma_flag:
        title_fmt += ', '
      title_fmt += '%s ${time}' % time_ds_name
      size_values[ 'time' ] = '9.99e+99'

    title_templ = string.Template( title_fmt )
    title_size = pil_font.getsize( title_templ.substitute( size_values ) )

    return  title_templ, title_size
  #end _CreateTitleTemplate2


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.  This implementation returns a blank string.
@param  cell_info	tuple returned from FindCell()
"""
    return  ''
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateValueDisplay()		-
  #----------------------------------------------------------------------
  def _CreateValueDisplay( self, value, precision, font, display_wd, font_size = 0 ):
    """Creates  string representation of the value that fits in the
requested width for the specified font.
@param  value		value to represent
@param  precision	requested precision
@param  font		rendering font
@param  display_wd	pixel width available for display
@param  font_size	optional size for dynamic resize
@return			( string of optimal length, ( wd, ht ), font )
"""
    value_str = self._CreateValueString( value, precision )
    value_size = font.getsize( value_str )
    eval_str = value_str if len( value_str ) >= precision else '9' * precision
    eval_size = font.getsize( eval_str )

    #if value_size[ 0 ] >= display_wd:
    if eval_size[ 0 ] >= display_wd:
      precision -= 1
      value_str = self._CreateValueString( value, precision )
      value_size = font.getsize( value_str )
      eval_str = value_str if len( value_str ) >= precision else '9' * precision
      eval_size = font.getsize( eval_str )

#new stuff
      #if value_size[ 0 ] >= display_wd and font_size > 7:
      if eval_size[ 0 ] >= display_wd and font_size > 7:
        font_size = int( font_size * 0.8 )
        font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
        value_str = self._CreateValueString( value, precision )
        value_size = font.getsize( value_str )

      if value_size[ 0 ] >= display_wd:
	value_str = ''
	value_size = ( 0, 0 )
#new stuff

    return  ( value_str, value_size, font )
  #end _CreateValueDisplay


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateValueString()		-
  #----------------------------------------------------------------------
  def _CreateValueString( self, value, precision = 3 ):
    """Creates the string representation of minimal length for a value to
be displayed in a cell.
@param  value		value to represent
@param  precision	requested precision
@return			string of minimal length
"""
    if value < 0.0:
      precision -= 1
    value_str = DataUtils.FormatFloat2( value, precision )
    e_ndx = value_str.lower().find( 'e' )
    #if e_ndx > 1:
    if e_ndx > 0:
      value_str = value_str[ : e_ndx ]

    return  value_str
  #end _CreateValueString


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._DrawValues()			-
  #----------------------------------------------------------------------
  def _DrawValues( self, draw_list, im_draw, font_size = 0 ):
    """Draws value text.
@param  draw_list	list of ( str, color, x, y, wd, ht )
@param  im_draw		PIL.ImageDraw.Draw reference
@param  font_size	font size hint
"""
    if draw_list and im_draw is not None:
#			-- Find widest string
#			--
      smallest_wd = sys.maxint
      widest_str = ""
      widest_len = 0
      for item in draw_list:
	if item[ -2 ] < smallest_wd:
	  smallest_wd = item[ -2 ]
	cur_len = len( item[ 0 ] )
        if cur_len > widest_len:
	  widest_str = item[ 0 ]
	  widest_len = cur_len
      #end for item

      if font_size == 0:
        font_size = smallest_wd >> 1

#			-- Reduce font size if necessary
#			--
    font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
    value_size = font.getsize( widest_str )
    while value_size[ 0 ] >= smallest_wd:
      font_size = int( font_size * 0.8 )
      if font_size < 6:
	value_size = ( 0, 0 )
      else:
        font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
	value_size = font.getsize( widest_str )
    #end if draw_list

    if value_size[ 0 ] > 0:
      for item in draw_list:
	value_size = font.getsize( item[ 0 ] )
        value_x = item[ 2 ] + ((item[ 4 ] - value_size[ 0 ]) >> 1)
	value_y = item[ 3 ] + ((item[ 5 ] - value_size[ 1 ]) >> 1)
	im_draw.text(
	    ( value_x, value_y ), item[ 0 ],
	    fill = item[ 1 ], font = font
	    )
      #end for item
    #end if value_size
  #end _DrawValues


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.FindCell()				-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return			tuple with cell info or None, where cell info is
			( item_index, col, row, ... )
"""
    return  None
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetData()				-
  #----------------------------------------------------------------------
  def GetData( self ):
    """
@return			data.DataModel reference or None
"""
    return  self.data
  #end GetData


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetInitialCellRange()		-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.data.ExtractSymmetryExtent().
Subclasses should override as needed.
@return			intial range of raster cells
			( left, top, right, bottom, dx, dy )
"""
    return \
        self.data.ExtractSymmetryExtent() if self.data is not None else \
	( 0, 0, 0, 0, 0, 0 )
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """Should be overridden by subclasses.
@return		28
"""
    return  28
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    """Show selections by drawing over the bitmap.  This implementation
does nothing.
@param  bmap		bitmap to highlight
@return			highlighted bitmap
"""
    return  bmap
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._InitEventHandlers()		-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    self.bitmapCtrl.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnLeftDown )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnLeftUp )
    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotion )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
Subclasses that override should call this implementation.
"""
    self.overlay = wx.Overlay()
    self.bitmapPanel = wx.Panel( self )
    self.bitmapCtrl = wx.StaticBitmap( self.bitmapPanel, bitmap = self.blankBitmap )

    self._InitEventHandlers()

#		-- Lay out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """Determines if the image tuple represents the current selection.
Must be overridden by subclasses.  Always returns False.
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    return  False
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Copies the state and initiates rendering of the first bitmap.
Sets attributes:
  axialValue
  cellRange
  cellRangeStack
  data
  stateIndex

Calls _LoadDataModelValues() and _LoadDataModelUI().
"""
    print >> sys.stderr, '[RasterWidget._LoadDataModel]'
    #self.data = State.FindDataModel( self.state )
    super( RasterWidget, self )._LoadDataModel()
    if self.data is not None and self.data.HasData() and \
        not self.isLoaded:
      self.isLoaded = True
      print >> sys.stderr, '[RasterWidget._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      self.cellRange = list( self.GetInitialCellRange() )
      del self.cellRangeStack[ : ]

      self.axialValue = self.state.axialValue
      self.stateIndex = self.state.stateIndex

      with self.bitmapsLock:
        self.bitmapThreadArgs = None

      self._LoadDataModelValues()
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModelUI()			-
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self ):
    """This implementation calls Redraw().
Must be called on the UI thread.
"""
#    self.axialBean.SetRange( 1, self.data.core.nax )
#    self.axialBean.axialLevel = 0
#    self.exposureBean.SetRange( 1, len( self.data.states ) )
#    self.exposureBean.stateIndex = 0
    self.Redraw()  # self._OnSize( None )
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    pass
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    self.isLoaded = True

    for k in (
	'axialValue', 'cellRange', 'cellRangeStack',
	'showLabels', 'showLegend', 'stateIndex'
        ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )
#    if 'axialValue' in props_dict:
#      self.axialValue = props_dict[ 'axialValue' ]
#    if 'cellRange' in props_dict:
#      self.cellRange = props_dict[ 'cellRange' ]
#    if 'cellRangeStack' in props_dict:
#      self.cellRangeStack = props_dict[ 'cellRangeStack' ]
#    if 'showLabels' in props_dict:
#      self.showLabels = props_dict[ 'showLabels' ]
#    if 'showLegend' in props_dict:
#      self.showLegend = props_dict[ 'showLegend' ]
#    if 'stateIndex' in props_dict:
#      self.stateIndex = props_dict[ 'stateIndex' ]

    super( RasterWidget, self ).LoadProps( props_dict )
    wx.CallAfter( self.UpdateState, resized = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnClick()				-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """Noop implementation to be provided by subclasses.
"""
    pass
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnDragFinished()			-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
This implementation is a noop.
"""
    pass
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnLeftDown()			-
  #----------------------------------------------------------------------
  def _OnLeftDown( self, ev ):
    """
"""
    self.bitmapCtrl.SetToolTipString( '' )
    cell_info = self.FindCell( *ev.GetPosition() )
    if cell_info is not None:
      self.dragStartCell = cell_info
      self.dragStartPosition = ev.GetPosition()
  #end _OnLeftDown


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnLeftUp()			-
  #----------------------------------------------------------------------
  def _OnLeftUp( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[RasterWidget._OnLeftUp] enter'
    zoom_flag = False

    if self.HasCapture():
      self.ReleaseMouse()

    rect = None
    if self.dragStartPosition is not None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    #elif self.dragStartPosition == ev.GetPosition():
    if rect is None or rect.width <= 5 or rect.height <= 5:
      self._OnClick( ev )

    else:
      x = ev.GetX()
      y = ev.GetY()
      cell_info = self.FindCell( x, y )
      #print >> sys.stderr, \
          #'\n[RasterWidget._OnLeftUp] cell_info=', str( cell_info )

      if cell_info is not None:
        left = min( self.dragStartCell[ 1 ], cell_info[ 1 ] )
        right = max( self.dragStartCell[ 1 ], cell_info[ 1 ] ) + 1
	top = min( self.dragStartCell[ 2 ], cell_info[ 2 ] )
	bottom = max( self.dragStartCell[ 2 ], cell_info[ 2 ] ) + 1

	self.cellRangeStack.append( self.cellRange )
	self.cellRange = [ left, top, right, bottom, right - left, bottom - top ]
	zoom_flag = True
	self._OnDragFinished( *self.cellRange[ 0 : 4 ] )
      #end if assy found
    #end else dragging

    self.dragStartAssembly = None
    self.dragStartPosition = None

    self.overlay.Reset()
    self.Refresh()

    if zoom_flag:
      self.Redraw()  # self._OnSize( None )
  #end _OnLeftUp


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnMouseMotion()			-
  #----------------------------------------------------------------------
  def _OnMouseMotion( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition is None:
      tip_str = ''
      cell_info = self.FindCell( *ev.GetPosition() )

      #if assy is not None and assy[ 0 ] >= 0:
      if cell_info is not None:
        tip_str = self._CreateToolTipText( cell_info )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      #print >> sys.stderr, '[RasterWidget._OnMouseMotion]', str( rect )

      if rect.width > 5 and rect.height > 5:
        dc = wx.ClientDC( self.bitmapCtrl )
        odc = wx.DCOverlay( self.overlay, dc )
#		MacOS bug doesn't properly copy or restore the saved
#		image, so we don't do this here until the bug is fixed
        #odc.Clear()

        if 'wxMac' in wx.PlatformInfo:
          dc.SetPen( wx.Pen( 'black', 2 ) )
          dc.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          dc.DrawRectangle( *rect )
        else:
	  odc.Clear()
          ctx = wx.GraphicsContext_Create( dc )
          ctx.SetPen( wx.GREY_PEN )
          ctx.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          ctx.DrawRectangle( *rect )
        del odc
      #end if moved sufficiently
    #end else dragging
  #end _OnMouseMotion


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnSize()				-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev is None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[RasterWidget._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data is not None and \
        (self.curSize is None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
      self._BusyBegin()
      self.curSize = ( wd, ht )
      #wx.CallAfter( self._Configure )
      wx.CallAfter( self.UpdateState, resized = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnToggleLabels()			-
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
        self.GetPopupMenu() \
	if menu == self.container.GetWidgetMenu() else \
	self.container.GetWidgetMenu()
    if other_menu is not None:
      self._UpdateVisibilityMenuItems(
          other_menu,
	  'Labels', self.showLabels
	  )

#		-- Redraw
#		--
    self.UpdateState( resized = True )
  #end _OnToggleLabels


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnToggleLegend()			-
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
        self.GetPopupMenu() \
	if menu == self.container.widgetMenu else \
	self.container.widgetMenu
    if other_menu is not None:
      self._UpdateVisibilityMenuItems(
          other_menu,
	  'Legend', self.showLegend
	  )

#		-- Redraw
#		--
    self.UpdateState( resized = True )
  #end _OnToggleLegend


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self.Redraw()  #self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.Redraw()				-
  #----------------------------------------------------------------------
  def Redraw( self ):
    """Calls _OnSize( None )
"""
    self._OnSize( None )
  #end Redraw


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( RasterWidget, self ).SaveProps( props_dict )

    for k in (
	'axialValue', 'cellRange', 'cellRangeStack',
	'showLabels', 'showLegend', 'stateIndex'
        ):
      props_dict[ k ] = getattr( self, k )

#    props_dict[ 'axialValue' ] = self.axialValue
#    props_dict[ 'cellRange' ] = self.cellRange
#    props_dict[ 'cellRangeStack' ] = self.cellRangeStack
#    props_dict[ 'showLabels' ] = self.showLabels
#    props_dict[ 'showLegend' ] = self.showLegend
#    props_dict[ 'stateIndex' ] = self.stateIndex
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.UpdateState()			-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """Called to update the components on a new state property.
Calls _UpdateStateValues().
@param  kwargs		any state change values plus 'resized', 'changed'
"""
    self._BusyBegin()

    if 'scale_mode' in kwargs:
      kwargs[ 'resized' ] = True

    kwargs = self._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    end_busy = True

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config is not None:
      tpl = self._CreateStateTuple()
      bitmap_args = tpl + self.curSize + tuple( self.cellRange )

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if tpl in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self._HiliteBitmap( self.bitmaps[ tpl ] ) )
	  must_create_image = False
        elif bitmap_args == self.bitmapThreadArgs:
	  must_create_image = False
        else:
	  self.bitmapThreadArgs = bitmap_args
      finally:
        self.bitmapsLock.release()

      if must_create_image:
	end_busy = False
        print >> sys.stderr, \
	    '[RasterWidget.UpdateState] %s starting worker, args=%s' % \
	    ( self.GetTitle(), str( tpl + self.curSize ) )
	th = wxlibdr.startWorker(
	    self._BitmapThreadFinish,
	    self._BitmapThreadStart,
	    wargs = [ tpl, 0 ]
	    )
      #else:
        #self._BusyEnd()
    #end if

    if end_busy:
      self._BusyEnd()
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
In this implementation 'axial_value', 'state_index', and 'time_dataset'
are handled.  Subclasses should override and call this first.
@return			kwargs with 'changed' and/or 'resized'
"""
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      changed = True
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      #changed = True
      if self.state.scaleMode == 'state':
        resized = True
      else:
        changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if 'time_dataset' in kwargs:
      resized = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end RasterWidget
