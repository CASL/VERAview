#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		exposure_slider.py				-
#	HISTORY:							-
#		2018-03-20	leerw@ornl.gov				-
#	  Using wx.Timer to eat transient events.
#		2016-03-14	leerw@ornl.gov				-
#	  Setting page size.
#		2016-02-20	leerw@ornl.gov				-
#	  Added {Decr,Incr}ement() methods.
#		2015-03-11	leerw@ornl.gov				-
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
#	EVENT:		StateIndexEvent, EVT_STATE_INDEX		-
#	PROPERTIES:							-
#	  value		0-based index
#------------------------------------------------------------------------
StateIndexEvent, EVT_STATE_INDEX = wx.lib.newevent.NewEvent()

TIMERID_EXPOSURE_SCROLL = 300


#------------------------------------------------------------------------
#	CLASS:		ExposureSliderBean				-
#------------------------------------------------------------------------
class ExposureSliderBean( wx.Panel ):
  """Simple Panel enclosing a Slider for now.  In the future there might
be some additional stuff like a representation of the exposure value.

Attributes/properties:
  slider		reference to slider
  stateIndex		current 0-based index
"""


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( ExposureSliderBean, self ).__init__( container, id )

    self.fSlider = None
    self.fTimer = None
    self.fTransientValue = None
    self._InitUI()
  #end __init__


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	slider						-
  #----------------------------------------------------------------------
  @property
  def slider( self ):
    """reference to wx.Slider instance, read-only"""
    return  self.fSlider
  #end axialLevel.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	stateIndex					-
  #----------------------------------------------------------------------
  @property
  def stateIndex( self ):
    """0-based index, not deletable"""
    return  self.fSlider.GetValue() - 1  if self.fSlider is not None  else  -1
  #end stateIndex.getter


#  @stateIndex.deleter
#  def stateIndex( self ):
#    pass
#  #end stateIndex.deleter


  @stateIndex.setter
  def stateIndex( self, value ):
    if self.fSlider is not None:
      cur_value = self.fSlider.GetValue()
      if cur_value != value + 1:
        self.fSlider.SetValue( value + 1 )
        self.fSlider.Refresh()
  #end stateIndex.setter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean.Decrement()			-
  #----------------------------------------------------------------------
  def Decrement( self ):
    if self.fSlider.GetValue() > self.fSlider.GetMin():
      val = self.fSlider.GetValue() - 1
      self.fSlider.SetValue( val )
      #wx.PostEvent( self, StateIndexEvent( value = val - 1 ) )
      self._UpdateValue( val )
  #end Decrement


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( ExposureSliderBean, self ).Enable( flag )
    if self.fSlider is not None:
      self.fSlider.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean.Increment()			-
  #----------------------------------------------------------------------
  def Increment( self ):
    if self.fSlider.GetValue() < self.fSlider.GetMax():
      val = self.fSlider.GetValue() + 1
      self.fSlider.SetValue( val )
      #wx.PostEvent( self, StateIndexEvent( value = val - 1 ) )
      self._UpdateValue( val )
  #end Increment


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Axial slider
#		--
    slider_label = wx.StaticText( self, -1, 'State: ' )

    self.fSlider = wx.Slider(
        self, -1,
	value = 1, minValue = 1, maxValue = 999,
	pos = wx.DefaultPosition, size = ( -1, -1 ),
	style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS
	)
    self.fSlider.SetPageSize( 1 )
    self.fSlider.Bind( wx.EVT_SCROLL, self._OnSlider )
    self.fSlider.Disable()

    self.fTimer = wx.Timer( self, TIMERID_EXPOSURE_SCROLL )
    self.Bind( wx.EVT_TIMER, self._OnTimer )

    sizer = wx.BoxSizer( wx.HORIZONTAL )
    sizer.Add( slider_label, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_CENTER )

    slider_wrapper = wx.BoxSizer( wx.HORIZONTAL )
    slider_wrapper.Add(
        self.fSlider, 1, wx.EXPAND | wx.RIGHT,
        self.fSlider.GetFont().GetPixelSize().width
        )
    #sizer.Add( self.fSlider, 1, wx.ALL | wx.EXPAND, 4 )
    sizer.Add( slider_wrapper, 1, wx.ALL | wx.EXPAND, 4 )
    self.SetSizer( sizer )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean._OnSlider()			-
  #----------------------------------------------------------------------
  def _OnSlider( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()
    obj = ev.GetEventObject()
    val = obj.GetValue()

    #wx.PostEvent( self, StateIndexEvent( value = val - 1 ) )
    self._UpdateValue( val )
  #end _OnSlider


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean._OnTimer()			-
  #----------------------------------------------------------------------
  def _OnTimer( self, ev ):
    """
"""
    if ev.Timer.Id == TIMERID_EXPOSURE_SCROLL:
      if self.fTransientValue is not None:
        wx.PostEvent( self, StateIndexEvent( value = self.fTransientValue - 1 ) )
	self.fTransientValue = None
    #end if ev.Timer.Id == TIMERID_EXPOSURE_SCROLL
  #end _OnTimer


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean._UpdateValue()		-
  #----------------------------------------------------------------------
  def _UpdateValue( self, val ):
    """
"""
    if val != self.fTransientValue:
      self.fTransientValue = val
      self.fTimer.Start( 500, wx.TIMER_ONE_SHOT )
  #end _UpdateValue


  #----------------------------------------------------------------------
  #	METHOD:		ExposureSliderBean.SetRange()			-
  #----------------------------------------------------------------------
  def SetRange( self, lo, hi ):
    """
"""
    #self.axialLevel = lo
    if self.fSlider is not None:
      self.fSlider.SetRange( lo, hi )
      self.fSlider.Refresh()
  #end SetRange
#end ExposureSliderBean
