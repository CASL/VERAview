#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		grid_sizer_bean_test.py				-
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

from bean.grid_sizer_bean import *


#------------------------------------------------------------------------
#	CLASS:		GridSizerBeanTestApp				-
#------------------------------------------------------------------------
class GridSizerBeanTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestApp.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    #super( GridSizerBeanTestApp, self ).__init__( *args, **kwargs )
    super( GridSizerBeanTestApp, self ).__init__( redirect = False )
    #super( GridSizerBeanTestApp, self ).__init__( redirect = True, filename = 'run.log' )

    self.SetAppName( 'GridSizerBeanTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestApp.OnInit()			-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestApp.main()			-
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
      args = parser.parse_args()

#			-- Create App
#			--
      app = GridSizerBeanTestApp()
      frame = GridSizerBeanTestFrame( app, args )
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

#end GridSizerBeanTestApp


#------------------------------------------------------------------------
#	CLASS:		GridSizerBeanTestFrame				-
#------------------------------------------------------------------------
class GridSizerBeanTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestFrame.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, app, args ):
    super( GridSizerBeanTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.bean = None
    self.panel = None
    self.statusBar = None

    self._InitUI( args )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestFrame._InitUI()		-
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
    self.statusBar.SetStatusText( '' )

    self.panel = wx.Panel( self, -1 )
    panel_sizer = wx.BoxSizer( wx.VERTICAL )
    self.panel.SetSizer( panel_sizer )

    self.bean = GridSizerBean( self, -1 )
    self.bean.SetMaxValues( args.max_rows, args.max_cols )
    self.bean.value = ( 2, 2 )
    self.bean.Bind( EVT_GRID_SIZER, self._OnSizer )
    panel_sizer.Add( self.bean, 1, wx.EXPAND, 4 )

#		-- Window Events
#		--
    self.Bind( wx.EVT_CLOSE, self._OnQuit )

#		-- Lay Out
#		--
    vbox = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( vbox )
    vbox.Add( self.panel, 1, wx.EXPAND, 0 )
    vbox.Layout()
    self.Fit()
    self.SetTitle( 'GridSizerBean Test' )
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestFrame._OnQuit()		-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.app.ExitMainLoop()
  #end _OnQuit


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBeanTestFrame._OnSizer()		-
  #----------------------------------------------------------------------
  def _OnSizer( self, ev ):
    ev.Skip()
    self.statusBar.SetStatusText( str( ev.value ) )
  #end _OnSizer

#end GridSizerBeanTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  GridSizerBeanTestApp.main()
