#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		table_view.py					-
#	HISTORY:							-
#		2019-01-16	leerw@ornl.gov				-
#         Transition from tally to fluence.
#		2018-10-18	leerw@ornl.gov				-
#	  Moved processing of AUTO_VISIBLE_DATASETS to
#	  _LoadDataModelValues().
#		2018-10-16	leerw@ornl.gov				-
#	  Auto-filling the last column.
#	  Using wx.SplitterWindow with an HtmlWindow attribute view.
#		2018-10-03	leerw@ornl.gov				-
#	  Reverted to just saving and restoring column widths.
#		2018-10-01	leerw@ornl.gov				-
#	  Attempting to auto size column widths.
#		2018-09-14	leerw@ornl.gov				-
#	  Fixed detector, node, and tally support.
#		2018-09-13	leerw@ornl.gov				-
#------------------------------------------------------------------------
import hashlib, logging, math, os, six, sys, tempfile, time, traceback
import numpy as np
import pdb  # pdb.set_trace()

try:
  import wx
  #from wx.html2 import WebView
  import wx.lib.agw.ultimatelistctrl as ulc
except Exception:
  raise ImportError, 'The wxPython module is required for this component'

from data.config import *
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
    'density', 'exposure', 'efpd',
    'inlet_temperature', 'keff', 'power'
  ]


#------------------------------------------------------------------------
#	CLASS:		TableView					-
#------------------------------------------------------------------------
class TableView( Widget ):
  """Table widget.
"""

  ATTRS_HTML = """
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
table.attrs
  {{
  border: 1px solid black;
  border-collapse: collapse;
  margin: 0;
  }}
table.attrs tr
  {{
  border-bottom: 1px solid gray;
  vertical-align: top;
  }}
table.attrs tr th
  {{
  background-color: #c9c9c9;
  border: 1px solid gray;
  font-weight: normal; /*bold*/
  padding: 0.25em;
  text-align: left;
  }}
table.attrs tr th.value
  {{
  padding-left: 1em;
  }}
table.attrs tr td
  {{
  /*border: 1px dotted gray;*/
  border-right: 1px dotted gray;
  font-weight: normal;
  padding: 0.25em;
  text-align: left;
  }}
table.attrs tr td.value
  {{
  padding-left: 1em;
  }}
</style>
</header>
<body>
<p class="title">{modelname} &nbsp; | &nbsp; {displayname}</p>
{table}
</body>
"""

  ATTRS_TABLE = """
<table class="attrs">
  <tr><th>Attribute</th><th class="value">Value</th></tr>
{rows}
</table>
"""

  ATTRS_TABLE_HTML_WINDOW = """
<table class="attrs" border="1" cellpadding="4" cellspacing="0">
  <tr><th>Attribute</th><th class="value">Value</th></tr>
{rows}
</table>
"""


#		-- Object Methods
#		--


#  #----------------------------------------------------------------------
#  #	METHOD:		TableView.__del__()				-
#  #----------------------------------------------------------------------
#  def __del__( self ):
#    if self.dataSetDialog is not None:
#      self.dataSetDialog.Destroy()
#
#    super( TableView, self ).__del__()
#  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		TableView.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, container, id = -1, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    #self.axialValue = DataModel.CreateEmptyAxialValue()
    self.axialValue = AxialValue()
    self.curDataSet = None
    self.curSize = None
#    self.dataSetDialog = None
#    self.dataSetOrder = []  # list of DataSetName
    self.dataSetSelections = {}  # keyed by DataSetName
    self.dataSetTypes = set()
		#-- keyed by DataSetName
    self.dataSetValues = {}

    self.fluenceAddr = FluenceAddress()
    self.nodeAddr = -1
    self.subAddr = ( -1, -1 )
    self.timeValue = -1.0

#		-- Controls
#		--
    self.attrView = None
    self.headerCtrl = None
    self.listCtrl = None
    self.splitterWindow = None

#		-- Fonts
#		--
    client_rect = wx.GetClientDisplayRect()
    font_pt_size = \
        18  if client_rect.Width >= 1600 else \
        16  if client_rect.Width >= 1280 else \
        14  if client_rect.Width >= 1024 else \
	12
#    label_font_params = dict(
#	family = wx.FONTFAMILY_ROMAN,
#	pointSize = font_pt_size,
#	style = wx.FONTSTYLE_NORMAL,
#	weight = wx.FONTWEIGHT_NORMAL
#        )
#    value_font_params = dict( label_font_params )

    if Config.IsWindows():
#      self.nameCharCount = 20
      self.valueCharCount = 12  # 16
      font_pt_size = int( font_pt_size * 0.8 )
#      label_font_params[ 'faceName' ] = 'Lucida Sans'
#      value_font_params[ 'faceName' ] = 'Courier New'
#      label_font_params[ 'pointSize' ] = \
#      value_font_params[ 'pointSize' ] = font_pt_size
#      label_font_params[ 'weight' ] = \
#      value_font_params[ 'weight' ] = wx.FONTWEIGHT_BOLD
#    else:
##      self.nameCharCount = 12  # 14
#      self.valueCharCount = 8
#      #value_font_params[ 'family' ] = wx.FONTFAMILY_TELETYPE
#      value_font_params[ 'faceName' ] = 'Courier New'

#    self.labelFont = wx.Font( **label_font_params )
#    self.valueFont = wx.Font( **value_font_params )

    screen_ppi = wx.ScreenDC().GetPPI()
    self.pixPerChar = 72 * font_pt_size / screen_ppi[ 0 ]

    super( TableView, self ).__init__( container, id )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		TableView._CreateClipboardData()		-
  #----------------------------------------------------------------------
  def _CreateClipboardData( self, mode = 'displayed' ):
    """Retrieves the from the displayed table.
@return			text or None
"""
    csv_text = None
    core = self.dmgr.GetCore()
    if core:
      csv_text = self.headerCtrl.GetValue() + '\n'

      nrows = self.listCtrl.GetItemCount()
      ncols = self.listCtrl.GetColumnCount()

#               -- Column headers
#               --
      row_text = ','.join([
          '"' + self.listCtrl.GetColumn( c ).GetText() + '"'
          for c in range( ncols )
          ])
      csv_text += row_text + '\n'

#               -- Row content
#               --
      if mode == 'displayed':
        row_range = range( nrows )
      else:
        row_ndx = self.listCtrl.GetFirstSelected()
        row_range = \
            range( row_ndx, row_ndx + 1 ) if row_ndx >= 0  else range( 0 )

      for r in row_range:
        row_text = ','.join([
            self.listCtrl.GetItem( r, c ).GetText()
            for c in range( ncols )
            ])
        csv_text += row_text + '\n'

    return  csv_text
  #end _CreateClipboardData


  #----------------------------------------------------------------------
  #	METHOD:		TableView._CreateClipboardImage()		-
  #----------------------------------------------------------------------
  def _CreateClipboardImage( self ):
    """Retrieves the currently-displayed bitmap.
@return			bitmap or None
"""
    ncols = self.listCtrl.GetColumnCount()
    nrows = self.listCtrl.GetItemCount()

    font = self.listCtrl.GetFont()
    font_px_size = font.GetPixelSize()
    col_gap = int( font_px_size[ 0 ] ) << 1
    row_gap = max( 1, int( font_px_size[ 1 ] ) >> 1 )

#       -- Create bitmap for sizing
#       --
    bmap = wx.EmptyBitmapRGBA( 400, 200 )
    dc = wx.MemoryDC()
    dc.SelectObject( bmap )
    dc.SetFont( font )

    row_size = dc.GetTextExtent( 'Xgj9' )
    row_leader = row_size[ 1 ] + row_gap
    #im_ht = ((nrows + 2) * row_size[ 1 ]) + ((nrows + 1) * row_gap)
    im_ht = (nrows + 2) * row_leader + row_gap
    header_size = dc.GetTextExtent( self.headerCtrl.GetValue() )

    col_widths = []
    for c in range( ncols ):
      cell_size = dc.GetTextExtent( self.listCtrl.GetColumn( c ).GetText() )
      cur_wd = cell_size[ 0 ]
      for r in range( nrows ):
        cell_size = dc.GetTextExtent( self.listCtrl.GetItem( r, c ).GetText() )
        cur_wd = max( cur_wd, cell_size[ 0 ] )
      col_widths.append( cur_wd )

    cols_extent = (len( col_widths ) - 1) * col_gap + sum( col_widths )
    im_wd = col_gap + max( header_size[ 0 ], cols_extent ) + col_gap

    dc.SelectObject( wx.NullBitmap )
    del dc
    del bmap

#       -- Create bitmap for rendering
#       --
    bmap, dc = self._CreateEmptyBitmapAndDC( im_wd, im_ht )
    gc = self._CreateGraphicsContext( dc )
    gc.SetFont( font, wx.Colour( 0, 0, 0, 255 ) )
    trans_brush = gc.CreateBrush( wx.TheBrushList.FindOrCreateBrush(
        wx.WHITE, wx.TRANSPARENT
	) )

#       -- Render header
#       --
    y = row_gap
    gc.DrawText( self.headerCtrl.GetValue(), col_gap, y, trans_brush )

    gc.SetPen( wx.ThePenList.FindOrCreatePen(
        wx.Colour( 155, 155, 155, 255 ), 1, wx.PENSTYLE_SOLID
        ) )

    y += row_leader
    x = col_gap
    for c in range( ncols ):
      gc.DrawText( self.listCtrl.GetColumn( c ).GetText(), x, y, trans_brush )
      y2 = y + row_size[ 1 ]
      path = gc.CreatePath()
      path.MoveToPoint( x, y2 )
      path.AddLineToPoint( x + col_widths[ c ], y2 )
      gc.StrokePath( path )

      x += col_widths[ c ] + col_gap

#       -- Render rows
#       --
    y += row_leader
    for r in range( nrows ):
      x = col_gap
      for c in range( ncols ):
        gc.DrawText( self.listCtrl.GetItem( r, c ).GetText(), x, y, trans_brush )
        x += col_widths[ c ] + col_gap
      y += row_leader

    dc.SelectObject( wx.NullBitmap )
    return  bmap
  #end _CreateClipboardImage


##  #----------------------------------------------------------------------
##  #	METHOD:		TableView._CreateMenuDef()			-
##  #----------------------------------------------------------------------
##  def _CreateMenuDef( self ):
##    """
##"""
###    menu_def = super( TableView, self )._CreateMenuDef()
###    more_def = \
###      [
###        { 'label': '-' },
###	{
###	'label': 'Edit Dataset Properties...',
###	'handler': self._OnEditDataSetProps
###	},
###      ]
###    return  menu_def + more_def
##
##    menu_def = \
##      [
##        { 'label': 'Copy Data',
##	   'handler': functools.partial( self._OnCopyData, 'displayed' ) },
##      ]
##  #end _CreateMenuDef


  #----------------------------------------------------------------------
  #	METHOD:		TableView.CreatePrintImage()			-
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
  #	METHOD:		TableView.GetAnimationIndexes()			-
  #----------------------------------------------------------------------
  def GetAnimationIndexes( self ):
    """Accessor for the list of indexes over which this widget can be
animated.  Possible values are 'axial:detector', 'axial:pin', 'statepoint'.
@return			list of indexes or None
"""
    return  ( 'axial:detector', 'axial:pin', 'statepoint' )
  #end GetAnimationIndexes


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """@return		AxialValue instance
( cm value, 0-based core index, 0-based detector index
			  0-based fixed_detector index )
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		TableView._GetDataSetName()			-
  #----------------------------------------------------------------------
  def _GetDataSetName( self, qds_name ):
    """Determines actual dataset name if a pseudo name is provided.
@param  name		DataSetName instance
@return			name to use, None if qds_name is None
"""
    return \
        None  if qds_name is None else \
	self.curDataSet  if qds_name == NAME_selectedDataSet else \
	qds_name
  #end _GetDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    return \
      (
      'channel', 'detector', 'fixed_detector', 'fluence', 'pin',
      'radial_detector', 'scalar',
      ':assembly', ':axial', ':chan_radial', ':core',
      ':node', ':radial', ':radial_assembly'
#      'subpin_cc'
#      ':core'
#      ':assembly', ':axial', ':chan_radial', ':core', ':node',
#      ':radial', ':radial_assembly', ':radial_node',
      )
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetDataSetDisplayMode()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayMode( self ):
    """Returns 'selected'
