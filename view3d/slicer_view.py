# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view.py					-
#	HISTORY:							-
#		2017-01-09	leerw@ornl.gov				-
#	  Migrating to DataModelMgr.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-08-31	leerw@ornl.gov				-
#	  Handle 'scale_mode' events.
#		2016-08-17	leerw@ornl.gov				-
#	  New State events.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-03-08	leerw@ornl.gov				-
#	  Getting correct figure for mlab.savefig() call.
#		2016-03-07	leerw@ornl.gov				-
#	  Now just Slicer3DView with single figure.
#------------------------------------------------------------------------
import bisect, functools, logging, math, os, sys
import numpy as np
import pdb

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required' )

from traits.api import HasTraits, Instance, Array, on_trait_change
from traitsui.api import View, Item, HGroup, Group

from tvtk.api import tvtk
from tvtk.pyface.scene import Scene

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel

#from data.datamodel import *
from event.state import *
from widget.widget import *
from widget.widgetcontainer import *


#------------------------------------------------------------------------
#	CLASS:		Slicer3DView					-
#------------------------------------------------------------------------
class Slicer3DView( Widget ):
  """Slicer 3D visualization widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.axialValue = ( 0.0, -1, -1 )
    self.coreExtent = None  # left, top, right + 1, bottom + 1, dx, dy
    self.curDataSet = None

    #self.autoSync = True
    self.isLoaded = False
    self.logger = logging.getLogger( 'view3d' )
    #self.menuDef = [ ( 'Disable Auto Sync', self._OnAutoSync ) ]
    self.meshLevels = None
    self.stateIndex = -1
    self.subAddr = None
    self.timeValue = -1.0

#    self.toolButtonDefs = \
#      [
#        ( 'sync_in_16x16', 'Sync From Other Widgets', self._OnSyncFrom ),
#        ( 'sync_out_16x16', 'Sync To Other Widgets', self._OnSyncTo )
#      ]

    self.viz = None
    self.vizcontrol = None

    super( Slicer3DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.CalcDataState()			-
  #----------------------------------------------------------------------
  def CalcDataState( self, slice_position ):
    """Calculates axial_value (axial_cm, core_ndx, detector_ndx ),
assembly_addr ( assy_ndx, assy_col, assy_row ), and sub_addr.
@param  slice_position	[ z, x, y ]
@return			dict with 'assembly_addr', 'axial_value', and
			'sub_addr' keys, or None if no data
"""
    rec = None

    core = self.dmgr.GetCore()
    #if self.data is not None and self.meshLevels is not None:
    if core is not None and self.curDataSet and self.meshLevels is not None:
      slice_z, slice_x, slice_y = slice_position

      if slice_z >= 0:
	ax_level = DataUtils.FindListIndex( self.meshLevels, slice_z )
	axial_value = self.dmgr.\
	    GetAxialValue( self.curDataSet, core_ndx = ax_level )
#        ax_level = min(
#	    bisect.bisect_left( self.meshLevels, slice_z ),
#	    len( self.meshLevels ) - 1
#            )
#        axial_value = self.data.CreateAxialValue( core_ndx = ax_level )
      else:
        axial_value = ( -1, -1, -1 )

      if slice_x >= 0 and slice_y >= 0:
        assy_col = int( slice_x / core.npinx ) + self.coreExtent[ 0 ]
        assy_row = self.coreExtent[ 3 ] - 1 - int( slice_y / core.npiny )
	assembly_addr = self.dmgr.CreateAssemblyAddr( assy_col, assy_row )

	pin_col = int( slice_x ) % core.npinx
	pin_row = core.npiny - (int( slice_y ) % core.npiny)
	sub_addr = ( pin_col, pin_row )
      else:
        assembly_addr = ( -1, -1, -1 )
        sub_addr = ( -1, -1 )
      #end if-else

      rec = \
        {
        'assembly_addr': assembly_addr,
        'axial_value': axial_value,
        'sub_addr': sub_addr
        }
    #end if data defined

    return  rec
  #end CalcDataState


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.CalcSlicePosition()		-
  #----------------------------------------------------------------------
  def CalcSlicePosition( self ):
    """Calculates viz slice positions from the current state.
