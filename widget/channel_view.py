#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		channel_view.py					-
#	HISTORY:							-
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DatModel.GetRange()
#	  directly.
#		2016-10-22	leerw@ornl.gov				-
#	  Calling DataModel.Core.Get{Col,Row}Label().
#		2016-10-21	leerw@ornl.gov				-
#	  Updating for node support.
#		2016-10-20	leerw@ornl.gov				-
#	  Calling DataModel.GetFactors().
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-10-14	leerw@ornl.gov				-
#	  Using new _DrawValues() method.
#		2016-09-29	leerw@ornl.gov				-
#	  Trying to prevent overrun of values displayed in cells.
#		2016-09-20	leerw@ornl.gov				-
#	  Fixed bug where brush_color might not have been defined when
#	  writing values.
#		2016-08-17	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-09	leerw@ornl.gov				-
#	  Added assembly label in clipboard headers.
#		2016-07-01	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _OnFindMax().
#		2016-02-29	leerw@ornl.gov				-
#	  Calling Redraw() instead of _OnSize( None ).
#		2016-02-19	leerw@ornl.gov				-
#	  Added copy selection.
#		2016-02-10	leerw@ornl.gov				-
#	  Title template and string creation now inherited from
#	  RasterWidget.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#	  Added _CreateClipboardData().
#		2015-11-28	leerw@ornl.gov				-
#	  Calling DataModel.IsNoDataValue() instead of checking for
#	  gt value to draw.
#		2015-11-23	leerw@ornl.gov				-
#	  Using new DataModel methods for dataset access.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-06-18	leerw@ornl.gov				-
# 	  Extending RasterWidget.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-23	leerw@ornl.gov				-
#		2015-05-21	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, sys, threading, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from event.state import *
from legend import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Channel2DView					-
#------------------------------------------------------------------------
class Channel2DView( RasterWidget ):
  """Channel-by-channel core and assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.channelDataSet = kwargs.get( 'dataset', 'channel_liquid_temps [C]' )
    self.mode = ''
    self.nodeAddr = -1
    self.nodalMode = False
    self.subAddr = None

    super( Channel2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateAssyDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateAssyDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per channel) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per channel
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    dataRange
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
    +
    assemblyRegion
    channelGap
    channelWidth
    lineWidth
    mode = 'assy'
"""
    ds_range = self._ResolveDataRange(
        self.channelDataSet,
	self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'size=%d,%d', wd, ht )

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      chan_adv_wd = region_wd / (self.data.core.npin + 1)

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      chan_adv_ht = region_ht / (self.data.core.npin + 1)

      if chan_adv_ht < chan_adv_wd:
        chan_adv_wd = chan_adv_ht

      #chan_gap = chan_adv_wd >> 3
      chan_gap = 0
      chan_wd = max( 1, chan_adv_wd - chan_gap )

      assy_wd = assy_ht = (self.data.core.npin + 1) * (chan_wd + chan_gap)

    else:
      chan_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 24
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'chan_wd=%d', chan_wd )

      #chan_gap = chan_wd >> 3
      chan_gap = 0
      assy_wd = assy_ht = (self.data.core.npin + 1) * (chan_wd + chan_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'channelGap' ] = chan_gap
    config[ 'channelWidth' ] = chan_wd
    config[ 'lineWidth' ] = max( 1, chan_gap )
    config[ 'mode' ] = 'assy'

    return  config
  #end _CreateAssyDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateAssyImage()		-
  #----------------------------------------------------------------------
  def _CreateAssyImage( self, tuple_in, config ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx, axial_level )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    tuple_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    
    if config is None:
      config = self.config
    if config is not None and tuple_valid:
      if 'assemblyRegion' not in config:
	if 'clientSize' in config:
          config = self._CreateAssyDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateAssyDrawConfig( scale = config[ 'scale' ] )

#			-- Draw channel "cells"
#			--
      assy_region = config[ 'assemblyRegion' ]
      chan_gap = config[ 'channelGap' ]
      chan_wd = config[ 'channelWidth' ]
      im_wd, im_ht = config[ 'clientSize' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]

      dset = self.data.GetStateDataSet( state_ndx, self.channelDataSet )
      chan_factors = None
      if self.state.weightsMode == 'on':
        #chan_factors = self.data.GetChannelFactors()
        chan_factors = self.data.GetFactors( self.channelDataSet )
        chan_factors_shape = chan_factors.shape

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
	cur_nxpin = cur_nypin = 0
      else:
        dset_array = dset.value
        dset_shape = dset.shape
        cur_nxpin = min( self.data.core.npinx, dset_shape[ 1 ] )
        cur_nypin = min( self.data.core.npiny, dset_shape[ 0 ] )

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )

#			-- Limit axial level
#			--
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      chan_y = assy_region[ 1 ]
      #for chan_row in range( self.data.core.npin + 1 ):
      for chan_row in range( cur_nypin + 1 ):
