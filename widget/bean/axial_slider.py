#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		axial_slider.py					-
#	HISTORY:							-
#		2016-02-20	leerw@ornl.gov				-
#	  Added {Decr,Incr}ement() methods.
#		2015-05-01	leerw@ornl.gov				-
# 	  Added title param to constructor and _InitUI().
#		2015-02-06	leerw@ornl.gov				-
#	  Only updating slider if value changes in axialLevel setter	-
#		2015-01-08	leerw@ornl.gov				-
#	  Generalized from assembly_view.py and core_view.py.
#------------------------------------------------------------------------
import math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx, wx.lib.newevent
#except ImportException:
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

#from event.state import *
#from legend import *
#from widget import *


#------------------------------------------------------------------------
#	EVENT:		AxialLevelEvent, EVT_AXIAL_LEVEL		-
#	PROPERTIES:							-
#	  value		0-based index
#------------------------------------------------------------------------
AxialLevelEvent, EVT_AXIAL_LEVEL = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		AxialSliderBean					-
#------------------------------------------------------------------------
class AxialSliderBean( wx.Panel ):
  """Simple Panel enclosing a Slider for now.  In the future there might
be some additional stuff like a representation of the axial pitch.

Attributes/properties:
  axialLevel		current 0-based axial level
  slider		reference to slider
"""


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, title = 'Axial:' ):
    super( AxialSliderBean, self ).__init__( container, id )

    self.fSlider = None
    self._InitUI( title )
  #end __init__


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	axialLevel					-
  #----------------------------------------------------------------------
  @property
  def axialLevel( self ):
    """0-based axial level, not deletable"""
    return  self.fSlider.GetValue() - 1  if self.fSlider is not None  else  -1
  #end axialLevel.getter


#  @axialLevel.deleter
#  def axialLevel( self ):
#    pass
#  #end axialLevel.deleter


  @axialLevel.setter
  def axialLevel( self, value ):
    if self.fSlider is not None:
      cur_value = self.fSlider.GetValue()
      if cur_value != value:
        self.fSlider.SetValue( value + 1 )
        self.fSlider.Refresh()
  #end axialLevel.setter


  #----------------------------------------------------------------------
  #	PROPERTY:	slider						-
  #----------------------------------------------------------------------
  @property
  def slider( self ):
    """reference to wx.Slider instance, read-only"""
    return  self.fSlider
  #end axialLevel.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean.Decrement()			-
  #----------------------------------------------------------------------
  def Decrement( self ):
    if self.fSlider.GetValue() > self.fSlider.GetMin():
      val = self.fSlider.GetValue() - 1
      self.fSlider.SetValue( val )
      wx.PostEvent( self, AxialLevelEvent( value = val - 1 ) )
  #end Decrement


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( AxialSliderBean, self ).Enable( flag )
    if self.fSlider is not None:
      self.fSlider.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean.Increment()			-
  #----------------------------------------------------------------------
  def Increment( self ):
    if self.fSlider.GetValue() < self.fSlider.GetMax():
      val = self.fSlider.GetValue() + 1
      self.fSlider.SetValue( val )
      wx.PostEvent( self, AxialLevelEvent( value = val - 1 ) )
  #end Increment


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, title = 'Axial:' ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Axial slider
#		--
    slider_label = wx.StaticText( self, -1, title )

    self.fSlider = wx.Slider(
        self, -1,
	value = 1, minValue = 1, maxValue = 99,
	pos = wx.DefaultPosition, size = ( -1, -1 ),
	style =
	    wx.SL_AUTOTICKS | wx.SL_INVERSE | wx.SL_LABELS | wx.SL_RIGHT |
	    wx.VERTICAL
	)
    self.fSlider.Bind( wx.EVT_SCROLL, self._OnSlider )
    self.fSlider.Disable()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( slider_label, 0, wx.ALL | wx.ALIGN_CENTER | wx.ALIGN_TOP )
    sizer.Add( self.fSlider, 1, wx.ALL | wx.EXPAND, 4 )
    self.SetSizer( sizer )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean._OnSlider()			-
  #----------------------------------------------------------------------
  def _OnSlider( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()
    obj = ev.GetEventObject()
    val = obj.GetValue()

    wx.PostEvent( self, AxialLevelEvent( value = val - 1 ) )
  #end _OnSlider


  #----------------------------------------------------------------------
  #	METHOD:		AxialSliderBean.SetRange()			-
  #----------------------------------------------------------------------
  def SetRange( self, lo, hi ):
    """
"""
    #self.axialLevel = lo
    if self.fSlider is not None:
      self.fSlider.SetRange( lo, hi )
      self.fSlider.Refresh()
  #end SetRange
#end AxialSliderBean
