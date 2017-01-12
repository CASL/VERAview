#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
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

from data.datamodel import *
from data.utils import *
from event.event import *


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


#		-- Class Attributes
#		--


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
    self.axialMesh = None
    self.axialMeshCenters = None
    self.core = None
    self.dataModelNames = []
    self.dataModels = {}
    #self.dataSetNamesVersion = 0
    self.detectorMap = None
    self.detectorMesh = None
    self.fixedDetectorMesh = None
    self.fixedDetectorMeshCenters = None
    self.listeners = \
        { 'dataSetAdded': [], 'modelAdded': [], 'modelRemoved': [] }
    self.logger = logging.getLogger( 'data' )
    self.maxAxialValue = 0.0
    self.timeDataSet = 'state'
    self.timeValues = []
    self.timeValuesById = {}
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
  #	METHOD:		DataModelMgr._CheckDataModelIsCompatible()	-
  #----------------------------------------------------------------------
  def _CheckDataModelIsCompatible( self, dm ):
    """Checks dm for a compatible core geometry.
@param  dm		DataModel to check
@throws			Exception with message if incompatible
"""
    if dm:
      if not dm.HasData():
        raise  Exception( 'Required VERA data not found' )

      msg = ''

      if len( self.dataModelNames ) > 0:
        #cur_dm = self.dataModels[ self.dataModelNames[ 0 ] ]
        #cur_core = cur_dm.GetCore()
	cur_core = self.core
	dm_core = dm.GetCore()
#			-- Core symmetry
#			--
	if cur_core.coreSym != dm_core.coreSym or \
	    cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_fmt = \
	      '\n* Incompatible core geometry:\n' + \
	      '\tcoreSym=%d, nass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d\n' + \
	      'is not compatible with\n' + \
	      '\tcoreSym=%d, nass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d'
	  msg = msg_fmt % (
	      dm_core.coreSym, dm_core.nass,
	      dm_core.nassx, dm_core.nassy,
	      dm_core.npinx, dm_core.npiny,
	      cur_core.coreSym, cur_core.nass,
	      cur_core.nassx, cur_core.nassy,
	      cur_core.npinx, cur_core.npiny
	      )

#			-- Core map
#			--
	if not np.array_equal( cur_core.coreMap, dm_core.coreMap ):
	  msg += '\n* core_map differs\n'

#			-- Detector map
#			--
	if self.detectorMap is not None and dm.HasDetectorData() and \
	    not np.array_equal( cur_core.detectorMap, dm_core.detectorMap ):
	  msg += '\n* detector_map differs\n'
      #end if len

      if msg:
        raise  Exception( msg )
    #end if dm
  #end _CheckDataModelIsCompatible


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
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( assy_ndx, col, row )
"""
    core = self.GetCore()
    return \
        ( core.coreMap[ row, col ], col, row ) \
	if core is not None else \
	( -1, -1, -1 )
  #end CreateAssemblyAddr


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
    #bounds = ( -1, -1, -1, -1, 0, 0 )
    #left = -1
    #bottom = -1
    #right = -1
    #top = -1

    result = None

    core = self.GetCore()
    if core is not None:
      bottom = core.nassy
      right = core.nassx

      #xxxxx decrementing on even nassx and nassy
      if core.coreSym == 4:
	left = core.nassx >> 1
	top = core.nassy >> 1
	if core.nassx % 2 == 0 and left > 0: left -= 1
	if core.nassy % 2 == 0 and top > 0: top -= 1
      elif core.coreSym == 8:
	left = core.nassx >> 2
	top = core.nassy >> 2
	if core.nassx % 2 == 0 and left > 0: left -= 1
	if core.nassy % 2 == 0 and top > 0: top -= 1
      else:
	left = 0
	top = 0

      result = ( left, top, right, bottom, right - left, bottom - top )
    #end if

    return  result  if result is not None else ( 0, 0, 0, 0, 0, 0 )
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindChannelMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindChannelMinMaxValue(
      self,
      mode, qds_name, time_value,
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
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindChannelMinMaxValue(
	  mode, qds_name.displayName, state_ndx,
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
  #	METHOD:		DataModelMgr.FindMultiDataSetMinMaxValue()	-
  #----------------------------------------------------------------------
  def FindMultiDataSetMinMaxValue( self, mode, time_value, cur_obj, *qds_names ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the maximum value among all the
specified datasets.
@param  mode		'min' or 'max', defaulting to the latter
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
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

      results = \
          dm.FindMultiDataSetMinMaxValue( mode, state_ndx, cur_obj, *ds_names )
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
      self,
      mode, qds_name, time_value,
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
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindPinMinMaxValue(
	  mode, qds_name.displayName, state_ndx,
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
      #method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
      method_name = 'On' + event_name.capitalize()
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
  def GetAxialMesh( self, model_name = None ):
    """Retrieves the axialMesh property for the specified model or
