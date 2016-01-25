#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		assembly_view.py				-
#	HISTORY:							-
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2015-12-03	leerw@ornl.gov				-
#	  Using self._CreateValueDisplay().
#		2015-11-28	leerw@ornl.gov				-
#	  Calling DataModel.IsNoDataValue() instead of checking for
#	  gt value to draw.
#		2015-11-19	leerw@ornl.gov				-
#	  Adding support for 'extra' datasets.
#		2015-11-18	leerw@ornl.gov				-
#	  Relaxing to allow any axial and assembly dimensions.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-06-18	leerw@ornl.gov				-
# 	  Extending RasterWidget.
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

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.utils import DataUtils
from event.state import *
from legend import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Assembly2DView					-
#------------------------------------------------------------------------
class Assembly2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and exposure times or states.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )

    super( Assembly2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self ):
    """Retrieves the data for the current assembly selection.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = self.assemblyIndex[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset != None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      if self.cellRange[ 0 ] <= dset_shape[ 1 ] and \
          self.cellRange[ 1 ] <= dset_shape[ 0 ]:
	pin_row_start = self.cellRange[ 1 ]
	pin_row_end = min( self.cellRange[ 3 ], dset_shape[ 0 ] )
	pin_row_size = pin_row_end - pin_row_start
	pin_col_start = self.cellRange[ 0 ]
	pin_col_end = min( self.cellRange[ 2 ], dset_shape[ 1 ] )
	pin_col_size = pin_col_end - pin_col_start

	clip_data = dset_value[
	    pin_row_start : pin_row_end,
	    pin_col_start : pin_col_end,
	    axial_level, self.assemblyIndex[ 0 ]
	    ]

        #clip_data = dset.value[ :, :, axial_level, self.assemblyIndex[ 0 ] ]
        title = \
'%s: Assembly=%d; Axial=%.3f; %s=%.3g; Col Range=[%d:%d]; Row Range=[%d:%d]' % \
	    (
	    self.pinDataSet,
	    self.assemblyIndex[ 0 ] + 1,
	    self.axialValue[ 0 ],
	    #self.data.core.axialMeshCenters[ axial_level ],
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet ),
	    pin_col_start + 1, pin_col_end,
	    pin_row_start + 1, pin_row_end
            )
        csv_text = DataModel.ToCSV( clip_data, title )
      #end if data in range

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
    +
    assemblyRegion
    lineWidth
    pinGap
    pinWidth
    valueFont
    valueFontSize
"""
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.pinDataSet ),
	**kwargs
	)

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / self.cellRange[ -1 ]

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      print >> sys.stderr, '[Assembly2DView._CreateDrawConfig] pin_wd=%d' % pin_wd

      pin_gap = pin_wd >> 3
      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    value_font_size = pin_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None
#    value_font_smaller_size = value_font_size - (value_font_size / 6)
#    value_font_smaller = \
#        PIL.ImageFont.truetype( self.valueFontPath, value_font_smaller_size ) \
#	if value_font_size >= 4 else None

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size
#    config[ 'valueFontSmaller' ] = value_font_smaller

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level, assy_ndx )
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    print >> sys.stderr, \
        '[Assembly2DView._CreateRasterImage] tuple_in=%s' % str( tuple_in )
    im = None
    dset_array = None

    tuple_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    if self.config != None and tuple_valid:
      assy_region = self.config[ 'assemblyRegion' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]
      pin_gap = self.config[ 'pinGap' ]
      pin_wd = self.config[ 'pinWidth' ]
      value_font = self.config[ 'valueFont' ]
#      value_font_smaller = self.config[ 'valueFontSmaller' ]

      title_fmt = '%s: Assembly %%d, Axial %%.3f, %s %%.3g' % \
          ( self.data.GetDataSetDisplayName( self.pinDataSet ),
	    self.state.timeDataSet )
      title_size = pil_font.getsize( title_fmt % ( 99, 99.999, 99.999 ) )

#      ds_value = \
#          self.data.states[ state_ndx ].group[ self.pinDataSet ].value \
#	  if self.pinDataSet in self.data.states[ state_ndx ].group \
#	  else None
      dset = self.data.GetStateDataSet( state_ndx, self.pinDataSet )
      #dset_shape = dset.shape if dset != None else ( 0, 0, 0, 0 )
      #ds_value = dset.value if dset != None else None
      if dset == None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
      ds_range = self.data.GetRange( self.pinDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

#			-- Must be valid assy ndx
#			--
    if dset_array != None and assy_ndx < dset_shape[ 3 ]:
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

#			-- Loop on rows
#			--
      pin_y = assy_region[ 1 ]
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

#	  if ds_value != None:
#	    #DataModel.GetPinIndex( assy_ndx, axial_level, pin_col, pin_row )
#	    value = ds_value[ pin_row, pin_col, axial_level, assy_ndx ]
	  if pin_row < dset_shape[ 0 ] and pin_col < dset_shape[ 1 ]:
	    value = dset_array[ pin_row, pin_col, axial_level, assy_ndx ]
	  else:
	    value = 0.0

	  #if value > 0.0:
	  if not self.data.IsNoDataValue( self.pinDataSet, value ):
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
#	      value_precision = 2 if value < 0.0 else 3
#	      value_str = DataUtils.FormatFloat2( value, value_precision )
#	      e_ndx = value_str.lower().find( 'e' )
#	      if e_ndx > 1:
#	        value_str = value_str[ : e_ndx ]
#	      value_size = value_font.getsize( value_str )

	      value_str, value_size = \
	          self._CreateValueDisplay( value, 3, value_font, pin_wd )
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
	  self.data.core.axialMeshCenters[ axial_level ],
	  self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
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
    #end if self.config exists

    #return  im
    return  im if im != None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, assy_ndx, axial_level )
