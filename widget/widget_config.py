#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget_config.py				-
#	HISTORY:							-
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
      'axialLevel': 0.0,
      'frameSize': ( 0, 0 ),
      'widgets': [],
      'stateIndex': 0
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
  #	METHOD:		WidgetConfig.GetAxialLevel()			-
  #----------------------------------------------------------------------
  def GetAxialLevel( self ):
    """
@return			axial level in cm
"""
    return  self.fDict.get( 'axialLevel', 0.0 )
  #end GetAxialLevel


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
  #	METHOD:		WidgetConfig.GetStateIndex()			-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """
@return			0-based state index
"""
    return  self.fDict.get( 'stateIndex', 0 )
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetWidgets()			-
  #----------------------------------------------------------------------
  def GetWidgets( self ):
    """
@return			list of widget properties recs
"""
    return  self.fDict.get( 'widgets', [] )
  #end GetWidgets


#  #----------------------------------------------------------------------
#  #	METHOD:		WidgetConfig.IsValid()				-
#  #----------------------------------------------------------------------
#  def IsValid( self ):
#    return  False
#  #end IsValid


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
      file_path = os.path.join(
          WidgetConfig.GetPlatformAppDataDir(),
	  'widget.config'
	  )

    if os.path.exists( file_path ):
      fp = file( file_path )
      try:
	content = fp.read( -1 )
	cur_dict = json.loads( content )
#	if 'filePath' in cur_dict:
#	  self.fDict[ 'filePath' ] = cur_dict[ 'filePath' ]
#	if 'frameSize' in cur_dict:
#	  self.fDict[ 'frameSize' ] = cur_dict[ 'frameSize' ]
#	if 'widgets' in cur_dict:
#	  self.fDict[ 'widgets' ] = cur_dict[ 'widgets' ]
        self.fDict = cur_dict
      finally:
        fp.close()
    #end if
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetAxialLevel()			-
  #----------------------------------------------------------------------
  def SetAxialLevel( self, level ):
    """
@param  level		axial level in cm
"""
    self.fDict[ 'axialLevel' ] = max( level, 0.0 )
  #end SetAxialLevel


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
  #	METHOD:		WidgetConfig.SetStateIndex()			-
  #----------------------------------------------------------------------
  def SetStateIndex( self, state_ndx ):
    """
@param  state_ndx	0-based index
"""
    self.fDict[ 'stateIndex' ] = max( state_ndx, 0 )
  #end SetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Write()				-
  #----------------------------------------------------------------------
  def Write( self, file_path = None ):
    """
@param  file_path	path to file to write or None to write the user file
"""
    if file_path is None:
      file_path = os.path.join(
          WidgetConfig.GetPlatformAppDataDir( True ),
	  'widget.config'
	  )

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
  #	METHOD:		WidgetConfig.ReadUserFile()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ReadUserFile():
    """
"""
    config = None
    file_path = \
        os.path.join( WidgetConfig.GetPlatformAppDataDir(), 'widget.config' )

    if os.path.exists( file_path ):
      config = WidgetConfig( file_path )

    return  config
  #end ReadUserFile
#end WidgetConfig