@return			( z, x, y )
"""
    result = ( 0, 0, 0 )
    core = self.dmgr.GetCore()
    if core and self.meshLevels:
#		-- Data matrix is z, x, y(reversed)
#		--
      z = self.meshLevels[ self.axialValue[ 1 ] ]

      assy_col = self.assemblyAddr[ 1 ] - self.coreExtent[ 0 ]
      #xxxxx channel? track with mode flag?
      x = core.npinx * assy_col + self.subAddr[ 0 ]

      assy_row = self.assemblyAddr[ 2 ] - self.coreExtent[ 1 ]
      #xxxxx channel?
      y = \
          core.npiny * (self.coreExtent[ -1 ] - assy_row) - \
	  self.subAddr[ 1 ]

      result = ( z, x, y )
    #end if core

    return  result
  #end CalcSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._Create3DMatrix()			-
  #----------------------------------------------------------------------
  def _Create3DMatrix( self ):
    matrix = None

    core = self.dmgr.GetCore()
    if core is not None and self.curDataSet and \
        self.coreExtent is not None and \
        (core.npinx > 0 or core.npiny > 0):
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )
      dset_value = np.array( dset )
      dset_shape = dset.shape

      cur_npinx = max( core.npinx, dset_shape[ 1 ] )
      cur_npiny = max( core.npiny, dset_shape[ 0 ] )

      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug(
	    'curDataSet=%s, stateIndex=%d',
	    self.curDataSet, self.stateIndex
	    )

      ax_mesh = self.dmgr.GetAxialMesh( self.curDataSet )
      #pin_pitch = 1.26
      pin_pitch = core.GetAssemblyPitch() / max( core.npinx, core.npinx )
      self.meshLevels = [
	  int( (ax_mesh[ i + 1 ] - ax_mesh[ 0 ]) / pin_pitch )
	  for i in range( len( ax_mesh ) - 1 )
          ]
      z_size = self.meshLevels[ -1 ]

      # z, x, y(bottom up)
      #xxxxx +1 on pin ranges if a channel dataset
      matrix = np.ndarray(
	( z_size,
	  cur_npinx * self.coreExtent[ -2 ],
	  cur_npiny * self.coreExtent[ -1 ] ),
	np.float64
	)
      matrix.fill( 0.0 )
    
      pin_y = 0
      for assy_y in \
          xrange( self.coreExtent[ 3 ] - 1, self.coreExtent[ 1 ] - 1, -1 ):
        pin_x = 0
        for assy_x in xrange( self.coreExtent[ 0 ], self.coreExtent[ 2 ] ):
          assy_ndx = core.coreMap[ assy_y, assy_x ] - 1
          if assy_ndx >= 0:
	    assy_ndx = min( assy_ndx, dset_shape[ 3 ] - 1 )
	    for z in xrange( z_size ):
	      #xxx is this off by one?
	      ax_level = DataUtils.FindListIndex( self.meshLevels, z )
#	      ax_level = min(
#	          bisect.bisect_left( self.meshLevels, z ),
#		  len( self.meshLevels ) - 1
#		  )
	      ax_level = min( ax_level, dset_shape[ 2 ] - 1 )
	      pin_y2 = 0
	      for y in xrange( cur_npiny - 1, -1, -1 ):
		data_y = min( y, dset_shape[ 0 ] - 1 )

	        for x in xrange( cur_npinx ):
		  data_x = min( x, dset_shape[ 1 ] - 1 )
	          matrix[ z, pin_x + x, pin_y + pin_y2 ] = \
	              dset_value[ data_y, data_x, ax_level, assy_ndx ]
	        #end for x
	        pin_y2 += 1
	      #end for y
	    #end for z
          #end if assy_ndx >= 0

          pin_x += cur_npinx
        #end for assy_x

        pin_y += cur_npiny
      #end for assy_y
    #end if valid properties

    return  matrix
  #end _Create3DMatrix


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    return \
        self._CreateClipboardDisplayedData()  if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
#        self._CreateClipboardSelectionData() if cur_selection_flag else \
#        self._CreateClipboardAllData()
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateClipboardDisplayedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardDisplayedData( self ):
    """Retrieves the data for the state and axial.