"""
    return  ( self.stateIndex, self.assemblyIndex[ 0 ], self.axialValue[ 1 ] )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = self.data.IsValid(
        assembly_index = self.assemblyIndex,
	axial_level = self.axialValue[ 1 ],
	#dataset_name = self.pinDataSet,
	pin_colrow = cell_info[ 1 : 3 ],
	state_index = self.stateIndex
	)

    if valid:
#      ds = self.data.states[ self.stateIndex ].group[ self.pinDataSet ]
#      ds_value = ds[
#          cell_info[ 2 ], cell_info[ 1 ],
#	  self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
#	  ]
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_shape = dset.shape if dset != None else ( 0, 0, 0, 0 )
      value = 0.0
      if cell_info[ 2 ] < dset_shape[ 0 ] and cell_info[ 1 ] < dset_shape[ 1 ]:
        value = dset[
            cell_info[ 2 ], cell_info[ 1 ],
	    min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 ),
	    min( self.assemblyIndex[ 0 ], dset_shape[ 3 ] - 1 )
	    ]

      #if value > 0.0:
      if not self.data.IsNoDataValue( self.pinDataSet, value ):
	ds_name = \
	    self.pinDataSet[ 6 : ] if self.pinDataSet.startswith( 'extra:' ) \
	    else self.pinDataSet
        show_pin_addr = ( cell_info[ 1 ] + 1, cell_info[ 2 ] + 1 )
	tip_str = \
	    'Pin: %s\n%s: %g' % \
	    ( str( show_pin_addr ), ds_name, value )
    #end if valid

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() and prepends -1 for an index value for drag processing.
@return			None if no match, otherwise tuple of
			( -1, 0-based cell_col, cell_row )
"""
    pin_addr = self.FindPin( ev_x, ev_y )
    return \
        None if pin_addr == None else \
	( -1, pin_addr[ 0 ], pin_addr[ 1 ] )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.FindPin()			-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin col and row.
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
  #	METHOD:		GetAllow4DDataSets()				-
  #----------------------------------------------------------------------
  def GetAllow4DDataSets( self ):
    """
@return			True
"""
    return  True
  #end GetAllow4DDataSets


  #----------------------------------------------------------------------
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


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
  #	METHOD:		Assembly2DView.GetInitialCellRange()		-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.data.ExtractSymmetryExtent().
Subclasses should override as needed.
@return			intial range of raster cells
			( left, top, right, bottom, dx, dy )
"""
    result = None
    if self.data != None:
      result = [
          0, 0,
	  self.data.core.npin, self.data.core.npin,
	  self.data.core.npin, self.data.core.npin
          ]
    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Assembly 2D View'
  #end GetTitle


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

	new_bmap = self._CopyBitmap( bmap )

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
  #	METHOD:		Assembly2DView.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = \
        tpl != None and len( tpl ) >= 3 and \
	tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.assemblyIndex[ 0 ] and \
	tpl[ 2 ] == self.axialValue[ 1 ]
    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    self.assemblyIndex = self.state.assemblyIndex
    self.pinDataSet = self.state.pinDataSet
    self.pinColRow = self.state.pinColRow
  #end _LoadDataModelValues


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
#      ds = self.data.states[ self.stateIndex ].group[ self.pinDataSet ]
#      ds_value = ds[
#          pin_addr[ 1 ], pin_addr[ 0 ],
#          self.axialValue[ 1 ], self.assemblyIndex[ 0 ] \
#	  ]
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_shape = dset.shape if dset != None else ( 0, 0, 0, 0 )
      value = 0.0
      if pin_addr[ 1 ] < dset_shape[ 0 ] and pin_addr[ 0 ] < dset_shape[ 1 ]:
        value = dset[
            pin_addr[ 1 ], pin_addr[ 0 ],
	    min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 ),
	    min( self.assemblyIndex[ 0 ], dset_shape[ 3 ] - 1 )
	    ]

      #if value > 0.0:
      if not self.data.IsNoDataValue( self.pinDataSet, value ):
        self.FireStateChange( pin_colrow = pin_addr )
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.pinDataSet:
      wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Assembly2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      resized = True
      self.pinDataSet = kwargs[ 'pin_dataset' ]

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Assembly2DView
