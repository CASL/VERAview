#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		animators.py				        -
#	HISTORY:							-
#		2015-08-31	leerw@ornl.gov				-
#		2015-08-29	leerw@ornl.gov				-
#------------------------------------------------------------------------
import glob, os, shutil, sys, time, tempfile, threading
#import pdb

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( "The wxPython module is required" )

from data.config import Config
from data.datamodel import *
from event.state import *
import widget


#------------------------------------------------------------------------
#	CLASS:		AnimatorThreads					-
#------------------------------------------------------------------------
class AnimatorThreads( object ):
  """Animator base class.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AnimatorThreads.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    """
@param  widget_in	Widget from which to get images, cannot be None
@param  kwargs
  'callback'		optional reference to callback callable on progress
#  'data_model'		required reference to DataModel object, cannot be None
#  'state'		required reference to State, cannot be None
"""
#		-- Assert
#		--
    self.widget = widget_in
    if widget_in == None:
      raise  Exception( 'widget cannot be None' )

    self.state = widget_in.GetState()
    if self.state == None:
      raise  Exception( 'widget state is missing' )

    self.data = State.GetDataModel( self.state )
    if self.data == None:
      raise  Exception( 'widget data model is missing' )

#    self.data = kwargs.get( 'data_model', None )
#    self.state = kwargs.get( 'state', None )
#    self.widget = kwargs.get( 'widget', None )

    self.callback = kwargs.get( 'callback', None )
    if self.callback != None and not hasattr( self.callback, '__call__' ):
      self.callback = None

    self.nextStep = 0
#		-- Subclasses must define these
#		--
    self.restoreValue = None
    self.totalSteps = 0
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AnimatorThreads.CreateAnimatedImage()		-
  #----------------------------------------------------------------------
  def CreateAnimatedImage( self, file_path, temp_dir ):
    """
"""
    fnames = glob.glob( os.path.join( temp_dir, '*.png' ) )
    for f in sorted( fnames ):
      # subprocess.call() fails on Windows
      os.system( 'convert "%s" "%s.gif"' % ( f, f ) )

    os.system(
        'convert -dispose Background -delay 50 -loop 99 "%s" "%s"' % \
        ( os.path.join( temp_dir, '*.gif' ), file_path )
        )

#               -- Create HTML file
#               --
    fp = file( file_path + '.html', 'w' )
    try:
      name = os.path.basename( file_path )
      print >> fp, '<header><title>%s</title></header>' % name
      print >> fp, '<body><img src="%s"/></body>' % name
    finally:
      fp.close()
  #end CreateAnimatedImage


  #----------------------------------------------------------------------
  #	METHOD:		AnimatorThreads._DoNextStep()			-
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Must not be called on the UI thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    return  False
  #end _DoNextStep


  #----------------------------------------------------------------------
  #	METHOD:		AnimatorThreads._Run()				-
  #----------------------------------------------------------------------
  def _Run( self, file_path ):
    """
Must not be called on the UI thread.
@param  file_path	path to gif file to create
@return			True if there are further steps, False if finished
"""
    try:
      #self.widget.Freeze()
      pdb.set_trace()
      temp_dir = tempfile.mkdtemp( '.animations' )

      count = 0
      while self._DoNextStep():
	if self.callback != None:
	  self.callback( count + 1, self.totalSteps + 1 )

        fpath = os.path.join( temp_dir, 'temp-%03d.png' % count )
	while self.widget.IsBusy():
	  time.sleep( 0.1 )
	self.widget.CreatePrintImage( fpath )

	count += 1
      #end while stepping

      if self.callback != None:
        self.callback( count, self.totalSteps + 1 )

      self.CreateAnimatedImage( file_path, temp_dir )

      if self.callback != None:
        self.callback( -1, self.totalSteps + 1 )

    except Exception, ex :
      msg = 'Error creating image:' + os.linesep + str( ex )
      if self.callback != None:
        self.callback( -2, 0, msg )

    finally:
      #self.widget.Thaw()
      if temp_dir != None:
        shutil.rmtree( temp_dir )
    #end if we have a destination file path
  #end _Run


  #----------------------------------------------------------------------
  #	METHOD:		AnimatorThreads.Start()				-
  #----------------------------------------------------------------------
  def Start( self, file_path ):
    """
