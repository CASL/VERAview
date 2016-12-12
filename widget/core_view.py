#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_view.py					-
#	HISTORY:							-
#		2016-12-09	leerw@ornl.gov				-
#		2016-12-08	leerw@ornl.gov				-
#	  Migrating to new DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DatModel.GetRange()
#	  directly.
#		2016-10-22	leerw@ornl.gov				-
#	  Calling DataModel.Core.Get{Col,Row}Label().
#		2016-10-20	leerw@ornl.gov				-
#	  In nodalMode, hiliting assembly in white and node in red.
#	  Calling DataModel.GetFactors().
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#	  Added auxNodeAddrs and nodeAddr attributes.
#		2016-10-14	leerw@ornl.gov				-
#	  Using new _DrawValues() method.
#		2016-10-01	leerw@ornl.gov				-
#	  Better handling with nodalMode attribute.
#		2016-09-30	leerw@ornl.gov				-
#	  Adding support for nodal derived types.
#		2016-09-29	leerw@ornl.gov				-
#	  Trying to prevent overrun of values displayed in cells.
#		2016-09-20	leerw@ornl.gov				-
#	  Fixed bug where brush_color might not have been defined when
#	  writing values.
#		2016-09-19	leerw@ornl.gov				-
#	  Using state.weightsMode to determine use of pinFactors.
#		2016-09-14	leerw@ornl.gov				-
#	  Using DataModel.pinFactors to determine no-value cells.
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-09	leerw@ornl.gov				-
#	  Added assembly label in clipboard headers.
#		2016-06-27	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _OnFindMax().
#		2016-03-07	leerw@ornl.gov				-
#	  Adding numbers for 'asy_' datasets.
#		2016-02-29	leerw@ornl.gov				-
#	  Calling Redraw() instead of _OnSize( None ).
#		2016-02-25	leerw@ornl.gov				-
#	  Modified _CreateToolTipText() to report the value of an
#	  assembly average or derived dataset.
#		2016-02-17	leerw@ornl.gov				-
#	  Added copy selection.
#		2016-02-11	leerw@ornl.gov				-
#	  Supporting pin:assembly datasets by duplicating the last pin
#	  value in each dimension.
#		2016-02-10	leerw@ornl.gov				-
#	  Title template and string creation now inherited from
#	  RasterWidget.
#		2016-02-09	leerw@ornl.gov				-
#	  Start on customizing title based on dataset shape.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2016-01-22	leerw@ornl.gov				-
#	  Adding clipboard copy.
#		2015-11-28	leerw@ornl.gov				-
#	  Calling DataModel.IsNoDataValue() instead of checking for
#	  gt value to draw.
#		2015-11-23	leerw@ornl.gov				-
#	  Fixed some bugs.
#		2015-11-19	leerw@ornl.gov				-
#	  Adding support for 'extra' datasets.
#		2015-11-18	leerw@ornl.gov				-
#	  Relaxing to allow any axial and assembly dimensions.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-06-17	leerw@ornl.gov				-
# 	  Extending RasterWidget.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-21	leerw@ornl.gov				-
#	  Showing legend now optional.
#		2015-05-18	leerw@ornl.gov				-
#	  Making the showing of assembly labels an option.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-04-22	leerw@ornl.gov				-
#	  Showing currently selected assembly.
#		2015-04-10	leerw@ornl.gov				-
#	  Minor fixes and removing sliders (now on VeraViewFrame).
#		2015-04-04	leerw@ornl.gov				-
#	  Zoom display to an assembly view.
#		2015-03-25	leerw@ornl.gov				-
#	  Many fixes and additions, most notably the SetDataSet()
#	  capability.  Also fixed some zooming issues and added
#	  the bitmapsLock protocol in _UpdateStateAndAxial().
#		2015-03-19	leerw@ornl.gov				-
#	  Trying per-menu item handler.
#		2015-03-11	leerw@ornl.gov				-
#	  Using ExposureSliderBean.
#		2015-03-06	leerw@ornl.gov				-
#	  New Widget.GetImage() for 'loading' image.
#	  Starting ellipse drawing at pixel (1,1).
#		2015-02-07	leerw@ornl.gov				-
#	  Processing average powers.
#		2015-02-06	leerw@ornl.gov				-
#	  Added tooltip.
#		2015-01-30	leerw@ornl.gov				-
#	  Added CreateMenu().
#		2015-01-28	leerw@ornl.gov				-
#	  Starting cell range and zoom processing.
#		2015-01-24	leerw@ornl.gov				-
#		2015-01-19	leerw@ornl.gov				-
#	  Re-designing
#		2015-01-16	leerw@ornl.gov				-
#		2015-01-07	leerw@ornl.gov				-
#	  Added popup on assembly.
#		2015-01-06	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, math, os, sys, threading, time, timeit, traceback
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
#	CLASS:		Core2DView					-
#------------------------------------------------------------------------
class Core2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

