#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		assembly_view.py				-
#	HISTORY:							-
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Calling _ResolveDataRange() instead of DatModel.GetRange()
#	  directly.
#		2016-10-20	leerw@ornl.gov				-
#	  Added auxNodeAddrs and nodeAddr attributes with firing of
#	  node_addr and aux_node_addr state changes on clicks.
#	  Calling DataModel.GetFactors().
#		2016-10-17	leerw@ornl.gov				-
#	  New approach where all dataset types are "primary".
#		2016-10-14	leerw@ornl.gov				-
#	  Using new _DrawValues() method.
#		2016-09-29	leerw@ornl.gov				-
#	  Trying to prevent overrun of values displayed in cells.
#		2016-09-19	leerw@ornl.gov				-
#	  Using state.weightsMode to determine use of pinFactors.
#		2016-09-14	leerw@ornl.gov				-
#	  Using DataModel.pinFactors to determine no-value cells.
#		2016-08-15	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Added clipboard copy option for selected data across all states.
#		2016-08-09	leerw@ornl.gov				-
#	  Including secondary selections in _CreateClipboardSelectionData().
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-09	leerw@ornl.gov				-
#	  Added assembly label in clipboard headers.
#		2016-07-01	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-06-16	leerw@ornl.gov				-
#	  Fixed bug in _HiliteBitmap() when the primary selection
#	  is not visible.
#		2016-04-25	leerw@ornl.gov				-
#	  Starting support for secondary pinColRow selections.
#		2016-04-18	leerw@ornl.gov				-
#	  Using State.scaleMode.
#		2016-03-14	leerw@ornl.gov				-
#	  Added _OnFindMax().
#		2016-02-18	leerw@ornl.gov				-
#	  Added copy selection.
#		2016-02-10	leerw@ornl.gov				-
#	  Title template and string creation now inherited from
#	  RasterWidget.
#		2016-02-08	leerw@ornl.gov				-
#	  Changed GetDataSetType() to GetDataSetTypes().
#		2016-01-25	leerw@ornl.gov				-
#	  Cleaning up the menu mess.
#		2015-12-03	leerw@ornl.gov				-
#	  Using self._CreateValueDisplay().
#		2015-11-28	leerw@ornl.gov				-
#	  Calling DataModel.IsNoDataValue() instead of checking for
#	  gt value to draw.
#		2015-11-19	leerw@ornl.gov				-
#	  Adding support for 'extra' datasets.
#		2015-11-18	leerw@ornl.gov				-
#	  Relaxing to allow any axial and assembly dimensions.
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().
#		2015-07-27	leerw@ornl.gov				-
#	  Fixing order of dataset references to row, col, axial, assy
#	  instead of col, row, ...
#		2015-06-18	leerw@ornl.gov				-
# 	  Extending RasterWidget.
#		2015-05-26	leerw@ornl.gov				-
#	  Migrating to global state.timeDataSet.
#		2015-05-21	leerw@ornl.gov				-
#	  Toggling legend.
#		2015-05-18	leerw@ornl.gov				-
#	  Making the showing of pin labels an option.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#		2015-04-22	leerw@ornl.gov				-
#	  Showing currently selected assembly.
#		2015-04-11	leerw@ornl.gov				-
#	  Transitioning to numbers and adding the capabilities of
#	  core_view.py.
#		2015-04-04	leerw@ornl.gov				-
#		2015-03-11	leerw@ornl.gov				-
#	  Using ExposureSliderBean.
#		2015-03-06	leerw@ornl.gov				-
#	  New Widget.GetImage() for 'loading' image.
#	  Starting ellipse drawing at pixel (1,1).
#		2015-02-06	leerw@ornl.gov				-
#	  New grid system.
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

try:
  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  #from PIL import Image, ImageDraw
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

#from bean.axial_slider import *
#from bean.exposure_slider import *
from data.utils import DataUtils
from event.state import *
from legend import *
from raster_widget import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		Assembly2DView					-
#------------------------------------------------------------------------
class Assembly2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and exposure times or states.

