#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		detector_multi_view.py				-
#	HISTORY:							-
#		2018-07-27	leerw@ornl.gov				-
#	  Fixed plot scaling bug.
#		2018-03-02	leerw@ornl.gov				-
#	  Migrating to _CreateEmptyBitmapAndDC().
#		2018-02-05	leerw@ornl.gov				-
#	  Moving Linux/GTK/X11 image manipulation to the UI thread.
#		2017-11-13	leerw@ornl.gov				-
#	  Using wx.Bitmap instead of PIL.Image.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-06-05	leerw@ornl.gov				-
#	  Fixed sizing to allow for title string with many datasets
#	  active.
#		2017-05-05	leerw@ornl.gov				-
#	  Modified LoadDataModelXxx() methods to process the reason param.
#		2017-03-10	leerw@ornl.gov				-
#	  Update to precisionDigits and precisionMode.
#		2017-03-06	leerw@ornl.gov				-
#	  Using fixed_detector dataset for background color in numbers
#	  mode if no detector dataset is selected.
#		2017-03-04	leerw@ornl.gov				-
#	  Reversed sense of mode toggle button.
#	  Applying self.precision.
#	  In "numbers" mode, drawing background with outline color.
#		2017-03-01	leerw@ornl.gov				-
#	  Calculating and setting image size.
#		2016-12-27	leerw@ornl.gov				-
#		2016-12-26	leerw@ornl.gov				-
#	  Transition to DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DatModel.GetRange()
#	  directly.
#		2016-10-22	leerw@ornl.gov				-
#	  Calling DataModel.Core.Get{Col,Row}Label().
#		2016-09-29	leerw@ornl.gov				-
#	  Trying to prevent overrun of values displayed in cells.
#		2016-08-18	leerw@ornl.gov				-
#	  Renamed detectorMeshCenters to correct detectorMesh.
#		2016-08-17	leerw@ornl.gov				-
#	  New State events.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-11	leerw@ornl.gov				-
#	  Implementing text/table mode.
#		2016-07-09	leerw@ornl.gov				-
#	  Implementing new clipboard ops.
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
import logging, math, os, sys, threading, time, traceback
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

from data.utils import DataUtils
from event.state import *
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

