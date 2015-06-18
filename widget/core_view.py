#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		core_view.py					-
#	HISTORY:							-
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
    self.assemblyIndex = ( -1, -1, -1 )
    self.avgValues = {}

#    self.menuDef = \
#      [
#	( 'Hide Labels', self._OnToggleLabels ),
#	( 'Hide Legend', self._OnToggleLegend ),
#        ( 'Unzoom', self._OnUnzoom )
#      ]
    self.mode = ''  # 'assy', 'core'
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )

    super( Core2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CalcAvgValues()			-
  #----------------------------------------------------------------------
  def _CalcAvgValues( self, data, state_ndx, force = False ):
    if (force or (state_ndx not in self.avgValues)) and \
	self.pinDataSet in data.states[ state_ndx ].group:
      ds_values = data.states[ state_ndx ].group[ self.pinDataSet ].value
      avg_values = np.zeros( shape = ( data.core.nax, data.core.nass ) )

      for ax in range( data.core.nax ):  # pp_powers.shape( 2 )
        for assy in range( data.core.nass ):  # pp_powers.shape( 3 )
          if data.core.pinVolumesSum > 0.0:
	    avg_values[ ax, assy ] = \
	        np.sum( ds_values[ :, :, ax, assy ] ) / data.core.pinVolumesSum
          else:
	    avg_values[ ax, assy ] = np.mean( ds_values[ :, :, ax, assy ] )
        #end for assy
      #end for ax

      self.avgValues[ state_ndx ] = avg_values
    #end if
  #end _CalcAvgValues


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

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      pin_adv_wd = region_wd / self.data.core.npin

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / self.data.core.npin

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      assy_wd = assy_ht = self.data.core.npin * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 24
      print >> sys.stderr, '[Assembly2DView._CreateDrawConfig] pin_wd=%d' % pin_wd

      pin_gap = pin_wd >> 3
      assy_wd = assy_ht = self.data.core.npin * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'mode' ] = 'assy'
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateAssyDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateAssyImage()			-
  #----------------------------------------------------------------------
  def _CreateAssyImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based
			( state_index, assy_ndx, axial_level, assy_col, assy_row )
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    print >> sys.stderr, \
        '[Core2DView._CreateAssyImage] tuple_in=%s' % str( tuple_in )
    im = None

    tuple_valid = DataModel.IsValidObj(
	self.data,
        assembly_index = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)
    if self.config != None and tuple_valid:
      assy_region = self.config[ 'assemblyRegion' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]
      pin_gap = self.config[ 'pinGap' ]
      pin_wd = self.config[ 'pinWidth' ]

      title_fmt = '%s: Assembly %%d, Axial %%.3f, %s %%.3g' % \
          ( self.pinDataSet, self.state.timeDataSet )
      #title_fmt = '%s: Assembly %%d, Axial %%.3f, Exposure %%.3f' % self.pinDataSet
      title_size = pil_font.getsize( title_fmt % ( 99, 99.999, 99.999 ) )

      ds_value = \
          self.data.states[ state_ndx ].group[ self.pinDataSet ].value \
	  if self.pinDataSet in self.data.states[ state_ndx ].group \
	  else None
      ds_range = self.data.GetRange( self.pinDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )

      pin_y = assy_region[ 1 ]
      for pin_row in range( self.data.core.npin ):
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
	for pin_col in range( self.data.core.npin ):
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

	  value = 0.0
	  if ds_value != None:
