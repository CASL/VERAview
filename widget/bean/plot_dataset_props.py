#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		plot_dataset_props.py				-
#	HISTORY:							-
#		2017-07-21	leerw@ornl.gov				-
#	  Fixing _OnCharHook for Linux.
#		2017-03-31	leerw@ornl.gov				-
#	  Added EVT_CHAR_HOOK.
#		2017-03-24	leerw@ornl.gov				-
#	  Explicit assign of each dataset to an axis.
#		2016-12-12	leerw@ornl.gov				-
#	  Updated with DataSetName keys.
#		2016-05-27	leerw@ornl.gov				-
#	  Accomodate left/right axis pairs as well as bottom/top.
#	  Enforcing axis selections.
#		2016-05-19	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys
import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.agw.ultimatelistctrl as ulc
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.datamodel import DataSetName


#------------------------------------------------------------------------
#	CLASS:		PlotDataSetPropsBean				-
#------------------------------------------------------------------------
class PlotDataSetPropsBean( ulc.UltimateListCtrl ):
  """List containing columns for the dataset name, top axis check,
bottom axis check, and scale value text control.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__(
      self, container,
      wid = -1, ds_props = None,
      axis1 = 'Bottom',
      axis2 = 'Top'
      ):
    super( PlotDataSetPropsBean, self ).__init__(
        container, wid,
	agwStyle = wx.LC_REPORT | wx.LC_VRULES | wx.LC_SINGLE_SEL |
	    ulc.ULC_HAS_VARIABLE_ROW_HEIGHT
	)

    self.fAxis1 = axis1
    self.fAxis2 = axis2

    #wx.LIST_AUTOSIZE only works the first time
    #wx.LIST_AUTOSIZE_FILL(-3)
    self.InsertColumn( 0, 'Dataset', width = 200 )
    self.InsertColumn( 1, axis1 + ' Axis' )
    self.InsertColumn( 2, axis2 + ' Axis' )
    self.InsertColumn( 3, 'Scale', width = 128 )

    self.fEvenColor = wx.Colour( 240, 240, 255 )
    self.fOddColor = wx.Colour( 240, 255, 240 )

    if ds_props and isinstance( ds_props, dict ):
      self.SetValue( ds_props )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean.GetProps()			-
  #----------------------------------------------------------------------
  def GetProps( self ):
    """Builds the dictionary of dataset properties from current control
values.
@return			dict of dataset properties keyed by name with keys:
			  axis:  axis name or ''
			  scale:  scale value
"""
    no_axis_names = []
    have_axes = [ False, False ]
    props = {}
    for row in range( self.GetItemCount() ):
      name = self.GetItem( row, 0 ).GetText()

      if self.GetItemWindow( row, 1 ).GetValue():
        axis = self.fAxis1.lower()
	have_axes[ 0 ] = True
      elif self.GetItemWindow( row, 2 ).GetValue():
        axis = self.fAxis2.lower()
	have_axes[ 1 ] = True
      else:
        axis = ''
	no_axis_names.append( name )

      scale_str = self.GetItemWindow( row, 3 ).GetValue()
      try:
        scale = float( scale_str )
      except ValueError:
        scale = 1.0

      props[ DataSetName( name ) ] = dict( axis = axis, scale = scale )
      #props[ name ] = { 'axis': axis, 'scale': scale }
    #end for

    if not have_axes[ 0 ] and len( no_axis_names ) > 0:
      props[ DataSetName( no_axis_names[ 0 ] ) ][ 'axis' ] = self.fAxis1.lower()
      del no_axis_names[ 0 ]
    if not have_axes[ 1 ] and len( no_axis_names ) > 0:
      props[ DataSetName( no_axis_names[ 0 ] ) ][ 'axis' ] = self.fAxis2.lower()

    return  props
  #end GetProps


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean._OnCheck()			-
  #----------------------------------------------------------------------
  def _OnCheck( self, row, col, ev ):
    """
"""
    if ev.IsChecked():
      other_axis_col = 1 if col == 2 else 2
      self.GetItemWindow( row, other_axis_col ).SetValue( False )

#      for i in range( self.GetItemCount() ):
#        if i != row:
#	  self.GetItemWindow( i, col ).SetValue( False )
      #end for
    #end if
  #end _OnCheck


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean._OnFocusKill()		-
  #----------------------------------------------------------------------
  def _OnFocusKill( self, ev ):
    """
"""
    ev.Skip()
    edit = ev.GetEventObject()
    try:
      scale = float( edit.GetValue() )
    except ValueError:
      edit.SetValue( '1.0' )
  #end _OnFocusKill


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean._OnFocusSet()		-
  #----------------------------------------------------------------------
  def _OnFocusSet( self, ev ):
    """