@return			'selected'
"""
    return  'selected'
  #end GetDataSetDisplayMode


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetEventLockSet()			-
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
  #	METHOD:		TableView.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """@return		0-based state/time index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetTimeValue()			-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """@return		0-based state/time index
"""
    return  self.timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetTitle()				-
  #----------------------------------------------------------------------
  def GetTitle( self ):
    return  'Table View'
  #end GetTitle


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetUsesScaleAndCmap()			-
  #----------------------------------------------------------------------
  def GetUsesScaleAndCmap( self ):
    """
    Returns:
        boolean: False
"""
    return  False
  #end GetUsesScaleAndCmap


  #----------------------------------------------------------------------
  #	METHOD:		TableView.GetVisibleDataSets()			-
  #----------------------------------------------------------------------
  def GetVisibleDataSets( self ):
    """Returns a set of DataSetName instances for visible datasets.
    Returns:
        set(DataSetName): visible DataSetNames
"""
    visibles = [
        k for k in self.dataSetSelections
        if self.dataSetSelections[ k ].get( 'visible', False )
        ]
    return  set( visibles )
  #end GetVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		TableView._InitUI()				-
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

#		-- Splitter window
#		--
    self.splitterWindow = wx.SplitterWindow(
        self, wx.ID_ANY,
	style = wx.SP_3DSASH | wx.SP_LIVE_UPDATE
	)

#		-- Table
#		--
    self.listCtrl = ulc.UltimateListCtrl(
	self.splitterWindow, -1,
	agwStyle =
	    #wx.LC_HRULES | wx.LC_REPORT | wx.LC_VRULES |
	    #wx.LC_SINGLE_SEL |
	    ulc.ULC_HRULES | ulc.ULC_REPORT | ulc.ULC_VRULES |
	    ulc.ULC_SINGLE_SEL |
	    ulc.ULC_HAS_VARIABLE_ROW_HEIGHT
        )
    ##x self.listCtrl.SetFont( self.valueFont )

#		-- Attribute view
#		--
#x    self.attrView = HtmlWindow(
#x        self.splitterWindow, wx.ID_ANY,
#x	style = wx.BORDER_SIMPLE | wx.html.HW_SCROLLBAR_AUTO
#x	)
    if WEB_VIEW:
      self.attrView = WebView.New( self.splitterWindow )
      self.attrView.SetBackgroundColour( self.GetBackgroundColour() )
    else:
      self.attrView = HtmlWindow( self.splitterWindow )

#		-- Lay Out
#		--
    self.listCtrl.Bind( wx.EVT_LIST_ITEM_SELECTED, self._OnItemSelected )
    self.splitterWindow.SplitHorizontally( self.listCtrl, self.attrView, -80 )

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
        self.headerCtrl, 0,
	wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_LEFT | wx.ALL | wx.EXPAND,
	2
	)
#    sizer.Add( self.listCtrl, 3, wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 0 )
#    sizer.Add(
#        self.attrView, 1,
#	wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 1
#	)
    sizer.Add(
        self.splitterWindow, 1,
        wx.ALL | wx.ALIGN_LEFT | wx.ALIGN_TOP | wx.EXPAND, 4
	)
    self.SetAutoLayout( True )
    self.SetSizer( sizer )

#		-- Events
#		--
    self.listCtrl.Bind( wx.EVT_LIST_ITEM_SELECTED, self._OnItemSelected )
    self.Bind( wx.EVT_CONTEXT_MENU, self._OnContextMenu )
    #self.Bind( wx.EVT_SIZE, self._OnSize )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		TableView.IsDataSetScaleCapable()		-
  #----------------------------------------------------------------------
  def IsDataSetScaleCapable( self ):
    """Returns False
    Returns:
        bool: False
"""
    return  False
  #end IsDataSetScaleCapable


  #----------------------------------------------------------------------
  #	METHOD:		TableView.IsDataSetVisible()			-
  #----------------------------------------------------------------------
  def IsDataSetVisible( self, qds_name ):
    """True if the specified dataset is currently displayed, False otherwise.
@param  qds_name	dataset name, DataSetName instance
@return			True if visible, else False
"""
    visible = \
        qds_name in self.dataSetSelections and \
        self.dataSetSelections[ qds_name ].get( 'visible', False )
    return  visible
  #end IsDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		TableView._LoadDataModel()			-
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
  #	METHOD:		TableView._LoadDataModelValues()		-
  #----------------------------------------------------------------------
  def _LoadDataModelValues( self, reason ):
    """This noop version should be implemented in subclasses to create a dict
to be passed to UpdateState().  Assumes self.dmgr is valid.
@return			dict to be passed to UpdateState()
"""
    update_args = {}
    self.dataSetSelections.clear()
    self.dataSetSelections[ self.GetSelectedDataSetName() ] = \
        { 'axis': 'left', 'draworder': 1, 'scale': 1.0, 'visible': True }
#    self.dataSetDialog = None

    #if self.data is not None and self.data.HasData():
    if self.dmgr.HasData():
      if (reason & STATE_CHANGE_axialValue) > 0:
	update_args[ 'axial_value' ] = self.state.axialValue
	    #self.dmgr.NormalizeAxialValue( None, self.state.axialValue )

      if (reason & STATE_CHANGE_coordinates) > 0:
	update_args[ 'assembly_addr' ] = self.dmgr.\
	    NormalizeAssemblyAddr( self.state.assemblyAddr )
	update_args[ 'aux_node_addrs' ] = self.dmgr.\
	    NormalizeNodeAddrs( self.state.auxNodeAddrs )
	update_args[ 'aux_sub_addrs' ] = self.dmgr.\
	    NormalizeSubAddrs( self.state.auxSubAddrs, mode = 'channel' )
	update_args[ 'node_addr' ] = self.dmgr.\
	    NormalizeNodeAddr( self.state.nodeAddr )
	update_args[ 'sub_addr' ] = self.dmgr.\
            NormalizeSubAddr( self.state.subAddr, mode = 'channel' )

      if (reason & STATE_CHANGE_curDataSet) > 0:
	update_args[ 'cur_dataset' ] = self.state.curDataSet

      if (reason & STATE_CHANGE_fluenceAddr) > 0:
        self.fluenceAddr = self.state.fluenceAddr.copy()

      if (reason & STATE_CHANGE_timeDataSet) > 0:
	update_args[ 'time_dataset' ] = self.state.timeDataSet

      if (reason & STATE_CHANGE_timeValue) > 0:
	update_args[ 'time_value' ] = self.state.timeValue

