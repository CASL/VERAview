#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		state.py					-
#	HISTORY:							-
#		2017-07-20	leerw@ornl.gov				-
#	  Added STATE_CHANGE_forceRedraw and reordered indexes to
#	  alphabetize.
#		2017-07-18	leerw@ornl.gov				-
#	  Added (de)serialization of dataModelMgr dataset thresholds.
#		2017-03-27	leerw@ornl.gov				-
#	  Added tallyAddr event and state property.
#		2017-03-16	leerw@ornl.gov				-
#	  Defaulting to the first time dataset by preference set in
#	  TIME_DS_NAMES_LIST
#		2017-01-04	leerw@ornl.gov				-
#	  Firing STATE_CHANGE_dataModelMgr in _OnDataModelMgr().
#		2016-12-28	leerw@ornl.gov				-
#	  Resolving curDataSet in _OnDataModelMgr().
#		2016-12-12	leerw@ornl.gov				-
#	  Added properties.
#		2016-12-10	leerw@ornl.gov				-
#	  In Change(), cur_dataset implies axial_value and time_value,
#	  and time_dataset implies time_value.
#		2016-12-07	leerw@ornl.gov				-
#	  Modified Init() to call self.dataModelMgr.GetFirstDataModel()
#	  to get the DataModel instance to use.
#		2016-11-30	leerw@ornl.gov				-
#	  Added timeValue property.
#		2016-11-29	leerw@ornl.gov				-
#	  Modfied {Add,Remove}Listeners() to accept multiple params.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-17	leerw@ornl.gov				-
#	  Added nodeAddr as a STATE_CHANGE_coordinates attribute.
#	  Added auxNodeAddrs.
#		2016-09-19	leerw@ornl.gov				-
#	  Added STATE_CHANGE_weightsMode.
#		2016-08-19	leerw@ornl.gov				-
#	  New DataModelMgr.
#		2016-08-15	leerw@ornl.gov				-
#	  Reducing events to one selected dataset, one coordinate,
#	  axial value, and one time.
#		2016-08-10	leerw@ornl.gov				-
#	  Changed Load() to start with indexes in the center of the core.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-21	leerw@ornl.gov				-
#	  Added GetDataSetChanges().
#		2016-07-18	leerw@ornl.gov				-
#	  Added {Get,Set}DataSetByType().
#		2016-07-07	leerw@ornl.gov				-
#	  Renaming "vanadium" to "fixed_detector".
#		2016-06-30	leerw@ornl.gov				-
#	  Added {Load,Save}Props().
#		2016-06-27	leerw@ornl.gov				-
#	  Moved EVENT_ID_NAMES here for better encapsulation.
#		2016-05-25	leerw@ornl.gov				-
#	  Special "vanadium" dataset type.
#		2016-04-25	leerw@ornl.gov				-
#	  Added aux{Channel,Pin}ColRows attributes and associated
#	  STATE_CHANGE_ mask bits.
#		2016-04-23	leerw@ornl.gov				-
#	  Calling DataModel.GetDefaultScalarDataSet() in Load().
#		2016-04-16	leerw@ornl.gov				-
#	  Added scaleMode.
#		2015-12-08	leerw@ornl.gov				-
#	  Managing events and changes on the State object.
#		2015-06-15	leerw@ornl.gov				-
#	  Refactoring.  Added State.CreateUpdateArgs().
#		2015-05-25	leerw@ornl.gov				-
#		2015-05-23	leerw@ornl.gov				-
#	  Added channelColRow property and event.
#		2015-05-21	leerw@ornl.gov				-
#	  Added channelDataSet property and event.
#		2015-05-18	leerw@ornl.gov				-
#	  Wiring together detectorIndex and assemblyIndex state changes.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed axialLevel to axialValue.
#		2015-04-27	leerw@ornl.gov				-
#	  Added STATE_CHANGE_detector{DataSet,Index}.
#		2015-04-22	leerw@ornl.gov				-
#	  Changed assemblyIndex to be a ( index, col, row ) tuple.
#		2015-04-11	leerw@ornl.gov				-
#	  Added {pin,scalar}DataSet as a state event.
#		2015-04-04	leerw@ornl.gov				-
#	  Reversing pinRowCol to pinColRow.
#		2015-02-18	leerw@ornl.gov				-
#	  Looping in ResolveLocks().
#		2015-02-11	leerw@ornl.gov				-
#	  Removed scale and added pinRowCol.
#		2014-12-30	leerw@ornl.gov				-
#	  New data model.
#		2014-12-08	leerw@ornl.gov				-
#		2014-11-15	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, logging, os, sys, traceback
import numpy as np
import pdb

