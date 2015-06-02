#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_chooser_test.py				-
#	HISTORY:							-
#		2015-05-12	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, json, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from widget.bean.dataset_chooser import *


#------------------------------------------------------------------------
#	CLASS:		DataSetChooserDialogTestApp			-
#------------------------------------------------------------------------
class DataSetChooserDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestApp.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( DataSetChooserDialogTestApp, self ).__init__( *args, **kwargs )
    super( DataSetChooserDialogTestApp, self ).__init__( redirect = False )
    #super( DataSetChooserDialogTestApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'DataSetChooserDialogTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestApp.OnInit()		-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestApp.main()		-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input file'
          )
      args = parser.parse_args()

      if args.file == None:
        ds_names = [ 'detector_response', 'pin_powers', 'pin_volumes' ]
	value_in = None
      else:
        fp = file( args.file )
	value_in = json.loads( fp.read() )
	fp.close()

	ds_names = value_in.keys()
	ds_names.sort()
      #end if

#			-- Create App
#			--
      app = DataSetChooserDialogTestApp()
      frame = DataSetChooserDialogTestFrame( app, ds_names, value_in )
      frame.Show()
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

#end DataSetChooserDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		DataSetChooserDialogTestFrame			-
#------------------------------------------------------------------------
class DataSetChooserDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestFrame.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, app, ds_names, value_in ):
    super( DataSetChooserDialogTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.dsNames = ds_names
    #self.statusBar = None
    self.value = value_in

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestFrame._InitUI()		-
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

#		-- Status Bar
#		--
#    self.statusBar = self.CreateStatusBar()
#    self.statusBar.SetStatusText( str( self.value ) )

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
    self.SetTitle( 'DataSetChooserDialog Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestFrame._OnEdit()		-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = DataSetChooserDialog( self, ds_names = self.dsNames )
    dialog.ShowModal( self.value )
    new_value = dialog.GetResult()
    if new_value != None:
      self.value = new_value
      print json.dumps( new_value )

    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		DataSetChooserDialogTestFrame._OnQuit()		-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.app.ExitMainLoop()
  #end _OnQuit

#end DataSetChooserDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataSetChooserDialogTestApp.main()
