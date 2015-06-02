#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_view.py				-
#	HISTORY:							-
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-21	leerw@ornl.gov				-
#	  Coloring boundary by value at current axial.
#		2015-05-01	leerw@ornl.gov				-
#	  Using data.core.detectorAxialMesh, detector and detector_operable.
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
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.utils import DataUtils
from event.state import *
from legend import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Detector2DView					-
#------------------------------------------------------------------------
class Detector2DView( Widget ):
  """Pin-by-pin assembly view across detector axials and state points.

Attrs/properties:
  bitmaps		ready-to-draw bitmaps[ ( state, ) ]
  data			data.DataModel
  detectorIndex		0-based index of selected detector, col, row
  stateIndex		0-based index of state point
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.axialValue = ( 0.0, -1, -1 )
    self.bitmaps = {}  # key is ( state_ndx, )
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

    self.menuDefs = \
      [
	( 'Hide Labels', self._OnToggleLabels ),
	( 'Hide Legend', self._OnToggleLegend ),
        ( 'Unzoom', self._OnUnzoom )
      ]
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

    super( Detector2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._BitmapThreadFinish()		-
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
        '[Detector2DView._BitmapThreadFinish] cur=%s, pil_im=%s' % \
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

      if cur_tuple[ 0 ] == self.stateIndex:
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
    #end if cur_pair != None:

    self._BusyEnd()
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._BitmapThreadStart()		-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, cur_tuple ):
    """Background thread task to create the wx.Bitmap for the next
pair in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateCoreImage().
"""
    print >> sys.stderr, \
        '[Detector2DView._BitmapThreadStart] cur_tuple=%s' % str( cur_tuple )
    pil_im = None

    if cur_tuple != None:
      pil_im = self._CreateCoreImage(
          self.config, self.data, self.dataSetName, cur_tuple
	  )

    return  ( cur_tuple, pil_im )
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._ClearBitmaps()			-
  # Must be called from the UI thread.
  # @param  keep_tuple	0-based ( state_ndx, ) to keep,
  #			or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_tuple = None ):
    """
