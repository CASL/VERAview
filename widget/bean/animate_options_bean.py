#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		animate_options_bean.py				-
#	HISTORY:							-
#		2018-10-02	leerw@ornl.gov				-
#		2018-10-01	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )


DEFAULT_frameDelay = 0.1

DEFAULT_showSelections = True


#------------------------------------------------------------------------
#	CLASS:		AnimateOptionsBean				-
#------------------------------------------------------------------------
class AnimateOptionsBean( wx.Panel ):
  """Panel with inputs for showing selections and setting the delay speed.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__(
      self, container, id = -1,
      frame_delay = DEFAULT_frameDelay,
      show_selections = DEFAULT_showSelections
      ):
    """
"""
    super( AnimateOptionsBean, self ).\
        __init__( container, id, style = wx.BORDER_THEME )

    self._delay_fmt = '{0:.2f}'
    self._values = dict(
	frame_delay = frame_delay,
	show_selections = show_selections
        )

    self._frame_delay_field = \
    self._show_selections_ctrl = None

    #self._InitUI( frame_delay, show_selections )
    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( AnimateOptionsBean, self ).Enable( flag )

    self._frame_delay_field.Enable( flag )
    self._show_selections_ctrl.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.GetFrameDelay()		-
  #----------------------------------------------------------------------
  def GetFrameDelay( self ):
    """
"""
    return  self._values.get( 'frame_delay', DEFAULT_frameDelay )
#  #end GetFrameDelay


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.GetShowSelections()		-
  #----------------------------------------------------------------------
  def GetShowSelections( self ):
    return  self._values.get( 'show_selections', DEFAULT_showSelections )
  #end GetShowSelections


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this panel.
"""
#		-- Panel
#		--
    sizer = wx.FlexGridSizer( 2, 2, 6, 4 )  # rows, cols, vgap, hgap
    sizer.SetFlexibleDirection( wx.HORIZONTAL )
    self.SetSizer( sizer )

#		-- Frame delay
#		--
    value_str = self._delay_fmt.format( self.GetFrameDelay() )
    self._frame_delay_field = wx.TextCtrl( self, wx.ID_ANY, value = value_str )
    self._frame_delay_field.Bind( wx.EVT_KILL_FOCUS, self._OnFocusOut )
    self._frame_delay_field.Bind( wx.EVT_SET_FOCUS, self._OnFocusIn )

    sizer.Add(
        wx.StaticText(
	    self, wx.ID_ANY, label = 'Frame Delay (s):',
	    style = wx.ALIGN_RIGHT
	    ),
	0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0
        )
    sizer.Add(
        self._frame_delay_field, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)

#		-- Show selections
#		--
    self._show_selections_ctrl = wx.CheckBox( self, wx.ID_ANY )
    self._show_selections_ctrl.SetValue( self.GetShowSelections() )
    self._show_selections_ctrl.Bind( wx.EVT_CHECKBOX, self._OnCheck )

    sizer.Add(
        wx.StaticText(
	    self, wx.ID_ANY, label = 'Show Selections:',
	    style = wx.ALIGN_RIGHT
	    ),
	0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0
        )
    sizer.Add(
        self._show_selections_ctrl, 0,
	wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0
	)
    #sizer.AddStretchSpacer()

    self.Fit()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean._OnCheck()			-
  #----------------------------------------------------------------------
  def _OnCheck( self, ev ):
    """
"""
    self._values[ 'show_selections' ] = ev.IsChecked()
  #end _OnCheck


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean._OnFocusIn()			-
  #----------------------------------------------------------------------
  def _OnFocusIn( self, ev ):
    """
"""
    ev.Skip()
    obj = ev.GetEventObject()
    obj.SelectAll()
  #end _OnFocusIn


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean._OnFocusOut()		-
  #----------------------------------------------------------------------
  def _OnFocusOut( self, ev ):
    """
"""
    ev.Skip()
    value = DEFAULT_frameDelay
    value_str = self._frame_delay_field.GetValue()
    try:
      value = float( value_str )
    except:
      self._frame_delay_field.SetValue( self._delay_fmt.format( value ) )

    self._values[ 'frame_delay' ] = value
  #end _OnFocusOut


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.SetFrameDelay()		-
  #----------------------------------------------------------------------
  def SetFrameDelay( self, value ):
    """
    Args:
        value (float): frame delay in seconds
"""
    self._values[ 'frame_delay' ] = value

    value_str = self._delay_fmt.format( value )
    self._frame_delay_field.SetValue( value_str )
    self._frame_delay_field.Update()
  #end SetFrameDelay


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsBean.SetShowSelections()		-
  #----------------------------------------------------------------------
  def SetShowSelections( self, value ):
    """
    Args:
        value (bool): show toggle value
"""
    self._values[ 'show_selections' ] = value
    self._show_selections_ctrl.SetValue( value )
    self._show_selections_ctrl.Update()
  #end SetShowSelections


