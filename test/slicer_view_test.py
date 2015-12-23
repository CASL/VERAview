#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		slicer_view_test.py				-
#	HISTORY:							-
#		2015-12-11	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, json, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from data.config import Config
from data.datamodel import *
from event.state import *
from view3d.env3d import *
#from view3d.slicer_view import *


#------------------------------------------------------------------------
#	CLASS:		SlicerViewTestApp				-
#------------------------------------------------------------------------
class SlicerViewTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestApp.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( SlicerViewTestApp, self ).__init__( *args, **kwargs )
    super( SlicerViewTestApp, self ).__init__( redirect = False )
    #super( SlicerViewTestApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'SlicerViewTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestApp.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  '-f', '--file-path',
	  default = None,
	  help = 'input HDF5 file'
          )
      args = parser.parse_args()

      if args.file_path == None:
        parser.print_help()

      else:
        Config.SetRootDir(
	    os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), '..' )
	    )

        data_model = DataModel( args.file_path )
	messages = data_model.Check()
	if len( messages ) > 0:
	  print >> sys.stderr, '\n'.join( messages )

	else:
          app = SlicerViewTestApp()
          frame = SlicerViewTestFrame( app, data_model )
          frame.Show()
          app.MainLoop()
      #end if-else

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

#end SlicerViewTestApp


#------------------------------------------------------------------------
#	CLASS:		SlicerViewTestFrame				-
#------------------------------------------------------------------------
class SlicerViewTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, app, data_model ):
    super( SlicerViewTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.data = data_model
    self.vizFrame = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
#		-- Menu Bar
#		--
    file_menu = wx.Menu()
    quit_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Quit\tCtrl+Q' )
    self.Bind( wx.EVT_MENU, self._OnQuit, quit_item )
    file_menu.AppendItem( quit_item )

    mbar = wx.MenuBar()
    mbar.Append( file_menu, '&File' )
    self.SetMenuBar( mbar )

    sizer = wx.BoxSizer( wx.HORIZONTAL )
    self.SetSizer( sizer )

    button = wx.Button( self, label = "Initialize 3D Environment" )
    button.Bind( wx.EVT_BUTTON, self._OnInit )
    sizer.AddStretchSpacer()
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 4 )
    #sizer.AddSpacer( 10 )

    button = wx.Button( self, label = "Show 3D Viz" )
    button.Bind( wx.EVT_BUTTON, self._OnShow )
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 4 )

    button = wx.Button( self, label = "Cycle State Point" )
    button.Bind( wx.EVT_BUTTON, self._OnCycleStatePoint )
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 4 )
    sizer.AddStretchSpacer()

#		-- Window Events
#		--
    self.Bind( wx.EVT_CLOSE, self._OnQuit )

#		-- Lay Out
#		--
    sizer.Layout()
    self.Fit()
    self.SetTitle( 'Slicer3DViewer Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnCloseVizFrame()		-
  #----------------------------------------------------------------------
  def _OnCloseVizFrame( self, ev ):
    ev.Skip()
    self.vizFrame = None
  #end _OnCloseVizFrame


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnCycleStatePoint()	-
  #----------------------------------------------------------------------
  def _OnCycleStatePoint( self, ev ):
    ev.Skip()
    if self.vizFrame != None:
      state = self.vizFrame.widgetContainer.state
      data = State.GetDataModel( state ) if state != None else None
      if data != None:
#	ndx = state.stateIndex + 1
#	if ndx > len( data.GetStates() ):
#	  ndx = 0
	ndx = state.stateIndex - 1
	if ndx < 0:
	  ndx = len( data.GetStates() ) - 1
        state.stateIndex = ndx
	self.vizFrame.widgetContainer.\
	    HandleStateChange( STATE_CHANGE_stateIndex )
      #end if data exists
    #end if vizFrame exists
  #end _OnCycleStatePoint


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnInit()			-
  #----------------------------------------------------------------------
  def _OnInit( self, ev ):
    ev.Skip()

    def feedback( loaded, errors ):
      msg = 'Loaded' if loaded else 'Not Loaded'
      if errors != None and len( errors ) > 0:
        msg += ':' + os.linesep.join( errors )
      wx.MessageBox(
	  msg, 'Load',
	  wx.OK_DEFAULT
          )
      #print >> sys.stderr, '** ' + msg
    #end feedback

    #Environment3D.LoadAndCall( feedback )
    Environment3D.LoadAndCall( feedback )
  #end _OnInit


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnShow()			-
  #----------------------------------------------------------------------
  def _OnShow( self, ev ):
    ev.Skip()

    def check_and_show( loaded, errors ):
      if errors != None and len( errors ) > 0:
        msg = \
	    'Error loading 3D environment:' + os.linesep + \
	    os.linesep.join( errors )
        wx.MessageBox( msg, 'Load', wx.ICON_ERROR | wx.OK_DEFAULT )

      elif loaded:
        self._OnShowImpl()
    #end check_and_show

    Environment3D.LoadAndCall( check_and_show )
  #end _OnShow


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnShowImpl()		-
  #----------------------------------------------------------------------
  def _OnShowImpl( self ):
    state = State()
    state.Load( self.data )

    object_classpath = 'view3d.slicer_view.Slicer3DFrame'
    module_path, class_name = object_classpath.rsplit( '.', 1 )

    try:
      module = __import__( module_path, fromlist = [ class_name ] )
    except ImportError:
      raise ValueError( 'Module "%s" could not be imported' % module_path )

    try:
      cls = getattr( module, class_name )
    except AttributeError:
      raise ValueError(
          'Class "%s" not found in module "%s"' % ( module_path, class_name )
	  )

    self.vizFrame = cls( None, -1, state )
    self.vizFrame.Bind( wx.EVT_CLOSE, self._OnCloseVizFrame )
    self.vizFrame.Show()
  #end _OnShowImpl


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnQuit()			-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.app.ExitMainLoop()
  #end _OnQuit

#end SlicerViewTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  SlicerViewTestApp.main()