#		-- Auto visible datasets
#		--
      for model_name in sorted( self.dmgr.GetDataModelNames() ):
        dm = self.dmgr.GetDataModel( model_name )
	if dm is not None:
	  st = dm.GetState( 0 )
	  if st is not None:
	    for ds_name in AUTO_VISIBLE_DATASETS:
	      if st.HasDataSet( ds_name ):
	        self.ToggleDataSetVisible(
		    DataSetName( model_name, ds_name ),
		    False
		    )
	    #end for ds_name in AUTO_VISIBLE_DATASETS
	  #end if st is not None
	#end if dm is not None
      #end for model_name in sorted( self.dmgr.GetDataModelNames() )
    #end if self.dmgr.HasData()

    for k in self.dataSetValues:
      qds_name = self._GetDataSetName( k )
      if self.dmgr.GetDataModel( qds_name ) is None:
        update_args[ 'rebuild' ] = True
	if qds_name in self.dataSetSelections:
	  del self.dataSetSelections[ qds_name ]
      #end if qds_name no longer exists
    #end for k

    return  update_args
  #end _LoadDataModelValues


  #----------------------------------------------------------------------
  #	METHOD:		TableView.LoadProps()				-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Called to load properties.
@param  props_dict	dict object from which to deserialize properties
"""
    # axialValue, fluenceAddr handled in Widget
    for k in (
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'subAddr', 'timeValue'
	#'dataSetOrder'
	):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    for k in ( 'dataSetSelections', ):
      if k in props_dict:
        cur_attr = props_dict[ k ]
	for name in cur_attr.keys():
	  cur_value = cur_attr[ name ]
	  del cur_attr[ name ]
          qds_name = DataSetName( name )
          if self.dmgr.HasDataSet( qds_name ):
	    cur_attr[ DataSetName( name ) ] = cur_value
	#end for name

        setattr( self, k, cur_attr )
      #end if k in props_dict
    #end for k

    super( TableView, self ).LoadProps( props_dict )
    self.container.dataSetMenu.UpdateAllMenus()
    wx.CallAfter( self.UpdateState, rebuild = True )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		TableView._OnContextMenu()			-
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


#  #----------------------------------------------------------------------
#  #	METHOD:		TableView._OnEditDataSetProps()			-
#  #----------------------------------------------------------------------
#  def _OnEditDataSetProps( self, ev ):
#    """Must be called from the UI thread.
#"""
#    if self.dataSetDialog is None:
#      self.dataSetDialog = PlotDataSetPropsDialog( self )
#
#    if self.dataSetDialog is not None:
#      self.dataSetDialog.ShowModal( self.dataSetSelections )
#      selections = self.dataSetDialog.GetProps()
#      if selections:
#        for name in self.dataSetSelections:
#	  if name in selections:
#	    ds_rec = self.dataSetSelections[ name ]
#	    sel_rec = selections[ name ]
#	    ds_rec[ 'axis' ] = sel_rec[ 'axis' ]
#	    ds_rec[ 'draworder' ] = sel_rec[ 'draworder' ]
#	    ds_rec[ 'scale' ] = sel_rec[ 'scale' ]
#	#end for
#
#	self.UpdateState( rebuild = True )
#      #end if selections
#    #end if self.dataSetDialog is not None
#  #end _OnEditDataSetProps


  #----------------------------------------------------------------------
  #	METHOD:		TableView._OnItemSelected()			-
  #----------------------------------------------------------------------
  def _OnItemSelected( self, ev ):
    """
"""
    ev_obj = ev.GetEventObject()
    selected_ndx = ev_obj.GetFirstSelected()
    if selected_ndx >= 0:
      #ds_name = self.listCtrl.GetItemText( selected_ndx );
      item_data = self.listCtrl.GetItemData( selected_ndx )
      self.UpdateAttrView( item_data )
  #end _OnItemSelected


  #----------------------------------------------------------------------
  #	METHOD:		TableView.Redraw()                              -
  #----------------------------------------------------------------------
  def Redraw( self ):
    """
"""
    #self.UpdateState( rebuild = True )
    self._BusyDoOp( self.UpdateState, rebuild = True )
  #end Redraw


  #----------------------------------------------------------------------
  #	METHOD:		TableView.SaveProps()				-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict, for_drag = False ):
    """Called to load properties.  This implementation takes care of
'dataSetSelections' and 'timeValue', but subclasses must override for
all other properties.
@param  props_dict	dict object to which to serialize properties
"""
    super( TableView, self ).SaveProps( props_dict, for_drag = for_drag )

    # axialValue, fluenceAddr handled in Widget
    for k in (
	'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs',
	'nodeAddr', 'subAddr', 'timeValue'
	#'dataSetOrder'
	):
      props_dict[ k ] = getattr( self, k )

    for k in ( 'dataSetSelections', ):
      if hasattr( self, k ):
        cur_attr = getattr( self, k )
	if isinstance( cur_attr, dict ):
	  for name in cur_attr.keys():
	    if isinstance( name, DataSetName ):
	      cur_value = cur_attr[ name ]
	      del cur_attr[ name ]
	      cur_attr[ name.name ] = cur_value
	  #end for name
	#end if isinstance( cur_value, dict )

	props_dict[ k ] = cur_attr
      #end if hasattr( self, k )
    #end for k
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		TableView.SetVisibleDataSets()			-
  #----------------------------------------------------------------------
  def SetVisibleDataSets( self, qds_names ):
    """Applys the set of visible DataSetName instances.
    Args:
        qds_names (set(DataSetName)): set of all visible DataSetNames
"""
#               -- Now invisible
#               --
    for k, rec in six.iteritems( self.dataSetSelections ):
      if rec.get( 'visible', False ) and k not in qds_names:
        rec[ 'visible' ] = False

    max_order = max(
        map(
            lambda x: x.get( 'draworder', 1 ),
	    six.itervalues( self.dataSetSelections )
	    )
        )

