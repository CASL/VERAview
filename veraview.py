#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		veraview.py					-
#	HISTORY:							-
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
import argparse, os, sys, threading, traceback
#import pdb  # set_trace()

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
#except ImportException:
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from bean.dataset_mgr import *
from bean.grid_sizer_dialog import *

from data.config import Config
from data.datamodel import *

from event.state import *

from widget.image_ops import *
from widget.widgetcontainer import *

from widget.bean.axial_slider import *
from widget.bean.exposure_slider import *


ID_REFIT_WINDOW = 1000

TITLE = 'VERAView (Build 16)'

TOOLBAR_ITEMS = \
  [
    {
    'widget': 'Core 2D View', 'icon': 'Core2DView.32.png', 'type': 'pin'
#'core_both_32x32.png'
    },
    {
    'widget': 'Assembly 2D View', 'icon': 'Assembly2DView.32.png', 'type': 'pin'
#'assy_both_32x32.png'
    },
    {
    'widget': 'Channel Core 2D View', 'icon': 'Channel2DView.32.png', 'type': 'channel'
#'channel_32x32.png'
    },
    {
    'widget': 'Channel Assembly 2D View', 'icon': 'ChannelAssembly2DView.32.png', 'type': 'channel'
#'channel_both_32x32.png'
    },
    {
    'widget': 'Detector 2D View', 'icon': 'Detector2DView.32.png', 'type': 'detector'
#'detector_32x32.png'
    },
#    {
#    'widget': 'Detector Axial Plot', 'icon': 'detector_plot_32x32.png',
#    'type': 'detector'
#    },
    {
    'widget': 'Axial Plots', 'icon': 'AllAxialPlot.32.png',
#'all_axial_plot_32x32.png'
    'type': ''
#    'func': lambda d: 'exposure' in d.GetDataSetNames( 'scalar' )
    },
#    {
#    'widget': 'Pin Axial Plot', 'icon': 'axial_plot_32x32.png', 'type': 'pin'
#    }
    {
    'widget': 'Time Plot', 'icon': 'TimePlot.32.png',
#'exposure_plot_32x32.png'
    'type': 'scalar'
#    'func': lambda d: 'exposure' in d.GetDataSetNames( 'scalar' )
    }
  ]

