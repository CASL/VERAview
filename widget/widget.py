#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget.py					-
#	HISTORY:							-
#		2015-12-22	leerw@ornl.gov				-
#	  Using Legend2 for a continuous legend.
#		2015-11-18	leerw@ornl.gov				-
#	  Added GetAllow4DDataSets().
#		2015-08-31	leerw@ornl.gov				-
#	  Added GetAnimationIndexes().  Renamed _UpdateState() to
#	  UpdateState() since now called by Animator.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring, generalization.
#		2015-05-11	leerw@ornl.gov				-
#	  New State.axialValue.
#		2015-04-13	leerw@ornl.gov				-
#	  Added GetColor{Contrast,Luminance}().
#		2015-03-19	leerw@ornl.gov				-
#	  Added GetDataSetType().
#		2015-02-11	leerw@ornl.gov				-
# 	  Added GetDarkerColor().
#		2015-02-03	leerw@ornl.gov				-
#	  Replaced CreateMenu() with GetMenuDef().
#		2015-01-30	leerw@ornl.gov				-
# 	  Added CreateMenu().
#		2015-01-05	leerw@ornl.gov				-
#	  Moved _CreateLegendPilImage() here.
#	  Added InvertColorXxx() static methods.
#		2014-12-19	leerw@ornl.gov				-
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-25	leerw@ornl.gov				-
#------------------------------------------------------------------------
#import os, sys, threading, traceback
import math, os, sys, threading
import pdb  # set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

from event.state import *
from legend import *
from legend2 import *


BMAP_NAME_green = 'led_green_16x16'
BMAP_NAME_red = 'led_red_16x16'

DEFAULT_BG_COLOR_TUPLE = ( 155, 155, 155, 255 )

#DEFAULT_BG_COLOR = wx.Colour( *DEFAULT_BG_COLOR_TUPLE )


#------------------------------------------------------------------------
#	CLASS:		Widget						-
#------------------------------------------------------------------------
class Widget( wx.Panel ):
  """Abstract base class for widgets.
"""


#		-- Class Attributes
#		--

  bitmaps_ = {}


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1 ):
    super( Widget, self ).__init__( container, id )

    self.busy = False
    #self.busyCursor = None
    self.container = container
    self.multiDataSets = []  # should always be sorted ascending
    self.state = None

    Widget.GetBitmap( BMAP_NAME_green )
    Widget.GetBitmap( BMAP_NAME_red )

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_BusyBegin()					-
  #----------------------------------------------------------------------
  def _BusyBegin( self ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
"""
    if not self.busy:
      self.busy = True
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
  #end _BusyBegin


  #----------------------------------------------------------------------
  #	METHOD:		_BusyBegin_cursor()				-
  #----------------------------------------------------------------------
  def _BusyBegin_cursor( self ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
"""
    if self.busyCursor == None:
      self.busyCursor = wx.BusyCursor()
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
  #end _BusyBegin_cursor


  #----------------------------------------------------------------------
  #	METHOD:		_BusyBeginOp()					-
  #----------------------------------------------------------------------
  def _BusyBeginOp( self, func, *args ):
    """Show indication of being busy.  Must call _EndBusy().
Must be called from the UI thread.
"""
    if not self.busy:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_red ) )
      self.container.led.Update()
      wx.CallAfter( func, *args )
  #end _BusyBeginOp


  #----------------------------------------------------------------------
  #	METHOD:		_BusyDoOp()					-
  #----------------------------------------------------------------------
  def _BusyDoOp( self, func, *args ):
    """Show some indication of being busy, make the call, then restore from
the busy indicator.
Must be called from the UI thread.
"""

    self._BusyBegin()
    try:
      func( *args )
