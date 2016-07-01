#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget_config.py				-
#	HISTORY:							-
#		2016-06-30	leerw@ornl.gov				-
#	  Replaced axialLevel and stateIndex with state.
#		2016-06-21	leerw@ornl.gov				-
#------------------------------------------------------------------------
import json, os, platform, sys
import pdb  # set_trace()

try:
  import wx
except Exception:
  raise ImportError( "The wxPython module is required" )

from event.state import *


#------------------------------------------------------------------------
#	CLASS:		WidgetConfig					-
#------------------------------------------------------------------------
class WidgetConfig( object ):
  """Per-user widget configuration.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, file_path = None ):
    """
#@param  kwargs		optional initialization arguments
#  file_path		path to file to read
#  frame_size		size of 
@param  file_path	optional path to file to read
"""
    self.fDict = \
      {
      'frameSize': ( 0, 0 ),
      'state': {},
      'widgets': []
      }

    if file_path is not None:
      self.Read( file_path )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.AddWidgets()			-
  #----------------------------------------------------------------------
  def AddWidgets( self, *widget_list ):
    """
"""
    for w in widget_list:
      module_path = w.__module__ + '.' + w.__class__.__name__
      rec = { 'classpath': module_path }
      w.SaveProps( rec )
      self.fDict[ 'widgets' ].append( rec )
    #end for w
  #end AddWidgets


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetFilePath()			-
  #----------------------------------------------------------------------
  def GetFilePath( self ):
    """
@return			path to saved file or None
"""
    return  self.fDict.get( 'filePath' )
  #end GetFilePath


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetFrameSize()			-
  #----------------------------------------------------------------------
  def GetFrameSize( self ):
    """
@return			size tuple ( wd, ht ), default to ( 0, 0 )
"""
    return  self.fDict.get( 'frameSize', ( 0, 0 ) )
  #end GetFrameSize


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetStateProps()			-
  #----------------------------------------------------------------------
  def GetStateProps( self ):
    """
@return			state properties
"""
    return  self.fDict.get( 'state', {} )
  #end GetStateProps


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetWidgetProps()			-
  #----------------------------------------------------------------------
  def GetWidgetProps( self ):
    """
@return			list of widget properties recs
"""
    return  self.fDict.get( 'widgets', [] )
  #end GetWidgetProps


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Read()				-
  #----------------------------------------------------------------------
  def Read( self, file_path ):
    """
@param  file_path	path to file to read or None to read the user file
"""
    if 'filePath' in self.fDict:
      del self.fDict[ 'filePath' ]
    self.fDict[ 'frameSize' ] = ( 0, 0 )
    del self.fDict[ 'widgets' ][ : ]

    if file_path is None:
      file_path = WidgetConfig.GetUserSessionPath()

    if os.path.exists( file_path ):
      fp = file( file_path )
      try:
	content = fp.read( -1 )
	self.fDict = json.loads( content )
      finally:
        fp.close()
    #end if
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetFilePath()			-
  #----------------------------------------------------------------------
  def SetFilePath( self, file_path = None ):
    """
@param  file_path	path to file or None
"""
    if file_path is None:
      del self.fDict[ 'filePath' ]
    else:
      self.fDict[ 'filePath' ] = file_path
  #end SetFilePath


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetFrameSize()			-
  #----------------------------------------------------------------------
  def SetFrameSize( self, wd, ht ):
    """
"""
    self.fDict[ 'frameSize' ] = ( wd, ht )
  #end SetFrameSize


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetState()				-
  #----------------------------------------------------------------------
  def SetState( self, state ):
    """
@param  state		event.state.State reference
"""
    rec = {}
    if state is not None:
      state.SaveProps( rec )
    self.fDict[ 'state' ] = rec
  #end SetState


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Write()				-
  #----------------------------------------------------------------------
  def Write( self, file_path = None ):
    """
@param  file_path	path to file to write or None to write the user file
"""
    if file_path is None:
      file_path = WidgetConfig.GetUserSessionPath()

    fp = file( file_path, 'w' )
    try:
      fp.write( json.dumps( self.fDict, indent = 2 ) )
    finally:
      fp.close()
  #end Write


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetPlatformAppDataDir()		-
  #----------------------------------------------------------------------
  @staticmethod
  def GetPlatformAppDataDir( create_flag = False ):
    """
@param  create_flag	true to create the app data dir
@return			path to application data directory
"""
    path = None
    sys_name = platform.system()

    if sys_name == 'Darwin':
      app_dir = os.path.join(
          os.environ.get( 'HOME', '' ),
	  'Library', 'Application Support'
	  )
      if os.path.exists( app_dir ):
        path = os.path.join( app_dir, 'VERAView' )

    elif sys_name == 'Windows':
      app_dir = os.environ.get( 'APPDATA' )
      if app_dir is not None and os.path.exists( app_dir ):
        path = os.path.join( app_dir, 'VERAView' )

    if path is None:
      home = os.environ.get( 'HOME', os.getcwd() )
      path = os.path.join( home, '.veraview' )

    if create_flag and not os.path.exists( path ):
      os.makedirs( path )

    return  path
  #end GetPlatformAppDataDir


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetUserSessionPath()		-
  #----------------------------------------------------------------------
  @staticmethod
  def GetUserSessionPath():
    return \
    os.path.join( WidgetConfig.GetPlatformAppDataDir(), 'session.vview' )
  #end GetUserSessionPath


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.ReadUserSession()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ReadUserSession():
    """
"""
    config = None
    file_path = WidgetConfig.GetUserSessionPath()
    if os.path.exists( file_path ):
      config = WidgetConfig( file_path )

    return  config
  #end ReadUserSession
#end WidgetConfig