the cross-model global mesh.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    result = self.axialMesh
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore().axialMesh

    return  result
  #end GetAxialMesh


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
    #return  self.axialMeshCenters
    result = self.axialMeshCenters
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore().axialMeshCenters

    return  result
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self, model_name = None, **kwargs ):
    """Retrieves the axial value tuple ( axial_cm, core_ndx, detector_ndx,
fixed_detector_ndx ) for the model with 'id' if specified.  Otherwise, the
cross-model levels are used and can be applied only with 'cm' and 'core_ndx'
arguments.  Calls CreateAxialValue() on the identified DataModel.
@param  model_name	a DataSetName instance, model name, or None for
			global axial values
@param  kwargs		arguments
    cm				axial value in cm
    core_ndx			0-based core axial index
    detector_ndx		0-based detector axial index
    fixed_detector_ndx		0-based fixed_detector axial index
    pin_ndx			0-based core axial index, alias for 'core_ndx'
    value			axial value in cm, alias for 'cm'
@return			( axial_cm, core_ndx, detector_ndx, fixed_detector_ndx )
"""
    core_ndx = -1
    det_ndx = -1
    fdet_ndx = -1
    axial_cm = -1.0  # 0.0

    if model_name:
      dm = self.GetDataModel( model_name )
      if dm:
	axial_cm, core_ndx, det_ndx, fdet_ndx = dm.CreateAxialValue( **kwargs )

    elif 'cm' in kwargs or 'value' in kwargs:
      axial_cm = kwargs.get( 'cm', kwargs.get( 'value', 0.0 ) )
      core_ndx = DataUtils.FindListIndex( self.axialMeshCenters, axial_cm )
      det_ndx = DataUtils.FindListIndex( self.detectorMesh, axial_cm )
      fdet_ndx = DataUtils.FindListIndex( self.fixedDetectorMeshCenters, axial_cm )

    elif 'core_ndx' in kwargs or 'pin_ndx' in kwargs:
      if self.axialMeshCenters:
        core_ndx = kwargs.get( 'core_ndx', kwargs.get( 'pin_ndx', 0 ) )
        core_ndx = max( 0, min( core_ndx, len( self.axialMeshCenters ) - 1 ) )
        axial_cm = self.axialMeshCenters[ core_ndx ]
        det_ndx = DataUtils.FindListIndex( self.detectorMesh, axial_cm )
        fdet_ndx = DataUtils.FindListIndex( self.fixedDetectorMeshCenters, axial_cm )

    elif 'detector_ndx' in kwargs:
      if self.detectorMesh:
        det_ndx = kwargs[ 'detector_ndx' ]
        det_ndx = max( 0, min( det_ndx, len( self.detectorMesh ) - 1 ) )
        axial_cm = self.detectorMesh[ det_ndx ]
        core_ndx = DataUtils.FindListIndex( self.axialMeshCenters, axial_cm )
        fdet_ndx = DataUtils.FindListIndex( self.fixedDetectorMeshCenters, axial_cm )

    elif 'fixed_detector_ndx' in kwargs:
      if self.fixedDetectorMeshCenters:
        fdet_ndx = kwargs[ 'fixed_detector_ndx' ]
	fdet_ndx = max( 0, min( fdet_ndx, len( self.fixedDetectorMeshCenters ) - 1 ) )
        axial_cm = self.fixedDetectorMeshCenters[ fdet_ndx ]
        core_ndx = DataUtils.FindListIndex( self.axialMeshCenters, axial_cm )
        det_ndx = DataUtils.FindListIndex( self.detectorMesh, axial_cm )

    return  axial_cm, core_ndx, det_ndx, fdet_ndx
  #end GetAxialValue


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
			( 'axial', 'channel', 'detector', 'fixed_detector',
			  'pin', 'scalar', etc. )