#				-- Row label
#				--
	#if self.showLabels and chan_row < self.data.core.npin:
	if self.showLabels:
	  label = '%d' % (chan_row + 1)
	  label_size = label_font.getsize( label )
	  #label_y = chan_y + ((chan_wd - label_size[ 1 ]) >> 1)
	  label_y = chan_y + chan_wd + ((chan_gap - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )

#				-- Loop on col
#				--
	chan_x = assy_region[ 0 ]
	#for chan_col in range( self.data.core.npin + 1 ):
	for chan_col in range( cur_nxpin + 1 ):
#					-- Column label
#					--
	  #if chan_row == 0 and self.showLabels and chan_col < self.data.core.npin:
	  if chan_row == 0 and self.showLabels:
	    label = '%d' % (chan_col + 1)
	    label_size = label_font.getsize( label )
	    #label_x = chan_x + ((chan_wd - label_size[ 0 ]) >> 1)
	    label_x = chan_x + chan_wd + ((chan_gap - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ), label,
		fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  value = dset_array[ chan_row, chan_col, axial_level, assy_ndx ]
	  if chan_factors is None:
	    chan_factor = 1
          else:
	    chan_factor = \
	        chan_factors[ chan_row, chan_col, axial_level, assy_ndx ]
	  #if not self.data.IsNoDataValue( self.channelDataSet, value ):
	  if not ( self.data.IsBadValue( value ) or chan_factor == 0 ):
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    #ellipse
	    im_draw.rectangle(
	        [ chan_x, chan_y, chan_x + chan_wd, chan_y + chan_wd ],
	        fill = brush_color, outline = pen_color
	        )
	  #end if value > 0

	  chan_x += chan_wd + chan_gap
	#end for chan_col

	chan_y += chan_wd + chan_gap
      #end for chan_row

#			-- Draw pins
#			--
      brush_color = ( 155, 155, 155, 128 )
      pen_color = Widget.GetDarkerColor( brush_color, 128 )
      pin_draw_wd = chan_wd >> 1

      pin_y = assy_region[ 1 ] + chan_wd + ((chan_gap - pin_draw_wd) >> 1)
      for pin_row in range( self.data.core.npin ):
	pin_x = assy_region[ 0 ] + chan_wd + ((chan_gap - pin_draw_wd) >> 1)
	for pin_col in range( self.data.core.npin ):
	  im_draw.ellipse(
	      [ pin_x, pin_y, pin_x + pin_draw_wd, pin_y + pin_draw_wd ],
	      fill = brush_color, outline = pen_color
	      )

	  pin_x += chan_wd + chan_gap
	#end for pin_col

	pin_y += chan_wd + chan_gap
      #end for pin_row

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 0 ] + assy_region[ 2 ] + 2 + font_size,
	      assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      chan_y = max( chan_y, legend_size[ 1 ] )
      chan_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  assembly = assy_ndx,
	  axial = self.data.core.axialMeshCenters[ axial_level ],
	  time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#(assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, chan_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateAssyImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardDisplayedData()  if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
#        self._CreateClipboardSelectionData() \
#        if cur_selection_flag else \
#        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      clip_shape = (
	  #self.core.npiny * self.cellRange[ -1 ],
          #self.core.npinx * self.cellRange[ -2 ]
	  dset_shape[ 0 ] * self.cellRange[ -1 ],
          dset_shape[ 1 ] * self.cellRange[ -2 ]
	  )
      clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      clip_data.fill( 0.0 )

      pin_row = 0
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
	#pin_row_to = pin_row + self.core.npiny
	pin_row_to = pin_row + dset_shape[ 0 ]

	pin_col = 0
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  #pin_col_to = pin_col + self.core.npinx
	  pin_col_to = pin_col + dset_shape[ 1 ]

          assy_ndx = self.data.core.coreMap[ assy_row, assy_col ] - 1
