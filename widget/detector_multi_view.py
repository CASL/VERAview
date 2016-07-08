#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_multi_view.py				-
#	HISTORY:							-
#		2016-07-07	leerw@ornl.gov				-
#	  Starting new, multi-dataset version.
#	  Renaming "vanadium" to "fixed_detector".
#		2016-07-01	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-05-25	leerw@ornl.gov				-
#	  Special "vanadium" dataset.
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
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
#		2015-11-23	leerw@ornl.gov				-
#	  Migrating to new dataset retrieval scheme.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-06-18	leerw@ornl.gov				-
# 	  Extending RasterWidget.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
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
from raster_widget import *
from widget import *


DET_LINE_COLORS = [
    ( 0, 0, 0, 255 ),
    ( 0, 155, 155, 255 ),
    ( 0, 0, 200, 255 ),
    ( 0, 155, 0, 255 )
    ]

FIXED_LINE_COLORS = [
    ( 200, 0, 0, 255 ),
    ( 200, 0, 200, 255 ),
    ( 255, 192, 203, 255 ),
    ( 200, 125, 0, 255 )
    ]


#------------------------------------------------------------------------
#	CLASS:		Detector2DMultiView				-
#------------------------------------------------------------------------
class Detector2DMultiView( RasterWidget ):
  """Pin-by-pin assembly view across detector axials and state points.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    #self.detectorDataSet = kwargs.get( 'dataset', 'detector_response' )
    #self.detectorDataSet = 'detector_response'
    self.detectorDataSets = set()
    self.detectorIndex = ( -1, -1, -1 )
    #self.fixedDetectorDataSet = 'fixed_detector_response'
    self.fixedDetectorDataSets = set()

    super( Detector2DMultiView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateClipboardAllData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardAllData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    #xxx
    if True:
      return  None

    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj( self.data, state_index = self.stateIndex )
    if is_valid and \
        self.data.core.detectorMeshCenters is not None and \
	len( self.data.core.detectorMeshCenters ) > 0:
      dset = self.data.GetStateDataSet( self.stateIndex, self.detectorDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape

      csv_text = '"%s: %s=%.3g"\n' % (
	  self.detectorDataSet,
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )

#		-- Header row
#		--
      row_text = 'Row,Axial Mesh Center'
      for det_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
        row_text += ',' + self.data.core.coreLabels[ 0 ][ det_col ]
      csv_text += row_text + '\n'

      for det_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        row_label = self.data.core.coreLabels[ 1 ][ det_row ]

	for ax_ndx in \
	    range( len( self.data.core.detectorMeshCenters ) - 1, -1, -1 ):
	  ax_value = self.data.core.detectorMeshCenters[ ax_ndx ]
	  row_text = '%s,%.7g' % ( row_label, ax_value )
	  for det_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
            det_ndx = self.data.core.detectorMap[ det_row, det_col ] - 1
	    if det_ndx >= 0:
	      row_text += ',%.7g' % dset_value[ ax_ndx, det_ndx ]
	    else:
	      row_text += ',0'
	  #end for det cols

	  csv_text += row_text + '\n'
	#end for ax
      #end for det rows

    return  csv_text
  #end _CreateClipboardAllData


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateClipboardData()	-
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
  #	METHOD:	Detector2DMultiView._CreateClipboardSelectionData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectionData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    #xxx
    if True:
      return  True

    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
        self.data,
	detector_index = self.detectorIndex[ 0 ],
	state_index = self.stateIndex
	)
    if is_valid and \
        self.data.core.detectorMeshCenters is not None and \
	len( self.data.core.detectorMeshCenters ) > 0:
      dset = self.data.GetStateDataSet( self.stateIndex, self.detectorDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape

      det_ndx = self.detectorIndex[ 0 ]

      csv_text = '"%s: Detector=%d; %s=%.3g"\n' % (
	  self.detectorDataSet,
	  det_ndx + 1,
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      for ax_ndx in range( len( self.data.core.detectorMeshCenters ) - 1, -1, -1 ):
        ax_value = self.data.core.detectorMeshCenters[ ax_ndx ]
	csv_text += '%.7g,%.7g\n' % ( ax_value, dset_value[ ax_ndx, det_ndx ] )
      #end for ax_ndx

    return  csv_text
  #end _CreateClipboardSelectionData


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
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
    coreRegion
    detectorGap
    detectorWidth
    lineWidth
"""
    ds_range = self._GetDataRange()
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
      det_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      det_adv_ht = region_ht / self.cellRange[ -1 ]

      if det_adv_ht < det_adv_wd:
        det_adv_wd = det_adv_ht

      det_gap = det_adv_wd >> 4
      det_wd = max( 1, det_adv_wd - det_gap )

      core_wd = self.cellRange[ -2 ] * (det_wd + det_gap)
      core_ht = self.cellRange[ -1 ] * (det_wd + det_gap)

    else:
      det_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      print >> sys.stderr, '[Detector2DMultiView._CreateDrawConfig] det_wd=%d' % det_wd
      det_gap = det_wd >> 4
      core_wd = self.cellRange[ -2 ] * (det_wd + det_gap)
      core_ht = self.cellRange[ -1 ] * (det_wd + det_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'detectorGap' ] = det_gap
    config[ 'detectorWidth' ] = det_wd
    config[ 'lineWidth' ] = max( 1, min( 4, det_gap >> 1 ) )