@return			text or None
"""
    csv_text = None
    matrix = self.viz.GetScalarData()
    if matrix is not None and self.meshLevels is not None:
      csv_text = ''

      z_count = min( matrix.shape[ 0 ], len( self.meshLevels ) )
      for z in range( z_count - 1, -1, -1 ):
        title = '"Axial=%d"' % self.meshLevels[ z ]
        csv_text += DataModel.ToCSV( matrix[ z ], title )
    #end if

    return  csv_text
  #end _CreateClipboardDisplayedData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateClipboardImage()		-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return			bitmap or None
"""
    bmap = None

    fd, name = tempfile.mkstemp( '.png' )
    try:
      os.close( fd )
      if self.CreatePrintImage( name ):
        bmap = wx.Image( name, wx.BITMAP_TYPE_PNG ).ConvertToBitmap()
    finally:
      os.remove( name )

    return  bmap
  #end _CreateClipboardImage


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateClipboardSelectedData()	-
  #----------------------------------------------------------------------
  def _CreateClipboardSelectedData( self ):
    """Retrieves the data for the state, axial, and assembly.
@return			text or None
"""
    csv_text = None

    valid = False
    matrix = self.viz.GetScalarData()
    if matrix is not None and self.meshLevels is not None:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr = self.assemblyAddr[ 0 ],
	  axial_level = self.axialValue[ 1 ]
	  )

    if valid:
      #pos = self.CalcSlicePosition()
      pos = self.viz.GetSlicePosition()
      if self.logger.isEnabledFor( logging.DEBUG ):
        self.logger.debug( 'pos=%s', str( pos ) )
      csv_text = '"Axial=%d,Col=%d,Row=%d\n' % pos
      csv_text += '%.7g' % matrix[ pos[ 2 ], pos[ 0 ], pos[ 1 ] ]
    #end if

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateMenuDef()			-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self ):
    """
"""
    menu_def = super( Slicer3DView, self )._CreateMenuDef()

    find_max_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'max', True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'max', False )
	}
      ]

    find_min_def = \
      [
        {
	'label': 'All State Points',
	'handler': functools.partial( self._OnFindMinMax, 'min', True )
	},
        {
	'label': 'Current State Point',
	'handler': functools.partial( self._OnFindMinMax, 'min', False )
	}
      ]

    slicer_def = \
      [
	{ 'label': '-' },
	{ 'label': 'Find Maximum', 'submenu': find_max_def },
	{ 'label': 'Find Minimum', 'submenu': find_min_def }
      ]
    return  menu_def + slicer_def
  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.CreatePrintImage()			-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    result = None

    if self.viz is not None:
      scene = self.viz.scene3d
      scene.mlab.savefig( file_path, figure = scene.mayavi_scene )
      result = file_path

    return  result
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateViz()			-
  #----------------------------------------------------------------------
  def _CreateViz( self, matrix, drange ):
    """Builds this wxPython component.
"""
#		-- Create components
#		--
    self.viz = VolumeSlicer( matrix = matrix, dataRange = drange )
    #Do this to automatically fire state changes on slice position changes
    #self.viz.SetSlicePositionListener( self._OnSlicePosition )
    self.vizcontrol = \
        self.viz.edit_traits( parent = self, kind = 'subpanel' ).control

    self.GetSizer().Add( self.vizcontrol, 0, wx.ALL | wx.EXPAND )
  #end _CreateViz


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin', ':assembly', ':radial' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    locks = set([
        STATE_CHANGE_axialValue,
        STATE_CHANGE_coordinates,
        STATE_CHANGE_curDataSet,
	STATE_CHANGE_scaleMode,
        STATE_CHANGE_timeValue
        ])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Volume Slicer 3D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this wxPython component.