@param  keep_tuple	0-based ( state_ndx, ) to keep,
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
  #	METHOD:		Detector2DView._Configure()			-
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    wd, ht = self.bitmapPanel.GetClientSize()
    print >> sys.stderr, '[Detector2DView._Configure] %d,%d' % ( wd, ht )


    self.config = None
    if wd > 0 and ht > 0 and self.data and self.data.HasData() and self.cellRange != None:
      self.config = self._CreateDrawConfig(
          self.data, self.dataSetName, self.cellRange,
	  size = ( wd, ht )
	  )
  #end _Configure


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, config, data, ds_name, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  tuple_in	0-based ( state_index )
"""
    state_ndx = tuple_in[ 0 ]
    print >> sys.stderr, \
        '[Detector2DView._CreateCoreImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = data.IsValid( state_index = state_ndx )
    if config != None and tuple_valid and \
	data.core.detectorMeshCenters != None and \
	len( data.core.detectorMeshCenters ) > 0:
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      det_gap = config[ 'detectorGap' ]
      det_wd = config[ 'detectorWidth' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      #value_font = config[ 'valueFont' ]

      title_fmt = '%s: %s %%.3g' % ( ds_name, self.state.timeDataSet )
      #title_fmt = '%s: Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % 99.999 )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      if 'detector_operable' in data.states[ state_ndx ].group:
        ds_operable = data.states[ state_ndx ].group[ 'detector_operable' ].value
      else:
        ds_operable = None

      axial_mesh_max = np.amax( data.core.detectorMeshCenters )
      axial_mesh_min = np.amin( data.core.detectorMeshCenters )
      axial_mesh_factor = (det_wd - 1) / (axial_mesh_max - axial_mesh_min)
#          (data.core.detectorMeshCenters[ -1 ] - data.core.detectorMeshCenters[ 0 ])
      if axial_mesh_factor < 0.0:
        axial_mesh_factor *= -1.0
      value_factor = (det_wd - 1) / value_delta

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      op_color = ( 255, 255, 255, 255 )
      noop_color = ( 155, 155, 155, 255 )
      grid_color = ( 200, 200, 200, 255 )
      line_color = ( 0, 0, 0, 255 )

#			-- Loop on rows
#			--
      #det_y = 1
      det_y = core_region[ 1 ]
      for det_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        detmap_row = data.core.detectorMap[ det_row, : ]

#				-- Row label
#				--
	if self.showLabels:
	  label = data.core.coreLabels[ 1 ][ det_row ]
	  label_size = label_font.getsize( label )
	  label_y = det_y + ((det_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )

#				-- Loop on col
#				--
	det_x = core_region[ 0 ]
	for det_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if det_row == self.cellRange[ 1 ] and self.showLabels:
	    label = data.core.coreLabels[ 0 ][ det_col ]
	    label_size = label_font.getsize( label )
	    label_x = det_x + ((det_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

#					-- Check for valid detector cell
#					--   and data
	  det_ndx = detmap_row[ det_col ] - 1
	  values = None
	  if det_ndx >= 0 and ds_value != None:
	    values = ds_value[ :, det_ndx ]

	  if values != None and len( values ) == len( data.core.detectorMeshCenters ):
#						-- Draw rectangle
#						--
#	    brush_color = Widget.GetColorTuple(
#	        value - ds_range[ 0 ], value_delta, 255
#	        )
#	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    if self.axialValue[ 2 ] >= 0:
	      color_value = values[ self.axialValue[ 2 ] ]
	    else:
	      color_value = np.average( values )
	    pen_color = Widget.GetColorTuple(
	        color_value - ds_range[ 0 ], value_delta, 255
	        )

	    brush_color = op_color
	    if ds_operable != None and len( ds_operable ) > det_ndx and \
	        ds_operable[ det_ndx ] != 0:
	      brush_color = noop_color

	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = brush_color, outline = pen_color
	        )

#						-- Draw plot grid lines
#						--
	    if det_wd >= 20:
	      incr = det_wd / 4.0
	      grid_y = det_y + 1
	      while grid_y < det_y + det_wd - 1:
	        im_draw.line(
		    [ det_x + 1, grid_y, det_x + det_wd - 1, grid_y ],
		    fill = grid_color
		    )
		grid_y += incr
	      grid_x = det_x + 1
	      while grid_x < det_x + det_wd - 1:
	        im_draw.line(
		    [ grid_x, det_y + 1, grid_x, det_y + det_wd - 1 ],
		    fill = grid_color
		    )
	        grid_x += incr
	    #end if det_wd ge 20 for grid lines

#						-- Draw plot
#						--
	    last_x = None
	    last_y = None
	    for i in range( len( values ) ):
	      dy = \
		  (axial_mesh_max - data.core.detectorMeshCenters[ i ]) * \
		  axial_mesh_factor
#                  (data.core.detectorMeshCenters[ i ] - axial_mesh_min) * \
#		  axial_mesh_factor
	      dx = (values[ i ] - ds_range[ 0 ]) * value_factor
	      cur_x = det_x + 1 + dx
	      cur_y = det_y + 1 + dy

	      if last_x != None:
	        im_draw.line(
		    [ last_x, last_y, cur_x, cur_y ],
		    fill = line_color
		    )
	      last_x = cur_x
	      last_y = cur_y
	    #end for values

	  elif data.core.coreMap[ det_row, det_col ] > 0:
	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = ( 0, 0, 0, 0 ), outline = ( 155, 155, 155, 255 )
	        )

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( core_region[ 2 ] + font_size, 0 ) )
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
      det_y = max( det_y, legend_size[ 1 ] )
      #det_y += font_size - det_gap
      det_y += font_size >> 2

      title_str = title_fmt % \
          data.GetTimeValue( state_ndx, self.state.timeDataSet )
#      title_str = title_fmt % data.states[ state_ndx ].exposure
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, det_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    return  im
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateDrawConfig()		-
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
    coreRegion
    detectorGap
    detectorWidth
    fontSize
    labelFont
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
          '[Detector2DView._CreateDrawConfig] size=%d,%d' % ( wd, ht )

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

# self.cellRange = None  # left, top, right, bottom, dx, dy
      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      det_adv_wd = region_wd / cell_range[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      det_adv_ht = region_ht / cell_range[ -1 ]

      if det_adv_ht < det_adv_wd:
        det_adv_wd = det_adv_ht

      det_gap = det_adv_wd >> 4
      det_wd = max( 1, det_adv_wd - det_gap )

      core_wd = cell_range[ -2 ] * (det_wd + det_gap)
      core_ht = cell_range[ -1 ] * (det_wd + det_gap)

    else:
      det_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      print >> sys.stderr, '[Detector2DView._CreateDrawConfig] det_wd=%d' % det_wd

      det_gap = det_wd >> 4
      core_wd = cell_range[ -2 ] * (det_wd + det_gap)
      core_ht = cell_range[ -1 ] * (det_wd + det_gap)

      font_size = self._CalcFontSize( 512 )
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
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size
    #end if-else

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    value_font_size = det_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    print >> sys.stderr, \
        '[Detector2DView._CreateDrawConfig]\n  font_size=%d, legend_size=%s, det_wd=%d, det_gap=%d, wd=%d, ht=%d\n  value_font_size=%d, value_font-None=%d' % \
        ( font_size, str( legend_size ), det_wd, det_gap, wd, ht, \
	  value_font_size, value_font == None )

    config = \
      {
      'clientSize': ( wd, ht ),
      'coreRegion': [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ],
      'detectorGap': det_gap,
      'detectorWidth': det_wd,
      'fontSize': font_size,
      'labelFont': label_font,
      'legendPilImage': legend_pil_im,
      'lineWidth': max( 1, det_gap ),
      'pilFont': pil_font,
      'valueFont': value_font,
      'valueFontSize': value_font_size
      }

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.CreateImage()			-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    wx_im = None

    config = self._CreateDrawConfig(
        self.data, self.dataSetName, self.cellRange, scale = 64
	)
    pil_im = self._CreateCoreImage(
        config, self.data, self.dataSetName,
	( self.stateIndex, )
	)
    wx_im = wx.EmptyImage( *pil_im.size )

    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
    wx_im.SetData( pil_im_data_str )

    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

    return  wx_im
  #end CreateImage


  #----------------------------------------------------------------------
  #     METHOD:         Detector2DView.CreateMenu()			-
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
  #     METHOD:         Detector2DView.CreatePopupMenu()		-
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
  #	METHOD:		Detector2DView.FindDetector()			-
  #----------------------------------------------------------------------
  def FindDetector( self, ev_x, ev_y ):
    """Finds the detector.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row )
