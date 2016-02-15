#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		image_ops.py				        -
#	HISTORY:							-
#		2015-09-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import glob, math, os, shutil, sys, tempfile
#import pdb

try:
  import wx
  import wx.lib.delayedresult as wxlibdr
except Exception:
  raise ImportError( "The wxPython module is required" )

try:
#  import PIL.Image, PIL.ImageDraw, PIL.ImageFont
  import PIL.Image
except Exception:
  raise ImportError, 'The Python Imaging Library (PIL) is required for this component'

from widget import *


#------------------------------------------------------------------------
#	CLASS:		ImageMontager					-
#------------------------------------------------------------------------
class ImageMontager( object ):
  """Creates threads with a ProgressDialog to create an image montage.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ImageMontager.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, **kwargs ):
    """
@param  kwargs
  'cols'		number of columns, where le 0 means no constraint
  'images'		list of images, defaults to empty
  'result_path'		path to image to create, defaults to 'montage.png'
  'rows'		number of rows, where le 0 means no constraint
"""
    self.cols = kwargs.get( 'cols', -1 )
    self.images = kwargs.get( 'images', [] )
    self.resultPath = kwargs.get( 'result_path', 'montage.png' )
    self.rows = kwargs.get( 'rows', -1 )

    self.nextStep = 0
    self.totalSteps = len( self.images ) << 1 + 2
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ImageMontager.Run()                           	-
  #----------------------------------------------------------------------
  def Run( self, title = 'Save Image Montage' ):
    """
Must be called from the UI event thread.
Creates a separate thread with the _Run() method as target.
@param  file_path	path to gif file to create
@return			thread that was started
"""
    dialog = wx.ProgressDialog( title, 'Loading images...', self.totalSteps )
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBegin,
	wargs = [ dialog, title ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		ImageMontager._RunBegin()			-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog, title ):
    """
"""
    status = { 'dialog': dialog, 'result_path': self.resultPath, 'title': title }

    try:
#			-- Open images to get sizes
#			--
      im_wd, im_ht = -1, -1
      pil_images = []
      for name in self.images:
	im = PIL.Image.open( name )
	if im is not None:
	  pil_images.append( im )
	  im_wd = max( im_wd, im.size[ 0 ] )
	  im_ht = max( im_ht, im.size[ 1 ] )
      #end for

#			-- Determine result image size
#			--
      if self.cols > 0 and self.rows > 0:
        im_cols = self.cols
	im_rows = self.rows

      elif self.cols > 0:
        im_cols = self.cols
	im_rows = (len( pil_images ) + self.cols - 1) / self.cols

      elif self.rows > 0:
	im_cols = (len( pil_images ) + self.rows - 1) / self.rows
	im_rows = self.rows

      else:
        im_cols = int( math.ceil( math.sqrt( len( pil_images ) ) ) )
	im_rows = (len( pil_images ) + im_cols - 1) / im_cols
      #end if-else

      result_wd = im_wd * im_cols + ((im_cols - 1) * 10)
      result_ht = im_ht * im_rows + ((im_rows - 1) * 10)

#			-- Create result image
#			--
      result_im = Image.new( 'RGBA', ( result_wd, result_ht ) )

      wx.CallAfter(
	  dialog.Update, 1,
	  'Processing image %d/%d' % ( 1, len( pil_images ) )
          )

      count = 1
      cur_col, cur_row = 0, 0
      cur_x, cur_y = 0, 0

      for im in pil_images:
        wx.CallAfter(
	    dialog.Update, count,
	    'Processing image %d/%d' % ( count, len( pil_images ) )
	    )

	result_im.paste( im, ( cur_x, cur_y ) )
	count += 1

	cur_col += 1
	if cur_col >= im_cols:
	  cur_col, cur_x = 0, 0
	  cur_row += 1
	  cur_y += im_ht + 10
        else:
	  cur_x += im_wd + 10
      #for images

      wx.CallAfter( dialog.Update, count, 'Saving result image' )
      result_im.save( self.resultPath, 'PNG' )

    except Exception, ex :
      status[ 'messages' ] = \
          [ 'Error creating image:' + os.linesep + str( ex ) ]

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		ImageMontager._RunEnd()				-
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
	    'Montage image not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, status[ 'title' ], wx.OK_DEFAULT )
    #end if
  #end _RunEnd

#end ImageMontager


#------------------------------------------------------------------------
#	CLASS:		WidgetImageMontager				-
#------------------------------------------------------------------------
class WidgetImageMontager( object ):
  """Creates threads with a ProgressDialog to create an image montage.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, **kwargs ):
    """
@param  kwargs
  'cols'		number of columns, where le 0 means no constraint
  'result_path'		path to image to create, defaults to 'montage.png'
  'rows'		number of rows, where le 0 means no constraint
  'widgets'		list of widgets from which to extract images
"""
    self.cols = kwargs.get( 'cols', -1 )
    self.widgets = kwargs.get( 'widgets', [] )
    self.resultPath = kwargs.get( 'result_path', 'montage.png' )
    self.rows = kwargs.get( 'rows', -1 )

    self.totalSteps = len( self.widgets ) << 1 + 2
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager.Run()			-
  #----------------------------------------------------------------------
  def Run( self, title = 'Save Image Montage' ):
    """
Must be called from the UI event thread.
Creates a separate thread with the _Run() method as target.
@param  file_path	path to gif file to create
@return			thread that was started
"""
    dialog = \
        wx.ProgressDialog( title, 'Creating widget images...', self.totalSteps )
    dialog.Show()

    wxlibdr.startWorker(
	self._RunEnd,
	self._RunBegin,
	wargs = [ dialog, title ]
        )
  #end Run


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager._RunBegin()			-
  #----------------------------------------------------------------------
  def _RunBegin( self, dialog, title ):
    """
"""
    status = { 'dialog': dialog, 'result_path': self.resultPath, 'title': title }

    temp_dir = None

    try:
#			-- Create images
#			--
      temp_dir = tempfile.mkdtemp( '.images', 'veraview' )
      step = 0

      for w in self.widgets:
        name = 'image.%03d.png' % step
        wx.CallAfter(
	    dialog.Update, step,
	    'Creating widget image %d/%d' % ( step + 1, len( self.widgets ) )
            )
	rname = w.CreatePrintImage( os.path.join( temp_dir, name ) )
	step += 1
      #end for


#			-- Open images to get sizes
#			--
      wx.CallAfter( dialog.Update, step, 'Creating result image' )
      step += 1

      image_names = sorted( glob.glob( os.path.join( temp_dir, '*.png' ) ) )

      im_wd, im_ht = -1, -1
      pil_images = []
      for name in image_names:
	im = PIL.Image.open( name )
	if im is not None:
	  pil_images.append( im )
	  im_wd = max( im_wd, im.size[ 0 ] )
	  im_ht = max( im_ht, im.size[ 1 ] )
      #end for

#			-- Determine result image size
#			--
      if self.cols > 0 and self.rows > 0:
        im_cols = self.cols
	im_rows = self.rows

      elif self.cols > 0:
        im_cols = self.cols
	im_rows = (len( pil_images ) + self.cols - 1) / self.cols

      elif self.rows > 0:
	im_cols = (len( pil_images ) + self.rows - 1) / self.rows
	im_rows = self.rows

      else:
        im_cols = int( math.ceil( math.sqrt( len( pil_images ) ) ) )
	im_rows = (len( pil_images ) + im_cols - 1) / im_cols
      #end if-else

      result_wd = im_wd * im_cols + ((im_cols - 1) * 10)
      result_ht = im_ht * im_rows + ((im_rows - 1) * 10)

#			-- Create result image
#			--
      result_im = PIL.Image.new( 'RGBA', ( result_wd, result_ht ) )

      count = 0
      cur_col, cur_row = 0, 0
      cur_x, cur_y = 0, 0

      for im in pil_images:
        wx.CallAfter(
	    dialog.Update, step,
	    'Rendering image %d/%d' % ( count, len( pil_images ) )
	    )

	paste_im = im
	if im.size[ 0 ] != im_wd or im.size[ 1 ] != im_ht:
	  paste_im = im.resize( ( im_wd, im_ht ) )

	result_im.paste( paste_im, ( cur_x, cur_y ) )
	count += 1
	step += 1

	cur_col += 1
	if cur_col >= im_cols:
	  cur_col, cur_x = 0, 0
	  cur_row += 1
	  cur_y += im_ht + 10
        else:
	  cur_x += im_wd + 10
      #for images

      wx.CallAfter( dialog.Update, step, 'Saving result image' )
      result_im.save( self.resultPath, 'PNG' )

    except Exception, ex :
      status[ 'messages' ] = \
          [ 'Error creating image:' + os.linesep + str( ex ) ]

    finally:
      if temp_dir is not None:
        shutil.rmtree( temp_dir )

    return  status
  #end _RunBegin


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager._RunEnd()			-
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
	    'Montage image not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, status[ 'title' ], wx.OK_DEFAULT )
    #end if
  #end _RunEnd

#end WidgetImageMontager
