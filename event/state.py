#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		state.py					-
#	HISTORY:							-
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
import h5py, os, sys, traceback
import numpy as np
import pdb

from data.datamodel import *


# New, reduced set of events
STATE_CHANGE_noop = 0
STATE_CHANGE_init = 0x1 << 0
STATE_CHANGE_axialValue = 0x1 << 1
STATE_CHANGE_coordinates = 0x1 << 2
STATE_CHANGE_curDataSet = 0x1 << 3
STATE_CHANGE_dataModel = 0x1 << 4
STATE_CHANGE_scaleMode = 0x1 << 5
STATE_CHANGE_stateIndex = 0x1 << 6
STATE_CHANGE_timeDataSet = 0x1 << 7

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
    ( STATE_CHANGE_curDataSet, 'Selected Dataset' ),
    ( STATE_CHANGE_scaleMode, 'Scale Mode' ),
    ( STATE_CHANGE_stateIndex, 'State Point' )
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
|             | auxSubAddrs    | aux_sub_addrs  | list of ( col, row )         |
|             |                |                | 0-based channel/pin indexes  |
+-------------+----------------+----------------+------------------------------+
|             | subAddr        | sub_addr       | ( col, row )                 |
|             |                |                | 0-based channel/pin indexes  |
+-------------+----------------+----------------+------------------------------+
| curDataSet  | curDataSet     | cur_dataset    | name of selected dataset     |
|             |                |                | (of any type)                |
+-------------+----------------+----------------+------------------------------+
| dataModel   | dataModel      | data_model     | data.DataModel object        |
+-------------+----------------+----------------+------------------------------+
| scaleMode   | scaleMode      | scale_mode     | 'all' or 'state'             |
+-------------+----------------+----------------+------------------------------+
| stateIndex  | stateIndex     | state_index    | 0-based state-point index    |
+-------------+----------------+----------------+------------------------------+
| timeDataSet | timeDataSet    | time_dataset   | dataset to use for "time"    |
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
    self.auxSubAddrs = []
    self.axialValue = DataModel.CreateEmptyAxialValue()
    self.curDataSet = 'pin_powers'
    self.dataModel = None
    self.listeners = []
    self.scaleMode = 'all'
    self.stateIndex = -1
    self.subAddr = ( -1, -1 )
    self.timeDataSet = 'state'

    self.Change( State.CreateLocks(), **kwargs )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    """This needs to be updated.  Perhaps dump the JSON sans dataModel.
"""
    coord = self.assemblyAddr + self.colRow + tuple( self.auxColRows )
    result = 'axial=%s,coord=%s,dataset=%s,scale=%s,state=%d,time=%s' % \
        (
	str( self.axialValue ), str( coord ),
	self.curDataSet, self.scaleMode,
	self.stateIndex, self.timeDataSet
        )
    return  result
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		AddListener()					-
  #----------------------------------------------------------------------
  def AddListener( self, listener ):
    """Adds the listener if not already added.  Listeners must implement
a HandleStateChange( self, reason ) method.
"""
    if listener not in self.listeners:
      self.listeners.append( listener )
  #end AddListener


  #----------------------------------------------------------------------
  #	METHOD:		Change()					-
  #----------------------------------------------------------------------
  def Change( self, locks, **kwargs ):
    """Applies the property changes specified in kwargs that are allowed
by locks.
@param  locks		dictionary of True/False values for each of the
			STATE_CHANGE_xxx indexes
@param  kwargs		name, value pairs with which to update this

Keys passed and the corresponding state bit are:
  assembly_addr		STATE_CHANGE_coordinates
  aux_sub_addrs		STATE_CHANGE_coordinates
  axial_value		STATE_CHANGE_axialValue
  cur_dataset		STATE_CHANGE_curDataSet
  data_model		STATE_CHANGE_dataModel
  scale_mode		STATE_CHANGE_scaleMode
  state_index		STATE_CHANGE_stateIndex
  sub_addr		STATE_CHANGE_coordinates
  time_dataset		STATE_CHANGE_timeDataSet
@return			change reason mask
"""
    reason = STATE_CHANGE_noop

    if 'assembly_addr' in kwargs and locks[ STATE_CHANGE_coordinates ]:
      self.assemblyAddr = kwargs[ 'assembly_addr' ]
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

    if 'data_model' in kwargs:
      self.dataModel = kwargs[ 'data_model' ]
      reason |= STATE_CHANGE_dataModel

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

