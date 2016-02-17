#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_view.py				-
#	HISTORY:							-
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


#------------------------------------------------------------------------
#	CLASS:		Detector2DView					-
#------------------------------------------------------------------------
class Detector2DView( RasterWidget ):
  """Pin-by-pin assembly view across detector axials and state points.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    #self.detectorDataSet = kwargs.get( 'dataset', 'detector_response' )
    self.detectorDataSet = 'detector_response'
    self.detectorIndex = ( -1, -1, -1 )

    super( Detector2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, cur_selection_flag = False ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
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
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateDrawConfig()		-
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
    config = self._CreateBaseDrawConfig(
        self.data.GetRange( self.detectorDataSet ),
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
      print >> sys.stderr, '[Detector2DView._CreateDrawConfig] det_wd=%d' % det_wd
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
    config[ 'lineWidth' ] = max( 1, det_gap )
#    config[ 'valueFont' ] = value_font
#    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index )
"""
    state_ndx = tuple_in[ 0 ]
    print >> sys.stderr, \
        '[Detector2DView._CreateRasterImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = DataModel.IsValidObj( self.data, state_index = state_ndx )
    if self.config is not None and tuple_valid and \
	self.data.core.detectorMeshCenters is not None and \
	len( self.data.core.detectorMeshCenters ) > 0:
      im_wd, im_ht = self.config[ 'clientSize' ]
      core_region = self.config[ 'coreRegion' ]
      det_gap = self.config[ 'detectorGap' ]
      det_wd = self.config[ 'detectorWidth' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]
      #value_font = self.config[ 'valueFont' ]

      dset = self.data.GetStateDataSet( state_ndx, self.detectorDataSet )
      #dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
      ds_value = dset.value if dset is not None else None
      ds_range = self.data.GetRange( self.detectorDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.detectorDataSet,
	  dset.shape, self.state.timeDataSet
	  )

      if 'detector_operable' in self.data.states[ state_ndx ].group:
        ds_operable = self.data.states[ state_ndx ].group[ 'detector_operable' ].value
      else:
        ds_operable = None

      axial_mesh_max = np.amax( self.data.core.detectorMeshCenters )
      axial_mesh_min = np.amin( self.data.core.detectorMeshCenters )
      axial_mesh_factor = (det_wd - 1) / (axial_mesh_max - axial_mesh_min)
#          (self.data.core.detectorMeshCenters[ -1 ] - self.data.core.detectorMeshCenters[ 0 ])
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
#					--   and self.data
	  det_ndx = detmap_row[ det_col ] - 1
	  values = None
	  if det_ndx >= 0 and ds_value is not None:
	    values = ds_value[ :, det_ndx ]

	  if values is not None and len( values ) == len( self.data.core.detectorMeshCenters ):
#						-- Draw rectangle
#						--
#	    brush_color = Widget.GetColorTuple(
#	        value - ds_range[ 0 ], value_delta, 255
#	        )
#	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    if self.axialValue[ 2 ] >= 0:
	      color_value = values[ self.axialValue[ 2 ] ]
	    else:
	      color_value = np.average( values )
	    pen_color = Widget.GetColorTuple(
	        color_value - ds_range[ 0 ], value_delta, 255
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
#						--
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

#						-- Draw plot
#						--
	    last_x = None
	    last_y = None
	    for i in range( len( values ) ):
	      dy = \
		  (axial_mesh_max - self.data.core.detectorMeshCenters[ i ]) * \
		  axial_mesh_factor
#                  (self.data.core.detectorMeshCenters[ i ] - axial_mesh_min) * \
#		  axial_mesh_factor
	      dx = (values[ i ] - ds_range[ 0 ]) * value_factor
	      cur_x = det_x + 1 + dx
	      cur_y = det_y + 1 + dy

	      if last_x is not None:
	        im_draw.line(
		    [ last_x, last_y, cur_x, cur_y ],
		    fill = line_color
		    )
	      last_x = cur_x
	      last_y = cur_y
	    #end for values

	  elif self.data.core.coreMap[ det_row, det_col ] > 0:
	    im_draw.rectangle(
	        [ det_x, det_y, det_x + det_wd, det_y + det_wd ],
	        fill = ( 0, 0, 0, 0 ), outline = ( 155, 155, 155, 255 )
	        )

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( core_region[ 2 ] + font_size, 0 ) )
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
      det_y = max( det_y, legend_size[ 1 ] )
      #det_y += font_size - det_gap
      det_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, det_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, )
"""
    return  ( self.stateIndex, )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    valid = self.data.IsValid(
        detector_index = cell_info[ 0 ],
	state_index = self.stateIndex
	)

    if valid:
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
  #	METHOD:		Detector2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindDetector().
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row )
"""
    return  self.FindDetector( ev_x, ev_y )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.FindDetector()			-
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

	det_ndx = self.data.core.detectorMap[ cell_y, cell_x ] - 1
	result = ( det_ndx, cell_x, cell_y )
      #end if event within display
    #end if we have data

    return  result
  #end FindDetector


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'detector' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
#	STATE_CHANGE_detectorDataSet, if there is ever more than one
    locks = set([
        STATE_CHANGE_axialValue, STATE_CHANGE_detectorIndex,
        STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		64
"""
    return  64
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detectors 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._HiliteBitmap()			-
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
  #	METHOD:		Detector2DView.IsTupleCurrent()			-
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
  #	METHOD:		Detector2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    self.detectorDataSet = self.state.detectorDataSet
    self.detectorIndex = self.state.detectorIndex
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._OnClick()			-
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
  #	METHOD:		Detector2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.detectorDataSet:
      wx.CallAfter( self.UpdateState, detector_dataset = ds_name )
      self.FireStateChange( detector_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
      self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )
      kwargs[ 'resized' ] = True
      del kwargs[ 'axial_value' ]

    kwargs = super( Detector2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'detector_dataset' in kwargs and kwargs[ 'detector_dataset' ] != self.detectorDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'detector_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.detectorDataSet = kwargs[ 'detector_dataset' ]

    if 'detector_index' in kwargs and kwargs[ 'detector_index' ] != self.detectorIndex:
      changed = True
      self.detectorIndex = kwargs[ 'detector_index' ]

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Detector2DView
