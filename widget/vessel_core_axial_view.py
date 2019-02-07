#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           vessel_core_axial_view.py                       -
#       HISTORY:                                                        -
#               2019-01-18      leerw@ornl.gov                          -
#         Transition from tally to fluence.
#               2018-03-02      leerw@ornl.gov                          -
#         Migrating to _CreateEmptyBitmapAndDC().
#               2018-02-06      leerw@ornl.gov                          -
#         Fixing scaling issues.
#               2018-02-05      leerw@ornl.gov                          -
#         Moving Linux/GTK/X11 image manipulation to the UI thread.
#               2018-02-03      leerw@ornl.gov                          -
#         Starting in middle of assembly for quarter symmetry.
#               2018-01-09      leerw@ornl.gov                          -
#         Implementing core slice along azimuth.
#               2017-11-17      leerw@ornl.gov                          -
#         Migrating to wx.Bitmap instead of PIL.Image.
#               2017-09-22      leerw@ornl.gov                          -
#         Added theta_rad to the drawing state tuple.
#               2017-09-18      leerw@ornl.gov                          -
#         Fixed baffle draw in _DrawVesselComponents().
#         Limited axial vessel vertical display to axialCoreDy (pixels).
#               2017-09-14      leerw@ornl.gov                          -
#         In LoadProps() converting tallyAddr[0] from a dict to a
#         DataSetName instance.
#               2017-09-11      leerw@ornl.gov                          -
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

#try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
#  #from PIL import Image, ImageDraw
#except Exception:
#  raise ImportError, 'The Python Imaging Library (PIL) is required for this component'

from data.datamodel import *
from data.utils import *
from event.state import *

from .raster_widget import *
from .widget import *


_DEBUG_ = False

#PI_OVER_2 = math.pi / 2.0
#TWO_PI = math.pi * 2.0


#------------------------------------------------------------------------
#       CLASS:          VesselCoreAxial2DView                           -
#------------------------------------------------------------------------
class VesselCoreAxial2DView( RasterWidget ):
  """Pin-by-pin assembly view across axials and states.

  21.6 * 8 =  172.8
  vessel  mod 187.96        ! barrel IR (cm)
           ss 193.68        ! barrel OR (cm)
          mod 219.15        ! vessel liner IR (cm)
           ss 219.71        ! vessel liner OR / vessel IR (cm)
           cs 241.70        ! vessel OR (cm)

  pad ss  194.64 201.63 32 45 135 225 315 ! neutron pad ID,OD arc length
(degrees), and angular positions (degrees)

Properties:
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.__init__()                -
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    """
"""
    self.angleSlider = None

    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.channelMode = False

    self.fluenceAddr = FluenceAddress( radiusIndex = 0, thetaIndex = 0 )
    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    #self.vesselShowPad = True
                        # offsets in cm to edge given current cellRange
    self.vesselOffset = [ 0, 0 ]

    super( VesselCoreAxial2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD: VesselCoreAxial2DView._CreateAdditionalUIControls()     -
  #----------------------------------------------------------------------
  def _CreateAdditionalUIControls( self ):
    """Creates a 'top' slider for selecting the view angle.

@return                 { 'top': panel }
"""
    panel = wx.Panel( self )
    label = wx.StaticText( panel, -1, 'Angle: ' )
    self.angleSlider = wx.Slider(
        panel, -1, 
        value = 0, minValue = 0, maxValue = 89,
        pos = wx.DefaultPosition, size = ( -1, -1 ),
        style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS
        )
    self.angleSlider.SetPageSize( 1 )
    self.angleSlider.Bind( wx.EVT_SCROLL, self._OnAngleSlider )

    sizer = wx.BoxSizer( wx.HORIZONTAL )
    sizer.Add( label, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER )
    sizer.Add( self.angleSlider, 1, wx.ALL | wx.EXPAND, 4 )
    panel.SetSizer( sizer )

    return  { 'top': panel }
  #end _CreateAdditionalUIControls


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateClipboardData()    -
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return                 text or None
"""
    return \
        self._CreateClipboardDisplayedData()  if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
#        self._CreateClipboardSelectionData() \
#        if cur_selection_flag else \
#        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #     METHOD: VesselCoreAxial2DView._CreateClipboardDisplayedData()   -
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return                 text or None
"""
    csv_text = None
    core = self.dmgr.core

    dset = None
    theta_ndx = self.fluenceAddr.thetaIndex
    if theta_ndx >= 0:
      dset = \
          self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )
      theta_ndx = min( theta_ndx, core.fluenceMesh.ntheta - 1 )

    if dset is not None:
      dset_array = np.array( dset )
      ax_ranges = self._GetAxialRanges( 'fluence' )
      r_start_ndx = self.config[ 'radiusStartIndex' ]

      csv_text = '"%s: theta=%.3f; %s=%.3g"\n' % (
          self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
          core.fluenceMesh.theta[ theta_ndx ],
          self.state.timeDataSet,
          self.timeValue
          )
      csv_text += 'z,r,value\n'

      #for ax in xrange( len( core.tally.z ) - 1, -1, -1 ):
      for ax in xrange(
          ax_ranges.get( 'fluence_top_ndx' ) - 1,
          ax_ranges.get( 'fluence_bottom_ndx' ) - 1,
          -1
          ):
        for ri in xrange( r_start_ndx, core.fluenceMesh.nr ):
          value = dset_array[ ax, theta_ndx, ri ]
          row = '%.3f,%.3f,%.7g\n' % \
              ( core.fluenceMesh.z[ ax ], core.fluenceMesh.r[ ri ], value )
          csv_text += row
        #end for ri
      #end for ax
    #end if dset is not None and core is not None

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #     METHOD: VesselCoreAxial2DView._CreateClipboardSelectedData()    -
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return                 text or None
"""
    csv_text = None
    core = self.dmgr.core

    dset = None
    theta_ndx = self.fluenceAddr.thetaIndex
    z_ndx = self.axialValue.fluenceIndex
    if z_ndx >= 0 and theta_ndx >= 0:
      dset = \
          self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )
      core = self.dmgr.GetCore()
      theta_ndx = min( theta_ndx, core.fluenceMesh.ntheta - 1 )
      #z_ndx = min( z_ndx, core.fluenceMesh.nz - 1 )
      z_ndx = min( z_ndx, core.fluenceMesh.nz - 2 )

    if dset is not None and z_ndx >= 0:
      dset_array = np.array( dset )
      r_start_ndx = self.config[ 'radiusStartIndex' ]

      csv_text = '"%s: axial=%.3f, theta=%.3f; %s=%.3g"\n' % (
          self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
          #self.axialValue.cm,
          core.fluenceMesh.zcenters[ z_ndx ],
          core.fluenceMesh.GetThetaRads( theta_ndx ),
          self.state.timeDataSet,
          self.timeValue
          )
      csv_text += 'r,value\n'

      for ri in xrange( r_start_ndx, core.fluenceMesh.nr ):
        value = dset_array[ z_ndx, theta_ndx, ri ]
        row = '%.3f,%.7g\n' % ( core.fluenceMesh.r[ ri ], value )
        csv_text += row
      #end for ri
    #end if dset is not None and core is not None

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateDrawConfig()       -
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ).
The technique is to determine the number of pixels per pin, with a minimum
of 1, meaning a forced scale might be necessary.
    Keyword Args:
        scale_type (str): 'linear' or 'log', defaulting to 'linear'
        size (tuple(int)): ( wd, ht) against which to calculate the scale
        fluence_scale_type (str): 'linear' or 'log', defaulting to 'linear'
    Returns:
        dict: keys (inherited from RasterWidget)
            clientSize (tuple(int)): wd, ht
            dataRange (tuple(float)):
                ( range_min, range_max, data_min, data_max )
            font (wx.Font):
            fontSize (int): font point size
            labelFont (wx.Font):
            labelSize (tuple(int)): wd, ht
            legendBitmap (wx.Bitmap):
            legendSize (tuple(int)): wd, ht
            mapper (matplotlib.cm.ScalarMappable): used to convert values to
                colors
            valueFont (wx.Font):

            (created here)
            assemblyWidth (int): pixels required to draw an assembly
            coreAxialDy (int): total of pixel offsets in y dimension for
                core datasets
            coreAxialLevelsDy (list(int)): list of pixel offsets in y dimension
                for core datasets
            coreAxialOffsetPix (int): vertical pixels for the core offset
            coreRegion (list(int)): x, y, wd, ht
            imageSize (tuple(int)): wd, ht
            lineWidth (int): hilite line pixel width
            npin (int): effective number of pins per assy for drawing
            npinxCosTheta (float): effective (cos theta) pin columns per assy
            npinySinTheta (float): effective (sin theta) pin rows per assy
            pinCm (float): centimenters per pin
            pinWidth (int): pixels to draw a pin
            pixPerCm (float): non-integral pixels per centimeter
            thetaCos (float): theta cosine
            thetaRad (float): theta in radians
            thetaSin (float): theta sine
            valueFontSize (int): point size
            vesselRegion (list(int)): x, y, wd, ht

            (if fluence)
            baffleWidth (int): pixel width for drawing the baffle
            barrelRadius (int): pixel at which the baffle starts on the
                top horizontal line
            barrelWidth (int): pixel width for drawing the barrel
            coreOffsetCm (float): offset to the start of the core in cm
            fluenceDataRange (tuple(float)):
                ( range_min, range_max, data_min, data_max )
            fluenceDataSetExpr (str): expression to apply when pulling data
                based on a threshold
            fleunceLegendBitmap (wx.Bitmap):
            fluenceLegenSize (tuple(int)): wd, ht
            fluenceMapper (matplotlib.cm.ScalarMappable): used to convert
                values to colors
            fluenceAxialDy (int): total of pixel offsets in y dimension for
                fluence datasets
            fluenceAxialLevelsDy (list(int)): list of pixel offsets in y
                dimension for fluence datasets
            fluenceAxialOffsetPix (int): vertical pixels for the vessel offset,
                should be 0
            linerRadius (int): pixel at which the liner starts on the
                top horizontal line
            linerWidth (int): pixel width for drawing the liner
            padAngles (list(float)): pad start angles in degrees
            padArc (float): pad arc in degrees
            padRadius (int): pixel at which the pad would start on the
                top horizontal line
            padWidth (int): pixel width for drawing the pad
            radiusStartIndex (int): 0-based index in the radius array at which
                to start drawing
            thetaStopIndex (int): 0-based exclusive index
            vesselRadius (int): pixel at which the vessel ends on the
                top horizontal line
