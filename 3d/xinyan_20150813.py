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
import wx
import h5py
import numpy as np

import threading

from traits.api import HasTraits, Instance, Array, \
    on_trait_change
from traitsui.api import View, Item, HGroup, Group

from tvtk.api import tvtk
from tvtk.pyface.scene import Scene

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import SceneEditor, MayaviScene, \
                                MlabSceneModel


#this function is only for internal test, use with caution
def get_matrix(size_x, size_y, size_z, det_dat):
    matrix = [[[0 for x in range(size_x)] for y in range(size_y)] for z in range(size_z)];
    for z in range(0, size_z):
        for y in range(0, size_y):
            for x in range(0, size_x):
                matrix[z][y][x] = det_dat[x][y][z][35]
    return matrix;

#get the matrix ready for plotting the contour
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

#get a matrix with all 0s, and the same dim as quarter reactor
def get_initial_matrix(det_dat, core_map, mesh_factor):
    size_y = len(det_dat[0])
    size_x = len(det_dat) 
    #print size_macro_full
    size_macro = (len(core_map) + 1) / 2
    #print size_macro
    size_x_macro = size_x * size_macro
    size_y_macro = size_y * size_macro

    size_z_2 = mesh_factor[len(mesh_factor) - 1]    
    #print len(matrix[0][0])
    #print  len(matrix[0])
    #print len(matrix) 
    
    matrix = [[[0 for x in range(size_x_macro)] for y in range(size_y_macro)] for z in range(size_z_2)]
    return matrix
    
#the matrix for cut planes.  Most time consuming part of this program
def get_cut_matrix(det_dat, core_map, mesh_factor):
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
        if(mesh_factor[i] == 0):
            mesh_factor[i] = 1;
    return mesh_factor

################################################################################
# Create some data
#x, y, z = np.ogrid[-5:5:64j, -5:5:64j, -5:5:64j]
#beavrs_cy1.h5
#4a-2d.h5
#3a_expected.h5  change variable directory
#3b_expected.h5  change variable directory
"""
myh5 = h5py.File("beavrs_cy1.h5")
det_dat = myh5["/STATE_0001/pin_powers"].value
core_map = myh5["/CORE/core_map"].value
ax_mesh = myh5["/CORE/axial_mesh"].value

mesh_factor = get_mesh_factor(ax_mesh, 1.26)
data2 = get_big_matrix(det_dat, core_map)
"""
#print core_map
#data2 = get_matrix(17, 17, 48, det_dat)
#data = get_matrix(17, 17, 48, det_dat)
################################################################################
# The object implementing the dialog
#x, y, z, k = arrays_for_contour(self.data2, self.core_map, self.det_dat, self.ax_mesh)
class workingthread(threading.Thread):
    def __init__(self, det_dat, core_map, mesh_factor, ax_mesh):
        threading.Thread.__init__(self)
        self.core_map = core_map;
        self.mesh_factor = mesh_factor;
        self.det_dat = det_dat;
        self.ax_mesh = ax_mesh
        self.data_comp = get_initial_matrix(self.det_dat, self.core_map, self.mesh_factor);
        self.data2 = get_big_matrix(self.det_dat, self.core_map)
        x = [];
        y = [];
        z = [];
        k = [];
        self.start()
    def run(self):
        print "Initializing 3D ...."
        self.data_comp = get_cut_matrix(self.det_dat, self.core_map, self.mesh_factor);
        self.x, self.y, self.z, self.k = arrays_for_contour(self.data2, self.core_map, 
                                                            self.det_dat, self.ax_mesh)
        print "3D is ready, click 3D button to see."
    def finished(self):
        if(self.is_alive()):
            return False;
        else:
            return True;
    def get_value(self):
        return self.data_comp, self.x, self.y, self.z, self.k
        