"""
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
  #	METHOD:		DataModelMgr.GetDataSetDefByQName()		-
  #----------------------------------------------------------------------
  def GetDataSetDefByQName( self, qds_name ):
    """Looks up the dataset definition dict for the type of the specified
dataset.
@param  qds_name	DataSetName instance
@return			dataset definition if found, None otherwise
"""
    ddef = None
    dm = self.GetDataModel( qds_name )
    if dm:
      ddef = dm.GetDataSetDefByDsName( qds_name.displayName )
    return  ddef
  #end GetDataSetDefByQName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, qds_name ):
    """If we have only a single model, we cull the model name for display
purpose.  Otherwise, we need the fully-qualified name.
@param  qds_name	DataSetName instance
@return			qds_name.displayName if we have a single mode,
			qds_name.name otherwise
"""
    if isinstance( qds_name, DataSetName ):
      result = \
          qds_name.name  if len( self.dataModels ) > 1 else \
	  qds_name.displayName
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
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetType( qds_name.displayName )  if dm else  None
  #end GetDataSetType


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
    #return  self.detectorMesh
    result = self.detectorMesh
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore().detectorMesh

    return  result
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMeshIndex()		-
  #----------------------------------------------------------------------
  def GetDetectorMeshIndex( self, value, model_name = None ):
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
    ndx = -1
    if isinstance( model_name, DataSetName ):
      model_name = model_name.modelName
    mesh = self.GetDetectorMesh( model_name )
    if mesh is not None:
      ndx = bisect.bisect_right( mesh, value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
    #end if

    return  ndx
  #end GetDetectorMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFactors()			-
  #----------------------------------------------------------------------
  def GetFactors( self, qds_name ):
    """Determines the factors from the dataset shape.
@param  qds_name	name of dataset, DataSetName instance
@return			factors np.ndarray or None
"""
    dm = self.GetDataModel( qds_name )
    return  dm.GetFactors( qds_name.displayName )  if dm else  None
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
@param  ds_type		datset category/type
@return			DataSetName instance or None if not found
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
  #end GetFirstDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMesh()		-
  #----------------------------------------------------------------------
  def GetFixedDetectorMesh( self, model_name = None ):
    """Retrieves the fixedDetectorMesh property for the specified model
or the cross-model global mesh.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    result = self.fixedDetectorMesh
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore().fixedDetectorMesh

    return  result
  #end GetFixedDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCenters()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self, model_name = None ):
    """Retrieves the fixedDetectorMeshCenters property for the specified model
or the cross-model global mesh centers.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh centers for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    #return  self.fixedDetectorMeshCenters
    result = self.fixedDetectorMeshCenters
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore().fixedDetectorMeshCenters

    return  result
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
    ndx = -1
    if isinstance( model_name, DataSetName ):
      model_name = model_name.modelName
    mesh = self.GetFixedDetectorMeshCenters( model_name )
    if mesh is not None:
      ndx = bisect.bisect_right( mesh, value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
    #end if

    return  ndx
  #end GetFixedDetectorMeshCentersIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetH5DataSet()			-
  #----------------------------------------------------------------------
  def GetH5DataSet( self, qds_name, time_value ):
    """Calls GetStateDataSet() on the corresponding DataModel.
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for current timeDataSet
@return			h5py.Dataset object if found or None
"""
    dset = None
    dm = None
    if qds_name is not None and time_value >= 0.0:
      state_ndx = self.GetTimeValueIndex( time_value, qds_name.modelName )
      if state_ndx >= 0:
        dm = self.GetDataModel( qds_name )

    if dm:
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
  #	METHOD:		DataModelMgr.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange( self, qds_name, time_value = -1.0 ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1
			for global range
@return			( min, max ), possible the range of floating point values
"""
    result = None
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      result = dm.GetRange( qds_name.displayName, state_ndx )
    #end if dm
   
    return  result
  #end GetRange


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
  #	METHOD:		DataModelMgr.HasDataSetType()			-
  #----------------------------------------------------------------------
  def HasDataSetType( self, ds_type ):
    """Convenience method to call HasDataSetType() on DataModel instances until 
True is returned.
@param  ds_type		one of type names, e.g., 'axial', 'channel', 'derived',
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
	    dset.shape[ 0 ] == self.core.npiny + 1 and
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
  #	METHOD:		DataModelMgr.NormalizeAxialValue()		-
  #----------------------------------------------------------------------
  def NormalizeAxialValue( self, model_param, axial_value ):
    """Normalizes against meshes specified by model_param or the global
