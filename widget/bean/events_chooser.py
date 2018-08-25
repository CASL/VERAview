#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		events_chooser.py				-
#	HISTORY:							-
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-03-31	leerw@ornl.gov				-
#	  Added EVT_CHAR_HOOK.
#		2016-08-15	leerw@ornl.gov				-
#	  New State and event names.
#		2016-06-27	leerw@ornl.gov				-
#	  Moved EVENT_ID_NAMES to event/state.py.
#		2015-05-28	leerw@ornl.gov				-
#	  Added scrolled panel.
#		2015-05-12	leerw@ornl.gov				-
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

from event.state import *


#------------------------------------------------------------------------
#	EVENT:		EventsChoiceEvent, EVT_EVENTS_CHOICE		-
#	PROPERTIES:							-
#	  value		same as EventsChooserBean value property
#------------------------------------------------------------------------
#EventsChoiceEvent, EVT_EVENTS_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		EventsChooserBean				-
#------------------------------------------------------------------------
class EventsChooserBean( wx.Panel ):
  """Panel containing a list of checkboxes.

Attributes/properties:
  events		dict keyed by state change IDs of True/False values
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	EventsChooserBean.events			-
  #----------------------------------------------------------------------
  @property
  def events( self ):
    """@return		new dict"""
    ev = {}
    for k in self.fEventControls:
      ev[ k ] = self.fEventControls[ k ].IsChecked()
    return  ev
  #end events.getter


#  @events.deleter
#  def value( self ):
#    pass
#  #end events.deleter


  @events.setter
  def events( self, value_in ):
    """@param  value_in	dict from which to copy"""
    if value_in is not None:
      for k in self.fEventControls:
        self.fEventControls[ k ].SetValue( value_in.get( k, False ) )
    #end if
  #end events.setter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, event_set = set() ):
    """
@param  events_in	dict by id of True/False event status
"""
    super( EventsChooserBean, self ).__init__( container, id )

    #self.fEvents = events

    self.fButtonPanel = None
    self.fEventControls = {}

    self._InitUI( event_set )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( EventsChooserBean, self ).Enable( flag )

    for panel in ( self.fButtonPanel, self.fTablePanel ):
      if panel is not None:
        for child in panel.GetChildren():
          if isinstance( child, wx.Window ):
	    child.Enable( flag )
        #end for
      #end if panel exists
    #end for panels

    #self._UpdateControls()
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, event_set ):
    """Builds this UI component frame with everything but the items for
manipulating Events.  That is done with _CreateEventsUI().
"""
    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    for ev_id, ev_name in LOCKABLE_STATES:
      if ev_id in event_set:
        cbox = wx.CheckBox( self, -1, label = ev_name )
#        cbox.Bind(
#            wx.EVT_CHECKBOX,
#	    functools.partial( self._OnCheckBox, ev_id )
#	    )
        sizer.Add( cbox, 0, wx.ALL | wx.ALIGN_LEFT | wx.ALL, 2 )

        self.fEventControls[ ev_id ] = cbox
      #end if ev_id in event_set
    #end for

    self.Fit()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserBean._OnCheckBox()			-
  #----------------------------------------------------------------------
#  def _OnCheckBox( self, ev_id, ev ):
#    """Handles events from checkboxes.  Called on the UI thread.
#"""
#    ev.Skip()
#
#    self.fEvents[ ev_id ] = ev.IsChecked()
#  #end _OnCheckBox
#end EventsChooserBean


#------------------------------------------------------------------------
#	CLASS:		EventsChooserDialog				-
#------------------------------------------------------------------------
class EventsChooserDialog( wx.Dialog ):
  """
Properties:
  bean			EventsChooserBean reference
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	EventsChooserDialog.bean			-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


  #----------------------------------------------------------------------
  #	PROPERTY:	EventsChooserDialog.result			-
  #----------------------------------------------------------------------
  @property
  def result( self ):
    """bean value, read-only"""
    return  self.fResult
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'event_set' parameter.
"""
    if 'event_set' in kwargs:
      event_set = kwargs[ 'event_set' ]
      del kwargs[ 'event_set' ]
    else:
      event_set = set()

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( EventsChooserDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fResult = None

    self._InitUI( event_set )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog.GetResult()			-
  #----------------------------------------------------------------------
  def GetResult( self ):
    return  self.fResult
  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, event_set ):
    self.fBean = EventsChooserBean( self, -1, event_set )

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
	self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetSizer( sizer )
    self.SetTitle( 'Events Chooser' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    if obj.GetLabel() != 'Cancel':
      self.fResult = self.fBean.events

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog._OnCharHook()		-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.fResult = self.fBean.events
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		EventsChooserDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self, events = None ):
    self.fResult = None
    if events is not None:
      self.fBean.events = events
    super( EventsChooserDialog, self ).ShowModal()
  #end ShowModal

#end EventsChooserDialog
