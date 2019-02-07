#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#       NAME:           vessel_core_view.py                             -
#       HISTORY:                                                        -
#               2019-01-30      leerw@ornl.gov                          -
#         Trying to account for full core on _OnClickImpl(), and trying
#         to divine a radius as well as a theta.
#               2019-01-17      leerw@ornl.gov                          -
#               2019-01-16      leerw@ornl.gov                          -
#         Transition from tally to fluence.
#               2018-05-04      leerw@ornl.gov                          -
#         Fixing color mapping, drawing tally cells outside in.
#               2018-03-02      leerw@ornl.gov                          -
#         Migrating to _CreateEmptyBitmapAndDC().
#               2018-02-05      leerw@ornl.gov                          -
#         Moving Linux/GTK/X11 image manipulation to the UI thread.
#               2018-02-03      leerw@ornl.gov                          -
#         Fixed buggy axial value handling b/w pin and tally datasets.
#               2017-12-01      leerw@ornl.gov                          -
#         Checking for thetaIndex-only change in tallyAddr in
#         _UpdateStateValues() to avoid recreating the image.
#               2017-11-16      leerw@ornl.gov                          -
#         Migratingt to wx.Bitmap instead of PIL.Image.
#               2017-09-23      leerw@ornl.gov                          -
#         Using new TallyAddress class.
#               2017-09-14      leerw@ornl.gov                          -
#         Fixed bug in LoadProps() where tallyAddr[0] must be converted
#         from a dict to a DataSetName instance.
#               2017-09-11      leerw@ornl.gov                          -
#         Minor cleanup while creating through vessel_core_axial_view.py.
#               2017-08-18      leerw@ornl.gov                          -
#         Using AxialValue class.
#               2017-07-14      leerw@ornl.gov                          -
#         Fixed pad display.
#               2017-05-19      leerw@ornl.gov                          -
#         Implemented clipboard copy of tally data.
#               2017-05-13      leerw@ornl.gov                          -
#         Added tallyAddr to {Load,Save}Props().
#               2017-05-05      leerw@ornl.gov                          -
#         Modified LoadDataModelXxx() methods to process the reason param.
#               2017-04-25      leerw@ornl.gov                          -
#         Processing multiple pad angles if specified.
#               2017-04-03      leerw@ornl.gov                          -
#         Using VesselGeometry.
#               2017-03-27      leerw@ornl.gov                          -
#               2017-02-27      leerw@ornl.gov                          -
#         To scale.
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

from data.datamodel import *
from data.utils import *
from event.state import *

from .raster_widget import *
from .widget import *


#RADS_PER_DEG = math.pi / 180.0
#TWO_PI = math.pi * 2.0


