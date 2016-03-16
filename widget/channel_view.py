#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		channel_view.py					-
#	HISTORY:							-
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
import math, os, sys, threading, time, traceback
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
    self.assemblyIndex = ( -1, -1, -1 )
    self.channelColRow = None
    self.channelDataSet = kwargs.get( 'dataset', 'channel_liquid_temps [C]' )
    self.mode = ''

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
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.channelDataSet ),
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
      print >> sys.stderr, \
          '[Assembly2DView._CreateDrawConfig] size=%d,%d' % ( wd, ht )

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
      print >> sys.stderr, '[Assembly2DView._CreateDrawConfig] chan_wd=%d' % chan_wd

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
  def _CreateAssyImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    print >> sys.stderr, \
        '[Channel2DView._CreateAssyImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    if self.config is not None and tuple_valid:
#			-- Draw channel "cells"
#			--
      assy_region = self.config[ 'assemblyRegion' ]
      chan_gap = self.config[ 'channelGap' ]
      chan_wd = self.config[ 'channelWidth' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]

      dset = self.data.GetStateDataSet( state_ndx, self.channelDataSet )
      #dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
      #ds_value = dset.value if dset is not None else None
      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
      ds_range = self.data.GetRange( self.channelDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )

      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      chan_y = assy_region[ 1 ]
      for chan_row in range( self.data.core.npin + 1 ):
#				-- Row label
#				--
	if self.showLabels and chan_row < self.data.core.npin:
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
	for chan_col in range( self.data.core.npin + 1 ):
