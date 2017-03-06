#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		dataset_creator.py				-
#	HISTORY:							-
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2015-11-14	leerw@ornl.gov				-
#		2015-11-13	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, logging, json, math, os, sys, time, traceback
import numpy as np
#import pdb  #pdb.set_trace()

try:
#  import wx, wx.lib.newevent
  import wx
  import wx.lib.delayedresult as wxlibdr
#  from wx.lib.scrolledpanel import ScrolledPanel
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )

from data.averager import *
from data.datamodel import *


#------------------------------------------------------------------------
#	CLASS:		DataSetCreator					-
# 3d assy (1, 1, nax, nass)
# 2d pin (npiny, npinx, 1, nass)
# 2d assy (1, 1, 1, nass)
# 1d (1, 1, nax, nass)
#------------------------------------------------------------------------
class DataSetCreator( object ):
  """Task manager.
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreator.__init__()			-
  #----------------------------------------------------------------------
  def __init__(
      self, data_model, src_ds_name, avg_ds_name, avg_shape,
      factors = None, weights = None
      ):
    """Starts average calculation for each state point in data_model
@param  data_model	DataModel with source dataset
@param  src_ds_name	source dataset name
@param  avg_ds_name	unqualified average dataset name
@param  avg_shape	tuple defining the shape of the resulting datasets,
			with a 1 for the axes over which averages will be
			computed
@param  factors		optional factors (numpy.ndarray) to apply, must have
			the same shape as the source dataset
@param  weights		optional weights (numpy.ndarray) to apply, must have
			the same shape as the source dataset
"""
    self.fDataModel = data_model
    self.fSrcDataSetName = src_ds_name
    self.fAvgDataSetName = avg_ds_name
    self.fAvgShape = avg_shape
    self.fFactors = factors
    self.fWeights = weights

    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info(
          'src_ds_name=%s, avg_ds_name=%s, avg_shape=%s',
	  src_ds_name, avg_ds_name, avg_shape
	  )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreator.Run()				-
  #----------------------------------------------------------------------
  def Run( self ):
    """Launches averages calculation for each state point.
Must be called in the UI thread.
"""
    dialog = wx.ProgressDialog(
        'Calculating Averages', 'Initializing...',
	len( self.fDataModel.GetStates() )
	)
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBegin,
	wargs = [ dialog ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreator._RunBegin()			-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog ):
    """
"""
    status = { 'dialog': dialog }

    try:
      averager = Averager()
      count = 0
      for st in self.fDataModel.GetStates():
        if self.logger.isEnabledFor( logging.INFO ):
          self.logger.info( 'calculating for state point=%d', count )
        wx.CallAfter(
	    dialog.Update,
	    count,
	    'Calculating for state point %3d/%d' % \
	        ( count + 1, len( self.fDataModel.GetStates() ) )
	    )

	avg_data = averager.CalcGeneralAverage(
	    st.GetDataSet( self.fSrcDataSetName ),
	    self.fAvgShape, self.fFactors, self.fWeights
	    )

	#avg_name = self.fSrcDataSetName + '.' + self.fAvgDataSetName
	self.fDataModel.StoreExtraDataSet(
	    ds_name = self.fAvgDataSetName,
	    data = avg_data,
	    src_name = self.fSrcDataSetName,
	    state_ndx = count
	    )

        count += 1
      #end for

    except Exception, ex:
      status[ 'messages' ] = \
          [ 'Error calculating average dataset:' + os.linesep + str( ex ) ]

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreator._RunEnd()			-
  #----------------------------------------------------------------------
  def _RunEnd( self, result ):
    """Called in the UI thread.
"""
    status = result.get()
    if status is not None:
      status[ 'dialog' ].Destroy()

      messages = status.get( 'messages' )
      if messages is not None and len( messages ) > 0:
        msg = \
	    'Averages not calculated:' + os.linesep + \
	    os.linesep.join( messages )
        wx.MessageBox( msg, 'Calculating Averages', wx.ICON_ERROR | wx.OK_DEFAULT )
        #wx.MessageDialog( self, msg, 'Calculating Averages' ).ShowWindowModal()
      #end if
    #end if
  #end _RunEnd

#end DataSetCreator


#------------------------------------------------------------------------
#	EVENT:		DataSetChoiceEvent, EVT_DATASET_CHOICE		-
#	PROPERTIES:							-
#	  value		same as DataSetChooserBean value property
#------------------------------------------------------------------------
#DataSetChoiceEvent, EVT_DATASET_CHOICE = wx.lib.newevent.NewEvent()


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorBean				-
#------------------------------------------------------------------------
class DataSetCreatorBean( wx.Panel ):
  """Panel with controls for specifying what axes of the dataset over