#      wx.CallAfter( func, *args )
    finally:
      self._BusyEnd()
  #end _BusyDoOp


  #----------------------------------------------------------------------
  #	METHOD:		_BusyEnd()					-
  #----------------------------------------------------------------------
  def _BusyEnd( self ):
    """End indication of being busy.
Must be called from the UI thread.
"""
    if self.busy:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      self.busy = False
  #end _BusyEnd


  #----------------------------------------------------------------------
  #	METHOD:		_BusyEnd_cursor()				-
  #----------------------------------------------------------------------
  def _BusyEnd_cursor( self ):
    """End indication of being busy.
Must be called from the UI thread.
"""
    if self.busyCursor != None:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      del self.busyCursor
      self.busyCursor = None
  #end _BusyEnd_cursor


  #----------------------------------------------------------------------
  #	METHOD:		_BusyEndOp()					-
  #----------------------------------------------------------------------
  def _BusyEndOp( self, func, *args ):
    """End indication of being busy.
Must be called from the UI thread.
"""
    if self.busyCursor != None:
      self.container.led.SetBitmap( Widget.GetBitmap( BMAP_NAME_green ) )
      self.container.led.Update()
      del self.busyCursor
      self.busyCursor = None
      wx.CallAfter( func, *args )
  #end _BusyEndOp


  #----------------------------------------------------------------------
  #	METHOD:		_CalcFontSize()					-
  #----------------------------------------------------------------------
  def _CalcFontSize( self, display_wd ):
    #limits = ( 280, 8, 1280, 28 )
    limits = ( 280, 8, 1280, 32 )
    if display_wd >= limits[ 2 ]:
      size = limits[ 3 ]
    elif display_wd < limits[ 0 ]:
      size = limits[ 1 ]
    else:
      size = limits[ 1 ] + int( math.floor(
          float( display_wd - limits[ 0 ] ) /
	  float( limits[ 2 ] - limits[ 0 ] ) *
	  float( limits[ 3 ] - limits[ 1 ] )
          ) )
    #size = max( size, 6 )
    return  size
  #end _CalcFontSize


  #----------------------------------------------------------------------
  #	METHOD:		CreateAnimateImages()				-
  #----------------------------------------------------------------------
  def CreateAnimateImages( self, temp_dir, over = 'axial' ):
    """
"""
    return  False
  #end CreateAnimateImages


  #----------------------------------------------------------------------
  #	METHOD:		_CreateLegendPilImage()				-
  #----------------------------------------------------------------------
  def _CreateLegendPilImage( self, value_range, font_size = 16 ):
    """For now this is linear only.
@param  value_range	( min, max )
"""
    legend = Legend2( Widget.GetColorTuple, value_range, 10, font_size )
    return  legend.image
  #end _CreateLegendPilImage


  #----------------------------------------------------------------------
  #	METHOD:		_CreateLegendPilImage_0()			-
  #----------------------------------------------------------------------
  def _CreateLegendPilImage_0( self, value_range, font_size = 16 ):
    """For now this is linear only.
@param  value_range	( min, max )
"""
    count = 10
    value_delta = value_range[ 1 ] - value_range[ 0 ]
    value_incr = value_delta / count

    colors = []
    values = []

    cur_value = value_range[ 1 ]
    values.append( cur_value )
    for i in range( count ):
      cur_value -= value_incr

      values.append( cur_value )
      colors.append(
          Widget.GetColorTuple( cur_value - value_range[ 0 ], value_delta, 255 )
	  )
#      cur_value -= value_incr
    #end for

    legend = Legend( values, colors, font_size )
    return  legend.image
  #end _CreateLegendPilImage_0


  #----------------------------------------------------------------------
  #	METHOD:		CreatePrintImage()				-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path ):
    """
Placeholder for widget implementations to create a PNG image.
The default implementation returns None.
@param  file_path	path to file if the widget creates the image
@return			file_path or None if not processed
"""
    #return  wx.EmptyImage( 400, 300 )
    return  None
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		_FindListIndex()				-
  #----------------------------------------------------------------------