WIDGET_MAP = \
  {
  'Assembly 2D View': 'widget.assembly_view.Assembly2DView',
  'Axial Plots': 'widget.all_axial_plot.AllAxialPlot',
  'Channel Core 2D View': 'widget.channel_view.Channel2DView',
  'Channel Assembly 2D View': 'widget.channel_assembly_view.ChannelAssembly2DView',
  'Core 2D View': 'widget.core_view.Core2DView',
  'Detector 2D View': 'widget.detector_view.Detector2DView',
  'Detector Axial Plot': 'widget.detector_axial_plot.DetectorAxialPlot',
  'Pin Axial Plot': 'widget.pin_axial_plot.PinAxialPlot',
  'Time Plot': 'widget.time_plot.TimePlot'
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

    self.SetAppName( TITLE )

    #self.data = None
    #self.dataSetDefault = 'pin_powers'
    self.filepath = None
    self.firstLoop = True
    self.frame = None
    self.state = None

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.MacHideApp()			-
  # These noworky
  #----------------------------------------------------------------------
  def MacHideApp( self ):
    print >> sys.stderr, '[VeraViewApp.MacHideApp]'
    pass
  #end MacHideApp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.MacReopenApp()			-
  # These noworky
  #----------------------------------------------------------------------
  def MacReopenApp( self ):
    print >> sys.stderr, '[VeraViewApp.MacReopenApp]'
    self.BringWindowToFront()
  #end MacReopenApp


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.OnEventLoopEnter()			-
  #----------------------------------------------------------------------
  def OnEventLoopEnter( self, *args, **kwargs ):
    print >> sys.stderr, '[VeraViewApp.OnEventLoopEnter]'

    if self.frame == None:
      print >> sys.stderr, '[VeraViewApp] no frame to show'
      self.ExitMainLoop()

    #else:
    elif self.firstLoop:
      self.firstLoop = False
      self.frame.GetStatusBar().SetStatusText( '' )

      if self.filepath != None and os.path.exists( self.filepath ):
        self.frame.OpenFile( self.filepath )
      else:
        self.frame._OnOpenFile( None )

##      self.frame.Raise()
    #end elif self.firstLoop:
  #end OnEventLoopEnter


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.OnInit()				-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewApp.main()				-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

#      parser.add_argument(
#	  '--assembly',
#	  type = int, nargs = 2,
#	  help = 'col row   optional 0-based index of assembly level display'
#          )
      parser.add_argument(
	  '--assembly',
	  type = int,
	  help = 'optional 1-based index of assembly to display'
          )

      parser.add_argument(
	  '-a', '--axial',
	  type = int,
	  help = 'optional 1-based index of core axial to display'
          )

      parser.add_argument(
	  '-d', '--dataset',
	  help = 'default dataset name, defaulting to "pin_powers"'
          )

      parser.add_argument(
	  '-f', '--file-path',
	  help = 'path to HDF5 data file'
          )

      parser.add_argument(
	  '-s', '--state',
	  type = int,
	  help = 'optional 1-based index of state to display' 
          )

      parser.add_argument(
	  '--scale',
	  type = int, default = 4,
	  help = 'not being used right now',
          )

      args = parser.parse_args()

      if args.axial == None:
        if args.state == None:
	  args.state = 0

      Config.SetRootDir( os.path.dirname( os.path.abspath( __file__ ) ) )
#      if args.dataset != None:
#        Config.SetDefaultDataSet( args.dataset )

      data_model = None
#1      if args.file_path != None:
#1        data_model = DataModel( args.file_path )

#			-- Create State
#			--
#1      state = State( data_model = data_model, scale = args.scale )
      state = State( scale = args.scale )
      if args.assembly != None and args.assembly > 0:
        state.assemblyIndex = ( args.assembly - 1, 0, 0 )
      if args.axial != None and args.axial > 0:
        state.axialValue = ( 0.0, args.axial - 1, -1 )
#        state.axialLevel = args.axial - 1
      elif args.state != None and args.state > 0:
        state.stateIndex = args.state - 1

#			-- Create App
#			--
      #app = VeraViewApp( redirect = False )  # redirect = False
      app = VeraViewApp()
#      app.dataSetDefault = \
#          args.dataset if args.dataset != None else 'pin_powers'
      app.filepath = args.file_path
      app.state = state

      app.frame = VeraViewFrame( app, state )
#			-- If MDI on Mac, don't show
      app.frame.Show()
      app.MainLoop()

    except Exception, ex:
      print >> sys.stderr, str( ex )
      et, ev, tb = sys.exc_info()
      while tb:
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
  #end main

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
  def __init__( self, app, state ):
    super( VeraViewFrame, self ).__init__( None, -1 )

    self.app = app
#    self.dataSetDefault = ds_default
    self.eventLocks = State.CreateLocks()
    self.state = state
#    self.windowMenu = None

    self.axialBean = None
    self.exposureBean = None
    self.grid = None
    self.timeDataSetMenu = None
    self.widgetToolBar = None

    self._InitUI()
  #end __init__


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
  #	METHOD:		VeraViewFrame.CreateWidget()			-
  #----------------------------------------------------------------------
  def CreateWidget( self, widget_class, refit_flag = True ):
    """Must be called on the UI thread.
@return		widget container object
"""
    print >> sys.stderr, '[VeraViewFrame.CreateWidget]'

    #xxx Reject if not enough grid spaces?
    # we'll get the widget classpath from the object
    try:
      grid_sizer = self.grid.GetSizer()
      #widget_count = len( self.grid.GetChildren() ) - 1  # - 2 + 1 (new one)
      widget_count = len( self.grid.GetChildren() ) + 1
      widget_space = grid_sizer.GetCols() * grid_sizer.GetRows()
      if widget_count > widget_space:
	if widget_space == 1:
          grid_sizer.SetCols( grid_sizer.GetCols() + 1 )
	elif grid_sizer.GetCols() > grid_sizer.GetRows():
	  grid_sizer.SetRows( grid_sizer.GetRows() + 1 )
	else:
          grid_sizer.SetCols( grid_sizer.GetCols() + 1 )
      #end if

      con = WidgetContainer( self.grid, widget_class, self.state )
      self.grid._FreezeWidgets()
      grid_sizer.Add( con, 0, wx.ALIGN_CENTER | wx.EXPAND, 0 )
      self.grid.Layout()
      self.Fit()
      self.grid._FreezeWidgets( False )

      if refit_flag:
        wx.CallAfter( self._Refit )

      return  con

    except Exception, ex:
      wx.MessageDialog( self, str( ex ), 'Widget Error' ).ShowWindowModal()
  #end CreateWidget


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
  #	METHOD:		VeraViewFrame.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self ):
    """Convenience accessor for the state.dataModel property.
@return			DataModel object
"""
    #return  None if self.state == None else self.state.GetDataModel()
    return  State.GetDataModel( self.state )
  #end GetDataModel


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
  #	METHOD:		VeraViewFrame.HandleStateChange()		-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    print >> sys.stderr, \
        '[VeraViewFrame.HandleStateChange] reason=%d' % reason
    if (reason & STATE_CHANGE_axialValue) > 0:
      if self.state.axialValue[ 1 ] != self.axialBean.axialLevel:
        self.axialBean.axialLevel = self.state.axialValue[ 1 ]
#    if (reason & STATE_CHANGE_axialLevel) > 0:
#      if self.state.axialLevel != self.axialBean.axialLevel:
#        self.axialBean.axialLevel = self.state.axialLevel

    if (reason & STATE_CHANGE_stateIndex) > 0:
      if self.state.stateIndex != self.exposureBean.stateIndex:
        self.exposureBean.stateIndex = self.state.stateIndex
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
#		-- File Menu
#		--
    file_menu = wx.Menu()

#			-- File->New Submenu
    new_menu = wx.Menu()
    widget_keys = WIDGET_MAP.keys()
    widget_keys.sort()
    #for k in WIDGET_MAP:
    for k in widget_keys:
      item = wx.MenuItem( new_menu, wx.ID_ANY, k )
      self.Bind( wx.EVT_MENU, self._OnNew, item )
      new_menu.AppendItem( item )
    file_menu.AppendSubMenu( new_menu, '&New' )

#			-- Open Item
    open_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Open\tCtrl+O' )
    self.Bind( wx.EVT_MENU, self._OnOpenFile, open_item )
    file_menu.AppendItem( open_item )

    min_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Minimize Window\tCtrl+M' )
    self.Bind( wx.EVT_MENU, self._OnMinimizeWindow, min_item )
    file_menu.AppendItem( min_item )

#    save_im_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Save Image\tCtrl+S' )
#    self.Bind( wx.EVT_MENU, self._OnSaveWindow, save_im_item )
#    file_menu.AppendItem( save_im_item )

    file_menu.AppendSeparator()
    save_item = wx.MenuItem(
        file_menu, wx.ID_ANY,
	'&Save Image of All Widgets\tCtrl+Shift+S'
	)
    self.Bind( wx.EVT_MENU, self._OnSaveImageAllWidgets, save_item )
    file_menu.AppendItem( save_item )

    file_menu.AppendSeparator()
    quit_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Quit\tCtrl+Q' )
    self.Bind( wx.EVT_MENU, self._OnQuit, quit_item )
    file_menu.AppendItem( quit_item )

#		-- Window Menu
#		--
#    self.windowMenu = wx.Menu()
#    raise_all_item = wx.MenuItem( self.windowMenu, wx.ID_ANY, 'Bring All To Front' )
#    self.Bind( wx.EVT_MENU, self.RaiseAllWidgets, raise_all_item )
#    self.windowMenu.AppendItem( raise_all_item )
#    self.windowMenu.AppendSeparator()

#		-- Edit Menu
#		--
    edit_menu = wx.Menu()
    datasets_item = wx.MenuItem( edit_menu, wx.ID_ANY, 'Manage Extra DataSets...' )
    self.Bind( wx.EVT_MENU, self._OnManageDataSets, datasets_item )
    edit_menu.AppendItem( datasets_item )

    self.timeDataSetMenu = wx.Menu()
    time_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, 'Select Time Dataset',
	subMenu = self.timeDataSetMenu
	)
    edit_menu.AppendItem( time_item )

    edit_menu.AppendSeparator()

    grid_item = wx.MenuItem( edit_menu, wx.ID_ANY, 'Resize &Grid\tCtrl+G' )
    self.Bind( wx.EVT_MENU, self._OnGridResize, grid_item )
    edit_menu.AppendItem( grid_item )

