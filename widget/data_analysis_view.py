#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_analysis.py				-
#	HISTORY:							-
#		2019-01-16	leerw@ornl.gov				-
#         Transition from tally to fluence.
#		2018-10-27	leerw@ornl.gov				-
#		2018-10-23	leerw@ornl.gov				-
#------------------------------------------------------------------------
import hashlib, logging, math, os, six, sys, tempfile, time, traceback
import numpy as np
import pdb  # pdb.set_trace()

try:
  import wx
  #from wx.html2 import WebView
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

from data.config import *
from data.utils import *
from event.state import *

from .bean.plot_dataset_props import *
from .widget import *
from .widgetcontainer import *

if Config.IsLinux():
  from wx.html import HtmlWindow
  WEB_VIEW = False
else:
  from wx.html2 import WebView
  WEB_VIEW = True


AUTO_VISIBLE_DATASETS = \
  [
    'AO', 'axial_offset', 'boron', 'crit_boron',
    'density', 'exposure', 'exposure_efpd',
    'inlet_temperature', 'keff', 'power'
  ]


#------------------------------------------------------------------------
#	CLASS:		DataAnalysisView				-
#------------------------------------------------------------------------
class DataAnalysisView( Widget ):
  """Table widget.
"""

  DATA_HTML = """
<header>
<style type="text/css">
body {{ background-color: #f1f1f1 }}
p.title
  {{
  /*font-size: 12pt;*/
  font-style: italic;
  /*font-weight: bold;*/
  margin-bottom: 0 0 0 0.25em;
  text-decoration: underline;
  }}
table.data
  {{
  border: 1px solid black;
  border-collapse: collapse;
  margin: 0;
  }}
table.data tr
  {{
  border-bottom: 1px solid gray;
  vertical-align: top;
  }}
table.data tr th
  {{
  background-color: #c9c9c9;
  border: 1px solid gray;
  font-weight: normal; /*bold*/
  padding: 0.25em 0.5em 0.25em 0.5em;
  text-align: left;
  }}
table.data tr td
  {{
  /*border: 1px dotted gray;*/
  border-right: 1px dotted gray;
  font-weight: normal;
  padding: 0.1em 0.5em 0.1em 0.5em;
  text-align: left;
  }}
</style>
</header>
<body>
{table}
</body>
"""

  DATA_TABLE = """
<table class="data">
  <theader>{header}
  </theader>
  <tbody>{rows}
  </tbody>
</table>
"""

  DATA_TABLE_HTML_VIEW = """
<table class="data" border="1" cellpadding="4" cellspacing="0">
  <theader>{header}
  </theader>
  <tbody>{rows}
  </tbody>
</table>
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
#    self.auxNodeAddrs = []
#    self.auxSubAddrs = []
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
    self.curDataSet = None
    self.curSize = None

#    self.nodeAddr = -1
#    self.subAddr = ( -1, -1 )
#    self.tallyAddr = DataModel.CreateEmptyTallyAddress()
    self.timeValue = -1.0

#		-- Controls
#		--
    self.headerCtrl = None
    self.webView = None

    super( DataAnalysisView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the from the displayed table.
@return			text or None
"""
    csv_text = ''

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._CreateClipboardImage()	-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return			bitmap or None
"""
    bmap = wx.EmptyBitmapRGBA( 400, 200 )
    return  bmap
  #end _CreateClipboardImage


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.CreatePrintImage()		-
  #----------------------------------------------------------------------
  def CreatePrintImage( self, file_path, bgcolor = None, hilite = False ):
    """