"""
    ds_range = self._ResolveDataRange(
        self.curDataSet,
        self.timeValue if self.state.scaleMode == 'state' else -1,
        apply_custom_range = False
        )
    kwargs[ 'colormap_name' ] = 'jet'
    if 'scale_type' not in kwargs:
      kwargs[ 'scale_type' ] = self.dmgr.GetDataSetScaleType( self.curDataSet )
    config = self._CreateBaseDrawConfig( ds_range, **kwargs )

    core = self.dmgr.GetCore()
    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    #legend_bmap = config[ 'legendBitmap' ]
    legend_size = config[ 'legendSize' ]

#               -- Calc axial_mesh range and cm/pin
#               --
    #axial_mesh = self.dmgr.GetAxialMesh2( self.curDataSet )
    #top_mesh_level = min( self.cellRange[ 3 ] - 1, len( axial_mesh ) - 1 )
    #could never happen
    #if top_mesh_level == self.cellRange[ 1 ]:
    #  axial_range_cm = axial_mesh[ -1 ] - axial_mesh[ 0 ]

# Note, if we ever allow zooming, we must call _GetAxialRanges() to
# account for cellRange, so we might as well do it now
    ax_ranges = self._GetAxialRanges( 'core', 'fluence' )
    axial_mesh = self.dmgr.GetAxialMesh2( mesh_type = 'all' )
    axial_range_cm = ax_ranges[ 'cm_top' ] - ax_ranges[ 'cm_bottom' ]
    if axial_range_cm == 0.0:
      axial_range_cm = 1.0

#               -- Core axial offset
    core_axial_mesh = self.dmgr.GetAxialMesh2( self.curDataSet, 'pin' )
    core_axial_offset_cm = axial_mesh[ -1 ] - core_axial_mesh[ -1 ]
    core_axial_range_cm = \
        core_axial_mesh[ ax_ranges[ 'core_top_ndx' ] ] - \
        core_axial_mesh[ ax_ranges[ 'core_bottom_ndx' ] ]
    fluence_axial_offset_cm = 0.0
    fluence_axial_range_cm = 1.0

#               -- Calc values based on theta
    vessel_geom = core.vesselGeom
    fluence_mesh = core.fluenceMesh

    theta_rad = fluence_mesh.GetThetaRads( self.fluenceAddr.thetaIndex )
    theta_cos = math.cos( theta_rad )
    theta_sin = math.sin( theta_rad )
    npinx_cos_theta = theta_cos * core.npinx
    npiny_sin_theta = theta_sin * core.npiny

    #npin = core.npin
    npin = max( core.npinx, core.npiny )
    if self.channelMode:
      npin += 1
    cm_per_pin = core.apitch / npin

#               -- Calc axial pin equivalents
    axial_pin_equivs = axial_range_cm / cm_per_pin
    horz_pin_equivs = npin
    core_aspect_ratio = core.apitch * self.cellRange[ -2 ] / axial_range_cm

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug(
          'theta_rad=%f, npin=%d, apitch=%f, ' +
          'cm_per_pin=%f, axial_pin_equivs=%f',
          theta_rad, npin, core.apitch, cm_per_pin, axial_pin_equivs
          )

#               -- Vessel stuff
#               --
    radius_start_ndx = 1
    fluence_ds_expr = fluence_ds_range = fluence_legend_bmap = None
    fluence_legend_size = ( 0, 0 )
    theta_stop_ndx = fluence_mesh.ntheta

    core_offset_cm = 0.0
    vessel_wd_cm = core_wd_cm = self.cellRange[ -2 ] * core.apitch

    if vessel_geom is not None and fluence_mesh.IsValid() and \
        self.fluenceAddr.dataSetName is not None:
      fluence_axial_mesh = \
          self.dmgr.GetAxialMesh2( self.fluenceAddr.dataSetName, 'fluence' )
      fluence_axial_offset_cm = axial_mesh[ -1 ] - fluence_axial_mesh[ -1 ]
      fluence_axial_range_cm = \
          fluence_axial_mesh[ ax_ranges[ 'fluence_top_ndx' ] ] - \
          fluence_axial_mesh[ ax_ranges[ 'fluence_bottom_ndx' ] ]

#      rndx = DataUtils.FindListIndex( fluence_mesh.r, vessel_geom.linerOuter )
#      if rndx > 1:
#        radius_start_ndx = min( rndx, fluence_mesh.nr - 1 )
      radius_start_ndx = fluence_mesh.FindRadiusStartIndex( vessel_geom )
#      if core.coreSym == 4:
#        tndx = DataUtils.FindListIndex( fluence_mesh.theta, PI_OVER_2 )
#       if fluence_mesh.theta[ tndx ] == PI_OVER_2:
#         tndx -= 1
#       theta_stop_ndx = min( tndx + 1, fluence_mesh.ntheta )
      theta_stop_ndx = fluence_mesh.FindThetaStopIndex( core.coreSym )
      fluence_ds_expr = '[:,:%d,%d:]' % ( theta_stop_ndx, radius_start_ndx )
      fluence_ds_range = self._ResolveDataRange(
          self.fluenceAddr.dataSetName,
          self.timeValue if self.state.scaleMode == 'state' else -1,
          ds_expr = fluence_ds_expr
          )

      if 'fluence_scale_type' in kwargs:
        fluence_scale_type = kwargs[ 'fluence_scale_type' ]
      else:
        fluence_scale_type = \
            self._ResolveScaleType( self.fluenceAddr.dataSetName )
      if fluence_scale_type == 'log':
        fluence_ds_range = self.dmgr.NormalizeLogRange( fluence_ds_range )
        norm = colors.LogNorm(
            vmin = fluence_ds_range[ 0 ], vmax = fluence_ds_range[ 1 ],
            clip = True
            )
      else:
        norm = colors.Normalize(
            vmin = fluence_ds_range[ 0 ], vmax = fluence_ds_range[ 1 ],
            clip = True
            )
      fluence_mapper = cm.ScalarMappable(
          norm = norm,
          cmap = cm.get_cmap( self.colormapName )
          )

      if self.showLegend:
        fluence_ds_name = \
            self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName )
        ndx = fluence_ds_name.find( '/' )
        if ndx >= 0:
          fluence_ds_name = fluence_ds_name[ ndx + 1 : ]
        fluence_legend_bmap = self._CreateLegendBitmap(
            fluence_ds_range,
            font_size = font_size,
            mapper = fluence_mapper,
            ntick_values = 8,
            scale_type = fluence_scale_type,
            title = fluence_ds_name
            )
        fluence_legend_size = \
            ( fluence_legend_bmap.GetWidth(), fluence_legend_bmap.GetHeight() )
      #end if self.showLegend

      if core.coreSym == 4 and max( core.nassx, core.nassy ) % 2 == 1:
        core_offset_cm = 0.5 * core.apitch

      vessel_wd_cm = max(
          core_offset_cm + core_wd_cm + vessel_geom.vesselOuterOffset,
          fluence_mesh.r[ -1 ]
          )
      horz_pin_equivs = vessel_wd_cm / cm_per_pin
    #end if vessel_geom and fluence_mesh

#               -- Scale to widget size?
#               --
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]
#                       -- Determine drawable region
#                       --
      # l2r  label : core : (baffle 1 px) : font-sp : legend : fluence_legend
      # t2b  label : core : (baffle 1 px) : font-sp : title
      #xxxxx revisit font_size, pt bigger than a pixel
      region_wd = \
          wd - label_size[ 0 ] - 2 - (font_size << 1) - \
          legend_size[ 0 ] - fluence_legend_size[ 0 ]
      working_ht = max( ht, legend_size[ 1 ], fluence_legend_size[ 1 ] )
      region_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)

      region_aspect_ratio = float( region_wd ) / float( region_ht )

#                       -- Limited by height
#x      if region_aspect_ratio > core_aspect_ratio:
#y    if self.fitMode == 'ht':
#y      pin_wd = max( 1, int( math.floor( region_ht / axial_pin_equivs ) ) )
#y      pin_wd = min( 10, pin_wd )
#                       -- Limited by width
#y    else:
#y      pin_wd = max( 1, int( math.floor( region_wd / horz_pin_equivs ) ) )

      pix_per_cm_x = float( region_wd ) / vessel_wd_cm
      pix_per_cm_y = float( region_ht ) / axial_range_cm

      if self.fitMode == 'ht':
        pix_per_pin = math.floor( pix_per_cm_y * cm_per_pin )
        #pix_per_pin = math.floor( min( pix_per_cm_x, pix_per_cm_y ) * cm_per_pin )
      else:
        pix_per_pin = math.floor( pix_per_cm_x * cm_per_pin )
        #pix_per_pin = math.ceil( min( pix_per_cm_x, pix_per_cm_y ) * cm_per_pin )
      pin_wd = pix_per_pin = min( 10, max( 1, int( pix_per_pin ) ) )

    else: #deprecated
      pin_wd = pix_per_pin = \
      int( kwargs[ 'scale' ] )  if 'scale' in kwargs else  4
      #font_size = self._CalcFontSize( 1024 * pix_per_pin )

#               -- Pixels per cm, assembly width, core and vessel size
#               --
    pix_per_cm = pix_per_pin / cm_per_pin
    assy_wd = npin * pix_per_pin

    #x core_wd is cm_per_pin * self.cellRange[ -2 ] * npin * pix_per_cm_x
    core_wd = self.cellRange[ -2 ] * assy_wd
    core_ht = int( math.ceil( core_axial_range_cm * pix_per_cm ) )
      #int( math.ceil( pix_per_cm * (axial_range_cm - core_axial_offset_cm) ) )

    vessel_wd = int( math.ceil( pix_per_cm * vessel_wd_cm ) )
    vessel_ht = int( math.ceil( pix_per_cm * fluence_axial_range_cm ) )

    core_axial_offset_pix = \
        0  if core_axial_offset_cm == 0.0 else \
        int( math.floor( core_axial_offset_cm * pix_per_cm ) )
    fluence_axial_offset_pix = \
        0  if fluence_axial_offset_cm == 0.0 else \
        int( math.floor( fluence_axial_offset_cm * pix_per_cm ) )

#               -- Calc image size
#               --
    region_x = label_size[ 0 ] + 2
    region_y = label_size[ 1 ] + 2
    image_wd = \
        region_x + vessel_wd + (font_size << 1) + \
        legend_size[ 0 ] + fluence_legend_size[ 0 ]
    image_ht = \
max( region_y + vessel_ht, legend_size[ 1 ], fluence_legend_size[ 1 ] ) + \
        (font_size << 2)

#               -- Create list of axial levels
#               --
    core_axials_dy = []
    #for ax in range( self.cellRange[ 3 ] - 1, self.cellRange[ 1 ] - 1, -1 ):
    for ax in xrange(
        ax_ranges[ 'core_top_ndx' ] - 1, ax_ranges[ 'core_bottom_ndx' ] - 1, -1
        ):
      ax_cm = core_axial_mesh[ ax + 1 ] - core_axial_mesh[ ax ]
      dy = int( math.floor( pix_per_cm * ax_cm ) )
      core_axials_dy.insert( 0, dy )
    #end for ax
    core_axial_dy = sum( core_axials_dy )

    fluence_axial_dy = 0
    fluence_axials_dy = []
    if fluence_ds_range is not None:
      for ax in range(
          ax_ranges[ 'fluence_top_ndx' ] - 1,
          ax_ranges[ 'fluence_bottom_ndx' ] - 1,
          -1
          ):
        ax_cm = fluence_axial_mesh[ ax + 1 ] - fluence_axial_mesh[ ax ]
        dy = int( math.floor( pix_per_cm * ax_cm ) )
        fluence_axials_dy.insert( 0, dy )
      fluence_axial_dy = sum( fluence_axials_dy )

#               -- Create config dict
#               --
    config[ 'assemblyWidth' ] = assy_wd
    config[ 'coreAxialDy' ] = core_axial_dy
    config[ 'coreAxialLevelsDy' ] = core_axials_dy
    config[ 'coreAxialOffsetPix' ] = core_axial_offset_pix
    config[ 'coreRegion' ] = [
        region_x, region_y + core_axial_offset_pix,
        core_wd, core_ht
        ]
        #[ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = \
        max( 1, min( int( assy_wd / 20.0 ), max( core_axials_dy ) >> 1, 5 ) )
        #max( 1, min( 5, int( assy_wd / 20.0 ) ) )
    config[ 'npin' ] = npin
    config[ 'npinxCosTheta' ] = npinx_cos_theta
    config[ 'npinySinTheta' ] = npiny_sin_theta
    config[ 'pinCm' ] = cm_per_pin
    config[ 'pinWidth' ] = pin_wd
    config[ 'pixPerCm' ] = pix_per_cm
    config[ 'thetaCos' ] = theta_cos
    config[ 'thetaRad' ] = theta_rad
    config[ 'thetaSin' ] = theta_sin
    config[ 'valueFontSize' ] = assy_wd >> 1
    config[ 'vesselRegion' ] = [ region_x, region_y, vessel_wd, vessel_ht ]

    if self.nodalMode:
      config[ 'nodeWidth' ] = assy_wd >> 1

    if fluence_ds_range is not None:
      baffle_wd = \
         max( 1, int( math.ceil( vessel_geom.baffleSize * pix_per_cm ) ) )

      barrel_r = int( math.ceil( vessel_geom.barrelInner * pix_per_cm ) )
      barrel_wd = max( 1, int( vessel_geom.barrelSize * pix_per_cm ) )

      liner_r = int( math.ceil( vessel_geom.linerInner * pix_per_cm ) )
      liner_wd = max( 1, int( vessel_geom.linerSize * pix_per_cm ) )

      pad_r = int( math.ceil( vessel_geom.padInner * pix_per_cm ) )
      pad_wd = \
          0  if vessel_geom.padSize <= 0 else \
          max( 1, int( vessel_geom.padSize * pix_per_cm ) )

      vessel_r = int( math.ceil( vessel_geom.vesselOuter * pix_per_cm ) )

      config[ 'baffleWidth' ] = baffle_wd
      config[ 'barrelRadius' ] = barrel_r
      config[ 'barrelWidth' ] = barrel_wd
      config[ 'coreOffsetCm' ] = core_offset_cm
      config[ 'linerRadius' ] = liner_r
      config[ 'linerWidth' ] = liner_wd
      config[ 'padAngles' ] = vessel_geom.padAngles  # DEF_pad_angles_deg
      config[ 'padArc' ] = vessel_geom.padArc  # DEF_pad_len_deg
      config[ 'padRadius' ] = pad_r
      config[ 'padWidth' ] = pad_wd
# We're suspending this with the new fluence data
      config[ 'radiusStartIndex' ] = radius_start_ndx
#      config[ 'radiusStartIndex' ] = 0

      config[ 'fluenceAxialDy' ] = fluence_axial_dy
      config[ 'fluenceAxialLevelsDy' ] = fluence_axials_dy
      config[ 'fluenceAxialOffsetPix' ] = fluence_axial_offset_pix
      config[ 'fluenceDataRange' ] = fluence_ds_range
      config[ 'fluenceDataSetExpr' ] = fluence_ds_expr
      config[ 'fluenceMapper' ] = fluence_mapper

      config[ 'thetaStopIndex' ] = theta_stop_ndx
      config[ 'vesselRadius' ] = vessel_r

      if self.showLegend:
        config[ 'fluenceLegendBitmap' ] = fluence_legend_bmap
        config[ 'fluenceLegendSize' ] = fluence_legend_size
    #end if fluence_mesh

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateMenuDef()          -
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( VesselCoreAxial2DView, self )._CreateMenuDef()
    new_menu_def = \
        [ x for x in menu_def if x.get( 'label' ) != 'Unzoom' ]
    return  new_menu_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateRasterImage()      -
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.
@param  tuple_in        0-based ( state_index, assy_col_or_row, pin_col_or_row,
                        theta_rad )
@param  config          optional config to use instead of self.config
"""
    #start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    node_addr = self.dmgr.GetNodeAddr( self.subAddr )
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None

    core = dset = None
    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

