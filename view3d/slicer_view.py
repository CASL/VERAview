# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view.py					-
#	HISTORY:							-
#		2015-12-08	leerw@ornl.gov				-
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
#	CLASS:		Slicer3DFrame					-
#------------------------------------------------------------------------
class Slicer3DFrame( wx.Frame ):


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DFrame.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, parent, id, state ):
    super( Slicer3DFrame, self ).__init__( parent, id )

    #self.state.Load( data_model )
    self.state = state

    self.widgetContainer = \
        WidgetContainer( self, 'view3d.slicer_view.Slicer3DView', self.state )
    self.SetSize( ( 700, 750 ) )
    self.SetTitle( 'VERAView 3D View' )

    #self.state.AddListener( self )
    self.widgetContainer.Bind( wx.EVT_CLOSE, self._OnCloseFrame )
    self.Bind( wx.EVT_CLOSE, self._OnCloseFrame )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DFrame._OnCloseFrame()			-
  #----------------------------------------------------------------------
  def _OnCloseFrame( self, ev ):
    #self.widgetContainer.Destroy()
    self.Destroy()
  #end _OnCloseFrame

#end Slicer3DFrame


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
    self.axialValue = ( 0.0, -1, -1 )
    #self.curSize = None
    self.data = None

    self.menuDef = None
    self.meshLevels = None
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.stateIndex = -1

    self.viz = None
    self.vizcontrol = None

    super( Slicer3DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._Create3DMatrix()			-
  #----------------------------------------------------------------------
  def _Create3DMatrix( self ):
    matrix = None

    if self.data != None:
      core = self.data.GetCore()
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_value = dset.value

      # left, top, right + 1, bottom + 1, dx, dy
      assy_range = self.data.ExtractSymmetryExtent()

      ax_mesh = core.axialMesh
      #ppinch = core.apitch if core.apitch > 0 else 1.0
      ppinch = 1.26
      self.meshLevels = [
	  int( (ax_mesh[ i + 1 ] - ax_mesh[ 0 ]) / ppinch )
	  for i in range( len( ax_mesh ) - 1 )
          ]
      z_size = self.meshLevels[ -1 ]

      # z, x, y
      matrix = np.ndarray(
	( z_size, core.npinx * assy_range[ 5 ], core.npiny * assy_range[ 4 ] ),
	np.float64
	)
      matrix.fill( 0.0 )
    
      pin_y = 0
      #for assy_y in range( assy_range[ 1 ], assy_range[ 3 ] ):
      for assy_y in range( assy_range[ 3 ] - 1, assy_range[ 1 ] - 1, -1 ):
        pin_x = 0
        for assy_x in range( assy_range[ 0 ], assy_range[ 2 ] ):
          assy_ndx = core.coreMap[ assy_y, assy_x ] - 1
          if assy_ndx >= 0:
	    for z in range( z_size ):
	      ax_level = min(
	          bisect.bisect_left( self.meshLevels, z ),
		  len( self.meshLevels ) - 1
		  )
	      for y in range( core.npiny ):
	        for x in range( core.npinx ):
	          matrix[ z, pin_x + x, pin_y + y ] = \
	              dset_value[ y, x, ax_level, assy_ndx ]
	        #end for x
	      #end for y
	    #end for z
          #end if assy_ndx

          pin_x += core.npinx
        #end for assy_x

        pin_y += core.npiny
      #end for assy_y
    #end if self.data != None

    return  matrix
  #end _Create3DMatrix


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
  #	METHOD:		Slicer3DView.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    return  'pin'
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetEventLockSet()			-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    locks = set([
        STATE_CHANGE_axialValue,
        STATE_CHANGE_pinColRow, STATE_CHANGE_pinDataSet,
        STATE_CHANGE_stateIndex, STATE_CHANGE_timeDataSet
        ])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetMenuDef()			-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    return  self.menuDef
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Volume Slicer'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this wxPython component.
"""

#		-- Getting started cheat data
#		--
    #self.data = DataModel( '/Users/re7x/study/casl/andrew/L1_ALL_STATES.h5' )
    #self.pinDataSet = 'pin_powers'
    #self.stateIndex = 0
    #_data = self._Create3DMatrix()
    _data = np.ndarray( ( 26, 17, 17 ), dtype = np.float64 )
    _data.fill( 1.0 )

#		-- Create components
#		--
    self.viz = VolumeSlicer( data = _data, dataRange = [ 0.0, 5.0 ] )
    self.vizcontrol = \
        self.viz.edit_traits( parent = self, kind = 'subpanel' ).control

#		-- Lay out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.vizcontrol, 0, wx.ALL | wx.EXPAND )

    self.SetAutoLayout( True )
    self.SetSizer( sizer )
    self.SetMinSize( ( 320, 320 ) )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._LoadDataModel()			-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      self.axialValue = self.state.axialValue
      self.pinColRow = self.state.pinColRow
      self.pinDataSet = self.state.pinDataSet
      self.stateIndex = self.state.stateIndex

      self._UpdateData()
    #end if
  #end _LoadDataModel


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
    if matrix != None:
      drange = self.data.GetRange( self.pinDataSet )
      self.viz.SetScalarData( matrix, drange )
  #end _UpdateData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateSlicePositions()		-
  #----------------------------------------------------------------------
  def _UpdateSlicePositions( self ):
    pass
    #xxx convert from pinColRow and axialIndex to slice positions
#    for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
#      ipw_3d = getattr( self, 'ipw3d%s' % uaxis )
#      ipw_3d.ipw.slice_position = position[ cur_ndx ]
  #end _UpdateSlicePositions


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.UpdateState()			-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    self._BusyBegin()

    try:
      #kwargs = self._UpdateStateValues( **kwargs )
      position_changed = kwargs.get( 'position_changed', False )
      data_changed = kwargs.get( 'data_changed', False )

      if 'axial_value' in kwargs and kwargs[ 'axial_value' ] != self.axialValue:
        position_changed = True
        self.axialValue = self.data.NormalizeAxialValue( kwargs[ 'axial_value' ] )

      if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != self.pinColRow:
        position_changed = True
        self.pinColRow = self.data.NormalizePinColRow( kwargs[ 'pin_colrow' ] )

      if 'pin_dataset' in kwargs and kwargs[ 'pin_dataset' ] != self.pinDataSet:
        data_changed = True
        self.pinDataSet = kwargs[ 'pin_dataset' ]

      if 'state_index' in kwargs and kwargs[ 'state_index' ] != self.stateIndex:
        data_changed = True
        self.stateIndex = self.data.NormalizeStateIndex( kwargs[ 'state_index' ] )

      if position_changed:
        self._UpdateSlicePositions()

      elif data_changed:
        self._UpdateData()
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

  SIDE_VIEWS = \
    {
    'x': (  0, 90 ),
    'y': ( 90, 90 ),
    'z': (  0,  0 )
    }

#			-- Must exist for reference to self.dataSource to
#			-- invoke _dataSource_default()
  dataSource = Instance( Source )

#			-- Must exist for references to
#			-- invoke _ipw3d{XYZ}_default()()
  ipw3dX = Instance( PipelineBase )
  ipw3dY = Instance( PipelineBase )
  ipw3dZ = Instance( PipelineBase )

  scene3d = Instance( MlabSceneModel, () )
  sceneCut = Instance( MlabSceneModel, () )
  sceneX = Instance( MlabSceneModel, () )
  sceneY = Instance( MlabSceneModel, () )
  sceneZ = Instance( MlabSceneModel, () )

  # accessible as VolumeSlicer.__view_traits__[ 'view' ]
  # type traitsui.view_elements.ViewElements
  view = View(
      HGroup(
          Group(
	      Item(
		  'sceneY',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneZ',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneX',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      show_labels = False
	      ),
          Group(
	      Item(
		  'scene3d',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 300, width = 300
	          ),
	      Item(
		  'sceneCut',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 200, width = 300
	          ),
	      show_labels = False
	      )
          ),
      resizable = True,
      title = 'Volume Slicer'
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

    #self.ipwX = None
    #self.ipwY = None
    #self.ipwZ = None

    #self.outlineX = None
    #self.outlineY = None
    #self.outlineZ = None
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._create_3d_ipw()			-
  #----------------------------------------------------------------------
  def _create_3d_ipw( self, axis ):
    """
"""
    ipw = mlab.pipeline.image_plane_widget(
	self.dataSource,
	figure = self.scene3d.mayavi_scene,
	name = 'Cut %s' % axis,
	plane_orientation = '%s_axes' % axis,
	vmin = self.dataRange[ 0 ],
	vmax = self.dataRange[ 1 ]
        )
    return  ipw
  #end _create_3d_ipw


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._create_side_view()		-
  #----------------------------------------------------------------------
  def _create_side_view( self, axis, pos = None ):
    """
"""
    uaxis = axis.upper()
    scene = getattr( self, 'scene%s' % uaxis )

    outline = mlab.pipeline.outline(
	self.dataSource.mlab_source.dataset,
	figure = scene.mayavi_scene
        )
    setattr( self, 'outline%s' % uaxis, outline )

    # added figure
    ipw = mlab.pipeline.image_plane_widget(
	outline,  #self.dataSource,
	figure = scene.mayavi_scene,
	name = 'Side %s' % axis,
	plane_orientation = '%s_axes' % axis,
	vmin = self.dataRange[ 0 ],
	vmax = self.dataRange[ 1 ]
        )

    setattr( self, 'ipw%s' % uaxis, ipw )

    ipw.ipw.sync_trait(
        'slice_position',
	getattr( self, 'ipw3d%s' % uaxis ).ipw
	)
    ipw.ipw.left_button_action = 0

    def move_view( obj, ev ):
      position = obj.GetCurrentCursorPosition()
      #xxx compute pinRowCol or axialIndex
      print >> sys.stderr, \
          '[move_view] axis=' + axis + ', position=' + str( position )
      for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
	if cur_axis != axis:
	  ipw_3d = getattr( self, 'ipw3d%s' % cur_axis.upper() )
	  ipw_3d.ipw.slice_position = position[ cur_ndx ]
    #end move_view

    #ipw.ipw.add_observer( 'InteractionEvent', move_view )
    #ipw.ipw.add_observer( 'StartInteractionEvent', move_view )
    ipw.ipw.add_observer(
        'InteractionEvent',
        functools.partial( self._on_view_change, axis )
        )
    ipw.ipw.add_observer(
        'StartInteractionEvent',
        functools.partial( self._on_view_change, axis )
        )

    ipw.ipw.slice_position = \
        pos if pos != None else \
        0.5 * self.data.shape[ self.AXIS_INDEX[ axis ] ]

    if pos == None:
      scene.mlab.view( *self.SIDE_VIEWS[ axis ] )

    scene.scene.background = ( 0, 0, 0 )
    scene.scene.interactor.interactor_style = \
        tvtk.InteractorStyleImage()
    if axis == 'x':
      scene.scene.parallel_projection = True
      scene.scene.camera.parallel_scale = \
          0.35 * np.mean( self.dataSource.scalar_data.shape )
   
    return  ipw
  #end _create_side_view


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.create_view()			-
  #----------------------------------------------------------------------
  def create_view( self ):
    view = View(
        HGroup(
          Group(
	      Item(
		  'sceneY',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneZ',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneX',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      show_labels = False
	      ),
          Group(
	      Item(
		  'scene3d',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 300, width = 300
	          ),
	      Item(
		  'sceneCut',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 200, width = 300
	          ),
	      show_labels = False
	      )
          ),
        resizable = True,
        title = 'Volume Slicer'
        )

    return  view
  #end create_view


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._dataSource_default()		-
  #----------------------------------------------------------------------
  def _dataSource_default( self ):
    """Magically called when self.dataSource first referenced
"""
    field = mlab.pipeline.scalar_field(
        self.data,
	figure = self.scene3d.mayavi_scene
	)
    return  field
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

    self.scene3d.scene.background = ( 0, 0, 0 )
    self.scene3d.scene.interactor.interactor_style = \
        tvtk.InteractorStyleTerrain()
  #end display_scene3d


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneCut()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneCut.activated' )
  def display_sceneCut( self ):
    """
"""
    outline = mlab.pipeline.outline(
	self.dataSource.mlab_source.dataset,
	figure = self.sceneCut.mayavi_scene
        )

    self.ipwCut = mlab.pipeline.image_plane_widget(
	outline,
	plane_orientation = 'y_axes',
        vmin = self.dataRange[ 0 ],
        vmax = self.dataRange[ 1 ]
        )

    self.sceneCut.scene.background = ( 0, 0, 0 )
    self.sceneCut.scene.interactor.interactor_style = \
        tvtk.InteractorStyleImage()
  #end display_sceneCut


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneX()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneX.activated' )
  def display_sceneX( self ):
    """
"""
    return  self._create_side_view( 'x' )
  #end display_sceneX


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneY()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneY.activated' )
  def display_sceneY( self ):
    """
"""
    return  self._create_side_view( 'y' )
  #end display_sceneY


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneZ()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneZ.activated' )
  def display_sceneZ( self ):
    """
"""
    return  self._create_side_view( 'z' )
  #end display_sceneZ


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dX_default()			-
  #----------------------------------------------------------------------
  def _ipw3dX_default( self ):
    """Magically called when self.ipw3dX first referenced
"""
    return  self._create_3d_ipw( 'x' )
  #end _ipw3dX_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dY_default()			-
  #----------------------------------------------------------------------
  def _ipw3dY_default( self ):
    """Magically called when self.ipw3dY first referenced
"""
    return  self._create_3d_ipw( 'y' )
  #end _ipw3dY_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipw3dZ_default()			-
  #----------------------------------------------------------------------
  def _ipw3dZ_default( self ):
    """Magically called when self.ipw3dZ first referenced
"""
    return  self._create_3d_ipw( 'z' )
  #end _ipw3dZ_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._on_view_change()                  -
  #----------------------------------------------------------------------
  def _on_view_change( self, axis, obj, ev ):
    position = obj.GetCurrentCursorPosition()
    #xxx compute pinRowCol or axialIndex
    print >> sys.stderr, \
        '[_on_view_change] axis=' + axis + ', position=' + str( position )
    for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
      if cur_axis != axis:
        ipw_3d = getattr( self, 'ipw3d%s' % cur_axis.upper() )
	ipw_3d.ipw.slice_position = position[ cur_ndx ]
  #end _on_view_change


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._remove_actors()                   -
  #----------------------------------------------------------------------
  def _remove_actors( self, scene, *preserve_list ):
    """Removes any ImagePlaneWidgets from scene.actor_list
@param  scene           MlabSceneModel from which to remove actors
@param  preserve_list   actor type matches for things not to remove
"""
    i = len( scene.actor_list ) - 1
    while i >= 0:
      type_name = str( type( scene.actor_list[ i ] ) )
      remove_flag = True
      for p in preserve_list:
        if type_name.find( p ) >= 0:
          remove_flag = False
          break
      #end for p

      if remove_flag:
        scene.remove_actor( scene.actor_list[ i ] )
        #del scene.actor_list[ i ]

      i -= 1
    #end while
  #end _remove_actors


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._remove_ipws()                     -
  #----------------------------------------------------------------------
  def _remove_ipws( self, scene ):
    """Removes any ImagePlaneWidgets from scene.actor_list
@param  scene           MlabSceneModel from which to remove ImagePlaneWidgets
"""
    i = len( scene.actor_list ) - 1
    while i > 0:
      type_name = str( type( scene.actor_list[ i ] ) )
      if type_name.find( 'ImagePlaneWidget' ) >= 0:
        del scene.actor_list[ i ]
      i -= 1
    #end while
  #end _remove_ipws


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._replace_side_view()		-
  #----------------------------------------------------------------------
  def _replace_side_view( self, axis, pos = None ):
    """
"""
    uaxis = axis.upper()
    scene = getattr( self, 'scene%s' % uaxis )

    outline = mlab.pipeline.outline(
	self.dataSource.mlab_source.dataset,
	figure = scene.mayavi_scene
        )
    setattr( self, 'outline%s' % uaxis, outline )

    # added figure
    ipw = mlab.pipeline.image_plane_widget(
	outline,  #self.dataSource,
	figure = scene.mayavi_scene,
	name = 'Side %s' % axis,
	plane_orientation = '%s_axes' % axis,
	vmin = self.dataRange[ 0 ],
	vmax = self.dataRange[ 1 ]
        )
    setattr( self, 'ipw%s' % uaxis, ipw )

    ipw.ipw.sync_trait(
        'slice_position',
	getattr( self, 'ipw3d%s' % uaxis ).ipw
	)
    ipw.ipw.left_button_action = 0

    ipw.ipw.add_observer(
        'InteractionEvent',
        functools.partial( self._on_view_change, axis )
        )
    ipw.ipw.add_observer(
        'StartInteractionEvent',
        functools.partial( self._on_view_change, axis )
        )

    ipw.ipw.slice_position = \
        pos if pos != None else \
        0.5 * self.data.shape[ self.AXIS_INDEX[ axis ] ]

    if pos == None:
      scene.mlab.view( *self.SIDE_VIEWS[ axis ] )
   
    return  ipw
  #end _replace_side_view


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._replace_side_view_1()		-
  #----------------------------------------------------------------------
  def _replace_side_view_1( self, axis, pos = None ):
    """
"""
    uaxis = axis.upper()
    scene = getattr( self, 'scene%s' % uaxis )
    outline = getattr( self, 'outline%s' % uaxis )

    #self._remove_actors( scene )
#1    mmgr = outline.module_manager
#1    for i in range( len( mmgr.children ) - 1, -1 , -1 ):
#1      mmgr.remove_child( mmgr.children[ i ] )

#1    outline = mlab.pipeline.outline(
#1	self.dataSource.mlab_source.dataset,
#1	figure = scene.mayavi_scene
#1        )
#1    setattr( self, 'outline%s' % uaxis, outline )

    outline.update_data()
    outline.update_pipeline()
    outline.data_changed = True
    outline.pipeline_changed = True

    # added figure
#1    ipw = mlab.pipeline.image_plane_widget(
#1	outline,  #self.dataSource,
#1	figure = scene.mayavi_scene,
#1	name = 'Side %s' % axis,
#1	plane_orientation = '%s_axes' % axis,
#1	vmin = self.dataRange[ 0 ],
#1	vmax = self.dataRange[ 1 ]
#1        )
#1    setattr( self, 'ipw%s' % uaxis, ipw )

#1    ipw.ipw.sync_trait(
#1        'slice_position',
#1	getattr( self, 'ipw3d%s' % uaxis ).ipw
#1	)
#1    ipw.ipw.left_button_action = 0

#1    ipw.ipw.add_observer(
#1        'InteractionEvent',
#1        functools.partial( self._on_view_change, axis )
#1        )
#1    ipw.ipw.add_observer(
#1        'StartInteractionEvent',
#1        functools.partial( self._on_view_change, axis )
#1        )

#1    ipw.ipw.slice_position = \
#1        pos if pos != None else \
#1        0.5 * self.data.shape[ self.AXIS_INDEX[ axis ] ]

#1    if pos == None:
#1      scene.mlab.view( *self.SIDE_VIEWS[ axis ] )

#1    scene.scene.background = ( 0, 0, 0 )
#1    scene.scene.interactor.interactor_style = \
#1        tvtk.InteractorStyleImage()
#1    if axis == 'x':
#1      scene.scene.parallel_projection = True
#1      scene.scene.camera.parallel_scale = \
#1          0.35 * np.mean( self.dataSource.scalar_data.shape )

    ipw = getattr( self, 'ipw%s' % uaxis )
    ipw.update_data()
    ipw.update_pipeline()
    ipw.data_changed = True
    ipw.pipeline_changed = True
    # ipw.parent.parent.scalar_data = self.dataSource.scalar_data  noworky

    outline.module_manager.update()
   
    return  ipw
  #end _replace_side_view_1


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.SetScalarData()			-
  #----------------------------------------------------------------------
  def SetScalarData( self, data, data_range ):
    self.dataRange = data_range

    self.dataSource.scalar_data = data
    self.dataSource.update()
    self.dataSource.data_changed = True
    self.dataSource.update_image_data = True

#               -- Replace existing 3D image plane widgets
#               --
    #xxx save and restore scene3d camera position/view
    #self._remove_actors( self.scene3d, 'ScalarBarWidget' )
    self._remove_actors( self.scene3d )

    pdb.set_trace()
    for axis in self.AXIS_INDEX:
    #for axis in ( 'x' ):
      uaxis = axis.upper()
      ipw = getattr( self, 'ipw%s' % uaxis )
      pos = ipw.ipw.slice_position

      ipw3d = self._create_3d_ipw( axis )
      ipw3d.ipw.interaction = 0
      ipw3d.ipw.slice_position = pos
      setattr( self, 'ipw3d%s' % uaxis, ipw3d )

#1      self._remove_actors( getattr( self, 'scene%s' % uaxis ) )
#1      ipw = self._create_side_view( axis, pos )
      #setattr( self, 'ipw%s' % uaxis, ipw )  done in _create_side_view()
#2      ipw.ipw.sync_trait( 'slice_position', ipw3d.ipw )  # ditto
#2      ipw.module_manager.scalar_lut_manager.data_range = data_range
#2      ipw.update_data()
      #nada ipw.module_manager.update()
      #nada getattr( self, 'outline%s' % uaxis ).update_data()
      self._replace_side_view_1( axis, pos )
    #end for
  #end SetScalarData


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.create_view()			-
  #----------------------------------------------------------------------
  @staticmethod
  def create_view():
    view = View(
        HGroup(
          Group(
	      Item(
		  'sceneY',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneZ',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      Item(
		  'sceneX',
		  editor = SceneEditor( scene_class = Scene ),
		  height = 250, width = 300
	          ),
	      show_labels = False
	      ),
          Group(
	      Item(
		  'scene3d',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 300, width = 300
	          ),
	      Item(
		  'sceneCut',
		  editor = SceneEditor( scene_class = MayaviScene ),
		  height = 200, width = 300
	          ),
	      show_labels = False
	      )
          ),
        resizable = True,
        title = 'Volume Slicer'
        )

    return  view
  #end create_view

#end VolumeSlicer
