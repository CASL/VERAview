# $Id$
# -----------------------------------------------------------------------
#  NAME:    volume_view.py          -
#  HISTORY:              -
#    2018-01-23  purvesmh@ornl.gov
#    VolumeViewAlt moved back to Volume3DView to provide new 3D volume
#    view capability. WIP full core viz support
#    2018-10-11  purvesmh@ornl.gov
#    Copy to VolumeViewAlt class - initial volume/plane cut capability
#    2017-08-18  leerw@ornl.gov        -
#    Using AxialValue class.
#    2017-05-13  leerw@ornl.gov        -
#    Added Is3D().
#    2017-05-05  leerw@ornl.gov        -
#    Added {Load,Save}Props(), modified LoadDataModel() to process
#    the reason param.
#    2017-01-09  leerw@ornl.gov        -
#    Migrating to DataModelMgr.
#    2016-10-26  leerw@ornl.gov        -
#    Using logging.
#    2016-08-31  leerw@ornl.gov        -
#    Handle 'scale_mode' events.  Cannot get the colormap to update
#    the display in Volume.SetScalarData().  Need to resolve later.
#    2016-08-17  leerw@ornl.gov        -
#    New State events.
#    2016-08-10  leerw@ornl.gov        -
#    Changed _CreateClipboardData() signature.
#    2016-03-08  leerw@ornl.gov        -
# -----------------------------------------------------------------------
import bisect
import functools
import logging
import math
import os
import sys
import numpy as np
import pdb

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError('The wxPython module is required')

from traits.api import HasTraits, Instance, Array, on_trait_change
from traitsui.api import View, Item, HGroup, Group

from tvtk.api import tvtk
from tvtk.pyface.scene import Scene
from tvtk.util import ctf

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel
from mayavi.filters.transform_data import TransformData

from matplotlib import cm, colors

from data.datamodel import *
from event.state import *
from widget.widget import *
from widget.widgetcontainer import *


# -----------------------------------------------------------------------
#  CLASS:    Volume3DView                                            -
# -----------------------------------------------------------------------
class Volume3DView(Widget):
  """ Volume 3D visualization widget.
  """

