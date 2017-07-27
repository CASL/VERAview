#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		grid_sizer_dialog.py				-
#	HISTORY:							-
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-03-31	leerw@ornl.gov				-
#	  Added EVT_CHAR_HOOK
#		2015-02-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx, wx.lib.newevent
except ImportException:
  raise ImportError, 'The wxPython module is required for this component'

from grid_sizer_bean import *


#------------------------------------------------------------------------
#	CLASS:		GridSizerDialog					-
#------------------------------------------------------------------------
class GridSizerDialog( wx.Dialog ):
  """
Properties:
  bean			component reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerDialog.bean				-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to component instance, read-only"""
    return  self.fBean
  #end bean.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerDialog.result				-
  #----------------------------------------------------------------------
  @property
  def result( self ):
    """( rows, cols ) or None, read-only"""
    return  self.fResult
  #end result.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerDialog.value				-
  #----------------------------------------------------------------------
#  @property
#  def value( self ):
#    """( rows, cols ), read-only"""
#    return  self.fBean.value  if self.fBean is not None  else ( 1, 1 )
#  #end value.getter


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  #def __init__( self, container, id = -1 ):
  def __init__( self, *args, **kwargs ):
    """
"""
    super( GridSizerDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fResult = None

    self._InitUI()
  #end __init__


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog.GetResult()			-
  #----------------------------------------------------------------------
  def GetResult( self ):
    return  self.result
  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Bean
#		--
    self.fBean = GridSizerBean( self, -1 )

#		-- Button Panel
#		--
    #button_panel = wx.Panel( self, -1 )
    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    ok_button = wx.Button( self, label = '&OK' )
    ok_button.Bind( wx.EVT_BUTTON, self._OnClick )
    cancel_button = wx.Button( self, label = 'Cancel' )
    cancel_button.Bind( wx.EVT_BUTTON, self._OnClick )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddSpacer( 10 )
    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 )
    button_sizer.AddStretchSpacer()

#		-- Lay Out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )

    sizer.Add(
        self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetTitle( 'Set Grid Size' )
    self.SetSizer( sizer )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.fResult = self.fBean.value
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog._OnClick()			-
  #----------------------------------------------------------------------
  def _OnClick( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0  if obj.GetLabel() == 'Cancel' else  1

    if obj.GetLabel() != 'Cancel':
      self.fResult = self.fBean.value

    self.EndModal( retcode )
  #end _OnClick


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self, value = None ):
    self.fResult = None
    if value is not None:
      self.fBean.value = value
    super( GridSizerDialog, self ).ShowModal()
  #end ShowModal
#end GridSizerDialog
