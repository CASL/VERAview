#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_list_bean.py				-
#	HISTORY:							-
#		2018-02-06	leerw@ornl.gov				-
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


#------------------------------------------------------------------------
#	CLASS:		DataSetListBean					-
#------------------------------------------------------------------------
class DataSetListBean( wx.Panel ):
  """Panel with controls for adding and removing (for now) calculated
average datasets.
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, qds_names, single_select = True, id = -1 ):
    super( DataSetListBean, self ).__init__( container, id )

    self.fQdsNames = qds_names
    self.fIsSingleSelect = single_select
    self.fListBox = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetListBean, self ).Enable( flag )
    self.fListBox.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean.GetQdsNames()			-
  #----------------------------------------------------------------------
  def GetQdsNames( self ):
    """
"""
    return  self.fQdsNames
  #end GetQdsNames


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean.GetSelections()			-
  #----------------------------------------------------------------------
  def GetSelections( self ):
    """
"""
    return  self.fListBox.GetSelections() if self.fListBox is not None else []
  #end GetSelections


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, is_selected_func = None ):
    """
"""
    styles = wx.LB_SINGLE if self.fIsSingleSelect else wx.LB_MULTIPLE
    styles |= wx.LB_ALWAYS_SB

    choice_names = [ x.displayName for x in self.fQdsNames ]
    self.fListBox = wx.ListBox(
	self, wx.ID_ANY,
	choices = choice_names, style = styles
        )

#		-- Lay Out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add(
	wx.StaticText(
	    self, -1, 
	    label = 'Datasets:', style = wx.ALIGN_LEFT
	    ),
	0, wx.LEFT, 4
        )
    sizer.Add( self.fListBox, 1, wx.ALL | wx.EXPAND, 4 )
    self.Fit()
    #self.Layout()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListBean.SetSelections()			-
  #----------------------------------------------------------------------
  def SetSelections( self, is_selected_func ):
    """
"""
    if not self.fIsSingleSelect:
      for i in xrange( self.fListBox.GetCount() ):
        if is_selected_func( self.fQdsNames[ i ] ):
          self.fListBox.SetSelection( i )
        else:
          self.fListBox.Deselect( i )
  #end SetSelections


#------------------------------------------------------------------------
#	CLASS:		DataSetListDialog				-
#------------------------------------------------------------------------
class DataSetListDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetListBean reference
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'qds_names' parameter, 'single_select' is optional and assumed
True
"""
#		-- Assert
#		--
    qds_names = kwargs.get( 'qds_names', [] )
    if 'qds_names' in kwargs:
      del kwargs[ 'qds_names' ]

    single_select = kwargs.get( 'single_select', True )
    if 'single_select' in kwargs:
      del kwargs[ 'single_select' ]

    if 'title' not in kwargs:
      kwargs[ 'title' ] = \
          'Select Dataset' if single_select else 'Select Datasets'

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetListDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fSelections = []

    self._InitUI( qds_names, single_select )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog.GetBean()			-
  #----------------------------------------------------------------------
  def GetBean( self ):
    return  self.fBean
  #end GetBean


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog.GetSelections()		-
  #----------------------------------------------------------------------
  def GetSelections( self ):
    """
    Returns:
        list(DataSetName): list of selections, possibly empty
"""
    return  self.fSelections
  #end GetSelections


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, qds_names, single_select ):
    self.fBean = DataSetListBean( self, qds_names, single_select, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    ok_button = wx.Button( self, label = '&OK' )
    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
    ok_button.SetDefault()
    cancel_button = wx.Button( self, label = 'Cancel' )
    cancel_button.Bind( wx.EVT_BUTTON, self._OnButton )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddSpacer( 8 )
    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
	self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.SetSizer( sizer )
    self.SetTitle( 'Select Dataset' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

    retcode = 0
    obj = ev.GetEventObject()
    if obj.GetLabel() != 'Cancel':
      selection_indexes = self.fBean.GetSelections()
      qds_names = self.fBean.GetQdsNames()
      self.fSelections = [ qds_names[ i ] for i in selection_indexes ]
      retcode = 1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetListDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    self.fSelections = []
    return  super( DataSetListDialog, self ).ShowModal()
  #end ShowModal


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	bean						-
  #----------------------------------------------------------------------
  bean = property( GetBean )


  #----------------------------------------------------------------------
  #	PROPERTY:	selections					-
  #----------------------------------------------------------------------
  selections = property( GetSelections )

#end DataSetListDialog