#	  if assy_ndx < 0:
#	    clip_data[ pin_row : pin_row_to, pin_col : pin_col_to ] = 0.0
#	  else:
	  if assy_ndx >= 0:
	    clip_data[ pin_row : pin_row_to, pin_col : pin_col_to ] = \
	        dset_value[ :, :, axial_level, assy_ndx ]

	  #pin_col += self.core.npinx
	  pin_col = pin_col_to
	#end for assy rows

	#pin_row += self.core.npiny
	pin_row = pin_row_to
      #end for assy rows

      title1 = '"%s: Axial=%.3f; %s=%.3g"' % (
	  self.channelDataSet,
	  self.axialValue[ 0 ],
	  #self.data.core.axialMeshCenters[ axial_level ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
#      col_labels = [
#          self.data.core.coreLabels[ 0 ][ i ]
#	  for i in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )
#          ]
      col_labels = self.data.core.\
          GetColLabel( self.cellRange[ 0 ], self.cellRange[ 2 ] )
#      row_labels = [
#          self.data.core.coreLabels[ 1 ][ i ]
#	  for i in range( self.cellRange[ 1 ], self.cellRange[ 3 ] )
#	  ]
      row_labels = self.data.core.\
          GetRowLabel( self.cellRange[ 1 ], self.cellRange[ 3 ] )
      title2 = 'Cols=%s; Rows=%s' % (
	  ':'.join( col_labels ),
	  ':'.join( row_labels )
          )
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the current assembly selection.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%d %s; Axial=%.3f; %s=%.3g"' % (
	  self.channelDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ],
	  #self.data.core.axialMeshCenters[ axial_level ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectedData



  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateCoreDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateCoreDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per channel) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per channel
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys:
    clientSize
    dataRange
    fontSize
    labelFont
    labelSize
    legendPilImage
    legendSize
    pilFont
    +
    assemblyAdvance
    assemblyWidth
    channelWidth
    coreRegion
    lineWidth
    mode = 'core'
    valueFont
    valueFontSize
