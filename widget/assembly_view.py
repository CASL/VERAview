#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		assembly_view.py				-
#	HISTORY:							-
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-21	leerw@ornl.gov				-
#	  Toggling legend.
#		2015-05-18	leerw@ornl.gov				-
#	  Making the showing of pin labels an option.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-04-22	leerw@ornl.gov				-
#	  Showing currently selected assembly.
#		2015-04-11	leerw@ornl.gov				-
#	  Transitioning to numbers and adding the capabilities of
#	  core_view.py.
#		2015-04-04	leerw@ornl.gov				-
#		2015-03-11	leerw@ornl.gov				-
#	  Using ExposureSliderBean.
#		2015-03-06	leerw@ornl.gov				-
#	  New Widget.GetImage() for 'loading' image.
#	  Starting ellipse drawing at pixel (1,1).
#		2015-02-06	leerw@ornl.gov				-
#	  New grid system.
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

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.utils import DataUtils
from event.state import *
from legend import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Assembly2DView					-
#------------------------------------------------------------------------
class Assembly2DView( Widget ):
  """Pin-by-pin assembly view across axials and exposure times or states.

Attrs/properties:
  assemblyIndex		0-based index of selected assembly, col, row
  bitmaps		ready-to-draw bitmaps[ ( state, axial, assy ) ]
  data			data.DataModel
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
#    self.axialLevel = -1
    self.axialValue = ( 0.0, -1, -1 )
    self.bitmaps = {}  # key is ( state_ndx, axial_level, assy_ndx )
    self.bitmapsLock = threading.RLock()
    #self.bitmapsLock = threading.Lock()
    self.cellRange = None  # left, top, right+1, bottom+1, dx, dy
    self.cellRangeStack = []
    self.config = None
    self.curSize = None
    self.data = None
    self.dataSetName = kwargs.get( 'dataset', 'pin_powers' )
    self.dragStartCell = None
    self.dragStartPosition = None

    self.menuDefs = \
      [
	( 'Hide Labels', self._OnToggleLabels ),
	( 'Hide Legend', self._OnToggleLegend ),
        ( 'Unzoom', self._OnUnzoom )
      ]
    self.pinColRow = None
    self.stateIndex = -1

    self.bitmapCtrl = None
    self.bitmapPanel = None
    self.blankBitmap = self.GetBitmap( 'loading' )
    self.overlay = None

    self.pilFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Black.ttf' )
#        os.path.join( Config.GetRootDir(), 'res/Times New Roman Bold.ttf' )

    self.popupMenu = None
    self.showLabels = True
    self.showLegend = True

    self.valueFontPath = \
        os.path.join( Config.GetRootDir(), 'res/Arial Narrow.ttf' )

    super( Assembly2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._BitmapThreadFinish()		-
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
        '[Assembly2DView._BitmapThreadFinish] cur=%s, pil_im=%s' % \
	( cur_tuple, pil_im != None )

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
          cur_tuple[ 1 ] == self.axialValue[ 1 ] and \
	  cur_tuple[ 2 ] == self.assemblyIndex[ 0 ]:
        self.bitmapCtrl.SetBitmap( self._HiliteBitmap( bmap ) )
    #end if cur_pair != None:

    self._BusyEnd()
  #end _BitmapThreadFinish


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._BitmapThreadStart()		-
  #----------------------------------------------------------------------
  def _BitmapThreadStart( self, cur_tuple ):
    """Background thread task to create the wx.Bitmap for the next
pair in the queue.  Paired with _BitmapThreadFinish().
Calls _CreateAssemblyImage().
"""
    print >> sys.stderr, \
        '[Assembly2DView._BitmapThreadStart] cur_tuple=%s' % str( cur_tuple )
    pil_im = None

    if cur_tuple != None:
      pil_im = self._CreateAssemblyImage(
          self.config, self.data, self.dataSetName, cur_tuple
	  )

    return  ( cur_tuple, pil_im )
  #end _BitmapThreadStart


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._ClearBitmaps()			-
  # Must be called from the UI thread.
  # @param  keep_tuple	0-based ( state_ndx, axial_level, assy_ndx ) to keep,
  #			or None
  #----------------------------------------------------------------------
  def _ClearBitmaps( self, keep_tuple = None ):
    """