from data.datamodel import *
from data.datamodel_mgr import *


LABEL_selectedDataSet = 'Selected Dataset'
NAME_selectedDataSet = DataSetName( LABEL_selectedDataSet )


# New, reduced set of events
STATE_CHANGE_noop = 0
STATE_CHANGE_init = 0x1 << 0		# never generated here
STATE_CHANGE_axialValue = 0x1 << 1
STATE_CHANGE_coordinates = 0x1 << 2
STATE_CHANGE_curDataSet = 0x1 << 3
STATE_CHANGE_dataModelMgr = 0x1 << 4
STATE_CHANGE_forceRedraw = 0x1 << 5
STATE_CHANGE_scaleMode = 0x1 << 6
#STATE_CHANGE_stateIndex = 0x1 << 7
STATE_CHANGE_tallyAddr = 0x1 << 8
STATE_CHANGE_timeDataSet = 0x1 << 9
STATE_CHANGE_timeValue = 0x1 << 10
STATE_CHANGE_weightsMode = 0x1 << 11

STATE_CHANGE_ALL = 0xffffffff


# New, reduced set of events
LOCKABLE_STATES = \
  [
    ( STATE_CHANGE_axialValue, 'Axial Value' ),
    ( STATE_CHANGE_coordinates, 'Coordinates' ),
    ( STATE_CHANGE_curDataSet, LABEL_selectedDataSet ),
    ( STATE_CHANGE_scaleMode, 'Scale Mode' ),
    ( STATE_CHANGE_timeValue, 'State Point/Time' ),
    ( STATE_CHANGE_tallyAddr, 'Tally Options' )
  ]


#------------------------------------------------------------------------
#	CLASS:		State						-
#------------------------------------------------------------------------
class State( object ):
  """Event state object.  State attributes currently in use are as follows.
All indices are 0-based.

+----------------+----------------+------------------+-------------------------+
|                | State          |                  |                         |
| Event Name     | Attrs/Props    | Param Name       | Param Value             |
+================+================+==================+=========================+
| axialValue     | axialValue     | axial_value      |                         |
|                |                | ( float value(cm), core-ndx,               |
|                |                |   detector-index, fixed-detector-index,    |
|                |                |   tally-index, subpin-index )              |
+----------------+----------------+------------------+-------------------------+
| coordinates    | assemblyAddr   | assembly_addr    | ( index, col, row )     |
|                |                | 0-based assembly/detector indexes          |
+----------------+----------------+------------------+-------------------------+
|                | auxNodeAddrs   | aux_node_addrs   | list of 0-based indexes |
+----------------+----------------+------------------+-------------------------+
|                | auxSubAddrs    | aux_sub_addrs    | list of ( col, row )    |
|                |                | 0-based channel/pin indexes                |
+----------------+----------------+------------------+-------------------------+
|                | nodeAddr       | node_addr        | 0-based node index      |
|                |                | range [0,3] or [0,4]                       |
+----------------+----------------+------------------+-------------------------+
|                | subAddr        | sub_addr         | ( col, row )            |
|                |                | 0-based channel/pin indexes                |
+----------------+----------------+------------------+-------------------------+
| curDataSet     | curDataSet     | cur_dataset      | DataSetName instance    |
+----------------+----------------+------------------+-------------------------+
| dataModelMgr   | dataModelMgr   | data_model_mgr   | data.DataModelMgr object|
+----------------+----------------+------------------+-------------------------+
| scaleMode      | scaleMode      | scale_mode       | 'all' or 'state'        |
+----------------+----------------+------------------+-------------------------+
| #stateIndex    | stateIndex     | state_index      | 0-based state-point ndx |
+----------------+----------------+------------------+-------------------------+
| tallyAddr      | tallyAddr      | tally_addr       | ( name, mult, stat )    |
|                |                | name is DataSetName instance,              |
|                |                | mult and state are 0-based indexes         |
+----------------+----------------+------------------+-------------------------+
| timeValue      | timeValue      | time_value       | time dataset value      |
|                |                |                  | (replaces stateIndex)   |
+----------------+----------------+------------------+-------------------------+
| weightsMode    | weightsMode    | weights_mode     | 'on' or 'off'           |
+----------------+----------------+------------------+-------------------------+
"""