#               -- Now visible
#               --
    for k in qds_names:
      #qds_name = self._GetDataSetName( k )
      if k in self.dataSetSelections:
        self.dataSetSelections[ k ][ 'visible' ] = True
      else:
        self.dataSetSelections[ k ] = \
          {
	  'axis': 'left',
	  'draworder': max_order + 1,
	  'scale': 1.0,
	  'visible': True
	  }
        max_order += 1
    #end for qds_name in qds_names
  #end SetVisibleDataSets


  #----------------------------------------------------------------------
  #	METHOD:		TableView.ToggleDataSetVisible()		-
  #----------------------------------------------------------------------
  def ToggleDataSetVisible( self, qds_name, rebuild = True ):
    """Toggles the visibility of the named dataset.
Must be called from the event thread.
@param  qds_name	dataset name, DataSetName instance
"""
    if qds_name in self.dataSetSelections:
      rec = self.dataSetSelections[ qds_name ]
      rec[ 'visible' ] = not rec[ 'visible' ]

    else:
      if len( self.dataSetSelections ) == 0:
        max_order = 0
      else:
        max_order = max(
            map(
	        lambda x: x.get( 'draworder', 1 ),
	        six.itervalues( self.dataSetSelections )
	        )
            )
      self.dataSetSelections[ qds_name ] = \
        {
	'axis': 'left',
	'draworder': max_order + 1,
	'scale': 1.0,
	'visible': True
	}

    if rebuild:
      self.UpdateState( rebuild = True )
  #end ToggleDataSetVisible


  #----------------------------------------------------------------------
  #	METHOD:		TableView.UpdateAttrView()			-
  #----------------------------------------------------------------------
  def UpdateAttrView( self, item_data ):
    """Must be called from the UI thread.
    Args:
	item_data (list): qds_name(DataSetName) [, h5py.AttributeManager ]
"""
    table_content = ''
    if item_data:
      qds_name = item_data[ 0 ]

      attrs = item_data[ 1 ]  if len( item_data ) > 1 else  {}
      names = sorted( attrs.keys() )
      if len( names ) == 0:
        table_content = '<p>No attributes</p>'
      else:
        table_rows = ''
	for name in sorted( names ):
	  value = attrs[ name ]
	  value_str = \
	      np.array2string( value ) if isinstance( value, np.ndarray ) else \
	      str( value_str )
          table_rows += '  <tr><td>{0:s}</td><td class="value">{1:s}</td></tr>'.\
              format( name, value_str )
        if WEB_VIEW:
          table_format = TableView.ATTRS_TABLE
        else:
          table_format = TableView.ATTRS_TABLE_HTML_WINDOW
        table_content = table_format.format( rows = table_rows )
      #end else not len( item_data ) == 0

    #end if item_data

    content = TableView.ATTRS_HTML.format(
        displayname = qds_name.displayName,
        modelname = qds_name.modelName,
        table = table_content
        )

    if WEB_VIEW:
      self.attrView.SetPage( content, '' )
    else:
      self.attrView.SetPage( content )
  #end UpdateAttrView


  #----------------------------------------------------------------------
  #	METHOD:		TableView.UpdateState()				-
  #----------------------------------------------------------------------
  def UpdateState( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    if bool( self ):
      kwargs = self._UpdateStateValues( **kwargs )
      if kwargs.get( 'rebuild', False ):
        self.UpdateTable()
  #end UpdateState


  #----------------------------------------------------------------------
  #	METHOD:		TableView._UpdateStateValues()			-
  # Must be called from the UI thread.
  #----------------------------------------------------------------------
  def _UpdateStateValues( self, **kwargs ):
    """
Must be called from the UI thread.
"""
    #xxxx
    #  track when need to blow away any cached values for current
    #  selections
    rebuild = kwargs.get( 'rebuild', kwargs.get( 'force_redraw', False ) )

    if 'assembly_addr' in kwargs and \
        kwargs[ 'assembly_addr' ] != self.assemblyAddr:
      rebuild = True
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
    #end if

    if 'aux_node_addrs' in kwargs and \
        kwargs[ 'aux_node_addrs' ] != self.auxNodeAddrs:
      rebuild = True
      self.auxNodeAddrs = \
          DataUtils.NormalizeNodeAddrs( kwargs[ 'aux_node_addrs' ] )

    if 'aux_sub_addrs' in kwargs and \
        kwargs[ 'aux_sub_addrs' ] != self.auxSubAddrs:
      rebuild = True
      self.auxSubAddrs = \
          self.dmgr.NormalizeSubAddrs( kwargs[ 'aux_sub_addrs' ], 'channel' )

    if 'axial_value' in kwargs and \
        kwargs[ 'axial_value' ].cm != self.axialValue.cm:
      rebuild = True
      self.axialValue = \
          self.dmgr.GetAxialValue( None, cm = kwargs[ 'axial_value' ].cm )
    #end if

    cur_dataset = kwargs.get( 'cur_dataset' )
    if cur_dataset and cur_dataset != self.curDataSet:
      ds_type = self.dmgr.GetDataSetType( cur_dataset )
      if ds_type in self.GetDataSetTypes():
        self.curDataSet = cur_dataset
	select_name = self.GetSelectedDataSetName()
	select_rec = self.dataSetSelections.get( select_name )
	if select_rec and select_rec.get( 'visible', False ):
	  rebuild = True
    #end if

    if 'data_model_mgr' in kwargs:
      rebuild = True

    if 'dataset_added' in kwargs:
      wx.CallAfter( self.container.GetDataSetMenu().UpdateAllMenus )

    if 'node_addr' in kwargs and kwargs[ 'node_addr' ] != self.nodeAddr:
      rebuild = True
      self.nodeAddr = DataUtils.NormalizeNodeAddr( kwargs[ 'node_addr' ] )

    if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] != self.subAddr:
      rebuild = True
      self.subAddr = kwargs[ 'sub_addr' ]
    #end if

    if 'fluence_addr' in kwargs and \
        kwargs[ 'fluence_addr' ] != self.fluenceAddr:
      rebuild = True
      self.fluenceAddr = self.state.fluenceAddr.copy()
    #end if 'fluence_addr'

    if 'time_dataset' in kwargs:
      rebuild = True

    if 'time_value' in kwargs and kwargs[ 'time_value' ] != self.timeValue:
      rebuild = True
      self.timeValue = kwargs[ 'time_value' ]

    if rebuild:
      kwargs[ 'rebuild' ] = True

    return  kwargs
  #end _UpdateStateValues


  #----------------------------------------------------------------------
  #	METHOD:		TableView.UpdateTable()				-
  #----------------------------------------------------------------------
  def UpdateTable( self ):
    """
Must be called from the UI thread.
"""
    def create_pin_label( col, row ):
      return  '({0:d},{1:d})'.format( col + 1, row + 1 )
    #end create_pin_label

