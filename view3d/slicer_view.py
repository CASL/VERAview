# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view.py					-
#	HISTORY:							-
#		2015-12-08	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys
import numpy as np

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
    self.SetSize( ( 600, 640 ) )
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
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.stateIndex = -1

    self.viz = None
    self.vizcontrol = None

    super( Slicer3DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView.GetAllow4DataSets()		-
  #----------------------------------------------------------------------
  def GetAllow4DataSets( self ):
    return  False
  #end GetAllow4DataSets


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

#		-- Create components
#		--
    _data = np.ndarray( ( 20, 20, 20 ), dtype = np.float64 )
    _data.fill( 1.0 )

    self.viz = VolumeSlicer( data = _data, data_range = [ 0.0, 5.0 ] )
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
    pass
  #end _UpdateData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateSlicePositions()		-
  #----------------------------------------------------------------------
  def _UpdateSlicePositions( self ):
    pass
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

#		-- Force creation of image_plane_widgets for now
#		--
    self.ipw3dX
    self.ipw3dY
    self.ipw3dZ

    self.ipwX = None
    self.ipwY = None
    self.ipwZ = None
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
	vmin = self.data_range[ 0 ], vmax = self.data_range[ 1 ]
        )
    return  ipw
  #end _create_3d_ipw


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._create_side_view()		-
  #----------------------------------------------------------------------
  def _create_side_view( self, axis ):
    """
"""
    uaxis = axis.upper()
    scene = getattr( self, 'scene%s' % uaxis )

    outline = mlab.pipeline.outline(
	self.dataSource.mlab_source.dataset,
	figure = scene.mayavi_scene
        )

    ipw = mlab.pipeline.image_plane_widget(
	outline,
	plane_orientation = '%s_axes' % axis,
	vmin = self.data_range[ 0 ],
	vmax = self.data_range[ 1 ]
        )

    setattr( self, 'ipw%s' % uaxis, ipw )

    ipw.ipw.sync_trait(
        'slice_position',
	getattr( self, 'ipw3d%s' % uaxis ).ipw
	)
    ipw.ipw.left_button_action = 0

    def move_view( obj, ev ):
      position = obj.GetCurrentCursorPosition()
      print >> sys.stderr, \
          '[move_view] axis=' + axis + ', position=' + str( position )
      for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
	if cur_axis != axis:
	  ipw_3d = getattr( self, 'ipw3d%s' % uaxis )
	  ipw_3d.ipw.slice_position = position[ cur_ndx ]
    #end move_view



    ipw.ipw.add_observer( 'InteractionEvent', move_view )
    ipw.ipw.add_observer( 'StartInteractionEvent', move_view )

    ipw.ipw.slice_position = 0.5 * self.data.shape[ self.AXIS_INDEX[ axis ] ]

    scene.mlab.view( *self.SIDE_VIEWS[ axis ] )

    scene.scene.background = ( 0, 0, 0 )
    scene.scene.interactor.interactor_style = \
        tvtk.InteractorStyleImage()
    if axis == 'x':
      scene.scene.parallel_projection = True
      scene.scene.camera.parallel_scale = \
          0.4 * np.mean( self.dataSource.scalar_data.shape )
  #end _create_side_view


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
	plane_orientation = 'y_axes'
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

#end VolumeSlicer
