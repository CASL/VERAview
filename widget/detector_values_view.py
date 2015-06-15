#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_values_view.py				-
#	HISTORY:							-
#		2015-04-27	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, threading, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  #from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from bean.axial_slider import *
from bean.exposure_slider import *
from data.utils import DataUtils
from event.state import *
from legend import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		DetectorValues2DView				-
#------------------------------------------------------------------------
class DetectorValues2DView( Widget ):
  """NOT USED.
Pin-by-pin assembly view across axials and exposure times or states.

Attrs/properties:
  bitmaps		ready-to-draw bitmaps[ ( state, axial, assy ) ]
  data			data.DataModel
  detectorIndex		0-based index of selected detector
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.axialLevel = -1
    self.bitmaps = {}  # key is ( state_ndx, axial_level, assy_ndx )
    self.bitmapsLock = threading.RLock()
    #self.bitmapsLock = threading.Lock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.config = None
    self.curSize = None
    self.data = None
    #self.dataSetName = kwargs.get( 'dataset', 'detector_response' )
    self.dataSetName = 'detector_response'
    self.detectorIndex = ( -1, -1, -1 )
    self.dragStartDetector = None
    self.dragStartPosition = None

    self.menuDefs = [ ( 'Unzoom', self._OnUnzoom ) ]
    self.stateIndex = -1

    self.bitmapCtrl = None
    self.bitmapPanel = None
    self.blankBitmap = self.GetBitmap( 'loading' )
    self.menu = None
    self.overlay = None

    self.pilFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Black.ttf' )
#        os.path.join( Config.GetRootDir(), 'res/Times New Roman Bold.ttf' )
    self.valueFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' )

    super( DetectorValues2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._BitmapThreadFinish()	-
  #----------------------------------------------------------------------
  def _BitmapThreadFinish( self, result ):
    """Background thread completion method called in the UI thread.
Paired to _BitmapThreadStart().
Calls _UpdateCoreImage() and launches the next axial background task
if not finished.
"""
    if result == None:
      cur_tuple = pil_im = None
    else:
      cur_tuple, pil_im = result.get()
    print >> sys.stderr, \
        '[DetectorValues2DView._BitmapThreadFinish] cur=%s, pil_im=%s' % \
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

      if cur_tuple[ 0 ] == self.stateIndex and \
          cur_tuple[ 1 ] == self.axialLevel:
        self.bitmapCtrl.SetBitmap( bmap )
    #end if cur_pair != None:

    self._BusyEnd()
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._BitmapThreadStart()	-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, cur_tuple ):
    """Background thread task to create the wx.Bitmap for the next
pair in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateCoreImage().
"""
    print >> sys.stderr, \
        '[DetectorValues2DView._BitmapThreadStart] cur_tuple=%s' % str( cur_tuple )
    pil_im = None

    if cur_tuple != None:
      pil_im = self._CreateCoreImage(
          self.config, self.data, self.dataSetName, cur_tuple
	  )

    return  ( cur_tuple, pil_im )
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._ClearBitmaps()		-
  # Must be called from the UI thread.
  # @param  keep_tuple	0-based ( state_ndx, axial_level ) to keep,
  #			or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_tuple = None ):
    """
@param  keep_tuple	0-based ( state_ndx, axial_level ) to keep,
			or None
