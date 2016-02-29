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
      x_pix_per_cm = Math.max( region_wd / core_wd_cm, 1 )
      y_pix_per_cm = Math.max( int( region_ht / axial_range_cm ), 1 )

      if y_pix_per_cm < x_pix_per_cm:
        x_pix_per_cm = y_pix_per_cm

      pin_wd_pix = int( Math.floor( pitch * x_pix_per_cm ) )
      assy_wd_pix = pin_count * pin_wd_pix
      core_wd_pix = self.cellRange[ -2 ] * assy_wd_pix

      core_ht_px = int( Math.floor( y_pix_per_cm * axial_range_cm ) )

    else:
      x_pix_per_cm = y_pix_per_cm = kwargs.get( 'scale', 4 )
      print >> sys.stderr, '[CoreAxial2DView._CreateDrawConfig] pix_per_cm=%d' % x_pix_per_cm

      pin_wd_pix = int( Math.floor( pitch * x_pix_per_cm ) )
      assy_wd_pix = pin_count * pin_wd_pix
      core_wd_pix = self.cellRange[ -2 ] * assy_wd_pix

      core_ht_px = int( Math.floor( y_pix_per_cm * axial_range_cm ) )

      font_size = self._CalcFontSize( 768 )

      # l2r, label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd_pix + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht_px, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    config[ 'assemblyWidth' ] = assy_wd_pix
    config[ 'axialPixPerCm' ] = y_pix_per_cm
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd_pix, core_ht_pix ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd_pix / 20.0 ) ) )
    config[ 'pinWidth' ] = pin_wd_pix

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
@param  tuple_in	0-based ( state_index, assy_col_or_row )
"""
    start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    assy_col_or_row = tuple_in[ 1 ]
    print >> sys.stderr, \
        '[CoreAxial2DView._CreateRasterImage] tuple_in=%d,%d' % \
	( state_ndx, assy_col_or_row )
    im = None

    if self.config is not None:
      assy_wd = self.config[ 'assemblyWidth' ]
      axial_pix_per_cm = self.config[ 'axialPixPerCm' ]
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
	cur_nxpin = cur_nypin = 0
      else:
        dset_array = dset.value
        dset_shape = dset.shape
        #cur_nxpin = min( self.data.core.npin, dset_shape[ 1 ] )
        #cur_nypin = min( self.data.core.npin, dset_shape[ 0 ] )
      ds_range = self.data.GetRange( self.pinDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
	  axial_ndx = 2
	  )

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

	  if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
	    pin_y = assy_y + 1
	    cur_nypin = min( self.data.core.npiny, dset_shape[ 0 ] )
	    cur_nxpin = min( self.data.core.npinx, dset_shape[ 1 ] )

	    #for pin_row in range( cur_nypin ):
	    for pin_row in range( self.data.core.npiny ):
	      pin_x = assy_x + 1

	      cur_pin_row = min( pin_row, cur_nypin - 1 )
	      #for pin_col in range( cur_nxpin ):
	      for pin_col in range( self.data.core.npinx ):
	        cur_pin_col = min( pin_col, cur_nxpin - 1 )
		#value = dset_array[ pin_row, pin_col, axial_level, assy_ndx ]
		value = dset_array[
		    cur_pin_row, cur_pin_col, axial_level, assy_ndx
		    ]

		#if value > 0.0:
	        if not self.data.IsNoDataValue( self.pinDataSet, value ):
	          pen_color = Widget.GetColorTuple(
	              value - ds_range[ 0 ], value_delta, 255
	              )
	          brush_color = \
		      ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )
		  #im_draw.ellipse
	          im_draw.rectangle(
		      [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
		      fill = brush_color, outline = pen_color
		      )
		#end if value gt 0
	        pin_x += pin_wd
	      #end for pin cols

	      pin_y += pin_wd
	    #end for pin rows

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
  #	METHOD:		CoreAxial2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    if self.mode == 'core' and cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      assy_ndx = cell_info[ 0 ]
      if dset is not None and assy_ndx < dset.shape[ 3 ]:
        show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
        tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )

	if dset.shape[ 0 ] == 1 or dset.shape[ 1 ] == 1:
          value = dset[
	      0, 0,
	      min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 ),
	      min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
	      ]
	  tip_str += ': %g' % value

# now we need to check for derived 'asy' dataset for pinDataSet
#	else:
#	  avg_values = self.avgValues.get( self.stateIndex )
#	  if avg_values is not None:
#            ax = min( self.axialValue[ 1 ], avg_values.shape[ 0 ] - 1 )
#	    assy_ndx = min( assy_ndx, avg_values.shape[ 1 ] - 1 )
#	    avg_value = avg_values[ ax, assy_ndx ]
#	    tip_str += '\nAvg %s: %.6g' % \
#	      ( self.data.GetDataSetDisplayName( self.avgDataSet ), avg_value )
	  #end if we have avg value
	#end if-else on shape
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row, pin_col, pin_row )
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

	pin_wd = self.config[ 'pinWidth' ]
	pin_col = int( (off_x % assy_advance) / pin_wd )
	if pin_col >= self.data.core.npin: pin_col = -1
	pin_row = int( (off_y % assy_advance) / pin_wd )
	if pin_row >= self.data.core.npin: pin_row = -1

	result = ( assy_ndx, cell_x, cell_y, pin_col, pin_row )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
"""
    result = None
    if self.mode == 'assy':
      pin = self.FindPin( ev_x, ev_y )
      result = ( -1, pin[ 0 ], pin[ 1 ] )
    else:
      result = self.FindAssembly( ev_x, ev_y )

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.FindPin()			-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    if self.config is not None and self.data is not None:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
        cell_x = min(
	    int( (ev_x - assy_region[ 0 ]) / pin_size ),
	    self.data.core.npin - 1
	    )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / pin_size ),
	    self.data.core.npin - 1
	    )

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
  #	METHOD:		CoreAxial2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin', 'pin:assembly', 'pin:radial' ]
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
      xy_range = list( self.data.ExtractSymmetryExtent() )
      if self.mode == 'yz':
        xy_range[ 0 ] = xy_range[ 1 ]
	xy_range[ 2 ] = xy_range[ 3 ]
	xy_range[ 4 ] = xy_range[ 5 ]

      xy_range[ 1 ] = 0
      xy_range[ 3 ] = xy_range[ 5 ] = self.data.nax

    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		24 in 'assy' mode, 4 in 'core' mode