#		-- Class Attributes
#		--

  allLocks_ = None


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    self._assemblyAddr = ( -1, -1, -1 )
    self._auxNodeAddrs = []
    self._auxSubAddrs = []
    self._axialValue = DataModel.CreateEmptyAxialValue()
    self._curDataSet = DataSetName( 'pin_powers' )

    #xxxxx listen to events, update timeDataSet, timeValue
    self._dataModelMgr = DataModelMgr()
    self._dataModelMgr.AddListener( 'modelAdded', self._OnDataModelMgr )
    self._dataModelMgr.AddListener( 'modelRemoved', self._OnDataModelMgr )

    self._listeners = []
    self._logger = logging.getLogger( 'event' )
    self._nodeAddr = -1
    self._scaleMode = 'all'
    #self.stateIndex = -1
    self._subAddr = ( -1, -1 )
    self._tallyAddr = ( None, 0, 0 )
    self._timeDataSet = 'state'
    self._timeValue = 0.0
    self._weightsMode = 'on'

    self.Change( **kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    """This needs to be updated.  Perhaps dump the JSON sans dataModelMgr.
"""
    fmt = \
        'axial=%s,coord={assemblyAddr=%s,auxNodeAddrs=%s,auxSubAddrs=%s' + \
	',nodeAddr=%s,subAddr=%s},dataset=%s,scale=%s,timeDataSet=%s' +  \
	',time=%f,weightsMode=%s'
    result = fmt % (
	str( self._axialValue ), str( self._assemblyAddr ),
	str( self._auxNodeAddrs ), str( self._auxSubAddrs ),
	str( self._nodeAddr ), str( self._subAddr ),
	str( self._curDataSet ), self._scaleMode,
	self._timeDataSet, self._timeValue, self._weightsMode
        )
    return  result
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		AddListener()					-
  #----------------------------------------------------------------------
  def AddListener( self, *listeners ):
    """Adds the listener(s) if not already added.  Listeners must implement
a HandleStateChange( self, reason ) method.
@param  listeners	one or more listeners to add
"""
#    if listener not in self._listeners:
#      self._listeners.append( listener )
    if listeners:
      for listener in listeners:
        if listener not in self._listeners:
          self._listeners.append( listener )
  #end AddListener


  #----------------------------------------------------------------------
  #	METHOD:		Change()					-
  #----------------------------------------------------------------------
  def Change( self, locks = None, **kwargs ):
    """Applies the property changes specified in kwargs that are allowed
by locks.
@param  locks		dictionary of True/False values for each of the
			STATE_CHANGE_xxx indexes, where None means enable
			all events
@param  kwargs		name, value pairs with which to update this

Keys passed and the corresponding state bit are:
  assembly_addr		STATE_CHANGE_coordinates
  aux_node_addrs	STATE_CHANGE_coordinates
  aux_sub_addrs		STATE_CHANGE_coordinates
  axial_value		STATE_CHANGE_axialValue
  cur_dataset		STATE_CHANGE_curDataSet
  data_model_mgr	STATE_CHANGE_dataModelMgr
  node_addr		STATE_CHANGE_coordinates
  forceRedraw		STATE_CHANGE_forceRedraw
  scale_mode		STATE_CHANGE_scaleMode
  #state_index		STATE_CHANGE_stateIndex
  sub_addr		STATE_CHANGE_coordinates
  tally_addr		STATE_CHANGE_tallyAddr
  time_dataset		STATE_CHANGE_timeDataSet
  time_value		STATE_CHANGE_timeValue
  weights_mode		STATE_CHANGE_weightsMode
@return			change reason mask
"""
    reason = STATE_CHANGE_noop
    if locks is None:
      locks = State.GetAllLocks()
      #locks = State.CreateLocks()

#		-- Changes with no side effects
#		--
    if 'assembly_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self._assemblyAddr = kwargs[ 'assembly_addr' ]
      reason |= STATE_CHANGE_coordinates

    if 'aux_node_addrs' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self._auxNodeAddrs = kwargs[ 'aux_node_addrs' ]
      reason |= STATE_CHANGE_coordinates

    if 'aux_sub_addrs' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self._auxSubAddrs = kwargs[ 'aux_sub_addrs' ]
      reason |= STATE_CHANGE_coordinates

    if 'axial_value' in kwargs and locks[ STATE_CHANGE_axialValue ]:
      self._axialValue = kwargs[ 'axial_value' ]
      reason |= STATE_CHANGE_axialValue

    if 'data_model_mgr' in kwargs:
      self._dataModelMgr = kwargs[ 'data_model_mgr' ]
      reason |= STATE_CHANGE_dataModelMgr

    if 'node_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self._nodeAddr = kwargs[ 'node_addr' ]
      reason |= STATE_CHANGE_coordinates

    if 'force_redraw' in kwargs and kwargs.get( 'force_redraw' ):
      reason |= STATE_CHANGE_forceRedraw

    if 'scale_mode' in kwargs and locks[ STATE_CHANGE_scaleMode ]:
      self._scaleMode = kwargs[ 'scale_mode' ]
      reason |= STATE_CHANGE_scaleMode

#    if 'state_index' in kwargs and locks[ STATE_CHANGE_stateIndex ]:
#      self.stateIndex = kwargs[ 'state_index' ]
#      reason |= STATE_CHANGE_stateIndex

    if 'sub_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self._subAddr = kwargs[ 'sub_addr' ]
      reason |= STATE_CHANGE_coordinates

    if 'tally_addr' in kwargs and locks[ STATE_CHANGE_tallyAddr ]:
      self._tallyAddr = kwargs[ 'tally_addr' ]
      reason |= STATE_CHANGE_tallyAddr

    if 'time_value' in kwargs and locks[ STATE_CHANGE_timeValue ]:
      self._timeValue = kwargs[ 'time_value' ]
      reason |= STATE_CHANGE_timeValue

    if 'weights_mode' in kwargs:
      self._weightsMode = kwargs[ 'weights_mode' ]
      reason |= STATE_CHANGE_weightsMode

#		-- Changes with side effects
#		--
    if 'cur_dataset' in kwargs and locks[ STATE_CHANGE_curDataSet ]:
      self._curDataSet = kwargs[ 'cur_dataset' ]
      reason |= STATE_CHANGE_curDataSet
      if 'axial_value' not in kwargs:
        reason |= STATE_CHANGE_axialValue
      if 'time_value' not in kwargs:
        reason |= STATE_CHANGE_timeValue
    #end 'cur_dataset'

    #if 'time_dataset' in kwargs and 
        #self._timeDataSet != kwargs[ 'time_dataset' ]:
    if 'time_dataset' in kwargs:
      if self._timeDataSet != kwargs[ 'time_dataset' ]:
        cur_ndx = -1
        if 'time_value' not in kwargs:
          cur_ndx = self._dataModelMgr.GetTimeValueIndex( self._timeValue )

        self._timeDataSet = kwargs[ 'time_dataset' ]
	self._dataModelMgr.SetTimeDataSet( self._timeDataSet )

	if cur_ndx >= 0:
	  self._timeValue = self._dataModelMgr.GetTimeIndexValue( cur_ndx )
	  reason |= STATE_CHANGE_timeValue
      #end if different self._timeDataSet

      reason |= STATE_CHANGE_timeDataSet
    #end 'time_dataset'

    return  reason
  #end Change


  #----------------------------------------------------------------------
  #	METHOD:		CreateUpdateArgs()				-
  #----------------------------------------------------------------------
  def CreateUpdateArgs( self, reason ):
    """
@return			dict with updated values based on reason
"""
    update_args = {}
    if (reason & STATE_CHANGE_axialValue) > 0:
      update_args[ 'axial_value' ] = self._axialValue

    if (reason & STATE_CHANGE_coordinates) > 0:
      update_args[ 'assembly_addr' ] = self._assemblyAddr
      update_args[ 'aux_node_addrs' ] = self._auxNodeAddrs
      update_args[ 'aux_sub_addrs' ] = self._auxSubAddrs
      update_args[ 'node_addr' ] = self._nodeAddr
      update_args[ 'sub_addr' ] = self._subAddr

    if (reason & STATE_CHANGE_curDataSet) > 0:
      update_args[ 'cur_dataset' ] = self._curDataSet

    if (reason & STATE_CHANGE_dataModelMgr) > 0:
      update_args[ 'data_model_mgr' ] = self._dataModelMgr

    if (reason & STATE_CHANGE_forceRedraw) > 0:
      update_args[ 'force_redraw' ] = True

    if (reason & STATE_CHANGE_scaleMode) > 0:
      update_args[ 'scale_mode' ] = self._scaleMode

#    if (reason & STATE_CHANGE_stateIndex) > 0:
#      update_args[ 'state_index' ] = self.stateIndex

    if (reason & STATE_CHANGE_tallyAddr) > 0:
      update_args[ 'tally_addr' ] = self._tallyAddr

    if (reason & STATE_CHANGE_timeDataSet) > 0:
      update_args[ 'time_dataset' ] = self._timeDataSet

    if (reason & STATE_CHANGE_timeValue) > 0:
      update_args[ 'time_value' ] = self._timeValue

    if (reason & STATE_CHANGE_weightsMode) > 0:
      update_args[ 'weights_mode' ] = self._weightsMode

    return  update_args
  #end CreateUpdateArgs


  #----------------------------------------------------------------------
  #	METHOD:		_FindDefaultDataSet()				-
  #----------------------------------------------------------------------
  def _FindDefaultDataSet( self, data_model = None ):
    """Determines a default dataset from available models.
@return			DataSetName instance
"""
    result = DataSetName( 'pin_powers' )

    if data_model is None:
      data_model = self._dataModelMgr.GetFirstDataModel()

    if data_model is not None:
      ds_display_name = 'pin_powers' \
	  if 'pin_powers' in data_model.GetDataSetNames( 'pin' ) else \
	  data_model.GetFirstDataSet( 'pin' )
      result = DataSetName( data_model.GetName(), ds_display_name )
    #end if data_model is not None

    return  result
  #end _FindDefaultDataSet


  #----------------------------------------------------------------------
  #	METHOD:		FireStateChange()				-
  #----------------------------------------------------------------------
  def FireStateChange( self, reason ):
    """Notifies all listeners of the change if not noop.
@param  reason		reason mask
"""
    if reason != STATE_CHANGE_noop:
      for listener in self._listeners:
	try:
	  if not listener:
	    self._logger.error( 'Listener is dead: %s', str( listener ) )

	  elif hasattr( listener, 'HandleStateChange' ):
            listener.HandleStateChange( reason )
	  elif hasattr( listener, 'OnStateChange' ):
            listener.OnStateChange( reason )
	  elif hasattr( listener, '__call__' ):
	    listener( reason )
	except Exception, ex:
	  self._logger.error( str( ex ) )
      #end for listeners
    #end if not noop
  #end FireStateChange


  #----------------------------------------------------------------------
  #	METHOD:		GetAssemblyAddr()				-
  #----------------------------------------------------------------------
  def GetAssemblyAddr( self ):
    """Accessor for the assemblyAddr property.
@return			0-based ( assembly index, col, rol )
"""
    return  self._assemblyAddr
  #end GetAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetAuxNodeAddrs()				-
  #----------------------------------------------------------------------
  def GetAuxNodeAddrs( self ):
    """Accessor for the auxNodeAddrs property.
@return			list of 0-based indexes, possibly empty
"""
    return  self._auxNodeAddrs
  #end GetAuxNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		GetAuxSubAddrs()				-
  #----------------------------------------------------------------------
  def GetAuxSubAddrs( self ):
    """Accessor for the auxSubAddrs property.
@return			list of 0-based channel/pin ( col, row ) indexes,
			possibly empty
"""
    return  self._auxSubAddrs
  #end GetAuxSubAddrs


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """Accessor for the axialValue property.
@return			( float value(cm), core-index, detector-index,
			  fixed-detector-index ), all indexes 0-based
"""
    return  self._axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		GetCurDataSet()					-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """Accessor for the curDataSet property.
@return			DataSetName instance, name of current/selected dataset
"""
    return  self._curDataSet
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		GetDataModelMgr()				-
  #----------------------------------------------------------------------
  def GetDataModelMgr( self ):
    """Accessor for the dataModelMgr property.
@return			DataModelMgr object
"""
    return  self._dataModelMgr
  #end GetDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		GetNodeAddr()					-
  #----------------------------------------------------------------------
  def GetNodeAddr( self ):
    """Accessor for the nodeAddr property.
@return			0-based node index in range [0,3] or [0,4)
"""
    return  self._nodeAddr
  #end GetNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetScaleMode()					-
  #----------------------------------------------------------------------
  def GetScaleMode( self ):
    """Accessor for the scaleMode property.
@return			'all' or 'state'
"""
    return  self._scaleMode
  #end GetScaleMode


#  #----------------------------------------------------------------------
#  #	METHOD:		GetStateIndex()					-
#  #----------------------------------------------------------------------
#  def GetStateIndex( self ):
#    """Accessor for the stateIndex property.
#@return			0-based state-point index
#@deprecated  use timeValue instead of stateIndex
#"""
#    return  self.stateIndex
#  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		GetSubAddr()					-
  #----------------------------------------------------------------------
  def GetSubAddr( self ):
    """Accessor for the subAddr property.
@return			0-based ( col, row ) channel/pin indexes
"""
    return  self._subAddr
  #end GetSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetTallyAddr()					-
  #----------------------------------------------------------------------
  def GetTallyAddr( self ):
    """Accessor for the tallyAddr property.
@return			( name, mult_ndx, stat_ndx ) 0-based indexes
"""
    return  self._tallyAddr
  #end GetTallyAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetTimeDataSet()				-
  #----------------------------------------------------------------------
  def GetTimeDataSet( self ):
    """Accessor for the timeDataSet property.
@return			dataset used for time
"""
    return  self._timeDataSet
  #end GetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTimeValue()					-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """Accessor for the timeValue property.
@return			current timeDataSet value
"""
    return  self._timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		GetWeightsMode()				-
  #----------------------------------------------------------------------
  def GetWeightsMode( self ):
    """Accessor for the weightsMode property.
@return			'all' or 'state'
"""
    return  self._weightsMode
  #end GetWeightsMode


  #----------------------------------------------------------------------
  #	METHOD:		Init()						-
  #----------------------------------------------------------------------
  def Init( self, fire_event_flag = False ):
    """Should be called only after the first DataModel is opened via
dataModelMgr.OpenModel().  Initializes with dataModelMgr.GetFirstDataModel().
#@param  data_model	DataModel to use for initializing properties
"""
    undefined_ax = DataModel.CreateEmptyAxialValue()
    #undefined_ax = ( 0.0, -1, -1 )
    undefined2 = ( -1, -1 )
    undefined3 = ( -1, -1, -1 )

    del self._auxNodeAddrs[ : ]
    del self._auxSubAddrs[ : ]
    #self.dataModel = data_model
    self._nodeAddr = 0

    self._scaleMode = 'all'
    self._tallyAddr = ( None, 0, 0 )
    self._weightsMode = 'on'

    data_model = self._dataModelMgr.GetFirstDataModel()
    if data_model is not None:
      core = data_model.GetCore()

      ##self._assemblyAddr = data_model.NormalizeAssemblyIndex( undefined3 )
      extent = data_model.ExtractSymmetryExtent()
      col = extent[ 0 ] + (extent[ 4 ] >> 1)
      row = extent[ 1 ] + (extent[ 5 ] >> 1)
      ndx = core.coreMap[ row, col ] - 1
      if ndx < 0:
        if col > 0: col -= 1
	if row > 0: row -= 1
        ndx = core.coreMap[ row, col ] - 1
      self._assemblyAddr = data_model.NormalizeAssemblyAddr( ( ndx, col, row ) )

      self._axialValue = data_model.CreateAxialValue( core_ndx = core.nax >> 1 )

      self._curDataSet = self._FindDefaultDataSet( data_model )
#      ds_display_name = 'pin_powers' \
#	  if 'pin_powers' in data_model.GetDataSetNames( 'pin' ) else \
#	  data_model.GetFirstDataSet( 'pin' )
#      self._curDataSet = DataSetName( data_model.GetName(), ds_display_name )
      #self.stateIndex = data_model.NormalizeStateIndex( -1 )

      ##self.colRow = data_model.NormalizeColRow( undefined2 )
      col = max( 0, (core.npinx >> 1) - 1 )
      row = max( 0, (core.npiny >> 1) - 1 )
      self._subAddr = data_model.NormalizeSubAddr( ( col, row ) )

      time_ds_names = self._dataModelMgr.ResolveAvailableTimeDataSets()
#      self._timeDataSet = \
#          'exposure'  if 'exposure' in time_ds_names else \
#	  'state'
##      self._timeDataSet = data_model.ResolveTimeDataSetName()
      self._timeDataSet = 'state'
      for t in TIME_DS_NAMES_LIST:
        if t in time_ds_names:
	  self._timeDataSet = t
	  break
      self._dataModelMgr.SetTimeDataSet( self._timeDataSet )
      self._timeValue = self._dataModelMgr.GetTimeIndexValue( 0 )

      if core.tally.IsValid():
	ds_names = data_model.GetDataSetNames( 'tally' )
#	ds_name = \
#	    'vessel_tally/total'  if 'vessel_tally/total' in ds_names else \
#	    ds_names[ 0 ]  if len( ds_names ) > 0 else \
#	    None
	ds_name = ds_names[ 0 ]  if len( ds_names ) > 0  else None
	qds_name = \
	    DataSetName( data_model.name, ds_name )  if ds_name else  None
        self._tallyAddr = ( qds_name, 0, 0 )

    else:
      self._assemblyAddr = undefined3
      self._axialValue = undefined_ax
      self._curDataSet = None
      self.scalarDataSet = None
      #self.stateIndex = -1
      self._subAddr = undefined2
      self._timeDataSet = 'state'
      self._timeValue = 0.0

    if fire_event_flag:
      self.FireStateChange( STATE_CHANGE_init | STATE_CHANGE_dataModelMgr )
  #end Init


  #----------------------------------------------------------------------
  #	METHOD:		LoadProps()					-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Deserializes.
@param  props_dict	dict containing property values
"""
    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs', 'axialValue', 
        'nodeAddr', 'scaleMode', 'subAddr',
	'tallyAddr', 'timeDataSet', 'timeValue', 'weightsMode'
        ):
      if k in props_dict:
        setattr( self, '_' + k, props_dict[ k ] )

    for k in ( 'curDataSet' ):
      if k in props_dict:
        setattr( self, k, DataSetName( props_dict[ k ] ) )
        #setattr( self, k, DataSetName.fromjson( props_dict[ k ] ) )

    if 'dataModelMgr.thresholds' in props_dict:
      self.dataModelMgr.\
          LoadDataSetThresholds( props_dict[ 'dataModelMgr.thresholds' ] )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		LogListeners()					-
  #----------------------------------------------------------------------
  def LogListeners( self, logger, header ):
    msg = ''
    for i in xrange( len( self._listeners ) ):
      l = self._listeners[ i ]
      ltype = type( l ).__name__
      msg += '\n  %3d: %s' % ( i, str( l ) )
      if ltype == 'WidgetContainer':
        msg += '\n    widget: %s' % str( l.widget )
      elif ltype == 'DataSetsMenu':
        msg += '\n    widget: %s' % str( l.widget )
    #end for i

    logger.info( header + msg )
  #end LogListeners


  #----------------------------------------------------------------------
  #	METHOD:		_OnDataModelMgr()				-
  #----------------------------------------------------------------------
  def _OnDataModelMgr( self, *args, **kwargs ):
    if self._dataModelMgr.GetDataModelCount() == 1:
      self.Init( True )

    else:
      change_args = { 'data_model_mgr' : self._dataModelMgr }

