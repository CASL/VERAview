#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
#		2016-11-30	leerw@ornl.gov				-
#		2016-11-29	leerw@ornl.gov				-
#	  Review and clean-up.
#		2016-08-19	leerw@ornl.gov				-
#		2016-08-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, copy, cStringIO, h5py, logging, json, math, os, sys, \
    tempfile, threading, traceback, uuid
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

Properties:
  dataModelIds		list of DataModel ids in order added
  dataModels		dict of DataModel objects keyed by id
  dataSetNamesVersion	counter to indicate changes
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
    self.dataModelIds = []
    self.dataModels = {}
    self.dataSetNamesVersion = 0
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
  #	METHOD:		DataModelMgr.AssembleQDataSetName()		-
  #----------------------------------------------------------------------
  def AssembleQDataSetName( self, ds_name, model_id = '' ):
    """Assembles the "qualified" dataset name.
@param  ds_name		dataset name (which might have a tag prefix)
@param  model_id	model id
@return			qualified name
"""
    return \
        '%s|%s' % ( model_id, ds_name )  if model_id else \
	ds_name
  #end AssembleQDataSetName


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

      if len( self.dataModelIds ) > 0:
        cur_dm = self.dataModels[ self.dataModelIds[ 0 ] ]
        cur_core = cur_dm.GetCore()
	dm_core = dm.GetCore()
	if cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_fmt = \
	      'Incompatible core geometry:\n' + \
	      '\tnass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d\n' + \
	      'is not compatible with\n' + \
	      '\tnass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d'
	  msg = msg_fmt % (
	      dm_core.nass, dm_core.nassx, dm_core.nassy,
	      dm_core.npinx, dm_core.npiny,
	      cur_core.nass, cur_core.nassx, cur_core.nassy,
	      cur_core.npinx, cur_core.npiny
	      )
          raise  Exception( msg )

        if cur_cure.coreSym != dm_core.coreSym:
	  msg = \
	      'Core symmetry mismatch: %d versus %d' % \
	      ( dm_core.coreSym, cur_core.coresym )
          raise  Exception( msg )
      #end if len
    #end if dm
  #end _CheckDataModelIsCompatible


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    for dm_id in self.dataModels:
      self.CloseModel( dm_id, True )
