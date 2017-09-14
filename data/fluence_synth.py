#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		fluence_synth.py				-
#	HISTORY:							-
#		2017-05-13	leerw@ornl.gov				-
#	  No longer creating 'binned_total' and 'total' datasets.
#		2017-04-25	leerw@ornl.gov				-
#	  Copying new vessel geometry datasets from shift output file.
#		2017-04-11	leerw@ornl.gov				-
#	  Bug fixes from Tara Pandya.
#		2017-04-10	leerw@ornl.gov				-
#	  Added relative error calculation described by Tara Pandya.
#		2017-04-01	leerw@ornl.gov				-
#	  Reading the "binned" dataset.
#		2017-03-31	leerw@ornl.gov				-
#	  Converted to a nice class.
#		2017-03-29	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, math, os, sys, traceback
import numpy as np
import pdb

#sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )
#sys.path.insert( 0, VVDIR )

from data.utils import *


DEF_barrel_outer_cm = 193.68
DEF_liner_inner_cm = 219.15
DEF_liner_outer_cm = 219.71
DEF_vessel_outer_ring_cm = 241.70

TALLY_CORE_DS_NAMES = (
    'description',
    'mesh_r', 'mesh_stat', 'mesh_theta', 'mesh_z',
    'multiplier_descs', 'multiplier_names', 'volumes'
    )

VESSEL_GEOM_DS_NAMES = (
    'baffle_gap_inner', 'baffle_inner_radius', 'baffle_outer_radius',
    'barrel_inner_radius', 'barrel_outer_radius',
    'liner_inner_radius', 'liner_outer_radius',
    'pad_angles', 'pad_arc',
    'pad_inner_radius', 'pad_outer_radius',
    'vessel_inner_radius', 'vessel_outer_radius'
    )


#------------------------------------------------------------------------
#	CLASS:		FluenceSynthesizer				-
#------------------------------------------------------------------------
class FluenceSynthesizer( object ):
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
  #	METHOD:		Run()						-
  #----------------------------------------------------------------------
  def Run( self, mpact_path, shift_path, output_path ):
    """
"""
    mpact_fp = h5py.File( mpact_path, 'r' )
    shift_fp = h5py.File( shift_path, 'r' )
    out_fp = h5py.File( output_path, 'w' )

    try:
#		-- MPACT CORE
      mpact_core_grp = mpact_fp.get( 'CORE' )
      assert mpact_core_grp is not None, \
          'CORE not found in "%s"' % mpact_fp.filename

#		-- MPACT STATE_0001
      mpact_st_grp = mpact_fp.get( 'STATE_0001' )
      assert mpact_st_grp is not None, \
          'STATE_0001 not found in "%s"' % mpact_fp.filename

#		-- MPACT STATE_0001/exposure_efpd
      exposure_secs = None
      dset = mpact_st_grp.get( 'exposure_efpd' )
      if dset is not None:
        value = dset[ () ]  if len( dset.shape ) == 0 else  dset[ 0 ]
        exposure_secs = value * 86400.0

      assert exposure_secs is not None, \
          'STATE_0001/exposure_efpd not found in "%s"' % mpact_fp.filename

#		-- Shift STATE_0001/vessel_tally
      shift_tally_grp = shift_fp.get( 'STATE_0001/vessel_tally' )
      assert shift_tally_grp is not None, \
          'STATE_0001/vessel_tally not found in "%s"' % shift_fp.filename

#		-- Shift STATE_0001/vessel_tally/{binned,total}
      binned_data = total_data = None
      if shift_tally_grp is not None:
        dset = shift_tally_grp.get( 'binned' )
	if dset is not None:
          binned_data = np.sum( np.array( dset ), axis = 0 )
        dset = shift_tally_grp.get( 'total' )
	if dset is not None:
          total_data = np.array( dset )
      #end if shift_tally_grp

      assert total_data is not None, \
          'STATE_0001/vessel_tally/total not found in "%s"' % shift_fp.filename

#		-- Determine mesh_r water range
#		--
      shift_tally_grp = shift_fp.get( 'STATE_0001/vessel_tally' )
      dset = shift_tally_grp.get( 'mesh_r' )
      assert dset is not None, \
          'STATE_0001/vessel_tally/mesh_r not found in "%s"' % shift_fp.filename

      r_data = np.array( dset )
      water_st_ndx = min(
          DataUtils.FindListIndex( r_data, DEF_barrel_outer_cm ) + 1,
	  len( r_data ) - 1
	  )
      water_en_ndx = min(
          DataUtils.FindListIndex( r_data, DEF_liner_inner_cm ) + 1,
	  len( r_data )
	  )
      water_range_expr = '[ :, :, %d : %d, :, : ]' % \
          ( water_st_ndx, water_en_ndx )

#		-- Copy MPACT CORE
#		--
      out_core_grp = out_fp.create_group( 'CORE' )
      for name in mpact_core_grp:
        dset = out_core_grp.\
            create_dataset( name, data = mpact_core_grp.get( name ) )

#		-- Copy SHIFT vessel_tally to CORE
#		--
      out_talley_grp = out_core_grp.create_group( 'vessel_tally' )
      for name in TALLY_CORE_DS_NAMES:
        if name in shift_tally_grp:
	  dset = out_talley_grp.\
	      create_dataset( name, data = shift_tally_grp.get( name ) )
      #end for name

#		-- Copy SHIFT CORE vessel geometry to CORE/vessel_tally
#		--
      shift_core_grp = shift_fp.get( 'CORE' )
      for name in VESSEL_GEOM_DS_NAMES:
        if name in shift_core_grp:
	  dset = out_talley_grp.\
	      create_dataset( name, data = shift_core_grp.get( name ) )
      #end for name