Attrs/properties:
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    self.nodeAddr = -1
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.subAddr = ( -1, -1 )

    super( Assembly2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardDisplayedData() if mode == 'displayed' else \
        self._CreateClipboardSelectedDataAllAxials() \
	  if mode == 'selected_all_axials' else \
        self._CreateClipboardSelectedDataAllStates() \
	  if mode == 'selected_all_states' else \
        self._CreateClipboardSelectedData()
#        self._CreateClipboardSelectionData() \
#        if cur_selection_flag else \
#        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the current assembly selection.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )

      if self.cellRange[ 0 ] <= dset_shape[ 1 ] and \
          self.cellRange[ 1 ] <= dset_shape[ 0 ]:
	pin_row_start = self.cellRange[ 1 ]
	pin_row_end = min( self.cellRange[ 3 ], dset_shape[ 0 ] )
	pin_row_size = pin_row_end - pin_row_start
	pin_col_start = self.cellRange[ 0 ]
	pin_col_end = min( self.cellRange[ 2 ], dset_shape[ 1 ] )
	pin_col_size = pin_col_end - pin_col_start

	clip_data = dset_value[
	    pin_row_start : pin_row_end,
	    pin_col_start : pin_col_end,
	    axial_level, self.assemblyAddr[ 0 ]
	    ]

        #clip_data = dset.value[ :, :, axial_level, self.assemblyAddr[ 0 ] ]
        title = \
            '"%s: Assembly=%d %s; Axial=%.3f; %s=%.3g;' % \
	    (
	    self.pinDataSet,
	    self.assemblyAddr[ 0 ] + 1,
	    self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	    self.axialValue[ 0 ],
	    self.state.timeDataSet,
	    self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
            )
        title += \
	    'Col Range=[%d,%d]; Row Range=[%d,%d]"' % \
	    (
	    pin_col_start + 1, pin_col_end,
	    pin_row_start + 1, pin_row_end
            )
        csv_text = DataModel.ToCSV( clip_data, title )
      #end if data in range

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the current pin selection(s).
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )

      sub_addrs = list( self.auxSubAddrs )
      sub_addrs.insert( 0, self.subAddr )

      csv_text = '"%s: Assembly=%d %s; Axial=%.3f; %s=%.3g"\n' % (
          self.pinDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ],
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      for rc in sub_addrs:
	csv_text += '"(%d,%d)",%.7g\n' % (
	    rc[ 0 ] + 1, rc[ 1 ] + 1,
	    dset_value[ rc[ 1 ], rc[ 0 ], axial_level, assy_ndx ]
	    )
    #end if dset is not None

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:	Assembly2DView._CreateClipboardSelectedDataAllAxials()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedDataAllAxials( self ):
    """Retrieves the data for the current pin selection(s) across all axials.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = self.assemblyAddr[ 0 ],
	#axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      core = self.data.GetCore()
      dset_shape = dset.value.shape
      #axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )

      sub_addrs = list( self.auxSubAddrs )
      sub_addrs.insert( 0, self.subAddr )

      csv_text = '"%s: Assembly=%d %s; %s=%.3g"\n' % (
          self.pinDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      row_text = 'Axial'
      for rc in sub_addrs:
        row_text += ',"(%d,%d)"' % ( rc[ 0 ] + 1, rc[ 1 ] + 1 )
      csv_text += row_text + '\n'

      for axial_level in range( dset_shape[ 2 ] - 1, -1, -1 ):
	row_text = '%.3f' % core.axialMeshCenters[ axial_level ]
	for rc in sub_addrs:
	  row_text += ',%.7g' % \
	      dset.value[ rc[ 1 ], rc[ 0 ], axial_level, assy_ndx ]
	#end for rc

        csv_text += row_text + '\n'
      #end for axial_level
    #end if dset is not None

    return  csv_text
  #end _CreateClipboardSelectedDataAllAxials


  #----------------------------------------------------------------------
  #	METHOD:	Assembly2DView._CreateClipboardSelectedDataAllStates()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedDataAllStates( self ):
    """Retrieves the data for the current pin selection(s) across all states.
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_shape = dset.value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )

      sub_addrs = list( self.auxSubAddrs )
      sub_addrs.insert( 0, self.subAddr )

      csv_text = '"%s: Assembly=%d %s; Axial=%.3f"\n' % (
          self.pinDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ]
          )
      row_text = self.state.timeDataSet
      for rc in sub_addrs:
        row_text += ',"(%d,%d)"' % ( rc[ 0 ] + 1, rc[ 1 ] + 1 )
      csv_text += row_text + '\n'

      for state_ndx in range( 0, self.data.GetStatesCount() ):
        dset = self.data.GetStateDataSet( state_ndx, self.pinDataSet )
	if dset is not None:
	  row_text = '%.3g' % \
	      self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
	  for rc in sub_addrs:
	    row_text += ',%.7g' % \
	        dset.value[ rc[ 1 ], rc[ 0 ], axial_level, assy_ndx ]
	  #end for rc

          csv_text += row_text + '\n'
	#end if dset
      #end for state_ndx
    #end if dset is not None

    return  csv_text
  #end _CreateClipboardSelectedDataAllStates


  #----------------------------------------------------------------------
  #	METHOD:	Assembly2DView._CreateClipboardSelectionData_orig()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectionData_orig( self ):
    """Retrieves the data for the current pin selection(s).
@return			text or None
"""
    csv_text = None
    dset = None
    is_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = self.assemblyAddr[ 0 ],
	axial_level = self.axialValue[ 1 ],
	state_index = self.stateIndex
	)
    if is_valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )

    if dset is not None:
      dset_value = dset.value
      dset_shape = dset_value.shape
      axial_level = min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 )
      assy_ndx = min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )

      pin_row = min( self.subAddr[ 1 ], dset_shape[ 0 ] - 1 )
      pin_col = min( self.subAddr[ 0 ], dset_shape[ 1 ] - 1 )
      #clip_data = dset_value[ pin_row, pin_col, axial_level, assy_ndx ]
      clip_data = np.ndarray( ( 1, ), dtype = np.float64 )
      clip_data[ 0 ] = dset_value[ pin_row, pin_col, axial_level, assy_ndx ]

      title = '"%s: Assembly=%d %s; Axial=%.3f; Pin=(%d,%d); %s=%.3g"' % (
          self.pinDataSet,
	  assy_ndx + 1,
	  self.data.core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] ),
	  self.axialValue[ 0 ],
	  pin_col + 1, pin_row + 1,
	  self.state.timeDataSet,
	  self.data.GetTimeValue( self.stateIndex, self.state.timeDataSet )
          )
      csv_text = DataModel.ToCSV( clip_data, title )
    #end if dset is not None

    return  csv_text
  #end _CreateClipboardSelectionData_orig


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateDrawConfig()		-
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
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
    pinGap
    pinWidth
    valueFont
    valueFontSize
