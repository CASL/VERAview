#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
#		2019-01-28	leerw@ornl.gov				-
#         Rounding "exposure.." time values to 3 decimal places in
#         _UpdateTimeValues().
#		2019-01-15	leerw@ornl.gov				-
#         Replacing 'tally' with 'fluence'.
#		2018-10-19	leerw@ornl.gov				-
#	  Replaced GetRadialMesh() with CalcRadialMesh() after guidance
#	  from Travis Lange and Cole Gentry on how to compute pin radius.
#		2018-10-18	leerw@ornl.gov				-
#	  Calling FixDuplicates() in _UpdateTimeValues().
#		2018-10-03	leerw@ornl.gov				-
#	  Added use_factors param to GetRange() and GetRangeAll().
#		2018-09-13	leerw@ornl.gov				-
#	  Added HasNodalDataSetType().
#		2018-09-05	leerw@ornl.gov				-
#	  Modifying ReadDataSetTimeValues() to return the x-axis values
#	  as well.
#		2018-08-31	leerw@ornl.gov				-
#	  New approach for radialMeshDict.
#		2018-08-24	leerw@ornl.gov				-
#	  Added radialMeshDict.
#		2018-07-26	leerw@ornl.gov				-
#	  Renaming non-derived dataset category/type from 'axial' to
#	  'axials' to disambiguate from ':axial' displayed name.
#		2018-06-01	leerw@ornl.gov				-
#	  Checking for offset 'pin' axial mesh in _UpdateMeshValues().
#		2018-05-29	leerw@ornl.gov				-
#	  Bug fix: can't use capitalize() b/c it lowers all but first char.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-07-18	leerw@ornl.gov				-
#	  Replacing ignore range with threshold and using RangeExpression.
#	  Added {Load,Save}DataSetThresholds().
#		2017-07-17	leerw@ornl.gov				-
#	  Adding by qds_name ignore ranges.
#		2017-06-05	leerw@ornl.gov				-
#	  Adapting to axial mesh changes.
#		2017-04-21	leerw@ornl.gov				-
#	  Added HtmlMessage, using for CheckDataModelIsCompatible().
#		2017-04-13	leerw@ornl.gov				-
#	  Renamed _CheckDataModelIsCompatible() to
#	  CheckDataModelIsCompatible() since called from FileManagerBean.
#		2017-03-27	leerw@ornl.gov				-
#	  Dealing with tally mesh.
#		2017-03-25	leerw@ornl.gov				-
#	  Added GetRangeAll().
#		2017-02-15	leerw@ornl.gov				-
#	  Not considering detectorMap in _CheckDataModelIsCompatible().
#		2017-02-06	leerw@ornl.gov				-
#	  Fixed bug in ExtractSymmetryExtent() with even number of
#	  assemblies.
#		2017-01-14	leerw@ornl.gov				-
#	  Starting CreateDiffDataSet().
#		2017-01-12	leerw@ornl.gov				-
#	  Added IsChannelType().
#		2016-12-27	leerw@ornl.gov				-
#	  Added GetDetectorMeshIndex and GetFixedDetectorMeshCentersIndex().
#		2016-12-26	leerw@ornl.gov				-
#	  Added check for core_map and detector_map equality in
#	  _CheckDataModelIsCompatible().
#	  Added IsDetectorOperable().
#		2016-12-22	leerw@ornl.gov				-
#	  Modified the GetXxxMeshXxx() methods to accept a model_name
#	  param.
#		2016-12-13	leerw@ornl.gov				-
#	  Added GetDataSetDisplayName().
#		2016-12-09	leerw@ornl.gov				-
#		2016-12-08	leerw@ornl.gov				-
#	  Adding support methods or widgets.
#		2016-12-02	leerw@ornl.gov				-
#	  Added GetFirstDataModel().
#		2016-12-01	leerw@ornl.gov				-
#	  Moved {Assemble,Parse}QDataSetName() to datamodel.DataSetNamer
#	  class.
#		2016-11-30	leerw@ornl.gov				-
#		2016-11-29	leerw@ornl.gov				-
#	  Review and clean-up.
#		2016-08-19	leerw@ornl.gov				-
#		2016-08-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, cStringIO, functools, h5py, \
    logging, json, math, os, sys, \
    tempfile, threading, traceback
import numpy as np
import pdb

from .datamodel import *
from .differences import *
from .utils import *
from event.event import *


#------------------------------------------------------------------------
#	CLASS:		HtmlException					-
#------------------------------------------------------------------------
class HtmlException( Exception ):
  """Extends Exception with an 'htmlMessage' property.  Note the
htmlMessage content is a body snippet.  Call the WrapDocument()
or WrapBody() method to add HTML trappings.
"""


  #----------------------------------------------------------------------
  #	METHOD:		HtmlException.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, message, html_message ):
    """
"""
    super( HtmlException, self ).__init__( message )
    self.htmlMessage = html_message
  #end __init__

#end HtmlException


#------------------------------------------------------------------------
#	CLASS:		DataModelMgr					-
#------------------------------------------------------------------------
class DataModelMgr( object ):
  """Data/model bean encapsulation.  For now we read the
'CORE' group as the 'core' property, and all the states as the 'states'
property.

Events:
  dataSetAdded		OnDataSetAdded( self, model, ds_display_name )
			callable( self, model, ds_display_name )
  modelAdded		OnModelAdded( self, model_name )
			callable( self, model_name )
  modelRemoved		OnModelRemoved( self, model_name )
			callable( self, model_name )

Properties:
  dataModelNames	list of model names in order added
  dataModels		dict of DataModel objects keyed by name
  #dataSetNamesVersion	counter to indicate changes
  maxAxialValue		maximum axial value (cm) across all DataModels
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.__del__()				-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.Close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self ):
    """
"""
    self.axialMeshCentersDict = {}
    self.axialMeshDict = {}
    self.core = None
    self.dataModelNames = []
    self.dataModels = {}
    #self.dataSetNamesVersion = 0
    self.detectorMap = None
    self.listeners = \
        { 'dataSetAdded': [], 'modelAdded': [], 'modelRemoved': [] }
    self.logger = logging.getLogger( 'data' )
    self.maxAxialValue = 0.0
    self.timeDataSet = 'state'
    self.timeValues = []
    self.timeValuesById = {}

#	-- Method aliases
#	--
    self.add_listener = self.AddListener
    self.calc_radial_mesh = self.CalcRadialMesh
    self.check_data_model_is_compatible = self.CheckDataModelIsCompatible
    self.close = self.Close
    self.close_model = self.CloseModel
    self.create_assembly_addr = self.CreateAssemblyAddr
    self.create_assembly_addr_from_index = self.CreateAssemblyAddrFromIndex
    self.create_detector_addr = self.CreateDetectorAddr
    self.create_detector_addr_from_index = self.CreateDetectorAddrFromIndex
    self.create_diff_dataset = self.CreateDiffDataSet
    self.extract_symmetry_extent = self.ExtractSymmetryExtent
    self.find_channel_min_max_value = self.FindChannelMinMaxValue
    self.find_fluence_min_max_value = self.FindFluenceMinMaxValue
    self.find_multi_dataset_min_max_value = self.FindMultiDataSetMinMaxValue
    self.find_pin_min_max_value = self.FindPinMinMaxValue
    self._fire_event = self._FireEvent
    self.get_axial_mesh = self.GetAxialMesh2
    self.get_axial_mesh_centers = self.GetAxialMeshCenters2
    self.get_axial_mesh_centers_index = self.GetAxialMeshCentersIndex
    self.get_axial_mesh_index = self.GetAxialMeshIndex
    self.get_axial_value = self.GetAxialValue
    self._get_axial_value_rec = self._GetAxialValueRec
    self.get_core = self.GetCore
    self.get_data_model = self.GetDataModel
    self.get_data_model_count = self.GetDataModelCount
    self.get_data_model_names = self.GetDataModelNames
    self.get_data_model_dataset_names = self.GetDataModelDataSetNames
    self.get_data_models = self.GetDataModels
    self.get_dataset_def_by_qname = self.GetDataSetDefByQName
    self.get_dataset_display_name = self.GetDataSetDisplayName
    self.get_dataset_has_sub_addr = self.GetDataSetHasSubAddr
    self.get_dataset_scale_type = self.GetDataSetScaleType
    self.get_dataset_scale_type_all = self.GetDataSetScaleTypeAll
    self.get_dataset_threshold = self.GetDataSetThreshold
    self.get_dataset_qnames = self.GetDataSetQNames
    self.get_dataset_type = self.GetDataSetType
    self.get_dataset_types = self.GetDataSetTypes
    self.get_detector_mesh = self.GetDetectorMesh
    self.get_detector_mesh_index = self.GetDetectorMeshIndex
    self.get_factors = self.GetFactors
    self.get_first_data_model = self.GetFirstDataModel
    self.get_first_dataset = self.GetFirstDataSet
    self.get_fixed_detector_mesh = self.GetFixedDetectorMesh
    self.get_fixed_detector_mesh_centers = self.GetFixedDetectorMeshCenters
    self.get_fixed_detector_mesh_centers_index = self.GetFixedDetectorMeshCentersIndex
    self.get_fluence_mesh = self.GetFluenceMesh
    self.get_fluence_mesh_centers = self.GetFluenceMeshCenters
    self.get_fluence_mesh_index = self.GetFluenceMeshIndex
    self.get_max_axial_value = self.GetMaxAxialValue
    self.get_node_addr = self.GetNodeAddr
    self.get_node_addrs = self.GetNodeAddrs
    self.get_node_pin_addr = self.GetNodePinAddr
    self.get_pin_node_addr = self.GetPinNodeAddr
    #self.get_radial_mesh = self.GetRadialMesh
    self.get_range = self.GetRange
    self.get_range_all = self.GetRangeAll
    self.get_sub_addr_from_node = self.GetSubAddrFromNode
    self.get_time_dataset = self.GetTimeDataSet
    self.get_time_index_value = self.GetTimeIndexValue
    self.get_time_value_index = self.GetTimeValueIndex
    self.get_time_values = self.GetTimeValues
    self.has_data = self.HasData
    self.has_dataset_type = self.HasDataSetType
    self.is_3d_ready = self.Is3DReady
    self.is_bad_value = self.IsBadValue
    self.is_channel_type = self.IsChannelType
    self.is_derived_dataset = self.IsDerivedDataSet
    self.is_detector_operable = self.IsDetectorOperable
    self.is_nodal_type = self.IsNodalType
    self.is_valid = self.IsValid
    self.load_dataset_thresholds = self.LoadDataSetThresholds
    self.normalize_assembly_addr = self.NormalizeAssemblyAddr
    self.normalize_log_range = self.NormalizeLogRange
    self.normalize_node_addr = self.NormalizeNodeAddr
    self.normalize_node_addrs = self.NormalizeNodeAddrs
    self.normalize_sub_addr = self.NormalizeSubAddr
    self.normalize_sub_addrs = self.NormalizeSubAddrs
    self.open_file = self.OpenModel
    self.read_dataset = self.GetH5DataSet
    self.read_dataset_axial_values = self.ReadDataSetAxialValues
    self.read_dataset_time_values = self.ReadDataSetTimeValues
    self.remove_listener = self.RemoveListener
    self.resolve_available_time_datasets = self.ResolveAvailableTimeDataSets
    self._resolve_data_model_name = self._ResolveDataModelName
    self.revert_if_derived_dataset = self.RevertIfDerivedDataSet
    self.save_dataset_thresholds = self.SaveDataSetThresholds
    self.set_dataset_threshold = self.SetDataSetThreshold
    self.set_time_dataset = self.SaveDataSetThresholds
    self._update_mesh_values = self._UpdateMeshValues
    self._update_time_values = self._UpdateTimeValues
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.AddListener()			-
  #----------------------------------------------------------------------
  def AddListener( self, event_name, listener ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener not in self.listeners[ event_name ]:
        self.listeners[ event_name ].append( listener )
    #end if event_name
  #end AddListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CalcRadialMesh()			-
  #----------------------------------------------------------------------
  def CalcRadialMesh( self,
      model_param, pin_col, pin_row, axial_level, assy_ndx, nrings
      ):
    """
    Args:
	model_param (DataSetName or str): a DataSetName instance or a
	    model name string
	pin_col (int): 0-based pin column index
	pin_row (int): 0-based row column index
	axial_level (int): 0-based axial index
        assy_ndx (int): 0-based assembly index
	nrings (int): number of radials
    Returns:
        list(float): nrings + 1 values from inside to outside (low to high)
