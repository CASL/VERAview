#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		veraview.py					-
#	HISTORY:							-
#		2019-01-19	leerw@ornl.gov				-
#         Transitioned to Murray's new Volume3DView.
#		2018-12-21	leerw@ornl.gov				-
#         Implemented VeraViewApp.DoBusyEventOp().
#         Added DataAnalysisView widget for testing.
#		2018-10-27	leerw@ornl.gov				-
#         Added DataAnalysisView widget for testing.
#		2018-10-22	leerw@ornl.gov				-
#         Added IntraPinEditsAssembly2DView.
#		2018-10-16	leerw@ornl.gov				-
#	  Adding TableView if there is an available grid slot in
#	  VeraViewFrame.UpdateFrame().
#		2018-10-16	purvesmh@ornl.gov			-
#	  Fix to frame positioning in VeraViewFrame._LoadWidgetConfig().
#		2018-10-01	leerw@ornl.gov				-
#	  Adding AnimateOptionsDialog.
#		2018-09-13	leerw@ornl.gov				-
#	  Adding TableView.
#		2018-08-18	leerw@ornl.gov				-
#	  Experimenting with Core2DPlot.
#		2018-07-26	leerw@ornl.gov				-
#	  Renaming non-derived dataset category/type from 'axial' to
#	  'axials' to disambiguate from ':axial' displayed name.
#		2018-06-01	leerw@ornl.gov				-
#	  Updated VeraViewFrame._OnLoadSession() to call
#	  DataModelMgr.Close() and OpenFile() before _LoadWidgetConfig().
#		2018-05-25	leerw@ornl.gov				-
#	  Initializing weights mode menu in UpdateFrame().
#		2018-03-02	leerw@ornl.gov				-
#	  Fixed bug for Mac in VeraViewApp.OnEventLoopEnter() when
#	  searching for the frame id/key 1, now increments ids.
#		2017-12-01	leerw@ornl.gov				-
#	  Enabled SubPin2DView.
#		2017-09-11	leerw@ornl.gov				-
#	  Added VesselCoreAxial2DView.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-07-20	leerw@ornl.gov				-
#	  Added Data->Manage Dataset Thresholds menu item.
#	  Added display of file open warning messages.
#		2017-07-15	leerw@ornl.gov				-
#	  Added VeraViewFrameAnimatorWidget and support for axial level
#	  and state point animation.
#		2017-07-07	leerw@ornl.gov				-
#	  Hooked ExcoreOutputDialog.
#		2017-05-31	leerw@ornl.gov				-
#	  Renamed SubPin2DView to SubPinRadial2DView.
#		2017-05-26	leerw@ornl.gov				-
#	  Added SubPin2DView but commenting for now.
#		2017-05-14	leerw@ornl.gov				-
#	  Fixed bug to call UpdateFrame() and UpdateAllFrames() in
#	  _OnOpenFileMgr().
#		2017-05-06	leerw@ornl.gov				-
#	  New Data menu.
#		2017-05-05	leerw@ornl.gov				-
#	  Added no_init param to Create{2D,3D,}Widget(), CreateWindow(),
#	  and UpdateFrame().
#		2017-04-22	leerw@ornl.gov				-
#	  Using FileManagerDialog.
#		2017-04-21	leerw@ornl.gov				-
#	  Checking HtmlException in _OpenFileBegin(), using
#	  HtmlMessageDialog in _OpenFileEnd().
#		2017-02-25	leerw@ornl.gov				-
#	  Developing with VesselCore2DView.
#		2017-01-25	leerw@ornl.gov				-
#	  Disabling auto-enable of Detector Detector2DMultiView when
#	  a detector dataset is present.
#		2017-01-17	leerw@ornl.gov				-
#	  Adding DataSetDiffCreatorDialog.
#		2017-01-14	leerw@ornl.gov				-
#	  Removing channel widgets since others support channel datasets.
#		2016-12-16	leerw@ornl.gov				-
#	  Trying to clean up Mac stuff with Anaconda.  Giving up!!.
#		2016-12-12	leerw@ornl.gov				-
#		2016-11-26	leerw@ornl.gov				-
#	  Using Config.CanDragNDrop() as a gate for the "Window" menubar
#	  item.
#		2016-11-19	leerw@ornl.gov				-
#	  Added CreateWindow() and modified LoadDataModel() to have a
#	  widget_props param in support of widgets-to-window and dragging
#	  widgets to a different window.
#		2016-10-25	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-02	leerw@ornl.gov				-
#	  Fixed bug where toolbar item event handlers were not removed
#	  in VeraViewFrame._UpdateToolBar(), resulting in double widgets
#	  after opening a new file.
#		2016-09-20	leerw@ornl.gov				-
#	  Added weights mode to the edit menu.
#		2016-09-03	leerw@ornl.gov				-
#	  Added TOOLBAR_ITEMS functions to enable core widgets only if
#	  core.nass gt 1, axial widgets if core.nax gt 1, and Time Plots
#	  only if data.GetStatesCount() gt 1.
#	  Only enable axial widgets if core.nax gt 1.
#		2016-08-20	leerw@ornl.gov				-
#	  Changing initial widgets to pin and plots only.
#	  Assigning last frame position and size on load.
#		2016-08-19	leerw@ornl.gov				-
#	  More messing with widget sizing in grids.
#		2016-08-19	leerw@ornl.gov				-
#	  New DataModelMgr.
#		2016-08-16	leerw@ornl.gov				-
#	  Messing with widget sizing in grids.
#		2016-08-10	leerw@ornl.gov				-
#	  Added --skip-startup-session-check command-line arg.
#	  Turning off 3D widgets on config load.
#	  Using Environment3D.IsAvailable() as a test for enabling the
#	  3D widgets.
#		2016-07-07	leerw@ornl.gov				-
#	  Renaming "vanadium" to "fixed_detector".
#		2016-07-01	leerw@ornl.gov				-
#	  Adding load/save session menu items.
#		2016-06-27	leerw@ornl.gov				-
#	  Moved prompt for widget config.
#		2016-06-20	leerw@ornl.gov				-
#	  Putting in hooks for reading/writing widget configurations.
#		2016-06-04	leerw@ornl.gov				-
#	  Using new "ScalarPlot" replacement for TimePlot.		-
#		2016-05-25	leerw@ornl.gov				-
# 	  Special "vanadium" dataset.  Calling
#	  DataModel.CreateEmptyAxialValue()
#		2016-04-16	leerw@ornl.gov				-
#	  Added "Select Scale Mode" pullright on the Edit menu.
#		2016-03-16	leerw@ornl.gov				-
#	  Playing with grid sizing when adding widgets, might finally
#	  have a workable solution.
#	  Removed status bar since we're not using it and it eats
#	  vertical screen real estate.
#		2016-03-08	leerw@ornl.gov				-
#	  Added Volume3DView, separators in the toolbar, and the CASL
#	  logo.
#		2016-03-07	leerw@ornl.gov				-
#	  Added Slicer3DView.
#		2016-03-05	leerw@ornl.gov				-
#		2016-03-05	leerw@ornl.gov				-
#	  Replaced Core[XY]ZView with CoreAxial2DView.
#		2016-03-01	leerw@ornl.gov				-
#	  Added Core[XY]ZView widget.
#		2016-02-20	leerw@ornl.gov				-
#	  Added EVT_CHAR_HOOK to VeraViewFrame.
#		2016-01-22	leerw@ornl.gov				-
#	  Added Edit->Copy menu item.
#		2015-12-29	leerw@ornl.gov				-
#	  Added View menu with creation of Slicer3DFrame.
#		2015-12-07	leerw@ornl.gov				-
#	  Back to original icons.
#		2015-11-24	leerw@ornl.gov				-
#	  After change to GridSizerBean, checking for more than 16
#	  widget cells and prompting the user to confirm.
#		2015-11-12	leerw@ornl.gov				-
#	  Adding menu to create a pseudo dataset.
#		2015-09-17	leerw@ornl.gov				-
#	  Remove erroneous 'func' from the Time Plot toolbar item definition.
#	  Began addition of the "plot everything" function.
#		2015-08-25	leerw@ornl.gov				-
#	  Replacing various axial plots with AllAxialPlot and specific
#	  "selected" datasets enabled.
#		2015-07-27	leerw@ornl.gov				-
#	  Build 15 with fixes to dataset reference order.
#		2015-07-15	leerw@ornl.gov				-
#	  Build 14.
#		2015-07-11	leerw@ornl.gov				-
#	  New ChannelAssembly2DView.
#		2015-05-25	leerw@ornl.gov				-
#	  New menu for the global time dataset.
#		2015-05-11	leerw@ornl.gov				-
#	  New State.axialValue attribute.
#		2015-04-27	leerw@ornl.gov				-
#	  New detector view and plot.
#	  Added type to TOOLBAR_ITEMS with enable/disable of toolbar
#	  buttons based on available datasets by type/category.
#		2015-04-13	leerw@ornl.gov				-
#	  Added DataModel.Check() call in OpenFile().  Added call to
#	  frame _OnOpenFile() in OnEventLoopEnter().
#	  Doing OpenFile() as background task with _OpenFile{Begin,End}().
#		2015-04-11	leerw@ornl.gov				-
#		2015-04-10	leerw@ornl.gov				-
#	  Putting sliders on the frame.
#		2015-04-02	leerw@ornl.gov				-
#	  No longer enforcing aspect ratio on resize.
#		2015-02-14	leerw@ornl.gov				-
#	  Trying a grid editor.
#		2015-01-10	leerw@ornl.gov				-
#		2015-01-08	leerw@ornl.gov				-
#		2015-01-07	leerw@ornl.gov				-
#		2015-01-05	leerw@ornl.gov				-
#		2014-12-18	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-15	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, logging, os, six, sys, threading, time, traceback
import pdb  # set_trace()

try:
  import wx
  import wx.lib.agw.genericmessagedialog as GMD
  import wx.lib.delayedresult as wxlibdr
#except ImportException:
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

try:
  import matplotlib
  matplotlib.use( 'WXAgg' )
except Exception:
  raise ImportError( 'The matplotlib module is required for this component' )

#from bean.dataset_menu_item import *
#from bean.dataset_mgr import *
from bean.dataset_creator import *
from bean.dataset_diff_creator import *
from bean.excore_output_bean import *
from bean.filemgr_bean import *
from bean.grid_sizer_dialog import *
from bean.html_message_dialog import *
from bean.range_bean import *

from data.config import Config
from data.datamodel import *
from data.datamodel_mgr import *

from event.state import *

from view3d.env3d import *

from widget.animators import *
from widget.image_ops import *
from widget.widget_config import *
from widget.widgetcontainer import *

from widget.bean.animate_options_bean import *
from widget.bean.axial_slider import *
from widget.bean.dataset_menu import *
from widget.bean.exposure_slider import *


ID_REFIT_WINDOW = 1000

SCALE_MODES = \
  {
  'All State Points': 'all',
  'Current State Point': 'state'
  }

#TITLE = 'VERAView Version 1.1 Build 85'
TITLE = 'VERAView Version 2.4.0'

TOOLBAR_ITEMS = \
  [
#    {
#    'widget': 'Core 2D Plot',
#    'icon': 'Core2DView.1.32.png',
#    'iconDisabled': 'Core2DView.disabled.1.32.png',
#    #'type': 'pin',
#    'type': '',
#    #'func': lambda d: d.GetCore() is not None and d.GetCore().nass > 1
#    'func': lambda d: d.core is not None and \
#	d.core.coreMap is not None and \
#	d.core.coreMap.shape[ 0 ] > 1 and \
#	d.core.coreMap.shape[ 1 ] > 1
#    },
    {
    'widget': 'Core 2D View',
    'icon': 'Core2DView.1.32.png',
    'iconDisabled': 'Core2DView.disabled.1.32.png',
    #'type': 'pin',
    'type': '',
    #'func': lambda d: d.GetCore() is not None and d.GetCore().nass > 1
    'func': lambda d: d.core is not None and
	d.core.coreMap is not None and
	d.core.coreMap.shape[ 0 ] > 1 and
	d.core.coreMap.shape[ 1 ] > 1 and
        (d.HasDataSetType( 'channel' ) or d.HasDataSetType( 'pin' ) or
         d.HasDataSetType( ':assembly' ) or
         d.HasDataSetType( ':chan_radial' ) or
         d.HasDataSetType( ':node' ) or
         d.HasDataSetType( ':radial' ) or
         d.HasDataSetType( ':radial_assembly' ) or
         d.HasDataSetType( ':radial_node' ))
    },
    {
    'widget': 'Core Axial 2D View',
    'icon': 'CoreAxial2DView.1.32.png',
    'iconDisabled': 'CoreAxial2DView.disabled.1.32.png',
    #'type': 'pin',
    'type': '',
    #'func': lambda d: d.GetCore() is not None and d.GetCore().nax > 1
    'func': lambda d: d.core is not None and
	d.core.nax > 1 and
	d.core.coreMap is not None and
	d.core.coreMap.shape[ 0 ] > 0 and
	d.core.coreMap.shape[ 1 ] > 0 and
        (d.HasDataSetType( 'channel' ) or
         d.HasDataSetType( 'pin' ) or
         d.HasDataSetType( ':assembly' ) or
         d.HasDataSetType( ':node' ))
    },
    {
    'widget': 'Vessel Core 2D View',
    'icon': 'VesselCore2DView.1.32.png',
    'iconDisabled': 'VesselCore2DView.disabled.1.32.png',
    'type': 'fluence',
    'func': lambda d: d.core and d.core.fluenceMesh.IsValid()
    },
    {
    'widget': 'Vessel Core Axial 2D View',
    'icon': 'VesselCoreAxial2DView.1.32.png',
    'iconDisabled': 'VesselCoreAxial2DView.disabled.1.32.png',
    'type': 'fluence',
    'func': lambda d:
        d.core and d.core.fluenceMesh.IsValid() and d.core.fluenceMesh.nz > 1
    },
    {
    'widget': 'Assembly 2D View',
    'icon': 'Assembly2DView.1.32.png',
    'iconDisabled': 'Assembly2DView.disabled.1.32.png',
    #'type': 'pin'
    'type': '',
    'func': lambda d: d.core is not None and
	d.core.npinx > 1 and d.core.npiny > 1 and
        (d.HasDataSetType( 'channel' ) or
         d.HasDataSetType( 'pin' ) or
         d.HasDataSetType( ':chan_radial' ) or
         d.HasDataSetType( ':radial' ))
    },
    {
    'widget': 'Intrapin Edits Assembly 2D View',
    'icon': 'IntraPinEditsAssembly2DView.1.32.png',
    'iconDisabled': 'IntraPinEditsAssembly2DView.disabled.1.32.png',
    'type': 'intrapin_edits',
    'func': lambda d: d.HasDataSetType( 'intrapin_edits' )
    },
    {
    'widget': 'Intrapin Edits Plot',
    'icon': 'SubPin2DView.1.32.png',
    'iconDisabled': 'SubPin2DView.disabled.1.32.png',
    'type': 'intrapin_edits',
    'func': lambda d: d.HasDataSetType( 'intrapin_edits' )
    },
#    {
#    'widget': 'Subpin 2D View',
#    'icon': 'SubPin2DView.1.32.png',
#    'iconDisabled': 'SubPin2DView.disabled.1.32.png',
#    'type': '',
#    'func': lambda d: d.HasDataSetType( 'subpin_r' ) or d.HasDataSetType( 'subpin_theta' )
#    },
#x    {
#x    'widget': 'Subpin Plot',
#x    'icon': 'SubPinPlot.32.png',
#x    'iconDisabled': 'SubPinPlot.disabled.32.png',
#x    'type': '',
#x    'func': lambda d: d.HasDataSetType( 'subpin_r' ) or d.HasDataSetType( 'subpin_theta' )
#x    },
    {
    'widget': 'Subpin Length Plot',
    'icon': 'SubPinLengthPlot.32.png',
    'iconDisabled': 'SubPinLengthPlot.disabled.32.png',
    'type': 'subpin_cc'
    #'func': lambda d: d.HasDataSetType( 'subpin_cc' )
    },
    { 'widget': 'separator' },
    {
    'widget': 'Detector 2D Multi View',
    'icon': 'Detector2DView.1.32.png',
    'iconDisabled': 'Detector2DView.disabled.1.32.png',
#    'type': 'detector'
    'type': '',
    'func': lambda d:
        d.HasDataSetType( 'detector' ) or
        d.HasDataSetType( 'fixed_detector' ) or
        d.HasDataSetType( 'radial_detector' )
    },
    { 'widget': 'separator' },
    {
    'widget': 'Volume Slicer 3D View',
    'icon': 'Slicer3DView.1.32.png',
    'iconDisabled': 'Slicer3DView.disabled.1.32.png',
    'type': 'pin',
    'func': lambda d: Environment3D.IsAvailable() and d.Is3DReady()
    },
#    {
#    'widget': 'Deprecated Volume 3D View',
#    'icon': 'Volume3DView-deprecated.1.32.png',
#    'iconDisabled': 'Volume3DView.disabled.1.32.png',
#    'type': 'pin',
#    'func': lambda d: Environment3D.IsAvailable() and d.Is3DReady()
#    },
#    { 'widget': 'separator' },
    {
    'widget': 'Volume 3D View',
    'icon': 'Volume3DView.1.32.png',
    'iconDisabled': 'Volume3DView.disabled.1.32.png',
    'type': 'pin',
    'func': lambda d: Environment3D.IsAvailable() and d.Is3DReady()
    },
    { 'widget': 'separator' },
    {
    'widget': 'Axial Plots',
    'icon': 'AllAxialPlot.32.png',
    'iconDisabled': 'AllAxialPlot.disabled.32.png',
    'type': '',
    'func': lambda d: d.HasDataSetType( 'axials' )
    #'func': lambda d: d.GetCore() is not None and d.GetCore().nax > 1
    },
    {
    'widget': 'Time Plots',
    'icon': 'TimePlot.32.png',
    'iconDisabled': 'TimePlot.disabled.32.png',
    'type': '',
    'func': lambda d: len( d.GetTimeValues() ) > 1
    },
    {
    'widget': 'Table View',
    'icon': 'TableView.32.png',
    'iconDisabled': 'TableView.disabled.32.png',
    'type': '',
    'func': lambda d: d.core is not None and d.core.coreMap is not None
    },
    {
    'widget': 'Data Analysis View',
    'icon': 'DataAnalysisView.1.32.png',
    'iconDisabled': 'DataAnalysisView.1.disabled.32.png',
    'type': '',
    'func': lambda d: d.core is not None and d.core.coreMap is not None
    }
  ]

