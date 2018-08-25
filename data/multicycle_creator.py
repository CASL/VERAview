#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		multicycle_creator.py				-
#	HISTORY:							-
#		2018-04-02	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, math, os, sys, traceback
import numpy as np
from scipy import interpolate
import pdb

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )
#sys.path.insert( 0, VVDIR )

#from data.utils import *
from data.datamodel import *
from data.pin_averages import *


#------------------------------------------------------------------------
#	CLASS:		MultiCycleCreator				-
#------------------------------------------------------------------------
class MultiCycleCreator( object ):
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
    self.logger = logging.getLogger( 'data' )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		_createInterpolator()				-
  #----------------------------------------------------------------------
  def _createInterpolator( self,
      src_data, src_mesh_centers,
      axis = 2, mode = 'nearest'
      ):
    """
"""
    f = interpolate.interp1d(
        src_mesh_centers, src_data,
	assume_sorted = True, axis = axis,
	bounds_error = False,
	kind = 'nearest'
	)
    x = f.x
    y = f.y

    def extrapolate( x ):
      if x < f.x[ 0 ]:
	y = \
	    (x - f.x[ 0 ]) / (f.x[ 1 ] - f.x[ 0 ]) * \
            (f.y[ :, :, 1, : ] - f.y[ :, :, 0, : ]) + \
	    f.y[ :, :, 0, : ]
      elif x > f.x[ -1 ]:
	y = \
	    (x - f.x[ -2 ]) / (f.x[ -1 ] - f.x[ -2 ]) * \
            (f.y[ :, :, -1, : ] - f.y[ :, :, -2, : ]) + \
	    f.y[ :, :, -2, : ]
      else:
        y = f( x )
      return  y
    #end extrapolate

    return  extrapolate
  #end _createInterpolator


  #----------------------------------------------------------------------
  #	METHOD:		_createLHR()					-
  #----------------------------------------------------------------------
  def _createLHR( self, mpact_model, state, pin_factors = None ):
    """
    Args:
        mpact_model (data.datamodel.DataModel): datamodel instance
	state (data.datamodel.State): current state
	pin_factors (np.ndarray): factors
"""
#		-- Rated power
    if '/INPUT/CASEID/CORE/rated_power' in mpact_model.core.group:
      dset = mpact_model.core.group.get( '/INPUT/CASEID/CORE/rated_power' )
      rated_power = dset[ 0 ]  if len( dset.shape ) > 0 else  dset[ () ]
    else:
      rated_power = 3459.0

#		-- Core height
    axial_mesh = mpact_model.core.axialMesh
    core_ht = axial_mesh[ -1 ] - axial_mesh[ 0 ]

#		-- Assembly and pin counts
    nass = len( np.argwhere( mpact_model.core.coreMap ) )
    if pin_factors is not None:
      mid_ass = pin_factors.shape[ 3 ] >> 1
      mid_ax = pin_factors.shape[ 2 ] >> 1
      npin = len( np.argwhere( pin_factors[ :, :, mid_ax, mid_ass ] ) )
    else:
      npin = 264

#		-- Calculate
    alhr = rated_power * 1.e6 / (nass * npin * core_ht)
    power = self._readStateValue( state, 'power' )

    pin_powers = np.array( state.GetDataSet( 'pin_powers' ) )
    lhr = pin_powers * alhr * power / 100.0
    lhr[ np.isnan( pin_powers ) ] = np.nan

    return  lhr
  #end _createLHR


  #----------------------------------------------------------------------
  #	METHOD:		_processCycle()					-
  #----------------------------------------------------------------------
  def _processCycle( self,
      results, mpact_out_fp, shift_out_fp, base_path, first_flag = False
      ):
    """
"""
    print '[multicycle_creator]', base_path
    mpact_path = base_path + '.h5'
    #mpact_in_fp = h5py.File( mpact_path, 'r' )

    shift_path = base_path + '.shift.h5'
    shift_in_fp = h5py.File( shift_path, 'r' )

    mpact_model = DataModel( mpact_path )

    try:
      axial_mesh = results[ 'axial_mesh' ]
      equal_axial_mesh = np.array_equal( mpact_model.core.axialMesh, axial_mesh )

