# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view.py					-
#	HISTORY:							-
#		2016-08-10	leerw@ornl.gov				-
#	  Changed _CreateClipboardData() signature.
#		2016-03-08	leerw@ornl.gov				-
#	  Getting correct figure for mlab.savefig() call.
#		2016-03-07	leerw@ornl.gov				-
#	  Now just Slicer3DView with single figure.
#------------------------------------------------------------------------
import bisect, functools, math, os, sys
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

from data.datamodel import *
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
    self.assemblyIndex = ( -1, -1, -1 )
    self.axialValue = ( 0.0, -1, -1 )
    self.coreExtent = None  # left, top, right + 1, bottom + 1, dx, dy
    #self.curSize = None
    self.data = None

    #self.autoSync = True
    #self.menuDef = [ ( 'Disable Auto Sync', self._OnAutoSync ) ]
    self.meshLevels = None
    self.colRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.stateIndex = -1

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
    """Calculates axialValue (axial_cm, core_ndx, detector_ndx ),
assemblyIndex ( assy_ndx, assy_col, assy_row ), and pinColRow.
@param  slice_position	[ z, x, y ]
@return			dict with 'axial_value', 'assembly_ndex', and
			'pin_colrow' keys, or None if no data
"""
    rec = None

    if self.data is not None and self.meshLevels is not None:
      slice_z, slice_x, slice_y = slice_position
      core = self.data.GetCore()

      if slice_z >= 0:
        ax_level = min(
	    bisect.bisect_left( self.meshLevels, slice_z ),
	    len( self.meshLevels ) - 1
            )
        axial_value = self.data.CreateAxialValue( core_ndx = ax_level )
      else:
        axial_value = ( -1, -1, -1 )

      if slice_x >= 0 and slice_y >= 0:
        #assy_col = int( slice_x / core.npinx )
        #assy_row = core.nassy - 1 - int( slice_y / core.npiny )
        assy_col = int( slice_x / core.npinx ) + self.coreExtent[ 0 ]
        assy_row = self.coreExtent[ 3 ] - 1 - int( slice_y / core.npiny )
	assembly_index = self.data.CreateAssemblyIndex( assy_col, assy_row )

	pin_col = int( slice_x ) % core.npinx
	pin_row = core.npiny - (int( slice_y ) % core.npiny)
	pin_colrow = ( pin_col, pin_row )
      else:
        assembly_index = ( -1, -1, -1 )
        pin_colrow = ( -1, -1 )
      #end if-else

      rec = \
        {
        'assembly_index': assembly_index,
        'axial_value': axial_value,
        'colrow': colrow
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
    core = self.data.GetCore()

#	-- Data matrix is z, x, y(reversed)
#	--
    z = self.meshLevels[ self.axialValue[ 1 ] ]

    assy_col = self.assemblyIndex[ 1 ] - self.coreExtent[ 0 ]
    x = core.npinx * assy_col + self.colRow[ 0 ]

    assy_row = self.assemblyIndex[ 2 ] - self.coreExtent[ 1 ]
    y = \
        core.npiny * (self.coreExtent[ -1 ] - assy_row) - \
	self.colRow[ 1 ]

    return  ( z, x, y )
  #end CalcSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._Create3DMatrix()			-
  #----------------------------------------------------------------------
  def _Create3DMatrix( self ):
    matrix = None

    if self.data is not None and self.coreExtent is not None and \
        (self.data.core.npinx > 0 or self.data.core.npiny > 0):
      core = self.data.GetCore()
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_value = dset.value
      dset_shape = dset.shape

      print >> sys.stderr, \
          '%s[_Create3DMatrix] pinDataSet=%s, stateIndex=%d%s' % \
	  ( os.linesep, self.pinDataSet, self.stateIndex, os.linesep )

      # left, top, right + 1, bottom + 1, dx, dy
      #assy_range = self.data.ExtractSymmetryExtent()

      ax_mesh = core.axialMesh
      #pin_pitch = 1.26
      pin_pitch = core.GetAssemblyPitch() / max( core.npinx, core.npiny )
      self.meshLevels = [
	  int( (ax_mesh[ i + 1 ] - ax_mesh[ 0 ]) / pin_pitch )
	  for i in range( len( ax_mesh ) - 1 )
          ]
      z_size = self.meshLevels[ -1 ]

      # z, x, y(bottom up)
      matrix = np.ndarray(
	#( z_size, core.npinx * assy_range[ 5 ], core.npiny * assy_range[ 4 ] ),
	( z_size,
	  core.npinx * self.coreExtent[ -2 ],
	  core.npiny * self.coreExtent[ -1 ] ),
	np.float64
	)
      matrix.fill( 0.0 )
    
      pin_y = 0
      #for assy_y in range( assy_range[ 3 ] - 1, assy_range[ 1 ] - 1, -1 ):
      for assy_y in range( self.coreExtent[ 3 ] - 1, self.coreExtent[ 1 ] - 1, -1 ):
        pin_x = 0
        #for assy_x in range( assy_range[ 0 ], assy_range[ 2 ] ):
        for assy_x in range( self.coreExtent[ 0 ], self.coreExtent[ 2 ] ):
          assy_ndx = core.coreMap[ assy_y, assy_x ] - 1
          if assy_ndx >= 0:
	    for z in range( z_size ):
	      #xxx is this off by one?
	      ax_level = min(
	          bisect.bisect_left( self.meshLevels, z ),
		  len( self.meshLevels ) - 1
		  )
              #print >> sys.stderr, '[XX] z=%d, ax_level=%d' % ( z, ax_level )
	      #for y in range( core.npiny ):
	      pin_y2 = 0
	      for y in range( core.npiny - 1, -1, -1 ):
		data_y = min( y, dset_shape[ 0 ] - 1 )

	        for x in range( core.npinx ):
		  data_x = min( x, dset_shape[ 1 ] - 1 )
	          matrix[ z, pin_x + x, pin_y + pin_y2 ] = \
	              dset_value[ data_y, data_x, ax_level, assy_ndx ]
	        #end for x
	        pin_y2 += 1
	      #end for y
	    #end for z
          #end if assy_ndx

          pin_x += core.npinx
        #end for assy_x

        pin_y += core.npiny
      #end for assy_y
    #end if self.data is not None

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
      valid = DataModel.IsValidObj(
	  self.data,
	  assembly_index = self.assemblyIndex[ 0 ],
	  axial_level = self.axialValue[ 1 ]
          )

    if valid:
      #pos = self.CalcSlicePosition()
      pos = self.viz.GetSlicePosition()
      print >> sys.stderr, \
          '[_CreateClipboardSelectedData] pos=' + str( pos )
      csv_text = '"Axial=%d,Col=%d,Row=%d\n' % pos
      csv_text += '%.7g' % matrix[ pos[ 2 ], pos[ 0 ], pos[ 1 ] ]
    #end if

    return  csv_text
  #end _CreateClipboardSelectedData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._CreateMenuDef()			-
  #----------------------------------------------------------------------
  def _CreateMenuDef( self, data_model ):
    """
"""
    menu_def = super( Slicer3DView, self )._CreateMenuDef( data_model )
    #my_def = [ ( 'Disable Auto Sync', self._OnAutoSync ) ]

    find_max_def = \
      [
        { 'label': 'All State Points',
	  'handler': functools.partial( self._OnFindMax, True ) },
        { 'label': 'Current State Point',
	  'handler': functools.partial( self._OnFindMax, False ) }
      ]

    my_def = \
      [
	{ 'label': '-' },
	{ 'label': 'Find Maximum', 'submenu': find_max_def }
      ]
    return  menu_def + my_def
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
  #	METHOD:		Slicer3DView.GetAllow4DataSets()		-
  #----------------------------------------------------------------------
  def GetAllow4DataSets( self ):
    return  False
  #end GetAllow4DataSets


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self ):
    return  self.data
  #end GetDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return  [ 'pin' ]
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    locks = set([
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
        STATE_CHANGE_colRow, STATE_CHANGE_pinDataSet,
        STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
        ])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetMenuDef()			-
  #----------------------------------------------------------------------