#			-- Resolve cur_dataset
#			--
      if self._curDataSet is None or not self._curDataSet.modelName or \
          self._curDataSet.modelName not in self._dataModelMgr.GetDataModelNames():
	change_args[ 'cur_dataset' ] = self._FindDefaultDataSet()

#			-- Resolve time_dataset
#			--
      new_name = ''
      time_ds_names = self._dataModelMgr.ResolveAvailableTimeDataSets()
      if len( time_ds_names ) == 0:
        new_name = 'state'
      elif self._timeDataSet not in time_ds_names:
        new_name = time_ds_names[ 0 ]

      if new_name:
	change_args[ 'time_dataset' ] = new_name
        #self.FireStateChange( self.Change( time_dataset = new_name ) )

      if len( change_args ) > 0:
        self.FireStateChange( self.Change( **change_args ) )
    #end if-else
    #xxxxx self.FireStateChange( STATE_CHANGE_dataModelMgr )
  #end _OnDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		RemoveListener()				-
  #----------------------------------------------------------------------
  def RemoveListener( self, *listeners ):
    """Removes the listener(s).
@param  listeners	one or more listeners to remove
"""
#    if listener in self._listeners:
#      self._listeners.remove( listener )
    if listeners:
      for listener in listeners:
        if listener in self._listeners:
          self._listeners.remove( listener )
  #end RemoveListener


  #----------------------------------------------------------------------
  #	METHOD:		ResolveLocks()					-
  #----------------------------------------------------------------------
  def ResolveLocks( self, reason, locks ):
    """
@return		resolved reason
"""
    if reason is None:
      reason = STATE_CHANGE_noop

    else:
      for mask, name in LOCKABLE_STATES:
        if not locks[ mask ]:
	  reason &= ~mask
      #end for
    #end if-else

    return  reason
  #end ResolveLocks


  #----------------------------------------------------------------------
  #	METHOD:		SaveProps()					-
  #----------------------------------------------------------------------
  def SaveProps( self, props_dict ):
    """Serializes.
@param  props_dict	dict to which to write property values
"""
    for k in (
        'assemblyAddr', 'auxNodeAddrs', 'auxSubAddrs', 'axialValue', 
        'nodeAddr', 'scaleMode', 'subAddr',
	'tallyAddr', 'timeDataSet', 'timeValue', 'weightsMode'
        ):
      props_dict[ k ] = getattr( self, '_' + k )

    for k in ( 'curDataSet', ):
      qds_name = self.dataModelMgr.\
          RevertIfDerivedDataSet( getattr( self, '_' + k ) )
      props_dict[ k ] = qds_name.name

    props_dict[ 'dataModelMgr.thresholds' ] = \
        self.dataModelMgr.SaveDataSetThresholds()
  #end SaveProps


  #----------------------------------------------------------------------
  #	METHOD:		SetDataSetByType()				-
  #----------------------------------------------------------------------