"""

#		-- Getting started cheat data
#		--
#    _data = np.ndarray( ( 26, 17, 17 ), dtype = np.float64 )
#    _data.fill( 1.0 )

#		-- Create components
#		--
#    self.viz = VolumeSlicer( matrix = _data, dataRange = [ 0.0, 5.0 ] )
#    self.vizcontrol = \
#        self.viz.edit_traits( parent = self, kind = 'subpanel' ).control

#		-- Lay out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
#    sizer.Add( self.vizcontrol, 0, wx.ALL | wx.EXPAND )

    self.SetAutoLayout( True )
    self.SetSizer( sizer )
    self.SetMinSize( ( 320, 320 ) )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    if self.dmgr.HasData() and not self.isLoaded:
      self.isLoaded = True

      self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

      self.assemblyAddr = self.state.assemblyAddr
      self.axialValue = self.dmgr.\
          GetAxialValue( self.curDataSet, cm = self.state.axialValue[ 0 ] )
      self.coreExtent = self.dmgr.ExtractSymmetryExtent()
      self.stateIndex = self.dmgr.\
          GetTimeValueIndex( self.state.timeValue, self.curDataSet )
      self.subAddr = self.state.subAddr
      self.timeValue = self.state.timeValue

      self._UpdateData()
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnAutoSync()			-
  #----------------------------------------------------------------------
#  def _OnAutoSync( self, ev ):
#    ev.Skip()
#
#    menu = ev.GetEventObject()
#    item = menu.FindItemById( ev.GetId() )
#    if item is not None:
#      if item.GetLabel().startswith( 'Enable' ):
#        item.SetText( item.GetLabel().replace( 'Enable', 'Disable' ) )
#	self.autoSync = True
#      else:
#        item.SetText( item.GetLabel().replace( 'Disable', 'Enable' ) )
#	self.autoSync = False
#    #end if
#  #end _OnAutoSync


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnFindMinMax()			-
  #----------------------------------------------------------------------
  def _OnFindMinMax( self, all_states_flag, ev ):
    """Calls _OnFindMinMaxPin().
"""
    if self.curDataSet:
      self._OnFindMinMaxPin( mode, self.curDataSet, all_states_flag )
  #end _OnFindMinMax


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnSlicePosition()			-
  #----------------------------------------------------------------------
#  def _OnSlicePosition( self, position ):
#    """Used if automagically firing state changes
#"""
#    rec = self.CalcDataState( position )
#    #print >> sys.stderr, '[Slicer3DView._OnSlicePosition]', str( rec )
#
#    if rec is not None:
#      if rec[ 'assembly_addr' ] != self.assemblyAddr:
#        self.assemblyAddr = rec[ 'assembly_addr' ]
#      else:
#        del rec[ 'assembly_addr' ]
#
#      if rec[ 'axial_value' ] != self.axialValue:
#        self.axialValue = self.data.NormalizeAxialValue( rec[ 'axial_value' ] )
#      else:
#        del rec[ 'axial_value' ]
#
#      if rec[ 'sub_addr' ] != self.subAddr:
#        self.subAddr = self.data.NormalizePinSubAddr( rec[ 'sub_addr' ] )
#      else:
#        del rec[ 'sub_addr' ]
#
##      if self.autoSync and len( rec ) > 0:
##        self.FireStateChange( **rec )
#    #end if rec is not None
#  #end _OnSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateData()			-
  #----------------------------------------------------------------------
  def _UpdateData( self ):
    matrix = self._Create3DMatrix()
    if matrix is not None:
      drange = self.dmgr.GetRange(
          self.curDataSet,
	  self.timeValue if self.state.scaleMode == 'state' else -1.0
	  )

      if self.viz is None:
        self._CreateViz( matrix, drange )
      else:
        self.viz.SetScalarData( matrix, drange )

      self._UpdateSlicePositions()
  #end _UpdateData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateSlicePositions()		-
  #----------------------------------------------------------------------
  def _UpdateSlicePositions( self ):
    pos = self.CalcSlicePosition()
    self.viz.UpdateView( pos )
  #end _UpdateSlicePositions


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.UpdateState()			-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """
"""
    self._BusyBegin()

    try:
      #kwargs = self._UpdateStateValues( **kwargs )
      position_changed = kwargs.get( 'position_changed', False )
      data_changed = kwargs.get( 'data_changed', False )

      if 'assembly_addr' in kwargs and \
          kwargs[ 'assembly_addr' ] != self.assemblyAddr:
        position_changed = True
	self.assemblyAddr = kwargs[ 'assembly_addr' ]

      if 'axial_value' in kwargs and \
          kwargs[ 'axial_value' ][ 0 ] != self.axialValue[ 0 ] and \
	  self.curDataSet:
        position_changed = True
        self.axialValue = self.dmgr.\
	    GetAxialValue( self.curDataSet, cm = kwargs[ 'axial_value' ][ 0 ] )

      if 'data_model_mgr' in kwargs or 'scale_mode' in kwargs:
        data_changed = True