cross-model meshes if model_param is None
@param  model_param	None for cross-model meshes, either a DataModel
			instance or a model name/ID string for
			model-specific meshes
@param  axial_value	( cm, core_ndx, det_ndx, fdet_ndx )
"""
    dm = None
    if model_param:
      dm = self.GetDataModel( model_param )
    if dm:
      core = dm.GetCore()
      axial_mesh_centers = core.GetAxialMeshCenters()
      detector_mesh = core.GetDetectorMesh()
      fdet_mesh_centers = core.GetFixedDetectorMeshCenters()
    else:
      axial_mesh_centers = self.GetAxialMeshCenters()
      detector_mesh = self.GetDetectorMesh()
      fdet_mesh_centers = self.GetFixedDetectorMeshCenters()

    result = (
        axial_value[ 0 ],
        max( 0, min( axial_value[ 1 ], len( axial_mesh_centers ) -1 ) ),
        max( 0, min( axial_value[ 2 ], len( detector_mesh ) -1 ) ),
        max( 0, min( axial_value[ 3 ], len( fdet_mesh_centers ) -1 ) )
        )
    return  result
  #end NormalizeAxialValue


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
      msg = 'Error reading "%s": %s' % ( h5f_param, ex.message )
      self.logger.error( msg )
      raise  IOError( msg )

#		-- Assert on compatibility
#		--
    self._CheckDataModelIsCompatible( dm )

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
      node_addrs = None,
      sub_addrs = None,
      detector_index = 0,
      time_value = 0.0
      ):
    """Reads axial values for a dataset for a specified time value.  Note the
returned values are over the approach mesh (axial mesh centers, detector
mesh, fixed detector mesh centers) for the DataModel.
Calls ReadDataSetAxialValues on the matching DataModel if found.
@param  qds_name	name of dataset, DataSetName instance, cannot be None
@param  assembly_index	0-based assembly index
@param  detector_index	0-based detector index
@param  node_addrs	list of node indexes
@param  sub_addrs	list of sub_addr pairs
@param  time_value	timeDataSet value
@return			None if the model or dataset cannot be found, otherwise
			dict with keys 'data' and 'mesh', where 'data value
			is dict by sub_addr of np.ndarray for datasets that vary
			by sub_addr,
			np.ndarray for other datasets
"""
    result = None
    dm = self.GetDataModel( qds_name )
    if dm:
      state_index = self.GetTimeValueIndex( time_value, qds_name )
      result_pair = dm.ReadDataSetAxialValues(
          qds_name.displayName, assembly_index,
	  node_addrs, sub_addrs,
	  detector_index, state_index
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
    """Reads values for datasets across time, axial values for a dataset for a specified time value.  Note the

    Reads values for a dataset across all state points, one state point
at a time for better performance.
@param  ds_specs_in	list of dataset specifications with the following keys:
	  assembly_index	0-based assembly index
	  axial_cm		axial value in cm
	  detector_index	0-based detector index for detector datasets
	  qds_name		required DataSetName instance
	  node_addrs		list of node addrs
	  sub_addrs		list of sub_addr pairs
