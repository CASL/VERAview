#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
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
import bisect, copy, cStringIO, functools, h5py, \
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
    self.axialMeshCenters = None
    self.dataModelNames = []
    self.dataModels = {}
    #self.dataSetNamesVersion = 0
    self.detectorMesh = None
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

      if len( self.dataModelNames ) > 0:
        cur_dm = self.dataModels[ self.dataModelNames[ 0 ] ]
        cur_core = cur_dm.GetCore()
	dm_core = dm.GetCore()
	if cur_core.coreSym != dm_core.coreSym or \
	    cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_fmt = \
	      'Incompatible core geometry:\n' + \
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
          raise  Exception( msg )
      #end if len
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
  def CloseModel( self, param, closing_all = False ):
    """Opens the HDF5 file or filename.
@param  param		either a DataModel instance or a model name/ID string
@param  closing_all	if True, no local state updates are performed
@param  update_flag	True to update 
@return			True if removed, False if not found
"""
    result = False
    if isinstance( param, DataModel ):
      model_name = param.GetName()
    else:
      model_name = str( param )

    if model_name in self.dataModels:
      dm = self.dataModels[ model_name ]
      #model_name = dm.GetName()
      dm.RemoveListener( 'newDataSet', self )
      dm.Close()

      del self.dataModels[ model_name ]
      del self.timeValuesById[ model_name ]
      self.dataModelNames.remove( model_name )

      if not closing_all:
        self._UpdateMeshValues()
        self._UpdateTimeValues()
        #self.dataSetNamesVersion += 1
	self._FireEvent( 'modelRemoved', model_name )

      result = True

    return  result
  #end CloseModel


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
	results[ 'time_value' ] = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
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
	results[ 'time_value' ] = self.\
	    GetTimeIndexValue( results[ 'state_index' ], model_name )
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
	results[ 'time_value' ] = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
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
      for listener in self.listeners[ event_name ]:
        method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
	if hasattr( listener, method_name ):
	  getattr( listener, method_name )( self, *params )
	elif hasattr( listener, '__call__' ):
	  listener( self, *params )
      #end for listener
    #end if event_name
  #end _FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self ):
    """Accessor for the axialMeshCenters property, which is all the mesh
values across all models.
@return			mesh values as a list
"""
    return  self.axialMeshCenters
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self, model_name = None, **kwargs ):
    """Retrieves the axial value tuple ( axial_cm, core_ndx, detector_ndx,
fixed_detector_ndx ) for the model with 'id' if specified.  Otherwise, the
cross-model levels are used and can be applied only with 'cm' and 'core_ndx'
arguments.  Calls CreateAxialValue() on the identified DataModel.
@param  model_name	model name, or None for global axial levels
			across all models
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
    axial_cm = 0.0

    if model_name:
      if model_name in self.dataModels:
	axial_cm, core_ndx, det_ndx, fdet_ndx = \
        self.dataModels[ model_name ].CreateAxialValue( kwargs )

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
  def GetCore( self ):
    """Convenience method to return the Core instance from the first
DataModel.
@return			Core instance or None if no models have been opened
"""
    dm = self.GetFirstDataModel()
    return  dm.GetCore()  if dm else  None
  #end GetCore


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self, param ):
    """Retrieves the DataModel by model name.  The param can be a string
model name or a DataSetName instance.
@param  param		a DataSetName instance or a model name string
@return			DataModel or None if not found
"""
    dm = None
    if param:
      model_name = \
          param.modelName  if isinstance( param, DataSetName ) else \
	  str( param )
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
  def GetDataModelDataSetNames( self, param ):
    """Retrieves the dataset types list for the specified model.
@param  param		either a model name or a DataSetName instance
@return			types lislt
"""
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetType( qds_name.displayName )
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
  def GetDetectorMesh( self ):
    """Accessor for the detectorMesh property, which is all the mesh
values across all models.
@return			mesh values as a list
"""
    return  self.detectorMesh
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFirstDataModel()		-
  #----------------------------------------------------------------------
  def GetFirstDataModel( self ):
    """Retrieves the first DataModel.
@return			DataModel or None if not found
"""
    dm = None
    if len( self.dataModelNames ) > 0:
      dm = self.dataModels.get( self.dataModelNames[ 0 ] )

    return  dm
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
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCenters()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self ):
    """Accessor for the fixedDetectorMeshCenters property, which is all the
