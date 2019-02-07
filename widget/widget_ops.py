#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget_ops.py				        -
#	HISTORY:							-
#		2018-12-24	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, os, sys
import pdb  # set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

#from event.state import *


#------------------------------------------------------------------------
#	CLASS:		WidgetBusyEventOp                               -
#------------------------------------------------------------------------
class WidgetBusyEventOp( object ):
  """Per-user widget configuration.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetBusyEventOp.__call__()                    -
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """
"""
    instance = args[ 0 ]
    parent = instance.GetTopLevelParent()
    if parent and hasattr( parent, 'ShowBusy' ):
      parent.ShowBusy( True )
      wx.CallLater( 100, self.do_later, *args, **kwargs )
    else:
      self.func( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetBusyEventOp.__get__()                     -
  #----------------------------------------------------------------------
  def __get__( self, instance, owner ):
    """
"""
    return  functools.partial( self.__call__, instance )
    #3  return  types.MethodType( self, instance ) if instance else self
  #end __get__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetBusyEventOp.__init__()                    -
  #----------------------------------------------------------------------
  def __init__( self, func ):
    """
"""
    self.func = func
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetBusyEventOp.do_later()                    -
  #----------------------------------------------------------------------
  def do_later( self, *args, **kwargs ):
    self.func( *args, **kwargs )
    args[ 0 ].GetTopLevelParent().ShowBusy( False )
  #end do_later

#end WidgetBusyEventOp