WEIGHTS_MODES = \
  {
  'Use Weights to Show/Hide Pins/Channels': 'on',
  'Show All Pins/Channels': 'off'
  }

WIDGET_MAP = \
  {
  'Assembly 2D View': 'widget.assembly_view.Assembly2DView',
  'Axial Plots': 'widget.axial_plot.AxialPlot',
  'Core 2D Plot': 'widget.core_view_plot.Core2DPlot',
  'Core 2D View': 'widget.core_view.Core2DView',
  'Core Axial 2D View': 'widget.core_axial_view.CoreAxial2DView',
  'Data Analysis View': 'widget.data_analysis_view.DataAnalysisView',
  'Detector 2D Multi View': 'widget.detector_multi_view.Detector2DMultiView',
  'Intrapin Edits Assembly 2D View': 'widget.intrapin_edits_assembly_view.IntraPinEditsAssembly2DView',
  'Intrapin Edits Plot': 'widget.intrapin_edits_plot.IntraPinEditsPlot',
#  'Subpin 2D View': 'widget.subpin_view.SubPin2DView',
#x  'Subpin Plot': 'widget.subpin_plot.SubPinPlot',
  'Subpin Length Plot': 'widget.subpin_len_plot.SubPinLengthPlot',
  'Table View': 'widget.table_view.TableView',
  'Time Plots': 'widget.time_plots.TimePlots',
  'Vessel Core 2D View': 'widget.vessel_core_view.VesselCore2DView',
  'Vessel Core Axial 2D View': 'widget.vessel_core_axial_view.VesselCoreAxial2DView',
#  'Deprecated Volume 3D View': 'view3d.volume_view_deprecated.Volume3DView',
  'Volume 3D View': 'view3d.volume_view.Volume3DView',
  'Volume Slicer 3D View': 'view3d.slicer_view.Slicer3DView'
  }


#------------------------------------------------------------------------
#	CLASS:		VeraViewApp					-
#------------------------------------------------------------------------
class VeraViewApp( wx.App ):
  """This will be the controller for now.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( VeraViewApp, self ).__init__( *args, **kwargs )
    super( VeraViewApp, self ).__init__( redirect = False )
    #super( VeraViewApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'VERAView' )

    self.busyCount = 0
    self.busyLock = threading.RLock()

    #self.data = None
    #self.dataSetDefault = 'pin_powers'
    self.filePaths = None
    self.firstLoop = True

    #self.frame = None
#		-- Dict by index of { 'frame', 'n', 'title' }
    self.frameRecs = {}

    self.loadSession = False
    self.logger = logging.getLogger( 'root' )
    self.sessionPath = None
    #self.skipSession = False
    self.state = None

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.AddFrame()				-
  #----------------------------------------------------------------------
  def AddFrame( self, frame, update_menus_flag = True ):
    """Adds a new VeraViewFrame.
"""
    if frame is not None:
#			-- Resolve Title
#			--
      n = 1
      while True:
        if n not in self.frameRecs:
          break
        n += 1

      #cur_title = frame.GetTitle()
      #if not cur_title:
        #cur_title = TITLE
      #title = '%d: %s' % ( n, cur_title )
      frame.SetFrameId( n )
      frame.UpdateTitle()

      self.frameRecs[ n ] = \
          { 'frame': frame, 'n': n, 'title': frame.GetTitle() }

      if update_menus_flag and Config.CanDragNDrop():
        self.UpdateWindowMenus( add_frame = frame )
    #end if frame
  #end AddFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.DoBusyEventOp()			-
  #----------------------------------------------------------------------
  def DoBusyEventOp( self, func, *args, **kwargs ):
    """Must be called on the UI thread.  Note the arguments cannot contain
references to transient wxwidgets C++ objects, such as events, b/c they
cannot be copied and are invalid in a ``wx.CallLater()`` invocation.
    Args:
        func (callable): function to call
        *args (list): positional arguments
        **kwargs (dict): keyword arguments
"""
    def do_later( func, *args, **kwargs ):
      func( *args, **kwargs )
      #for rec in six.itervalues( self.frameRecs ):
      #  rec.get( 'frame' ).ShowBusyIcon( False )

      self.busyLock.acquire()
      if self.busyCount == 1:
        for rec in six.itervalues( self.frameRecs ):
          rec.get( 'frame' ).ShowBusyIcon( False )
      self.busyCount -= 1
      self.busyLock.release()
    #end do_later

    #for rec in six.itervalues( self.frameRecs ):
    #  rec.get( 'frame' ).ShowBusyIcon( True )

    self.busyLock.acquire()
    if self.busyCount == 0:
      for rec in six.itervalues( self.frameRecs ):
        rec.get( 'frame' ).ShowBusyIcon( True )

    self.busyCount += 1
    self.busyLock.release()

    wx.CallLater( 100, do_later, func, *args, **kwargs )
  #end DoBusyEventOp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp._DoFirstLoop()			-
  #----------------------------------------------------------------------
  def _DoFirstLoop( self, frame ):
    """Must be called on the UI thread.
"""
    opened = False
    session = WidgetConfig.ReadUserSession()
    frame.SetConfig( session )
    #wx.CallAfter( frame.SetConfig, session )

    if self.sessionPath and os.path.exists( self.sessionPath ):
      data_paths, session = frame._ResolveFile( self.sessionPath )
      if not data_paths:
        wx.MessageBox(
            'Error reading session file: ' + self.sessionPath,
	    'Open File', wx.OK, None
	    )
      else:
        opened = True
        frame.OpenFile( data_paths, session )
        #wx.CallAfter( frame.OpenFile, data_paths, session )

    elif self.filePaths:
      paths = []
      for f in self.filePaths:
        if os.path.exists( f ):
          paths.append( f )
      if paths:
        opened = True
        frame.OpenFile( paths )
        #wx.CallAfter( frame.OpenFile, paths )

    elif session is not None and self.loadSession:
      data_paths = session.GetDataModelPaths()
      if data_paths and len( data_paths ) > 0:
        found = True
        for f in data_paths:
          found |= os.path.exists( f )
          if not found:
	    break
      else:
        found = False

      if found:
# For some reason modal dialog don't work at this stage with Anaconda
	opened = True
        wx.CallAfter( frame.OpenFile, data_paths, session )
    #end if-else
  #end _DoFirstLoop


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.FindFrameByTitle()			-
  #----------------------------------------------------------------------
  def FindFrameByTitle( self, title ):
    """Finds the specified frame
@return			frame rec or None if not found
"""
    match = None
    title_n = 0
    if title:
      ndx = title.find( ':' )
      if ndx > 0:
        title_n = int( title[ 0 : ndx ] )

    if title_n > 0:
      for n, rec in self.frameRecs.iteritems():
        #if rec[ 'title' ] == title:
	if n == title_n:
	  match = rec
	  break
      #end for n, rec
    #end if frame

    return  match
  #end FindFrameByTitle


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.GetFrameRecs()			-
  #----------------------------------------------------------------------
  def GetFrameRecs( self ):
    """Removes a new VeraViewFrame.
@return			frames dict
"""
    return  self.frameRecs
  #end GetFrameRecs


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.MacHideApp()			-
  # These noworky
  #----------------------------------------------------------------------
  def MacHideApp( self ):
    print >> sys.stderr, 'XXX MacHideHap'
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    pass
  #end MacHideApp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.MacReopenApp()			-
  # These noworky
  #----------------------------------------------------------------------
  def MacReopenApp( self ):
    print >> sys.stderr, 'XXX MacReopenApp'
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    #self.BringWindowToFront()

    if len( self.frameRecs ) > 0:
      rec = six.next( six.itervalues( self.frameRecs ) )
      rec[ 'frame' ].Raise()
  #end MacReopenApp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.OnEventLoopEnter()			-
  #----------------------------------------------------------------------
  def OnEventLoopEnter( self, *args, **kwargs ):
    """It looks like this is called only once, so the firstLoop flag is
unnecessary.
"""
    #DEBUG,INFO,WARNING,ERROR,CRITICAL
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )

    #original frame_rec = self.frameRecs.get( 1 )
    n = 1
    frame_rec = None
    while frame_rec is None and n < 32768:
      frame_rec = self.frameRecs.get( n )
      n += 1

    frame = frame_rec.get( 'frame' ) if frame_rec else None
    #if self.frame is None:
    if frame is None:
      self.logger.critical( '* No frame to show *' )
      self.ExitMainLoop()

    elif self.firstLoop:
      self.firstLoop = False
      wx.CallAfter( self._DoFirstLoop, frame )
    #end elif self.firstLoop:
  #end OnEventLoopEnter


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.OnInit()				-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pdb.set_trace()
#    super( VeraViewApp, self ).OnInit()
#    #DEBUG,INFO,WARNING,ERROR,CRITICAL
#    if self.logger.isEnabledFor( logging.DEBUG ):
#      self.logger.debug( 'entered' )
#
#    frame_rec = self.frameRecs.get( 1 )
#    frame = frame_rec.get( 'frame' ) if frame_rec else None
#    #if self.frame is None:
#    if frame is None:
#      self.logger.critical( '* No frame to show *' )
#      status = False
#    else:
#      status = True
#      wx.CallAfter( self._DoFirstLoop, frame )
#
#    return  status
#  #end OnInit


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.RemoveFrame()			-
  #----------------------------------------------------------------------
  def RemoveFrame( self, frame, update_menus_flag = True ):
    """Removes a new VeraViewFrame.
@param  frame		wx.Frame instance
"""
    rec = self.FindFrameByTitle( frame.GetTitle() )
    if rec:
      n = rec.get( 'n' )
      if n in self.frameRecs:
	frame = rec.get( 'frame' )
        del self.frameRecs[ n ]

        if update_menus_flag and Config.CanDragNDrop():
          self.UpdateWindowMenus( remove_frame = frame )
      #end if n in self.frameRecs
    #end if rec
  #end RemoveFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.UpdateAllFrames()			-
  #----------------------------------------------------------------------
  def UpdateAllFrames( self, *skip_frames ):
    """Must be called on the UI thread.
@param  skip_frames	frames to skip
"""
    model_names = self.state.dataModelMgr.GetDataModelNames()
    file_path = sorted( model_names )[ 0 ]  if model_names else  ''
    for rec in six.itervalues( self.frameRecs ):
      frame = rec.get( 'frame' )
      if frame and (skip_frames is None or frame not in skip_frames):
        frame.UpdateFrame( file_path = file_path )
    #end for rec
  #end UpdateAllFrames


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.UpdateWindowMenus()			-
  #----------------------------------------------------------------------
  def UpdateWindowMenus( self, **kwargs ):
    """Assume this will only be called if the 'Window' menubar item has