"""
    mesh = None
    dm = self.GetDataModel( model_param )
    if dm is not None:
      area = \
          dm.core.pinVolumes[ pin_row, pin_col, axial_level, assy_ndx ] / \
          (dm.core.axialMesh[ axial_level + 1 ] - dm.core.axialMesh[ axial_level ])
      radius = math.sqrt( area / math.pi )
      mesh = DataUtils.CalcEqualAreaRadii( radius * 2, nrings )

    return  mesh
  #end CalcRadialMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CheckDataModelIsCompatible()	-
  #----------------------------------------------------------------------
  def CheckDataModelIsCompatible( self, dm ):
    """Checks dm for a compatible core geometry.
@param  dm		DataModel to check
@throws			HtmlException with message body snippet if incompatible
"""
    if dm:
      if not dm.HasData():
        raise  HtmlException( 'Incompatible', 'Required VERA data not found' )

      msg = ''

      if len( self.dataModelNames ) > 0:
	cur_core = self.core
	dm_core = dm.GetCore()
#			-- Core symmetry
#			--
	if cur_core.coreSym != dm_core.coreSym or \
	    cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_templ = """<ul>
<li>Incompatible core geometry</li>
<p/><table border="1" cellpadding="6" cellspacing="0">
<tr><th>Property</th><th>%(dm.name)s</th><th>Current</th></tr>
<tr><td>coreSym</td><td>%(dm_core.coreSym)d</td><td>%(cur_core.coreSym)d</td></tr>
<tr><td>nass</td><td>%(dm_core.nass)d</td><td>%(cur_core.nass)d</td></tr>
<tr><td>nassx</td><td>%(dm_core.nassx)d</td><td>%(cur_core.nassx)d</td></tr>
<tr><td>nassy</td><td>%(dm_core.nassy)d</td><td>%(cur_core.nassy)d</td></tr>
<tr><td>npinx</td><td>%(dm_core.npinx)d</td><td>%(cur_core.npinx)d</td></tr>
<tr><td>npiny</td><td>%(dm_core.npiny)d</td><td>%(cur_core.npiny)d</td></tr>
</table><p/>
"""
	  values = \
	    {
	    'cur_core.coreSym': cur_core.coreSym,
	    'cur_core.nass': cur_core.nass,
	    'cur_core.nassx': cur_core.nassx,
	    'cur_core.nassy': cur_core.nassy,
	    'cur_core.npinx': cur_core.npinx,
	    'cur_core.npiny': cur_core.npiny,
	    'dm.name': dm.name,
	    'dm_core.coreSym': dm_core.coreSym,
	    'dm_core.nass': dm_core.nass,
	    'dm_core.nassx': dm_core.nassx,
	    'dm_core.nassy': dm_core.nassy,
	    'dm_core.npinx': dm_core.npinx,
	    'dm_core.npiny': dm_core.npiny
	    }
	  msg = msg_templ % values

#			-- Core map
#			--
	if not np.array_equal( cur_core.coreMap, dm_core.coreMap ):
	  if len( msg ) == 0:
	    msg = '<ul>\n'
	  msg += '<li>CORE/core_map differs</li>\n'

#			-- Detector map
#			--
#	if self.detectorMap is not None and dm.HasDetectorData() and \
#	    not np.array_equal( cur_core.detectorMap, dm_core.detectorMap ):
#	  msg += '\n* detector_map differs\n'
      #end if len

      if msg:
	msg += '</ul>\n'
	raise HtmlException( 'Incompatible', msg )
    #end if dm
  #end CheckDataModelIsCompatible


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    names = list( self.dataModelNames )
    for dm_name in names:
      self.CloseModel( dm_name, True )
  #end Close


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CloseModel()			-
  #----------------------------------------------------------------------
  def CloseModel( self, model_param, closing_all = False ):
    """Opens the HDF5 file or filename.
@param  model_param	either a DataModel instance or a model name/ID string
@param  closing_all	if True, no local state updates are performed
@param  update_flag	True to update 
@return			True if removed, False if not found
"""
    result = False
    if isinstance( model_param, DataModel ):
      model_name = model_param.GetName()
    else:
      model_name = str( model_param )

    if model_name in self.dataModels:
      dm = self.dataModels[ model_name ]
      #model_name = dm.GetName()
      dm.RemoveListener( 'newDataSet', self )
      dm.Close()

      del self.dataModels[ model_name ]
      del self.timeValuesById[ model_name ]
      self.dataModelNames.remove( model_name )

      if not closing_all:
        if len( self.dataModelNames ) == 1:
	  #self.core = self.dataModels.get( self.dataModelNames[ 0 ] ).GetCore()
	  first_core = self.dataModels.get( self.dataModelNames[ 0 ] ).GetCore()
	  self.core = first_core.Clone()

        self._UpdateMeshValues()
        self._UpdateTimeValues()
        #self.dataSetNamesVersion += 1
	self._FireEvent( 'modelRemoved', model_name )
      #end if not closing_all

      result = True

    return  result
  #end CloseModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateAssemblyAddr()		-
  #----------------------------------------------------------------------
  def CreateAssemblyAddr( self, col, row ):
    """Creates tuple from the column and row indexes.
    Args:
        col (int): 0-based column index
        row (int): 0-based row index
    Returns:
        tuple: ( assy_ndx, col, row )