#------------------------------------------------------------------------
#       CLASS:          VesselCore2DView                                -
#------------------------------------------------------------------------
class VesselCore2DView( RasterWidget ):
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
  #     METHOD:         VesselCore2DView.__init__()                     -
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.channelMode = False

    self.fluenceAddr = FluenceAddress( radiusIndex = 0, thetaIndex = 0 )
    self.nodalMode = False
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )

    #self.vesselShowPad = True
                        # -- offsets in cm to edge given current cellRange
    self.vesselOffset = [ 0, 0 ]

    super( VesselCore2DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateClipboardData()         -
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
  #     METHOD: VesselCore2DView._CreateClipboardDisplayedData()        -
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return                 text or None
"""
    csv_text = None
    core = self.dmgr.core

    dset = None
    z_ndx = self.axialValue.fluenceIndex
    if z_ndx >= 0:
      dset = \
          self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )
      #z_ndx = min( z_ndx, core.fluenceMesh.nz - 1 )
      z_ndx = min( z_ndx, core.fluenceMesh.nz - 2 )

    if dset is not None and z_ndx >= 0:
      break_angle = TWO_PI  if core.coreSym == 1 else  PI_OVER_2
      dset_array = np.array( dset )

      #csv_text = '"%s (mult=%s,stat=%s): axial=%.3f; %s=%.3g"\n'
      csv_text = '"%s: z=%.3f; %s=%.3g"\n' % (
          self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
          #core.fluenceMesh.z[ z_ndx ],
          core.fluenceMesh.zcenters[ z_ndx ],
          self.state.timeDataSet,
          self.timeValue
          )
      csv_text += 'r,theta,value\n'

      r_start_ndx = self.config[ 'radiusStartIndex' ]
      for ri in xrange( r_start_ndx, core.fluenceMesh.nr ):
        for ti in xrange( core.fluenceMesh.ntheta ):
          start = core.fluenceMesh.theta[ ti ]
          if start >= break_angle:  break
          value = dset_array[ z_ndx, ti, ri ]
          row = '%.3f,%.7g,%.7g\n' % \
              ( core.fluenceMesh.r[ ri ], core.fluenceMesh.theta[ ti ], value )
          csv_text += row
        #end for ti
      #end for ri
    #end if dset is not None and z_ndx >= 0

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateClipboardSelectedData() -
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return                 text or None
"""
    csv_text = None
    core = self.dmgr.core

    dset = None
    z_ndx = self.axialValue.fluenceIndex
    theta_ndx = self.fluenceAddr.thetaIndex
    #r_ndx = self.fluenceAddr.radiusIndex
    #if z_ndx >= 0 and theta_ndx >= 0 and r_ndx >= 0:
    if z_ndx >= 0 and theta_ndx >= 0:
      dset = \
          self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )
      #z_ndx = min( z_ndx, core.fluenceMesh.nz - 1 )
      z_ndx = min( z_ndx, core.fluenceMesh.nz - 2 )
      theta_ndx = min( theta_ndx, core.fluenceMesh.ntheta - 1 )
      #r_ndx = min( r_ndx, core.fluenceMesh.nr - 1 )

    if dset is not None and z_ndx >= 0:
      dset_array = np.array( dset )

      #csv_text = '"%s: z=%.3f; theta=%.3f, r=%.3f %s=%.3g"\n'
      csv_text = '"%s: z=%.3f; theta=%.3f, %s=%.3g"\n' % (
          self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
          core.fluenceMesh.zcenters[ z_ndx ],
          core.fluenceMesh.GetThetaRads( theta_ndx ),
          #core.fluenceMesh.GetRadius( r_ndx ),
          self.state.timeDataSet,
          self.timeValue
          )
      csv_text += 'r,value\n'

      r_start_ndx = self.config[ 'radiusStartIndex' ]
      for ri in xrange( r_start_ndx, core.fluenceMesh.nr ):
        value = dset_array[ z_ndx, theta_ndx, ri ]
        row = '%.3f,%.7g\n' % ( core.fluenceMesh.r[ ri ], value )
        csv_text += row
      #end for ri
    #end if dset is not None and core is not None

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateDrawConfig()            -
  #----------------------------------------------------------------------
  def _CreateDrawConfig( self, **kwargs ):
    """Creates a draw configuration based on imposed 'size' (wd, ht ) or
'scale' (pixels per pin) from which a size is determined.
If neither are specified, a default 'scale' value of 4 is used.
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
            coreRegion (list(int)): x, y, wd, ht
            imageSize (tuple(int)): wd, ht
            lineWidth (int): hilite line pixel width
            pinWidth (int): pixels to draw a pin
            pixPerCm (float): non-integral pixels per centimeter
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

    font_size = config[ 'fontSize' ]
    label_size = config[ 'labelSize' ]
    legend_bmap = config[ 'legendBitmap' ]
    legend_size = config[ 'legendSize' ]

    core = self.dmgr.GetCore()
    vessel_geom = core.vesselGeom
    fluence_mesh = core.fluenceMesh

    radius_start_ndx = 1
    fluence_ds_expr = fluence_ds_range = fluence_legend_pil_im = None
    fluence_legend_size = ( 0, 0 )
    theta_stop_ndx = fluence_mesh.ntheta

    if vessel_geom is not None and fluence_mesh.IsValid() and \
        self.fluenceAddr.dataSetName is not None:
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
            vmin = max( fluence_ds_range[ 0 ], 1.0e-16 ),
            vmax = max( fluence_ds_range[ 1 ], 1.0e-16 ),
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
    #end if vessel_geom is not None and fluence_mesh.IsValid()...

#               -- We want an integral number of pixels per pin
#               --
    npin = max( core.npinx, core.npiny )

    if self.nodalMode:
      cm_per_pin = core.apitch / 2.0
    elif self.channelMode:
      cm_per_pin = float( core.apitch ) / (npin + 1)
    else:
      cm_per_pin = float( core.apitch ) / npin

    vessel_wd_cm = core_wd_cm = self.cellRange[ -2 ] * core.apitch
    vessel_ht_cm = core_ht_cm = self.cellRange[ -1 ] * core.apitch

    if fluence_mesh.IsValid():
      if core.coreSym == 4 and max( core.nassx, core.nassy ) % 2 == 1:
        core_offset_cm = 0.5 * core.apitch
      else:
        core_offset_cm = 0.0

      if core.coreSym == 4:
        vessel_wd_cm = max(
            core_wd_cm + core_offset_cm + vessel_geom.vesselOuterOffset,
            fluence_mesh.r[ -1 ]
            )
        vessel_ht_cm = max(
            core_ht_cm + core_offset_cm + vessel_geom.vesselOuterOffset,
            fluence_mesh.r[ -1 ]
            )
      elif core.coreSym == 1:
        vessel_wd_cm = max(
            core_wd_cm + (vessel_geom.vesselOuterOffset * 2.0),
            fluence_mesh.r[ -1 ] * 2.0
            )
        vessel_ht_cm = max(
            core_ht_cm + (vessel_geom.vesselOuterOffset * 2.0),
            fluence_mesh.r[ -1 ] * 2.0
            )
      else:
        vessel_wd_cm = core_wd_cm
        vessel_ht_cm = core_ht_cm
    #end if fluence_mesh.IsValid()

    #xxxxx _CreateBaseDrawConfig() sets
    if 'clientSize' in config:
      wd, ht = config[ 'clientSize' ]

      # label : core : font-sp : legend : legend
      #   plus 1 pix for baffle, wd and ht
      #xxxxx revisit font_size, bigger than pixel
      vessel_wd = \
          wd - label_size[ 0 ] - 2 - (font_size << 1) - \
          legend_size[ 0 ] - fluence_legend_size[ 0 ]
      working_ht = max( ht, legend_size[ 1 ], fluence_legend_size[ 1 ] )
      vessel_ht = working_ht - label_size[ 1 ] - 2 - (font_size << 1)

      pix_per_cm_x = float( vessel_wd ) / vessel_wd_cm
      pix_per_cm_y = float( vessel_ht ) / vessel_ht_cm
      if self.fitMode == 'ht':
        pix_per_pin = math.floor( min( pix_per_cm_x, pix_per_cm_y ) * cm_per_pin )
      else:
        pix_per_pin = math.ceil( min( pix_per_cm_x, pix_per_cm_y ) * cm_per_pin )
      pix_per_pin = max( 1, int( pix_per_pin ) )

    else:
      pix_per_pin = int( kwargs[ 'scale' ] ) if 'scale' in kwargs else 4
      #font_size = self._CalcFontSize( 768 )
      font_size = self._CalcFontSize( 1024 * pix_per_pin )

    pix_per_cm = pix_per_pin / cm_per_pin

    if self.nodalMode:
      pin_wd = int( pix_per_pin ) << 4
      assy_wd = pin_wd << 1
    elif self.channelMode:
      pin_wd = pix_per_pin
      assy_wd = pin_wd * (npin + 1)
    else:
      pin_wd = pix_per_pin
      assy_wd = pin_wd * npin

    core_wd = self.cellRange[ -2 ] * assy_wd
    core_ht = self.cellRange[ -1 ] * assy_wd

    vessel_wd = int( math.ceil( pix_per_cm * vessel_wd_cm ) )
    vessel_ht = int( math.ceil( pix_per_cm * vessel_ht_cm ) )

    region_x = label_size[ 0 ] + 2
    region_y = label_size[ 1 ] + 2
    image_wd = \
        region_x + vessel_wd + (font_size << 1) + \
        legend_size[ 0 ] + fluence_legend_size[ 0 ]
    image_ht = \
max( region_y + vessel_ht, legend_size[ 1 ], fluence_legend_size[ 1 ] ) + \
(font_size << 2)

    value_font_size = assy_wd >> 1

    config[ 'assemblyWidth' ] = assy_wd
    config[ 'coreRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, core_wd, core_ht ]
    config[ 'imageSize' ] = ( image_wd, image_ht )
    config[ 'lineWidth' ] = max( 1, min( 5, int( assy_wd / 20.0 ) ) )
    config[ 'pinWidth' ] = pin_wd
    config[ 'pixPerCm' ] = pix_per_cm
    config[ 'valueFontSize' ] = value_font_size
    config[ 'vesselRegion' ] = \
        [ label_size[ 0 ] + 2, label_size[ 1 ] + 2, vessel_wd, vessel_ht ]

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
#      config[ 'radiusStartIndex' ] = 1

      config[ 'fluenceDataRange' ] = fluence_ds_range
      config[ 'fluenceDataSetExpr' ] = fluence_ds_expr
      config[ 'fluenceMapper' ] = fluence_mapper

      config[ 'thetaStopIndex' ] = theta_stop_ndx
      config[ 'vesselRadius' ] = vessel_r

      if self.showLegend:
        config[ 'fluenceLegendBitmap' ] = fluence_legend_bmap
        config[ 'fluenceLegendSize' ] = fluence_legend_size
    #end if fluence_ds_range is not None

    return  config
  #end _CreateDrawConfig


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateMenuDef()               -
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( VesselCore2DView, self )._CreateMenuDef()
    new_menu_def = \
        [ x for x in menu_def if x.get( 'label' ) != 'Unzoom' ]
    return  new_menu_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateRasterImage()           -
  #----------------------------------------------------------------------
  def _CreateRasterImage( self, tuple_in, config = None ):
    """Called in background task to create the PIL image for the state.

    Args:
        tuple_in: (tuple) 0-based indexes
            ( state_index, pin_axial_level, fluence_axial_level )
