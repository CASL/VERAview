#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		state.py					-
#	HISTORY:							-
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


#LABEL_selectedDataSet = 'Selected Dataset'
LABEL_selectedDataSet = DataSetName( 'Selected Dataset' )


# New, reduced set of events
STATE_CHANGE_noop = 0
STATE_CHANGE_init = 0x1 << 0		# never generated here
STATE_CHANGE_axialValue = 0x1 << 1
STATE_CHANGE_coordinates = 0x1 << 2
STATE_CHANGE_curDataSet = 0x1 << 3
STATE_CHANGE_dataModelMgr = 0x1 << 4	# maybe should toss this, not used?
STATE_CHANGE_scaleMode = 0x1 << 5
STATE_CHANGE_stateIndex = 0x1 << 6
STATE_CHANGE_timeDataSet = 0x1 << 7
STATE_CHANGE_timeValue = 0x1 << 8
STATE_CHANGE_weightsMode = 0x1 << 9

STATE_CHANGE_ALL = 0xffffffff

# These are in the order of being added
##  STATE_CHANGE_noop = 0
##  STATE_CHANGE_init = 0x1 << 0
##  STATE_CHANGE_dataModel = 0x1 << 1
##  STATE_CHANGE_assemblyIndex = 0x1 << 2
##  ##STATE_CHANGE_axialLevel = 0x1 << 3
##  STATE_CHANGE_axialValue = 0x1 << 3
##  STATE_CHANGE_stateIndex = 0x1 << 4
##  #STATE_CHANGE_pinColRow = 0x1 << 5
##  STATE_CHANGE_colRow = 0x1 << 5
##  STATE_CHANGE_pinDataSet = 0x1 << 6
##  STATE_CHANGE_scalarDataSet = 0x1 << 7
##  STATE_CHANGE_detectorDataSet = 0x1 << 8
##  STATE_CHANGE_detectorIndex = 0x1 << 9
##  STATE_CHANGE_channelDataSet = 0x1 << 10
##  #STATE_CHANGE_channelColRow = 0x1 << 11
##  STATE_CHANGE_timeDataSet = 0x1 << 12
##  STATE_CHANGE_scaleMode = 0x1 << 13
##  #STATE_CHANGE_auxChannelColRows = 0x1 << 14
##  #STATE_CHANGE_auxPinColRows = 0x1 << 15
##  STATE_CHANGE_auxColRows = 0x1 << 15
##  STATE_CHANGE_fixedDetectorDataSet = 0x1 << 16
##  #STATE_CHANGE_ALL = 0x1fff


# New, reduced set of events
LOCKABLE_STATES = \
  [
    ( STATE_CHANGE_axialValue, 'Axial Value' ),
    ( STATE_CHANGE_coordinates, 'Coordinates' ),
    ( STATE_CHANGE_curDataSet, LABEL_selectedDataSet ),
    ( STATE_CHANGE_scaleMode, 'Scale Mode' ),
    ( STATE_CHANGE_stateIndex, 'State Point' ),
    ( STATE_CHANGE_timeValue, 'Time' )
  ]

##  LOCKABLE_STATES = \
##    (
##    STATE_CHANGE_assemblyIndex,
##  #  STATE_CHANGE_auxChannelColRows,
##    STATE_CHANGE_auxColRows,
##  #  STATE_CHANGE_auxPinColRows,
##    STATE_CHANGE_axialValue,
##  #  STATE_CHANGE_channelColRow,
##    STATE_CHANGE_channelDataSet,
##    STATE_CHANGE_colRow,
##    STATE_CHANGE_detectorDataSet,
##    STATE_CHANGE_detectorIndex,
##  #  STATE_CHANGE_pinColRow,
##    STATE_CHANGE_pinDataSet,
##    STATE_CHANGE_scalarDataSet,
##    STATE_CHANGE_scaleMode,
##    STATE_CHANGE_stateIndex,
##    STATE_CHANGE_timeDataSet,
##    STATE_CHANGE_fixedDetectorDataSet
##    )