"""
    return  24 if self.mode == 'assy' else 4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config is not None:
      line_wd = -1
      rect = None

#			-- Core mode
#			--
      if self.config[ 'mode' ] == 'core':
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
	if self.pinColRow[ 0 ] >= 0 and self.pinColRow[ 1 ] >= 0 and \
	    self.pinColRow[ 0 ] < self.data.core.npin and \
	    self.pinColRow[ 1 ] < self.data.core.npin:
          assy_region = self.config[ 'assemblyRegion' ]
	  pin_gap = self.config[ 'pinGap' ]
	  pin_wd = self.config[ 'pinWidth' ]
	  pin_adv = pin_wd + pin_gap
	  line_wd = self.config[ 'lineWidth' ]

	  rect = \
	    [
	      self.pinColRow[ 0 ] * pin_adv + assy_region[ 0 ],
	      self.pinColRow[ 1 ] * pin_adv + assy_region[ 1 ],
	      pin_adv, pin_adv
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
	        wx.Colour( 255, 255, 255, 255 ), line_wd, wx.PENSTYLE_SOLID
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
  #	METHOD:		CoreAxial2DView._InitEventHandlers()		-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    self._SetMode( 'core' )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView.IsTupleCurrent()		-
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
  #	METHOD:		CoreAxial2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    self.avgValues.clear()
    self.assemblyIndex = self.state.assemblyIndex
    self.pinDataSet = self.state.pinDataSet
    self.pinColRow = self.state.pinColRow
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnClick()			-
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

      pin_addr = cell_info[ 3 : 5 ]
      if pin_addr != self.pinColRow:
	state_args[ 'pin_colrow' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		_OnCopy()					-
  #----------------------------------------------------------------------
  def _OnCopy( self, ev ):
    """Method that should be implemented by subclasses for a clipboard