"""
    #start_time = timeit.default_timer()
    state_ndx = tuple_in[ 0 ]
    pin_axial_level = tuple_in[ 1 ]
    fluence_mesh_ndx = tuple_in[ 2 ]
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'tuple_in=%s', str( tuple_in ) )

    bmap = None

    core = dset = None
    if config is None:
      config = self.config
    if config is not None and self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      core = self.dmgr.GetCore()

    if dset is not None and core is not None:
      #xxxxx needed?
      if 'coreRegion' not in config:
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug( 'coreRegion missing from config, reconfiguring' )
        if 'clientSize' in config:
          config = self._CreateDrawConfig( size = config[ 'clientSize' ] )
        else:
          config = self._CreateDrawConfig( scale = config[ 'scale' ] )

      assy_wd = config[ 'assemblyWidth' ]
      core_region = config[ 'coreRegion' ]
      font = config[ 'font' ]
      font_size = config[ 'fontSize' ]
      im_wd, im_ht = config[ 'imageSize' ]
      label_font = config[ 'labelFont' ]
      legend_bmap = config[ 'legendBitmap' ]
      legend_size = config[ 'legendSize' ]
      mapper = config[ 'mapper' ]
      pin_wd = config[ 'pinWidth' ]
      pix_per_cm = config[ 'pixPerCm' ]
      fluence_ds_range = config.get( 'fluenceDataRange' )
      fluence_legend_bmap = config.get( 'fluenceLegendBitmap' )
      fluence_legend_size = config.get( 'fluenceLegendSize' )
      value_font = config[ 'valueFont' ]
      value_font_size = config[ 'valueFontSize' ]
      vessel_region = config[ 'vesselRegion' ]

      fluence_mesh = core.fluenceMesh

#               -- "Item" refers to channel or pin
      item_factors = None
      if self.state.weightsMode == 'on':
        item_factors = self.dmgr.GetFactors( self.curDataSet )

      dset_array = np.array( dset )
      dset_shape = dset.shape
      if self.nodalMode:
        cur_nxpin = cur_nypin = item_col_limit = item_row_limit = 2
      else:
        if self.channelMode:
          item_col_limit = core.npinx + 1
          item_row_limit = core.npiny + 1
        else:
          item_col_limit = core.npinx
          item_row_limit = core.npiny
        cur_nxpin = min( item_col_limit, dset_shape[ 1 ] )
        cur_nypin = min( item_row_limit, dset_shape[ 0 ] )
      #end if-else self.nodalMode

      ds_range = config[ 'dataRange' ]
      #value_delta = ds_range[ 1 ] - ds_range[ 0 ]

#                       -- Limit axial level
#                       --
      pin_axial_level = min( pin_axial_level, dset_shape[ 2 ] - 1 )
      pin_axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, pin_ndx = pin_axial_level )
      fluence_axial_value = self.dmgr.\
          GetAxialValue( self.curDataSet, fluence_ndx = fluence_mesh_ndx )

      additional = None
      if fluence_ds_range is not None:
        additional = '%s at %.3f' % (
            self.dmgr.GetDataSetDisplayName( self.fluenceAddr.dataSetName ),
            fluence_axial_value.cm
            )
      title_templ, title_size = self._CreateTitleTemplate2(
          font, self.curDataSet, dset_shape, self.state.timeDataSet,
          axial_ndx = 2,
          additional = additional
          )

      draw_value_flag = \
          self.curDataSet is not None and \
          dset_shape[ 0 ] == 1 and dset_shape[ 1 ] == 1
          #value_font is not None
      node_value_draw_list = []
      assy_value_draw_list = []

#                       -- Create image
#                       --
      bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
      gc = self._CreateGraphicsContext( dc )
      trans_brush = self._CreateTransparentBrush( gc )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      if self.showLabels:
        glabel_font = gc.CreateFont( label_font, wx.BLACK )
        gc.SetFont( glabel_font )

      assy_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
          ) )
      node_pen = gc.CreatePen( wx.ThePenList.FindOrCreatePen(
          wx.Colour( 100, 100, 100, 255 ), 1, wx.PENSTYLE_SOLID
          ) )

#                       -- Loop on assembly rows
#                       --
      assy_y = core_region[ 1 ]
      for assy_row in range( self.cellRange[ 1 ], self.cellRange[ 3 ], 1 ):
#                               -- Row label
#                               --
        if self.showLabels:
          label = core.GetRowLabel( assy_row )
          #label_size = pil_font.getsize( label )
          label_size = gc.GetFullTextExtent( label )
          label_y = assy_y + ((assy_wd - label_size[ 1 ]) / 2.0)
          gc.DrawText( label, 1, label_y )

#                               -- Loop on col
#                               --
        assy_x = core_region[ 0 ]
        for assy_col in range( self.cellRange[ 0 ], self.cellRange[ 2 ], 1 ):
          brush_color = None
#                                       -- Column label
#                                       --
          if assy_row == self.cellRange[ 1 ] and self.showLabels:
            label = core.GetColLabel( assy_col )
            #label_size = pil_font.getsize( label )
            label_size = gc.GetFullTextExtent( label )
            label_x = assy_x + ((assy_wd - label_size[ 0 ]) / 2.0)
            gc.DrawText( label, label_x, 1 )
          #end if writing column label

          assy_ndx = core.coreMap[ assy_row, assy_col ] - 1

          if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
            #item_y = assy_y + 1
            item_y = assy_y

#                                               -- Map to colors
            cur_array = dset_array[ :, :, pin_axial_level, assy_ndx ]
            colors = mapper.to_rgba( cur_array, bytes = True )
            if item_factors is not None:
              cur_factors = item_factors[ :, :, pin_axial_level, assy_ndx ]
              colors[ cur_factors == 0 ] = trans_color_arr
            colors[ np.isnan( cur_array ) ] = trans_color_arr
            colors[ np.isinf( cur_array ) ] = trans_color_arr

#                                               -- Loop on chan/pin rows
            node_ndx = 0
            for item_row in xrange( item_row_limit ):
              #item_x = assy_x + 1
              item_x = assy_x
#                                                       -- Loop on chan/pin cols
              cur_item_row = min( item_row, cur_nypin - 1 )
              if cur_item_row >= 0:
                for item_col in range( item_col_limit ):
                  cur_item_col = min( item_col, cur_nxpin - 1 )
                  if self.nodalMode:
                    cur_color = colors[ 0, node_ndx ]
                  else:
                    cur_color = colors[ cur_item_row, cur_item_col ]

                  if cur_color[ 3 ] > 0:
                    pen_color = cur_color.tolist()
                    gc.SetPen( gc.CreatePen( wx.ThePenList.FindOrCreatePen(
                        wx.Colour( *pen_color ), 1, wx.PENSTYLE_SOLID
                        ) ) )
                    brush_color = pen_color
                    gc.SetBrush( gc.CreateBrush(
                        wx.TheBrushList.FindOrCreateBrush(
                            wx.Colour( *brush_color ), wx.BRUSHSTYLE_SOLID
                            )
                        ) )
                    gc.DrawRectangle( item_x, item_y, pin_wd + 1, pin_wd + 1 )

                    if self.nodalMode:
                      gc.SetBrush( trans_brush )
                      gc.SetPen( node_pen )
                      gc.DrawRectangle( item_x, item_y, pin_wd + 1, pin_wd + 1 )
                      value = dset_array[ 0, node_ndx, pin_axial_level, assy_ndx ]
                      node_value_draw_list.append((
                          self._CreateValueString( value ),
                          Widget.GetContrastColor( *brush_color ),
                          item_x, item_y, pin_wd, pin_wd
                          ))
                    #end if nodalMode
                  #end if good value, not hidden by pin_factor

                  item_x += pin_wd
                  if self.nodalMode:
                    node_ndx += 1
                #end for item_col
              #end if cur_item_row >= 0

              item_y += pin_wd
            #end for item_row

            if draw_value_flag and brush_color is not None:
              value = dset_array[ 0, 0, pin_axial_level, assy_ndx ]
              assy_value_draw_list.append((
                  self._CreateValueString( value, 3 ),
                  Widget.GetContrastColor( *brush_color ),
                  assy_x, assy_y, assy_wd, assy_wd
                  ))
            #end if draw_value_flag

          else:  # if assy_ndx >= 0 and assy_ndx < dset_shape[ 3 ]:
            pass
#           im_draw.rectangle(
#               [ assy_x, assy_y, assy_x + assy_wd, assy_y + assy_wd ],
#               fill = None, outline = assy_pen
#               )

          assy_x += assy_wd
        #end for assy_col

        assy_y += assy_wd
      #end for assy_row

#                       -- Draw values
#                       --
      if node_value_draw_list:
        self._DrawValuesWx( node_value_draw_list, gc )

      if assy_value_draw_list:
        self._DrawValuesWx( assy_value_draw_list, gc )

#                       -- Draw vessel components and fluence
#                       --
      if fluence_ds_range is not None:
        self._DrawVesselComponents( gc, config )

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
      assy_y = max(
          vessel_region[ 1 ] + vessel_region[ 3 ],
          max( legend_size[ 1 ], fluence_legend_size[ 1 ] )
          )
      #assy_y += font_size >> 1
      assy_y += font_size >> 2

      title_str = self._CreateTitleString(
          title_templ,
          axial = self.axialValue.cm,
          time = self.timeValue
          #time = self.data.GetTimeValue( state_ndx, self.state.timeDataSet )
          )
      self._DrawStringsWx(
          gc, font,
          ( title_str, ( 0, 0, 0, 255 ),
            vessel_region[ 0 ], assy_y,
            im_wd - vessel_region[ 0 ] - (font_size << 2),
            'c' )
          )

#                       -- Draw vessel fluence values
#                       --
      if fluence_ds_range is not None and \
          self.fluenceAddr.dataSetName is not None:
        self._DrawFluenceCells( gc, config )

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
  #     METHOD:         VesselCore2DView._CreateStateTuple()            -
  #----------------------------------------------------------------------
  def _CreateStateTuple( self ):
    """
