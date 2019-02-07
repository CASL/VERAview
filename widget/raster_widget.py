#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           raster_widget.py                                -
#       HISTORY:                                                        -
#               2018-12-26      leerw@ornl.gov                          -
#         Working on seemless notification for busy operations.
#               2018-12-24      leerw@ornl.gov                          -
#         Invoking VeraViewApp.DoBusyEventOp() in event handlers.
#               2018-11-14      leerw@ornl.gov                          -
#         Stripping trailing zeros in _CreateValueDisplay().
#               2018-10-20      leerw@ornl.gov                          -
#         Moved _CreateEmptyBitmapAndDC() and _CreateGraphicsContext()
#         to RasterWidget.
#               2018-08-13      leerw@ornl.gov                          -
#         Enforcing minimum font size in _DrawValuesWx().
#               2018-05-30      leerw@ornl.gov                          -
#         Fixed _OnLeftUp() to append to zoom stack only if the new range
#         differs from self.cellRange.
#               2018-03-09      leerw@ornl.gov                          -
#         New 'mapper' (matplotlib.cm.ScalarMappable) draw config param.
#               2018-03-08      leerw@ornl.gov                          -
#         New 'scale_type' draw config param.
#               2018-03-02      leerw@ornl.gov                          -
#         Added _CreateGraphicsContent().  Fixed _CreateBaseDrawConfig()
#         to apply the font_scale to the label font.
#               2018-03-01      leerw@ornl.gov                          -
#         Added _CreateEmptyBitmapAndDC() and _CreateTransparentBrush().
#               2018-02-14      leerw@ornl.gov                          -
#         Using a wx.Timer to manage resize events to avoid bitmap
#         creation for transient sizes.
#               2018-02-10      leerw@ornl.gov                          -
#         Fixed dataset menu update after creation of a derived dataset
#         with call-after invocation of menu.UpdateMenu() in
#         _UpdateStateValues().
#               2018-02-09      leerw@ornl.gov                          -
#         Using assembly address in _CreateTitleString().
#               2018-02-05      leerw@ornl.gov                          -
#         Moving Linux/GTK/X11 image manipulation to the UI thread.
#         Added _CreateEmptyBitmap().
#               2018-01-16      leerw@ornl.gov                          -
#         Fixed bug in _CreateMenuDef() for not _IsAssemblyAware().
#               2017-11-13      leerw@ornl.gov                          -
#         Added _GetPointSize().
#               2017-11-03      leerw@ornl.gov                          -
#         Working with new point-based font scaling.
#               2017-10-24      leerw@ornl.gov                          -
#         Switching to wxPython Fonts and wx.Bitmap instead of PIL.Image.
#               2017-09-13      leerw@ornl.gov                          -
#         Added DrawLinePoly().
#               2017-08-18      leerw@ornl.gov                          -
#         Using AxialValue class.
#               2017-05-13      leerw@ornl.gov                          -
#         Added legend_title param to _CreateBaseDrawConfig(), passed
#         to _CreateLegendPilImage().
#               2017-05-05      leerw@ornl.gov                          -
#         Modified LoadDataModelXxx() methods to process the reason param.
#               2017-04-01      leerw@ornl.gov                          -
#         Added self.formatter, calling self.formatter.Format() in
#         _CreateValueString().
#               2017-03-28      leerw@ornl.gov                          -
#         Added DrawArcPoly2().
#               2017-03-10      leerw@ornl.gov                          -
#         Modified _CreateValue{Display,String}() to handle precision
#         digits and mode and use string.format().
#               2017-03-08      leerw@ornl.gov                          -
#         Added DrawArc().
#               2017-02-28      leerw@ornl.gov                          -
#         Using ScrolledPanel
#               2017-02-03      leerw@ornl.gov                          -
#         Adding white background image save option.
#               2017-01-26      leerw@ornl.gov                          -
#         Applying new limits to font scaling.
#               2017-01-18      leerw@ornl.gov                          -
#         Back to multiple threads.
#               2016-12-15      leerw@ornl.gov                          -
#         Cleaning up BitmapThreadFinish() to report exception. Duh!!.
#               2016-12-09      leerw@ornl.gov                          -
#               2016-12-08      leerw@ornl.gov                          -
#         Migrating to new DataModelMgr.
#               2016-10-30      leerw@ornl.gov                          -
#         Checking smallest_ht in _DrawValues().
#               2016-10-26      leerw@ornl.gov                          -
#         Using logging.
#               2016-10-20      leerw@ornl.gov                          -
#         Removed Redraw() call from _LoadDataModelUI() since
#         Widget.HandleStateChange() now calls UpdateState().
#               2016-10-14      leerw@ornl.gov                          -
#         Added _DrawValues() method.
#               2016-09-29      leerw@ornl.gov                          -
#         Modified _CreateValue{Display,String}() in an effort to
#         prevent overrun of values displayed in cells.
#               2016-08-15      leerw@ornl.gov                          -
#         New State events.
#               2016-06-30      leerw@ornl.gov                          -
#         Added isLoaded with check in _LoadDataModel() against call to
#         _LoadDataModelValues().
#               2016-06-23      leerw@ornl.gov                          -
#         Added {Load,Save}Props().
#               2016-03-16      leerw@ornl.gov                          -
#         Moving find-max calcs to DataModel and methods to Widget.
#               2016-03-14      leerw@ornl.gov                          -
#         Added menu options to find maximum values.
#               2016-02-29      leerw@ornl.gov                          -
#         Added Redraw() to call _OnSize( None ).
#               2016-01-25      leerw@ornl.gov                          -
#         Cleaning up the menu mess.
#               2016-01-22      leerw@ornl.gov                          -
#         Adding clipboard copy.
#               2016-01-15      leerw@ornl.gov                          -
#         Fixed bug in UpdateState() where _BusyEnd() was not called if
#         no state changes.
#               2015-12-03      leerw@ornl.gov                          -
#         Added _CreateValueString().
#               2015-11-28      leerw@ornl.gov                          -
#         Added 'dataRange' to returned config rec in _CreateBaseDrawConfig().
#               2015-11-23      leerw@ornl.gov                          -
#         Added self.bitmapThreadArgs = tpl + self.curSize to help
#         eliminate unnecessary threads.
#               2015-11-18      leerw@ornl.gov                          -
#         Added GetData().
#               2015-08-20      leerw@ornl.gov                          -
#         Added workaround for MacOS DCOverlay bug in _OnMouseMotion().
#               2015-06-17      leerw@ornl.gov                          -
#         Generalization of the 2D raster view widgets.
#------------------------------------------------------------------------
import cStringIO, functools, logging, math, os, re
import six, string, sys, traceback, threading, time
import numpy as np
import pdb  #pdb.set_trace()
#import time, traceback

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  from matplotlib import cm, colors, transforms
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.config import *
from data.rangescaler import *
from event.state import *

from .widget import *


REGEX_trailingZeros = re.compile( '([^\.]*)\.0*$' )


#------------------------------------------------------------------------
#       CLASS:          RasterWidget                                    -
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

timeValue
  current time value

Framework Methods
-----------------

_CreateAdditionalUIControls()
  Optional hook for extensions to create panels to be placed at the top,
  right, bottom, or left of the widget.

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
  Implementation here returns self.dmgr.ExtractSymmetryExtent(), but extensions
  may override as appropriate to define the range of assembly columns/rows, or
  channel/pin columns/rows to display initially.

GetPrintFontScale()
  Scale factor to apply to font sizing, defaults to 2.0.

#GetPrintScale()
#  Configuration scale factor to apply for creating raster images for printing.
#  The default here is 28, but this should be overridden by extensions.

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

_IsAssemblyAware()
  True if the processes or cares about the assembly selection

IsTupleCurrent()
  Must be implemented by extensions to indicate if the specified event state
  tuple represents the current selection.

_LoadDataModel()
  Implements this Widget framework method by populating properties
  *axialValue*, *cellRange*, *cellRangeStack*, *data*, and *stateIndex*.  It
  then calls _LoadDataModelValues() and _LoadDataModelUI(), the latter on the
  UI thread.

_LoadDataModelUI()
  The method defined here is a noop, but extensions can override this
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
---------------

_CreateEmptyBitmap()
  Deprecated, handles Linux-vs-Mac,Win calls to wx.EmptyBitmapRGBA().

_CreateEmptyBitmapAndDC()
  Encapsulates platform-specific creation of a transparent bitmap

_CreateGraphicsContext()
  Creates a wx.GraphicsContext and initializes it.

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
"""


#               -- Class Attributes
#               --

  jobid_ = 0


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.__init__()                         -
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    """
"""
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
#nt self.bitmapThreads = {}  # key is args, only used in threaded image creation
    #self.bitmapThreadArgs = None
    self.bitmaps = {}  # key is (row,col)
    self.bitmapsLock = threading.RLock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.config = None
    self.curDataSet = None  # DataSetName instance
    self.curSize = None
    self.dragStartCell = None
    self.dragStartPosition = None
    self.fitMode = 'ht'
    #self.isLoaded = False

    self.showLabels = True
    self.showLegend = True
    self.stateIndex = -1
    self.timeValue = -1.0
    self.timer = None

    self.bitmapCtrl = None
    self.bitmapPanel = None
    self.blankBitmap = self.GetBitmap( 'loading' )
    self.emptyBitmap = wx.EmptyBitmapRGBA( 16, 16 )
    ##self.emptyPilImage = PIL.Image.new( "RGBA", ( 16, 16 ) )
    #self.emptyImage = wx.EmptyImage( 16, 16 )

    self.overlay = None
    
#               -- Fonts
#               --
    client_rect = wx.GetClientDisplayRect()
    font_pt_size = \
        12  if client_rect.Width >= 1280 else \
        10  if client_rect.Width >= 1024 else \
        8
    if Config.IsWindows():
      font_pt_size = int( font_pt_size * 0.8 )

    # FONTFAMILY_: SWISS(sans), ROMAN(serif), SCRIPT, MODERN, TELETYPE
    # FONTSTYLE_: NORMAL, ITALIC, SLANT
    # FONTWEIGHT_: NORMAL, LIGHT, BOLD
    font_params = \
      {
      'pointSize': font_pt_size,
      'family': wx.FONTFAMILY_SWISS,
      'style': wx.FONTSTYLE_NORMAL,
      'weight': wx.FONTWEIGHT_NORMAL
      }
    font2_params = dict( font_params )
    if Config.IsWindows():
      font_params[ 'faceName' ] = 'Lucida Sans' # 'Arial'
      font_params[ 'weight' ] = wx.FONTWEIGHT_BOLD
      font2_params[ 'faceName' ] = 'Lucida Sans' # 'Times New Roman'
      font2_params[ 'weight' ] = wx.FONTWEIGHT_BOLD
    else:
      font2_params[ 'family' ] = wx.FONTFAMILY_ROMAN

    self.font = self.labelFont = self.valueFont = wx.Font( **font_params )
    self.font2 = wx.Font( **font2_params )

    super( RasterWidget, self ).__init__( container, id )

    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info(
          '%s: client_rect=%s, font_pt_size=%d',
          self.GetTitle(), str( client_rect ), font_pt_size
          )
      if self.GetTitle() == 'Core 2D View':
        self.logger.info(
            'font info: face=%s, pointsize=%d',
            self.font.GetFaceName(), self.font.GetPointSize()
            )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._BitmapThreadFinish()              -
  #----------------------------------------------------------------------
  def _BitmapThreadFinish( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
"""
    bitmap_args = cur_tuple = bmap = None
    job_id = -1
    if result is not None:
      try:
        #cur_tuple, bmap, bitmap_args = result.get()
        #job_id = result.getJobID()
        result_obj = result.get()
        if result_obj is not None and len( result_obj ) == 3:
          cur_tuple, bmap, bitmap_args = result_obj
          job_id = result.getJobID()

        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug(
              '%s: cur_tuple=%s, bitmap_args=%s, job_id=%d, bmap-is-None=%d',
              self.GetTitle(), cur_tuple, str( bitmap_args ), job_id,
              bmap is None
              )