"""
    bmap = self._CreateClipboardImage()
    im = wx.ImageFromBitmap( bmap )

    if im.HasAlpha() and bgcolor and \
        hasattr( bgcolor, '__iter__' ) and len( bgcolor ) >= 4:
      for y in xrange( im.GetHeight() ):
        for x in xrange( im.GetWidth() ):
          pix_value = (
              im.GetRed( x, y ), im.GetGreen( x, y ), im.GetBlue( x, y ),
              im.GetAlpha( x, y )
              )
	  if pix_value == ( 0, 0, 0, 0 ) or pix_value == ( 255, 255, 255, 0 ):
            im.SetRGB( x, y, bgcolor[ 0 ], bgcolor[ 1 ], bgcolor[ 2 ] )
	    im.SetAlpha( x, y, bgcolor[ 3 ] )
    #end if bgcolor

    im.SaveFile( file_path, wx.BITMAP_TYPE_PNG )
    return  file_path
  #end CreatePrintImage


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetAnimationIndexes()		-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:all', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetAxialValue()		-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		AxialValue instance
( cm value, 0-based core index, 0-based detector index
			  0-based fixed_detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetDataSetTypes()		-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      (
      'channel', 'pin', 'subpin_cc',
      #'intrapin_edits', 'tally',
      )
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetEventLockSet()		-
  #----------------------------------------------------------------------
  def GetEventLockSet( self ):
    """By default, all locks are enabled except
"""
    locks = set([
	STATE_CHANGE_axialValue,
	STATE_CHANGE_coordinates,
	STATE_CHANGE_curDataSet,
	STATE_CHANGE_fluenceAddr,
	STATE_CHANGE_timeValue
	])
    return  locks
  #end GetEventLockSet


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetStateIndex()		-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetTimeValue()			-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """@return		0-based state/time index
"""
    return  self.timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetTitle()			-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Data Analysis View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.GetUsesScaleAndCmap()		-
  #----------------------------------------------------------------------
  def GetUsesScaleAndCmap( self ):
    """
    Returns:
        boolean: False
"""
    return  False
  #end GetUsesScaleAndCmap


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self ):
    """Builds this UI component.  Obviously, must be called in the UI thread.
"""
#		-- Header
#		--
    self.headerCtrl = wx.TextCtrl(
        self, wx.ID_ANY,
	style = wx.BORDER_NONE | wx.TE_DONTWRAP | wx.TE_READONLY
	)
    self.headerCtrl.SetBackgroundColour( self.GetBackgroundColour() )

#		-- View
#		--
    if WEB_VIEW:
      self.webView = WebView.New( self )
      self.webView.SetBackgroundColour( self.GetBackgroundColour() )
    else:
      self.webView = HtmlWindow( self )

#		-- Lay Out
#		--
    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
        self.headerCtrl, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND,
	2
	)
    sizer.Add(
        self.webView, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 4
	)
    self.SetAutoLayout( True )
    self.SetSizer( sizer )

#		-- Events
#		--
    self.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    #self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.IsDataSetScaleCapable()	-
  #----------------------------------------------------------------------
#  def IsDataSetScaleCapable( self ):
#    """Returns False
#    Returns:
#        bool: False
#"""
#    return  False
#  #end IsDataSetScaleCapable


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._LoadDataModel()		-
  #----------------------------------------------------------------------
  def _LoadDataModel( self, reason ):
    """Updates the components for the current model.
"""
    if not self.isLoading:
      update_args = self._LoadDataModelValues( reason )
      if 'rebuild' in update_args:
        wx.CallAfter( self.UpdateState, rebuild = True )
  #end _LoadDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """
@return			dict to be passed to UpdateState()
"""
    update_args = {}

    #if self.data is not None and self.data.HasData():
    if self.dmgr.HasData():
      update_args[ 'rebuild' ] = True

      if (reason & STATE_CHANGE_axialValue) > 0:
	update_args[ 'axial_value' ] = self.state.axialValue

      if (reason & STATE_CHANGE_coordinates) > 0:
	update_args[ 'assembly_addr' ] = self.dmgr.\
	    NormalizeAssemblyAddr( self.state.assemblyAddr )

      if (reason & STATE_CHANGE_curDataSet) > 0:
        self.curDataSet = self._FindFirstDataSet( self.state.curDataSet )

      if (reason & STATE_CHANGE_timeDataSet) > 0:
	update_args[ 'time_dataset' ] = self.state.timeDataSet

      if (reason & STATE_CHANGE_timeValue) > 0:
	update_args[ 'time_value' ] = self.state.timeValue
    #end if self.dmgr.HasData()

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.LoadProps()			-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.
@param  props_dict	dict object from which to deserialize properties
"""
    # axialValue, tallyAddr handled in Widget
    for k in ( 'assemblyAddr', 'timeValue' ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    super( DataAnalysisView, self ).LoadProps( props_dict )
    wx.CallAfter( self.UpdateState, rebuild = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._OnContextMenu()		-
  #----------------------------------------------------------------------
  def _OnContextMenu( self, ev ):
    """
"""
    ev_obj = ev.GetEventObject()
    if ev_obj.HasCapture():
      ev_obj.ReleaseMouse()

    pos = ev.GetPosition()
    pos = self.ScreenToClient( pos )

    menu = self.GetPopupMenu()
    self.PopupMenu( menu, pos )
  #end _OnContextMenu


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysis.Redraw()                           -
  #----------------------------------------------------------------------
  def Redraw( self ):
    """
"""
    self.UpdatePage()
  #end Redraw


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.SaveProps()			-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to load properties.  This implementation takes care of
'dataSetSelections' and 'timeValue', but subclasses must override for
all other properties.
@param  props_dict	dict object to which to serialize properties
"""
    super( DataAnalysisView, self ).SaveProps( props_dict, for_drag = for_drag )

    # axialValue, tallyAddr handled in Widget
    for k in ( 'assemblyAddr', 'timeValue' ):
      props_dict[ k ] = getattr( self, k )
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.SetDataSet()			-
  #----------------------------------------------------------------------
  def SetDataSet( self, qds_name ):
    """May be called from any thread.
"""
    if qds_name != self.curDataSet:
      wx.CallAfter( self.UpdateState, cur_dataset = qds_name )
      self.FireStateChange( cur_dataset = qds_name )
  #end SetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.UpdatePage()			-
  #----------------------------------------------------------------------
  def UpdatePage( self ):
    """Must be called from the UI thread.
"""
    html_content = ''

    #assy_ndx = self.assemblyAddr[ 0 ]
    #if assy_ndx >= 0 and self.dmgr.HasData():
    if self.dmgr.HasData():
      dset = self.dmgr.GetH5DataSet( self.curDataSet, self.timeValue )

    if dset is not None:
      core = self.dmgr.GetCore()
      ds_def = self.dmgr.GetDataSetDefByQName( self.curDataSet )
#      assy_axis = ds_def.get( 'assy_axis', -1 )
      ds_type = ds_def.get( 'type', '' )
      assy_axis = ds_def.get( 'assy_axis', -1 )
      axial_axis = ds_def.get( 'axial_axis', -1 )
      axial_index = ds_def.get( 'axial_index' )
      axis_names = ds_def.get( 'axis_names', () )
      pin_axes = ds_def.get( 'pin_axes' )
      shape_expr = ds_def.get( 'copy_shape_expr', ds_def.get( 'shape_expr' ) )

#                       -- Build header
#                       --
      table_header = os.linesep + '<tr><th>Value</th>'
#      for n in axis_names[ ::-1 ]:
#        if n != 'axial':
#          table_header += '<th>' + n + '</th>'
      if axis_names:
        for ndx, name in axis_names:
          if name != 'axial':
            table_header += '<th>' + name.capitalize() + '</th>'
      #else:
        #table_header += '<th>&nbsp;</th>'

      table_header += '</tr>'

#                       -- Filter dataset
#                       --
      expr_items = [ ':' ] * len( dset.shape )
      if axial_axis >= 0 and axial_index:
        axial_level = min(
            eval( 'self.axialValue.' + axial_index ),
            dset.shape[ axial_axis ] - 1
            )
        expr_items[ axial_axis ] = str( axial_level )
        axis_names = core.CollapseAxisNames( axis_names, 'axial' )

      ds_expr = '[' + ','.join( expr_items ) + ']'
      data = eval( 'dset' + ds_expr )
      #flat_data = data[ np.logical_not( np.isnan( data ) ) ]

#                       -- Build rows
#                       --
      table_rows = ''

      if data is not None and data.size > 0:
        coords = zip( *np.unravel_index(
            np.argsort( data.flatten() ),
            data.shape
            ) )
        #for i in range( len( coords ) - 1, -1, -1 ):
          #coord = coords[ i ]
        row_count = 0
        for coord in coords[ ::-1 ]:
          #if not self.dmgr.IsBadValue( data[ coord ] ):
          if not np.isnan( data[ coord ] ):
            cur_row = '{0}<tr><td>{1}</td>'.\
                format( os.linesep, self._CreateValueString( data[ coord ] ) )
            if axis_names:
              for ndx, name in axis_names:
                if name == 'assembly':
                  addr = self.dmgr.CreateAssemblyAddrFromIndex( coord[ ndx ] )
                  label = core.CreateAssyLabel( *addr[ 1 : 3 ] )
                elif name == 'detector':
                  addr = self.dmgr.CreateDetectorAddrFromIndex( coord[ ndx ] )
                  label = core.CreateAssyLabel( *addr[ 1 : 3 ] )
                elif hasattr( ndx, '__iter__' ):
                  addr = [ coord[ i ] for i in ndx ]
                  label = DataUtils.ToAddrString( *addr )
                else:
                  label = '{0:d}'.format( ndx + 1 )

                cur_row += '<td>{0}</td>'.format( label )
              #end for ndx, name in axis_names

            cur_row += '</tr>'
            table_rows += cur_row

            row_count += 1
            if row_count > 100: break
          #end if not np.isnan( data[ coord ] )
        #end for coord in coords[ ::-1 ]
      #end if data

      if WEB_VIEW:
        table_format = DataAnalysisView.DATA_TABLE
      else:
        table_format = DataAnalysisView.DATA_TABLE_HTML_VIEW
      table_content = table_format.format(
          header = table_header,
          rows = table_rows
          )
      html_content = DataAnalysisView.DATA_HTML.format( table = table_content )
    #end if dset is not None

    title_str = '{0}: Axial {1:.3f}; {2} {3:.4g}'.format(
        self.dmgr.GetDataSetDisplayName( self.curDataSet ),
        self.axialValue.cm,
        self.state.timeDataSet, self.timeValue
        )
    self.headerCtrl.SetValue( title_str )
    if WEB_VIEW:
      self.webView.SetPage( html_content, '' )
    else:
      self.webView.SetPage( html_content )
  #end UpdatePage


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView.UpdateState()			-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    if bool( self ):
      kwargs = self._UpdateStateValues( **kwargs )
      if kwargs.get( 'rebuild', False ):
        self.UpdatePage()
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		DataAnalysisView._UpdateStateValues()		-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    rebuild = kwargs.get( 'rebuild', kwargs.get( 'force_redraw', False ) )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      rebuild = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
    #end if

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      rebuild = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

#		-- Special handling for cur_dataset
    if 'cur_dataset' in kwargs and kwargs[ 'cur_dataset' ] != self.curDataSet:
      ds_type = self.dmgr.GetDataSetType( kwargs[ 'cur_dataset' ] )
      if ds_type and ds_type in self.GetDataSetTypes():
        rebuild = True
        self.curDataSet = kwargs[ 'cur_dataset' ]
	self.container.GetDataSetMenu().Reset()
	wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

        if 'dataset_added' in kwargs:
          del kwargs[ 'dataset_added' ]

        self.axialValue = self.dmgr.\
            GetAxialValue( self.curDataSet, cm = self.axialValue.cm )
        self.stateIndex = max(
            0, self.dmgr.GetTimeValueIndex( self.timeValue, self.curDataSet )
            )

    if 'dataset_added' in kwargs:
      wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

    if 'data_model_mgr' in kwargs:
      rebuild = True

    if 'time_dataset' in kwargs:
      rebuild = True

    if 'time_value' in kwargs and kwargs[ 'time_value' ] != self.timeValue:
      rebuild = True
      self.timeValue = kwargs[ 'time_value' ]

    if rebuild:
      kwargs[ 'rebuild' ] = True

    return  kwargs
  #end _UpdateStateValues

#end DataAnalysisView