@return                 state_index, axial_level, fluence_index
"""
    #return  self.stateIndex, self.axialValue.pinIndex
    return  \
        self.stateIndex, self.axialValue.pinIndex, self.axialValue.fluenceIndex
  #end _CreateStateTuple


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._CreateToolTipText()           -
  #----------------------------------------------------------------------
  def _CreateToolTipText( self, cell_info ):
    """Create a tool tip.
@param  cell_info       tuple returned from FindCell()
"""
    tip_str = ''

    if cell_info is not None and cell_info[ 0 ] >= 0:
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      #if dset is not None and assy_ndx < dset.shape[ 3 ]:
      if dset is not None:
        core = self.dmgr.GetCore()
        assy_ndx = min( cell_info[ 0 ], dset.shape[ 3 ] - 1 )
        #axial_level = min( self.axialValue.fluenceIndex, dset.shape[ 2 ] - 1 ),
        axial_level = min( self.axialValue.pinIndex, dset.shape[ 2 ] - 1 ),
        assy_addr_display = core.CreateAssyLabel( *cell_info[ 1 : 3 ] )
        value = None

        if self.nodalMode:
          node_addr = cell_info[ 5 ]  if len( cell_info ) > 5 else  -1
          if self.dmgr.IsValid( self.curDataSet, node_addr = node_addr ):
            tip_str = 'Assy: %s, Node %d' % \
                ( assy_addr_display, node_addr + 1 )
            value = dset[ 0, node_addr, axial_level, assy_ndx ]
        else:
          tip_str = 'Assy: %s' % assy_addr_display
          if dset.shape[ 0 ] == 1 or dset.shape[ 1 ] == 1:
            value = dset[ 0, 0, axial_level, assy_ndx ]
        #end if self.nodalMode

        if not self.dmgr.IsBadValue( value ):
          tip_str += ': %g' % value
      #end if assy_ndx in range
    #end if cell_info

    return  tip_str
  #end _CreateToolTipText


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._DrawBaffle()                  -
  #----------------------------------------------------------------------
  def _DrawBaffle( self, gc, config ):
    """Handles drawing the baffle.  This needs a better algorithm.
It is assumed config[ 'baffleWidth' ] gt 0.
    Args:
        gc (wx.GraphicsContext): used for drawing
        config (dict): draw configuration
@param  gc              wx.GraphicsContext instance
@param  config          draw configuration dict
"""
    assy_wd = config[ 'assemblyWidth' ]
    baffle_wd = config[ 'baffleWidth' ]
    #baffle_wd = 3
    core_region = config[ 'coreRegion' ]
    vessel_region = config[ 'vesselRegion' ]
    pix_per_cm = config[ 'pixPerCm' ]

    vessel_origin = vessel_region[ 0 : 2 ]
    if config[ 'coreOffsetCm' ] > 0:
      vessel_origin[ 0 ] += assy_wd >> 1
      vessel_origin[ 1 ] += assy_wd >> 1

    core = self.dmgr.GetCore()

    pt_list = []

#               -- Start at bottom
#               --
    assy_col = self.cellRange[ 0 ]  # self.cellRange[ 2 ] - 1
    assy_row = self.cellRange[ 3 ] - 1
    assy_x = core_region[ 0 ]
    assy_y = core_region[ 1 ] + core_region[ 3 ] + 1
    finished = False
    while not finished:
      assy_ndx = core.coreMap[ assy_row, assy_col ] - 1
      if assy_ndx >= 0:
        if assy_col == self.cellRange[ 0 ]:
          pts = [
              ##vessel_origin[ 0 ] - 1, assy_y,
              vessel_origin[ 0 ] - 2, assy_y,
              core_region[ 0 ] + assy_wd, assy_y
              ]
        else:
          pts = [ assy_x, assy_y, assy_x + assy_wd, assy_y ]
        #im_draw.line( pts, fill = ( 155, 155, 155, 255 ), width = baffle_wd )
        pt_list.extend( pts )
        assy_col += 1
        assy_x += assy_wd
        if assy_col >= self.cellRange[ 2 ]:
          finished = True

      elif assy_row <= self.cellRange[ 1 ]:
        finished = True

      else:
        pts = [ assy_x, assy_y, assy_x, assy_y - assy_wd - 1 ]
#       im_draw.line(
#           #[ assy_x, assy_y, assy_x, assy_y - assy_wd ],
#           [ assy_x, assy_y + (baffle_wd >> 1), assy_x, assy_y - assy_wd - 1 ],
#           fill = ( 155, 155, 155, 255 ), width = baffle_wd
#           )
        pt_list.extend( pts )
        assy_row -= 1
        if assy_row <= self.cellRange[ 1 ]:
          finished = True
        else:
          assy_y -= assy_wd
    #end while

#               -- Finish on right
#               --
    while assy_row >= self.cellRange[ 1 ]:
      if assy_row == self.cellRange[ 1 ]:
        #pts = [ assy_x, assy_y, assy_x, vessel_origin[ 1 ] - 1 ]
        pts = [ assy_x, assy_y, assy_x, vessel_origin[ 1 ] - 2 ]
      else:
        pts = [ assy_x, assy_y, assy_x, assy_y - assy_wd ]
        #pts = [ assy_x, assy_y, assy_x, assy_y - assy_wd - 1 ]
      #im_draw.line( pts, fill = ( 155, 155, 155, 255 ), width = baffle_wd )
      pt_list.extend( pts )
      assy_row -= 1
      assy_y -= assy_wd
    #end while

#    if len( pt_list ) > 0:
#      im_draw.line( pt_list, fill = ( 155, 155, 155, 255 ), width = baffle_wd )
    if len( pt_list ) >= 4:
      path = gc.CreatePath()
      path.MoveToPoint( pt_list[ 0 ], pt_list[ 1 ] )
      for i in xrange( 2, len( pt_list ) - 1, 2 ):
        path.AddLineToPoint( pt_list[ i ], pt_list[ i + 1 ] )

      cur_pen = wx.ThePenList.FindOrCreatePen(
          wx.Colour( 155, 155, 155, 255 ), baffle_wd, wx.PENSTYLE_SOLID
          )
      cur_pen.SetCap( wx.CAP_BUTT )
      gc.SetPen( gc.CreatePen( cur_pen ) )
      gc.StrokePath( path )
    #end if len( pt_list ) >= 4
  #end _DrawBaffle


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._DrawFluenceCells()            -
  #----------------------------------------------------------------------
  def _DrawFluenceCells( self, gc, config ):
    """Handles drawing fluence data.
    Args:
        gc (wx.GraphicsContext): used for rendering
        config (dict): draw configuration