#		-- Copy COREs
#		--
      #if not ( first_flag or 'CORE' in mpact_out_fp ):
      if equal_axial_mesh and 'CORE' not in mpact_out_fp:
        print '[multicycle_creator] copying %s/CORE' % mpact_path
	mpact_model.h5File.copy( 'CORE', mpact_out_fp )
	axial_mesh = results[ 'axial_mesh' ]
	#if not np.array_equal( mpact_model.core.axialMesh, axial_mesh ):
	if False:
	  out_core_grp = mpact_out_fp.get( 'CORE' )
	  del out_core_grp[ 'axial_mesh' ]
	  out_core_grp.create_dataset( 'axial_mesh', data = axial_mesh )

	  if 'initial_mass' in out_core_grp:
	    to_data = self._resolveAxialDataSet(
		axial_mesh, out_core_grp.get( 'initial_mass' ),
		2, mpact_model.core.axialMesh, False
	        )
	    del out_core_grp[ 'initial_mass' ]
	    out_core_grp.create_dataset( 'initial_mass', data = to_data )

	  if 'pin_volumes' in out_core_grp:
	    to_data = self._resolveAxialDataSet(
		axial_mesh, out_core_grp.get( 'pin_volumes' ),
		2, mpact_model.core.axialMesh, False
	        )
	    del out_core_grp[ 'pin_volumes' ]
	    out_core_grp.create_dataset( 'pin_volumes', data = to_data )

	  if 'pin_factors' in out_core_grp:
	    to_data = self._resolveAxialDataSet(
		axial_mesh, out_core_grp.get( 'pin_factors' ),
		2, mpact_model.core.axialMesh, False
	        )
	    del out_core_grp[ 'pin_factors' ]
	    out_core_grp.create_dataset( 'pin_factors', data = to_data )
	#end if not np.array_equal( mpact_model.core.axialMesh, axial_mesh )
      #end if not ( first_flag or 'CORE' in mpact_out_fp )

      #if not ( first_flag or 'CORE' in shift_out_fp ):
      if equal_axial_mesh and 'CORE' not in shift_out_fp:
        print '[multicycle_creator] copying %s/CORE' % shift_path
        shift_in_fp.copy( 'CORE', shift_out_fp )
      #end if 'core' not in shift_out_fp

#		-- Compute averages
#		--
      if 'pin_factors' in mpact_model.core.group:
        pin_factors = np.array( mpact_model.core.group.get( 'pin_factors' ) )
      else:
        ref_st = \
            mpact_model.states[ 1 ]  if len( mpact_model.states ) > 1 else \
            mpact_model.states[ 0 ]  if len( mpact_model.states ) > 0 else \
	    None
        pin_powers = np.array( ref_st.GetDataSet( 'pin_powers' ) )
	averages = Averages( mpact_model.core, pin_powers, None )
	pin_factors = averages.pinWeights

#		-- Process each statepoint
#		--
      #for st in mpact_model.states:
      state_ndx_start = 0  if first_flag else  1
      for state_ndx in xrange( state_ndx_start, len( mpact_model.states ) ):
        st = mpact_model.states[ state_ndx ]
#			-- Break if statepoint not in Shift file
	if st.group.name not in shift_in_fp: break

	to_state_name = 'STATE_%04d' % results[ 'state' ]
	self._processMpactState(
	    results, mpact_out_fp, to_state_name, mpact_model, st, pin_factors
	    )

	shift_in_fp.copy( st.group.name, shift_out_fp, to_state_name )
	results[ 'state' ] += 1
      #end for st in mpact_model.states

      if len( results[ 'history_exposure' ] ) > 0:
        results[ 'base_exposure' ] = results[ 'history_exposure' ][ -1 ]
      if len( results[ 'history_exposure_efpd' ] ) > 0:
        results[ 'base_exposure_efpd' ] = \
	    results[ 'history_exposure_efpd' ][ -1 ]

    finally:
      #mpact_in_fp.close()
      mpact_model.Close()
      shift_in_fp.close()
  #end _processCycle


  #----------------------------------------------------------------------
  #	METHOD:		_processMpactState()				-
  #----------------------------------------------------------------------
  def _processMpactState(
      self, results, to_fp, to_state_name,
      mpact_model, state, pin_factors
      ):
    """
"""
    print '[multicycle_creator] MPACT %s to /%s' % \
        ( state.group.name, to_state_name )

