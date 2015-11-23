#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		raster_widget.py				-
#	HISTORY:							-
#		2015-11-18	leerw@ornl.gov				-
# 	  Added GetData().
#		2015-08-20	leerw@ornl.gov				-
#	  Added workaround for MacOS DCOverlay bug in _OnMouseMotion().
#		2015-06-17	leerw@ornl.gov				-
#	  Generalization of the 2D raster view widgets.
#------------------------------------------------------------------------
import math, os, sys, threading, time, traceback
import numpy as np
#import pdb  #pdb.set_trace()

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

Properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    #x self.assemblyIndex = ( -1, -1, -1 )
    self.axialValue = ( 0.0, -1, -1 )
    self.bitmaps = {}  # key is (row,col)
    self.bitmapsLock = threading.RLock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.config = None
    self.curSize = None
    self.data = None
    self.dragStartCell = None
    self.dragStartPosition = None

    self.menuDef = \
      [
	( 'Hide Labels', self._OnToggleLabels ),
	( 'Hide Legend', self._OnToggleLegend ),
        ( 'Unzoom', self._OnUnzoom )
      ]
    #x self.pinColRow = None
    self.showLabels = True
    self.showLegend = True
    self.stateIndex = -1

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

    super( RasterWidget, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadFinish()		-
  #----------------------------------------------------------------------
  def _BitmapThreadFinish( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
"""
    if result == None:
      cur_tuple = pil_im = None
    else:
      cur_tuple, pil_im = result.get()
    print >> sys.stderr, \
        '[RasterWidget._BitmapThreadFinish] cur_tuple=%s, pil_im=%s' % \
	( str( cur_tuple ), pil_im != None )

    if cur_tuple != None:
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
	  self.bitmaps[ cur_tuple ] = bmap
	finally:
	  self.bitmapsLock.release()
      #end else pil_im not None

#      if cur_pair[ 0 ] == self.stateIndex and cur_pair[ 1 ] == self.axialValue[ 1 ]:
      if self.IsTupleCurrent( cur_tuple ):
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
    #end if cur_pair != None:

    self._BusyEnd()
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._BitmapThreadStart()		-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, next_tuple ):
    """Background thread task to create the wx.Bitmap for the next
tuple in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateRasterImage().
@return			( next_tuple, PIL_image )
"""
    pil_im = None

    if next_tuple != None and self.config != None:
      pil_im = self._CreateRasterImage( next_tuple )

    return  ( next_tuple, pil_im )
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
	if keep_tuple == None or keep_tuple != t:
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
    if wd > 0 and ht > 0 and self.data != None and \
        self.data.HasData() and self.cellRange != None:
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

    if bmap != None:
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
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
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

    config = \
      {
      'fontSize': font_size,
      'labelFont': label_font,
      'labelSize': label_size,
      'legendPilImage': legend_pil_im,
      'legendSize': legend_size,
      'pilFont': pil_font
      }
    if 'size' in kwargs:
      config[ 'clientSize' ] = kwargs[ 'size' ]

    return  config
  #end _CreateBaseDrawConfig


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
  #     METHOD:         RasterWidget.CreatePopupMenu()			-
  #----------------------------------------------------------------------
  def CreatePopupMenu( self ):
    """Lazily creates.  Must be called from the UI thread.
"""
    if self.popupMenu == None:
      self.popupMenu = wx.Menu()

      #for label, handler in self.menuDef:
      for label, handler in self.GetMenuDef( None ):
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
  #	METHOD:		RasterWidget.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
#    wx_im = None

    config = self._CreateDrawConfig( scale = self.GetPrintScale() )
    pil_im = self._CreateRasterImage( self._CreateStateTuple() )
#    wx_im = wx.EmptyImage( *pil_im.size )

#    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
#    wx_im.SetData( pil_im_data_str )

#    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
#    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )
#    #return  wx_im

#    wx_im.SaveFile( file_path, wx.BITMAP_TYPE_PNG )
    if pil_im != None:
      pil_im.save( file_path, 'PNG' )
    return  file_path
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
The config and data attributes are good to go.
This implementation returns None and must be overridden by subclasses.
@param  tuple_in	state tuple
@return			PIL image
"""
    return  None
  #end _CreateRasterImage


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
  #	METHOD:		RasterWidget._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.  This implementation returns a blank string.
@param  cell_info	tuple returned from FindCell()
"""
    return  ''
  #end _CreateToolTipText


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
        self.data.ExtractSymmetryExtent() if self.data != None else \
	( 0, 0, 0, 0, 0, 0 )
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
    return  self.menuDef
  #end GetMenuDef


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
    #self.CreatePopupMenu()

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
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[RasterWidget._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      self.cellRange = list( self.GetInitialCellRange() )
      del self.cellRangeStack[ : ]

      self.axialValue = self.state.axialValue
      self.stateIndex = self.state.stateIndex
      self._LoadDataModelValues()

      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModelUI()			-
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self ):
    """This implementation calls _OnSize( None ).
Must be called on the UI thread.
"""
#    self.axialBean.SetRange( 1, self.data.core.nax )
#    self.axialBean.axialLevel = 0
#    self.exposureBean.SetRange( 1, len( self.data.states ) )
#    self.exposureBean.stateIndex = 0
    self._OnSize( None )
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
  #	METHOD:		RasterWidget._OnClick()				-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """Noop implementation to be provided by subclasses.
"""
    pass
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnContextMenu()			-
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
    if cell_info != None:
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
    if self.dragStartPosition != None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    #elif self.dragStartPosition == ev.GetPosition():
    if rect == None or rect.width <= 5 or rect.height <= 5:
      self._OnClick( ev )

    else:
      x = ev.GetX()
      y = ev.GetY()
      cell_info = self.FindCell( x, y )

      if cell_info != None:
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
      self._OnSize( None )
  #end _OnLeftUp


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnMouseMotion()			-
  #----------------------------------------------------------------------
  def _OnMouseMotion( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition == None:
      tip_str = ''
      cell_info = self.FindCell( *ev.GetPosition() )

      #if assy != None and assy[ 0 ] >= 0:
      if cell_info != None:
        tip_str = self._CreateToolTipText( cell_info )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      #print >> sys.stderr, '[RasterWidget._OnMouseMotion]', str( rect )

      if rect.width > 5 and rect.height > 5:
        dc = wx.ClientDC( self.bitmapCtrl )
        odc = wx.DCOverlay( self.overlay, dc )
#		MacOS bug doesn't properly copy or restore the saved
#		image, so we don't this hear until the bug is fixed
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
    if ev == None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[RasterWidget._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None and \
        (self.curSize == None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
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
      self._OnSize( None )
  #end _OnUnzoom


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

    kwargs = self._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      tpl = self._CreateStateTuple()

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if tpl in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self._HiliteBitmap( self.bitmaps[ tpl ] ) )
	  must_create_image = False
      finally:
        self.bitmapsLock.release()

      if must_create_image:
        print >> sys.stderr, \
	    '[RasterWidget.UpdateState] starting worker, tpl=%s' % \
	    str( tpl )
        wxlibdr.startWorker(
	    self._BitmapThreadFinish,
	    self._BitmapThreadStart,
	    wargs = [ tpl ]
	    )
      else:
        self._BusyEnd()
    #end if
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