"""

    dset = None
    core = self.dmgr.GetCore()
    ds_range = config.get( 'fluenceDataRange' )
    z_ndx = self.axialValue.fluenceIndex
    if z_ndx >= 0 and ds_range is not None:
      dset = self.dmgr.GetH5DataSet( self.fluenceAddr.dataSetName, self.timeValue )
      z_ndx = min( z_ndx, core.fluenceMesh.nz - 1 )

    if dset is not None and core is not None:
      amode = gc.GetAntialiasMode()
      cmode = gc.GetCompositionMode()
      gc.SetAntialiasMode( wx.ANTIALIAS_NONE )  # _DEFAULT
      gc.SetCompositionMode( wx.COMPOSITION_SOURCE )  # _OVER

      #break_angle = PI_OVER_2  if core.coreSym == 4 else  TWO_PI
      dset_array = np.array( dset )
      trans_color_arr = np.array([ 0, 0, 0, 0 ], dtype = np.uint8 )

      pix_per_cm = config[ 'pixPerCm' ]
      r_start_ndx = config[ 'radiusStartIndex' ]
      fluence_mapper = config[ 'fluenceMapper' ]
      th_stop_ndx = config[ 'thetaStopIndex' ]
      vessel_region = config[ 'vesselRegion' ]

      vessel_origin = vessel_region[ 0 : 2 ]
      if config[ 'coreOffsetCm' ] > 0:
        assy_wd = config[ 'assemblyWidth' ]
        vessel_origin[ 0 ] += assy_wd >> 1
        vessel_origin[ 1 ] += assy_wd >> 1

#               -- Map to colors
#               --
      cur_array = dset_array[ z_ndx, :, : ]
      #cur_array[ cur_array <= 0.0 ] = np.nan
      colors = fluence_mapper.to_rgba( cur_array, bytes = True )
      colors[ np.isnan( cur_array ) ] = trans_color_arr
      colors[ np.isinf( cur_array ) ] = trans_color_arr
      colors[ cur_array < fluence_mapper.norm.vmin ] = trans_color_arr
      colors[ cur_array > fluence_mapper.norm.vmax ] = trans_color_arr

#               -- Outer loop is r
#               --
      for ri in xrange( core.fluenceMesh.nr - 1, r_start_ndx - 1, -1 ):
        if ri == core.fluenceMesh.nr - 1:
          r2_wd = int( math.ceil( core.fluenceMesh.r[ ri + 1 ] * pix_per_cm ) )
        r1_wd = int( math.ceil( core.fluenceMesh.r[ ri ] * pix_per_cm ) )

        cur_r = (r1_wd + r2_wd) >> 1
        #cur_wd = max( 1, r2_wd - r1_wd + 1 )
        cur_wd = max( 1, r2_wd - r1_wd )

#                       -- Inner loop is theta
#                       --
        use_stop_ndx = min( th_stop_ndx, core.fluenceMesh.ntheta - 1 )
        last_theta = min( core.fluenceMesh.theta[ use_stop_ndx ], TWO_PI )
        for ti in xrange( 0, th_stop_ndx ):
          start = core.fluenceMesh.theta[ ti ]
          end = min(
              core.fluenceMesh.theta[ ti + 1 ],
              last_theta
              )
          cur_color = colors[ ti, ri ]
          if cur_color[ 3 ] > 0:
            #pen_color = fluence_mapper.to_rgba( value, bytes = True )
            pen_color = cur_color.tolist()
            cur_pen = wx.ThePenList.FindOrCreatePen(
                wx.Colour( *pen_color ), cur_wd + 1, wx.PENSTYLE_SOLID
                )
            cur_pen.SetCap( wx.CAP_BUTT )
            gc.SetPen( gc.CreatePen( cur_pen ) )
            path = gc.CreatePath()
            path.AddArc(
                vessel_origin[ 0 ], vessel_origin[ 1 ], cur_r,
                start, end
                )
            gc.StrokePath( path )
          #if valid value
        #end for ti

#        r1_wd = r2_wd
        r2_wd = r1_wd
      #end for ri

      gc.SetAntialiasMode( amode )
      gc.SetCompositionMode( cmode )
    #end if dset
  #end _DrawFluenceCells


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._DrawVesselComponents()        -
  #----------------------------------------------------------------------
  def _DrawVesselComponents( self, gc, config ):
    """Handles drawing vessel components from the vessel definition