#		-- Menu Bar
#		--
    mbar = wx.MenuBar()
    mbar.Append( file_menu, '&File' )
    mbar.Append( edit_menu, '&Edit' )
#    mbar.Append( self.windowMenu, '&Window' )
    self.SetMenuBar( mbar )

#		-- Widget Tool Bar
#		--
    # wx.{NO,RAISED,SIMPLE,SUNKEN}_BORDER
    widget_tbar = \
        wx.ToolBar( self, -1, style = wx.TB_HORIZONTAL | wx.SIMPLE_BORDER )
    self.widgetToolBar = widget_tbar

    ti_count = 1
    for ti in TOOLBAR_ITEMS:
      widget_name = ti[ 'widget' ]
      widget_im = wx.Image(
          os.path.join( Config.GetResDir(), ti[ 'icon' ] ),
	  wx.BITMAP_TYPE_PNG
	  )
      widget_tbar.AddTool(
          ti_count, widget_im.ConvertToBitmap(),
	  shortHelpString = widget_name
	  )
      self.Bind( wx.EVT_TOOL, self._OnWidgetTool, id = ti_count )
      ti_count += 1
    #end for

#    im = wx.Image( os.path.join( Config.GetResDir(), 'fit_32x32.png' ), wx.BITMAP_TYPE_PNG )
#    #widget_tbar.AddSeparator()
#    widget_tbar.AddStretchableSpace()
#    widget_tbar.AddTool(
#	ID_REFIT_WINDOW, im.ConvertToBitmap(),
#	shortHelpString = 'Refit window'
#        )
#    self.Bind( wx.EVT_TOOL, self._OnControlTool, id = ID_REFIT_WINDOW )

    widget_tbar.Realize()