#x    config[ 'coreOffsetY' ] = core_offset_y_cm * pix_per_cm
    if dset is not None and core is not None:
      assy_wd = config[ 'assemblyWidth' ]
      axial_levels_dy = config[ 'coreAxialLevelsDy' ]
      core_axial_offset_pix = config[ 'coreAxialOffsetPix' ]
      core_offset_cm = config.get( 'coreOffsetCm', 0 )
      core_region = config[ 'coreRegion' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      if self.nodalMode:
        node_wd = config[ 'nodeWidth' ]
      npin = config[ 'npin' ]
      npinx_cos_theta = config[ 'npinxCosTheta' ]
      npiny_sin_theta = config[ 'npinySinTheta' ]
      pin_wd = config[ 'pinWidth' ]
      pix_per_cm = config[ 'pixPerCm' ]
      fluence_ds_range = config.get( 'fluenceDataRange' )
      fluence_legend_bmap = config.get( 'fluenceLegendBitmap' )
      fluence_legend_size = config.get( 'fluenceLegendSize' )
      theta_cos = config.get( 'thetaCos' )
      theta_rad = config.get( 'thetaRad' )
      theta_sin = config.get( 'thetaSin' )
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]
      vessel_region = config[ 'vesselRegion' ]

      fluence_mesh = core.fluenceMesh

      ds_range = config[ 'dataRange' ]
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

#               -- "Item" refers to channel or pin
      item_factors = None
      if self.state.weightsMode == 'on':
        item_factors = self.dmgr.GetFactors( self.curDataSet )

      dset_array = np.array( dset )
      dset_shape = dset.shape

