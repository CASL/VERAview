#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		config.py					-
#	HISTORY:							-
#		2016-10-25	leerw@ornl.gov				-
#	  Configuring logging.
#		2016-03-17	leerw@ornl.gov				-
#	  We now care about gifsicle instead of ImageMagick.
#		2016-01-15	leerw@ornl.gov				-
#	  Better way to find ImageMagick convert.
#		2015-08-29	leerw@ornl.gov				-
#	  Added test for ImageMagick.
#		2015-04-11	leerw@ornl.gov				-
#	  Added defaultDataSetName property.
#		2014-12-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import logging, logging.config, os, platform, subprocess
from distutils.spawn import find_executable
import pdb


#------------------------------------------------------------------------
#	CLASS:		Config						-
#------------------------------------------------------------------------
class Config( object ):
  """Global state class.

Static properties (use accessors):
  defaultDataSetName	default name for vector dataset
  resDir		resources directory
  rootDir		root directory
"""


#		-- Class Attributes
#		--

  defaultDataSetName_ = 'pin_powers'
  haveGifsicle_ = None
  #haveImageMagick_ = None
  resDir_ = ''
  rootDir_ = ''


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		GetDefaultDataSetName()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetDefaultDataSetName():
    return  Config.defaultDataSetName_
  #end GetDefaultDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		GetResDir()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetResDir():
    return  Config.resDir_
  #end GetResDir


  #----------------------------------------------------------------------
  #	METHOD:		GetRootDir()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetRootDir():
    return  Config.rootDir_
  #end GetRootDir


  #----------------------------------------------------------------------
  #	METHOD:		HaveGifsicle()					-
  #----------------------------------------------------------------------
  @staticmethod
  def HaveGifsicle():
    """
@return			True or False
"""
    if Config.haveGifsicle_ is None:
      #path = find_executable( 'gifsicle' )
      #Config.haveGifsicle_ = path is not None
      path = None
      mach = platform.machine()
      sys = platform.system().lower()
      if sys == 'linux':
        if mach.find( '64' ) >= 0:
	  path = 'linux64'
      elif sys == 'darwin':
        if mach.find( '64' ) >= 0:
	  path = 'macos'
      elif sys == 'windows':
        path = 'win64' if mach.find( '64' ) >= 0 else 'win32'

      if path is not None:
        Config.haveGifsicle_ = os.path.join( Config.rootDir_, 'bin', path )
	os.environ[ 'PATH' ] += os.pathsep + Config.haveGifsicle_
    #end if

    return  Config.haveGifsicle_
  #end HaveGifsicle


  #----------------------------------------------------------------------
  #	METHOD:		HaveImageMagick()				-
  #----------------------------------------------------------------------
#  @staticmethod
#  def HaveImageMagick():
#    """
#@return			True or False
#"""
#    if Config.haveImageMagick_ is None:
#      path = find_executable( 'convert' )
#      Config.haveImageMagick_ = path is not None
#    #end if
#
#    return  Config.haveImageMagick_
#  #end HaveImageMagick


  #----------------------------------------------------------------------
  #	METHOD:		SetDefaultDataSetName()				-
  #----------------------------------------------------------------------
  @staticmethod
  def SetDefaultDataSetName( value ):
    Config.defaultDataSetName_ = value
  #end SetDefaultDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		SetRootDir()					-
  #----------------------------------------------------------------------
  @staticmethod
  def SetRootDir( value ):
    Config.rootDir_ = value
    Config.resDir_ = os.path.join( value, 'res' )

    log_file = os.path.join( Config.resDir_, 'logging.conf' )
    logging.config.fileConfig( log_file )
    #logging.config.fileConfig( os.path.join( Config.resDir_, 'logging.conf' ) )
  #end SetRootDir

#end Config