#		-- Status Bar
#		--
    status_bar = self.CreateStatusBar()
    status_bar.SetStatusText( 'Creating...' )

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
    self.grid.SetListener( self )

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
    vbox.Add( widget_tbar, 0, wx.EXPAND, 0 )
    vbox.Add( inside_panel, 1, wx.EXPAND, 0 )
    vbox.Add( self.exposureBean, 0, wx.ALL | wx.EXPAND, 1 )
    self.SetSizer( vbox )
    vbox.Layout()
    self.Fit()
    self.SetTitle( TITLE )

#    self.Center()
    pos = ( 5, 40 ) if 'wxMac' in wx.PlatformInfo else ( 5, 5 )
    self.SetPosition( pos )
    self.SetSize( ( 640, 480 ) )

#		-- Window Events
#		--
    self.Bind( wx.EVT_CLOSE, self.OnCloseFrame )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.LoadDataModel()			-
  #----------------------------------------------------------------------
  def LoadDataModel( self, file_path ):
    """Called when a data file is opened and set in the state.
Must be called from the UI thread.
"""
    print >> sys.stderr, '[VeraViewFrame.LoadDataModel]'

    data = self.state.dataModel

    self.CloseAllWidgets()
    self.SetRepresentedFilename( file_path )

    self.GetStatusBar().SetStatusText( 'Loading data model...' )

#		-- Re-create Time DataSet Menu
#		--
    while self.timeDataSetMenu.GetMenuItemCount() > 0:
      self.timeDataSetMenu.\
          DestroyItem( self.timeDataSetMenu.FindItemByPosition( 0 ) )

    check_item = None
    #ds_names = data.GetDataSetNames( 'scalar' ) + [ 'state' ]
    ds_names = data.GetDataSetNames( 'time' )
    for ds in ds_names:
      item = wx.MenuItem( self.timeDataSetMenu, wx.ID_ANY, ds, kind = wx.ITEM_RADIO )
      if ds == self.state.timeDataSet:
        check_item = item
      self.Bind( wx.EVT_MENU, self._OnTimeDataSet, item )
      self.timeDataSetMenu.AppendItem( item )
    #end for

    if check_item != None:
      check_item.Check()

#		-- Determine Initial Widgets
#		--
    axial_plot_types = set()
    widget_list = []

    if data.core.nass > 1:
      widget_list.append( 'widget.core_view.Core2DView' )

#		-- Detector Mode
#		--
    if len( data.GetDataSetNames()[ 'detector' ] ) > 0:
      widget_list.append( 'widget.detector_view.Detector2DView' )
      if data.core.ndetax > 1:
	axial_plot_types.add( 'detector' )
	axial_plot_types.add( 'pin' )
        #widget_list.append( 'widget.detector_axial_plot.DetectorAxialPlot' )
        #widget_list.append( 'widget.pin_axial_plot.PinAxialPlot' )

