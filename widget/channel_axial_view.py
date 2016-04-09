#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		channel_axial_view.py				-
#	HISTORY:							-
#		2016-04-09	leerw@ornl.gov				-
#	  Starting with core_axial_view.py.
#------------------------------------------------------------------------
import math, os, sys, threading, time, timeit, traceback
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
  raise ImportError, 'The Python Imaging Library (PIL) is required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.datamodel import *
from event.state import *
from legend import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		ChannelAxial2DView				-
#------------------------------------------------------------------------
class ChannelAxial2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.channelColRow = None
    self.channelDataSet = kwargs.get( 'dataset', 'channel_liquid_temps [C]' )

    self.mode = kwargs.get( 'mode', 'xz' )  # 'xz' and 'yz'

    self.toolButtonDefs = [ ( 'X_16x16', 'Toggle Slice Axis', self._OnMode ) ]

    super( ChannelAxial2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateClipboardAllData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardAllData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      #axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      if self.mode == 'xz':
	assy_row = self.assemblyIndex[ 2 ]
	chan_row = self.channelColRow[ 1 ]
	chan_count = dset_shape[ 0 ]
      else:
	assy_col = self.assemblyIndex[ 1 ]
	chan_col = self.channelColRow[ 0 ]
	chan_count = dset_shape[ 1 ]

      clip_shape = (
          self.cellRange[ -1 ],
	  (chan_count * self.cellRange[ -2 ]) + 1
	  )
      clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      clip_data.fill( 0.0 )

      #for ax in range( self.cellRange[ -1 ] ):
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
	#ax_offset = ax - self.cellRange[ 1 ]
	ax_offset = self.cellRange[ 3 ] - 1 - ax
	clip_data[ ax_offset, 0 ] = self.data.core.axialMeshCenters[ ax ]

	chan_cell = 1
        for assy_cell in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  chan_cell_to = chan_cell + chan_count
	  if self.mode == 'xz':
	    assy_ndx = self.data.core.coreMap[ assy_row, assy_cell ] - 1
	    if assy_ndx >= 0:
	      clip_data[ ax_offset, chan_cell : chan_cell_to ] = \
	        dset_value[ chan_row, :, ax, assy_ndx ]

	  else:
	    assy_ndx = self.data.core.coreMap[ assy_cell, assy_col ] - 1
	    if assy_ndx >= 0:
	      clip_data[ ax_offset, chan_cell : chan_cell_to ] = \
	        dset_value[ :, chan_col, ax, assy_ndx ]

	  chan_cell = chan_cell_to
        #end for assy_cel
      #end for axials

      if self.mode == 'xz':
        title1 = '"%s: Assy Row=%s; Chan Row=%d; %s=%.3g"' % (
	    self.channelDataSet,
            self.data.core.coreLabels[ 1 ][ assy_row ],
	    chan_row + 1,
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )
        col_labels = [
            self.data.core.coreLabels[ 0 ][ i ]
	    for i in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )
            ]
        title2 = '"Axial; Cols=%s"' % ':'.join( col_labels )

      else:
        title1 = '"%s: Assy Col=%s; Pin Col=%d; %s=%.3g"' % (
	    self.channelDataSet,
            self.data.core.coreLabels[ 0 ][ assy_col ],
	    chan_col + 1,
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	    )
        row_labels = [
            self.data.core.coreLabels[ 1 ][ i ]
	    for i in range( self.cellRange[ 0 ], self.cellRange[ 2 ] )
            ]
        title2 = '"Axial; Rows=%s"' % ':'.join( row_labels )
      #end if-else

