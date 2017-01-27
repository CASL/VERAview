#------------------------------------------------------------------------
#	NAME:		differences.py					-
#	HISTORY:							-
#		2017-01-26	leerw@ornl.gov				-
#		2017-01-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys
import numpy as np
import pdb

from data.datamodel import DataSetName


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
    base_dm = self.dmgr.GetDataModel( base_qds_name )
    sub_dm = self.dmgr.GetDataModel( sub_qds_name )

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

#		-- Retrieve meshes, assert
#		--
    ddef = base_dm.GetDataSetDef( base_type )

    if ddef[ 'axial_axis' ] < 0:
      base_mesh_values = sub_mesh_values = None
      mesh_type = ''
    elif base_type == 'detector':
      base_mesh_values = self.dmgr.GetDetectorMesh( base_qds_name )
      sub_mesh_values = self.dmgr.GetDetectorMesh( sub_qds_name )
      mesh_type = 'Detector mesh'
    elif base_type == 'fixed_detector':
      base_mesh_values = self.dmgr.GetFixedDetectorMeshCenters( base_qds_name )
      sub_mesh_values = self.dmgr.GetFixedDetectorMeshCenters( sub_qds_name )
      mesh_type = 'Fixed detector mesh centers'
    else:
      base_mesh_values = self.dmgr.GetAxialMeshCenters( base_qds_name )
      sub_mesh_values = self.dmgr.GetAxialMeshCenters( sub_qds_name )
      mesh_type = 'Axial mesh centers'
    #equal_meshes = base_mesh_values == sub_mesh_values

#xxxxx
#    assert np.array_equal( base_mesh_values, sub_mesh_values ), \
#        '%s mismatch' % mesh_type
    assert len( base_mesh_values ) == len( sub_mesh_values ), \
        '%s length mismatch' % mesh_type

#		-- Retrieve times
#		--
    base_time_values = self.dmgr.GetTimeValues( base_qds_name )
    sub_time_values = self.dmgr.GetTimeValues( sub_qds_name )
    equal_times = base_time_values == sub_time_values

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
          diff_data = np.copy( base_dset )
	  diff_data -= sub_dset
          base_derived_st.CreateDataSet( diff_ds_name, diff_data )
        #end if base_derived_st
      #end for state_ndx

      base_dm.AddDataSetName( base_type, diff_ds_name )
      return  DataSetName( base_qds_name.modelName, diff_ds_name )

    except Exception, ex:
      msg = 'Error calculating difference for "%s" and "%s":%s%s' % \
          ( base_qds_name, sub_qds_name, os.linesep, str( ex ) )
      self.dmgr.logger.error( msg )
      raise Exception( msg )
  #end calc

#end Differences