#		-- Channel Mode
#		--
    if len( data.GetDataSetNames()[ 'channel' ] ) > 0:
      if data.core.nass > 1:
        widget_list.append( 'widget.channel_view.Channel2DView' )
      widget_list.append( 'widget.channel_assembly_view.ChannelAssembly2DView' )
      if data.core.nax > 1:
	axial_plot_types.add( 'channel' )
        #widget_list.append( 'widget.all_axial_plot.AllAxialPlot' )

#		-- Pin Mode
#		--
    if len( data.GetDataSetNames()[ 'pin' ] ) > 0:
      widget_list.append( 'widget.assembly_view.Assembly2DView' )
      if data.core.nax > 1:
	axial_plot_types.add( 'pin' )
        #widget_list.append( 'widget.pin_axial_plot.PinAxialPlot' )

#		-- Axial Plot?
#		--
    if len( axial_plot_types ) > 0:
      widget_list.append( 'widget.all_axial_plot.AllAxialPlot' )

#		-- Time Plot?
#		--
    if len( data.states ) > 1:
      widget_list.append( 'widget.time_plot.TimePlot' )

#		-- Create widgets, find AllAxialPlot widget reference
#		--
#    widget_list = [ 'widget.core_view.Core2DView', 'widget.all_axial_plot.AllAxialPlot' ]
    axial_plot_widget = None
    for w in widget_list:
      con = self.CreateWidget( w, False )
      if con.widget.GetTitle() == 'Axial Plots':
        axial_plot_widget = con.widget
    #end for

    if axial_plot_widget != None:
      axial_plot_widget.InitDataSetSelections( axial_plot_types )
    #end if

#		-- Update title
#		--
    title = TITLE
    if file_path != None:
      title += (': %s' % os.path.basename( file_path ))
    self.SetTitle( title )

#		-- Refit
#		--
    self._Refit()
    self.GetStatusBar().SetStatusText( 'Data model loaded' )

#		-- Set bean ranges
#		--
    self.axialBean.SetRange( 1, data.core.nax )
    self.axialBean.axialLevel = self.state.axialValue[ 1 ]
#    self.axialBean.axialLevel = self.state.axialLevel
    self.exposureBean.SetRange( 1, len( data.states ) )
    self.exposureBean.stateIndex = self.state.stateIndex

