"""
Example of an elaborate dialog showing a multiple views on the same data, with
3 cuts synchronized.

This example shows how to have multiple views on the same data, how to
embedded multiple scenes in a dialog, and the caveat in populating them
with data, as well as how to add some interaction logic on an
ImagePlaneWidget.

The order in which things happen in this example is important, and it is
easy to get it wrong. First of all, many properties of the visualization
objects cannot be changed if there is not a scene created to view them.
This is why we put a lot of the visualization logic in the callback of
scene.activated, which is called after creation of the scene.
Second, default values created via the '_xxx_default' callback are created
lazyly, that is, when the attributes are accessed. As the establishement
of the VTK pipeline can depend on the order in which it is built, we
trigger these access by explicitely calling the attributes.
In particular, properties like scene background color, or interaction
properties cannot be set before the scene is activated.

The same data is exposed in the different scenes by sharing the VTK
dataset between different Mayavi data sources. See
the :ref:`sharing_data_between_scenes` tip for more details.

In this example, the interaction with the scene and the various elements
on it is strongly simplified by turning off interaction, and choosing
specific scene interactor styles. Indeed, non-technical users can be
confused with too rich interaction.
"""
# Author: Gael Varoquaux <gael.varoquaux@normalesup.org>
# Copyright (c) 2009, Enthought, Inc.
# License: BSD Style.

#------------------------------------------------------------------------
#	Update after changing data in a file
#source.base_file_name = filename
## Force re-read.
#source.reader.modified()
#source.update()
## Propagate changes in the pipeline.
#source.data_changed = True
#------------------------------------------------------------------------


import bisect, functools, os, sys, time
os.environ[ 'ETS_TOOLKIT' ] = 'wx'

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )
from data.datamodel import *

try:
  #import wxversion
  #wxversion.ensureMinimal( '3.0' )
  import wx
  #import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

start = time.time()
print "importing h5py"
import h5py
print "importing numpy"
import numpy as np

print "importing traits.api"
from traits.api import HasTraits, Instance, Array, \
    on_trait_change
print "importing traitsui.api"
from traitsui.api import View, Item, HGroup, Group

print "importing tvtk.api"
from tvtk.api import tvtk
print "importing tvtk.pyface.scene"
from tvtk.pyface.scene import Scene

print "importing mayavi"
from mayavi import mlab
print "importing mayavi.core.api"
from mayavi.core.api import PipelineBase, Source
print "importing mayavi.core.ui.api"
from mayavi.core.ui.api import SceneEditor, MayaviScene, \
                                MlabSceneModel
end = time.time()
print "finished importing in %f secs" % (end - start)



def get_matrix(size_x, size_y, size_z, det_dat):
    matrix = [[[0 for x in range(size_x)] for y in range(size_y)] for z in range(size_z)];
    for z in range(0, size_z):
        for y in range(0, size_y):
            for x in range(0, size_x):
                matrix[z][y][x] = det_dat[x][y][z][35]
    return matrix;

def get_big_matrix(det_dat, core_map):
    #size_assm = len(det_dat[0][0][0]);
    size_z = len(det_dat[0][0])
    size_y = len(det_dat[0])
    size_x = len(det_dat) 
    size_macro_full = len(core_map)
    #print size_macro_full
    size_macro = (len(core_map) + 1) / 2
    #print size_macro
    size_x_macro = size_x * size_macro
    size_y_macro = size_y * size_macro

    #size_z_2 = mesh_factor[len(mesh_factor) - 1]    
    #print len(matrix[0][0])
    #print  len(matrix[0])
    #print len(matrix) 
    
    
    matrix = [[[0 for x in range(size_x_macro)] for y in range(size_y_macro)] for z in range(size_z)]
    for i in range(size_macro - 1, size_macro_full):
        for j in range(size_macro - 1, size_macro_full):
            assm_number = core_map[i][j]
            if(assm_number != 0):
                for z in range(0, size_z):
                    for y in range(0, size_y):
                        for x in range(0, size_x):
                            x_index = (i - (size_macro - 1)) * size_x + x
                            y_index = (j - (size_macro - 1)) * size_y + y
                            matrix[z][x_index][y_index] = det_dat[x][y][z][assm_number - 1]
    
                        
    return matrix