"""
    ds_range = self._ResolveDataRange(
        self.channelDataSet,
	self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

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
      assy_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      assy_ht = region_ht / self.cellRange[ -1 ]

      if assy_ht < assy_wd:
        assy_wd = assy_ht

      chan_wd = max( 1, (assy_wd - 2) / (self.data.core.npin + 1) )
      assy_wd = chan_wd * (self.data.core.npin + 1) + 1
      assy_advance = assy_wd
      core_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = self.cellRange[ -1 ] * assy_advance

    else:
      chan_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'chan_wd=%d', chan_wd )
      assy_wd = chan_wd * (self.data.core.npin + 1) + 1
      assy_advance = assy_wd

      font_size = self._CalcFontSize( 768 )

      core_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = self.cellRange[ -1 ] * assy_advance

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    value_font_size = assy_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    config[ 'assemblyAdvance' ] = assy_advance
    config[ 'assemblyWidth' ] = assy_wd
    config[ 'channelWidth' ] = chan_wd
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'mode' ] = 'core'
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, tuple_in, config ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    if config is None:
      config = self.config
    if config is not None:
      if 'coreRegion' not in config:
	if 'clientSize' in config:
          config = self._CreateCoreDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateCoreDrawConfig( scale = config[ 'scale' ] )

      assy_advance = config[ 'assemblyAdvance' ]
      assy_wd = config[ 'assemblyWidth' ]
      chan_wd = config[ 'channelWidth' ]
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]

      dset = self.data.GetStateDataSet( state_ndx, self.channelDataSet )
      chan_factors = None
      if self.state.weightsMode == 'on':
        #chan_factors = self.data.GetChannelFactors()
        chan_factors = self.data.GetFactors( self.channelDataSet )
        chan_factors_shape = chan_factors.shape

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
	cur_nxpin = cur_nypin = 0
      else:
        dset_array = dset.value
        dset_shape = dset.shape
        cur_nxpin = min( self.data.core.npinx + 1, dset_shape[ 1 ] )
        cur_nypin = min( self.data.core.npiny + 1, dset_shape[ 0 ] )

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	  axial_ndx = 2
	  )

      draw_value_flag = \
          self.channelDataSet is not None and \
          dset_shape[ 0 ] == 1 and dset_shape[ 1 ] == 1
          #value_font is not None
      #node_value_draw_list = []
      assy_value_draw_list = []

#			-- Limit axial level
#			--
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )

#			-- Loop on assembly rows
#			--
      assy_y = core_region[ 1 ]
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        core_data_row = self.data.core.coreMap[ assy_row, : ]

#				-- Row label
#				--
	if self.showLabels:
#	  label = self.data.core.coreLabels[ 1 ][ assy_row ]
	  label = self.data.core.GetRowLabel( assy_row )
	  label_size = pil_font.getsize( label )
	  label_y = assy_y + ((assy_wd - label_size[ 1 ]) >> 1)
	  im_draw.text(
	      ( 1, label_y ),
	      label, fill = ( 0, 0, 0, 255 ), font = label_font
	      )

#				-- Loop on col
#				--
	assy_x = core_region[ 0 ]
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  brush_color = None
#					-- Column label
#					--
	  if assy_row == self.cellRange[ 1 ] and self.showLabels:
#	    label = self.data.core.coreLabels[ 0 ][ assy_col ]
	    label = self.data.core.GetColLabel( assy_col )
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  assy_ndx = core_data_row[ assy_col ] - 1
	  #if assy_ndx >= 0:
	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    chan_y = assy_y + 1
	    #cur_nypin = min( self.data.core.npin + 1, dset_shape[ 0 ] )
	    #cur_nxpin = min( self.data.core.npin + 1, dset_shape[ 1 ] )

	    #for chan_row in range( cur_nypin ):
	    for chan_row in range( self.data.core.npiny + 1 ):
	      chan_x = assy_x + 1

	      cur_chan_row = min( chan_row, cur_nypin - 1 )
	      #for chan_col in range( cur_nxpin ):
	      for chan_col in range( self.data.core.npinx + 1 ):
	        cur_chan_col = min( chan_col, cur_nxpin - 1 )
		value = 0.0
		chan_factor = 0
		if cur_chan_row >= 0 and cur_chan_col >= 0:
		  value = dset_array[
		      cur_chan_row, cur_chan_col, axial_level, assy_ndx
		      ]
	          if chan_factors is None:
	            chan_factor = 1
		  else:
	            chan_factor = chan_factors[
		        cur_chan_row, cur_chan_col, axial_level, assy_ndx
			]
		#end if cur_chan_row and cur_chan_col

	        #if not self.data.IsNoDataValue( self.channelDataSet, value ):
	        if not ( self.data.IsBadValue( value ) or chan_factor == 0 ):
	          pen_color = Widget.GetColorTuple(
	              value - ds_range[ 0 ], value_delta, 255
	              )
	          brush_color = \
		      ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
		  #im_draw.ellipse
	          im_draw.rectangle(
		      [ chan_x, chan_y, chan_x + chan_wd, chan_y + chan_wd ],
		      fill = brush_color, outline = pen_color
		      )
		#end if good value and not hidden by chan_factor
	        chan_x += chan_wd
	      #end for chan cols

	      chan_y += chan_wd
	    #end for chan rows

	    im_draw.rectangle(
		[ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
		fill = None, outline = assy_pen
	        )

#           -- Draw value for cross-pin integrations
	    if draw_value_flag and brush_color is not None:
	      value = dset_array[ 0, 0, axial_level, assy_ndx ]
	      assy_value_draw_list.append((
	          self._CreateValueString( value, 3 ),
                  Widget.GetContrastColor( *brush_color ),
		  assy_x, assy_y, assy_wd, assy_wd
	          ))
#	      value_str, value_size, tfont = self._CreateValueDisplay(
#	          value, 3, value_font, assy_wd, value_font_size
#		  )
#	      if value_str:
#		value_x = assy_x + ((assy_wd - value_size[ 0 ]) >> 1)
#		value_y = assy_y + ((assy_wd - value_size[ 1 ]) >> 1)
#                im_draw.text(
#		    ( value_x, value_y ), value_str,
#		    fill = Widget.GetContrastColor( *brush_color ),
#		    font = tfont
#                    )
	    #end if draw_value_flag
	  #end if assembly referenced

	  assy_x += assy_advance
	#end for assy_col

        assy_y += assy_advance
      #end for assy_row

#			-- Draw Values
#			--
      if assy_value_draw_list:
        self._DrawValues( assy_value_draw_list, im_draw )

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( core_region[ 0 ] + core_region[ 2 ] + 2 + font_size,
	      core_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      assy_y = max( assy_y, legend_size[ 1 ] )
      assy_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  axial = self.data.core.axialMeshCenters[ axial_level ],
	  time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
#(core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, assy_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys needed by _CreateRasterImage().
"""
    return \
        self._CreateAssyDrawConfig( **kwargs ) if self.mode == 'assy' else \
	self._CreateCoreDrawConfig( **kwargs )
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config_in = None ):
    """Called in background task to create the PIL image for the state.
The config and data attributes are good to go.
@param  tuple_in	state tuple
@param  config_in	optional config to use instead of self.config
@return			PIL image
"""
    return \
        self._CreateAssyImage( tuple_in, config_in ) \
	if self.mode == 'assy' else \
	self._CreateCoreImage( tuple_in, config_in )
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			mode == 'assy':
			( state_index, assy_ndx, axial_level,
			  assy_col, assy_row )
			mode == 'core':
			( state_index, axial_level )