#                       -- Log these conditions
#                       --
        if cur_tuple is None:
          self.logger.warning( '* %s: cur_tuple is None *' % self.GetTitle() )
        if bmap is None:
          self.logger.warning( '* %s: bmap is None *' % self.GetTitle() )

      except Exception, ex:
        msg = '%s%s: Error creating image: %s' % \
            ( os.linesep, self.GetTitle(), str( ex ) )
        if hasattr( ex, 'extraInfo' ):
          msg += os.linesep + str( ex.extraInfo )
#       et, ev, tb = sys.exc_info()
#       log_msg = msg
#       while tb:
#         log_msg += \
#             os.linesep + 'File=' + str( tb.tb_frame.f_code ) + \
#             ', Line=' + str( traceback.tb_lineno( tb ) )
#         tb = tb.tb_next
        #self.logger.exception( msg )
        output = cStringIO.StringIO()
        try:
          print >> output, msg
          traceback.print_exc( 10, output )
          self.logger.error( output.getvalue() )
        finally:
          output.close()
        wx.MessageBox( msg, 'CreateImage', wx.ICON_ERROR | wx.OK_DEFAULT )
    #end if result is not None

#               -- Always complete
#               --
    self._BitmapThreadFinishImpl( cur_tuple, bmap, bitmap_args )
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._BitmapThreadFinishImpl()          -
  #----------------------------------------------------------------------
  def _BitmapThreadFinishImpl( self, cur_tuple, bmap, bitmap_args ):
    """Called from _BitmapThreadFinish().
"""

#               -- No tuple, give up
#               --
    if cur_tuple is not None and bitmap_args is not None:
      #bmap = None

      if bmap is None:
        bmap = self.blankBitmap
        if self.logger.isEnabledFor( logging.INFO ):
          self.logger.info( '%s: ** bmap is None **', self.GetTitle() )

#                       -- Create bitmap
#                       --
      #else:
      elif bitmap_args is not None:
        self.bitmapsLock.acquire()
        try:
          if bitmap_args in self.bitmapThreads:
#            wx_im = wx.EmptyImage( *pil_im.size )
#
#            pil_im_data_str = pil_im.convert( 'RGB' ).tobytes()
#            wx_im.SetData( pil_im_data_str )
#
#            pil_im_data_str = pil_im.convert( 'RGBA' ).tobytes()
#            wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )
#
#            bmap = wx.BitmapFromImage( wx_im )

            self.bitmaps[ cur_tuple ] = bmap
            del self.bitmapThreads[ bitmap_args ]
            #self.bitmapThreadArgs = None
          #end if bitmap_args in self.bitmapThreads

        finally:
          self.bitmapsLock.release()

        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug(
              '%s: bmap is not None, cur_tuple=%s, bmap=%s',
              self.GetTitle(), str( cur_tuple ), str( bmap )
              )
      #end else im not None

      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
            '%s: cur_tuple=%s, isTupleCurrent=%d, bmap-is-blankBitmap=%d',
            self.GetTitle(), str( cur_tuple ),
            self.IsTupleCurrent( cur_tuple ), bmap == self.blankBitmap
            )
      if bmap is not None and self.IsTupleCurrent( cur_tuple ):
        self._SetBitmap( self._HiliteBitmap( bmap ) )
    #end if cur_tuple is not None and bitmap_args is not None

#x    self._BusyEnd()
    if len( self.bitmapThreads ) == 0:
      self._BusyEnd()
  #end _BitmapThreadFinishImpl


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._BitmapThreadStart()               -
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, next_tuple, bitmap_args, job_id ):
    """Background thread task to create the wx.Bitmap for the next
tuple in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateRasterImage().
@return                 ( next_tuple, wx.Bitmap )
"""
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          '%s: next_tuple=%s, bitmap_args=%s, job_id=%d',
          self.GetTitle(), str( next_tuple ), str( bitmap_args ), job_id
          )

    bmap = None

    #xxx catch exception, add to returned tuple
    if next_tuple is not None and self.config is not None:
      bmap = self._CreateRasterImage( next_tuple )

      if bmap is None:
        self.logger.warning( '%s: * bmap is None *', self.GetTitle() )

# There is some sync issue with wx.lib.delayedresult where the return value
# from this method is not available to result.get() in _BitmapThreadFinish().
# Hence, we add a short sleep.
      #time.sleep( 0.001 )

    #return  ( next_tuple, im, try_count )
    result_tpl = ( next_tuple, bmap, bitmap_args )
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          '%s: returning, next_tuple=%s, bmap-is-None=%d',
          self.GetTitle(), next_tuple, bmap is None
          )

    return  result_tpl
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._ClearBitmaps()                    -
  # Must be called from the UI thread.
  # @param  keep_tuple  tuple to keep, or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_tuple = None ):
    self.bitmapsLock.acquire()
    try:
#nt   self.bitmapThreads.clear()
      self._SetBitmap( self.blankBitmap )

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
  #     METHOD:         RasterWidget._Configure()                       -
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    #xxx if scrollable it would be self.GetClientSize()
    wd, ht = self.bitmapPanel.GetClientSize()
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( '%s: wd=%d, ht=%d', self.GetTitle(), wd, ht )

    self.config = None
    if wd > 0 and ht > 0 and \
        self.dmgr.HasData() and self.cellRange is not None:
      self.config = self._CreateDrawConfig( size = ( wd, ht ) )
  #end _Configure


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CopyBitmap()                      -
  #----------------------------------------------------------------------
  def _CopyBitmap( self, bmap ):
    """Makes a copy of the bitmap, which is assumed to be in RGBA format.
@param  bmap            bitmap to copy
@return                 copy of bitmap
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
  #     METHOD:         RasterWidget._CreateAdditionalUIControls()      -
  #----------------------------------------------------------------------
  def _CreateAdditionalUIControls( self ):
    """Hook for extensions to add controls/panels to the widget.  This noop
implementation returns None.

@return                 None or a dict with keys 'top', 'right', 'bottom',
                        and/or 'left' with values being a Control
"""
    return  None
  #end _CreateAdditionalUIControls


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateAndSetBitmap()              -
  #----------------------------------------------------------------------
  def _CreateAndSetBitmap( self, cur_tuple, bitmap_args = None ):
    """Non-threaded image creation.
"""
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( '%s: cur_tuple=%s', self.GetTitle(), cur_tuple )

    #bmap = None
    bmap = self.blankBitmap

    if cur_tuple is not None and self.config is not None:
      self.bitmapsLock.acquire()
      try:
        bmap = self._CreateRasterImage( cur_tuple )

        if bmap is None:
          self.logger.warning( '%s: * bmap is None *', self.GetTitle() )
          #bmap = self.blankBitmap
          if cur_tuple in self.bitmaps:
            del self.bitmaps[ cur_tuple ]

        else:
          self.bitmaps[ cur_tuple ] = bmap

#nt       if bitmap_args is not None and bitmap_args in self.bitmapThreads:
#nt         del self.bitmapThreads[ bitmap_args ]
        #end else im is not None:

      finally:
        self.bitmapsLock.release()

      if self.IsTupleCurrent( cur_tuple ):
        if bmap is not None:
          bmap = self._HiliteBitmap( bmap )
        else:
          bmap = self.blankBitmap
        self._SetBitmap( bmap )
    #end if cur_tuple is not None and self.config is not None
  #end _CreateAndSetBitmap


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateBaseDrawConfig()            -
  #----------------------------------------------------------------------
  def _CreateBaseDrawConfig( self, ds_range, **kwargs ):
    """Creates common config values needed by most rasters.  Should be
called from subclass _CreateDrawConfig() methods.
@param  ds_range        current dataset value range
@param  kwargs
    colormap_name  optional override colormap name
    font_scale  optional scaling to apply to fonts
    printing  True if printing
    scale_type  'linear' or 'log', defaulting to 'linear'
    size        ( wd, ht ) against which to compute the scale
    legend_title  optional legend title
@return                 config dict with keys:
    clientSize      (if size specified)
    dataRange
    font
    fontExtent                  pixel size of an 'X'
    fontSize                    point size
    labelFont
    labelSize
    legendBitmap
    legendSize
    mapper (cm.Scalarappable)
#    pilFont
#    pilFontSmall
    valueFont
"""
    font_scale = kwargs.get( 'font_scale', 1.0 )

#               -- Determine widget size
#               --
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( '%s: size=%d,%d', self.GetTitle(), wd, ht )
    else:
      wd = 1280
      ratio = float( self.cellRange[ -1 ] ) / float( self.cellRange[ -2 ] )
      if ratio >= 3.0:
        ratio = min( ratio, 3.0 )
        ht = 1900
        wd = int( math.ceil( ht / ratio ) )
      else:
        ht = int( math.ceil( wd * ratio ) )
      kwargs[ 'size' ] = ( wd, ht )

#               -- Get fonts, scaled if necessary
#               --
    if font_scale == 1.0:
      font_size = self.font.GetPointSize()
      font = self.font
      label_font = self.labelFont
      value_font = self.valueFont
    else:
      font_size = int( self.font.GetPointSize() * font_scale )
      font = self.font.Scaled( font_scale )
      label_font = self.labelFont.Scaled( font_scale )
      value_font = self.valueFont.Scaled( font_scale )

#               -- Create Mapper
#               --
    scale_type = kwargs.get( 'scale_type', 'linear' )
#    class_name = \
#        'colors.LogNorm'  if scale_type == 'log' else \
#       'colors.Normalize'
#    params = '( vmin = ds_range[ 0 ], vmax = ds_range[ 1 ], clip = True )'
#    norm = eval( class_name + params )
    if scale_type == 'log':
      norm = colors.LogNorm(
          vmin = max( ds_range[ 0 ], 1.0e-16 ),
          vmax = max( ds_range[ 1 ], 1.0e-16 ),
          clip = True
          )
    else:
      norm = colors.Normalize(
          vmin = ds_range[ 0 ], vmax = ds_range[ 1 ], clip = True
          )
    cmap_name = kwargs.get( 'colormap_name', self.colormapName )
    mapper = cm.ScalarMappable(
        norm = norm,
        cmap = cm.get_cmap( cmap_name )  # Config.defaultCmapName_
        )

#               -- Create legend
#               --
    if self.showLegend:
      legend_bmap = self._CreateLegendBitmap(
          ds_range,
          font_size = font_size,
          mapper = mapper,
          ntick_values = 8,
          scale_type = scale_type,
          title = kwargs.get( 'legend_title' )
          )
#      legend_bmap = self._CreateLegendBitmap(
#          ds_range, font_size,
#         gray = kwargs.get( 'gray', False ),
#         scale_type = kwargs.get( 'scale_type', 'linear' ),
#         title = kwargs.get( 'legend_title' )
#         )
      legend_size = ( legend_bmap.GetWidth(), legend_bmap.GetHeight() )
    else:
      legend_bmap = None
      legend_size = ( 0, 0 )

#               -- Calculate label size
#               --
    dc = wx.MemoryDC()
    dc.SelectObject( self.emptyBitmap )
    dc.SetFont( label_font )
    if self.showLabels:
      #dc = wx.MemoryDC()
      #dc.SelectObject( self.emptyBitmap )
      #dc.SetFont( label_font )
      label_size = dc.GetTextExtent( "99" )
      #dc.SelectObject( wx.NullBitmap )
    else:
      label_size = ( 0, 0 )

    dc.SetFont( font )
    font_extent = dc.GetTextExtent( 'X' )
    dc.SelectObject( wx.NullBitmap )

#               -- Create dict
#               --
    config = \
      {
      'clientSize': kwargs[ 'size' ],
      'dataRange': ds_range,
      'font': font,
#      'fontSmall': font_small,
      'fontExtent': font_extent,
      'fontSize': font_size,
      'labelFont': label_font,
      'labelSize': label_size,
      'legendBitmap': legend_bmap,
      'legendSize': legend_size,
      'mapper': mapper,
      'valueFont': value_font
      }
#    if 'size' in kwargs:
#      config[ 'clientSize' ] = kwargs[ 'size' ]

    return  config
  #end _CreateBaseDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateClipboardImage()            -
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return                 bitmap or None
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
  #     METHOD:         RasterWidget._CreateDrawConfig()                -
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Noop version which must be overridden by subclasses, calling this
first.
Either size or scale should be specified as arguments.  If neither are
specified, a default scale value of 8 is used.
@param  kwargs
    scale       pixels per pin
    size        ( wd, ht ) against which to compute the scale
@return                 config dict with keys needed by _CreateRasterImage().
"""
    return  {}
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateEmptyBitmap()               -
  #----------------------------------------------------------------------
  def _CreateEmptyBitmap( self, wd, ht ):
    """Encapsulates Linux/GTK differences.
    Args:
        wd (int): Image width in pixels
        ht (int): Image height in pixels
    Returns:
        wx.Bitmap: New bitmap object
"""
    if Config.IsLinux():
      bg_color = self.GetBackgroundColour()
      bmap = wx.EmptyBitmapRGBA(
          wd, ht,
          bg_color.red, bg_color.green, bg_color.blue, bg_color.alpha
          )
    else:
      bmap = wx.EmptyBitmapRGBA( wd, ht )

    return  bmap
  #end _CreateEmptyBitmap