#               -- Total pins, effectively
      if core_offset_cm > 0:
        pin_eff_count = self.cellRange[ -2 ] * npin - (npin >> 1)
      else:
        pin_eff_count = self.cellRange[ -2 ] * npin

      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
            'core_region=%s, vessel_region=%s\n' +
            'core.npinx=%d, core.npiny=%d\n' +
            'npinx_cos_theta=%f, npiny_sin_theta=%f\n' +
            'npin=%d, pin_eff_count=%d',
            str( core_region ), str( vessel_region ),
            core.npinx, core.npiny, npinx_cos_theta, npiny_sin_theta,
            npin, pin_eff_count
            )

#               -- Create title template
      addresses = None
      if fluence_ds_range is not None:
        addresses = \
        ' {0:s} th={1:d}deg'.format(
            self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
            int( theta_rad * 180.0 / math.pi )
            )

      title_templ, title_size = self._CreateTitleTemplate2(
          font, self.curDataSet, dset_shape, self.state.timeDataSet,
          additional = addresses
          )

      node_value_draw_list = []

#                       -- Create image
#                       --
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      glabel_font = gc.CreateFont( label_font, wx.BLACK )
      if self.showLabels:
        #gc.SetFont( glabel_font )
        yfont_size = int( math.floor( font_size * 0.6 ) )
        gylabel_font = Widget.CopyFont( value_font, pt_size = yfont_size )
        gc.SetFont( gylabel_font )

      assy_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
          ) )
      node_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 100, 100, 100, 255 ), 1, wx.PENSTYLE_SOLID
          ) )

      colors = mapper.to_rgba( dset_array, bytes = True )
      if item_factors is not None:
	colors[ item_factors == 0 ] = trans_color_arr
      colors[ np.isnan( dset_array ) ] = trans_color_arr
      colors[ np.isinf( dset_array ) ] = trans_color_arr

#                       -- Loop on axial levels
#                       --
      last_axial_label_y = 0
      axial_y = core_region[ 1 ]
      for ax in xrange( len( axial_levels_dy ) - 1, -1, -1 ):
        cur_dy = axial_levels_dy[ ax ]
        axial_level = ax + self.cellRange[ 1 ]

#                               -- Row label
#                               --
        if self.showLabels and cur_dy > 1:
          label = '{0:02d}'.format( axial_level + 1 )
          #label_size = ylabel_font.getsize( label )
          label_size = gc.GetFullTextExtent( label )
          label_y = axial_y + ((cur_dy - label_size[ 1 ]) / 2.0)
          if (last_axial_label_y + label_size[ 1 ] + 1) < (axial_y + cur_dy):
            gc.SetFont( gylabel_font )
            gc.DrawText( label, 1 ,label_y )
            last_axial_label_y = axial_y
        #end if self.showLabels and cur_dy > 1

#                               -- Loop on horizontal assemblies/pins
#                               --
        pin_x = core_region[ 0 ]
        pin_col_f = self.cellRange[ 0 ] * core.npinx
        pin_row_f = self.cellRange[ 0 ] * core.npiny

        if core_offset_cm > 0:
          pin_x += assy_wd >> 1
          pin_col_f += core.npinx >> 1
          pin_row_f += core.npiny >> 1

        pin_col_incr_f = \
            (npinx_cos_theta * self.cellRange[ -2 ]) / pin_eff_count
        pin_row_incr_f = \
            (npiny_sin_theta * self.cellRange[ -2 ]) / pin_eff_count

        if self.logger.isEnabledFor( logging.DEBUG ) and \
            ax == len( axial_levels_dy ) - 1:
          self.logger.debug(
              'pin_col_f=%f, pin_row_f=%f\n' +
              'pin_col_incr_f=%f, pin row_incr_f=%f',
              pin_col_f, pin_row_f, pin_col_incr_f, pin_row_incr_f
              )

        for i in xrange( pin_eff_count ):
#xxxxx
#                                       -- Column/row label
##        if ax == len( axial_levels_dy ) - 1 and self.showLabels:
##          label_ndx = 0 if self.mode == 'xz' else 1
##          label = core.GetCoreLabel( label_ndx, assy_col )
##          label_size = gc.GetFullTextExtent( label )
##          label_x = assy_x + ((assy_wd - label_size[ 0 ]) / 2.0)
##          gc.SetFont( glabel_font )
##          gc.DrawText( label, label_x, 1 )
##        #end if writing column label

          pin_col = int( pin_col_f )
          pin_row = int( pin_row_f )

          assy_col_raw = (pin_col // core.npinx)
          assy_row_raw = (pin_row // core.npiny)
          assy_col = min( assy_col_raw, core.coreMap.shape[ 1 ] - 1 )
          assy_row = min( assy_row_raw, core.coreMap.shape[ 0 ] - 1 )
          assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

          assy_pin_col = pin_col % core.npinx
          assy_pin_row = pin_row % core.npiny

          if _DEBUG_ and self.logger.isEnabledFor( logging.DEBUG ):
            self.logger.debug(
'i=%d: pin_x=%d\n  pin_col=%d, pin_row=%d\n' +
'  assy_col_raw=%d, assy_row_raw=%d, assy_col=%d, assy_row=%d\n' +
'  assy_pin_col=%d, assy_pin_row=%d',
                i, pin_x, pin_col, pin_row,
                assy_col_raw, assy_row_raw, assy_col, assy_row,
                assy_pin_col, assy_pin_row
                )

          if self.nodalMode:
            node_col = assy_pin_col // (core.npinx >> 1)
            node_row = assy_pin_row // (core.npiny >> 1)
            if node_col > 0:
              node_ndx = 3 if node_row > 0 else 1
            else:
              node_ndx = 2 if node_row > 0 else 0
            #value = dset_array[ 0, node_ndx, axial_level, assy_ndx ]
            cur_color = colors[ 0, node_ndx, axial_level, assy_ndx ]

            if cur_color[ 3 ] > 0:
              brush_color = pen_color = cur_color.tolist()
              gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
                  wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
                  ) ) )
              gc.SetBrush( gc.CreateBrush(
                  wx.TheBrushList.FindOrCreateBrush(
                      wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
                      )
                  ) )
              gc.DrawRectangle( node_x, axial_y, node_wd + 1, cur_dy + 1 )
              node_value_draw_list.append((
                  self._CreateValueString( value ),
                  Widget.GetContrastColor( *brush_color ),
                  node_x, axial_y, node_wd, cur_dy
                  ))
            #end if cur_color[ 3 ] > 0

          #else:
          elif assy_pin_col < dset_shape[ 1 ] and assy_pin_row < dset_shape[ 0 ]:
            cur_color = \
                colors[ assy_pin_row, assy_pin_col, axial_level, assy_ndx ]
            if cur_color[ 3 ] > 0:
              brush_color = pen_color = cur_color.tolist()
              gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
                  wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
                  ) ) )
              gc.SetBrush( gc.CreateBrush(
                  wx.TheBrushList.FindOrCreateBrush(
                      wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
                      )
                  ) )
              gc.DrawRectangle( pin_x, axial_y, pin_wd, cur_dy )
            #end if cur_color[ 3 ] > 0
          #end elif assy_pin_col < dset_shape[ 1 ] and ...

          pin_x += pin_wd
          pin_col_f += pin_col_incr_f
          pin_row_f += pin_row_incr_f
        #end for i in xrange( pin_eff_count )

        axial_y += cur_dy
      #end for ax

#                       -- Draw values
#                       --
      if node_value_draw_list:
        self._DrawValuesWx( node_value_draw_list, gc )

#                       -- Draw vessel components and fluence
#                       --
      if fluence_ds_range is not None:
        self._DrawVesselComponents( gc, config, tuple_in )

#                       -- Draw Legend Image
#                       --
      if legend_bmap is not None:
        gc.DrawBitmap(
            legend_bmap,
            vessel_region[ 0 ] + vessel_region[ 2 ] + 2 + font_size, 2,
            legend_bmap.GetWidth(), legend_bmap.GetHeight()
            )
      else:
        legend_size = ( 0, 0 )

      if fluence_legend_bmap is not None:
        at = (
            vessel_region[ 0 ] + vessel_region[ 2 ] + 2 + font_size +
            legend_size[ 0 ],
            2 # vessel_region[ 1 ]
            )
        gc.DrawBitmap(
            fluence_legend_bmap, at[ 0 ], at[ 1 ],
            fluence_legend_bmap.GetWidth(), fluence_legend_bmap.GetHeight()
            )
      else:
        fluence_legend_size = ( 0, 0 )

#                       -- Draw Title String
#                       --
      #axial_y = max( axial_y, legend_size[ 1 ], fluence_legend_size[ 1 ] )
      axial_y = max(
          axial_y,
          vessel_region[ 1 ] + vessel_region[ 3 ],
          legend_size[ 1 ], fluence_legend_size[ 1 ]
          )
      axial_y += font_size >> 2

      title_str = self._CreateTitleString(
          title_templ,
          time = self.timeValue
          )
      gc.SetFont( glabel_font )
      self._DrawStringsWx(
          gc, font,
          ( title_str, ( 0, 0, 0, 255 ),
            vessel_region[ 0 ], axial_y,
            #vessel_region[ 2 ] - vessel_region[ 0 ],
            im_wd - vessel_region[ 0 ] - (font_size << 2),
            'c' )
          )

#                       -- Draw vessel fluence values
#                       --
      if fluence_ds_range is not None and \
          self.fluenceAddr.dataSetName is not None:
        self._DrawFluenceCells( gc, config, tuple_in )

