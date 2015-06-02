#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		grid_sizer_bean.py				-
#	HISTORY:							-
#		2015-02-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
  import wx, wx.lib.newevent
except ImportException:
  raise ImportError, 'The wxPython module is required for this component'

#from event.state import *
#from legend import *
#from widget import *


#------------------------------------------------------------------------
#	EVENT:		GridSizerEvent, EVT_GRID_SIZER			-
#	PROPERTIES:							-
#	  source	reference to source component
#	  value		( rows, cols )
#------------------------------------------------------------------------
GridSizerEvent, EVT_GRID_SIZER = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		GridSizerBean					-
#------------------------------------------------------------------------
class GridSizerBean( wx.Panel ):
  """Simple Panel enclosing a Slider for now.  In the future there might
be some additional stuff like a representation of the axial pitch.

Properties:
  gridSizerForm		reference to component
  gridSizerGraphic	reference to component
  value			( rows, cols )
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerBean.gridSizerForm			-
  #----------------------------------------------------------------------
  @property
  def gridSizerForm( self ):
    """reference to component instance, read-only"""
    return  self.gridSizerForm
  #end gridSizerForm.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerBean.gridSizerGraphic			-
  #----------------------------------------------------------------------
  @property
  def gridSizerGraphic( self ):
    """reference to component instance, read-only"""
    return  self.gridSizerGraphic
  #end gridSizerGraphic.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerBean.value				-
  #----------------------------------------------------------------------
  @property
  def value( self ):
    """( rows, cols )"""
    return  self.fValue
  #end value.getter

#  @value.deleter
#  def value( self ):
#    pass
#  #end value.deleter

  @value.setter
  def value( self, pair ):
    if pair != None and len( pair ) >= 2:
      self.fValue = pair
      if self.fGridSizerForm != None:
        self.fGridSizerForm.value = pair
      if self.fGridSizerGraphic != None:
        self.fGridSizerGraphic.value = pair
    #end if
  #end value.setter


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( GridSizerBean, self ).__init__( container, id )

    self.fGridSizerForm = None
    self.fGridSizerGraphic = None
    self.fValue = ( 1, 1 )
    self._InitUI()
  #end __init__


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean.Enable()				-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( GridSizerBean, self ).Enable( flag )
    if self.fGridSizerForm != None:
      self.fGridSizerForm.Enable( flag )
    if self.fGridSizerGraphic != None:
      self.fGridSizerGraphic.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean.GetMaxValues()			-
  #----------------------------------------------------------------------
  def GetMaxValues( self, max_rows, max_cols ):
    """
@return			( max_rows, max_cols )
"""
    result = (
        self.fGridSizerForm.colSpinner.GetRange()[ 1 ],
	self.fGridSizerForm.rowSpinner.GetRange()[ 1 ]
	)
    return  result
  #end GetMaxValues


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean.GetValue()			-
  #----------------------------------------------------------------------
  def GetValue( self ):
    return  self.value
  #end GetValue


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Form
#		--
    self.fGridSizerForm = GridSizerForm( self, -1 )
    self.fGridSizerForm.Bind( EVT_GRID_SIZER, self._OnSizer )

#		-- Graphic
#		--
    self.fGridSizerGraphic = GridSizerGraphic( self, -1 )
    self.fGridSizerGraphic.SetMinSize( wx.Size( 200, 200 ) )
    self.fGridSizerGraphic.Bind( EVT_GRID_SIZER, self._OnSizer )

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add( self.fGridSizerForm, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP, 6 )
    sizer.Add( self.fGridSizerGraphic, 0, wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP, 6 )
    sizer.AddStretchSpacer()
    self.SetSizer( sizer )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean._OnSizer()			-
  #----------------------------------------------------------------------
  def _OnSizer( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()

    if ev.value != self.fValue:
      self.fValue = ev.value

      if ev.source == self.fGridSizerForm:
        self.fGridSizerGraphic.value = ev.value
      elif ev.source == self.fGridSizerGraphic:
        self.fGridSizerForm.value = ev.value

      wx.PostEvent( self, GridSizerEvent( source = self, value = self.fValue ) )
    #end if changed
  #end _OnSizer


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean.SetMaxValues()			-
  #----------------------------------------------------------------------
  def SetMaxValues( self, max_rows, max_cols ):
    self.fGridSizerForm.colSpinner.SetRange( 1, max_cols )
    self.fGridSizerForm.rowSpinner.SetRange( 1, max_rows )
    self.fGridSizerGraphic.maxValues = ( max_rows, max_cols )
  #end SetMaxValues


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerBean.SetValue()			-
  #----------------------------------------------------------------------
  def SetValue( self, max_rows, max_cols ):
    self.value = ( max_rows, max_cols )
  #end SetValue
#end GridSizerBean


#------------------------------------------------------------------------
#	CLASS:		GridSizerForm					-
#------------------------------------------------------------------------
class GridSizerForm( wx.Panel ):
  """Simple panel with rows and columns spinners.