##  #----------------------------------------------------------------------
##  #     METHOD:         RasterWidget._CreateEmptyBitmapAndDC()                -
##  #----------------------------------------------------------------------
##  def _CreateEmptyBitmapAndDC( self, wd, ht, bg_color = None, dc = None ):
##    """Encapsulates platform differences.
##    Args:
##        wd (int): Image width in pixels
##      ht (int): Image height in pixels
##      bg_color (wx.Colour): optional explicit background color
##      dc (wx.MemoryDC): optional DC to initialize, None to create a new
##          instance
##    Returns:
##        wx.Bitmap, wx.MemoryDC: New bitmap object, new DC or ``dc``
##"""
##    if Config.IsLinux() and bg_color is None:
##      bg_color = self.GetBackgroundColour()
##
##    if bg_color is None:
##      bmap = wx.EmptyBitmapRGBA( wd, ht )
##    else:
##      bmap = wx.EmptyBitmapRGBA(
##          wd, ht,
##        bg_color.red, bg_color.green, bg_color.blue, bg_color.alpha
##        )
##
##    if dc is None:
##      dc = wx.MemoryDC()
##    dc.SelectObject( bmap )
##
##    if Config.IsWindows():
##      dc.SetBackground( wx.TheBrushList.FindOrCreateBrush(
##          wx.WHITE, wx.BRUSHSTYLE_SOLID
##        ) )
##      dc.Clear()
##    else:
##      dc.SetBackground( wx.TheBrushList.FindOrCreateBrush(
##          wx.WHITE, wx.TRANSPARENT
##        ) )
##
##    return  bmap, dc
##  #end _CreateEmptyBitmapAndDC


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateEmptyPilImage()             -
  #----------------------------------------------------------------------
#  def _CreateEmptyPilImage( self, size = ( 16, 16 ) ):
#    return  PIL.Image.new( "RGBA", size )
#  #end _CreateEmptyPilImage


##  #----------------------------------------------------------------------
##  #     METHOD:         RasterWidget._CreateGraphicsContext()         -
##  #----------------------------------------------------------------------
##  def _CreateGraphicsContext( self, dc ):
##    """Calls wx.GraphicsContent.Create() and then SetAntialiasMode() and
##SetInterpolationQuality() on the resulting GC.
##    Args:
##      dc (wx.DC): DC from which to create the GC
##    Returns:
##      wx.GraphicsContext
##"""
##    gc = wx.GraphicsContext.Create( dc )
##    if Config.IsWindows():
##      gc.SetAntialiasMode( wx.ANTIALIAS_NONE )
##    else:
##      gc.SetAntialiasMode( wx.ANTIALIAS_DEFAULT )
##      gc.SetInterpolationQuality( wx.INTERPOLATION_BEST )
##
##    return  gc
##  #end _CreateGraphicsContext


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateMenuDef()                   -
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( RasterWidget, self )._CreateMenuDef()

    if self._IsAssemblyAware():
      all_assy_max_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'max', True, True )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'max', False, True )
          }
        ]
      all_assy_min_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'min', True, True )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'min', False, True )
          }
        ]

      cur_assy_max_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'max', True, False )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'max', False, False )
          }
        ]
      cur_assy_min_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'min', True, False )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'min', False, False )
          }
        ]

      find_max_def = \
        [
          { 'label': 'All Assemblies', 'submenu': all_assy_max_def },
          { 'label': 'Current Assembly', 'submenu': cur_assy_max_def }
        ]
      find_min_def = \
        [
          { 'label': 'All Assemblies', 'submenu': all_assy_min_def },
          { 'label': 'Current Assembly', 'submenu': cur_assy_min_def }
        ]

    else:
      find_max_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'max', True, True )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'max', False, True )
          }
        ]

      find_min_def = \
        [
          {
          'label': 'All State Points',
          'handler': functools.partial( self._OnFindMinMax, 'min', True, True )
          },
          {
          'label': 'Current State Point',
          'handler': functools.partial( self._OnFindMinMax, 'min', False, True )
          }
        ]
    #end else not self._IsAssemblyAware()

    raster_def = \
      [
        { 'label': '-' },
        { 'label': 'Find Maximum', 'submenu': find_max_def },
        { 'label': 'Find Minimum', 'submenu': find_min_def },
        { 'label': '-' },
        { 'label': 'Fit Width', 'handler': self._OnToggleFit },
        { 'label': 'Hide Labels', 'handler': self._OnToggleLabels },
        { 'label': 'Hide Legend', 'handler': self._OnToggleLegend },
        { 'label': 'Unzoom', 'handler': self._OnUnzoom }
      ]
#    raster_def = \
#      [
#       ( '-', None ),
#       ( 'Find Maximum', find_max_def ),
#       ( '-', None ),
#       ( 'Hide Labels', self._OnToggleLabels ),
#       ( 'Hide Legend', self._OnToggleLegend ),
#        ( 'Unzoom', self._OnUnzoom )
#      ]
    return  menu_def + raster_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreatePopupMenu()                 -
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
  #     METHOD:         RasterWidget.CreatePrintImage()                 -
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path, bgcolor = None, hilite = False ):
    """
"""
    config = self._CreateDrawConfig(
        font_scale = self.GetPrintFontScale(),
        printing = True
        )
    bmap = self._CreateRasterImage( self._CreateStateTuple(), config )

    if bmap is not None:
      if hilite:
        bmap = self._HiliteBitmap( bmap, config )
      #pil_im.save( file_path, 'PNG' )
      im = wx.ImageFromBitmap( bmap )
      if im.HasAlpha() and bgcolor and \
          hasattr( bgcolor, '__iter__' ) and len( bgcolor ) >= 4:
        for y in xrange( im.GetHeight() ):
          for x in xrange( im.GetWidth() ):
            pix_value = (
                im.GetRed( x, y ), im.GetGreen( x, y ), im.GetBlue( x, y ),
                im.GetAlpha( x, y )
                )
            if pix_value == ( 0, 0, 0, 0 ) or pix_value == ( 255, 255, 255, 0 ):
              im.SetRGB( x, y, bgcolor[ 0 ], bgcolor[ 1 ], bgcolor[ 2 ] )
              im.SetAlpha( x, y, bgcolor[ 3 ] )
      #end if bgcolor

      im.SaveFile( file_path, wx.BITMAP_TYPE_PNG )
    #end if bmap is not None

    return  file_path
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateRasterImage()               -
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config_in = None ):
    """Called in background task to create the wx.Image for the state.
The config and data attributes are good to go.
This implementation returns None and must be overridden by subclasses.
@param  tuple_in        state tuple
@param  config_in       optional config to use instead of self.config
@return                 wx.Image
"""
    return  None
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateStateBitmapArgs()           -
  #----------------------------------------------------------------------