been created.
"""
    titles = []
    frames = []
    for frame_rec in self.frameRecs.values():
      frame = frame_rec.get( 'frame' )
      if frame is not None:
	frames.append( frame )
        titles.append( frame.GetTitle() )
    #end for frame_rec

#		-- Process menu for each frame
#		--
    for frame in frames:
#			-- Find items to remove
#			--
      removes = []
      for i in xrange( frame.windowMenu.GetMenuItemCount() ):
        item = frame.windowMenu.FindItemByPosition( i )
	if item:
	  label = item.GetItemLabelText()
	  if label and label != 'Tile Windows':
	    removes.append( item )
      #end for i
#			-- Remove items
#			--
      for item in removes:
        frame.windowMenu.DestroyItem( item )

#			-- Add new items
#			--
      for title in titles:
        item = wx.MenuItem( frame.windowMenu, wx.ID_ANY, title )
	frame.Bind( wx.EVT_MENU, frame._OnWindowMenuItem, item )
	frame.windowMenu.AppendItem( item )
	#frame.windowMenu.UpdateUI()
      #end for title
    #end for frame
  #end UpdateWindowMenus


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.main()				-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

#      parser.add_argument(
#	  '--assembly',
#	  default = 0,
#	  type = int,
#	  help = 'optional 1-based index of assembly to display'
#          )

#      parser.add_argument(
#	  '-a', '--axial',
#	  default = 0,
#	  type = int,
#	  help = 'optional 1-based index of core axial to display'
#          )

#      parser.add_argument(
#	  '-d', '--dataset',
#	  help = 'default dataset name, defaulting to "pin_powers"'
#          )

      parser.add_argument(
	  #'-f', '--file-paths',
	  'file_path',
	  help = 'path to HDF5 data file',
	  nargs = '*'
          )

      parser.add_argument(
	  '--debug',
	  action = 'store_true',
	  help = 'run in debug mode'
          )

      parser.add_argument(
	  '--load-session',
	  action = 'store_true',
	  help = 'load the session on startup, overriding any file paths'
          )

      parser.add_argument(
	  '--session',
	  help = 'path to session file to load'
          )

      parser.add_argument(
	  '--trace',
	  action = 'store_true',
	  help = 'trace call calls to stderr'
          )

#      parser.add_argument(
#	  '--skip-startup-session-check',
#	  action = 'store_true',
#	  help = 'skip the check for a session on startup when no file path is specified'
#          )

      args = parser.parse_args()

      if args.trace:
        sys.settrace( VeraViewApp.trace )

      #Config.SetRootDir( os.path.dirname( os.path.abspath( __file__ ) ) )
      root_dir = os.path.dirname( os.path.abspath( __file__ ) )
      if not os.path.isdir( os.path.join( root_dir, 'res' ) ):
        root_dir = os.path.dirname( root_dir )
      Config.SetRootDir( root_dir )

#			-- Check existence of files
#			--
      files_not_found = [ f for f in args.file_path if not os.path.exists( f ) ]
      for f in files_not_found:
        print >> sys.stderr, '[VERAView] File not found:', f
      files_found = [ f for f in args.file_path if f not in files_not_found ]

#			-- Create State
#			--
      state = State()

#			-- Create App
#			--
      #app = VeraViewApp( redirect = False )  # redirect = False
      app = VeraViewApp()
      app.debug = args.debug
      app.filePaths = files_found
      app.loadSession = args.load_session
      app.sessionPath = args.session
      #app.skipSession = args.skip_startup_session_check
      app.state = state

      #app.frame = VeraViewFrame( app, state )
      frame = VeraViewFrame( app, state )
      app.AddFrame( frame )
#			-- If MDI on Mac, don't show
      #app.frame.Show()
      frame.Show()
      app.MainLoop()

    except Exception, ex:
      msg = str( ex )
      print >> sys.stderr, msg
      et, ev, tb = sys.exc_info()
      while tb:
	msg += \
	    os.linesep + 'File=' + str( tb.tb_frame.f_code ) + \
	    ', Line=' + str( traceback.tb_lineno( tb ) )
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
      logging.error( msg )
  #end main


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.trace()				-
  #----------------------------------------------------------------------
  @staticmethod
  def trace( frame, event, arg ):
    six.print_(
        '{0}, {1}:{2:d}'.
            format( event, frame.f_code.co_filename, frame.f_lineno ),
        file = sys.stderr
        )
  #end trace

#end VeraViewApp


#------------------------------------------------------------------------
#	CLASS:		VeraViewFrame					-
#------------------------------------------------------------------------
#class VeraViewFrame( wx.MDIParentFrame ):
class VeraViewFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, app, state, file_path = '' ):
    super( VeraViewFrame, self ).__init__( None, -1 )

    self.app = app
#    self.axialPlotTypes = set()
    self.config = None
#    self.dataSetDefault = ds_default
    self.eventLocks = State.CreateLocks()
    self.filepath = file_path
    self.frameId = 0
    self.initialized = False
    #self.logger = logging.getLogger( 'root' )
    self.logger = app.logger
    self.state = state
    self.windowMenu = None

    self.animateOptionsDialog = None
    self.axialBean = None
#    self.busyCount = 0
#    self.busyLock = threading.RLock()
    self.caslIcon = None
    self.caslIconBg = None
#x    self.closeFileItem = None
    self.dataSetMenu = None
    self.exposureBean = None
    self.fileNewMenu = None
    self.grid = None
    self.scaleModeItems = {}
    self.timeDataSetMenu = None
    self.weightsModeItems = {}
    self.widgetToolBar = None
    self.widgetToolBarPanel = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.AddWidgetContainer()		-
  #----------------------------------------------------------------------
  def AddWidgetContainer( self, wc, refit_flag = True ):
    """Called by Create[23]DWidget() to add a grid with the container.
The hackit deal is pure ugliness but seems necessary given the weirdess
in GridSizer when adding grids.
@param  wc		WidgetContainer instance to add
@param  refit_flag	True to refit the window after adding
"""
    grow_flag = False
    grid_sizer = self.grid.GetSizer()
    widget_count = len( self.grid.GetChildren() )
    widget_space = grid_sizer.GetCols() * grid_sizer.GetRows()
    if widget_count > widget_space:
#      grow_flag = True
      if widget_space == 1:
        grid_sizer.SetCols( grid_sizer.GetCols() + 1 )
      elif grid_sizer.GetCols() > grid_sizer.GetRows():
	grid_sizer.SetRows( grid_sizer.GetRows() + 1 )
	grow_flag = True
      else:
	#grow_flag = grid_sizer.GetCols() >= 2
        grid_sizer.SetCols( grid_sizer.GetCols() + 1 )
    #end if

    frame_size = self.GetSize()
    self.grid._FreezeWidgets()
    grid_sizer.Add( wc, 0, wx.ALIGN_CENTER | wx.EXPAND, 0 )
    self.grid.Layout()
#		-- If you don't call Fit() here, the window will not grow
#		-- with the addition of the new widget
    if grow_flag:
      refit_flag = True
      #self.Fit()

    if refit_flag:
      wx.CallAfter( self._Refit, False, self.grid._FreezeWidgets, False )
    else:
      self.grid._FreezeWidgets( False )
  #end AddWidgetContainer


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.CloseAllWidgets()			-
  #----------------------------------------------------------------------
  def CloseAllWidgets( self ):
    close_list = []
    for child in self.grid.GetChildren():
      if isinstance( child, WidgetContainer ):
        close_list.append( child )
    #end for

    for child in close_list:
      child.Destroy()
  #end CloseAllWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._CloseFrame()			-
  #----------------------------------------------------------------------
  def _CloseFrame( self, frame ):
    """Performs action of closing a frame.
"""
    if frame:
      self.app.RemoveFrame( frame )
      frame.Bind( wx.EVT_CLOSE, None )
      frame.Close()
      # In RemoveFrame()
      #if Config.CanDragNDrop():
        #self.app.UpdateWindowMenus( remove_frame = frame )
  #end _CloseFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.Create2DWidget()			-
  #----------------------------------------------------------------------
  def Create2DWidget( self, widget_class, refit_flag = True, no_init = False ):
    """Must be called on the UI thread.
@return		widget container object
"""
    wc = WidgetContainer( self.grid, widget_class, self.state, no_init = no_init )
    self.AddWidgetContainer( wc, refit_flag )
    return  wc
  #end Create2DWidget


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.Create3DWidget()			-
  #----------------------------------------------------------------------
  def Create3DWidget( self, widget_class, refit_flag = True, no_init = False ):
    """Must be called on the UI thread.
"""
    def check_3d_env( loaded, errors ):
      result = None
      if errors:
        msg = \
	    'Error loading 3D envrionment:' + os.linesep + \
	    os.linesep.join( errors )
        wx.MessageBox(
	    msg, 'Create 3D Widget',
	    wx.ICON_ERROR | wx.OK_DEFAULT
	    )
      elif loaded:
        wc = WidgetContainer( self.grid, widget_class, self.state, no_init = no_init )
        self.AddWidgetContainer( wc, refit_flag )
      return  result
    #end check_3d_env

    Environment3D.LoadAndCall( check_3d_env )
  #end Create3DWidget


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._CreateToolBarItem()		-
  #----------------------------------------------------------------------
  def _CreateToolBarItem( self, tbar, tool_id, tool_def, enabled = False ):
    """It seems necessary to re-create tool items to show a different icon.
@param  tbar		owning toolbar
@param  tool_id		tool id
@param  tool_def	definition from TOOLBAR_ITEMS
@return			ToolBarToolBase
"""
    widget_icon = tool_def.get( 'icon' if enabled else 'iconDisabled' )
    widget_name = tool_def[ 'widget' ]
    widget_im = wx.Image(
        os.path.join( Config.GetResDir(), widget_icon ),
	wx.BITMAP_TYPE_PNG
	)

    tip = widget_name
    if not enabled:
      tip += ' (disabled)'

    tb_item = tbar.AddTool(
        tool_id, widget_im.ConvertToBitmap(),
        shortHelpString = tip
	)
    tb_item.Enable( enabled )
    self.Bind( wx.EVT_TOOL, self._OnWidgetTool, id = tool_id )

    return  tb_item
  #end _CreateToolBarItem


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.CreateWidget()			-
  #----------------------------------------------------------------------
  def CreateWidget( self, widget_class, refit_flag = True, no_init = False ):
    """Must be called on the UI thread.  Note we are determining the need
to load the 3D viz environment based on "3D" being in the class name.
This is precarious but fast for now to avoid the double O(n) lookups in
WIDGET_MAP and TOOLBAR_ITEMS
@return		WidgetContainer object for 2D, None for a 3D widget
"""
    wc = None

    #data_mgr = State.FindDataModelMgr( self.state )
    data_mgr = self.state.dataModelMgr
    if data_mgr is None or not data_mgr.HasData():
      msg = 'A VERAOutput file must be opened'
      wx.MessageDialog( self, msg, 'Add Widget' ).ShowWindowModal()

    else:
      try:
        if widget_class.find( '3D' ) >= 0:
          self.Create3DWidget( widget_class, refit_flag, no_init = no_init )
        else:
          wc = self.Create2DWidget( widget_class, refit_flag, no_init = no_init )
      except Exception, ex:
	self.logger.exception( 'Error creating widget' )
        wx.MessageDialog( self, str( ex ), 'Widget Error' ).ShowWindowModal()
    #end if-else

    return  wc
  #end CreateWidget


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.CreateWindow()			-
  #----------------------------------------------------------------------
  def CreateWindow( self, widget_props = None, no_widgets = False, no_init = False ):
    """Creates a new VeraViewFrame.  If widget_props is None and no_widgets
is False, the default processing of creating default widgets occurs.
@param  widget_props	optional widget serialization to deserialize in the
			new frame
@param  no_widget	True to to create an empty window
"""
    new_frame = VeraViewFrame( self.app, self.state, self.filepath )
    self.app.AddFrame( new_frame )
    new_frame.Show()

    # In AddFrame()
    #if Config.CanDragNDrop():
      #self.app.UpdateWindowMenus( add_frame = new_frame )

    skip_frames = [ new_frame ]
    if widget_props:
      wx.CallAfter( new_frame.UpdateFrame, widget_props = widget_props, no_init = no_init )

    elif no_widgets:
      wx.CallAfter( new_frame.UpdateFrame, no_widgets = no_widgets )

    wx.CallAfter( self.app.UpdateAllFrames, *skip_frames )
  #end CreateWindow


#  #----------------------------------------------------------------------
#  #	METHOD:		VeraViewFrame.FireStateChange()			-
#  #----------------------------------------------------------------------
#  def FireStateChange( self, reason ):
#    if reason != STATE_CHANGE_noop:
#      for child in self.GetChildren():
#        if isinstance( child, WidgetContainer ):
#	  child.HandleStateChange( reason )
#      #end for
#    #end if
#  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetApp()			        -
  #----------------------------------------------------------------------
  def GetApp( self ):
    """Not sure why this is necessary, but ``wx.App.Get()`` called in
DataModelMenu returns a ``wx.App`` instance, not a ``VeraViewApp`` instance.
However, calling ``self.binder.GetTopLevelParent().GetApp()`` returns a
``VeraViewApp`` instance.  Must be some sort of SWIG weirdness.
"""
    #return  wx.App.Get()  this works, too
    return  self.app
  #end GetApp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetConfig()			-
  #----------------------------------------------------------------------
  def GetConfig( self ):
    """Accessor for the config property.
@return			WidgetConfig object
"""
    return  self.config
  #end GetConfig


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetDataModelMgr()			-
  #----------------------------------------------------------------------
  def GetDataModelMgr( self ):
    """Convenience accessor for the state.dataModelMgr property.
@return			DataModelMgr object
"""
    #return  None if self.state is None else self.state.GetDataModel()
    return  State.FindDataModelMgr( self.state )
  #end GetDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetFirstWidgetContainer()		-
  #----------------------------------------------------------------------
  def GetFirstWidgetContainer( self ):
    """Retrieves the first WidgetContainer instance that is a child of
the grid.
@return			widget.WidgetContainer instance or None
"""
    result = None

    for wc in self.grid.GetChildren():
      if isinstance( wc, WidgetContainer ):
        result = wc
	break

    return  result
  #end GetFirstWidgetContainer


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetFrameId()			-
  #----------------------------------------------------------------------
  def GetFrameId( self ):
    """Accessor for the frameId property.
@return			1-based ordinal number
"""
    return  self.frameId
  #end GetFrameId


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.GetState()			-
  #----------------------------------------------------------------------
  def GetState( self ):
    """Accessor for the state property.