"""
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
  #	METHOD:		DetectorValues2DView._Configure()		-
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    wd, ht = self.bitmapPanel.GetClientSize()
    print >> sys.stderr, '[DetectorValues2DView._Configure] %d,%d' % ( wd, ht )


    self.config = None
    if wd > 0 and ht > 0 and self.data and self.data.HasData() and self.cellRange != None:
      self.config = self._CreateDrawConfig(
          self.data, self.dataSetName, self.cellRange,
	  size = ( wd, ht )
	  )
  #end _Configure


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, config, data, ds_name, tuple_in ):
    """Called in background task to create the PIL image for the state/exposure.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  tuple_in	0-based ( state_index, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    print >> sys.stderr, \
        '[DetectorValues2DView._CreateCoreImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = data.IsValid(
	axial_level = axial_level,
	state_index = state_ndx
	)
    if config != None and tuple_valid:
      im_wd, im_ht = config[ 'clientSize' ]
      core_wd = config[ 'coreWidth' ]
      det_gap = config[ 'detectorGap' ]
      det_wd = config[ 'detectorWidth' ]
      font_size = config[ 'fontSize' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      value_font = config[ 'valueFont' ]

      title_fmt = '%s: Axial %%.3f, Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % ( 99.999, 99.999 ) )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      det_y = 1
#      for pin_row in range( data.core.npin ):
      for det_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        detmap_row = data.core.detectorMap[ det_row, : ]

	det_x = 1
#	for pin_col in range( data.core.npin ):
	for det_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  det_ndx = detmap_row[ det_col ] - 1
	  value = 0.0
	  if det_ndx >= 0 and ds_value != None:
	    value = ds_value[ axial_level, det_ndx ]
	  if value > 0:
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    #im_draw.ellipse
	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = brush_color, outline = pen_color
	        )

	    if value_font != None:
	      #value_str = '%.3g' % value
	      value_str = DataUtils.FormatFloat2( value )
	      value_size = value_font.getsize( value_str )
	      #if value_size[ 0 ] <= pin_wd:
	      if True:
		value_x = det_x + ((det_wd - value_size[ 0 ]) >> 1)
		value_y = det_y + ((det_wd - value_size[ 1 ]) >> 1) 
                im_draw.text(
		    ( value_x, value_y ), value_str,
		    fill = Widget.GetContrastColor( *brush_color ),
		    font = value_font
                    )
	    #end if value_font defined
	  #end if value > 0

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

#			-- Draw Legend Image
#			--
      im.paste( legend_pil_im, ( core_wd + font_size, 0 ) )

#			-- Draw Title String
#			--
      det_y = max( det_y, legend_pil_im.size[ 1 ] )
      det_y += font_size

      title_str = title_fmt % ( \
	  data.core.axialMeshCenters[ axial_level ],
	  data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (core_wd + font_size + legend_pil_im.size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, det_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

    return  im
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, config, data, ds_name, tuple_in ):
    """Called in background task to create the PIL image for the state/exposure.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  tuple_in	0-based ( state_index, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    print >> sys.stderr, \
        '[DetectorValues2DView._CreateCoreImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = data.IsValid(
	axial_level = axial_level,
	state_index = state_ndx
	)
    if config != None and tuple_valid:
      im_wd, im_ht = config[ 'clientSize' ]
      core_wd = config[ 'coreWidth' ]
      det_gap = config[ 'detectorGap' ]
      det_wd = config[ 'detectorWidth' ]
      font_size = config[ 'fontSize' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      value_font = config[ 'valueFont' ]

      title_fmt = '%s: Axial %%.3f, Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % ( 99.999, 99.999 ) )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      det_y = 1
#      for pin_row in range( data.core.npin ):
      for det_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        detmap_row = data.core.detectorMap[ det_row, : ]

	det_x = 1
#	for pin_col in range( data.core.npin ):
	for det_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  det_ndx = detmap_row[ det_col ] - 1
	  value = 0.0
	  if det_ndx >= 0 and ds_value != None:
	    value = ds_value[ axial_level, det_ndx ]
	  if value > 0:
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    #im_draw.ellipse
	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = brush_color, outline = pen_color
	        )

	    if value_font != None:
	      #value_str = '%.3g' % value
	      value_str = DataUtils.FormatFloat2( value )
	      value_size = value_font.getsize( value_str )
	      #if value_size[ 0 ] <= pin_wd:
	      if True:
		value_x = det_x + ((det_wd - value_size[ 0 ]) >> 1)
		value_y = det_y + ((det_wd - value_size[ 1 ]) >> 1) 
                im_draw.text(
		    ( value_x, value_y ), value_str,
		    fill = Widget.GetContrastColor( *brush_color ),
		    font = value_font
                    )
	    #end if value_font defined
	  #end if value > 0

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

#			-- Draw Legend Image
#			--
      im.paste( legend_pil_im, ( core_wd + font_size, 0 ) )

#			-- Draw Title String
#			--
      det_y = max( det_y, legend_pil_im.size[ 1 ] )
      det_y += font_size

      title_str = title_fmt % ( \
	  data.core.axialMeshCenters[ axial_level ],
	  data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (core_wd + font_size + legend_pil_im.size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, det_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

    return  im
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._CreateDrawConfig()	-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, data, ds_name, cell_range, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  data		data model
@param  ds_name		dataset name
@param  cell_range	cell range to display
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    coreHeight
    coreWidth
    detectorGap
    detectorWidth
    fontSize
    legendPilImage
    pilFont
    valueFont
    valueFontSize
"""

    ds_range = data.GetRange( ds_name )

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[DetectorValues2DView._CreateDrawConfig] size=%d,%d' % ( wd, ht )

      font_size = self._CalcFontSize( wd )
      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )

# self.cellRange = None  # left, top, right, bottom, dx, dy
      det_adv_wd = \
          (wd - legend_pil_im.size[ 0 ] - font_size) / cell_range[ -2 ]
      working_ht = max( ht, legend_pil_im.size[ 1 ] )

      det_adv_ht = (working_ht - (font_size << 1)) / cell_range[ - 1 ]
      if det_adv_ht < det_adv_wd:
        det_adv_wd = det_adv_ht

      det_gap = det_adv_wd >> 3
      det_wd = max( 1, det_adv_wd - det_gap )

      core_wd = cell_range[ -2 ] * (det_wd + det_gap)
      core_ht = cell_range[ -1 ] * (det_wd + det_gap)

    else:
      det_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4
      print >> sys.stderr, '[DetectorValues2DView._CreateDrawConfig] det_wd=%d' % det_wd

      det_gap = pin_wd >> 3
      core_wd = cell_range[ -2 ] * (det_wd + det_gap)
      core_ht = cell_range[ -1 ] * (det_wd + det_gap)

      font_size = self._CalcFontSize( 1024 )
      legend_pil_im = self._CreateLegendPilImage( ds_range, font_size )

      wd = core_wd + (font_size << 1) + legend_pil_im.size[ 0 ]
      ht = max( core_wd, legend_pil_im.size[ 1 ] )
      ht += (font_size << 1) + font_size
    #end if-else

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    value_font_size = det_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    print >> sys.stderr, \
        '[DetectorValues2DView._CreateDrawConfig]\n  font_size=%d, legend_pil_im.size=%s, det_wd=%d, det_gap=%d, wd=%d, ht=%d\n  value_font_size=%d, value_font-None=%d' % \
        ( font_size, str( legend_pil_im.size ), det_wd, det_gap, wd, ht, \
	  value_font_size, value_font == None )

    config = \
      {
      'clientSize': ( wd, ht ),
      'coreHeight': core_ht,
      'coreWidth': core_wd,
      'detectorGap': det_gap,
      'detectorWidth': det_wd,
      'fontSize': font_size,
      'legendPilImage': legend_pil_im,
      'lineWidth': max( 1, det_gap ),
      'pilFont': pil_font,
      'valueFont': value_font,
      'valueFontSize': value_font_size
      }

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         DetectorValues2DView.CreateMenu()		-
  #----------------------------------------------------------------------
  def CreateMenu( self ):
    if self.menu == None:
      self.menu = wx.Menu()

      for label, handler in self.menuDefs:
        item = wx.MenuItem( self.menu, wx.ID_ANY, label )
        self.Bind( wx.EVT_MENU, handler, item )
        self.menu.AppendItem( item )
      #end for
    #end if

    return  self.menu
  #end CreateMenu


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.CreatePrintImage()		-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    wx_im = None

    config = self._CreateDrawConfig(
        self.data, self.dataSetName, self.cellRange, scale = 28
	)
    pil_im = self._CreateCoreImage(
        config, self.data, self.dataSetName,
	( self.stateIndex, self.axialLevel )
	)
    wx_im = wx.EmptyImage( *pil_im.size )

    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
    wx_im.SetData( pil_im_data_str )

    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

    return  wx_im
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.FindDetector()		-
  #----------------------------------------------------------------------
  def FindDetector( self, ev_x, ev_y ):
    """Finds the pin index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row )
"""
    result = None

    if self.config != None and self.data != None:
      if ev_x >= 0 and ev_y >= 0:
        det_size = self.config[ 'detectorWidth' ] + self.config[ 'detectorGap' ]
        cell_x = min(
	    int( ev_x / det_size ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        cell_y = min(
	    int( ev_y / det_size ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	det_ndx = self.data.core.detectorMap[ cell_y, cell_x ] - 1
	result = ( det_ndx, cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindDetector


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetAxialLevel()		-
  #----------------------------------------------------------------------
  def GetAxialLevel( self ):
    """@return		0-based axial level
"""
    return  self.axialLevel
  #end GetAxialLevel


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetDataSetType()		-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_axialLevel,
	STATE_CHANGE_detectorDataSet,
	STATE_CHANGE_stateIndex,
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetMenuDef()		-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
    return  self.menuDefs
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetStateIndex()		-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detectors 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.HandleStateChange()	-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    print >> sys.stderr, \
        '[DetectorValues2DView.HandleStateChange] reason=%d' % reason
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[DetectorValues2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      state_args = {}

      if (reason & STATE_CHANGE_axialLevel) > 0:
        if self.state.axialLevel != self.axialLevel:
	  state_args[ 'axial_level' ] = self.state.axialLevel

      if (reason & STATE_CHANGE_detectorDataSet) > 0:
        if self.state.detectorDataSet != self.dataSetName:
	  state_args[ 'detector_dataset' ] = self.state.detectorDataSet

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  state_args[ 'state_index' ] = self.state.stateIndex

      if len( state_args ) > 0:
        wx.CallAfter( self._UpdateState, **state_args )
    #end else not STATE_CHANGE_init
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    self.overlay = wx.Overlay()

#		-- Bitmap panel
#		--
    self.bitmapPanel = wx.Panel( self )
    self.bitmapCtrl = wx.StaticBitmap( self.bitmapPanel, bitmap = self.blankBitmap )
    self.bitmapCtrl.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnDragStart )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnDragEnd )
    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnDragMove )
#    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnMouseUp )
#    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotion )

#		-- Lay out
#		--
#    inside_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    inside_sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
#    inside_sizer.Add( self.axialBean, 0, wx.ALL | wx.EXPAND, 1 )
#    inside_panel.SetSizer( inside_sizer )

    sizer = wx.BoxSizer( wx.VERTICAL )
#    sizer.Add( inside_panel, 1, wx.ALL | wx.EXPAND )
    sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
#    sizer.Add( self.exposureBean, 0, wx.ALL | wx.EXPAND, 2 )

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._LoadDataModel()		-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.  Sets properties: data
"""
    print >> sys.stderr, '[DetectorValues2DView._LoadDataModel]'
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[DetectorValues2DView._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      assy_extent = self.data.ExtractSymmetryExtent()
      self.cellRange = list( assy_extent )
      del self.cellRangeStack[ : ]

      self.axialLevel = self.state.axialLevel
      self.detectorIndex = 0
      self.stateIndex = self.state.stateIndex
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._LoadDataModelUI()		-
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self ):
    """Must be called on the UI thread.
"""
    print >> sys.stderr, \
        '[DetectorValues2DView._LoadDataModelUI] state: stateIndex=%d, axialLevel=%d' % \
	( self.state.stateIndex, self.state.axialLevel )
#    self.axialBean.SetRange( 1, self.data.core.nax )
#    self.axialBean.axialLevel = 0
#    self.exposureBean.SetRange( 1, len( self.data.states ) )
#    self.exposureBean.stateIndex = 0
    self._OnSize( None )
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnContextMenu()		-
  #----------------------------------------------------------------------
  def _OnContextMenu( self, ev ):
    """
"""
    pos = ev.GetPosition()
    pos = self.bitmapCtrl.ScreenToClient( pos )

    menu = self.CreateMenu()
    self.bitmapCtrl.PopupMenu( menu, pos )
  #end _OnContextMenu


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnDragEnd()		-
  #----------------------------------------------------------------------
  def _OnDragEnd( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[DetectorValues2DView._OnDragEnd] enter'
    zoom_flag = False

    if self.HasCapture():
      self.ReleaseMouse()

    rect = None
    if self.dragStartPosition != None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    if rect == None or rect.width <= 5 or rect.height <= 5:
      pass
      #self._OnClick( ev )

    else:
      det = self.FindDetector( *ev.GetPosition() )
      if det != None:
        left = min( self.dragStartDetector[ 1 ], det[ 1 ] )
        right = max( self.dragStartDetector[ 1 ], det[ 1 ] ) + 1
	top = min( self.dragStartDetector[ 2 ], det[ 2 ] )
	bottom = max( self.dragStartDetector[ 2 ], det[ 2 ] ) + 1

	self.cellRangeStack.append( self.cellRange )
	self.cellRange = [ left, top, right, bottom, right - left, bottom - top ]
	zoom_flag = True
      #end if pin found
    #end else dragging

    self.dragStartDetector = None
    self.dragStartPosition = None

    self.overlay.Reset()
    self.Refresh()

    if zoom_flag:
      self._OnSize( None )
  #end _OnDragEnd


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnDragMove()		-
  #----------------------------------------------------------------------
  def _OnDragMove( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition == None:
      tip_str = ''
      det = self.FindDetector( *ev.GetPosition() )
      valid = self.data.IsValid(
	  axial_level = self.axialLevel,
	  detector_index = det[ 0 ],
	  state_index = self.stateIndex
	  )

      if valid:
        ds = self.data.states[ self.stateIndex ].group[ self.dataSetName ]
        ds_value = ds[ self.axialLevel, det[ 0 ] ]

        if ds_value > 0.0:
	  show_det_addr = ( det[ 1 ] + 1, det[ 0 ] + 1 )
	  tip_str = \
	      'Detector: %d %s\n%s: %g' % \
	      ( det[ 0 ] + 1, str( show_det_addr ), self.dataSetName, ds_value )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      print >> sys.stderr, '[DetectorValues2DView._OnDragMove]', str( rect )

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
  #end _OnDragMove


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnDragStart()		-
  #----------------------------------------------------------------------
  def _OnDragStart( self, ev ):
    """
"""
    self.bitmapCtrl.SetToolTipString( '' )
    det = self.FindDetector( *ev.GetPosition() )
    if det != None and det[ 0 ] >= 0:
      self.dragStartDetector = det
      self.dragStartPosition = ev.GetPosition()
  #end _OnDragStart


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnSize()			-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev == None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[DetectorValues2DView._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None and \
        (self.curSize == None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
      self._BusyBegin()
      self.curSize = ( wd, ht )
      #wx.CallAfter( self._Configure )
      wx.CallAfter( self._UpdateState, resized = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._OnUnzoom()		-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView.SetDataSet()		-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.dataSetName:
#      self.dataSetName = ds_name
#      wx.CallAfter( self._OnSize, None )
      wx.CallAfter( self._UpdateState, detector_dataset = ds_name )
      self.FireStateChange( detector_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DetectorValues2DView._UpdateState()		-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateState( self, **kwargs ):
    """Called to update the components when a new exposure is selected.  It
is assumed all the exposure images have been built.
Must be called from the UI thread.
@param  kwargs		'resized', 'changed'
"""
    self._BusyBegin()
    changed = kwargs[ 'changed' ] if 'changed' in kwargs  else False
    resized = kwargs[ 'resized' ] if 'resized' in kwargs  else False

    if 'axial_level' in kwargs and kwargs[ 'axial_level' ] != self.axialLevel:
      changed = True
      self.axialLevel = self.data.NormalizeAxialLevel( kwargs[ 'axial_level' ] )
#      self.axialBean.axialLevel = \
#          max( 0, min( axial_level, self.data.core.nax - 1 ) )

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.dataSetName:
      resized = True
      self.dataSetName = kwargs[ 'detector_dataset' ]

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      t = ( self.stateIndex, self.axialLevel )

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if t in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self.bitmaps[ t ] )
	  must_create_image = False
      finally:
        self.bitmapsLock.release()

      if must_create_image:
        wxlibdr.startWorker(
	    self._BitmapThreadFinish,
	    self._BitmapThreadStart,
	    wargs = [ t ]
	    )
      else:
        self._BusyEnd()
    #end if
  #end _UpdateState

#end DetectorValues2DView