"""
    return \
        ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue[ 1 ],
	  self.assemblyAddr[ 1 ], self.assemblyAddr[ 2 ] ) \
        if self.mode == 'assy' else \
        ( self.stateIndex, self.axialValue[ 1 ] )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    if self.mode == 'core' and cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )
      #if dset is not None and assy_ndx < dset.shape[ 3 ]:
      if dset is not None:
        assy_ndx = min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
        axial_value = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 ),
        show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
	value = None

	if self.nodalMode:
	  node_addr = cell_info[ 5 ] if len( cell_info ) > 5 else -1
	  if self.data.IsValid( node_addr = node_addr ):
	    tip_str = 'Assy: %d %s, Node %d' % \
	        ( assy_ndx + 1, show_assy_addr, node_addr + 1 )
	    value = dset[ 0, node_addr, axial_value, assy_ndx ]
	else:
          tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )
	  if dset.shape[ 0 ] == 1 or dset.shape[ 1 ] == 1:
	    value = dset[ 0, 0, axial_value, assy_ndx ]
	#end if self.nodalMode

	if not self.data.IsBadValue( value ):
	  tip_str += ': %g' % value
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row,
			  chan_col, chan_row, node_addr )
"""
    result = None

    if self.config is not None and self.data is not None and \
        self.data.core is not None and self.data.core.coreMap is not None:
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

	chan_wd = self.config[ 'channelWidth' ]
	if self.nodalMode:
	  node_col = int( (off_x % assy_advance) / chan_wd )
	  node_row = int( (off_y % assy_advance) / chan_wd )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  chan_col, chan_row = \
	      self.data.GetSubAddrFromNode( node_addr, 'channel' )
	else:
	  chan_col = int( (off_x % assy_advance) / chan_wd )
	  if chan_col > self.data.core.npinx: chan_col = -1
	  chan_row = int( (off_y % assy_advance) / chan_wd )
	  if chan_row > self.data.core.npiny: chan_row = -1
	  node_addr = self.data.GetNodeAddr( ( chan_col, chan_row ), 'channel' )

	result = ( assy_ndx, cell_x, cell_y, chan_col, chan_row, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
"""
    return \
        self.FindChannel( ev_x, ev_y ) if self.mode == 'assy' else \
        self.FindAssembly( ev_x, ev_y )

    result = None
    if self.mode == 'assy':
      chan = self.FindChannel( ev_x, ev_y )
      result = ( -1, chan[ 0 ], chan[ 1 ] )
    else:
      result = self.FindAssembly( ev_x, ev_y )

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.FindChannel()			-
  #----------------------------------------------------------------------
  def FindChannel( self, ev_x, ev_y ):
    """Finds the channel index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row, node_addr )
"""
    result = None

    if self.config is not None and self.data is not None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        chan_size = self.config[ 'channelWidth' ] + self.config[ 'channelGap' ]

	if self.nodalMode:
	  node_col = min( int( (ev_x - assy_region[ 0 ]) / chan_size ), 1 )
	  node_row = min( int( (ev_y - assy_region[ 1 ]) / chan_size ), 1 )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  cell_x, cell_y = self.data.GetSubAddrFromNode( node_addr, 'channel' )
	else:
          cell_x = min(
	      int( (ev_x - assy_region[ 0 ]) / chan_size ),
	      self.data.core.npin
	      )
          cell_y = min(
	      int( (ev_y - assy_region[ 1 ]) / chan_size ),
	      self.data.core.npin
	      )
          node_addr = self.data.GetNodeAddr( ( cell_x, cell_y ), 'channel' )

	result = ( cell_x, cell_y, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindChannel


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  \
      [
        'channel', ':assembly', ':chan_radial', ':radial_assembly'
      ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_stateIndex
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		24 in 'assy' mode, 4 in 'core' mode
"""
    return  24 if self.mode == 'assy' else 4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Channel Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config is not None:
      line_wd = self.config[ 'lineWidth' ]
      half_line_wd = line_wd >> 1
      draw_list = []  # ( rect, pen )

      if self.nodalMode:
        node_addr_list = list( self.auxNodeAddrs )
        #node_addr_list.insert( 0, self.nodeAddr )
        node_addr_list.append( self.nodeAddr )
        select_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 255, 255, 255, 255 ),
	    half_line_wd, wx.PENSTYLE_SOLID
	    )
        primary_pen = wx.ThePenList.FindOrCreatePen(
#	    wx.Colour( 255, 255, 255, 255 ),
	    wx.Colour( 255, 0, 0, 255 ),
	    #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
	    line_wd, wx.PENSTYLE_SOLID
	    )
        secondary_pen = wx.ThePenList.FindOrCreatePen(
	    wx.Colour( 255, 255, 0, 255 ),
	    #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
	    line_wd, wx.PENSTYLE_SOLID
	    )
      else:
        select_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 255, 0, 0, 255 ),
	    line_wd, wx.PENSTYLE_SOLID
	    )
      #end if-else self.nodalMode

#      if self.cellRange[ -2 ] == 1 and self.cellRange[ -1 ] == 1:
#        pass

#			-- Core mode
#			--
      if self.config[ 'mode' ] == 'core':
        rel_col = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
        rel_row = self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
          assy_adv = self.config[ 'assemblyAdvance' ]
	  assy_wd = self.config[ 'assemblyWidth' ]
	  core_region = self.config[ 'coreRegion' ]

	  rect = \
	    [
	      rel_col * assy_adv + core_region[ 0 ],
	      rel_row * assy_adv + core_region[ 1 ],
	      assy_wd, assy_wd
	    ]
	  draw_list.append( ( rect, select_pen ) )