@return			dict keyed by found qds_name of:
			  dict with keys 'data' and 'times', where 'data' value
			  is
			    dict keyed by sub_addr of np.ndarray for pin-based
			    datasets,
			    np.ndarray for datasets that are not pin-based
			  'times' value is np.ndarray
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
  #	METHOD:		DataModelMgr._ResolveLists()			-
  #----------------------------------------------------------------------
  def _ResolveLists( self, master, values ):
    """Updates master with values.  Both are assumed to be in ascending
order.
@param  master		master list to update, created if necessary
@param  values		list of values to add
@return			master or new list if master is None
"""
    if master is None:
      master = []

    i = 0
    while i < len( values ):
      cur_value = values[ i ]
      master_ndx = DataUtils.FindListIndex( master, values[ i ] )

      values_count = 1
      while i < len( values ) - 1 and values[ i + 1 ] == cur_value:
        values_count += 1
	i += 1

      master_count = 0
      if master_ndx >= 0:
        while master_ndx < len( master ) and master[ master_ndx ] == cur_value:
	  master_count += 1
	  master_ndx += 1

      for k in xrange( values_count - master_count ):
        master.insert( master_ndx + 1, cur_value )
	master_ndx += 1

      i += 1

#      while i < len( values ) and values[ i ] == cur_value:
#	if master_ndx >= len( master ):
#	  master.append( cur_value )
#	elif master[ master_ndx ] != cur_value:
#	  master.insert( master_ndx, values[ i ] )
#	master_ndx += 1
#        i += 1
    #end outer while

    return  master
  #end _ResolveLists


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
    dm = self.GetDataModel( qds_name )
    if dm:
      ds_name = dm.RevertIfDerivedDataSet( qds_name.displayName )
      if ds_name:
        result = DataSetName( qds_name.modelName, ds_name )

    return  result
  #end RevertIfDerivedDataSet


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
    """Updates the axialMesh, axialMeshCenters, detectorMap, detectorMesh,
fixedDetectorMesh, fixedDetectorMeshCenters, and maxAxialValue properties.
@return			maxAxialValue property value
"""
    self.maxAxialValue = -1.0
    axial_mesh = set()
    axial_mesh_centers = set()
    detector_mesh = set()
    fixed_detector_mesh = set()
    fixed_detector_mesh_centers = set()

    self.detectorMap = None

    for dm in self.dataModels.values():
      core = dm.GetCore()
      if core is not None:
	if core.axialMesh is not None:
	  self.maxAxialValue = max( self.maxAxialValue, core.axialMesh[ -1 ] )
	  axial_mesh.update( set( core.axialMesh ) )

        if core.axialMeshCenters is not None:
	  axial_mesh_centers.update( set( core.axialMeshCenters ) )

        if core.detectorMesh is not None:
	  self.maxAxialValue = \
	      max( self.maxAxialValue, core.detectorMesh[ -1 ] )
	  detector_mesh.update( set( core.detectorMesh ) )

        if core.fixedDetectorMesh is not None:
	  self.maxAxialValue = \
	      max( self.maxAxialValue, core.fixedDetectorMesh[ -1 ] )
	  fixed_detector_mesh.update( set( core.fixedDetectorMesh ) )

        if core.fixedDetectorMeshCenters is not None:
	  fixed_detector_mesh_centers.\
	      update( set( core.fixedDetectorMeshCenters ) )

        if self.detectorMap is None and dm.HasDetectorData():
          self.detectorMap = np.copy( dm.GetCore().detectorMap )
      #if core
    #end for dm

    self.axialMesh = list( sorted( axial_mesh ) )
    self.axialMeshCenters = list( sorted( axial_mesh_centers ) )
    self.detectorMesh = list( sorted( detector_mesh ) )
    self.fixedDetectorMesh = list( sorted( fixed_detector_mesh ) )
    self.fixedDetectorMeshCenters = \
        list( sorted( fixed_detector_mesh_centers ) )

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
	self.timeValuesById[ name ] = range( dm.GetStatesCount() )
        cur_count = max( cur_count, dm.GetStatesCount() )
      result = range( cur_count )

    elif self.timeDataSet:
      # cannot resolve with sets b/c values repeat
      #cur_set = set()
      spec = dict( ds_name = self.timeDataSet )
      for name, dm in self.dataModels.iteritems():
	cur_values = dm.ReadDataSetTimeValues( spec )
	if cur_values and self.timeDataSet in cur_values:
	  cur_list = cur_values[ self.timeDataSet ].tolist()
	  self.timeValuesById[ name ] = cur_list
	  #cur_set.update( set( cur_list ) )
	  self._ResolveLists( result, cur_list )
	else:
	  self.timeValuesById[ name ] = []
      #result = list( cur_set )
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
