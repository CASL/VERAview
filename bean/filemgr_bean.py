#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		filemgr_mgr.py					-
#	HISTORY:							-
#		2017-04-21	leerw@ornl.gov				-
#	  Catching HtmlException and using HtmlMessageDialog.
#		2017-04-13	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from bean.html_message_dialog import *
from data.datamodel import *
from data.datamodel_mgr import *


#------------------------------------------------------------------------
#	EVENT:		DataSetChoiceEvent, EVT_DATASET_CHOICE		-
#	PROPERTIES:							-
#	  value		same as DataSetChooserBean value property
#------------------------------------------------------------------------
#DataSetChoiceEvent, EVT_DATASET_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		FileManagerBean					-
#------------------------------------------------------------------------
class FileManagerBean( wx.Panel ):
  """Panel with controls for adding and removing VERAOut files.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, dmgr, id = -1 ):
    """
@param  container	owning window
@param  dmgr		DataModelMgr instance
"""
    super( FileManagerBean, self ).__init__( container, id )

    self.fDataModelMgr = dmgr

    self.fCloseButton = \
    self.fFileListBean = \
    self.fOpenButton = None

    self._InitUI()
    self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean.CloseFiles()			-
  #----------------------------------------------------------------------
  def CloseFiles( self, *paths ):
    """
"""
    if paths:
      for path in paths:
        self.fDataModelMgr.CloseModel( path )
      self._UpdateControls()
  #end CloseFiles


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( FileManagerBean, self ).Enable( flag )

    # self.fCreateDsButton, self.fDeleteButton,
    objs = ( self.fCloseButton, self.fFileList, self.fOpenButton )
    for obj in objs:
      obj.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""

#		-- File list
#		--
    self.fFileListBean = wx.ListCtrl(
	self, wx.ID_ANY,
	style = wx.LC_REPORT | wx.LC_VRULES
        )
    self.fFileListBean.InsertColumn( 0, 'Name' )
    self.fFileListBean.InsertColumn( 1, 'Shape' )
    self.fFileListBean.InsertColumn( 2, 'State Points' )

    self.fFileListBean.InsertStringItem( 0, 'X' * 40 )
    self.fFileListBean.SetStringItem( 0, 1, '(999, 999, 999, 999)' )
    self.fFileListBean.SetStringItem( 0, 2, '9999' )
    for i in range( self.fFileListBean.GetColumnCount() ):
      self.fFileListBean.SetColumnWidth( i, -1 )
    self.fFileListBean.Fit()

    self.fFileListBean.Bind( wx.EVT_LIST_ITEM_SELECTED, self._OnListSelect )

#		-- Buttons
#		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
    button_panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    button_sizer = wx.BoxSizer( wx.VERTICAL )
    button_panel.SetSizer( button_sizer )

    self.fOpenButton = wx.Button( button_panel, -1, '&Open File' )
    self.fOpenButton.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnButton, 'open' )
	)

    self.fCloseButton = wx.Button( button_panel, -1, 'C&lose File' )
    self.fCloseButton.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnButton, 'close' )
	)

    #button_sizer.AddStretchSpacer()
    button_sizer.Add(
        self.fOpenButton, 0,
	wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 6
	)
    button_sizer.AddSpacer( 10 )
    button_sizer.Add(
        self.fCloseButton, 0,
	wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, 6
	)
    #button_sizer.AddStretchSpacer()

#		-- Lay Out
#		--
    button_panel_wrapper = wx.BoxSizer( wx.VERTICAL )
    button_panel_wrapper.Add(
        button_panel, 0,
	wx.ALIGN_TOP | wx.ALL, 8
	)
    button_panel_wrapper.AddStretchSpacer()

    inner_sizer = wx.BoxSizer( wx.HORIZONTAL )
    inner_sizer.Add(
        self.fFileListBean, 1,
	wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 4
	)
    inner_sizer.Add(
        button_panel_wrapper, 0,
	wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL, 4
	)

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add(
	wx.StaticText(
	    self, -1,
	    label = 'VERAOutput Files:', style = wx.ALIGN_LEFT
	    ),
	0, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.LEFT | wx.TOP, 4
        )
    sizer.Add( inner_sizer, 1, wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 4 )

    self.Fit()
    #self.Layout()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, mode, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    if mode == 'close':
      if self.fFileListBean.GetSelectedItemCount() > 0:
	ndx = self.fFileListBean.GetFirstSelected()
        files = [ self.fFileListBean.GetItemText( ndx, 0 ) ]

	ndx = self.fFileListBean.GetNextSelected( ndx )
	while ndx >= 0:
	  files.append( self.fFileListBean.GetItemText( ndx, 0 ) )
	  ndx = self.fFileListBean.GetNextSelected( ndx )

	self.CloseFiles( *files )
    #end if mode == 'close'

    elif mode == 'open':
      dialog = wx.FileDialog(
	  self, 'Open VERAOutput File', '', '',
	  'HDF5 files (*.h5)|*.h5',
	  wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR
          )
      path = None
      if dialog.ShowModal() != wx.ID_CANCEL:
        path = dialog.GetPath()
      dialog.Destroy()

      if path:
	self.OpenFile( path )
    #end elif mode == 'open'
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean._OnListSelect()			-
  #----------------------------------------------------------------------
  def _OnListSelect( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()
    self.fCloseButton.Enable()
  #end _OnListSelect


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean.OpenFile()			-
  #----------------------------------------------------------------------
  def OpenFile( self, path ):
    """