#		-- Rated power
    if '/INPUT/CASEID/CORE/rated_power' in mpact_model.core.group:
      dset = mpact_model.core.group.get( '/INPUT/CASEID/CORE/rated_power' )
      rated_power = dset[ 0 ]  if len( dset.shape ) > 0 else  dset[ () ]
    else:
      rated_power = 3459.0

    to_state_grp = to_fp.create_group( to_state_name )
#xx
##    cur_exposure = self._readStateValue( state, 'exposure' )
##    if cur_exposure == 0.0 and results[ 'exposure' ] >= 0.0 and \
##        len( results[ 'history_exposure' ] ) > 0:
##      cur_exposure = results[ 'history_exposure' ][ -1 ]
##    results[ 'history_exposure' ].append( cur_exposure )
##
##    cur_efpd = self._readStateValue( state, 'exposure_efpd' )
##    if cur_efpd == 0.0 and results[ 'exposure_efpd' ] >= 0.0 and \
##        len( results[ 'history_exposure_efpd' ] ) > 0:
##      cur_efpd = results[ 'history_exposure_efpd' ][ -1 ]
##    results[ 'history_exposure_efpd' ].append( cur_efpd )
##
##    results[ 'exposure' ] += cur_exposure
##    to_state_grp.create_dataset(
##        'exposure',
##	data = np.array( [ results[ 'exposure' ] ], dtype = np.float64 )
##	)
##
##    results[ 'exposure_efpd' ] += cur_efpd
##    to_state_grp.create_dataset(
##        'exposure_efpd',
##	data = np.array( [ results[ 'exposure_efpd' ] ], dtype = np.float64 )
##	)
##
##    cur_efpy = cur_efpd / 365.25
##    results[ 'exposure_efpy' ] += cur_efpy
##    to_state_grp.create_dataset(
##        'exposure_efpy',
##	data = np.array( [ results[ 'exposure_efpy' ] ], dtype = np.float64 )
##	)
#xx
    st_exposure = self._readStateValue( state, 'exposure' )
    cur_exposure = st_exposure + results[ 'base_exposure' ]
    results[ 'history_exposure' ].append( cur_exposure )
    to_state_grp.create_dataset( 'exposure', data = cur_exposure )
	#data = np.array( [ cur_exposure ], dtype = np.float64 )
    to_state_grp.create_dataset( 'cycle_exposure', data = st_exposure )

    st_efpd = self._readStateValue( state, 'exposure_efpd' )
    cur_efpd = st_efpd + results[ 'base_exposure_efpd' ]
    results[ 'history_exposure_efpd' ].append( cur_efpd )
    to_state_grp.create_dataset( 'exposure_efpd', data = cur_efpd )
	#data = np.array( [ cur_efpd ], dtype = np.float64 )
    to_state_grp.create_dataset( 'cycle_exposure_efpd', data = st_efpd )

    st_efpy = st_efpd / 365.25
    to_state_grp.create_dataset( 'cycle_exposure_efpy', data = st_efpy )
    cur_efpy = cur_efpd / 365.25
    to_state_grp.create_dataset( 'exposure_efpy', data = cur_efpy )
	#data = np.array( [ cur_efpy ], dtype = np.float64 )

    power = self._readStateValue( state, 'power' )
    mw = power * rated_power / 100.0
    to_state_grp.create_dataset( 'MW', data = mw )

    axial_mesh = results[ 'axial_mesh' ]
    equal_axial_mesh = np.array_equal( mpact_model.core.axialMesh, axial_mesh )

    for ds_name in state.group:
      if ds_name not in ( 'exposure', 'exposure_efpd', 'exposure_efpy' ):
        ds_def = mpact_model.GetDataSetDefByDsName( ds_name )
	if ds_def is not None:
	  ds_type = ds_def.get( 'type', '' )
	  axial_axis = ds_def.get( 'axial_axis', -1 )
	  if ds_type.find( 'detector' ) >= 0 or axial_axis < 0 or \
	      equal_axial_mesh:
	    state.group.copy( ds_name, to_state_grp )
	  else:
	    dset = state.group.get( ds_name )
	    to_data = self._resolveAxialDataSet(
	        axial_mesh, dset,
	        axial_axis, mpact_model.core.axialMesh
	        )
	    to_state_grp.create_dataset( ds_name, data = to_data )
	  #end else axial_axis >= 0 and not equal_axial_mesh:
	#end if ds_def is not None
      #end if ds_name not in
    #end for ds_name in cur_state_grp

    lhr_array = self._createLHR( mpact_model, state, pin_factors )
    if not equal_axial_mesh:
      lhr_array = self._resolveAxialDataSet(
	  axial_mesh, lhr_array, 2, mpact_model.core.axialMesh
          )
    to_state_grp.create_dataset( 'pin_lhr', data = lhr_array )
  #end _processMpactState


  #----------------------------------------------------------------------
  #	METHOD:		_readDataSet()					-
  #----------------------------------------------------------------------
  def _readDataSet( self, group, ds_name ):
    """
    Returns:
        np.ndarray: data in an array
"""
    return \
        np.array( group.get( ds_name ) )  if ds_name in group else \
	None
  #end _readDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_readStateValue()				-
  #----------------------------------------------------------------------
  def _readStateValue( self, state, ds_name ):
    """
"""
    value = np.nan

    dset = state.GetDataSet( ds_name )
    if dset is not None:
      value = dset[ 0 ]  if len( dset.shape ) > 0 else  dset[ () ]

    return  value
  #end _readStateValue


  #----------------------------------------------------------------------
  #	METHOD:		_readValue()					-
  #----------------------------------------------------------------------
  def _readValue( self, group, name ):
    """
"""
    value = np.nan

    if name in group:
      dset = group.get( name )
      value = \
          dset[ () ]  if len( dset.shape ) == 0 else \
	  dset[ 0 ]

    return  value
  #end _readValue


  #----------------------------------------------------------------------
  #	METHOD:		_resolveAxialDataSet()				-
  #----------------------------------------------------------------------
  def _resolveAxialDataSet( self,
      to_axial_mesh, dset, axial_axis, from_axial_mesh, mode = 'nearest'
      ):
    """
"""
    from_centers = (from_axial_mesh[ 0 : -1 ] + from_axial_mesh[ 1 : ]) / 2.0
    to_centers = (to_axial_mesh[ 0 : -1 ] + to_axial_mesh[ 1 : ]) / 2.0

    to_shape = list( dset.shape )
    to_shape[ axial_axis ] = len( to_centers )
    to_array = np.zeros( to_shape, dtype = np.float64 )

    from_array = dset  if isinstance( dset, np.ndarray ) else  np.array( dset )

    expr_items = [ ':' ] * len( to_shape )
    #expr_items[ axial_axis ] = '%d'
    #expr_fmt = '[' + ','.join( expr_items ) + ']'
    expr_items[ axial_axis ] = 'k'
    exec_str = 'X[' + ','.join( expr_items ) + '] = F( Y[ k ] )'

    f = self._createInterpolator( from_array, from_centers, axial_axis, mode )
    locals_env = { 'F': f, 'X': to_array, 'Y': to_centers, 'k': 0 }
    for k in xrange( to_shape[ axial_axis ] ):
      locals_env[ 'k' ] = k
      exec( exec_str, {}, locals_env )
    #end for k in xrange( to_shape[ axial_axis ] )

    return  to_array
  #end _resolveAxialDataSet


  #----------------------------------------------------------------------
  #	METHOD:		_resolveAxialDataSet_nans()			-
  #----------------------------------------------------------------------
  def _resolveAxialDataSet_nans( self,
      to_axial_mesh, dset, axial_axis, from_axial_mesh, fill_nan = True
      ):
    """
"""
    globals_env = {}

    to_shape = list( dset.shape )
    to_shape[ axial_axis ] = len( to_axial_mesh ) - 1

    expr_items = [ ':' ] * len( to_shape )
    expr_items[ axial_axis ] = '%d'
    expr_fmt = '[' + ','.join( expr_items ) + ']'

    if fill_nan:
      to_array = np.empty( to_shape, dtype = np.float64 )
      to_array.fill( np.nan )
    else:
      to_array = np.zeros( to_shape, dtype = np.float64 )

    from_array = dset  if isinstance( dset, np.ndarray ) else  np.array( dset )
    from_ndx = to_ndx = 0
    while to_ndx < len( to_axial_mesh ) - 1 and \
        from_ndx < len( from_axial_mesh ) - 1:
      if to_axial_mesh[ to_ndx ] == from_axial_mesh[ from_ndx ]:
        to_expr = expr_fmt % to_ndx
	from_expr = expr_fmt % from_ndx

	exec_str = 'to_array' + to_expr + ' = from_array' + from_expr
        locals_env = { 'from_array': from_array, 'to_array': to_array }
	exec( exec_str, globals_env, locals_env )

	from_ndx += 1
	to_ndx += 1

      elif to_axial_mesh[ to_ndx ] > from_axial_mesh[ from_ndx ]:
        from_ndx += 1
      elif to_axial_mesh[ to_ndx ] < from_axial_mesh[ from_ndx ]:
        to_ndx += 1
    #end while

    return  to_array
  #end _resolveAxialDataSet_nans


  #----------------------------------------------------------------------
  #	METHOD:		_resolveAxialMesh()				-
  #----------------------------------------------------------------------
  def _resolveAxialMesh( self, *input_paths ):
    """
"""
    if len( input_paths ) > 2:
      start_ndx = len( input_paths ) >> 1
    else:
      start_ndx = 1
    fp = h5py.File( input_paths[ start_ndx ], 'r' )
    mesh = None
    try:
      mesh = np.array( fp.get( 'CORE/axial_mesh' ) )
    finally:
      fp.close()

    for ndx in xrange( start_ndx + 1, len( input_paths ) ):
      fp = h5py.File( input_paths[ ndx ], 'r' )
      try:
        cur_mesh = np.array( fp.get( 'CORE/axial_mesh' ) )
	if len( cur_mesh ) > len( mesh ):
	  mesh = cur_mesh
      finally:
        fp.close()
    #end for ndx

    return  mesh
  #end _resolveAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		_resolveAxialMesh_nope()			-
  #----------------------------------------------------------------------
  def _resolveAxialMesh_nope( self, *input_paths ):
    """
"""
    mesh_set = set( [] )
    for fpath in input_paths:
      fp = h5py.File( fpath, 'r' )
      try:
        dset = fp.get( 'CORE/axial_mesh' )
	darray = np.array( dset )
	mesh_set |= set( darray.tolist() )
      finally:
        fp.close()
    #end for fpath in input_paths

    return  np.array( sorted( mesh_set ), dtype = np.float64 )
  #end _resolveAxialMesh_nope


  #----------------------------------------------------------------------
  #	METHOD:		run()						-
  #----------------------------------------------------------------------
  def run( self, output_path, *cycle_input_paths ):
    """Assume all ``cycle_input_paths`` are valid with MPACT and Shift files,
and there are at least two of them.
"""
#	-- Resolve axial_mesh
#	--
    mpact_paths = [ f + '.h5' for f in cycle_input_paths ]
    axial_mesh = self._resolveAxialMesh( *mpact_paths )