Properties:
  colSpinner		reference to wx.SpinCtrl
  rowSpinner		reference to wx.SpinCtrl
  value			( rows, cols )
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerForm.colSpinner			-
  #----------------------------------------------------------------------
  @property
  def colSpinner( self ):
    """reference to wx.SpinCtrl instance, read-only"""
    return  self.fColSpinner
  #end colSpinner.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerForm.rowSpinner			-
  #----------------------------------------------------------------------
  @property
  def rowSpinner( self ):
    """reference to wx.SpinCtrl instance, read-only"""
    return  self.fRowSpinner
  #end rowSpinner.getter


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( GridSizerForm, self ).__init__( container, id )

    self.fColSpinner = None
    self.fRowSpinner = None
    self.fValue = ( 1, 1 )
    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerForm.value				-
  #----------------------------------------------------------------------
  @property
  def value( self ):
    """( rows, cols )"""
    return  self.fValue
  #end value.getter

#  @value.deleter
#  def value( self ):
#    pass
#  #end value.deleter

  @value.setter
  def value( self, pair ):
    if pair != None and len( pair ) >= 2:
      self.fValue = pair
      if self.fColSpinner != None:
        self.fColSpinner.SetValue( pair[ 1 ] )
      if self.fRowSpinner != None:
        self.fRowSpinner.SetValue( pair[ 0 ] )
    #end if
  #end value.setter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerForm.Enable()				-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( GridSizerForm, self ).Enable( flag )
    if self.fColSpinner != None:
      self.fColSpinner.Enable( flag )
    if self.fRowSpinner != None:
      self.fRowSpinner.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerForm._InitUI()				-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Components
#		--
    rows_label = wx.StaticText( self, -1, 'Rows: ' )
    self.fRowSpinner = wx.SpinCtrl( self, -1, min = 1, max = 5, initial = 1 )
    self.fRowSpinner.Bind( wx.EVT_SPINCTRL, self._OnSpinner )

    cols_label = wx.StaticText( self, -1, 'Cols: ' )
    self.fColSpinner = wx.SpinCtrl( self, -1, min = 1, max = 5, initial = 1 )
    self.fColSpinner.Bind( wx.EVT_SPINCTRL, self._OnSpinner )

    sizer = wx.BoxSizer( wx.HORIZONTAL )
    sizer.Add( rows_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0 )
    sizer.Add( self.fRowSpinner, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0 )

    sizer.AddSpacer( 10 )
    sizer.Add( cols_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0 )
    sizer.Add( self.fColSpinner, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0 )

    self.SetSizer( sizer )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerForm._OnSpinner()			-
  #----------------------------------------------------------------------
  def _OnSpinner( self, ev ):
    """Handles events from the axial slider.  Called on the UI thread.
"""
    ev.Skip()

    cols = self.fColSpinner.GetValue()
    rows = self.fRowSpinner.GetValue()
    if rows != self.fValue[ 0 ] or cols != self.fValue[ 1 ]:
      self.fValue = ( rows, cols )
      wx.PostEvent( self, GridSizerEvent( source = self, value = self.fValue ) )
  #end _OnSpinner
#end GridSizerForm


#------------------------------------------------------------------------
#	CLASS:		GridSizerGraphic				-
#------------------------------------------------------------------------
class GridSizerGraphic( wx.Panel ):
  """Simple panel with rows and columns spinners.
Properties:
  maxValues		( rows, cols )
  value			( rows, cols )
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerGraphic.maxValues			-
  #----------------------------------------------------------------------
  @property
  def maxValues( self ):
    """( rows, cols )"""
    return  self.fMaxValues
  #end maxValues.getter

#  @maxValues.deleter
#  def value( self ):
#    pass
#  #end maxValues.deleter

  @maxValues.setter
  def maxValues( self, pair ):
    if pair != None and len( pair ) >= 2:
      self.fMaxValues = pair
      self.Refresh()
    #end if
  #end maxValues.setter


  #----------------------------------------------------------------------
  #	PROPERTY:	GridSizerGraphic.value				-
  #----------------------------------------------------------------------
  @property
  def value( self ):
    """( rows, cols )"""
    return  self.fValue
  #end value.getter

#  @value.deleter
#  def value( self ):
#    pass
#  #end value.deleter

  @value.setter
  def value( self, pair ):
    if pair != None and len( pair ) >= 2:
      self.fValue = pair
      self.Refresh()
    #end if
  #end value.setter


#		-- Builtin Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( GridSizerGraphic, self ).__init__( container, id )

    self.fMaxValues = ( 5, 5 )
    self.fValue = ( 1, 1 )
    self.fRectSize = 0
    self._InitUI()
  #end __init__


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._DoMouseEvent()		-
  #----------------------------------------------------------------------
  def _DoMouseEvent( self, x, y ):
    """Called from _OnMouseDown() and _OnMouseMotion().