copy operation.  This method just calls ev.Skip().
"""
    ev.Skip()
  #end _OnCopy


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnDragFinished()		-
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
  #	METHOD:		CoreAxial2DView._OnMouseMotionAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr is not None:
      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
#      if ds_name in self.data.states[ state_ndx ].group:
#        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
      dset = self.data.GetStateDataSet( state_ndx, ds_name )
      if dset is not None:
	ds_value = dset.value
#	pin_value = ds_value[
#	    pin_addr[ 1 ], pin_addr[ 0 ],
#	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
#	    ]
	if pin_addr[ 1 ] < ds_value.shape[ 0 ] and \
	    pin_addr[ 0 ] < ds_value.shape[ 1 ] and \
	    self.assemblyIndex[ 0 ] < ds_value.shape[ 3 ]:
	  pin_value = ds_value[
	      pin_addr[ 1 ], pin_addr[ 0 ],
	      min( self.axialValue[ 1 ], ds_value.shape[ 2 ] - 1 ),
	      self.assemblyIndex[ 0 ]
	      #min( self.assemblyIndex[ 0 ], ds_value.shape[ 3 ] - 1 )
	      ]
      #end if

      #if pin_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, pin_value ):
	pin_rc = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
        tip_str = 'Pin: %s\n%s: %g' % ( str( pin_rc ), ds_name, pin_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnMouseUpAssy()		-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr is not None and pin_addr != self.pinColRow:
#      print >> sys.stderr, \
#          '[CoreAxial2DView._OnMouseUp] new pinColRow=%s' % str( pin_addr )

      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
#      if ds_name in self.data.states[ state_ndx ].group:
#        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
      dset = self.data.GetStateDataSet( state_ndx, ds_name )
      if dset is not None:
        ds_value = dset.value
#	pin_value = ds_value[
#	    pin_addr[ 1 ], pin_addr[ 0 ],
#	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
#	    ]
	if pin_addr[ 1 ] < ds_value.shape[ 0 ] and \
	    pin_addr[ 0 ] < ds_value.shape[ 1 ] and \
	    self.assemblyIndex[ 0 ] < ds_value.shape[ 3 ]:
	  pin_value = ds_value[
	      pin_addr[ 1 ], pin_addr[ 0 ],
	      min( self.axialValue[ 1 ], ds_value.shape[ 2 ] - 1 ),
	      self.assemblyIndex[ 0 ]
	      ]
      #end if ds_name

      #if pin_value > 0.0:
      if not self.data.IsNoDataValue( ds_name, pin_value ):
	self.FireStateChange( pin_colrow = pin_addr )
    #end if pin_addr changed
  #end _OnMouseUpAssy


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnSelectAverageDataSet()	-
  #----------------------------------------------------------------------
  def _OnSelectAverageDataSet( self, ev ):
    """
"""
    ev.Skip()

    if self.data is not None:
      matching_ds_names = self.data.GetExtra4DDataSets()

      if len( matching_ds_names ) == 0:
        wx.MessageBox(
	    'No matching extra datasets',
	    'Select Average Dataset', wx.OK_DEFAULT, self
	    )
      else:
        dialog = wx.SingleChoiceDialog(
	    self, 'Select', 'Select Average Dataset',
	    matching_ds_names
	    )
        status = dialog.ShowModal()
	if status == wx.ID_OK:
	  name = dialog.GetStringSelection()
	  if name is not None:
	    self.UpdateState( avg_dataset = 'extra:' + name )
      #end if-else matching_ds_names
    #end if self.data
  #end _OnSelectAverageDataSet


  #----------------------------------------------------------------------
  #	METHOD:		CoreAxial2DView._OnUnzoom()			-
  #----------------------------------------------------------------------
  def _OnUnzoom( self, ev ):
    """
"""
    if len( self.cellRangeStack ) > 0:
      self.cellRange = self.cellRangeStack.pop( -1 )
      self._SetMode( 'core' )
      self._OnSize( None )
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
  #	METHOD:		CoreAxial2DView._SetMode()			-
  #----------------------------------------------------------------------
  def _SetMode( self, mode ):
    """Must be called from the UI thread.
"""
    if mode != self.mode:
      if mode == 'assy':
        self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, None )
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnMouseUpAssy )
        self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotionAssy )

      else:  # if mode == 'core':
#        self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, None )
#        self.bitmapCtrl.Bind( wx.EVT_MOTION, None )

	super( CoreAxial2DView, self )._InitEventHandlers()
      #end if-else

      self.mode = mode
    #end if different mode
  #end _SetMode


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

      t_nax = min( self.data.core.nax, dset_array.shape[ 2 ] )
      t_nass = min( self.data.core.nass, dset_array.shape[ 3 ] )
      avg_values = np.zeros( shape = ( t_nax, t_nass ) )

      for ax in range( t_nax ):  # pp_powers.shape( 2 )
        for assy in range( t_nass ):  # pp_powers.shape( 3 )
	  avg_values[ ax, assy ] = np.mean( dset_array[ :, :, ax, assy ] )
        #end for assy
      #end for ax

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

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'avg_dataset' in kwargs and kwargs[ 'avg_dataset' ] != self.avgDataSet:
      changed = True
      self.avgDataSet = kwargs[ 'avg_dataset' ]
      if self.avgDataSet == '':
        self.avgDataSet = None
      self.avgValues.clear()

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'pin_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.pinDataSet = kwargs[ 'pin_dataset' ]
        self.avgValues.clear()

    if (changed or resized) and self.config is not None:
      self._UpdateAvgValues( self.stateIndex )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end CoreAxial2DView
