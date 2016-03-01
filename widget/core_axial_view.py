#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_axial_view.py				-
#	HISTORY:							-
#		2016-02-29	leerw@ornl.gov				-
#	  Starting with core_view.py.
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
#	CLASS:		CoreAxial2DView					-
#------------------------------------------------------------------------
class CoreAxial2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    self.avgDataSet = None
    self.avgValues = {}

    self.mode = kwargs.get( 'mode', 'xz' )  # 'xz' and 'yz'
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.pinIndex = 0

    super( CoreAxial2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardAllData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardAllData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    #XXXXX
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

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
	#end for assy cols

	#pin_row += self.core.npiny
	pin_row = pin_row_to
      #end for assy rows

      title1 = '"%s: Axial=%.3f; %s=%.3g"' % (
	  self.pinDataSet,
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
      title2 = '"Cols=%s; Rows=%s"' % (
	  ':'.join( col_labels ),
	  ':'.join( row_labels )
          )
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardAllData


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardData()		-
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
  #	METHOD:		CoreAxial2DView._CreateClipboardSelectionData()	-
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
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyIndex[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      #clip_shape = ( dset_shape[ 0 ], dset_shape[ 1 ] )
      #clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      #clip_data.fill( 0.0 )
      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%d; Axial=%.3f; %s=%.3g"' % (
	  self.pinDataSet,
	  assy_ndx + 1,
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectionData


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
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
    coreRegion
    lineWidth
    pinWidth
"""
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.pinDataSet ),
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

    display_pin_count = self.cellRange[ -2 ] * npin
    pins_per_axial_cm = \
        (self.data.core.GetPitch() * display_pin_count) / axial_range_cm

#    axial_dists_cm = []
#    for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
#      axial_dists_cm.insert( 0, axial_mesh[ ax + 1 ] - axial_mesh[ ax ] )
#    axial_dist_cm_max = np.max( axial_dists_cm )
#    pins_per_axial = self.data.core.GetPitch() / axial_dist_cm_max

#		-- Must calculate scale?
#		--
#		self.cellRange ( xy-left, z-bottom, xy-right, z-top, d-xy, dz )
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

#			-- Determine drawable region in image
#			--
      # l2r, label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      # t2b, core : title
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)

#			-- Calc scale
#			--
#				-- Horizontally
      assy_wd = region_wd / self.cellRange[ -2 ]
      pin_wd = max( 1, (assy_wd - 2) / npin )

#				-- Axially
      #axial_cm_ht = int( math.floor( region_ht / axial_range_cm ) )
      axial_pix_per_cm = region_ht / axial_range_cm
      pin_ht = int( math.floor( axial_pix_per_cm / pins_per_axial_cm ) )

      pixels_per_pin = max( 1, min( pin_wd, pin_ht ) )
      #axial_pix_per_cm = pixels_per_pin * pins_per_axial_cm

#			-- Calc sizes
#			--
      assy_wd = pixels_per_pin * npin + 1
      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

    else:
      pixels_per_pin = y_pix_per_cm = kwargs.get( 'scale', 4 )
      axial_pix_per_cm = pixels_per_pin * pins_per_axial_cm

      assy_wd = pixels_per_pin * npin + 1
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
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'pinWidth' ] = pixels_per_pin

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateDrawConfig_0()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig_0( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
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
    axialPixPerCm
    coreRegion
    lineWidth
    pinWidth
"""
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.pinDataSet ),
	**kwargs
	)

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_pil_im = config[ 'legendPilImage' ]
    legend_size = config[ 'legendSize' ]

    axial_range_cm = \
        self.data.core.axialMesh[ self.cellRange[ 3 ] ] - \
        self.data.core.axialMesh[ self.cellRange[ 1 ] ]

#		-- Must calculate scale?
#		--
#		self.cellRange ( xy-left, z-bottom, xy-right, z-top, d-xy, dz )
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

#			-- Calculate image scale
#			--
      pin_count = \
          self.data.core.npinx  if self.mode == 'xz' else \
	  self.data.core.npiny
      display_pin_count = self.cellRange[ -2 ] * pin_count
      pitch = self.data.core.GetPitch()
      core_wd_cm = display_pin_count * pitch
      #display_ratio = axial_range_cm / float( core_wd_cm )

#			-- Determine drawable region in image
#			--
      # l2r, label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]

      # t2b, core : title
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)