Properties:
"""

#  MENU_ID_unzoom = 10000
#  MENU_DEFS = [ ( 'Unzoom', MENU_ID_unzoom ) ]


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.avgDataSet = None
    #self.avgValues = {}

    self.mode = ''  # 'assy', 'core'
    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    super( Core2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateAssyDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateAssyDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 24 is used.
@param  kwargs
    scale	pixels per pin
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
    lineWidth
    mode = 'assy'
    pinGap
    pinWidth		used for pin or node width, depending on self.nodalMode
    valueFont
    valueFontSize
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
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

      if self.nodalMode:
        pin_adv_wd = region_wd >> 1
      else:
        pin_adv_wd = region_wd / core.npin

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      if self.nodalMode:
        pin_adv_ht = region_ht >> 1
      else:
        pin_adv_ht = region_ht / core.npin

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      if self.nodalMode:
        assy_wd = assy_ht = (pin_wd + pin_gap) << 1
      else:
        assy_wd = assy_ht = core.npin * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 24
      pin_gap = pin_wd >> 3

      if self.nodalMode:
        pin_wd <<= 4
        assy_wd = assy_ht = (pin_wd + pin_gap) << 1
      else:
        assy_wd = assy_ht = core.npin * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    value_font_size = assy_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'mode' ] = 'assy'
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateAssyDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateAssyImage()			-
  #----------------------------------------------------------------------
  def _CreateAssyImage( self, tuple_in, config ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, assy_ndx, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    tuple_valid = self.dmgr.IsValid(
	self.curDataSet,
        assembly_addr = assy_ndx,
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

      assy_region = config[ 'assemblyRegion' ]
      im_wd, im_ht = config[ 'clientSize' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_gap = config[ 'pinGap' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]

      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()
      pin_factors = None
      if self.state.weightsMode == 'on':
        pin_factors = self.dmgr.GetFactors( self.curDataSet )
#	if self.nodalMode:
#          pin_factors = self.data.GetNodeFactors()
#          pin_factors_shape = pin_factors.shape
#	else:
#          pin_factors = self.data.GetPinFactors()
#          pin_factors_shape = pin_factors.shape

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
	cur_nxpin = cur_nypin = 0
      else:
        dset_array = dset.value
        dset_shape = dset.shape
        cur_nxpin = 2 if self.nodalMode else min( core.npinx, dset_shape[ 1 ] )
        cur_nypin = 2 if self.nodalMode else min( core.npiny, dset_shape[ 0 ] )

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )

      node_value_draw_list = []

#			-- Limit axial level
#			--
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )
      axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, core_ndx = axial_level )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      node_ndx = 0
      pin_y = assy_region[ 1 ]
#      for pin_row in range( core.npin ):
      for pin_row in xrange( cur_nypin ):
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
#	for pin_col in range( core.npin ):
	for pin_col in xrange( cur_nxpin ):
#					-- Column label
#					--
	  if pin_row == 0 and self.showLabels:
	    label = '%d' % (pin_col + 1)
	    label_size = label_font.getsize( label )
	    label_x = pin_x + ((pin_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ), label,
		fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

	  if self.nodalMode:
	    value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
	    if pin_factors is None:
	      pin_factor = 1
	    else:
	      pin_factor = pin_factors[ 0, node_ndx, axial_level, assy_ndx ]
	    node_ndx += 1
	  else:
	    value = dset_array[ pin_row, pin_col, axial_level, assy_ndx ]
	    if pin_factors is None:
	      pin_factor = 1
	    else:
	      pin_factor = pin_factors[ pin_row, pin_col, axial_level, assy_ndx ]

	  if not ( self.dmgr.IsBadValue( value ) or pin_factor == 0 ):
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    if self.nodalMode:
	      im_draw.rectangle(
	          [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	          fill = brush_color, outline = pen_color
	          )
	      node_value_draw_list.append((
	          self._CreateValueString( value, 3 ),
                  Widget.GetContrastColor( *brush_color ),
                  pin_x, pin_y, pin_wd, pin_wd
                  ))
#	      value_str, value_size, tfont = self._CreateValueDisplay(
#	          value, 3, value_font, pin_wd, value_font_size >> 1
#	          )
#	      if value_str:
#	        value_x = pin_x + ((pin_wd - value_size[ 0 ]) >> 1)
#		value_y = pin_y + ((pin_wd - value_size[ 1 ]) >> 1)
#                im_draw.text(
#		    ( value_x, value_y ), value_str,
#		    fill = Widget.GetContrastColor( *brush_color ),
#		    font = tfont
#                    )
	    else:
	      im_draw.ellipse(
	          [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	          fill = brush_color, outline = pen_color
	          )
	  #end if value > 0

	  pin_x += pin_wd + pin_gap
	#end for pin_col

	pin_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw Values
#			--
      if node_value_draw_list:
        self._DrawValues( node_value_draw_list, im_draw )

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( assy_wd + font_size, 1 ) )
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
      pin_y = max( pin_y, legend_size[ 1 ] )
      pin_y += font_size >> 2

      title_str = self._CreateTitleString(
	  title_templ,
	  assembly = assy_ndx,
	  axial = axial_value[ 0 ],
	  time = self.timeValue
	  #time = self.dmgr.GetTimeIndexValue( state_ndx, qds_name )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#0,
#(assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, pin_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateAssyImage


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateClipboardData()		-
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
  #	METHOD:		Core2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = self.dmgr.IsValid(
	self.curDataSet,
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      clip_shape = (
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

          assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
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
	  self.curDataSet.displayName,
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      col_labels = core.GetColLabel( self.cellRange[ 0 ], self.cellRange[ 2 ] )
      row_labels = core.GetRowLabel( self.cellRange[ 1 ], self.cellRange[ 3 ] )
      title2 = '"Cols=%s; Rows=%s"' % (
	  ':'.join( col_labels ),
	  ':'.join( row_labels )
          )
      csv_text = DataModel.ToCSV( clip_data, ( title1, title2 ) )

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = self.dmgr.IsValid(
        self.curDataSet,
        assembly_addr = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      #clip_shape = ( dset_shape[ 0 ], dset_shape[ 1 ] )
      #clip_data = np.ndarray( clip_shape, dtype = np.float64 )
      #clip_data.fill( 0.0 )
      clip_data = dset_value[ :, :, axial_level, assy_ndx ]

      title = '"%s: Assembly=%d %s; Axial=%.3f; %s=%.3g"' % (
	  self.curDataSet.displayName,
	  assy_ndx + 1,
	  core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.timeValue
	  #self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateCoreDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
@param  kwargs
    scale	pixels per pin
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
    coreRegion
    lineWidth
    mode = 'core'
    pinWidth		used for pin or node width, depending on self.nodalMode
    valueFont
    valueFontSize
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
	self.timeValue if self.state.scaleMode == 'state' else -1
	##self.stateIndex if self.state.scaleMode == 'state' else -1
	)
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
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
      #x region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)
      assy_ht = region_ht / self.cellRange[ -1 ]

      if assy_ht < assy_wd:
        assy_wd = assy_ht

      if self.nodalMode:
        pin_wd = max( 1, (assy_wd - 2) >> 1 )
        assy_wd = pin_wd * 2
      else:
        pin_wd = max( 1, (assy_wd - 2) / core.npin )
        assy_wd = pin_wd * core.npin + 1
      assy_advance = assy_wd
      core_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = self.cellRange[ -1 ] * assy_advance

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4
      if self.nodalMode:
        pin_wd <<= 4

      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'nodalMode=%d, pin_wd=%d', self.nodalMode, pin_wd )
      if self.nodalMode:
        assy_wd = pin_wd << 1
      else:
        assy_wd = pin_wd * core.npin + 1
      assy_advance = assy_wd

      font_size = self._CalcFontSize( 768 )

      core_wd = region_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = region_ht = self.cellRange[ -1 ] * assy_advance

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
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'coreFullRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, region_wd, region_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'mode' ] = 'core'
    config[ 'pinWidth' ] = pin_wd
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreImage()			-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, tuple_in, config ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level )
"""
    start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None

    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      if 'coreRegion' not in config:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'coreRegion missing from config, reconfiguring' )
	if 'clientSize' in config:
          config = self._CreateCoreDrawConfig( size = config[ 'clientSize' ] )
	else:
          config = self._CreateCoreDrawConfig( scale = config[ 'scale' ] )

      assy_advance = config[ 'assemblyAdvance' ]
      assy_wd = config[ 'assemblyWidth' ]
      im_wd, im_ht = config[ 'clientSize' ]
      core_region = config[ 'coreRegion' ]
      font_size = config[ 'fontSize' ]
      label_font = config[ 'labelFont' ]
      legend_pil_im = config[ 'legendPilImage' ]
      pil_font = config[ 'pilFont' ]
      pin_wd = config[ 'pinWidth' ]
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]

      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()
      pin_factors = None
      if self.state.weightsMode == 'on':
        pin_factors = self.dmgr.GetFactors( self.curDataSet )
