#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		html_message_dialog.py				-
#	HISTORY:							-
#		2017-04-20	leerw@ornl.gov				-
#------------------------------------------------------------------------
import functools, json, math, os, sys, time, traceback
import pdb  #pdb.set_trace()

try:
  import wx
  from wx.html import HtmlWindow
#  from wx.lib.scrolledpanel import ScrolledPanel
#  import wx, wx.lib.newevent
except Exception:
  raise ImportError( 'The wxPython module is required for this component' )


#------------------------------------------------------------------------
#	CLASS:		HtmlMessageWindow				-
#------------------------------------------------------------------------
class HtmlMessageWindow( HtmlWindow ):
  """Wrapper on HtmlWindow to handle links.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageWindow.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, parent, id = -1, size = ( 600, 400 ) ):
    """
"""
    super( HtmlMessageWindow, self ).__init__(
        parent, id,
	size = size,
	style = wx.html.HW_SCROLLBAR_AUTO
	)

    if 'gtk2' in wx.PlatformInfo:
      self.SetStandardFonts()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageWindow.OnLinkClicked()		-
  #----------------------------------------------------------------------
  def OnLinkClicked( self, link ):
    """
"""
    wx.LaunchDefaultBrowser( link.GetLinkInfo().GetHref() )
  #end OnLinkClicked

#end HtmlMessageWindow


#------------------------------------------------------------------------
#	CLASS:		HtmlMessageDialog				-
#------------------------------------------------------------------------
class HtmlMessageDialog( wx.Dialog ):
  """
Properties:
  window		HtmlMessageWindow reference
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """
@param  message		optional message
"""
    message = kwargs.get( 'message' )
    if message:
      del kwargs[ 'message' ]

    style = kwargs.get(
        'style',
	wx.DEFAULT_DIALOG_STYLE | wx.TAB_TRAVERSAL | wx.THICK_FRAME
	)
    style |= wx.RESIZE_BORDER
    kwargs[ 'style' ] = style

    super( HtmlMessageDialog, self ).__init__( *args, **kwargs )

    self.fWindow = None
    self._InitUI( message )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.GetWindow()			-
  #----------------------------------------------------------------------
  def GetWindow( self ):
    return  self.fWindow
  #end GetWindow


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog._InitUI()			-
  #----------------------------------------------------------------------
  def _InitUI( self, message = None ):
    """
"""
    self.fWindow = HtmlMessageWindow( self )
    if message:
      self.fWindow.SetPage( message )

    close_button = wx.Button( self, label = '&Close' )
    close_button.Bind(
        wx.EVT_BUTTON,
	functools.partial( self._OnButton, 'close' )
	)
    close_button.SetDefault()

    button_sizer = wx.BoxSizer( wx.HORIZONTAL )
    button_sizer.AddStretchSpacer()
    button_sizer.Add( close_button, 0, wx.ALL | wx.EXPAND, 6 );
    button_sizer.AddStretchSpacer()

    sizer = wx.BoxSizer( wx.VERTICAL )
    sizer.Add(
	self.fWindow, 1,
	wx.ALIGN_TOP | wx.ALL | wx.EXPAND,
	6
	)
    sizer.Add( button_sizer, 0, wx.ALL | wx.EXPAND, 6 )
    sizer.Layout()

    self.SetSizer( sizer )
    self.Fit()
    self.CenterOnParent( wx.BOTH )
  #end _InitUI


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog._OnButton()			-
  #----------------------------------------------------------------------
  def _OnButton( self, mode, ev ):
    ev.Skip()

    if mode == 'close':
      self.EndModal( 0 )
  #end _OnButton


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.ShowModal()			-
  #----------------------------------------------------------------------
#  def ShowModal( self ):
#    #self.fResult = None
#    super( HtmlMessageDialog, self ).ShowModal()
#  #end ShowModal


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	HtmlMessageDialog.window			-
  #----------------------------------------------------------------------
  window = property( GetWindow )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.CreateBody()			-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateBody( content ):
    """Wraps the message in <body> tags.
@return			self.htmlMessage
"""
    body = '<body>\n' + content + '\n</body>\n'
    return  body
  #end CreateBody


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.CreateDocument()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateDocument( body_content, header_content = None ):
    """Wraps the message in <html> tags.
"""
    if not header_content:
      header_content = '<head></head>'

    html = \
        '<html>\n' + header_content + '\n<body>' + body_content + '</body>\n'
    return  html
  #end CreateDocument


  #----------------------------------------------------------------------
  #	METHOD:		HtmlMessageDialog.ShowBox()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ShowBox( message, caption, parent ):
    """
"""
    dialog = HtmlMessageDialog( parent, wx.ID_ANY, caption, message = message )
    dialog.ShowModal()
  #end ShowBox

#end HtmlMessageDialog