Must be called from the UI event thread.
Creates a separate thread with the _Run() method as target.
@param  file_path	path to gif file to create
@return			thread that was started
"""
    t = threading.Thread( target = self._Run, args = ( file_path, ) )
    t.start()
    return  t
  #end Start

#end AnimatorThreads


#------------------------------------------------------------------------
#	CLASS:		Animator					-
#------------------------------------------------------------------------
class Animator( object ):
  """Animator base class.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Animator.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    """
@param  widget_in	Widget from which to get images, cannot be None
@param  kwargs
  'callback'		optional reference to callback callable on progress
#  'data_model'		required reference to DataModel object, cannot be None
#  'state'		required reference to State, cannot be None
"""
#		-- Assert
#		--
    self.widget = widget_in
    if widget_in == None:
      raise  Exception( 'widget cannot be None' )

    self.state = widget_in.GetState()
    if self.state == None:
      raise  Exception( 'widget state is missing' )

    self.data = State.GetDataModel( self.state )
    if self.data == None:
      raise  Exception( 'widget data model is missing' )

#    self.data = kwargs.get( 'data_model', None )
#    self.state = kwargs.get( 'state', None )
#    self.widget = kwargs.get( 'widget', None )

    self.callback = kwargs.get( 'callback', None )
    if self.callback != None and not hasattr( self.callback, '__call__' ):
      self.callback = None

    self.nextStep = 0
#		-- Subclasses must define these
#		--
    self.restoreValue = None
    self.totalSteps = 0
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Animator.CreateAnimatedImage()                  -
  #----------------------------------------------------------------------
  def CreateAnimatedImage( self, file_path, temp_dir ):
    """
"""
    fnames = glob.glob( os.path.join( temp_dir, '*.png' ) )
    for f in sorted( fnames ):
      # subprocess.call() fails on Windows
      os.system( 'convert "%s" "%s.gif"' % ( f, f ) )

    os.system(
        'convert -dispose Background -delay 50 -loop 99 "%s" "%s"' % \
        ( os.path.join( temp_dir, '*.gif' ), file_path )
        )

#               -- Create HTML file
#               --
    fp = file( file_path + '.html', 'w' )
    try:
      name = os.path.basename( file_path )
      print >> fp, '<header><title>%s</title></header>' % name
      print >> fp, '<body><img src="%s"/></body>' % name
    finally:
      fp.close()
  #end CreateAnimatedImage


  #----------------------------------------------------------------------
  #	METHOD:		Animator._DoNextStep()                           -
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Must not be called on the UI thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    return  False
  #end _DoNextStep


  #----------------------------------------------------------------------
  #	METHOD:		Animator.Run()                           	-
  #----------------------------------------------------------------------
  def Run( self, file_path ):
    """
Must be called from the UI event thread.
Creates a separate thread with the _Run() method as target.
@param  file_path	path to gif file to create
@return			thread that was started
"""
    dialog = wx.ProgressDialog(
	'Save Animated Image',
	'Initializing...'
        )
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBegin,
	wargs = [ dialog, file_path ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RunBegin()                           	-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog, file_path ):
    """
"""
    temp_dir = tempfile.mkdtemp( '.animation' )
    status = { 'dialog': dialog, 'file_path': file_path, 'temp_dir': temp_dir }

    try:
      count = 0
      while self._DoNextStep():
        wx.CallAfter(
	    dialog.Update,
	    int( count * 100.0 / (self.totalSteps + 1) ),
	    'Creating frame %d/%d' % ( count + 1, self.totalSteps )
	    )

        fpath = os.path.join( temp_dir, 'temp-%03d.png' % count )
	while self.widget.IsBusy():
	  time.sleep( 0.1 )
	self.widget.CreatePrintImage( fpath )

	count += 1
      #end while stepping

      wx.CallAfter(
	  dialog.Update,
	  int( count * 100.0 / (self.totalSteps + 1) ),
	  'Creating animated GIF'
          )

      self.CreateAnimatedImage( file_path, temp_dir )

    except Exception, ex :
      status[ 'messages' ] = \
          [ 'Error creating image:' + os.linesep + str( ex ) ]

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RunEnd()                           	-
  #----------------------------------------------------------------------
  def _RunEnd( self, result ):
    """
"""
    status = result.get()
    if status != None:
      status[ 'dialog' ].Destroy()

      messages = status.get( 'messages' )
      if messages != None and len( messages ) > 0:
        msg = \
	    'Animated GIF not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, 'Save Animated Image', wx.OK_DEFAULT )
    #end if

    shutil.rmtree( status[ 'temp_dir' ] )
  #end _RunEnd