#		-- Save any existing column widths
#		--
    col_widths = []
    for i in range( self.listCtrl.GetColumnCount() ):
      col_widths.append( self.listCtrl.GetColumnWidth( i ) )
    if len( col_widths ) > 0:
      del col_widths[ -1 ]

    self.listCtrl.ClearAll()
    self.headerCtrl.SetValue( '' )

    core = None
    if self.dmgr.HasData() and \
        self.assemblyAddr[ 0 ] >= 0 and self.axialValue.cm >= 0.0:
      core = self.dmgr.GetCore()

    if core:
      dc = wx.ClientDC( self )

      # fill with state values core.CreateAssyLabel(), timeValue, fluenceAddr
      #self.headerCtrl.SetValue( 'Header here' )
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
      title_str = 'Assy %s; Axial %.3f; %s %.4g' % (
          show_assy_addr,
	  self.axialValue.cm,
	  self.state.timeDataSet,
	  self.timeValue
	  )
      if self.dmgr.HasDataSetType( 'fluence' ):
        th = \
int( core.fluenceMesh.GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' ) )
        block = '; Fluence r={0:.1f} th={1:d}'.format(
            core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ), th
	    )
        title_str += block
      self.headerCtrl.SetValue( title_str )

      have_nodals = self.dmgr.HasNodalDataSetType()

#		-- Create columns
#		--
      self.listCtrl.InsertColumn(
          0, 'Dataset',
	  width = wx.LIST_AUTOSIZE
	  )

      sub_addr_col = 1
      self.listCtrl.InsertColumn(
          1, create_pin_label( *self.subAddr ),
	  format = ulc.ULC_FORMAT_RIGHT,
	  width = wx.LIST_AUTOSIZE
	  )
      ncols = 2

      aux_sub_addrs = sorted( self.auxSubAddrs, Widget.CompareAuxAddrs )
      for addr in aux_sub_addrs:
        self.listCtrl.InsertColumn(
	    ncols, create_pin_label( *addr ),
	    format = ulc.ULC_FORMAT_RIGHT,
	    width = wx.LIST_AUTOSIZE
	    )
        ncols += 1

      if have_nodals and self.nodeAddr >= 0:
        node_addr_set = set([ self.nodeAddr ])
        for node_addr in self.auxNodeAddrs:
	  node_addr_set.add( node_addr )

        node_addr_col = ncols
        for node_addr in node_addr_set:
          self.listCtrl.InsertColumn(
	      ncols, '@{0:d}'.format( node_addr + 1 ),
	      format = ulc.ULC_FORMAT_RIGHT,
	      width = wx.LIST_AUTOSIZE
              )
	  ncols += 1
      #end if self.nodeAddr >= 0

#		-- Add Rows
#		--
      qds_names = [
          k for k in self.dataSetSelections
	  if self.dataSetSelections[ k ].get( 'visible', False )
	  ]
      qds_names.sort()
      if NAME_selectedDataSet in qds_names and len( qds_names ) > 1:
        qds_names.remove( NAME_selectedDataSet )
	qds_names.insert( 0, NAME_selectedDataSet )

      row = 0
      for k in qds_names:
        rec = self.dataSetSelections[ k ]
        qds_name = self._GetDataSetName( k )
	if rec.get( 'visible', False ) and qds_name is not None:
	  values = [ np.nan ] * ncols
	  value_str = self.dmgr.GetDataSetDisplayName( qds_name, True )
	  self.listCtrl.InsertStringItem( row, value_str )
	  #self.listCtrl.SetItemData( row, qds_name )
	  item_data = [ qds_name ]

	  dset = None
	  ds_def = self.dmgr.GetDataSetDefByQName( qds_name )
	  if ds_def:
	    dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
	  if dset is not None:
	    #dset_array = np.array( dset )
	    ds_shape = dset.shape
	    ds_type = self.dmgr.GetDataSetType( qds_name )
	    #self.listCtrl.SetItemData( row, dset.attrs )
	    item_data.append( dset.attrs )

	    assy_ndx = self.assemblyAddr[ 0 ]

#					-- scalar
	    if ds_type == 'scalar':
	      values[ 1 ] = dset[ 0 ]  if len( ds_shape ) > 0 else  dset[ () ]

#					-- detector, fixed_detector
	    elif ds_type == 'detector' or ds_type == 'fixed_detector':
	      axial_level = \
	          self.axialValue.fixedDetectorIndex \
		  if ds_type == 'fixed_detector' else \
	          self.axialValue.detectorIndex
	      axial_level = min( axial_level, ds_shape[ 0 ] - 1 )
	      det_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 1 ] - 1 )
	      values[ 1 ] = dset[ axial_level, det_ndx ]

#					-- radial_detector
	    elif ds_type == 'radial_detector':
	      det_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 0 ] - 1 )
	      values[ 1 ] = dset[ det_ndx ]

#					-- fluence
	    elif ds_type == 'fluence':
	      axial_level = \
                  min( self.axialValue.fluenceIndex, ds_shape[ 0 ] - 1 )
	      theta_ndx = min( self.fluenceAddr.thetaIndex, ds_shape[ 1 ] - 1 )
	      radius_ndx = \
                  min( self.fluenceAddr.radiusIndex, ds_shape[ 2 ] - 1 )
	      values[ 1 ] = dset[ axial_level, theta_ndx, radius_ndx ]