class VolumeSlicer(HasTraits):
    # The data to plot
    
    data = Array()  #not necessary?
    # The 4 views displayed
    sceneReal = Instance(MlabSceneModel, ())
    scene3d = Instance(MlabSceneModel, ())
    sceneCut = Instance(MlabSceneModel, ())
    scene_x = Instance(MlabSceneModel, ())
    scene_y = Instance(MlabSceneModel, ())
    scene_z = Instance(MlabSceneModel, ())

    # The data source
    data_src3d = Instance(Source)

    # The image plane widgets of the 3D scene
    ipw_3d_x = Instance(PipelineBase)
    ipw_3d_y = Instance(PipelineBase)
    ipw_3d_z = Instance(PipelineBase)

    _axis_names = dict(x=0, y=1, z=2)


    #---------------------------------------------------------------------------
    def __init__(self, x, y, z, k, **traits):
        super(VolumeSlicer, self).__init__(**traits)
        # Force the creation of the image_plane_widgets:
        self.x = x
        self.y = y
        self.z = z
        self.k = k
        self.ipw_3d_x
        self.ipw_3d_y
        self.ipw_3d_z


    #---------------------------------------------------------------------------
    # Default values
    #---------------------------------------------------------------------------
    def _data_src3d_default(self):
        return mlab.pipeline.scalar_field(self.data,
                            figure=self.scene3d.mayavi_scene)

    def make_ipw_3d(self, axis_name):
        ipw = mlab.pipeline.image_plane_widget(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        plane_orientation='%s_axes' % axis_name)
        return ipw

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
        outline = mlab.points3d(self.x, self.y, self.z, self.k, 
                                scale_mode = "none", vmin = 0, vmax = 2.5)
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
    
        #text = mlab.text(10, 20, 0, "text test",  figure=self.scene3d.mayavi_scene);
        
        outline = mlab.pipeline.outline(self.data_src3d,
                        figure=self.scene3d.mayavi_scene,
                        )
        
        self.scene3d.mlab.view(40, 50)
        
        # Interaction properties can only be changed after the scene
        # has been created, and thus the interactor exists
        
        for ipw in (self.ipw_3d_x, self.ipw_3d_y, self.ipw_3d_z):
            # Turn the interaction off
            ipw.ipw.interaction = 0
        
        
        self.scene3d.scene.background = (0, 0, 0)
        # Keep the view always pointing up
        self.scene3d.scene.interactor.interactor_style = \
                                 tvtk.InteractorStyleTerrain()


    

    def make_side_view(self, axis_name):
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
                            plane_orientation='%s_axes' % axis_name)
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
                            height=250, width=300),
                       Item('sceneCut',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       show_labels=False,
                  ),
                  Group(
                       Item('sceneReal',
                            editor=SceneEditor(scene_class=MayaviScene),
                            height=250, width=300),
                       show_labels=False,
                  ),
                  
                ),
                resizable=True,
                title='Volume Slicer',
                )


class my_app(wx.Frame): #allow the class to use Frame in wx
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, "VERAView", size = (300, 300));
        #the fourth parameter is the title of the frame
        self.myh5 = h5py.File("/Users/re7x/study/casl/andrew/beavrs.h5")
        self.det_dat = self.myh5["/STATE_0001/pin_powers"].value
        self.core_map = self.myh5["/CORE/core_map"].value
        self.ax_mesh = self.myh5["/CORE/axial_mesh"].value
        
        self.mesh_factor = get_mesh_factor(self.ax_mesh, 1.26)
        self.data_comp = get_initial_matrix(self.det_dat, self.core_map, self.mesh_factor);
        self.clicked = False;
        self.x = []
        self.y = []
        self.z = []
        self.k = []
        self.worker = workingthread(self.det_dat, self.core_map, self.mesh_factor, self.ax_mesh);
        #self.worker.start()
        """
        Note: wx series elements are the most basic ones, and always appear after boxes
        """        
        
        panel = wx.Panel(self)      #containers of all buttons
        button = wx.Button(panel, label = "start 3D", pos = (180, 15), size = (80, 20))
                #panel the button is on, label on the button, position, size
        self.Bind(wx.EVT_BUTTON, self.plot_3d, button);
        
    def plot_3d(self, event):
        if(self.clicked == False):
            if(self.worker.is_alive()):
                print "3D is setting up, please wait"
            else:
                print "It's coming, just a few moment."
                self.data_comp, self.x, self.y, self.z, self.k = self.worker.get_value();
                self.clicked = True;
                m = VolumeSlicer(self.x, self.y, self.z, self.k, 
                                     data=self.data_comp);
                m.configure_traits()
        else:
            print "It's coming, just a few moment."
            m = VolumeSlicer(self.x, self.y, self.z, self.k, data=self.data_comp);
            m.configure_traits()
        
    

#main()
if( __name__ == "__main__"):
    app = wx.App()
    frame = my_app(parent = None, id = -1)
    frame.Show()
    app.MainLoop()