@return			State object
"""
    return  self.state
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
#		-- File Menu
#		--
    file_menu = wx.Menu()

#			-- File->New Submenu
    new_menu = wx.Menu()
    if Config.CanDragNDrop():
      new_window_item = wx.MenuItem( new_menu, wx.ID_ANY, '&Window\tCtrl+N' )
      self.Bind( wx.EVT_MENU, self._OnNewWindow, new_window_item )
      new_menu.AppendItem( new_window_item )
      new_menu.AppendSeparator()
    #end if
    self.fileNewMenu = new_menu

    widget_keys = WIDGET_MAP.keys()
    widget_keys.sort()
    #for k in WIDGET_MAP:
    for k in widget_keys:
      item = wx.MenuItem( new_menu, wx.ID_ANY, k )
      self.Bind( wx.EVT_MENU, self._OnNewWidget, item )
      new_menu.AppendItem( item )
    file_menu.AppendSubMenu( new_menu, '&New' )

#			-- Open File items

    open_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Open Single File...\tCtrl+O' )
    self.Bind( wx.EVT_MENU, self._OnOpenSingleFile, open_item )
    file_menu.AppendItem( open_item )

    open_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Open File Manager...\tShift+Ctrl+O' )
    self.Bind( wx.EVT_MENU, self._OnOpenFileMgr, open_item )
    file_menu.AppendItem( open_item )

#			-- Close File item
#x    self.closeFileItem = \
#x        wx.MenuItem( file_menu, wx.ID_ANY, '&Close File...\tShift+Ctrl+W' )
#x    self.Bind( wx.EVT_MENU, self._OnCloseFile, self.closeFileItem )
#x    file_menu.AppendItem( self.closeFileItem )
#x    self.closeFileItem.Enable( False )

#			-- Session items
    file_menu.AppendSeparator()

    load_session_item = wx.MenuItem( file_menu, wx.ID_ANY, 'Load Session...' )
    self.Bind( wx.EVT_MENU, self._OnLoadSession, load_session_item )
    file_menu.AppendItem( load_session_item )

    save_session_item = wx.MenuItem( file_menu, wx.ID_ANY, 'Save Session...' )
    self.Bind( wx.EVT_MENU, self._OnSaveSession, save_session_item )
    file_menu.AppendItem( save_session_item )

    restore_session_item = \
        wx.MenuItem( file_menu, wx.ID_ANY, 'Restore Previous Session' )
    self.Bind( wx.EVT_MENU, self._OnRestoreSession, restore_session_item )
    file_menu.AppendItem( restore_session_item )

    file_menu.AppendSeparator()
#			-- Save animated image
    anim_menu = wx.Menu()
    for sub_label in ( 'All Axial Levels', 'State Points' ):
      anim_item = wx.MenuItem( anim_menu, wx.ID_ANY, sub_label )
      self.Bind( wx.EVT_MENU, self._OnSaveAnimated, anim_item )
      anim_menu.AppendItem( anim_item )
    anim_item = wx.MenuItem(
        file_menu, wx.ID_ANY, 'Save Animated Image of All Widgets',
	subMenu = anim_menu
	)
    file_menu.AppendItem( anim_item )
#			-- Save images
    save_item = wx.MenuItem(
        file_menu, wx.ID_ANY,
	'&Save Image of All Widgets...\tCtrl+Shift+S'
	)
    self.Bind( wx.EVT_MENU, self._OnSaveImageAllWidgets, save_item )
    file_menu.AppendItem( save_item )

    file_menu.AppendSeparator()
    close_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Close Window\tCtrl+W' )
    self.Bind( wx.EVT_MENU, self._OnCloseWindow, close_item )
    file_menu.AppendItem( close_item )

    min_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Minimize Window\tCtrl+M' )
    self.Bind( wx.EVT_MENU, self._OnMinimizeWindow, min_item )
    file_menu.AppendItem( min_item )

    file_menu.AppendSeparator()
    quit_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Quit\tCtrl+Q' )
    self.Bind( wx.EVT_MENU, self._OnQuit, quit_item )
    file_menu.AppendItem( quit_item )

#		-- Edit Menu
#		--
    edit_menu = wx.Menu()
#    copy_item = wx.MenuItem( edit_menu, wx.ID_ANY, '&Copy\tCtrl+C' )
#    self.Bind( wx.EVT_MENU, self._OnCopy, copy_item )
#    edit_menu.AppendItem( copy_item )

    grid_item = wx.MenuItem( edit_menu, wx.ID_ANY, 'Resize &Grid\tCtrl+G' )
    self.Bind( wx.EVT_MENU, self._OnGridResize, grid_item )
    edit_menu.AppendItem( grid_item )

    edit_menu.AppendSeparator()

#Moved to data menu
#    self.dataSetMenu = \
#        DataSetsMenu( self.state, binder = self, mode = 'subsingle' )
#    dataset_item = wx.MenuItem(
#        edit_menu, wx.ID_ANY, 'Select Dataset',
#	subMenu = self.dataSetMenu
#	)
#    edit_menu.AppendItem( dataset_item )

#		 	-- Scale Mode
    scale_mode_menu = wx.Menu()
    check_item = None
    for label in sorted( SCALE_MODES.keys() ):
      item = wx.MenuItem( scale_mode_menu, wx.ID_ANY, label, kind = wx.ITEM_RADIO )
      scale_mode = SCALE_MODES.get( label )
      if scale_mode == 'all':
	check_item = item
      self.Bind( wx.EVT_MENU, self._OnScaleMode, item )
      scale_mode_menu.AppendItem( item )
      self.scaleModeItems[ scale_mode ] = item
    #end for
    if check_item:
      check_item.Check()
    scale_mode_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, 'Select Scale Mode',
	subMenu = scale_mode_menu
	)
    edit_menu.AppendItem( scale_mode_item )

#		 	-- Time Dataset
    self.timeDataSetMenu = wx.Menu()
    time_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, 'Select Time Dataset',
	subMenu = self.timeDataSetMenu
	)
    edit_menu.AppendItem( time_item )

#		 	-- Weights Mode
    weights_mode_menu = wx.Menu()
    check_item = None
    for label in sorted( WEIGHTS_MODES.keys() ):
      item = wx.MenuItem( weights_mode_menu, wx.ID_ANY, label, kind = wx.ITEM_RADIO )
      weights_mode = WEIGHTS_MODES.get( label )
      #if weights_mode == 'on':
      if weights_mode == self.state.weightsMode:
	check_item = item
      self.Bind( wx.EVT_MENU, self._OnWeightsMode, item )
      weights_mode_menu.AppendItem( item )
      self.weightsModeItems[ weights_mode ] = item
    #end for
    if check_item:
      check_item.Check()
    weights_mode_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, 'Select Weights Mode',
	subMenu = weights_mode_menu
	)
    edit_menu.AppendItem( weights_mode_item )

#		-- Data Menu
#		--
    data_menu = wx.Menu()

    derived_dataset_item = wx.MenuItem(
	data_menu, wx.ID_ANY, 'Create Derived Dataset...'
        )
    self.Bind( wx.EVT_MENU, self._OnCreateDerivedDataSet, derived_dataset_item )
    data_menu.AppendItem( derived_dataset_item )

    diff_dataset_item = wx.MenuItem(
	data_menu, wx.ID_ANY, 'Create Difference Dataset...'
        )
    self.Bind( wx.EVT_MENU, self._OnCreateDiffDataSet, diff_dataset_item )
    data_menu.AppendItem( diff_dataset_item )

    excore_file_item = wx.MenuItem(
	data_menu, wx.ID_ANY, 'Create Excore Output File...'
        )
    self.Bind( wx.EVT_MENU, self._OnCreateExcoreFile, excore_file_item )
    data_menu.AppendItem( excore_file_item )

    thresholds_file_item = wx.MenuItem(
	data_menu, wx.ID_ANY, 'Manage Dataset Thresholds...'
        )
    self.Bind( wx.EVT_MENU, self._OnManageThresholds, thresholds_file_item )
    data_menu.AppendItem( thresholds_file_item )

    data_menu.AppendSeparator()

    self.dataSetMenu = DataSetsMenu(
        self.state, binder = self, mode = 'subsingle',
	show_core_datasets = True
	)
    dataset_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, 'Select Dataset',
	subMenu = self.dataSetMenu
	)
    data_menu.AppendItem( dataset_item )

#		-- View Menu
#		--
#    view_menu = wx.Menu()
#    view3d_item = wx.MenuItem( view_menu, wx.ID_ANY, '3D Volume Slicer' )
#    self.Bind( wx.EVT_MENU, self._OnView3D, view3d_item )
#    view_menu.AppendItem( view3d_item )

#		-- Window Menu
#		--
    if Config.CanDragNDrop():
      self.windowMenu = wx.Menu()
      tile_item = wx.MenuItem( self.windowMenu, wx.ID_ANY, 'Tile Windows' )
      self.Bind( wx.EVT_MENU, self._OnTileWindows, tile_item )
      self.windowMenu.AppendItem( tile_item )
      self.windowMenu.AppendSeparator()
#    raise_all_item = wx.MenuItem( self.windowMenu, wx.ID_ANY, 'Bring All To Front' )
#    self.Bind( wx.EVT_MENU, self.RaiseAllWidgets, raise_all_item )
#    self.windowMenu.AppendItem( raise_all_item )
#    self.windowMenu.AppendSeparator()

#		-- Menu Bar
#		--
    mbar = wx.MenuBar()
    mbar.Append( file_menu, '&File' )
    mbar.Append( edit_menu, '&Edit' )
    mbar.Append( data_menu, '&Data' )
#    mbar.Append( view_menu, '&View' )
    if self.windowMenu:
      mbar.Append( self.windowMenu, '&Window' )
    self.SetMenuBar( mbar )

#		-- Widget Tool Bar
#		--
    # wx.{NO,RAISED,SIMPLE,SUNKEN}_BORDER
    tbar_panel = wx.Panel( self )
    widget_tbar = wx.ToolBar(
        tbar_panel, -1,
	style = wx.TB_HORIZONTAL | wx.SIMPLE_BORDER
	)
    self.widgetToolBar = widget_tbar
    #self._UpdateToolBar( widget_tbar )

    tbar_sizer = wx.BoxSizer( wx.HORIZONTAL )
    tbar_sizer.Add( widget_tbar, 1, wx.ALL | wx.EXPAND )
    logo_im = wx.Image(
        os.path.join( Config.GetResDir(), 'casl-logo.32.png' ),
	wx.BITMAP_TYPE_PNG
	)
    logo_busy_im = wx.Image(
        os.path.join( Config.GetResDir(), 'casl-logo-busy.32.png' ),
	wx.BITMAP_TYPE_PNG
	)
#    tbar_sizer.Add(
#	wx.StaticBitmap( tbar_panel, -1, logo_im.ConvertToBitmap() ),
#	0, wx.ALL | wx.ALIGN_RIGHT
#        )
    self.caslIcon = wx.StaticBitmap( tbar_panel, -1, logo_im.ConvertToBitmap() )
    self.caslIdleBitmap = logo_im.ConvertToBitmap()
    self.caslBusyBitmap = logo_busy_im.ConvertToBitmap()
    self.caslIconBg = self.caslIcon.GetBackgroundColour()
    #casl_icon.SetDropTarget( VeraViewFrameDropTarget( self ) )
    tbar_sizer.Add( self.caslIcon, 0, wx.ALL | wx.ALIGN_RIGHT )
    tbar_panel.SetSizer( tbar_sizer )
    self.widgetToolBarPanel = tbar_panel

#		-- Status Bar
#		--
    #status_bar = self.CreateStatusBar()
    #status_bar.SetStatusText( 'Creating...' )

#		-- Icons
#    icon_fname = os.path.join( os.path.dirname( __file__ ), 'reactor_icon.iconset', 'test128.gif' )
#    icon_img = wx.Image( icon_fname )
#    if 'wxMSW' in wx.PlatformInfo:
#      icon_img.Scale( 16, 16 )
#    elif 'wxGTK' in wx.PlatformInfo:
#      icon_img.Scale( 22, 22 )
#    self.SetIcon( wx.IconFromBitmap( icon_img.ConvertToBitmap() ) )

#		-- Axial slider
#		--
    inside_panel = wx.Panel( self )
    self.axialBean = AxialSliderBean( inside_panel )
    self.axialBean.Bind( EVT_AXIAL_LEVEL, self._OnAxial )
    self.axialBean.Enable()

#		-- Grid
#		--
    self.grid = VeraViewGrid( inside_panel, -1 )
#    self.grid.SetListener( self )

#		-- Exposure slider
#		--
    self.exposureBean = ExposureSliderBean( self )
    self.exposureBean.Bind( EVT_STATE_INDEX, self._OnExposure )
    self.exposureBean.Enable()

#		-- Lay Out
#		--
    inside_sizer = wx.BoxSizer( wx.HORIZONTAL )
    inside_sizer.Add( self.grid, 1, wx.ALL | wx.EXPAND )
    inside_sizer.Add( self.axialBean, 0, wx.ALL | wx.EXPAND, 1 )
    inside_panel.SetSizer( inside_sizer )

    vbox = wx.BoxSizer( wx.VERTICAL )
    #vbox.Add( widget_tbar, 0, wx.EXPAND, 0 )
    vbox.Add( tbar_panel, 0, wx.EXPAND, 0 )
    vbox.Add( inside_panel, 1, wx.EXPAND, 0 )
    vbox.Add( self.exposureBean, 0, wx.ALL | wx.EXPAND, 1 )
    self.SetSizer( vbox )
    vbox.Layout()
    self.Fit()
    self.SetTitle( TITLE )

#    self.Center()
    #pos = ( 5, 35 ) if 'wxMac' in wx.PlatformInfo else ( 5, 5 )
    #self.SetPosition( pos )
    client_rect = wx.GetClientDisplayRect()
    self.SetPosition( client_rect.GetPosition() )

    #display_size = wx.DisplaySize()
    display_size = client_rect.GetSize()
    #if display_size[ 0 ] >= 1200 and display_size[ 1 ] >= 800:
    if display_size[ 0 ] >= 1024 and display_size[ 1 ] >= 768:
      self.SetSize( ( 1024, 768 ) )
    elif display_size[ 0 ] >= 800 and display_size[ 1 ] >= 600:
      self.SetSize( ( 800, 600 ) )
    else:
      self.SetSize( ( 640, 480 ) )

    self.SetDropTarget( VeraViewFrameDropTarget( self ) )

#		-- Window Events
#		--
    self.state.AddListener( self )
    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )
    self.Bind( wx.EVT_CLOSE, self._OnCloseFrame )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._LoadWidgetConfig()		-
  #----------------------------------------------------------------------
  def _LoadWidgetConfig( self, widget_config, check_types = False ):
    """Updates based on a widget configuration.
Note this defines a new State as well as widgets in the grid.
@param  widget_config	WidgetConfig instance, cannot be None
@param  check_types	true to check widget dataset types
"""
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    #xxxxx recreate derived datasets

    self.state.LoadProps( widget_config.GetStateProps() )
    if check_types:
      dmgr = self.state.dataModelMgr

    self.CloseAllWidgets()
    grid_sizer = self.grid.GetSizer()
    ncols, nrows = widget_config.GetGridSize()
    grid_sizer.SetCols( ncols )
    grid_sizer.SetRows( nrows )

    for props in widget_config.GetWidgetProps():
      if 'classpath' in props:
#			-- 3D widgets won't auto load
	if props[ 'classpath' ].find( '3D' ) < 0:
          con = self.CreateWidget( props[ 'classpath' ], False )
	  con.LoadProps( props )

	  #xxx we need a cheaper way to check for the types
	  if check_types:
	    must_remove = True
	    for t in con.widget.GetDataSetTypes():
	      if dmgr.HasDataSetType( t ):
	        must_remove = False
	        addit = True
	    if must_remove:
	      con.OnClose( None )
	  #end if check_types
	#end if not 3D
      #end if classpath
    #end for props

    if self.state.scaleMode in self.scaleModeItems:
      self.scaleModeItems[ self.state.scaleMode ].Check()

    if self.state.weightsMode in self.weightsModeItems:
      self.weightsModeItems[ self.state.weightsMode ].Check()

    fr_pos = widget_config.GetFramePosition()
    fr_size = widget_config.GetFrameSize()
    if fr_size[ 0 ] > 0 and fr_size[ 1 ] > 0:
      # Ensure window will appear on screen (not cut off or hidden)
      display_size = wx.DisplaySize()
      xmin = 0
      ymin = 0
      if not Config.IsWindows():
        ymin = 23 # space for menu bar on linux/mac (sized for mac)
      xpos = max(min(fr_pos[0], (display_size[0] - fr_size[0])), xmin)
      ypos = max(min(fr_pos[1], (display_size[1] - fr_size[1])), ymin)

      self.SetPosition((xpos, ypos))
      self.SetSize( fr_size )
    #self.dataSetMenu.Init()
  #end _LoadWidgetConfig


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnAxial()			-
  #----------------------------------------------------------------------
  def _OnAxial( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()
    value = ev.value
    self.app.DoBusyEventOp( self._OnAxialImpl, value )
  #end _OnAxial


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnAxialImpl()			-
  #----------------------------------------------------------------------
  def _OnAxialImpl( self, value ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    reason = STATE_CHANGE_noop
    dmgr = self.state.dataModelMgr
    if dmgr:
      axial_value = dmgr.GetAxialValue( core_ndx = value )
      if axial_value and axial_value.cm >= 0.0:
        reason = self.state.Change( self.eventLocks, axial_value = axial_value )
    #end if dmgr

    if reason != STATE_CHANGE_noop:
      self.state.FireStateChange( reason )
  #end _OnAxialImpl


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_DOWN:
      self.axialBean.Decrement()
    elif code == wx.WXK_LEFT:
      self.exposureBean.Decrement()
    elif code == wx.WXK_RIGHT:
      self.exposureBean.Increment()
    elif code == wx.WXK_UP:
      self.axialBean.Increment()
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCloseFile()			-
  #----------------------------------------------------------------------
  def _OnCloseFile( self, ev ):
    """Used for a File:Close menu item.
