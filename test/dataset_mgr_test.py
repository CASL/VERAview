#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_mgr_test.py				-
#	HISTORY:							-
#		2015-11-12	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, json, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from data.datamodel import *
from bean.dataset_mgr import *


#------------------------------------------------------------------------
#	CLASS:		DataSetManagerDialogTestApp			-
#------------------------------------------------------------------------
class DataSetManagerDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestApp.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( DataSetManagerDialogTestApp, self ).__init__( *args, **kwargs )
    super( DataSetManagerDialogTestApp, self ).__init__( redirect = False )
    #super( DataSetManagerDialogTestApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'DataSetManagerDialogTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestApp.OnInit()		-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestApp.main()		-
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
        data_model = DataModel( args.file_path )
	messages = data_model.Check()
	if len( messages ) > 0:
	  print >> sys.stderr, '\n'.join( messages )

	else:
          app = DataSetManagerDialogTestApp()
          frame = DataSetManagerDialogTestFrame( app, data_model )
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

#end DataSetManagerDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		DataSetManagerDialogTestFrame			-
#------------------------------------------------------------------------
class DataSetManagerDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestFrame.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, app, data_model ):
    super( DataSetManagerDialogTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.data = data_model

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestFrame._InitUI()		-
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

    button = wx.Button( self, label = "Edit..." )
    button.Bind( wx.EVT_BUTTON, self._OnEdit )
    sizer.Add( button, 1, wx.ALL | wx.EXPAND, 10 )

#		-- Window Events
#		--
    self.Bind( wx.EVT_CLOSE, self._OnQuit )

#		-- Lay Out
#		--
    sizer.Layout()
    self.Fit()
    self.SetTitle( 'DataSetManagerDialog Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestFrame._OnEdit()		-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = DataSetManagerDialog( self, data_model = self.data )
    dialog.ShowModal()
    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		DataSetManagerDialogTestFrame._OnQuit()		-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.app.ExitMainLoop()
  #end _OnQuit

#end DataSetManagerDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataSetManagerDialogTestApp.main()
