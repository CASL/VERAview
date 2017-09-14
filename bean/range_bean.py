#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		range_bean.py					-
#	HISTORY:							-
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-07-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, re, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from data.datamodel_mgr import *
from data.range_expr import *
from widget.bean.dataset_menu import *


ABOVE_OPS = [ 'N/A', '>', '>=', '!=' ]

BELOW_OPS = [ 'N/A', '<', '<=' ]

REGEX_ws = re.compile( '[\s,]+' )


#------------------------------------------------------------------------
#	CLASS:		MenuWidget					-
#------------------------------------------------------------------------
class MenuWidget( BaseDataModelMenuWidget ):
  """Dummy DataSetModelMenu widget.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		MenuWidget.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, field, callback = None ):
    self.fCallback = \
        callback  if callback and hasattr( callback, '__call__' ) else  None
    self.fField = field
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		MenuWidget.SetDataSet()				-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    if self.fField is not None:
      self.fField.SetValue( str( qds_name ) if qds_name else '' )

      if self.fCallback:
        self.fCallback()
  #end SetDataSet

#end MenuWidget


#------------------------------------------------------------------------
#	CLASS:		RangeBean					-
#------------------------------------------------------------------------
class RangeBean( wx.Panel ):
  """Panel with controls for selecting a dataset and a value range to
ignore.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, id = -1 ):
    super( RangeBean, self ).__init__( parent, id )

    self.fState = state
    #self.fDataMgr = state.dataModelMgr

    self.fAboveComboBox = \
    self.fAboveField = \
    self.fAddButton = \
    self.fBelowComboBox = \
    self.fBelowField = \
    self.fButtonPanel = \
    self.fDataSetMenu = \
    self.fDataSetMenuButton = \
    self.fDataSetNameField = \
    self.fDeleteButton = \
    self.fListBean = \
    self.fOpComboBoxLeft = \
    self.fOpComboBoxRight = None

    self._InitUI()
    self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean.Enable()				-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( RangeBean, self ).Enable( flag )
    for obj in ( self.fAddButton, self.fDeleteButton ):
      if obj is not None:
        obj.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    all_types = DATASET_DEFS.keys()
    name_ht = 28
    name_wd = 280  # 240

#		-- Grid panel
#		--
    grid_wrapper = wx.Panel( self, -1, style = wx.BORDER_THEME )
    gw_sizer = wx.BoxSizer( wx.HORIZONTAL )
    grid_wrapper.SetSizer( gw_sizer )

    grid_panel = wx.Panel( grid_wrapper, -1 )
    grid_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    grid_panel.SetSizer( grid_sizer )