#		-- Properties
#		--

  frame_delay = property( GetFrameDelay, SetFrameDelay )

  show_selections = property( GetShowSelections, SetShowSelections )

#end AnimateOptionsBean


#------------------------------------------------------------------------
#	CLASS:		AnimateOptionsDialog				-
#------------------------------------------------------------------------
class AnimateOptionsDialog( wx.Dialog ):
  """
"""


#		-- Class Attributes
#		--

  last_frame_delay_ = DEFAULT_frameDelay
  last_show_selections_ = DEFAULT_showSelections


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
    Args:
#        **kwargs: keyword arguments
#	    frame_delay (float), frame delay in seconds
#	    show_selections (bool), show selections
"""
#    if 'frame_delay' in kwargs:
#      frame_delay = kwargs[ 'frame_delay' ]
#      del kwargs[ 'frame_delay' ]
#    else:
#      frame_delay = DEFAULT_frameDelay
#
#    if 'show_selections' in kwargs:
#      show_selections = kwargs[ 'show_selections' ]
#      del kwargs[ 'show_selections' ]
#    else:
#      show_selections = DEFAULT_showSelections

    super( AnimateOptionsDialog, self ).__init__( *args, **kwargs )

    self._bean = None
    self._values = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    self._bean = AnimateOptionsBean( self, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    ok_button = wx.Button( self, label = '&OK' )
    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
    cancel_button = wx.Button( self, label = 'Cancel' )
    cancel_button.Bind( wx.EVT_BUTTON, self._OnButton )

    button_sizer.AddStretchSpacer()
    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddSpacer( 10 )
    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )

    sizer.Add(
	self._bean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetSizer( sizer )
    self.SetTitle( 'Animation Options' )
    self.Fit()
    #self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    if obj.GetLabel() == 'Cancel':
      retcode = wx.ID_CANCEL
    else:
      retcode = wx.ID_OK
      self._values = self._bean._values

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsDialog._OnCharHook()		-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self._values = self._bean._values
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		AnimateOptionsDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self, frame_delay = None, show_selections = None ):
    self._bean.frame_delay = \
	frame_delay  if frame_delay is not None else \
        AnimateOptionsDialog.last_frame_delay_
    self._bean.show_selections = \
	show_selections  if show_selections is not None else \
        AnimateOptionsDialog.last_show_selections_

    retcode = super( AnimateOptionsDialog, self ).ShowModal()

    if retcode != wx.ID_CANCEL:
      AnimateOptionsDialog.last_frame_delay_ = self.frame_delay
      AnimateOptionsDialog.last_show_selections_ = self.show_selections

    return  retcode
  #end ShowModal


#		-- Property Definitions
#		--

  bean = property( lambda x: x._bean )

  frame_delay = property(
      lambda x: x._values.get( 'frame_delay', DEFAULT_frameDelay )
      )

  show_selections = property(
      lambda x: x._values.get( 'show_selections', DEFAULT_showSelections )
      )

#end AnimateOptionsDialog