# New, reduced set of events

##  EVENT_ID_NAMES = \
##    [
##      ( STATE_CHANGE_assemblyIndex, 'Assembly Index' ),
##      ( STATE_CHANGE_axialValue, 'Axial Value' ),
##  #    ( STATE_CHANGE_channelColRow, 'Channel Column and Row' ),
##  #    ( STATE_CHANGE_auxChannelColRows, '2ndary Channel Column and Row' ),
##      ( STATE_CHANGE_channelDataSet, 'Channel Dataset' ),
##  #    ( STATE_CHANGE_colRow, 'Pin/Channel Column and Row' ),
##      ( STATE_CHANGE_colRow, 'Column and Row' ),
##  #    ( STATE_CHANGE_auxColRows, '2ndary Pin/Channel Column and Row' ),
##      ( STATE_CHANGE_auxColRows, '2ndary Column and Row' ),
##      ( STATE_CHANGE_detectorDataSet, 'Detector Dataset' ),
##      ( STATE_CHANGE_detectorIndex, 'Detector Index' ),
##  #    ( STATE_CHANGE_pinColRow, 'Pin Column and Row' ),
##  #    ( STATE_CHANGE_auxPinColRows, '2ndary Pin Column and Row' ),
##      ( STATE_CHANGE_pinDataSet, 'Pin Dataset' ),
##      ( STATE_CHANGE_scalarDataSet, 'Scalar Dataset' ),
##      ( STATE_CHANGE_stateIndex, 'State Point Index' ),
##      ( STATE_CHANGE_fixedDetectorDataSet, 'Fixed Detector Dataset' )
##    ]


#------------------------------------------------------------------------
#	CLASS:		State						-
#------------------------------------------------------------------------
class State( object ):
  """Event state object.  State attributes currently in use are as follows.
All indices are 0-based.

+-------------+----------------+----------------+------------------------------+
|             | State          |                |                              |
| Event Name  | Attrs/Props    | Param Name     | Param Value                  |
+=============+================+================+==============================+
| axialValue  | axialValue     | axial_value    | ( float value(cm), core-ndx, |
|             |                |                |   detector-index,            |
|             |                |                |   fixed-detector-index )     |
+-------------+----------------+----------------+------------------------------+
| coordinates | assemblyAddr   | assembly_addr  | ( index, col, row )          |
|             |                |                | 0-based assembly/detector    |
|             |                |                | indexes                      |
+-------------+----------------+----------------+------------------------------+
|             | auxNodeAddrs   | aux_node_addrs | list of 0-based indexes      |
+-------------+----------------+----------------+------------------------------+
|             | auxSubAddrs    | aux_sub_addrs  | list of ( col, row )         |
|             |                |                | 0-based channel/pin indexes  |
+-------------+----------------+----------------+------------------------------+
|             | nodeAddr       | node_addr      | 0-based node index in range  |
|             |                |                | [0,3] or [0,4)               |
+-------------+----------------+----------------+------------------------------+
|             | subAddr        | sub_addr       | ( col, row )                 |
|             |                |                | 0-based channel/pin indexes  |
+-------------+----------------+----------------+------------------------------+
| curDataSet  | curDataSet     | cur_dataset    | DataSetName instance         |
|             |                |                | (of any type)                |
+-------------+----------------+----------------+------------------------------+
| dataModelMgr| dataModelMgr   | data_model_mgr | data.DataModelMgr object     |
+-------------+----------------+----------------+------------------------------+
| scaleMode   | scaleMode      | scale_mode     | 'all' or 'state'             |
+-------------+----------------+----------------+------------------------------+
| stateIndex  | stateIndex     | state_index    | 0-based state-point index    |
+-------------+----------------+----------------+------------------------------+
| timeDataSet | timeDataSet    | time_dataset   | dataset to use for "time"    |
+-------------+----------------+----------------+------------------------------+
| timeValue   | timeValue      | time_value     | time dataset value           |
|             |                |                | (replaces stateIndex)        |
+-------------+----------------+----------------+------------------------------+
| weightsMode | weightsMode    | weights_mode   | 'on' or 'off'                |
+-------------+----------------+----------------+------------------------------+
"""

