#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		animators.py				        -
#	HISTORY:							-
#		2018-08-16	leerw@ornl.gov				-
#	  Working around wxPython ProgressDialog and GenericProgressDialog
#	  bugginess under Windows.
#		2018-06-19	leerw@ornl.gov				-
#	  Fixed logic for canceling/aborting animation.
#		2018-05-05	leerw@ornl.gov				-
#	  Created BaseAxialAnimator, with {Detector,Pin,SubPin,Tally}Xxx
#	  extensions.
#		2018-02-01	leerw@ornl.gov				-
#	  Sorting all glob.glob() results. !!
#		2017-10-10	leerw@ornl.gov				-
#	  Axial animations from the bottom up.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
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
import glob, inspect, logging, os, platform, shutil, six, subprocess, sys, \
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
    fnames = sorted( glob.glob( os.path.join( temp_dir, '*.png' ) ) )
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

#        [ 'gifsicle', '--disposal=background', '--delay=50', '--loop' ]
    args = \
        [ 'gifsicle', '--disposal=background', '--delay=10' ] + \
        sorted( glob.glob( os.path.join( temp_dir, '*.gif' ) ) ) + \
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
  def _CreateStepImage( self, dialog, fpath, show_selections = False ):
    """Must be called on the UI thread.
"""
    pct = int( self.nextStep * 100.0 / (self.totalSteps + 1) )
    msg = 'Creating frame %d/%d' % ( (self.nextStep + 1), self.totalSteps )
    self.logger.info( msg )

    #cancelled, skipped = dialog.Update( pct, msg )
    cancelled = dialog.WasCancelled()
    pair = dialog.Update( pct, msg )
    six.print_(
        '[Animator._CreateStepImage] cancelled={0}'.format( cancelled ),
	file = sys.stderr
	)
    dialog.Fit()

    if not cancelled:
      if self.callback:
        self.callback( self.nextStep + 1, self.totalSteps, msg )

      self._DoStepUpdate()
      while self.widget.IsBusy():
	self.logger.debug( 'widget.IsBusy wait' )
        wx.Yield()

      self.widget.CreatePrintImage( fpath, hilite = show_selections )

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
  def Run( self, file_path, show_selections = False ):
    """
Must be called from the UI event thread.
Creates a worker thread with the _RunBegin() and _Runend() methods.
@param  file_path	path to gif file to create
"""
    
    if Config.IsWindows():
      dialog = wx.GenericProgressDialog(
	  'Save Animated Image',
	  'Initializing...',
	  style = wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
          )
    else:
      dialog = wx.ProgressDialog(
	  'Save Animated Image',
	  'Initializing...',
	  style = wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT
          )
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBackground,
	wargs = [ dialog, file_path, show_selections ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		Animator._RunBackground()			-
  #----------------------------------------------------------------------
  def _RunBackground( self, dialog, file_path, show_selections ):
    """
"""
    temp_dir = tempfile.mkdtemp( '.animation' )
    status = { 'dialog': dialog, 'file_path': file_path, 'temp_dir': temp_dir }

    try:
      self.nextStep = 0
      while not dialog.WasCancelled() and self.nextStep < self.totalSteps:
        wait_for_step = self.nextStep + 1
	fpath = os.path.join( temp_dir, '{0:04d}.png'.format( self.nextStep ) )
	wx.CallAfter( self._CreateStepImage, dialog, fpath, show_selections )

	blocking = True
	while blocking:
	  time.sleep( 0.25 )  # 0.1
	  self.stepLock.acquire()
	  try:
	    blocking = self.nextStep < wait_for_step
	  finally:
	    self.stepLock.release()
	#end while blocking

        six.print_(
	    '[Animator._RunBackground] wasCancelled=%s',
	    str( dialog.WasCancelled() ),
	    file = sys.stderr
	    )
      #end while stepping

      if dialog.WasCancelled() or self.nextStep > self.totalSteps:
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
    #axial_level = self.totalSteps - 1 - self.nextStep
    axial_level = self.nextStep
    axial_value = self.dmgr.GetAxialValue( None, all_ndx = axial_level )
    self.widget.UpdateState( axial_value = axial_value )

    while self.widget.axialValue.cm != axial_value.cm:
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
#	CLASS:		BaseAxialAnimator				-
#------------------------------------------------------------------------
class BaseAxialAnimator( Animator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		BaseAxialAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, axial_name, axial_ndx_name, **kwargs ):
    """Subclasses must set self.restoreValue and self.totalSteps.
@param  widget_in	Widget from which to get images, cannot be None
@param  axial_name	name of axial mesh ('all, 'detector',
			'fixed_detector', 'pin'/'core', 'subpin', 'tally')
@param  axial_ndx_name	index name ('cm'/'value', 'core_ndx'/'pin_ndx', etc.)
@param  centers		True to use mesh centers, False for mesh values
@param  kwargs
  'callback'		optional reference to callback callable on progress
  			that will be called on the UI thread
"""
    self.axialName = axial_name
    self.indexName = axial_ndx_name

    # Why does super() fail here, confused about __init__() signature ???
    #super( Animator, self ).__init__( widget_in, **kwargs )
    Animator.__init__( self, widget_in, **kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		BaseAxialAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoStepUpdate( self ):
    """Called on the UI thread.
"""
    #axial_level = self.totalSteps - 1 - self.nextStep
    axial_level = self.nextStep
    ax_args = { self.indexName: axial_level }
    axial_value = self.dmgr.GetAxialValue( None, **ax_args )
    self.widget.UpdateState( axial_value = axial_value )

    self.logger.debug(
        'nextStep=%d/%d, axial_value=%s',
	self.nextStep, self.totalSteps, str( axial_value )
	)
    while self.widget.axialValue.cm != axial_value.cm:
      self.logger.debug( 'value wait' )
      time.sleep( 0.1 )
  #end _DoStepUpdate


  #----------------------------------------------------------------------
  #	METHOD:		BaseAxialAnimator._GetInitValues()		-
  #----------------------------------------------------------------------
  def _GetInitValues( self ):
    """Subclasses must override.
@return			( total_steps, restore_value )
"""
    mesh_values = \
        self.dmgr.GetAxialMeshCenters2( self.curDataSet, self.axialName )
    return  len( mesh_values ), self.state.axialValue
  #end _GetInitValues


  #----------------------------------------------------------------------
  #	METHOD:		BaseAxialAnimator._RestoreState()		-
  #----------------------------------------------------------------------
  def _RestoreState( self, value ):
    """Subclasses must override, called in the UI thread.
@param  value		will always be self.restoreValue
"""
    self.widget.UpdateState( axial_value = value )
  #end _RestoreState

#end BaseAxialAnimator


#------------------------------------------------------------------------
#	CLASS:		DetectorAxialAnimator				-
#------------------------------------------------------------------------
class DetectorAxialAnimator( BaseAxialAnimator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator.__init__()		-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( DetectorAxialAnimator, self ).__init__(
        widget_in, 'detector', 'detector_ndx', **kwargs
	)
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DetectorAxialAnimator._DoStepUpdate()		-
  #----------------------------------------------------------------------
  def _DoNextStep( self ):
    """
Called on the worker thread.
@return			True if there are further steps, False if finished
"""
    #axial_level = self.totalSteps - 1 - self.nextStep
    axial_level = self.nextStep
    axial_value = self.dmgr.GetAxialValue( None, detector_ndx = axial_level )
    self.widget.UpdateState( axial_value = axial_value )

    while self.widget.axialValue.cm != axial_value.cm:
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

#end DetectorAxialAnimator


#------------------------------------------------------------------------
#	CLASS:		PinAxialAnimator				-
#------------------------------------------------------------------------
class PinAxialAnimator( BaseAxialAnimator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PinAxialAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( PinAxialAnimator, self ).__init__(
        widget_in, 'pin', 'pin_ndx', **kwargs
	)
  #end __init__

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


#------------------------------------------------------------------------
#	CLASS:		SubPinAxialAnimator				-
#------------------------------------------------------------------------
class SubPinAxialAnimator( BaseAxialAnimator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		SubPinAxialAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( SubPinAxialAnimator, self ).__init__(
        widget_in, 'subpin', 'subpin_ndx', **kwargs
	)
  #end __init__

#end SubPinAxialAnimator


#------------------------------------------------------------------------
#	CLASS:		TallyAxialAnimator				-
#------------------------------------------------------------------------
class TallyAxialAnimator( BaseAxialAnimator ):
  """Animator interface
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		TallyAxialAnimator.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, widget_in, **kwargs ):
    super( TallyAxialAnimator, self ).__init__(
        widget_in, 'tally', 'tally_ndx', **kwargs
	)
  #end __init__

#end TallyAxialAnimator