#      if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
#        data_changed = True
#        self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

      if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] != self.subAddr:
        position_changed = True
        self.subAddr = self.dmgr.NormalizeSubAddr( kwargs[ 'sub_addr' ] )

      if 'time_value' in kwargs and \
          kwargs[ 'time_value' ] != self.timeValue and \
          self.curDataSet:
        self.timeValue = kwargs[ 'time_value' ]
	state_index = max(
	    0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet )
	    )
	if state_index != self.stateIndex:
	  self.stateIndex = state_index
	  data_changed = True
      #end if 'time_value' in kwargs

#		-- Special handling for cur_dataset
#		--
      if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
        ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
        if ds_type and ds_type in self.GetDataSetTypes():
          data_changed = True
          self.curDataSet = kwargs[ 'cur_dataset' ]
	  self.container.GetDataSetMenu().Reset()
	  self.axialValue = self.dmgr.\
	      GetAxialValue( self.curDataSet, cm = self.axialValue[ 0 ] )
	  self.stateIndex = max(
	      0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet )
	      )

      if data_changed:
        self._UpdateData()
      elif position_changed:
        self._UpdateSlicePositions()
    #end try

    finally:
      self._BusyEnd()
  #end UpdateState

#end Slicer3DView


#------------------------------------------------------------------------
#	CLASS:		VolumeSlicer					-
#------------------------------------------------------------------------
class VolumeSlicer( HasTraits ):


#		-- Class Attributes?
#		--   (Just copying volume_slicer{_advanced}.py example)

  AXIS_INDEX = dict( x = 0, y = 1, z = 2 )

#			-- Must exist for reference to self.dataSource to
#			-- invoke _dataSource_default()
  dataSource = Instance( Source )
  #dataSourceCut = Instance( Source )
  #dataSourceX = Instance( Source )
  #dataSourceY = Instance( Source )
  #dataSourceZ = Instance( Source )

#			-- Must exist for references to
#			-- invoke _ipw3d{XYZ}_default()()
  ipw3dX = Instance( PipelineBase )
  ipw3dY = Instance( PipelineBase )
  ipw3dZ = Instance( PipelineBase )

  scene3d = Instance( MlabSceneModel, () )

  # accessible as VolumeSlicer.__view_traits__[ 'view' ]
  # type traitsui.view_elements.ViewElements
  view = View(
      Group(
          Item(
	      'scene3d',
	      editor = SceneEditor( scene_class = MayaviScene ),
	      height = 300, width = 300
	      ),
	  show_labels = False
          ),
      resizable = True
      #title = 'Volume Slicer'
      )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, **traits ):
    super( VolumeSlicer, self ).__init__( **traits )

    #self.dataRange = [ 0.0, 10.0 ]

#		-- Force creation of image_plane_widgets for now
#		--
    self.ipw3dX
    self.ipw3dY
    self.ipw3dZ

    #self.ipwCut
    #self.ipwX
    #self.ipwY
    #self.ipwZ

    #self.outlineX = None
    #self.outlineY = None
    #self.outlineZ = None

    self.logger = logging.getLogger( 'view3d' )

    self.slicePosition = [ -1, -1, -1 ]
    self.slicePositionListener = None
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.create_3d_ipw()			-
  #----------------------------------------------------------------------
  def create_3d_ipw( self, axis ):
    """
"""
    ipw = mlab.pipeline.image_plane_widget(
	self.dataSource,
	figure = self.scene3d.mayavi_scene,
	name = 'Cut ' + axis,
	plane_orientation = axis + '_axes',
	vmin = self.dataRange[ 0 ],
	vmax = self.dataRange[ 1 ]
        )
    return  ipw
  #end create_3d_ipw


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.create_data_source()		-
  #----------------------------------------------------------------------
  def create_data_source( self, uaxis ):
    """Magically called when self.dataSource first referenced
"""
    field = mlab.pipeline.scalar_field(
        self.matrix,
	figure = getattr( self, 'scene' + uaxis ).mayavi_scene
	)
    return  field
  #end create_data_source


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._dataSource_default()		-
  #----------------------------------------------------------------------
  def _dataSource_default( self ):
    """Magically called when self.dataSource first referenced
"""
#    field = mlab.pipeline.scalar_field(
#        self.matrix,
#	figure = self.scene3d.mayavi_scene
#	)
#    return  field
    return  self.create_data_source( '3d' )
  #end _dataSource_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_scene3d()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'scene3d.activated' )
  def display_scene3d( self ):
    """
"""
#    outline = mlab.pipeline.outline(
#	self.dataSource.mlab_source.dataset,
#	figure = self.scene3d.mayavi_scene
#        )

    self.scene3d.mlab.view( 10, 70 )

    for ipw in ( self.ipw3dX, self.ipw3dY, self.ipw3dZ ):
      ipw.ipw.interaction = 0

    #self.scene3d.scene.background = ( 0, 0, 0 )
    self.scene3d.scene.background = ( 0.925, 0.925, 0.925 )
    self.scene3d.scene.interactor.interactor_style = \
        tvtk.InteractorStyleTerrain()

