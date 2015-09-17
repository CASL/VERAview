#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		image_ops.py				        -
#	HISTORY:							-
#		2015-09-17	leerw@ornl.gov				-
#------------------------------------------------------------------------
import math, os, sys
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
    self.totalSteps = len( self.images ) + 2
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
	if im != None:
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
    if status != None:
      status[ 'dialog' ].Destroy()

      messages = status.get( 'messages' )
      if messages != None and len( messages ) > 0:
        msg = \
	    'Montage image not created:\n' + \
            '\n '.join( messages )
        wx.MessageBox( msg, status[ 'title' ], wx.OK_DEFAULT )
    #end if
  #end _RunEnd

#end ImageMontager
