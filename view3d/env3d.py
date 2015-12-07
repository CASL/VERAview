# $Id$
#------------------------------------------------------------------------
#	NAME:		env3d.py					-
#	HISTORY:							-
#		2015-12-07	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, subprocess, timeit
#import h5py
#import numpy as np

os.environ[ 'ETS_TOOLKIT' ] = 'wx'

try:
  #import wxversion
  #wxversion.ensureMinimal( '3.0' )
  import wx
  #import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required' )


#------------------------------------------------------------------------
#	CLASS:		Environment3D					-
#------------------------------------------------------------------------
class Environment3D( object ):
  """Global state class.

Static properties (use accessors):
  loaded		true if loaded
"""


#		-- Class Attributes
#		--

  loaded_ = False


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		IsLoaded()					-
  #----------------------------------------------------------------------
  @staticmethod
  def IsLoaded():
    """
@return			True if loaded, False otherwise
"""
    return  Environment3D.loaded_
  #end IsLoaded


  #----------------------------------------------------------------------
  #	METHOD:		Load()						-
  #----------------------------------------------------------------------
  @staticmethod
  def Load():
    """Loads if not already loaded.
@return			load time in seconds
@throws			Exception on load error
"""
    load_time = -1.0
    if not Environment3D.loaded_:
      os.environ[ 'ETS_TOOLKIT' ] = 'wx'

      start_time = timeit.default_timer()
      from traits.api import HasTraits, Instance, Array, on_trait_change
      from traitsui.api import View, Item, HGroup, Group

      from tvtk.api import tvtk
      from tvtk.pyface.scene import Scene

      from mayavi import mlab
      from mayavi.core.api import PipelineBase, Source
      from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel

      load_time = timeit.default_timer() - start_time
      Environment3D.loaded_ = True
    #end if

    return  load_time
  #end Load

#end Environment3D