#		-- Dataset panel
#		--
    self.fDataSetNameField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd, name_ht )
        )
    self.fDataSetNameField.SetEditable( False )

    self.fDataSetMenu = DataSetsMenu(
	self.fState, binder = self, mode = 'subsingle',
	ds_types = all_types,
	widget = MenuWidget( self.fDataSetNameField )
	#widget = MenuWidget( self.fDataSetNameField, self.OnNameUpdate )
        )

    self.fDataSetMenuButton = wx.Button( grid_panel, -1, label = 'Select...' )
    self.fDataSetMenuButton.Bind(
        wx.EVT_BUTTON,
	functools.partial(
	    self._OnShowMenu, self.fDataSetMenuButton, self.fDataSetMenu
	    )
	)

    st = wx.StaticText(
        grid_panel, -1, label = 'Dataset:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fDataSetNameField, 1,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fDataSetMenuButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Above range
#		--
    self.fAboveComboBox = wx.ComboBox(
        grid_panel, -1, ABOVE_OPS[ 0 ],
	choices = ABOVE_OPS, style = wx.CB_READONLY
	)
    self.fAboveField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd >> 1, name_ht )
        )
    above_sizer = wx.BoxSizer( wx.HORIZONTAL )
    above_sizer.Add( self.fAboveComboBox, 0, wx.ALIGN_LEFT | wx.ALL, 0 )
    above_sizer.AddSpacer( 10 )
    above_sizer.Add( self.fAboveField, 1, wx.ALIGN_LEFT | wx.ALL, 0 )

    st = wx.StaticText(
        grid_panel, -1, label = 'Above:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        above_sizer, 1,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.AddSpacer( 0 )

#		-- Below range
#		--
    self.fBelowComboBox = wx.ComboBox(
        grid_panel, -1, BELOW_OPS[ 0 ],
	choices = BELOW_OPS, style = wx.CB_READONLY
	)
    self.fBelowField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd >> 1, name_ht )
        )
    below_sizer = wx.BoxSizer( wx.HORIZONTAL )
    below_sizer.Add( self.fBelowComboBox, 0, wx.ALIGN_LEFT | wx.ALL, 0 )
    below_sizer.AddSpacer( 10 )
    below_sizer.Add( self.fBelowField, 1, wx.ALIGN_LEFT | wx.ALL, 0 )

    st = wx.StaticText(
        grid_panel, -1, label = 'Below:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        below_sizer, 1,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.AddSpacer( 0 )

#		-- Add button
#		--
    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    self.fAddButton = \
        wx.Button( grid_panel, -1, label = 'Add', size = ( -1, name_ht ) )
    self.fAddButton.SetFont( self.fAddButton.GetFont().Larger() )
    self.fAddButton.Bind( wx.EVT_BUTTON, self._OnAdd )

    self.fDeleteButton = \
        wx.Button( grid_panel, -1, label = 'Delete', size = ( -1, name_ht ) )
    self.fDeleteButton.Bind( wx.EVT_BUTTON, self._OnDelete )
    self.fDeleteButton.Enable( False )

    button_sizer.Add( self.fAddButton, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    button_sizer.AddSpacer( 16 )
    button_sizer.Add( self.fDeleteButton, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )

    grid_sizer.AddSpacer( 0 )
#    grid_sizer.Add( self.fAddButton, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    grid_sizer.Add( button_sizer, 0, wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0 )
    grid_sizer.AddSpacer( 0 )

#		-- List panel
#		--
    self.fListBean = wx.ListCtrl(
	self, wx.ID_ANY,
	style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VRULES
        )
    self.fListBean.InsertColumn( 0, 'DataSet' )
    self.fListBean.InsertColumn( 1, 'Range' )

    self.fListBean.InsertStringItem( 0, 'X' * 40 )
    self.fListBean.SetStringItem( 0, 1, '>= 9.999e999 and <= 9.999e999' )
    for i in range( self.fListBean.GetColumnCount() ):
      self.fListBean.SetColumnWidth( i, -1 )
    self.fListBean.Fit()
    self.fListBean.Bind( wx.EVT_LIST_ITEM_SELECTED, self._OnListSelect )

#		-- Lay self out
#		--
    gw_sizer.Add( grid_panel, 0, wx.ALL | wx.EXPAND, 8 )
    #gw_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( grid_wrapper, 0, wx.BOTTOM | wx.EXPAND, 10 )
    sizer.Add(
        self.fListBean, 1,
	wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.ALL | wx.EXPAND, 6
	)
    #sizer.AddStretchSpacer()

    self.Fit()

    self.fDataSetMenu.Init()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._OnAdd()				-
  #----------------------------------------------------------------------
  def _OnAdd( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    qds_name = DataSetName( self.fDataSetNameField.GetValue() )
    above_op = str( self.fAboveComboBox.GetValue() )
    try:
      above_value = float( self.fAboveField.GetValue() )
    except:
      above_value = NAN
    below_op = str( self.fBelowComboBox.GetValue() )
    try:
      below_value = float( self.fBelowField.GetValue() )
    except:
      below_value = NAN

    msg = ''
    if len( qds_name.displayName ) == 0:
      msg = 'Please select a dataset'
    elif above_op == ABOVE_OPS[ 0 ] and below_op == BELOW_OPS[ 0 ]:
      msg = 'Please specify at least one term'
    elif above_op != ABOVE_OPS[ 0 ] and math.isnan( above_value ):
      msg = 'Please enter a value for the "above" range'
    elif below_op != BELOW_OPS[ 0 ] and math.isnan( below_value ):
      msg = 'Please enter a value for the "below" range'

    if msg:
      wx.MessageDialog( self, msg, 'Add Range' ).\
          ShowWindowModal()
    else:
      expr_str = ''
      if above_op != ABOVE_OPS[ 0 ]:
	expr_str += '{0:s} {1:6g}'.format( above_op, above_value )
      if below_op != BELOW_OPS[ 0 ]:
	expr_str += ' {0:s} {1:6g}'.format( below_op, below_value )

      self.fState.dataModelMgr.SetDataSetThreshold( qds_name, expr_str )
      self._UpdateControls()
    #end if-else msg
  #end _OnAdd


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._OnDelete()				-
  #----------------------------------------------------------------------
  def _OnDelete( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()
    ndx = self.fListBean.GetFirstSelected()
    if ndx >= 0:
      name = self.fListBean.GetItemText( ndx, 0 )
      qds_name = DataSetName( name )
      self.fState.dataModelMgr.SetDataSetThreshold( qds_name )
      self._UpdateControls()
  #end _OnDelete


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._OnListSelect()			-
  #----------------------------------------------------------------------
  def _OnListSelect( self, ev ):
    """
"""
    ev.Skip()
    self.fDeleteButton.Enable()

    ndx = self.fListBean.GetFirstSelected()
    if ndx >= 0:
      name = self.fListBean.GetItemText( ndx, 0 )
      self.fDataSetNameField.SetValue( name )

      above_op = ABOVE_OPS[ 0 ]
      below_op = BELOW_OPS[ 0 ]
      above_text = ''
      below_text = ''
      expr = self.fListBean.GetItemText( ndx, 1 )

      try:
        range_expr = RangeExpression( expr )
	terms = range_expr.terms
	if 'aboveop' in terms:
	  above_op = terms.get( 'aboveop' )
	if 'abovevalue' in terms:
	  above_text = '{0:.6g}'.format( terms.get( 'abovevalue', 0.0 ) )
	if 'belowop' in terms:
	  below_op = terms.get( 'belowop' )
	if 'belowvalue' in terms:
	  below_text = '{0:.6g}'.format( terms.get( 'belowvalue', 0.0 ) )
      except Exception, ex:
        wx.MessageBox(
	    str( ex ), 'Parsing Expression',
	    wx.ICON_WARNING | wx.OK_DEFAULT
	    )

      self.fAboveComboBox.SetValue( above_op )
      self.fAboveField.SetValue( above_text )
      self.fBelowComboBox.SetValue( below_op )
      self.fBelowField.SetValue( below_text )
    #end if ndx >= 0
  #end _OnListSelect


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean.OnNameUpdate()			-
  #----------------------------------------------------------------------
  def OnNameUpdate( self, *args, **kwargs ):
    """
"""
    pass
    #qds_name = DataSetName( self.fDataSetNameField.GetValue() )
  #end OnNameUpdate


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._OnShowMenu()				-
  #----------------------------------------------------------------------
  def _OnShowMenu( self, button, menu, ev ):
    """
"""
    ev.Skip()
    button.PopupMenu( menu )
  #end _OnShowMenu


  #----------------------------------------------------------------------
  #	METHOD:		RangeBean._UpdateControls()			-
  #----------------------------------------------------------------------
  def _UpdateControls( self ):
    """Must be called on the UI thread.
"""
    self.fListBean.DeleteAllItems()

    range_list = self.fState.dataModelMgr.GetDataSetThreshold()
    if range_list and hasattr( range_list, '__iter__' ) and \
        len( range_list ) > 0:
      ndx = 0
      for ( qds_name, expr ) in range_list:
        self.fListBean.InsertStringItem( ndx, qds_name.name )
	self.fListBean.SetStringItem( ndx, 1, expr.displayExpr )

        ndx += 1
      #end for
    #end if range_list
  #end _UpdateControls

#end RangeBean


#------------------------------------------------------------------------
#	CLASS:		RangeDialog					-
#------------------------------------------------------------------------
class RangeDialog( wx.Dialog ):
  """
Properties:
  bean			RangeBean reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	RangeDialog.bean				-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'state' parameter.
"""
#		-- Assert
#		--
    if 'state' not in kwargs:
      raise  Exception( 'state argument required' )

    state = kwargs.get( 'state' )
    del kwargs[ 'state' ]

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    if 'title' not in kwargs:
      kwargs[ 'title' ] = 'Data Set Thresholds'

    super( RangeDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self._InitUI( state )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog.GetResult()				-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self, state ):
    self.fBean = RangeBean( self, state, -1 )


    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
    close_button.SetDefault()

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    button_sizer.AddStretchSpacer()
    button_sizer.Add( close_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
	self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetSizer( sizer )
    #self.SetTitle( 'Dataset Thresholds' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog._OnButton()				-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.EndModal( 1 )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( 0 )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		RangeDialog.ShowModal()				-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    super( RangeDialog, self ).ShowModal()
  #end ShowModal

#end RangeDialog