def get_cut_matrix(det_dat, core_map, mesh_factor):
    #size_assm = len(det_dat[0][0][0]);
    npinx = det_dat.shape[ 1 ]
    npiny = det_dat.shape[ 0 ]
    nax = det_dat.shape[ 2 ]
    nassy = core_map.shape[ 0 ]
    nassx = core_map.shape[ 1 ]
    #data_model.ExtractSymmetryExtent() # left, top, right + 1, bottom + 1, dx, dy

    size_z = nax  # len(det_dat[0][0])
    size_y = npinx  # len(det_dat[0])
    size_x = npiny  # len(det_dat) 
    size_macro_full = nassx  # len(core_map)
    size_macro = (nassx + 1) / 2  # (len(core_map) + 1) / 2
    size_x_macro = size_x * size_macro
    size_y_macro = size_y * size_macro

    size_z_2 = mesh_factor[len(mesh_factor) - 1]    
    #print len(matrix[0][0])
    #print  len(matrix[0])
    #print len(matrix) 

    matrix = [[[0 for x in range(size_x_macro)] for y in range(size_y_macro)] for z in range(size_z_2)]
    for i in range(size_macro - 1, size_macro_full):
        for j in range(size_macro - 1, size_macro_full):
            assm_number = core_map[i][j]
            if(assm_number != 0):
                for z in range(0, size_z_2):
                    for y in range(0, size_y):
                        for x in range(0, size_x):
                            x_index = (i - (size_macro - 1)) * size_x + x
                            y_index = (j - (size_macro - 1)) * size_y + y
                            z_real = layer_number(z, mesh_factor)
                            matrix[z][x_index][y_index] = det_dat[x][y][z_real][assm_number - 1]
                        
    return matrix


def arrays_for_contour(matrix, core_map, det_dat, ax_mesh):
    x_array = []
    y_array = []
    z_array = []
    k_array = []
    size_macro_full = len(core_map)
    size_macro = (len(core_map) + 1) / 2
    
    size_micro = len(det_dat) 
    size_x = len(matrix[0][0])
    size_y = len(matrix[0])
    size_z = len(matrix)     
    
    #construct z covers
    for i in range(size_macro - 1, size_macro_full):
        for j in range(size_macro - 1, size_macro_full):
            if(core_map[i][j] == 0):
                break;
            #add top and bottom covers
            y_start = size_micro * (i - (size_macro - 1))
            x_start = size_micro * (j - (size_macro - 1))
            for x in range(x_start, x_start + size_micro):
                for y in range(y_start, y_start + size_micro):
                    x_array.append(x)
                    y_array.append(y)
                    z_array.append(0)
                    k_array.append(matrix[0][y][x])
                    
                    x_array.append(x)
                    y_array.append(y)
                    z_index = int(ax_mesh[size_z]/1.26)
                    z_array.append(z_index)
                    k_array.append(matrix[size_z - 1][y][x])
    
    #construct x and y cover
    for i in range(size_macro - 1, size_macro_full):
        #construct y cover        
        if(core_map[i][size_macro - 1] != 0):
            y_start = size_micro * (i - (size_macro - 1))
            for y in range(y_start, y_start + size_micro):
                for z in range(0, size_z):
                    x_array.append(0)
                    y_array.append(y)
                    z_index = int(ax_mesh[z]/1.26)
                    z_array.append(z_index)
                    k_array.append(matrix[z][y][0])
        #construct x cover
        if(core_map[size_macro - 1][i] != 0):
            x_start = size_micro * (i - (size_macro - 1))
            for x in range(x_start, x_start + size_micro):
                for z in range(0, size_z):
                    x_array.append(x)
                    y_array.append(0)
                    z_index = int(ax_mesh[z]/1.26)
                    z_array.append(z_index)
                    k_array.append(matrix[z][0][x])
            
    
    #get right side on the zig zag
    for i in range(size_macro - 1, size_macro_full):
        for j in range(size_macro - 1, size_macro_full):
            if((core_map[i][j] == 0) and j == (size_macro - 1)):
                break
            if(core_map[i][j] == 0):
                x_pos = size_micro * (j - (size_macro - 1)) - 1
                y_start = size_micro * (i - (size_macro - 1))
                for z in range(0, size_z):
                    for y in range(y_start, y_start + size_micro):
                        x_array.append(x_pos)
                        y_array.append(y)
                        z_index = int(ax_mesh[z]/1.26)
                        z_array.append(z_index)
                        k_array.append(matrix[z][y][x_pos])
                break;
            if((j == size_macro_full - 1) and core_map[i][j] != 0):
                x_pos = size_micro * (j - (size_macro - 1) + 1) - 1
                y_start = size_micro * (i - (size_macro - 1))
                for z in range(0, size_z):
                    for y in range(y_start, y_start + size_micro):
                        x_array.append(x_pos)
                        y_array.append(y)
                        z_index = int(ax_mesh[z]/1.26)
                        z_array.append(z_index)
                        k_array.append(matrix[z][y][x_pos])
                break;
            #print core_map[i][j]
    #get bottom side on the zig zag
    for j in range(size_macro - 1, size_macro_full):
        for i in range(size_macro - 1, size_macro_full):
            if((core_map[i][j] == 0) and i == (size_macro - 1)):
                break
            if(core_map[i][j] == 0):
                y_pos = size_micro * (i - (size_macro - 1)) - 1
                x_start = size_micro * (j - (size_macro - 1))
                for z in range(0, size_z):
                    for x in range(x_start, x_start + size_micro):
                        x_array.append(x)
                        y_array.append(y_pos)
                        z_index = int(ax_mesh[z]/1.26)
                        z_array.append(z_index)
                        k_array.append(matrix[z][y_pos][x])
                break;
            if((i == size_macro_full - 1) and core_map[i][j] != 0):
                y_pos = size_micro * (i - (size_macro - 1) + 1) - 1
                x_start = size_micro * (j - (size_macro - 1))
                for z in range(0, size_z):
                    for x in range(x_start, x_start + size_micro):
                        x_array.append(x)
                        y_array.append(y_pos)
                        z_index = int(ax_mesh[z]/1.26)
                        z_array.append(z_index)
                        k_array.append(matrix[z][y_pos][x])
                break;
    return x_array, y_array, z_array, k_array;
    