"""
    #ds_range = self.data.GetRange
    ds_range = self._ResolveDataRange(
        self.pinDataSet,
	self.stateIndex if self.state.scaleMode == 'state' else -1
	)
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
      pin_adv_wd = region_wd / self.cellRange[ -2 ]

      working_ht = max( ht, legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size * 3 / 2)
      pin_adv_ht = region_ht / self.cellRange[ -1 ]

      if pin_adv_ht < pin_adv_wd:
        pin_adv_wd = pin_adv_ht

      pin_gap = pin_adv_wd >> 3
      pin_wd = max( 1, pin_adv_wd - pin_gap )

      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

    else:
      pin_wd = kwargs[ 'scale' ] if 'scale' in kwargs else 20

      pin_gap = pin_wd >> 3
      assy_wd = self.cellRange[ -2 ] * (pin_wd + pin_gap)
      assy_ht = self.cellRange[ -1 ] * (pin_wd + pin_gap)

      # label : core : font-sp : legend
      wd = label_size[ 0 ] + assy_wd + (font_size << 1) + legend_size[ 0 ]
      ht = max( assy_ht, legend_size[ 1 ] )
      ht += (font_size << 1) + font_size

      config[ 'clientSize' ] = ( wd, ht )
    #end if-else

    value_font_size = pin_wd >> 1
    value_font = \
        PIL.ImageFont.truetype( self.valueFontPath, value_font_size ) \
	if value_font_size >= 6 else None
#    value_font_smaller_size = value_font_size - (value_font_size / 6)
#    value_font_smaller = \
#        PIL.ImageFont.truetype( self.valueFontPath, value_font_smaller_size ) \
#	if value_font_size >= 4 else None

    config[ 'assemblyRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, assy_wd, assy_ht ]
    config[ 'lineWidth' ] = max( 1, pin_gap )
    config[ 'pinGap' ] = pin_gap
    config[ 'pinWidth' ] = pin_wd
    config[ 'valueFont' ] = value_font
    config[ 'valueFontSize' ] = value_font_size
#    config[ 'valueFontSmaller' ] = value_font_smaller

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateMenuDef()			-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( Assembly2DView, self )._CreateMenuDef( data_model )

    ndx = 0
    for item in menu_def:
      if item.get( 'label', '' ) == 'Copy Selected Data':
        break
      ndx += 1
    #end for

    if ndx < len( menu_def ):
      new_item = \
        {
	'label': 'Copy Selected Data All States',
	'handler': functools.partial( self._OnCopyData, 'selected_all_states' )
	}
      menu_def.insert( ndx + 1, new_item )

      new_item = \
        {
	'label': 'Copy Selected Data All Axials',
	'handler': functools.partial( self._OnCopyData, 'selected_all_axials' )
	}
      menu_def.insert( ndx + 1, new_item )

    return  menu_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateRasterImage()		-
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in	0-based ( state_index, axial_level, assy_ndx )
@param  config		optional config to use instead of self.config
"""
    state_ndx = tuple_in[ 0 ]
    assy_ndx = tuple_in[ 1 ]
    axial_level = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    im = None
    dset_array = None

    tuple_valid = DataModel.IsValidObj(
	self.data,
        assembly_addr = assy_ndx,
	axial_level = axial_level,
	state_index = state_ndx
	)

    if config is None:
      config = self.config
    if config is not None and tuple_valid:
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

      dset = self.data.GetStateDataSet( state_ndx, self.pinDataSet )
      pin_factors = None
      if self.state.weightsMode == 'on':