"""
    ev.Skip()
    edit = ev.GetEventObject()
    edit.SelectAll()
  #end _OnFocusSet


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean.SetProps()			-
  #----------------------------------------------------------------------
  def SetProps( self, props_in ):
    """
@param  props_in	dict of dataset properties keyed by name with keys:
			  axis:  axis name or ''
			  scale:  scale factor
"""
    if props_in:
      self._UpdateControls( props_in )
    #end if
  #end SetProps


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsBean._UpdateControls()		-
  #----------------------------------------------------------------------
  def _UpdateControls( self, props ):
    """
"""
    self.DeleteAllItems()

    if props:
      ndx = 0
      for qds_name, rec in sorted( props.iteritems() ):
	name = qds_name.name
        self.InsertStringItem( ndx, name )

#			-- First Axis
	check = wx.CheckBox( self, wx.ID_ANY )
	check.SetValue( rec[ 'axis' ] == self.fAxis1.lower() )
	check.Bind(
	    wx.EVT_CHECKBOX,
	    functools.partial( self._OnCheck, ndx, 1 )
	    )
	self.SetItemWindow( ndx, 1, check, expand = True )

#			-- Second Axis
	check = wx.CheckBox( self, wx.ID_ANY )
	check.SetValue( rec[ 'axis' ] == self.fAxis2.lower() )
	check.Bind(
	    wx.EVT_CHECKBOX,
	    functools.partial( self._OnCheck, ndx, 2 )
	    )
	self.SetItemWindow( ndx, 2, check, expand = True )

#			-- Scale
	value_str = '%.6g' % rec.get( 'scale', 1.0 )
	edit = wx.TextCtrl( self, wx.ID_ANY, value = value_str )
	edit.Bind( wx.EVT_KILL_FOCUS, self._OnFocusKill )
	edit.Bind( wx.EVT_SET_FOCUS, self._OnFocusSet )
	self.SetItemWindow( ndx, 3, edit, expand = True )

	self.SetItemBackgroundColour(
	    ndx,
	    self.fEvenColor if ndx % 2 == 0 else self.fOddColor
	    )

        ndx += 1
      #end for
    #end if
  #end _UpdateControls


#------------------------------------------------------------------------
#	CLASS:		PlotDataSetPropsDialog				-
#------------------------------------------------------------------------
class PlotDataSetPropsDialog( wx.Dialog ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialog.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
"""
    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    if 'axis1' in kwargs:
      axis1 = kwargs[ 'axis1' ]
      del kwargs[ 'axis1' ]
    else:
      axis1 = 'Bottom'
    if 'axis2' in kwargs:
      axis2 = kwargs[ 'axis2' ]
      del kwargs[ 'axis2' ]
    else:
      axis2 = 'Top'

    super( PlotDataSetPropsDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    self.fProps = None

    self._InitUI( axis1, axis2 )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialog.GetProps()		-
  #----------------------------------------------------------------------
  def GetProps( self ):
    return  self.fProps
  #end GetProps


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialog._InitUI()		-
  #----------------------------------------------------------------------
  def _InitUI( self, axis1, axis2  ):
    self.fBean = PlotDataSetPropsBean( self, -1, axis1 = axis1, axis2 = axis2 )

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
    self.SetSizer( sizer )

    sizer.Add(
	self.fBean, 1,
	wx.ALL | wx.EXPAND | wx.ALIGN_LEFT | wx.ALIGN_TOP,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )

    self.Bind( wx.EVT_CHAR_HOOK, self._OnCharHook )

    self.SetSize( wx.Size( 640, 400 ) )
    self.SetTitle( 'DataSet Plot Properties' )
    #sizer.Layout()
    #self.Fit()
    #self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()

    if obj.GetLabel() == 'Cancel':
      retcode = 0
    else:
      retcode = 1
      self.fProps = self.fBean.GetProps()

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataRangeDialog._OnCharHook()			-
  #----------------------------------------------------------------------
  def _OnCharHook( self, ev ):
    code = ev.GetKeyCode()
    if code == wx.WXK_RETURN:
      self.fProps = self.fBean.GetProps()
      self.EndModal( wx.ID_OK )
    elif code == wx.WXK_ESCAPE:
      self.EndModal( wx.ID_CANCEL )
    else:
      ev.DoAllowNextEvent()

    ev.Skip()
  #end _OnCharHook


  #----------------------------------------------------------------------
  #	METHOD:		PlotDataSetPropsDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self, ds_props ):
    self.fProps = {}

    self.fBean.SetProps( ds_props if ds_props else {} )
    super( PlotDataSetPropsDialog, self ).ShowModal()
  #end ShowModal

#end PlotDataSetPropsDialog
