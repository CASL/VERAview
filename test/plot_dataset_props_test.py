#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		plot_dataset_props_test.py			-
#	HISTORY:							-
#		2016-05-19	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, json, os, random, sys, traceback
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from widget.bean.plot_dataset_props import *


#------------------------------------------------------------------------
#	CLASS:		PlotDataSetPropsDialogTestApp			-
#------------------------------------------------------------------------
class PlotDataSetPropsDialogTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialogTestApp.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    super( PlotDataSetPropsDialogTestApp, self ).__init__( redirect = False )

    self.SetAppName( 'PlotDataSetPropsDialogTestApp' )

    #wx.ToolTip.Enable( True )
    #wx.ToolTip.SetAutoPop( 10000 )
    #wx.ToolTip.SetDelay( 500 )
    #wx.ToolTip.SetReshow( 100 )
  #end __init__


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialogTestApp.main()		-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      random.seed()

      parser = argparse.ArgumentParser()
      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input file'
          )
      args = parser.parse_args()

      if args.file is None:
	have_top = False
	have_bottom = False
	props = {}
        for i in range( 24 ):
	  name = 'dataset %02d' % i
	  axis = ''
	  if not have_top and random.random() >= 0.75:
	    axis = 'top'
	    have_top = True
	  if not have_bottom and random.random() >= 0.75:
	    axis = 'bottom'
	    have_bottom = True
	  scale = 5.0 if random.random() > 0.75 else 1.0

	  props[ name ] = dict( axis = axis, scale = scale )
	#end for

      else:
        fp = file( args.file )
	props = json.loads( fp.read() )
	fp.close()
      #end if

#			-- Create App
#			--
      app = PlotDataSetPropsDialogTestApp()
      frame = PlotDataSetPropsDialogTestFrame( app, props )
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

#end PlotDataSetPropsDialogTestApp


#------------------------------------------------------------------------
#	CLASS:		PlotDataSetPropsDialogTestFrame			-
#------------------------------------------------------------------------
class PlotDataSetPropsDialogTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialogTestFrame.__init__()	-
  #----------------------------------------------------------------------
  def __init__( self, app, props ):
    super( PlotDataSetPropsDialogTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.props = props

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialogTestFrame._InitUI()	-
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
  #	METHOD:		PlotDataSetPropsDialogTestFrame._OnEdit()	-
  #----------------------------------------------------------------------
  def _OnEdit( self, ev ):
    ev.Skip()

    dialog = PlotDataSetPropsDialog( self )
    dialog.ShowModal( self.props )
    self.props = dialog.GetProps()
    print json.dumps( self.props )

    dialog.Destroy()
  #end _OnEdit


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialogTestFrame._OnQuit()	-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    self.app.ExitMainLoop()
  #end _OnQuit

#end PlotDataSetPropsDialogTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  PlotDataSetPropsDialogTestApp.main()