Assumes fRectSize gt 0.
"""
    cols = (x + self.fRectSize - 1) / self.fRectSize
    rows = (y + self.fRectSize - 1) / self.fRectSize

    if rows != self.fValue[ 0 ] or cols != self.fValue[ 1 ]:
      self.fValue = ( rows, cols )
      wx.PostEvent( self, GridSizerEvent( source = self, value = self.fValue ) )
      self.Refresh()
    #end if
  #end _DoMouseEvent


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( GridSizerGraphic, self ).Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
    self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
    self.SetMinClientSize( wx.Size( 100, 100 ) )
    self.Bind( wx.EVT_LEFT_DOWN, self._OnMouseDown )
    self.Bind( wx.EVT_MOTION, self._OnMouseMotion )
    self.Bind( wx.EVT_PAINT, self._OnPaint )
    self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._OnMouseDown()			-
  #----------------------------------------------------------------------
  def _OnMouseDown( self, ev ):
    if self.fRectSize > 0:
      self._DoMouseEvent( ev.GetX(), ev.GetY() )
  #end _OnMouseDown


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._OnMouseMotion()		-
  #----------------------------------------------------------------------
  def _OnMouseMotion( self, ev ):
    if ev.Dragging() and self.fRectSize > 0:
      self._DoMouseEvent( ev.GetX(), ev.GetY() )
  #end _OnMouseMotion


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._OnPaint()			-
  #----------------------------------------------------------------------
  def _OnPaint( self, ev ):
    wd, ht = self.GetClientSize()

    dc = wx.AutoBufferedPaintDC( self )
    dc.SetBackground( wx.Brush( wx.Colour( 255, 255, 255, 255 ), wx.SOLID ) )
    #dc.SetBackgroundMode( wx.TRANSPARENT )
    dc.Clear()

    if self.fRectSize > 0:
      off_brush = wx.TRANSPARENT_BRUSH
      off_pen = wx.Pen( wx.Colour( 0, 0, 0, 255 ), 2 )

      on_brush = wx.Brush( wx.Colour( 255, 0, 0, 200 ) )
      on_pen = wx.Pen( wx.Colour( 155, 0, 0, 255 ), 2 )

      y = 0
      for row in range( 0, self.fMaxValues[ 0 ] ):
	x = 0
        for col in range( 0, self.fMaxValues[ 1 ] ):
	  if col < self.fValue[ 1 ] and row < self.fValue[ 0 ]:
	    dc.SetBrush( on_brush )
	    dc.SetPen( on_pen )
	  else:
	    dc.SetBrush( off_brush )
	    dc.SetPen( off_pen )
	  dc.DrawRectangle( x, y, self.fRectSize, self.fRectSize )
	  x += self.fRectSize
	#end for colow
        y += self.fRectSize
      #end for row

#      for row in range( 0, self.fValue[ 0 ] ):
#	 x = 0
#        for col in range( 0, self.fValue[ 1 ] ):
#	  dc.DrawRectangle( x, y, self.fRectSize, self.fRectSize )
#	  x += self.fRectSize
#	#end for colow
#        y += self.fRectSize
#      #end for row

#      dc.SetBrush( off_brush )
#      dc.SetPen( off_pen )
#      for row in range( self.fValue[ 0 ], self.fMaxValues[ 0 ] ):
#	 x = 0
#        for col in range( self.fValue[ 1 ], self.fMaxValues[ 1 ] ):
#	  dc.DrawRectangle( x, y, self.fRectSize, self.fRectSize )
#	  x += self.fRectSize
#	#end for colow
#        y += self.fRectSize
#      #end for row
    #end if
  #end _OnPaint


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerGraphic._OnSize()			-
  #----------------------------------------------------------------------
  def _OnSize( self, ev ):
    wd, ht = self.GetClientSize()
    self.fRectSize = int( min( wd, ht ) / max( *self.fMaxValues ) )
    self.Refresh()
  #end _OnSize
#end GridSizerGraphic