#    config[ 'valueFont' ] = value_font
#    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateRasterImage()	-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    print >> sys.stderr, \
        '[Detector2DMultiView._CreateRasterImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = DataModel.IsValidObj( self.data, state_index = state_ndx )

    if config is None:
      config = self.config

    if config is not None and tuple_valid:
#	self.data.core.detectorMeshCenters is not None and \
#	len( self.data.core.detectorMeshCenters ) > 0:
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      det_gap = config[ 'detectorGap' ]
      det_wd = config[ 'detectorWidth' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      line_wd = config[ 'lineWidth' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      #value_font = config[ 'valueFont' ]

      core = self.data.GetCore()
      ds_range = self._GetDataRange()
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      st = self.data.GetState( state_ndx )
      ds_operable = \
          st.GetDataSet( 'detector_operable' ) \
	  if st is not None else None

      axial_mesh_min, axial_mesh_max = self._GetAxialRange()
      axial_mesh_factor = (det_wd - 1) / (axial_mesh_max - axial_mesh_min)
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
      fdet_center_color = ( 255, 255, 255, 255 )
      fdet_line_color = ( 200, 0, 0, 255 )

#			-- Need first detector dataset to color cell border
#			--
      first_det_values = None
      if len( self.detectorDataSets ) > 0:
	for d in sorted( self.detectorDataSets ):
	  dset = self.data.GetStateDataSet( state_ndx, d )
	  if dset is not None:
	    first_det_values = dset.value
	  break
      #end if len

#			-- Loop on rows
#			--
      #det_y = 1
      det_y = core_region[ 1 ]
      for det_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        detmap_row = self.data.core.detectorMap[ det_row, : ]

#				-- Row label
#				--
	if self.showLabels:
	  label = self.data.core.coreLabels[ 1 ][ det_row ]
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
	    label = self.data.core.coreLabels[ 0 ][ det_col ]
	    label_size = label_font.getsize( label )
	    label_x = det_x + ((det_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

#					-- Check for valid detector cell
#					--
	  det_ndx = detmap_row[ det_col ] - 1
	  if det_ndx >= 0:
#						-- Draw rectangle
	    if first_det_values is None:
	      color_ds_value = ds_range[ 0 ]
	    elif self.axialValue[ 2 ] >= 0:
	      color_ds_value = first_det_values[ self.axialValue[ 2 ], det_ndx ]
	    else:
	      color_ds_value = np.average( first_det_values[ :, det_ndx ] )
	    pen_color = Widget.GetColorTuple(
	        color_ds_value - ds_range[ 0 ], value_delta, 255
	        )

	    brush_color = op_color
	    if ds_operable is not None and len( ds_operable ) > det_ndx and \
	        ds_operable[ det_ndx ] != 0:
	      brush_color = noop_color

	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = brush_color, outline = pen_color
	        )

#						-- Draw plot grid lines
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

#						-- Draw detector plots
            color_ndx = 0
	    for ds_name in sorted( self.detectorDataSets ):
	      line_color = DET_LINE_COLORS[ color_ndx ]

	      values = None
	      dset = self.data.GetStateDataSet( state_ndx, ds_name )
	      if dset is not None and dset.value.shape[ 1 ] > det_ndx:
		dset_values = dset.value[ :, det_ndx ]
		if len( dset_values ) == len( core.detectorMeshCenters ):
		  values = dset_values

	      if values is not None:
	        last_x = None
	        last_y = None
	        for i in range( len( values ) ):
	          dy = \
		      (axial_mesh_max - core.detectorMeshCenters[ i ]) * \
		      axial_mesh_factor
	          dx = (values[ i ] - ds_range[ 0 ]) * value_factor
	          cur_x = det_x + 1 + dx
	          cur_y = det_y + 1 + dy

	          if last_x is not None:
	            im_draw.line(
		        [ last_x, last_y, cur_x, cur_y ],
		        fill = line_color, width = line_wd
		        )
	          last_x = cur_x
	          last_y = cur_y
	        #end for i
	      #end if values is not None

	      color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
	    #end for self.detectorDataSets

#						-- Draw fixed detector bars
	    fdet_line_wd = line_wd
            color_ndx = 0
	    for ds_name in sorted( self.fixedDetectorDataSets ):
	      line_color = FIXED_LINE_COLORS[ color_ndx ]

	      values = None
	      dset = self.data.GetStateDataSet( state_ndx, ds_name )
	      if dset is not None and dset.value.shape[ 1 ] > det_ndx:
		dset_values = dset.value[ :, det_ndx ]
		if len( dset_values ) == len( core.fixedDetectorMeshCenters ):
		  values = dset_values

	      if values is not None:
	        for i in range( len( values ) ):
		  dy_center = \
		    (axial_mesh_max - core.fixedDetectorMeshCenters[ i ]) * \
		    axial_mesh_factor
		  dy_lo = \
		    (axial_mesh_max - core.fixedDetectorMesh[ i ]) * \
		    axial_mesh_factor
		  dy_hi = \
		    (axial_mesh_max - core.fixedDetectorMesh[ i + 1 ]) * \
		    axial_mesh_factor
	          dx = (values[ i ] - ds_range[ 0 ]) * value_factor
	          cur_x = det_x + 1 + dx
	          cur_ylo = det_y + 1 + dy_lo
	          cur_yhi = det_y + 2 + dy_hi
		  cur_y_center = det_y + 1 + dy_center

		  im_draw.line(
		      [ cur_x, cur_ylo, cur_x, cur_yhi ],
		      fill = line_color, width = fdet_line_wd
		      )
#		  im_draw.line(
#		      [ cur_x, cur_y_center, cur_x, cur_y_center + 1 ],
#		      fill = fdet_center_color, width = fdet_line_wd
#		      )
	        #end for i
	      #end if values is not None

	      color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
	    #end for self.fixedDetectorDataSets

	  elif self.data.core.coreMap[ det_row, det_col ] > 0:
	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = ( 0, 0, 0, 0 ), outline = ( 155, 155, 155, 255 )
	        )
	  #end if-else det_ndx >= 0

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

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
      det_y = max( det_y, legend_size[ 1 ] )
      #det_y += font_size - det_gap
      det_y += font_size >> 2

      title_items = self._CreateTitleStrings( pil_font )
      title_size = title_items[ 0 ][ 1 : 3 ]
      title_x = max(
	  font_size,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
	  )

      for i in range( 1, len( title_items ) ):
	item = title_items[ i ]
        im_draw.text(
	    ( title_x + item[ 1 ], det_y + item[ 2 ] ),
	    item[ 0 ], fill = item[ 3 ], font = pil_font
	    )
      #end for

      del im_draw
    #end if config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, )
"""
    return  ( self.stateIndex, )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateTitleStrings()	-
  #----------------------------------------------------------------------
  def _CreateTitleStrings( self, pil_font ):
    """
@return			[ ( '_total_', wd, ht ), ( string, x, y, color ), ... ]
"""
    results = []

    xpos = ht = 0
    phrase = '%s %.4g: ' % (
        self.state.timeDataSet,
	self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
	)
    results.append( ( phrase, xpos, 0, ( 0, 0, 0, 255 ) ) )
    cur_size = pil_font.getsize( phrase )
    xpos += cur_size[ 0 ]
    ht = max( ht, cur_size[ 1 ] )

    color_ndx = 0
    for ds_name in sorted( self.detectorDataSets ):
      phrase = '%s ' % ds_name
      results.append( ( phrase, xpos, 0, DET_LINE_COLORS[ color_ndx ] ) )
      cur_size = pil_font.getsize( phrase )
      xpos += cur_size[ 0 ]
      ht = max( ht, cur_size[ 1 ] )
      color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
    #end for

    color_ndx = 0
    for ds_name in sorted( self.fixedDetectorDataSets ):
      phrase = '%s ' % ds_name
      results.append( ( phrase, xpos, 0, FIXED_LINE_COLORS[ color_ndx ] ) )
      cur_size = pil_font.getsize( phrase )
      xpos += cur_size[ 0 ]
      ht = max( ht, cur_size[ 1 ] )
      color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
    #end for

    results.insert( 0, ( '_total_', xpos, ht ) )
    return  results
  #end _CreateTitleStrings


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateToolTipText()	-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    valid = cell_info is not None and \
        self.data.IsValid(
            detector_index = cell_info[ 0 ],
	    state_index = self.stateIndex
	    )

    #xxx all in self.detectorDataSets and self.fixedDetectorDataSets
    #if valid:
    if False:
      ds = self.data.states[ self.stateIndex ].group[ self.detectorDataSet ]
      ds_value = np.amax( ds[ :, cell_info[ 0 ] ] )

      if ds_value > 0.0:
        show_det_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
	tip_str = \
	    'Detector: %d %s\n%s max: %g' % \
	    ( cell_info[ 0 ] + 1, show_det_addr, self.detectorDataSet, ds_value )
    #end if valid

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindDetector().
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row )
"""
    return  self.FindDetector( ev_x, ev_y )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.FindDetector()		-
  #----------------------------------------------------------------------
  def FindDetector( self, ev_x, ev_y ):
    """Finds the detector.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row )
"""
    result = None

    if self.config is not None and self.data is not None:
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

	result = self.data.CreateDetectorIndex( cell_x, cell_y )
	#det_ndx = self.data.core.detectorMap[ cell_y, cell_x ] - 1
	#result = ( det_ndx, cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindDetector


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetAnimationIndexes()	-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._GetAxialRange()		-
  #----------------------------------------------------------------------
  def _GetAxialRange( self ):
    """
@return		( min, max )
"""
    core = self.data.GetCore()
    axial_mesh_max = None
    axial_mesh_min = None

    if len( self.detectorDataSets ) > 0:
      axial_mesh_max = np.amax( core.detectorMeshCenters )
      axial_mesh_min = np.amin( core.detectorMeshCenters )

    if len( self.fixedDetectorDataSets ) > 0:
      #using core.fixedDetectorMesh instead of core.fixedDetectorMeshCenters
      if axial_mesh_max == None:
        axial_mesh_max = np.amax( core.fixedDetectorMesh )
        axial_mesh_min = np.amin( core.fixedDetectorMesh )
      else:
        axial_mesh_max = \
	    max( axial_mesh_max, np.amax( core.fixedDetectorMesh ) )
        axial_mesh_min = \
	    min( axial_mesh_min, np.amin( core.fixedDetectorMesh ) )
    #end if len

    if axial_mesh_max is None:
      axial_mesh_max = 100.0
      axial_mesh_min = 0.0
    elif axial_mesh_max == axial_mesh_min:
      axial_mesh_max = axial_mesh_min + 10.0

    return  ( axial_mesh_min, axial_mesh_max )
  #end _GetAxialRange


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._GetDataRange()		-
  #----------------------------------------------------------------------
  def _GetDataRange( self ):
    """
@return		( min, max )
"""
    ds_max = None
    ds_min = None
    for ds_name in self.detectorDataSets.union( self.fixedDetectorDataSets ):
      cur_min, cur_max = self.data.GetRange(
          ds_name,
	  self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
      if self.data.IsValidRange( cur_min, cur_max ):
	if ds_max is None:
	  ds_max = cur_max
	  ds_min = cur_min
        else:
	  ds_max = max( ds_max, cur_max )
	  ds_min = min( ds_min, cur_min )
      #end if valid range
    #end for

    if ds_max is None:
      ds_min, ds_max = 0.0, 1.0
    elif ds_max == ds_min:
      ds_max = ds_min + 0.5
      ds_min -= 0.5

    return  ( ds_min, ds_max )
  #end _GetDataRange


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetDataSetDisplayMode()	-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns 'multi'
@return			'multi'
"""
    #xxx
    #return  'selected'
    return  'multi'
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'detector', 'fixed_detector' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_axialValue,
	STATE_CHANGE_detectorDataSet, STATE_CHANGE_detectorIndex,
        STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet,
        STATE_CHANGE_fixedDetectorDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetPrintScale()		-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		64
"""
    return  64
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detector 2D Multi View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._HiliteBitmap()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config is not None:
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
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.InitDataSetSelections()	-
  #----------------------------------------------------------------------
  def InitDataSetSelections( self, *ds_names ):
    """Special hook called in VeraViewFrame.LoadDataModel().
"""
    #xxx

    for name in ds_names:
      ds_type = self.data.GetDataSetType( name )
      if ds_type == 'detector':
        self.detectorDataSets.add( name )
      elif ds_type == 'fixed_detector':
        self.fixedDetectorDataSets.add( name )
  #end InitDataSetSelections


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.IsDataSetVisible()		-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, ds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  ds_name		dataset name
@return			True if visible, else False
"""
    visible = \
        ds_name in self.detectorDataSets or \
        ds_name in self.fixedDetectorDataSets
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.IsTupleCurrent()		-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    return  \
        tpl is not None and len( tpl ) >= 1 and \
	tpl[ 0 ] == self.stateIndex
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    #self.detectorDataSet = self.state.detectorDataSet
    self.detectorIndex = self.state.detectorIndex
    #self.fixedDetectorDataSet = self.state.fixedDetectorDataSet
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
#	'detectorDataSet', 'detectorDataSets', 'detectorIndex',
#	'fixedDetectorDataSet', 'fixedDetectorDataSets'
    for k in ( 'detectorDataSets', 'fixedDetectorDataSets' ):
      if k in props_dict:
        setattr( self, k, set( props_dict[ k ] ) )
    for k in ( 'detectorIndex', ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Detector2DMultiView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    #ev.Skip()

#		-- Validate
#		--
    valid = False
    det = self.FindDetector( *ev.GetPosition() )
    if det is not None and det[ 0 ] >= 0 and det != self.detectorIndex:
      valid = self.data.IsValid(
	  detector_index = det[ 0 ],
	  state_index = self.stateIndex
	  )

    if valid:
      self.FireStateChange( detector_index = det )
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._OnFindMax()		-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Calls _OnFindMaxDetector().
"""
    pass
    #xxx find max in all datasets
#    if DataModel.IsValidObj( self.data ) and self.detectorDataSet is not None:
#      self._OnFindMaxDetector( self.detectorDataSet, all_states_flag )
  #end _OnFindMax


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Detector2DMultiView, self ).SaveProps( props_dict )
#	'detectorDataSet', 'detectorDataSets', 'detectorIndex',
#	'fixedDetectorDataSet', 'fixedDetectorDataSets'
#x    for k in ( 'detectorDataSets', 'detectorIndex', 'fixedDetectorDataSets' ):
#x      props_dict[ k ] = getattr( self, k )
    for k in ( 'detectorDataSets', 'fixedDetectorDataSets' ):
      props_dict[ k ] = list( getattr( self, k ) )
    for k in ( 'detectorIndex', ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.SetDataSet()		-
  #----------------------------------------------------------------------
#  def SetDataSet( self, ds_name ):
#    """May be called from any thread.
#"""
#    if ds_name != self.detectorDataSet:
#      wx.CallAfter( self.UpdateState, detector_dataset = ds_name )
#      self.FireStateChange( detector_dataset = ds_name )
#  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.ToggleDataSetVisible()	-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, ds_name ):
    """Toggles the visibility of the named dataset.
Must be called from the event thread.
@param  ds_name		dataset name
"""
    changed = False

    if ds_name in self.detectorDataSets:
      self.detectorDataSets.remove( ds_name )
      changed = True

    elif ds_name in self.fixedDetectorDataSets:
      self.fixedDetectorDataSets.remove( ds_name )
      changed = True

    else:
      ds_type = self.data.GetDataSetType( ds_name )
      if ds_type == 'detector':
        self.detectorDataSets.add( ds_name )
	changed = True
      elif ds_type == 'fixed_detector':
        self.fixedDetectorDataSets.add( ds_name )
	changed = True

    if changed:
      self.Redraw()
  #end ToggleDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._UpdateStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )
      kwargs[ 'resized' ] = True
      del kwargs[ 'axial_value' ]

    kwargs = super( Detector2DMultiView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

#    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.detectorDataSet:
#      ds_type = self.data.GetDataSetType( kwargs[ 'detector_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#        self.detectorDataSet = kwargs[ 'detector_dataset' ]

    if 'detector_index' in kwargs and kwargs[ 'detector_index' ] != self.detectorIndex:
      changed = True
      self.detectorIndex = kwargs[ 'detector_index' ]

#    if 'fixed_detector_dataset' in kwargs and kwargs[ 'fixed_detector_dataset' ] != self.fixedDetectorDataSet:
#      ds_type = self.data.GetDataSetType( kwargs[ 'fixed_detector_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#        self.fixedDetectorDataSet = kwargs[ 'fixed_detector_dataset' ]

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Detector2DMultiView