#		-- Initialize
#		--
      prev_exposure_secs = exposure_secs
      accum_binned_fluence_data = \
          np.zeros( total_data.shape, dtype = np.float64 )
      accum_binned_fluence_var_data = \
          np.zeros( total_data.shape, dtype = np.float64 )
      accum_fluence_data = np.zeros( total_data.shape, dtype = np.float64 )
      accum_fluence_var_data = np.zeros( total_data.shape, dtype = np.float64 )

      prev_shift_tally_grp = shift_tally_grp

      state_ndx = 1
      while state_ndx > 0:
        state_name = 'STATE_%04d' % state_ndx
        mpact_st_grp = mpact_fp.get( state_name )
        if mpact_st_grp is None:
          state_ndx = -1

        else:
          out_st_grp = out_fp.create_group( state_name )

	  exposure_secs = None
          for name in mpact_st_grp:
            dset = out_st_grp.\
	        create_dataset( name, data = mpact_st_grp.get( name ) )
	    if name == 'exposure_efpd':
	      exposure_efpd = \
	          dset[ () ]  if len( dset.shape ) == 0 else  dset[ 0 ]
	      exposure_secs = exposure_efpd * 86400.0
          #end for name
#			-- Assert on exposure_efpd
#			--
	  assert exposure_secs is not None, \
	      '%s/exposure_efpd not found in "%s"' % \
	      ( state_name, mpact_fp.filename )

	  out_tally_grp = out_st_grp.create_group( 'vessel_tally' )

	  binned_fluence_incr = fluence_incr = \
	  binned_fluence_var_incr = fluence_var_incr = \
	  None

          tally_name = state_name + '/vessel_tally'
	  shift_tally_grp = shift_fp.get( tally_name )
	  if shift_tally_grp is None:
	    shift_tally_grp = prev_shift_tally_grp

          #out_st.copy( shift_st, 'vessel_tally', 'vessel_tally' )
          for name in shift_tally_grp:
	    dt = exposure_secs - prev_exposure_secs
	    if name == 'binned':
	      dset = shift_tally_grp.get( name )
	      binned_data = np.sum( np.array( dset ), axis = 0 )
	      exec_str = 'binned_data' + water_range_expr + ' = 0.0'
	      exec( exec_str, {}, { 'binned_data': binned_data } )
	      #out_tally_grp.create_dataset( 'binned_total', data = binned_data )

	      binned_fluence_incr = binned_data * dt
	      binned_fluence_var_incr = \
	          (binned_fluence_incr * dt * binned_data)

	    elif name == 'total':
	      dset = shift_tally_grp.get( name )
	      total_data = np.array( dset )
	      exec_str = 'total_data' + water_range_expr + ' = 0.0'
	      exec( exec_str, {}, { 'total_data': total_data } )
              #out_tally_grp.create_dataset( 'total', data = total_data )

	      fluence_incr = total_data * dt
	      fluence_var_incr = (fluence_incr * dt * total_data)

	    elif name not in TALLY_CORE_DS_NAMES:
	      dset = out_tally_grp.\
	          create_dataset( name, data = shift_tally_grp.get( name ) )
          #end for name
#			-- Assert on total
#			--
	  assert fluence_incr is not None, \
	      '%s/total not found in "%s"' % ( state_name, shift_fp.filename )

	  err_save = np.seterr( all = 'ignore' )
	  try:
	    accum_fluence_data += fluence_incr
            out_tally_grp.create_dataset( 'fluence', data = accum_fluence_data )

	    accum_fluence_var_data += fluence_var_incr
	    z_places = np.argwhere( fluence_incr == 0.0 ).transpose().tolist()
	    fluence_re = np.sqrt( accum_fluence_var_data ) / fluence_incr;
	    fluence_re[ z_places ] = 0.0
            out_tally_grp.\
	        create_dataset( 'fluence_rel_error', data = fluence_re )

	    prev_exposure_secs = exposure_secs
	    prev_shift_tally_grp = shift_tally_grp

	    if binned_fluence_incr is not None:
	      accum_binned_fluence_data += binned_fluence_incr
              out_tally_grp.create_dataset(
	          'binned_fluence',
		  data = accum_binned_fluence_data
		  )

	      accum_binned_fluence_var_data += binned_fluence_var_incr
	      z_places = np.argwhere( binned_fluence_incr == 0.0 ).\
	          transpose().tolist()
	      fluence_re = \
	          np.sqrt( accum_binned_fluence_var_data ) / \
		  binned_fluence_incr;
	      fluence_re[ z_places ] = 0.0
              out_tally_grp.create_dataset(
	          'binned_fluence_rel_error',
		  data = fluence_re
		  )
	  #end if binned_fluence_incr is not None

	  finally:
	    np.seterr( **err_save )

          state_ndx += 1
        #end else state_name in mpact_fp
      #end while

    finally:
      out_fp.close()
      mpact_fp.close()
      shift_fp.close()
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
	  '-m', '--mpact-file',
	  help = 'path to input MPACT HDF5 file',
	  required = True,
	  type = extant_file
          )
      parser.add_argument(
	  '-o', '--output-file',
	  default = 'out.h5',
	  help = 'path to output HDF5 file'
          )
      parser.add_argument(
	  '-s', '--shift-file',
	  help = 'path to input Shift HDF5 file',
	  required = True,
	  type = extant_file
          )
      args = parser.parse_args()

      obj = FluenceSynthesizer()
      obj( args.mpact_file, args.shift_file, args.output_file )

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

#end FluenceSynthesizer


#------------------------------------------------------------------------
#	NAME:		__main__					-
#------------------------------------------------------------------------
if __name__ == '__main__':
  FluenceSynthesizer.main()
