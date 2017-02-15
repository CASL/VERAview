#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_diff_creator_itest.py			-
#	HISTORY:							-
#		2016-11-30	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, logging.config, os, re, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from bean.dataset_diff_creator import *
#from data.datamodel import *
#from data.datamodel_mgr import *
from event.state import *


#------------------------------------------------------------------------
#	CLASS:		DataSetDiffCreatorDialogTestApp			-
#------------------------------------------------------------------------
class DataSetDiffCreatorDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestApp.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    super( DataSetDiffCreatorDialogTestApp, self ).__init__( redirect = False )

    self.SetAppName( 'DataSetDiffCreatorDialogTestApp' )
  #end __init__


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestApp.main()		-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      log_file = os.path.\
          join( os.path.dirname( __file__ ), '..', 'res', 'logging.conf' )
      logging.config.fileConfig( log_file )

      parser = argparse.ArgumentParser()

      parser.add_argument(
	  #'-f', '--files',
	  'files',
	  default = None,
	  help = 'input files',
	  nargs = '+'
          )
      args = parser.parse_args()

#			-- Open files
#			--
      state = State()
      for f in args.files:
	print '[dataset_diff_creator_itest] opening', f, ' ...'
        state.dataModelMgr.OpenModel( f )

#			-- Create App
#			--
      app = DataSetDiffCreatorDialogTestApp()
      frame = DataSetDiffCreatorDialogTestFrame( app, state )
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

#end DataSetDiffCreatorDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		DataSetDiffCreatorDialogTestFrame		-
#------------------------------------------------------------------------
class DataSetDiffCreatorDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestFrame.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, app, state ):
    super( DataSetDiffCreatorDialogTestFrame, self ).__init__( None, -1 )

    self.fApp = app
    self.fState = state

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestFrame._InitUI()	-
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
    self.SetTitle( 'DataSetDiffCreatorDialog Test' )
    self.Center()
    self.SetPosition( ( 50, 50 ) )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestFrame._OnEdit()	-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = DataSetDiffCreatorDialog( self, state = self.fState )
    dialog.ShowModal()

    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		DataSetDiffCreatorDialogTestFrame._OnQuit()	-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    #self.Close()
    self.fApp.ExitMainLoop()
  #end _OnQuit

#end DataSetDiffCreatorDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataSetDiffCreatorDialogTestApp.main()