#		-- Write with axial mesh centers
#		--
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardAllData


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateClipboardData()	-
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
  #	METHOD:	ChannelAxial2DView._CreateClipboardSelectionData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectionData( self ):
    """Retrieves the data for the state, axial, and assembly.
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

      if self.mode == 'xz':
	chan_row = self.channelColRow[ 1 ]
	clip_data = dset_value[ chan_row, :, axial_level, assy_ndx ]
	chan_title = 'Chan Row=%d' % (chan_row + 1)

      else:
	chan_col = self.channelColRow[ 0 ]
	clip_data = dset_value[ :, chan_col, axial_level, assy_ndx ]
	chan_title = 'Chan Col=%d' % (chan_col + 1)

      title = '"%s: Assembly=%d %s; %s; Axial=%.3f; %s=%.3g"' % (
	  self.channelDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] ),
	  chan_title,
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectionData


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per channel) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per cm
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
    assemblyWidth
    axialLevelsDy	list of pixel offsets in y dimension
    axialPixPerCm	used?
    channelWidth
    coreRegion
    lineWidth
"""
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.channelDataSet ),
	**kwargs
	)

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

    axial_mesh = self.data.core.axialMesh
    axial_range_cm = \
        axial_mesh[ self.cellRange[ 3 ] ] - axial_mesh[ self.cellRange[ 1 ] ]
    npin = \
        self.data.core.npinx  if self.mode == 'xz' else \
	self.data.core.npiny

    # pin equivalents in the axial range
    cm_per_pin = self.data.core.GetAssemblyPitch() / npin
    axial_pin_equivs = axial_range_cm / cm_per_pin
    core_aspect_ratio = \
        self.data.core.GetAssemblyPitch() * self.cellRange[ -2 ] / \
	axial_range_cm
    #core_aspect_ratio = (self.cellRange[ -2 ] * npin) / axial_pin_equivs

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

#			-- Determine drawable region in image
#			--
      # l2r, label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      # t2b, core : title
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)

      #axial_pix_per_cm = region_ht / axial_range_cm

      region_aspect_ratio = float( region_wd ) / float( region_ht )
      fmt_str = \
          '[ChannelAxial2DView._CreateDrawConfig]' + \
	  '\n  region=%d,%d' + \
	  '\n  region_aspect_ratio=%f' + \
	  '\n  cm_per_pin=%f' + \
	  '\n  axial_pin_equivs=%f' + \
	  '\n  core_aspect_ratio=%f'
      print >> sys.stderr, fmt_str % (
	  region_wd, region_ht, region_aspect_ratio,
	  cm_per_pin, axial_pin_equivs, core_aspect_ratio
	  )

#				-- Limited by height
      if region_aspect_ratio > core_aspect_ratio:
	chan_wd = max( 1, int( math.floor( region_ht / axial_pin_equivs ) ) )

#				-- Limited by width
      else:
        assy_wd = region_wd / self.cellRange[ -2 ]
        chan_wd = max( 1, (assy_wd - 2) / (npin + 1) )

      assy_wd = chan_wd * (npin + 1) + 1
      axial_pix_per_cm = chan_wd / cm_per_pin

      print >> sys.stderr, \
          '[ChannelAxial2DView._CreateDrawConfig] after scale' + \
	  '\n  assy_wd=%d, chan_wd=%d\n  axial_pix_per_cm=%f' % \
	  ( assy_wd, chan_wd, axial_pix_per_cm )

#			-- Calc sizes
#			--
      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

#		-- Or, scale set explicitly
#		--
    else:
      chan_wd = kwargs.get( 'scale', 4 )
      axial_pix_per_cm = chan_wd / cm_per_pin

      assy_wd = chan_wd * (npin + 1) + 1
      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

      font_size = self._CalcFontSize( 768 )

      # l2r, label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    axials_dy = []
    for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
      ax_cm = axial_mesh[ ax + 1 ] - axial_mesh[ ax ]
      dy = max( 1, int( math.floor( axial_pix_per_cm * ax_cm ) ) )
      axials_dy.insert( 0, dy )
    #end for

    config[ 'assemblyWidth' ] = assy_wd
    config[ 'axialLevelsDy' ] = axials_dy
    config[ 'axialPixPerCm' ] = axial_pix_per_cm
    config[ 'channelWidth' ] = chan_wd
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateMenuDef()		-
  #----------------------------------------------------------------------
