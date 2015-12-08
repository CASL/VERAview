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
class Slicer3DView( wx.Panel ):
  """Slicer 3D visualization widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id, data_model ):
    self.axialValue = ( 0.0, -1, -1 )
    self.curSize = None
    self.data = None
    self.stateIndex = -1
    self.state = None

    self.control = None
    self.panel = None
    self.viz = None

    super( Slicer3DView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this wxPython component.
"""
    sizer = wx.BoxSizer( wx.VERTICAL )

    self.SetMinSize( ( 320, 320 ) )
  #end _InitUI

#end Slicer3DView