Must be called from the UI thread.
"""
    if ev is not None:
      ev.Skip()

    dialog = None
    try:
      model_names = None
      if self.state.dataModelMgr is not None:
        model_names = self.state.dataModelMgr.GetDataModelNames()

      if model_names:
        #if self.state.dataModelMgr.GetDataModelCount() == 1:
        if False:
          dialog = wx.MessageDialog(
	      self, 'Last File, Quit VERAView?', 'Close File',
	      wx.ICON_QUESTION | wx.YES_NO | wx.YES_DEFAULT
	      )
          if dialog.ShowModal() == wx.ID_YES:
	    self._OnQuit( None )

        else:
          dialog = wx.SingleChoiceDialog(
	      self, 'Select File to Close:', 'Close File',
	      sorted( model_names ),
	      wx.CHOICEDLG_STYLE
              )
          if dialog.ShowModal() == wx.ID_OK:
	    self.state.LogListeners( self.logger, 'Before CloseModel()' )
	    self.state.dataModelMgr.CloseModel( dialog.GetStringSelection() )
	    self.state.LogListeners( self.logger, 'After CloseModel()' )
	    wx.CallAfter( self.app.UpdateAllFrames )
      #end if model_names

    finally:
      if dialog is not None:
        dialog.Destroy()
  #end _OnCloseFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCloseFrame()			-
  #----------------------------------------------------------------------
  def _OnCloseFrame( self, ev ):
    """Called on EVT_CLOSE event.
"""
    if len( self.app.GetFrameRecs() ) == 1:
#			-- Windows focus hack
      win = wx.Window_FindFocus()
      if win is not None:
        win.Disconnect( -1, -1, wx.wxEVT_KILL_FOCUS )

      self._OnQuit( None )

    else:
      frame = ev.GetEventObject()
      self._CloseFrame( frame )
  #end _OnCloseFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCloseFrame_singleWindow()	-
  #----------------------------------------------------------------------
  def _OnCloseFrame_singleWindow( self, ev ):
#	-- Windows focus hack
    win = wx.Window_FindFocus()
    if win is not None:
      win.Disconnect( -1, -1, wx.wxEVT_KILL_FOCUS )
#
    #self._OnQuit( None )
  #end _OnCloseFrame_singleWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCloseWindow()			-
  #----------------------------------------------------------------------
  def _OnCloseWindow( self, ev ):
    """Menu item handler.
"""
    ev.Skip()

    match = None
    for rec in six.itervalues( self.app.GetFrameRecs() ):
      frame = rec.get( 'frame' )
      if frame and frame.IsActive():
        match = frame
	break
    #end for rec

    if match:
      if len( self.app.GetFrameRecs() ) == 1:
        self._OnQuit( None )
      else:
#			-- Sends close event, so _OnCloseFrame() will be called
	match.Close()
  #end _OnCloseWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnControlTool()			-
  #----------------------------------------------------------------------
  def _OnControlTool( self, ev ):
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    ev.Skip()

    tbar = ev.GetEventObject()
    if ev.GetId() == ID_REFIT_WINDOW:
      self._Refit( True )
  #end _OnControlTool


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCopy()				-
  #----------------------------------------------------------------------
  def _OnCopy( self, ev ):
    ev.Skip()

    if not wx.TheClipboard.Open():
      wx.MessageDialog(
          self, 'Could not open the clipboard', 'Copy Data',
	  style = wx.ICON_WARNING | wx.OK
	  ).\
	  ShowWindowModal()

    else:
      try:
	wx.TheClipboard.SetData( wx.TextDataObject( "xxx" ) )

      except Exception, ex:
	self.logger.exception( 'Clipboard copy error' )
        wx.MessageDialog(
            self, 'Could not open the clipboard', 'Copy Data',
	    style = wx.ICON_WARNING | wx.OK
	    ).\
	    ShowWindowModal()

      finally:
	wx.TheClipboard.Close()
    #end if-else
  #end _OnCopy


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCreateDerivedDataSet()		-
  #----------------------------------------------------------------------
  def _OnCreateDerivedDataSet( self, ev ):
    ev.Skip()

    dialog = DataSetCreatorDialog( self, state = self.state )
    try:
      dialog.ShowModal()
    finally:
      dialog.Destroy()
  #end _OnCreateDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCreateDiffDataSet()		-
  #----------------------------------------------------------------------
  def _OnCreateDiffDataSet( self, ev ):
    ev.Skip()

    dialog = DataSetDiffCreatorDialog( self, self.state )
    try:
      dialog.ShowModal()
    finally:
      dialog.Destroy()
  #end _OnCreateDiffDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCreateExcoreFile()		-
  #----------------------------------------------------------------------
  def _OnCreateExcoreFile( self, ev ):
    ev.Skip()

    dialog = ExcoreOutputDialog( self )
    try:
      dialog.ShowModal()
    finally:
      dialog.Destroy()
  #end _OnCreateExcoreFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnExposure()			-
  #----------------------------------------------------------------------
  def _OnExposure( self, ev ):
    """Handles events from the exposure slider.  Called on the UI thread.
"""
    ev.Skip()
    value = ev.value
    self.app.DoBusyEventOp( self._OnExposureImpl, value )
  #end _OnExposure


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnExposureImpl()			-
  #----------------------------------------------------------------------
  def _OnExposureImpl( self, value ):
    """Handles events from the exposure slider.  Called on the UI thread.
"""
    reason = STATE_CHANGE_noop
    dmgr = self.state.dataModelMgr
    if dmgr:
      value = dmgr.GetTimeIndexValue( value )
      if value >= 0.0:
        reason = self.state.Change( self.eventLocks, time_value = value )
    #end if dmgr

    if reason != STATE_CHANGE_noop:
      self.state.FireStateChange( reason )
  #end _OnExposureImpl


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnManageDataSets()		-
  #----------------------------------------------------------------------
#  def _OnManageDataSets( self, ev ):
#    ev.Skip()
#
#    msg = None
#    data_model = self.GetDataModel()
#
#    if data_model is None:
#      msg = 'No VERAOutput file has been read'
#
#    elif len( data_model.GetStates() ) == 0:
#      msg = 'No state points read from VERAOutput file'
#
#    if msg is not None:
#      wx.MessageDialog( self, msg, 'Manage Extra DataSets' ).ShowWindowModal()
#
#    else:
#      dialog = DataSetManagerDialog( self, data_model = data_model )
#      dialog.ShowModal()
#      data_model.ReadExtraDataSets()
#      dialog.Destroy()
#    #end if-else
#  #end _OnManageDataSets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnManageThresholds()		-
  #----------------------------------------------------------------------
  def _OnManageThresholds( self, ev ):
    ev.Skip()

    dialog = \
        RangeDialog( self, state = self.state, title = 'Dataset Thresholds' )
    try:
      dialog.ShowModal()
      self.state.FireStateChange( STATE_CHANGE_forceRedraw )
    finally:
      dialog.Destroy()
#      if hasattr( wx, 'AppConsole' ):
#        wx.AppConsole.Yield()
#      else:
#        wx.Yield()
  #end _OnManageThresholds


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnGridResize()			-
  #----------------------------------------------------------------------
  def _OnGridResize( self, ev ):
    ev.Skip()

    grid_sizer = self.grid.GetSizer()
    cur_size = ( grid_sizer.GetRows(), grid_sizer.GetCols() )

    dialog = GridSizerDialog( None )
    dialog.ShowModal( cur_size )
    new_size = dialog.GetResult()
    if new_size is not None and new_size != cur_size:
      proceed = True
      cell_count = new_size[ 0 ] * new_size[ 1 ]
      widget_count = len( self.grid.GetChildren() )
      if widget_count > cell_count:
	message = \
	    'That would be too few grids for all your widgets.\n' + \
	    'Delete some widgets first.'
        wx.MessageDialog(
	    self, message, 'Resize Grid',
	    style = wx.OK
	    ).\
	    ShowWindowModal()
	proceed = False

      elif cell_count > 16:
	message = \
	    'You have defined more than 16 widget windows!\n' + \
	    'You must have a really big screen.  Are you sure?'
        choice = wx.MessageDialog(
	    self, message,
	    'Resize Grid',
	    style = wx.ICON_QUESTION | wx.YES_NO
	    ).\
	    ShowWindowModal()
	proceed = choice == wx.ID_YES
      #end if-else on widget_count

      if proceed:
        grid_sizer.SetRows( new_size[ 0 ] )
        grid_sizer.SetCols( new_size[ 1 ] )
	self._Refit( True )
    #end if different size
  #end _OnGridResize


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnLoadSession()			-
  #----------------------------------------------------------------------
  def _OnLoadSession( self, ev ):
    ev.Skip()

    path = None
    dialog = wx.FileDialog(
	self, 'Load Session', '', '',
	'VERAView session files (*.vview)|*.vview',
	wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
        )
    if dialog.ShowModal() != wx.ID_CANCEL:
      path = dialog.GetPath()
      dialog.Destroy()

    if path is not None:
      try:
        config = WidgetConfig( path )
        self.state.dataModelMgr.Close()
	self.OpenFile( config.GetDataModelPaths(), config )
	self._LoadWidgetConfig( config, True )
      except Exception, ex:
	self.logger.exception( 'Error loading session' )
        msg = 'Error loading session:' + os.linesep + str( ex )
        self.ShowMessageDialog( msg, 'Load Session' )

    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'exiting' )
  #end _OnLoadSession


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnMinimizeWindow()		-
  #----------------------------------------------------------------------
  def _OnMinimizeWindow( self, ev ):
    ev.Skip()
    self.Iconize( True )
  #end _OnMinimizeWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnNewWidget()			-
  #----------------------------------------------------------------------
  def _OnNewWidget( self, ev ):
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    ev.Skip()

    title = None
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item is not None and item.GetLabel() in WIDGET_MAP:
      self.CreateWidget( WIDGET_MAP[ item.GetItemLabelText() ] )
  #end _OnNewWidget


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnNewWindow()			-
  #----------------------------------------------------------------------
  def _OnNewWindow( self, ev ):
    if ev:
      ev.Skip()
    self.CreateWindow( no_widgets = True )
  #end _OnNewWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnOpenFile()			-
  #----------------------------------------------------------------------
  def _OnOpenFile( self, ev ):
    """This handles opening an additional file.
Must be called from the UI thread.
"""
    if ev is not None:
      ev.Skip()

    if self.state.dataModelMgr is not None:
      self._UpdateConfig()

    dialog = wx.FileDialog(
	self, 'Open File', '', '',
        'HDF5 files (*.h5)|*.h5|VERAView session files (*.vview)|*.vview',
	wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
        )

    path = None
    if dialog.ShowModal() != wx.ID_CANCEL:
      path = dialog.GetPath()
    dialog.Destroy()

    if path:
      path, session = self._ResolveFile( path )
      self.OpenFile( path, session )
  #end _OnOpenFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnOpenFileMgr()			-
  #----------------------------------------------------------------------
  def _OnOpenFileMgr( self, ev ):
    """
Must be called from the UI thread.
"""
    if ev is not None:
      ev.Skip()

    if self.state.dataModelMgr is None:
      wx.MessageBox(
	  'No DataModelMgr exists!  Contact the VERAView development team!',
          'Application Error',
	  wx.ICON_WARNING | wx.OK_DEFAULT,
	  None
          )
    else:
      self._UpdateConfig()
      dialog = FileManagerDialog( self, dmgr = self.state.dataModelMgr )
      dialog.ShowModal()

      wx.CallAfter(
          self.UpdateFrame,
          ','.join( self.state.dataModelMgr.GetDataModelNames() )
	  )
      wx.CallAfter( self.app.UpdateAllFrames, self )
    #end else self.state.dataModelMgr is not None
  #end _OnOpenFileMgr


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnOpenSingleFile()		-
  #----------------------------------------------------------------------
  def _OnOpenSingleFile( self, ev ):
    """This handles opening an single file, closing all existing open files.
Must be called from the UI thread.
"""
    if ev is not None:
      ev.Skip()

    if self.state.dataModelMgr is None:
      wx.MessageBox(
	  'No DataModelMgr exists!  Contact the VERAView development team!',
          'Application Error',
	  wx.ICON_WARNING | wx.OK_DEFAULT,
	  None
          )
    else:
      self._UpdateConfig()

      dialog = wx.FileDialog(
	  self, 'Open File', '', '',
          'HDF5 files (*.h5)|*.h5|VERAView session files (*.vview)|*.vview',
	  wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
          )
      path = None
      if dialog.ShowModal() != wx.ID_CANCEL:
        path = dialog.GetPath()
      dialog.Destroy()

      if path:
        path, session = self._ResolveFile( path )

#        model_names = list( self.state.dataModelMgr.GetDataModelNames() )
#	for n in model_names:
#	  self.state.dataModelMgr.CloseModel( n )
        self.state.dataModelMgr.Close()

        self.OpenFile( path, session )
    #end else self.state.dataModelMgr is not None
  #end _OnOpenSingleFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnRestoreSession()               -
  #----------------------------------------------------------------------
  def _OnRestoreSession( self, ev ):
    ev.Skip()

    try:
      session = WidgetConfig.ReadUserSession()
      self.state.dataModelMgr.Close()
      self.OpenFile( session.GetDataModelPaths(), session )
      self._LoadWidgetConfig( session, True )

    except Exception, ex:
      self.logger.exception( 'Error restoring session' )
      msg = 'Error restoring session:' + os.linesep + str( ex )
      self.ShowMessageDialog( msg, 'Restore Session' )
  #end _OnRestoreSession


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnSaveAnimated()			-
  #----------------------------------------------------------------------
  def _OnSaveAnimated( self, ev ):
    """
Must be called on the UI event thread.
"""
    item = None
    if len( self.grid.GetChildren() ) == 0:
      wx.MessageBox(
          'No widgets defined', 'Save Animated Image',
	  wx.OK_DEFAULT, self
	  )
    else:
      menu = ev.GetEventObject()
      item = menu.FindItemById( ev.GetId() )

    if item is not None:
      try:
        animator = None
        label = item.GetLabel().lower()

	if label.find( 'all axial' ) >= 0:
	  animator = AllAxialAnimator(
	      VeraViewFrameAnimatorWidget( self ),
	      logger = self.logger
	      )

	elif label.find( 'state' ) >= 0:
	  animator = StatePointAnimator(
	      VeraViewFrameAnimatorWidget( self ),
	      logger = self.logger
	      )

        if animator is not None:
          self.SaveWidgetsAnimatedImage( animator )
      #end try

      except Exception, ex:
        wx.MessageBox(
	    'Cannot animate the widget, data missing:\n' + str( ex ),
	    'Save Animated Image', wx.OK_DEFAULT, self
	    )
    #end if item found
  #end _OnSaveAnimated


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnSaveImageAllWidgets()		-
  #----------------------------------------------------------------------
  def _OnSaveImageAllWidgets( self, ev ):
    """