#  def _FindListIndex( self, values, value ):
#    """Values in the list are assumed in ascending order.
#@param  values		list of values in ascending order
#@param  value		value to find
#@return			0-based index N, where
#			(values[ N ] le value lt values[ N + 1 ]), or
#			-1 if all items are gt value
#@deprecated	Use DataModel.FindListIndex()
#"""
#    match_ndx = -1
#
#    if len( values ) > 0 and value >= values[ 0 ]:
#      for i in range( len( values ) - 1, -1, -1 ):
#        if value >= values[ i ]:
#	  match_ndx = i
#	  break
#      #end for
#    #end if
#
#    return  match_ndx
#  #end _FindListIndex


  #----------------------------------------------------------------------
  #	METHOD:		FireStateChange()				-
  #----------------------------------------------------------------------
  def FireStateChange( self, **kwargs ):
    self.container.FireStateChange( **kwargs )
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		GetAllow4DDataSets()				-
  #----------------------------------------------------------------------
  def GetAllow4DDataSets( self ):
    """Accessor specifying if the widget can visualize any dataset with a
4-tuple shape.  Extensions must override as necessary.
@return			None
"""
    return  None
  #end GetAllow4DDataSets


  #----------------------------------------------------------------------
  #	METHOD:		GetAnimationIndexes()				-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  None
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		GetContainer()					-
  #----------------------------------------------------------------------
  def GetContainer( self ):
    return  self.container
  #end GetContainer


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetType()				-
  #----------------------------------------------------------------------
  def GetDataSetType( self ):
    """Accessor specifying the type of dataset which can be single-selected
for this widget.  The type is one of 'channel', 'pin', or 'scalar'.
Subclasses should override as this implementation returns None
@return			dataset_type
"""
    return  None
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetEventLockSet()				-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
        STATE_CHANGE_assemblyIndex,
        STATE_CHANGE_axialValue,
#        STATE_CHANGE_axialLevel,
        STATE_CHANGE_scale,
        STATE_CHANGE_stateIndex
        ])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		GetInitialSize()				-
  #----------------------------------------------------------------------
  def GetInitialSize( self ):
    """Returns None.
"""
    return  wx.Size( 640, 480 )
  #end GetInitialSize


  #----------------------------------------------------------------------
  #	METHOD:		GetMenuDef()					-
  #----------------------------------------------------------------------
  def GetMenuDef( self, data_model ):
    """List of (label, handler) pairs to present in a menu.
Returning None means no menu, which is the default implemented here.
@param  data_model	loaded data model, might be None
@return			[ ( label, handler ), ... ]
"""
    return  None
  #end GetMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		GetMultiDataSetType()				-
  #----------------------------------------------------------------------
  def GetMultiDataSetType( self ):
    """Accessor specifying the type of datasets which can be toggled
on/off for this widget.  The type is one of 'axial' or None.
Subclasses should override as this implementation returns None
@return			dataset_type
"""
    return  None
  #end GetMultiDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		GetState()					-
  #----------------------------------------------------------------------
  def GetState( self ):
    return  self.state
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		GetTitle()					-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'unnamed'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		HandleMenuItem()				-
  #----------------------------------------------------------------------
  def HandleMenuItem( self, id ):
    """Menu handler.  Noop implemented here
@param  id		menu item id as specified in GetMenuDef().
"""
    pass
  #end HandleMenuItem


  #----------------------------------------------------------------------
  #	METHOD:		HandleStateChange()				-
  #----------------------------------------------------------------------
  def HandleStateChange( self, reason ):
    """Note value difference checks must occur in UpdateState()
"""
    ct = threading.current_thread()
    print >> sys.stderr, \
        '[Widget.HandleStateChange] reason=%d, thread=%s/%d' % \
        ( reason, ct.name, -1 if ct.ident == None else ct.ident )

    load_mask = STATE_CHANGE_init | STATE_CHANGE_dataModel
    if (reason & load_mask) > 0:
      print >> sys.stderr, \
          '[Core2DView.HandleStateChange] calling _LoadDataModel()'
      self._LoadDataModel()

    else:
      update_args = self.state.CreateUpdateArgs( reason )
      if len( update_args ) > 0:
        wx.CallAfter( self.UpdateState, **update_args )
    #end else not a data model load
  #end HandleStateChange


  #----------------------------------------------------------------------
  #	METHOD:		_InitUI()					-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Implementation classes must override.