#end Animator


#------------------------------------------------------------------------
#	CLASS:		DetectorAxialAnimator				-
#------------------------------------------------------------------------
class DetectorAxialAnimator( Animator ):
  """Animator interface
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( DetectorAxialAnimator, self ).__init__( widget_in, **kwargs )

    self.restoreValue = self.state.axialValue
    self.totalSteps = self.data.GetCore().ndetax
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator._DoNextStep()		-
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Must be called on the UI thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    #continue_flag = self.nextStep < self.data.GetCore().ndetax
    continue_flag = self.nextStep < self.totalSteps

    axial_value = \
        self.data.CreateAxialValue( detector_ndx = self.nextStep ) \
        if continue_flag else \
        self.restoreValue
    self.widget.UpdateState( axial_value = axial_value )
    #self.widget.HandleStateChange( STATE_CHANGE_axialValue )

    self.nextStep += 1
    return  continue_flag
  #end _DoNextStep

#end DetectorAxialAnimator


#------------------------------------------------------------------------
#	CLASS:		PinAxialAnimator				-
#------------------------------------------------------------------------
class PinAxialAnimator( Animator ):
  """Animator interface
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PinAxialAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( PinAxialAnimator, self ).__init__( widget_in, **kwargs )

    self.restoreValue = self.state.axialValue
    self.totalSteps = self.data.GetCore().nax
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		PinAxialAnimator._DoNextStep()                  -
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Must be called on the UI thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    #continue_flag = self.nextStep < self.data.GetCore().nax
    continue_flag = self.nextStep < self.totalSteps

    axial_value = \
        self.data.CreateAxialValue( core_ndx = self.nextStep ) \
        if continue_flag else \
        self.restoreValue
    self.widget.UpdateState( axial_value = axial_value )
    #self.widget.HandleStateChange( STATE_CHANGE_axialValue )

    self.nextStep += 1
    return  continue_flag
  #end _DoNextStep

#end PinAxialAnimator


#------------------------------------------------------------------------
#	CLASS:		StatePointAnimator				-
#------------------------------------------------------------------------
class StatePointAnimator( Animator ):
  """Animator interface
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		StatePointAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( StatePointAnimator, self ).__init__( widget_in, **kwargs )

    self.restoreValue = self.state.stateIndex
    self.totalSteps = len( self.data.GetStates() )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		StatePointAnimator._DoNextStep()		-
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Must be called on the UI thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    #continue_flag = self.nextStep < len( self.data.GetStates() )
    continue_flag = self.nextStep < self.totalSteps

    state_ndx = self.nextStep if continue_flag else self.restoreValue
    self.widget.UpdateState( state_index = state_ndx )
    #self.widget.HandleStateChange( STATE_CHANGE_stateIndex )

    self.nextStep += 1
    return  continue_flag
  #end _DoNextStep

#end StatePointAnimator