#		-- Wire assembly_index and detector_index together
#		--
#    if (reason & STATE_CHANGE_assemblyIndex) > 0:
#      if (reason & STATE_CHANGE_detectorIndex) == 0 and \
#          self.dataModel.core.detectorMap is not None:
#	col = self.assemblyIndex[ 1 ]
#	row = self.assemblyIndex[ 2 ]
#	det_ndx = self.dataModel.core.detectorMap[ row, col ] - 1
#	reason |= STATE_CHANGE_detectorIndex
#	self.detectorIndex = ( det_ndx, col, row )
#
#    elif (reason & STATE_CHANGE_detectorIndex) > 0:
#      if (reason & STATE_CHANGE_assemblyIndex) == 0:
#          #self.dataModel.core.coreMap is not None:
#	col = self.detectorIndex[ 1 ]
#	row = self.detectorIndex[ 2 ]
#	assy_ndx = self.dataModel.core.coreMap[ row, col ] - 1
#	reason |= STATE_CHANGE_assemblyIndex
#	self.assemblyIndex = ( assy_ndx, col, row )
#    #end if

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
      update_args[ 'aux_sub_addrs' ] = self.auxSubAddrs
      update_args[ 'sub_addr' ] = self.subAddr

    if (reason & STATE_CHANGE_curDataSet) > 0:
      update_args[ 'cur_dataset' ] = self.curDataSet

    if (reason & STATE_CHANGE_dataModel) > 0:
      update_args[ 'data_model' ] = self.dataModel

    if (reason & STATE_CHANGE_scaleMode) > 0:
      update_args[ 'scale_mode' ] = self.scaleMode

    if (reason & STATE_CHANGE_stateIndex) > 0:
      update_args[ 'state_index' ] = self.stateIndex

    if (reason & STATE_CHANGE_timeDataSet) > 0:
      update_args[ 'time_dataset' ] = self.timeDataSet

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
          listener.HandleStateChange( reason )
	except Exception, ex:
	  print >> sys.stderr, '[State.FireStateChange] ' + str( ex )
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
@return			name of current/selected dataset
"""
    return  self.curDataSet
  #end GetCurDataSet


  #----------------------------------------------------------------------
  #	METHOD:		GetDataModel()					-
  #----------------------------------------------------------------------
  def GetDataModel( self ):
    """Accessor for the dataModel property.
@return			DataModel object
"""
    return  self.dataModel
  #end GetDataModel


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
  #	METHOD:		Load()						-
  #----------------------------------------------------------------------
  def Load( self, data_model = None ):
    """
@param  data_model	if None, use the current dataModel
"""
    undefined_ax = DataModel.CreateEmptyAxialValue()
    #undefined_ax = ( 0.0, -1, -1 )
    undefined2 = ( -1, -1 )
    undefined3 = ( -1, -1, -1 )

    del self.auxSubAddrs[ : ]
    self.dataModel = data_model
    self.scaleMode = 'all'

    if data_model is not None:
      core = data_model.GetCore()

      ##self.assemblyAddr = data_model.NormalizeAssemblyIndex( undefined3 )
      extent = data_model.ExtractSymmetryExtent()
      col = extent[ 0 ] + (extent[ 4 ] >> 1)
      row = extent[ 1 ] + (extent[ 5 ] >> 1)
      ndx = core.coreMap[ row, col ] - 1
      self.assemblyAddr = data_model.NormalizeAssemblyAddr( ( ndx, col, row ) )

      ##self.axialValue = data_model.NormalizeAxialValue( undefined_ax )
      self.axialValue = data_model.CreateAxialValue( core_ndx = core.nax >> 1 )

      #self.channelDataSet = data_model.GetFirstDataSet( 'channel' )

      #self.detectorDataSet = data_model.GetFirstDataSet( 'detector' )
      #self.detectorIndex = data_model.NormalizeDetectorIndex( undefined3 )
      #self.fixedDetectorDataSet = data_model.GetFirstDataSet( 'fixed_detector' )
      self.curDataSet = 'pin_powers' \
	  if 'pin_powers' in data_model.GetDataSetNames( 'pin' ) else \
	  data_model.GetFirstDataSet( 'pin' )
      #self.scalarDataSet = data_model.GetDefaultScalarDataSet()
      self.stateIndex = data_model.NormalizeStateIndex( -1 )

      ##self.colRow = data_model.NormalizeColRow( undefined2 )
      col = max( 0, (core.npinx >> 1) - 1 )
      row = max( 0, (core.npiny >> 1) - 1 )
      self.subAddr = data_model.NormalizeSubAddr( ( col, row ) )

      self.timeDataSet = 'exposure' \
          if 'exposure' in data_model.GetDataSetNames( 'time' ) else \
	  'state'
      ##self.timeDataSet = data_model.ResolveTimeDataSetName()

    else:
      self.assemblyAddr = undefined3
      self.axialValue = undefined_ax
      self.curDataSet = None
      self.scalarDataSet = None
      self.stateIndex = -1
      self.subAddr = undefined2
      self.timeDataSet = 'state'

    self.auxColRows = []
  #end Load


  #----------------------------------------------------------------------
  #	METHOD:		LoadProps()					-
  #----------------------------------------------------------------------
  def LoadProps( self, props_dict ):
    """Deserializes.
@param  props_dict	dict containing property values
"""
    for k in (
        'assemblyAddr', 'auxSubAddrs', 'axialValue', 
        'curDataSet', 'scaleMode', 'stateIndex',
	'subAddr', 'timeDataSet'
        ):
      if k in props_dict:
        setattr( self, k, props_dict[ k ] )
  #end LoadProps


  #----------------------------------------------------------------------
  #	METHOD:		RemoveListener()				-
  #----------------------------------------------------------------------
  def RemoveListener( self, listener ):
    """Removes the listener.
"""
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
        'assemblyAddr', 'auxSubAddrs', 'axialValue', 
        'curDataSet', 'scaleMode', 'stateIndex',
	'subAddr', 'timeDataSet'
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
  #	METHOD:		FindDataModel()					-
  #----------------------------------------------------------------------
  @staticmethod
  def FindDataModel( state ):
    data_model = None
    if state is not None and state.dataModel is not None:
      data_model = state.dataModel

    return  data_model
  #end FindDataModel
#end State
