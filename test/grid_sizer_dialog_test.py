#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		grid_sizer_dialog_test.py			-
#	HISTORY:							-
#		2015-02-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except ImportException:
  raise ImportError, 'The wxPython module is required to run this program'

from bean.grid_sizer_dialog import *


#------------------------------------------------------------------------
#	CLASS:		GridSizerDialogTestApp				-
#------------------------------------------------------------------------
class GridSizerDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestApp.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( GridSizerDialogTestApp, self ).__init__( *args, **kwargs )
    super( GridSizerDialogTestApp, self ).__init__( redirect = False )
    #super( GridSizerDialogTestApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'GridSizerDialogTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestApp.OnInit()			-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestApp.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  '-c', '--max-cols',
	  default = 5, type = int,
	  help = 'maximum cols'
          )
      parser.add_argument(
	  '-r', '--max-rows',
	  default = 5, type = int,
	  help = 'maximum rows'
          )
      parser.add_argument(
	  '-v', '--value', nargs = 2,
	  default = [ 1, 1 ], type = int,
	  help = 'initial value'
          )
      args = parser.parse_args()

#			-- Create App
#			--
      app = GridSizerDialogTestApp()
      frame = GridSizerDialogTestFrame( app, args )
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

#end GridSizerDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		GridSizerDialogTestFrame			-
#------------------------------------------------------------------------
class GridSizerDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestFrame.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, app, args ):
    super( GridSizerDialogTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.statusBar = None
    self.value = args.value

    self._InitUI( args )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestFrame._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self, args ):
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
    self.statusBar = self.CreateStatusBar()
    self.statusBar.SetStatusText( str( self.value ) )

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
    self.SetTitle( 'GridSizerDialog Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestFrame._OnEdit()		-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = GridSizerDialog( None )
#	-- ** Noworky **
#    result = dialog.ShowModal( self.value )
#    if result > 0:
#      self.value = dialog.value
#      self.statusBar.SetStatusText( str( self.value ) )
    dialog.ShowModal( self.value )
    new_value = dialog.GetResult()
    if new_value != None:
      self.value = new_value
      self.statusBar.SetStatusText( str( self.value ) )

    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialogTestFrame._OnQuit()		-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.app.ExitMainLoop()
  #end _OnQuit

#end GridSizerDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  GridSizerDialogTestApp.main()