#    for dm in self.dataModels.values():
#      dm.Close()
#    del self.dataModelIds[ : ]
#    self.dataModels.clear()
  #end Close


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CloseModel()			-
  #----------------------------------------------------------------------
  def CloseModel( self, param, closing_all = False ):
    """Opens the HDF5 file or filename.
@param  param		either a DataModel instance or an ID string
@param  closing_all	if True, no local state updates are performed
@param  update_flag	True to update 
@return			True if removed, False if not found
"""
    result = False
    if isinstance( param, DataModel ):
      id = param.GetId()
    else:
      id = str( param )

    if id in self.dataModels:
      dm = self.dataModels[ id ]
      model_name = dm.GetName()
      dm.RemoveListener( 'newDataSet', self )
      dm.Close()

      del self.dataModels[ id ]
      del self.timeValuesById[ id ]
      self.dataModelIds.remove( id )

      if not closing_all:
        self._UpdateMeshValues()
        self._UpdateTimeValues()
        self.dataSetNamesVersion += 1
	self._FireEvent( 'modelRemoved', model_name )

      result = True

    return  result
  #end CloseModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._FireEvent()			-
  #----------------------------------------------------------------------
  def _FireEvent( self, event_name, *params ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  params		event params
"""
    if event_name in self.listeners:
      for listener in self.listeners[ event_name ]:
        method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
	if hasattr( listener, method_name ):
	  getattr( listener, method_name )( *params )
	elif hasattr( listener, '__call__' ):
	  listener( *params )
      #end for listener
    #end if event_name
  #end _FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self, id = None ):
    """Accessor for the axialMeshCenters property, which is all the mesh
values across all models.
@return			mesh values as a list
"""
    return  self.axialMeshCenters
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self, id = None, **kwargs ):
    """Retrieves the axial value tuple ( axial_cm, core_ndx, detector_ndx,
fixed_detector_ndx ) for the model with 'id' if specified.  Otherwise, the
cross-model levels are used and can be applied only with 'cm' and 'core_ndx'
arguments.  Calls CreateAxialValue() on the identified DataModel.
@param  id		id to identify model, or None for across all models
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

    if id:
      if id in self.dataModels:
	axial_cm, core_ndx, det_ndx, fdet_ndx = \
        self.dataModels[ id ].CreateAxialValue( kwargs )

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
  #	METHOD:		DataModelMgr.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self, id ):
    """Retrieves the DataModel by ID
@return			DataModel or None if not found
"""
    return  self.dataModels.get( id )
  #end GetDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelCount()		-
  #----------------------------------------------------------------------
  def GetDataModelCount( self ):
    return  len( self.dataModels )
  #end GetDataModelCount


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelIds()			-
  #----------------------------------------------------------------------
  def GetDataModelIds( self ):
    """
@return			list of model IDs
"""
    return  self.dataModelIds
  #end GetDataModelIds


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
  #	METHOD:		DataModelMgr.GetDataSetNamesVersion()		-
  #----------------------------------------------------------------------
  def GetDataSetNamesVersion( self ):
    """Used to determine the generation of dataset changes for menus and
lists that must be rebuilt when the sets of available datasets change.
"""
    return  self.dataSetNamesVersion
    #return  self.dataSetNamesVersion
  #end GetDataSetNamesVersion


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMesh()			-
  #----------------------------------------------------------------------
  def GetDetectorMesh( self, id = None ):
    """Accessor for the detectorMesh property, which is all the mesh
values across all models.
@return			mesh values as a list
"""
    return  self.detectorMesh
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCenters()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self, id = None ):
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
  #	METHOD:		DataModelMgr.GetTimeDataSet()			-
  #----------------------------------------------------------------------
  def GetTimeDataSet( self ):
    """Accessor for the timeDataSet property.
@return			dataset used for time
"""
    return  self.timeDataSet
  #end GetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValueIndex()		-
  #----------------------------------------------------------------------
  def GetTimeValueIndex( self, value, id = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If id is specified, only the
list of values for the specified model are used.  Otherwise, the cross-model
values are used.
@param  id		optional ID to identify the model of interest
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    ndx = -1
    values = self.GetTimeValues( id )
    if values:
      ndx = bisect.bisect_right( values, value ) - 1
      ndx = max( 0, min( ndx, len( values ) - 1 ) )
    #end if

    return  ndx
  #end GetTimeValueIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValues()			-
  #----------------------------------------------------------------------
  def GetTimeValues( self, id = None ):
    """Retrieves the time dataset values for the specified model if 'id'
is not None, otherwise retrieves the union of values across all models.
@param  id		optional ID to identify the model of interest
@return			list of time dataset values for the specified model
			or across all models
"""
    return \
	self.timeValuesById[ id ]  if id and id in self.timeValuesById else \
	self.timeValues
  #end GetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasData()				-
  #----------------------------------------------------------------------
  def HasData( self ):
    return  len( self.dataModels ) > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._OnNewDataSet()			-
  #----------------------------------------------------------------------
  def _OnNewDataSet( self, model, ds_name ):
    """Callback for model 'newDataSet' events.
"""
    self.dataSetNamesVersion += 1
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
      id = str( uuid.uuid4() )
      dm = DataModel( h5f_param, id )
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
      dm.AddListener( 'newDataSet', self._OnNewDataSet )
      self.dataModelIds.append( id )
      self.dataModels[ id ] = dm
      self._UpdateMeshValues()
      self._UpdateTimeValues()
      self.dataSetNamesVersion += 1
      self._FireEvent( 'modelAdded', dm.GetName() )

      return  dm

    except Exception, ex:
      msg = 'Error processing "%s": %s' % ( h5f_param, ex.message )
      self.logger.error( msg )
      raise  IOError( msg )
  #end OpenModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ParseQDataSetName()		-
  #----------------------------------------------------------------------
  def ParseQDataSetName( self, qds_name ):
    """Parses the "qualified" dataset name into a tuple containing the
display_name, model_id, and tag (e.g., 'copy').
@param  qds_name	qualified dataset name
@return			display_name, model_id, tag
"""
    display_name = ''
    model_id = ''
    tag = ''

    if qds_name:
      bar_ndx = qds_name.find( '|' )
      if bar_ndx < 0:
        remainder = qds_name
      else:
        model_id = qds_name[ 0 : bar_ndx ]
	remainder = qds_name[ bar_ndx + 1 : ]

      if remainder.startswith( 'copy:' ):
        display_name = remainder[ 5 : ]
	tag = 'copy'
      elif remainder.startswith( 'derived:' ):
        display_name = remainder[ 8 : ]
	tag = 'derived'
      else:
        display_name = remainder
    #end if qds_name

    return  display_name, model_id, tag
  #end ParseQDataSetName


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
      for id, dm in self.dataModels.iteritems():
	self.timeValuesById[ id ] = range( dm.GetStatesCount() )
        cur_count = max( cur_count, dm.GetStatesCount() )
      result = range( cur_count )

    elif self.timeDataSet:
      cur_set = set()
      spec = dict( ds_name = self.timeDataSet )
      for id, dm in self.dataModels.iteritems():
	cur_values = dm.ReadDataSetValues2( spec )
	if cur_values and self.timeDataSet in cur_values:
	  cur_list = cur_values[ self.timeDataSet ].tolist()
	  self.timeValuesById[ id ] = cur_list
	  cur_set.update( set( cur_list ) )
	else:
	  self.timeValuesById[ id ] = []
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