#			-- What can we draw?
      assy_border_pix = self.cellRange[ -2 ] << 1
      x_pix_per_cm = max( (region_wd - assy_border_pix) / core_wd_cm, 1 )
      y_pix_per_cm = max( int( region_ht / axial_range_cm ), 1 )

      if y_pix_per_cm < x_pix_per_cm:
        x_pix_per_cm = y_pix_per_cm

      pin_wd_pix = int( math.floor( pitch * x_pix_per_cm ) )
      assy_wd_pix = pin_count * pin_wd_pix + 2
      core_wd_pix = self.cellRange[ -2 ] * assy_wd_pix

      core_ht_pix = int( math.floor( y_pix_per_cm * axial_range_cm ) )

    else:
      x_pix_per_cm = y_pix_per_cm = kwargs.get( 'scale', 4 )
      print >> sys.stderr, '[CoreAxial2DView._CreateDrawConfig] x_pix_per_cm=%d' % x_pix_per_cm

      pin_wd_pix = int( math.floor( pitch * x_pix_per_cm ) )
      assy_wd_pix = pin_count * pin_wd_pix
      core_wd_pix = self.cellRange[ -2 ] * assy_wd_pix

      core_ht_pix = int( math.floor( y_pix_per_cm * axial_range_cm ) )

      font_size = self._CalcFontSize( 768 )

      # l2r, label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd_pix + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht_px, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    axial_mesh = self.data.core.axialMesh
    axials_dy = []
    for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
      ax_cm = axial_mesh[ ax + 1 ] - axial_mesh[ ax ]
      axials_dy.insert( 0, int( math.floor( y_pix_per_cm * ax_cm ) ) )
    #end for

    config[ 'assemblyWidth' ] = assy_wd_pix
    config[ 'axialLevelsDy' ] = axials_dy
    config[ 'axialPixPerCm' ] = y_pix_per_cm
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd_pix, core_ht_pix ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd_pix / 20.0 ) ) )
    config[ 'pinWidth' ] = pin_wd_pix

    return  config
  #end _CreateDrawConfig_0


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateMenuDef()		-
  #----------------------------------------------------------------------