#                       -- Finished
#                       --
      dc.SelectObject( wx.NullBitmap )
    #end if config exists

    #elapsed_time = timeit.default_timer() - start_time
    #if self.logger.isEnabledFor( logging.DEBUG ):
      #self.logger.debug( 'time=%.3fs, im-None=%s', elapsed_time, im is None )

    return  bmap  if bmap is not None else  self.emptyBitmap
  #end _CreateRasterImage


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateStateTuple()       -
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """Create tuple that is used for comparison in IsTupleCurrent().
#m @return                      state_index, assy_col_or_row, pin_col_or_row, theta_ndx
@return                 state_index, theta_ndx
"""
#m    th = self.fluenceAddr.thetaIndex
#m    if self.mode == 'xz':
#m      t = ( self.stateIndex, self.assemblyAddr[ 2 ], self.subAddr[ 1 ], th )
#m    else:
#m      t = ( self.stateIndex, self.assemblyAddr[ 1 ], self.subAddr[ 0 ], th )
    t = ( self.stateIndex, self.fluenceAddr.thetaIndex )
    return  t
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateToolTipText()      -
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info       tuple returned from FindCell()
( axial_level, assy_ndx, assy_col, assy_row, pin_col, pin_row, node_addr )
"""
    tip_str = ''
    dset = None
    valid = False

    if cell_info is not None and \
        self.dmgr.IsValid( self.curDataSet, axial_level = cell_info[ 0 ] ):
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      core = self.dmgr.GetCore()

      assy_addr = self.dmgr.NormalizeAssemblyAddr( cell_info[ 1 : 4 ] )
      assy_addr_str = core.CreateAssyLabel( *assy_addr[ 1 : 3 ] )
      tip_str = 'Assy: ' + assy_addr_str

      axial_value = self.dmgr.\
            GetAxialValue( self.curDataSet, core_ndx = cell_info[ 0 ] )
      tip_str += ', Axial: {0:.2f}'.format( axial_value.cm )
    #end if dset is not None and assy_ndx < dset.shape[ 3 ]

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._CreateToolTipText()      -
  #----------------------------------------------------------------------
#m  def _CreateToolTipText( self, cell_info ):
#m    """Create a tool tip.
#m@param  cell_info     tuple returned from FindCell()
#m"""
#m    tip_str = ''
#m    dset = None
#m    valid = False
#m
#m    if cell_info is not None:
#m      valid = self.dmgr.IsValid(
#m        self.curDataSet,
#m        assembly_index = cell_info[ 0 ],
#m        axial_level = cell_info[ 2 ]
#m          )
#m
#m    if valid:
#m      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
#m
#m    if dset is not None and assy_ndx < dset.shape[ 3 ]:
#m      core = self.dmgr.GetCore()
#m      if self.mode == 'xz':
#m        assy_addr = ( cell_info[ 1 ], self.assemblyAddr[ 2 ] )
#m      else:
#m        assy_addr = ( self.assemblyAddr[ 1 ], cell_info[ 1 ] )
#m
#m      assy_addr_str = core.CreateAssyLabel( *assy_addr )
#m      tip_str = 'Assy: ' + assy_addr_str
#m
#m      if cell_info[ 2 ] >= 0:
#m        axial_value = self.dmgr.\
#m          GetAxialValue( self.curDataSet, core_ndx = cell_info[ 2 ] )
#m        tip_str += ', Axial: {0:.2f}'.format( axial_value.cm )
#m    #end if dset is not None and assy_ndx < dset.shape[ 3 ]
#m
#m    return  tip_str
#m  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._DrawFluenceCells()       -
  #----------------------------------------------------------------------
  def _DrawFluenceCells( self, gc, config, tuple_in ):
    """Handles drawing fluence data.
@param  im_draw         PIL.ImageDraw instance
@param  config          draw configuration dict
@param  tuple_in        state tuple ( state_index, theta_ndx )
"""

    theta_ndx = tuple_in[ 1 ]

    dset = None
    core = self.dmgr.GetCore()
    ds_range = config.get( 'fluenceDataRange' )

    if theta_ndx >= 0 and ds_range is not None:
      dset = \
          self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )

    if dset is not None and core is not None:
      amode = gc.GetAntialiasMode()
      cmode = gc.GetCompositionMode()
      gc.SetAntialiasMode( wx.ANTIALIAS_NONE )  # _DEFAULT
      gc.SetCompositionMode( wx.COMPOSITION_SOURCE )  # _OVER

      theta_ndx = min( theta_ndx, dset.shape[ 1 ] - 1 )
      dset_array = np.array( dset )
      value_delta = ds_range[ 1 ] - ds_range[ 0 ]

      ax_ranges = self._GetAxialRanges()
      core_bottom_cm = ax_ranges.get( 'cm_bottom' )

      #core_axial_dy = config[ 'coreAxialDy' ]
      core_region = config[ 'coreRegion' ]
      #x liner_r = config[ 'linerRadius' ]
      pix_per_cm = config[ 'pixPerCm' ]
      r_start_ndx = config[ 'radiusStartIndex' ]
      fluence_axials_dy = config[ 'fluenceAxialLevelsDy' ]
      fluence_axial_offset_pix = config[ 'fluenceAxialOffsetPix' ]
      fluence_mapper = config[ 'fluenceMapper' ]
      vessel_region = config[ 'vesselRegion' ]

      vessel_origin = vessel_region[ 0 : 2 ]
      vessel_origin[ 1 ] += fluence_axial_offset_pix
      if config.get( 'coreOffsetCm', 0 ) > 0:
        assy_wd = config[ 'assemblyWidth' ]
        vessel_origin[ 0 ] += assy_wd >> 1
        #vessel_origin[ 1 ] += assy_wd >> 1

      max_axial_y = vessel_origin[ 1 ] + config[ 'fluenceAxialDy' ]
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

# Can't do this here b/c to_rgba() treats ndim == 3 or 4 as image
#      cur_array = dset_array[ :, :, : ]
#      colors = fluence_mapper.to_rgba( cur_array, bytes = True )
#      colors[ np.isnan( cur_array ) ] = trans_color_arr
#      colors[ np.isinf( cur_array ) ] = trans_color_arr

#               -- Outer loop is r
#               --
      for ri in xrange( r_start_ndx, core.fluenceMesh.nr ):
        if ri == r_start_ndx:
          r1_wd = int( math.ceil( core.fluenceMesh.r[ ri ] * pix_per_cm ) )
        r2_wd = int( math.ceil( core.fluenceMesh.r[ ri + 1 ] * pix_per_cm ) )

        #cur_r = (r1_wd + r2_wd) >> 1
        cur_r = r2_wd
        cur_wd = max( 1, r2_wd - r1_wd + 1 )

        cur_array = dset_array[ :, :, ri ]
        colors = fluence_mapper.to_rgba( cur_array, bytes = True )
        colors[ np.isnan( cur_array ) ] = trans_color_arr
        colors[ np.isinf( cur_array ) ] = trans_color_arr

#                       -- Inner loop is z
#                       --
        axial_y = vessel_origin[ 1 ]
        axial_cm = ax_ranges.get( 'cm_top' )

        for ax in xrange( len( fluence_axials_dy ) - 1, -1, -1 ):
          cur_dy = fluence_axials_dy[ ax ]
          cur_color = colors[ ax, theta_ndx ]
          if cur_color[ 3 ] > 0:
            pen_color = cur_color.tolist()
            path = gc.CreatePath()
            path.MoveToPoint( vessel_origin[ 0 ] + cur_r, axial_y )
            path.AddLineToPoint(
                vessel_origin[ 0 ] + cur_r,
                min( axial_y + cur_dy, max_axial_y )
                )
            cur_pen = wx.ThePenList.FindOrCreatePen(
                wx.Colour( *pen_color ), cur_wd, wx.PENSTYLE_SOLID
                )
            cur_pen.SetCap( wx.CAP_BUTT )
            gc.SetPen( gc.CreatePen( cur_pen ) )
            gc.StrokePath( path )
          #end if not self.dmgr.IsBadValue( value )

          axial_y += cur_dy
        #end for ax in xrange( len( fluence_axial_levels_dy ) - 1, -1, -1 )

        r1_wd = r2_wd
      #end for ri

      gc.SetAntialiasMode( amode )
      gc.SetCompositionMode( cmode )
    #end if dset
  #end _DrawFluenceCells


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._DrawVesselComponents()   -
  #----------------------------------------------------------------------
  def _DrawVesselComponents( self, gc, config, tuple_in ):
    """Handles drawing vessel components from the vessel definition
@param  gc              wx.GraphicsContext instance
@param  config          draw configuration dict
@param  tuple_in        state tuple ( state_index, theta_ndx )
"""
    core = self.dmgr.GetCore()

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'config\n%s', str( config ) )

    theta_rad = core.fluenceMesh.GetThetaRads( tuple_in[ 1 ] )
    theta_deg = theta_rad * 180.0 / math.pi

    assy_wd = config[ 'assemblyWidth' ]
    core_axial_dy = config[ 'coreAxialDy' ]
    axial_levels_dy = config[ 'coreAxialLevelsDy' ]
    core_axial_offset_pix = config[ 'coreAxialOffsetPix' ]
    core_region = config[ 'coreRegion' ]
    pin_cm = config[ 'pinCm' ]
    pix_per_cm = config[ 'pixPerCm' ]
    fluence_axial_dy = config[ 'fluenceAxialDy' ]
    fluence_axial_offset_pix = config[ 'fluenceAxialOffsetPix' ]
    vessel_region = config[ 'vesselRegion' ]

