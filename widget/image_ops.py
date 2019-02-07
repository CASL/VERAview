#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		image_ops.py				        -
#	HISTORY:							-
#		2018-10-02	leerw@ornl.gov				-
#	  Fixing scaling and sizing of images.
#		2017-07-15	leerw@ornl.gov				-
#	  Added CreateImage().  Allow no creation of a ProgressDialog.
#		2015-09-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import glob, math, os, shutil, sys, tempfile
import pdb

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

from .widget import *


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
    self.ncols = kwargs.get( 'cols', -1 )
    self.images = kwargs.get( 'images', [] )
    self.resultPath = kwargs.get( 'result_path', 'montage.png' )
    self.nrows = kwargs.get( 'rows', -1 )

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
      if self.ncols > 0 and self.nrows > 0:
        im_cols = self.ncols
	im_rows = self.nrows

      elif self.ncols > 0:
        im_cols = self.ncols
	im_rows = (len( pil_images ) + self.ncols - 1) / self.ncols

      elif self.nrows > 0:
	im_cols = (len( pil_images ) + self.nrows - 1) / self.nrows
	im_rows = self.nrows

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
  def __init__( self,
      result_path = 'montage.png',
      widgets = [],
      ncols = -1,
      nrows = -1,
      no_dialog = False,
      hilite = False
      ):
    """
    Args:
	result_path (str): path to image file to create
	widgets (list(Widget)): list of widgets to draw
	ncols (int): number of columns, where le 0 means no constraint
	nrows (int): number of rows, where le 0 means no constraint
	no_dialog (bool): True to display no progress dialog
	hilite (bool): True to hilite selections in widgets
"""
    self._hilite = hilite
    self._ncols = ncols
    self._nrows = nrows
    self._no_dialog = no_dialog
    self._result_path = result_path
    self._widgets = widgets

    self._total_steps = (len( widgets ) << 1) + 2
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager.__init__1()			-
  #----------------------------------------------------------------------
##  def __init__1( self, **kwargs ):
##    """
##    Args:
##        **kwargs: keywoard args
##@param  kwargs
##  'cols'		number of columns, where le 0 means no constraint
##  'result_path'		path to image to create, defaults to 'montage.png'
##  'rows'		number of rows, where le 0 means no constraint
##  'widgets'		list of widgets from which to extract images
##  'no_dialog'		defaults to False, if True no progress dialog
##  			is displayed
##  'hilite'		defaults to False, if True hilites are rendered
##"""
##    self.cols = kwargs.get( 'cols', -1 )
##    self.widgets = kwargs.get( 'widgets', [] )
##    self.resultPath = kwargs.get( 'result_path', 'montage.png' )
##    self.rows = kwargs.get( 'rows', -1 )
##    self.noDialog = kwargs.get( 'no_dialog', False )
##    self.hilite = kwargs.get( 'hilite', False )
##
##    self.totalSteps = len( self.widgets ) << 1 + 2
##  #end __init__1


  #----------------------------------------------------------------------
  #	METHOD:		WidgetImageMontager.CreateImage()		-
  #----------------------------------------------------------------------
  def CreateImage( self, dialog, title = 'Create Montage Image' ):
    """Calls _RunBegin() to create the image.
    Args:
        dialog (wx.Dialog): optional progress dialog
	title (str): title for any error message boxes
"""
    self._RunBegin( dialog, title )
  #end CreateImage


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
    if self._no_dialog:
      dialog = None
    else:
      dialog = wx.ProgressDialog(
          title, 'Creating widget images...', self._total_steps
	  )
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
    status = \
        { 'dialog': dialog, 'result_path': self._result_path, 'title': title }
    temp_dir = None

    try:
#			-- Create images
#			--
      temp_dir = tempfile.mkdtemp( '.images', 'veraview' )
      step = 0

      for w in self._widgets:
        name = 'image.%03d.png' % step
	if dialog:
          wx.CallAfter(
	      dialog.Update, step,
	      'Creating widget image %d/%d' % ( step + 1, len( self._widgets ) )
              )
	rname = w.CreatePrintImage(
	    os.path.join( temp_dir, name ),
	    hilite = self._hilite
	    )
	step += 1
      #end for