#  def GetMenuDef( self, data_model ):
#    return  self.menuDef
#  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Volume Slicer 3D View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
#  def GetToolButtonDefs( self, data_model ):
#    return  self.toolButtonDefs
#  #end GetToolButtonDefs


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
    self.data = State.FindDataModel( self.state )
    if self.data is not None and self.data.HasData():
      self.assemblyIndex = self.state.assemblyIndex
      self.axialValue = self.state.axialValue
      self.coreExtent = self.data.ExtractSymmetryExtent()
      self.colRow = self.state.colRow
      #self.pinDataSet = self.state.pinDataSet
      self.stateIndex = self.state.stateIndex

#      if DataModel.IsExtra( self.state.pinDataSet ):
#        self.pinDataSet = 'pin_powers'
#        wx.MessageBox(
#	    'Extra datasets not supported in the 3D Volume Slicer.\n' +
#	    'Loading "pin_powers" instead.',
#	    'View 3D Volume Slicer',
#	    wx.ICON_INFORMATION | wx.OK_DEFAULT
#	    )
#      else:
      self.pinDataSet = self.state.pinDataSet

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
  #	METHOD:		Slicer3DView._OnFindMax()			-
  #----------------------------------------------------------------------
  def _OnFindMax( self, all_states_flag, ev ):
    """Calls _OnFindMaxPin().
"""
    if DataModel.IsValidObj( self.data ) and self.pinDataSet is not None:
      self._OnFindMaxPin( self.pinDataSet, all_states_flag )
  #end _OnFindMax


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
#      if rec[ 'assembly_index' ] != self.assemblyIndex:
#        self.assemblyIndex = rec[ 'assembly_index' ]
#      else:
#        del rec[ 'assembly_index' ]
#
#      if rec[ 'axial_value' ] != self.axialValue:
#        self.axialValue = self.data.NormalizeAxialValue( rec[ 'axial_value' ] )
#      else:
#        del rec[ 'axial_value' ]
#
#      if rec[ 'pin_colrow' ] != self.pinColRow:
#        self.pinColRow = self.data.NormalizePinColRow( rec[ 'pin_colrow' ] )
#      else:
#        del rec[ 'pin_colrow' ]
#
##      if self.autoSync and len( rec ) > 0:
##        self.FireStateChange( **rec )
#    #end if rec is not None
#  #end _OnSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    if ds_name != self.pinDataSet:
      wx.CallAfter( self.UpdateState, pin_dataset = ds_name )
      self.FireStateChange( pin_dataset = ds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateData()			-
  #----------------------------------------------------------------------
  def _UpdateData( self ):
    matrix = self._Create3DMatrix()
    if matrix is not None:
      drange = self.data.GetRange( self.pinDataSet )

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
    self.viz.UpdateView( self.CalcSlicePosition() )
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

      if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
        position_changed = True
	self.assemblyIndex = kwargs[ 'assembly_index' ]

      if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
        position_changed = True
        self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )

      if 'colrow' in kwargs and kwargs[ 'colrow' ] != self.colRow:
        position_changed = True
        self.colRow = self.data.NormalizeColRow( kwargs[ 'colrow' ] )

      if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
        data_changed = True
        self.pinDataSet = kwargs[ 'pin_dataset' ]

      if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
        data_changed = True
        self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

      if data_changed:
        self._UpdateData()

#      elif position_changed and self.autoSync:
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
    print >> sys.stderr, \
        '[UpdateView] position=' + str( position )
    for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
      ipw_3d = getattr( self, 'ipw3d%s' % cur_axis.upper() )
      ipw_3d.ipw.slice_position = float( position[ cur_ndx ] )

    #was set on on_slice_change()
    self.slicePosition = tuple( position )

    #self.class_trait_view().trait_set( title = 'Hello World' )
    #mlab.title( 'Hello World 2' )
  #end UpdateView

#end VolumeSlicer