@param  gc              wx.GraphicsContext instance
@param  config          draw configuration dict
"""
    core = self.dmgr.GetCore()

#       -- Params
#       --
    assy_wd = config[ 'assemblyWidth' ]
    core_region = config[ 'coreRegion' ]
    vessel_region = config[ 'vesselRegion' ]

    baffle_wd = config[ 'baffleWidth' ]
    barrel_r = config[ 'barrelRadius' ]
    barrel_wd = config[ 'barrelWidth' ]
    barrel_r += (barrel_wd >> 1)
    liner_r = config[ 'linerRadius' ]
    vessel_r = config[ 'vesselRadius' ]
    vessel_wd = vessel_r - (liner_r + 1)
    vessel_r = liner_r + 1 + (vessel_wd >> 1)

    if core.coreSym == 1:
      vessel_origin = (
          (vessel_region[ 0 ] + vessel_region[ 2 ]) >> 1,
          (vessel_region[ 1 ] + vessel_region[ 3 ]) >> 1
          )
    else:
      vessel_origin = vessel_region[ 0 : 2 ]
      if config[ 'coreOffsetCm' ] > 0:
        vessel_origin[ 0 ] += assy_wd >> 1
        vessel_origin[ 1 ] += assy_wd >> 1

    #end_angle = 90  if core.coreSym == 4 else  360
    end_angle = 360  if core.coreSym == 1  else 90
    end_angle_rads = end_angle * RADS_PER_DEG

#       -- Baffle
#       --
    if core.coreSym == 4:
      self._DrawBaffle( gc, config )

#       -- Barrel
#       --
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 200, 200, 200, 255 ), barrel_wd, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    path = gc.CreatePath()
    path.AddArc(
        vessel_origin[ 0 ], vessel_origin[ 1 ], barrel_r,
        0, PI_OVER_2
        )
    gc.StrokePath( path )

#       -- Pad
#       --
    pad_wd = config[ 'padWidth' ]
    pad_r = config[ 'padRadius' ] + (pad_wd >> 1)
    #if self.vesselShowPad:
    if pad_wd > 0:
      pad_angles = config[ 'padAngles' ]
      if len( pad_angles ) > 0:
#        pad_wd = config[ 'padWidth' ]
        pad_arc_half = config[ 'padArc' ] / 2.0
        cur_pen = wx.ThePenList.FindOrCreatePen(
            wx.Colour( 175, 175, 175, 255 ), pad_wd, wx.PENSTYLE_SOLID
            )
        cur_pen.SetCap( wx.CAP_BUTT )
        gc.SetPen( gc.CreatePen( cur_pen ) )

        for an in pad_angles:
          if an < end_angle:
            pad_st = an - pad_arc_half
            pad_en = an + pad_arc_half
            path = gc.CreatePath()
            path.AddArc(
                vessel_origin[ 0 ], vessel_origin[ 1 ], pad_r,
                pad_st * RADS_PER_DEG, pad_en * RADS_PER_DEG
                )
            gc.StrokePath( path )
          #end if an < end_angle
        #end for an
      #end if pad_angles
    #end if pad_wd > 0

#       -- Vessel ring
#       --
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 175, 175, 175, 255 ), vessel_wd, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    path = gc.CreatePath()
    path.AddArc(
        vessel_origin[ 0 ], vessel_origin[ 1 ], vessel_r,
        0, end_angle_rads
        )
    gc.StrokePath( path )

#       -- Liner
#       --
    cur_pen = wx.ThePenList.FindOrCreatePen(
        wx.Colour( 0, 0, 0, 255 ), 1, wx.PENSTYLE_SOLID
        )
    cur_pen.SetCap( wx.CAP_BUTT )
    gc.SetPen( gc.CreatePen( cur_pen ) )
    path = gc.CreatePath()
    path.AddArc(
        vessel_origin[ 0 ], vessel_origin[ 1 ], liner_r,
        0, end_angle_rads
        )
    gc.StrokePath( path )
  #end _DrawVesselComponents


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.FindAssembly()                 -
  #----------------------------------------------------------------------
  def FindAssembly( self, ev_x, ev_y ):
    """Finds the assembly index.
@param  ev_x            event x coordinate (relative to this)
@param  ev_y            event y coordinate (relative to this)
@return                 None if no match, otherwise tuple of
                        ( 0-based index, cell_col, cell_row,
                          pin_col, pin_row, node_addr )
"""
    result = None

    core = None
    if self.config is not None and self.dmgr is not None:
      core = self.dmgr.GetCore()

    if core is not None and core.coreMap is not None:
      if ev_x >= 0 and ev_y >= 0:
        assy_wd = self.config[ 'assemblyWidth' ]
        core_region = self.config[ 'coreRegion' ]
        off_x = ev_x - core_region[ 0 ]
        off_y = ev_y - core_region[ 1 ]
        cell_x = min(
            int( off_x / assy_wd ) + self.cellRange[ 0 ],
            self.cellRange[ 2 ] - 1
            )
        cell_x = max( self.cellRange[ 0 ], cell_x )
        cell_y = min(
            int( off_y / assy_wd ) + self.cellRange[ 1 ],
            self.cellRange[ 3 ] - 1
            )
        cell_y = max( self.cellRange[ 1 ], cell_y )

        assy_ndx = core.coreMap[ cell_y, cell_x ] - 1

        pin_wd = self.config[ 'pinWidth' ]
        if self.nodalMode:
          node_col = int( (off_x % assy_wd) / pin_wd )
          node_row = int( (off_y % assy_wd) / pin_wd )
          node_addr = 2 if node_row > 0 else 0
          if node_col > 0:
            node_addr += 1
          pin_col, pin_row = self.dmgr.GetSubAddrFromNode(
              node_addr,
              'channel' if self.channelMode else 'pin'
              )
        else:
          pin_col = int( (off_x % assy_wd) / pin_wd )
          if pin_col >= core.npinx: pin_col = -1
          pin_row = int( (off_y % assy_wd) / pin_wd )
          if pin_row >= core.npiny: pin_row = -1
          node_addr = self.dmgr.GetNodeAddr(
              ( pin_col, pin_row ),
              'channel' if self.channelMode else 'pin'
              )

        result = ( assy_ndx, cell_x, cell_y, pin_col, pin_row, node_addr )
      #end if event within display
    #end if we have data

    return  result
  #end FindAssembly


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.FindCell()                     -
  #----------------------------------------------------------------------
  def FindCell( self, ev_x, ev_y ):
    """Calls FindAssembly().
"""
    return  self.FindAssembly( ev_x, ev_y )
  #end FindCell


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.GetAnimationIndexes()          -
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return                 list of indexes or None
"""
    return  ( 'axial:fluence', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.GetDataSetTypes()              -
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin' ]
#    return  [
#       'channel', 'pin',
#       ':assembly', ':chan_radial', ':node',
#       ':radial', ':radial_assembly', ':radial_node'
#       ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.GetEventLockSet()              -
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
  #     METHOD:         VesselCore2DView.GetPrintFontScale()            -
  #----------------------------------------------------------------------
  def GetPrintFontScale( self ):
    """
@return         1.5
"""
    return  1.5
  #end GetPrintFontScale


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.GetSpecialDataSetTypes()       -
  #----------------------------------------------------------------------
  def GetSpecialDataSetTypes( self ):
    """Accessor specifying the types of special datasets which can be
processed in this widget.

@return                 [ 'fluence' ]
"""
    return  [ 'fluence' ]
  #end GetSpecialDataSetTypes


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.GetTitle()                     -
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Vessel Core 2D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._HiliteBitmap()                -
  #----------------------------------------------------------------------
  def _HiliteBitmap( self, bmap, config = None ):
    result = bmap

    if config is None:
      config = self.config

    core = self.dmgr.GetCore()
    if config is not None and core is not None and 'vesselRadius' in config:
      line_wd = config[ 'lineWidth' ]
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
            HILITE_COLOR_primary,
            #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
            line_wd, wx.PENSTYLE_SOLID
            )
        secondary_pen = wx.ThePenList.FindOrCreatePen(
            HILITE_COLOR_secondary,
            #max( half_line_wd, 1 ), wx.PENSTYLE_SOLID
            line_wd, wx.PENSTYLE_SOLID
            )
      else:
        select_pen = wx.ThePenList.FindOrCreatePen(
            HILITE_COLOR_primary,
            line_wd, wx.PENSTYLE_SOLID
            )
      #end if-else self.nodalMode