#  def _CreateMenuDef( self, data_model ):
#    """
#"""
#    menu_def = super( ChannelAxial2DView, self )._CreateMenuDef( data_model )
#    other_def = \
#      [
#        ( 'Select Average Dataset...', self._OnSelectAverageDataSet ),
#	( '-', None )
#      ]
#    return  other_def + menu_def
#  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_col_or_row, pin_col_or_row )
@param  config		optional config to use instead of self.config
"""
    start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    print >> sys.stderr, \
        '[ChannelAxial2DView._CreateRasterImage] tuple_in=%s' % \
	str( tuple_in )
    im = None

    if config is None:
      config = self.config
    if config is not None:
      assy_wd = config[ 'assemblyWidth' ]
      axial_levels_dy = config[ 'axialLevelsDy' ]
      im_wd, im_ht = config[ 'clientSize' ]
      chan_wd = config[ 'channelWidth' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]

      dset = self.data.GetStateDataSet( state_ndx, self.channelDataSet )

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
      ds_range = self.data.GetRange( self.channelDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      if self.mode == 'xz':
	chan_cell = min( tuple_in[ 2 ], dset_shape[ 0 ] - 1 )
	cur_nchan = min( self.data.core.npinx + 1, dset_shape[ 1 ] )
	chan_range = range( self.data.core.npinx + 1 )
	addresses = 'Assy Row %s, Chan Row %d' % \
	    ( self.data.core.coreLabels[ 1 ][ tuple_in[ 1 ] ], chan_cell + 1 )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	    additional = addresses
	    )
      else: # 'yz'
	chan_cell = min( tuple_in[ 2 ], dset_shape[ 1 ] - 1 )
	cur_nchan = min( self.data.core.npiny + 1, dset_shape[ 0 ] )
	chan_range = range( self.data.core.npiny + 1 )
	addresses = 'Assy Col %s, Chan Col %d' % \
	    ( self.data.core.coreLabels[ 0 ][ tuple_in[ 1 ] ], chan_cell + 1 )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.channelDataSet, dset_shape, self.state.timeDataSet,
	    additional = addresses
	    )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )

#			-- Loop on axial levels
#			--
      last_axial_label_y = 0;
      axial_y = core_region[ 1 ]
#      for axial_level in \
#          range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
#        cur_dy = axial_levels_dy[ axial_level - self.cellRange[ 1 ] ]
      for ax in range( len( axial_levels_dy ) - 1, -1, -1 ):
        cur_dy = axial_levels_dy[ ax ]
	axial_level = ax + self.cellRange[ 1 ]

#				-- Row label
#				--
	if self.showLabels:
	  label = '%02d' % (axial_level + 1)
	  label_size = pil_font.getsize( label )
	  label_y = axial_y + ((cur_dy - label_size[ 1 ]) >> 1)
	  if last_axial_label_y  + label_size[ 1 ] < axial_y + cur_dy:
	    im_draw.text(
	        ( 1, label_y ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	    last_axial_label_y = label_y

#				-- Loop on col
#				--
	assy_x = core_region[ 0 ]
	for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  #if axial_level == self.cellRange[ 3 ] - 1 and self.showLabels:
	  if ax == len( axial_levels_dy ) - 1 and self.showLabels:
	    label_ndx = 0 if self.mode == 'xz' else 1
	    label = self.data.core.coreLabels[ label_ndx ][ assy_col ]
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if

	  if self.mode == 'xz':
	    assy_ndx = self.data.core.coreMap[ tuple_in[ 1 ], assy_col ] - 1
	  else:
	    assy_ndx = self.data.core.coreMap[ assy_col, tuple_in[ 1 ] ] - 1

	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    chan_x = assy_x + 1

	    for chan_col in chan_range:
	      cur_chan_col = min( chan_col, cur_nchan - 1 )
	      if self.mode == 'xz':
	        value = dset_array[
		    chan_cell, cur_chan_col, axial_level, assy_ndx
		    ]
	      else:
	        value = dset_array[
		    cur_chan_col, chan_cell, axial_level, assy_ndx
		    ]

	      if not self.data.IsNoDataValue( self.channelDataSet, value ):
	        chan_color = Widget.GetColorTuple(
	            value - ds_range[ 0 ], value_delta, 255
	            )
	        brush_color = \
		    ( chan_color[ 0 ], chan_color[ 1 ], chan_color[ 2 ], 255 )
	        im_draw.rectangle(
		    [ chan_x, axial_y,
		      chan_x + chan_wd + 1, axial_y + cur_dy + 1 ],
		    fill = brush_color, outline = chan_color
		    )
	      #end if valid value
	      chan_x += chan_wd
	    #end for pin cols

	    im_draw.rectangle(
		[ assy_x, axial_y, assy_x + assy_wd, axial_y + cur_dy ],
		fill = None, outline = assy_pen
	        )
	  #end if assembly referenced

	  assy_x += assy_wd
	#end for assy_col

	axial_y += cur_dy
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
      axial_y = max( axial_y, legend_size[ 1 ] )
      axial_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
#(core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, axial_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists
    elapsed_time = timeit.default_timer() - start_time
    print >> sys.stderr, \
        '\n[ChannelAxial2DView._CreateRasterImage] time=%.3fs, im-None=%s' % \
	( elapsed_time, im is None )

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return  ( state_index, pin_offset )
"""
#    colrow_ndx = 1 if self.mode == 'xz' else 0
#    return  ( self.stateIndex, self.pinColRow[ colrow_ndx ] )
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyIndex[ 2 ], self.channelColRow[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyIndex[ 1 ], self.channelColRow[ 0 ] )
    return  t
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = cell_info is not None and \
        self.data.IsValid(
            assembly_index = cell_info[ 0 ],
	    axial_level = cell_info[ 2 ],
	    state_index = self.stateIndex
	    )

    if valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.channelDataSet )
      assy_ndx = cell_info[ 0 ]
      if dset is not None and assy_ndx < dset.shape[ 3 ]:
        if self.mode == 'xz':
	  assy_addr = ( cell_info[ 1 ], self.assemblyIndex[ 2 ] )
	else:
	  assy_addr = ( self.assemblyIndex[ 1 ], cell_info[ 1 ] )

        show_assy_addr = self.data.core.CreateAssyLabel( *assy_addr )
        tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )

	if cell_info[ 2 ] >= 0:
	  axial_value = self.data.CreateAxialValue( core_ndx = cell_info[ 2 ] )
	  tip_str += ', Axial: %.2f' % axial_value[ 0 ]
	#end if
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return  ( assy_ndx, assy_col_or_row, axial_level, chan_col_or_row )
"""
    result = None
    if self.config is not None and self.data is not None and \
        self.data.core is not None and self.data.core.coreMap is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axials_dy = self.config[ 'axialLevelsDy' ]
      core_region = self.config[ 'coreRegion' ]
      chan_wd = self.config[ 'channelWidth' ]

      off_x = ev_x - core_region[ 0 ]
      off_y = ev_y - core_region[ 1 ]

      if self.mode == 'xz':
	assy_row = self.assemblyIndex[ 2 ]
        assy_col = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        assy_col = max( self.cellRange[ 0 ], assy_col )
	assy_col_or_row = assy_col

	chan_col_or_row = int( (off_x % assy_wd) / chan_wd )
	if chan_col_or_row >= self.data.core.npinx + 1: chan_col_or_row = -1

      else:
        assy_col = self.assemblyIndex[ 1 ]
	assy_row = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	assy_row = max( self.cellRange[ 0 ], assy_row )
	assy_col_or_row = assy_row

	chan_col_or_row = int( (off_x % assy_wd) / chan_wd )
	if chan_col_or_row >= self.data.core.npiny: chan_col_or_row = -1
      #end if-else

      axial_level = 0
      ax_y = 0
      for ax in range( len( axials_dy ) - 1, -1, -1 ):
        ax_y += axials_dy[ ax ]
	if off_y <= ax_y:
	  axial_level = ax + self.cellRange[ 1 ]
	  break
      #end for

      assy_ndx = self.data.core.coreMap[ assy_row, assy_col ] - 1
      result = ( assy_ndx, assy_col_or_row, axial_level, chan_col_or_row )
    #end if we have data

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.FindCellAll()		-
  #----------------------------------------------------------------------
  def FindCellAll( self, ev_x, ev_y ):
    """Not used.