#					-- Core nodal
	  if self.nodalMode:
	    node_wd = self.config[ 'channelWidth' ]
            for i in range( len( node_addr_list ) ):
	      node_addr = node_addr_list[ i ]
	      if node_addr >= 0:
	        rel_x = node_wd if node_addr in ( 1, 3 ) else half_line_wd
	        rel_y = node_wd if node_addr in ( 2, 3 ) else half_line_wd
	        node_rect = [
	            rect[ 0 ] + rel_x, rect[ 1 ] + rel_y,
		    node_wd - half_line_wd, node_wd - half_line_wd
		    ]
		#pen = primary_pen if i == 0 else secondary_pen
		pen = \
		    secondary_pen if i < len( node_addr_list ) - 1 else \
		    primary_pen
	        draw_list.append( ( node_rect, pen ) )
	      #end if valid node addr
	    #end for i
	  #end if nodalMode
        #end if cell in drawing range

#			-- Assy nodal mode
#			--
      elif self.nodalMode:
        assy_region = self.config[ 'assemblyRegion' ]
        chan_gap = self.config[ 'channelGap' ]
	chan_wd = self.config[ 'channelWidth' ]
	chan_adv = chan_wd + chan_gap

	for i in range( len( node_addr_list ) ):
	  node_addr = node_addr_list[ i ]
	  if node_addr >= 0:
	    rel_x = chan_adv if node_addr in ( 1, 3 ) else 0
	    rel_y = chan_adv if node_addr in ( 2, 3 ) else 0
	    node_rect = [
		assy_region[ 0 ] + rel_x,
		assy_region[ 1 ] + rel_y,
		chan_wd, chan_wd
		]
	    #pen = primary_pen if i == 0 else secondary_pen
	    pen = \
	        secondary_pen if i < len( node_addr_list ) - 1 else primary_pen
	    draw_list.append( ( node_rect, pen ) )
	  #end if valid node addr
	#end for i

#			-- Assy not nodal mode
#			--
      else:  # 'assy'
	if self.subAddr[ 0 ] >= 0 and self.subAddr[ 1 ] >= 0 and \
	    self.subAddr[ 0 ] <= self.data.core.npinx and \
	    self.subAddr[ 1 ] <= self.data.core.npiny:
          assy_region = self.config[ 'assemblyRegion' ]
	  chan_gap = self.config[ 'channelGap' ]
	  chan_wd = self.config[ 'channelWidth' ]
	  chan_adv = chan_wd + chan_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.subAddr[ 0 ] * chan_adv + assy_region[ 0 ],
	      self.subAddr[ 1 ] * chan_adv + assy_region[ 1 ],
	      chan_adv, chan_adv
	    ]
	  draw_list.append( ( rect, select_pen ) )
        #end if cell in drawing range
      #end if-else on mode

#			-- Draw?
#			--
      if draw_list:
	new_bmap = self._CopyBitmap( bmap )

        dc = wx.MemoryDC( new_bmap )
	gc = wx.GraphicsContext.Create( dc )

	for draw_item in draw_list:
	  gc.SetPen( draw_item[ 1 ] )
	  path = gc.CreatePath()
	  path.AddRectangle( *draw_item[ 0 ] )
	  gc.StrokePath( path )
	#end for draw_item

	dc.SelectObject( wx.NullBitmap )
	result = new_bmap
      #end if draw_list
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._HiliteBitmap_old()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap_old( self, bmap ):
    result = bmap

    if self.config is not None:
      line_wd = -1
      rect = None

      if self.cellRange[ -2 ] == 1 and self.cellRange[ -1 ] == 1:
        pass

#			-- Core mode
#			--
      elif self.config[ 'mode' ] == 'core':
        rel_col = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
        rel_row = self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]

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
	if self.subAddr[ 0 ] >= 0 and self.subAddr[ 1 ] >= 0 and \
	    self.subAddr[ 0 ] <= self.data.core.npinx and \
	    self.subAddr[ 1 ] <= self.data.core.npiny:
          assy_region = self.config[ 'assemblyRegion' ]
	  chan_gap = self.config[ 'channelGap' ]
	  chan_wd = self.config[ 'channelWidth' ]
	  chan_adv = chan_wd + chan_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.subAddr[ 0 ] * chan_adv + assy_region[ 0 ],
	      self.subAddr[ 1 ] * chan_adv + assy_region[ 1 ],
	      chan_adv, chan_adv
	    ]
        #end if cell in drawing range
      #end if-else on mode

