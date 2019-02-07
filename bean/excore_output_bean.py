#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		excore_output_bean.py				-
#	HISTORY:							-
#		2018-03-02	leerw@ornl.gov				-
#	  Renamed FluenceSynthesizer to ExcoreCreator.
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-07-07	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import numpy as np
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.excore_creator import *
#from data.fluence_synth import *


#------------------------------------------------------------------------
#	CLASS:		ExcoreOutputBean				-
#------------------------------------------------------------------------
class ExcoreOutputBean( wx.Panel ):
  """Panel with controls for selecting MPACT and Shift files, specifying
the output file, and executing an ExcoreCreator instance.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, parent, state, id = -1 ):
    super( ExcoreOutputBean, self ).__init__( parent, id )

    self.fButtonPanel = None
    self.fCreateButton = None

    self.fMpactButton = None
    self.fMpactField = None

    self.fOutputButton = None
    self.fOutputField = None

    self.fProgressField = None
    self.fProgressGauge = None

    self.fShiftButton = None
    self.fShiftField = None

    self.fWorkerIsCanceled = False

    self._InitUI()
    #self._UpdateControls()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean._CreateTaskBegin()		-
  #----------------------------------------------------------------------
  def _CreateTaskBegin( self, mpact_path, shift_path, output_path ):
    try:
      obj = ExcoreCreator()
      obj( mpact_path, shift_path, output_path )
      result = output_path
    except Exception, ex:
      result = ex
    return  result
  #end _CreateTaskBegin


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean._CreateTaskEnd()		-
  #----------------------------------------------------------------------
  def _CreateTaskEnd( self, result ):
    error_message = None
    output_name = ''

    try:
      if result is None:
        error_message = 'File creation failed!'
      else:
	result_obj = result.get()
        if isinstance( result_obj, Exception ):
          error_message = 'File creation failed:\n' + str( result_obj )
        else:
	  output_name = str( result_obj )

    except Exception, ex:
      error_message = 'File creation failed:\n' + str( ex )

    finally:
      self.fCreateButton.Enable()
      self.fProgressGauge.Hide()
      self.fProgressGauge.SetValue( 0 )
      if output_name:
        self.fProgressField.SetLabel( 'Created {0:s}'.format( output_name ) )
      else:
        self.fProgressField.SetLabel( '' )
      self.Layout()

    if error_message:
      wx.MessageDialog( self, error_message, 'Create Excore File' ).\
          ShowWindowModal()
  #end _CreateTaskEnd


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( ExcoreOutputBean, self ).Enable( flag )

    for obj in (
        self.fCreateButton, self.fMpactButton,
	self.fOutputButton, self.fShiftButton
	):
      if obj is not None:
        obj.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    name_ht = 28
    name_wd = 320

    grid_wrapper = wx.Panel( self, -1, style = wx.BORDER_THEME )
    gw_sizer = wx.BoxSizer( wx.HORIZONTAL )
    grid_wrapper.SetSizer( gw_sizer )

    grid_panel = wx.Panel( grid_wrapper, -1 )
    self.fGridSizer = \
    grid_sizer = wx.FlexGridSizer( cols = 3, vgap = 10, hgap = 8 )
    grid_panel.SetSizer( grid_sizer )

#		-- MPACT panel
#		--
    self.fMpactField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd, name_ht )
        )
    self.fMpactField.SetEditable( False )

    self.fMpactButton = wx.Button( grid_panel, -1, label = 'Browse...' )
    self.fMpactButton.Bind(
	wx.EVT_BUTTON,
	functools.partial(
	    self._OnBrowse, self.fMpactField,
	    'Select MPACT File',
	    wx.FD_FILE_MUST_EXIST | wx.FD_OPEN
	    )
        )

    st = wx.StaticText(
        grid_panel, -1, label = 'MPACT File:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fMpactField, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fMpactButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Shift panel
#		--
    self.fShiftField = wx.TextCtrl(
	grid_panel, -1, '',
	size = ( name_wd, name_ht )
        )
    self.fShiftField.SetEditable( False )

    self.fShiftButton = wx.Button( grid_panel, -1, label = 'Browse...' )
    self.fShiftButton.Bind(
	wx.EVT_BUTTON,
	functools.partial(
	    self._OnBrowse, self.fShiftField,
	    'Select Shift File',
	    wx.FD_FILE_MUST_EXIST | wx.FD_OPEN
	    )
        )

    st = wx.StaticText(
        grid_panel, -1, label = 'Shift File:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fShiftField, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fShiftButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Output panel
#		--
    self.fOutputField = wx.TextCtrl(
	grid_panel, -1, 'out.excore.h5',
	size = ( name_wd, name_ht )
        )
    #self.fOutputField.SetEditable( False )

    self.fOutputButton = wx.Button( grid_panel, -1, label = 'Browse...' )
    self.fOutputButton.Bind(
	wx.EVT_BUTTON,
	functools.partial(
	    self._OnBrowse, self.fOutputField,
	    'Choose Output File',
	    wx.FD_OVERWRITE_PROMPT | wx.FD_SAVE
	    )
        )

    st = wx.StaticText(
        grid_panel, -1, label = 'Output File:',
	style = wx.ALIGN_RIGHT
	)
    grid_sizer.Add(
	st, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_RIGHT | wx.TOP, 0
        )
    grid_sizer.Add(
        self.fOutputField, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0
	)
    grid_sizer.Add(
        self.fOutputButton, 0,
	wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 0
	)

#		-- Create row
#		--
    self.fCreateButton = wx.Button( grid_panel, -1, label = 'Create', size = ( -1, 28 ) )
    self.fCreateButton.SetFont( self.fCreateButton.GetFont().Larger() )
    self.fCreateButton.Bind( wx.EVT_BUTTON, self._OnCreate )

    grid_sizer.AddSpacer( 0 )
    grid_sizer.Add( self.fCreateButton, 0, wx.ALIGN_CENTRE | wx.ALL, 0 )
    grid_sizer.AddSpacer( 0 )

#		-- Progress
#		--
    self.fProgressField = \
        wx.StaticText( self, -1, label = '', style = wx.ALIGN_LEFT )
    self.fProgressGauge = wx.Gauge( self, wx.ID_ANY, size = ( 40, 24 ) )
    self.fProgressGauge.SetValue( 0 )

#		-- Lay self out
#		--
    gw_sizer.Add( grid_panel, 0, wx.ALL, 8 )
    gw_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( grid_wrapper, 0, wx.BOTTOM, 10 )
    sizer.Add(
        self.fProgressField, 0,
	wx.ALIGN_LEFT | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT,
	10
	)
    sizer.Add(
        self.fProgressGauge, 0,
	wx.ALIGN_LEFT | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT,
	10
	)
    sizer.AddStretchSpacer()

    self.Fit()

    wx.CallAfter( self.fProgressGauge.Hide )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean._OnBrowse()			-
  #----------------------------------------------------------------------
  def _OnBrowse( self, field, title, fd_style, ev ):
    """