@return  ( assy_ndx, assy_col, assy_row, chan_col, chan_row, axial_level )
"""
    result = None
    if self.config is not None and self.data is not None and \
        self.data.core is not None and self.data.core.coreMap is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axials_dy = self.config[ 'axialLevelsDy' ]
      core_region = self.config[ 'coreRegion' ]
      chan_wd = self.config[ 'channelWidth' ]

      off_x = ev_x - core_region[ 0 ]
      off_y = ev_y - core_region[ 1 ]

      if self.mode == 'xz':
	assy_row = self.assemblyIndex[ 2 ]
        chan_row = self.pinColRow[ 1 ]
        assy_col = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        assy_col = max( self.cellRange[ 0 ], assy_col )
	chan_col = int( (off_x % assy_wd) / chan_wd )
	if chan_col >= self.data.core.npinx: chan_col = -1

      else:
        assy_col = self.assemblyIndex[ 1 ]
	chan_col = self.pinColRow[ 0 ]
	assy_row = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	assy_row = max( self.cellRange[ 0 ], assy_row )
	chan_row = int( (off_x % assy_wd) / chan_wd )
	if chan_row >= self.data.core.npiny: chan_row = -1

      axial_level = 0
      ax_y = 0
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
	ax_y += axials_dy[ ax ]
        if off_y <= ax_y:
	  axial_level = ax
	  break
      #end for

      assy_ndx = self.data.core.coreMap[ assy_row, assy_col ] - 1
      result = ( assy_ndx, assy_col, assy_row, chan_col, chan_row, axial_level )
    #end if we have data

    return  result
  #end FindCellAll


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetAnimationIndexes()	-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'channel' ]
    #return  [ 'pin', 'pin:assembly', 'pin:axial' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetEventLockSet()		-
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
  #	METHOD:		ChannelAxial2DView.GetInitialCellRange()	-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """Creates the range using y for the axial.