#			-- Draw?
#			--
      if rect is not None:
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
      #end if rect
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap_old


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._InitEventHandlers()		-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    self._SetMode( 'core' )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = False

    if self.mode == 'assy':
      result = \
          tpl is not None and len( tpl ) >= 5 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == self.assemblyAddr[ 0 ] and \
	  tpl[ 2 ] == self.axialValue[ 1 ] and \
	  tpl[ 3 ] == self.assemblyAddr[ 1 ] and \
	  tpl[ 4 ] == self.assemblyAddr[ 2 ]

    else:
      result = \
          tpl is not None and len( tpl ) >= 2 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == self.axialValue[ 1 ]

    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    self.assemblyAddr = self.state.assemblyAddr
    self.channelDataSet = self._FindFirstDataSet( self.state.curDataSet )
    self.subAddr = self.state.subAddr
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in (
        'assemblyAddr', 'auxNodeAddr' 'channelDataSet', 'mode',
	'nodeAddr', 'subAddr'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Channel2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindAssembly( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_addr = cell_info[ 0 : 3 ]
      if assy_addr != self.assemblyAddr:
	state_args[ 'assembly_addr' ] = assy_addr

      if self.nodalMode:
        node_addr = cell_info[ 5 ]
        is_aux = self.IsAuxiliaryEvent( ev )
	if is_aux:
	  addrs = list( self.auxNodeAddrs )
	  if node_addr in addrs:
	    addrs.remove( node_addr )
	  else:
	    addrs.append( node_addr )
	  if addrs != self.auxNodeAddrs:
	    state_args[ 'aux_node_addrs' ] = addrs
	elif node_addr != self.nodeAddr:
	  state_args[ 'node_addr' ] = node_addr
	  state_args[ 'aux_node_addrs' ] = []
	elif ev.GetClickCount() > 1:
	  sub_addr = self.data.GetSubAddrFromNode( node_addr, 'channel' )
	  if sub_addr != self.subAddr:
	    state_args[ 'sub_addr' ] = sub_addr
	#end if-elif is_aux

      #if ev.GetClickCount() > 1:
      elif ev.GetClickCount() > 1:
        chan_addr = cell_info[ 3 : 5 ]
        if chan_addr != self.subAddr:
	  state_args[ 'sub_addr' ] = chan_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnDragFinished()			-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    if right - left == 1 and bottom - top == 1:
      self.assemblyAddr = self.dragStartCell
      self.FireStateChange( assembly_addr = self.assemblyAddr )
      self._SetMode( 'assy' )
    else:
      self._SetMode( 'core' )
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnFindMax()			-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Calls _OnFindMaxChannel().
"""
    if DataModel.IsValidObj( self.data ) and self.channelDataSet is not None:
      self._OnFindMaxChannel( self.channelDataSet, all_states_flag )
  #end _OnFindMax


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxChannel().
"""
    if DataModel.IsValidObj( self.data ) and self.channelDataSet is not None:
      self._OnFindMinMaxChannel( mode, self.channelDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseMotionAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''

    dset = None
    chan_info = self.FindChannel( *ev.GetPosition() )
    if chan_info is not None:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )

    if dset is not None:
      axial_level = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 )
      assy_ndx = self.assemblyAddr[ 0 ]
      chan_factors = None

      if self.nodalMode:
        if self.state.weightsMode == 'on':
          chan_factors = self.data.GetFactors( self.channelDataSet )
        node_addr = chan_info[ 2 ]
	if node_addr < dset.shape[ 1 ] and assy_ndx < dset.shape[ 3 ]:
	  chan_factor = 1
	  if chan_factors is not None:
	    chan_factor = chan_factors[ 0, node_addr, axial_level, assy_ndx ]
          chan_value = dset[ 0, node_addr, axial_level, assy_ndx ]
	  if not ( self.data.IsBadValue( chan_value ) or chan_factor == 0 ):
            tip_str = 'Node: %d\n%s: %g' % \
		( node_addr + 1, self.channelDataSet, chan_value )
	#end if node_addr and assy_ndx valid

      else:
        if self.state.weightsMode == 'on':
          chan_factors = self.data.GetFactors( self.channelDataSet )
        chan_addr = chan_info[ 0 : 2 ]
        if chan_addr[ 1 ] < dset.shape[ 0 ] and \
	    chan_addr[ 0 ] < dset.shape[ 1 ] and \
	    assy_ndx < dset.shape[ 3 ]:
	  chan_factor = 1
	  if chan_factors is not None:
	    chan_factor = chan_factors[
	        chan_addr[ 1 ], chan_addr[ 0 ],
		axial_level, assy_ndx
		]
          chan_value = \
	      dset[ chan_addr[ 1 ], chan_addr[ 0 ], axial_level, assy_ndx ]
	  if not ( self.data.IsBadValue( chan_value ) or chan_factor == 0 ):
	    chan_rc = ( chan_addr[ 0 ] + 1, chan_addr[ 1 ] + 1 )
            tip_str = 'Pin: %s\n%s: %g' % \
	        ( str( chan_rc ), self.channelDataSet, chan_value )
      #end if-else nodalMode
    #end if dset

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseMotionAssy_old()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy_old( self, ev ):
    """
"""
    tip_str = ''
    chan_addr = self.FindChannel( *ev.GetPosition() )
    if chan_addr is not None:
      state_ndx = self.stateIndex
      ds_name = self.channelDataSet
      chan_value = 0.0
#      if ds_name in self.data.states[ state_ndx ].group:
#        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
      dset = self.data.GetStateDataSet( state_ndx, ds_name )
      if dset is not None:
        dset_array = dset.value
	if chan_addr[ 1 ] < dset_array.shape[ 0 ] and \
	    chan_addr[ 0 ] < dset_array.shape[ 1 ] and \
	    self.assemblyAddr[ 0 ] < dset_array.shape[ 3 ]:
	  chan_value = dset_array[
	      chan_addr[ 1 ], chan_addr[ 0 ],
	      min( self.axialValue[ 1 ], dset_array.shape[ 2 ] - 1 ),
	      self.assemblyAddr[ 0 ]
	      ]
#	    self.axialBean.axialLevel, self.assemblyAddr

      #if chan_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, chan_value ):
	chan_rc = ( chan_addr[ 0 ] + 1, chan_addr[ 1 ] + 1 )
        tip_str = 'Channel: %s\n%s: %g' % ( str( chan_rc ), ds_name, chan_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy_old


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    chan_info = self.FindChannel( *ev.GetPosition() )
    if chan_info is None:
      pass

    elif self.nodalMode:
      node_addr = chan_info[ 2 ]
      valid = self.data.IsValid( node_addr = node_addr )
      if valid:
        is_aux = self.IsAuxiliaryEvent( ev )
	if is_aux:
	  addrs = list( self.auxNodeAddrs )
	  if node_addr in addrs:
	    addrs.remove( node_addr )
	  else:
	    addrs.append( node_addr )
	  self.FireStateChange( aux_node_addrs = addrs )
	else:
          self.FireStateChange( node_addr = node_addr, aux_node_addrs = [] )
      #end if valid

    else:
      chan_addr = chan_info[ 0 : 2 ]
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )
      if dset is not None:
        axial_level = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 )
        assy_ndx = self.assemblyAddr[ 0 ]
        if chan_addr[ 1 ] < dset.shape[ 0 ] and \
	    chan_addr[ 0 ] < dset.shape[ 1 ] and \
	    assy_ndx < dset.shape[ 3 ]:
          chan_value = \
	      dset[ chan_addr[ 1 ], chan_addr[ 0 ], axial_level, assy_ndx ]
	  if not self.data.IsBadValue( chan_value ):
	    self.FireStateChange( sub_addr = chan_addr )
      #end if dset
    #end if-else
  #end _OnMouseUpAssy


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseUpAssy_old()		-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy_old( self, ev ):
    """
"""
    chan_addr = self.FindChannel( *ev.GetPosition() )
    if chan_addr is not None and chan_addr != self.subAddr:
      state_ndx = self.stateIndex
      ds_name = self.channelDataSet
      chan_value = 0.0