"""
    raise  Exception( "subclasses must implement" )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		IsBusy()                                        -
  #----------------------------------------------------------------------
  def IsBusy( self ):
    return  self.busy
  #end IsBusy


  #----------------------------------------------------------------------
  #	METHOD:		_LoadDataModel()				-
  #----------------------------------------------------------------------
  def _LoadDataModel( self ):
    """Must be implemented by extensions.  This is a noop implementation
"""
    pass
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSet()					-
  #----------------------------------------------------------------------
  def SetDataSet( self, ds_name ):
    pass
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		SetState()					-
  #----------------------------------------------------------------------
  def SetState( self, state ):
    self.state = state
    self.HandleStateChange( STATE_CHANGE_init )
  #end SetState


  #----------------------------------------------------------------------
  #	METHOD:		ShowMultiDataSet()				-
  #----------------------------------------------------------------------
  def ShowMultiDataSet( self, name, visible, update_menu = True ):
    """Subclasses should call this when programmatically toggling a dataset.
"""
#    already_visible = name in self.multiDataSets
#    if visible ^ already_visible:

    changed = False
    if visible:
      if name not in self.multiDataSets:
        changed = True
        self.multiDataSets.append( name )
        self.multiDataSets.sort()

    elif name in self.multiDataSets:
      changed = True
      self.multiDataSets.remove( name )

    if changed:
      self._ShowMultiDataSetImpl( name, visible )
      if update_menu:
        self.container.UpdateMultiDataSetMenu( name, visible )
    #end if changing
  #end ShowMultiDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_ShowMultiDataSetImpl()				-
  #----------------------------------------------------------------------
  def _ShowMultiDataSetImpl( self, name, visible ):
    """Subclasses should override this.
"""
    pass
  #end _ShowMultiDataSetImpl


  #----------------------------------------------------------------------
  #	METHOD:		UpdateState()					-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """Must be implemented by extensions.  This is a noop implementation
"""
    pass
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		_UpdateVisibilityMenuItems()			-
  #----------------------------------------------------------------------
  def _UpdateVisibilityMenuItems( self, menu, *suffixes_and_flags ):
    """Must be called on the UI event thread.
@param  menu		menu to process
@param  suffixes_and_flags  ( suffix, flag, ... ) where suffix appears
			after "Show" or "Hide" in the menu item and
			flag is the current visibility state
"""
    if menu != None and \
        suffixes_and_flags != None and len( suffixes_and_flags ) >= 2:
      for item in menu.GetMenuItems():
        label = item.GetItemLabel()

	for i in range( 0, len( suffixes_and_flags ), 2 ):
	  suffix = suffixes_and_flags[ i ]
	  flag = suffixes_and_flags[ i + 1 ]

	  if label.startswith( 'Show ' + suffix ):
	    if flag:
	      item.SetItemLabel( label.replace( 'Show', 'Hide' ) )

	  elif label.startswith( 'Hide ' + suffix ):
	    if not flag:
	      item.SetItemLabel( label.replace( 'Hide', 'Show' ) )
	#end for
      #end for
  #end _UpdateVisibilityMenuItems


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GetBitmap()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetBitmap( name ):
    """Lazily creates and caches.