@param  keep_tuple	0-based ( state_ndx, axial_level, assy_ndx ) to keep,
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
  #	METHOD:		Assembly2DView._Configure()			-
  #----------------------------------------------------------------------
  def _Configure( self ):
    """Must be called after the model is set to compute the draw
configuration based on the current size
Sets the config attribute.
"""
    wd, ht = self.bitmapPanel.GetClientSize()
    print >> sys.stderr, '[Assembly2DView._Configure] %d,%d' % ( wd, ht )


    self.config = None
    if wd > 0 and ht > 0 and self.data and self.data.HasData() and self.cellRange != None:
      self.config = self._CreateDrawConfig(
          self.data, self.dataSetName, self.cellRange,
	  size = ( wd, ht )
	  )
  #end _Configure


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateAssemblyImage()		-
  #----------------------------------------------------------------------
  def _CreateAssemblyImage( self, config, data, ds_name, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  config		draw configuration
@param  data		data model
@param  ds_name		dataset name
@param  tuple_in	0-based ( state_index, axial_level, assy_ndx )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    assy_ndx = tuple_in[ 2 ]
    print >> sys.stderr, \
        '[Assembly2DView._CreateAssemblyImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = data.IsValid(
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    if config != None and tuple_valid:
      assy_region = config[ 'assemblyRegion' ]
      im_wd, im_ht = config[ 'clientSize' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]

      title_fmt = '%s: Assembly %%d, Axial %%.3f, %s %%.3g' % \
          ( ds_name, self.state.timeDataSet )
      #title_fmt = '%s: Assembly %%d, Axial %%.3f, Exposure %%.3f' % ds_name
      title_size = pil_font.getsize( title_fmt % ( 99, 99, 99.999 ) )

      ds_value = \
          data.states[ state_ndx ].group[ ds_name ].value \
	  if ds_name in data.states[ state_ndx ].group \
	  else None
      ds_range = data.GetRange( ds_name )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

#			-- Loop on rows
#			--
      pin_y = assy_region[ 1 ]
#      for pin_row in range( data.core.npin ):
      for pin_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):