#       -- Barrel
#       --
    barrel_r = config[ 'barrelRadius' ]
    barrel_wd = config[ 'barrelWidth' ]
    barrel_r += (barrel_wd >> 1)
    liner_r = config[ 'linerRadius' ]
    vessel_r = config[ 'vesselRadius' ]
    vessel_wd = vessel_r - (liner_r + 1)
    vessel_r = liner_r + 1 + (vessel_wd >> 1)

    core_origin = core_region[ 0 : 2 ]
    vessel_origin = vessel_region[ 0 : 2 ]
    vessel_origin[ 1 ] += fluence_axial_offset_pix
    if config.get( 'coreOffsetCm', 0 ) > 0:
      core_origin[ 0 ] += assy_wd >> 1
      vessel_origin[ 0 ] += assy_wd >> 1
      #vessel_origin[ 1 ] += assy_wd >> 1

#       -- Baffle
#       --
    if core.coreSym == 4:
      baffle_wd = config[ 'baffleWidth' ]

      cur_dx = core_region[ 2 ] + 1

      path = gc.CreatePath()
#      axial_y = core_region[ 1 ]
#      for ax in range( len( axial_levels_dy ) - 1, -1, -1 ):
#        cur_dy = axial_levels_dy[ ax ]
#       if cur_dy > 0:
#         axial_y += cur_dy
#       #end if cur_dy > 0
      #end for ax
      path.MoveToPoint( core_region[ 0 ] + cur_dx, core_region[ 1 ] )
      #path.AddLineToPoint( core_region[ 0 ] + cur_dx, axial_y )
      path.AddLineToPoint(
          core_region[ 0 ] + cur_dx, core_region[ 1 ] + core_axial_dy
          )
      cur_pen = wx.ThePenList.FindOrCreatePen(
          wx.Colour( 155, 155, 155, 255 ), baffle_wd, wx.PENSTYLE_SOLID
          )
      cur_pen.SetCap( wx.CAP_BUTT )
      gc.SetPen( gc.CreatePen( cur_pen ) )
      gc.StrokePath( path )
    #end if core.coreSym == 4

#       -- Barrel
#       --
    path = gc.CreatePath()
    path.MoveToPoint( vessel_origin[ 0 ] + barrel_r, core_region[ 1 ] )
    path.AddLineToPoint(
        vessel_origin[ 0 ] + barrel_r,
        core_region[ 1 ] + core_axial_dy
        )
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 200, 200, 200, 255 ), barrel_wd, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    gc.StrokePath( path )

#       -- Pad
#       --
    pad_wd = config[ 'padWidth' ]
    if pad_wd > 0:
      show_pad = False
      pad_angles = config[ 'padAngles' ]
      if len( pad_angles ) > 0:
        pad_arc_half = config[ 'padArc' ] / 2.0
        for an in pad_angles:
          if theta_deg >= an - pad_arc_half and theta_deg <= an + pad_arc_half:
            show_pad = True
            break
        #end for an
      #end if pad_angles

      if show_pad:
        pad_r = config[ 'padRadius' ] + (pad_wd >> 1)
        path = gc.CreatePath()
        path.MoveToPoint( vessel_origin[ 0 ] + pad_r, core_region[ 1 ] )
        path.AddLineToPoint(
            vessel_origin[ 0 ] + pad_r,
            core_region[ 1 ] + core_axial_dy
            )
        cur_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 175, 175, 175, 255 ), pad_wd, wx.PENSTYLE_SOLID
            )
        cur_pen.SetCap( wx.CAP_BUTT )
        gc.SetPen( gc.CreatePen( cur_pen ) )
        gc.StrokePath( path )
      #end if show_pad
    #end if self.vesselShowPad

#       -- Vessel ring
#       --
    path = gc.CreatePath()
    vx = vessel_origin[ 0 ] + vessel_r
    path.MoveToPoint( vx, vessel_origin[ 1 ] )
    #path.AddLineToPoint( vx, vessel_origin[ 1 ] + vessel_region[ 3 ] )
    path.AddLineToPoint( vx, vessel_origin[ 1 ] + fluence_axial_dy )
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 175, 175, 175, 255 ), vessel_wd, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    gc.StrokePath( path )

#       -- Liner
#       --
    path = gc.CreatePath()
    path.MoveToPoint( vessel_origin[ 0 ] + liner_r, vessel_origin[ 1 ] )
    path.AddLineToPoint(
        vessel_origin[ 0 ] + liner_r,
        vessel_origin[ 1 ] + fluence_axial_dy
        #vessel_origin[ 1 ] + vessel_region[ 3 ]
        )
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 0, 0, 0, 255 ), 1, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    gc.StrokePath( path )
  #end _DrawVesselComponents


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.FindCell()                -
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """
  :returns: ( axial_level, assy_ndx, assy_col, assy_row, pin_col, pin_row,
              node_addr )
"""
    result = core = None

    if self.config is not None and self.dmgr is not None and \
        'coreOffsetCm' in self.config:
      core = self.dmgr.GetCore()

    in_region_flag = False
    if core is not None and core.coreMap is not None:
      core_region = self.config[ 'coreRegion' ]
      if ev_x >= core_region[ 0 ] and ev_y >= core_region[ 1 ] and \
          ev_x <= core_region[ 0 ] + core_region[ 2 ] and \
          ev_y <= core_region[ 1 ] + core_region[ 3 ]:
        in_region_flag = True

    #if core is not None and core.coreMap is not None:
    if in_region_flag:
      assy_wd = self.config[ 'assemblyWidth' ]
      core_axials_dy = self.config[ 'coreAxialLevelsDy' ]
      core_offset_cm = self.config[ 'coreOffsetCm' ]
      npin = self.config[ 'npin' ]
      npinx_cos_theta = self.config[ 'npinxCosTheta' ]
      npiny_sin_theta = self.config[ 'npinySinTheta' ]
      pin_wd = self.config[ 'pinWidth' ]
      theta_cos = self.config[ 'thetaCos' ]
      theta_sin = self.config[ 'thetaSin' ]
      node_addr = -1

