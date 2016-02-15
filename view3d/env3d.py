# $Id$
#------------------------------------------------------------------------
#	NAME:		env3d.py					-
#	HISTORY:							-
#		2015-12-23	leerw@ornl.gov				-
#	  Added Environment3DLoader and Environment3D.LoadAndCall().
#		2015-12-07	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, sys, subprocess, time, timeit
#import h5py
#import numpy as np
import pdb

os.environ[ 'ETS_TOOLKIT' ] = 'wx'

try:
  #import wxversion
  #wxversion.ensureMinimal( '3.0' )
  import wx
  import wx.lib.delayedresult as wxlibdr
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
  #	METHOD:		Environment3D.IsLoaded()			-
  #----------------------------------------------------------------------
  @staticmethod
  def IsLoaded():
    """
@return			True if loaded, False otherwise
"""
    return  Environment3D.loaded_
  #end IsLoaded


  #----------------------------------------------------------------------
  #	METHOD:		Environment3D.Load()				-
  #----------------------------------------------------------------------
  @staticmethod
  def Load():
    """Loads if not already loaded.
@return			load time in seconds
@throws			Exception on load error
"""
    load_time = -1.0
    if not Environment3D.loaded_:
      #os.environ[ 'ETS_TOOLKIT' ] = 'wx'

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


  #----------------------------------------------------------------------
  #	METHOD:		Environment3D.LoadAndCall()			-
  #----------------------------------------------------------------------
  @staticmethod
  def LoadAndCall( callback = None ):
    """Loads with a progress dialog if not already loaded.
@param  callback	optional callback invoked upon completion
			with prototype
			callback( bool env_loaded, errors )
"""
    if not Environment3D.loaded_:
      loader = Environment3DLoader()
      loader.Run( callback )
    elif callback is not None:
      callback( True, None )
  #end LoadAndCall

#end Environment3D


#------------------------------------------------------------------------
#	CLASS:		Environment3DLoader				-
#------------------------------------------------------------------------
class Environment3DLoader( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Environment3DLoader.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self ):
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Environment3DLoader.Run()			-
  #----------------------------------------------------------------------
  def Run( self, callback = None ):
    """Launches load.
Must be called in the UI thread.
@param  callback	optional callback function invoked upon completion
			with prototype
			callback( boolean env_loaded, float load_time_secs )
"""
    dialog = wx.ProgressDialog(
        'Loading 3D Environment', 'Initializing...', 10
	)
    dialog.Show();

    wxlibdr.startWorker(
	self._RunEnd, self._RunBegin,
	wargs = [ dialog, callback ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		Environment3DLoader._RunBegin()			-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog, callback ):
    """
"""
    #status = { 'callback': callback, 'dialog': dialog, 'loadtime': -1.0 }
    status = { 'callback': callback, 'dialog': dialog }

    try:
      start_time = timeit.default_timer()
      count = 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Traits API'
          )
      from traits.api import HasTraits, Instance, Array, on_trait_change

      count += 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Traits UI'
          )
      from traitsui.api import View, Item, HGroup, Group

      count += 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Tvtk API'
          )
      from tvtk.api import tvtk
      from tvtk.pyface.scene import Scene

      count += 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Mayavi MLab'
          )
      from mayavi import mlab

      count += 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Mayavi Core API'
          )
      from mayavi.core.api import PipelineBase, Source

      count += 1
      wx.CallAfter(
	  dialog.Update, count,
	  'Loading Mayavi Core UI API'
          )
      from mayavi.core.ui.api import SceneEditor, MayaviScene, MlabSceneModel

      wx.CallAfter( dialog.Update, 9, 'Finishing' )
      time.sleep( 1.0 )

      #status[ 'loadtime' ] = timeit.default_timer() - start_time
      Environment3D.loaded_ = True

    except Exception, ex:
      status[ 'errors' ] = [ str( ex ) ]

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		Environment3DLoader._RunEnd()			-
  #----------------------------------------------------------------------
  def _RunEnd( self, result ):
    """
"""
    status = result.get()
    #pdb.set_trace()

    if status is not None:
      dialog = status.get( 'dialog' )
      if dialog is not None:
        dialog.Destroy()

#      messages = status.get( 'messages' )
#      if messages is not None and len( messages ) > 0:
#        msg = \
#	    'Mayavi 3D environment could not be loaded:' + os.linesep + \
#	    os.linesep.join( messages )
#        wx.MessageBox(
#	    msg, 'Loading 3D Environment',
#	    wx.ICON_ERROR | wx.OK_DEFAULT
#	    )

      callback = status.get( 'callback' )
      if callback is not None:
        #callback( Environment3D.IsLoaded(), status.get( 'errors' ) )
        wx.CallAfter(
	    callback, Environment3D.IsLoaded(), status.get( 'errors' )
	    )
    #end if status
  #end _RunEnd


  #----------------------------------------------------------------------
  #	METHOD:		Environment3DLoader._RunEnd1()			-
  #----------------------------------------------------------------------
  def _RunEnd1( self, result ):
    """
"""
    status = result.get()
    pdb.set_trace()

    if status is not None:
      dialog = status.get( 'dialog' )
      if dialog is not None:
	dialog.Update( 9, 'Finished!' )
    #end if status
  #end _RunEnd1

#end Environment3DLoader