#  def _CreateMenuDef( self, data_model ):
#    """
#"""
#    menu_def = super( CoreAxial2DView, self )._CreateMenuDef( data_model )
#    other_def = \
#      [
#        ( 'Select Average Dataset...', self._OnSelectAverageDataSet ),
#	( '-', None )
#      ]
#    return  other_def + menu_def
#  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_col_or_row )
"""
    start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    print >> sys.stderr, \
        '[CoreAxial2DView._CreateRasterImage] tuple_in=%s' % \
	str( tuple_in )
    im = None

    if self.config is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axial_levels_dy = self.config[ 'axialLevelsDy' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      core_region = self.config[ 'coreRegion' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]
      pin_wd = self.config[ 'pinWidth' ]

      dset = self.data.GetStateDataSet( state_ndx, self.pinDataSet )

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
      ds_range = self.data.GetRange( self.pinDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      if self.mode == 'xz':
        assy_cell = ( -1, min( tuple_in[ 1 ], dset_shape[ 0 ] - 1 ) )
	cur_npin = min( self.data.core.npinx, dset_shape[ 1 ] )
	pin_range = range( self.data.core.npinx )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
	    additional = 'Pin Row %d' % self.pinIndex
	    )
      else: # 'yz'
        assy_cell = ( min( tuple_in[ 1 ], dset_shape[ 1 ] - 1 ), -1 )
	cur_npin = min( self.data.core.npiny, dset_shape[ 0 ] )
	pin_range = range( self.data.core.npiny )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
	    additional = 'Pin Col %d' % self.pinIndex
	    )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      assy_pen = ( 155, 155, 155, 255 )

#			-- Loop on axial levels
#			--
      axial_y = core_region[ 1 ]
      if self.mode == 'xz':
        cur_npin = min( self.data.core.npinx, dset_shape[ 1 ] )
      else:
        cur_npin = min( self.data.core.npiny, dset_shape[ 0 ] )

      for axial_level in \
          range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
        cur_dy = axial_levels_dy[ axial_level ]

#				-- Row label
#				--
	if self.showLabels:
	  label = '%02d' % (axial_level + 1)
	  label_size = pil_font.getsize( label )
	  label_y = axial_y + ((cur_dy - label_size[ 1 ]) >> 1)
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
	  if axial_level == self.cellRange[ 3 ] -1 and self.showLabels:
	    label_ndx = 0 if self.mode == 'xz' else 0
	    label = self.data.core.coreLabels[ label_ndx ][ assy_col ]
	    label_size = pil_font.getsize( label )
	    label_x = assy_x + ((assy_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if

	  if self.mode == 'xz':
	    assy_ndx = self.data.core.coreMap[ tuple_in[ 1 ], assy_col ]
	  else:
	    assy_ndx = self.data.core.coreMap[ assy_col, tuple_in[ 1 ] ]

	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    pin_x = assy_x + 1

	    for pin_col in pin_range:
	      cur_pin_col = min( pin_col, cur_npin - 1 )
	      if self.mode == 'xz':
	        value = dset_array[
		    tuple_in[ 1 ], cur_pin_col, axial_level, assy_ndx
		    ]
	      else:
	        value = dset_array[
		    cur_pin_col, tuple_in[ 1 ], axial_level, assy_ndx
		    ]

	      if not self.data.IsNoDataValue( self.pinDataSet, value ):
	        pen_color = Widget.GetColorTuple(
	            value - ds_range[ 0 ], value_delta, 255
	            )
	        brush_color = \
		    ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
	        im_draw.rectangle(
		    [ pin_x, axial_y, pin_x + pin_wd, axial_y + cur_dy ],
		    fill = brush_color, outline = pen_color
		    )
	      #end if valid value
	      pin_x += pin_wd
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
	  0,
          (core_region[ 3 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, axial_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists
    elapsed_time = timeit.default_timer() - start_time
    print >> sys.stderr, \
        '\n[CoreAxial2DView._CreateRasterImage] time=%.3fs, im-None=%s' % \
	( elapsed_time, im is None )

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return  ( state_index, pin_offset )
"""
#    colrow_ndx = 1 if self.mode == 'xz' else 0
#    return  ( self.stateIndex, self.pinColRow[ colrow_ndx ] )
    return  ( self.stateIndex, self.pinIndex )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = cell_info is not None and \
        self.data.IsValid(
            assembly_index = cell_info[ 0 ],
	    #dataset_name = self.pinDataSet,
	    pin_colrow = cell_info[ 3 : 5 ],
	    state_index = self.stateIndex
	    )

    if valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      assy_ndx = cell_info[ 0 ]
      if dset is not None and assy_ndx < dset.shape[ 3 ]:
        show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
        tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )

	if cell_info[ 5 ] >= 0:
	  axial_value = self.data.CreateAxialValue( core_ndx = cell_info[ 5 ] )
	  tip_str += ', Axial: %.2f' % axial_value[ 0 ]
	#end if
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return  ( assy_ndx, assy_col, assy_row, pin_col, pin_row, axial_level )
"""
    result = None
    if self.config is not None and self.data is not None and \
        self.data.core is not None and self.data.core.coreMap is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axials_dy = self.config[ 'axialLevelsDy' ]
      core_region = self.config[ 'coreRegion' ]
      pin_wd = self.config[ 'pinWidth' ]

      off_x = ev_x - core_region[ 0 ]
      off_y = ev_y - core_region[ 1 ]

      if self.mode == 'xz':
	assy_row = self.assemblyIndex[ 2 ]
        pin_row = self.pinColRow[ 1 ]
        assy_col = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        assy_col = max( self.cellRange[ 0 ], assy_col )
	pin_col = int( (off_x % assy_wd) / pin_wd )
	if pin_col >= self.data.core.npinx: pin_col = -1

      else:
        assy_col = self.assemblyIndex[ 1 ]
	pin_col = self.pinColRow[ 0 ]
	assy_row = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	assy_row = max( self.cellRange[ 0 ], assy_row )
	pin_row = int( (off_x % assy_wd) / pin_wd )
	if pin_row >= self.data.core.npiny: pin_row = -1

      axial_level = -1
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
        if off_y <= axials_dy[ ax ]:
	  axial_level = ax
	  break
      #end for

      assy_ndx = self.data.core.coreMap[ assy_row, assy_col ] - 1
      result = ( assy_ndx, assy_col, assy_row, pin_col, pin_row, axial_level )
    #end if we have data

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin', 'pin:assembly', 'pin:axial' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetEventLockSet()		-
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
  #	METHOD:		CoreAxial2DView.GetInitialCellRange()		-
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
  #	METHOD:		CoreAxial2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		4
"""
    return  4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    mode_str = 'XZ' if self.mode == 'xz' else 'YZ'
    return  'Core Axial ' + mode_str + ' View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    return  bmap
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    return \
        tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.pinIndex
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    self.avgValues.clear()
    self.assemblyIndex = self.state.assemblyIndex
    self.pinDataSet = self.state.pinDataSet
    self.pinColRow = self.state.pinColRow

    if self.mode == 'xz':
      self.pinOffset = \
          self.assemblyIndex[ 2 ] * self.data.core.npiny + self.pinColRow[ 1 ]
    else:
      self.pinOffset = \
          self.assemblyIndex[ 1 ] * self.data.core.npinx + self.pinColRow[ 0 ]
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindCell( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_ndx = cell_info[ 0 : 3 ]
      if assy_ndx != self.assemblyIndex:
	state_args[ 'assembly_index' ] = assy_ndx

      pin_addr = cell_info[ 3 : 5 ]
      if pin_addr != self.pinColRow:
	state_args[ 'pin_colrow' ] = pin_addr

      axial_level = cell_info[ 5 ]
      if axial_level != self.axialValue[ 1 ]:
        state_args[ 'axial_value' ] = \
	    self.data.CreateAxialValue( core_ndx = axial_level )

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnDragFinished()		-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    pass
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self.Redraw()
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.pinDataSet:
      wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._UpdateAvgValues()		-
  #----------------------------------------------------------------------
  def _UpdateAvgValues( self, state_ndx, force = False ):
    dset = None
    if self.avgDataSet is not None and \
        (force or (state_ndx not in self.avgValues)):
      dset = self.data.GetStateDataSet( state_ndx, self.avgDataSet )

    if dset is not None:
      dset_array = dset.value
      dset_shape = dset_array.shape

#			-- Axial
      #if dset_shape[ 0 ] == 1 and dset_shape[ 3 ] == 1
      if dset_shape[ 3 ] == 1:
        t_nax = min( self.data.core.nax, dset_shape[ 2 ] )
        avg_values = np.zeros( shape = ( t_nax, ) )
	for ax in range( t_nax ):
	  avg_values[ ax ] = np.mean( dset_array[ :, :, ax, : ] )

#			-- Assembly
      else:
        t_nax = min( self.data.core.nax, dset_shape[ 2 ] )
        t_nass = min( self.data.core.nass, dset_shape[ 3 ] )
	for ax in range( t_nax ):
	  for assy in range( t_nass ):
	    avg_values[ ax, assy ] = np.mean( dset_array[ :, :, ax, assy ] )

      self.avgValues[ state_ndx ] = avg_values
    #end if
  #end _UpdateAvgValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( CoreAxial2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    new_pin_index_flag = False

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      new_pin_index_flag = True
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'avg_dataset' in kwargs and kwargs[ 'avg_dataset' ] != self.avgDataSet:
      changed = True
      self.avgDataSet = kwargs[ 'avg_dataset' ]
      if self.avgDataSet == '':
        self.avgDataSet = None
      self.avgValues.clear()

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      new_pin_index_flag = True
      changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'pin_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.pinDataSet = kwargs[ 'pin_dataset' ]
        self.avgValues.clear()

    if new_pin_index_flag:
      if self.mode == 'xz':
        self.pinOffset = \
            self.assemblyIndex[ 2 ] * self.data.core.npiny + self.pinColRow[ 1 ]
      else:
        self.pinOffset = \
            self.assemblyIndex[ 1 ] * self.data.core.npinx + self.pinColRow[ 0 ]
    #end if new_pin_index_flag

    if (changed or resized) and self.config is not None:
      self._UpdateAvgValues( self.stateIndex )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end CoreAxial2DView


#------------------------------------------------------------------------
#	CLASS:		CoreXZView					-
#------------------------------------------------------------------------
class CoreXZView( CoreAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( CoreXZView, self ).__init__( container, id, mode = 'xz' )
  #end __init__
#end CoreXZView


#------------------------------------------------------------------------
#	CLASS:		CoreYZView					-
#------------------------------------------------------------------------
class CoreYZView( CoreAxial2DView ):
  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    super( CoreYZView, self ).__init__( container, id, mode = 'yz' )
  #end __init__
#end CoreYZView