"""
    try:
      self.fDataModelMgr.OpenModel( path )
      self._UpdateControls()

    except HtmlException, ex:
      ex.htmlMessage
      HtmlMessageDialog.ShowBox(
          HtmlMessageDialog.CreateDocument( ex.htmlMessage ),
	  'Cannot Open: ' + path, self
          )

    except Exception, ex:
      wx.MessageBox(
          #'File "{0:s}" is incompatible\n\n{1:s}'.format( path, str( ex ) ),
	  str( ex ),
	  'Error Opening VERAOutput File',
	  wx.ICON_WARNING | wx.OK_DEFAULT,
	  self
	  )
  #end OpenFile


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerBean._UpdateControls()		-
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    """
"""
    self.fFileListBean.DeleteAllItems()

    model_names = list( self.fDataModelMgr.GetDataModelNames() )
    model_names.sort()

    ndx = 0
    for name in model_names:
      model = self.fDataModelMgr.GetDataModel( name )
      self.fFileListBean.InsertStringItem( ndx, model.name )
      core = model.core
      self.fFileListBean.SetStringItem(
	  ndx, 1,
	  '({0:d}, {1:d}, {2:d}, {3:d})'.\
	      format( core.npiny, core.npinx, core.nax, core.nass )
          )
      self.fFileListBean.SetStringItem(
	  ndx, 2,
	  '({0:d})'.format( model.GetStatesCount() )
          )

      ndx += 1
    #end for name

    self.fCloseButton.Enable( len( model_names ) > 0 )
  #end _UpdateControls
#end FileManagerBean


#------------------------------------------------------------------------
#	CLASS:		FileManagerDialog				-
#------------------------------------------------------------------------
class FileManagerDialog( wx.Dialog ):
  """
Properties:
  bean			FileManagerBean reference
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'dmgr' parameter.
"""
#		-- Assert
#		--
    if 'dmgr' not in kwargs:
      raise  Exception( 'dmgr argument required' )

    dmgr = kwargs.get( 'dmgr' )
    del kwargs[ 'dmgr' ]

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( FileManagerDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    #self.fResult = None

    self._InitUI( dmgr )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog.GetBean()			-
  #----------------------------------------------------------------------
  def GetBean( self ):
    return  self.fBean
  #end GetBean


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog.GetResult()			-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, dmgr ):
    """
"""
    self.fBean = FileManagerBean( self, dmgr, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
    close_button.SetDefault()

    button_sizer.AddStretchSpacer()
    button_sizer.Add( close_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
	self.fBean, 1,
	wx.ALIGN_CENTER | wx.ALIGN_TOP | wx.ALL | wx.EXPAND,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.SetSizer( sizer )
    self.SetTitle( 'File Manager' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		FileManagerDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    super( FileManagerDialog, self ).ShowModal()
  #end ShowModal


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	FileManagerDialog.bean				-
  #----------------------------------------------------------------------
  bean = property( GetBean )

#end FileManagerDialog