#  def _CreateStateBitmapArgs( self ):
#    """Concatenates the results of _CreateRasterImage(), curSize, and
#cellRange.
#"""
#    return  self._CreateStateTuple() + self.curSize + self.cellRange
#  #end _CreateStateBitmapArgs


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateStateTuple()                -
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """Should be overridden by subclasses to create the tuple passed to
_CreateRasterImage().
"""
    return  ()
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateTitleFormat()               -
  #----------------------------------------------------------------------
  def _CreateTitleFormat(
      self, font, qds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1
      ):
    """Creates the title format and default string for sizing.
@param  font            wx.Font to use for sizing
@param  qds_name        name of dataset, DataSetName instance
@param  ds_shape        dataset shape
@param  time_ds_name    optional time dataset name
@param  assembly_ndx    shape index for Assembly, or -1 if Assembly should not                          be displayed
@param  axial_ndx       shape index for Axial, or -1 if Axial should not be
                        displayed
@return                 ( format-string, size-tuple )
"""
    #title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    title_fmt = '%s: ' % qds_name.displayName
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

    dc = wx.MemoryDC()
    dc.SelectObject( self.emptyBitmap )
    dc.SetFont( font )
    title_size = dc.GetTextExtent( title_fmt % tuple( size_args ) )
    dc.SelectObject( wx.NullBitmap )

    return  title_fmt, title_size
  #end _CreateTitleFormat


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateTitleString()               -
  #----------------------------------------------------------------------
  def _CreateTitleString( self, title_templ, **kwargs ):
    """Creates the title template and default string for sizing.
    Args:
        title_templ (str): template created with _CreateTitleTemplate()
    Keyword Args:
        assembly (?): assembly address label or 0-based index
        axial (float): axial value in cm
        time (float): time dataset value
    Return:
        str: title string
"""
    targs = {}
    if 'assembly' in kwargs:
      if isinstance( kwargs[ 'assembly' ], int ):
        targs[ 'assembly' ] = '%d' % (kwargs[ 'assembly' ] + 1)
      else:
        targs[ 'assembly' ] = '%s' % str( kwargs[ 'assembly' ] )
    if 'axial' in kwargs:
      targs[ 'axial' ] = '%.3f' % kwargs[ 'axial' ]
    if 'time' in kwargs:
      targs[ 'time' ] = '%.4g' % kwargs[ 'time' ]
      
    return  title_templ.substitute( targs )
  #end _CreateTitleString


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateTitleTemplate()             -
  #----------------------------------------------------------------------
  def _CreateTitleTemplate(
      self, font, qds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1
      ):
    """Creates the title template and default string for sizing.
@param  font            wx.Font to use for sizing
@param  qds_name        name of dataset, DataSetName instance
@param  ds_shape        dataset shape
@param  time_ds_name    optional time dataset name
@param  assembly_ndx    shape index for Assembly, or -1 if Assembly should not                          be displayed
@param  axial_ndx       shape index for Axial, or -1 if Axial should not be
                        displayed
@return                 ( string.Template, size-tuple )
"""
    #title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    title_fmt = '%s: ' % self.dmgr.GetDataSetDisplayName( qds_name )
    comma_flag = False
    size_values = {}

    if assembly_ndx >= 0 and ds_shape[ assembly_ndx ] > 1:
      #title_fmt += 'Assembly ${assembly}'
      #size_values[ 'assembly' ] = '99'
      title_fmt += 'Assy ${assembly}'
      size_values[ 'assembly' ] = '(X-99)'
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

    dc = wx.MemoryDC()
    dc.SelectObject( self.emptyBitmap )
    dc.SetFont( font )
    title_size = dc.GetTextExtent( title_templ.substitute( size_values ) )
    dc.SelectObject( wx.NullBitmap )

    return  title_templ, title_size
  #end _CreateTitleTemplate


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateTitleTemplate2()            -
  #----------------------------------------------------------------------
  def _CreateTitleTemplate2(
      self, font, qds_name, ds_shape, time_ds_name = None,
      assembly_ndx = -1, axial_ndx = -1, additional = None
      ):
    """Creates the title template and default string for sizing.
@param  font            wx.Font to use for sizing
@param  qds_name        name of dataset, DataSetName instance
@param  ds_shape        dataset shape
@param  time_ds_name    optional time dataset name
@param  assembly_ndx    shape index for Assembly, or -1 if Assembly should not                          be displayed
@param  axial_ndx       shape index for Axial, or -1 if Axial should not be
                        displayed
@param  additional      single or tuple of items to add
@return                 ( string.Template, size-tuple )
"""
    #title_fmt = '%s: ' % self.data.GetDataSetDisplayName( ds_name )
    title_fmt = '%s: ' % self.dmgr.GetDataSetDisplayName( qds_name )
    comma_flag = False
    size_values = {}

    if assembly_ndx >= 0 and ds_shape[ assembly_ndx ] > 1:
      #title_fmt += 'Assembly ${assembly}'
      #size_values[ 'assembly' ] = '99'
      title_fmt += 'Assy ${assembly}'
      size_values[ 'assembly' ] = '(X-99)'
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

    if time_ds_name is not None:
      if comma_flag:
        title_fmt += ', '
      title_fmt += '%s ${time}' % time_ds_name
      size_values[ 'time' ] = '9.99e+99'

    title_templ = string.Template( title_fmt )

    dc = wx.MemoryDC()
    dc.SelectObject( self.emptyBitmap )
    dc.SetFont( font )
    title_size = dc.GetTextExtent( title_templ.substitute( size_values ) )
    dc.SelectObject( wx.NullBitmap )

    return  title_templ, title_size
  #end _CreateTitleTemplate2


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateToolTipText()               -
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.  This implementation returns a blank string.
@param  cell_info       tuple returned from FindCell()
"""
    return  ''
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateTransparentBrush()          -
  #----------------------------------------------------------------------
  def _CreateTransparentBrush( self, gc ):
    """Encapsulates platform differences.
    Args:
        gc (wx.GraphicsContext): context on which CreateBrush() is called
    Returns:
        wx.GraphicsBrush: brush
"""
#    if Config.IsWindows():
#      trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
#          wx.WHITE, wx.BRUSHSTYLE_SOLID
#         ) )
#    else:
    trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
        wx.WHITE, wx.TRANSPARENT
        ) )
    return  trans_brush
  #end _CreateTransparentBrush


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._CreateValueDisplay()              -
  #----------------------------------------------------------------------
  def _CreateValueDisplay(
       self, value, font, display_wd,
       prec_digits = None,
       prec_mode = None,
       font_size = 0
       ):
    """Creates  string representation of the value that fits in the
requested width for the specified font.
@param  value           value to represent
@param  font            rendering wx.Font
@param  display_wd      pixel width available for display
@param  prec_digits     optional override of self.precisionDigits
@param  prec_mode       optional override of self.precisionMode
@param  font_size       optional size for dynamic resize
@return                 ( string of optimal length, ( wd, ht ), font )
"""
    if prec_digits is None:
      prec_digits = self.precisionDigits
    if prec_mode is None:
      prec_mode = self.precisionMode

    dc = wx.MemoryDC()
    dc.SelectObject( self.emptyBitmap )
    dc.SetFont( font )
    font_size = font.GetPointSize()

    value_str = self._CreateValueString( value, prec_digits, prec_mode )
    value_size = dc.GetFullTextExtent( value_str )
    eval_str = \
        value_str  if len( value_str ) >= prec_digits else \
        '9' * prec_digits
    eval_size = dc.GetFullTextExtent( eval_str )

    while eval_size[ 0 ] >= display_wd and font_size > 6:
      font = font.Scaled( 5.0 / 6.0 )
      dc.SetFont( font )
      value_size = dc.GetFullTextExtent( value_str )
      eval_size = dc.GetFullTextExtent( eval_str )
      font_size = font.GetPointSize()

    if eval_size[ 0 ] >= display_wd and prec_digits > 1:
      prec_digits -= 1
      value_str = self._CreateValueString( value, prec_digits, prec_mode )
      value_size = dc.GetFullTextExtent( value_str )

    m = REGEX_trailingZeros.search( value_str )
    if m:
      value_str = m.group( 1 )
      value_size = dc.GetFullTextExtent( value_str )

    if value_size[ 0 ] >= display_wd:
      value_str = ''
      value_size = ( 0, 0 )

#    if Config.IsWindows() and value_size[ 1 ] > 2:
#      value_size = ( value_size[ 0 ], value_size[ 1 ] - 2 )
    if Config.IsWindows() and value_size[ 1 ] > (value_size[ 2 ] + 2):
      value_size = ( value_size[ 0 ], value_size[ 1 ] - value_size[ 2 ] )

    dc.SelectObject( wx.NullBitmap )
    return  ( value_str, value_size, font )
  #end _CreateValueDisplay


##  #----------------------------------------------------------------------
##  #   METHOD:         RasterWidget._CreateValueString()               -
##  #----------------------------------------------------------------------
##  def _CreateValueString( self, value, prec_digits = None, prec_mode = None ):
##    """Creates the string representation of minimal length for a value to
##be displayed in a cell.
##@param  value         value to represent
##@param  prec_digits   optional override of self.precisionDigits
##@param  prec_mode     optional override of self.precisionMode
##@return                       string of minimal length
##"""
##    if prec_digits is None:
##      prec_digits = self.precisionDigits
##    if prec_mode is None:
##      prec_mode = self.precisionMode
##
##    #value_str = DataUtils.FormatFloat4( value, prec_digits, prec_mode )
##    value_str = self.formatter.Format( value, prec_digits, prec_mode )
##    e_ndx = value_str.lower().find( 'e' )
##    #if e_ndx > 1:
##    if e_ndx > 0:
##      value_str = value_str[ : e_ndx ]
##
##    return  value_str
##  #end _CreateValueString


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.DrawArc()                          -
  #----------------------------------------------------------------------
  def DrawArc(
      self, draw, bbox, start, end, fill,
      width = 1, units = 'deg'
      ):
    """Fills a functional shortfall in PIL.ImageDraw.Draw by drawing an arc
with a specified line thickness.  Calls PIL.ImageDraw.line(), which takes
a width param.
@param  draw            PIL.ImageDraw.Draw instance
@param  bbox            bounding box
#@param  origin_x       origin X coordinate
#@param  origin_y       origin Y coordinate
#@param  radius         radius
@param  start           arc start angle
@param  end             arc end angle
@param  fill            fill/line color
@param  width           line width
@param  units           angle units, either 'deg' or 'rad', defaulting to the
                        former
"""
#    bbox = [
#       origin_x - radius, origin_y - radius,
#       origin_x + radius, origin_y + radius
#        ]

    st_rad = start * math.pi / 180.0  if units != 'rad'  else start
    en_rad = end * math.pi / 180.0  if units != 'rad'  else end
    #seg_incr = 2.0 * math.pi / 180.0
    seg_incr = math.pi / 180.0
    seg_incr_half = seg_incr / 2.0

    #st_rad -= seg_incr_half
    en_rad -= seg_incr_half

    rx = (bbox[ 2 ] - bbox[ 0 ]) / 2
    ry = (bbox[ 3 ] - bbox[ 1 ]) / 2

    cx = bbox[ 0 ] + rx
    cy = bbox[ 1 ] + ry
    seg_len = (rx + ry) * seg_incr / 2.0

    while st_rad < en_rad:
      cur_angle = st_rad + seg_incr_half
      cur_cos = math.cos( cur_angle )
      cur_sin = math.sin( cur_angle )
      x = cur_cos * rx + cx
      y = cur_sin * ry + cy

      dx = seg_len * -cur_sin * rx / (rx + ry)
      dy = seg_len * cur_cos * ry / (rx + ry)
      draw.line(
          [ x - dx, y - dy, x + dx, y + dy ],
          fill = fill,
          width = width
          )

      st_rad += seg_incr_half
    #end while
  #end DrawArc


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.DrawArcPoly()                      -
  #----------------------------------------------------------------------
  def DrawArcPoly(
      self, draw, bbox, start, end, fill,
      width = 1, units = 'deg'
      ):
    """Fills a functional shortfall in PIL.ImageDraw.Draw by drawing an arc
with a specified line thickness.  Calls PIL.ImageDraw.polygon() multiple times.
@param  draw            PIL.ImageDraw.Draw instance
@param  bbox            bounding box
@param  start           arc start angle
@param  end             arc end angle
@param  fill            fill/line color
@param  width           line width
@param  units           angle units, either 'deg' or 'rad', defaulting to the
                        former
"""
    st_rad = start * math.pi / 180.0  if units != 'rad'  else start
    en_rad = end * math.pi / 180.0  if units != 'rad'  else end
    if en_rad < st_rad:
      en_rad += 2.0 * math.pi

    seg_incr = math.pi / 180.0
    half_seg_incr = seg_incr / 2.0

    #incr_count = int( math.ceil( (en_rad - st_rad) / seg_incr ) )
    #st_rad -= seg_incr_half
    #en_rad -= seg_incr_half

    rx = (bbox[ 2 ] - bbox[ 0 ]) / 2
    ry = (bbox[ 3 ] - bbox[ 1 ]) / 2

    cx = bbox[ 0 ] + rx
    cy = bbox[ 1 ] + ry

    half_wd = width >> 1

#       -- Inside poly loop
    inner_pts = []
    cur_rad = st_rad
    while cur_rad <= en_rad:
      if len( inner_pts ) == 0:
        inner_pts.append(
            int( math.cos( cur_rad ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad ) * (ry - half_wd) + cy )
            )

      if cur_rad + half_seg_incr <= en_rad:
        inner_pts.append(
            int( math.cos( cur_rad + half_seg_incr ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad + half_seg_incr ) * (ry - half_wd) + cy )
            )
      if cur_rad + seg_incr <= en_rad:
        inner_pts.append(
            int( math.cos( cur_rad + seg_incr ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad + seg_incr ) * (ry - half_wd) + cy )
            )

      cur_rad += seg_incr
    #end while

    inner_pts.append( int( math.cos( en_rad ) * (rx - half_wd) + cx ) )
    inner_pts.append( int( math.sin( en_rad ) * (ry - half_wd) + cy ) )

    if width <= 2:
      draw.line( inner_pts, fill = fill, width = width )

    else:
#               -- Outside poly loop
      outer_pts = []
      cur_rad = en_rad
      while cur_rad >= st_rad:
        if len( outer_pts ) == 0:
          outer_pts.append(
              int( math.cos( cur_rad ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad ) * (ry + half_wd) + cy )
              )

        if cur_rad - half_seg_incr >= st_rad:
          outer_pts.append(
              int( math.cos( cur_rad - half_seg_incr ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad - half_seg_incr ) * (ry + half_wd) + cy )
              )
        if cur_rad - seg_incr >= st_rad:
          outer_pts.append(
              int( math.cos( cur_rad - seg_incr ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad - seg_incr ) * (ry + half_wd) + cy )
              )

        cur_rad -= seg_incr
      #end while

      outer_pts.append( int( math.cos( st_rad ) * (rx + half_wd) + cx ) )
      outer_pts.append( int( math.sin( st_rad ) * (ry + half_wd) + cy ) )

      pts = inner_pts + outer_pts
      pts.append( pts[ 0 ] )
      pts.append( pts[ 1 ] )

      draw.polygon( pts, fill = fill, outline = fill )
    #end if-else width <= 2
  #end DrawArcPoly


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.DrawArcPoly2()                     -
  #----------------------------------------------------------------------
  def DrawArcPoly2(
      self, draw_color_pairs, bbox, start, end,
      width = 1, units = 'deg'
      ):
    """Fills a functional shortfall in PIL.ImageDraw.Draw by drawing an arc
with a specified line thickness.  Calls PIL.ImageDraw.polygon() multiple times.
This version applies the calculated segments to mulitiple PIL.ImageDraw
instances.
@param  draw_color_pairs  sequence of ( PIL.ImageDraw.Draw instance,
                        color value ) pairs
                        cannot be None, wasteful to be empty
@param  bbox            bounding box
@param  start           arc start angle in specified units
@param  end             arc end angle in specified units
@param  fill            fill/line color
@param  width           line width in pixels
@param  units           angle units, either 'deg' or 'rad', defaulting to the
                        former
"""
    st_rad = start * math.pi / 180.0  if units != 'rad'  else start
    en_rad = end * math.pi / 180.0  if units != 'rad'  else end
    if en_rad < st_rad:
      en_rad += 2.0 * math.pi

    seg_incr = math.pi / 180.0
    half_seg_incr = seg_incr / 2.0

    rx = (bbox[ 2 ] - bbox[ 0 ]) / 2
    ry = (bbox[ 3 ] - bbox[ 1 ]) / 2

    cx = bbox[ 0 ] + rx
    cy = bbox[ 1 ] + ry

    half_wd = width >> 1

#       -- Inside poly loop
    inner_pts = []
    cur_rad = st_rad
    while cur_rad <= en_rad:
      if len( inner_pts ) == 0:
        inner_pts.append(
            int( math.cos( cur_rad ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad ) * (ry - half_wd) + cy )
            )

      if cur_rad + half_seg_incr <= en_rad:
        inner_pts.append(
            int( math.cos( cur_rad + half_seg_incr ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad + half_seg_incr ) * (ry - half_wd) + cy )
            )
      if cur_rad + seg_incr <= en_rad:
        inner_pts.append(
            int( math.cos( cur_rad + seg_incr ) * (rx - half_wd) + cx )
            )
        inner_pts.append(
            int( math.sin( cur_rad + seg_incr ) * (ry - half_wd) + cy )
            )

      cur_rad += seg_incr
    #end while

    inner_pts.append( int( math.cos( en_rad ) * (rx - half_wd) + cx ) )
    inner_pts.append( int( math.sin( en_rad ) * (ry - half_wd) + cy ) )

    if width <= 2:
      #draw.line( inner_pts, fill = fill, width = width )
      for draw, color in draw_color_pairs:
        draw.line( inner_pts, fill = color, width = width )

    else:
#               -- Outside poly loop
      outer_pts = []
      cur_rad = en_rad
      while cur_rad >= st_rad:
        if len( outer_pts ) == 0:
          outer_pts.append(
              int( math.cos( cur_rad ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad ) * (ry + half_wd) + cy )
              )

# Why not loop over half_seg_incr?
        if cur_rad - half_seg_incr >= st_rad:
          outer_pts.append(
              int( math.cos( cur_rad - half_seg_incr ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad - half_seg_incr ) * (ry + half_wd) + cy )
              )
        if cur_rad - seg_incr >= st_rad:
          outer_pts.append(
              int( math.cos( cur_rad - seg_incr ) * (rx + half_wd) + cx )
              )
          outer_pts.append(
              int( math.sin( cur_rad - seg_incr ) * (ry + half_wd) + cy )
              )

        cur_rad -= seg_incr
      #end while

      outer_pts.append( int( math.cos( st_rad ) * (rx + half_wd) + cx ) )
      outer_pts.append( int( math.sin( st_rad ) * (ry + half_wd) + cy ) )

      pts = inner_pts + outer_pts
      pts.append( pts[ 0 ] )
      pts.append( pts[ 1 ] )

      for draw, color in draw_color_pairs:
        draw.polygon( pts, fill = color, outline = color )
    #end if-else width <= 2
  #end DrawArcPoly2


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.DrawLinePoly()                     -
  #----------------------------------------------------------------------
  def DrawLinePoly( self, draw, pts, fill, width = 1 ):
    """Fills a functional shortfall in PIL.ImageDraw.Draw by drawing an arc
with a specified line thickness.  Calls PIL.ImageDraw.polygon() multiple times.
Not tested!!
@param  draw            PIL.ImageDraw.Draw instance
@param  pts             [ x1, y1, x2, y2 ]
@param  fill            fill/line color
@param  width           line width
"""

    if width <= 2:
      draw.line( pts, fill = fill, width = width )

    elif len( pts ) >= 4:
      half_wd = width >> 1

      inner_pts = []
      outer_pts = []
      for i in xrange( 0, len( pts ) - 3, 2 ):
        dx = pts[ i + 2 ] - pts[ i ]
        dy = pts[ i + 3 ] - pts[ i + 1 ]

        if dy >= dx:
          if len( inner_pts ) == 0:
            inner_pts.append( pts[ i ] - half_wd )
            inner_pts.append( pts[ i + 1 ] )
            outer_pts.append( pts[ i ] + half_wd )
            outer_pts.append( pts[ i + 1 ] )
          inner_pts.append( pts[ i + 2 ] - half_wd )
          inner_pts.append( pts[ i + 3 ] )
          outer_pts.append( pts[ i + 2 ] + half_wd )
          outer_pts.append( pts[ i + 3 ] )
        else:
          if len( inner_pts ) == 0:
            inner_pts.append( pts[ i ] )
            inner_pts.append( pts[ i + 1 ] - half_wd )
            outer_pts.append( pts[ i ] )
            outer_pts.append( pts[ i + 1 ] + half_wd )
          inner_pts.append( pts[ i + 2 ] )
          inner_pts.append( pts[ i + 3 ] - half_wd )
          outer_pts.append( pts[ i + 2 ] )
          outer_pts.append( pts[ i + 3 ] + half_wd )
      #end for i

      for i in xrange( len( outer_pts ) - 2, 0, -2 ):
        inner_pts.append( outer_pts[ i ] )
        inner_pts.append( outer_pts[ i + 1 ] )

      draw.polygon( inner_pts, fill = fill, outline = fill )
    #end else width > 2
  #end DrawLinePoly


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawStrings()                     -
  #----------------------------------------------------------------------
  def _DrawStrings( self, im_draw, font_size, *draw_list ):
    """Draws value text.
@param  im_draw         PIL.ImageDraw.Draw reference
@param  font_size       starting font size
@param  draw_list       list of ( str, color, x, y, wd, align 'l','r','c' )
"""
    if draw_list and im_draw is not None:
      for draw_tuple in draw_list:
        if len( draw_tuple ) >= 5:
          font = PIL.ImageFont.truetype( self.pilFontPath, font_size )
          value_size = font.getsize( draw_tuple[ 0 ] )
          while value_size[ 0 ] >= draw_tuple[ 4 ] and font_size > 6:
            font_size = int( font_size * 0.8 )
            font = PIL.ImageFont.truetype( self.pilFontPath, font_size )
            value_size = font.getsize( draw_tuple[ 0 ] )

          align = \
              'l'  if value_size[ 0 ] >= draw_tuple[ 4 ] else \
              draw_tuple[ 5 ]  if len( draw_tuple ) > 5  else \
              'c'
          if align == 'c':
            x = draw_tuple[ 2 ] + ((draw_tuple[ 4 ] - value_size[ 0 ]) / 2.0)
          elif align == 'r':
            x = draw_tuple[ 2 ] + draw_tuple[ 4 ] - value_size[ 0 ] - 1
          else:
            x = draw_tuple[ 2 ]

          im_draw.text(
              ( x, draw_tuple[ 3 ] ), draw_tuple[ 0 ],
              fill = draw_tuple[ 1 ], font = font
              )
        #end if len( draw_tuple ) >= 5
      #end for draw_tuple
    #end if draw_list and im_draw is not None
  #end _DrawStrings


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawStringsWx()                   -
  #----------------------------------------------------------------------
  def _DrawStringsWx( self, gc, font, *draw_list ):
    """Draws value text.
@param  gc              wx.GraphicsContext
@param  font            basis font
@param  draw_list       list of
            ( str, color, x, y, wd, align{ 'l','r','c' } [, center_wd ]  )
"""
    if draw_list and gc is not None:
#      trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
#          wx.WHITE, wx.TRANSPARENT
#         ) )

      for draw_tuple in draw_list:
        if len( draw_tuple ) >= 5:
          max_wd = draw_tuple[ 6 ] if len( draw_tuple ) > 6 else draw_tuple[ 4 ]
          #font = self.font.Scaled( font_size / 10.0 )
          cur_font = Widget.CopyFont( font )
          font_size = font.GetPointSize()
          gc.SetFont( cur_font )
          # wd, ht, descending, leading
          value_size = gc.GetFullTextExtent( draw_tuple[ 0 ] )
          while value_size[ 0 ] >= max_wd and font_size > 6:
            cur_font = cur_font.Scaled( 5.0 / 6.0 )
            font_size = cur_font.GetPointSize()
            gc.SetFont( cur_font )
            value_size = gc.GetFullTextExtent( draw_tuple[ 0 ] )

          align = \
              'l' if value_size[ 0 ] >= draw_tuple[ 4 ] else \
              draw_tuple[ 5 ]

          if align == 'c':
            x = draw_tuple[ 2 ] + ((draw_tuple[ 4 ] - value_size[ 0 ]) / 2.0)
          elif align == 'r':
            x = draw_tuple[ 2 ] + draw_tuple[ 4 ] - value_size[ 0 ] - 1
          else:
            x = draw_tuple[ 2 ]

          gc.SetPen( wx.ThePenList.FindOrCreatePen(
              wx.Colour( *draw_tuple[ 1 ] ), 1, wx.PENSTYLE_SOLID
              ) )
          #gc.DrawText( draw_tuple[ 0 ], x, draw_tuple[ 3 ], trans_brush )
          gc.DrawText( draw_tuple[ 0 ], x, draw_tuple[ 3 ] )
        #end if len( draw_tuple ) >= 5
      #end for draw_tuple
    #end if draw_list and gc is not None
  #end _DrawStringsWx


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawStringsWxDC()                 -
  #----------------------------------------------------------------------
  def _DrawStringsWxDC( self, dc, font, *draw_list ):
    """Draws value text.
@param  dc              wx.DC
@param  font            basis font
@param  draw_list       list of
            ( str, color, x, y, wd, align{ 'l','r','c' } [, center_wd ]  )
"""
    if draw_list and dc is not None:
      trans_brush = wx.TheBrushList.\
          FindOrCreateBrush( wx.WHITE, wx.TRANSPARENT )

      for draw_tuple in draw_list:
        if len( draw_tuple ) >= 5:
          max_wd = draw_tuple[ 6 ] if len( draw_tuple ) > 6 else draw_tuple[ 4 ]
          #font = self.font.Scaled( font_size / 10.0 )
          cur_font = Widget.CopyFont( font )
          font_size = font.GetPointSize()
          dc.SetFont( cur_font )
          # wd, ht, descending, leading
          value_size = dc.GetFullTextExtent( draw_tuple[ 0 ] )
          while value_size[ 0 ] >= max_wd and font_size > 6:
            cur_font = cur_font.Scaled( 5.0 / 6.0 )
            font_size = cur_font.GetPointSize()
            dc.SetFont( cur_font )
            value_size = dc.GetFullTextExtent( draw_tuple[ 0 ] )

          align = \
              'l' if value_size[ 0 ] >= draw_tuple[ 4 ] else \
              draw_tuple[ 5 ]

          if align == 'c':
            x = draw_tuple[ 2 ] + ((draw_tuple[ 4 ] - value_size[ 0 ]) / 2.0)
          elif align == 'r':
            x = draw_tuple[ 2 ] + draw_tuple[ 4 ] - value_size[ 0 ] - 1
          else:
            x = draw_tuple[ 2 ]

          dc.SetPen( wx.ThePenList.FindOrCreatePen(
              wx.Colour( *draw_tuple[ 1 ] ), 1, wx.PENSTYLE_SOLID
              ) )
          dc.DrawText( draw_tuple[ 0 ], x, draw_tuple[ 3 ] )
        #end if len( draw_tuple ) >= 5
      #end for draw_tuple
    #end if draw_list and gc is not None
  #end _DrawStringsWxDC


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawValues()                      -
  #----------------------------------------------------------------------
  def _DrawValues( self, draw_list, im_draw, font_size = 0 ):
    """Draws value text.
@param  draw_list       list of ( str, color, x, y, wd, ht )
@param  im_draw         PIL.ImageDraw.Draw reference
@param  font_size       font size hint
"""
    if draw_list and im_draw is not None:
#                       -- Align numbers
#                       --
      labels = []
      for item in draw_list:
        labels.append( item[ 0 ] )
      #RangeScaler.Format() now calls its own ForceSigDigits() method

#                       -- Find widest string
#                       --
      smallest_wd = sys.maxint
      smallest_ht = sys.maxint
      widest_str = ""
      widest_len = 0
      #for item in draw_list:
      for i in xrange( len( draw_list ) ):
        item = draw_list[ i ]
        if item[ -2 ] < smallest_wd:
          smallest_wd = item[ -2 ]
        if item[ -1 ] < smallest_ht:
          smallest_ht = item[ -1 ]
        cur_len = len( labels[ i ] )
        if cur_len > widest_len:
          widest_str = labels[ i ]
          widest_len = cur_len
      #end for item

      if font_size == 0:
        font_size = int( smallest_wd ) >> 1
      font_size = min( font_size, 28 )

#                       -- Reduce font size if necessary
#                       --
      font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
      value_size = font.getsize( widest_str )
      while value_size[ 0 ] >= smallest_wd or value_size[ 1 ] >= smallest_ht:
        font_size = int( font_size * 0.8 )
        if font_size < 6:
          value_size = ( 0, 0 )
        else:
          font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
          value_size = font.getsize( widest_str )

      if value_size[ 0 ] > 0:
        #for item in draw_list:
        for i in xrange( len( draw_list ) ):
          item = draw_list[ i ]
          value_size = font.getsize( labels[ i ] )
          value_x = item[ 2 ] + ((item[ 4 ] - value_size[ 0 ]) >> 1)
          value_y = item[ 3 ] + ((item[ 5 ] - value_size[ 1 ]) >> 1)
          im_draw.text(
              ( value_x, value_y ), labels[ i ],
              fill = item[ 1 ], font = font
              )
        #end for item
      #end if value_size
    #end if draw_list and im_draw is not None
  #end _DrawValues


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawValuesWx()                    -
  #----------------------------------------------------------------------
  def _DrawValuesWx( self, draw_list, gc, font_size = 0 ):
    """Draws value text.
@param  draw_list       list of ( str, color, x, y, wd, ht )
@param  gc              wx.GraphicsContext instance
@param  font_size       font pixel size hint
"""
    if draw_list and gc is not None:
      trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
          wx.WHITE, wx.TRANSPARENT
          ) )

#                       -- Align numbers
#                       --
      labels = []
      for item in draw_list:
        labels.append( item[ 0 ] )
      #RangeScaler.Format() now calls its own ForceSigDigits() method

#                       -- Find widest string
#                       --
      smallest_wd = sys.maxint
      smallest_ht = sys.maxint
      widest_str = ""
      widest_len = 0
      #for item in draw_list:
      for i in xrange( len( draw_list ) ):
        item = draw_list[ i ]
        if item[ -2 ] < smallest_wd:
          smallest_wd = item[ -2 ]
        if item[ -1 ] < smallest_ht:
          smallest_ht = item[ -1 ]
        cur_len = len( labels[ i ] )
        if cur_len > widest_len:
          widest_str = labels[ i ]
          widest_len = cur_len
      #end for item

      if smallest_wd > 3:
        smallest_wd -= 2

      #pts_per_dot = 72.0 / gc.GetDPI()[ 0 ]
      font = Widget.CopyFont( self.valueFont )
      if font_size == 0:
        font_size = max( int( smallest_wd ) >> 1, 1 )
      #font_pt_size = min( int( pts_per_dot * font_size ), 28 )
      font_pt_size = min( int( Widget.CalcPointSize( gc, font_size ) ), 24 )
      font.SetPointSize( font_pt_size )

#                       -- Reduce font size if necessary
#                       --
      gc.SetFont( font )
      value_size = gc.GetFullTextExtent( widest_str )
      while value_size[ 0 ] >= smallest_wd or value_size[ 1 ] >= smallest_ht:
        font = font.Scaled( 5.0 / 6.0 )
        font_pt_size = font.GetPointSize()
        if font_pt_size < 4:
          value_size = ( 0, 0 )
        else:
          gc.SetFont( font )
          value_size = gc.GetFullTextExtent( widest_str )

      if value_size[ 0 ] > 0:
        for i in xrange( len( draw_list ) ):
          item = draw_list[ i ]
          value_size = gc.GetFullTextExtent( labels[ i ] )
          value_x = item[ 2 ] + ((item[ 4 ] - value_size[ 0 ]) / 2.0)
          value_y = item[ 3 ] + ((item[ 5 ] - value_size[ 1 ]) / 2.0)

#         gc.SetPen( wx.ThePenList.FindOrCreatePen(
#             wx.Colour( *item[ 1 ] ), 1, wx.PENSTYLE_SOLID
#             ) )
          gc.SetFont( font, wx.Colour( *item[ 1 ] ) )
          gc.DrawText( labels[ i ], value_x, value_y, trans_brush )
        #end for item
      #end if value_size
    #end if draw_list and gc is not None
  #end _DrawValuesWx


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._DrawValuesWxDC()                  -
  #----------------------------------------------------------------------
  def _DrawValuesWxDC( self, draw_list, dc, font_size = 0 ):
    """Draws value text.
@param  draw_list       list of ( str, color, x, y, wd, ht )
@param  gc              wx.DC instance
@param  font_size       font pixel size hint
"""
    if draw_list and dc is not None:
      trans_brush = wx.TheBrushList.\
          FindOrCreateBrush( wx.WHITE, wx.TRANSPARENT )

#                       -- Align numbers
#                       --
      labels = []
      for item in draw_list:
        labels.append( item[ 0 ] )
      #RangeScaler.Format() now calls its own ForceSigDigits() method

#                       -- Find widest string
#                       --
      smallest_wd = sys.maxint
      smallest_ht = sys.maxint
      widest_str = ""
      widest_len = 0
      #for item in draw_list:
      for i in xrange( len( draw_list ) ):
        item = draw_list[ i ]
        if item[ -2 ] < smallest_wd:
          smallest_wd = item[ -2 ]
        if item[ -1 ] < smallest_ht:
          smallest_ht = item[ -1 ]
        cur_len = len( labels[ i ] )
        if cur_len > widest_len:
          widest_str = labels[ i ]
          widest_len = cur_len
      #end for item

      #pts_per_dot = 72.0 / gc.GetDPI()[ 0 ]
      font = Widget.CopyFont( self.valueFont )
      if font_size == 0:
        font_size = int( smallest_wd ) >> 1
      #font_pt_size = min( int( pts_per_dot * font_size ), 28 )
      font_pt_size = min( int( Widget.CalcPointSize( dc, font_size ) ), 28 )
      font.SetPointSize( font_pt_size )

#                       -- Reduce font size if necessary
#                       --
      dc.SetFont( font )
      value_size = dc.GetFullTextExtent( widest_str )
      while value_size[ 0 ] >= smallest_wd or value_size[ 1 ] >= smallest_ht:
        font = font.Scaled( 5.0 / 6.0 )
        font_pt_size = font.GetPointSize()
        if font_pt_size < 6:
          value_size = ( 0, 0 )
        else:
          dc.SetFont( font )
          value_size = dc.GetFullTextExtent( widest_str )

      if value_size[ 0 ] > 0:
        for i in xrange( len( draw_list ) ):
          item = draw_list[ i ]
#x          value_size = gc.GetFullTextExtent( labels[ i ] )
          value_size = dc.GetFullTextExtent( labels[ i ] )
          value_x = item[ 2 ] + ((item[ 4 ] - value_size[ 0 ]) / 2.0)
          value_y = item[ 3 ] + ((item[ 5 ] - value_size[ 1 ]) / 2.0)

#x        gc.SetPen( wx.ThePenList.FindOrCreatePen(
#x            wx.Colour( *item[ 1 ] ), 1, wx.PENSTYLE_SOLID
#x            ) )
#x        gc.DrawText( labels[ i ], value_x, value_y, trans_brush )
          dc.SetPen( wx.ThePenList.FindOrCreatePen(
              wx.Colour( *item[ 1 ] ), 1, wx.PENSTYLE_SOLID
              ) )
          dc.DrawText( labels[ i ], value_x, value_y )
        #end for item
      #end if value_size
    #end if draw_list and gc is not None
  #end _DrawValuesWxDC


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.FindCell()                         -
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return                 tuple with cell info or None, where cell info is
                        ( item_index, col, row, ... )
"""
    return  None
  #end FindCell


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.GetAxialValue()                    -
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return          AxialValue instance
( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.GetInitialCellRange()              -
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.dmgr.ExtractSymmetryExtent().
Subclasses should override as needed.
@return                 intial range of raster cells
                        ( left, top, right+1, bottom+1, dx, dy )
"""
    return  self.dmgr.ExtractSymmetryExtent()
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.GetPrintFontScale()                -
  #----------------------------------------------------------------------
  def GetPrintFontScale( self ):
    """Should be overridden by subclasses.
@return         2.0
"""
    return  2.0
  #end GetPrintFontScale


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.GetPrintScale()                    -
  #----------------------------------------------------------------------