#		-- Update toolbar
#		--
    ti_count = 1
    for ti in TOOLBAR_ITEMS:
      item = self.widgetToolBar.FindById( ti_count )
      if item != None:
        ds_names = data.GetDataSetNames()
        ds_type = ti[ 'type' ]
	tip = ti[ 'widget' ]

        enabled = \
	    ( ds_type == None or ds_type == '' ) or \
            ( ds_type in ds_names and ds_names[ ds_type ] != None and \
	      len( ds_names[ ds_type ] ) > 0 )
	if enabled and 'func' in ti:
	  enabled = ti[ 'func' ]( data )

        item.Enable( enabled )
	if not enabled:
	  tip += ' (disabled)'
	item.SetShortHelp( tip )
	#item.Update()

      ti_count += 1
    #end for
  #end LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnAxial()			-
  #----------------------------------------------------------------------
  def _OnAxial( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()
    axial_value = self.state.dataModel.CreateAxialValue( core_ndx = ev.value )
    reason = self.state.Change( self.eventLocks, axial_value = axial_value )
#    reason = self.state.Change( self.eventLocks, axial_level = ev.value )
    if reason != STATE_CHANGE_noop:
      self.grid.FireStateChange( reason )
  #end _OnAxial


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.OnCloseFrame()			-
  #----------------------------------------------------------------------
  def OnCloseFrame( self, ev ):
    self._OnQuit( None )
  #end OnCloseFrame


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnCloseWindow()			-
  #----------------------------------------------------------------------
#  def _OnCloseWindow( self, ev ):
#    ev.Skip()
#    for child in self.GetChildren():
#      if isinstance( child, wx.Frame ) and child.IsActive():
#	child.Close()
#	break
#    #end for
#  #end _OnCloseWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnControlTool()			-
  #----------------------------------------------------------------------
  def _OnControlTool( self, ev ):
    print >> sys.stderr, '[VeraViewFrame._OnControlTool]'
    ev.Skip()

    tbar = ev.GetEventObject()
    if ev.GetId() == ID_REFIT_WINDOW:
      self._Refit()
  #end _OnControlTool


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnExposure()			-
  #----------------------------------------------------------------------
  def _OnExposure( self, ev ):
    """Handles events from the exposure slider.  Called on the UI thread.
"""
    ev.Skip()
    reason = self.state.Change( self.eventLocks, state_index = ev.value )
    if reason != STATE_CHANGE_noop:
      self.grid.FireStateChange( reason )
  #end _OnExposure



  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnManageDataSets()		-
  #----------------------------------------------------------------------
  def _OnManageDataSets( self, ev ):
    ev.Skip()

    msg = None
    data_model = self.GetDataModel()

    if data_model == None:
      msg = 'No VERAOutput file has been read'

    elif len( data_model.GetStates() ) == 0:
      msg = 'No state points read from VERAOutput file'

    if msg != None:
      wx.MessageDialog( self, msg, 'Manage Extra DataSets' ).ShowWindowModal()

    else:
      dialog = DataSetManagerDialog( self, data_model = data_model )
      dialog.ShowModal()
      dialog.Destroy()
    #end if-else
  #end _OnManageDataSets



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
    if new_size != None and new_size != cur_size:
      widget_count = len( self.grid.GetChildren() )
      if widget_count > (new_size[ 0 ] * new_size[ 1 ]):
	message = \
	    'That would be too few grids for all your widgets.\n' + \
	    'Delete some widget first.'
        wx.MessageDialog( self, message, 'Resize Grid' ).ShowWindowModal()

      else:
        grid_sizer.SetRows( new_size[ 0 ] )
        grid_sizer.SetCols( new_size[ 1 ] )
        #self.grid.FitWidgets()
	self._Refit()
    #end if different size
  #end _OnGridResize


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnMinimizeWindow()		-
  #----------------------------------------------------------------------
  def _OnMinimizeWindow( self, ev ):
    ev.Skip()
    self.Iconize( True )
  #end _OnMinimizeWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnNew()				-
  #----------------------------------------------------------------------
  def _OnNew( self, ev ):
    print >> sys.stderr, '[VeraViewFrame._OnNew]'
    ev.Skip()

    title = None
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )
    if item != None and item.GetText() in WIDGET_MAP:
      self.CreateWidget( WIDGET_MAP[ item.GetText() ] )
      self._Refit()

#    menu_id = ev.GetId()
#    for item in menu.GetMenuItems():
#      if item.GetId() == menu_id:
#        title = item.GetText()
#	break
#    #end for

#    if title != None and title in WIDGET_MAP:
#      self.CreateWidget( WIDGET_MAP[ title ] )
  #end _OnNew


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnOpenFile()			-
  #----------------------------------------------------------------------
  def _OnOpenFile( self, ev ):
    """
Must be called from the UI thread.
"""
    if ev != None:
      ev.Skip()

    dialog = wx.FileDialog(
	self, 'Open File', '', '',
	'HDF5 files (*.h5)|*.h5',
	wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
        )
    if dialog.ShowModal() != wx.ID_CANCEL:
      path = dialog.GetPath()
      dialog.Destroy()
      self.OpenFile( path )
  #end _OnOpenFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnTimeDataSet()			-
  #----------------------------------------------------------------------
  def _OnTimeDataSet( self, ev ):
    ev.Skip()
    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    if item != None:
      title = item.GetText()
      reason = self.state.Change( self.eventLocks, time_dataset = title )
      self.grid.FireStateChange( reason )
    #end if
  #end _OnTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnQuit()				-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    #self.app.ExitMainLoop()
    wx.App.Get().ExitMainLoop()
  #end _OnQuit


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
  #	METHOD:		VeraViewFrame._OnSaveWindow()			-
  #----------------------------------------------------------------------