#        pin_factors = self.data.GetPinFactors()
        pin_factors = self.data.GetFactors( self.pinDataSet )
        pin_factors_shape = pin_factors.shape

      #dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
      #ds_value = dset.value if dset is not None else None
      if dset is None:
        dset_array = None
	dset_shape = ( 0, 0, 0, 0 )
      else:
        dset_array = dset.value
        dset_shape = dset.shape
#      ds_range = self.data.GetRange(
#          self.pinDataSet,
#	  state_ndx if self.state.scaleMode == 'state' else -1
#	  )
      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      title_templ, title_size = self._CreateTitleTemplate(
	  pil_font, self.pinDataSet, dset_shape, self.state.timeDataSet,
	  assembly_ndx = 3, axial_ndx = 2
	  )
    #end if valid config

#			-- Must be valid assy ndx
#			--
    if dset_array is not None and assy_ndx < dset_shape[ 3 ]:
      axial_level = min( axial_level, dset_shape[ 2 ] - 1 )

#			-- Create image
#			--
      im = PIL.Image.new( "RGBA", ( im_wd, im_ht ) )
      #im_pix = im.load()
      im_draw = PIL.ImageDraw.Draw( im )
      value_draw_list = []

      nodata_pen_color = ( 155, 155, 155, 255 )

#			-- Loop on rows
#			--
      pin_y = assy_region[ 1 ]
      for pin_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
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
	for pin_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
#					-- Column label
#					--
	  if pin_row == self.cellRange[ 1 ] and self.showLabels:
	    label = '%d' % (pin_col + 1)
	    label_size = label_font.getsize( label )
	    label_x = pin_x + ((pin_wd - label_size[ 0 ]) >> 1)
	    im_draw.text(
	        ( label_x, 1 ),
	        label, fill = ( 0, 0, 0, 255 ), font = label_font
	        )
	  #end if writing column label

