#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		raster_widget.py				-
#	HISTORY:							-
#		2015-06-17	leerw@ornl.gov				-
#	  Generalization of the 2D raster view widgets.
#------------------------------------------------------------------------
import math, os, sys, threading, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

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
    self.assemblyExtent = None  # left, top, right, bottom, dx, dy
    self.assemblyIndex = ( -1, -1, -1 )
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

    self.menuDefs = \
      [
	( 'Hide Labels', self._OnToggleLabels ),
	( 'Hide Legend', self._OnToggleLegend ),
        ( 'Unzoom', self._OnUnzoom )
      ]
    self.pinColRow = None
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
  #	METHOD:		RasterWidget._CreateBaseDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateBaseDrawConfig( self, ds_range, **kwargs ):
    """Creates common config values needed by most rasters.  Should be
called from subclass _CreateDrawConfig() methods.
@param  ds_range	current dataset value range
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize      (if size specified)
    fontSize
    labelFont
    legendPilImage
    pilFont
"""

    ds_range = data.GetRange( ds_name )

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[RasterWidget._CreateBaseDrawConfig] size=%d,%d' % ( wd, ht )

      font_size = self._CalcFontSize( wd )
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

    else:
      scale = kwargs.get( 'scale', 8 )
      print >> sys.stderr, \
          '[RasterWidget._CreateBaseDrawConfig] scale=%d' % scale

      font_size = self._CalcFontSize( 512 )
      if self.showLegend:
        legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )
	legend_size = legend_pil_im.size
      else:
        legend_pil_im = None
	legend_size = ( 0, 0 )

      label_font = PIL.ImageFont.truetype( self.valueFontPath, font_size )
      label_size = \
          label_font.getsize( '99' ) \
	  if self.showPinLabels else \
	  ( 0, 0 )
    #end if-else

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    config = \
      {
      'fontSize': font_size,
      'labelFont': label_font,
      'legendPilImage': legend_pil_im,
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
  #	METHOD:		RasterWidget.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    wx_im = None

    config = self._CreateDrawConfig( self.GetPrintScale() )
    pil_im = self._CreateRasterImage( self._CreateStateTuple() )
    wx_im = wx.EmptyImage( *pil_im.size )

    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
    wx_im.SetData( pil_im_data_str )

    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

    return  wx_im
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
The config and data attributes are good to go.
This implementation returns None and must be overridden by subclasses.
@param  tuple_in	state tuple
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
  #	METHOD:		RasterWidget.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row, pin_col, pin_row )
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

	pin_wd = self.config[ 'pinWidth' ]
	pin_col = int( (off_x % assy_advance) / pin_wd )
	if pin_col >= self.data.core.npin: pin_col = -1
	pin_row = int( (off_y % assy_advance) / pin_wd )
	if pin_row >= self.data.core.npin: pin_row = -1

	result = ( assy_ndx, cell_x, cell_y, pin_col, pin_row )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.FindPin()				-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    if self.config != None and self.data != None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
        cell_x = min(
	    int( (ev_x - assy_region[ 0 ]) / pin_size ),
	    self.data.core.npin - 1
	    )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / pin_size ),
	    self.data.core.npin - 1
	    )

	result = ( cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindPin


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
#    return  Core2DView.MENU_DEFS
    return  self.menuDefs
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
  #	METHOD:		RasterWidget.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.HandleMenuItem()			-
  #----------------------------------------------------------------------
#  def HandleMenuItem( self, id ):
#    """
#"""
#    if id == RasterWidget.MENU_ID_unzoom:
#      self._OnUnzoom( None )
#  #end HandleMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget.HandleStateChange_()		-
  #----------------------------------------------------------------------
  def HandleStateChange_( self, reason ):
    print >> sys.stderr, \
        '[RasterWidget.HandleStateChange] reason=%d' % reason
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[RasterWidget.HandleStateChange] calling _LoadDataModel()'
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

      if (reason & STATE_CHANGE_pinColRow) > 0:
        if self.state.pinColRow != self.pinColRow:
	  state_args[ 'pin_colrow' ] = self.state.pinColRow
#	  wx.CallAfter( self._UpdateState, pin_colrow = self.state.pinColRow )

      if (reason & STATE_CHANGE_pinDataSet) > 0:
        if self.state.pinDataSet != self.pinDataSet:
	  state_args[ 'pin_dataset' ] = self.state.pinDataSet

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  state_args[ 'state_index' ] = self.state.stateIndex
#          wx.CallAfter( self._UpdateState, state_index = self.state.stateIndex )

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        state_args[ 'resized' ] = True

      if len( state_args ) > 0:
        wx.CallAfter( self._UpdateState, **state_args )
    #end else not a data model load
  #end HandleStateChange_


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config != None:
      line_wd = -1
      rect = None

#			-- Core mode
#			--
      if self.config[ 'mode' ] == 'core':
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
	if self.pinColRow[ 0 ] >= 0 and self.pinColRow[ 1 ] >= 0 and \
	    self.pinColRow[ 0 ] < self.data.core.npin and \
	    self.pinColRow[ 1 ] < self.data.core.npin:
          assy_region = self.config[ 'assemblyRegion' ]
	  pin_gap = self.config[ 'pinGap' ]
	  pin_wd = self.config[ 'pinWidth' ]
	  pin_adv = pin_wd + pin_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.pinColRow[ 0 ] * pin_adv + assy_region[ 0 ],
	      self.pinColRow[ 1 ] * pin_adv + assy_region[ 1 ],
	      pin_adv, pin_adv
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
  #	METHOD:		RasterWidget._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    self.overlay = wx.Overlay()
#    inside_panel = wx.Panel( self )

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
  #	METHOD:		RasterWidget.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """Must be overridden by subclasses.  Always returns False.
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    return  False
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.  Sets properties: assemblyExtent, cellRange, data
"""
    print >> sys.stderr, '[RasterWidget._LoadDataModel]'
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[RasterWidget._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      self.assemblyExtent = self.data.ExtractSymmetryExtent()
      self.avgValues.clear()
      self.cellRange = list( self.assemblyExtent )
      del self.cellRangeStack[ : ]

      self.assemblyIndex = self.state.assemblyIndex
      self.axialValue = self.state.axialValue
      self.pinDataSet = self.state.pinDataSet
      self.pinColRow = self.state.pinColRow
      self.stateIndex = self.state.stateIndex
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._LoadDataModelUI()			-
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
  #	METHOD:		RasterWidget._OnClick()				-
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
        #self.assemblyIndex = assy_ndx
        #self.FireStateChange( assembly_index = assy_ndx )
	state_args[ 'assembly_index' ] = assy_ndx

      pin_addr = cell_info[ 3 : 5 ]
      if pin_addr != self.pinColRow:
        #self.FireStateChange( pin_colrow = pin_addr )
	state_args[ 'pin_colrow' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
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
  #	METHOD:		RasterWidget._OnDragEndCore()			-
  #----------------------------------------------------------------------
  def _OnDragEndCore( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[RasterWidget._OnDragEndCore] enter'
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
  #	METHOD:		RasterWidget._OnDragMoveCore()			-
  #----------------------------------------------------------------------
  def _OnDragMoveCore( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition == None:
      tip_str = ''
      assy = self.FindAssembly( *ev.GetPosition() )

#      if assy == None or assy[ 0 ] < 0:
#        tip_str = ''

      if assy != None and assy[ 0 ] >= 0:
	if self.stateIndex in self.avgValues:
	  avg_value = self.avgValues[ self.stateIndex ][ self.axialValue[ 1 ], assy[ 0 ] ]
	else:
	  avg_value = 0.0

	show_assy_addr = self.data.core.CreateAssyLabel( *assy[ 1 : 3 ] )
	tip_str = 'Assy: %d %s\n%s %s: %.3g' % \
	    ( assy[ 0 ] + 1, show_assy_addr,
	      'Avg' if self.data.core.pinVolumesSum > 0.0 else 'Mean',
	      self.pinDataSet, avg_value )
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
      print >> sys.stderr, '[RasterWidget._OnDragMoveCore]', str( rect )

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
  #	METHOD:		RasterWidget._OnDragStartCore()			-
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
  #	METHOD:		RasterWidget._OnMouseMotionAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None:
      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	pin_value = ds_value[
	    pin_addr[ 0 ], pin_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if pin_value > 0:
	pin_rc = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
        tip_str = 'Pin: %s\n%s: %g' % ( str( pin_rc ), ds_name, pin_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None and pin_addr != self.pinColRow:
#      print >> sys.stderr, \
#          '[Assembly2DView._OnMouseUp] new pinColRow=%s' % str( pin_addr )

      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	pin_value = ds_value[
	    pin_addr[ 0 ], pin_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if pin_value > 0.0:
	self.FireStateChange( pin_colrow = pin_addr )
    #end if pin_addr changed
  #end _OnMouseUpAssy


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
      wx.CallAfter( self._UpdateState, resized = True )
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
    self._UpdateState( resized = True )
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
    self._UpdateState( resized = True )
  #end _OnToggleLegend


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._OnUnzoom()			-
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
  #	METHOD:		RasterWidget.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.pinDataSet:
#      self.avgValues.clear()
#      self.pinDataSet = ds_name
#      wx.CallAfter( self._OnSize, None )
      wx.CallAfter( self._UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		RasterWidget._SetMode()				-
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
  #	METHOD:		RasterWidget._UpdateState()			-
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

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      resized = True
      self.pinDataSet = kwargs[ 'pin_dataset' ]
      self.avgValues.clear()

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if 'time_dataset' in kwargs:
      resized = True

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      self._CalcAvgValues( self.data, self.stateIndex )
      pair = ( self.stateIndex, self.axialValue[ 1 ] )
#      pair = ( self.stateIndex, self.axialLevel )

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if pair in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self._HiliteBitmap( self.bitmaps[ pair ] ) )
	  must_create_image = False
      finally:
        self.bitmapsLock.release()

      if must_create_image:
        print >> sys.stderr, '[RasterWidget._UpdateState] starting worker'
        wxlibdr.startWorker(
	    self._BitmapThreadFinish,
	    self._BitmapThreadStart,
	    wargs = [ pair ]
	    )
      else:
        self._BusyEnd()
    #end if
    print >> sys.stderr, '[RasterWidget._UpdateState] exit'
  #end _UpdateState

#end RasterWidget