#	-- Create output
#	--
    if not output_path.endswith( '.h5' ):
      output_path += '.h5'
    shift_output_path = output_path[ : -3 ] + '.shift.h5'
    mpact_out_fp = h5py.File( output_path, 'w' )
    shift_out_fp = h5py.File( shift_output_path, 'w' )

    try:
      results = \
        {
	'axial_mesh': axial_mesh,
	'base_exposure': 0.0,
	'base_exposure_efpd': 0.0,
	#'exposure': 0.0,
	#'exposure_efpd': 0.0,
	'history_exposure_efpd': [],
	#'exposure_efpy': 0.0,
	'history_exposure': [],
	'state': 1
	}
      first_flag = True
      for base_path in cycle_input_paths:
	try:
	  self._processCycle(
	      results, mpact_out_fp, shift_out_fp, base_path,
	      first_flag
	      )
	  first_flag = False
	except Exception, ex:
          print >> sys.stderr, \
              '[multicycle_creator] {0:s}{1:s}:{2:s}'.\
	      format( base_path, os.linesep, str( ex ) )
      #end for path in mpact_paths:

    finally:
      mpact_out_fp.close()
      shift_out_fp.close()
  #end run


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		checkCycleFiles()				-
  #----------------------------------------------------------------------
  @staticmethod
  def checkCycleFiles( fpath ):
    if fpath.endswith( '.h5' ):
      fpath = fpath[ 0 : -3 ]
    mpact_fpath = fpath + '.h5'
    if not os.path.exists( mpact_fpath ):
      raise argparse.ArgumentTypeError( '{0} not found'.format( mpact_fpath ) )

    shift_fpath = fpath + '.shift.h5'
    if not os.path.exists( shift_fpath ):
      raise argparse.ArgumentTypeError( '{0} not found'.format( shift_fpath ) )