#    -- Object Methods
#    --
  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.__init__()                              -
  # ---------------------------------------------------------------------
  def __init__(self, container, id=-1, **kwargs):
    self.assemblyAddr = (-1, -1, -1)
    self.axialValue = AxialValue()
    self.coreExtent = None  # left, top, right + 1, bottom + 1, dx, dy
    self.curDataSet = None

    self.isLoaded = False
    self.logger = logging.getLogger('view3d')
    self.meshLevels = None
    self.pinDataSet = kwargs.get('dataset', 'pin_powers')
    self.stateIndex = -1
    self.subAddr = None
    self.timeValue = -1.0

    self.viz = None
    self.vizcontrol = None

    super(Volume3DView, self).__init__(container, id)
  # end __init__

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.CalcSlicePosition()                     -
  # ---------------------------------------------------------------------
  def CalcSlicePosition(self):
    """Calculates viz slice positions from the current state.
    @return      ( z, x, y )
    """
    result = (0, 0, 0)
    core = self.dmgr.GetCore()
    if core and self.meshLevels:
      # -- Data matrix is z, x, y(reversed)
      # --
      # z = self.meshLevels[ self.axialValue[ 1 ] ]
      z = self.meshLevels[self.axialValue.pinIndex]

      assy_col = self.assemblyAddr[1] - self.coreExtent[0]
      # xxxxx channel? track with mode flag?
      x = core.npinx * assy_col + self.subAddr[0]

      assy_row = self.assemblyAddr[2] - self.coreExtent[1]
      # xxxxx channel?
      y = \
          core.npiny * (self.coreExtent[-1] - assy_row) - \
          self.subAddr[1]

      result = (z, x, y)
    # end if core

    return result
  # end CalcSlicePosition

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._Create3DMatrix()                       -
  # ---------------------------------------------------------------------
  def _Create3DMatrix(self):
    matrix = None

    core = self.dmgr.GetCore()
    if core is not None and self.curDataSet and \
            self.coreExtent is not None and \
            (core.npinx > 0 or core.npiny > 0):
      dset = self.dmgr.GetH5DataSet(self.curDataSet, self.timeValue)
      dset_value = np.array(dset)
      dset_shape = dset.shape

      cur_npinx = max(core.npinx, dset_shape[1])
      cur_npiny = max(core.npiny, dset_shape[0])

      if self.logger.isEnabledFor(logging.DEBUG):
        self.logger.debug(
            'curDataSet=%s, stateIndex=%d',
            self.curDataSet, self.stateIndex
        )

      ax_mesh = self.dmgr.GetAxialMesh(self.curDataSet)
      # pin_pitch = 1.26
      pin_pitch = core.GetAssemblyPitch() / max(core.npinx, core.npinx)
      self.meshLevels = [
          int((ax_mesh[i + 1] - ax_mesh[0]) / pin_pitch)
          for i in range(len(ax_mesh) - 1)
      ]
      z_size = self.meshLevels[-1]

      # z, x, y(bottom up)
      # xxxxx +1 on pin ranges if a channel dataset
      matrix = np.ndarray(
          # (z_size, core.npinx * assy_range[5], core.npiny * assy_range[4]),
          (z_size,
              cur_npinx * self.coreExtent[-2],
              cur_npiny * self.coreExtent[-1]),
          np.float64
      )
      matrix.fill(0.0)

      pin_y = 0
      # for assy_y in range( assy_range[ 3 ] - 1, assy_range[ 1 ] - 1, -1 ):
      for assy_y in xrange(self.coreExtent[3] - 1, self.coreExtent[1] - 1, -1):
        pin_x = 0
        # for assy_x in range( assy_range[ 0 ], assy_range[ 2 ] ):
        for assy_x in xrange(self.coreExtent[0], self.coreExtent[2]):
          assy_ndx = core.coreMap[assy_y, assy_x] - 1
          if assy_ndx >= 0:
            for z in xrange(z_size):
              ax_level = min(
                  bisect.bisect_left(self.meshLevels, z),
                  len(self.meshLevels) - 1
              )
              # for y in range( core.npiny ):
              pin_y2 = 0
              for y in xrange(cur_npiny - 1, -1, -1):
                data_y = min(y, dset_shape[0] - 1)

                for x in xrange(cur_npinx):
                  data_x = min(x, dset_shape[1] - 1)
                  matrix[z, pin_x + x, pin_y + pin_y2] = \
                      dset_value[data_y, data_x, ax_level, assy_ndx]
                # end for x
                pin_y2 += 1
              # end for y
            # end for z
          # end if assy_ndx

          pin_x += cur_npinx
        # end for assy_x

        pin_y += cur_npiny
      # end for assy_y
    # end if self.data is not None

    return matrix
  # end _Create3DMatrix

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateClipboardData()                  -
  # ---------------------------------------------------------------------
  def _CreateClipboardData(self, mode='displayed'):
    """Retrieves the data for the state and axial.
    @return      text or None
    """
    return \
        self._CreateClipboardDisplayedData() if mode == 'displayed' else \
        self._CreateClipboardSelectedData()
  # end _CreateClipboardData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateClipboardDisplayedData()         -
  # ---------------------------------------------------------------------
  def _CreateClipboardDisplayedData(self):
    """Retrieves the data for the state and axial.
    @return text or None
    """
    csv_text = None
    matrix = self.viz.GetScalarData()
    if matrix is not None and self.meshLevels is not None:
      csv_text = ''

      z_count = min(matrix.shape[0], len(self.meshLevels))
      for z in range(z_count - 1, -1, -1):
        title = '"Axial=%d"' % self.meshLevels[z]
        csv_text += DataModel.ToCSV(matrix[z], title)
    # end if

    return csv_text
  # end _CreateClipboardDisplayedData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateClipboardImage()                 -
  # ---------------------------------------------------------------------
  def _CreateClipboardImage(self):
    """Retrieves the currently-displayed bitmap.
    @return bitmap or None
    """
    bmap = None

    fd, name = tempfile.mkstemp('.png')
    try:
      os.close(fd)
      if self.CreatePrintImage(name):
        bmap = wx.Image(name, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
    finally:
      os.remove(name)

    return bmap
  # end _CreateClipboardImage

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateClipboardSelectedData()          -
  # ---------------------------------------------------------------------
  def _CreateClipboardSelectedData(self):
    """Retrieves the data for the state, axial, and assembly.
    @return      text or None
    """
    csv_text = None

    valid = False
    matrix = self.viz.GetScalarData()
    if matrix is not None and self.meshLevels is not None:
      valid = self.dmgr.IsValid(
          self.curDataSet,
          assembly_addr=self.assemblyAddr[0],
          axial_level=self.axialValue.pinIndex
      )

    core = self.dmgr.GetCore()
    if valid and core is not None:
      z = self.meshLevels[self.axialValue.pinIndex]

      assy_col = self.assemblyAddr[1] - self.coreExtent[0]
      x = core.npinx * assy_col + self.subAddr[0]

      assy_row = self.assemblyAddr[2] - self.coreExtent[1]
      y = \
          core.npiny * (self.coreExtent[-1] - assy_row) - \
          self.subAddr[1]
      csv_text = '"Axial=%d,Col=%d,Row=%d\n' % (z, x, y)
      csv_text += '%.7g' % matrix[y, z, x, ]
    # end if

    return csv_text
  # end _CreateClipboardSelectedData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateMenuDef()                        -
  # ---------------------------------------------------------------------
  def _CreateMenuDef(self):
    """
    """
    menu_def = super(Volume3DView, self)._CreateMenuDef()
    new_menu_def = \
        [x for x in menu_def if x.get('label') != 'Edit Data Scale...']
    return new_menu_def
  # end _CreateMenuDef

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.CreatePrintImage()                      -
  # ---------------------------------------------------------------------
  def CreatePrintImage(self, file_path, bgcolor=None, hilite=False):
    result = None

    if self.viz is not None:
      scene = self.viz.vscene3d
      scene.mlab.savefig(file_path, figure=scene.mayavi_scene)
      result = file_path

    return result
  # end CreatePrintImage

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._CreateViz()                            -
  # ---------------------------------------------------------------------
  def _CreateViz(self, matrix, drange, coreSym):
    """Builds this wxPython component.
    """
    #    -- Create components
    #    --
    self.viz = Volume(matrix=matrix, dataRange=drange, coreSym=coreSym)
    # Do this to automatically fire state changes on slice position changes
    self.vizcontrol = \
        self.viz.edit_traits(parent=self, kind='subpanel').control

    self.GetSizer().Add(self.vizcontrol, 0, wx.ALL | wx.EXPAND)
  # end _CreateViz

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.GetDataSetTypes()                       -
  # ---------------------------------------------------------------------
  def GetDataSetTypes(self):
    return ['pin']
  # end GetDataSetTypes

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.GetEventLockSet()                       -
  # ---------------------------------------------------------------------
  def GetEventLockSet(self):
    locks = set([
        STATE_CHANGE_axialValue,
        STATE_CHANGE_coordinates,
        STATE_CHANGE_curDataSet,
        STATE_CHANGE_scaleMode,
        STATE_CHANGE_timeValue
    ])
    return locks
  # end GetEventLockSet

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.GetTitle()                              -
  # ---------------------------------------------------------------------
  def GetTitle(self):
    return 'Volume 3D View'
  # end GetTitle

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.GetUsesScaleAndCmap()                   -
  # ---------------------------------------------------------------------
  def GetUsesScaleAndCmap(self):
    """
    Returns:
        boolean: False
    """
    return False
  # end GetUsesScaleAndCmap

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._InitUI()                               -
  # ---------------------------------------------------------------------
  def _InitUI(self):
    """Builds this wxPython component.
    """

    #    -- Lay out
    #    --
    sizer = wx.BoxSizer(wx.VERTICAL)

    self.SetAutoLayout(True)
    self.SetSizer(sizer)
    self.SetMinSize((320, 320))
  # end _InitUI

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.Is3D()                                  -
  # ---------------------------------------------------------------------
  def Is3D(self):
    """
    @return      True
    """
    return True
  # end Is3D

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._LoadDataModel()                        -
  # ---------------------------------------------------------------------
  def _LoadDataModel(self, reason):
    if self.dmgr.HasData() and not self.isLoaded:
      self.isLoaded = True

      if (reason & STATE_CHANGE_curDataSet) > 0:
        self.curDataSet = self._FindFirstDataSet(self.state.curDataSet)

      if (reason & STATE_CHANGE_coordinates) > 0:
        self.assemblyAddr = self.state.assemblyAddr
        self.subAddr = self.state.subAddr

      if (reason & STATE_CHANGE_axialValue) > 0:
        self.axialValue = self.dmgr.\
            GetAxialValue(self.curDataSet, cm=self.state.axialValue.cm)

      if (reason & STATE_CHANGE_timeValue) > 0:
        self.timeValue = self.state.timeValue
        self.stateIndex = self.dmgr.\
            GetTimeValueIndex(self.timeValue, self.curDataSet)

      self.coreExtent = self.dmgr.ExtractSymmetryExtent()
      self._UpdateData()
    # end if
  # end _LoadDataModel

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._LoadDataModel_1()                      -
  # ---------------------------------------------------------------------
  def _LoadDataModel_1(self, reason):
    if self.dmgr.HasData() and not self.isLoaded:
      self.isLoaded = True

      self.curDataSet = self._FindFirstDataSet(self.state.curDataSet)

      self.assemblyAddr = self.state.assemblyAddr
      self.axialValue = self.dmgr.\
          GetAxialValue(self.curDataSet, cm=self.state.axialValue.cm)
      self.coreExtent = self.dmgr.ExtractSymmetryExtent()
      self.stateIndex = self.dmgr.\
          GetTimeValueIndex(self.state.timeValue, self.curDataSet)
      self.subAddr = self.state.subAddr
      self.timeValue = self.state.timeValue

      self._UpdateData()
    # end if
  # end _LoadDataModel_1

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.LoadProps()                             -
  # ---------------------------------------------------------------------
  def LoadProps(self, props_dict):
    """Called to load properties.  This implementation is a noop and should
    be overridden by subclasses.
    @param  props_dict  dict object from which to deserialize properties
    """
    for k in ('assemblyAddr', 'subAddr'):
      if k in props_dict:
        setattr(self, k, props_dict[k])

    super(Volume3DView, self).LoadProps(props_dict)
  # end LoadProps

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.SetDataSet()                            -
  # ---------------------------------------------------------------------
  def SetDataSet(self, qds_name):
    if qds_name != self.curDataSet:
      wx.CallAfter(self.UpdateState, cur_dataset=qds_name)
      self.FireStateChange(cur_dataset=qds_name)
  # end SetDataSet

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.SaveProps()                             -
  # ---------------------------------------------------------------------
  def SaveProps(self, props_dict):
    """Called to save properties.  Subclasses should override calling this
    method via super.SaveProps().
    @param  props_dict  dict object to which to serialize properties
    """
    super(Volume3DView, self).SaveProps(props_dict)

    for k in ('assemblyAddr', 'subAddr'):
      props_dict[k] = getattr(self, k)
  # end SaveProps

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._UpdateData()                           -
  # ---------------------------------------------------------------------
  def _UpdateData(self):
    matrix = self._Create3DMatrix()
    if matrix is not None:
      drange = self.dmgr.GetRange(
          self.curDataSet,
          self.timeValue if self.state.scaleMode == 'state' else -1.0
      )

      if self.viz is None:
        coreSym = self.dmgr.GetCore().coreSym
        self._CreateViz(matrix, drange, coreSym)
      else:
        self.viz.SetScalarData(matrix, drange)

      self._UpdateSlicePositions()
  # end _UpdateData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView._UpdateSlicePositions()                 -
  # ---------------------------------------------------------------------
  def _UpdateSlicePositions(self):
    pos = self.CalcSlicePosition()
    self.viz.UpdateViewPositionChange(pos)
  # end _UpdateSlicePositions

  # ---------------------------------------------------------------------
  #  METHOD:    Volume3DView.UpdateState()                           -
  # ---------------------------------------------------------------------
  def UpdateState(self, **kwargs):
    """
    """
    self._BusyBegin()

    try:
      position_changed = kwargs.get('position_changed', False)
      data_changed = kwargs.get('data_changed', False)

      if 'assembly_addr' in kwargs and \
              kwargs['assembly_addr'] != self.assemblyAddr:
        position_changed = True
        self.assemblyAddr = kwargs['assembly_addr']

      if 'axial_value' in kwargs and \
              kwargs['axial_value'][0] != self.axialValue.cm and \
              self.curDataSet:
        position_changed = True
        self.axialValue = self.dmgr.\
            GetAxialValue(self.curDataSet, cm=kwargs['axial_value'][0])

      if 'data_model_mgr' in kwargs or 'scale_mode' in kwargs:
        data_changed = True

      if 'sub_addr' in kwargs and kwargs['sub_addr'] != self.subAddr:
        position_changed = True
        self.subAddr = self.dmgr.NormalizeSubAddr(kwargs['sub_addr'])

      if 'time_value' in kwargs and \
              kwargs['time_value'] != self.timeValue and \
              self.curDataSet:
        self.timeValue = kwargs['time_value']
        state_index = max(
            0, self.dmgr.GetTimeValueIndex(self.timeValue, self.curDataSet)
        )
        if state_index != self.stateIndex:
          self.stateIndex = state_index
          data_changed = True
      # end if 'time_value' in kwargs

      #    -- Special handling for cur_dataset
      #    --
      if 'cur_dataset' in kwargs and kwargs['cur_dataset'] != self.curDataSet:
        ds_type = self.dmgr.GetDataSetType(kwargs['cur_dataset'])
        if ds_type and ds_type in self.GetDataSetTypes():
          data_changed = True
          self.curDataSet = kwargs['cur_dataset']
          self.axialValue = self.dmgr.\
              GetAxialValue(self.curDataSet, cm=self.axialValue.cm)
          self.stateIndex = max(
              0, self.dmgr.GetTimeValueIndex(self.timeValue, self.curDataSet)
          )
          self.container.GetDataSetMenu().Reset()
          wx.CallAfter(self.container.GetDataSetMenu().UpdateAllMenus)

      if data_changed:
        self._UpdateData()
      elif position_changed:
        self._UpdateSlicePositions()
    # end try

    finally:
      self._BusyEnd()
  # end UpdateState

# end Volume3DView

# -----------------------------------------------------------------------
#  CLASS:    Volume                                                     -
# -----------------------------------------------------------------------
class Volume(HasTraits):

  #      -- Must exist for reference to self.var to invoke _var_default()
  dataSource = Instance(Source)
  otf = Instance(ctf.PiecewiseFunction)
  scalar_field = Instance(PipelineBase)
  full_scalar_field = Instance(PipelineBase)
  full_volume = Instance(PipelineBase)
  chopped_volume = Instance(PipelineBase)
  cutplane_y = Instance(PipelineBase)
  cutplane_x = Instance(PipelineBase)
  cutplane_z = Instance(PipelineBase)
  full_grid = Instance(PipelineBase)
  grid = Instance(PipelineBase)

  vscene3d = Instance(MlabSceneModel, ())

  view = View(
      Group(
          Item(
              'vscene3d',
              editor=SceneEditor(scene_class=MayaviScene),
              height=300, width=300
          ),
          show_labels=False
      ),
      resizable=True
      # title = 'Volume'
  )

  first_view = True

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.__init__()                                       -
  # ---------------------------------------------------------------------
  def __init__(self, **traits):
    super(Volume, self).__init__(**traits)

    # created by traits assignment, as is matrix
    # self.dataRange = [ 0.0, 10.0 ]

    # Slice position variables
    self.slicePosition = [1, 1, 1]
    self.slicePositionListener = None

    # Force creation of volumes, cut planes and underlying data
    self.otf
    self.full_scalar_field
    self.scalar_field
    self.full_volume
    self.chopped_volume
    self.cutplane_y
    self.cutplane_x
    self.cutplane_z
    self.full_grid
    self.grid

    self.logger = logging.getLogger('view3d')

  # end __init__

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._dataSource_default()                            -
  # ---------------------------------------------------------------------
  def _dataSource_default(self):
    """Magically called when self.dataSource first referenced
    """
    matrix = self.matrix
    matrix = np.fliplr(matrix)

    field = mlab.pipeline.scalar_field(
        matrix,
        figure=getattr(self, 'vscene3d').mayavi_scene
    )
    return field
  # end _dataSource_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.display_vscene3d()                               -
  # ---------------------------------------------------------------------
  @on_trait_change('vscene3d.activated')
  def display_vscene3d(self):
    """
    """
    self.vscene3d.mlab.view(10, 70)

    self.vscene3d.scene.background = (0.925, 0.925, 0.925)
    self.vscene3d.scene.interactor.interactor_style = \
        tvtk.InteractorStyleTerrain()
  # end display_vscene3d

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._otf_default()                                   -
  # ---------------------------------------------------------------------
  def _otf_default(self):
    """Magically called when self.otf first referenced
    """
    otf = ctf.PiecewiseFunction()
    otf.add_point(0, 0)
    otf.add_point(self.dataRange[0] - 0.01, 0)
    otf.add_point(self.dataRange[0] + 0.01, 1)
    otf.add_point(self.dataRange[1], 1)

    return otf
  # end _otf_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._scalar_field_default()                          -
  # ---------------------------------------------------------------------
  def _scalar_field_default(self):
    """Magically called when self.scalar_field first referenced
    """
    matrix = self.matrix
    scalar_field = None

    if self.coreSym == 4:
      # Quarter core
      matrix = np.fliplr(matrix)
      scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )
    elif self.coreSym == 1:
      # Full core
      shape = matrix.shape
      matrix = matrix[:shape[0] / 2, :shape[1] / 2, :shape[2] / 2]
      scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )

    return scalar_field
  # end _scalar_field_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._full_scalar_field_default()                     -
  # ---------------------------------------------------------------------
  def _full_scalar_field_default(self):
    """Magically called when self.full_scalar_field first referenced
    """
    scalar_field = None

    if self.coreSym == 4:
      # Quarter core
      matrix = np.concatenate((self.matrix,
                               self.matrix[:, :, ::-1]), 2)
      matrix2 = np.concatenate((np.fliplr(self.matrix),
                                np.fliplr(self.matrix)[:, :, ::-1]), 2)
      matrix = np.concatenate((matrix2, matrix), 1)

      scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )
    elif self.coreSym == 1:
      # Full core
      scalar_field = mlab.pipeline.scalar_field(
          self.matrix,
          figure=self.vscene3d.mayavi_scene
      )

    return scalar_field
  # end _full_scalar_field_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._grid_default()                                  -
  # ---------------------------------------------------------------------
  def _grid_default(self):
    """Magically called when self.grid first referenced
    """
    grid = mlab.pipeline.extract_grid(self.scalar_field)

    return grid
  # end _grid_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._full_grid_default()                             -
  # ---------------------------------------------------------------------
  def _full_grid_default(self):
    """Magically called when self.full_grid first referenced
    """
    grid = mlab.pipeline.extract_grid(self.full_scalar_field)

    return grid
  # end _full_grid_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._full_volume_default()                           -
  # ---------------------------------------------------------------------
  def _full_volume_default(self):
    """Magically called when self.full_volume first referenced
    """
    grid = self.full_grid

    y_min = 0
    if self.coreSym == 4:
      y_min = self.matrix.shape[1] + 2
    elif self.coreSym == 1:
      y_min = (self.matrix.shape[1] / 2) + 2
    grid.trait_set(y_min=y_min)

    volume = mlab.pipeline.volume(
        grid,
        figure=self.vscene3d.mayavi_scene,
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    volume._otf = self.otf
    volume._volume_property.set_scalar_opacity(self.otf)

    return volume
  # end _full_volume_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._chopped_volume_default()                        -
  # ---------------------------------------------------------------------
  def _chopped_volume_default(self):
    """Magically called when self.chopped_volume first referenced
    """
    grid = self.grid
    grid.trait_set(x_max=self.slicePosition[1])

    volume = mlab.pipeline.volume(
        grid,
        figure=self.vscene3d.mayavi_scene,
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    volume._otf = self.otf
    volume._volume_property.set_scalar_opacity(self.otf)

    return volume
  # end _chopped_volume_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._cutplane_x_default()                            -
  # ---------------------------------------------------------------------
  def _cutplane_x_default(self):
    """Magically called when self.cutplane_x first referenced
    """
    slice_index = self.slicePosition[0]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='x_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    return plane
  # end _cutplane_x_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._cutplane_y_default()                            -
  # ---------------------------------------------------------------------
  def _cutplane_y_default(self):
    """Magically called when self.cutplane_y first referenced
    """
    slice_index = 0
    if self.coreSym == 4:
      # Quarter core
      slice_index = self.matrix.shape[1]
    elif self.coreSym == 1:
      # Full core
      slice_index = self.matrix.shape[1] / 2

    plane = mlab.pipeline.image_plane_widget(
        self.full_scalar_field,
        plane_orientation='y_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    return plane
  # end _cutplane_y_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume._cutplane_z_default()                            -
  # ---------------------------------------------------------------------
  def _cutplane_z_default(self):
    """Magically called when self.cutplane_z first referenced
    """
    slice_index = self.matrix.shape[2]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='z_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    return plane
  # end _cutplane_z_default

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.GetScalarData()                                  -
  # ---------------------------------------------------------------------
  def GetScalarData(self):
    return  \
        self.dataSource.scalar_data \
        if self.dataSource is not None else \
        None
  # end GetScalarData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.GetSlicePosition()                               -
  # ---------------------------------------------------------------------
  def GetSlicePosition(self):
    return self.slicePosition
  # end GetSlicePosition

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.GetSlicePositionListener()                       -
  # ---------------------------------------------------------------------
  def GetSlicePositionListener(self):
    return self.slicePositionListener
  # end GetSlicePositionListener

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.SetScalarData()                                  -
  # ---------------------------------------------------------------------
  def SetScalarData(self, matrix, data_range):

    self.matrix = matrix
    self.dataRange = data_range

    d = self.dataSource
    d.scalar_data = matrix
    d.data_changed = True
    d.update()

    vol = getattr(self, 'chopped_volume')
    # vol.module_manager.scalar_lut_manager.data_range = data_range
    # vol.module_manager.update()
    # vol._ctf.range = data_range
    # vol.update_ctf = True
    vol.lut_manager.data_range = data_range
    vol.update_pipeline()

    self.UpdateViewDataChange()
  # end SetScalarData

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.SetSlicePositionListener()                       -
  # ---------------------------------------------------------------------
  def SetSlicePositionListener(self, listener):
    """
    @param  listener  func( slice_position ), can be None
    """
    self.slicePositionListener = listener
  # end SetSlicePositionListener

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateScalarField()                              -
  # ---------------------------------------------------------------------
  def UpdateScalarField(self):
    matrix = self.matrix
    scalar_field = None
    z_max = 0

    if self.coreSym == 4:
      # Quarter core
      matrix = np.fliplr(matrix)
      matrix = matrix[0:self.slicePosition[0], :, :]

      scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )
      z_max = self.matrix.shape[2] - 3

    elif self.coreSym == 1:
      # Full core
      shape = matrix.shape
      matrix = matrix[:shape[0] / 2, :shape[1] / 2, :shape[2] / 2]
      scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )
      z_max = (self.matrix.shape[2] / 2) - 3

    self.scalar_field = scalar_field

    # Update the grid as well
    self.grid = mlab.pipeline.extract_grid(self.scalar_field)
    self.grid.trait_set(x_max=self.slicePosition[0] - 3,
                        z_max=z_max)

  # end UpdateScalarField

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateFullScalarField()                          -
  # ---------------------------------------------------------------------
  def UpdateFullScalarField(self):
    full_scalar_field = None

    if self.coreSym == 4:
      # Quarter core
      matrix = np.concatenate((self.matrix,
                               self.matrix[:, :, ::-1]), 2)
      matrix2 = np.concatenate((np.fliplr(self.matrix),
                                np.fliplr(self.matrix)[:, :, ::-1]), 2)
      matrix = np.concatenate((matrix2, matrix), 1)

      full_scalar_field = mlab.pipeline.scalar_field(
          matrix,
          figure=self.vscene3d.mayavi_scene
      )
    elif self.coreSym == 1:
      # Full core
      full_scalar_field = mlab.pipeline.scalar_field(
          self.matrix,
          figure=self.vscene3d.mayavi_scene
      )

    self.full_scalar_field = full_scalar_field

    # Update the grid as well
    self.full_grid = mlab.pipeline.extract_grid(self.full_scalar_field)

  # end UpdateFullScalarField

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateCutPlaneX()                                -
  # ---------------------------------------------------------------------
  def UpdateCutPlaneX(self):
    # Update the movable cut plane
    # self.cutplane_x.implicit_plane.origin = (
    #     (self.slicePosition[0],
    #      self.slicePosition[1],
    #      self.slicePosition[2])
    # )

    self.cutplane_x.remove()

    slice_index = self.slicePosition[0]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='x_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    plane.ipw.interaction = 0

    self.cutplane_x = plane

  # end UpdateCutPlaneX

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateCutPlaneZ()                                -
  # ---------------------------------------------------------------------
  def UpdateCutPlaneZ(self):
    self.cutplane_z.remove()

    # threshold = mlab.pipeline.threshold(self.scalar_field,
    #                                     low=self.dataRange[0])

    # plane = mlab.pipeline.scalar_cut_plane(threshold,
    #                                        plane_orientation='z_axes',
    #                                        colormap='jet',
    #                                        view_controls=False,
    #                                        vmin=self.dataRange[0],
    #                                        vmax=self.dataRange[1])
    # plane.implicit_plane.origin = (0, 0, self.matrix.shape[2])
    # plane.implicit_plane.widget.enabled = False

    slice_index = self.matrix.shape[2]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='z_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    plane.ipw.interaction = 0

    self.cutplane_z = plane

  # end UpdateCutPlaneZ

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.ResetCutPlaneX()                                 -
  # ---------------------------------------------------------------------
  def ResetCutPlaneX(self):
    self.cutplane_x.remove()

    # threshold = mlab.pipeline.threshold(self.scalar_field,
    #                                     low=self.dataRange[0])

    # plane = mlab.pipeline.scalar_cut_plane(threshold,
    #                                        plane_orientation='x_axes',
    #                                        colormap='jet',
    #                                        view_controls=False,
    #                                        vmin=self.dataRange[0],
    #                                        vmax=self.dataRange[1])

    # plane.implicit_plane.origin = (self.slicePosition[0],
    #                                self.slicePosition[1],
    #                                self.slicePosition[2])
    # plane.implicit_plane.widget.enabled = False

    slice_index = self.slicePosition[0]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='x_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    plane.ipw.interaction = 0

    self.cutplane_x = plane

  # end ResetCutPlaneX

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.ResetCutPlaneY()                                 -
  # ---------------------------------------------------------------------
  def ResetCutPlaneY(self):
    self.cutplane_y.remove()

    # threshold = mlab.pipeline.threshold(self.full_scalar_field,
    #                                     low=self.dataRange[0])

    # plane = mlab.pipeline.scalar_cut_plane(threshold,
    #                                        plane_orientation='y_axes',
    #                                        colormap='jet',
    #                                        view_controls=False,
    #                                        vmin=self.dataRange[0],
    #                                        vmax=self.dataRange[1])
    # plane.implicit_plane.origin = (0, self.matrix.shape[1], 0)
    # plane.implicit_plane.widget.enabled = False

    slice_index = 0
    if self.coreSym == 4:
      # Quarter core
      slice_index = self.matrix.shape[1]
    elif self.coreSym == 1:
      # Full core
      slice_index = self.matrix.shape[1] / 2

    plane = mlab.pipeline.image_plane_widget(
        self.full_scalar_field,
        plane_orientation='y_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    plane.ipw.interaction = 0

    self.cutplane_y = plane

  # end ResetCutPlaneY

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.ResetCutPlaneZ()                                 -
  # ---------------------------------------------------------------------
  def ResetCutPlaneZ(self):
    self.cutplane_z.remove()

    # threshold = mlab.pipeline.threshold(self.scalar_field,
    #                                     low=self.dataRange[0])

    # plane = mlab.pipeline.scalar_cut_plane(threshold,
    #                                        plane_orientation='z_axes',
    #                                        colormap='jet',
    #                                        view_controls=False,
    #                                        vmin=self.dataRange[0],
    #                                        vmax=self.dataRange[1])
    # plane.implicit_plane.origin = (0, 0, self.matrix.shape[2])
    # plane.implicit_plane.widget.enabled = False

    slice_index = self.matrix.shape[2]

    plane = mlab.pipeline.image_plane_widget(
        self.scalar_field,
        plane_orientation='z_axes',
        slice_index=slice_index,
        colormap='jet',
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    plane.ipw.interaction = 0

    self.cutplane_z = plane

  # end ResetCutPlaneZ

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateVolumes()                                  -
  # ---------------------------------------------------------------------
  def UpdateFullVolume(self):
    # Update the full volume
    self.full_volume.remove()
    grid = self.full_grid

    y_min = 0
    if self.coreSym == 4:
      y_min = self.matrix.shape[1] + 2
    elif self.coreSym == 1:
      y_min = (self.matrix.shape[1] / 2) + 2
    grid.trait_set(y_min=y_min)

    volume = mlab.pipeline.volume(
        grid,
        figure=self.vscene3d.mayavi_scene,
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )
    volume.update_ctf = True
    volume._otf = self.otf
    volume._volume_property.set_scalar_opacity(self.otf)
    self.full_volume = volume

  # end UpdateFullVolume

  def UpdateChoppedVolume(self):
    # Update the chopped volume
    self.chopped_volume.remove()
    grid = self.grid
    # grid.trait_set(x_max=self.slicePosition[0] - 3,
    #                z_max=self.matrix.shape[2] - 3)
    volume = mlab.pipeline.volume(
        grid,
        figure=self.vscene3d.mayavi_scene,
        vmin=self.dataRange[0],
        vmax=self.dataRange[1]
    )

    volume.update_ctf = True
    volume._otf = self.otf
    volume._volume_property.set_scalar_opacity(self.otf)
    self.chopped_volume = volume

  # end UpdateChoppedVolume

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateViewPositionChange()                       -
  # ---------------------------------------------------------------------
  def UpdateViewPositionChange(self, position):
    if self.logger.isEnabledFor(logging.DEBUG):
      self.logger.debug('position=%s', str(position))

    previous_position = self.slicePosition
    self.slicePosition = position

    # Check for new slice position
    if not previous_position[0] == position[0]:
      self.UpdateScalarField()
      self.UpdateChoppedVolume()
      self.UpdateCutPlaneX()
      self.UpdateCutPlaneZ()

    # Ensure the cut planes are not movable
    # self.cutplane_x.implicit_plane.widget.enabled = False
    # self.cutplane_y.implicit_plane.widget.enabled = False
    # self.cutplane_z.implicit_plane.widget.enabled = False

    # Set initial camera angle
    if self.first_view:
      mlab.view(120, -45, 900)
      mlab.roll(75)
      self.first_view = False

  # end UpdateViewPositionChange

  # ---------------------------------------------------------------------
  #  METHOD:    Volume.UpdateViewDataChange()                           -
  # ---------------------------------------------------------------------
  def UpdateViewDataChange(self):
    self.UpdateScalarField()
    self.UpdateChoppedVolume()
    self.UpdateFullScalarField()
    self.UpdateFullVolume()
    self.ResetCutPlaneX()
    self.ResetCutPlaneY()
    self.ResetCutPlaneZ()

  # end UpdateViewDataChange

# end Volume
