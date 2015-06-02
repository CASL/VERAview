#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		basewidget.py					-
#	HISTORY:							-
#		2014-11-25	leerw@ornl.gov				-
#------------------------------------------------------------------------
#import os, sys, threading, traceback
import os, sys

try:
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import *
from event.state import *
from widget import *


#------------------------------------------------------------------------
#	CLASS:		BaseWidget					-
#------------------------------------------------------------------------
class BaseWidget( Widget ):
  """Simple widget implementation for testing.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    self.t1 = None
    self.t2 = None
    super( BaseWidget, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Basic'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    #super( BaseWidget, self ).HandleStateChange( reason )

    self.t1.Clear()
    if self.state != None:
      self.t1.AppendText( 'axialCm=%f' % self.state.axialCm )
      self.t1.AppendText( ', axialLevel=%d' % self.state.axialLevel )
      self.t1.AppendText( ', scale=%d' % self.state.scale )

    self.t2.Clear()
    if self.state != None and self.state.depletionData != None:
      self.t2.AppendText( 'depletionData=' + str( self.state.depletionData ) )
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Implementation classes must override.
"""
    self.t1 = wx.TextCtrl(
        self, -1, '',
	size = ( -1, 20 ),
	style = wx.TE_MULTILINE | wx.TE_READONLY
	)
    self.t2 = wx.TextCtrl(
        self, -1, '',
	size = ( -1, 20 ),
	style = wx.TE_MULTILINE | wx.TE_READONLY
	)

    vbox = wx.BoxSizer( wx.VERTICAL )
    vbox.Add( self.t1, 0, border = 2, flag = wx.EXPAND )
    vbox.Add( self.t2, 0, border = 2, flag = wx.EXPAND )
    self.SetSizer( vbox )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		SetState()					-
  #----------------------------------------------------------------------
#  def SetState( self, state ):
#    super( BaseWidget, self ).SetState( state )
#    #self.state = state
#    self.HandleStateChange()
  #end SetState
#end BaseWidget