def layer_number(height, mesh_factor):
    #could be used for both factor height and number height
    for i in range(0, len(mesh_factor)):
        if(height < mesh_factor[i]):
            return i;
    return len(mesh_factor) - 1;

def get_mesh_factor(ax_mesh, ppinch):
    mesh_factor = [0 for x in range(len(ax_mesh) - 1)]
    for i in range(0, len(ax_mesh) - 1):
        mesh_factor[i] = int((ax_mesh[i + 1] - ax_mesh[0])/ppinch)
    return mesh_factor



def create_cut_matrix( data_model, ds_name, state_ndx ):
  core = data_model.GetCore()
  dset = data_model.GetStateDataSet( state_ndx, ds_name )
  dset_value = dset.value
  assy_range = data_model.ExtractSymmetryExtent() # left, top, right + 1, bottom + 1, dx, dy

  ax_mesh = core.axialMesh
  #ppinch = core.apitch if core.apitch > 0 else 1.0
  ppinch = 1.26
  mesh_factors = [
      int( (ax_mesh[ i + 1 ] - ax_mesh[ 0 ]) / ppinch )
      for i in range( len( ax_mesh ) - 1 )
      ]
  z_size = mesh_factors[ -1 ]

  matrix = np.ndarray(
#yx	( z_size, core.npiny * assy_range[ 4 ], core.npinx * assy_range[ 5 ] ),
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
	  ax_level = min( bisect.bisect_left( mesh_factors, z ), len( mesh_factors ) - 1 )
	  for y in range( core.npiny ):
	    for x in range( core.npinx ):
	      matrix[ z, pin_x + x, pin_y + y ] = \
	          dset_value[ y, x, ax_level, assy_ndx ]
#yx	      matrix[ z, pin_y + y, pin_x + x ] = \
#yx	          dset_value[ y, x, ax_level, assy_ndx ]
	    #end for x
	  #end for y
	#end for z
      #end if assy_ndx

      pin_x += core.npinx
    #end for assy_x

    pin_y += core.npiny
  #end for assy_y

  #return  matrix.tolist()
  return  matrix
#end create_cut_matrix



################################################################################
# Create some data
#x, y, z = np.ogrid[-5:5:64j, -5:5:64j, -5:5:64j]
#myh5 = h5py.File("beavrs_cy1.h5")
if False:
  myh5 = h5py.File("/Users/re7x/study/casl/andrew/beavrs.h5")
  det_dat = myh5["/STATE_0001/pin_powers"].value
  core_map = myh5["/CORE/core_map"].value
  ax_mesh = myh5["/CORE/axial_mesh"].value
  mesh_factor = get_mesh_factor(ax_mesh, 1.26)
#print ax_mesh
#data = np.sin(3*x)/x + 0.05*z**2 + np.cos(3*y)
  data = get_cut_matrix(det_dat, core_map, mesh_factor)
#x data2 = get_big_matrix(det_dat, core_map)
#print core_map
#data2 = get_matrix(17, 17, 48, det_dat)
#data = get_matrix(17, 17, 48, det_dat)

else:
  data_model = DataModel( '/Users/re7x/study/casl/andrew/beavrs.h5' )
  data = create_cut_matrix( data_model, 'pin_powers', 0 )


################################################################################
# The object implementing the dialog
class VolumeSlicer(HasTraits):
    # The data to plot
    
    ## position = Array( shape = ( 3, ) )

    #data = Array()  #not necessary?

    # The 4 views displayed
    #x sceneReal = Instance(MlabSceneModel, ())
    scene3d = Instance(MlabSceneModel, ())
    sceneCut = Instance(MlabSceneModel, ())
    scene_x = Instance(MlabSceneModel, ())
    scene_y = Instance(MlabSceneModel, ())
    scene_z = Instance(MlabSceneModel, ())

    # The data source
    # this must exist for reference to
    #   self.data_src3d to invoke _data_src3d_default()
    data_src3d = Instance(Source)

    # The image plane widgets of the 3D scene
    # these must exist for default mechanism to work
    ipw_3d_x = Instance(PipelineBase)
    ipw_3d_y = Instance(PipelineBase)
    ipw_3d_z = Instance(PipelineBase)

    _axis_names = dict(x=0, y=1, z=2)


    #---------------------------------------------------------------------------
    def __init__(self, **traits):
        super(VolumeSlicer, self).__init__(**traits)
        # Force the creation of the image_plane_widgets
	# xxx these call _ipw_3d_?_default()
        self.ipw_3d_x
        self.ipw_3d_y
        self.ipw_3d_z


    #---------------------------------------------------------------------------
    # Default values
    #---------------------------------------------------------------------------
    def _data_src3d_default(self):
	# called once, in first make_ipw_3d() call from _ipw_3d_x_default()
        return mlab.pipeline.scalar_field(self.data,
                            figure=self.scene3d.mayavi_scene)

    def make_ipw_3d(self, axis_name):
        ipw = mlab.pipeline.image_plane_widget(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        plane_orientation='%s_axes' % axis_name,
			name = 'Cut %s' % axis_name,
			vmin = self.data_range[ 0 ],
			vmax = self.data_range[ 1 ]
			)
	#ipw.module_manager.scalar_lut_manager.use_default_range = False
	#ipw.module_manager.scalar_lut_manager.data_range = self.data_range
        return ipw

##    def _position_default( self ):
 ##     return  0.5 * np.array( self.data_src3d.shape )

    def _ipw_3d_x_default(self):
        return self.make_ipw_3d('x')

    
    def _ipw_3d_y_default(self):
        return self.make_ipw_3d('y')

    def _ipw_3d_z_default(self):
        return self.make_ipw_3d('z')


    #---------------------------------------------------------------------------
    # Scene activation callbaks
    #---------------------------------------------------------------------------
    
    @on_trait_change('sceneReal.activated')
    def display_sceneReal(self):
	"""Not used"""
        x, y, z, k = arrays_for_contour(data2, core_map, det_dat, ax_mesh)
        outline = mlab.points3d(x, y, z, k, scale_mode = "none", vmin = 0, vmax = 2.5)
        self.sceneReal.mlab.view(40, 50)
        
        # Interaction properties can only be changed after the scene
        # has been created, and thus the interactor exists
    
        
    
    @on_trait_change('sceneCut.activated')
    def display_sceneCut(self):
        #outline = mlab.points3d(data2, scale_mode = "none")
        scene = getattr(self, 'scene_%s' % 'y')

        # To avoid copying the data, we take a reference to the
        # raw VTK dataset, and pass it on to mlab. Mlab will create
        # a Mayavi source from the VTK without copying it.
        # We have to specify the figure so that the data gets
        # added on the figure we are interested in.
        outline = mlab.pipeline.outline(
                            self.data_src3d.mlab_source.dataset,
                            figure=self.scene3d.mayavi_scene,
                            )
        ipw = mlab.pipeline.image_plane_widget(
                            outline,
                            plane_orientation='%s_axes' % 'y')
        setattr(self, 'ipw_%s' % 'y', ipw)

        # Synchronize positions between the corresponding image plane
        # widgets on different views.

        # Make left-clicking create a crosshair
        # Add a callback on the image plane widget interaction to
        # move the others

        # Center the image plane widget

        # Position the view for the scene
        views = dict(x=( 0, 90),
                     y=(90, 90),
                     z=( 0,  0),
                     )
        # 2D interaction: only pan and zoom
        scene.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleImage()
        self.sceneCut.scene.background = (0, 0, 0)    
    
    
    @on_trait_change('scene3d.activated')
    def display_scene3d(self):
        #outline = mlab.points3d(data2, scale_mode = "none")
        
#        outline = mlab.pipeline.outline(self.data_src3d,
#                        figure=self.scene3d.mayavi_scene,
#                        )
        
        ##self.scene3d.mlab.view(40, 50)
        #self.scene3d.mlab.view(10, 60)
        self.scene3d.mlab.view(10, 70)
        
        # Interaction properties can only be changed after the scene
        # has been created, and thus the interactor exists
        
        for ipw in (self.ipw_3d_x, self.ipw_3d_y, self.ipw_3d_z):
            # Turn the interaction off
            ipw.ipw.interaction = 0
        
        
        self.scene3d.scene.background = (0, 0, 0)
        # Keep the view always pointing up
        self.scene3d.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleTerrain()

	## refer to Examples/mayavi-4.2.0/mayavi/interactive/volume_slicer_advanced.py
        ## self.update_position()


    

    def make_side_view(self, axis_name):
	print >> sys.stderr, '[X.4 make_side_view] axis_name=', axis_name
        scene = getattr(self, 'scene_%s' % axis_name)

        # To avoid copying the data, we take a reference to the
        # raw VTK dataset, and pass it on to mlab. Mlab will create
        # a Mayavi source from the VTK without copying it.
        # We have to specify the figure so that the data gets
        # added on the figure we are interested in.
        outline = mlab.pipeline.outline(
                            self.data_src3d.mlab_source.dataset,
                            figure=scene.mayavi_scene,
                            )
        ipw = mlab.pipeline.image_plane_widget(
                            outline,
                            plane_orientation='%s_axes' % axis_name,
			    vmin = self.data_range[ 0 ],
			    vmax = self.data_range[ 1 ]
			    )
	#ipw.module_manager.scalar_lut_manager.use_default_range = False
	#ipw.module_manager.scalar_lut_manager.data_range = self.data_range
        setattr(self, 'ipw_%s' % axis_name, ipw)

        # Synchronize positions between the corresponding image plane
        # widgets on different views.
        ipw.ipw.sync_trait('slice_position',
                            getattr(self, 'ipw_3d_%s'% axis_name).ipw)

        # Make left-clicking create a crosshair
        ipw.ipw.left_button_action = 0
        # Add a callback on the image plane widget interaction to
        # move the others
        def move_view(obj, evt):
            position = obj.GetCurrentCursorPosition()
	    print >> sys.stderr, \
	        '[move_view] axis=' + axis_name + ', position=' + str(position)
            for other_axis, axis_number in self._axis_names.iteritems():
                if other_axis == axis_name:
                    continue
                ipw3d = getattr(self, 'ipw_3d_%s' % other_axis)
                ipw3d.ipw.slice_position = position[axis_number]

        ipw.ipw.add_observer('InteractionEvent', move_view)
        ipw.ipw.add_observer('StartInteractionEvent', move_view)

        # Center the image plane widget
        ipw.ipw.slice_position = 0.5*self.data.shape[
                    self._axis_names[axis_name]]

        # Position the view for the scene
        views = dict(x=( 0, 90),
                     y=(90, 90),
                     z=( 0,  0),
                     )
        scene.mlab.view(*views[axis_name])
        # 2D interaction: only pan and zoom
        scene.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleImage()
        scene.scene.background = (0, 0, 0)
	if axis_name == 'x':
	  scene.scene.parallel_projection = True
	  scene.scene.camera.parallel_scale = \
	      0.4 * np.mean( self.data_src3d.scalar_data.shape )


    @on_trait_change('scene_x.activated')
    def display_scene_x(self):
        return self.make_side_view('x')

    @on_trait_change('scene_y.activated')
    def display_scene_y(self):
        return self.make_side_view('y')

    @on_trait_change('scene_z.activated')
    def display_scene_z(self):
        return self.make_side_view('z')


    #---------------------------------------------------------------------------
    # The layout of the dialog created
    #---------------------------------------------------------------------------
    view = View(HGroup(
                  Group(
                       Item('scene_y',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       Item('scene_z',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       Item('scene_x',
                            editor=SceneEditor(scene_class=Scene),
                            height=250, width=300),
                       show_labels=False,
                  ),
                  Group(
                       Item('scene3d',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=300, width=300),  # 250, 300
                       Item('sceneCut',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=200, width=300),  # 250, 300
                       show_labels=False,
                  )
#x                  Group(
#x                       Item('sceneReal',
#x                            editor=SceneEditor(scene_class=MayaviScene),
#x                            height=250, width=300),
#x                       show_labels=False,
#x                  )
                  
                ),
                resizable=True,
                title='Volume Slicer'
                )



class MainWindow( wx.Frame ):

  def __init__( self, data_model, data ):
    super( MainWindow, self ).__init__( None, -1, 'Mayavi in Wx' )
    self.dataModel = data_model
    self.stateIndex = 0
    drange = data_model.GetRange( 'pin_powers' )
    #self.dataRange = np.array( [ drange[ 0 ], drange[ 1 ] ], dtype = np.float64 )
    self.dataRange = list( drange )
    self.vs = VolumeSlicer( data = data, data_range = self.dataRange )

    button_panel = wx.Panel( self, -1 )
    button_panel_sizer = wx.BoxSizer( wx.HORIZONTAL )
    button_panel.SetSizer( button_panel_sizer )
    for name in ( 'x', 'y', 'z' ):
      button = wx.Button( button_panel, -1, name.upper() )
      button.Bind(
          wx.EVT_BUTTON,
	  functools.partial( self._OnButton, name )
	  )
      button_panel_sizer.Add( button, 1, wx.ALL, 2 )

    self.vizpanel = wx.Panel( self, -1 )
    vizpanel_sizer = wx.BoxSizer( wx.VERTICAL )
    #noworky self.vizpanel.SetMinSize( ( 700, 750 ) )
    self.vizpanel.SetSizer( vizpanel_sizer )

    self.control = \
        self.vs.edit_traits( parent = self.vizpanel, kind = 'subpanel' ).control
    vizpanel_sizer.Add( self.control, 1, wx.ALL | wx.EXPAND, 2 )
    vizpanel_sizer.Layout()

#standalone
#    self.control = \
#        self.vs.edit_traits( parent = self, kind = 'subpanel' ).control
    #self.vs.configure_traits()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( button_panel, 0, wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 1 )
    sizer.Add( self.vizpanel, 1, wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 1 )
    self.SetSizer( sizer )
    #self.Fit()
    self.SetSize( ( 725, 750 ) )
  #end __init__


  def _OnButton( self, ax, ev ):
    # z->x, x->y, y->z
    name = \
        'x' if ax == 'z' else \
	'y' if ax == 'x' else \
	'z'
    ipw3d = getattr( self.vs, 'ipw_3d_%s' % name )
    ipw3d.ipw.slice_position = 0

    ipw = getattr( self.vs, 'ipw_%s' % name )

    if ax == 'z':
      # self.vs.data_src3d.mlab_source.dataset,
      # self.vs.data_src3d.mlab_source.scalars,
      # self.vs.scene3d.scene.disable_render = True
      new_state_ndx = self.stateIndex + 1
      if new_state_ndx >= len( self.dataModel.GetStates() ):
        new_state_ndx = 0

      if new_state_ndx != self.stateIndex:
        self.stateIndex = new_state_ndx
        self.vs.data = create_cut_matrix( self.dataModel, 'pin_powers', self.stateIndex )
        self.vs.data_src3d.scalar_data = self.vs.data
      else:
        self.vs.data_src3d.scalar_data *= 0.1

      #print >> sys.stderr, self.vs.data_src3d.scalar_data
      #self.vs.data_src3d.mlab_source.scalars = data
      #self.vs.data_src3d.mlab_source.update()
      self.vs.data_src3d.scalar_name = 'pin_powers %d' % self.stateIndex
      self.vs.data_src3d.update()
      self.vs.data_src3d.data_changed = True

#      self.vs.ipw_3d_x = self.vs.make_ipw_3d( 'x' )
#      self.vs.ipw_3d_y = self.vs.make_ipw_3d( 'y' )
#      self.vs.ipw_3d_z = self.vs.make_ipw_3d( 'z' )

#      for n in ( 'x', 'y', 'z' ):
#	cur_ipw_3d = getattr( self.vs, 'ipw_3d_%s' % n )
#	cur_ipw_3d.module_manager.scalar_lut_manager.data_range = self.vs.data_range
#	cur_ipw_3d.module_manager.scalar_lut_manager.use_default_range = False
#
#	cur_ipw = getattr( self.vs, 'ipw_%s' % n )
#	cur_ipw.module_manager.scalar_lut_manager.data_range = self.vs.data_range
#	cur_ipw.module_manager.scalar_lut_manager.use_default_range = False
#      #end for

      #self.vs.ipw_3d_x.update_data()
      #self.vs.ipw_3d_y.update_data()
      #self.vs.ipw_3d_z.update_data()

      # self.vs.scene3d.scene.disable_render = False
      # self.vs.scene3d.render()

# http://stackoverflow.com/questions/30097205/updating-data-of-an-image-plane-widget
      #self.vs.data_src3d.image_data and .outputs
      #self.vs.ipw_x.data_changed = True
      #self.vs.ipw_x.pipeline_changed = True
      #self.vs.ipw_x.module_manager.update()
      # module_manager.scalar_lut_manager
      #  .data_range np.ndarray [ lo, hi ]
      #  .lut_mode (blue-red)
      #  .lut
      #    .table  list of 4-tuples (rgba?)
      #      .to_array() returns np.ndarray( dtype = uint8 )
      #    assign .table from np.ndarray
      #  .load_lut_from_file()
      #  .load_lut_from_list()

      #ipw3d.mlab_source.scalars = data
      #ipw3d.mlab_source.update()
      #ipw3d.mlab_source.data_changed = True
      #ipw3d.pipeline_changed = True
      #ipw.update_data()
      #ipw.data_changed = true
      #ipw.pipeline_changed = true

    elif False:
      sd = self.vs.data_src3d.scalar_data
      new_data = np.ndarray( sd.shape, np.float64 )
      new_data.fill( 0.01 )
      new_data[ 0 : 5, 0 : 5, 0 : 5 ] = sd[ 0 : 5, 0 : 5, 0 : 5 ]
      #new_data = np.copy( sd )
      #new_data[ :, :, : ] /= 2.0
      self.vs.data_src3d.scalar_data = new_data
      self.vs.data_src3d.update()
      self.vs.data_src3d.data_changed = True
      self.vs.data_src3d.render()

#      #self.vs.ipw_x.data_changed = True
#      #self.vs.ipw_x.render()
#      self.vs.ipw_3d_x.mlab_source.scalars = new_data
#      self.vs.ipw_3d_x.mlab_source.update()
#      self.vs.ipw_3d_x.mlab_source.data_changed = True
#      #self.vs.ipw_3d_x.data_changed = True
#      self.vs.ipw_3d_x.render()
#      self.vs.scene_x.render()
  #end _OnButton

#end MainWindow


app = wx.App()
frame = MainWindow( data_model, data )
frame.Show()
app.MainLoop()
