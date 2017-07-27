#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		animators.py				        -
#	HISTORY:							-
#		2017-06-09	leerw@ornl.gov				-
#	  New widget-synchronous scheme.
#		2017-02-17	leerw@ornl.gov				-
#	  Zipping individual images.
#		2017-01-12	leerw@ornl.gov				-
#	  Migrating to DataModelMgr.
#		2016-03-17	leerw@ornl.gov				-
#	  Using PIL and gifsicle instead of ImageMagick.
#		2015-08-31	leerw@ornl.gov				-
#		2015-08-29	leerw@ornl.gov				-
#------------------------------------------------------------------------
import glob, logging, os, platform, shutil, subprocess, sys, \
    time, tempfile, threading, zipfile
#import traceback
#import pdb

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( "The wxPython module is required" )

try:
  import PIL.Image
  #import PIL.Image, PIL.ImageDraw, PIL.ImageFont
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) required for this component'

from data.config import Config
from data.datamodel import *
from event.state import *
import widget


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
    """Subclasses must set self.restoreValue and self.totalSteps.
@param  widget_in	Widget from which to get images, cannot be None
@param  kwargs
  'callback'		optional reference to callback callable on progress
  			that will be called on the UI thread
"""
#		-- Assert
#		--
    self.widget = widget_in
    if widget_in is None:
      raise  Exception( 'widget cannot be None' )

    self.curDataSet = widget_in.GetCurDataSet()
#    if self.curDataSet is None:
#      raise  Exception( 'widget current dataset is missing' )

    self.state = widget_in.GetState()
    if self.state is None:
      raise  Exception( 'widget state is missing' )

    self.dmgr = self.state.dataModelMgr
    if self.dmgr is None:
      raise  Exception( 'widget data model manager is missing' )

    self.callback = kwargs.get( 'callback' )
    if self.callback is not None and not hasattr( self.callback, '__call__' ):
      self.callback = None

    self.logger = logging.getLogger( 'widget' )
    self.nextStep = 0
    self.stepLock = threading.RLock()
    self.working = False

    self.totalSteps, self.restoreValue = self._GetInitValues()

    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'totalSteps=%d', self.totalSteps )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Animator.CreateAnimatedImage()                  -
  #----------------------------------------------------------------------
  def CreateAnimatedImage( self, file_path, temp_dir ):
    """
"""
    zfp = zipfile.ZipFile( file_path + '.images.zip', 'w', zipfile.ZIP_DEFLATED )
    fnames = glob.glob( os.path.join( temp_dir, '*.png' ) )
    try:
      for f in sorted( fnames ):
#      # subprocess.call() fails on Windows
#      os.system( 'convert "%s" "%s.gif"' % ( f, f ) )
	gif_name = f.replace( '.png', '.gif' )
        png_im = PIL.Image.open( f )
        gif_im = PIL.Image.new( "RGBA", png_im.size, ( 236, 236, 236, 255 ) )
        gif_im.paste( png_im, ( 0, 0 ), png_im )
        #gif_im.save( f + '.gif', 'GIF' )
        gif_im.save( gif_name, 'GIF' )

	zfp.write( f, os.path.basename( f ) )
	zfp.write( gif_name, os.path.basename( gif_name ) )
      #end for f
    finally:
      zfp.close()

    args = \
        [ 'gifsicle', '--disposal=background', '--delay=50', '--loop' ] + \
        glob.glob( os.path.join( temp_dir, '*.gif' ) ) + \
	[ '-o', file_path ]
    proc = subprocess.Popen( args )
    proc.wait()
#    os.system(
#        'convert -dispose Background -delay 50 -loop 99 "%s" "%s"' % \
#        ( os.path.join( temp_dir, '*.gif' ), file_path )
#        )

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
  #	METHOD:		Animator._CreateStepImage()			-
  #----------------------------------------------------------------------
  def _CreateStepImage( self, dialog, fpath ):
    """Must be called on the UI thread.
"""
    pct = int( self.nextStep * 100.0 / (self.totalSteps + 1) )
    msg = 'Creating frame %d/%d' % ( (self.nextStep + 1), self.totalSteps )
    self.logger.info( msg )

    dialog.Update( pct, msg )
    dialog.Fit()
    if not dialog.WasCancelled():
      if self.callback:
        self.callback( self.nextStep + 1, self.totalSteps, msg )

      self._DoStepUpdate()
      while self.widget.IsBusy():
	self.logger.debug( 'widget.IsBusy wait' )