LINE_COLORS = [
    ( 0, 0, 0, 255 ),
#    ( 240, 163, 255, 255 ),
    ( 0, 117, 220, 255 ),
    ( 153, 63, 0, 255 ),
    ( 76, 0, 92, 255 ),
    ( 25, 25, 25, 255 ),
    ( 0, 92, 49, 255 ),
    ( 43, 206, 72, 255 ),
    ( 255, 204, 153, 255 ),
    ( 128, 128, 128, 255 ),
    ( 148, 255, 181, 255 ),
    ( 143, 124, 0, 255 ),
    ( 157, 204, 0, 255 ),
    ( 194, 0, 136, 255 ),
    ( 0, 51, 128, 255 ),
    ( 255, 164, 5, 255 ),
    ( 255, 168, 187, 255 ),
    ( 66, 102, 0, 255 ),
    ( 255, 0, 16, 255 ),
    ( 94, 241, 242, 255 ),
    ( 0, 153, 143, 255 ),
    ( 224, 255, 102, 255 ),
    ( 116, 10, 255, 255 ),
    ( 153, 0, 0, 255 ),
    ( 255, 255, 128, 255 ),
    ( 255, 255, 0, 255 ),
    ( 255, 80, 5, 255 )
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
    self.detectorAddr = ( -1, -1, -1 )
    self.detectorDataSets = set()
    self.fixedDetectorDataSets = set()
    self.mode = 'plot'  # 'numbers', 'plot'

#		-- Drawing properties
#		--
    self.fillColorOperable = ( 255, 255, 255, 255 )
    self.fillColorUnoperable = ( 155, 155, 155, 255 )
    self.lineColorGrid = ( 200, 200, 200, 255 )
    self.lineColorFixedCenter = ( 255, 255, 255, 255 )

    self.toolButtonDefs = [ ( 'numbers_16x16', 'Toggle Mode to Numbers', self._OnMode ) ]

    super( Detector2DMultiView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateClipboardData()	-
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
  #	METHOD:	Detector2DMultiView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None

#		-- Must be valid state
#		--
    core = None
    if self.dmgr.HasData():
      core = self.dmgr.GetCore()

    if core is not None:
      csv_text = '"%s=%.3g"\n' % ( self.state.timeDataSet, self.timeValue )
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )

#			-- Detector datasets
#			--
      #det_mesh = self.dmgr.GetDetectorMesh()
      det_mesh = self.dmgr.GetAxialMesh2( None, 'detector' )
      if det_mesh is not None and len( det_mesh ) > 0 and \
          len( det_mesh ) > 0:
        for qds_name in sorted( self.detectorDataSets ):
	  dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
          if dset is not None:
            dset_value = np.array( dset )
            #dset_shape = dset_value.shape
	    csv_text += self.dmgr.GetDataSetDisplayName( qds_name ) + '\n'
#						-- Header row
            row_text = 'Row,Mesh'
            for det_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
              row_text += ',' + core.GetColLabel( det_col )
#              row_text += ',' + core.coreLabels[ 0 ][ det_col ]
            csv_text += row_text + '\n'

#						-- Data rows
	    #cur_det_mesh = self.dmgr.GetDetectorMesh( qds_name )
	    cur_det_mesh = self.dmgr.GetAxialMesh2( qds_name, 'detector' )
            for det_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#              row_label = core.coreLabels[ 1 ][ det_row ]
              row_label = core.GetRowLabel( det_row )
	      for ax_ndx in xrange( len( cur_det_mesh ) - 1, -1, -1 ):
	        ax_value = cur_det_mesh[ ax_ndx ]
	        row_text = '%s,%.7g' % ( row_label, ax_value )
	        for det_col in \
		    xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
                  det_ndx = core.detectorMap[ det_row, det_col ] - 1
	          if det_ndx >= 0:
	            row_text += ',%.7g' % dset_value[ ax_ndx, det_ndx ]
	          else:
	            row_text += ',0'
	        #end for det_col

	        csv_text += row_text + '\n'
	      #end for ax
            #end for det_row
          #end if dset
        #end for ds_name
      #end if det_mesh

#			-- Fixed detector datasets
#			--
      #fdet_mesh_centers = self.dmgr.GetFixedDetectorMeshCenters()
      fdet_mesh_centers = self.dmgr.GetAxialMeshCenters2( None, 'fixed_detector' )
      if fdet_mesh_centers is not None and len( fdet_mesh_centers ) > 0 and \
          len( fdet_mesh_centers ) > 0:
        for qds_name in sorted( self.fixedDetectorDataSets ):
	  dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
          if dset is not None:
            dset_value = np.array( dset )
	    csv_text += self.dmgr.GetDataSetDisplayName( qds_name ) + '\n'
#						-- Header row
            row_text = 'Row,Mesh Center'
            for det_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
              row_text += ',' + core.GetColLabel( det_col )
#              row_text += ',' + core.coreLabels[ 0 ][ det_col ]
            csv_text += row_text + '\n'

#						-- Data rows
	    #cur_mesh_centers = self.dmgr.GetFixedDetectorMeshCenters( qds_name )
	    cur_mesh_centers = \
	        self.dmgr.GetAxialMeshCenters2( qds_name, 'fixed_detector' )
            for det_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
              row_label = core.GetRowLabel( det_row )
	      for ax_ndx in xrange( len( cur_mesh_centers ) - 1, -1, -1 ):
	        ax_value = cur_mesh_centers[ ax_ndx ]
	        row_text = '%s,%.7g' % ( row_label, ax_value )
	        for det_col in \
		    xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
                  det_ndx = core.detectorMap[ det_row, det_col ] - 1
	          if det_ndx >= 0:
	            row_text += ',%.7g' % dset_value[ ax_ndx, det_ndx ]
	          else:
	            row_text += ',0'
	        #end for det_col

	        csv_text += row_text + '\n'
	      #end for ax
            #end for det_row
          #end if dset
        #end for ds_name
      #end if core.fixedDetectorMeshCenters
    #end if core is not None

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:	Detector2DMultiView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None

#		-- Must be valid state
#		--
    core = None
    if self.dmgr.HasData():
      core = self.dmgr.GetCore()

    if core is not None:
      det_ndx = self.detectorAddr[ 0 ]
      csv_text = '"Detector=%s; %s=%.3g"\n' % (
	  core.CreateAssyLabel( *self.detectorAddr[ 1 : 3 ] ),
	  self.state.timeDataSet, self.timeValue
          )

#			-- Detector datasets
#			--
      #det_mesh = self.dmgr.GetDetectorMesh()
      det_mesh = self.dmgr.GetAxialMesh2( None, 'detector' )
      if det_mesh is not None and len( det_mesh ) > 0 and len( det_mesh ) > 0:
        header_row_text = 'Mesh'
	data_rows = []
        for ax_ndx in xrange( len( det_mesh ) - 1, -1, -1 ):
	  data_rows.append( '%.7g' % det_mesh[ ax_ndx ] )

        for qds_name in sorted( self.detectorDataSets ):
	  dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
          if dset is not None:
            dset_value = np.array( dset )
	    header_row_text += ',' + self.dmgr.GetDataSetDisplayName( qds_name )

	    row_ndx = 0
            for ax_ndx in xrange( len( det_mesh ) - 1, -1, -1 ):
#	      cur_ax_ndx = self.dmgr.\
#	          GetDetectorMeshIndex( det_mesh[ ax_ndx ], qds_name )
	      cur_ax_ndx = self.dmgr.\
	          GetAxialMeshIndex( det_mesh[ ax_ndx ], qds_name, 'detector' )
	      cur_value = \
	          dset_value[ cur_ax_ndx, det_ndx ] \
		  if cur_ax_ndx >= 0 else \
		  0.0
	      data_rows[ row_ndx ] += ',%.7g' % cur_value
	      row_ndx += 1
            #end for ax_ndx
          #end if dset
        #end for ds_name

	csv_text += header_row_text + '\n'
	for r in data_rows:
	  csv_text += r + '\n'
      #end if core.detectorMesh

#			-- Fixed detector datasets
#			--
      #fdet_mesh_centers = self.dmgr.GetFixedDetectorMeshCenters()
      fdet_mesh_centers = self.dmgr.GetAxialMeshCenters2( None, 'fixed_detector' )
      if fdet_mesh_centers is not None and len( fdet_mesh_centers ) > 0 and \
          len( fdet_mesh_centers ) > 0:
        header_row_text = 'Mesh Center'
	data_rows = []
        for ax_ndx in xrange( len( fdet_mesh_centers ) - 1, -1, -1 ):
	  data_rows.append( '%.7g' % fdet_mesh_centers[ ax_ndx ] )

        for ds_name in sorted( self.fixedDetectorDataSets ):
	  dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
          if dset is not None:
            dset_value = np.array( dset )
	    header_row_text += ',' + self.dmgr.GetDataSetDisplayName( qds_name )

	    row_ndx = 0
	    ax_range = xrange( len( fdet_mesh_centers ) - 1, -1, -1 )
            for ax_ndx in ax_range:
#	      cur_ax_ndx = self.dmgr.GetFixedDetectorMeshCentersIndex(
#	          fdet_mesh_centers[ ax_ndx ], qds_name
#		  )
	      cur_ax_ndx = self.dmgr.GetAxialMeshCentersIndex(
	          fdet_mesh_centers[ ax_ndx ], qds_name, 'fixed_detector'
		  )
	      cur_value = \
	          dset_value[ cur_ax_ndx, det_ndx ] \
		  if cur_ax_ndx >= 0 else \
		  0.0
	      data_rows[ row_ndx ] += ',%.7g' % cur_value
	      row_ndx += 1
            #end for ax_ndx
          #end if dset
        #end for ds_name

	csv_text += header_row_text + '\n'
	for r in data_rows:
	  csv_text += r + '\n'
      #end if core.fixedDetectorMeshCenters
    #end if is_valid

    return  csv_text
  #end _CreateClipboardSelectedData


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
    dataRange
    font
    fontSize
    labelFont
    labelSize
    legendBitmap
    legendSize
    mapper
    valueFont
    +
    coreRegion
    detectorGap
    detectorWidth
    imageSize
    lineWidth
"""
    ds_range = self._GetDataRange()
    if 'scale_type' not in kwargs:
      #kwargs[ 'scale_type' ] = self.dmgr.GetDataSetScaleType( self.curDataSet )
      qds_names = self.detectorDataSets.union( self.fixedDetectorDataSets )
      kwargs[ 'scale_type' ] = \
          self.dmgr.GetDataSetScaleTypeAll( 'all', *qds_names )
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    #core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    #legend_bmap = config[ 'legendBitmap' ]
    legend_size = config[ 'legendSize' ]

    ds_name_count = len( self.detectorDataSets ) + len( self.fixedDetectorDataSets )
    #title_line_count = (ds_name_count >> 1) + 1
    title_line_count = max( 1, (ds_name_count + 1) >> 1 )

#		-- Must calculate scale?
#		--
    #xxxxx _CreateBaseDrawConfig() sets
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      #xxxxx revisit font_size, bigger than pixel
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      det_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      # allow for multiple title lines
      #xxxxx revisit font_size, bigger than pixel
      region_ht = working_ht - label_size[ 1 ] - 2 - \
          (font_size * (title_line_count + 1))
      det_adv_ht = region_ht / self.cellRange[ -1 ]

      if det_adv_ht < det_adv_wd:
        det_adv_wd = det_adv_ht

      det_gap = det_adv_wd >> 4
      det_wd = max( 1, det_adv_wd - det_gap )

      core_wd = self.cellRange[ -2 ] * (det_wd + det_gap)
      core_ht = self.cellRange[ -1 ] * (det_wd + det_gap)

    else:
      det_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'det_wd=%d', det_wd )
      det_gap = det_wd >> 4
      core_wd = self.cellRange[ -2 ] * (det_wd + det_gap)
      core_ht = self.cellRange[ -1 ] * (det_wd + det_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + core_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( core_ht, legend_size[ 1 ] )
      #ht += (font_size << 2)
      ht += (font_size * (title_line_count + 1))

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

#    image_wd = \
#        label_size[ 0 ] + 2 + core_wd + (font_size << 1) + legend_size[ 0 ]
#    image_ht = max(
#        #label_size[ 1 ] + 2 + core_ht + (font_size << 2),
#        label_size[ 1 ] + 2 + core_ht + (font_size * (title_line_count + 1)),
#	legend_size[ 1 ]
#	)
    region_x = label_size[ 0 ] + 2
    region_y = label_size[ 1 ] + 2
    image_wd = region_x + core_wd + (font_size << 1) + legend_size[ 0 ]
    image_ht = \
        max( region_y + core_ht, legend_size[ 1 ] ) + \
	(font_size * (title_line_count + 1))

    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'detectorGap' ] = det_gap
    config[ 'detectorWidth' ] = det_wd
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, min( 4, det_gap >> 1 ) )

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
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None
    #tuple_valid = DataModel.IsValidObj( self.data, state_index = state_ndx )

    if config is None:
      config = self.config

    if config is not None and self.dmgr.HasData():
      #im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      det_gap = config[ 'detectorGap' ]
      det_wd = config[ 'detectorWidth' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      line_wd = config[ 'lineWidth' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      value_font = config[ 'valueFont' ]

      core = self.dmgr.GetCore()
      ds_range = self._GetDataRange()
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

#      st = self.data.GetState( state_ndx )
#      ds_operable = \
#          st.GetDataSet( 'detector_operable' ) \
#	  if st is not None else None

      axial_mesh_min, axial_mesh_max = self._GetAxialRange()
      axial_mesh_factor = (det_wd - 1) / (axial_mesh_max - axial_mesh_min)
      if axial_mesh_factor < 0.0:
        axial_mesh_factor *= -1.0
      value_factor = (det_wd - 1) / value_delta

#			-- Create image
#			--
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )

      trans_brush = self._CreateTransparentBrush( gc )
      outline_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	  wx.Colour( 155, 155, 155 ), 1, wx.PENSTYLE_SOLID
          ) )

      if self.mode == 'numbers':
        ds_count = \
	    len( self.detectorDataSets ) + len( self.fixedDetectorDataSets )
        value_font_size = det_wd / (ds_count + 1)
	value_font_pts = Widget.CalcPointSize( gc, value_font_size )
	value_font = Widget.CopyFont( value_font )
	value_font.SetPointSize( min( 28, value_font_pts ) )

      if self.showLabels:
        glabel_font = gc.CreateFont( label_font, wx.BLACK )
	gc.SetFont( glabel_font )

#			-- Need first detector dataset to color cell border
#			--
      first_det_values = None
      if len( self.detectorDataSets ) > 0:
        qds_name = sorted( self.detectorDataSets )[ 0 ]
	dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
	if dset is not None:
	  first_det_values = np.array( dset )
	  first_axial_value = self.dmgr.\
	      GetAxialValue( qds_name, cm = self.axialValue.cm )
          first_axial_ndx = 2
      #end if len

      if first_det_values is None and len( self.fixedDetectorDataSets ) > 0:
        qds_name = sorted( self.fixedDetectorDataSets )[ 0 ]
	dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
	if dset is not None:
	  first_det_values = np.array( dset )
	  first_axial_value = self.dmgr.\
	      GetAxialValue( qds_name, cm = self.axialValue.cm )
          first_axial_ndx = 3
      #end if

#			-- Loop on rows
#			--
      #det_y = 1
      det_y = core_region[ 1 ]
      for det_row in xrange( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        detmap_row = core.detectorMap[ det_row, : ]

#				-- Row label
#				--
	if self.showLabels:
	  gc.SetFont( glabel_font )
	  label = core.GetRowLabel( det_row )
	  label_size = gc.GetFullTextExtent( label )
	  label_y = det_y + ((det_wd - label_size[ 1 ]) / 2.0)
	  gc.DrawText( label, 1, label_y )

#				-- Loop on col
#				--
	det_x = core_region[ 0 ]
	for det_col in xrange( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if det_row == self.cellRange[ 1 ] and self.showLabels:
	    gc.SetFont( glabel_font )
	    label = core.GetColLabel( det_col )
	    label_size = gc.GetFullTextExtent( label )
	    label_x = det_x + ((det_wd - label_size[ 0 ]) / 2.0)
	    gc.DrawText( label, label_x, 1 )
	  #end if writing column label

#					-- Check for valid detector cell
#					--
	  det_ndx = detmap_row[ det_col ] - 1
	  if det_ndx >= 0:
#						-- Draw rectangle
	    if first_det_values is None:
	      color_ds_value = ds_range[ 0 ]
	    elif first_axial_value[ first_axial_ndx ] >= 0:
	      color_ds_value = \
	      first_det_values[ first_axial_value[ first_axial_ndx ], det_ndx ]
	    else:
	      color_ds_value = np.average( first_det_values[ :, det_ndx ] )
	    #end if first_det_values is None
#	    pen_color = Widget.GetColorTuple(
#	        color_ds_value - ds_range[ 0 ], value_delta, 255
#	        )
	    pen_color = mapper.to_rgba( color_ds_value, bytes = True )

            if self.dmgr.IsDetectorOperable( det_ndx, self.timeValue ):
	      if self.mode == 'numbers' and first_det_values is not None:
	        fill_color = pen_color
		pen_color =  Widget.GetDarkerColor( pen_color, 255 )
	      else:
	        fill_color = self.fillColorOperable
	    else:
	      fill_color = self.fillColorUnoperable

	    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
		wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
	        ) ) )
	    gc.SetBrush( gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
		wx.Colour( *fill_color ), wx.BRUSHSTYLE_SOLID
	        ) ) )
	    gc.DrawRectangle( det_x, det_y, det_wd, det_wd )

#						-- Draw number
	    if self.mode == 'numbers':
	      #self.axialValue[ 2 or 3 ]
              self._DrawNumbers(
		  gc,
		  axial_value = self.axialValue,
		  time_value = self.timeValue,
		  det_ndx = det_ndx, det_wd = det_wd,
		  det_x = det_x, det_y = det_y,
		  brush = trans_brush,
		  value_font = value_font,
		  value_font_size = value_font_size
	          )
#						-- Draw plot
	    else:
              self._DrawPlots(
		  gc,
		  time_value = self.timeValue,
		  det_ndx = det_ndx, det_wd = det_wd,
		  det_x = det_x, det_y = det_y,
		  axial_max = axial_mesh_max, axial_factor = axial_mesh_factor,
		  #value_min = ds_range[ 0 ],
		  value_range = ds_range,
		  value_factor = value_factor,
		  line_wd = line_wd
	          )

	  elif core.coreMap[ det_row, det_col ] > 0:
	    gc.SetPen( outline_pen )
	    gc.SetBrush( trans_brush )
	    gc.DrawRectangle( det_x, det_y, det_wd, det_wd )
	  #end if-else det_ndx >= 0

	  det_x += det_wd + det_gap
	#end for det_col

	det_y += det_wd + det_gap
      #end for det_row

#			-- Draw Legend Image
#			--
      if legend_bmap is not None:
	gc.DrawBitmap(
	    legend_bmap,
	    core_region[ 0 ] + core_region[ 2 ] + 2 + font_size,
	    2, # core_region[ 1 ],
	    legend_bmap.GetWidth(), legend_bmap.GetHeight()
	    )
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      det_y = max( det_y, legend_size[ 1 ] )
      #det_y += font_size - det_gap
      #det_y += font_size / 4.0
      det_y += (font_size >> 2)

      #gc.SetFont( gc.CreateFont( font, wx.BLACK ) )
      gc.SetFont( font )
      title_items = self._CreateTitleStrings2( gc, core_region[ 3 ] )
      start = 0
      while start < len( title_items ):
#				-- Find end of this line
	end = len( title_items )
        line_y = title_items[ start ][ 2 ]
	for i in xrange( start, len( title_items ) ):
	  if title_items[ i ][ 2 ] != line_y:
	    end = i
	    break

        wd = title_items[ end - 1 ][ 4 ]
	line_x = (core_region[ 0 ] + core_region[ 2 ] - wd) / 2.0
	for i in xrange( start, end ):
	  item = title_items[ i ]
          gc.SetFont( gc.CreateFont( font, wx.Colour( *item[ 3 ] ) ) )
#	  gc.SetPen( wx.ThePenList.FindOrCreatePen(
#	      wx.Colour( *item[ 3 ] ), 1, wx.PENSTYLE_SOLID
#	      ) )
	  gc.DrawText( item[ 0 ], line_x + item[ 1 ], det_y + line_y )

        start = end
      #end while

      dc.SelectObject( wx.NullBitmap )
    #end if config exists

    #return  im
    return  bmap  if bmap is not None else  self.emptyBitmap
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
  #	METHOD:		Detector2DMultiView._CreateTitleStrings2()	-
  #----------------------------------------------------------------------
  def _CreateTitleStrings2( self, gc, max_wd ):
    """
@param  gc		wx.GraphicsContext instance
@return			[ ( string, x, y, color, xend ), ... ]
"""
    results = []

    x = y = 0
    phrase = '%s %.4g: ' % ( self.state.timeDataSet, self.timeValue )
	#self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
    cur_size = gc.GetFullTextExtent( phrase )
    xend = x + cur_size[ 0 ]
    results.append( ( phrase, x, y, ( 0, 0, 0, 255 ), xend ) )
    x += cur_size[ 0 ]
    wd = x
    ht = y + cur_size[ 1 ]

    color_ndx = 0
#    for qds_name in sorted( self.detectorDataSets ):
    names = \
        list( sorted( self.detectorDataSets ) ) + \
        list( sorted( self.fixedDetectorDataSets ) )
    for qds_name in names:
      phrase = '%s, ' % self.dmgr.GetDataSetDisplayName( qds_name )
      cur_size = gc.GetFullTextExtent( phrase )
      xend = x + cur_size[ 0 ]
      if xend > max_wd - 2:
        x = 0
	xend = x + cur_size[ 0 ]
	y = ht
	ht += cur_size[ 1 ] + 1

      #color = DET_LINE_COLORS[ color_ndx ]
      color = LINE_COLORS[ color_ndx ]
      results.append( ( phrase, x, y, color, xend ) )
      x = xend
      wd = max( wd, x )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name

    return  results
  #end _CreateTitleStrings2


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateTitleStrings2PIL()	-
  #----------------------------------------------------------------------
  def _CreateTitleStrings2PIL( self, pil_font, max_wd ):
    """
@return			[ ( string, x, y, color, xend ), ... ]
"""
    results = []

    x = y = 0
    phrase = '%s %.4g: ' % ( self.state.timeDataSet, self.timeValue )
	#self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
    cur_size = pil_font.getsize( phrase )
    xend = x + cur_size[ 0 ]
    results.append( ( phrase, x, y, ( 0, 0, 0, 255 ), xend ) )
    x += cur_size[ 0 ]
    wd = x
    ht = y + cur_size[ 1 ]

    color_ndx = 0
#    for qds_name in sorted( self.detectorDataSets ):
    names = \
        list( sorted( self.detectorDataSets ) ) + \
        list( sorted( self.fixedDetectorDataSets ) )
    for qds_name in names:
      phrase = '%s, ' % self.dmgr.GetDataSetDisplayName( qds_name )
      cur_size = pil_font.getsize( phrase )
      xend = x + cur_size[ 0 ]
      if xend > max_wd - 2:
        x = 0
	xend = x + cur_size[ 0 ]
	y = ht
	ht += cur_size[ 1 ] + 1

      #color = DET_LINE_COLORS[ color_ndx ]
      color = LINE_COLORS[ color_ndx ]
      results.append( ( phrase, x, y, color, xend ) )
      x = xend
      wd = max( wd, x )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name

    return  results
  #end _CreateTitleStrings2PIL


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._CreateToolTipText()	-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

#xxxxx
#    valid = False
#    core = self.dmgr.GetCore()
#    if cell_info is not None and core is not None:
#      valid = self.data.IsValid( detector_index = cell_info[ 0 ] )

    #if valid:
    if False:
      dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
      ds_value = np.amax( dset[ :, cell_info[ 0 ] ] )

      if ds_value > 0.0:
        show_det_addr = core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
	tip_str = \
	    'Detector: %s\n%s max: %g' % \
	    ( show_det_addr, qds_name, ds_value )
    #end if valid

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._DrawNumbers()		-
  #----------------------------------------------------------------------
  def _DrawNumbers(
      self,
      gc, axial_value, time_value,
      det_ndx, det_wd, det_x, det_y,
      brush, value_font, value_font_size = 0
      ):
    """
"""
    draw_items = []  # [ ( text, x, rely, color, font ) ]
    tfont = value_font

#		-- Build detector values
#		--
    center_x = det_x + (det_wd >> 1)
    #text_y = det_y + 1
    text_y = 0
    color_ndx = 0
    for qds_name in sorted( self.detectorDataSets ):
      #text_color = DET_LINE_COLORS[ color_ndx ]
      text_color = LINE_COLORS[ color_ndx ]

      dset = self.dmgr.GetH5DataSet( qds_name, time_value )
      axial_obj = \
          self.dmgr.GetAxialValue( qds_name, cm = axial_value.cm )
      if dset is not None and \
          dset.shape[ 1 ] > det_ndx and \
	  dset.shape[ 0 ] > axial_obj.detectorIndex:
	value_str, value_size, tfont = self._CreateValueDisplay(
	    dset[ axial_obj.detectorIndex, det_ndx ],
	    value_font, det_wd
	    )
	draw_items.append((
	    value_str, center_x - (value_size[ 0 ] / 2.0), text_y,
	    text_color, tfont
	    ))
	text_y += value_size[ 1 ] + 1
      #end if valid value

      #color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.detectorDataSets

#		-- Build fixed detector values
#		--
    #color_ndx = 0
    for qds_name in sorted( self.fixedDetectorDataSets ):
      #text_color = FIXED_LINE_COLORS[ color_ndx ]
      text_color = LINE_COLORS[ color_ndx ]

      dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
      axial_obj = \
          self.dmgr.GetAxialValue( qds_name, cm = axial_value.cm )
      if dset is not None and \
          dset.shape[ 1 ] > det_ndx and \
	  dset.shape[ 0 ] > axial_obj.fixedDetectorIndex:
	value_str, value_size, tfont = self._CreateValueDisplay(
	    dset[ axial_obj.fixedDetectorIndex, det_ndx ],
	    value_font, det_wd
	    #value_font, det_wd, font_size = value_font_size
	    )
	if value_str:
	  draw_items.append((
	      value_str, center_x - (value_size[ 0 ] / 2.0), text_y,
	      text_color, tfont
	      ))
	text_y += value_size[ 1 ] + 1
      #end if valid value

      #color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.fixedDetectorDataSets

#		-- Render fixed detector values
#		--
    top = det_y + ((det_wd - text_y) / 2.0)
    for item in draw_items:
#      gc.SetPen( wx.ThePenList.FindOrCreatePen(
#	  wx.Colour( *item[ 3 ], 1, wx.PENSTYLE_SOLID
#          ) )
      gc.SetFont( gc.CreateFont( item[ 4 ], wx.Colour( *item[ 3 ] ) ) )
      gc.DrawText( item[ 0 ], item[ 1 ], top + item[ 2 ] )
    #end for item
  #end _DrawNumbers


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._DrawNumbersPIL()		-
  #----------------------------------------------------------------------
  def _DrawNumbersPIL(
      self,
      im_draw, axial_value, time_value,
      det_ndx, det_wd, det_x, det_y,
      value_font, value_font_size = 0
      ):

    draw_items = []  # [ ( text, x, rely, color, font ) ]
    tfont = value_font

#		-- Build detector values
#		--
    center_x = det_x + (det_wd >> 1)
    #text_y = det_y + 1
    text_y = 0
    color_ndx = 0
    for qds_name in sorted( self.detectorDataSets ):
      #text_color = DET_LINE_COLORS[ color_ndx ]
      text_color = LINE_COLORS[ color_ndx ]

      dset = self.dmgr.GetH5DataSet( qds_name, time_value )
      axial_obj = \
          self.dmgr.GetAxialValue( qds_name, cm = axial_value.cm )
      if dset is not None and \
          dset.shape[ 1 ] > det_ndx and \
	  dset.shape[ 0 ] > axial_obj.detectorIndex:
	value_str, value_size, tfont = self._CreateValueDisplay(
	    dset[ axial_obj.detectorIndex, det_ndx ],
	    value_font, det_wd
	    )
	draw_items.append((
	    value_str, center_x - (value_size[ 0 ] / 2.0), text_y,
	    text_color, tfont
	    ))
	text_y += value_size[ 1 ] + 1
      #end if valid value

      #color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.detectorDataSets

#		-- Build fixed detector values
#		--
    #color_ndx = 0
    for qds_name in sorted( self.fixedDetectorDataSets ):
      #text_color = FIXED_LINE_COLORS[ color_ndx ]
      text_color = LINE_COLORS[ color_ndx ]

      dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
      axial_obj = \
          self.dmgr.GetAxialValue( qds_name, cm = axial_value.cm )
      if dset is not None and \
          dset.shape[ 1 ] > det_ndx and \
	  dset.shape[ 0 ] > axial_obj.fixedDetectorIndex:
	value_str, value_size, tfont = self._CreateValueDisplay(
	    dset[ axial_obj.fixedDetectorIndex, det_ndx ],
	    value_font, det_wd
	    #value_font, det_wd, font_size = value_font_size
	    )
	if value_str:
	  draw_items.append((
	      value_str, center_x - (value_size[ 0 ] / 2.0), text_y,
	      text_color, tfont
	      ))
	text_y += value_size[ 1 ] + 1
      #end if valid value

      #color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.fixedDetectorDataSets

#		-- Render fixed detector values
#		--
    top = det_y + ((det_wd - text_y) / 2.0)
    for item in draw_items:
      im_draw.text(
          ( item[ 1 ], top + item[ 2 ] ),
	  item[ 0 ], fill = item[ 3 ], font = item[ 4 ]
	  )
    #end for item
  #end _DrawNumbersPIL


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._DrawPlots()		-
  #----------------------------------------------------------------------
  def _DrawPlots(
      self,
      gc, time_value, line_wd,
      det_ndx, det_wd, det_x, det_y,
      axial_max, axial_factor,
      value_range, value_factor
      #value_min, value_factor
      ):
#		-- Draw grid lines
#		--
    if det_wd >= 20:
      incr = det_wd / 4.0

      gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	  wx.Colour( *self.lineColorGrid ), 1, wx.PENSTYLE_SOLID
          ) ) )
      path = gc.CreatePath()

      grid_y = det_y + 1
      while grid_y < det_y + det_wd - 1:
	path.MoveToPoint( det_x + 1, grid_y )
	path.AddLineToPoint( det_x + det_wd - 1, grid_y )
        grid_y += incr

      grid_x = det_x + 1
      while grid_x < det_x + det_wd - 1:
	path.MoveToPoint( grid_x, det_y + 1 )
	path.AddLineToPoint( grid_x, det_y + det_wd - 1 )
        grid_x += incr

      gc.StrokePath( path )
    #end if det_wd ge 20 for grid lines

#		-- Draw detector plots
#		--
    color_ndx = 0
    for qds_name in sorted( self.detectorDataSets ):
      #line_color = DET_LINE_COLORS[ color_ndx ]
      line_color = LINE_COLORS[ color_ndx ]

      values = None
      dset = self.dmgr.GetH5DataSet( qds_name, time_value )
      #det_mesh = self.dmgr.GetDetectorMesh( qds_name )
      det_mesh = self.dmgr.GetAxialMesh2( qds_name, 'detector' )
      if dset is not None and dset.shape[ 1 ] > det_ndx and \
          det_mesh is not None:
        dset_values = dset[ :, det_ndx ]
        if len( dset_values ) == len( det_mesh ):
	  values = dset_values

      if values is not None:
        gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	    wx.Colour( *line_color ), line_wd, wx.PENSTYLE_SOLID
            ) ) )
        path = gc.CreatePath()
	for i in xrange( len( values ) ):
	  dy = (axial_max - det_mesh[ i ]) * axial_factor
	  #dx = (values[ i ] - value_range[ 0 ]) * value_factor
	  cur_value = \
	      max( value_range[ 0 ], min( value_range[ 1 ], values[ i ] ) )
	  dx = (cur_value - value_range[ 0 ]) * value_factor

	  cur_x = det_x + 1 + dx
	  cur_y = det_y + 1 + dy
	  if i == 0:
	    path.MoveToPoint( cur_x, cur_y )
	  else:
	    path.AddLineToPoint( cur_x, cur_y )
	#end for i

        gc.StrokePath( path )
      #end if values is not None

      #color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.detectorDataSets

#		-- Draw fixed detector plots
#		--
    fdet_line_wd = line_wd
    #color_ndx = 0
    for qds_name in sorted( self.fixedDetectorDataSets ):
      #line_color = FIXED_LINE_COLORS[ color_ndx ]
      line_color = LINE_COLORS[ color_ndx ]

      values = None
      dset = None
      dm = self.dmgr.GetDataModel( qds_name )
      if dm:
        dset = self.dmgr.GetH5DataSet( qds_name, time_value )
	core = dm.GetCore()
	det_mesh = self.dmgr.GetAxialMesh2( qds_name, 'fixed_detector' )
	det_mesh_c = self.dmgr.GetAxialMeshCenters2( qds_name, 'fixed_detector' )
      if dset is not None and dset.shape[ 1 ] > det_ndx and \
          det_mesh is not None and det_mesh_c is not None:
        dset_values = dset[ :, det_ndx ]
#        if len( dset_values ) == len( core.fixedDetectorMeshCenters ):
        if len( dset_values ) == len( det_mesh_c ):
	  values = dset_values

      if values is not None:
        gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
	    wx.Colour( *line_color ), fdet_line_wd, wx.PENSTYLE_SOLID
            ) ) )
        path = gc.CreatePath()
        for i in xrange( len( values ) ):
	  dy_center = (axial_max - det_mesh_c[ i ]) * axial_factor
	  dy_lo = (axial_max - det_mesh[ i ]) * axial_factor
	  dy_hi = (axial_max - det_mesh[ i + 1 ]) * axial_factor
	  dx = (values[ i ] - value_min) * value_factor
	  cur_x = det_x + 1 + dx
	  cur_ylo = det_y + 1 + dy_lo
	  cur_yhi = det_y + 2 + dy_hi
	  cur_y_center = det_y + 1 + dy_center

	  path.MoveToPoint( cur_x, cur_ylo )
	  path.AddLineToPoint( cur_x, cur_yhi )
	  gc.StrokePath( path )
        #end for i
      #end if values is not None

      #color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.fixedDetectorDataSets
  #end _DrawPlots


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._DrawPlotsPIL()		-
  #----------------------------------------------------------------------
  def _DrawPlotsPIL(
      self,
      im_draw, time_value, line_wd,
      det_ndx, det_wd, det_x, det_y,
      axial_max, axial_factor,
      value_min, value_factor
      ):
#		-- Draw grid lines
#		--
    if det_wd >= 20:
      incr = det_wd / 4.0

      grid_y = det_y + 1
      while grid_y < det_y + det_wd - 1:
        im_draw.line(
	    [ det_x + 1, grid_y, det_x + det_wd - 1, grid_y ],
	    fill = self.lineColorGrid
	    )
        grid_y += incr

      grid_x = det_x + 1
      while grid_x < det_x + det_wd - 1:
        im_draw.line(
	    [ grid_x, det_y + 1, grid_x, det_y + det_wd - 1 ],
	    fill = self.lineColorGrid
	    )
        grid_x += incr
    #end if det_wd ge 20 for grid lines

#		-- Draw detector plots
#		--
    color_ndx = 0
    for qds_name in sorted( self.detectorDataSets ):
      #line_color = DET_LINE_COLORS[ color_ndx ]
      line_color = LINE_COLORS[ color_ndx ]

      values = None
      dset = self.dmgr.GetH5DataSet( qds_name, time_value )
      #det_mesh = self.dmgr.GetDetectorMesh( qds_name )
      det_mesh = self.dmgr.GetAxialMesh2( qds_name, 'detector' )
      if dset is not None and dset.shape[ 1 ] > det_ndx and \
          det_mesh is not None:
        dset_values = dset[ :, det_ndx ]
        if len( dset_values ) == len( det_mesh ):
	  values = dset_values

      if values is not None:
        last_x = None
	last_y = None
	for i in xrange( len( values ) ):
	  dy = (axial_max - det_mesh[ i ]) * axial_factor
	  dx = (values[ i ] - value_min) * value_factor
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

      #color_ndx = (color_ndx + 1) % len( DET_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.detectorDataSets

#		-- Draw fixed detector plots
#		--
    fdet_line_wd = line_wd
    #color_ndx = 0
    for qds_name in sorted( self.fixedDetectorDataSets ):
      #line_color = FIXED_LINE_COLORS[ color_ndx ]
      line_color = LINE_COLORS[ color_ndx ]

      values = None
      dset = None
      dm = self.dmgr.GetDataModel( qds_name )
      if dm:
        dset = self.dmgr.GetH5DataSet( qds_name, time_value )
	core = dm.GetCore()
	det_mesh = self.dmgr.GetAxialMesh2( qds_name, 'fixed_detector' )
	det_mesh_c = self.dmgr.GetAxialMeshCenters2( qds_name, 'fixed_detector' )
      if dset is not None and dset.shape[ 1 ] > det_ndx and \
          det_mesh is not None and det_mesh_c is not None:
        dset_values = dset[ :, det_ndx ]
#        if len( dset_values ) == len( core.fixedDetectorMeshCenters ):
        if len( dset_values ) == len( det_mesh_c ):
	  values = dset_values

      if values is not None:
        for i in xrange( len( values ) ):
#	  dy_center = \
#	      (axial_max - core.fixedDetectorMeshCenters[ i ]) * \
#	      axial_factor
#	  dy_lo = \
#	      (axial_max - core.fixedDetectorMesh[ i ]) * \
#	      axial_factor
#	  dy_hi = \
#	      (axial_max - core.fixedDetectorMesh[ i + 1 ]) * \
#	      axial_factor
	  dy_center = (axial_max - det_mesh_c[ i ]) * axial_factor
	  dy_lo = (axial_max - det_mesh[ i ]) * axial_factor
	  dy_hi = (axial_max - det_mesh[ i + 1 ]) * axial_factor
	  dx = (values[ i ] - value_min) * value_factor
	  cur_x = det_x + 1 + dx
	  cur_ylo = det_y + 1 + dy_lo
	  cur_yhi = det_y + 2 + dy_hi
	  cur_y_center = det_y + 1 + dy_center

	  im_draw.line(
	      [ cur_x, cur_ylo, cur_x, cur_yhi ],
	      fill = line_color, width = fdet_line_wd
	      )
        #end for i
      #end if values is not None

      #color_ndx = (color_ndx + 1) % len( FIXED_LINE_COLORS )
      color_ndx = (color_ndx + 1) % len( LINE_COLORS )
    #end for qds_name in self.fixedDetectorDataSets
  #end _DrawPlotsPIL


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

    core = None
    if self.config is not None and self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is not None and core.detectorMap is not None:
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

	result = ( core.detectorMap[ cell_y, cell_x ] - 1, cell_x, cell_y )
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
    core = self.dmgr.GetCore()
    axial_mesh_max = None
    axial_mesh_min = None

    if len( self.detectorDataSets ) > 0:
      #det_mesh = self.dmgr.GetDetectorMesh()
      det_mesh = self.dmgr.GetAxialMesh2( None, 'detector' )
      axial_mesh_max = np.amax( det_mesh )
      axial_mesh_min = np.amin( det_mesh )

    if len( self.fixedDetectorDataSets ) > 0:
      fdet_mesh = self.dmgr.GetAxialMesh2( None, 'fixed_detector' )
      if axial_mesh_max == None:
        axial_mesh_max = np.amax( fdet_mesh )
        axial_mesh_min = np.amin( fdet_mesh )
      else:
        axial_mesh_max = max( axial_mesh_max, np.amax( fdet_mesh ) )
        axial_mesh_min = min( axial_mesh_min, np.amin( fdet_mesh ) )
    #end if len

    if axial_mesh_max is None:
      axial_mesh_max = 100.0
      axial_mesh_min = 0.0
    elif axial_mesh_max == axial_mesh_min:
      axial_mesh_max = axial_mesh_min + 10.0

    return  ( axial_mesh_min, axial_mesh_max )
  #end _GetAxialRange


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetCurDataSet()		-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """Returns the first detector dataset.
@return		dataset name (DataSetName instance) or None
"""
    qds_name = None
#    if len( self.detectorDataSets ) > 0:
    if len( self.detectorDataSets ) == 1:
      qds_name = iter( self.detectorDataSets ).next()

    return  qds_name
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._GetDataRange()		-
  #----------------------------------------------------------------------
  def _GetDataRange( self ):
    """
@return		( min, max )
"""
    ds_max = None
    ds_min = None
    for qds_name in self.detectorDataSets.union( self.fixedDetectorDataSets ):
      cur_min, cur_max, data_min, data_max = self._ResolveDataRange(
          qds_name,
	  self.timeValue if self.state.scaleMode == 'state' else -1
	  #self.stateIndex if self.state.scaleMode == 'state' else -1
	  )
      if DataUtils.IsValidRange( cur_min, cur_max ):
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
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_timeValue
	])
#	STATE_CHANGE_stateIndex
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetPrintScale()		-
  #----------------------------------------------------------------------
#  def GetPrintScale( self ):
#    """
#@return		64
#"""
#    return  64
#  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Detector 2D Multi View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self ):
    """
"""
    return  self.toolButtonDefs
  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.GetUsesScaleAndCmap()	-
  #----------------------------------------------------------------------
  def GetUsesScaleAndCmap( self ):
    """
    Returns:
        boolean: False
"""
    return  False
  #end GetUsesScaleAndCmap


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._HiliteBitmap()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None:
      rel_col = self.detectorAddr[ 1 ] - self.cellRange[ 0 ]
      rel_row = self.detectorAddr[ 2 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	core_region = config[ 'coreRegion' ]
        det_gap = config[ 'detectorGap' ]
        det_wd = config[ 'detectorWidth' ]
	det_adv = det_gap + det_wd
        line_wd = config[ 'lineWidth' ]

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
	dc.SelectObject( wx.NullBitmap )

	result = new_bmap
      #end if within range
    #end if config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.IsDataSetVisible()		-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, qds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  qds_name	dataset name, DataSetName instance
@return			True if visible, else False
"""
    visible = \
        qds_name in self.detectorDataSets or \
        qds_name in self.fixedDetectorDataSets
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
  #	METHOD:		Detector2DMultiView._LoadDataModelValues()	-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """
"""
    if (reason & STATE_CHANGE_coordinates) > 0:
      self.detectorAddr = self.state.assemblyAddr

    if (reason & STATE_CHANGE_curDataSet) > 0:
      self.detectorDataSets.clear()
      self.fixedDetectorDataSets.clear()

      qds_name = self.dmgr.GetFirstDataSet( 'detector' )
      if qds_name:
        self.detectorDataSets.add( qds_name )

      qds_name = self.dmgr.GetFirstDataSet( 'fixed_detector' )
      if qds_name:
        self.fixedDetectorDataSets.add( qds_name )
    #end if (reason & STATE_CHANGE_curDataSet)
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._LoadDataModelValues_1()	-
  #----------------------------------------------------------------------
  def _LoadDataModelValues_1( self ):
    """
"""
    self.detectorAddr = self.state.assemblyAddr
    self.detectorDataSets.clear()
    self.fixedDetectorDataSets.clear()

    qds_name = self.dmgr.GetFirstDataSet( 'detector' )
    if qds_name:
      self.detectorDataSets.add( qds_name )

    qds_name = self.dmgr.GetFirstDataSet( 'fixed_detector' )
    if qds_name:
      self.fixedDetectorDataSets.add( qds_name )
  #end _LoadDataModelValues_1


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in ( 'detectorDataSets', 'fixedDetectorDataSets' ):
      if k in props_dict:
	new_set = set()
	props_set = props_dict[ k ]
	for n in props_set:
	  new_set.add( DataSetName( n ) )
        setattr( self, k, new_set )

    for k in ( 'detectorAddr', ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    for p, m in ( ( 'mode', 'SetMode' ), ):
      if p in props_dict:
        getattr( self, m )( props_dict[ p ] )

    super( Detector2DMultiView, self ).LoadProps( props_dict )
    self.container.dataSetMenu.UpdateAllMenus()
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
    det_addr = self.FindDetector( *ev.GetPosition() )
    if det_addr is not None and det_addr[ 0 ] >= 0 and \
        det_addr != self.detectorAddr:
      self.FireStateChange( assembly_addr = det_addr )
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._OnFindMinMax()		-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxMultiDataSets().
"""
    if self.dmgr.HasData():
      ds_list = \
          list( self.detectorDataSets.union( self.fixedDetectorDataSets ) )
      self._OnFindMinMaxMultiDataSets(
          mode, all_states_flag, all_assy_flag, *ds_list
	  )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._OnMode()			-
  #----------------------------------------------------------------------
  def _OnMode( self, ev ):
    """Must be called from the event thread.
"""
    new_mode = 'plot' if self.mode == 'numbers' else 'numbers'
    button = ev.GetEventObject()
    self.SetMode( new_mode, button )
  #end _OnMode


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Detector2DMultiView, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'detectorAddr', 'mode' ):
      props_dict[ k ] = getattr( self, k )

    #for k in ( 'detectorDataSets', 'fixedDetectorDataSets' ):
      #props_dict[ k ] = list( getattr( self, k ) )

    if self.dmgr.HasData() is not None:
      for k in ( 'detectorDataSets', 'fixedDetectorDataSets' ):
        cur_set = set( getattr( self, k ) )
	new_set = set()
	for cur_name in cur_set:
	  rev_name = self.dmgr.RevertIfDerivedDataSet( cur_name )
	  if rev_name != cur_name:
	    cur_set.remove( cur_name )
	    cur_set.add( rev_name )
	  new_set.add( rev_name.name )
	#end for cur_name
        props_dict[ k ] = list( new_set )
      #end for k
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
  #	METHOD:		Detector2DMultiView.SetMode()			-
  #----------------------------------------------------------------------
  def SetMode( self, mode, button = None ):
    """May be called from any thread.
@param  mode		either 'plot' or 'numbers', defaulting to the former on
			any other value
@param  button		optional button to update
"""
    if mode != self.mode:
      self.mode = 'numbers' if mode == 'numbers' else 'plot'
      wx.CallAfter( self._SetModeImpl, button )
  #end SetMode


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView._SetModeImpl()		-
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
	    ch.GetToolTip().GetTip().find( 'Toggle Mode' ) >= 0:
          button = ch
	  break
    #end if

    if button is not None:
      #bmap = Widget.GetBitmap( self.mode + '_16x16' )
      if self.mode == 'plot':
	bmap = Widget.GetBitmap( 'numbers_16x16' )
	tip_str = 'Toggle Mode to Numbers'
      else:
	bmap = Widget.GetBitmap( 'plot_16x16' )
	tip_str = 'Toggle Mode to Plot'

      button.SetBitmapLabel( bmap )
      button.SetToolTip( wx.ToolTip( tip_str ) )
      button.Update()
      self.GetParent().GetControlPanel().Layout()
    #end if

    self.Redraw()
  #end _SetModeImpl


  #----------------------------------------------------------------------
  #	METHOD:		Detector2DMultiView.ToggleDataSetVisible()	-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, qds_name ):
    """Toggles the visibility of the named dataset.
Must be called from the event thread.
@param  qds_name	dataset name, DataSetName instance
"""
    changed = False

    if qds_name in self.detectorDataSets:
      self.detectorDataSets.remove( qds_name )
      changed = True

    elif qds_name in self.fixedDetectorDataSets:
      self.fixedDetectorDataSets.remove( qds_name )
      changed = True

    else:
      ds_type = self.dmgr.GetDataSetType( qds_name )
      if ds_type == 'detector':
        self.detectorDataSets.add( qds_name )
	changed = True
      elif ds_type == 'fixed_detector':
        self.fixedDetectorDataSets.add( qds_name )
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
    if 'axial_value' in kwargs:
      value_cm = kwargs[ 'axial_value' ].cm
      if value_cm != self.axialValue.cm:
        self.axialValue = self.dmgr.GetAxialValue( None, cm = value_cm )
        kwargs[ 'resized' ] = True
        del kwargs[ 'axial_value' ]
    #end if 'axial_value'

    kwargs = super( Detector2DMultiView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.detectorAddr:
      changed = True
      self.detectorAddr = kwargs[ 'assembly_addr' ]

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