which to average.
Not being used.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, data_model, ds_name, id = -1 ):
    super( DataSetCreatorBean, self ).__init__( container, id )

    self.fDataModel = data_model
    self.fSrcDataSetName = ds_name

    dset = None
    st = data_model.GetState( 0 )
    if st is not None:
      dset = st.GetDataSet( ds_name )

    self.fShape = dset.shape if dset is not None else ( 0, 0, 0, 0 )

    #extra_names = data_model.GetDataSetNames( 'extra' )
    #self.fExtraNames = [] if extra_names is None else extra_names

    self.fAvgNameField = None
    self.fAxisCheckBoxes = []
    self.fCreateButton = None
    self.fPinFactorsCheckBox = None

    self._InitUI()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean.Enable()			-
  #----------------------------------------------------------------------
  def Enable( self, flag = True ):
    super( DataSetCreatorBean, self ).Enable( flag )

    self.fCreateButton.Enable( flag )
    for cb in self.fAxisCheckBoxes:
      cb.Enable( flag )
  #end Enable


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """
"""
    #axis_names = ( 'npiny', 'npinx', 'nax', 'nass' )
    axis_names_rev = ( 'nass', 'nax', 'npinx', 'npiny' )
    shape_rev = self.fShape[ ::-1 ]

#		-- Create names panel
#		--
    names_panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    names_sizer = wx.FlexGridSizer( 3, 2, 6, 4 )
    names_panel.SetSizer( names_sizer )

    self.fAvgNameField = wx.TextCtrl(
        names_panel, -1, 'average',
	size = ( 240, 24 )
	#style = wx.TE_DONTWRAP
	)

    self.fPinFactorsCheckBox = wx.CheckBox( names_panel, -1, '' )
    if self.fDataModel.HasExtraDataSet( 'core.pin_factors' ):
      self.fPinFactorsCheckBox.SetValue( True )
    else:
      self.fPinFactorsCheckBox.Enable( False )
      self.fPinFactorsCheckBox.SetValue( False )

    names_sizer.Add(
	wx.StaticText(
	    names_panel, -1,
	    label = 'Source Dataset:',
	    style = wx.ALIGN_LEFT
	    ),
	0, wx.ALIGN_LEFT | wx.LEFT | wx.TOP, 8
        )
    names_sizer.Add(
	wx.TextCtrl(
	    names_panel, -1, self.fSrcDataSetName,
	    size = ( 40, -1 ),
	    style = wx.ALIGN_LEFT | wx.TE_READONLY
	    ),
	1, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT | wx.TOP, 8
        )
    names_sizer.Add(
	wx.StaticText(
	    names_panel, -1,
	    label = 'New Dataset:',
	    style = wx.ALIGN_LEFT
	    ),
	0, wx.ALIGN_LEFT | wx.LEFT | wx.TOP, 8
        )
    names_sizer.Add(
        self.fAvgNameField,
	1, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT | wx.TOP, 8
	)
    names_sizer.Add(
	wx.StaticText(
	    names_panel, -1,
	    label = 'Use Pin Factors:',
	    style = wx.ALIGN_LEFT
	    ),
	0, wx.ALIGN_LEFT | wx.LEFT | wx.TOP, 8
        )
    names_sizer.Add(
        self.fPinFactorsCheckBox,
	1, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT | wx.TOP, 8
	)

#		-- Create axis panel
#		--
    axis_panel = wx.Panel( self, -1, style = wx.BORDER_THEME )
    axis_sizer = wx.FlexGridSizer( 3, len( shape_rev ), 8, 6 )
    axis_panel.SetSizer( axis_sizer )

    for i in range( len( axis_names_rev ) ):
      axis_sizer.Add(
	  wx.StaticText(
	      axis_panel, -1,
	      label = axis_names_rev[ i ], style = wx.ALIGN_CENTER
	      ),
	  1, wx.EXPAND | wx.TOP, 4
          )
    #end for

    for i in range( len( shape_rev ) ):
      axis_sizer.Add(
	  wx.StaticText(
	      axis_panel, -1,
	      label = str( shape_rev[ i ] ), style = wx.ALIGN_CENTER
	      ),
	  1, wx.EXPAND, 0
          )
    #end for

    for i in range( len( shape_rev ) ):
      #cb = wx.CheckBox( axis_panel, -1, 'xx', style = wx.ALIGN_RIGHT )
      cb = wx.CheckBox( axis_panel, -1, '' )
      self.fAxisCheckBoxes.append( cb )
      #axis_sizer.Add( cb, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT, 6 )
      axis_sizer.Add(
          cb, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, 8
	  )
    #end for

#		-- Buttons
#		--
#		--  BORDER _NONE, _THEME, _SUNKEN, _RAISED, _SIMPLE
    button_panel = wx.Panel( self, -1, style = wx.BORDER_NONE )
    button_sizer = wx.BoxSizer( wx.VERTICAL )
    button_panel.SetSizer( button_sizer )

    self.fCreateButton = wx.Button( button_panel, -1, label = 'C&reate' )
    #create_button.SetToolTipString( 'Create/calculate a dataset' )
    self.fCreateButton.Bind( wx.EVT_BUTTON, self._OnCreate )
    self.fCreateButton.Enable( self.fShape[ 0 ] > 0 )
    #self.fCreateButton.SetForegroundColour( wx.Colour( 0, 0, 255 ) )
    #self.fCreateButton.SetDefault()

    #button_sizer.AddStretchSpacer()
    button_sizer.Add( self.fCreateButton, 0, wx.ALL | wx.EXPAND, 6 )
    #button_sizer.AddSpacer( 8 )
    button_sizer.AddStretchSpacer()