#					-- nodal
	    elif self.dmgr.IsNodalType( ds_type ):
	      if self.nodeAddr >= 0 and 'copy_shape' in ds_def:
	        ds_shape = ds_def[ 'copy_shape' ]
		assy_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 3 ] - 1 )
	        axial_level = min( self.axialValue.pinIndex, ds_shape[ 2 ] - 1 )
		col = node_addr_col
		for node_addr in node_addr_set:
		  values[ col ] = dset[ 0, node_addr, axial_level, assy_ndx ]
		  col += 1
	      #end if self.nodeAddr >= 0 and if 'copy_shape' in ds_def

#					-- pin-based
	    else:
	      assy_axis = ds_def.get( 'assy_axis', -1 )
	      assy_ndx = \
	          0  if assy_axis < 0 else \
		  min( self.assemblyAddr[ 0 ], ds_shape[ assy_axis ] - 1 )
	      assy_ndx = max( 0, assy_ndx )

	      axial_axis = ds_def.get( 'axial_axis', -1 )
	      axial_level = \
	          0  if axial_axis < 0 else \
		  min( self.axialValue.pinIndex, ds_shape[ axial_axis ] - 1 )
	      axial_level = max( 0, axial_level )

	      pin_col = max( 0, min( self.subAddr[ 0 ], ds_shape[ 1 ] - 1 ) )
	      pin_row = max( 0, min( self.subAddr[ 1 ], ds_shape[ 0 ] - 1 ) )

	      col = sub_addr_col
	      values[ col ] = dset[ pin_row, pin_col, axial_level, assy_ndx ]
	      for addr in aux_sub_addrs:
	        pin_col = max( 0, min( addr[ 0 ], ds_shape[ 1 ] - 1 ) )
	        pin_row = max( 0, min( addr[ 1 ], ds_shape[ 0 ] - 1 ) )
		col += 1
		values[ col ] = dset[ pin_row, pin_col, axial_level, assy_ndx ]
	  #end if dset is not None

	  #dc.SetFont( self.valueFont )
	  for col in range( 1, ncols ):
	    value = values[ col ]
	    value_str = \
	        ''  if np.isnan( value ) else \
		'{0:.7g}'.format( value )
	    self.listCtrl.SetStringItem( row, col, value_str )

	  self.listCtrl.SetItemData( row, item_data )
	  row += 1
	#end if rec.get( 'visible', False )
      #end for k in qds_names

#		-- Restore any column widths
#		--
      for i in range( min( ncols, len( col_widths ) ) ):
        self.listCtrl.SetColumnWidth( i, col_widths[ i ] )
      self.listCtrl.SetColumnWidth(
          self.listCtrl.GetColumnCount() - 1,
	  -3 # wx.LIST_AUTOSIZE_FILL
          )
    #end if core

    self.listCtrl.DoLayout()
  #end UpdateTable


  #----------------------------------------------------------------------
  #	METHOD:		TableView.UpdateTable_calc_widths()		-
  #----------------------------------------------------------------------
  def UpdateTable_calc_widths( self ):
    """
Must be called from the UI thread.
"""
    def create_pin_label( col, row ):
      return  '({0:d},{1:d})'.format( col + 1, row + 1 )
    #end create_pin_label

    self.listCtrl.ClearAll()
    self.headerCtrl.SetValue( '' )

    core = None
    if self.dmgr.HasData() and \
        self.assemblyAddr[ 0 ] >= 0 and self.axialValue.cm >= 0.0:
      core = self.dmgr.GetCore()

    if core:
      dc = wx.ClientDC( self )

      # fill with state values core.CreateAssyLabel(), timeValue, fluenceAddr
      #self.headerCtrl.SetValue( 'Header here' )
      show_assy_addr = core.CreateAssyLabel( *self.assemblyAddr[ 1 : 3 ] )
      title_str = 'Assy %s; Axial %.3f; %s %.4g' % (
          show_assy_addr,
	  self.axialValue.cm,
	  self.state.timeDataSet,
	  self.timeValue
	  )
      if self.dmgr.HasDataSetType( 'fluence' ):
        th = \
int( core.fluenceMesh.GetTheta( self.fluenceAddr.thetaIndex, units = 'deg' ) )
        block = '; Fluence r={2:.1f},th={3:d}'.format(
            core.fluenceMesh.GetRadius( self.fluenceAddr.radiusIndex ), th
	    )
        title_str += block
      self.headerCtrl.SetValue( title_str )

      have_nodals = self.dmgr.HasNodalDataSetType()

#		-- Create columns
#		--
      value_wd = self.valueCharCount * self.pixPerChar
      self.listCtrl.InsertColumn(
          0, 'Dataset',
	  width = wx.LIST_AUTOSIZE
	  )

      sub_addr_col = 1
      self.listCtrl.InsertColumn(
          1, create_pin_label( *self.subAddr ),
	  format = ulc.ULC_FORMAT_RIGHT,
	  width = wx.LIST_AUTOSIZE
	  )
      ncols = 2

      aux_sub_addrs = sorted( self.auxSubAddrs, Widget.CompareAuxAddrs )
      for addr in aux_sub_addrs:
        self.listCtrl.InsertColumn(
	    ncols, create_pin_label( *addr ),
	    format = ulc.ULC_FORMAT_RIGHT,
	    width = wx.LIST_AUTOSIZE
	    )
        ncols += 1

      if have_nodals and self.nodeAddr >= 0:
        node_addr_set = set([ self.nodeAddr ])
        for node_addr in self.auxNodeAddrs:
	  node_addr_set.add( node_addr )

        node_addr_col = ncols
        for node_addr in node_addr_set:
          self.listCtrl.InsertColumn(
	      ncols, '@{0:d}'.format( node_addr + 1 ),
	      format = ulc.ULC_FORMAT_RIGHT,
	      #width = value_wd
	      width = wx.LIST_AUTOSIZE
              )
	  ncols += 1
      #end if self.nodeAddr >= 0

# noworky
#      for i in range( 1, self.listCtrl.GetColumnCount() ):
#        self.listCtrl.GetColumn( i ).SetFont( self.valueFont )