@return			( xy-left, z-bottom, xy-right, z-top, d-xy, dz )
"""
    if self.data is None:
      result = ( 0, 0, 0, 0, 0, 0 )

    else:
      result = list( self.data.ExtractSymmetryExtent() )
      if self.mode == 'yz':
        result[ 0 ] = result[ 1 ]
	result[ 2 ] = result[ 3 ]
	result[ 4 ] = result[ 5 ]

      result[ 1 ] = 0
      result[ 3 ] = result[ 5 ] = self.data.core.nax

    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetMode()			-
  #----------------------------------------------------------------------
  def GetMode( self ):
    """
"""
    return  self.mode
  #end GetMode


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetPrintScale()		-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		8
"""
    return  4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self, data_model ):
    """
"""
    return  self.toolButtonDefs
  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Channel Axial 2D View'
    #mode_str = 'XZ' if self.mode == 'xz' else 'YZ'
    #return  'Core Axial ' + mode_str + ' View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._HiliteBitmap()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    #return  bmap
    result = bmap

    if self.config is not None:
      line_wd = -1
      rect = None

      rel_axial = self.axialValue[ 1 ] - self.cellRange[ 1 ]

      if self.mode == 'xz':
        rel_cell = self.assemblyIndex[ 1 ] - self.cellRange[ 0 ]
      else:
        rel_cell = self.assemblyIndex[ 2 ] - self.cellRange[ 0 ]

      if rel_cell >= 0 and rel_cell < self.cellRange[ -2 ] and \
          rel_axial >= 0 and rel_axial < self.cellRange[ -1 ]:
        assy_wd = self.config[ 'assemblyWidth' ]
        axial_levels_dy = self.config[ 'axialLevelsDy' ]
	core_region = self.config[ 'coreRegion' ]
	line_wd = self.config[ 'lineWidth' ]
        #chan_wd = self.config[ 'channelWidth' ]

        axial_y = core_region[ 1 ]
        for ax in range( len( axial_levels_dy ) - 1, rel_axial, -1 ):
	  axial_y += axial_levels_dy[ ax ]

	rect = [
	    rel_cell * assy_wd + core_region[ 0 ], axial_y,
	    assy_wd, axial_levels_dy[ rel_axial ]
	    ]
      #end if selection w/in image

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
    #end if self.config

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyIndex[ 2 ], self.channelColRow[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyIndex[ 1 ], self.channelColRow[ 0 ] )
    return  tpl == t
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._LoadDataModelValues()	-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    self.assemblyIndex = self.state.assemblyIndex
    self.channelDataSet = self.state.channelDataSet
    self.channelColRow = self.state.channelColRow

    if self.mode == 'xz':
      self.channelOffset = \
          self.assemblyIndex[ 2 ] * (self.data.core.npiny + 1) + \
	  self.channelColRow[ 1 ]
    else:
      self.channelOffset = \
          self.assemblyIndex[ 1 ] * (self.data.core.npinx + 1) + \
	  self.channelColRow[ 0 ]
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindCell( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}

      if self.mode == 'xz':
	assy_ndx = ( cell_info[ 0 ], cell_info[ 1 ], self.assemblyIndex[ 2 ] )
	chan_addr = ( cell_info[ 3 ], self.channelColRow[ 1 ] )
      else:
	assy_ndx = ( cell_info[ 0 ], self.assemblyIndex[ 1 ], cell_info[ 1 ] )
	chan_addr = ( self.channelColRow[ 0 ], cell_info[ 3 ] )

      if assy_ndx != self.assemblyIndex:
	state_args[ 'assembly_index' ] = assy_ndx

      if chan_addr != self.channelColRow:
	state_args[ 'channel_colrow' ] = chan_addr

      axial_level = cell_info[ 2 ]
      if axial_level != self.axialValue[ 1 ]:
        state_args[ 'axial_value' ] = \
	    self.data.CreateAxialValue( core_ndx = axial_level )

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._OnDragFinished()		-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    pass
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._OnFindMax()			-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Calls _OnFindMaxPin().
"""
    if DataModel.IsValidObj( self.data ) and self.channelDataSet is not None:
      self._OnFindMaxChannel( self.channelDataSet, all_states_flag )
  #end _OnFindMax


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._OnMode()			-
  #----------------------------------------------------------------------
  def _OnMode( self, ev ):
    """Must be called from the event thread.