"""
    result = None

    if self.config != None and self.data != None:
      if ev_x >= 0 and ev_y >= 0:
        det_size = self.config[ 'detectorWidth' ] + self.config[ 'detectorGap' ]
	core_region = self.config[ 'coreRegion' ]
        cell_x = min(
	    int( (ev_x - core_region[ 0 ]) / det_size ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
	    int( (ev_y - core_region[ 1 ]) / det_size ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	cell_y = max( self.cellRange[ 1 ], cell_y )

	det_ndx = self.data.core.detectorMap[ cell_y, cell_x ] - 1
	result = ( det_ndx, cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindDetector


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'detector'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
#	STATE_CHANGE_detectorDataSet, if there is ever more than one
    locks = set([
        STATE_CHANGE_axialValue, STATE_CHANGE_detectorIndex,
        STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
    return  self.menuDefs
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detectors 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.HandleStateChange()		-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    print >> sys.stderr, \
        '[Detector2DView.HandleStateChange] reason=%d' % reason
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[Detector2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      state_args = {}

      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
	  state_args[ 'axial_value' ] = self.state.axialValue

      if (reason & STATE_CHANGE_detectorDataSet) > 0:
        if self.state.detectorDataSet != self.dataSetName:
	  state_args[ 'detector_dataset' ] = self.state.detectorDataSet

      if (reason & STATE_CHANGE_detectorIndex) > 0:
        if self.state.detectorIndex != self.detectorIndex:
	  state_args[ 'detector_index' ] = self.state.detectorIndex

      if (reason & STATE_CHANGE_stateIndex) > 0:
        if self.state.stateIndex != self.stateIndex:
	  state_args[ 'state_index' ] = self.state.stateIndex

      if (reason & STATE_CHANGE_timeDataSet) > 0:
        state_args[ 'resized' ] = True

      if len( state_args ) > 0:
        wx.CallAfter( self._UpdateState, **state_args )
    #end else not STATE_CHANGE_init
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config != None:
      rel_col = self.detectorIndex[ 1 ] - self.cellRange[ 0 ]
      rel_row = self.detectorIndex[ 2 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	core_region = self.config[ 'coreRegion' ]
        det_gap = self.config[ 'detectorGap' ]
        det_wd = self.config[ 'detectorWidth' ]
	det_adv = det_gap + det_wd
        line_wd = self.config[ 'lineWidth' ]

	rect = \
	  [
	    rel_col * det_adv + core_region[ 0 ],
	    rel_row * det_adv + core_region[ 1 ],
	    det_wd + 1, det_wd + 1
	  ]

        block = chr( 0 ) * bmap.GetWidth() * bmap.GetHeight() * 4
        bmap.CopyToBuffer( block, wx.BitmapBufferFormat_RGBA )
	#new_bmap = wx.Bitmap.FromBufferRGBA( bmap.GetWidth(), bmap.GetHeight(),block )
        new_bmap = wx.EmptyBitmapRGBA( bmap.GetWidth(), bmap.GetHeight() )
        new_bmap.CopyFromBuffer( block, wx.BitmapBufferFormat_RGBA )

        dc = wx.MemoryDC( new_bmap )
	gc = wx.GraphicsContext.Create( dc )
	gc.SetPen(
	    wx.ThePenList.FindOrCreatePen(
	        wx.Colour( 255, 0, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
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
      #end if within range
    #end if self.config != None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._InitUI()			-
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

#		-- Lay out for both slides
#		--
#    inside_sizer = wx.BoxSizer( wx.HORIZONTAL )
#    inside_sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )
#    inside_sizer.Add( self.axialBean, 0, wx.ALL | wx.EXPAND, 1 )
#    inside_panel.SetSizer( inside_sizer )

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.bitmapPanel, 1, wx.ALL | wx.EXPAND )

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.  Sets properties: data
"""
    print >> sys.stderr, '[Detector2DView._LoadDataModel]'
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[Detector2DView._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      assy_extent = self.data.ExtractSymmetryExtent()
      self.cellRange = list( assy_extent )
      del self.cellRangeStack[ : ]

      self.axialValue = self.state.axialValue
      self.dataSetName = self.state.detectorDataSet
      self.detectorIndex = self.state.detectorIndex
      self.stateIndex = self.state.stateIndex
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._LoadDataModelUI()		-
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self ):
    """Must be called on the UI thread.
"""
    print >> sys.stderr, \
        '[Detector2DView._LoadDataModelUI] state: stateIndex=%d' % \
	self.state.stateIndex
