#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		intrapin_edits_assembly_view.py			-
#	HISTORY:							-
#		2018-10-22	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, six, sys, threading, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  #from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.config import *
from data.utils import DataUtils
from event.state import *

from .raster_widget import *
from .widget import *


#------------------------------------------------------------------------
#	CLASS:		IntraPinEditsAssembly2DView			-
#------------------------------------------------------------------------
class IntraPinEditsAssembly2DView( RasterWidget ):
  """Pin-by-pin intrapin edits assembly view across axials and times.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    self.nodeAddr = -1
    self.showChannelPins = True
    self.subAddr = ( -1, -1 )

    self.startDataSet = None
    self.countDataSet = None

    super( IntraPinEditsAssembly2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._CreateClipboardData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
#        self._CreateClipboardDisplayedData() if mode == 'displayed' else \
#        self._CreateClipboardSelectedDataAllAxials() \
#	  if mode == 'selected_all_axials' else \
#        self._CreateClipboardSelectedDataAllStates() \
#	  if mode == 'selected_all_states' else \
#        self._CreateClipboardSelectedData()

    csv_text = ''

    dset = start_dset = count_dset = None
    is_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_index = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue.pinIndex
	#state_index = self.stateIndex
	)
    if is_valid:
      dset, start_dset, count_dset = self._ReadDataSets()

    #if dset is not None and core is not None:
    if dset is not None and start_dset is not None and count_dset is not None:
      core = self.dmgr.GetCore()
      assy_ndx = self.assemblyAddr[ 0 ]
      axial_level = min( self.axialValue.pinIndex, start_dset.shape[ 2 ] - 1 )

      if mode != 'displayed':
        pin_row_start = self.subAddr[ 1 ]
        pin_row_end = pin_row_start + 1
        pin_col_start = self.subAddr[ 0 ]
        pin_col_end = pin_col_start + 1

      else:
        pin_row_start = min( self.cellRange[ 1 ], start_dset.shape[ 0 ] - 1 )
        pin_row_end = min( self.cellRange[ 3 ], start_dset.shape[ 0 ] )
        pin_col_start = min( self.cellRange[ 0 ], start_dset.shape[ 1 ] - 1 )
        pin_col_end = min( self.cellRange[ 2 ], start_dset.shape[ 1 ] )

      title_fmt = \
'"{0:s}: Assy={1:s}; Axial={2:.3f}; {3}={4:.3g};' + \
' Col Range=[{5:d},{6:d}]; Row Range=[{7:d},{8:d}]"\n'
      csv_text = title_fmt.format(
	  self.dmgr.GetDataSetDisplayName( self.curDataSet ),
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue.cm, self.state.timeDataSet, self.timeValue,
	  pin_col_start + 1, pin_col_end,
	  pin_row_start + 1, pin_row_end
          )

      for r in range( pin_row_start, pin_row_end ):
        for c in range( pin_col_start, pin_col_end ):
          csv_text += '\nradius,pin({0:d},{1:d})\n'.format( c + 1, r + 1 )
          region_count = count_dset[ r, c, axial_level, assy_ndx ]
          region_start = start_dset[ r, c, axial_level, assy_ndx ]
	  start_ndx = max( 0, region_start )
	  stop_ndx = min( region_start + region_count, dset.shape[ 0 ] )
          values = dset[ start_ndx : stop_ndx ]
          radial_mesh = self.dmgr.CalcRadialMesh(
              self.curDataSet, c, r, axial_level, assy_ndx,
              len( values )
              )
          for i in range( len( values ) ):
            csv_text += '{0:g},{1:g}\n'.format( radial_mesh[ i + 1 ], values[ i ] )
    #end if dset is not None and start_dset is not None and ...

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
@param  kwargs
    scale	pixels per pin (deprecated)
    scale_type  'linear' or 'log', defaulting to 'linear'
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    dataRange
    font
    fontSize
    labelFont
    labelSize
    legendBitmap
    legendSize
    mapper
    +
    assemblyRegion
    imageSize
    lineWidth
    pinGap
    pinWidth
    valueFont
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	)
    units = self.dmgr.GetDataSetAttr( self.curDataSet, 'units', self.timeValue )
    if units is not None:
      kwargs[ 'legend_title' ] = DataUtils.ToString( units )
    if 'scale_type' not in kwargs:
      kwargs[ 'scale_type' ] = self._ResolveScaleType( self.curDataSet )
      #kwargs[ 'scale_type' ] = self.dmgr.GetDataSetScaleType( self.curDataSet )
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_size = config[ 'legendSize' ]

#		-- Must calculate scale?
#		--
    wd, ht = config[ 'clientSize' ]

    # label : core : font-sp : legend
    region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
    pin_adv_wd = region_wd / self.cellRange[ -2 ]

    working_ht = max( ht, legend_size[ 1 ] )
    region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)
    pin_adv_ht = region_ht / self.cellRange[ -1 ]

    if self.fitMode == 'ht':
      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht
    else:
      if pin_adv_wd < pin_adv_ht:
        pin_adv_wd = pin_adv_ht

    pin_gap = pin_adv_wd >> 3
    pin_wd = max( 5, pin_adv_wd - pin_gap )

    assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
    assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

    region_x = label_size[ 0 ] + 2
    region_y = label_size[ 1 ] + 2
    image_wd = region_x + assy_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = max( region_y + assy_ht, legend_size[ 1 ] ) + (font_size << 1)

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    #config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'lineWidth' ] = max( 1, pin_gap >> 2 )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._CreateMenuDef()		-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( IntraPinEditsAssembly2DView, self )._CreateMenuDef()

##    ndx = 0
##    for item in menu_def:
##      if item.get( 'label', '' ) == 'Copy Selected Data':
##        break
##      ndx += 1
##    #end for
##
##    if ndx < len( menu_def ):
##      new_item = \
##        {
##	'label': 'Copy Selected Data All States',
##	'handler': functools.partial( self._OnCopyData, 'selected_all_states' )
##	}
##      menu_def.insert( ndx + 1, new_item )
##
##      new_item = \
##        {
##	'label': 'Copy Selected Data All Axials',
##	'handler': functools.partial( self._OnCopyData, 'selected_all_axials' )
##	}
##      menu_def.insert( ndx + 1, new_item )
##    #end if ndx < len( menu_def )

    return  menu_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._CreateRasterImage()	-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the wx.Image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx, axial_level )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None
    dset = start_dset = count_dset = dset_array = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
	axial_level = axial_level
	)
    if tuple_valid:
      dset, start_dset, count_dset = self._ReadDataSets()

    if config is None:
      config = self.config
    if config is not None and dset is not None and \
        start_dset is not None and count_dset is not None and \
        assy_ndx < start_dset.shape[ 3 ]:
      assy_region = config[ 'assemblyRegion' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]

      core = self.dmgr.GetCore()

#		-- intrapin_edits has no_factors, so this should always be None
      cur_factors = pin_factors = None
      if self.state.weightsMode == 'on':
        pin_factors = self.dmgr.GetFactors( self.curDataSet, True )
        cur_factors = pin_factors[ :, :, axial_level, assy_ndx ]

      title_templ, title_size = self._CreateTitleTemplate(
	  font, self.curDataSet, start_dset.shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )

#               -- Render
#               --
#			-- Limit axial level
      axial_level = min( axial_level, start_dset.shape[ 2 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )

      trans_brush = self._CreateTransparentBrush( gc )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      nodata_pen_color = ( 155, 155, 155, 255 )
      nodata_pen = gc.CreatePen( wx.Pen( nodata_pen_color, 1 ) )

      if self.showLabels:
	glabel_font = gc.CreateFont( label_font, wx.BLACK )
        gc.SetFont( glabel_font )

#			-- Loop on rows
#			--
      pin_y = assy_region[ 1 ]
      for pin_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#				-- Row label
#				--
	if self.showLabels and pin_row < core.npiny:
	  label = '%d' % (pin_row + 1)
	  text_size = gc.GetFullTextExtent( label )
	  label_y = pin_y + ((pin_wd - text_size[ 1 ]) / 2.0)
	  gc.DrawText( label, 1, label_y )
	#end if self.showLabels and pin_row < core.npiny

#				-- Loop on col
#				--
	pin_x = assy_region[ 0 ]
	for pin_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if self.showLabels and \
	      pin_row == self.cellRange[ 1 ] and pin_col < core.npinx:
	    label = '%d' % (pin_col + 1)
	    text_size = gc.GetFullTextExtent( label )
	    label_x = pin_x + ((pin_wd - text_size[ 0 ]) / 2.0)
	    gc.DrawText( label, label_x, 1 )
	  #end if self.showLabels and ...

#					-- Check row and col in range
          region_count = 0
	  if pin_row < start_dset.shape[ 0 ] and \
              pin_col < start_dset.shape[ 1 ] and \
              (cur_factors is None or cur_factors[ pin_row, pin_col ] > 0):
            region_count = count_dset[ pin_row, pin_col, axial_level, assy_ndx ]

	  if region_count > 0:
            #if ( pin_col, pin_row ) == ( 12, 10 ): pdb.set_trace()
            region_start = start_dset[ pin_row, pin_col, axial_level, assy_ndx ]
	    start_ndx = max( 0, region_start )
	    stop_ndx = min( region_start + region_count, dset.shape[ 0 ] )
            values = dset[ start_ndx : stop_ndx ]
            radial_mesh = self.dmgr.CalcRadialMesh(
                self.curDataSet, pin_col, pin_row, axial_level, assy_ndx,
                len( values )
                )
            self._DrawPin(
                gc, box = ( pin_x, pin_y, pin_wd ),
                mapper = mapper,
                rings = radial_mesh,
                values = values
                )

	  else:
	    gc.SetBrush( trans_brush )
	    gc.SetPen( nodata_pen )
	    gc.DrawEllipse( pin_x, pin_y, pin_wd, pin_wd )

	  pin_x += pin_wd + pin_gap
	#end for pin_col

	pin_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw Legend Image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    legend_bmap,
	    assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size, 2,
	    legend_bmap.GetWidth(), legend_bmap.GetHeight()
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      pin_y = max( pin_y, legend_size[ 1 ] )
      pin_y += font_size >> 1

      title_str = self._CreateTitleString(
	  title_templ,
	  #assembly = assy_ndx,
	  assembly = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  axial = axial_value.cm,
	  time = self.timeValue
          )
      self._DrawStringsWx(
	  gc, font,
	  ( title_str, ( 0, 0, 0, 255 ),
	    #assy_region[ 0 ], pin_y, assy_region[ 2 ] - assy_region[ 0 ],
	    assy_region[ 0 ], pin_y, assy_region[ 2 ],
	    'c' )
          )

      dc.SelectObject( wx.NullBitmap )
    #end if config is not None...

    return  bmap  if bmap is not None else  self.emptyBitmap
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:	        IntraPinEditsAssembly2DView._CreateStateTuple()	-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, assy_ndx, axial_level )
"""
#    dset, start_dset, count_dset = self._ReadDataSets()
#    if dset is not None and dset.attrs and \
#        'PinFirstRegionIndexArray' in dset.attrs:
#      start_name = DataSetName(
#          self.curDataSet.modelName,
#	  DataUtils.ToString( dset.attrs[ 'PinFirstRegionIndexArray' ] )
#	  )
#      start_dset = self.dmgr.GetH5DataSet( start_name, self.timeValue )
#      if start_dset is not None and start_dset.shape[ 2 ] == 1:
#        axial_level = 0

    return  ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue.pinIndex )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:        IntraPinEditsAssembly2DView._CreateToolTipText()	-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = False
    if cell_info is not None:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr = self.assemblyAddr,
	  axial_level = self.axialValue.pinIndex,
	  sub_addr = cell_info[ 1 : 3 ],
	  sub_addr_mode = 'pin'
          )

    dset = start_dset = count_dset = None
    if valid:
      dset, start_dset, count_dset = self._ReadDataSets()

    if start_dset is not None:
      axial_level = self.axialValue.pinIndex
      assy_ndx = self.assemblyAddr[ 0 ]
      dset_shape = start_dset.shape

      pin_col = cell_info[ 1 ]
      pin_row = cell_info[ 2 ]
      if pin_col < dset_shape[ 0 ] and pin_row < dset_shape[ 1 ]:
        region_count = count_dset[ pin_row, pin_col, axial_level, assy_ndx ]
        region_start = start_dset[ pin_row, pin_col, axial_level, assy_ndx ]
        start_ndx = max( 0, region_start )
        end_ndx = min( region_start + region_count, dset.shape[ 0 ] )

        values = dset[ start_ndx : end_ndx ]
        values_str = ','.join( [ '{0:g}'.format( i ) for i in values ] )

        show_pin_addr = ( pin_col + 1, pin_row + 1 )
        tip_str = 'Pin: {0}\n{1}: {2}'.format(
	    str( show_pin_addr ),
	    self.dmgr.GetDataSetDisplayName( self.curDataSet ),
            values_str
	    )
    #end if dset

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._DrawPin()		-
  #----------------------------------------------------------------------
  def _DrawPin( self, gc, box, mapper, rings, values ):
    """
    Args:
        gc (wx.GraphicsContext): context to use for rendering
        box (tuple): drawing extent ( x, y, wd )
        mapper (cm.ScalarMappable): for mapping colors
        rings (list): ring distances in cm
        values (np.ndarray): values for each ring
"""
    if len( rings ) > 1:
      color = mapper.to_rgba( values[ -1 ], bytes = True )
      wxcolor = wx.Colour( *color )
      gc.SetBrush( wx.TheBrushList.FindOrCreateBrush(
          wxcolor, wx.BRUSHSTYLE_SOLID
          ) )
      gc.SetPen( wx.ThePenList.FindOrCreatePen( wxcolor, 1, wx.PENSTYLE_SOLID ) )
      gc.DrawEllipse( box[ 0 ], box[ 1 ], box[ 2 ], box[ 2 ] )

    if len( rings ) > 2:
      half_wd = box[ 2 ] >> 1
      cx = box[ 0 ] + half_wd
      cy = box[ 1 ] + half_wd
      pix_per_cm = box[ 2 ] / (rings[ -1 ] * 2.0)
      for r in range( len( rings ) - 2, 0, -1 ):
        color = mapper.to_rgba( values[ r - 1 ], bytes = True )
        wxcolor = wx.Colour( *color )
        radius = rings[ r ] * pix_per_cm
        gc.SetBrush( wx.TheBrushList.FindOrCreateBrush(
            wxcolor, wx.BRUSHSTYLE_SOLID
            ) )
        gc.SetPen( wx.ThePenList.FindOrCreatePen( wxcolor, 1, wx.PENSTYLE_SOLID ) )
        gc.DrawEllipse( cx - radius, cy - radius, radius * 2.0, radius * 2.0 )
  #end _DrawPin


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.FindCell()		-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() and prepends -1 for an index value for drag processing.
@return			None if no match, otherwise tuple of
			( -1, 0-based cell_col, cell_row )