#		-- Verify MPACT file
#		--
    fp = h5py.File( mpact_fpath )
    try:
      fmt = '%s required in ' + mpact_fpath
      assert 'CORE' in fp, fmt % 'CORE/ group'
      assert 'CORE/axial_mesh' in fp, fmt % 'CORE/axial_mesh'

      assert 'STATE_0001' in fp, fmt % 'STATE_0001/'
      assert 'STATE_0001/exposure_efpd' in fp, \
	  fmt % 'STATE_0001/exposure_efpd'
      assert 'STATE_0001/pin_powers' in fp, fmt % 'STATE_0001/pin_powers'
      assert 'STATE_0001/power' in fp, fmt % 'STATE_0001/power'
    finally:
      fp.close()

#		-- Verify Shift file
#		--
    fp = h5py.File( shift_fpath )
    try:
      fmt = '%s required in ' + shift_fpath
      assert 'CORE' in fp, fmt % 'CORE/ group'
      for name in (
          'baffle_gap_inner',
	  'baffle_inner_radius', 'baffle_outer_radius',
	  'barrel_inner_radius', 'barrel_outer_radius',
	  'liner_inner_radius', 'liner_outer_radius',
	  'pad_angles', 'pad_inner_radius', 'pad_outer_radius',
	  'vessel_inner_radius', 'vessel_outer_radius'
	  ):
	core_name = 'CORE/' + name
        assert core_name in fp, fmt % core_name

      assert 'STATE_0001' in fp, fmt % 'STATE_0001/'
      assert 'STATE_0001/vessel_tally' in fp, fmt % 'STATE_0001/vessel_tally'
    finally:
      fp.close()

    return  fpath
  #end checkCycleFiles


  #----------------------------------------------------------------------
  #	METHOD:		main()						-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    """
"""
    from data.config import Config
    def check_all( *paths ):
      for f in paths:
        MultiCycleCreator.checkCheckFiles( f )
      return  paths
    #end check_all

    try:
      parser = argparse.ArgumentParser()

      parser.add_argument(
	  '-o', '--output-file',
	  default = 'multicycle.h5',
	  help = 'path to MPACT output file'
          )
      parser.add_argument(
	  'file_path',
	  default = [],
	  help = 'path to cycle base filename with .h5 and .shift.h5 extension (at least two cycles required)',
	  nargs = '+',
	  type = MultiCycleCreator.checkCycleFiles
	  #type = check_all
          )
      args = parser.parse_args()

      if len( args.file_path ) < 2:
        parser.print_usage()
      else:
        MultiCycleCreator()( args.output_file, *args.file_path )
        print '[multicycle_creator] finished'

    except Exception, ex:
      msg = str( ex )
      print >> sys.stderr, msg
      et, ev, tb = sys.exc_info()
      while tb:
        print >> sys.stderr
        print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
      logging.error( msg )
  #end main

#end MultiCycleCreator


#------------------------------------------------------------------------
#	NAME:		__main__					-
#------------------------------------------------------------------------
if __name__ == '__main__':
  MultiCycleCreator.main()