#					-- Column label
#					--
	  if chan_row == 0 and self.showLabels and chan_col < self.data.core.npin:
	    label = '%d' % (chan_col + 1)
	    label_size = label_font.getsize( label )
	    #label_x = chan_x + ((chan_wd - label_size[ 0 ]) >> 1)
	    label_x = chan_x + chan_wd + ((chan_gap - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ), label,
		fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

#	  value = 0.0
#	  if ds_value is not None:
#	    #DataModel.GetPinIndex( assy_ndx, axial_level, chan_col, chan_row )
#	    value = ds_value[ chan_row, chan_col, axial_level, assy_ndx ]
	  value = dset_array[ chan_row, chan_col, axial_level, assy_ndx ]
	  #if value > 0.0:
	  if not self.data.IsNoDataValue( self.channelDataSet, value ):
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
#      im.paste( legend_pil_im, ( assy_wd + font_size, 1 ) )
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 2 ] + 2 + font_size, assy_region[ 1 ] )
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
	  0,
          (assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, chan_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateAssyImage


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardAllData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardAllData( self, cur_selection_flag = False ):
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
      col_labels = [
          self.data.core.coreLabels[ 0 ][ i ]
	  for i in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )
          ]
      row_labels = [
          self.data.core.coreLabels[ 1 ][ i ]
	  for i in range( self.cellRange[ 1 ], self.cellRange[ 3 ] )
	  ]
      title2 = 'Cols=%s; Rows=%s' % (
	  ':'.join( col_labels ),
	  ':'.join( row_labels )
          )
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardAllData


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardSelectionData() \
        if cur_selection_flag else \
        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateClipboardSelectionData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectionData( self, cur_selection_flag = False ):
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
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyIndex[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%d; Axial=%.3f; %s=%.3g"' % (
	  self.channelDataSet,
	  assy_ndx + 1,
	  self.axialValue[ 0 ],
	  #self.data.core.axialMeshCenters[ axial_level ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectionData



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
"""
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.channelDataSet ),
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
      print >> sys.stderr, '[Channel2DView._CreateCoreDrawConfig] chan_wd=%d' % chan_wd
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

    config[ 'assemblyAdvance' ] = assy_advance
    config[ 'assemblyWidth' ] = assy_wd
    config[ 'channelWidth' ] = chan_wd
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'mode' ] = 'core'

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._CreateCoreImage()		-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    print >> sys.stderr, \
        '[Channel2DView._CreateCoreImage] tuple_in=%d,%d' % \
	( state_ndx, axial_level )
    im = None

    if self.config is not None:
      assy_advance = self.config[ 'assemblyAdvance' ]
      assy_wd = self.config[ 'assemblyWidth' ]
      chan_wd = self.config[ 'channelWidth' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      core_region = self.config[ 'coreRegion' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]

      dset = self.data.GetStateDataSet( state_ndx, self.channelDataSet )
      #dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
      #ds_value = dset.value if dset is not None else None
      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
      ds_range = self.data.GetRange( self.channelDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	  axial_ndx = 2
	  )

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
	  label = self.data.core.coreLabels[ 1 ][ assy_row ]
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
#					-- Column label
#					--
	  if assy_row == self.cellRange[ 1 ] and self.showLabels:
	    label = self.data.core.coreLabels[ 0 ][ assy_col ]
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
	    cur_nypin = min( self.data.core.npin + 1, dset_shape[ 0 ] )
	    cur_nxpin = min( self.data.core.npin + 1, dset_shape[ 1 ] )

	    #for chan_row in range( self.data.core.npin + 1 ):
	    for chan_row in range( cur_nypin ):
	      chan_x = assy_x + 1
	      #for chan_col in range( self.data.core.npin + 1 ):
	      for chan_col in range( cur_nxpin ):
#		value = 0.0
#	        if ds_value is not None:
#		  #DataModel.GetPinIndex( assy_ndx, axial_level, chan_col, chan_row )
#		  value = ds_value[ chan_row, chan_col, axial_level, assy_ndx ]
		value = dset_array[ chan_row, chan_col, axial_level, assy_ndx ]
		#if value > 0.0:
	        if not self.data.IsNoDataValue( self.channelDataSet, value ):
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
		#end if value gt 0
	        chan_x += chan_wd
	      #end for chan cols

	      chan_y += chan_wd
	    #end for chan rows

	    im_draw.rectangle(
		[ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
		fill = None, outline = assy_pen
	        )
	  #end if assembly referenced

	  assy_x += assy_advance
	#end for assy_col

        assy_y += assy_advance
      #end for assy_row

#			-- Draw Legend Image
#			--
      if legend_pil_im is not None:
        im.paste(
	    legend_pil_im,
	    ( core_region[ 2 ] + 2 + font_size, core_region[ 1 ] )
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
          (core_region[ 3 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, assy_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

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
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
The config and data attributes are good to go.
@param  tuple_in	state tuple
@return			PIL image
"""
    return \
        self._CreateAssyImage( tuple_in ) if self.mode == 'assy' else \
	self._CreateCoreImage( tuple_in )
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
        ( self.stateIndex, self.assemblyIndex[ 0 ], self.axialValue[ 1 ],
	  self.assemblyIndex[ 1 ], self.assemblyIndex[ 2 ] ) \
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
      #xxxx must get this later, like Core2DView
#      avg_value = 0.0
#      show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
#      tip_str = 'Assy: %d %s\n%s %s: %.3g' % \
#          ( cell_info[ 0 ] + 1, show_assy_addr, 'Avg', \
#	    self.channelDataSet, avg_value )
      show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
      tip_str = 'Assy: %d %s\n%s' % \
          ( cell_info[ 0 ] + 1, show_assy_addr,
	    self.data.GetDataSetDisplayName( self.channelDataSet ) )
    #end if

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
			( 0-based index, cell_col, cell_row, chan_col, chan_row )
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
	chan_col = int( (off_x % assy_advance) / chan_wd )
	if chan_col > self.data.core.npin: chan_col = -1
	chan_row = int( (off_y % assy_advance) / chan_wd )
	if chan_row > self.data.core.npin: chan_row = -1

	result = ( assy_ndx, cell_x, cell_y, chan_col, chan_row )
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
			( 0-based cell_col, cell_row )
"""
    result = None

    if self.config is not None and self.data is not None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        chan_size = self.config[ 'channelWidth' ] + self.config[ 'channelGap' ]
        cell_x = min(
	    int( (ev_x - assy_region[ 0 ]) / chan_size ),
	    self.data.core.npin
	    )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / chan_size ),
	    self.data.core.npin
	    )

	result = ( cell_x, cell_y )
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
    return  [ 'channel' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
	STATE_CHANGE_channelColRow, STATE_CHANGE_channelDataSet,
	STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
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
      line_wd = -1
      rect = None

      if self.cellRange[ -2 ] == 1 and self.cellRange[ -1 ] == 1:
        pass

#			-- Core mode
#			--
      elif self.config[ 'mode' ] == 'core':
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
	if self.channelColRow[ 0 ] >= 0 and self.channelColRow[ 1 ] >= 0 and \
	    self.channelColRow[ 0 ] <= self.data.core.npin and \
	    self.channelColRow[ 1 ] <= self.data.core.npin:
          assy_region = self.config[ 'assemblyRegion' ]
	  chan_gap = self.config[ 'channelGap' ]
	  chan_wd = self.config[ 'channelWidth' ]
	  chan_adv = chan_wd + chan_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.channelColRow[ 0 ] * chan_adv + assy_region[ 0 ],
	      self.channelColRow[ 1 ] * chan_adv + assy_region[ 1 ],
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
  #end _HiliteBitmap


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
	  tpl[ 1 ] == self.assemblyIndex[ 0 ] and \
	  tpl[ 2 ] == self.axialValue[ 1 ] and \
	  tpl[ 3 ] == self.assemblyIndex[ 1 ] and \
	  tpl[ 4 ] == self.assemblyIndex[ 2 ]

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
    self.assemblyIndex = self.state.assemblyIndex
    self.channelColRow = self.state.channelColRow
    self.channelDataSet = self.state.channelDataSet
  #end _LoadDataModelValues


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
      assy_ndx = cell_info[ 0 : 3 ]
      if assy_ndx != self.assemblyIndex:
	state_args[ 'assembly_index' ] = assy_ndx

      chan_addr = cell_info[ 3 : 5 ]
      if chan_addr != self.channelColRow:
	state_args[ 'channel_colrow' ] = chan_addr

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
      self.assemblyIndex = self.dragStartCell
      self.FireStateChange( assembly_index = self.assemblyIndex )
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
  #	METHOD:		Channel2DView._OnMouseMotionAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
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
	    self.assemblyIndex[ 0 ] < dset_array.shape[ 3 ]:
	  chan_value = dset_array[
	      chan_addr[ 1 ], chan_addr[ 0 ],
	      min( self.axialValue[ 1 ], dset_array.shape[ 2 ] - 1 ),
	      self.assemblyIndex[ 0 ]
	      ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      #if chan_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, chan_value ):
	chan_rc = ( chan_addr[ 0 ] + 1, chan_addr[ 1 ] + 1 )
        tip_str = 'Channel: %s\n%s: %g' % ( str( chan_rc ), ds_name, chan_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Channel2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    chan_addr = self.FindChannel( *ev.GetPosition() )
    if chan_addr is not None and chan_addr != self.channelColRow:
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
	    self.assemblyIndex[ 0 ] < dset_array.shape[ 3 ]:
	  chan_value = dset_array[
	      chan_addr[ 1 ], chan_addr[ 0 ],
	      min( self.axialValue[ 1 ], dset_array.shape[ 2 ] - 1 ),
	      self.assemblyIndex[ 0 ]
	      ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      #if chan_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, chan_value ):
	self.FireStateChange( channel_colrow = chan_addr )
    #end if chan_addr changed
  #end _OnMouseUpAssy


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
  #	METHOD:		Channel2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.channelDataSet:
      wx.CallAfter( self.UpdateState, channel_dataset = ds_name )
      self.FireStateChange( channel_dataset = ds_name )
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

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] != self.channelColRow:
      changed = True
      self.channelColRow = self.data.NormalizeChannelColRow( kwargs[ 'channel_colrow' ] )

    if 'channel_dataset' in kwargs and kwargs[ 'channel_dataset' ] != self.channelDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'channel_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.channelDataSet = kwargs[ 'channel_dataset' ]

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Channel2DView
