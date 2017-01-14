#------------------------------------------------------------------------
#	NAME:		differences.py					-
#	HISTORY:							-
#		2017-01-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys
import numpy as np
import pdb


#------------------------------------------------------------------------
#	CLASS:		Differences					-
#------------------------------------------------------------------------
class Differences( object ):


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
  def calc( self, base_qds_name, sub_qds_name, diff_ds_name ):
    """Create new difference dataset to be stored as a derived dataset in
the base_qds_name model.  Thus, the axial mesh and time
values are from the base_qds_name model.  The current timeDataSet is used
to resolve times between the datasets.  The base and sub DataModels can
be the same.
@param  base_qds_name	dataset x in x - y
@param  sub_qds_name	dataset y in x - y
@param  diff_ds_name	name of difference dataset
@return			difference DataSetName
@exception		if diff_ds_name not created in base_qds_name.modelName
"""
#		-- Assert on models
#		--
    base_dm = self.GetDataModel( base_qds_name )
    sub_dm = self.GetDataModel( sub_qds_name )

    assert base_dm is not None, \
        'DataModel "%s" not found' % base_qds_name.modelName
    assert sub_dm is not None, \
        'DataModel "%s" not found' % sub_qds_name.modelName

#		-- Assert on dataset types match
#		--
    base_type = base_dm.GetDataSetType( base_qds_name.displayName )
    sub_type = sub_dm.GetDataSetType( sub_qds_name.displayName )

    assert base_type and sub_type and base_type == sub_type, \
        'Dataset types mismatch: %s ne %s' % ( base_type, sub_type )

#		-- Retrieve dataset definition and times
#		--
    ddef = base_dm.GetDataSetDef( base_type )

    base_time_values = self.GetTimeValues( base_qds_name )
    sub_time_values = self.GetTimeValues( sub_qds_name )
    equal_times = base_time_values == sub_time_values

#		-- Retrieve meshes
#		--
    if ddef[ 'axial_axis' ] < 0:
      base_mesh_values = sub_mesh_values = None
    elif base_type == 'detector':
      base_mesh_values = self.GetDetectorMesh( base_qds_name )
      sub_mesh_values = self.GetDetectorMesh( sub_qds_name )
    elif base_type == 'fixed_detector':
      base_mesh_values = self.GetFixedDetectorMeshCenters( base_qds_name )
      sub_mesh_values = self.GetFixedDetectorMeshCenters( sub_qds_name )
    else:
      base_mesh_values = self.GetAxialMeshCenters( base_qds_name )
      sub_mesh_values = self.GetAxialMeshCenters( sub_qds_name )
    equal_meshes = base_mesh_values == sub_mesh_values

#		-- State by state
#		--
    try:
      #calculator = Differences()
      for base_state_ndx in xrange( len( base_time_values ) ):
        cur_time = base_time_values[ base_state_ndx ]
        if equal_times:
	  sub_state_ndx = base_state_ndx
        else:
	  cur_time = base_time_values[ base_state_ndx ]
	  sub_state_ndx = \
	      DataUtils.FindListIndex( sub_time_values, cur_time, 'a' )

        base_dset = base_dm.\
	    GetStateDataSet( base_state_ndx, base_qds_name.displayName )
        sub_dset = sub_dm.\
	    GetStateDataSet( sub_state_ndx, sub_qds_name.displayName )
	base_derived_st = base_dm.GetDerivedState( base_state_ndx )

        if base_derived_st is not None and \
	    base_dset is not None and sub_dset is not None:
	  pass
	  #xxxxx
          #base_derived_st.CreateDataSet( diff_ds_name, diff_data )
        #end if base_derived_st
      #end for state_ndx

      return  DataSetName( base_qds_name.modelName, diff_ds_name )

    except Exception, ex:
      msg = 'Error calculating difference for "%s" and "%s"' % \
          ( base_qds_name, sub_qds_name )
      self.logger.error( msg )
      raise Exception( msg )
  #end calc

#end Differences
