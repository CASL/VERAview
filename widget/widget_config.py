#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget_config.py				-
#	HISTORY:							-
#		2016-06-21	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, platform, sys
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
@param  kwargs		default behavior is to read the current
  read
@param  file_path	optional path to file to read
"""
    if file_path is not None:
      self.Read( file_path )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.IsValid()				-
  #----------------------------------------------------------------------
  def IsValid( self ):
    return  False
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Read()				-
  #----------------------------------------------------------------------
  def Read( self, file_path ):
    """
@param  file_path	path to file to read
"""
    pass
  #end Read


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