#  def _OnSaveWindow( self, ev ):
#    ev.Skip()
#    for child in self.GetChildren():
#      if isinstance( child, WidgetContainer ) and child.IsActive():
#	child.SaveWidgetImage()
#	break
#    #end for
#  #end _OnSaveWindow


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnWidgetTool()			-
  #----------------------------------------------------------------------
  def _OnWidgetTool( self, ev ):
    print >> sys.stderr, '[VeraViewFrame._OnWidgetTool]'
    ev.Skip()

    tbar = ev.GetEventObject()
    item = tbar.FindById( ev.GetId() )
    if item != None and item.GetShortHelp() in WIDGET_MAP:
      self.CreateWidget( WIDGET_MAP[ item.GetShortHelp() ] )
      self._Refit()
  #end _OnWidgetTool


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OnWindowMenuItem()		-
  #----------------------------------------------------------------------
#  def _OnWindowMenuItem( self, ev ):
#    ev.Skip()
#    menu = ev.GetEventObject()
#    item = menu.FindItemById( ev.GetId() )
#
#    if item != None:
#      title = item.GetText()
#      for child in self.GetChildren():
#        if isinstance( child, WidgetContainer ) and child.GetTitle() == title:
#	  child.Iconize( False )
#          child.Raise()
#	  break
#      #end for
#    #end if
#  #end _OnWindowMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.OpenFile()			-
  #----------------------------------------------------------------------
  def OpenFile( self, file_path ):
    """
Must be called from the UI thread.
"""
    self.CloseAllWidgets()

    dialog = wx.ProgressDialog(
        'Open File',
	'Reading file "%s"' % file_path
	)
    dialog.Show()

    wxlibdr.startWorker(
	self._OpenFileEnd,
	self._OpenFileBegin,
	wargs = [ dialog, file_path ]
        )
  #end OpenFile


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OpenFileBegin()			-
  #----------------------------------------------------------------------
  def _OpenFileBegin( self, dialog, file_path ):
    """
"""
    dialog.Pulse()
    status = { 'dialog': dialog, 'file_path': file_path }

    try:
      data_model = DataModel( file_path )
      messages = data_model.Check()

      status[ 'data_model' ] = data_model
      status[ 'messages' ] = messages

    except Exception, ex:
      status[ 'messages' ] = \
        [ 'Error opening data file:' + os.linesep + str( ex ) ]

    return  status
  #end _OpenFileBegin


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._OpenFileEnd()			-
  #----------------------------------------------------------------------
  def _OpenFileEnd( self, result ):
    """
"""
    status = result.get()
    if status != None:
      if 'dialog' in status:
	dlg = status[ 'dialog' ]
	#dlg.Lower()
	#dlg.Hide()
	dlg.Destroy()

      if 'messages' in status and len( status[ 'messages' ] ) > 0:
	msg = \
	    'Data file cannot be processed:\n' + \
	    '\n  '.join( status[ 'messages' ] )
	self.ShowMessageDialog( msg, 'Open File' )
	#dlg = wx.MessageDialog( self, msg, 'Open File' )
	#wx.CallAfter( dlg, ShowModal )

      elif 'data_model' in status and 'file_path' in status:
	self.state.Load( status[ 'data_model' ] )
        self.LoadDataModel( status[ 'file_path' ] )
    #end if
  #end _OpenFileEnd


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.OpenFileImpl()			-
  #----------------------------------------------------------------------
  def OpenFileImpl( self, file_path ):
    """
@deprecated
"""
    #examine the file and determine the type
    self.CloseAllWidgets()
    try:
      data_model = DataModel( file_path )

      messages = data_model.Check()
      if messages != None and len( messages ) > 0:
	msg = 'Data file cannot be processed:' + '\n  '.join( messages )
	wx.CallAfter( self.ShowMessageDialog, msg, 'Open File' )

      else:
        self.state.dataModel = data_model

        self.state.assemblyIndex = ( 0, 0, 0 )
        self.state.axialValue = ( 0.0, 0, 0 )
#        self.state.axialLevel = 0
        self.state.pinColRow = ( 0, 0 )
        self.state.stateIndex = 0

        self.LoadDataModel( file_path )
      #end if-else

    except Exception, ex:
      msg = 'Error opening data file:' + os.linesep + str( ex )
      wx.CallAfter( self.ShowMessageDialog, msg, 'Open Error' )
  #end OpenFileImpl


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._Refit()				-
  #----------------------------------------------------------------------
  def _Refit( self ):
    self.grid.FitWidgets()
    self.Fit()
  #end _Refit


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame._ResolveTitle()			-
  #----------------------------------------------------------------------
  def _ResolveTitle( self, title ):
    result = title
