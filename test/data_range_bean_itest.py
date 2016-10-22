#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_range_bean_itest.py			-
#	HISTORY:							-
#		2016-10-22	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, os, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from widget.bean.data_range_bean import *


#------------------------------------------------------------------------
#	CLASS:		DataRangeDialogTestApp				-
#------------------------------------------------------------------------
class DataRangeDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestApp.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    super( DataRangeDialogTestApp, self ).__init__( redirect = False )

    self.SetAppName( 'DataRangeDialogTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestApp.OnInit()			-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestApp.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  '-r', '--range',
	  default = None,
	  help = 'initial range',
	  nargs = 2
          )
      args = parser.parse_args()

#			-- Create App
#			--
      app = DataRangeDialogTestApp()
      frame = DataRangeDialogTestFrame( app, args.range )
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

#end DataRangeDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		DataRangeDialogTestFrame			-
#------------------------------------------------------------------------
class DataRangeDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestFrame.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, app, value_in ):
    super( DataRangeDialogTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.value = value_in

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestFrame._InitUI()		-
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
    self.SetTitle( 'DataSetChooserDialog Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestFrame._OnEdit()		-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = DataRangeDialog( self )
    dialog.ShowModal( self.value )
    new_value = dialog.GetResult()
    if new_value is not None:
      self.value = new_value
      print str( new_value )

    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialogTestFrame._OnQuit()		-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    self.app.ExitMainLoop()
  #end _OnQuit

#end DataRangeDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataRangeDialogTestApp.main()
