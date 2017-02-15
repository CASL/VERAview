#------------------------------------------------------------------------
#	NAME:		differences.py					-
#	HISTORY:							-
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
  def calc( self, ref_qds_name, comp_qds_name, diff_ds_name, listener = None ):
    """Create new difference dataset to be stored as a derived dataset in
the comp_qds_name model.  Thus, the axial mesh and time
values are from comp_qds_name model.  The current timeDataSet is used
to resolve times between the datasets.  The ref and comp DataModels can
be the same.
@param  ref_qds_name	reference dataset x in x - y
@param  comp_qds_name	comparison dataset y in x - y
@param  diff_ds_name	name of difference dataset
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
#			-- Retrieve meshes, assert
#			--
      ddef = comp_dm.GetDataSetDef( comp_type )

      if ddef[ 'axial_axis' ] < 0:
        ref_mesh_values = comp_mesh_values = None
        mesh_type = ''
      elif ref_type == 'detector':
        ref_mesh_values = self.dmgr.GetDetectorMesh( ref_qds_name )
        comp_mesh_values = self.dmgr.GetDetectorMesh( comp_qds_name )
        mesh_type = 'Detector mesh'
      elif ref_type == 'fixed_detector':
        ref_mesh_values = self.dmgr.GetFixedDetectorMeshCenters( ref_qds_name )
        comp_mesh_values = self.dmgr.GetFixedDetectorMeshCenters( comp_qds_name )
        mesh_type = 'Fixed detector mesh centers'
      else:
        ref_mesh_values = self.dmgr.GetAxialMeshCenters( ref_qds_name )
        comp_mesh_values = self.dmgr.GetAxialMeshCenters( comp_qds_name )
        mesh_type = 'Axial mesh centers'

#xxxxx
#      assert len( ref_mesh_values ) == len( comp_mesh_values ), \
#          '%s length mismatch' % mesh_type
      must_interpolate = not np.array_equal( ref_mesh_values, comp_mesh_values )
      if must_interpolate:
        interp = Interpolator( ref_mesh_values, comp_mesh_values )

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
	    ref_data = interp.interpolate( ref_dset, skip_assertions = True )
	  else:
	    ref_data = np.array( ref_dset )

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

#end Differences
