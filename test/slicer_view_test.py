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
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 10 )
    #sizer.AddSpacer( 10 )

    button = wx.Button( self, label = "Show 3D Viz" )
    button.Bind( wx.EVT_BUTTON, self._OnShow )
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 10 )
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
  #	METHOD:		SlicerViewTestFrame._OnInit()			-
  #----------------------------------------------------------------------
  def _OnInit( self, ev ):
    ev.Skip()
    Environment3D.Load()
  #end _OnInit


  #----------------------------------------------------------------------
  #	METHOD:		SlicerViewTestFrame._OnShow()			-
  #----------------------------------------------------------------------
  def _OnShow( self, ev ):
    ev.Skip()

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

    frame = cls( None, -1, state )
    frame.Show()
  #end _OnShow


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