Must be called on the UI event thread.
"""
    self.SaveWidgetsImage()
  #end _OnSaveImageAllWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnSaveSession()			-
  #----------------------------------------------------------------------
  def _OnSaveSession( self, ev ):
    ev.Skip()

    dialog = wx.FileDialog(
        self, 'Save Session', '', '',
	'VERAView session files (*.vview)|*.vview',
	wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	)

    if dialog.ShowModal() != wx.ID_CANCEL:
      file_path = dialog.GetPath()
      dialog.Destroy()
      try:
        self.SaveSession( file_path )
      except Exception, ex:
	self.logger.exception( 'Error saving session' )
        msg = 'Error saving session:' + os.linesep + str( ex )
        self.ShowMessageDialog( msg, 'Save Session' )
  #end _OnSaveSession


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnScaleMode()			-
  #----------------------------------------------------------------------
  def _OnScaleMode( self, ev ):
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item is not None:
      mode = SCALE_MODES.get( item.GetLabel(), 'all' )
      reason = self.state.Change( self.eventLocks, scale_mode = mode )
      self.state.FireStateChange( reason )
    #end if
  #end _OnScaleMode


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.OnStateChange()			-
  #----------------------------------------------------------------------
  def OnStateChange( self, reason ):
    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( '[VeraViewFrame.OnStateChange] reason=%d', reason )

#    init_mask = STATE_CHANGE_init | STATE_CHANGE_dataModelMgr
#    if (reason & init_mask) > 0:
#      wx.CallAfter( self.UpdateFrame, widget_props = 'noop' )

    if (reason & STATE_CHANGE_axialValue) > 0:
      dmgr = self.state.dataModelMgr
      if dmgr.HasData():
        global_ax_value = dmgr.GetAxialValue( cm = self.state.axialValue[ 0 ] )
	#if global_ax_value[ 1 ] != self.axialBean.axialLevel:
          #self.axialBean.axialLevel = global_ax_value[ 1 ]
	if global_ax_value.pinIndex != self.axialBean.axialLevel:
          self.axialBean.axialLevel = global_ax_value.pinIndex

    if (reason & STATE_CHANGE_timeValue) > 0:
      dmgr = self.state.dataModelMgr
      if dmgr.HasData():
        state_ndx = dmgr.GetTimeValueIndex( self.state.timeValue )
	if state_ndx != self.exposureBean.stateIndex:
	  self.exposureBean.stateIndex = state_ndx
    #end if STATE_CHANGE_timeValue
  #end OnStateChange


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnTileWindows()			-
  #----------------------------------------------------------------------
  def _OnTileWindows( self, ev ):
    ev.Skip()

#		-- Determine number of tile rows
#		--
    #display_size = wx.DisplaySize()
    display_rect = wx.GetClientDisplayRect()
    display_left = display_rect.GetLeft()
    display_top = display_rect.GetTop()
    display_wd = display_rect.GetWidth()
    display_ht = display_rect.GetHeight()
#Not necessary
#    if 'wxMac' in wx.PlatformInfo:
#      display_ht -= 32
#      display_top += 32

    count = len( self.app.GetFrameRecs() )
    frows = math.sqrt( count * display_ht / float( display_wd ) )
    rows100 = int( frows * 100.0 )
    rounder = rows100 % 100
    if rounder >= 50:
      rows100 += 100
    nrows = max( 1, rows100 / 100 )
    ncols = (count + nrows - 1) / nrows

#		-- Window size
#		--
    win_wd = int( display_wd / ncols )
    win_ht = int( display_ht / nrows )
    win_size = ( win_wd, win_ht )

    col = row = 0
    win_x = display_left
    win_y = display_top

    for frame_rec in self.app.GetFrameRecs().values():
      fr = frame_rec.get( 'frame' )
      if fr:
        fr.SetPosition( ( win_x, win_y ) )
	fr.SetSize( win_size )
	fr.Iconize( False )
	fr.Raise()

	col += 1
	if col > ncols:
	  win_x = display_left
	  col = 0
	  row += 1
	  win_y += win_ht
	else:
	  win_x += win_wd
	#end if-else ncols exceeded
      #end if fr
    #end for
  #end _OnTileWindows


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnQuit()				-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    dmgr = self.state.dataModelMgr
    try:
      #if self.app.filepath is not None:
      if dmgr.GetDataModelCount() > 0:
        self.SaveSession()
    except Exception, ex:
      self.logger.exception( 'Error saving session on quit' )
      msg = 'Error saving session:' + os.linesep + str( ex )
      # dialog flashes, not modal.
      #self.ShowMessageDialog( msg, 'Save Session' )
      if self.logger.isEnabledFor( logging.ERROR ):
        self.logger.error( msg )
      wx.MessageBox(
          msg, 'Save Configuration',
	  wx.ICON_WARNING | wx.OK_DEFAULT,
	  None
          )

    if dmgr is not None:
      dmgr.Close()
    #self.Close()
    wx.App.Get().ExitMainLoop()
  #end _OnQuit


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnTimeDataSet()			-
  #----------------------------------------------------------------------
  def _OnTimeDataSet( self, ev ):
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item is not None:
      title = item.GetLabel()
      reason = self.state.Change( self.eventLocks, time_dataset = title )
      #self.state.RemoveListener( self )
      self.state.FireStateChange( reason )
      #self.state.AddListener( self )
    #end if
  #end _OnTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnWeightsMode()			-
  #----------------------------------------------------------------------
  def _OnWeightsMode( self, ev ):
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item is not None:
      mode = WEIGHTS_MODES.get( item.GetLabel(), 'on' )
      reason = self.state.Change( self.eventLocks, weights_mode = mode )
      self.state.FireStateChange( reason )
    #end if
  #end _OnWeightsMode


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnWidgetTool()			-
  #----------------------------------------------------------------------
  def _OnWidgetTool( self, ev ):
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'entered' )
    ev.Skip()

    tbar = ev.GetEventObject()
    item = tbar.FindById( ev.GetId() )
    if item is not None and item.GetShortHelp() in WIDGET_MAP:
      self.CreateWidget( WIDGET_MAP[ item.GetShortHelp() ] )
  #end _OnWidgetTool


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnWindowMenuItem()		-
  #----------------------------------------------------------------------
  def _OnWindowMenuItem( self, ev ):
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item is not None:
      title = item.GetLabel()
      frame_rec = self.app.FindFrameByTitle( title )
      if frame_rec:
        frame = frame_rec.get( 'frame' )
	if frame:
	  frame.Iconize( False )
	  frame.Raise()
      #end if frame_rec
    #end if item

#      for child in self.GetChildren():
#        if isinstance( child, WidgetContainer ) and child.GetTitle() == title:
#	  child.Iconize( False )
#          child.Raise()
#	  break
#      #end for
    #end if
  #end _OnWindowMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.OpenFile()			-
  #----------------------------------------------------------------------
  def OpenFile( self, file_paths, session = None ):
    """
May be called from any thread.
"""
    #self.CloseAllWidgets()

#    msg = \
#        ', '.join( file_paths )  if hasattr( file_paths, '__iter__' ) else \
#	str( file_paths )
#    dialog = wx.ProgressDialog( 'Open File', 'Reading files: %s' % msg )
    names = \
        os.linesep.join( file_paths ) \
        if hasattr( file_paths, '__iter__' ) else \
	str( file_paths )

    dialog = wx.ProgressDialog(
        'Open File',
        'Reading files:{0}{1}'.format( os.linesep, names )
        )
    dialog.Show()

#    wxlibdr.startWorker(
#	self._OpenFileEnd,
#	self._OpenFileBegin,
#	wargs = [ dialog, file_paths, session ]
#	#wkwargs = { 'config': config, 'session': session }
#        )

    if threading.current_thread().name == 'MainThread':
      result = self._OpenFileBegin( dialog, file_paths, session )
      self._OpenFileEnd( wxlibdr.DelayedResult( result ) )
    else:
      wxlibdr.startWorker(
	  self._OpenFileEnd,
	  self._OpenFileBegin,
	  wargs = [ dialog, file_paths, session ]
	  #wkwargs = { 'config': config, 'session': session }
          )
  #end OpenFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OpenFileBegin()			-
  #----------------------------------------------------------------------
  def _OpenFileBegin( self, dialog, file_paths, session = None ):
    """
"""
    dialog.Pulse()
    status = \
      {
      'dialog': dialog,
      'file_paths': file_paths,
      'session': session
      }

    try:
      dmgr = self.state.dataModelMgr
      html_message = ''
      warning_messages = []

      if not hasattr( file_paths, '__iter__' ):
        file_paths = [ file_paths ]

      data_model = None
      for f in file_paths:
	try:
	  self.state.LogListeners( self.logger, 'Before OpenModel()' )
          dm = dmgr.OpenModel( f )
	  warning_messages += dm.GetReadMessages()
	  self.state.LogListeners( self.logger, 'After OpenModel()' )
	  if not data_model:
	    data_model = dm

	  #messages += dm.Check()
	  messages = dm.Check()
	  if messages:
	    cur_message = '\n<h3>' + f + '</h3>\nMissing:\n<ul>\n'
	    for m in messages:
	      cur_message += '<li>' + m + '</li>\n'
	    cur_message += '</ul>\n'
	    html_message += cur_message
	  #end if messages

	except HtmlException, ex:
	  html_message += '\n<h3>' + f + '</h3>\n' + ex.htmlMessage

        except Exception, ex:
	  html_message += '\n<h3>' + f + '</h3>\n' + str( ex )
      #end for f

      status[ 'data_model' ] = data_model
      status[ 'html_message' ] = html_message
      status[ 'warning_messages' ] = warning_messages
      #status[ 'messages' ] = messages

    except Exception, ex:
      status[ 'messages' ] = \
        [ 'Error opening data file(s):' + os.linesep + str( ex ) ]

    return  status
  #end _OpenFileBegin


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OpenFileEnd()			-
  #----------------------------------------------------------------------
  def _OpenFileEnd( self, result ):
    """On UI thread.
"""
    #status = result.get()
    if isinstance( result, dict ):
      status = result
    else:
      status = result.get()
    if status is not None:
      if 'dialog' in status:
	dlg = status[ 'dialog' ]
	#dlg.Lower()
	dlg.Hide()
	dlg.Destroy()

      html_message = status.get( 'html_message' )
      if html_message:
	HtmlMessageDialog.ShowBox(
	    HtmlMessageDialog.CreateDocument( html_message ),
	    'Cannot Open File(s)', self
	    )

      elif 'messages' in status and len( status[ 'messages' ] ) > 0:
	msg = \
	    'Data file cannot be processed:\n' + \
	    '\n  '.join( status[ 'messages' ] )
	self.ShowMessageDialog( msg, 'Open File' )

      elif 'data_model' in status and 'file_paths' in status and \
          len( status[ 'file_paths' ] ) > 0:
	dmgr = self.state.dataModelMgr
	#if dmgr.GetDataModelCount() == 1:
	  #self.state.Init()
	session = status.get( 'session' )
	display_path = status[ 'file_paths' ][ 0 ]
	#display_path = status[ 'data_model' ].GetH5File().filename

	warnings = status.get( 'warning_messages' )
	if warnings:
	  self.ShowMessageDialog( '\n'.join( warnings ), 'File Warnings' )

	wx.CallAfter( self.UpdateFrame, display_path, session )
	wx.CallAfter( self.app.UpdateAllFrames, self )
      #end if-elif
    #end if status
  #end _OpenFileEnd


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._Refit()				-
  #----------------------------------------------------------------------
  def _Refit( self, apply_widget_ratio = False, *additionals ):
    display_size = wx.DisplaySize()
    frame_size = self.GetSize()
    if frame_size[ 0 ] > display_size[ 0 ] or \
        frame_size[ 1 ] > display_size[ 1 ]:
      if not self.IsMaximized():
        self.Maximize()
        frame_size = self.GetSize()

    #grid_size = self.grid.GetSize()
    #if grid_size[ 0 ] > new_size[ 0 ] or grid_size[ 1 ] > new_size[ 1 ] :
    self.grid.FitWidgets( apply_widget_ratio )
    self.Fit()

    if additionals:
      additionals[ 0 ]( *additionals[ 1 : ] )
  #end _Refit


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._ResolveFile()			-
  #----------------------------------------------------------------------
  def _ResolveFile( self, path ):
    """Checks the path for a session (.vview) file.
@param  path		file path
@return			data_model_paths, session
"""
    session = None
    if path.endswith( '.vview' ):
      session = WidgetConfig( path )
      data_paths = session.GetDataModelPaths()
    else:
      data_paths = [ path ]

    return  data_paths, session
  #end _ResolveFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._ResolveTitle()			-
  #----------------------------------------------------------------------
  def _ResolveTitle( self, title ):
    """
@deprecated from multi-window days.
"""
    result = title
#    last = 0
#    for item in self.windowMenu.GetMenuItems():
#      text = item.GetLabel()
#      colon_ndx = text.find( ':' )
#      if colon_ndx > 0:
#        number = int( text[ : colon_ndx ] )
#	last = max( number, last )
#      #end if
#    #end for
#
#    result = '%d: %s' % ( last + 1, title )
    return  result
  #end _ResolveTitle


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SaveSession()			-
  #----------------------------------------------------------------------
  def SaveSession( self, file_path = None ):
    """
@param  file_path	path of VERAView (.vview) file or None to save the
			user session file
"""
    #xxxxx list derived datasets to be re-created
    config = WidgetConfig()

    fr_pos = self.GetPosition()
    fr_size = self.GetSize()
    config.SetFramePosition( fr_pos[ 0 ], fr_pos[ 1 ] )
    config.SetFrameSize( fr_size[ 0 ], fr_size[ 1 ] )
    #config.SetFrameSize( fr_size.GetWidth(), fr_size.GetHeight() )

    grid_sizer = self.grid.GetSizer()
    config.SetGridSize( grid_sizer.GetCols(), grid_sizer.GetRows() )

    config.SetState( self.state )

    widget_list = []
    for wc in self.grid.GetChildren():
      if isinstance( wc, WidgetContainer ):
        widget_list.append( wc.widget )

    config.AddWidgets( *widget_list )

    dmgr = self.state.dataModelMgr
    if dmgr is not None:
      data_paths = []
      for dm in dmgr.GetDataModels().values():
        hfp = dm.GetH5File()
        if hfp is not None:
	  data_paths.append( hfp.filename )

      config.SetDataModelPaths( *data_paths )

    config.Write( file_path )
  #end SaveSession


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SaveWidgetsAnimatedImage()	-
  #----------------------------------------------------------------------
  def SaveWidgetsAnimatedImage( self, animator, file_path = None ):
    """
