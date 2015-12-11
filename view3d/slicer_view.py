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

from data.model import *
from event.state import *
from widget.widget import *


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

    self.viz = VolumeSlicer( data = _data )
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

  AXIS_NAMES = dict( x = 0, y = 1, z = 2 )

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


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, **traits ):
    super( VolumeSlicer, this ).__init__( **traits )

#		-- Force creation of image_plane_widgets for now
#		--
    self.ipw3dX
    self.ipw3dY
    self.ipw3dZ
  #end __init__


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
  #end _dataSource_default

#end VolumeSlicer
