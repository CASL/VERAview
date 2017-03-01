#------------------------------------------------------------------------
#	NAME:		differences.py					-
#	HISTORY:							-
#		2017-02-24	leerw@ornl.gov				-
#		2017-02-16	leerw@ornl.gov				-
#	  Added diff_mode and interp_mode params.
#		2017-02-15	leerw@ornl.gov				-
#	  New approach with interpolation				-
#		2017-01-26	leerw@ornl.gov				-
#		2017-01-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys
import numpy as np
import pdb

from data.datamodel import DataSetName
from data.interpolator import *
from data.utils import DataUtils


#------------------------------------------------------------------------
#	CLASS:		Differences					-
#------------------------------------------------------------------------
class Differences( object ):


  #----------------------------------------------------------------------
  #	METHOD:		__call__()					-
  #----------------------------------------------------------------------
  def __call__( self, *args, **kwargs ):
    return  self.calc( *args, **kwargs )
  #end __call__


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, dmgr ):
    """
"""
    self.dmgr = dmgr
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		calc()						-
  #----------------------------------------------------------------------
  def calc(
      self, ref_qds_name, comp_qds_name, diff_ds_name,
      diff_mode = 'delta', interp_mode = 'linear',
      listener = None
      ):
    """Create new difference dataset to be stored as a derived dataset in
the comp_qds_name model.  Thus, the axial mesh and time
values are from comp_qds_name model.  The current timeDataSet is used
to resolve times between the datasets.  The ref and comp DataModels can
be the same.
@param  ref_qds_name	reference dataset x in x - y
@param  comp_qds_name	comparison dataset y in x - y
@param  diff_ds_name	name of difference dataset
@param  diff_mode	difference mode, must start with one of 'delta', 'pct'
@param  interp_mode	interpolation mode, one of 'linear', 'quad', 'cubic'
@param  listener	optional callable( message, cur_step, step_count )
@return			difference DataSetName
@exception		if diff_ds_name not created in comp_qds_name.modelName
"""
#		-- Assert on models
#		--
    ref_dm = self.dmgr.GetDataModel( ref_qds_name )
    comp_dm = self.dmgr.GetDataModel( comp_qds_name )

    assert ref_dm is not None, \
        'DataModel "%s" not found' % ref_qds_name.modelName
    assert comp_dm is not None, \
        'DataModel "%s" not found' % comp_qds_name.modelName

#		-- Assert on dataset types match
#		--
    ref_type = ref_dm.GetDataSetType( ref_qds_name.displayName )
    comp_type = comp_dm.GetDataSetType( comp_qds_name.displayName )

    assert ref_type and comp_type and ref_type == comp_type, \
        'Dataset types mismatch: %s ne %s' % ( ref_type, comp_type )

    try:
#      print >> sys.stderr, '[calc] diff_mode=%s, interp_mode=%s' % \
#          ( diff_mode, interp_mode )
#			-- Retrieve meshes, assert
#			--
      ddef = comp_dm.GetDataSetDef( comp_type )
      comp_mesh_centers = None

      if ddef[ 'axial_axis' ] < 0:
        ref_mesh_centers = comp_mesh = None
        mesh_type = ''
      elif ref_type == 'detector':
        ref_mesh_centers = self.dmgr.GetDetectorMesh( ref_qds_name )
	comp_mesh_centers = \
        comp_mesh = self.dmgr.GetDetectorMesh( comp_qds_name )
        mesh_type = 'detector'
      elif ref_type == 'fixed_detector':
        ref_mesh_centers = self.dmgr.GetFixedDetectorMeshCenters( ref_qds_name )
        comp_mesh = self.dmgr.GetFixedDetectorMesh( comp_qds_name )
        comp_mesh_centers = \
	    self.dmgr.GetFixedDetectorMeshCenters( comp_qds_name )
        mesh_type = 'fixed_detector'
      else:
        ref_mesh_centers = self.dmgr.GetAxialMeshCenters( ref_qds_name )
        comp_mesh = self.dmgr.GetAxialMesh( comp_qds_name )
        comp_mesh_centers = self.dmgr.GetAxialMeshCenters( comp_qds_name )
        mesh_type = 'axial'