# wx.Yield() seems necessary for raster widgets
        #time.sleep( 0.5 )
        wx.Yield()

      self.widget.CreatePrintImage( fpath )

      self.stepLock.acquire()
      try:
        self.nextStep += 1
      finally:
        self.stepLock.release()

    else:
      if self.callback:
        self.callback( 0, 0, 'Aborted' )
      self.stepLock.acquire()
      try:
        self.nextStep = self.totalSteps + 1
      finally:
        self.stepLock.release()
    #end else canceled
  #end _CreateStepImage


  #----------------------------------------------------------------------
  #	METHOD:		Animator._DoStepUpdate()			-
  #----------------------------------------------------------------------
  def _DoStepUpdate( self ):
    """Must be implemented by subclasses.  Called on the UI thread.
"""
    pass
  #end _DoStepUpdate


  #----------------------------------------------------------------------
  #	METHOD:		Animator._GetInitValues()			-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
    return  ( 0, None )
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RestoreState()			-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    pass
  #end _RestoreState


  #----------------------------------------------------------------------
  #	METHOD:		Animator.Run()                           	-
  #----------------------------------------------------------------------
  def Run( self, file_path ):
    """
Must be called from the UI event thread.
Creates a worker thread with the _RunBegin() and _Runend() methods.
@param  file_path	path to gif file to create
"""
    
    dialog = wx.ProgressDialog(
	'Save Animated Image',
	'Initializing...',
	style = wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
        )
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBackground,
	wargs = [ dialog, file_path ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RunBackground()			-
  #----------------------------------------------------------------------
  def _RunBackground( self, dialog, file_path ):
    """
"""
    temp_dir = tempfile.mkdtemp( '.animation' )
    status = { 'dialog': dialog, 'file_path': file_path, 'temp_dir': temp_dir }

    try:
      self.nextStep = 0
      while self.nextStep < self.totalSteps:
        wait_for_step = self.nextStep + 1
	fpath = os.path.join( temp_dir, '{0:04d}.png'.format( self.nextStep ) )
	wx.CallAfter( self._CreateStepImage, dialog, fpath )

	blocking = True
	while blocking:
	  time.sleep( 0.1 )
	  self.stepLock.acquire()
	  try:
	    blocking = self.nextStep < wait_for_step
	  finally:
	    self.stepLock.release()
	#end while blocking
      #end while stepping

      if self.nextStep > self.totalSteps:
        status[ 'messages' ] = [ 'Aborted' ]
      else:
        wx.CallAfter( dialog.Pulse, 'Creating animated GIF' )
        self.CreateAnimatedImage( file_path, temp_dir )

    except Exception, ex :
      status[ 'messages' ] = \
          [ 'Error creating image:' + os.linesep + str( ex ) ]
#      et, ev, tb = sys.exc_info()
#      while tb:
#	print >> sys.stderr, '{0:s}File={1:s}, Line={2:s}'.format(
#	    os.linesep,
#            str( tb.tb_frame.f_code ),
#            str( traceback.tb_lineno( tb ) )
#	    )
#        tb = tb.tb_next

    finally:
      shutil.rmtree( status[ 'temp_dir' ] )

    if self.logger.isEnabledFor( logging.INFO ):
      self.logger.info( 'status=%s', str( status ) )
    return  status
  #end _RunBackground


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RunEnd()                           	-
  #----------------------------------------------------------------------
  def _RunEnd( self, result ):
    """
"""
    status = result.get()
    if status is not None:
      status[ 'dialog' ].Destroy()

      messages = status.get( 'messages' )
      if messages is not None and len( messages ) > 0:
        msg = \
	    'Animated GIF not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, 'Save Animated Image', wx.OK_DEFAULT )
    #end if

    self._RestoreState( self.restoreValue )
    #shutil.rmtree( status[ 'temp_dir' ] )
  #end _RunEnd

#end Animator


#------------------------------------------------------------------------
#	CLASS:		AllAxialAnimator				-
#------------------------------------------------------------------------
class AllAxialAnimator( Animator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AllAxialAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoStepUpdate( self ):
    """
Called on the worker thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    axial_level = self.totalSteps - 1 - self.nextStep
    axial_value = self.dmgr.GetAxialValue2( None, all_ndx = axial_level )
    self.widget.UpdateState( axial_value = axial_value )

    while self.widget.axialValue[ 0 ] != axial_value[ 0 ]:
      time.sleep( 0.1 )
  #end _DoStepUpdate


  #----------------------------------------------------------------------
  #	METHOD:		AllAxialAnimator._GetInitValues()		-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
    mesh_values = self.dmgr.GetAxialMeshCenters2( self.curDataSet, 'all' )
    return  len( mesh_values ), self.state.axialValue
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		AllAxialAnimator._RestoreState()		-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    self.widget.UpdateState( axial_value = value )
  #end _RestoreState

#end AllAxialAnimator


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

#    mesh_values = self.dmgr.GetDetectorMesh( self.curDataSet )
    mesh_values = self.dmgr.GetAxialMesh2( self.curDataSet, 'detector' )
    self.totalSteps = len( mesh_values )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Called on the worker thread.
@return			True if there are further steps, False if finished
"""
    axial_level = self.totalSteps - 1 - self.nextStep
    axial_value = self.dmgr.GetAxialValue2( None, detector_ndx = axial_level )
    self.widget.UpdateState( axial_value = axial_value )

    while self.widget.axialValue[ 0 ] != axial_value[ 0 ]:
      time.sleep( 0.1 )
  #end _DoNextStep


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator._GetInitValues()		-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
    mesh_values = self.dmgr.GetAxialMesh2( self.curDataSet, 'detector' )
    return  len( mesh_values ), self.state.axialValue
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator._RestoreState()		-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    self.widget.UpdateState( axial_value = value )
  #end _RestoreState

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
  #	METHOD:		PinAxialAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoStepUpdate( self ):
    """Called on the UI thread.
"""
    axial_level = self.totalSteps - 1 - self.nextStep
    axial_value = self.dmgr.GetAxialValue2( None, pin_ndx = axial_level )
    self.widget.UpdateState( axial_value = axial_value )

    self.logger.debug(
        'nextStep=%d/%d, axial_value=%s',
	self.nextStep, self.totalSteps, str( axial_value )
	)
    while self.widget.axialValue[ 0 ] != axial_value[ 0 ]:
      self.logger.debug( 'value wait' )
      time.sleep( 0.1 )
  #end _DoStepUpdate


  #----------------------------------------------------------------------
  #	METHOD:		PinAxialAnimator._GetInitValues()		-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
    mesh_values = self.dmgr.GetAxialMeshCenters2( self.curDataSet, 'pin' )
    return  len( mesh_values ), self.state.axialValue
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		PinAxialAnimator._RestoreState()		-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    self.widget.UpdateState( axial_value = value )
  #end _RestoreState

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
  #	METHOD:		StatePointAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoStepUpdate( self ):
    """
Called on the worker thread.
@param  w               widget on which to act
@return			True if there are further steps, False if finished
"""
    time_value = self.dmgr.GetTimeIndexValue( self.nextStep, self.curDataSet )
    self.widget.UpdateState( time_value = time_value )

    while self.widget.timeValue != time_value:
      time.sleep( 0.1 )
  #end _DoStepUpdate


  #----------------------------------------------------------------------
  #	METHOD:		StatePointAnimator._GetInitValues()		-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
#    restore_value = \
#        self.dmgr.GetTimeValueIndex( self.state.timeValue, self.curDataSet )
    time_values = self.dmgr.GetTimeValues( self.curDataSet )
    return  len( time_values ), self.state.timeValue
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		StatePointAnimator._RestoreState()		-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    self.widget.UpdateState( time_value = value )
  #end _RestoreState

#end StatePointAnimator