#	  if ds_value is not None:
#	    #DataModel.GetPinIndex( assy_ndx, axial_level, pin_col, pin_row )
#	    value = ds_value[ pin_row, pin_col, axial_level, assy_ndx ]
	  if pin_row < dset_shape[ 0 ] and pin_col < dset_shape[ 1 ]:
	    value = dset_array[ pin_row, pin_col, axial_level, assy_ndx ]
	  else:
	    value = 0.0

	  if pin_factors is None:
	    pin_factor = 1
	  elif pin_row < pin_factors_shape[ 0 ] and \
	      pin_col < pin_factors_shape[ 1 ]:
	    pin_factor = pin_factors[ pin_row, pin_col, axial_level, assy_ndx ]
	  else:
	    pin_factor = 0

	  #if not self.data.IsNoDataValue( self.pinDataSet, value ):
	  #if pin_factor != 0:
	  if not ( self.data.IsBadValue( value ) or pin_factor == 0 ):
	    brush_color = Widget.GetColorTuple(
	        value - ds_range[ 0 ], value_delta, 255
	        )
	    pen_color = Widget.GetDarkerColor( brush_color, 255 )

	    #im_draw.ellipse
	    im_draw.rectangle(
	        [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	        fill = brush_color, outline = pen_color
	        )

	    if value_font is not None:
	      value_draw_list.append((
	          self._CreateValueString( value, 3 ),
                  Widget.GetContrastColor( *brush_color ),
                  pin_x, pin_y, pin_wd, pin_wd
                  ))
#	      value_str, value_size, tfont = self._CreateValueDisplay(
#	          value, 3, value_font, pin_wd, value_font_size
#		  )
#	      if value_str:
#		value_x = pin_x + ((pin_wd - value_size[ 0 ]) >> 1)
#		value_y = pin_y + ((pin_wd - value_size[ 1 ]) >> 1) 
#                im_draw.text(
#		    ( value_x, value_y ), value_str,
#		    fill = Widget.GetContrastColor( *brush_color ),
#		    font = tfont
#                    )
	    #end if value_font defined

	  else:
	    im_draw.rectangle(
	        [ pin_x, pin_y, pin_x + pin_wd, pin_y + pin_wd ],
	        fill = None, outline = nodata_pen_color
	        )
	  #end else good value not hidden by pin_factor

	  pin_x += pin_wd + pin_gap
	#end for pin_col

	pin_y += pin_wd + pin_gap
      #end for pin_row

#			-- Draw Values
#			--
      if value_draw_list:
        self._DrawValues( value_draw_list, im_draw )

#			-- Draw Legend Image
#			--
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
	  axial = self.data.core.axialMeshCenters[ axial_level ],
	  time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      title_size = pil_font.getsize( title_str )
      title_x = max(
	  font_size,
	  (assy_region[ 0 ] + assy_region[ 2 ] - title_size[ 0 ]) >> 1
#(assy_region[ 2 ] + font_size + legend_size[ 0 ] - title_size[ 0 ]) >> 1
	  )

      im_draw.text(
          ( title_x, pin_y ),
	  title_str, fill = ( 0, 0, 0, 255 ), font = pil_font
          )

      del im_draw
    #end if valid assy_ndx

    #return  im
    return  im if im is not None else self.emptyPilImage
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateStateTuple()		-
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return			( state_index, assy_ndx, axial_level )
"""
    return  ( self.stateIndex, self.assemblyAddr[ 0 ], self.axialValue[ 1 ] )
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._CreateToolTipText()		-
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info	tuple returned from FindCell()
"""
    tip_str = ''
    valid = cell_info is not None and \
        self.data.IsValid(
            assembly_addr = self.assemblyAddr,
	    axial_level = self.axialValue[ 1 ],
	    sub_addr = cell_info[ 1 : 3 ],
	    sub_addr_mode = 'pin',
	    state_index = self.stateIndex
	    )

    if valid:
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
      value = None
      if cell_info[ 2 ] < dset_shape[ 0 ] and cell_info[ 1 ] < dset_shape[ 1 ]:
        value = dset[
            cell_info[ 2 ], cell_info[ 1 ],
	    min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 ),
	    min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
	    ]

      if not self.data.IsBadValue( value ):
        show_pin_addr = ( cell_info[ 1 ] + 1, cell_info[ 2 ] + 1 )
	tip_str = \
	    'Pin: %s\n%s: %g' % \
	    ( str( show_pin_addr ), self.pinDataSet, value )
    #end if valid

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.FindCell()			-
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindPin() and prepends -1 for an index value for drag processing.
@return			None if no match, otherwise tuple of
			( -1, 0-based cell_col, cell_row )