#xxxxx
#      assert len( ref_mesh_values ) == len( comp_mesh_values ), \
#          '%s length mismatch' % mesh_type
#      must_interpolate = not np.array_equal( ref_mesh_values, comp_mesh_values )
      must_interpolate = \
          comp_mesh_centers is None or \
          not self.equal_meshes( ref_mesh_centers, comp_mesh_centers )
      if must_interpolate:
        interp = Interpolator( ref_mesh_centers, comp_mesh, comp_mesh_centers )

#			-- Retrieve times
#			--
      ref_time_values = self.dmgr.GetTimeValues( ref_qds_name )
      comp_time_values = self.dmgr.GetTimeValues( comp_qds_name )
      equal_times = ref_time_values == comp_time_values

#			-- Statept by statept
#			--
      step_count = len( comp_time_values )
      cur_step = 0

      for comp_state_ndx in xrange( len( comp_time_values ) ):
	if listener:
          listener( 'Calculating differences', cur_step, step_count )

        cur_time = comp_time_values[ comp_state_ndx ]
	if equal_times:
	  ref_state_ndx = comp_state_ndx
	else:
	  ref_state_ndx = \
	      DataUtils.FindListIndex( ref_time_values, cur_time, 'a' )

	ref_dset = ref_dm.\
	    GetStateDataSet( ref_state_ndx, ref_qds_name.displayName )
        comp_dset = comp_dm.\
	    GetStateDataSet( comp_state_ndx, comp_qds_name.displayName )
	comp_derived_st = comp_dm.GetDerivedState( comp_state_ndx )

        if comp_derived_st is not None and \
	    ref_dset is not None and comp_dset is not None:

	  if must_interpolate:
	    if mesh_type == 'detector':
	      ref_data = interp.interpolate_on_spline(
	          ref_dset,
		  mode = interp_mode, skip_assertions = True
		  )
	    else:
	      ref_data = interp.interpolate_integral_over_spline(
	          ref_dset,
		  mode = interp_mode, skip_assertions = True
		  )
	  else:
	    ref_data = np.array( ref_dset )

	  if diff_mode.startswith( 'pct' ):
            errors_save = np.seterr( divide = 'ignore', invalid = 'ignore' )
            try:
	      diff_data = (comp_dset - ref_data) / ref_data
	      diff_data = np.nan_to_num( diff_data )
	      diff_data *= 100.0
            finally:
	      np.seterr( **errors_save )
	  else:
	    diff_data = comp_dset - ref_data

          comp_derived_st.CreateDataSet( diff_ds_name, diff_data )
        #end if comp_derived_st

	cur_step += 1
      #end for comp_state_ndx

      comp_dm.AddDataSetName( comp_type, diff_ds_name )
      return  DataSetName( comp_qds_name.modelName, diff_ds_name )

    except Exception, ex:
      msg = 'Error calculating difference for "%s" and "%s":%s%s' % \
          ( ref_qds_name, comp_qds_name, os.linesep, str( ex ) )
      self.dmgr.logger.error( msg )
      raise Exception( msg )
  #end calc


  #----------------------------------------------------------------------
  #	METHOD:		equal_meshes()					-
  #----------------------------------------------------------------------
  def equal_meshes( self, one, two, tolerance = 0.01 ):
    """
@param  one		first mesh, assumed not None
@param  two		second mesh, assumed not None
@param  tolerance	percentage error tolerance
"""
    equal = len( one ) == len( two )
    if equal:
      for i in xrange( len( one ) ):
	pct_error = abs( one[ i ] - two[ i ] ) / ((one[ i ] + two[ i ]) / 2.0)
	if pct_error > tolerance:
	  equal = False
	  break
      #end for i
    #end if

    return  equal
  #end equal_meshes

#end Differences