#  def SetDataSetByType( self, *ds_type_name_pairs ):
#    """Returns the current dataset for the type.
#@param  ds_type_name_pairs  category/type, name pairs to assign
#@return			reason mask
#"""
#    mask = STATE_CHANGE_noop
#    if ds_type_name_pairs:
#      for i in range( 0, len( ds_type_name_pairs ) - 1, 2 ):
#        ds_type = ds_type_name_pairs[ i ]
#        ds_name = ds_type_name_pairs[ i + 1 ]
#        attr_rec = State.DS_ATTR_BY_TYPE.get( ds_type )
#        if attr_rec and 'mask' in attr_rec and \
#	    hasattr( self, attr_rec[ 'attr' ] ):
#	  setattr( self, attr_rec[ 'attr' ], ds_name )
#	  mask |= attr_rec[ 'mask' ]
#    #end if ds_type_name_pairs
#
#    return  mask
#  #end SetDataSetByType


#		-- Property Definitions
#		--


  assemblyAddr = property( GetAssemblyAddr )
  auxNodeAddrs = property( GetAuxNodeAddrs )
  auxSubAddrs = property( GetAuxSubAddrs )
  axialValue = property( GetAxialValue )
  curDataSet = property( GetCurDataSet )
  dataModelMgr = property( GetDataModelMgr )
  nodeAddr = property( GetNodeAddr )
  scaleMode = property( GetScaleMode )
  subAddr = property( GetSubAddr )
  tallyAddr = property( GetTallyAddr )
  timeDataSet = property( GetTimeDataSet )
  timeValue = property( GetTimeValue )
  weightsMode = property( GetWeightsMode )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		CreateLocks()					-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateLocks():
    """
@return		dict with all True for LOCKABLE_STATES
"""
    locks = {}
    for mask, name in LOCKABLE_STATES:
      locks[ mask ] = True
    return  locks
  #end CreateLocks


  #----------------------------------------------------------------------
  #	METHOD:		FindDataModelMgr()				-
  #----------------------------------------------------------------------
  @staticmethod
  def FindDataModelMgr( state ):
    data_model_mgr = None
    if state is not None and state.dataModelMgr is not None:
      data_model_mgr = state.dataModelMgr

    return  data_model_mgr
  #end FindDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		GetAllLocks()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetAllLocks():
    """Lazily creates
@return		dict with all True for LOCKABLE_STATES
"""
    if State.allLocks_ is None:
      State.allLocks_ = State.CreateLocks()
    return  State.allLocks_
  #end GetAllLocks

#end State