"""
    pin_addr = self.FindPin( ev_x, ev_y )
    return \
        None if pin_addr is None else \
	( -1, pin_addr[ 0 ], pin_addr[ 1 ] )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.FindPin()		-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin col and row.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    core = None
    if self.config is not None and 'assemblyRegion' in self.config:
      core = self.dmgr.GetCore()

    if core and ev_x >= 0 and ev_y >= 0:
      assy_region = self.config[ 'assemblyRegion' ]
      pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
      off_x = ev_x - assy_region[ 0 ]
      off_y = ev_y - assy_region[ 1 ]
      cell_x = min(
          int( off_x / pin_size ) + self.cellRange[ 0 ],
	  self.cellRange[ 2 ] - 1
	  )
      cell_x = max( self.cellRange[ 0 ], cell_x )
      cell_y = min(
	  int( off_y / pin_size ) + self.cellRange[ 1 ],
	  self.cellRange[ 3 ] - 1
	  )
      cell_y = max( self.cellRange[ 1 ], cell_y )
      result = ( cell_x, cell_y )
      #end if event within display
    #end if core and ev_x >= 0 and ev_y >= 0

    return  result
  #end FindPin


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView.GetAnimationIndexes()	-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.GetDataSetTypes()	-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'intrapin_edits' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.GetEventLockSet()	-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_timeValue
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView.GetInitialCellRange()	-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.dmgr.ExtractSymmetryExtent().
Subclasses should override as needed.
@return			initial range of raster cells
			( left, top, right, bottom, dx, dy )
"""
    core = self.dmgr.GetCore()
    return  ( 0, 0, core.npinx, core.npiny, core.npinx, core.npiny )
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.GetTitle()		-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Intrapin Edits Assembly 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._HiliteBitmap()	-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None:
      addr_list = list( self.auxSubAddrs )
      addr_list.insert( 0, self.subAddr )

      new_bmap = None
      dc = None
      secondary_pen = None

      assy_region = config[ 'assemblyRegion' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      pin_adv = pin_gap + pin_wd
      #line_wd = config[ 'lineWidth' ] + 1
      line_wd = min( max( 1, pin_gap - 1 ), 6 )

      for i in range( len( addr_list ) ):
	addr = addr_list[ i ]
        rel_col = addr[ 0 ] - self.cellRange[ 0 ]
        rel_row = addr[ 1 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	  if new_bmap is None:
	    new_bmap = self._CopyBitmap( bmap )
            dc = wx.MemoryDC( new_bmap )
	    gc = wx.GraphicsContext.Create( dc )

	  if i == 0:
	    gc.SetPen( wx.ThePenList.FindOrCreatePen(
                HILITE_COLOR_primary,
                line_wd, wx.PENSTYLE_SOLID
		) )
	  elif secondary_pen is None:
	    secondary_pen = wx.ThePenList.FindOrCreatePen(
	        HILITE_COLOR_secondary,
                line_wd, wx.PENSTYLE_SOLID
	        )
	    gc.SetPen( secondary_pen )

	  rect = [
	      rel_col * pin_adv + assy_region[ 0 ],
	      rel_row * pin_adv + assy_region[ 1 ],
	      #pin_wd + 1, pin_wd + 1
	      pin_wd, pin_wd
	      ]
	  path = gc.CreatePath()
	  path.AddRectangle( *rect )
	  gc.StrokePath( path )
        #end if addr within range
      #end for i

      if dc is not None:
        dc.SelectObject( wx.NullBitmap )
      if new_bmap is not None:
        result = new_bmap
    #end if config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.IsTupleCurrent()	-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    dset, start_dset, count_dset = self._ReadDataSets()
    axial_level = self.axialValue.pinIndex
    if start_dset is not None and start_dset.shape[ 2 ] == 1:
      axial_level = 0

    result = \
        tpl is not None and len( tpl ) >= 3 and \
	tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.assemblyAddr[ 0 ] and \
	tpl[ 2 ] == axial_level
	#tpl[ 2 ] == self.axialValue.pinIndex
    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._LoadDataModelValues()	-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    if (reason & STATE_CHANGE_coordinates) > 0:
      self.assemblyAddr = self.state.assemblyAddr
      self.subAddr = self.state.subAddr
    if (reason & STATE_CHANGE_curDataSet) > 0:
      self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.LoadProps()		-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'subAddr'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( IntraPinEditsAssembly2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._OnClick()		-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    is_aux = self.IsAuxiliaryEvent( ev )
    pos = ev.GetPosition()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnClickImpl, pos, is_aux )
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._OnClickImpl()	-
  #----------------------------------------------------------------------
  def _OnClickImpl( self, pos, is_aux ):
    """
"""
#		-- Validate
#		--
    valid = False
    pin_addr = self.FindPin( *pos )

    if pin_addr is not None and pin_addr != self.subAddr:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr = self.assemblyAddr[ 0 ],
	  axial_level = self.axialValue.pinIndex,
	  sub_addr = pin_addr,
	  sub_addr_mode = 'pin'
	  #state_index = self.stateIndex
	  )

    if valid:
      if is_aux:
	addrs = list( self.auxSubAddrs )
	if pin_addr in addrs:
	  addrs.remove( pin_addr )
	else:
	  addrs.append( pin_addr )
	#self.FireStateChange( aux_sub_addrs = addrs )
	node_addrs = self.dmgr.NormalizeNodeAddrs(
	    self.auxNodeAddrs + self.dmgr.GetNodeAddrs( addrs )
	    )
	self.FireStateChange(
	    aux_node_addrs = node_addrs,
	    aux_sub_addrs = addrs
	    )

      else:
        #self.FireStateChange( sub_addr = pin_addr, aux_sub_addrs = [] )
        #state_args = { 'aux_sub_addrs': [] 'sub_addr': pin_addr }
	state_args = dict(
	    aux_node_addrs = [],
	    aux_sub_addrs = [],
	    sub_addr = pin_addr
	    )
	node_addr = self.dmgr.GetNodeAddr( pin_addr )
	if node_addr >= 0:
	  state_args[ 'node_addr' ] = node_addr
        self.FireStateChange( **state_args )
      #end if-else is_aux
    #end if valid
  #end _OnClickImpl


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._OnFindMinMax()	-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    self.GetTopLevelParent().GetApp().DoBusyEventOp(
        self._OnFindMinMaxImpl, mode, all_states_flag, all_assy_flag
        )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._OnFindMinMaxImpl()	-
  #----------------------------------------------------------------------
  def _OnFindMinMaxImpl( self, mode, all_states_flag, all_assy_flag ):
    """Calls _OnFindMinMaxPin().
"""
    #xxxxx
    if self.curDataSet:
      self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag, all_assy_flag )
  #end _OnFindMinMaxImpl


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView._ReadDataSets()	-
  #----------------------------------------------------------------------
  def _ReadDataSets( self, time_value = -1 ):
    """
    Args:
        time_value (float): time value or -1 to use self.timeValue
    Returns:
        tuple: ( dataset, start_dataset, count_dataset ) or None if all
            three could not be read
"""
    if time_value < 0.0:
      time_value = self.timeValue

    dset = self.dmgr.GetH5DataSet( self.curDataSet, time_value )
    start_dset = count_dset = None
    if dset is not None and dset.attrs and \
        'PinFirstRegionIndexArray' in dset.attrs and \
        'PinNumRegionsArray' in dset.attrs:
      start_name = DataSetName(
          self.curDataSet.modelName,
	  DataUtils.ToString( dset.attrs[ 'PinFirstRegionIndexArray' ] )
	  )
      start_dset = self.dmgr.GetH5DataSet( start_name, self.timeValue )
      count_name = DataSetName(
	  self.curDataSet.modelName,
	  DataUtils.ToString( dset.attrs[ 'PinNumRegionsArray' ] )
	  )
      count_dset = self.dmgr.GetH5DataSet( count_name, self.timeValue )

    return  dset, start_dset, count_dset
  #end _ReadDataSets


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.SaveProps()		-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( IntraPinEditsAssembly2DView, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'showChannelPins', 'subAddr'
	):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsAssembly2DView.SetDataSet()	-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:	IntraPinEditsAssembly2DView._UpdateStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( IntraPinEditsAssembly2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

#		-- Just send aux_node_addrs event updates on clicks
    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.dmgr.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
	self.auxNodeAddrs = aux_node_addrs

    if 'aux_sub_addrs' in kwargs:
      aux_sub_addrs = self.dmgr.NormalizeSubAddrs(
          kwargs[ 'aux_sub_addrs' ],
	  'pin'
	  )
      if aux_sub_addrs != self.auxSubAddrs:
        changed = True
	self.auxSubAddrs = aux_sub_addrs

# Now handled in RasterWidget
#    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.pinDataSet:
#      ds_type = self.data.GetDataSetType( kwargs[ 'cur_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#        self.pinDataSet = kwargs[ 'cur_dataset' ]
#	self.container.GetDataSetMenu().Reset()

#		-- Just send node_addr event updates on clicks
    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr(
          kwargs[ 'sub_addr' ],
	  'pin'
	  )
      if sub_addr != self.subAddr:
        changed = True
	self.subAddr = sub_addr

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end IntraPinEditsAssembly2DView