"""
    pin_addr = self.FindPin( ev_x, ev_y )
    return \
        None if pin_addr is None else \
	( -1, pin_addr[ 0 ], pin_addr[ 1 ] )
  #end FindCell


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.FindPin()			-
  #----------------------------------------------------------------------
  def FindPin( self, ev_x, ev_y ):
    """Finds the pin col and row.
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
	    int( (ev_x - assy_region[ 0 ]) / pin_size ) + self.cellRange[ 0 ],
	    self.cellRange[ 2 ] - 1
	    )
	cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
	    int( (ev_y - assy_region[ 1 ]) / pin_size ) + self.cellRange[ 1 ],
	    self.cellRange[ 3 ] - 1
	    )
	cell_y = max( self.cellRange[ 1 ], cell_y )
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
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin', ':radial' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
	STATE_CHANGE_stateIndex
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetInitialCellRange()		-
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """This implementation returns self.data.ExtractSymmetryExtent().
Subclasses should override as needed.
@return			intial range of raster cells
			( left, top, right, bottom, dx, dy )
"""
    result = None
    if self.data is not None:
      result = [
          0, 0,
	  self.data.core.npin, self.data.core.npin,
	  self.data.core.npin, self.data.core.npin
          ]
    return  result
  #end GetInitialCellRange


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Assembly 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._HiliteBitmap()			-
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap ):
    result = bmap

    if self.config is not None:
      addr_list = list( self.auxSubAddrs )
      addr_list.insert( 0, self.subAddr )

      new_bmap = None
      dc = None
      secondary_pen = None

      assy_region = self.config[ 'assemblyRegion' ]
      pin_gap = self.config[ 'pinGap' ]
      pin_wd = self.config[ 'pinWidth' ]
      pin_adv = pin_gap + pin_wd
      line_wd = self.config[ 'lineWidth' ]

      for i in range( len( addr_list ) ):
	addr = addr_list[ i ]
        rel_col = addr[ 0 ] - self.cellRange[ 0 ]
        rel_row = addr[ 1 ] - self.cellRange[ 1 ]

        if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
            rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	  if new_bmap is None:
	    new_bmap = self._CopyBitmap( bmap )
            dc = wx.MemoryDC( new_bmap )
	    gc = wx.GraphicsContext.Create( dc )

	  if i == 0:
	    gc.SetPen(
	        wx.ThePenList.FindOrCreatePen(
	            wx.Colour( 255, 0, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
		    )
	        )
	  elif secondary_pen is None:
	    secondary_pen = wx.ThePenList.FindOrCreatePen(
	        wx.Colour( 255, 255, 0, 255 ), line_wd, wx.PENSTYLE_SOLID
	        )
	    gc.SetPen( secondary_pen )

	  rect = \
	    [
	      rel_col * pin_adv + assy_region[ 0 ],
	      rel_row * pin_adv + assy_region[ 1 ],
	      pin_wd + 1, pin_wd + 1
	    ]
	  path = gc.CreatePath()
	  path.AddRectangle( *rect )
	  gc.StrokePath( path )
        #end if addr within range
      #end for i

      if dc is not None:
        dc.SelectObject( wx.NullBitmap )
      if new_bmap is not None:
        result = new_bmap
    #end if self.config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._HiliteBitmap_0()		-
  #----------------------------------------------------------------------
  def _HiliteBitmap_0( self, bmap ):
    result = bmap

    if self.config is not None:
      rel_col = self.subAddr[ 0 ] - self.cellRange[ 0 ]
      rel_row = self.subAddr[ 1 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
	assy_region = self.config[ 'assemblyRegion' ]
        pin_gap = self.config[ 'pinGap' ]
        pin_wd = self.config[ 'pinWidth' ]
	pin_adv = pin_gap + pin_wd
        line_wd = self.config[ 'lineWidth' ]

	rect = \
	  [
	    rel_col * pin_adv + assy_region[ 0 ],
	    rel_row * pin_adv + assy_region[ 1 ],
	    pin_wd + 1, pin_wd + 1
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
  #end _HiliteBitmap_0


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.IsTupleCurrent()			-
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl		tuple of state values
@return			True if it matches the current state, false otherwise
"""
    result = \
        tpl is not None and len( tpl ) >= 3 and \
	tpl[ 0 ] == self.stateIndex and \
	tpl[ 1 ] == self.assemblyAddr[ 0 ] and \
	tpl[ 2 ] == self.axialValue[ 1 ]
    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self ):
    """This noop version should be implemented in subclasses to initialize
attributes/properties that aren't already set in _LoadDataModel():
  axialValue
  stateIndex
"""
    self.assemblyAddr = self.state.assemblyAddr
    self.pinDataSet = self._FindFirstDataSet( self.state.curDataSet )
    self.subAddr = self.state.subAddr
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict	dict object from which to deserialize properties
"""
    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'pinDataSet', 'subAddr'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( Assembly2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    #ev.Skip()
    is_aux = self.IsAuxiliaryEvent( ev )

#		-- Validate
#		--
    valid = False
    pin_addr = self.FindPin( *ev.GetPosition() )

    if pin_addr is not None and pin_addr != self.subAddr:
      valid = self.data.IsValid(
          assembly_addr = self.assemblyAddr[ 0 ],
	  axial_level = self.axialValue[ 1 ],
	  sub_addr = pin_addr,
	  state_index = self.stateIndex
	  )

    if valid:
#      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
#      dset_shape = dset.shape if dset is not None else ( 0, 0, 0, 0 )
#      value = 0.0
#      if pin_addr[ 1 ] < dset_shape[ 0 ] and pin_addr[ 0 ] < dset_shape[ 1 ]:
#        value = dset[
#            pin_addr[ 1 ], pin_addr[ 0 ],
#	    min( self.axialValue[ 1 ], dset_shape[ 2 ] - 1 ),
#	    min( self.assemblyAddr[ 0 ], dset_shape[ 3 ] - 1 )
#	    ]
      #if not self.data.IsNoDataValue( self.pinDataSet, value ):
      #xxxxx node_addr = self.data.GetNodeAddr( ( pin_col, pin_row ) )
      if is_aux:
	addrs = list( self.auxSubAddrs )
	if pin_addr in addrs:
	  addrs.remove( pin_addr )
	else:
	  addrs.append( pin_addr )
	#self.FireStateChange( aux_sub_addrs = addrs )
	node_addrs = self.data.NormalizeNodeAddrs(
	    self.auxNodeAddrs + self.data.GetNodeAddrs( addrs )
	    )
	self.FireStateChange(
	    aux_node_addrs = node_addrs,
	    aux_sub_addrs = addrs
	    )

      else:
        #self.FireStateChange( sub_addr = pin_addr, aux_sub_addrs = [] )
        #state_args = { 'aux_sub_addrs': [] 'sub_addr': pin_addr }
	state_args = dict(
	    aux_node_addrs = [],
	    aux_sub_addrs = [],
	    sub_addr = pin_addr
	    )
	node_addr = self.data.GetNodeAddr( pin_addr )
	if node_addr >= 0:
	  state_args[ 'node_addr' ] = node_addr
        self.FireStateChange( **state_args )
      #end if-else is_aux
    #end if valid
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnFindMax()			-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Calls _OnFindMaxPin().
"""
    if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
      self._OnFindMaxPin( self.pinDataSet, all_states_flag )
  #end _OnFindMax


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
      self._OnFindMinMaxPin( mode, self.pinDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict	dict object to which to serialize properties
"""
    super( Assembly2DView, self ).SaveProps( props_dict )

    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'subAddr'
	):
      props_dict[ k ] = getattr( self, k )

    if self.data is not None:
      for k in ( 'pinDataSet', ):
        props_dict[ k ] = self.data.RevertIfDerivedDataSet( getattr( self, k ) )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    """May be called from any thread.
"""
    if ds_name != self.pinDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = ds_name )
      self.FireStateChange( cur_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Assembly2DView._UpdateStateValues()		-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return			kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( Assembly2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

    if 'aux_node_addrs' in kwargs:
      aux_node_addrs = \
          self.data.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )
      if aux_node_addrs != self.auxNodeAddrs:
	self.auxNodeAddrs = aux_node_addrs

    if 'aux_sub_addrs' in kwargs:
      aux_sub_addrs = \
          self.data.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'pin' )
      if aux_sub_addrs != self.auxSubAddrs:
        changed = True
	self.auxSubAddrs = aux_sub_addrs

    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.pinDataSet:
      ds_type = self.data.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        resized = True
        self.pinDataSet = kwargs[ 'cur_dataset' ]
	self.container.GetDataSetMenu().Reset()

    if 'node_addr' in kwargs:
      node_addr = self.data.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.data.NormalizeSubAddr( kwargs[ 'sub_addr' ], 'pin' )
      if sub_addr != self.subAddr:
        changed = True
	self.subAddr = sub_addr

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end Assembly2DView