#  def GetPrintScale( self ):
#    """Should be overridden by subclasses.
#@return                28
#"""
#    return  28
#  #end GetPrintScale


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.GetStateIndex()                    -
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return          0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._HiliteBitmap()                    -
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config_in = None ):
    """Show selections by drawing over the bitmap.  This implementation
does nothing.
@param  bmap            bitmap to highlight
@return                 highlighted bitmap
"""
    return  bmap
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._InitEventHandlers()               -
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
  #     METHOD:         RasterWidget._InitUI()                          -
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
Subclasses that override should call this implementation.
"""
    self.overlay = wx.Overlay()

    self.bitmapPanel = ScrolledPanel( self, -1 )
    self.bitmapPanel.SetAutoLayout( True )
    self.bitmapPanel.SetupScrolling()
    bmp_sizer = wx.BoxSizer( wx.VERTICAL )
    self.bitmapCtrl = \
        wx.StaticBitmap( self.bitmapPanel, bitmap = self.blankBitmap )
    bmp_sizer.Add( self.bitmapCtrl )
    self.bitmapPanel.SetSizer( bmp_sizer )

    self._InitEventHandlers()

#               -- Lay out
#               --
    sizer = wx.BoxSizer( wx.VERTICAL )
    controls = self._CreateAdditionalUIControls()

    if controls and isinstance( controls, dict ):
      horz_sizer = None
      bottom_control = controls.get( 'bottom' )
      left_control = controls.get( 'left' )
      right_control = controls.get( 'right' )
      top_control = controls.get( 'top' )

      if left_control is not None or right_control is not None:
        horz_sizer = wx.BoxSizer( wx.HORIZONTAL )
        if left_control is not None:
          horz_sizer.Add( left_control, 0, wx.ALL, 1 )
        horz_sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
        if right_control is not None:
          horz_sizer.Add( right_control, 0, wx.ALL, 1 )

      if top_control is not None:
        sizer.Add( top_control, 0, wx.ALL | wx.EXPAND, 1 )

      if horz_sizer is not None:
        sizer.Add( horz_sizer, 1, wx.ALL | wx.EXPAND )
      else:
        sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )

      if bottom_control is not None:
        sizer.Add( bottom_control, 0, wx.ALL | wx.EXPAND, 1 )

    else:
      sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
    #end if-else controls

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )

    self.Bind( wx.EVT_SIZE, self._OnSize )

    self.timer = wx.Timer( self, TIMERID_RESIZE )
    self.Bind( wx.EVT_TIMER, self._OnTimer )
  #end _InitUI


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._IsAssemblyAware()                 -
  #----------------------------------------------------------------------
  def _IsAssemblyAware( self ):
    """Returns true if this widget cares about assembly selections.
Subclasses should override as appropriate.
    Returns:
        bool: True
"""
    return  True
  #end _IsAssemblyAware


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.IsTupleCurrent()                   -
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """Determines if the image tuple represents the current selection.
Must be overridden by subclasses.  Always returns False.
@param  tpl             tuple of state values
@return                 True if it matches the current state, false otherwise
"""
    return  False
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._LoadDataModel()                   -
  #----------------------------------------------------------------------
  def _LoadDataModel( self, reason ):
    """Copies the state and initiates rendering of the first bitmap.
Sets attributes:
  axialValue
  cellRange
  cellRangeStack
  data
  timeValue

Calls _LoadDataModelValues() and _LoadDataModelUI().
"""
    #super( RasterWidget, self )._LoadDataModel()
    if self.dmgr.HasData() and not self.isLoading:
      self._LoadDataModelValues( reason )

#               -- Do here what is not dependent on size
#               --
      self.cellRange = list( self.GetInitialCellRange() )
      del self.cellRangeStack[ : ]

      if (reason & STATE_CHANGE_axialValue) > 0:
        self.axialValue = self.dmgr.\
            GetAxialValue( self.curDataSet, cm = self.state.axialValue.cm )

      if (reason & STATE_CHANGE_timeValue) > 0:
        self.timeValue = self.state.timeValue

      self.stateIndex = self.dmgr.\
          GetTimeValueIndex( self.timeValue, self.curDataSet )

      wx.CallAfter( self._LoadDataModelUI, reason )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._LoadDataModelUI()                 -
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self, reason ):
    """This implementation is a noop and may be implemented by subclasses
to perform any GUI component initialization that depends on self.state
or self.dmgr.
Must be called on the UI thread.
"""
    #x self.Redraw()  # self._OnSize( None )
    pass
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._LoadDataModelValues()             -
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    pass
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.LoadProps()                        -
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict      dict object from which to deserialize properties
"""
    for k in (
        'cellRange', 'cellRangeStack', 'fitMode',
        'showLabels', 'showLegend', 'timeValue'
        ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

# Handled in Widget
#    for k in ( 'axialValue', ):
#      if k in props_dict and hasattr( self, k ):
#        setattr( self, k, AxialValue( props_dict[ k ] ) )

    super( RasterWidget, self ).LoadProps( props_dict )
    wx.CallAfter( self.UpdateState, resized = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnClick()                         -
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """Noop implementation to be provided by subclasses.
"""
    pass
  #end _OnClick


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnDragFinished()                  -
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
This implementation is a noop.
"""
    pass
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnLeftDown()                      -
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
  #     METHOD:         RasterWidget._OnLeftUp()                        -
  #----------------------------------------------------------------------
  def _OnLeftUp( self, ev ):
    """
"""
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

      if cell_info is not None:
        left = min( self.dragStartCell[ 1 ], cell_info[ 1 ] )
        right = max( self.dragStartCell[ 1 ], cell_info[ 1 ] ) + 1
        top = min( self.dragStartCell[ 2 ], cell_info[ 2 ] )
        bottom = max( self.dragStartCell[ 2 ], cell_info[ 2 ] ) + 1

#       self.cellRangeStack.append( self.cellRange )
#       self.cellRange = [ left, top, right, bottom, right - left, bottom - top ]
        new_range = [ left, top, right, bottom, right - left, bottom - top ]
        if new_range != self.cellRange:
          self.cellRangeStack.append( self.cellRange )
          self.cellRange = new_range
          zoom_flag = True
          self._OnDragFinished( *self.cellRange[ 0 : 4 ] )
      #end if assy found
    #end else dragging

    self.dragStartAssembly = None
    self.dragStartPosition = None

    self.overlay.Reset()
    self.Refresh()

    if zoom_flag:
      #self.Redraw()  # self._OnSize( None )
      self.GetTopLevelParent().GetApp().DoBusyEventOp( self.Redraw )
  #end _OnLeftUp


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnMouseMotion()                   -
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

      if rect.width > 5 and rect.height > 5:
        dc = wx.ClientDC( self.bitmapCtrl )
        odc = wx.DCOverlay( self.overlay, dc )
#               MacOS bug doesn't properly copy or restore the saved
#               image, so we don't do this here until the bug is fixed
        #odc.Clear()

        if 'wxMac' in wx.PlatformInfo:
          #dc.SetPen( wx.Pen( wx.BLACK, 2 ) )
          #dc.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          dc.SetPen( wx.ThePenList.FindOrCreatePen(
              wx.BLACK, 2, wx.PENSTYLE_SOLID
              ) )
          dc.SetBrush( wx.TheBrushList.FindOrCreateBrush(
              wx.Colour( 192, 192, 192, 128 ), wx.BRUSHSTYLE_SOLID
              ) )
          dc.DrawRectangle( *rect )
        else:
          odc.Clear()
          ctx = wx.GraphicsContext_Create( dc )
          ctx.SetPen( wx.GREY_PEN )
          #ctx.SetBrush( wx.Brush( wx.Colour( 192, 192, 192, 128 ) ) )
          ctx.SetBrush( wx.TheBrushList.FindOrCreateBrush(
              wx.Colour( 192, 192, 192, 128 ), wx.BRUSHSTYLE_SOLID
              ) )
          ctx.DrawRectangle( *rect )
        del odc
      #end if moved sufficiently
    #end else dragging
  #end _OnMouseMotion


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnSize()                          -
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev is None:
      self.curSize = None
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( '%s: forced resize', self.GetTitle() )
      wx.CallAfter( self.UpdateState, resized = True )

    else:
      ev.Skip()

      wd, ht = self.GetClientSize()
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( '%s: clientSize=%d,%d', self.GetTitle(), wd, ht )

      if wd > 0 and ht > 0:
        if self.curSize is None or \
            wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
          self.curSize = ( wd, ht )
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug( '%s: starting timer', self.GetTitle() )
          self.timer.Start( 500, wx.TIMER_ONE_SHOT )
    #end else ev is not None
  #end _OnSize


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnSize_0()                        -
  #----------------------------------------------------------------------
##   def _OnSize_0( self, ev ):
##     """
## """
##     if ev is None:
##       self.curSize = None
##     else:
##       ev.Skip()
## 
##     wd, ht = self.GetClientSize()
##     if self.logger.isEnabledFor( logging.DEBUG ):
##       self.logger.debug( '%s: clientSize=%d,%d', self.GetTitle(), wd, ht )
## 
##     if wd > 0 and ht > 0:
##       if self.curSize is None or \
##           wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
##         self.curSize = ( wd, ht )
##         if self.logger.isEnabledFor( logging.DEBUG ):
##           self.logger.debug( '%s: calling UpdateState', self.GetTitle() )
##         wx.CallAfter( self.UpdateState, resized = True )
##   #end _OnSize_0


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnSize_1()                        -
  #----------------------------------------------------------------------
##  def _OnSize_1( self, ev ):
##    """
##"""
##    if ev is None:
##      self.curSize = None
##    else:
##      ev.Skip()
##
##    wd, ht = self.GetClientSize()
##    if self.logger.isEnabledFor( logging.DEBUG ):
##      self.logger.debug( '%s: clientSize=%d,%d', self.GetTitle(), wd, ht )
##
##    if wd > 0 and ht > 0:
##      if self.curSize is None or \
##          wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
##        self.curSize = ( wd, ht )
##        if self.logger.isEnabledFor( logging.DEBUG ):
##          self.logger.debug( '%s: calling timer', self.GetTitle() )
##      self.timer.Start( 500, wx.TIMER_ONE_SHOT )
##  #end _OnSize_1


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnTimer()                         -
  #----------------------------------------------------------------------
  def _OnTimer( self, ev ):
    """
"""
    if ev.Timer.Id == TIMERID_RESIZE:
      wd, ht = self.GetClientSize()
      if self.curSize is None or \
          wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( '%s: size has changed', self.GetTitle() )
      else:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( '%s: calling UpdateState resized', self.GetTitle() )
        wx.CallAfter( self.UpdateState, resized = True )
    #end if ev.Timer.Id == TIMERID_RESIZE
  #end _OnTimer


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleFit()                     -
  #----------------------------------------------------------------------
  def _OnToggleFit( self, ev ):
    """Must be called on the UI thread.
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item_id = ev.GetId()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnToggleFitImpl, menu, item_id )
  #end _OnToggleFit


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleFitImpl()                 -
  #----------------------------------------------------------------------
  def _OnToggleFitImpl( self, menu, item_id ):
    """Must be called on the UI thread.
"""
    item = menu.FindItemById( item_id )
    label = item.GetItemLabel()

#               -- Change Label for Toggle Items
#               --
    if label.find( 'Width' ) >= 0:
      item.SetItemLabel( label.replace( 'Width', 'Height' ) )
      self.fitMode = 'wd'
    else:
      item.SetItemLabel( label.replace( 'Height', 'Width' ) )
      self.fitMode = 'ht'

#               -- Change Toggle Labels for Other Menu
#               --
    other_menu = \
        self.GetPopupMenu() \
        if menu == self.container.GetWidgetMenu() else \
        self.container.GetWidgetMenu()
    if other_menu is not None:
      self._UpdateMenuItems(
          other_menu,
          '^Fit .*', 'Fit Height' if self.fitMode == 'wd' else 'Fit Width'
          )

#               -- Redraw
#               --
    self.UpdateState( resized = True )
  #end _OnToggleFitImpl


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleLabels()                  -
  #----------------------------------------------------------------------
  def _OnToggleLabels( self, ev ):
    """Must be called on the UI thread.
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item_id = ev.GetId()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnToggleLabelsImpl, menu, item_id )
  #end _OnToggleLabels


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleLabelsImpl()              -
  #----------------------------------------------------------------------
  def _OnToggleLabelsImpl( self, menu, item_id ):
    """Must be called on the UI thread.
"""
    item = menu.FindItemById( item_id )
    label = item.GetItemLabel()

#               -- Change Label for Toggle Items
#               --
    if label.startswith( 'Show' ):
      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )
      self.showLabels = True
    else:
      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
      self.showLabels = False