Must be called from the UI event thread
"""
    first_wc = self.GetFirstWidgetContainer()
    if first_wc is not None:
      if self.animateOptionsDialog is None:
        self.animateOptionsDialog = AnimateOptionsDialog( self, -1 )

      if self.animateOptionsDialog.ShowModal() != wx.ID_CANCEL:
        file_path = first_wc._CheckAndPromptForAnimatedImage( file_path )
        if file_path is not None:
	  animator.Run(
	      file_path,
	      self.animateOptionsDialog.frame_delay,
	      self.animateOptionsDialog.show_selections
	      )
      #end if file_path is not None
    #end if we have a destination file path
  #end SaveWidgetsAnimatedImage


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SaveWidgetsAnimatedImage_1()	-
  #----------------------------------------------------------------------
##  def SaveWidgetsAnimatedImage_1( self, animator, file_path = None ):
##    """
##Must be called from the UI event thread
##"""
##    first_wc = self.GetFirstWidgetContainer()
##    if first_wc is not None:
##      file_path = first_wc._CheckAndPromptForAnimatedImage( file_path )
##      if file_path is not None:
##        answer = wx.MessageBox(
##	    'Show selections in images?',
##            'Save Widget Animated Image',
##	    wx.YES_NO, self
##	    )
##        animator.Run( file_path, answer == wx.YES )
##      #end if file_path is not None
##    #end if we have a destination file path
##  #end SaveWidgetsAnimatedImage_1


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SaveWidgetsImage()		-
  #----------------------------------------------------------------------
  def SaveWidgetsImage( self, file_path = None ):
    """
Must be called on the UI event thread.
"""
    if len( self.grid.GetChildren() ) == 0:
      self.ShowMessageDialog( 'No widgets to save', 'Save Image' )

    else:
      if file_path is None:
        dialog = wx.FileDialog(
	    self, 'Save Widgets Image', '', '',
	    'PNG files (*.png)|*.png',
	    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	    )
        if dialog.ShowModal() != wx.ID_CANCEL:
	  file_path = dialog.GetPath()
      #end if

      if file_path is not None:
        answer = wx.MessageBox(
	    'Show selections in images?',
            'Save Widget Animated Image',
	    wx.YES_NO, self
	    )
        try:
	  widgets = []
	  for wc in self.grid.GetChildren():
	    if isinstance( wc, WidgetContainer ):
	      widgets.append( wc.widget )

	  montager = WidgetImageMontager(
	      result_path = file_path,
	      widgets = widgets,
	      ncols = self.grid.GetSizer().GetCols(),
	      nrows = self.grid.GetSizer().GetRows(),
	      hilite = answer == wx.YES
	      )
	  montager.Run( 'Save Widgets Image' )

	except Exception, ex:
	  self.logger.exception( 'Error saving widgets image' )
	  msg = 'Error saving image:' + os.linesep + str( ex )
          self.ShowMessageDialog( msg, 'Save Image' )
      #end if
    #end else we have child widget containers
  #end SaveWidgetsImage


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SetConfig()			-
  #----------------------------------------------------------------------
  def SetConfig( self, value ):
    """Accessor for the config property.
@param  value		WidgetConfig object
"""
    self.config = value
  #end SetConfig


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.SetFrameId()			-
  #----------------------------------------------------------------------
  def SetFrameId( self, value ):
    """Accessor for the frameId property.
@param  value		1-based ordinal number
"""
    self.frameId = value
  #end SetFrameId


##  #----------------------------------------------------------------------
##  #	METHOD:		VeraViewFrame.ShowBusy()		        -
##  #----------------------------------------------------------------------
##  def ShowBusy( self, busy = True ):
##    """Should be called on MainThread.
##"""
##    def do_update( bmap ):
##      self.caslIcon.SetBitmap( bmap )
##      #self.caslIcon.SetBackgroundColour( color )
##      self.caslIcon.Update()
##    #end do_update
##
##    bmap = None
##
##    self.busyLock.acquire()
##    if busy:
##      if self.busyCount == 0:
##        bmap = self.caslBusyBitmap
##      self.busyCount += 1
##    else:
##      if self.busyCount == 1:
##        bmap = self.caslIdleBitmap
##      self.busyCount -= 1
##
##    self.busyLock.release()
##
##    if bmap:
##      if threading.current_thread().name == 'MainThread':
##        do_update( bmap )
##      else:
##        wx.CallAfter( do_update, bmap )
##  #end ShowBusy


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.ShowBusyIcon()		        -
  #----------------------------------------------------------------------
  def ShowBusyIcon( self, busy = True ):
    """Should be called on MainThread.
"""
    self.caslIcon.SetBitmap(
        self.caslBusyBitmap if busy  else self.caslIdleBitmap
        )
    self.caslIcon.Update()
  #end ShowBusyIcon


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.ShowMessageDialog()		-
  #----------------------------------------------------------------------
  def ShowMessageDialog( self, message, title ):
    """Must be called on the UI thread.
"""
    wx.MessageDialog( self, message, title ).ShowWindowModal()
  #end ShowMessageDialog


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._UpdateConfig()			-
  #----------------------------------------------------------------------
  def _UpdateConfig( self ):
    """Updates with current frame properties.
"""
    fr_pos = self.GetPosition()
    fr_size = self.GetSize()
    if self.config is None:
      self.config = WidgetConfig()

    self.config.SetFramePosition( fr_pos[ 0 ], fr_pos[ 1 ] )
    self.config.SetFrameSize( fr_size[ 0 ], fr_size[ 1 ] )
  #end _UpdateConfig


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.UpdateFrame()			-
  #----------------------------------------------------------------------
  def UpdateFrame(
      self, file_path = None, session = None, widget_props = None,
      no_widgets = False, no_init = False
      ):
    """Called when self.state.dataModelMgr changes.
Must be called from the UI thread.  Note in decreasing priority the params
session, widget_props, no_widgets are processed.
@param  file_path	optional path to VERAOutput file
@param  session		optional WidgetConfig instance for session restoration
@param  widget_props	widget properties (must have 'classpath') to create
			a single widget, where None means to apply default
			processing where applicable widgets are created if
			not previously intialized
@param  no_widgets	flags that no widgets are to be created
"""
    self.state.LogListeners( self.logger, 'Enter UpdateFrame()' )
    if self.logger.isEnabledFor( logging.DEBUG ):
      self.logger.debug( 'file_path=%s', file_path )

    dmgr = self.state.dataModelMgr
    core = dmgr.GetCore()
    time_values = dmgr.GetTimeValues()

    if file_path:
      self.filepath = file_path
      self.SetRepresentedFilename( file_path )

    #self.GetStatusBar().SetStatusText( 'Loading data model...' )

#		-- Update toolbar
#		--
# Merely enabling/disabling a tool by calling ToolBar.EnableTool() does
# not work!!  The same bitmap is used.  So, we re-create the tool.
    self._UpdateToolBar( self.widgetToolBar )

#		-- Update title
#		--
    self.UpdateTitle()

#		-- Initialize
#		--
    grid_sizer = self.grid.GetSizer()

#		-- 1. Highest priority is a session to load
#		--
    if session is not None:
      self._LoadWidgetConfig( session )
      self.dataSetMenu.Init()
      self.initialized = True

#		-- 2. Next, check for specific widget to create
#		--
    elif widget_props is not None:
      if 'classpath' in widget_props:
        self.CloseAllWidgets()
        grid_sizer.SetRows( 1 )
        grid_sizer.SetCols( 1 )

        wc = self.CreateWidget( widget_props[ 'classpath' ], no_init = no_init )
	if wc:
          wc.LoadProps( widget_props )
	# called in WidgetContainer.LoadProps()
        self.dataSetMenu.Init()
        self.initialized = True

#		-- 3. Next, skip default widget creation
#		--
    elif no_widgets:
      self.initialized = True
      self.dataSetMenu.Init()

#		-- 4. Finally, create widgets if not already initialized
#		--
    #elif widget_props is None:
    elif not self.initialized:
      self.initialized = True
      self.dataSetMenu.Init()

      self.CloseAllWidgets()
      widget_list = []
      has_axials = dmgr.HasDataSetType( 'axials' )
      has_pin = dmgr.HasDataSetType( 'pin' )
#      has_subpin = \
#          dmgr.HasDataSetType( 'subpin_r' ) or \
#          dmgr.HasDataSetType( 'subpin_theta' )
      has_subpin = dmgr.HasDataSetType( 'subpin_theta' )

      has_core = \
          has_pin or \
          dmgr.HasDataSetType( 'channel' ) or \
          dmgr.HasDataSetType( ':assembly' ) or \
          dmgr.HasDataSetType( ':chan_radial' ) or \
          dmgr.HasDataSetType( ':node' ) or \
          dmgr.HasDataSetType( ':radial' ) or \
          dmgr.HasDataSetType( ':radial_assembly' ) or \
          dmgr.HasDataSetType( ':radial_node' )

      if core.nass > 1 and has_core:
        widget_list.append( 'widget.core_view.Core2DView' )
#z        widget_list.append( 'widget.core_view_plot.Core2DPlot' )

#			-- Detector mode
#      if dmgr.HasDataSetType( 'detector' ):
#        widget_list.append( 'widget.detector_multi_view.Detector2DMultiView' )

#      if dmgr.HasDataSetType( 'fixed_detector' ):
#        if 'widget.detector_multi_view.Detector2DMultiView' not in widget_list:
#          widget_list.append( 'widget.detector_multi_view.Detector2DMultiView' )

#			-- Pin mode
      if has_pin:
        if core.nax > 1:
          widget_list.append( 'widget.core_axial_view.CoreAxial2DView' )
        widget_list.append( 'widget.assembly_view.Assembly2DView' )

#			-- Channel mode
#x      if len( data.GetDataSetNames( 'channel' ) ) > 0:
#x        if data.core.nass > 1:
#x          widget_list.append( 'widget.channel_view.Channel2DView' )
#x        widget_list.append( 'widget.channel_assembly_view.ChannelAssembly2DView' )
#x        if data.core.nax > 1:
#x          widget_list.append( 'widget.channel_axial_view.ChannelAxial2DView' )

#			-- Special check for Detector
#z      if 'widget.core_view_plot.Core2DPlot' not in widget_list and \
      if 'widget.core_view.Core2DView' not in widget_list and \
(dmgr.HasDataSetType( 'detector' ) or dmgr.HasDataSetType( 'fixed_detector' )):
        widget_list.append( 'widget.detector_multi_view.Detector2DMultiView' )

#			-- Subpin
      if has_subpin:
        if core.nax > 1:
          widget_list.append( 'widget.subpin_plot.SubPinPlot' )
          #widget_list.append( 'widget.subpin_view.SubPin2DView' )

#			-- Subpin Length
      if dmgr.HasDataSetType( 'subpin_cc' ):
        widget_list.append( 'widget.subpin_len_plot.SubPinLengthPlot' )

#			-- Axial plot?
      #if core.nax > 1:
      if has_axials and core.nax > 1:
        widget_list.append( 'widget.axial_plot.AxialPlot' )

#			-- Time plot?
      if len( time_values ) > 1:
        widget_list.append( 'widget.time_plots.TimePlots' )

      #if _debug_:
      if self.app.debug:
        widget_list = [
#            'widget.core_view_plot.Core2DPlot',
#            'widget.core_view.Core2DView',
#            'widget.assembly_view.Assembly2DView',
#            'widget.core_axial_view.CoreAxial2DView',
#            'widget.data_analysis_view.DataAnalysisView',
#            'widget.detector_multi_view.Detector2DMultiView',
            'widget.vessel_core_view.VesselCore2DView',
            'widget.vessel_core_axial_view.VesselCoreAxial2DView',
#            'widget.axial_plot.AxialPlot',
#            'widget.intrapin_edits_assembly_view.IntraPinEditsAssembly2DView',
#            'widget.intrapin_edits_plot.IntraPinEditsPlot',
#            'widget.subpin_view.SubPin2DView',
#            'widget.subpin_plot.SubPinPlot',
#            'widget.table_view.TableView',
#            'widget.time_plots.TimePlots',
            ]

      if self.config is None:
	widget_count = len( widget_list )
	cols = \
	    5 if widget_count > 8 else \
	    4 if widget_count > 6 else \
	    3 if widget_count > 4 else \
	    2 if widget_count > 1 else 1
	rows = 2 if widget_count > 1 else 1
	grid_sizer.SetCols( cols )
	grid_sizer.SetRows( rows )
      #end if config

#			-- Create widgets
#			--
      for w in widget_list:
        self.CreateWidget( w, False )
        if self.logger.isEnabledFor( logging.DEBUG ):
          self.logger.debug(
	      'widget added="%s", grid.size=%s',
	      w, str( self.grid.GetSize() )
	      )
      #end for

      fr_size = None if self.config is None else self.config.GetFrameSize()
      if fr_size is not None and fr_size[ 0 ] > 0 and fr_size[ 1 ] > 0:
        fr_pos = self.config.GetFramePosition()
        # Ensure window will appear on screen (not cut off or hidden)
        display_size = wx.DisplaySize()
        xmin = 0
        ymin = 0
        if not Config.IsWindows():
          ymin = 23 # space for menu bar on linux/mac (sized for mac)
        xpos = max(min(fr_pos[0], (display_size[0] - fr_size[0])), xmin)
        ypos = max(min(fr_pos[1], (display_size[1] - fr_size[1])), ymin)

        self.SetPosition((xpos, ypos))
        self.SetSize( fr_size )
      else:
        self._Refit( False )  # True

#			-- Add extra widget if space allows
#			--
      if not self.app.debug and \
          len( widget_list ) < (grid_sizer.GetCols() * grid_sizer.GetRows()):
        self.CreateWidget( 'widget.table_view.TableView', False )
    #end elif not self.initialized

#		-- Update various widgets
    self._UpdateTimeDataSetMenu()
    self.weightsModeItems[ self.state.weightsMode ].Check()

#		-- Set bean ranges and values
#		--
    axial_mesh_centers = dmgr.GetAxialMeshCenters()
    #axial_value = dmgr.GetAxialValue( cm = self.state.axialValue[ 0 ] )
    axial_value = dmgr.GetAxialValue( cm = self.state.axialValue.cm )
    self.axialBean.SetRange( 1, len( axial_mesh_centers ) )
    #self.axialBean.axialLevel = axial_value[ 1 ]
    self.axialBean.axialLevel = axial_value.pinIndex

    self.exposureBean.SetRange( 1, len( time_values ) )
    self.exposureBean.stateIndex = \
        dmgr.GetTimeValueIndex( self.state.timeValue )
    self.state.LogListeners( self.logger, 'Exit UpdateFrame()' )
  #end UpdateFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._UpdateTimeDataSetMenu()		-
  #----------------------------------------------------------------------
  def _UpdateTimeDataSetMenu( self ):
    """
"""
    dmgr = self.state.dataModelMgr

    while self.timeDataSetMenu.GetMenuItemCount() > 0:
      self.timeDataSetMenu.\
          DestroyItem( self.timeDataSetMenu.FindItemByPosition( 0 ) )

    ds_names = dmgr.ResolveAvailableTimeDataSets()
    for ds in sorted( ds_names ):
      item = wx.MenuItem(
          self.timeDataSetMenu, wx.ID_ANY, ds,
	  kind = wx.ITEM_RADIO
	  )
      self.Bind( wx.EVT_MENU, self._OnTimeDataSet, item )
      self.timeDataSetMenu.AppendItem( item )
      if ds == self.state.timeDataSet:
        item.Check();
    #end for
  #end _UpdateTimeDataSetMenu


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.UpdateTitle()			-
  #----------------------------------------------------------------------
  def UpdateTitle( self ):
    """
"""
    title = '%d: %s' % ( self.frameId, TITLE )
    if self.filepath:
      title += ':: %s' % os.path.basename( self.filepath )
    self.SetTitle( title )
  #end UpdateTitle


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._UpdateToolBar()			-
  #----------------------------------------------------------------------
  def _UpdateToolBar( self, tbar, enable_all = False ):
    """An irritating Mac bug results in the icon for removed tools hanging
around after the tool is deleted, so we work around this by creating
a new toolbar to replace the old one.
"""
    dmgr = self.state.dataModelMgr
    if tbar is None:
      tbar = self.widgetToolBar  # should have been passed in anyway

    widget_tbar = wx.ToolBar(
        self.widgetToolBarPanel, -1,
	style = wx.TB_HORIZONTAL | wx.SIMPLE_BORDER
	)