"""
    dialog = wx.FileDialog(
	self, title,
	wildcard = 'HDF5 files (*.h5,*.hdf5)|*.h5;*.hdf5',
	style = fd_style | wx.FD_CHANGE_DIR
        )
    path = None
    if dialog.ShowModal() != wx.ID_CANCEL:
      path = dialog.GetPath()
    dialog.Destroy()

    if path:
      field.SetValue( path )
  #end _OnBrowse


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputBean._OnCreate()			-
  #----------------------------------------------------------------------
  def _OnCreate( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    mpact_path = self.fMpactField.GetValue()
    shift_path = self.fShiftField.GetValue()
    output_path = self.fOutputField.GetValue()

#		-- Check inputs
#		--
    msg = ''
    if len( mpact_path ) == 0:
      msg = 'Please select an MPACT file'
    elif not os.path.exists( mpact_path ):
      msg = 'MPACT file "{0:s}" not found'.format( mpact_path )

    elif len( shift_path ) == 0:
      msg = 'Please select a Shift file'
    elif not os.path.exists( shift_path ):
      msg = 'Shift file "{0:s}" not found'.format( shift_path )

    elif len( output_path ) == 0:
      msg = 'Please specify an output file'

    if msg:
      wx.MessageDialog( self, msg, 'Create Excore Output' ).\
          ShowWindowModal()
    else:
      self.fCreateButton.Disable()
      self.fProgressField.SetLabel(
	  'Creating {0:s} from {1:s} and {2:s}'.\
	  format( output_path, mpact_path, shift_path )
          )
      #self.fProgressGauge.SetValue( 0 )
      self.fProgressGauge.Pulse()
      self.fProgressGauge.Show()

      wargs = [ mpact_path, shift_path, output_path ]
      th = wxlibdr.startWorker(
          self._CreateTaskEnd, self._CreateTaskBegin,
	  wargs = wargs
	  )
    #end if-else msg
  #end _OnCreate

#end ExcoreOutputBean


#------------------------------------------------------------------------
#	CLASS:		ExcoreOutputDialog				-
#------------------------------------------------------------------------
class ExcoreOutputDialog( wx.Dialog ):
  """
Properties:
  bean			ExcoreOutputBean reference
Not being used.
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	ExcoreOutputDialog.bean				-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
"""
#		-- Assert
#		--
    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( ExcoreOutputDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    #self.fResult = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog.GetApp()                     -
  #----------------------------------------------------------------------
  def GetApp( self ):
    """Not sure why this is necessary, but ``wx.App.Get()`` called in
DataModelMenu returns a ``wx.App`` instance, not a ``VeraViewApp`` instance.
"""
    return  wx.App.Get()
  #end GetApp


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog.GetResult()			-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    self.fBean = ExcoreOutputBean( self, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind( wx.EVT_BUTTON, self._OnButton )
    close_button.SetDefault()

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
    self.SetTitle( 'Excore Output Creation' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = wx.ID_CANCEL if obj.GetLabel() == 'Cancel' else  wx.ID_OK

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		GridSizerDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		ExcoreOutputDialog.ShowModal()			-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    return  super( ExcoreOutputDialog, self ).ShowModal()
  #end ShowModal

#end ExcoreOutputDialog
