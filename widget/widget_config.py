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
    self.fDict = {}

    if file_path is not None:
      self.Read( file_path )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.AddWidgets()			-
  #----------------------------------------------------------------------
  def AddWidgets( self, *widget_list ):
    """
"""
    pass
  #end AddWidgets


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetFrameSize()			-
  #----------------------------------------------------------------------
  def GetFrameSize( self ):
    """
@return			size tuple ( wd, ht ), default to ( 0, 0 )
"""
    return  self.fDict.get( 'frameSize', ( 0, 0 ) )
  #end GetFrameSize


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
@param  file_path	path to file to read
"""
    pass
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetFrameSize()			-
  #----------------------------------------------------------------------
  def SetFrameSize( self, wd, ht ):
    """
"""
    self.fDict[ 'frameSize' ] = ( wd, ht )
  #end SetFrameSize


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
      pass
      #config = WidgetConfig( file_path )

    return  config
  #end ReadUserFile
#end WidgetConfig