"""
    core = self.core
    if core is not None and \
	col >= 0 and row >= 0 and \
        col < core.coreMap.shape[ 1 ] and row < core.coreMap.shape[ 0 ]:
      result = ( core.coreMap[ row, col ] - 1, col, row )
    else:
      result = ( -1, -1, -1 )

    return  result
  #end CreateAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateAssemblyAddrFromIndex()      -
  #----------------------------------------------------------------------
  def CreateAssemblyAddrFromIndex( self, assy_ndx ):
    """Creates a 3-tuple from the 0-based assembly index.
    Args:
        assy_ndx (int): 0-based assembly index
    Returns:
        tuple: ( assy_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    if self.core is not None:
      places = np.argwhere( self.core.coreMap == assy_ndx + 1 )
      if len( places ) > 0:
        place = places[ -1 ]
        result = ( assy_ndx, int( place[ 1 ] ), int( place[ 0 ] ) )
    return  result
  #end CreateAssemblyAddrFromIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateDetectorAddr()		-
  #----------------------------------------------------------------------
  def CreateDetectorAddr( self, col, row ):
    """Creates tuple from the column and row indexes.
    Args:
        col (int): 0-based column index
        row (int): 0-based row index
    Returns:
        tuple: ( det_ndx, col, row )
"""
    core = self.core
    if core is not None and \
	col >= 0 and row >= 0 and \
        col < core.detectorMap.shape[ 1 ] and row < core.detectorMap.shape[ 0 ]:
      result = ( core.detectorMap[ row, col ] - 1, col, row )
    else:
      result = ( -1, -1, -1 )

    return  result
  #end CreateDetectorAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateDetectorAddrFromIndex()      -
  #----------------------------------------------------------------------
  def CreateDetectorAddrFromIndex( self, det_ndx ):
    """Creates a 3-tuple from the 0-based detector index.
    Args:
        det_ndx (int): 0-based detector index
    Returns:
        tuple: ( det_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    if self.core is not None:
      places = np.argwhere( self.core.detectorMap == det_ndx + 1 )
      if len( places ) > 0:
        place = places[ -1 ]
        result = ( det_ndx, int( place[ 1 ] ), int( place[ 0 ] ) )
    return  result
  #end CreateDetectorAddrFromIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateDiffDataSet()		-
  #----------------------------------------------------------------------
  def CreateDiffDataSet( self,
      ref_qds_name, comp_qds_name, diff_ds_name,
      diff_mode = 'delta', interp_mode = 'linear',
      listener = None
      ):
    """Create new difference dataset to be stored as a derived dataset in
the comp_qds_name model.  Thus, the axial mesh and time
values are from the comp_qds_name model.  The current timeDataSet is used
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
@deprecated  Just instantiate differences.Differences.
"""
    return \
    Differences( self )(
        ref_qds_name, comp_qds_name, diff_ds_name,
	listener
	)
  #end CreateDiffDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ExtractSymmetryExtent()		-
  #----------------------------------------------------------------------
  def ExtractSymmetryExtent( self ):
    """Returns the starting horizontal (left) and ending vertical (top)
assembly 0-based indexes, inclusive, and the right and bottom indexes,
exclusive, followed by the number of assemblies in the horizontal and vertical
dimensions.
@return			None if core is None, otherwise
			( left, top, right+1, bottom+1, dx, dy )
"""
    result = None

    core = self.GetCore()
    if core is not None:
      bottom = core.nassy
      right = core.nassx

      if core.coreSym == 4:
        left = 0  if core.nassx <= 2 else  core.nassx >> 1
        top = 0  if core.nassy <= 2 else  core.nassy >> 1
      elif core.coreSym == 8:
	left = core.nassx >> 2
	top = core.nassy >> 2
      else:
	left = 0
	top = 0

      result = ( left, top, right, bottom, right - left, bottom - top )
    #end if

    return  result  if result is not None else  ( 0, 0, 0, 0, 0, 0 )
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindChannelMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindChannelMinMaxValue(
      self, mode, qds_name, time_value, assy_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with channel addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'channel' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindChannelMinMaxValue(
	  mode, qds_name.displayName, state_ndx, assy_ndx,
	  cur_obj, use_factors
          )
      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindChannelMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindFluenceMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindFluenceMinMaxValue(
      self, mode, fluence_addr, time_value,
      cur_obj = None, ds_expr = None,
      radius_start_ndx = 0
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
    Args:
        mode (str): 'min' or 'max', defaulting to the latter
        fluence_addr (FluenceAddress): instance from dataSetName and other
            properties are obtained
        time_value (float): time value to search, or lt 0 for all times
        cur_obj (object): optional object with attributes/properties to compare
            against for changes:
                axialValue (AxialValue instance)
                fluenceAddr (FluenceAddress instance)
                stateIndex (int)
        ds_expr (str): expression to apply to dataset min/max search
        radius_start_ndx (int): starting 0-based index of radius range of
            validity
    Returns:
        dict: changes with possible keys: 'axial_value', 'fluence_addr',
            'state_index'
"""
    results = {}

    qds_name = fluence_addr.dataSetName
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindFluenceMinMaxValue(
	  mode, fluence_addr, state_ndx,
	  cur_obj, ds_expr, radius_start_ndx
          )

      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindFluenceMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindMultiDataSetMinMaxValue()	-
  #----------------------------------------------------------------------
  def FindMultiDataSetMinMaxValue(
      self, mode, time_value, assy_ndx,
      cur_obj, *qds_names
      ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the maximum value among all the
specified datasets.
@param  mode		'min' or 'max', defaulting to the latter
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  qds_names	dataset names to search, DataSetName instances
@return			dict with possible keys: 'assembly_addr',
			'axial_value', 'state_index', 'sub_addr'
"""
    results = {}
    dm = self.GetDataModel( qds_names[ 0 ] )  if qds_names else  None
    if dm:
      model_name = qds_names[ 0 ].modelName
      ds_names = []
      for q in qds_names:
        ds_names.append( q.displayName )

      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, model_name )

      results = dm.FindMultiDataSetMinMaxValue(
          mode, state_ndx, assy_ndx, cur_obj, *ds_names
	  )
      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], model_name )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm

    return  results
  #end FindMultiDataSetMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindPinMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindPinMinMaxValue(
      self, mode, qds_name, time_value, assy_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindPinMinMaxValue(
	  mode, qds_name.displayName, state_ndx, assy_ndx,
	  cur_obj, use_factors
          )

      if 'state_index' in results:
#	results[ 'time_value' ] = self.\
#	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindPinMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._FireEvent()			-
  #----------------------------------------------------------------------
  def _FireEvent( self, event_name, *params ):
    """Calls event_name listeners passing self and the params list.
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  params		event params
"""
    if event_name in self.listeners:
      #method_name = 'On' + event_name.capitalize()
      method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
      for listener in self.listeners[ event_name ]:
        if not listener:
	  self._logger.error( 'Listener is dead: %s', str( listener ) )
	elif hasattr( listener, method_name ):
	  getattr( listener, method_name )( self, *params )
	elif hasattr( listener, '__call__' ):
	  listener( self, *params )
      #end for listener
    #end if event_name
  #end _FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMesh()			-
  #----------------------------------------------------------------------
  def GetAxialMesh( self, qds_name = None ):
    """Retrieves the axialMesh property for the specified model or
the cross-model global mesh.
@param  qds_name	optional DataSetName instance
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    return  self.GetAxialMesh2( qds_name )
  #end GetAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMesh2()			-
  #----------------------------------------------------------------------
  def GetAxialMesh2( self, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh for the specified dataset or mesh type.
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'fluence', or 'all' for the combined mesh
			for all datasets
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    result = None
    if qds_name is not None:
      qds_name = DataSetName.Resolve( qds_name )
      dm = self.GetDataModel( qds_name )
      if dm:
	result = dm.GetAxialMesh( qds_name.displayName, mesh_type )

    if result is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      result = self.axialMeshDict.get( mesh_type )

    return  result  if result is not None else  self.axialMeshDict.get( 'all' )
  #end GetAxialMesh2


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self, model_name = None ):
    """Retrieves the axialMeshCenters property for the specified model or
the cross-model global mesh centers.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh centers for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( model_name )
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters2()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters2( self, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh centers for the specified dataset and/or
mesh type.
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'fixed_detector', 'pin',
			'subpin', 'fluence', or 'all' for the combined mesh
			for all datasets
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    result = None
    if qds_name is not None:
      qds_name = DataSetName.Resolve( qds_name )
      dm = self.GetDataModel( qds_name )
      if dm:
	result = dm.GetAxialMeshCenters( qds_name.displayName, mesh_type )

    if result is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      result = self.axialMeshCentersDict.get( mesh_type )

    return  \
        result  if result is not None else \
	self.axialMeshCentersDict.get( 'all' )
  #end GetAxialMeshCenters2


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCentersIndex()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCentersIndex(
      self, mesh_value,
      qds_name = None, mesh_type = 'pin'
      ):
    """Retrieves the index in the axial mesh for the specified value.
@param  mesh_value	mesh value in cm
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'fluence'
@return			0-based index in the mesh for the specified dataset
			or the cross-model global mesh if qds_name is None
			or not found
"""
    ndx = -1
    qds_name = DataSetName.Resolve( qds_name )
    mesh = self.GetAxialMeshCenters2( qds_name, mesh_type )
    if mesh is not None and len( mesh ) > 1:
      ndx = bisect.bisect_right( mesh, mesh_value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )

    return  ndx
  #end GetAxialMeshCentersIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshIndex()		-
  #----------------------------------------------------------------------
  def GetAxialMeshIndex( self, mesh_value, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh for the specified dataset or mesh type.
@param  mesh_value	mesh value in cm
@param  qds_name	optional DataSetName instance, overrides ``mesh_type``
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'fluence'
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    ndx = -1
    qds_name = DataSetName.Resolve( qds_name )
    mesh = self.GetAxialMesh2( qds_name, mesh_type )
    if mesh is not None and len( mesh ) > 1:
      ndx = bisect.bisect_right( mesh, mesh_value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )

    return  ndx
  #end GetAxialMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self, qds_name = None, **kwargs ):
    """Retrieves the axial value for the specified model, if specified.
Otherwise, the
cross-model levels are used and can be applied only with 'cm' and 'core_ndx'
arguments.  Calls ``CreateAxialValue()`` on the identified DataModel.
    Args:
        qds_name (DataSetName): optional dataset name from which to find the
            DataModel
    Keyword Args:
        cm (float): axial value in cm
        core_ndx (int): 0-based core/pin axial index
        detector_ndx (int): 0-based detector axial index
        fixed_detector_ndx (int): 0-based fixed detector axial index
        fluence_ndx (int): 0-based fluence axial index
        pin_ndx (int): 0-based core/pin axial index
        subpin_ndx (int): 0-based subpin axial index
        value (float): axial value in cm, alias for 'cm'
    Returns:
        AxialValue: instance
"""
    qds_name = DataSetName.Resolve( qds_name )
    results = self._GetAxialValueRec( qds_name, **kwargs )
    return  AxialValue( results )
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._GetAxialValueRec()		-
  #----------------------------------------------------------------------
  def _GetAxialValueRec( self, qds_name = None, **kwargs ):
    """Creates an axial index dict with keys 'cm', 'detector', 'fixed_detector',
'pin', 'subpin', 'fluence'.
@param  qds_name	optional DataSetName instance
Parameters:
  cm			axial value in cm
  cm_bin                range in cm
  core_ndx		0-based core axial index
  detector_ndx		0-based detector axial index
  fixed_detector_ndx	0-based fixed_detector axial index
  pin_ndx		alias for 'core_ndx'
  subpin_ndx		0-based subpin axial index
  fluence_ndx          	0-based fluence axial index
  value			alias for 'cm'
  xxx_ndx		0-based axial index for mesh type 'xxx'
@return			dictionary of axial index values
"""
    results = {}

    if qds_name:
      qds_name = DataSetName.Resolve( qds_name )
      dm = self.GetDataModel( qds_name )
      if dm:
	results = dm.CreateAxialValue( **kwargs )
	#results = dm.CreateAxialValueRec( **kwargs )

    elif self.core is not None:
      not_centers_names = set([ 'detector' ])
      predef_names = \
          set([ 'pin', 'detector', 'fixed_detector', 'subpin', 'fluence' ])

#		-- Process arguments
#		--
      for n, v in kwargs.iteritems():
	if n == 'cm' or n == 'value':
	  results[ 'cm' ] = kwargs.get( n )

        elif n.endswith( '_ndx' ):
	  name = n[ 0 : -4 ]
	  if name == 'core':
	    name = 'pin'
	  if name in not_centers_names:
	    mesh = self.axialMeshDict.get( name )
	  else:
	    mesh = self.axialMeshCentersDict.get( name )
	  if mesh is not None:
	    ndx = max( 0, min( v, len( mesh ) - 1 ) )
	    results[ name ] = ndx
            results[ 'cm' ] = mesh[ ndx ]

	else:
	  results[ n ] = kwargs.get( n )
	#end elif _ndx
      #end for n, v

#		-- Resolve predefined indexes
#		--
      for name in predef_names:
        ndx = results.get( name, -1 )
	if ndx < 0 and name in self.axialMeshDict:
	  mesh = self.axialMeshDict.get( name )
	  if len( mesh ) > 0:
	    ndx = DataUtils.FindListIndex( mesh[ : -1 ], results[ 'cm' ] )
	    #ndx = min( ndx, len( mesh ) -1 )
	results[ name ] = ndx
      #end for name

      results[ 'value' ] = results[ 'cm' ]
    #end elif self.core

    return  results
  #end _GetAxialValueRec


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetCore()				-
  #----------------------------------------------------------------------
  def GetCore( self, model_name = None ):
    """Retrieves the core property for the specified model or
the cross-model core.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			Core instance for the specified model or the
			cross-model instance if model_name is None
			or not found
"""
    #return  self.core
    result = self.core
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore()

    return  result
  #end GetCore


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self, model_param ):
    """Retrieves the DataModel by model name.  The param can be a string
model name or a DataSetName instance.
@param  model_param	a DataSetName instance or a model name string
@return			DataModel or None if not found
"""
    dm = None
    if model_param:
      model_name = \
          model_param.modelName \
	  if isinstance( model_param, DataSetName ) else \
	  str( model_param )
      dm = self.dataModels.get( model_name )

    return  dm
  #end GetDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelCount()		-
  #----------------------------------------------------------------------
  def GetDataModelCount( self ):
    return  len( self.dataModels )
  #end GetDataModelCount


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelNames()		-
  #----------------------------------------------------------------------
  def GetDataModelNames( self ):
    """
@return			list of model names
"""
    return  self.dataModelNames
  #end GetDataModelNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelDataSetNames()		-
  #----------------------------------------------------------------------
  def GetDataModelDataSetNames( self, qds_name, ds_type = None ):
    """Calls GetDataSetNames() on the model specified by qds_name.
    Retrieves the dataset types list for the specified model.
@param  qds_name	DataSetName instance
@param  ds_type		optional type name
@return			empty list if model name found, else
			if ds_type is not None, list of dataset names
			for ds_type or empty if not found, else
			if ds_type is None, copy of dict of dataset name lists
			by ds_type
			( 'axials', 'channel', 'detector', 'fixed_detector',
			  'pin', 'scalar', etc. )
"""
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetNames( ds_type )  if dm else []
  #end GetDataModelDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModels()			-
  #----------------------------------------------------------------------
  def GetDataModels( self ):
    """Accessor for the dataModels property.
@return			reference
"""
    return  self.dataModels
  #end GetDataModels


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetAttr()			-
  #----------------------------------------------------------------------
  def GetDataSetAttr( self, qds_name, attr_name, time_value ):
    """Retrieves the type for the name dataset.
    Args:
        qds_name (DataSetName): dataset name
        attr_name (str): attribute name
        time_value (float): time value
    Returns:
        obj: value of attribute or None if not found
"""
    attr_value = None
    dset = self.GetH5DataSet( qds_name, time_value )
    if dset is not None and dset.attrs and attr_name in dset.attrs:
      attr_value = dset.attrs[ attr_name ]
    return  attr_value
  #end GetDataSetAttr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetDefByQName()		-
  #----------------------------------------------------------------------
  def GetDataSetDefByQName( self, qds_name ):
    """Looks up the dataset definition dict for the type of the specified
dataset.
@param  qds_name	DataSetName instance
@return			dataset definition if found, None otherwise
"""
    ddef = None
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      ddef = dm.GetDataSetDefByDsName( qds_name.displayName )
    return  ddef
  #end GetDataSetDefByQName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, qds_name, short = False ):
    """If we have only a single model, we cull the model name for display
purpose.  Otherwise, we need the fully-qualified name.
@param  qds_name	DataSetName instance
@param  short		if true, only the first letter of the model name
			is shown
@return			qds_name.displayName if we have a single model,
			otherwise qds_name.shortName if short else
			qds_name.name
"""
    if isinstance( qds_name, DataSetName ):
      result = \
          qds_name.displayName  if len( self.dataModels ) <= 1 else \
	  qds_name.shortName  if short else \
	  qds_name.name
    else:
      result = str( qds_name )

    return  result
  #end GetDataSetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetHasSubAddr()		-
  #----------------------------------------------------------------------
  def GetDataSetHasSubAddr( self, qds_name ):
    """Looks up the dataset definition for the type of the specified
dataset to determine if it is addressible by sub_addr.
@param  qds_name	DataSetName instance
@return			True if addressible by sub_addr, False otherwise
"""
    result = False
    ddef = None

    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      ddef = dm.GetDataSetDefByDsName( qds_name.displayName )

    #if ddef and 'shape' in ddef:
    if ddef:
      ddef_shape = ddef.get( 'shape' )
      result = \
          len( ddef_shape ) == 4 and  \
	  ddef_shape[ 0 ] > 1 and ddef_shape[ 1 ] > 1

    return  result
  #end GetDataSetHasSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetScaleType()		-
  #----------------------------------------------------------------------
  def GetDataSetScaleType( self, qds_name ):
    """Looks up the scale types for the dataset name.
    Args:
        qds_name (DataSetName): name, cannot be None
    Returns:
        str: scale type name, defaulting to 'linear'
"""
    result = 'linear'
    if qds_name:
      qds_name = DataSetName.Resolve( qds_name )
      dm = self.GetDataModel( qds_name )
      if dm:
        result = dm.GetDataSetScaleType( qds_name.displayName )

    return  result
  #end GetDataSetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetScaleTypeAll()		-
  #----------------------------------------------------------------------
  def GetDataSetScaleTypeAll( self, log_mode = 'all', *qds_names ):
    """Looks up the scale types for the dataset name.
    Args:
	log_mode (str): 'all' or 'any' for log scale if all or any of
	    ``qds_names`` have a log type
        qds_names (list(DataSetName)): names to search
    Returns:
        str: scale type name, defaulting to 'linear'
"""
    result = 'linear'
    if qds_names:
      scale_types = []
      for qds_name in qds_names:
        scale_types.append( self.GetDataSetScaleType( qds_name ) )

      log_count = len( [ x for x in scale_types if x == 'log' ] )
      if log_mode == 'all':
        if log_count == len( scale_types ): result = 'log'
      else:
        if log_count > 0: result = 'log'
    #end if qds_names

    return  result
  #end GetDataSetScaleTypeAll


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetThreshold()		-
  #----------------------------------------------------------------------
  def GetDataSetThreshold( self, qds_name = None ):
    """Returns the range expression for the specified qds_name, or a list
of range expressions for all datasets.
@param  qds_name	DataSetName instance or None for all range expressions
@return			if qds_name specified, the RangeExpression instance
			if found otherwise None
			if qds_name is None list of
			( qds_name, RangeExpression ) pairs
"""
    result = None

    #if isinstance( qds_name, DataSetName ):
    if qds_name:
      qds_name = DataSetName.Resolve( qds_name )
      dm = self.GetDataModel( qds_name )
      if dm:
        result = dm.GetDataSetThreshold( qds_name.displayName )
    else:
      result = []
      for model_name in sorted( self.dataModelNames ):
        dm = self.dataModels.get( model_name )
	ranges = dm.GetDataSetThreshold()
	for ( ds_name, expr ) in sorted( ranges.iteritems() ):
	  result.append( ( DataSetName( model_name, ds_name ), expr ) )
      #end for model_name
    #end if-else qds_name

    return  result
  #end GetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetQNames()			-
  #----------------------------------------------------------------------
  def GetDataSetQNames( self, model_param, ds_type = None ):
    """Returns the qualified names (DataSetName instances) for ds_type,
for a single DataModel if model_param is specified or across all models.
If ds_type is None or empty, all types are matched.
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for all models
@param  ds_type		optional type name, where None matches all types
@return			empty list if model_param specified and not found,
			list of qualified names (DataSetName instances)
			otherwise
"""
    result = set()
    dm_list = []

    if model_param:
      dm = self.GetDataModel( model_param )
      if dm:
        dm_list.append( dm )
    else:
      dm_list = self.dataModels.values()

    for dm in dm_list:
      if ds_type:
        names = dm.GetDataSetNames( ds_type )
      else:
        names_dict = dm.GetDataSetNames()
	names = []
	for cur_names in names_dict.values():
	  names += cur_names

      for n in names:
        result.add( DataSetName( dm.GetName(), n ) )
    #end for dm

    return  sorted( list( result ) )
  #end GetDataSetQNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self, qds_name ):
    """Retrieves the type for the name dataset.
@param  qds_name	DataSetName instance
@return			type or None
"""
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetType( qds_name.displayName )  if dm else  None
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    """Creates a set of all dataset categories/types across all DataModel
instances.
@return			set of type names
"""
    ds_types = set()
    for dm in self.dataModels.values():
      ds_types |= set( dm.GetDataSetDefs().keys() )

    return  ds_types
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMesh()			-
  #----------------------------------------------------------------------
  def GetDetectorMesh( self, model_name = None ):
    """Retrieves the detectorMesh property for the specified model or
the cross-model global mesh.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh if model_name is None or is
			not found
"""
    return  self.GetAxialMesh2( model_name, 'detector' )
#    #return  self.detectorMesh
#
#    result = None
#    if model_name is not None:
#      dm = self.GetDataModel( model_name )
#      if dm:
#        result = dm.core.detectorMesh
#
#    if result is None:
#      result = self.axialMeshDict.get( 'detector' )
#
#    return  result
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMeshIndex()		-
  #----------------------------------------------------------------------
  def GetDetectorMeshIndex( self, value, model_name = None ):
    """Determines the 0-based index of the value in the mesh list such that
mesh[ ndx ] <= value < mesh[ ndx + 1 ].  If model_name is specified,
only the mesh for the specified model is used.  Otherwise, the global,
cross-model mesh is used.
@param  value		mesh value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshIndex( value, model_name, 'detector' )
#    ndx = -1
#    if isinstance( model_name, DataSetName ):
#      model_name = model_name.modelName
#    mesh = self.GetDetectorMesh( model_name )
#    if mesh is not None:
#      ndx = bisect.bisect_right( mesh, value ) - 1
#      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
#    #end if
#
#    return  ndx
  #end GetDetectorMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFactors()			-
  #----------------------------------------------------------------------
  def GetFactors( self, qds_name, use_pin_factors = False ):
    """Determines the factors from the dataset shape.
    Args:
        qds_name (DataSetName): dataset name
        use_pin_factors (bool): True to return pinFactors
    Returns:
        np.naddarray: factors array or None
"""
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    #return  dm.GetFactors( qds_name.displayName )  if dm is not None else  None
    result = None
    if dm is not None:
      result = \
          dm.pinFactors  if use_pin_factors else \
          dm.GetFactors( qds_name.displayName )

    return  result
  #end GetFactors


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFirstDataModel()		-
  #----------------------------------------------------------------------
  def GetFirstDataModel( self ):
    """Retrieves the first DataModel.
@return			DataModel or None if not found
"""
    return \
        self.dataModels.get( self.dataModelNames[ 0 ] ) \
	if len( self.dataModelNames ) > 0 else \
	None
#    dm = None
#    if len( self.dataModelNames ) > 0:
#      dm = self.dataModels.get( self.dataModelNames[ 0 ] )
#
#    return  dm
  #end GetFirstDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFirstDataSet()			-
  #----------------------------------------------------------------------
  def GetFirstDataSet( self, ds_type ):
    """Retrieves the first matching dataset.
@param  ds_type         datset category/type
@return                 DataSetName instance or None if not found
"""
    qds_name = None
    if ds_type:
      for model_name in self.dataModelNames:
        dm = self.dataModels.get( model_name )
        ds_name = dm.GetFirstDataSet( ds_type )
        if ds_name:
          qds_name = DataSetName( model_name, ds_name )
          break

    return  qds_name
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMesh()		-
  #----------------------------------------------------------------------
  def GetFixedDetectorMesh( self, qds_name = None ):
    """Retrieves the fixedDetectorMesh property for the specified model
or the cross-model global mesh.
@param  qds_name	DataSetName instance
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMesh2( qds_name, 'fixed_detector' )
  #end GetFixedDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCenters()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self, qds_name = None ):
    """Retrieves the fixedDetectorMeshCenters property for the specified model
or the cross-model global mesh centers.
@param  qds_name	DataSetName instance
@return			mesh centers for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( qds_name, 'fixed_detector' )
  #end GetFixedDetectorMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCentersIndex()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCentersIndex( self, value, model_name = None ):
    """Determines the 0-based index of the value in the mesh list such that
mesh[ ndx ] <= value < mesh[ ndx + 1 ].  If model_name is specified,
only the mesh for the specified model is used.  Otherwise, the global,
cross-model mesh is used.
@param  value		global time value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshCentersIndex( value, model_name, 'fixed_detector' )
#    ndx = -1
#    if isinstance( model_name, DataSetName ):
#      model_name = model_name.modelName
#    mesh = self.GetFixedDetectorMeshCenters( model_name )
#    if mesh is not None:
#      ndx = bisect.bisect_right( mesh, value ) - 1
#      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
#    #end if
#
#    return  ndx
  #end GetFixedDetectorMeshCentersIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFluenceMesh()			-
  #----------------------------------------------------------------------
  def GetFluenceMesh( self, model_name = None ):
    """Calls GetAxialMesh2( model_name, 'fluence' ).
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMesh2( model_name, 'fluence' )
  #end GetFluenceMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFluenceMeshCenters()		-
  #----------------------------------------------------------------------
  def GetFluenceMeshCenters( self, model_name = None ):
    """Calls GetAxialMeshCenters2( model_name, 'fluence' ).
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( model_name, 'fluence' )
  #end GetFluenceMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFluenceMeshIndex()		-
  #----------------------------------------------------------------------
  def GetFluenceMeshIndex( self, value, model_name = None ):
    """ Calls GetAxialMeshCentersIndex( value_model_name, 'fluence' ).
@param  value		global time value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshCentersIndex( value, model_name, 'fluence' )
  #end GetFluenceMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetH5DataSet()			-
  #----------------------------------------------------------------------
  def GetH5DataSet( self, qds_name, time_value ):
    """Calls GetStateDataSet() on the corresponding DataModel.
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for current timeDataSet
@return			h5py.Dataset object if found or None
"""
    dm = dset = None
    if qds_name is not None and time_value >= 0.0:
      qds_name = DataSetName.Resolve( qds_name )
      state_ndx = self.GetTimeValueIndex( time_value, qds_name.modelName )
      if state_ndx >= 0:
        dm = self.GetDataModel( qds_name )

    if dm is not None:
      dset = dm.GetStateDataSet( state_ndx, qds_name.displayName )
    return  dset
  #end GetH5DataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetMaxAxialValue()			-
  #----------------------------------------------------------------------
  def GetMaxAxialValue( self ):
    """Accessor for the maxAxialValue property.
@return			maximum axial value in cm
"""
    return  self.maxAxialValue
  #end GetMaxAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetNodeAddr()			-
  #----------------------------------------------------------------------
  def GetNodeAddr( self, sub_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  sub_addr	0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
@return			node addr in range [0,3], or -1 if sub_addr is invalid
"""
    node_addr = -1
    core = self.GetCore()
    if core is not None:
      cx = core.npinx >> 1
      cy = core.npiny >> 1 
      if mode == 'channel':
        cx += 1
	cy += 1

      node_addr = 2 if max( 0, sub_addr[ 1 ] ) >= cy else 0
      if max( 0, sub_addr[ 0 ] ) >= cx:
        node_addr += 1

    return  node_addr
  #end GetNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetNodeAddrs()			-
  #----------------------------------------------------------------------
  def GetNodeAddrs( self, sub_addrs, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  sub_addrs	list of 0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
@return			list of unique node addrs in range [0,3]
"""
    result = []
    for sub_addr in sub_addrs:
      ndx = self.GetNodeAddr( sub_addr, mode )
      if ndx >= 0 and ndx not in result:
        result.append( ndx )

    return  result
  #end GetNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetNodePinAddr()			-
  #----------------------------------------------------------------------
  def GetNodePinAddr( self, node_addr ):
    """Assumes 2x2 pin array.
    Args:
	node_addr (int): 0-3
    Returns
	tuple: ( pin_col, pin_row )
"""
    return \
        ( 1, 0 )  if node_addr == 1  else \
        ( 0, 1 )  if node_addr == 2  else \
        ( 1, 1 )  if node_addr == 3  else \
	( 0, 0 )
  #end GetNodePinAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetPinNodeAddr()			-
  #----------------------------------------------------------------------
  def GetPinNodeAddr( self, pin_col, pin_row ):
    """Assumes 2x2 pin array.
    Args:
        pin_col (int): 0 or 1
	pin_row (int): 0 or 1
    Returns
        int: node addr, 0, 1, 2, 3, or -1 if inputs invalid
"""
    pair = ( pin_col, pin_row )
    return \
        0  if pair == ( 0, 0 )  else \
        1  if pair == ( 1, 0 )  else \
        2  if pair == ( 0, 1 )  else \
        3  if pair == ( 1, 1 )  else \
	-1
  #end GetPinNodeAddr


##  #----------------------------------------------------------------------
##  #	METHOD:		DataModelMgr.GetRadialMesh()			-
##  #----------------------------------------------------------------------
##  def GetRadialMesh( self, nrings ):
##    """Retrieves or if necessary calculates the equal-area(volume) radial mesh
##for the specified number of rings.
##    Args:
##	nrings (int): number of radial rings
##"""
##    mesh = self.radialMeshDict.get( nrings )
##    if mesh is None:
##      mesh = DataUtils.CalcEqualAreaRadii( self.core.GetPinDiameter(), nrings )
##      self.radialMeshDict[ nrings ] = mesh
##    #end if mesh is None
##
##    return  mesh
##  #end GetRadialMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange(
      self, qds_name,
      time_value = -1.0,
      ds_expr = None,
      use_factors = False
      ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
    Args:
        qds_name (DataSetName): dataset name
	time_value (float): value for the current timeDataSet, or -1 for
	    global range
	ds_expr (str): optional numpy array index expression to apply to
	    the dataset (e.g., '[ :, :, :, 0, 0 ]')
	use_factors (bool): True to apply factors
    Returns:
        tuple: ( min_value, max_value ), possibly the range of floating pt
	    values or None if ``qds_name`` not found
"""
    result = None
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm is not None:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      result = \
          dm.GetRange( qds_name.displayName, state_ndx, ds_expr, use_factors )
    #end if dm
   
    return  result
  #end GetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetRangeAll()			-
  #----------------------------------------------------------------------
  def GetRangeAll( self, time_value = -1.0, use_factors = False, *qds_names ):
    """Calculates the range across all the specified datasets.
Note all requests for multiple ranges should flow through this method.
    Args:
	time_value (float): value for the current timeDataSet, or -1 for
	    global range
	use_factors (bool): True to apply factors
        qds_names (list): list of DataSetName instances
    Returns:
        tuple: ( min_value, max_value ), possibly the range of floating pt
	    values or None if none of ``qds_names`` exist
"""
    result = None

    if qds_names:
      for qds_name in qds_names:
	cur_range = \
	    self.GetRange( qds_name, time_value, use_factors = use_factors )
	if cur_range is None:
	  pass
	elif result is None:
	  result = list( cur_range )
        else:
	  result[ 0 ] = min( result[ 0 ], cur_range[ 0 ] )
	  result[ 1 ] = max( result[ 1 ], cur_range[ 1 ] )
      #end for qds_name
    #end if qds_names
   
#    if result is None:
#      result = DataModel.DEFAULT_range
    return  result
  #end GetRangeAll


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetSubAddrFromNode()		-
  #----------------------------------------------------------------------
  def GetSubAddrFromNode( self, node_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  node_addr	0, 1, 2, or 3
@param  mode		'channel' or 'pin', defaulting to the latter
@return			0-based sub_addr ( col, row )
"""
    core = self.GetCore()
    if core is None or node_addr < 0 or node_addr >= 4:
      sub_addr = ( -1, -1 )
    else:
      npinx = core.npinx
      npiny = core.npiny
      if mode == 'channel':
        npinx += 1
        npiny += 1
      col = 0 if node_addr in ( 0, 2 ) else npinx - 1
      row = 0 if node_addr in ( 0, 1 ) else npiny - 1

      sub_addr = ( col, row )

    return  sub_addr
  #end GetSubAddrFromNode


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeDataSet()			-
  #----------------------------------------------------------------------
  def GetTimeDataSet( self ):
    """Accessor for the timeDataSet property.
@return			dataset used for time
"""
    return  self.timeDataSet
  #end GetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeIndexValue()		-
  #----------------------------------------------------------------------
  def GetTimeIndexValue( self, ndx, model_name = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If model_name is specified,
only the list of values for the specified model are used.  Otherwise,
the global, cross-model values are used.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    value = -1

    values = None
    if ndx >= 0:
      if isinstance( model_name, DataSetName ):
        model_name = model_name.modelName
      values = self.GetTimeValues( model_name )
      if values:
        ndx = min( ndx, len( values ) -1 )
        value = values[ ndx ]

    return  value
  #end GetTimeIndexValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValueIndex()		-
  #----------------------------------------------------------------------
  def GetTimeValueIndex( self, value, model_param = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If model_param is specified,
only the list of values for the specified model are used.  Otherwise,
the global, cross-model values are used.
@param  value		global time value
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for global index
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    ndx = -1
    if isinstance( model_param, DataSetName ):
      model_param = model_param.modelName
    values = self.GetTimeValues( model_param )
    if values:
      ndx = bisect.bisect_right( values, value ) - 1
      ndx = max( 0, min( ndx, len( values ) - 1 ) )
    #end if

    return  ndx
  #end GetTimeValueIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValues()			-
  #----------------------------------------------------------------------
  def GetTimeValues( self, model_param = None ):
    """Retrieves the time dataset values for the specified model if 'id'
is not None, otherwise retrieves the union of values across all models.
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for global time values
@return			list of time dataset values for the specified model
			or across all models
"""
    if isinstance( model_param, DataSetName ):
      model_param = model_param.modelName

    return \
	self.timeValuesById[ model_param ] \
	if model_param and model_param in self.timeValuesById else \
	self.timeValues
  #end GetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasData()				-
  #----------------------------------------------------------------------
  def HasData( self ):
    return  len( self.dataModels ) > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasDataSet()			-
  #----------------------------------------------------------------------
  def HasDataSet( self, qds_name, time_value = 0.0 ):
    """Checks for existence of the specified dataset at the specified time.
    Args:
        qds_name (DataSetName): qualified dataset name to check
        time_value (float): time value in the current time dataset
    Returns:
        bool: True if the dataset exists, False otherwise
"""
    found = False
    dm = self.GetDataModel( qds_name )
    if dm is not None:
      time_ndx = self.GetTimeValueIndex( time_value, dm.name )
      found = dm.GetState( time_ndx ).HasDataSet( qds_name.displayName )

    return  found
  #end HasDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasDataSetType()			-
  #----------------------------------------------------------------------
  def HasDataSetType( self, ds_type ):
    """Convenience method to call HasDataSetType() on DataModel instances until 
True is returned.
@param  ds_type		one of type names, e.g., 'axials', 'channel', 'derived',
			'detector', 'fixed_detector', 'pin', 'scalar'
@return			True if there are datasets, False otherwise
"""
    found = False
    for dm in self.dataModels.values():
      found = dm.HasDataSetType( ds_type )
      if found:
        break

    return  found
  #end HasDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasNodalDataSetType()		-
  #----------------------------------------------------------------------
  def HasNodalDataSetType( self ):
    """Convenience method to call HasDataSetType() on DataModel instances until 
True is returned.
@param  ds_type		one of type names, e.g., 'axials', 'channel', 'derived',
			'detector', 'fixed_detector', 'pin', 'scalar'
@return			True if there are datasets, False otherwise
"""
    found = False
    for dm in self.dataModels.values():
      found = \
          dm.HasDataSetType( ':node' ) or \
	  dm.HasDataSetType( ':radial_node' )
      if found:
        break

    return  found
  #end HasNodalDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Is3DReady()			-
  #----------------------------------------------------------------------
  def Is3DReady( self ):
    """Checks having length gt 1 in all three dimensions.
"""
    core = self.GetCore()
    valid = \
        core is not None and \
	core.nax > 1 and \
	(core.nassx * core.npinx) > 1 and \
	(core.nassy * core.npiny) > 1

    return  valid
  #end Is3DReady


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsBadValue()			-
  #----------------------------------------------------------------------
  def IsBadValue( self, value ):
    """Checks for nan and inf.
@param  value		value to check
@return			True if nan or inf, False otherwise
"""
    #np.logical_or( np.isnan( value ), np.isinf( value ) )
    return  value is None or math.isnan( value ) or math.isinf( value )
  #end IsBadValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsChannelType()			-
  #----------------------------------------------------------------------
  def IsChannelType( self, qds_name ):
    """Determines if the qds_name represents a channel dataset.
@param  qds_name	DataSetName instance
@return			True if channel, False otherwise
"""
    result = False
    if self.core:
      dset = self.GetH5DataSet( qds_name, 0.0 )
      if dset:
	result = \
	    dset.shape[ 0 ] == self.core.npiny + 1 and \
	    dset.shape[ 1 ] == self.core.npinx + 1

    return  result
  #end IsChannelType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsDerivedDataSet()			-
  #----------------------------------------------------------------------
  def IsDerivedDataSet( self, qds_name ):
    """
@param  qds_name	name of dataset, DataSetName instance
@return			True if derived, false otherwise
"""
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    return  dm.IsDerivedDataSet( qds_name.displayName )  if dm else  False
  #end IsDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsDetectorOperable()		-
  #----------------------------------------------------------------------
  def IsDetectorOperable( self, det_ndx, time_value, model_name = None ):
    """Determines if there is/are 'detector_operable' datasets that mark
the det_ndx as inoperable.  If model_name is None, then all models must
report inoperability for the result to be False.
@param  det_ndx		0-based detector index
@param  time_value	time value
@param  model_name	optional model name, can be a DataSetName instance
@return			True if det_ndx for model_name or any model is
			operable, False if inoperable for model_name or
			all models
"""
    operable = False

    if model_name:
      model_names = [ model_name ]
    else:
      model_names = self.dataModelNames

    for name in model_names:
      det_operable_dset = None
      dm = self.GetDataModel( name )
      if dm:
        state_ndx = self.GetTimeValueIndex( time_value, name )
	det_operable_dset = dm.GetStateDataSet( state_ndx, 'detector_operable' )

      operable |= \
          (det_operable_dset is None or det_operable_dset[ det_ndx ] == 0)
      if operable:
        break
    #end for name

    return  operable
  #end IsDetectorOperable


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsNodalType()			-
  #----------------------------------------------------------------------
  def IsNodalType( self, ds_type ):
    """Determines if the category/type represents a nodal dataset.
@param  ds_type		dataset category/type
@return			True if nodal, False otherwise
"""
    return  \
        ds_type and \
        (ds_type.find( ':node' ) >= 0 or ds_type.find( ':radial_node' ) >= 0)
  #end IsNodalType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsValid()				-
  #----------------------------------------------------------------------
  def IsValid( self, qds_name, **kwargs ):
    """Checks values for validity w/in ranges available for the specified
dataset.
@param  qds_name	name of dataset, DataSetName instance
@param  kwargs		named values to check:
		'assembly_addr'
		'assembly_index'
		'axial_level'
		'dataset_name' (requires 'time_value')
		'node_addr'
		'sub_addr'
		'sub_addr_mode'
		  (either 'channel', or 'pin', defaulting to 'pin')
		'detector_index'
		'time_value'
"""
    valid = False
    dm = self.GetDataModel( qds_name )
    if dm:
      if 'dataset_name' in kwargs:
        state_index = self.GetTimeValueIndex( kwargs.get( 'time_value', 0.0 ) )
	if state_index >= 0:
	  kwargs[ 'state_index' ] = state_index
      valid = dm.IsValid( **kwargs )

    return  valid
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.LoadDataSetThresholds()		-
  #----------------------------------------------------------------------
  def LoadDataSetThresholds( self, expr_dict ):
    """Deserializes the names and threshold expressions.
@param  expr_dict	dict of expressions by DataSetName.name
"""
    for ( name_str, expr_str ) in expr_dict.iteritems():
      try:
        qds_name = DataSetName( name_str )
        dm = self.GetDataModel( qds_name )
        if dm:
	  dm.SetDataSetThreshold( qds_name.displayName, expr_str )
      except Exception, ex:
        self.logger.exception( 'qds_name=%s, expr=%s', qds_name.name, expr_str )
    #end for ( name_str, expr_str )
  #end LoadDataSetThresholds


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeAssemblyAddr()		-
  #----------------------------------------------------------------------
  def NormalizeAssemblyAddr( self, assy_ndx ):
    core = self.GetCore()
    if core is None:
      result = ( -1, -1, -1 )
    else:
      result = \
        (
        max( 0, min( assy_ndx[ 0 ], core.nass - 1 ) ),
        max( 0, min( assy_ndx[ 1 ], core.nassx - 1 ) ),
        max( 0, min( assy_ndx[ 2 ], core.nassy - 1 ) )
        )
    return  result
  #end NormalizeAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeLogRange()		-
  #----------------------------------------------------------------------
  def NormalizeLogRange( self, data_range ):
    """Forces the ranges to be positive.
    Args:
        data_range (list or tuple): range_min, range_max, data_min, data_max
    Returns:
        tuple: range_min, range_max, data_min, data_max
"""
    new_range = list( data_range )
    for i in xrange( 0, 3, 2 ):
      if len( new_range ) >= i + 1 and new_range[ i ] <= 0.0:
	if new_range[ i + 1 ] <= 0.0:
	  new_range[ i ] = 1.0
	  new_range[ i + 1 ] = 10.0
	else:
	  new_range[ i ] = new_range[ i + 1 ] / 100.0
#	  new_range[ i ] = \
#	      new_range[ i + 1 ] / 10.0  if new_range[ i + 1 ] < 1.0 else \
#	      1.0
      #end if len( new_range ) >= i + 1 and new_range[ i ] <= 0.0
    #end for i in xrange( 0, 3, 2 )

    return  tuple( new_range )
  #end NormalizeLogRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeNodeAddr()		-
  #----------------------------------------------------------------------
  def NormalizeNodeAddr( self, ndx ):
    """Here for completeness.
@param  ndx		0-based index
"""
    return  DataUtils.NormalizeNodeAddr( ndx )
  #end NormalizeNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeNodeAddrs()		-
  #----------------------------------------------------------------------
  def NormalizeNodeAddrs( self, addr_list ):
    """Normalizes each index in the list.
@param  addr_list	list of 0-based indexes
"""
    return  DataUtils.NormalizeNodeAddrs( addr_list )
  #end NormalizeNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeSubAddr()			-
  #----------------------------------------------------------------------
  def NormalizeSubAddr( self, addr, mode = 'pin' ):
    """Normalizes the address, accounting for channel shape being one greater
in each dimension.
@param  addr		0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    core = self.GetCore()
    if core is None:
      result = ( -1, -1 )
    else:
      maxx = core.npinx - 1
      maxy = core.npiny - 1
      if mode == 'channel':
        maxx += 1
        maxy += 1

      result = \
        (
        max( 0, min( addr[ 0 ], maxx ) ),
        max( 0, min( addr[ 1 ], maxy ) )
        )
    return  result
  #end NormalizeSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeSubAddrs()		-
  #----------------------------------------------------------------------
  def NormalizeSubAddrs( self, addr_list, mode = 'pin' ):
    """Normalizes each address in the list, accounting for channel shape
being one greater in each dimension.
@param  addr_list	list of 0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    core = self.GetCore()
    if core is None:
      maxx = maxy = -1
    else:
      maxx = core.npinx - 1
      maxy = core.npiny - 1
      if mode == 'channel':
        maxx += 1
        maxy += 1

    result = []
    for addr in addr_list:
      result.append( (
          max( 0, min( addr[ 0 ], maxx ) ),
          max( 0, min( addr[ 1 ], maxy ) )
	  ) )

    return  list( set( result ) )
  #end NormalizeSubAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._OnNewDataSet()			-
  #----------------------------------------------------------------------
  def _OnNewDataSet( self, model, ds_name ):
    """Callback for model 'newDataSet' events.
"""
    #self.dataSetNamesVersion += 1
    self._FireEvent( 'dataSetAdded', model, ds_name )
  #end _OnNewDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.OpenModel()			-
  #----------------------------------------------------------------------
  def OpenModel( self, h5f_param ):
    """Opens the HDF5 file or filename.
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
@return			new DataModel object
@throws			Exception with error or incompatibility message
"""
#		-- Assert on file read
#		--
    dm = None
    try:
      #id = str( uuid.uuid4() )
      #dm = DataModel( h5f_param, id )
      dm = DataModel( h5f_param )
    except Exception, ex:
      #msg = 'Error reading "%s": %s' % ( h5f_param, ex.message )
      msg = 'Error reading "{0}":\n{1}'.format( h5f_param, ex.message )
      output = cStringIO.StringIO()
      try:
        print >> output, msg
        traceback.print_exc( 10, output )
        self.logger.error( output.getvalue() )
      finally:
        output.close()
      raise  IOError( msg )

#		-- Assert on compatibility
#		--
    self.CheckDataModelIsCompatible( dm )

#		-- Process
#		--
    try:
      #xxxxx check for duplicate path, dm.GetH5File().filename
      model_name = self._ResolveDataModelName( dm )
      dm.AddListener( 'newDataSet', self._OnNewDataSet )
      self.dataModelNames.append( model_name )
      self.dataModels[ model_name ] = dm

      if len( self.dataModelNames ) == 1:
        #self.core = dm.GetCore()
	self.core = dm.GetCore().Clone()

      self._UpdateMeshValues()
      self._UpdateTimeValues()
      #self.dataSetNamesVersion += 1
      self._FireEvent( 'modelAdded', dm.GetName() )

      return  dm

    except Exception, ex:
      msg = 'Error processing "%s": %s' % ( h5f_param, ex.message )
      self.logger.error( msg )
      raise  IOError( msg )
  #end OpenModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ReadDataSetAxialValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetAxialValues( self,
      qds_name,
      assembly_index = 0,
      fluence_addr = None,
      node_addrs = None,
      sub_addrs = None,
      detector_index = 0,
      time_value = 0.0
      ):
    """Reads axial values for a dataset for a specified time value.  Note the
returned values are over the appropriate mesh (axial mesh centers, detector
mesh, fixed detector mesh centers) for the DataModel.
Calls ReadDataSetAxialValues() on the matching DataModel if found.
    Args:
        qds_name (data.datamodel.DataSetName): dataset name, cannot be none
	assembly_index (int): optional 0-based assembly index
	detector_index (int): optional 0-based detector index
	fluence_addr (FluenceAddress): optional fluence address
	node_addrs (list(int)): optional list of node indexes
	sub_addrs (list(pin_col,pin_row)): optional list of 0-based pin
	   col and row indexes
	time_value (float): timeDataSet value
    Returns:
        tuple( np.ndarray, dict or np.ndarray ): None if ds_name cannot be found
	    or processed, otherwise mesh_values and results, where the latter
	    is a dict by sub_addr (or node col,row) of np.ndarray for datasets
	    that vary by sub_addr, np.ndarray for other datasets.
"""
    result = None
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      state_index = self.GetTimeValueIndex( time_value, qds_name )
      result_pair = dm.ReadDataSetAxialValues(
          qds_name.displayName,
	  assembly_index = assembly_index,
	  detector_index = detector_index,
	  fluence_addr = fluence_addr,
	  node_addrs = node_addrs,
	  state_index = state_index,
	  sub_addrs = sub_addrs
	  )
      if result_pair is not None:
        result = dict( data = result_pair[ 1 ], mesh = result_pair[ 0 ] )
    #end if dm

    return  result
  #end ReadDataSetAxialValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ReadDataSetTimeValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetTimeValues( self, *ds_specs_in ):
    """Reads values for datasets across time, axial values for a dataset for a specified time value.
    Args:
	ds_specs_in (list): list of dataset specifications with the following
	    keys:
	      assembly_index	0-based assembly index
	      axial_cm		axial value in cm
	      detector_index	0-based detector index for detector datasets
	      ds_name		required dataset name, where a '*' prefix
				means it's not a time-based dataset but
				rather another dataset to be treated as
				the time basis
	      fluence_addr	FluenceAddress
	      node_addrs	list of node addrs
	      sub_addrs		list of sub_addr pairs
    Returns:
        dict: dict keyed by found qds_name of:
	    {
	    'data': either
	        dict keyed by sub_addr of np.ndarray for pin-based datasets, or
		np.ndarray for datasets that are not pin-based,
	    'times': np.ndarray of times
	    }
"""
    results = {}

#		-- Collate specs by model name
#		--
    specs_by_model = {}
    for spec in ds_specs_in:
      if spec is not None and 'qds_name' in spec:
	qds_name = spec[ 'qds_name' ]
	model_name = qds_name.modelName
	if model_name in self.dataModels:
          spec_list = specs_by_model.get( model_name )
	  if spec_list is None:
	    spec_list = []
	    specs_by_model[ model_name ] = spec_list
	  spec[ 'ds_name' ] = qds_name.displayName
          spec_list.append( spec )
	#end if model_name
      #end if value spec
    #end for spec

    for model_name, spec_list in specs_by_model.iteritems():
      time_values = np.array( self.timeValuesById.get( model_name ) )
      dm = self.dataModels.get( model_name )
      if dm is not None and time_values is not None:
        model_results = dm.ReadDataSetTimeValues( *spec_list )
	for ds_name, item in model_results.iteritems():
	  qds_name = DataSetName( model_name, ds_name )
	  # this is either a dict or a np.ndarray
	  item = model_results[ ds_name ]
	  results[ qds_name ] = dict( data = item, times = time_values )
	#end for ds_name
    #end for model_name, spec_list

    return  results
  #end ReadDataSetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.RemoveListener()			-
  #----------------------------------------------------------------------
  def RemoveListener( self, event_name, listener ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener in self.listeners[ event_name ]:
	self.listeners[ event_name ].remove( listener )
    #end if event_name
  #end RemoveListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ResolveAvailableTimeDataSets()	-
  #----------------------------------------------------------------------
  def ResolveAvailableTimeDataSets( self ):
    """Determines which time datasets are available across all models.
The fallback is 'state', meaning state point index.
@return			list of ds names
"""
    time_ds_names = set([ 'state' ])
    for name in TIME_DS_NAMES:
      found = True
      for dm in self.dataModels.values():
        st = dm.GetState()
	if not (st and st.HasDataSet( name )):
	  found = False
	  break
      #end for dm

      if found:
        name = DS_NAME_ALIASES_FORWARD.get( name, name )
        time_ds_names.add( name )
    #end for name

    return  list( time_ds_names )
  #end ResolveAvailableTimeDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._ResolveDataModelName()		-
  #----------------------------------------------------------------------
  def _ResolveDataModelName( self, dm ):
    """Checks for a name clash, appending to the name as necessary to make it
unique.  Calls dm.SetName() if necessary.
@param  dm		DataModel to check
@return			resulting name for dm
"""
    name = None
    if dm:
      cur_name = dm.GetName()
      ndx = 2
      while cur_name in self.dataModelNames:
        cur_name = '%s_%d' % ( dm.GetName(), ndx )
	ndx += 1
      #end while

      name = cur_name
      if name != dm.GetName():
        dm.SetName( name )

    return  name
  #end _ResolveDataModelName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.RevertIfDerivedDataSet()		-
  #----------------------------------------------------------------------
  def RevertIfDerivedDataSet( self, qds_name ):
    """If qds_name is a derived dataset, return the first dataset of the
base type.  Calls GetFirstDataSet().
Note: We are now hard-coding this to look for ':chan_xxx' for
a derived type, in which case we pass 'channel' to GetFirstDataSet().  For all
other derived types we pass 'pin'.
@param  qds_name	name of dataset, DataSetName instance
@return			ds_name if it is not derived, the first dataset from
			the base category/type if it is derived
"""
    result = None
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      ds_name = dm.RevertIfDerivedDataSet( qds_name.displayName )
      if ds_name:
        result = DataSetName( qds_name.modelName, ds_name )

    return  result
  #end RevertIfDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SaveDataSetThresholds()		-
  #----------------------------------------------------------------------
  def SaveDataSetThresholds( self ):
    """Serializes the names and threshold expressions.
@return			dict of expressions by DataSetName
"""
    result = {}
    for ( model_name, dm ) in self.dataModels.iteritems():
      expr_dict = dm.GetDataSetThreshold()
      for ( ds_name, expr ) in expr_dict.iteritems():
        result[ DataSetName( model_name, ds_name ).name ] = expr.displayExpr
      #end for ( ds_name, expr )
    #end for ( model_name, dm )

    return  result
  #end SaveDataSetThresholds


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SetDataSetThreshold()		-
  #----------------------------------------------------------------------
  def SetDataSetThreshold( self, qds_name, range_expr = None ):
    """Adds or replaces the ignore range expressions for the specified
dataset.
@param  qds_name	DataSetName instance
@param  range_expr	either an expression string, a RangeExpression
			instance, or None to remove the threshold
@param  op_value_pairs	sequence of op-value pairs, where op is one of
			'=', '<', '<=', '>', '>='
"""
    qds_name = DataSetName.Resolve( qds_name )
    dm = self.GetDataModel( qds_name )
    if dm:
      dm.SetDataSetThreshold( qds_name.displayName, range_expr )
  #end SetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SetTimeDataSet()			-
  #----------------------------------------------------------------------
  def SetTimeDataSet( self, ds_name ):
    """Accessor for the timeDataSet property.
@param  ds_name		cross-model dataset used for time
"""
    self.timeDataSet = ds_name
    self._UpdateTimeValues()
  #end SetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateMeshValues()		-
  #----------------------------------------------------------------------
  def _UpdateMeshValues( self ):
    """Updates the allMesh, allMeshCenters, axialMesh, axialMeshCenters,
detectorMap, detectorMesh, fixedDetectorMesh, fixedDetectorMeshCenters,
tallyMesh, tallyMeshCenters, and maxAxialValue properties.
@return			maxAxialValue property value
"""
    #--------------------------------------------------------------------
    #	INNER METHOD:	is_offset_mesh()				-
    #--------------------------------------------------------------------
    def is_offset_mesh( global_set, cur_mesh ):
      result = False
      global_mesh = np.array( sorted( global_set ), dtype = np.float64 )
      if global_mesh.shape == cur_mesh.shape:
        global_diffs = global_mesh[ 1 : ] - global_mesh[ 0 : -1 ]
        cur_diffs = cur_mesh[ 1 : ] - cur_mesh[ 0 : -1 ]
	result = np.array_equal( global_diffs, cur_diffs )

      return  result
    #end is_offset_mesh

    #--------------------------------------------------------------------
    #	INNER METHOD:	update_mesh()					-
    #--------------------------------------------------------------------
    def update_mesh( global_meshes, dm, dm_mesh_dict ):
      max_value = -1
      dm_mesh_updates = {}
      for cur_type, cur_mesh in dm_mesh_dict.iteritems():
	if cur_type and len( cur_mesh ) > 0:
	  if cur_type in global_meshes:
	    cur_global = global_meshes[ cur_type ]
	  else:
	    cur_global = set()
	    global_meshes[ cur_type ] = cur_global

	  if cur_type == 'pin' and is_offset_mesh( cur_global, cur_mesh ):
	    dm_mesh_updates[ cur_type ] = np.array( sorted( cur_global ) )
	  else:
	    max_value = max( max_value, cur_mesh[ -1 ] )
	    cur_mesh_set = set( cur_mesh )
	    cur_global.update( cur_mesh_set )
	    if not (cur_type == 'detector' and dm.core.detectorMeshIsCopied):
	      global_meshes[ 'all' ].update( cur_mesh_set )
	  #end else not is_offset_mesh( cur_global, cur_mesh )
	#end if cur_type and len( cur_mesh ) > 0
      #end for cur_name, cur_mesh

      for t, m in dm_mesh_updates.iteritems():
        dm_mesh_dict[ t ] = m

      return  max_value
    #end update_mesh

    #--------------------------------------------------------------------
    #	Method Body                                                     -
    #--------------------------------------------------------------------
    self.detectorMap = None
    self.maxAxialValue = -1.0
    global_mesh_centers = { 'all': set() }
    global_meshes = { 'all': set() }

    for dm in self.dataModels.values():
      core = dm.GetCore()
      if core is not None:
	self.maxAxialValue = max(
	    self.maxAxialValue,
	    update_mesh( global_meshes, dm, dm.axialMeshDict )
	    )

        if self.detectorMap is None and dm.HasDetectorData():
          self.detectorMap = np.copy( dm.core.detectorMap )
      #end if core
    #end for dm

    for k, v in global_meshes.iteritems():
      if k != 'detector':
	vdata = np.array( sorted( list( v ) ), dtype = np.float64 )
        global_mesh_centers[ k ] = (vdata[ 0 : -1 ] + vdata[ 1 : ]) / 2.0

#		-- Convert sets to list
#		--
    self.axialMeshDict.clear()
    for n, v in global_meshes.iteritems():
      self.axialMeshDict[ n ] = list( sorted( v ) )

    self.axialMeshCentersDict.clear()
    for n, v in global_mesh_centers.iteritems():
      self.axialMeshCentersDict[ n ] = list( sorted( v ) )

    return  self.maxAxialValue
  #end _UpdateMeshValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateTimeValues()		-
  #----------------------------------------------------------------------
  def _UpdateTimeValues( self ):
    """Updates the timeValues and timeValuesById properties based on the
open DataModels and the timeDataSet property.
@return			timeValues property value
"""
    result = []

    if self.timeDataSet == 'state':
      cur_count = 0
      for name, dm in self.dataModels.iteritems():
	#self.timeValuesById[ name ] = range( dm.GetStatesCount() )
	self.timeValuesById[ name ] = range( 1, dm.GetStatesCount() + 1 )
        cur_count = max( cur_count, dm.GetStatesCount() )
      #result = range( cur_count )
      result = range( 1, cur_count + 1 )

    elif self.timeDataSet:
      spec = dict( ds_name = self.timeDataSet )
      for name, dm in self.dataModels.iteritems():
	cur_values = dm.ReadDataSetTimeValues( spec )
	if cur_values and self.timeDataSet in cur_values:
          if self.timeDataSet.find( 'exposure' ) == 0:
            time_values = cur_values[ self.timeDataSet ]
            cur_values[ self.timeDataSet ] = time_values.round( 3 )
	  cur_list = cur_values[ self.timeDataSet ].tolist()
	  cur_list = DataUtils.FixDuplicates( cur_list )
	  self.timeValuesById[ name ] = cur_list
	  result = DataUtils.MergeList( result, *cur_list )
	else:
	  self.timeValuesById[ name ] = []
    #end if-elif

    #result.sort()
    self.timeValues = result
    return  result
  #end _UpdateTimeValues


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.main()				-
  #----------------------------------------------------------------------
#  @staticmethod
#  def main():
#    try:
#      if len( sys.argv ) < 2:
#        print >> sys.stderr, 'Usage: datamodel.py casl-output-fname'
#
#      else:
#        data = DataModel( sys.argv[ 1 ] )
#	print str( data )
#      #end if-else
#
#    except Exception, ex:
#      print >> sys.stderr, str( ex )
#      et, ev, tb = sys.exc_info()
#      while tb:
#	print >> sys.stderr, \
#            'File=' + str( tb.tb_frame.f_code ) + \
#            ', Line=' + str( traceback.tb_lineno( tb ) )
#        tb = tb.tb_next
#      #end while
#  #end main
#end DataModelMgr


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
#if __name__ == '__main__':
  #DataModelMgr.main()