#      if ds_name in self.data.states[ state_ndx ].group:
#        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
      dset = self.data.GetStateDataSet( state_ndx, ds_name )
      if dset is not None:
        dset_array = dset.value
	if chan_addr[ 1 ] < dset_array.shape[ 0 ] and \
	    chan_addr[ 0 ] < dset_array.shape[ 1 ] and \
	    self.assemblyAddr[ 0 ] < dset_array.shape[ 3 ]:
	  chan_value = dset_array[
	      chan_addr[ 1 ], chan_addr[ 0 ],
	      min( self.axialValue[ 1 ], dset_array.shape[ 2 ] - 1 ),
	      self.assemblyAddr[ 0 ]
	      ]
#	    self.axialBean.axialLevel, self.assemblyAddr

      #if chan_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, chan_value ):
	self.FireStateChange( sub_addr = chan_addr )
    #end if chan_addr changed
  #end _OnMouseUpAssy_old


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._SetMode( 'core' )
      self.Redraw()  # self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Channel2DView, self ).SaveProps( props_dict )

    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'mode', 'nodeAddr', 'subAddr' ):
      props_dict[ k ] = getattr( self, k )

    if self.data is not None:
      for k in ( 'channelDataSet', ):
        props_dict[ k ] = self.data.RevertIfDerivedDataSet( getattr( self, k ) )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.channelDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = ds_name )
      self.FireStateChange( cur_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._SetMode()			-
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

	super( Channel2DView, self )._InitEventHandlers()
      #end if-else

      self.mode = mode
    #end if different mode
  #end _SetMode


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Channel2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.data.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
        changed = True
	self.auxNodeAddrs = aux_node_addrs

    if 'cur_dataset' in kwargs and \
        kwargs[ 'cur_dataset' ] != self.channelDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.channelDataSet = kwargs[ 'cur_dataset' ]
	self.container.GetDataSetMenu().Reset()

    if 'node_addr' in kwargs:
      node_addr = self.data.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        changed = True
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.data.NormalizeSubAddr( kwargs[ 'sub_addr' ], 'channel' )
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

#end Channel2DView