#	if self.nodalMode:
#          pin_factors = self.data.GetNodeFactors()
#          pin_factors_shape = pin_factors.shape
#	else:
#          pin_factors = self.data.GetPinFactors()
#          pin_factors_shape = pin_factors.shape

      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
	cur_nxpin = cur_nypin = 0
      else:
        dset_array = np.array( dset )
        dset_shape = dset.shape
        cur_nxpin = 2 if self.nodalMode else min( core.npinx, dset_shape[ 1 ] )
        cur_nypin = 2 if self.nodalMode else min( core.npiny, dset_shape[ 0 ] )

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.curDataSet, dset_shape, self.state.timeDataSet,
	  axial_ndx = 2
	  )

      draw_value_flag = \
          self.curDataSet is not None and \
	  dset_shape[ 0 ] == 1 and dset_shape[ 1 ] == 1
          #value_font is not None
      node_value_draw_list = []
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
      node_pen = ( 100, 100, 100, 255 )

#			-- Loop on assembly rows
#			--
      assy_y = core_region[ 1 ]
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
        core_data_row = core.coreMap[ assy_row, : ]

#				-- Row label
#				--
	if self.showLabels:
	  label = core.GetRowLabel( assy_row )
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
	    label = core.GetColLabel( assy_col )
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

	    #for pin_row in range( self.data.core.npiny ):
	    pin_row_limit = 2 if self.nodalMode else core.npiny
	    pin_col_limit = 2 if self.nodalMode else core.npinx
	    node_ndx = 0

	    for pin_row in range( pin_row_limit ):
	      pin_x = assy_x + 1

	      cur_pin_row = min( pin_row, cur_nypin - 1 )
	      for pin_col in range( pin_col_limit ):
	        cur_pin_col = min( pin_col, cur_nxpin - 1 )
		value = 0.0
		pin_factor = 0
		if cur_pin_row >= 0 and cur_pin_col >= 0:
		  if self.nodalMode:
		    value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
		    if pin_factors is None:
		      pin_factor = 1
		    else:
	              pin_factor = \
		          pin_factors[ 0, node_ndx, axial_level, assy_ndx ]
		    node_ndx += 1
		  else:
		    value = dset_array[
		        cur_pin_row, cur_pin_col, axial_level, assy_ndx
		        ]
	            if pin_factors is None:
	              pin_factor = 1
		    else:
	              pin_factor = pin_factors[
		          cur_pin_row, cur_pin_col, axial_level, assy_ndx
		          ]
		  #end if-else
		#end if cur_pin_row and cur_pin_col

	        if not ( self.dmgr.IsBadValue( value ) or pin_factor == 0 ):
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

		  if self.nodalMode:
	            im_draw.rectangle(
		        [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
		        fill = None, outline = node_pen
		        )
		    node_value_draw_list.append((
			self._CreateValueString( value, 3 ),
                        Widget.GetContrastColor( *brush_color ),
			pin_x, pin_y, pin_wd, pin_wd
		        ))
		  #end if nodalMode
		#end if value gt 0

	        pin_x += pin_wd
	      #end for pin cols

	      pin_y += pin_wd
	    #end for pin rows

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
	    #end if draw_value_flag
	  #end if assembly referenced

	  assy_x += assy_advance
	#end for assy_col

        assy_y += assy_advance
      #end for assy_row

#			-- Draw Values
#			--
      if node_value_draw_list:
        self._DrawValues( node_value_draw_list, im_draw )

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
      #x assy_y += font_size >> 2
      assy_y += font_size >> 1

      title_str = self._CreateTitleString(
	  title_templ,
	  axial = core.axialMeshCenters[ axial_level ],
	  time = self.timeValue
	  #time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (core_region[ 0 ] + core_region[ 2 ] - title_size[ 0 ]) >> 1
#0,
#(core_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )
      im_draw.text(
          ( title_x, assy_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if config exists
    elapsed_time = timeit.default_timer() - start_time
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'time=%.3fs, im-None=%s', elapsed_time, im is None )

    return  im if im is not None else self.emptyPilImage
  #end _CreateCoreImage


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateDrawConfig()			-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """
@param  kwargs
    scale	pixels per pin
    size	( wd, ht ) against which to compute the scale
@return			config dict with keys needed by _CreateRasterImage().
"""
#    dset = self.data.GetStateDataSet( 0, self.pinDataSet )
#    if dset is not None and dset.shape[ 0 ] == 1 and dset.shape[ 1 ] == 4:
#      kwargs[ 'nodal' ] = True
    return \
        self._CreateAssyDrawConfig( **kwargs ) if self.mode == 'assy' else \
	self._CreateCoreDrawConfig( **kwargs )
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateMenuDef()			-
  #----------------------------------------------------------------------
#  def _CreateMenuDef( self, data_model ):
#    """
#"""
#    menu_def = super( Core2DView, self )._CreateMenuDef( data_model )
#    other_def = \
#      [
#        ( 'Select Average Dataset...', self._OnSelectAverageDataSet ),
#	( '-', None )
#      ]
#    return  other_def + menu_def
#  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateRasterImage()			-
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
  #	METHOD:		Core2DView._CreateStateTuple()			-
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
  #	METHOD:		Core2DView._CreateToolTipText()			-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''

    if self.mode == 'core' and cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      #if dset is not None and assy_ndx < dset.shape[ 3 ]:
      if dset is not None:
        core = self.dmgr.GetCore()
        assy_ndx = min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
        axial_value = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 ),
        show_assy_addr = core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
	value = None

	if self.nodalMode:
	  node_addr = cell_info[ 5 ] if len( cell_info ) > 5 else -1
	  if self.dmgr.IsValid( self.curDataSet, node_addr = node_addr ):
	    tip_str = 'Assy: %d %s, Node %d' % \
	        ( assy_ndx + 1, show_assy_addr, node_addr + 1 )
	    value = dset[ 0, node_addr, axial_value, assy_ndx ]
	else:
          tip_str = 'Assy: %d %s' % ( assy_ndx + 1, show_assy_addr )
	  if dset.shape[ 0 ] == 1 or dset.shape[ 1 ] == 1:
	    value = dset[ 0, 0, axial_value, assy_ndx ]
	#end if self.nodalMode

	if not self.dmgr.IsBadValue( value ):
	  tip_str += ': %g' % value
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.FindAssembly()			-
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based index, cell_col, cell_row,
			  pin_col, pin_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is not None and core.coreMap is not None:
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

	assy_ndx = core.coreMap[ cell_y, cell_x ] - 1

	pin_wd = self.config[ 'pinWidth' ]
	if self.nodalMode:
	  node_col = int( (off_x % assy_advance) / pin_wd )
	  node_row = int( (off_y % assy_advance) / pin_wd )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  pin_col, pin_row = self.dmgr.GetSubAddrFromNode( node_addr )
	else:
	  pin_col = int( (off_x % assy_advance) / pin_wd )
	  if pin_col >= core.npinx: pin_col = -1
	  pin_row = int( (off_y % assy_advance) / pin_wd )
	  if pin_row >= core.npiny: pin_row = -1
	  node_addr = self.dmgr.GetNodeAddr( ( pin_col, pin_row ) )

	result = ( assy_ndx, cell_x, cell_y, pin_col, pin_row, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.FindCell()				-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() in 'assy' mode or FindAssembly() in 'core' mode.
"""
    result = None
    if self.mode == 'assy':
      pin = self.FindPin( ev_x, ev_y )
      if pin is not None:
	result = ( -1, ) + pin
        #result = ( -1, pin[ 0 ], pin[ 1 ] )
    else:
      result = self.FindAssembly( ev_x, ev_y )

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.FindPin()				-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.  Must be in 'assy' mode.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and 'assemblyRegion' in self.config:
      core = self.dmgr.GetCore()

    if core:
      if ev_x >= 0 and ev_y >= 0:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_size = self.config[ 'pinWidth' ] + self.config[ 'pinGap' ]
	
	if self.nodalMode:
	  node_col = min( int( (ev_x - assy_region[ 0 ]) / pin_size ), 1 )
	  node_row = min( int( (ev_y - assy_region[ 1 ]) / pin_size ), 1 )
	  node_addr = 2 if node_row > 0 else 0
	  if node_col > 0:
	    node_addr += 1
	  cell_x, cell_y = self.dmgr.GetSubAddrFromNode( node_addr )
	else:
          cell_x = \
	      min( int( (ev_x - assy_region[ 0 ]) / pin_size ), core.npin - 1 )
          cell_y = \
	      min( int( (ev_y - assy_region[ 1 ]) / pin_size ), core.npin - 1 )
          node_addr = self.dmgr.GetNodeAddr( ( cell_x, cell_y ) )

	result = ( cell_x, cell_y, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindPin


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [
        'pin', ':assembly', ':node',
	':radial', ':radial_assembly', ':radial_node'
	]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
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
  #	METHOD:		Core2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """
@return		24 in 'assy' mode, 4 in 'core' mode
"""
    return  24 if self.mode == 'assy' else 4
  #end GetPrintScale


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    core = self.dmgr.GetCore()
    if self.config is not None and core is not None:
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
	    node_wd = self.config[ 'pinWidth' ]
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
        pin_gap = self.config[ 'pinGap' ]
	pin_wd = self.config[ 'pinWidth' ]
	pin_adv = pin_wd + pin_gap

	for i in range( len( node_addr_list ) ):
	  node_addr = node_addr_list[ i ]
	  if node_addr >= 0:
	    rel_x = pin_adv if node_addr in ( 1, 3 ) else 0
	    rel_y = pin_adv if node_addr in ( 2, 3 ) else 0
	    node_rect = [
		assy_region[ 0 ] + rel_x,
		assy_region[ 1 ] + rel_y,
		pin_wd, pin_wd
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
	    self.subAddr[ 0 ] < core.npin and \
	    self.subAddr[ 1 ] < core.npin:
          assy_region = self.config[ 'assemblyRegion' ]
	  pin_gap = self.config[ 'pinGap' ]
	  pin_wd = self.config[ 'pinWidth' ]
	  pin_adv = pin_wd + pin_gap
	  rect = \
	    [
	      self.subAddr[ 0 ] * pin_adv + assy_region[ 0 ],
	      self.subAddr[ 1 ] * pin_adv + assy_region[ 1 ],
	      pin_adv, pin_adv
	    ]
	  draw_list.append( ( rect, select_pen ) )
        #end if cell in drawing range
      #end if-else on mode

#			-- Draw?
#			--
      #if rect is not None:
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
  #	METHOD:		Core2DView._InitEventHandlers()			-
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    self._SetMode( 'core' )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.IsTupleCurrent()			-
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
  #	METHOD:		Core2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """
"""
    #self.avgValues.clear()
    self.assemblyAddr = self.state.assemblyAddr
    self.curDataSet = self._FindFirstDataSet()
    self.subAddr = self.state.subAddr
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'nodeAddr',
	'pinDataSet', 'subAddr', 'mode'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Core2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnClick()				-
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
	  sub_addr = self.dmgr.GetSubAddrFromNode( node_addr )
	  if sub_addr != self.subAddr:
	    state_args[ 'sub_addr' ] = sub_addr
	#end if-elif is_aux

      #if ev.GetClickCount() > 1:
      elif ev.GetClickCount() > 1:
        pin_addr = cell_info[ 3 : 5 ]
        if pin_addr != self.subAddr:
	  state_args[ 'sub_addr' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnClick_old()			-
  #----------------------------------------------------------------------
  def _OnClick_old( self, ev ):
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
	if node_addr != self.nodeAddr:
	  state_args[ 'node_addr' ] = node_addr

      if ev.GetClickCount() > 1:
        pin_addr = cell_info[ 3 : 5 ]
        if pin_addr != self.subAddr:
	  state_args[ 'sub_addr' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClick_old


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnDragFinished()			-
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    if right - left == 1 and bottom - top == 1:
      self.assemblyAddr = self.dragStartCell
      self._SetMode( 'assy' )
      self.FireStateChange( assembly_addr = self.assemblyAddr )
    else:
      self._SetMode( 'core' )
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    #if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
    if self.curDataSet:
      self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseMotionAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''

    dset = None
    pin_info = self.FindPin( *ev.GetPosition() )
    if pin_info is not None:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      axial_level = min( self.axialValue[ 1 ], dset.shape[ 2 ] - 1 )
      assy_ndx = self.assemblyAddr[ 0 ]
      pin_factors = None

      if self.nodalMode:
        if self.state.weightsMode == 'on':
          pin_factors = self.dmgr.GetFactors( self.curDataSet )
        node_addr = pin_info[ 2 ]
	if node_addr < dset.shape[ 1 ] and assy_ndx < dset.shape[ 3 ]:
	  pin_factor = 1
	  if pin_factors is not None:
	    pin_factor = pin_factors[ 0, node_addr, axial_level, assy_ndx ]
          pin_value = dset[ 0, node_addr, axial_level, assy_ndx ]
	  if not ( self.dmgr.IsBadValue( pin_value ) or pin_factor == 0 ):
            tip_str = 'Node: %d\n%s: %g' % \
		( node_addr + 1, self.curDataSet.displayName, pin_value )
	#end if node_addr and assy_ndx valid

      else:
        if self.state.weightsMode == 'on':
          pin_factors = self.dmgr.GetFactors( self.curDataSet )
        pin_addr = pin_info[ 0 : 2 ]
        if pin_addr[ 1 ] < dset.shape[ 0 ] and \
	    pin_addr[ 0 ] < dset.shape[ 1 ] and \
	    assy_ndx < dset.shape[ 3 ]:
	  pin_factor = 1
	  if pin_factors is not None:
	    pin_factor = pin_factors[
	        pin_addr[ 1 ], pin_addr[ 0 ],
		axial_level, assy_ndx
		]
          pin_value = \
	      dset[ pin_addr[ 1 ], pin_addr[ 0 ], axial_level, assy_ndx ]
	  if not ( self.dmgr.IsBadValue( pin_value ) or pin_factor == 0 ):
	    pin_rc = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
            tip_str = 'Pin: %s\n%s: %g' % \
	        ( str( pin_rc ), self.curDataSet, pin_value )
      #end if-else nodalMode
    #end if dset

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    pin_info = self.FindPin( *ev.GetPosition() )
    if pin_info is None:
      pass

    elif self.nodalMode:
      node_addr = pin_info[ 2 ]
      valid = self.dmgr.IsValid( self.curDataSet, node_addr = node_addr )
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
      pin_addr = pin_info[ 0 : 2 ]
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      if dset is not None:
        if pin_addr[ 1 ] < dset.shape[ 0 ] and \
	    pin_addr[ 0 ] < dset.shape[ 1 ] and \
	    self.assemblyAddr[ 0 ] < dset.shape[ 3 ]:
          pin_value = dset[
	      pin_addr[ 1 ], pin_addr[ 0 ],
	      min( self.axialValue[ 1 ], ds_value.shape[ 2 ] - 1 ),
	      self.assemblyAddr[ 0 ]
	      ]
	  if not self.dmgr.IsBadValue( pin_value ):
	    self.FireStateChange( sub_addr = pin_addr )
      #end if dset
    #end if-else
  #end _OnMouseUpAssy


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnUnzoom()				-
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
  #	METHOD:		Core2DView.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Core2DView, self ).SaveProps( props_dict )

    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._SetMode()				-
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

	super( Core2DView, self )._InitEventHandlers()
      #end if-else

      self.mode = mode
    #end if different mode
  #end _SetMode


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._UpdateDataSetStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type ):
    """
@param  ds_type		dataset category/type
Updates the nodalMode property.
"""
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._UpdateStateValues()			-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Core2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.dmgr.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
        changed = True
	self.auxNodeAddrs = aux_node_addrs

# Now handled in RasterWidget
#    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
#      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
#      if ds_type and ds_type in self.GetDataSetTypes():
#        resized = True
#	self.nodalMode = self.dmgr.IsNodalType( ds_type )
#        self.curDataSet = kwargs[ 'cur_dataset' ]
#	self._UpdateAxialValue()
#	self.container.GetDataSetMenu().Reset()

    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        changed = True
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr( kwargs[ 'sub_addr' ], 'pin' )
      if sub_addr != self.subAddr:
        changed = True
        self.subAddr = sub_addr
    #end if 'sub_addr'

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Core2DView