#    self.exposureBean.SetRange( 1, len( self.data.states ) )
#    self.exposureBean.stateIndex = 0
    self._OnSize( None )
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    #ev.Skip()

#		-- Validate
#		--
    valid = False
    det = self.FindDetector( *ev.GetPosition() )
    if det != None and det[ 0 ] >= 0 and det != self.detectorIndex:
      valid = self.data.IsValid(
	  detector_index = det[ 0 ],
	  state_index = self.stateIndex
	  )

    if valid:
      self.FireStateChange( detector_index = det )
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._OnContextMenu()			-
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
  #	METHOD:		Detector2DView._OnDragEnd()			-
  #----------------------------------------------------------------------
  def _OnDragEnd( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[Detector2DView._OnDragEnd] enter'
    zoom_flag = False

    if self.HasCapture():
      self.ReleaseMouse()

    rect = None
    if self.dragStartPosition != None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    if rect == None or rect.width <= 5 or rect.height <= 5:
      self._OnClick( ev )

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
  #	METHOD:		Detector2DView._OnDragMove()			-
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
	  detector_index = det[ 0 ],
	  state_index = self.stateIndex
	  )

      if valid:
        ds = self.data.states[ self.stateIndex ].group[ self.dataSetName ]
        ds_value = np.amax( ds[ :, det[ 0 ] ] )

        if ds_value > 0.0:
#	  show_det_addr = '(%s-%s)' % \
#              ( self.data.core.coreLabels[ 0 ][ det[ 1 ] ], \
#	        self.data.core.coreLabels[ 1 ][ det[ 2 ] ]  )
	  show_det_addr = self.data.core.CreateAssyLabel( *det[ 1 : 3 ] )
	  tip_str = \
	      'Detector: %d %s\n%s max: %g' % \
	      ( det[ 0 ] + 1, show_det_addr, self.dataSetName, ds_value )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      print >> sys.stderr, '[Detector2DView._OnDragMove]', str( rect )

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
  #	METHOD:		Detector2DView._OnDragStart()			-
  #----------------------------------------------------------------------
  def _OnDragStart( self, ev ):
    """
"""
    self.bitmapCtrl.SetToolTipString( '' )
    det = self.FindDetector( *ev.GetPosition() )
    #if det != None and det[ 0 ] >= 0:
    if det != None:
      self.dragStartDetector = det
      self.dragStartPosition = ev.GetPosition()
  #end _OnDragStart


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._OnSize()			-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev == None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[Detector2DView._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None and \
        (self.curSize == None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
      self._BusyBegin()
      self.curSize = ( wd, ht )
      #wx.CallAfter( self._Configure )
      wx.CallAfter( self._UpdateState, resized = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._OnToggleLabels()		-
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
  #	METHOD:		Detector2DView._OnToggleLegend()		-
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
  #	METHOD:		Detector2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.SetDataSet()			-
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
  #	METHOD:		Detector2DView._UpdateState()			-
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

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      resized = True
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.dataSetName:
      resized = True
      self.dataSetName = kwargs[ 'detector_dataset' ]

    if 'detector_index' in kwargs and kwargs[ 'detector_index' ] != self.detectorIndex:
      changed = True
      self.detectorIndex = kwargs[ 'detector_index' ]

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      t = ( self.stateIndex, )

      must_create_image = True
      self.bitmapsLock.acquire()
      try:
        if t in self.bitmaps:
          self.bitmapCtrl.SetBitmap( self._HiliteBitmap( self.bitmaps[ t ] ) )
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

#end Detector2DView