#    self.scene3d.scene.interactor.add_observer(
#	'KeyPressEvent', func
#        )
#    func( vtk_obj, ev ):  vtk_obj.GetKeyCode()
  #end display_scene3d


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dX_default()			-
  #----------------------------------------------------------------------
  def _ipw3dX_default( self ):
    """Magically called when self.ipw3dX first referenced
"""
    return  self.create_3d_ipw( 'x' )
  #end _ipw3dX_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dY_default()			-
  #----------------------------------------------------------------------
  def _ipw3dY_default( self ):
    """Magically called when self.ipw3dY first referenced
"""
    return  self.create_3d_ipw( 'y' )
  #end _ipw3dY_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dZ_default()			-
  #----------------------------------------------------------------------
  def _ipw3dZ_default( self ):
    """Magically called when self.ipw3dZ first referenced
"""
    return  self.create_3d_ipw( 'z' )
  #end _ipw3dZ_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.GetScalarData()			-
  #----------------------------------------------------------------------
  def GetScalarData( self ):
    return  \
        self.dataSource.scalar_data \
	if self.dataSource is not None else \
	None
  #end GetScalarData


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.GetSlicePosition()			-
  #----------------------------------------------------------------------
  def GetSlicePosition( self ):
    return  self.slicePosition
  #end GetSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.GetSlicePositionListener()		-
  #----------------------------------------------------------------------
  def GetSlicePositionListener( self ):
    return  self.slicePositionListener
  #end GetSlicePositionListener


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.SetScalarData()			-
  #----------------------------------------------------------------------
  def SetScalarData( self, matrix, data_range ):
    self.dataRange = data_range

#    for d in (
#        self.dataSource, self.dataSourceCut,
#	self.dataSourceX, self.dataSourceY, self.dataSourceZ
#	):
    d = self.dataSource
    d.scalar_data = matrix
    d.update()
    d.data_changed = True
    d.update_image_data = True
    #end for

    #for uaxis in ( 'X', 'Y', 'Z', '3dX', '3dY', '3dZ', 'Cut' ):
    for uaxis in ( '3dX', '3dY', '3dZ' ):
      ipw = getattr( self, 'ipw' + uaxis )
      ipw.module_manager.scalar_lut_manager.data_range = data_range
    #end for
  #end SetScalarData


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.SetSlicePositionListener()		-
  #----------------------------------------------------------------------
  def SetSlicePositionListener( self, listener ):
    """
@param  listener	func( slice_position ), can be None
"""
    self.slicePositionListener = listener
  #end SetSlicePositionListener


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.UpdateView()			-
  #----------------------------------------------------------------------
  def UpdateView( self, position ):
    #position = obj.GetCurrentCursorPosition()
    #xxx compute pinRowCol or axialIndex
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'position=%s', str( position ) )
    for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
      ipw_3d = getattr( self, 'ipw3d%s' % cur_axis.upper() )
      ipw_3d.ipw.slice_position = float( position[ cur_ndx ] )

    #was set on on_slice_change()
    self.slicePosition = tuple( position )

    #self.class_trait_view().trait_set( title = 'Hello World' )
    #mlab.title( 'Hello World 2' )
  #end UpdateView

#end VolumeSlicer