#                       -- Core mode
#                       --
      rel_col = self.assemblyAddr[ 1 ] - self.cellRange[ 0 ]
      rel_row = self.assemblyAddr[ 2 ] - self.cellRange[ 1 ]

      if rel_col >= 0 and rel_col < self.cellRange[ -2 ] and \
          rel_row >= 0 and rel_row < self.cellRange[ -1 ]:
        assy_wd = config[ 'assemblyWidth' ]
        core_region = config[ 'coreRegion' ]

        rect = [
            rel_col * assy_wd + core_region[ 0 ],
            rel_row * assy_wd + core_region[ 1 ],
            assy_wd, assy_wd
            ]
        draw_list.append( ( rect, select_pen ) )

#                               -- Core nodal
        if self.nodalMode:
          node_wd = config[ 'pinWidth' ]
          for i in range( len( node_addr_list ) ):
            node_addr = node_addr_list[ i ]
            if node_addr >= 0:
              rel_x = node_wd if node_addr in ( 1, 3 ) else half_line_wd
              rel_y = node_wd if node_addr in ( 2, 3 ) else half_line_wd
              node_rect = [
                  rect[ 0 ] + rel_x, rect[ 1 ] + rel_y,
                  node_wd - half_line_wd, node_wd - half_line_wd
                  ]
              pen = \
                  secondary_pen if i < len( node_addr_list ) - 1 else \
                  primary_pen
              draw_list.append( ( node_rect, pen ) )
            #end if valid node addr
          #end for i
        #end if nodalMode
      #end if cell in drawing range

#                       -- Draw?
#                       --
      new_bmap = self._CopyBitmap( bmap )
      dc = wx.MemoryDC( new_bmap )
      gc = wx.GraphicsContext.Create( dc )
      if draw_list:
        #new_bmap = self._CopyBitmap( bmap )
        #dc = wx.MemoryDC( new_bmap )
        #gc = wx.GraphicsContext.Create( dc )

        for draw_item in draw_list:
          gc.SetPen( draw_item[ 1 ] )
          path = gc.CreatePath()
          path.AddRectangle( *draw_item[ 0 ] )
          gc.StrokePath( path )
        #end for draw_item

        #dc.SelectObject( wx.NullBitmap )
        #result = new_bmap
      #end if draw_list

#                       -- Theta indicator
#                       --
      vessel_region = config[ 'vesselRegion' ]
      liner_r = config[ 'linerRadius' ]
      pad_wd = config[ 'padWidth' ]
      pad_r = config[ 'padRadius' ]
      rad_px2 = liner_r - 2
      rad_px1 = min( pad_r + pad_wd + 2, rad_px2 - 4 )

      if core.coreSym == 1:
        vessel_origin = (
            (vessel_region[ 0 ] + vessel_region[ 2 ]) >> 1,
            (vessel_region[ 1 ] + vessel_region[ 3 ]) >> 1
            )
      else:
        vessel_origin = vessel_region[ 0 : 2 ]
        if config[ 'coreOffsetCm' ] > 0:
          assy_wd = config[ 'assemblyWidth' ]
          vessel_origin[ 0 ] += assy_wd >> 1
          vessel_origin[ 1 ] += assy_wd >> 1

      theta_rad = core.fluenceMesh.GetThetaRads( self.fluenceAddr.thetaIndex )
      th_cos = math.cos( theta_rad )
      th_sin = math.sin( theta_rad )
      if core.coreSym == 1:
        dx1 = th_sin * rad_px1
        dy1 = th_cos * rad_px1
        dx2 = th_sin * rad_px2
        dy2 = th_cos * rad_px2
      else:
        dx1 = th_cos * rad_px1
        dy1 = th_sin * rad_px1
        dx2 = th_cos * rad_px2
        dy2 = th_sin * rad_px2

      gc.SetPen( select_pen )
      path = gc.CreatePath()
      path.MoveToPoint( vessel_origin[ 0 ] + dx1, vessel_origin[ 1 ] + dy1 )
      path.AddLineToPoint( vessel_origin[ 0 ] + dx2, vessel_origin[ 1 ] + dy2 )
      gc.StrokePath( path )

      dc.SelectObject( wx.NullBitmap )
      result = new_bmap
    #end if config is not None:

    return  result
  #end _HiliteBitmap


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._InitEventHandlers()           -
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
  #     METHOD:         VesselCore2DView._IsAssemblyAware()             -
  #----------------------------------------------------------------------
  def _IsAssemblyAware( self ):
    """
@return                 False
"""
    return  False
  #end _IsAssemblyAware


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.IsTupleCurrent()               -
  #----------------------------------------------------------------------
  def IsTupleCurrent( self, tpl ):
    """
@param  tpl             tuple of state values
@return                 True if it matches the current state, false otherwise
"""
    result = \
        tpl is not None and len( tpl ) >= 2 and \
        tpl[ 0 ] == self.stateIndex and \
        tpl[ 1 ] == self.axialValue.pinIndex and \
        tpl[ 2 ] == self.axialValue.fluenceIndex

    return  result
  #end IsTupleCurrent


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._LoadDataModelValues()         -
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
  #     METHOD:         VesselCore2DView.LoadProps()                    -
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.  This implementation is a noop and should
be overridden by subclasses.
@param  props_dict      dict object from which to deserialize properties
"""
    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( VesselCore2DView, self ).LoadProps( props_dict )
  #end LoadProps


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnClick()                     -
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    """
"""
    if self.config:
      x = ev.GetX()
      y = ev.GetY()
      is_aux = self.IsAuxiliaryEvent( ev )
      click_count = ev.GetClickCount()
      self.GetTopLevelParent().GetApp().\
          DoBusyEventOp( self._OnClickImpl, x, y, is_aux, click_count )
  #end _OnClick


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnClickCore()                 -
  #----------------------------------------------------------------------
  def _OnClickCore( self, x, y, is_aux, click_count ):
    """
"""
    #core_region = self.config[ 'coreRegion' ]

    cell_info = self.FindAssembly( x, y )
    if cell_info is not None and cell_info[ 0 ] >= 0:
      state_args = {}
      assy_addr = cell_info[ 0 : 3 ]
      if assy_addr != self.assemblyAddr:
        state_args[ 'assembly_addr' ] = assy_addr

      if self.nodalMode:
        node_addr = cell_info[ 5 ]
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
        elif click_count > 1:
          sub_addr = self.dmgr.GetSubAddrFromNode(
              node_addr,
              'channel' if self.channelMode else 'pin'
              )
          if sub_addr != self.subAddr:
            state_args[ 'sub_addr' ] = sub_addr
        #end if-elif is_aux

      elif click_count > 1:
        pin_addr = cell_info[ 3 : 5 ]
        if pin_addr != self.subAddr:
          state_args[ 'sub_addr' ] = pin_addr

      if len( state_args ) > 0:
        self.FireStateChange( **state_args )
    #end if cell found
  #end _OnClickCore


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnClickImpl()                 -
  #----------------------------------------------------------------------
  def _OnClickImpl( self, x, y, is_aux, click_count ):
    """
