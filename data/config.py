#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		config.py					-
#	HISTORY:							-
#		2015-08-29	leerw@ornl.gov				-
#	  Added test for ImageMagick.
#		2015-04-11	leerw@ornl.gov				-
#	  Added defaultDataSetName property.
#		2014-12-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, subprocess
#import h5py, os, sys, traceback
#import numpy as np


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
  haveImageMagick_ = None
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
  #	METHOD:		HaveImageMagick()				-
  #----------------------------------------------------------------------
  @staticmethod
  def HaveImageMagick():
    """
@return			True or False
"""
    if Config.haveImageMagick_ == None:
      proc = subprocess.Popen(
          [ 'convert', '-h' ],
	  shell = True, stdout = subprocess.PIPE
	  )
      line = proc.stdout.readline()
      proc.stdout.readlines()
      proc.wait()

      Config.haveImageMagick_ = \
        line != None and line.lower().find( 'version: imagemagick' ) == 0
    #end if

    return  Config.haveImageMagick_
  #end HaveImageMagick


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
  #end SetRootDir

#end Config
