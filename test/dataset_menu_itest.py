#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_menu_itest.py				-
#	HISTORY:							-
#		2016-12-05	leerw@ornl.gov				-
#		2016-08-22	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, json, os, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required to run this program' )

from data.datamodel import *
from event.state import *
from widget.bean.dataset_menu import *


#------------------------------------------------------------------------
#	CLASS:		DataSetMenuTestApp				-
#------------------------------------------------------------------------
class DataSetMenuTestApp( wx.App ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestApp.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    super( DataSetMenuTestApp, self ).__init__( redirect = False )

    self.SetAppName( 'DataSetMenuTest' )

    wx.ToolTip.Enable( True )
    wx.ToolTip.SetAutoPop( 10000 )
    wx.ToolTip.SetDelay( 500 )
    wx.ToolTip.SetReshow( 100 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestApp.OnInit()			-
  #----------------------------------------------------------------------
#  def OnInit( self ):
#    pass  # create and show frame here?
#  #end OnInit


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestApp.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  #'files',
	  '-f', '--files',
	  default = None,
	  help = 'input files, required',
	  nargs = '+'
          )
      parser.add_argument(
	  '--popup-mode',
	  default = 'multi',
	  help = 'mode for popup menu (""/"single", "multi", "selected", "subsingle", "submulti", "subselected"'
          )
      parser.add_argument(
	  '--popup-types',
	  default = None,
	  help = 'dataset types',
	  nargs = '+'
          )
      parser.add_argument(
	  '--pullright-mode',
	  default = '',
	  help = 'mode for pullright menu (""/"single", "multi", "selected", "subsingle", "submulti", "subselected"'
          )
      parser.add_argument(
	  '--pullright-types',
	  default = None,
	  help = 'dataset types',
	  nargs = '+'
          )
      args = parser.parse_args()

      if args.files is None:
        parser.print_help()

      else:
        state = State()
	#data = DataModel( args.file )
	#state.Load( data )
	dmgr = state.GetDataModelMgr()
	for f in args.files:
	  dmgr.OpenModel( f )
        state.Init( dmgr.GetFirstDataModel() )

	app = DataSetMenuTestApp()
	frame = DataSetMenuTestFrame( app, state, args )
	frame.Show()
	app.MainLoop()
      #end if

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

#end DataSetMenuTestApp


#------------------------------------------------------------------------
#	CLASS:		DataSetMenuTestFrame				-
#------------------------------------------------------------------------
class DataSetMenuTestFrame( wx.Frame ):
  """Top level viewer window.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, app, state, args ):
    super( DataSetMenuTestFrame, self ).__init__( None, -1 )

    self.app = app
    self.args = args
    self.state = state

    self.dataSetPopupMenu = None
    self.dataSetPullrightMenu = None
    self.dataSetToggleMap = {}

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    dmgr = self.state.GetDataModelMgr()

#		-- File Menu
#		--
    file_menu = wx.Menu()

    #xxxxx
#    set_menu = wx.Menu()
#    for cat, ds_names in data.GetDataSetNames().iteritems():
#      if cat != 'axial' and cat.find( ':' ) < 0 and ds_names:
#	cat_menu = wx.Menu()
#	for name in ds_names:
#	  item = wx.MenuItem( cat_menu, wx.ID_ANY, name )
#	  self.Bind( wx.EVT_MENU, self._OnDataSetItem, item )
#	  cat_menu.AppendItem( item )
#        cat_item = wx.MenuItem( set_menu, wx.ID_ANY, cat, subMenu = cat_menu )
#	set_menu.AppendItem( cat_item )
#      #end if
#    #end for cat, ds_names
#    set_item = wx.MenuItem( file_menu, wx.ID_ANY, 'Set', subMenu = set_menu )
#    file_menu.AppendItem( set_item )

    quit_item = wx.MenuItem( file_menu, wx.ID_ANY, '&Quit\tCtrl+Q' )
    self.Bind( wx.EVT_MENU, self._OnQuit, quit_item )
    file_menu.AppendItem( quit_item )

#		-- Edit Menu
#		--
    edit_menu = wx.Menu()
    self.dataSetPullrightMenu = DataModelMenu(
        self.state, binder = self, ds_listener = self,
	mode = self.args.pullright_mode,
	ds_types = self.args.pullright_types
	)
    edit_item = wx.MenuItem(
        edit_menu, wx.ID_ANY, '&Dataset',
	subMenu = self.dataSetPullrightMenu
	)
    edit_menu.AppendItem( edit_item )

#		-- Menu Bar
#		--
    mbar = wx.MenuBar()
    mbar.Append( file_menu, '&File' )
    mbar.Append( edit_menu, '&Edit' )
    self.SetMenuBar( mbar )

#		-- Panel with Button
#		--
    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    self.dataSetPopupMenu = DataModelMenu(
        self.state, binder = self, ds_listener = self,
	mode = self.args.popup_mode,
	ds_types = self.args.popup_types
	)
    button = wx.Button( self, wx.ID_ANY, label = 'Set...' )
    self.Bind( wx.EVT_BUTTON, self._OnSetButton )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( button, 0, wx.ALL | wx.EXPAND, 10 )
    button_sizer.AddStretchSpacer()

#		-- Layout
#		--
#    sizer = wx.BoxSizer( wx.HORIZONTAL )
#    self.SetSizer( sizer )
#    sizer.AddStretchSpacer()
#    sizer.Add( button, 0, wx.ALL | wx.EXPAND, 6 )
#    sizer.AddStretchSpacer()
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )
    sizer.Add( button_sizer, 0, wx.ALL| wx.EXPAND, 4 )
    sizer.Add(
	wx.StaticText( self, label = 'Button above is for popup menu' ),
	0, wx.ALL | wx.ALIGN_CENTRE_HORIZONTAL | wx.EXPAND, 4
	)

    sizer.Layout()
    self.Fit()

#		-- Window Events
#		--
    self.Bind( wx.EVT_CLOSE, self._OnQuit )

#		-- Lay Out
#		--
    self.SetTitle( 'DataSetChooserDialog Test' )
    #self.Center()

    self.dataSetPopupMenu.Init()
    self.dataSetPullrightMenu.Init()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame.IsDataSetVisible()		-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, qds_name ):
    return  self.dataSetToggleMap.get( qds_name, False )
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame._OnDataSetItem()		-
  #----------------------------------------------------------------------
  def _OnDataSetItem( self, ev ):
    ev.Skip()

    menu = ev.GetEventObject()
    item = menu.FindItemById( ev.GetId() )

    #xxxxx
    reason = self.state.Change( None, cur_dataset = item.GetItemLabelText() )
    self.state.FireStateChange( reason )
  #end _OnDataSetItem


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame._OnQuit()			-
  #----------------------------------------------------------------------
  def _OnQuit( self, ev ):
    ev.Skip()
    self.app.ExitMainLoop()
  #end _OnQuit


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame._OnSetButton()		-
  #----------------------------------------------------------------------
  def _OnSetButton( self, ev ):
    ev.Skip()

    button = ev.GetEventObject()
    button.PopupMenu( self.dataSetPopupMenu )
  #end _OnSetButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetMenuTestFrame.ToggleDataSetVisible()	-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, qds_name ):
    visible = self.dataSetToggleMap.get( qds_name, False )
    self.dataSetToggleMap[ qds_name ] = not visible
  #end ToggleDataSetVisible

#end DataSetMenuTestFrame


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataSetMenuTestApp.main()