mesh values across all models.
@return			mesh values as a list
"""
    return  self.fixedDetectorMeshCenters
  #end GetFixedDetectorMeshCenters


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
@param  model_name	optional name for the model of interest
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    value = -1

    values = None
    if ndx >= 0:
      values = self.GetTimeValues( model_name )
      if values:
        ndx = min( ndx, len( values ) -1 )
        value = values[ ndx ]

    return  value
  #end GetTimeIndexValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValueIndex()		-
  #----------------------------------------------------------------------
  def GetTimeValueIndex( self, value, model_name = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If model_name is specified,
only the list of values for the specified model are used.  Otherwise,
the global, cross-model values are used.
@param  model_name	optional name for the model of interest
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    ndx = -1
    values = self.GetTimeValues( model_name )
    if values:
      ndx = bisect.bisect_right( values, value ) - 1
      ndx = max( 0, min( ndx, len( values ) - 1 ) )
    #end if

    return  ndx
  #end GetTimeValueIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValues()			-
  #----------------------------------------------------------------------
  def GetTimeValues( self, model_name = None ):
    """Retrieves the time dataset values for the specified model if 'id'
is not None, otherwise retrieves the union of values across all models.
@param  model_name	optional name for the model of interest
@return			list of time dataset values for the specified model
			or across all models
"""
    return \
	self.timeValuesById[ model_name ] \
	if model_name and model_name in self.timeValuesById else \
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
  #	METHOD:		DataModelMgr.RemoveListener()			-
  #----------------------------------------------------------------------
  def RemoveListener( self, event_name, listener ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener in self.listeners[ event_name ]:
        del self.listeners[ event_name ][ listener ]
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
  #	METHOD:		DataModelMgr.SetTimeDataSet()			-
  #----------------------------------------------------------------------
  def SetTimeDataSet( self, ds_name ):
    """Accessor for the timeDataSet property.
@param  ds_name		dataset used for time
"""
    self.timeDataSet = ds_name
    self._UpdateTimeValues()
  #end SetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateMeshValues()		-
  #----------------------------------------------------------------------
  def _UpdateMeshValues( self ):
    """Updates the axialMeshCenters, detectorMesh,
fixedDetectorMeshCenters, and maxAxialValue properties.
@return			maxAxialValue property value
"""
    self.maxAxialValue = -1.0
    axial_mesh_centers = set()
    detector_mesh = set()
    fixed_detector_mesh_centers = set()

    for dm in self.dataModels.values():
      core = dm.GetCore()
      if core is not None:
        if core.axialMeshCenters is not None:
	  self.maxAxialValue = \
	      max( self.maxAxialValue, core.axialMeshCenters[ -1 ] )
	  axial_mesh_centers.update( set( core.axialMeshCenters ) )

        if core.detectorMesh is not None:
	  self.maxAxialValue = \
	      max( self.maxAxialValue, core.detectorMesh[ -1 ] )
	  detector_mesh.update( set( core.detectorMesh ) )

        if core.fixedDetectorMeshCenters is not None:
	  self.maxAxialValue = \
	      max( self.maxAxialValue, core.fixedDetectorMeshCenters[ -1 ] )
	  fixed_detector_mesh_centers.\
	      update( set( core.fixedDetectorMeshCenters ) )
      #if core
    #end for dm

    self.axialMeshCenters = list( sorted( axial_mesh_centers ) )
    self.detectorMesh = list( sorted( detector_mesh ) )
    self.fixedDetectorMeshCenters = list( sorted( fixed_detector_mesh_centers ) )

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
      cur_set = set()
      spec = dict( ds_name = self.timeDataSet )
      for name, dm in self.dataModels.iteritems():
	cur_values = dm.ReadDataSetValues2( spec )
	if cur_values and self.timeDataSet in cur_values:
	  cur_list = cur_values[ self.timeDataSet ].tolist()
	  self.timeValuesById[ name ] = cur_list
	  cur_set.update( set( cur_list ) )
	else:
	  self.timeValuesById[ name ] = []
      result = list( cur_set )
    #end if-elif

    result.sort()
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