#    last = 0
#    for item in self.windowMenu.GetMenuItems():
#      text = item.GetText()
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
  #	METHOD:		VeraViewFrame.SaveWidgetsImage()		-
  #----------------------------------------------------------------------
  def SaveWidgetsImage( self, file_path = None ):
    """
Must be called on the UI event thread.
"""
    if len( self.grid.GetChildren() ) == 0:
      self.ShowMessageDialog( 'No widgets to save', 'Save Image' )

    else:
      if file_path == None:
        dialog = wx.FileDialog(
	    self, 'Save Widgets Image', '', '',
	    'PNG files (*.png)|*.png',
	    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
	    )
        if dialog.ShowModal() != wx.ID_CANCEL:
	  file_path = dialog.GetPath()
      #end if

      if file_path != None:
        try:
	  widgets = []
	  for wc in self.grid.GetChildren():
	    widgets.append( wc.widget )

	  montager = WidgetImageMontager(
	      result_path = file_path,
	      widgets = widgets,
	      cols = self.grid.GetSizer().GetCols()
	      )
	  montager.Run( 'Save Widgets Image' )

	except Exception, ex:
	  msg = 'Error saving image:' + os.linesep + str( ex )
          self.ShowMessageDialog( msg, 'Save Image' )
      #end if
    #end else we have child widget containers
  #end SaveWidgetsImage


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewFrame.ShowMessageDialog()		-
  #----------------------------------------------------------------------
  def ShowMessageDialog( self, message, title ):
    """Can be called from any thread.
"""
    wx.MessageDialog( self, message, title ).ShowWindowModal()
  #end ShowMessageDialog

#end VeraViewFrame


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
    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.CalcWidgetSize()			-
  #----------------------------------------------------------------------
  def CalcWidgetSize( self ):
    sizer = self.GetSizer()
    size = self.GetClientSize()

#		-- Works b/c there's no border or margin
    item_wd = int( math.floor( size[ 0 ] / sizer.GetCols() ) )
    item_ht = int( math.floor( size[ 1 ] / sizer.GetRows() ) )

    temp_wd = int( math.floor( item_ht * WIDGET_PREF_RATIO ) )
    if temp_wd > item_wd:
      item_ht = int( math.floor( item_wd / WIDGET_PREF_RATIO ) )
    else:
      item_wd = temp_wd

    return  ( item_wd, item_ht )
  #end CalcWidgetSize


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.FireStateChange()			-
  #----------------------------------------------------------------------
  def FireStateChange( self, reason ):
    if reason != STATE_CHANGE_noop:
      for child in self.GetChildren():
        if isinstance( child, WidgetContainer ):
	  try:
	    child.HandleStateChange( reason )
          except Exception, ex:
	    print >> sys.stderr, '[VeraViewGrid.FireStateChanged]', str( ex )
      #end for

      self.listener.HandleStateChange( reason )
    #end if
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.FitWidgets()			-
  #----------------------------------------------------------------------
  def FitWidgets( self ):
    self._ResizeWidgets( self.CalcWidgetSize() )
  #end FitWidgets


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid.FitWidgets_orig()			-
  #----------------------------------------------------------------------
  def FitWidgets_orig( self ):
    sizer = self.GetSizer()
    #size = self.GetSize()
    size = self.GetClientSize()

#		-- Works b/c there's no border or margin
    item_wd = int( math.floor( size[ 0 ] / sizer.GetCols() ) )
    item_ht = int( math.floor( size[ 1 ] / sizer.GetRows() ) )

    temp_wd = int( math.floor( item_ht * WIDGET_PREF_RATIO ) )
    if temp_wd > item_wd:
      item_ht = int( math.floor( item_wd / WIDGET_PREF_RATIO ) )
    else:
      item_wd = temp_wd

    self._ResizeWidgets( ( item_wd, item_ht ) )
  #end FitWidgets_orig


  #----------------------------------------------------------------------
  #	METHOD:		VeraViewGrid._FreezeWidgets()			-
  #----------------------------------------------------------------------
  def _FreezeWidgets( self, freeze_flag = True ):
    """
@param  freeze_flag	True to freeze, False to Thaw
"""
    if freeze_flag:
      for item in self.GetChildren():
        item.Freeze()
    else:
      for item in self.GetChildren():
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


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  VeraViewApp.main()