#	    value = ds_value[ pin_col, pin_row, axial_level, assy_ndx ]
	    value = ds_value[ pin_row, pin_col, axial_level, assy_ndx ]
	  if value > 0.0:
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )
	    #brush_color = ( pen_color[ 0 ], pen_color[ 1 ], pen_color[ 2 ], 255 )

	    im_draw.ellipse(
	        [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	        fill = brush_color, outline = pen_color
	        )
	  #end if value > 0

	  pin_x += pin_wd + pin_gap
	#end for pin_col

	pin_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw Legend Image
#			--
#      im.paste( legend_pil_im, ( assy_wd + font_size, 1 ) )
      if legend_pil_im != None:
        im.paste(
	    legend_pil_im,
	    ( assy_region[ 2 ] + 2 + font_size, assy_region[ 1 ] )
	    )
	legend_size = legend_pil_im.size
      else:
	legend_size = ( 0, 0 )

#			-- Draw Title String
#			--
      pin_y = max( pin_y, legend_size[ 1 ] )
      pin_y += font_size >> 2

      title_str = title_fmt % ( \
	  assy_ndx + 1,
	  self.data.core.axialMeshCenters[ axial_level ],
	  self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
#	  self.data.states[ state_ndx ].exposure
	  )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  0,
          (assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, pin_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if self.config exists

    return  im
  #end _CreateAssyImage


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

#		-- Must calculate scale?
#		--
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend
      region_wd = wd - label_size[ 0 ] - 2 - (font_size << 1) - legend_size[ 0 ]
      assy_wd = region_wd / self.cellRange[ -2 ]

#      working_ht = max( ht, legend_pil_im.size[ 1 ] )
      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      assy_ht = region_ht / self.cellRange[ -1 ]

      if assy_ht < assy_wd:
        assy_wd = assy_ht

      pin_wd = max( 1, (assy_wd - 2) / self.data.core.npin )
      assy_wd = pin_wd * self.data.core.npin + 1
      assy_advance = assy_wd
      core_wd = self.cellRange[ -2 ] * assy_advance
      core_ht = self.cellRange[ -1 ] * assy_advance

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 4
      print >> sys.stderr, '[Core2DView._CreateCoreDrawConfig] pin_wd=%d' % pin_wd
      assy_wd = pin_wd * self.data.core.npin + 1
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
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'lineWidth' ] = max( 1, min( 10, int( assy_wd / 20.0 ) ) )
    config[ 'mode' ] = 'core'
    config[ 'pinWidth' ] = pin_wd

    return  config
  #end _CreateCoreDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateCoreImage()			-
  #----------------------------------------------------------------------
  def _CreateCoreImage( self, tuple_in ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level )
"""
    state_ndx = tuple_in[ 0 ]
    axial_level = tuple_in[ 1 ]
    print >> sys.stderr, \
        '[Core2DView._CreateCoreImage] tuple_in=%d,%d' % \
	( state_ndx, axial_level )
    im = None

    if self.config != None:
      assy_advance = self.config[ 'assemblyAdvance' ]
      assy_wd = self.config[ 'assemblyWidth' ]
      im_wd, im_ht = self.config[ 'clientSize' ]
      core_region = self.config[ 'coreRegion' ]
      font_size = self.config[ 'fontSize' ]
      label_font = self.config[ 'labelFont' ]
      legend_pil_im = self.config[ 'legendPilImage' ]
      pil_font = self.config[ 'pilFont' ]
      pin_wd = self.config[ 'pinWidth' ]

      title_fmt = '%s: Axial %%.3f, %s %%.3g' % \
          ( self.pinDataSet, self.state.timeDataSet )
      title_size = pil_font.getsize( title_fmt % ( 99, 99.999 ) )

      ds_value = \
          self.data.states[ state_ndx ].group[ self.pinDataSet ].value \
	  if self.pinDataSet in self.data.states[ state_ndx ].group \
	  else None
      ds_range = self.data.GetRange( self.pinDataSet )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

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

	  if assy_ndx >= 0:
	    pin_y = assy_y + 1
	    for pin_row in range( self.data.core.npin ):
	      pin_x = assy_x + 1
	      for pin_col in range( self.data.core.npin ):
		value = 0.0
	        if ds_value != None:
		  value = ds_value[ pin_row, pin_col, axial_level, assy_ndx ]
		if value > 0.0:
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
      if legend_pil_im != None:
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

      title_str = title_fmt % ( \
	  self.data.core.axialMeshCenters[ axial_level ],
	  self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
#	  self.data.states[ state_ndx ].exposure
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

    return  im
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
    return \
        self._CreateAssyDrawConfig( **kwargs ) if self.mode == 'assy' else \
	self._CreateCoreDrawConfig( **kwargs )
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._CreateRasterImage()			-
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
        ( self.stateIndex, self.assemblyIndex[ 0 ], self.axialValue[ 1 ],
	  self.assemblyIndex[ 1 ], self.assemblyIndex[ 2 ] ) \
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

    if self.mode == 'core' and cell_info != None and cell_info[ 0 ] >= 0:
      if self.stateIndex in self.avgValues:
        avg_value = self.avgValues[ self.stateIndex ][ self.axialValue[ 1 ], cell_info[ 0 ] ]
      else:
        avg_value = 0.0

      show_assy_addr = self.data.core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
      tip_str = 'Assy: %d %s\n%s %s: %.3g' % \
          ( cell_info[ 0 ] + 1, show_assy_addr,
	    'Avg' if self.data.core.pinVolumesSum > 0.0 else 'Mean',
	    self.pinDataSet, avg_value )

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
			( 0-based index, cell_col, cell_row, pin_col, pin_row )
"""
    result = None

    if self.config != None and self.data != None and \
        self.data.core != None and self.data.core.coreMap != None:
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
  #	METHOD:		Core2DView.FindCell()				-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
"""
    return \
        self.FindPin( ev_x, ev_y ) if self.mode == 'assy' else \
        self.FindAssembly( ev_x, ev_y )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.FindPin()				-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin index.
@param  ev_x		event x coordinate (relative to this)
@param  ev_y		event y coordinate (relative to this)
@return			None if no match, otherwise tuple of
			( 0-based cell_col, cell_row )
"""
    result = None

    if self.config != None and self.data != None:
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
  #	METHOD:		Core2DView.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.GetEventLockSet()			-
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
  #	METHOD:		Core2DView.GetPrintScale()			-
  #----------------------------------------------------------------------
  def GetPrintScale( self ):
    """Should be overridden by subclasses.
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

    if self.config != None:
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
      if rect != None:
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
    #end if self.config != None:

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
          tpl != None and len( tpl ) >= 5 and \
          tpl[ 0 ] == self.stateIndex and \
	  tpl[ 1 ] == self.assemblyIndex[ 0 ] and \
	  tpl[ 2 ] == self.axialValue[ 1 ] and \
	  tpl[ 3 ] == self.assemblyIndex[ 1 ] and \
	  tpl[ 4 ] == self.assemblyIndex[ 2 ]

    else:
      result = \
          tpl != None and len( tpl ) >= 2 and \
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
    self.avgValues.clear()
    self.assemblyIndex = self.state.assemblyIndex
    self.pinDataSet = self.state.pinDataSet
    self.pinColRow = self.state.pinColRow
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnClick()				-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()

    cell_info = self.FindAssembly( x, y )
    if cell_info != None and cell_info[ 0 ] >= 0:
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
  #	METHOD:		Core2DView._OnDragFinished()			-
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
  #	METHOD:		Core2DView._OnMouseMotionAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseMotionAssy( self, ev ):
    """
"""
    tip_str = ''
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None:
      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	pin_value = ds_value[
	    pin_addr[ 0 ], pin_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if pin_value > 0:
	pin_rc = ( pin_addr[ 0 ] + 1, pin_addr[ 1 ] + 1 )
        tip_str = 'Pin: %s\n%s: %g' % ( str( pin_rc ), ds_name, pin_value )
    #end if pin found

    self.bitmapCtrl.SetToolTipString( tip_str )
  #end _OnMouseMotionAssy


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView._OnMouseUpAssy()			-
  #----------------------------------------------------------------------
  def _OnMouseUpAssy( self, ev ):
    """
"""
    pin_addr = self.FindPin( *ev.GetPosition() )
    if pin_addr != None and pin_addr != self.pinColRow:
#      print >> sys.stderr, \
#          '[Assembly2DView._OnMouseUp] new pinColRow=%s' % str( pin_addr )

      state_ndx = self.stateIndex
      ds_name = self.pinDataSet
      pin_value = 0.0
      if ds_name in self.data.states[ state_ndx ].group:
        ds_value = self.data.states[ state_ndx ].group[ ds_name ].value
	pin_value = ds_value[
	    pin_addr[ 0 ], pin_addr[ 1 ],
	    self.axialValue[ 1 ], self.assemblyIndex[ 0 ]
	    ]
#	    self.axialBean.axialLevel, self.assemblyIndex

      if pin_value > 0.0:
	self.FireStateChange( pin_colrow = pin_addr )
    #end if pin_addr changed
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
      self._OnSize( None )
  #end _OnUnzoom


  #----------------------------------------------------------------------
  #	METHOD:		Core2DView.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.pinDataSet:
      wx.CallAfter( self._UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
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
  #	METHOD:		Core2DView._UpdateStateValues()			-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Core2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
      changed = True
      self.assemblyIndex = kwargs[ 'assembly_index' ]

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
      changed = True
      self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

    if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
      resized = True
      self.pinDataSet = kwargs[ 'pin_dataset' ]
      self.avgValues.clear()

    if changed and self.config != None:
      self._CalcAvgValues( self.data, self.stateIndex )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Core2DView