"""
    new_mode = 'xz' if self.mode == 'yz' else 'yz'
    button = ev.GetEventObject()
    self.SetMode( new_mode, button )
  #end _OnMode


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self.Redraw()
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.channelDataSet:
      wx.CallAfter( self.UpdateState, channel_dataset = ds_name )
      self.FireStateChange( channel_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.SetMode()			-
  #----------------------------------------------------------------------
  def SetMode( self, mode, button = None ):
    """May be called from any thread.
@param  mode		either 'xz' or 'yz', defaulting to the former on
			any other value
@param  button		optional button to update
"""
    if mode != self.mode:
      self.mode = 'yz' if mode == 'yz' else 'xz'
      self.cellRange = list( self.GetInitialCellRange() )
      del self.cellRangeStack[ : ]

      wx.CallAfter( self._SetModeImpl, button )
  #end SetMode


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._SetModeImpl()		-
  #----------------------------------------------------------------------
  def _SetModeImpl( self, button = None ):
    """Must be called from the event thread.
@param  mode		mode, already setjdd
			any other value
@param  button		optional button to update
"""
    if button is None:
      for ch in self.GetParent().GetControlPanel().GetChildren():
        if isinstance( ch, wx.BitmapButton ) and \
	    ch.GetToolTip().GetTip().find( 'Toggle Slice' ) >= 0:
          button = ch
	  break
    #end if

    if button is not None:
      if self.mode == 'yz':
        bmap = Widget.GetBitmap( 'Y_16x16' )
      else:
        bmap = Widget.GetBitmap( 'X_16x16' )
      button.SetBitmapLabel( bmap )
      button.Update()
      self.GetParent().GetControlPanel().Layout()
    #end if

    self.Redraw()
  #end _SetModeImpl


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( ChannelAxial2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    new_chan_index_flag = False
    if self.mode == 'xz':
      assy_ndx = 2
      chan_ndx = 1
      npin = self.data.core.npiny + 1
    else:
      assy_ndx = 1
      chan_ndx = 0
      npin = self.data.core.npinx + 1
    #if 'assembly_index' in kwargs:
      #self._stopme_ = True

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      #changed = True
      if kwargs[ 'assembly_index' ][ assy_ndx ] != self.assemblyIndex[ assy_ndx ]:
        resized = True
	new_chan_index_flag = True
      else:
        changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

#    if 'avg_dataset' in kwargs and kwargs[ 'avg_dataset' ] != self.avgDataSet:
#      changed = True
#      self.avgDataSet = kwargs[ 'avg_dataset' ]
#      if self.avgDataSet == '':
#        self.avgDataSet = None

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] != self.channelColRow:
      #changed = True
      if kwargs[ 'channel_colrow' ][ chan_ndx ] != self.channelColRow[ chan_ndx ]:
        resized = True
	new_chan_index_flag = True
      else:
        changed = True
      self.channelColRow = \
          self.data.NormalizeChannelColRow( kwargs[ 'channel_colrow' ] )

    if 'channel_dataset' in kwargs and kwargs[ 'channel_dataset' ] != self.channelDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'channel_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.channelDataSet = kwargs[ 'channel_dataset' ]

    if new_chan_index_flag:
      self.channelOffset = \
          self.assemblyIndex[ assy_ndx ] * (npin + 1) + \
	  self.channelColRow[ chan_ndx ]
    #end if new_pin_index_flag

#    if (changed or resized) and self.config is not None:
#      self._UpdateAvgValues( self.stateIndex )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end ChannelAxial2DView


#------------------------------------------------------------------------
#	CLASS:		ChannelXZView					-
#------------------------------------------------------------------------
class ChannelXZView( ChannelAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( ChannelXZView, self ).__init__( container, id, mode = 'xz' )
  #end __init__
#end ChannelXZView


#------------------------------------------------------------------------
#	CLASS:		ChannelYZView					-
#------------------------------------------------------------------------
class ChannelYZView( ChannelAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		ChannelAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( ChannelYZView, self ).__init__( container, id, mode = 'yz' )
  #end __init__
#end ChannelYZView