#               -- Change Toggle Labels for Other Menu
#               --
    other_menu = \
        self.GetPopupMenu() \
        if menu == self.container.GetWidgetMenu() else \
        self.container.GetWidgetMenu()
    if other_menu is not None:
      self._UpdateVisibilityMenuItems(
          other_menu,
          'Labels', self.showLabels
          )

#               -- Redraw
#               --
    self.UpdateState( resized = True )
  #end _OnToggleLabelsImpl


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleLegend()                  -
  #----------------------------------------------------------------------
  def _OnToggleLegend( self, ev ):
    """Must be called on the UI thread.
"""
    ev.Skip()
    menu = ev.GetEventObject()
    item_id = ev.GetId()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnToggleLegendImpl, menu, item_id )
  #end _OnToggleLegend


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnToggleLegendImpl()              -
  #----------------------------------------------------------------------
  def _OnToggleLegendImpl( self, menu, item_id ):
    """Must be called on the UI thread.
"""
    item = menu.FindItemById( item_id )
    label = item.GetItemLabel()

#               -- Change Label for Toggle Items
#               --
    if label.startswith( 'Show' ):
      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )
      self.showLegend = True
    else:
      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
      self.showLegend = False

#               -- Change Toggle Labels for Other Menu
#               --
    other_menu = \
        self.GetPopupMenu() \
        if menu == self.container.GetWidgetMenu() else \
        self.container.GetWidgetMenu()
    if other_menu is not None:
      self._UpdateVisibilityMenuItems(
          other_menu,
          'Legend', self.showLegend
          )

#               -- Redraw
#               --
    self.UpdateState( resized = True )
  #end _OnToggleLegendImpl


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._OnUnzoom()                        -
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      #self.Redraw()
      self.GetTopLevelParent().GetApp().DoBusyEventOp( self.Redraw )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.SaveProps()                        -
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict      dict object to which to serialize properties
"""
    super( RasterWidget, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in (
#t      'axialValue',
        'cellRange', 'cellRangeStack', 'fitMode',
        'showLabels', 'showLegend', 'timeValue'
        ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._SetBitmap()                       -
  #----------------------------------------------------------------------
  def _SetBitmap( self, bmap ):
    """
"""
    self.bitmapCtrl.SetBitmap( bmap )
    self.bitmapCtrl.Update()
    self.bitmapPanel.Layout()
    self.bitmapPanel.SetupScrolling()
  #end _SetBitmap


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._UpdateDataSetStateValues()        -
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type, clear_zoom_stack = True ):
    """
Performs any additional state value updates after self.curDataSet has
been updated.
    Args:
        ds_type (str): dataset category/type
        clear_zoom_stack (boolean): True to clear in zoom stack
"""
    pass
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget.UpdateState()                      -
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """Called to update the components on a new state property.
Calls _UpdateStateValues().
@param  kwargs          any state change values plus 'resized', 'changed'
"""
    if bool( self ):
      #self._UpdateStateImpl( **kwargs )
      self._BusyDoOp( self._UpdateStateImpl, **kwargs )
  #end UpdateState


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._UpdateStateImpl()                 -
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateImpl( self, **kwargs ):
    """Called to update the components on a new state property.
Calls ``_UpdateStateValues()``.
"""

    if 'scale_mode' in kwargs:
      kwargs[ 'resized' ] = True

    kwargs = self._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

#               -- Create bitmap_args
#               --
    tpl = self._CreateStateTuple()
    cur_size = self.curSize
    if cur_size is None:
      cur_size = tuple( self.GetClientSize() )
    bitmap_args = tpl + cur_size + tuple( self.cellRange )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          '%s: changed=%s, resized=%s, bitmap_args=%s',
          self.GetTitle(), str( changed ), str( resized ), str( bitmap_args )
          )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config is not None:
      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if tpl in self.bitmaps:
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug( '%s: cache hit', self.GetTitle() )
          self._SetBitmap( self._HiliteBitmap( self.bitmaps[ tpl ] ) )
          must_create_image = False

        elif self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug(
              '%s: cache miss, must create image',
              self.GetTitle()
              )

      finally:
        self.bitmapsLock.release()

      if must_create_image:
        self._CreateAndSetBitmap( tpl, bitmap_args )
    #end if

    self._UpdateMenuItems(
        self.container.widgetMenu,
        '^Fit .*', 'Fit Height' if self.fitMode == 'wd' else 'Fit Width'
        )
    self._UpdateMenuItems(
        self.GetPopupMenu(),
        '^Fit .*', 'Fit Height' if self.fitMode == 'wd' else 'Fit Width'
        )
  #end _UpdateStateImpl


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._UpdateStateImpl_old()             -
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateImpl_old( self, **kwargs ):
    """Called to update the components on a new state property.
Calls _UpdateStateValues().
@param  kwargs          any state change values plus 'resized', 'changed'
"""
    self._BusyBegin()

    if 'scale_mode' in kwargs:
      kwargs[ 'resized' ] = True

    kwargs = self._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    end_busy = True

#               -- Create bitmap_args
#               --
    tpl = self._CreateStateTuple()
    #bitmap_args = tpl + self.curSize + tuple( self.cellRange )
    cur_size = self.curSize
    if cur_size is None:
      cur_size = tuple( self.GetClientSize() )
    bitmap_args = tpl + cur_size + tuple( self.cellRange )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          '%s: changed=%s, resized=%s, bitmap_args=%s',
          self.GetTitle(), str( changed ), str( resized ), str( bitmap_args )
          )

    if resized:
      if bitmap_args not in self.bitmapThreads:
        self._ClearBitmaps()
        self._Configure()
      changed = True

    if changed and self.config is not None:
      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if tpl in self.bitmaps:
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug( '%s: cache hit', self.GetTitle() )
          self._SetBitmap( self._HiliteBitmap( self.bitmaps[ tpl ] ) )
          must_create_image = False

        elif bitmap_args in self.bitmapThreads:
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
                '%s: cache miss, already have thread',
                self.GetTitle()
                )
          must_create_image = False

        else:
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
                '%s: cache miss, creating thread, bitmapThreads.keys=%s',
                self.GetTitle(), str( self.bitmapThreads.keys() )
                )
          #xx some day, some how tell other threads to stop
          #xx maybe semaphore for one thread, check in CreateRasterImage()
          self.bitmapThreads[ bitmap_args ] = 1

      finally:
        self.bitmapsLock.release()

      if must_create_image:
        end_busy = False
        if Config.IsLinux():
          self._CreateAndSetBitmap( tpl, bitmap_args )
        else:
          RasterWidget.jobid_ += 1
          if self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
                '%s: starting worker, args=%s, jobid=%d',
                self.GetTitle(), str( bitmap_args ), RasterWidget.jobid_
                )

          th = wxlibdr.startWorker(
              self._BitmapThreadFinish,
              self._BitmapThreadStart,
              wargs = [ tpl, bitmap_args, RasterWidget.jobid_ ],
              jobID = RasterWidget.jobid_
              )
    #end if

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( '%s: exit', self.GetTitle() )

    self._UpdateMenuItems(
        self.container.widgetMenu,
        '^Fit .*', 'Fit Height' if self.fitMode == 'wd' else 'Fit Width'
        )
    self._UpdateMenuItems(
        self.GetPopupMenu(),
        '^Fit .*', 'Fit Height' if self.fitMode == 'wd' else 'Fit Width'
        )

    if end_busy:
      self._BusyEnd()
  #end _UpdateStateImpl_old


  #----------------------------------------------------------------------
  #     METHOD:         RasterWidget._UpdateStateValues()               -
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
In this implementation 'axial_value', (no longer 'state_index'), 'cur_dataset',
'time_dataset', and 'time_value' are handled.  Subclasses should override
and call this first.  If 'cur_dataset' is in kwargs, _UpdateDataSetStateValues()
will be called.
@return                 kwargs with 'changed' and/or 'resized'
"""
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', kwargs.get( 'force_redraw', False ) )

    values_updated = False

#    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
#      changed = True
#      self.axialValue = self.mgr.NormalizeAxialValue( kwargs[ 'axial_value' ] )

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm and \
        self.curDataSet:
      # Note the state tuple will take care of forcing a redraw if images
      # depend on the axial value
      changed = True
      self.axialValue = self.dmgr.\
          GetAxialValue( self.curDataSet, cm = kwargs[ 'axial_value' ].cm )
    #end if 'axial_value'

    if 'data_model_mgr' in kwargs:
      resized = True

#    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
#      #changed = True
#      if self.state.scaleMode == 'state':
#        resized = True
#      else:
#        changed = True
#      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if 'time_dataset' in kwargs:
      resized = True

#    if 'time_value' in kwargs and kwargs[ 'time_value' ] != self.timeValue and \
#        self.curDataSet:
    if 'time_value' in kwargs and kwargs[ 'time_value' ] != self.timeValue:
      self.timeValue = kwargs[ 'time_value' ]
      #state_index = max( 0, self.dmgr.GetTimeValueIndex( self.timeValue ) )
      state_index = \
          max( 0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet ) )
      if state_index != self.stateIndex:
        if self.state.scaleMode == 'state':
          resized = True
        else:
          changed = True
        self.stateIndex = state_index
      #end if state_index
    #end if 'time_value'

#               -- Special handling for cur_dataset
    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        values_updated = \
        resized = True
        self.curDataSet = kwargs[ 'cur_dataset' ]
        self._UpdateDataSetStateValues( ds_type )
        self.container.GetDataSetMenu().Reset()
        wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

        if 'dataset_added' in kwargs:
          del kwargs[ 'dataset_added' ]

        self.axialValue = self.dmgr.\
            GetAxialValue( self.curDataSet, cm = self.axialValue.cm )
        self.stateIndex = \
          max( 0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet ) )

    if 'dataset_added' in kwargs:
      wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

    if changed:
      kwargs[ 'changed' ] = True

    if resized:
      kwargs[ 'resized' ] = True
      if not values_updated:
        ds_type = self.dmgr.GetDataSetType( self.curDataSet )
        if ds_type and ds_type in self.GetDataSetTypes():
          self._UpdateDataSetStateValues( ds_type, False )

    return  kwargs
  #end _UpdateStateValues

#end RasterWidget