#				-- Row label
#				--
	if self.showLabels:
	  label = '%d' % (pin_row + 1)
	  label_size = label_font.getsize( label )
	  label_y = pin_y + ((pin_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )

#				-- Loop on col
#				--
	pin_x = assy_region[ 0 ]
	for pin_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if pin_row == self.cellRange[ 1 ] and self.showLabels:
	    label = '%d' % (pin_col + 1)
	    label_size = label_font.getsize( label )
	    label_x = pin_x + ((pin_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  value = 0.0
	  if ds_value != None:
	    value = ds_value[ pin_row, pin_col, axial_level, assy_ndx ]
	  if value > 0:
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    #im_draw.ellipse
	    im_draw.rectangle(
	        [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	        fill = brush_color, outline = pen_color
	        )

	    if value_font != None:
	      value_str = DataUtils.FormatFloat2( value )
	      e_ndx = value_str.lower().find( 'e' )
	      if e_ndx > 1:
	        value_str = value_str[ : e_ndx ]
	      value_size = value_font.getsize( value_str )
	      #if value_size[ 0 ] <= pin_wd:
	      if True:
		value_x = pin_x + ((pin_wd - value_size[ 0 ]) >> 1)
		value_y = pin_y + ((pin_wd - value_size[ 1 ]) >> 1) 
                im_draw.text(
		    ( value_x, value_y ), value_str,
		    fill = Widget.GetContrastColor( *brush_color ),
		    font = value_font
                    )
	    #end if value_font defined
	  #end if value > 0

	  pin_x += pin_wd + pin_gap
	#end for pin_col

	pin_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( assy_region[ 2 ] + font_size, 0 ) )
      if legend_pil_im != None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 2 ] + 2 + font_size, assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      pin_y = max( pin_y, legend_size[ 1 ] )
      pin_y += font_size >> 2

      title_str = title_fmt % ( \
	  assy_ndx + 1,
	  data.core.axialMeshCenters[ axial_level ],
	  data.GetTimeValue( state_ndx, self.state.timeDataSet )
#	  data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, pin_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    return  im
  #end _CreateAssemblyImage


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateDrawConfig()		-
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
    assemblyRegion
    clientSize
    fontSize
    labelFont
    legendPilImage
    pilFont
    pinGap
    pinWidth
    valueFont
    valueFontSize
"""

    ds_range = data.GetRange( ds_name )

#		-- Must calculate scale?
#		--
    if 'size' in kwargs:
      wd, ht = kwargs[ 'size' ]
      print >> sys.stderr, \
          '[Assembly2DView._CreateDrawConfig] size=%d,%d' % ( wd, ht )

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
      pin_adv_wd = region_wd / cell_range[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / cell_range[ -1 ]

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      assy_wd = cell_range[ -2 ] * (pin_wd + pin_gap)
      assy_ht = cell_range[ -1 ] * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      print >> sys.stderr, '[Assembly2DView._CreateDrawConfig] pin_wd=%d' % pin_wd

      pin_gap = pin_wd >> 3
      assy_wd = cell_range[ -2 ] * (pin_wd + pin_gap)
      assy_ht = cell_range[ -1 ] * (pin_wd + pin_gap)

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
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size
    #end if-else

    pil_font = PIL.ImageFont.truetype( self.pilFontPath, font_size )

    #value_font_size = int( pin_wd * 3.0 / 4.0 )
    value_font_size = pin_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    print >> sys.stderr, \
        '[Assembly2DView._CreateDrawConfig]\n  font_size=%d, legend_size=%s, pin_wd=%d, pin_gap=%d, wd=%d, ht=%d\n  value_font_size=%d, value_font-None=%d' % \
        ( font_size, str( legend_size ), pin_wd, pin_gap, wd, ht, \
	  value_font_size, value_font == None )

    config = \
      {
      'assemblyRegion': [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ],
      'clientSize': ( wd, ht ),
      'fontSize': font_size,
      'labelFont': label_font,
      'legendPilImage': legend_pil_im,
      'lineWidth': max( 1, pin_gap ),
      'pilFont': pil_font,
      'pinGap': pin_gap,
      'pinWidth': pin_wd,
      'valueFont': value_font,
      'valueFontSize': value_font_size
      }
#      'lineWidth': max( 1, min( 5, int( pin_wd / 20.0 ) ) ),

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.CreateImage()			-
  #----------------------------------------------------------------------
  def CreateImage( self, file_path ):
    wx_im = None

    config = self._CreateDrawConfig(
        self.data, self.dataSetName, self.cellRange, scale = 28
	)
    pil_im = self._CreateAssemblyImage(
        config, self.data, self.dataSetName,
	( self.stateIndex, self.axialValue[ 1 ] ) + self.assemblyIndex
	)
    wx_im = wx.EmptyImage( *pil_im.size )

    pil_im_data_str = pil_im.convert( 'RGB' ).tostring()
    wx_im.SetData( pil_im_data_str )

    pil_im_data_str = pil_im.convert( 'RGBA' ).tostring()
    wx_im.SetAlphaData( pil_im_data_str[ 3 : : 4 ] )

    return  wx_im
  #end CreateImage


  #----------------------------------------------------------------------
  #     METHOD:         Assembly2DView.CreatePopupMenu()		-
  #----------------------------------------------------------------------
  def CreatePopupMenu( self ):
    if self.popupMenu == None:
      self.popupMenu = wx.Menu()

      for label, handler in self.menuDefs:
        item = wx.MenuItem( self.popupMenu, wx.ID_ANY, label )
        self.Bind( wx.EVT_MENU, handler, item )
        self.popupMenu.AppendItem( item )
      #end for

      self._UpdateVisibilityMenuItems(
          self.popupMenu,
	  'Legend', self.showLegend,
	  'Pin Labels', self.showLabels
	  )
    #end if

    return  self.popupMenu
  #end CreatePopupMenu


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.FindPin()			-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row ), -1 if outside bounds
"""
    result = None

    if self.config != None and self.data != None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
        cell_x = min(
	    int( (ev_x - assy_region[ 0 ]) / pin_size ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / pin_size ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	cell_y = max( self.cellRange[ 1 ], cell_y )
	result = ( cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindPin


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetAxialLevel()			-
  #----------------------------------------------------------------------
#  def GetAxialLevel( self ):
#    """@return		0-based axial level
#"""
#    return  self.axialLevel
#  #end GetAxialLevel


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		( value, 0-based core index, 0-based detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """
"""
    return  self.menuDefs
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Assembly 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.HandleStateChange()		-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    print >> sys.stderr, \
        '[Assembly2DView.HandleStateChange] reason=%d' % reason
    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[Assembly2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      state_args = {}

      if (reason & STATE_CHANGE_assemblyIndex) > 0:
        if self.state.assemblyIndex != self.assemblyIndex:
	  state_args[ 'assembly_index' ] = self.state.assemblyIndex

      if (reason & STATE_CHANGE_axialValue) > 0:
        if self.state.axialValue != self.axialValue:
	  state_args[ 'axial_value' ] = self.state.axialValue
#      if (reason & STATE_CHANGE_axialLevel) > 0:
#        if self.state.axialLevel != self.axialLevel:
#	  state_args[ 'axial_level' ] = self.state.axialLevel

      if (reason & STATE_CHANGE_pinColRow) > 0:
        if self.state.pinColRow != self.pinColRow:
	  state_args[ 'pin_colrow' ] = self.state.pinColRow

      if (reason & STATE_CHANGE_pinDataSet) > 0:
        if self.state.pinDataSet != self.dataSetName:
	  state_args[ 'pin_dataset' ] = self.state.pinDataSet

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
  #	METHOD:		Assembly2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config != None:
      rel_col = self.pinColRow[ 0 ] - self.cellRange[ 0 ]
      rel_row = self.pinColRow[ 1 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_gap = self.config[ 'pinGap' ]
        pin_wd = self.config[ 'pinWidth' ]
	pin_adv = pin_gap + pin_wd
        line_wd = self.config[ 'lineWidth' ]

	rect = \
	  [
	    rel_col * pin_adv + assy_region[ 0 ],
	    rel_row * pin_adv + assy_region[ 1 ],
	    pin_wd + 1, pin_wd + 1
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
  #	METHOD:		Assembly2DView._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    self.overlay = wx.Overlay()
#    inside_panel = wx.Panel( self )

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

    self.SetAutoLayout( True )
    #self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetSizer( sizer )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Builds the images/bitmaps and updates the components for the current
model.  Sets properties: data
"""
    print >> sys.stderr, '[Assembly2DView._LoadDataModel]'
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      print >> sys.stderr, '[Assembly2DView._LoadDataModel] we have data'

#		-- Do here what is not dependent on size
#		--
      self.cellRange = [ \
          0, 0, \
	  self.data.core.npin, self.data.core.npin, \
	  self.data.core.npin, self.data.core.npin, \
	  ]
      del self.cellRangeStack[ : ]

      self.assemblyIndex = self.state.assemblyIndex
      self.axialValue = self.state.axialValue
      self.dataSetName = self.state.pinDataSet
      self.pinColRow = self.state.pinColRow
      self.stateIndex = self.state.stateIndex
      wx.CallAfter( self._LoadDataModelUI )
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._LoadDataModelUI()		-
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
  #	METHOD:		Assembly2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    #ev.Skip()

#		-- Validate
#		--
    valid = False
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None and pin_addr != self.pinColRow:
      valid = self.data.IsValid(
          assembly_index = self.assemblyIndex[ 0 ],
	  axial_level = self.axialValue[ 1 ],
	  pin_colrow = pin_addr,
	  state_index = self.stateIndex
	  )

    if valid:
      ds = self.data.states[ self.stateIndex ].group[ self.dataSetName ]
      ds_value = ds[ \
          pin_addr[ 1 ], pin_addr[ 0 ], self.axialValue[ 1 ], self.assemblyIndex[ 0 ] \
	  ]
      if ds_value > 0.0:
        self.FireStateChange( pin_colrow = pin_addr )
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnContextMenu()			-
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
  #	METHOD:		Assembly2DView._OnDragEnd()			-
  #----------------------------------------------------------------------
  def _OnDragEnd( self, ev ):
    """
"""
    #wd, ht = self.GetClientSize()
    #print >> sys.stderr, '[Assembly2DView._OnDragEnd] enter'
    zoom_flag = False

    if self.HasCapture():
      self.ReleaseMouse()

    rect = None
    if self.dragStartPosition != None:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )

    if rect == None or rect.width <= 5 or rect.height <= 5:
      self._OnClick( ev )

    else:
      pin_addr = self.FindPin( *ev.GetPosition() )
      #if pin_addr != None and self.data.IsValid( pin_colrow = pin_addr ):
      if pin_addr != None:
        left = min( self.dragStartCell[ 0 ], pin_addr[ 0 ] )
        right = max( self.dragStartCell[ 0 ], pin_addr[ 0 ] ) + 1
	top = min( self.dragStartCell[ 1 ], pin_addr[ 1 ] )
	bottom = max( self.dragStartCell[ 1 ], pin_addr[ 1 ] ) + 1

	self.cellRangeStack.append( self.cellRange )
	self.cellRange = [ left, top, right, bottom, right - left, bottom - top ]
	zoom_flag = True
      #end if pin found
    #end else dragging

    self.dragStartCell = None
    self.dragStartPosition = None

    self.overlay.Reset()
    self.Refresh()

    if zoom_flag:
      self._OnSize( None )
  #end _OnDragEnd


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnDragMove()			-
  #----------------------------------------------------------------------
  def _OnDragMove( self, ev ):
    """
"""
    #if self.HasCapture():
    #if ev.Dragging() and ev.LeftIsDown():
    if self.dragStartPosition == None:
      tip_str = ''
      pin_addr = self.FindPin( *ev.GetPosition() )
      valid = self.data.IsValid(
          assembly_index = self.assemblyIndex,
	  axial_level = self.axialValue[ 1 ],
	  dataset_name = self.dataSetName,
	  pin_colrow = pin_addr,
	  state_index = self.stateIndex
	  )

      if valid:
        ds = self.data.states[ self.stateIndex ].group[ self.dataSetName ]
        ds_value = ds[ \
            pin_addr[ 1 ], pin_addr[ 0 ], self.axialValue[ 1 ], self.assemblyIndex[ 0 ] \
	    ]

        if ds_value > 0.0:
	  show_pin_addr = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
	  tip_str = \
	      'Pin: %s\n%s: %g' % \
	      ( str( show_pin_addr ), self.dataSetName, ds_value )

      self.bitmapCtrl.SetToolTipString( tip_str )

    else:
      rect = wx.RectPP( self.dragStartPosition, ev.GetPosition() )
      print >> sys.stderr, '[Assembly2DView._OnDragMove]', str( rect )

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
  #	METHOD:		Assembly2DView._OnDragStart()			-
  #----------------------------------------------------------------------
  def _OnDragStart( self, ev ):
    """
"""
    self.bitmapCtrl.SetToolTipString( '' )
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None and pin_addr[ 0 ] >= 0 and pin_addr[ 1 ] >= 0:
      self.dragStartCell = pin_addr
      self.dragStartPosition = ev.GetPosition()
  #end _OnDragStart


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnSize()			-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    """
"""
    if ev == None:
      self.curSize = None
    else:
      ev.Skip()

    wd, ht = self.GetClientSize()
    print >> sys.stderr, '[Assembly2DView._OnSize] clientSize=%d,%d' % ( wd, ht )

    if wd > 0 and ht > 0 and self.data != None and \
        (self.curSize == None or wd != self.curSize[ 0 ] or ht != self.curSize[ 1 ]):
      self._BusyBegin()
      self.curSize = ( wd, ht )
      #wx.CallAfter( self._Configure )
      wx.CallAfter( self._UpdateState, resized = True )
  #end _OnSize


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnToggleLabels()		-
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
  #	METHOD:		Assembly2DView._OnToggleLegend()		-
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
  #	METHOD:		Assembly2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.dataSetName:
#      self.dataSetName = ds_name
#      wx.CallAfter( self._OnSize, None )
      wx.CallAfter( self._UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._UpdateState()			-
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

    if 'assembly_index' in kwargs and \
        kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = self.data.NormalizeAssemblyIndex( kwargs[ 'assembly_index' ] )

    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      changed = True
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )
#    if 'axial_level' in kwargs and kwargs[ 'axial_level' ] != self.axialLevel:
#      changed = True
#      self.axialLevel = self.data.NormalizeAxialLevel( kwargs[ 'axial_level' ] )
##      self.axialBean.axialLevel = \
##          max( 0, min( axial_level, self.data.core.nax - 1 ) )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.dataSetName:
      resized = True
      self.dataSetName = kwargs[ 'pin_dataset' ]

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      changed = True
      self.pinColRow = kwargs[ 'pin_colrow' ]

    if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
      changed = True
      self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

    if resized:
      self._ClearBitmaps()
      self._Configure()
      changed = True

    if changed and self.config != None:
      t = ( self.stateIndex, self.axialValue[ 1 ], self.assemblyIndex[ 0 ] )

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

#end Assembly2DView