#		-- Class Attributes
#		--

##    DS_ATTR_BY_TYPE = \
##      {
##      'channel':
##        { 'attr': 'channelDataSet', 'mask': STATE_CHANGE_channelDataSet,
##          'param': 'channel_dataset' },
##      'detector':
##        { 'attr': 'detectorDataSet', 'mask': STATE_CHANGE_detectorDataSet,
##          'param': 'detector_dataset' },
##      'fixed_detector':
##        { 'attr': 'fixedDetectorDataSet',
##          'mask': STATE_CHANGE_fixedDetectorDataSet,
##          'param': 'fixed_detector_dataset' },
##      'pin':
##        { 'attr': 'pinDataSet', 'mask': STATE_CHANGE_pinDataSet,
##          'param': 'pin_dataset' },
##      'scalar':
##        { 'attr': 'scalarDataSet', 'mask': STATE_CHANGE_scalarDataSet,
##          'param': 'scalar_dataset' },
##      'time':
##        { 'attr': 'timeDataSet', 'mask': STATE_CHANGE_timeDataSet,
##          'param': 'time_dataset' }
##      }

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    self.assemblyAddr = ( -1, -1, -1 )
    self.auxNodeAddrs = []
    self.auxSubAddrs = []
    self.axialValue = DataModel.CreateEmptyAxialValue()
    self.curDataSet = DataSetName( 'pin_powers' )
    self.dataModelMgr = DataModelMgr()
    self.listeners = []
    self.logger = logging.getLogger( 'event' )
    self.nodeAddr = -1
    self.scaleMode = 'all'
    self.stateIndex = -1
    self.subAddr = ( -1, -1 )
    self.timeDataSet = 'state'
    self.timeValue = 0.0
    self.weightsMode = 'on'

    self.Change( State.CreateLocks(), **kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    """This needs to be updated.  Perhaps dump the JSON sans dataModelMgr.
"""
    coord = self.assemblyAddr + self.colRow + tuple( self.auxColRows )
    result = 'axial=%s,coord=%s,dataset=%s,scale=%s,state=%d,timeDataSet=%s,time=%f,weights=%s' % \
        (
	str( self.axialValue ), str( coord ),
	self.curDataSet, self.scaleMode,
	self.stateIndex, self.timeDataSet,
	self.timeValue, self.weightsMode
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
#    if listener not in self.listeners:
#      self.listeners.append( listener )
    if listeners:
      for listener in listeners:
        if listener not in self.listeners:
          self.listeners.append( listener )
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
  scale_mode		STATE_CHANGE_scaleMode
  state_index		STATE_CHANGE_stateIndex
  sub_addr		STATE_CHANGE_coordinates
  time_dataset		STATE_CHANGE_timeDataSet
  time_value		STATE_CHANGE_timeValue
  weights_mode		STATE_CHANGE_weightsMode
@return			change reason mask
"""
    reason = STATE_CHANGE_noop
    if locks is None:
      locks = State.CreateLocks()

    if 'assembly_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
      reason |= STATE_CHANGE_coordinates

    if 'aux_node_addrs' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.auxNodeAddrs = kwargs[ 'aux_node_addrs' ]
      reason |= STATE_CHANGE_coordinates

    if 'aux_sub_addrs' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.auxSubAddrs = kwargs[ 'aux_sub_addrs' ]
      reason |= STATE_CHANGE_coordinates

    if 'axial_value' in kwargs and locks[ STATE_CHANGE_axialValue ]:
      self.axialValue = kwargs[ 'axial_value' ]
      reason |= STATE_CHANGE_axialValue

    if 'cur_dataset' in kwargs and locks[ STATE_CHANGE_curDataSet ]:
      self.curDataSet = kwargs[ 'cur_dataset' ]
      reason |= STATE_CHANGE_curDataSet

    if 'data_model_mgr' in kwargs:
      self.dataModelMgr = kwargs[ 'data_model_mgr' ]
      reason |= STATE_CHANGE_dataModelMgr

    if 'node_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.nodeAddr = kwargs[ 'node_addr' ]
      reason |= STATE_CHANGE_coordinates

    if 'scale_mode' in kwargs and locks[ STATE_CHANGE_scaleMode ]:
      self.scaleMode = kwargs[ 'scale_mode' ]
      reason |= STATE_CHANGE_scaleMode

    if 'state_index' in kwargs and locks[ STATE_CHANGE_stateIndex ]:
      self.stateIndex = kwargs[ 'state_index' ]
      reason |= STATE_CHANGE_stateIndex

    if 'sub_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.subAddr = kwargs[ 'sub_addr' ]
      reason |= STATE_CHANGE_coordinates

    #if 'time_dataset' in kwargs and locks[ STATE_CHANGE_timeDataSet ]:
    if 'time_dataset' in kwargs:
      if self.timeDataSet != kwargs[ 'time_dataset' ]:
        self.timeDataSet = kwargs[ 'time_dataset' ]
        reason |= STATE_CHANGE_timeDataSet

    if 'time_value' in kwargs and locks[ STATE_CHANGE_timeValue ]:
      self.timeValue = kwargs[ 'time_value' ]
      reason |= STATE_CHANGE_timeValue

    if 'weights_mode' in kwargs:
      self.weightsMode = kwargs[ 'weights_mode' ]
      reason |= STATE_CHANGE_weightsMode

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
      update_args[ 'axial_value' ] = self.axialValue

    if (reason & STATE_CHANGE_coordinates) > 0:
      update_args[ 'assembly_addr' ] = self.assemblyAddr
      update_args[ 'aux_node_addrs' ] = self.auxNodeAddrs
      update_args[ 'aux_sub_addrs' ] = self.auxSubAddrs
      update_args[ 'node_addr' ] = self.nodeAddr
      update_args[ 'sub_addr' ] = self.subAddr

    if (reason & STATE_CHANGE_curDataSet) > 0:
      update_args[ 'cur_dataset' ] = self.curDataSet

    if (reason & STATE_CHANGE_dataModelMgr) > 0:
      update_args[ 'data_model_mgr' ] = self.dataModelMgr

    if (reason & STATE_CHANGE_scaleMode) > 0:
      update_args[ 'scale_mode' ] = self.scaleMode

    if (reason & STATE_CHANGE_stateIndex) > 0:
      update_args[ 'state_index' ] = self.stateIndex

    if (reason & STATE_CHANGE_timeDataSet) > 0:
      update_args[ 'time_dataset' ] = self.timeDataSet

    if (reason & STATE_CHANGE_timeValue) > 0:
      update_args[ 'time_value' ] = self.timeValue

    if (reason & STATE_CHANGE_weightsMode) > 0:
      update_args[ 'weights_mode' ] = self.weightsMode

    return  update_args
  #end CreateUpdateArgs


  #----------------------------------------------------------------------
  #	METHOD:		FireStateChange()				-
  #----------------------------------------------------------------------
  def FireStateChange( self, reason ):
    """Notifies all listeners of the change if not noop.
@param  reason		reason mask
"""
    if reason != STATE_CHANGE_noop:
      for listener in self.listeners:
	try:
	  if hasattr( listener, 'HandleStateChange' ):
            listener.HandleStateChange( reason )
	  elif hasattr( listener, '__call__' ):
	    listener( reason )
	except Exception, ex:
	  self.logger.error( str( ex ) )
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
    return  self.assemblyAddr
  #end GetAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetAuxNodeAddrs()				-
  #----------------------------------------------------------------------
  def GetAuxNodeAddrs( self ):
    """Accessor for the auxNodeAddrs property.
@return			list of 0-based indexes, possibly empty
"""
    return  self.auxNodeAddrs
  #end GetAuxNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		GetAuxSubAddrs()				-
  #----------------------------------------------------------------------
  def GetAuxSubAddrs( self ):
    """Accessor for the auxSubAddrs property.
@return			list of 0-based channel/pin ( col, row ) indexes,
			possibly empty
"""
    return  self.auxSubAddrs
  #end GetAuxSubAddrs


  #----------------------------------------------------------------------
  #	METHOD:		GetAxialValue()					-
  #----------------------------------------------------------------------
  def GetAxialValue( self ):
    """Accessor for the axialValue property.
@return			( float value(cm), core-index, detector-index,
			  fixed-detector-index ), all indexes 0-based
"""
    return  self.axialValue
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		GetCurDataSet()					-
  #----------------------------------------------------------------------
  def GetCurDataSet( self ):
    """Accessor for the curDataSet property.
@return			DataSetName instance, name of current/selected dataset
"""
    return  self.curDataSet
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		GetDataModelMgr()				-
  #----------------------------------------------------------------------
  def GetDataModelMgr( self ):
    """Accessor for the dataModelMgr property.
@return			DataModelMgr object
"""
    return  self.dataModelMgr
  #end GetDataModelMgr


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetByType()				-
  #----------------------------------------------------------------------
#  def GetDataSetByType( self, ds_type ):
#    """Returns the current dataset for the type.
#@param  ds_type		one of the categories/types defined in DataModel
#@return			current dataset or None
#"""
#    result = None
#    attr_rec = State.DS_ATTR_BY_TYPE.get( ds_type )
#    if attr_rec and hasattr( self, attr_rec[ 'attr' ] ):
#      result = getattr( self, attr_rec[ 'attr' ] )
#    return  result
#  #end GetDataSetByType


  #----------------------------------------------------------------------
  #	METHOD:		GetDataSetChanges()				-
  #----------------------------------------------------------------------
#  def GetDataSetChanges( self, reason ):
#    """Returns a dict of dataset selection changes by category/type
#@param  reason		reason mask
#@return			dict by category/type of new names
#"""
#    changes = {}
#    for ds_type, rec in State.DS_ATTR_BY_TYPE.iteritems():
#      if (reason & rec[ 'mask' ]) > 0:
#	changes[ ds_type ] = getattr( self, rec[ 'attr' ] )
#    #end for
#
#    return  changes
#  #end GetDataSetChanges


  #----------------------------------------------------------------------
  #	METHOD:		GetNodeAddr()					-
  #----------------------------------------------------------------------
  def GetNodeAddr( self ):
    """Accessor for the nodeAddr property.
@return			0-based node index in range [0,3] or [0,4)
"""
    return  self.nodeAddr
  #end GetNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetScaleMode()					-
  #----------------------------------------------------------------------
  def GetScaleMode( self ):
    """Accessor for the scaleMode property.
@return			'all' or 'state'
"""
    return  self.scaleMode
  #end GetScaleMode


  #----------------------------------------------------------------------
  #	METHOD:		GetStateIndex()					-
  #----------------------------------------------------------------------
  def GetStateIndex( self ):
    """Accessor for the stateIndex property.
@return			0-based state-point index
"""
    return  self.stateIndex
  #end GetStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		GetSubAddr()					-
  #----------------------------------------------------------------------
  def GetSubAddr( self ):
    """Accessor for the subAddr property.
@return			0-based ( col, row ) channel/pin indexes
"""
    return  self.subAddr
  #end GetSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		GetTimeDataSet()				-
  #----------------------------------------------------------------------
  def GetTimeDataSet( self ):
    """Accessor for the timeDataSet property.
@return			dataset used for time
"""
    return  self.timeDataSet
  #end GetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		GetTimeValue()					-
  #----------------------------------------------------------------------
  def GetTimeValue( self ):
    """Accessor for the timeValue property.
@return			current timeDataSet value
"""
    return  self.timeValue
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		GetWeightsMode()				-
  #----------------------------------------------------------------------
  def GetWeightsMode( self ):
    """Accessor for the weightsMode property.
@return			'all' or 'state'
"""
    return  self.weightsMode
  #end GetWeightsMode


  #----------------------------------------------------------------------
  #	METHOD:		Init()						-
  #----------------------------------------------------------------------
  def Init( self, data_model ):
    """Initializes with the specified data_model.  It is assumed data_model
has already been added to dataModelMgr.
@param  data_model	DataModel to use for initializing properties
"""
    undefined_ax = DataModel.CreateEmptyAxialValue()
    #undefined_ax = ( 0.0, -1, -1 )
    undefined2 = ( -1, -1 )
    undefined3 = ( -1, -1, -1 )

    del self.auxNodeAddrs[ : ]
    del self.auxSubAddrs[ : ]
    #self.dataModel = data_model
    self.nodeAddr = 0

    self.scaleMode = 'all'
    self.weightsMode = 'on'

    if data_model is not None:
      core = data_model.GetCore()

      ##self.assemblyAddr = data_model.NormalizeAssemblyIndex( undefined3 )
      extent = data_model.ExtractSymmetryExtent()
      col = extent[ 0 ] + (extent[ 4 ] >> 1)
      row = extent[ 1 ] + (extent[ 5 ] >> 1)
      ndx = core.coreMap[ row, col ] - 1
      if ndx < 0:
        if col > 0: col -= 1
	if row > 0: row -= 1
        ndx = core.coreMap[ row, col ] - 1
      self.assemblyAddr = data_model.NormalizeAssemblyAddr( ( ndx, col, row ) )

      self.axialValue = data_model.CreateAxialValue( core_ndx = core.nax >> 1 )

      ds_display_name = 'pin_powers' \
	  if 'pin_powers' in data_model.GetDataSetNames( 'pin' ) else \
	  data_model.GetFirstDataSet( 'pin' )
      self.curDataSet = DataSetName( data_model.GetName(), ds_display_name )
      self.stateIndex = data_model.NormalizeStateIndex( -1 )

      ##self.colRow = data_model.NormalizeColRow( undefined2 )
      col = max( 0, (core.npinx >> 1) - 1 )
      row = max( 0, (core.npiny >> 1) - 1 )
      self.subAddr = data_model.NormalizeSubAddr( ( col, row ) )

      self.timeDataSet = 'exposure' \
          if 'exposure' in data_model.GetDataSetNames( 'time' ) else \
	  'state'
      ##self.timeDataSet = data_model.ResolveTimeDataSetName()
      if self.timeDataSet == 'state':
        self.timeValue = 0.0
      else:
        time_dset = data_model.GetStateDataSet( 0, self.timeDataSet )
	self.timeValue = \
	    time_dset[ 0 ] if len( time_dset.shape ) > 0 else time_dset[ () ]

    else:
      self.assemblyAddr = undefined3
      self.axialValue = undefined_ax
      self.curDataSet = None
      self.scalarDataSet = None
      self.stateIndex = -1
      self.subAddr = undefined2
      self.timeDataSet = 'state'
      self.timeValue = 0.0

    self.auxColRows = []
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
        'nodeAddr', 'scaleMode', 'stateIndex',
	'subAddr', 'timeDataSet', 'weightsMode'
        ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )

    for k in ( 'curDataSet' ):
      if k in props_dict:
        setattr( self, k, DataSetName.fromjson( props_dict[ k ] ) )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		RemoveListener()				-
  #----------------------------------------------------------------------
  def RemoveListener( self, *listeners ):
    """Removes the listener(s).
@param  listeners	one or more listeners to remove
"""
#    if listener in self.listeners:
#      self.listeners.remove( listener )
    if listeners:
      for listener in listeners:
        if listener in self.listeners:
          self.listeners.remove( listener )
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
        'curDataSet', 'nodeAddr', 'scaleMode', 'stateIndex',
	'subAddr', 'timeDataSet', 'weightsMode'
        ):
      props_dict[ k ] = getattr( self, k )
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


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		CreateLocks()					-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateLocks():
    """
@return		dict with all True for
    STATE_CHANGE_axialValue
    STATE_CHANGE_coordinates
    STATE_CHANGE_curDataSet
    STATE_CHANGE_stateIndex
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
#end State