#		-- Add Rows
#		--
      col_widths = [ 1 ] * ncols
      qds_names = [
          k for k in self.dataSetSelections
	  if self.dataSetSelections[ k ].get( 'visible', False )
	  ]
      qds_names.sort()
      if NAME_selectedDataSet in qds_names and len( qds_names ) > 1:
        qds_names.remove( NAME_selectedDataSet )
	qds_names.insert( 0, NAME_selectedDataSet )

      row = 0
      for k in qds_names:
        rec = self.dataSetSelections[ k ]
        qds_name = self._GetDataSetName( k )
	if rec.get( 'visible', False ):
	  values = [ np.nan ] * ncols
	  value_str = self.dmgr.GetDataSetDisplayName( qds_name, True )
	  self.listCtrl.InsertStringItem( row, value_str )

	  dset = None
	  ds_def = self.dmgr.GetDataSetDefByQName( qds_name )
	  if ds_def:
	    dset = self.dmgr.GetH5DataSet( qds_name, self.timeValue )
	  if dset is not None:
	    #dset_array = np.array( dset )
	    ds_shape = dset.shape
	    ds_type = self.dmgr.GetDataSetType( qds_name )

	    assy_ndx = self.assemblyAddr[ 0 ]

#					-- scalar
	    if ds_type == 'scalar':
	      values[ 1 ] = dset[ 0 ]  if len( ds_shape ) > 0 else  dset[ () ]

#					-- detector, fixed_detector
	    elif ds_type == 'detector' or ds_type == 'fixed_detector':
	      axial_level = \
	          self.axialValue.fixedDetectorIndex \
		  if ds_type == 'fixed_detector' else \
	          self.axialValue.detectorIndex
	      axial_level = min( axial_level, ds_shape[ 0 ] - 1 )
	      det_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 1 ] - 1 )
	      values[ 1 ] = dset[ axial_level, det_ndx ]

#					-- radial_detector
	    elif ds_type == 'radial_detector':
	      det_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 0 ] - 1 )
	      values[ 1 ] = dset[ det_ndx ]

#					-- fluence
	    elif ds_type == 'fluence':
	      axial_level = min( self.axialValue.fluence, ds_shape[ 0 ] - 1 )
	      theta_ndx = min( self.fluenceAddr.thetaIndex, ds_shape[ 1 ] - 1 )
	      radius_ndx = \
                  min( self.fluenceAddr.radiusIndex, ds_shape[ 2 ] - 1 )
	      values[ 1 ] = dset[ axial_level, theta_ndx, radius_ndx ]

#					-- nodal
	    elif self.dmgr.IsNodalType( ds_type ):
	      if self.nodeAddr >= 0 and 'copy_shape' in ds_def:
	        ds_shape = ds_def[ 'copy_shape' ]
		assy_ndx = min( self.assemblyAddr[ 0 ], ds_shape[ 3 ] - 1 )
	        axial_level = min( self.axialValue.pin, ds_shape[ 2 ] - 1 )
		col = node_addr_col
		for node_addr in node_addr_set:
		  values[ col ] = dset[ 0, node_addr, axial_level, assy_ndx ]
		  col += 1
	      #end if self.nodeAddr >= 0 and if 'copy_shape' in ds_def

#					-- pin-based
	    else:
	      assy_axis = ds_def.get( 'assy_axis', -1 )
	      assy_ndx = \
	          0  if assy_axis < 0 else \
		  min( self.assemblyAddr[ 0 ], ds_shape[ assy_axis ] - 1 )
	      assy_ndx = max( 0, assy_ndx )

	      axial_axis = ds_def.get( 'axial_axis', -1 )
	      axial_level = \
	          0  if axial_axis < 0 else \
		  min( self.axialValue.pinIndex, ds_shape[ axial_axis ] - 1 )
	      axial_level = max( 0, axial_level )

	      pin_col = max( 0, min( self.subAddr[ 0 ], ds_shape[ 1 ] - 1 ) )
	      pin_row = max( 0, min( self.subAddr[ 1 ], ds_shape[ 0 ] - 1 ) )

	      col = sub_addr_col
	      values[ col ] = dset[ pin_row, pin_col, axial_level, assy_ndx ]
	      for addr in aux_sub_addrs:
	        pin_col = max( 0, min( addr[ 0 ], ds_shape[ 1 ] - 1 ) )
	        pin_row = max( 0, min( addr[ 1 ], ds_shape[ 0 ] - 1 ) )
		col += 1
		values[ col ] = dset[ pin_row, pin_col, axial_level, assy_ndx ]
	  #end if dset is not None

	  item = self.listCtrl.GetItem( row, 0 )
##x	  item.SetFont( self.labelFont )
##x	  item.SetText( item.GetText() )
##x	  self.listCtrl.SetItem( item )

	  #dc.SetFont( self.labelFont )
	  if item.GetFont():
	    dc.SetFont( item.GetFont() )
	  else:
	    dc.SetFont( self.listCtrl.GetFont() )
	  value_size = dc.GetTextExtent( item.GetText() )
	  col_widths[ 0 ] = max( col_widths[ 0 ], value_size[ 0 ] )

	  #dc.SetFont( self.valueFont )
	  for col in range( 1, ncols ):
	    value = values[ col ]
	    value_str = ''  if np.isnan( value ) else  '{0:.7g}'.format( value )

	    self.listCtrl.SetStringItem( row, col, value_str )
	    item = self.listCtrl.GetItem( row, col )
##x	    item.SetFont( self.valueFont )
##x	    item.SetText( value_str )
##x	    self.listCtrl.SetItem( item )

	    value_size = dc.GetTextExtent( value_str )
	    col_widths[ col ] = max( col_widths[ col ], value_size[ 0 ] )

	  row += 1
	#end if rec.get( 'visible', False )
      #end for k in qds_names

#		-- Explicitly resize all the columns
#		--
      for col in range( ncols ):
        self.listCtrl.SetColumnWidth( col, int( col_widths[ col ] * 1.2 ) )
    #end if core

    self.listCtrl.DoLayout()
  #end UpdateTable_calc_widths

#end TableView