"""
    if self.config:
      core_region = self.config[ 'coreRegion' ]

      if x >= core_region[ 0 ] and x >= core_region[ 1 ] and \
          x <= core_region[ 0 ] + core_region[ 2 ] and \
          y <= core_region[ 1 ] + core_region[ 3 ]:
        self._OnClickCore( x, y, is_aux, click_count )

      elif x > 0 and y > 0:
        core = self.dmgr.GetCore()
        barrel_radius = self.config[ 'barrelRadius' ]
        vessel_region = self.config[ 'vesselRegion' ]
        vessel_radius = self.config[ 'vesselRadius' ]

        if core.coreSym == 1:
          vessel_origin = (
              (vessel_region[ 0 ] + vessel_region[ 2 ]) >> 1,
              (vessel_region[ 1 ] + vessel_region[ 3 ]) >> 1
              )
        else:
          assy_wd = self.config[ 'assemblyWidth' ]
          vessel_origin = vessel_region[ 0 : 2 ]
          if self.config[ 'coreOffsetCm' ] > 0:
            vessel_origin[ 0 ] += assy_wd >> 1
            vessel_origin[ 1 ] += assy_wd >> 1

        dx = x - vessel_origin[ 0 ]
        dy = y - vessel_origin[ 1 ]

        r = math.sqrt( (dx * dx) + (dy * dy) )
        #if r >= barrel_radius and r <= vessel_radius + 10:
        if r >= barrel_radius:
          if core.coreSym == 1:
            th_rad = math.atan2( dx, dy )
            if th_rad < 0.0:
              th_rad += math.pi * 2.0
          else:
            # 1 degree under pi/2
            th_rad = min( PI_OVER_2 - 0.017, max( 0.0, math.atan2( dy, dx ) ) )
          ti = core.fluenceMesh.GetThetaIndex( th_rad )

          radius = r / self.config[ 'pixPerCm' ]
          ri = core.fluenceMesh.GetRadiusIndex( radius )

          fluence_addr = self.fluenceAddr.copy()
          fluence_addr.update( radiusIndex = ri, thetaIndex = ti )
          self.FireStateChange( fluence_addr = fluence_addr )
        #end if r >= barrel_radius and r <= vessel_radius + 10
      #end elif x > 0 and y > 0
    #end if self.config
  #end _OnClickImpl


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnClickImpl_1()               -
  #----------------------------------------------------------------------
  def _OnClickImpl_1( self, x, y, is_aux, click_count ):
    """
"""
    if self.config:
      core_region = self.config[ 'coreRegion' ]

      if x <= core_region[ 0 ] + core_region[ 2 ] and \
          y <= core_region[ 1 ] + core_region[ 3 ]:
        self._OnClickCore( x, y, is_aux, click_count )

      elif x > core_region[ 0 ] and y > core_region[ 1 ]:
        core = self.dmgr.GetCore()
        barrel_radius = self.config[ 'barrelRadius' ]
        vessel_region = self.config[ 'vesselRegion' ]
        vessel_radius = self.config[ 'vesselRadius' ]

        if core.coreSym == 1:
          vessel_origin = (
              (vessel_region[ 0 ] + vessel_region[ 2 ]) >> 1,
              (vessel_region[ 1 ] + vessel_region[ 3 ]) >> 1
              )
        else:
          assy_wd = self.config[ 'assemblyWidth' ]
          vessel_origin = vessel_region[ 0 : 2 ]
          if self.config[ 'coreOffsetCm' ] > 0:
            vessel_origin[ 0 ] += assy_wd >> 1
            vessel_origin[ 1 ] += assy_wd >> 1

        dx = x - vessel_origin[ 0 ]
        dy = y - vessel_origin[ 1 ]

        r = math.sqrt( (dx * dx) + (dy * dy) )
        if r >= barrel_radius and r <= vessel_radius + 10:
          if core.coreSym == 1:
            th_rad = math.atan2( dx, dy )
            if th_rad < 0.0:
              th_rad += math.pi * 2.0
          else:
            # 1 degree under pi/2
            th_rad = min( PI_OVER_2 - 0.017, max( 0.0, math.atan2( dy, dx ) ) )

          ti = core.fluenceMesh.GetThetaIndex( th_rad )
          fluence_addr = self.fluenceAddr.copy()
          fluence_addr.update( thetaIndex = ti )
          self.FireStateChange( fluence_addr = fluence_addr )
      #end elif
    #end if self.config
  #end _OnClickImpl_1


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnDragFinished()              -
  #----------------------------------------------------------------------
  def _OnDragFinished( self, left, top, right, bottom ):
    """Do post drag things after drag processing.
"""
    pass
#    if right - left == 1 and bottom - top == 1:
#      self.assemblyAddr = self.dragStartCell
#      self._SetMode( 'assy' )
#      self.FireStateChange( assembly_addr = self.assemblyAddr )
#    else:
#      self._SetMode( 'core' )
  #end _OnDragFinished


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnFindMinMax()                -
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, mode, all_states_flag, all_assy_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    self.GetTopLevelParent().GetApp().DoBusyEventOp(
        self._OnFindMinMaxImpl, mode, all_states_flag, all_assy_flag
        )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._OnFindMinMaxImpl()            -
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
  #     METHOD:         VesselCore2DView.SaveProps()                    -
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to save properties.  Subclasses should override calling this
method via super.SaveProps().
@param  props_dict      dict object to which to serialize properties
"""
    super( VesselCore2DView, self ).SaveProps( props_dict, for_drag = for_drag )

    #for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr', 'mode' ):
    for k in ( 'assemblyAddr', 'auxNodeAddrs', 'nodeAddr', 'subAddr' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView.SetDataSet()                   -
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
  #     METHOD:         VesselCore2DView._UpdateDataSetStateValues()    -
  #----------------------------------------------------------------------
  def _UpdateDataSetStateValues( self, ds_type, clear_zoom_stack = False ):
    """Updates channelMode and nodalMode properties.
    Args:
        ds_type (str): dataset category/type
        clear_zoom_stack (boolean): True to clear in zoom stack
"""
    #no self.channelMode = ds_type == 'channel'
    self.channelMode = self.dmgr.IsChannelType( self.curDataSet )
    self.nodalMode = self.dmgr.IsNodalType( ds_type )
  #end _UpdateDataSetStateValues


  #----------------------------------------------------------------------
  #     METHOD:         VesselCore2DView._UpdateStateValues()           -
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
@return                 kwargs with 'changed' and/or 'resized'
"""
    kwargs = super( VesselCore2DView, self )._UpdateStateValues( **kwargs )
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
#       self.nodalMode = self.dmgr.IsNodalType( ds_type )
#        self.curDataSet = kwargs[ 'cur_dataset' ]
#       self._UpdateAxialValue()
#       self.container.GetDataSetMenu().Reset()

    if 'fluence_addr' in kwargs and \
        kwargs[ 'fluence_addr' ] != self.fluenceAddr:
      #resized = True
#               -- If only thetaIndex changed, we don't need a new image,
#               --   just a new indicator
      if self.fluenceAddr.Equals( kwargs[ 'fluence_addr' ], 'thetaIndex' ):
        changed = True
      else:
        resized = True
      self.fluenceAddr.update( self.state.fluenceAddr )
    #end if 'fluence_addr'

    if 'node_addr' in kwargs:
      node_addr = self.dmgr.NormalizeNodeAddr( kwargs[ 'node_addr' ] )
      if node_addr != self.nodeAddr:
        changed = True
        self.nodeAddr = node_addr

    if 'sub_addr' in kwargs:
      sub_addr = self.dmgr.NormalizeSubAddr(
          kwargs[ 'sub_addr' ],
          'channel' if self.channelMode else 'pin'
          )
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

#end VesselCore2DView
