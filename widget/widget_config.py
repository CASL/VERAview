#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		widget_config.py				-
#	HISTORY:							-
#		2018-08-27	leerw@ornl.gov				-
#	  Added filter for ASCII chars in Decode().
#		2017-09-23	leerw@ornl.gov				-
#	  Implemented decoding object_hook with __jsonclass__ and
#	  fromjson() convention.
#		2016-12-08	leerw@ornl.gov				-
#	  Multiple file paths.
#		2016-12-02	leerw@ornl.gov				-
#	  Renamed NumpyEncoder to WidgetEncoder and added WidgetDecoder.
#		2016-11-19	leerw@ornl.gov				-
#	  Added static methods CreateWidgetProps(), Decode(), Encode().
#		2016-08-20	leerw@ornl.gov				-
#	  Added framePosition property.
#		2016-07-08	leerw@ornl.gov				-
#	  Added NumpyEncoder.
#		2016-06-30	leerw@ornl.gov				-
#	  Replaced axialLevel and stateIndex with state.
#		2016-06-21	leerw@ornl.gov				-
#------------------------------------------------------------------------
import json, logging, os, platform, six, sys
import numpy as np
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


#		-- Class Attributes
#		--

  fLogger_ = logging.getLogger( 'widget' )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self,
      file_path = None, frame_position = None, frame_size = None
      ):
    """
@param  file_path	optional path to file to read
@param  frame_position	optional ( x, y ) to store
@param  frame_size	optional ( wd, ht ) to store
"""
    if frame_position is None:
      frame_position = ( 0, 0 )
    if frame_size is None:
      frame_size = ( 0, 0 )

    self.fDict = \
      {
      'framePosition': frame_position,
      'frameSize': frame_size,
      'state': {},
      'widgets': []
      }
    self.fLogger = WidgetConfig.fLogger_

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
      #CreateWidgetProps()
      module_path = w.__module__ + '.' + w.__class__.__name__
      rec = { 'classpath': module_path }
      w.SaveProps( rec )
      self.fDict[ 'widgets' ].append( rec )
    #end for w
  #end AddWidgets


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetDataModelPaths()		-
  #----------------------------------------------------------------------
  def GetDataModelPaths( self ):
    """
@return			path to saved file or None
"""
    return  self.fDict.get( 'dataModelPaths' )
  #end GetDataModelPaths


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.GetFramePosition()			-
  #----------------------------------------------------------------------
  def GetFramePosition( self ):
    """
@return			position tuple ( x, y ), default to ( 0, 0 )
"""
    return  self.fDict.get( 'framePosition', ( 0, 0 ) )
  #end GetFramePosition


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
  #	METHOD:		WidgetConfig.GetGridSize()			-
  #----------------------------------------------------------------------
  def GetGridSize( self ):
    """
@return			size tuple ( ncols, nrows ), default to ( 1, 1 )
"""
    return  self.fDict.get( 'gridSize', ( 1, 1 ) )
  #end GetGridSize


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
    #if 'dataModelPaths' in self.fDict:
      #del self.fDict[ 'dataModelPaths' ]
    self.fDict[ 'frameSize' ] = ( 0, 0 )
    del self.fDict[ 'widgets' ][ : ]

    if file_path is None:
      file_path = WidgetConfig.GetUserSessionPath()

    if os.path.exists( file_path ):
      fp = file( file_path )
      try:
	content = fp.read( -1 )
	#self.fDict = json.loads( content )
	self.fDict = \
	    json.loads( content, object_hook = WidgetConfig.DecodeObject )
      finally:
        fp.close()
    #end if
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetDataModelPaths()		-
  #----------------------------------------------------------------------
  def SetDataModelPaths( self, *paths ):
    """
@param  paths	path to file or None
"""
    if paths and len( paths ) > 0:
      self.fDict[ 'dataModelPaths' ] = paths
    else:
      del self.fDict[ 'dataModelPaths' ]
  #end SetDataModelPaths


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetFramePosition()			-
  #----------------------------------------------------------------------
  def SetFramePosition( self, x, y ):
    """
"""
    self.fDict[ 'framePosition' ] = ( x, y )
  #end SetFramePosition


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetFrameSize()			-
  #----------------------------------------------------------------------
  def SetFrameSize( self, wd, ht ):
    """
"""
    self.fDict[ 'frameSize' ] = ( wd, ht )
  #end SetFrameSize


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.SetGridSize()			-
  #----------------------------------------------------------------------
  def SetGridSize( self, ncols, nrows ):
    """
"""
    self.fDict[ 'gridSize' ] = ( ncols, nrows )
  #end SetGridSize


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
      file_path = WidgetConfig.GetUserSessionPath( True )

    fp = file( file_path, 'w' )
    #fp2 = file( file_path + '.pickle', 'w' )
    try:
      fp.write( json.dumps( self.fDict, cls = WidgetEncoder, indent = 2 ) )
      #pickle.dump( self.fDict, fp2 )
    finally:
      fp.close()
      #fp2.close()
  #end Write


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.CreateWidgetProps()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateWidgetProps( widget, for_drag = False ):
    """Creates widget properties with classpath.
    Args:
        widget (widget.Widget): widget to serialize
	for_drag (bool): True if serializing for drag-n-drop
    Returns:
        dict: properties dict
"""
    module_path = widget.__module__ + '.' + widget.__class__.__name__
    widget_props = { 'classpath': module_path }
    widget.SaveProps( widget_props, for_drag = for_drag )
    return  widget_props
  #end CreateWidgetProps


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Decode()				-
  #----------------------------------------------------------------------
  @staticmethod
  def Decode( json_str ):
    """Decodes/deserializes obj to JSON.
@param  json_str	JSON string to be decoded
@return			Python object
"""
    #return  json.loads( json_str.rstrip( '\t\r\n ' ) )
    content = json_str.rstrip( '\t\r\n ' )
    content = filter( lambda c : ord(c) < 128, content )
    try:
      return  json.loads( content, object_hook = WidgetConfig.DecodeObject )
    except Exception as ex:
      WidgetConfig.fLogger_.exception( 'content:' + os.linesep + content )
  #end Decode


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.DecodeObject()			-
  #----------------------------------------------------------------------
  @staticmethod
  def DecodeObject( json_obj ):
    """Decoder hook that looks for a '__jsonclass__' key identifying the
full classpath, for which there should be a static fromjson() method.
"""
    result = json_obj
    classpath = json_obj.get( '__jsonclass__' )
    if classpath:
      try:
        module_path, class_name = classpath.rsplit( '.', 1 )
	module = __import__( module_path, fromlist = [ class_name ] )
	cls = getattr( module, class_name )
	if hasattr( cls, 'fromjson' ):
	  result = getattr( cls, 'fromjson' )( json_obj )
      except Exception, ex:
        msg = 'instantiating ' + classpath + ':' + os.linesep
        WidgetConfig.fLogger_.exception( msg )

    return  result
  #end DecodeObject


  #----------------------------------------------------------------------
  #	METHOD:		WidgetConfig.Encode()				-
  #----------------------------------------------------------------------
  @staticmethod
  def Encode( obj ):
    """Encodes/serializes obj to JSON.
@param  obj		Python object to be encoded
@return			JSON string
"""
    return  json.dumps( obj, cls = WidgetEncoder, indent = 2 )
  #end Encode


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
  def GetUserSessionPath( create_flag = False ):
    return \
    os.path.join(
        WidgetConfig.GetPlatformAppDataDir( create_flag ),
	'session.vview'
	)
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


#------------------------------------------------------------------------
#	CLASS:		WidgetEncoder					-
#------------------------------------------------------------------------
class WidgetEncoder( json.JSONEncoder ):
  """Extension to handle numpy types and objects with tojson().
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetEncoder.default()				-
  #----------------------------------------------------------------------
  def default( self, obj ):
    result = \
        int( obj )  if isinstance( obj, np.integer ) else \
        float( obj )  if isinstance( obj, np.floating ) else \
        obj.tolist()  if isinstance( obj, np.ndarray ) else \
	obj.tojson()  if hasattr( obj, 'tojson' )  else \
	super( WidgetEncoder, self ).default( obj )
    return  result
  #end default

#end WidgetEncoder