#			-- Open images to get sizes
#			--
      if dialog:
        wx.CallAfter( dialog.Update, step, 'Creating result image' )
      step += 1

      image_names = sorted( glob.glob( os.path.join( temp_dir, '*.png' ) ) )

      tile_wd, tile_ht = -1, -1
      pil_images = []
      for name in image_names:
	im = PIL.Image.open( name )
	if im is not None:
	  pil_images.append( im )
	  tile_wd = max( tile_wd, im.size[ 0 ] )
	  tile_ht = max( tile_ht, im.size[ 1 ] )
      #end for

#			-- Determine result image size
#			--
      if self._ncols > 0 and self._nrows > 0:
        tile_ncols = self._ncols
	tile_nrows = self._nrows

      elif self._ncols > 0:
        tile_ncols = self._ncols
	tile_nrows = (len( pil_images ) + self._ncols - 1) / self._ncols

      elif self._nrows > 0:
	tile_ncols = (len( pil_images ) + self._nrows - 1) / self._nrows
	tile_nrows = self._nrows

      else:
        tile_ncols = int( math.ceil( math.sqrt( len( pil_images ) ) ) )
	tile_nrows = (len( pil_images ) + tile_ncols - 1) / tile_ncols
      #end if-else

      tile_hgap = tile_vgap = 10
      result_wd = tile_wd * tile_ncols + ((tile_ncols - 1) * tile_hgap)
      result_ht = tile_ht * tile_nrows + ((tile_nrows - 1) * tile_vgap)

#			-- Create result image
#			--
      result_im = PIL.Image.new( 'RGBA', ( result_wd, result_ht ) )

      count = 0
      cur_col, cur_row = 0, 0
      cur_x, cur_y = 0, 0

#			-- Process each tile image
#			--
      for im in pil_images:
	if dialog:
          wx.CallAfter(
	      dialog.Update, step,
	      'Rendering image %d/%d' % ( count, len( pil_images ) )
	      )

	paste_im = im
	im_filter = None
	diff_wd = im.size[ 0 ] - tile_wd
	diff_ht = im.size[ 1 ] - tile_ht
#				-- Must downsize? (shouldn't happen)
#				--
	if diff_wd > 0 or diff_ht > 0:
	  if diff_wd >= diff_ht:
	    new_wd = tile_wd
	    new_ht = im.size[ 1 ] * tile_wd / im.size[ 0 ]
	  else:
	    new_ht = tile_ht
	    new_wd = im.size[ 0 ] * tile_ht / im.size[ 1 ]
	  #paste_im = im.resize( ( new_wd, new_ht ), PIL.Image.ANTIALIAS )
	  if ( new_wd, new_ht ) != im.size:
	    im_filter = PIL.Image.ANTIALIAS

	elif diff_wd < 0 or diff_ht < 0:
	  if diff_wd <= diff_ht:
	    new_ht = tile_ht
	    new_wd = im.size[ 0 ] * tile_ht / im.size[ 1 ]
	  else:
	    new_wd = tile_wd
	    new_ht = im.size[ 1 ] * tile_wd / im.size[ 0 ]
	  #paste_im = im.resize( ( new_wd, new_ht ), PIL.Image.BICUBIC )
	  if ( new_wd, new_ht ) != im.size:
	    im_filter = PIL.Image.BICUBIC

	if im_filter is not None:
	  paste_im = im.resize( ( new_wd, new_ht ), im_filter )

	result_im.paste( paste_im, ( cur_x, cur_y ) )
	count += 1
	step += 1

	cur_col += 1
	if cur_col >= tile_ncols:
	  cur_col, cur_x = 0, 0
	  cur_row += 1
	  cur_y += tile_ht + tile_vgap
        else:
	  cur_x += tile_wd + tile_hgap
      #for images

      if dialog:
        wx.CallAfter( dialog.Update, step, 'Saving result image' )
      result_im.save( self._result_path, 'PNG' )

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
      dialog = status.get( 'dialog' )
      if dialog:
        dialog.Destroy()

      messages = status.get( 'messages' )
      if messages is not None and len( messages ) > 0:
        msg = \
	    'Montage image not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, status[ 'title' ], wx.OK_DEFAULT )
    #end if
  #end _RunEnd

#end WidgetImageMontager