"""
    if name in Widget.bitmaps_:
      bmap = Widget.bitmaps_[ name ]
    else:
      image_path = os.path.join( Config.GetResDir(), name + '.png' )
      if os.path.exists( image_path ):
        bmap = wx.Image( image_path, wx.BITMAP_TYPE_PNG ).ConvertToBitmap()
      else:
        bmap = wx.EmptyBitmap( 16, 16 )
      Widget.bitmaps_[ name ] = bmap

    return  bmap
  #end GetBitmap


  #----------------------------------------------------------------------
  #	METHOD:		GetColor()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColor( value, max_value, alpha = 255 ):
    """Calls GetColorTuple().
"""
    return  wx.Colour( *Widget.GetColorTuple( value, max_value, alpha ) )
  #end GetColor


  #----------------------------------------------------------------------
  #	METHOD:		GetColorLuminance()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColorLuminance( r, g, b ):
    value = \
        0.2126 * (r / 255.0) + \
	0.7151 * (g / 255.0) + \
	0.0721 * (b / 255.0)
    return  value
  #end GetColorLuminance


  #----------------------------------------------------------------------
  #	METHOD:		GetColorTuple()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetColorTuple( value, max_value, alpha = 255, debug = False ):
    """
http://www.particleincell.com/blog/2014/colormap/
@return			( red, green, blue, alpha )
"""
    if debug:
      print >> sys.stderr, \
      '[Widget.GetColorTuple] value=%f, max_value=%f' % \
      ( value, max_value )

    f = float( value ) / max_value  if max_value != 0.0  else 0.0
    a = (1.0 - f) / 0.25
    x = int( math.floor( a ) )
    y = int( math.floor( 255 * (a - x) ) )

    if x == 0:
      red = 255
      green = y
      blue = 0

    elif x == 1:
      red = 255 - y
      green = 255
      blue = 0

    elif x == 2:
      red = 0
      green = 255
      blue = y

    elif x == 3:
      red = 0
      green = 255 - y
      blue = 200

    else:
      red = 0
      green = 0
      blue = 100

    if debug:
      print >> sys.stderr, \
      '[Widget.GetColorTuple] f=%f, a=%f, x=%f, y=%f, rgb=(%d,%d,%d)' % \
      ( f, a, x, y, red, green, blue )

    return  ( red, green, blue, alpha )
  #end GetColorTuple


  #----------------------------------------------------------------------
  #	METHOD:		GetContrastColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetContrastColor( r, g, b, alpha = 255 ):
    if Widget.GetColorLuminance( r, g, b ) < 0.5:
      color = ( 255, 255, 255, alpha )
    else:
      color = ( 0, 0, 0, alpha )
    return  color
  #end GetContrastColor


  #----------------------------------------------------------------------
  #	METHOD:		GetContrastRedColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetContrastRedColor( r, g, b, alpha = 255 ):
    if Widget.GetColorLuminance( r, g, b ) < 0.5:
      color = ( 255, 0, 0, alpha )
    else:
      color = ( 100, 0, 0, alpha )
    return  color
  #end GetContrastRedColor


  #----------------------------------------------------------------------
  #	METHOD:		GetDarkerColor()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetDarkerColor( tuple_in, alpha = 255 ):
    """Adjusts each component by a factor of .5.
"""
    result = ( tuple_in[ 0 ] >> 1, tuple_in[ 1 ] >> 1, tuple_in[ 2 ] >> 1, alpha )
    return  result
  #end GetDarkerColor


  #----------------------------------------------------------------------
  #	METHOD:		InvertColor()					-
  #----------------------------------------------------------------------
  @staticmethod
  def InvertColor( color ):
    result = wx.Colour(
        *Widget.InvertColorTuple( color.Red(), color.Green(), color.Blue() )
	)
    return  result
  #end InvertColor


  #----------------------------------------------------------------------
  #	METHOD:		InvertColorTuple()				-
  #----------------------------------------------------------------------
  @staticmethod
  def InvertColorTuple( r, g, b ):
    return  ( 255 - r, 255 - g, 255 - b )
  #end InvertColorTuple
#end Widget
