#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		crud_synth.py					-
#	HISTORY:							-
#		2017-06-12	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, math, os, re, sys, traceback
import numpy as np
import pdb

#sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.utils import *

PATTERN_ws = re.compile( '[\s,]+' )


#------------------------------------------------------------------------
#	CLASS:		CrudSynthesizer					-
#------------------------------------------------------------------------
class CrudSynthesizer( object ):
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
    self.Run( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self ):
    self.logger = logging.getLogger( 'data' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_ReadFile()					-
  #----------------------------------------------------------------------
  def _ReadFile( self, fp ):
    """
"""
    nax = n = 0
    mesh = None
#		-- First line has N and nax
#		--
    line = fp.readline()
    if line:
      tokens = PATTERN_ws.split( line.rstrip( '\r\n' ).lstrip( ' \t' ) )
      if len( tokens ) >= 2:
        n = int( tokens[ 0 ] )
        nax = int( tokens[ 1 ] )

#		-- Second line is mesh
#		--
    line = fp.readline()
    if line:
      tokens = PATTERN_ws.split( line.rstrip( '\r\n' ).lstrip( ' \t' ) )
      if len( tokens ) >= nax:
        mesh_list = [ float( tokens[ j ] ) for j in xrange( nax ) ]
	mesh = np.array( mesh_list, dtype = np.float64 )

#		-- Remaining lines are data
#		--
    data = np.zeros( ( nax, n ), dtype = np.float64 )
    z = 0
    line = fp.readline()
    while line and z < nax:
      tokens = PATTERN_ws.split( line.rstrip( '\r\n' ).lstrip( ' \t' ) )
      if len( tokens ) >= n:
        data[ z ] = [ float( tokens[ j ] ) for j in xrange( n ) ]

      line = fp.readline()
      z += 1
    #end while line

#		-- Return results, data[ z, n ]
#		--
    rec = { 'data': data, 'mesh': mesh, 'n': n, 'nax': nax }
    return  rec
  #end _ReadFile


  #----------------------------------------------------------------------
  #	METHOD:		Run()						-
  #----------------------------------------------------------------------
  def Run( self, temp_path, thick_path, output_path ):
    """
"""
    temp_fp = file( temp_path, 'r' )
    thick_fp = file( thick_path, 'r' )
    out_fp = h5py.File( output_path, 'w' )

    try:
      temp_rec = self._ReadFile( temp_fp )
      nth = temp_rec.get( 'n', 1 )

      thick_rec = self._ReadFile( thick_fp )
      nr = thick_rec.get( 'n', 1 )
#      r_incr = 1.26 / nr
#      r = [ i * r_incr for i in xrange( nr ) ]

#		-- Assert on equal axial meshes
#		--
      temp_mesh = temp_rec.get( 'mesh' )
      thick_mesh = thick_rec.get( 'mesh' )
      assert temp_mesh is not None and thick_mesh is not None, \
          'Axial_mesh missing!'
      assert np.array_equal( temp_mesh, thick_mesh ), \
          'Incompatible files, axial_mesh mismatch!'

      nax = temp_mesh.shape[ 0 ]

#		-- Create CORE
#		--
      out_core = out_fp.create_group( 'CORE' )
      out_core.create_dataset( 'apitch', data = 1.25 )
      out_core.create_dataset( 'axial_mesh', data = temp_mesh )
      out_core.create_dataset(
          'core_map',
	  data = np.ones( ( 1, 1 ), dtype = np.int32 )
	  )
      out_core.create_dataset( 'core_sym', data = 1 )
      out_core.create_dataset( 'nsubr', data = nr )
      out_core.create_dataset( 'nsubtheta', data = nth )
      out_core.create_dataset(
          'pin_volumes',
	  data = np.ones( ( 1, 1, nax - 1, 1 ), dtype = np.float64 )
	  )

#		-- Create STATE_0001
#		--
      out_st = out_fp.create_group( 'STATE_0001' )

      out_st.create_dataset(
          'pin_powers',
	  data = np.ones( ( 1, 1, nax - 1, 1 ), dtype = np.float64 )
	  )

      data = np.zeros( ( nth, 1, 1, nax - 1, 1 ), dtype = np.float64 )
      temp_data = temp_rec.get( 'data' )
      for z in xrange( nax - 1 ):
        data[ :, 0, 0, z, 0 ] = temp_data[ z ]
      out_st.create_dataset( 'temperature', data = data )

      data = np.zeros( ( nr, 1, 1, nax - 1, 1 ), dtype = np.float64 )
      temp_data = thick_rec.get( 'data' )
      for z in xrange( nax - 1 ):
        data[ :, 0, 0, z, 0 ] = temp_data[ z ]
      out_st.create_dataset( 'thickness', data = data )

    finally:
      out_fp.close()
      temp_fp.close()
      thick_fp.close()
  #end Run


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

      parser.add_argument(
	  '-k', '--thickness-file',
	  help = 'thickness file',
	  required = True,
	  type = extant_file
          )
      parser.add_argument(
	  '-t', '--temp-file',
	  help = 'temperature file',
	  required = True,
	  type = extant_file
          )
      parser.add_argument(
	  '-o', '--output-file',
	  default = 'out.h5',
	  help = 'path to output HDF5 file'
          )
      args = parser.parse_args()

      obj = CrudSynthesizer()
      obj( args.temp_file, args.thickness_file, args.output_file )

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

#end CrudSynthesizer


#------------------------------------------------------------------------
#	NAME:		__main__					-
#------------------------------------------------------------------------
if __name__ == '__main__':
  CrudSynthesizer.main()