#		-- Lay Out
#		--
    middle_sizer = wx.BoxSizer( wx.HORIZONTAL )
    middle_sizer.Add( axis_panel, 0, wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 0 )
    middle_sizer.AddStretchSpacer()
    middle_sizer.Add( button_panel, 0, wx.ALIGN_LEFT | wx.ALL, 0 )

    sizer = wx.BoxSizer( wx.VERTICAL )
    self.SetSizer( sizer )

    sizer.Add( names_panel, 0, wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 )
    sizer.Add( middle_sizer, 0, wx.ALIGN_LEFT | wx.ALL | wx.EXPAND, 4 )
    sizer.AddStretchSpacer()

    self.Fit()
    #self.Layout()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorBean._OnCreate()			-
  #----------------------------------------------------------------------
  def _OnCreate( self, ev ):
    """
Called on the UI thread.
"""
    ev.Skip()

    shape_rev = self.fShape[ ::-1 ]
    avg_shape = []

    have_one = False
    for i in range( len( shape_rev ) ):
      val = 1 if self.fAxisCheckBoxes[ i ].GetValue() else shape_rev[ i ]
      avg_shape.insert( 0, val )
      have_one |= val == 1
    #end for

    if not have_one:
      wx.MessageBox(
	  'You must select at least one axis over which to calculate averages',
	  'Create Average Dataset',
	  wx.OK_DEFAULT | wx.ICON_EXCLAMATION
          )

    else:
      #avg_name = self.fAvgNameField.GetValue()
      avg_name = self.fAvgNameField.GetValue().replace( ' ', '_' ).lower()
      if len( avg_name ) == 0:
        avg_name = 'average'

      factors = None
      if self.fPinFactorsCheckBox.GetValue():
        factors = self.fDataModel.LoadExtraDataSet( 'pin_factors' )

      creator = DataSetCreator(
          self.fDataModel, self.fSrcDataSetName,
	  avg_name, avg_shape, factors
	  )
      creator.Run()
    #end if-else
  #end _OnCreate

#end DataSetCreatorBean


#------------------------------------------------------------------------
#	CLASS:		DataSetCreatorDialog				-
#------------------------------------------------------------------------
class DataSetCreatorDialog( wx.Dialog ):
  """
Properties:
  bean			DataSetCreatorBean reference
Not being used.
"""


#		-- Properties
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	DataSetCreatorDialog.bean			-
  #----------------------------------------------------------------------
  @property
  def bean( self ):
    """reference to bean, read-only"""
    return  self.fBean
  #end bean.getter


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
Must pass the 'data_model' parameter.
	'data_model'
	'ds_name'
"""
#		-- Assert
#		--
    if 'data_model' not in kwargs or 'ds_name' not in kwargs:
      raise  Exception( 'data_model and ds_name arguments required' )

    data_model = kwargs.get( 'data_model' )
    del kwargs[ 'data_model' ]

    ds_name = kwargs.get( 'ds_name' )
    del kwargs[ 'ds_name' ]

    style = kwargs.get( 'style', wx.DEFAULT_DIALOG_STYLE )
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( DataSetCreatorDialog, self ).__init__( *args, **kwargs )

    self.fBean = None
    #self.fResult = None

    self._InitUI( data_model, ds_name )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog.GetResult()		-
  #----------------------------------------------------------------------
#  def GetResult( self ):
#    return  self.fResult
#  #end GetResult


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, data_model, ds_name ):
    self.fBean = DataSetCreatorBean( self, data_model, ds_name, -1 )

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )

#    ok_button = wx.Button( self, label = '&OK' )
#    ok_button.Bind( wx.EVT_BUTTON, self._OnButton )
#    cancel_button = wx.Button( self, label = 'Cancel' )
#    cancel_button.Bind( wx.EVT_BUTTON, self._OnButton )

#    button_sizer.AddStretchSpacer()
#    button_sizer.Add( ok_button, 0, wx.ALL | wx.EXPAND, 6 );
#    button_sizer.AddSpacer( 10 )
#    button_sizer.Add( cancel_button, 0, wx.ALL | wx.EXPAND, 6 );
#    button_sizer.AddStretchSpacer()

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

    self.SetSizer( sizer )
    self.SetTitle( 'Average Dataset Creator' )
    self.Fit()
    self.Center()
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog._OnButton()		-
  #----------------------------------------------------------------------
  def _OnButton( self, ev ):
    ev.Skip()

#	-- ** EndModel() not passing result to caller via ShowModal() **
    obj = ev.GetEventObject()
    retcode = 0 if obj.GetLabel() == 'Cancel' else  1

    self.EndModal( retcode )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		DataSetCreatorDialog.ShowModal()		-
  #----------------------------------------------------------------------
  def ShowModal( self ):
    #self.fResult = None
    super( DataSetCreatorDialog, self ).ShowModal()
  #end ShowModal

#end DataSetCreatorDialog