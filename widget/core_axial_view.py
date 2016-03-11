#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_axial_view.py				-
#	HISTORY:							-
#		2016-03-05	leerw@ornl.gov				-
#	  Single widget with tool button for toggling slice axis.
#		2016-03-04	leerw@ornl.gov				-
#	  Not redrawing on changes to the slice assembly or pin col/row.
#		2016-03-02	leerw@ornl.gov				-
#	  Scaling correctly.  Just lacking clipboard data copy.
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
    self.pinColRow = ( -1, -1 )
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.pinIndex = 0

    self.toolButtonDefs = [ ( 'X_16x16', 'Toggle Slice Axis', self._OnMode ) ]

    super( CoreAxial2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._CreateClipboardAllData()	-
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
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      #axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      if self.mode == 'xz':
	assy_row = self.assemblyIndex[ 2 ]
	pin_row = self.pinColRow[ 1 ]
	pin_count = dset_shape[ 0 ]
      else:
	assy_col = self.assemblyIndex[ 1 ]
	pin_col = self.pinColRow[ 0 ]
	pin_count = dset_shape[ 1 ]

      clip_shape = (
          self.cellRange[ -1 ],
	  (pin_count * self.cellRange[ -2 ]) + 1
	  )
      clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      clip_data.fill( 0.0 )

      #for ax in range( self.cellRange[ -1 ] ):
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
	#ax_offset = ax - self.cellRange[ 1 ]
	ax_offset = self.cellRange[ 3 ] - 1 - ax
	clip_data[ ax_offset, 0 ] = self.data.core.axialMeshCenters[ ax ]

	pin_cell = 1
        for assy_cell in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
	  pin_cell_to = pin_cell + pin_count
	  if self.mode == 'xz':
	    assy_ndx = self.data.core.coreMap[ assy_row, assy_cell ] - 1
	    if assy_ndx >= 0:
	      clip_data[ ax_offset, pin_cell : pin_cell_to ] = \
	        dset_value[ pin_row, :, ax, assy_ndx ]

	  else:
	    assy_ndx = self.data.core.coreMap[ assy_cell, assy_col ] - 1
	    if assy_ndx >= 0:
	      clip_data[ ax_offset, pin_cell : pin_cell_to ] = \
	        dset_value[ :, pin_col, ax, assy_ndx ]

	  pin_cell = pin_cell_to
        #end for assy_cel
      #end for axials

      if self.mode == 'xz':
        title1 = '"%s: Assy Row=%s; Pin Row=%d; %s=%.3g"' % (
	    self.pinDataSet,
            self.data.core.coreLabels[ 1 ][ assy_row ],
	    pin_row + 1,
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
	    self.pinDataSet,
            self.data.core.coreLabels[ 0 ][ assy_col ],
	    pin_col + 1,
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

      if self.mode == 'xz':
	pin_row = self.pinColRow[ 1 ]
	clip_data = dset_value[ pin_row, :, axial_level, assy_ndx ]
	pin_title = 'Pin Row=%d' % (pin_row + 1)

      else:
	pin_col = self.pinColRow[ 0 ]
	clip_data = dset_value[ :, pin_col, axial_level, assy_ndx ]
	pin_title = 'Pin Col=%d' % (pin_col + 1)

      title = '"%s: Assembly=%d %s; %s; Axial=%.3f; %s=%.3g"' % (
	  self.pinDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyIndex[ 1 : 3 ] ),
	  pin_title,
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
          '[CoreAxial2DView._CreateDrawConfig]' + \
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
	pin_wd = max( 1, int( math.floor( region_ht / axial_pin_equivs ) ) )

#				-- Limited by width
      else:
        assy_wd = region_wd / self.cellRange[ -2 ]
        pin_wd = max( 1, (assy_wd - 2) / npin )

      assy_wd = pin_wd * npin + 1
      axial_pix_per_cm = pin_wd / cm_per_pin

      print >> sys.stderr, \
          '[CoreAxial2DView._CreateDrawConfig] after scale' + \
	  '\n  assy_wd=%d, pin_wd=%d\n  axial_pix_per_cm=%f' % \
	  ( assy_wd, pin_wd, axial_pix_per_cm )

#			-- Calc sizes
#			--
      core_wd = self.cellRange[ -2 ] * assy_wd
      core_ht = int( math.ceil( axial_pix_per_cm * axial_range_cm ) )

#		-- Or, scale set explicitly
#		--
    else:
      pin_wd = kwargs.get( 'scale', 4 )
      axial_pix_per_cm = pin_wd / cm_per_pin

      assy_wd = pin_wd * npin + 1
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
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateDrawConfig


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
@param  tuple_in	0-based ( state_index, assy_col_or_row, pin_col_or_row )
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
	pin_cell = min( tuple_in[ 2 ], dset_shape[ 0 ] - 1 )
	cur_npin = min( self.data.core.npinx, dset_shape[ 1 ] )
	pin_range = range( self.data.core.npinx )
	addresses = 'Assy Row %s, Pin Row %d' % \
	    ( self.data.core.coreLabels[ 1 ][ tuple_in[ 1 ] ], pin_cell + 1 )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
	    additional = addresses
	    )
      else: # 'yz'
	pin_cell = min( tuple_in[ 2 ], dset_shape[ 1 ] - 1 )
	cur_npin = min( self.data.core.npiny, dset_shape[ 0 ] )
	pin_range = range( self.data.core.npiny )
	addresses = 'Assy Col %s, Pin Col %d' % \
	    ( self.data.core.coreLabels[ 0 ][ tuple_in[ 1 ] ], pin_cell + 1 )
        title_templ, title_size = self._CreateTitleTemplate2(
	    pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
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
	    pin_x = assy_x + 1

	    for pin_col in pin_range:
	      cur_pin_col = min( pin_col, cur_npin - 1 )
	      if self.mode == 'xz':
	        value = dset_array[
		    pin_cell, cur_pin_col, axial_level, assy_ndx
		    ]
	      else:
	        value = dset_array[
		    cur_pin_col, pin_cell, axial_level, assy_ndx
		    ]

	      if not self.data.IsNoDataValue( self.pinDataSet, value ):
	        pen_color = Widget.GetColorTuple(
	            value - ds_range[ 0 ], value_delta, 255
	            )
	        brush_color = \
		    ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
	        im_draw.rectangle(
		    [ pin_x, axial_y, pin_x + pin_wd + 1, axial_y + cur_dy + 1 ],
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
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyIndex[ 2 ], self.pinColRow[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyIndex[ 1 ], self.pinColRow[ 0 ] )
    return  t
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
	    axial_level = cell_info[ 2 ],
	    state_index = self.stateIndex
	    )

    if valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
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
  #	METHOD:		CoreAxial2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
@return  ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row )
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
        assy_col = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
        assy_col = max( self.cellRange[ 0 ], assy_col )
	assy_col_or_row = assy_col

	pin_col_or_row = int( (off_x % assy_wd) / pin_wd )
	if pin_col_or_row >= self.data.core.npinx: pin_col_or_row = -1

      else:
        assy_col = self.assemblyIndex[ 1 ]
	assy_row = min(
	    int( off_x / assy_wd ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	assy_row = max( self.cellRange[ 0 ], assy_row )
	assy_col_or_row = assy_row

	pin_col_or_row = int( (off_x % assy_wd) / pin_wd )
	if pin_col_or_row >= self.data.core.npiny: pin_col_or_row = -1
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
      result = ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row )
    #end if we have data

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindCellAll()			-
  #----------------------------------------------------------------------
  def FindCellAll( self, ev_x, ev_y ):
    """Not used.
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

      axial_level = 0
      ax_y = 0
      for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
	ax_y += axials_dy[ ax ]
        if off_y <= ax_y:
	  axial_level = ax
	  break
      #end for

      assy_ndx = self.data.core.coreMap[ assy_row, assy_col ] - 1
      result = ( assy_ndx, assy_col, assy_row, pin_col, pin_row, axial_level )
    #end if we have data

    return  result
  #end FindCellAll


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
  #	METHOD:		CoreAxial2DView.GetMode()			-
  #----------------------------------------------------------------------
  def GetMode( self ):
    """
"""
    return  self.mode
  #end GetMode


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		24
"""
    return  24
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self, data_model ):
    """
"""
    return  self.toolButtonDefs
  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core Axial 2D View'
    #mode_str = 'XZ' if self.mode == 'xz' else 'YZ'
    #return  'Core Axial ' + mode_str + ' View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._HiliteBitmap()			-
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
        #pin_wd = self.config[ 'pinWidth' ]

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
  #	METHOD:		CoreAxial2DView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    if self.mode == 'xz':
      t = ( self.stateIndex, self.assemblyIndex[ 2 ], self.pinColRow[ 1 ] )
    else:
      t = ( self.stateIndex, self.assemblyIndex[ 1 ], self.pinColRow[ 0 ] )
    return  tpl == t
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

      if self.mode == 'xz':
	assy_ndx = ( cell_info[ 0 ], cell_info[ 1 ], self.assemblyIndex[ 2 ] )
	pin_addr = ( cell_info[ 3 ], self.pinColRow[ 1 ] )
      else:
	assy_ndx = ( cell_info[ 0 ], self.assemblyIndex[ 1 ], cell_info[ 1 ] )
	pin_addr = ( self.pinColRow[ 0 ], cell_info[ 3 ] )

      if assy_ndx != self.assemblyIndex:
	state_args[ 'assembly_index' ] = assy_ndx

      if pin_addr != self.pinColRow:
	state_args[ 'pin_colrow' ] = pin_addr

      axial_level = cell_info[ 2 ]
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
  #	METHOD:		CoreAxial2DView._OnMode()			-
  #----------------------------------------------------------------------
  def _OnMode( self, ev ):
    """Must be called from the event thread.
"""
    new_mode = 'xz' if self.mode == 'yz' else 'yz'
    button = ev.GetEventObject()
    self.SetMode( new_mode, button )
  #end _OnMode


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
  #	METHOD:		CoreAxial2DView.SetMode()			-
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
  #	METHOD:		CoreAxial2DView._SetModeImpl()			-
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
	    ch.GetToolTip().GetTip().find( 'Togle Slice' ) >= 0:
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
    if self.mode == 'xz':
      assy_ndx = 2
      pin_ndx = 1
      npin = self.data.core.npiny
    else:
      assy_ndx = 1
      pin_ndx = 0
      npin = self.data.core.npinx
    #if 'assembly_index' in kwargs:
      #self._stopme_ = True

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      #changed = True
      if kwargs[ 'assembly_index' ][ assy_ndx ] != self.assemblyIndex[ assy_ndx ]:
        resized = True
	new_pin_index_flag = True
      else:
        changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'avg_dataset' in kwargs and kwargs[ 'avg_dataset' ] != self.avgDataSet:
      changed = True
      self.avgDataSet = kwargs[ 'avg_dataset' ]
      if self.avgDataSet == '':
        self.avgDataSet = None
      self.avgValues.clear()

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      #changed = True
      if kwargs[ 'pin_colrow' ][ pin_ndx ] != self.pinColRow[ pin_ndx ]:
        resized = True
	new_pin_index_flag = True
      else:
        changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'pin_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.pinDataSet = kwargs[ 'pin_dataset' ]
        self.avgValues.clear()

    if new_pin_index_flag:
      self.pinOffset = \
          self.assemblyIndex[ assy_ndx ] * npin + self.pinColRow[ pin_ndx ]
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
