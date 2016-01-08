# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view.py					-
#	HISTORY:							-
#		2016-01-08	leerw@ornl.gov				-
#	  Fixed calculation of assemblyIndex from/to slicePosition.
#		2016-01-07	leerw@ornl.gov				-
#	  Added autoSync field and widget menu item.  Seems to be working.
#		2016-01-06	leerw@ornl.gov				-
#	  Tying events to slice position changes.
#		2016-01-05	leerw@ornl.gov				-
#		2015-12-29	leerw@ornl.gov				-
#	  Creating VolumeSlicer after data first defined.
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

    #not needed self.state.AddListener( self )
    self.widgetContainer.Bind(
        wx.EVT_CLOSE,
	functools.partial( self._OnCloseFrame, False )
	)
    self.Bind(
        wx.EVT_CLOSE,
	functools.partial( self._OnCloseFrame, True )
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DFrame._OnCloseFrame()			-
  #----------------------------------------------------------------------
  def _OnCloseFrame( self, remove_listener, ev ):
    #self.widgetContainer.Destroy()

    if remove_listener:
      self.widgetContainer._OnClose( ev )

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
    self.assemblyIndex = ( -1, -1, -1 )
    self.axialValue = ( 0.0, -1, -1 )
    self.coreExtent = None  # left, top, right + 1, bottom + 1, dx, dy
    #self.curSize = None
    self.data = None

    self.autoSync = True
    self.menuDef = [ ( 'Disable Auto Sync', self._OnAutoSync ) ]
    self.meshLevels = None
    self.pinColRow = None
    self.pinDataSet = kwargs.get( 'dataset', 'pin_powers' )
    self.stateIndex = -1

    self.toolButtonDefs = \
      [
        ( 'sync_in_16x16.png', 'Sync From Other Widgets', self._OnSyncFrom ),
        ( 'sync_out_16x16.png', 'Sync To Other Widgets', self._OnSyncTo )
      ]

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

    if self.data != None and self.meshLevels != None:
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
        'pin_colrow': pin_colrow
        }
    #end if data defined

    return  rec
  #end CalcDataState


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._Create3DMatrix()			-
  #----------------------------------------------------------------------
  def _Create3DMatrix( self ):
    matrix = None

    if self.data != None and self.coreExtent != None:
      core = self.data.GetCore()
      dset = self.data.GetStateDataSet( self.stateIndex, self.pinDataSet )
      dset_value = dset.value

      print >> sys.stderr, \
          '%s[_Create3DMatrix] pinDataSet=%s, stateIndex=%d%s' % \
	  ( os.linesep, self.pinDataSet, self.stateIndex, os.linesep )

      # left, top, right + 1, bottom + 1, dx, dy
      #assy_range = self.data.ExtractSymmetryExtent()

      ax_mesh = core.axialMesh
      #ppinch = core.apitch if core.apitch > 0 else 1.0
      ppinch = 1.26
      self.meshLevels = [
	  int( (ax_mesh[ i + 1 ] - ax_mesh[ 0 ]) / ppinch )
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
	      ax_level = min(
	          bisect.bisect_left( self.meshLevels, z ),
		  len( self.meshLevels ) - 1
		  )
	      #for y in range( core.npiny ):
	      pin_y2 = 0
	      for y in range( core.npiny - 1, -1, -1 ):
	        for x in range( core.npinx ):
	          matrix[ z, pin_x + x, pin_y + pin_y2 ] = \
	              dset_value[ y, x, ax_level, assy_ndx ]
	        #end for x
	        pin_y2 += 1
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
  #	METHOD:		Slicer3DView._CreateViz()			-
  #----------------------------------------------------------------------
  def _CreateViz( self, matrix, drange ):
    """Builds this wxPython component.
"""
#		-- Create components
#		--
    self.viz = VolumeSlicer( matrix = matrix, dataRange = drange )
    #Do this to automatically fire state changes on slice position changes
    self.viz.SetSlicePositionListener( self._OnSlicePosition )
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
        STATE_CHANGE_assemblyIndex, STATE_CHANGE_axialValue,
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
  #	METHOD:		Slicer3DView.GetToolButtonDefs()		-
  #----------------------------------------------------------------------
  def GetToolButtonDefs( self, data_model ):
    return  self.toolButtonDefs
  #end GetToolButtonDefs


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
    self.data = State.GetDataModel( self.state )
    if self.data != None and self.data.HasData():
      self.assemblyIndex = self.state.assemblyIndex
      self.axialValue = self.state.axialValue
      self.coreExtent = self.data.ExtractSymmetryExtent()
      self.pinColRow = self.state.pinColRow
      self.pinDataSet = self.state.pinDataSet
      self.stateIndex = self.state.stateIndex

      self._UpdateData()
    #end if
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnAutoSync()			-
  #----------------------------------------------------------------------
  def _OnAutoSync( self, ev ):
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item != None:
      if item.GetText().startswith( 'Enable' ):
        item.SetText( item.GetText().replace( 'Enable', 'Disable' ) )
	self.autoSync = True
      else:
        item.SetText( item.GetText().replace( 'Disable', 'Enable' ) )
	self.autoSync = False
    #end if
  #end _OnAutoSync


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnSlicePosition()			-
  #----------------------------------------------------------------------
  def _OnSlicePosition( self, position ):
    """Used if automagically firing state changes
"""
    rec = self.CalcDataState( position )
    #print >> sys.stderr, '[Slicer3DView._OnSlicePosition]', str( rec )

    if rec != None:
      if rec[ 'assembly_index' ] != self.assemblyIndex:
        self.assemblyIndex = rec[ 'assembly_index' ]
      else:
        del rec[ 'assembly_index' ]

      if rec[ 'axial_value' ] != self.axialValue:
        self.axialValue = self.data.NormalizeAxialValue( rec[ 'axial_value' ] )
      else:
        del rec[ 'axial_value' ]

      if rec[ 'pin_colrow' ] != self.pinColRow:
        self.pinColRow = self.data.NormalizePinColRow( rec[ 'pin_colrow' ] )
      else:
        del rec[ 'pin_colrow' ]

      if self.autoSync and len( rec ) > 0:
        self.FireStateChange( **rec )
    #end if rec != None
  #end _OnSlicePosition


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnSyncFrom()			-
  #----------------------------------------------------------------------
  def _OnSyncFrom( self, ev ):
    self._UpdateSlicePositions()
  #end _OnSyncFrom


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._OnSyncTo()			-
  #----------------------------------------------------------------------
  def _OnSyncTo( self, ev ):
    if self.viz != None:
#      rec = self.CalcDataState( self.viz.GetSlicePosition() )
#      if rec != None:
#        self.FireStateChange( **rec )
      rec = \
        {
	'assembly_index': self.assemblyIndex,
	'axial_value': self.axialValue,
	'pin_colrow': self.pinColRow
	}
      self.FireStateChange( **rec )
    #end if rec != None
  #end _OnSyncTo


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

      if self.viz == None:
        self._CreateViz( matrix, drange )
      else:
        self.viz.SetScalarData( matrix, drange )

      self._UpdateSlicePositions()
  #end _UpdateData


  #----------------------------------------------------------------------
  #	METHOD:		Slicer3DView._UpdateSlicePositions()		-
  #----------------------------------------------------------------------
  def _UpdateSlicePositions( self ):
    core = self.data.GetCore()

#	-- Data matrix is z, x, y(reversed)
#	--
    z = self.meshLevels[ self.axialValue[ 1 ] ]

    assy_col = self.assemblyIndex[ 1 ] - self.coreExtent[ 0 ]
    x = core.npinx * assy_col + self.pinColRow[ 0 ]

    assy_row = self.assemblyIndex[ 2 ] - self.coreExtent[ 1 ]
    #derive y =
        #(core.npiny * self.coreExtent[ -1 ]) -
        #core.npiny * assy_row - self.pinColRow[ 1 ]
    y = \
        core.npiny * (self.coreExtent[ -1 ] - assy_row) - \
	self.pinColRow[ 1 ]

    pos = {}
    pos[ self.viz.AXIS_INDEX[ 'x' ] ] = z
    pos[ self.viz.AXIS_INDEX[ 'y' ] ] = x
    pos[ self.viz.AXIS_INDEX[ 'z' ] ] = y

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

      if 'assembly_index' in kwargs and kwargs[ 'assembly_index' ] != self.assemblyIndex:
        position_changed = True
	self.assemblyIndex = kwargs[ 'assembly_index' ]

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

      if data_changed:
        self._UpdateData()

      elif position_changed and self.autoSync:
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

  SIDE_VIEWS = \
    {
    'x': (  0, 90 ),
    'y': ( 90, 90 ),
    'z': (  0,  0 )
    }

#			-- Must exist for reference to self.dataSource to
#			-- invoke _dataSource_default()
  dataSource = Instance( Source )
  dataSourceX = Instance( Source )
  dataSourceY = Instance( Source )
  dataSourceZ = Instance( Source )

#			-- Must exist for references to
#			-- invoke _ipw3d{XYZ}_default()()
  ipw3dX = Instance( PipelineBase )
  ipw3dY = Instance( PipelineBase )
  ipw3dZ = Instance( PipelineBase )

  #ipwX = Instance( PipelineBase )
  #ipwY = Instance( PipelineBase )
  #ipwZ = Instance( PipelineBase )

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
  #	METHOD:		VolumeSlicer.create_side_view()			-
  #----------------------------------------------------------------------
  def create_side_view( self, axis, pos = None ):
    """
"""
    uaxis = axis.upper()
    scene = getattr( self, 'scene' + uaxis )
    data_source = getattr( self, 'dataSource' + uaxis )

    outline = mlab.pipeline.outline(
	#self.dataSource.mlab_source.dataset,
	data_source,
	figure = scene.mayavi_scene
        )
    setattr( self, 'outline' + uaxis, outline )

    # added figure
    ipw = mlab.pipeline.image_plane_widget(
	outline,  # self.dataSource.mlab_source.dataset
	#figure = scene.mayavi_scene,
	#name = 'Side ' + axis,
	plane_orientation = axis + '_axes',
	vmin = self.dataRange[ 0 ],
	vmax = self.dataRange[ 1 ]
        )
    setattr( self, 'ipw' + uaxis, ipw )

    ipw.ipw.left_button_action = 0
    ipw.ipw.add_observer(
        'InteractionEvent',
        functools.partial( self.on_slice_change, axis )
        )
    ipw.ipw.add_observer(
        'StartInteractionEvent',
        functools.partial( self.on_slice_change, axis )
        )

    print >> sys.stderr, '[create_side_view] uaxis=%s, pos=%s' % ( uaxis, pos )
    ipw.ipw.slice_position = \
        pos if pos != None else \
        0.5 * self.matrix.shape[ self.AXIS_INDEX[ axis ] ]

    ipw.ipw.sync_trait(
        'slice_position',
	getattr( self, 'ipw3d' + uaxis ).ipw
	)

#    if axis == 'x':
#      scene.scene.parallel_projection = True
#      scene.scene.camera.parallel_scale = \
#          0.5 * np.mean( data_source.scalar_data.shape )
#          #0.35 * np.mean( self.dataSource.scalar_data.shape )
#      print >> sys.stderr, '[create_side_view] xaxis scale=%f' % \
#          scene.scene.camera.parallel_scale
   
    return  ipw
  #end create_side_view


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
#    field = mlab.pipeline.scalar_field(
#        self.matrix,
#	figure = self.scene3d.mayavi_scene
#	)
#    return  field
    return  self.create_data_source( '3d' )
  #end _dataSource_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._dataSourceX_default()		-
  #----------------------------------------------------------------------
  def _dataSourceX_default( self ):
    """Magically called when self.dataSource first referenced
"""
    return  self.create_data_source( 'X' )
  #end _dataSourceX_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._dataSourceY_default()		-
  #----------------------------------------------------------------------
  def _dataSourceY_default( self ):
    """Magically called when self.dataSource first referenced
"""
    return  self.create_data_source( 'Y' )
  #end _dataSourceY_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._dataSourceZ_default()		-
  #----------------------------------------------------------------------
  def _dataSourceZ_default( self ):
    """Magically called when self.dataSource first referenced
"""
    return  self.create_data_source( 'Z' )
  #end _dataSourceZ_default


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
    return  self.display_side_view( 'x' )
    #return  self.create_side_view( 'x' )
  #end display_sceneX


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneY()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneY.activated' )
  def display_sceneY( self ):
    """
"""
    return  self.display_side_view( 'y' )
    #return  self.create_side_view( 'y' )
  #end display_sceneY


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_sceneZ()			-
  #----------------------------------------------------------------------
  @on_trait_change( 'sceneZ.activated' )
  def display_sceneZ( self ):
    """
"""
    return  self.display_side_view( 'z' )
    #return  self.create_side_view( 'z' )
  #end display_sceneZ


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.display_side_view()		-
  #----------------------------------------------------------------------
  def display_side_view( self, axis ):
    """
"""
    ipw = self.create_side_view( axis )
    uaxis = axis.upper()
    scene = getattr( self, 'scene' + uaxis )
    #outline = getattr( self, 'outline' + uaxis )
    #ipw = getattr( self, 'ipw' + uaxis )

    scene.mlab.view( *self.SIDE_VIEWS[ axis ] )

    scene.scene.background = ( 0, 0, 0 )
    scene.scene.interactor.interactor_style = \
        tvtk.InteractorStyleImage()

    if axis == 'x':
      scene.scene.parallel_projection = True
      scene.scene.camera.parallel_scale = \
          0.4 * np.mean( self.dataSourceX.scalar_data.shape )
#          #0.35 * np.mean( self.dataSource.scalar_data.shape )
      print >> sys.stderr, '[create_side_view] xaxis scale=%f' % \
          scene.scene.camera.parallel_scale
   
    return  ipw
  #end display_side_view


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
  #	METHOD:		VolumeSlicer._ipwX_default()			-
  #----------------------------------------------------------------------
  def _ipwX_default( self ):
    """Magically called when self.ipwX first referenced
Not called.
"""
    return  self.create_side_view( 'x' )
  #end _ipwX_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipwY_default()			-
  #----------------------------------------------------------------------
  def _ipwY_default( self ):
    """Magically called when self.ipwY first referenced
Not called.
"""
    return  self.create_side_view( 'y' )
  #end _ipwY_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer._ipwZ_default()			-
  #----------------------------------------------------------------------
  def _ipwZ_default( self ):
    """Magically called when self.ipwZ first referenced
Not called.
"""
    return  self.create_side_view( 'z' )
  #end _ipwZ_default


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.on_slice_change()			-
  #----------------------------------------------------------------------
  def on_slice_change( self, axis, obj, ev ):
    self.slicePosition = \
    position = obj.GetCurrentCursorPosition()
    for cur_axis, cur_ndx in self.AXIS_INDEX.iteritems():
      if cur_axis != axis:
        ipw_3d = getattr( self, 'ipw3d%s' % cur_axis.upper() )
	ipw_3d.ipw.slice_position = position[ cur_ndx ]

    if self.slicePositionListener != None:
      self.slicePositionListener( position )
  #end on_slice_change


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.remove_actors()			-
  #----------------------------------------------------------------------
  def remove_actors( self, scene, *preserve_list ):
    """Removes any ImagePlaneWidgets from scene.actor_list
@param  scene           MlabSceneModel from which to remove actors
@param  preserve_list   actor type matches for things not to remove
"""
    removed_flag = False
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
	removed_flag = True

      i -= 1
    #end while

    if remove_flag:
      scene.actor_removed = True
  #end remove_actors


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.remove_ipws()                      -
  #----------------------------------------------------------------------
  def remove_ipws( self, scene ):
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
  #end remove_ipws


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

    for d in ( self.dataSource, self.dataSourceX, self.dataSourceY, self.dataSourceZ ):
      d.scalar_data = matrix
      d.update()
      d.data_changed = True
      d.update_image_data = True
    #end for

    for axis in self.AXIS_INDEX:
      uaxis = axis.upper()
      ipw = getattr( self, 'ipw' + uaxis )
      ipw.module_manager.scalar_lut_manager.data_range = data_range

      ipw = getattr( self, 'ipw3d' + uaxis )
      ipw.module_manager.scalar_lut_manager.data_range = data_range
    #end for
  #end SetScalarData


  #----------------------------------------------------------------------
  #	METHOD:		VolumeSlicer.SetScalarData_1()			-
  #----------------------------------------------------------------------
  def SetScalarData_1( self, matrix, data_range ):
    self.dataRange = data_range

    for d in ( self.dataSource, self.dataSourceX, self.dataSourceY, self.dataSourceZ ):
      d.scalar_data = matrix
      d.update()
      d.data_changed = True
      d.update_image_data = True

#               -- Replace existing 3D image plane widgets
#               --
    #xxx save and restore scene3d camera position/view
    #self.remove_actors( self.scene3d, 'ScalarBarWidget' )
    scene3d_view = self.scene3d.mlab.view()
    self.remove_actors( self.scene3d )
    print >> sys.stderr, '[SetScalarData] scene3d_view=', str( scene3d_view )

    pos = {}
    for axis in self.AXIS_INDEX:
      uaxis = axis.upper()
      ipw = getattr( self, 'ipw' + uaxis )
      #x pos = ipw.ipw.slice_position
      pos[ axis ] = ipw.ipw.slice_position

      scene = getattr( self, 'scene' + uaxis )
      scene_view = scene.mlab.view()
      para_scale = scene.scene.camera.parallel_scale  if axis == 'x' else  None
      print >> sys.stderr, \
          '[SetScalarData] uaxis=%s, pos=%s, scene_view=%s, para_scale=%s' % \
	  ( uaxis, pos, str( scene_view ), str( para_scale) )

      ipw3d = self.create_3d_ipw( axis )
      ipw3d.ipw.interaction = 0
      #x ipw3d.ipw.slice_position = pos
      setattr( self, 'ipw3d' + uaxis, ipw3d )

      self.remove_actors( scene )
      #x ipw = self.create_side_view( axis, pos )
      ipw = self.create_side_view( axis, pos[ axis ] )
      print >> sys.stderr, \
          '[SetScalarData] uaxis=%s, restoring view=%s' % \
	  ( uaxis, str( scene_view ) )
      scene.mlab.view( *scene_view )
      if para_scale != None:
        scene.scene.parallel_projection = True
        scene.scene.camera.parallel_projection = True
        scene.scene.camera.parallel_scale = para_scale
    #end for

    for axis in self.AXIS_INDEX:
      uaxis = axis.upper()
      getattr( self, 'ipw3d' + uaxis ).ipw.slice_position = pos[ axis ]
      getattr( self, 'ipw' + uaxis ).ipw.slice_position = pos[ axis ]

    print >> sys.stderr, \
        '[SetScalarData] restoring scene3d view=%s' % \
	str( scene3d_view )
    self.scene3d.mlab.view( *scene3d_view )
  #end SetScalarData_1


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
      ipw_3d.ipw.slice_position = position[ cur_ndx ]

    #self.class_trait_view().trait_set( title = 'Hello World' )
    #mlab.title( 'Hello World 2' )
  #end UpdateView


#		-- Static Methods
#		--

#end VolumeSlicer
