#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		intrapin_edits_attrs.py				-
#	HISTORY:							-
#		2018-10-01	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, math, os, re, shutil, sys, traceback
import numpy as np
import pdb

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), os.pardir ) )

from .utils import *

PATTERN_ws = re.compile( '[\s,]+' )


#------------------------------------------------------------------------
#	CLASS:		IntraPinEditsAttrs				-
#------------------------------------------------------------------------
class IntraPinEditsAttrs( object ):
  """
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    """Calls Run().
"""
    self.run( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self ):
    """
"""
    formatter = logging.Formatter( '[IntraPinEditsAttrs] %(message)s' )
    handler = logging.StreamHandler( sys.stderr )
    handler.setFormatter( formatter )
    handler.setLevel( logging.DEBUG )
    self._logger = logging.getLogger()
    self._logger.addHandler( handler )
    self._logger.setLevel( logging.INFO )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		process_group()					-
  #----------------------------------------------------------------------
  def process_group(
      self, group, start_name, count_name,
      match_list = None, match_regex = None
      ):
    """
    Args:
        group (h5py.Group): group to search for datasets to tag
	start_name (str): start index dataset name, which must exist in
	    ``group``
	count_name (str): count dataset name, which must exist in ``group``
	match_list (list): list of dataset names to tag
	match_regex (re): regex to apply to get match names
"""
#		-- Index datasets must exist
#		--
    self._logger.info( 'processing %s', group.name )
    if start_name in group and count_name in group and \
        (match_list or match_regex):
      for k in group.keys():
	matched = False
	if k == start_name or k == count_name:
	  pass
	elif match_list and k in match_list:
	  matched = True
	  self._logger.info( '%s in list', k )
	elif match_regex and match_regex.search( k ):
	  matched = True
	  self._logger.info( '%s matches regex', k )

        if matched:
	  dset = group.get( k )
	  dset.attrs.create( 'region_start_index', start_name )
	  dset.attrs.create( 'region_count_index', count_name )
    #end if start_name in group and count_name in group
  #end process_group


  #----------------------------------------------------------------------
  #	METHOD:		run()						-
  #----------------------------------------------------------------------
  def run( self, veraout, **kwargs ):
    """
    Args:
        veraout (str): path to veraout file to edit
	**kwargs: keyword params
	    'count_dataset': required name of region count dataset
	    'datasets': optional list of datasets to tag with attributes
	    'datasets_re': optional regex for datasets to tag with attributes
	    'start_dataset': required name of region start index dataset
"""
#		-- Assert
#		--
    assert 'count_dataset' in kwargs and 'start_dataset' in kwargs, \
        'Params "count_dataset" and "start_dataset" required'
    assert 'datasets' in kwargs or 'datasets_re' in kwargs, \
        'One of "datasets" and "datasets_re" required'

#		-- Copy file
#		--
    veraout_bup = veraout + '.backup'
    shutil.copy( veraout, veraout_bup )

    start_name = kwargs.get( 'start_dataset' )
    count_name = kwargs.get( 'count_dataset' )

    match_list = kwargs.get( 'datasets' )
    match_regex = None
    if 'datasets_re' in kwargs:
      match_regex = re.compile( kwargs.get( 'datasets_re' ) )

#		-- Open file and process each state
#		--
    fp = h5py.File( veraout, 'r+' )
    try:
      state_ndx = 1
      found = True
      while found:
        state_name = 'STATE_{0:04d}'.format( state_ndx )
        found = state_name in fp
        if found:
          self.process_group(
	      fp.get( state_name ),
	      start_name, count_name,
	      match_list, match_regex
	      )
          state_ndx += 1
      #end while found
    finally:
      fp.flush()
  #end run


#		-- Properties
#		--

  logger = property( lambda x: x._logger )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		main()						-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    """
"""
    from data.config import Config
    def extant_file( f ):
      if not os.path.exists( f ):
        raise argparse.ArgumentTypeError( '{0} not found'.format( f ) )
      return  f
    #end extant_file

    try:
      parser = argparse.ArgumentParser()
      group = parser.add_mutually_exclusive_group()

      parser.add_argument(
	  '-c', '--count', '--region-count-dataset',
	  dest = 'count_dataset',
	  help = 'region count dataset',
	  required = True
          )
      group.add_argument(
	  '-d', '--datasets',
	  dest = 'datasets',
	  help = 'datasets to which to add attributes',
	  nargs = '+'
          )
      group.add_argument(
	  '-r', '--datasets-re',
	  dest = 'datasets_re',
	  help = 'regular expression to match dataset names'
          )
      parser.add_argument(
	  '-s', '--start', '--region-start-dataset',
	  dest = 'start_dataset',
	  help = 'region start dataset',
	  required = True
          )

      parser.add_argument(
	  'veraout',
	  help = 'VERAOut file to modify',
	  type = extant_file
          )
      args = parser.parse_args()

      kwargs = dict(
	  count_dataset = args.count_dataset,
	  start_dataset = args.start_dataset
          )
      if args.datasets_re:
        kwargs[ 'datasets_re' ] = args.datasets_re
      else:
        kwargs[ 'datasets' ] = args.datasets

      IntraPinEditsAttrs()( args.veraout, **kwargs )

    except Exception, ex:
      msg = str( ex )
      print >> sys.stderr, msg
      et, ev, tb = sys.exc_info()
      while tb:
        print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
      logging.error( msg )
  #end main

#end IntraPinEditsAttrs


#------------------------------------------------------------------------
#	NAME:		__main__					-
#------------------------------------------------------------------------
if __name__ == '__main__':
  IntraPinEditsAttrs.main()