#               -- Total pins, effectively
      pin_eff_count = self.cellRange[ -2 ] * npin

      off_x = ev_x - core_region[ 0 ]
      off_y = ev_y - core_region[ 1 ]

      if core_offset_cm > 0:
        off_x -= assy_wd >> 1
        pin_eff_count -= npin >> 1

      axial_level = 0
      ax_y = 0
      for ax in range( len( core_axials_dy ) -1, -1, -1 ):
        ax_y += core_axials_dy[ ax ]
        if off_y <= ax_y:
          axial_level = ax + self.cellRange[ 1 ]
          break

      horz_factor = float( off_x ) / core_region[ 2 ]
      #pin_col = int( horz_factor * npinx_cos_theta * core.npinx )
      #pin_row = int( horz_factor * npiny_sin_theta * core.npiny )
      pin_col = int( horz_factor * theta_cos * pin_eff_count )
      pin_col = max( 0, min( pin_col, pin_eff_count - 1 ) )
      pin_row = int( horz_factor * theta_sin * pin_eff_count )
      pin_row = max( 0, min( pin_row, pin_eff_count - 1 ) )

      assy_col_raw = (pin_col // core.npinx) + self.cellRange[ 0 ]
      assy_row_raw = (pin_row // core.npiny) + self.cellRange[ 0 ]
      assy_col = min( assy_col_raw, core.coreMap.shape[ 1 ] - 1 )
      assy_row = min( assy_row_raw, core.coreMap.shape[ 0 ] - 1 )
      assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

      assy_pin_col = pin_col % core.npinx
      assy_pin_row = pin_row % core.npiny

      if _DEBUG_ and self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
'off_x=%d/%d, pin_eff_count=%d, horz_factor=%f\n  pin_col=%d, pin_row=%d\n' +
'  assy_col_raw=%d, assy_row_raw=%d, assy_col=%d, assy_row=%d\n' +
'  assy_pin_col=%d, assy_pin_row=%d',
            off_x, core_region[ 2 ], pin_eff_count, horz_factor,
            pin_col, pin_row,
            assy_col_raw, assy_row_raw, assy_col, assy_row,
            assy_pin_col, assy_pin_row
            )

      if self.nodalMode:
        node_col = assy_pin_col // (core.npinx >> 1)
        node_row = assy_pin_row // (core.npiny >> 1)
        if node_col > 0:
          node_addr = 3 if node_row > 0 else 1
        else:
          node_addr = 2 if node_row > 0 else 0

      result = (
          axial_level, assy_ndx, assy_col, assy_row,
          assy_pin_col, assy_pin_row, node_addr
          )
    #end if core is not None and core.coreMap is not None

    return  result
  #end FindCell


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.FindCell()                -
  #----------------------------------------------------------------------
#m  def FindCell( self, ev_x, ev_y ):
#m    """
#m@return  ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row, node_addr )
#m"""
#m    result = core = None
#m
#m    if self.config is not None and self.dmgr is not None:
#m      core = self.dmgr.GetCore()
#m
#m    if core is not None and core.coreMap is not None:
#m      assy_wd = self.config[ 'assemblyWidth' ]
#m      axials_dy = self.config[ 'axialLevelsDy' ]
#m      core_region = self.config[ 'coreRegion' ]
#m      node_addr = -1
#m
#m      off_x = ev_x - core_region[ 0 ]
#m      off_y = ev_y - core_region[ 1 ]
#m
#m      if self.mode == 'xz':
#m        assy_row = self.assemblyAddr[ 2 ]
#m      assy_col = min(
#m          int( off_x / assy_wd ) + self.cellRange[ 0 ],
#m          self.cellRange[ 2 ] - 1
#m          )
#m      assy_col = max( assy_col, self.cellRange[ 0 ] )
#m      assy_col_or_row = assy_col
#m
#m      pin_offset = off_x % assy_wd
#m      if self.nodalMode:
#m        pin_col_or_row, node_addr = self._FindPinNodal( pin_offset )
#m      else:
#m        pin_col_or_row = self._FindPinNonNodal( pin_offset )
#m      max_col_or_row = core.npinx + 1 if self.channelMode else core.npinx
#m      if pin_col_or_row >= max_col_or_row: pin_col_or_row = -1
#m
#m      else:
#m        assy_col = self.assemblyAddr[ 1 ]
#m      assy_row = min(
#m          int( off_y / assy_wd ) + self.cellRange[ 0 ],
#m          self.cellRange[ 2 ] - 1
#m          )
#m      assy_row = max( assy_row, self.cellRange[ 0 ] )
#m      assy_col_or_row = assy_row
#m
#m      pin_offset = off_x % assy_wd
#m      if self.nodalMode:
#m        pin_col_or_row, node_addr = self._FindPinNodal( pin_offset )
#m      else:
#m        pin_col_or_row = self._FindPinNonNodal( pin_offset )
#m      max_col_or_row = core.npiny + 1 if self.channelMode else core.npiny
#m      if pin_col_or_row >= max_col_or_row: pin_col_or_row = -1
#m      #end if-else self.mode
#m
#m      axial_level = 0
#m      ax_y = 0
#m      for ax in range( len( axials_dy ) -1, -1, -1 ):
#m        ax_y += axials_dy[ ax ]
#m      if off_y <= ax_y:
#m        axial_level = ax + self.cellRange[ 1 ]
#m        break
#m
#m      assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
#m      result = \
#m          ( assy_ndx, assy_col_or_row, axial_level, pin_col_or_row, node_addr )
#m    #end if core is not None and core.coreMap is not None
#m
#m    return  result
#m  #end FindCell


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetAnimationIndexes()     -
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return                 list of indexes or None
"""
    return  ( 'statepoint', )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._GetAxialRanges()         -
  #----------------------------------------------------------------------
  def _GetAxialRanges( self, *types  ):
    """Resolves the axial range in the core.fluenceMesh.z that should be
displayed against the current vertical zoom level (which we don't currently do) and the non-fluence dataset axial mesh.
    Args:
        types (list): 'core', 'fluence'
    Returns:
        dict: keys
            cm_bottom:     bottom level in cm
            cm_top:        top level in cm
            core_bottom_ndx: core bottom index (if ``types`` includes 'core')
            core_top_ndx: core top index (if ``types`` includes 'core')
            fluence_bottom_ndx: fluence bottom index
                (if ``types`` includes 'fluence')
            fluence_top_ndx: fluence top index
                (if ``types`` includes 'fluence')
"""
    core = self.dmgr.GetCore()

    axial_mesh = self.dmgr.GetAxialMesh2( mesh_type = 'all' )
#    core_axial_mesh = self.dmgr.GetAxialMesh2( self.curDataSet, 'pin' )
#    fluence_axial_mesh = self.dmgr.GetAxialMesh2( self.fluenceAddr.dataSetName, 'fluence' )

    #top_ndx = min( self.cellRange[ 3 ] - 1, len( axial_mesh ) - 1 )
    top_ndx = min( self.cellRange[ 3 ], len( axial_mesh ) - 1 )
    bottom_ndx = max( self.cellRange[ 1 ], 0 )
    cm_top = axial_mesh[ top_ndx ]
    cm_bottom = axial_mesh[ bottom_ndx ]

    result = { 'cm_bottom': cm_bottom, 'cm_top': cm_top }

    if types:
      if 'core' in types:
        core_axial_mesh = self.dmgr.GetAxialMesh2( self.curDataSet, 'pin' )
        result[ 'core_bottom_ndx' ] = \
            self.dmgr.GetAxialMeshIndex( cm_bottom, self.curDataSet, 'pin' )
        result[ 'core_top_ndx' ] = \
            self.dmgr.GetAxialMeshIndex( cm_top, self.curDataSet, 'pin' )

      if 'fluence' in types:
        fluence_axial_mesh = self.dmgr.\
            GetAxialMesh2( self.fluenceAddr.dataSetName, 'fluence' )
        result[ 'fluence_bottom_ndx' ] = self.dmgr.GetAxialMeshIndex(
            cm_bottom, self.fluenceAddr.dataSetName, 'fluence'
            )
        result[ 'fluence_top_ndx' ] = self.dmgr.\
            GetAxialMeshIndex( cm_top, self.fluenceAddr.dataSetName, 'fluence' )
    #end if types

    return  result
  #end _GetAxialRanges


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetDataSetTypes()         -
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    #return  [ 'channel', 'pin', ':assembly', ':node' ]
    return  [ 'channel', 'pin', ':assembly' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetEventLockSet()         -
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """
"""
    locks = set([
        STATE_CHANGE_axialValue,
        STATE_CHANGE_coordinates,
        STATE_CHANGE_curDataSet,
        STATE_CHANGE_fluenceAddr,
        STATE_CHANGE_scaleMode,
        STATE_CHANGE_timeValue
        ])
#       STATE_CHANGE_stateIndex
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetInitialCellRange()     -
  #----------------------------------------------------------------------
  def GetInitialCellRange( self ):
    """Creates the range using y for the axial.
@return                 ( xy-left, z-bottom, xy-right+1, z-top+1, d-xy, dz )
"""
    core = None
    if self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is None:
      result = ( 0, 0, 0, 0, 0, 0 )

    else:
      result = list( self.dmgr.ExtractSymmetryExtent() )
      result[ 1 ] = 0
      #mesh = self.dmgr.GetAxialMeshCenters2( self.curDataSet )
      mesh = self.dmgr.GetAxialMeshCenters2( mesh_type = 'all' )
      result[ 3 ] = result[ 5 ] = len( mesh )

    return  result
  #end GetInitialCellRange



  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetPrintFontScale()       -
  #----------------------------------------------------------------------
  def GetPrintFontScale( self ):
    """
@return         1.0
"""
    return  1.0
  #end GetPrintFontScale


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetSpecialDataSetTypes()  -
  #----------------------------------------------------------------------
  def GetSpecialDataSetTypes( self ):
    """Accessor specifying the types of special datasets which can be
processed in this widget.  For now this is limited to 'fluence'.

@return                 [ 'fluence' ]
"""
    return  [ 'fluence' ]
  #end GetSpecialDataSetTypes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetTitle()                -
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Vessel Core Axial 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.GetToolButtonDefs()       -
  #----------------------------------------------------------------------
#m  def GetToolButtonDefs( self ):
#m    """
#m"""
#m    return  self.toolButtonDefs
#m  #end GetToolButtonDefs


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._HiliteBitmap()           -
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None:
      line_wd = -1
      rect = None

      rel_axial = self.axialValue.pinIndex - self.cellRange[ 1 ]

#      if self.mode == 'xz':
#        rel_cell = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
#      else:
#        rel_cell = self.assemblyAddr[ 2 ] - self.cellRange[ 0 ]
      rel_cell = 0

      if rel_cell >= 0 and rel_cell < self.cellRange[ -2 ] and \
          rel_axial >= 0 and rel_axial < self.cellRange[ -1 ]:
        assy_wd = config[ 'assemblyWidth' ]
        axial_levels_dy = config[ 'coreAxialLevelsDy' ]
        core_region = config[ 'coreRegion' ]
        line_wd = config[ 'lineWidth' ]
        #pin_wd = config[ 'pinWidth' ]

        axial_y = core_region[ 1 ]
        for ax in range( len( axial_levels_dy ) - 1, rel_axial, -1 ):
          axial_y += axial_levels_dy[ ax ]

        rect = [
            rel_cell * assy_wd + core_region[ 0 ], axial_y,
            assy_wd, axial_levels_dy[ rel_axial ]
            ]
      #end if selection w/in image

#                       -- Draw?
#                       --
      if rect is not None:
        new_bmap = self._CopyBitmap( bmap )

        dc = wx.MemoryDC( new_bmap )
        gc = wx.GraphicsContext.Create( dc )
        gc.SetPen(
            wx.ThePenList.FindOrCreatePen(
                HILITE_COLOR_primary,
                line_wd, wx.PENSTYLE_SOLID
                )
            )
        path = gc.CreatePath()
        path.AddRectangle( *rect )
        gc.StrokePath( path )

        dc.SelectObject( wx.NullBitmap )
        result = new_bmap
      #end if rect
    #end if config

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._InitEventHandlers()      -
  #----------------------------------------------------------------------
  def _InitEventHandlers( self ):
    """
"""
    #self._SetMode( 'core' )

    self.bitmapCtrl.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    #self.bitmapCtrl.Bind( wx.EVT_LEFT_DOWN, self._OnLeftDown )
    self.bitmapCtrl.Bind( wx.EVT_LEFT_UP, self._OnLeftUp )
    self.bitmapCtrl.Bind( wx.EVT_MOTION, self._OnMouseMotion )
  #end _InitEventHandlers


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._IsAssemblyAware()        -
  #----------------------------------------------------------------------
  def _IsAssemblyAware( self ):
    """
@return                 False
"""
    return  False
  #end _IsAssemblyAware


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.IsTupleCurrent()          -
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """Compares tuple created with _CreateStateTuple( self ).
@param  tpl             tuple of state values
@return                 True if it matches the current state, false otherwise
"""
#m    th = self.fluenceAddr.thetaIndex
#m    if self.mode == 'xz':
#m      t = ( self.stateIndex, self.assemblyAddr[ 2 ], self.subAddr[ 1 ], th )
#m    else:
#m      t = ( self.stateIndex, self.assemblyAddr[ 1 ], self.subAddr[ 0 ], th )
    t = ( self.stateIndex, self.fluenceAddr.thetaIndex )
    return  tpl == t
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._LoadDataModelUI()        -
  #----------------------------------------------------------------------
  def _LoadDataModelUI( self, reason ):
    """Updates self.angleSlider range based on coreSym.
Must be called on the UI thread.
"""
    core = self.dmgr.GetCore()
    r = ( 0, 359 )  if core is not None and core.coreSym == 1  else ( 0, 89 )
    self.angleSlider.SetRange( *r )
    self.angleSlider.SetValue( r[ 0 ] )
  #end _LoadDataModelUI


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._LoadDataModelValues()    -
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """
"""
    if (reason & STATE_CHANGE_coordinates) > 0:
      self.assemblyAddr = self.state.assemblyAddr
      self.subAddr = self.state.subAddr

    if (reason & STATE_CHANGE_curDataSet) > 0:
      self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

    if (reason & STATE_CHANGE_fluenceAddr) > 0:
      self.fluenceAddr.update( self.state.fluenceAddr )
      self.fluenceAddr.dataSetName = \
self._FindFirstDataSet( self.fluenceAddr.dataSetName, ds_type = 'fluence' )

    ds_type = self.dmgr.GetDataSetType( self.curDataSet )
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.LoadProps()               -
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict      dict object from which to deserialize properties
"""
    #for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
    for k in ( 'assemblyAddr', 'nodeAddr', 'subAddr' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( VesselCoreAxial2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnAngleSlider()          -
  #----------------------------------------------------------------------
  def _OnAngleSlider( self, ev ):
    """Handles events from the angle slider.  Called on the UI thread.
"""
    ev.Skip()
    obj = ev.GetEventObject()
    val = obj.GetValue()
    self.GetTopLevelParent().GetApp().\
        DoBusyEventOp( self._OnAngleSliderImpl, val )
  #end _OnAngleSlider


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnAngleSliderImpl()      -
  #----------------------------------------------------------------------
  def _OnAngleSliderImpl( self, val ):
    """Handles events from the angle slider.  Called on the UI thread.
"""
    core = self.dmgr.GetCore()
    val_ndx = core.fluenceMesh.GetThetaIndex( val * math.pi / 180.0 )

    if val_ndx >= 0 and val_ndx != self.fluenceAddr.thetaIndex:
      fluence_addr = self.fluenceAddr.copy()
      fluence_addr.update( thetaIndex = val_ndx )
      self.FireStateChange( fluence_addr = fluence_addr )
  #end _OnAngleSliderImpl


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnClick()                -
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    x = ev.GetX()
    y = ev.GetY()
    self.GetTopLevelParent().GetApp().DoBusyEventOp( self._OnClickImpl, x, y )
  #end _OnClick


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnClickImpl()            -
  #----------------------------------------------------------------------
  def _OnClickImpl( self, x, y ):
    """
"""
    valid = False
    cell_info = self.FindCell( x, y )
    if cell_info is not None:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          axial_level = cell_info[ 0 ],
          assembly_index = cell_info[ 1 ]
          )

    if valid:
      state_args = {}
      state_args[ 'assembly_addr' ] = cell_info[ 1 : 4 ]
      state_args[ 'axial_value' ] = self.dmgr.GetAxialValue(
          self.curDataSet, core_ndx = cell_info[ 0 ]
          )
      self.FireStateChange( **state_args )
    #end if valid
  #end _OnClickImpl


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnFindMinMax()           -
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    self.GetTopLevelParent().GetApp().DoBusyEventOp(
        self._OnFindMinMaxImpl, mode, all_states_flag, all_assy_flag
        )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._OnFindMinMaxImpl()       -
  #----------------------------------------------------------------------
  def _OnFindMinMaxImpl( self, mode, all_states_flag, all_assy_flag ):
    """Calls _OnFindMinMaxPin().
"""
    if self.config and self.fluenceAddr and self.fluenceAddr.dataSetName:
      self._OnFindMinMaxFluence(
          mode, self.fluenceAddr, all_states_flag,
          self.config.get( 'fluenceDataSetExpr' ),
          self.config.get( 'radiusStartIndex', 0 )
          )
  #end _OnFindMinMaxImpl


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.SaveProps()               -
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict      dict object to which to serialize properties
"""
    super( VesselCoreAxial2DView, self ).SaveProps( props_dict, for_drag = for_drag )

    for k in ( 'assemblyAddr', 'nodeAddr', 'subAddr' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.SetDataSet()              -
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    ds_type = self.dmgr.GetDataSetType( qds_name )
    if ds_type == 'fluence':
      if qds_name != self.fluenceAddr.dataSetName:
        self.fluenceAddr.SetDataSetName( qds_name )
        wx.CallAfter( self.UpdateState, resized = True )
        self.FireStateChange( fluence_addr = self.fluenceAddr )

    elif qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView.SetMode()                 -
  #----------------------------------------------------------------------
#m  def SetMode( self, mode, button = None ):
#m    """May be called from any thread.
#m@param  mode          either 'xz' or 'yz', defaulting to the former on
#m                      any other value
#m@param  button                optional button to update
#m"""
#m    if mode != self.mode:
#m      self.mode = 'yz' if mode == 'yz' else 'xz'
#m      self.cellRange = list( self.GetInitialCellRange() )
#m      del self.cellRangeStack[ : ]
#m
#m      wx.CallAfter( self._SetModeImpl, button )
#m  #end SetMode


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._SetModeImpl()            -
  #----------------------------------------------------------------------
#m  def _SetModeImpl( self, button = None ):
#m    """Must be called from the event thread.
#m@param  mode          mode, already setjdd
#m                      any other value
#m@param  button                optional button to update
#m"""
#m    if button is None:
#m      for ch in self.GetParent().GetControlPanel().GetChildren():
#m        if isinstance( ch, wx.BitmapButton ) and \
#m          ch.GetToolTip().GetTip().find( 'Toggle Slice' ) >= 0:
#m          button = ch
#m        break
#m    #end if
#m
#m    if button is not None:
#m      if self.mode == 'yz':
#m        bmap = Widget.GetBitmap( 'X_16x16' )
#m      tip_str = 'Toggle Slice to X-Axis'
#m      else:
#m        bmap = Widget.GetBitmap( 'Y_16x16' )
#m      tip_str = 'Toggle Slice to Y-Axis'
#m
#m      button.SetBitmapLabel( bmap )
#m      button.SetToolTip( wx.ToolTip( tip_str ) )
#m      button.Update()
#m      self.GetParent().GetControlPanel().Layout()
#m    #end if
#m
#m    self.Redraw()
#m  #end _SetModeImpl


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._UpdateControls()         -
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    """Must be called from the UI thread.
"""
    core = self.dmgr.GetCore()
    if self.angleSlider is not None and core is not None:
      theta_deg = core.fluenceMesh.\
          GetTheta( self.fluenceAddr.thetaIndex, center = False, units = 'deg' )
      if theta_deg != self.angleSlider.GetValue():
        self.angleSlider.SetValue( theta_deg )
  #end _UpdateControls


  #----------------------------------------------------------------------
  #     METHOD: VesselCoreAxial2DView._UpdateDataSetStateValues()       -
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type, clear_zoom_stack = False ):
    """Updates channelmode and nodalMode properties.
    Args:
        ds_type (str): dataset category/type
        clear_zoom_stack (boolean): True to clear in zoom stack
"""
    self.cellRange = list( self.GetInitialCellRange() )
    del self.cellRangeStack[ : ]

    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #     METHOD:         VesselCoreAxial2DView._UpdateStateValues()      -
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return                 kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( VesselCoreAxial2DView, self )._UpdateStateValues( **kwargs )
    changed = kwargs.get( 'changed', False )
    resized = kwargs.get( 'resized', False )
    update_controls = False

    core = self.dmgr.GetCore()

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      changed = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]

#    if 'node_addr' in kwargs:
#      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
#      if node_addr != self.nodeAddr:
#        self.nodeAddr = node_addr

#    if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] != self.subAddr:
#      if kwargs[ 'sub_addr' ][ pin_ndx ] != self.subAddr[ pin_ndx ]:
#        resized = True
#      else:
#        changed = True
#      self.subAddr = self.dmgr.NormalizeSubAddr(
#          kwargs[ 'sub_addr' ],
#         'channel' if self.channelMode else 'pin'
#         )
#    #end if 'sub_addr'

    if 'fluence_addr' in kwargs and \
        kwargs[ 'fluence_addr' ] != self.fluenceAddr:
      resized = update_controls = True
      self.fluenceAddr.update( self.state.fluenceAddr )

    if 'weights_mode' in kwargs:
      kwargs[ 'resized' ] = True

    if update_controls or resized:
      wx.CallAfter( self._UpdateControls )

    if changed:
      kwargs[ 'changed' ] = True
    if resized:
      kwargs[ 'resized' ] = True

    return  kwargs
  #end _UpdateStateValues

#end VesselCoreAxial2DView