#		-- Needed if items will be destroyed?
    for i in xrange( len( TOOLBAR_ITEMS ) ):
      item = tbar.FindById( i + 1 )
      if item is not None:
        self.Unbind( wx.EVT_TOOL, item )
        #self.Unbind( wx.EVT_TOOL, self._OnWidgetTool, id = i + 1 )

    if dmgr is not None:
      ti_count = 1
      for ti in TOOLBAR_ITEMS:
        widget_icon = ti.get( 'icon' )
        if widget_icon is None:
          widget_tbar.AddSeparator()

        else:
          ds_type = ti[ 'type' ]

          enabled = \
	      enable_all or ds_type == '' or \
	      dmgr.HasDataSetType( ds_type )
	  if enabled and 'func' in ti:
	    enabled = ti[ 'func' ]( dmgr )

          if enabled:
            widget_icon = ti.get( 'icon' )
            widget_im = wx.Image(
                os.path.join( Config.GetResDir(), widget_icon ),
	        wx.BITMAP_TYPE_PNG
	        )

            tip = ti[ 'widget' ]
            tb_item = widget_tbar.AddTool(
                ti_count, widget_im.ConvertToBitmap(),
	        shortHelpString = tip
	        )
	    tb_item.Enable( enabled )
            self.Bind( wx.EVT_TOOL, self._OnWidgetTool, tb_item )

            ti_count += 1
          #end if enabled

#				-- File->New menu
	  mid = self.fileNewMenu.FindItem( ti[ 'widget' ] )
	  if mid != wx.NOT_FOUND:
	    self.fileNewMenu.FindItemById( mid ).Enable( enabled )
        #end if-else separator
      #end for ti
    #end if dmgr

    self.widgetToolBarPanel.GetSizer().Replace( tbar, widget_tbar )
    widget_tbar.Realize()
    self.widgetToolBarPanel.GetSizer().Layout()
    self.widgetToolBar = widget_tbar

    tbar.Destroy()
  #end _UpdateToolBar


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._UpdateToolBar_1()                -
  #----------------------------------------------------------------------
  def _UpdateToolBar_1( self, tbar, enable_all = False ):
    """An irritating Mac bug results in the icon for removed tools hanging
around after the tool is deleted, so we work around this by creating
a new toolbar to replace the old one.
"""
    dmgr = self.state.dataModelMgr
    if tbar is None:
      tbar = self.widgetToolBar  # should have been passed in anyway

    widget_tbar = wx.ToolBar(
        self.widgetToolBarPanel, -1,
	style = wx.TB_HORIZONTAL | wx.SIMPLE_BORDER
	)

#		-- Needed if items will be destroyed?
    for i in xrange( len( TOOLBAR_ITEMS ) ):
      item = tbar.FindById( i + 1 )
      if item is not None:
        self.Unbind( wx.EVT_TOOL, item )
        #self.Unbind( wx.EVT_TOOL, self._OnWidgetTool, id = i + 1 )

    if dmgr is not None:
      ti_count = 1
      for ti in TOOLBAR_ITEMS:
        widget_icon = ti.get( 'icon' )
        if widget_icon is None:
          widget_tbar.AddSeparator()

        else:
          ds_type = ti[ 'type' ]

          enabled = \
	      enable_all or ds_type == '' or \
	      dmgr.HasDataSetType( ds_type )
	  if enabled and 'func' in ti:
	    enabled = ti[ 'func' ]( dmgr )

          widget_icon = ti.get( 'icon' if enabled else 'iconDisabled' )
          widget_im = wx.Image(
              os.path.join( Config.GetResDir(), widget_icon ),
	      wx.BITMAP_TYPE_PNG
	      )

          tip = ti[ 'widget' ]
          if not enabled:
            tip += ' (disabled)'

          tb_item = widget_tbar.AddTool(
              ti_count, widget_im.ConvertToBitmap(),
	      shortHelpString = tip
	      )
	  tb_item.Enable( enabled )
          self.Bind( wx.EVT_TOOL, self._OnWidgetTool, tb_item )

#				-- File->New menu
	  mid = self.fileNewMenu.FindItem( ti[ 'widget' ] )
	  if mid != wx.NOT_FOUND:
	    self.fileNewMenu.FindItemById( mid ).Enable( enabled )
        #end if-else separator

        ti_count += 1
      #end for ti
    #end if dmgr

    self.widgetToolBarPanel.GetSizer().Replace( tbar, widget_tbar )
    widget_tbar.Realize()
    self.widgetToolBarPanel.GetSizer().Layout()
    self.widgetToolBar = widget_tbar

    tbar.Destroy()
  #end _UpdateToolBar_1


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._UpdateToolBar_sane()		-
  #----------------------------------------------------------------------
  def _UpdateToolBar_sane( self, tbar, enable_all = False ):
    """An irritating Mac bug results in the icon for removed tools hanging
around after the tool is deleted, so we work around this by creating
a new toolbar to replace the old one.
"""
    dmgr = self.state.dataModelMgr

    for i in xrange( len( TOOLBAR_ITEMS ) ):
      item = tbar.FindById( i + 1 )
      if item is not None:
        self.Unbind( wx.EVT_TOOL, item )
        #self.Unbind( wx.EVT_TOOL, self._OnWidgetTool, id = i + 1 )
    #tbar.ClearTools() doesn't remove separators
    while tbar.GetToolsCount() > 0:
      tbar.DeleteToolByPos( 0 )

    if dmgr is not None:
      ti_count = 1
      for ti in TOOLBAR_ITEMS:
        widget_icon = ti.get( 'icon' )
        if widget_icon is None:
          tbar.AddSeparator()

        else:
          ds_type = ti[ 'type' ]

          enabled = \
	      enable_all or ds_type == '' or \
	      dmgr.HasDataSetType( ds_type )
	  if enabled and 'func' in ti:
	    enabled = ti[ 'func' ]( dmgr )

          widget_icon = ti.get( 'icon' if enabled else 'iconDisabled' )
          widget_im = wx.Image(
              os.path.join( Config.GetResDir(), widget_icon ),
	      wx.BITMAP_TYPE_PNG
	      )

          tip = ti[ 'widget' ]
          if not enabled:
            tip += ' (disabled)'

          tb_item = tbar.AddTool(
              ti_count, widget_im.ConvertToBitmap(),
	      shortHelpString = tip
	      )
	  tb_item.Enable( enabled )
          self.Bind( wx.EVT_TOOL, self._OnWidgetTool, tb_item )

#				-- File->New menu
	  mid = self.fileNewMenu.FindItem( ti[ 'widget' ] )
	  if mid != wx.NOT_FOUND:
	    self.fileNewMenu.FindItemById( mid ).Enable( enabled )
        #end if-else separator

        ti_count += 1
      #end for ti
    #end if dmgr

    tbar.Realize()
  #end _UpdateToolBar_sane

#end VeraViewFrame


#------------------------------------------------------------------------
#	CLASS:		VeraViewFrameAnimatorWidget			-
#------------------------------------------------------------------------
class VeraViewFrameAnimatorWidget( object ):
  """Implements the Widget interface required by widget.Animator and
its extensions so we can use widget.Animator for animating display of
all the widgets.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, frame ):
    """
@param  frame		VeraViewFrame instance
"""
    self.frame = frame

    #self._axialValue = DataModel.CreateEmptyAxialValueObject()
    self._axialValue = AxialValue()
    self.busy = False
    self.busyLock = threading.RLock()

    self.dmgr = frame.state.dataModelMgr
    self._timeValue = -1.0
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.CreatePrintImage()	-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, fpath, hilite = False ):
    """
"""
    if not self.IsBusy():
      self.SetBusy()
      try:
	widgets = []
	for wc in self.frame.grid.GetChildren():
	  if isinstance( wc, WidgetContainer ):
	    widgets.append( wc.widget )

	montager = WidgetImageMontager(
	   result_path = fpath,
	   widgets = widgets,
	   ncols = self.frame.grid.GetSizer().GetCols(),
	   nrows = self.frame.grid.GetSizer().GetRows(),
	   no_dialog = True,
	   hilite = hilite
	   )
	montager.CreateImage( None )
      finally:
        self.SetBusy( False )
    #end if
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.GetAxialValue()	-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """
@return			AxialValue instance
"""
    #return  self.frame.state.axialValue
    return  self._axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.GetCurDataSet()	-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """
"""
    #return  self.frame.state.curDataSet

    first_wc = self.frame.GetFirstWidgetContainer()
    return \
        first_wc.widget.GetCurDataSet() \
	if first_wc is not None else \
	self.frame.state.curDataSet
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.GetState()		-
  #----------------------------------------------------------------------
  def GetState( self ):
    """
"""
    return  self.frame.state
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.GetTimeValue()	-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """
"""
    #return  self.frame.state.timeValue
    return  self._timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.IsBusy()		-
  #----------------------------------------------------------------------
  def IsBusy( self ):
    """
"""
    self.busyLock.acquire()
    try:
      is_busy = self.busy
    finally:
      self.busyLock.release()

    return  is_busy
  #end IsBusy


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.SetBusy()		-
  #----------------------------------------------------------------------
  def SetBusy( self, busy_in = True ):
    """
"""
    self.busyLock.acquire()
    try:
      self.busy = busy_in
    finally:
      self.busyLock.release()
  #end SetBusy


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameAnimatorWidget.UpdateState()	-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """
"""
    widget_list = []

    axial_value = kwargs.get( 'axial_value', None )
    time_value = kwargs.get( 'time_value', -1.0 )
    if axial_value is not None or time_value >= 0.0:
      for wc in self.frame.grid.GetChildren():
        if isinstance( wc, WidgetContainer ):
	  widget_list.append( wc.widget )

    if widget_list:
      self.SetBusy( True )
      for widget in widget_list:
        widget.UpdateState( **kwargs )

      self._UpdateStateValues( **kwargs )
      self.SetBusy( False )
    #end if widget_list
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:	VeraViewFrameAnimatorWidget._UpdateStateValues()	-
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
"""
    first_wc = self.frame.GetFirstWidgetContainer()
    if first_wc is not None:
      if 'axial_value' in kwargs and \
          kwargs[ 'axial_value' ].cm != self._axialValue.cm:
        self._axialValue = self.dmgr.GetAxialValue(
            first_wc.widget.GetCurDataSet(),
	    cm = kwargs[ 'axial_value' ].cm
	    )
      if 'time_value' in kwargs and kwargs[ 'time_value' ] != self._timeValue:
        self._timeValue = kwargs[ 'time_value' ]
    #end if first_wc is not None
  #end _UpdateStateValues


#		-- Property Definitions
#		--

  axialValue = property( GetAxialValue )
  timeValue = property( GetTimeValue )

#end VeraViewFrameAnimatorWidget


#------------------------------------------------------------------------
#	CLASS:		VeraViewFrameDropTarget				-
#------------------------------------------------------------------------
class VeraViewFrameDropTarget( wx.TextDropTarget ):
  """Processes widget drags."""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameDropTarget.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, frame ):
    super( VeraViewFrameDropTarget, self ).__init__()

    self.frame = frame
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrameDropTarget.OnDropText()		-
  #----------------------------------------------------------------------
  def OnDropText( self, x, y, data ):
    result = False
    if data:
      widget_props = WidgetConfig.Decode( data )
      if widget_props and 'classpath' in widget_props:
        wc = self.frame.CreateWidget( widget_props[ 'classpath' ], no_init = True )
	wc.LoadProps( widget_props )
	result = True
    #end if

    return  result
  #end OnDropText

#end VeraViewFrameDropTarget


#------------------------------------------------------------------------
#	CLASS:		VeraViewGrid					-
#------------------------------------------------------------------------
class VeraViewGrid( wx.Panel ):
  """Grid panel.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    super( VeraViewGrid, self ).__init__( *args, **kwargs )

    self.listener = None
    self.logger = logging.getLogger( 'root' )
    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.CalcWidgetSize()			-
  #----------------------------------------------------------------------
  def CalcWidgetSize( self, apply_widget_ratio = False ):
    sizer = self.GetSizer()
    size = self.GetClientSize()

#		-- Works b/c there's no border or margin
    item_wd = int( math.floor( size[ 0 ] / sizer.GetCols() ) )
    item_ht = int( math.floor( size[ 1 ] / sizer.GetRows() ) )

    if apply_widget_ratio:
      temp_wd = int( math.floor( item_ht * WIDGET_PREF_RATIO ) )

#			-- Constrained by width
      if temp_wd > item_wd:
        item_ht = int( math.floor( item_wd / WIDGET_PREF_RATIO ) )
      else:
        item_wd = temp_wd
    #end if apply_widget_ratio

    return  ( item_wd, item_ht )
  #end CalcWidgetSize


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.FireStateChange()			-
  #----------------------------------------------------------------------
#  def FireStateChange( self, reason ):
#    if reason != STATE_CHANGE_noop:
#      for child in self.GetChildren():
#        if isinstance( child, WidgetContainer ):
#	  try:
#	    child.HandleStateChange( reason )
#          except Exception, ex:
#	    print >> sys.stderr, '[VeraViewGrid.FireStateChanged]', str( ex )
#      #end for
#
#      self.listener.HandleStateChange( reason )
#    #end if
#  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.FitWidgets()			-
  #----------------------------------------------------------------------
  def FitWidgets( self, apply_widget_ratio = False ):
    self._ResizeWidgets( self.CalcWidgetSize( apply_widget_ratio ) )
  #end FitWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid._FreezeWidgets()			-
  #----------------------------------------------------------------------
  def _FreezeWidgets( self, freeze_flag = True ):
    """
@param  freeze_flag	True to freeze, False to Thaw
"""
    if freeze_flag:
      for item in self.GetChildren():
	if not item.IsFrozen():
          item.Freeze()
    else:
      for item in self.GetChildren():
	if item.IsFrozen():
          item.Thaw()
  #end _FreezeWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.GetListener()			-
  #----------------------------------------------------------------------
  def GetListener( self ):
    return  self.listener
  #end GetListener


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    cols = 1
    rows = 1

    sizer = wx.GridSizer( cols, rows, 0, 0 )
    self.SetSizer( sizer )

#		-- Size this
#		--
#    display_size = wx.DisplaySize()
#    ht = display_size[ 1 ] - 64
#    wd = int( ht * WIDGET_PREF_RATIO )
#    self.SetSize( ( wd, ht ) )

#    display_size = wx.DisplaySize()
#    ht = display_size[ 1 ] - 64
#    if ht < WIDGET_PREF_SIZE[ 1 ]:
#      grid_size = ( int( ht * WIDGET_PREF_RATIO ), ht )
#    else:
#      grid_size = WIDGET_PREF_SIZE
#    #self.SetMinSize( grid_size )
#    self.SetSize( grid_size )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid._ResizeWidgets()			-
  #----------------------------------------------------------------------
  def _ResizeWidgets( self, new_size ):
    self._FreezeWidgets()
    grid = self.GetSizer()
    items = []
    for item in self.GetChildren():
      if isinstance( item, WidgetContainer ):
        items.append( item )
        grid.Detach( item )

    for item in self.GetChildren():
      item.SetMinSize( new_size )
      item.SetSize( new_size )
#      grid.Add( item, 0, wx.ALIGN_CENTER | wx.SHAPED, 0 )
      grid.Add( item, 0, wx.ALIGN_CENTER | wx.EXPAND, 0 )

    grid.Layout()
    self.Fit()

    self._FreezeWidgets( False )
  #end _ResizeWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.SetListener()			-
  #----------------------------------------------------------------------
  def SetListener( self, l ):
    self.listener = l
  #end SetListener

#end VeraViewGrid

if __name__ == '__main__':
  VeraViewApp.main()
