#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		state.py					-
#	HISTORY:							-
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


# These are in the order of being added
STATE_CHANGE_noop = 0
STATE_CHANGE_init = 0x1 << 0
STATE_CHANGE_dataModel = 0x1 << 1
STATE_CHANGE_assemblyIndex = 0x1 << 2
#STATE_CHANGE_axialLevel = 0x1 << 3
STATE_CHANGE_axialValue = 0x1 << 3
STATE_CHANGE_stateIndex = 0x1 << 4
STATE_CHANGE_pinColRow = 0x1 << 5
STATE_CHANGE_pinDataSet = 0x1 << 6
STATE_CHANGE_scalarDataSet = 0x1 << 7
STATE_CHANGE_detectorDataSet = 0x1 << 8
STATE_CHANGE_detectorIndex = 0x1 << 9
STATE_CHANGE_channelDataSet = 0x1 << 10
STATE_CHANGE_channelColRow = 0x1 << 11
STATE_CHANGE_timeDataSet = 0x1 << 12
#STATE_CHANGE_ALL = 0x1fff

LOCKABLE_STATES = \
  (
  STATE_CHANGE_assemblyIndex,
  #STATE_CHANGE_axialLevel,
  STATE_CHANGE_axialValue,
  STATE_CHANGE_channelColRow,
  STATE_CHANGE_channelDataSet,
  STATE_CHANGE_detectorDataSet,
  STATE_CHANGE_detectorIndex,
  STATE_CHANGE_pinColRow,
  STATE_CHANGE_pinDataSet,
  STATE_CHANGE_scalarDataSet,
  STATE_CHANGE_stateIndex,
  STATE_CHANGE_timeDataSet
  )


#------------------------------------------------------------------------
#	CLASS:		State						-
#------------------------------------------------------------------------
class State( object ):
  """Event state object.  State attributes currently in use are as follows.
All indices are 0-based.

  assemblyIndex			( int index, int column, int row )
  axialValue			( float value(cm), int core-index, int detector-index )
  channelColRow			str name
  channelDataSet		str name
  dataModel			DataModel object
  detectorDataSet		str name
  detectorIndex			( int index, int column, int row )
  pinColRow			( int column, int row )
  pinDataSet			str name
  scalarDataSet			str name
  stateIndex			int index
  timeDataSet			state dataset to be used for "time"
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    self.assemblyIndex = ( -1, -1, -1 )
    #self.axialLevel = -1
    self.axialValue = ( 0.0, -1, -1 )
    self.channelColRow = ( -1, -1 )
    self.channelDataSet = 'channel_liquid_temps [C]'
    self.dataModel = None
    self.detectorDataSet = 'detector_response'
    self.detectorIndex = ( -1, -1, -1 )
    self.pinColRow = ( -1, -1 )
    self.pinDataSet = 'pin_powers'
    self.scalarDataSet = 'keff'
    self.stateIndex = -1
    self.timeDataSet = 'state'

    if 'assembly_index' in kwargs:
      self.assemblyIndex = kwargs[ 'assembly_index' ]
    if 'axial_value' in kwargs:
      self.axialValue = kwargs[ 'axial_value' ]
    if 'channel_colrow' in kwargs:
      self.channelColRow = kwargs[ 'channel_colrow' ]
    if 'channel_dataset' in kwargs:
      self.channelDataSet = kwargs[ 'channel_dataset' ]
    if 'data_model' in kwargs:
      self.dataModel = kwargs[ 'data_model' ]
    if 'detector_dataset' in kwargs:
      self.detectorDataSet = kwargs[ 'detector_dataset' ]
    if 'detector_index' in kwargs:
      self.detectorIndex = kwargs[ 'detector_index' ]
    if 'pin_colrow' in kwargs:
      self.pinColRow = kwargs[ 'pin_colrow' ]
    if 'pin_dataset' in kwargs:
      self.pinDataSet = kwargs[ 'pin_dataset' ]
    if 'scalar_dataset' in kwargs:
      self.scalarDataSet = kwargs[ 'scalar_dataset' ]
    if 'state_index' in kwargs:
      self.stateIndex = kwargs[ 'state_index' ]
    if 'time_dataset' in kwargs:
      self.timeDataSet = kwargs[ 'time_dataset' ]
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    """This needs to be updated.  Perhaps dump the JSON sans dataModel.
"""
    result = \
        'assembly=%s,axial=%s,datasets=(%s,%s),pin=%d,%d,state=%d' % ( \
	    str( self.assemblyIndex ), str( self.axialValue ), \
	    self.pinDataSet, self.scalarDataSet, \
	    self.pinColRow[ 1 ], self.pinColRow[ 0 ], self.stateIndex \
	    )
    return  result
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		Change()					-
  #----------------------------------------------------------------------
  def Change( self, locks, **kwargs ):
    """
Keys passed and the corresponding state bit are:
  assembly_index	STATE_CHANGE_assemblyIndex
  axial_value		STATE_CHANGE_axialValue
  data_model		STATE_CHANGE_dataModel
  channel_colrow	STATE_CHANGE_channelColRow
  channel_dataset	STATE_CHANGE_channelDataSet
  detector_dataset	STATE_CHANGE_detectorDataSet
  detector_index	STATE_CHANGE_detectorIndex
  pin_colrow		STATE_CHANGE_pinColRow
  pin_dataset		STATE_CHANGE_pinDataSet
  state_index		STATE_CHANGE_stateIndex
  scalar_dataset	STATE_CHANGE_scalarDataSet
  time_dataset		STATE_CHANGE_timeDataSet
@return		reason
"""
    reason = STATE_CHANGE_noop

    if 'assembly_index' in kwargs and locks[ STATE_CHANGE_assemblyIndex ]:
      self.assemblyIndex = kwargs[ 'assembly_index' ]
      reason |= STATE_CHANGE_assemblyIndex

    if 'axial_value' in kwargs and locks[ STATE_CHANGE_axialValue ]:
      self.axialValue = kwargs[ 'axial_value' ]
      reason |= STATE_CHANGE_axialValue
#    if 'axial_level' in kwargs and locks[ STATE_CHANGE_axialLevel ]:
#      self.axialLevel = kwargs[ 'axial_level' ]
#      reason |= STATE_CHANGE_axialLevel

    if 'channel_colrow' in kwargs and locks[ STATE_CHANGE_channelColRow ]:
      self.channelColRow = kwargs[ 'channel_colrow' ]
      reason |= STATE_CHANGE_channelColRow

    if 'channel_dataset' in kwargs and locks[ STATE_CHANGE_channelDataSet ]:
      self.channelDataSet = kwargs[ 'channel_dataset' ]
      reason |= STATE_CHANGE_channelDataSet

    if 'data_model' in kwargs:
      self.dataModel = kwargs[ 'data_model' ]
      reason |= STATE_CHANGE_dataModel

    if 'detector_dataset' in kwargs and locks[ STATE_CHANGE_detectorDataSet ]:
      self.detectorDataSet = kwargs[ 'detector_dataset' ]
      reason |= STATE_CHANGE_detectorDataSet

    if 'detector_index' in kwargs and locks[ STATE_CHANGE_detectorIndex ]:
      self.detectorIndex = kwargs[ 'detector_index' ]
      reason |= STATE_CHANGE_detectorIndex

    if 'pin_colrow' in kwargs and locks[ STATE_CHANGE_pinColRow ]:
      self.pinColRow = kwargs[ 'pin_colrow' ]
      reason |= STATE_CHANGE_pinColRow

    if 'pin_dataset' in kwargs and locks[ STATE_CHANGE_pinDataSet ]:
      self.pinDataSet = kwargs[ 'pin_dataset' ]
      reason |= STATE_CHANGE_pinDataSet

    if 'scalar_dataset' in kwargs and locks[ STATE_CHANGE_scalarDataSet ]:
      self.scalarDataSet = kwargs[ 'scalar_dataset' ]
      reason |= STATE_CHANGE_scalarDataSet

    if 'state_index' in kwargs and locks[ STATE_CHANGE_stateIndex ]:
      self.stateIndex = kwargs[ 'state_index' ]
      reason |= STATE_CHANGE_stateIndex

    if 'time_dataset' in kwargs and locks[ STATE_CHANGE_timeDataSet ]:
      if self.timeDataSet != kwargs[ 'time_dataset' ]:
        self.timeDataSet = kwargs[ 'time_dataset' ]
        reason |= STATE_CHANGE_timeDataSet

#		-- Wire assembly_index and detector_index together
#		--
    if (reason & STATE_CHANGE_assemblyIndex) > 0:
      if (reason & STATE_CHANGE_detectorIndex) == 0 and \
          self.dataModel.core.detectorMap != None:
	col = self.assemblyIndex[ 1 ]
	row = self.assemblyIndex[ 2 ]
	det_ndx = self.dataModel.core.detectorMap[ row, col ] - 1
	reason |= STATE_CHANGE_detectorIndex
	self.detectorIndex = ( det_ndx, col, row )

    elif (reason & STATE_CHANGE_detectorIndex) > 0:
      if (reason & STATE_CHANGE_assemblyIndex) == 0:
          #self.dataModel.core.coreMap != None:
	col = self.detectorIndex[ 1 ]
	row = self.detectorIndex[ 2 ]
	assy_ndx = self.dataModel.core.coreMap[ row, col ] - 1
	reason |= STATE_CHANGE_assemblyIndex
	self.assemblyIndex = ( assy_ndx, col, row )
    #end if

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
    if (reason & STATE_CHANGE_assemblyIndex) > 0:
      update_args[ 'assembly_index' ] = self.assemblyIndex
#      if hasattr( self, 'assemblyIndex' ) and \
#          self.state.assemblyIndex != self.assemblyIndex:

    if (reason & STATE_CHANGE_axialValue) > 0:
      update_args[ 'axial_value' ] = self.axialValue

    if (reason & STATE_CHANGE_channelColRow) > 0:
      update_args[ 'channel_colrow' ] = self.channelColRow

    if (reason & STATE_CHANGE_channelDataSet) > 0:
      update_args[ 'channel_dataset' ] = self.channelDataSet

    if (reason & STATE_CHANGE_dataModel) > 0:
      update_args[ 'data_model' ] = self.dataModel

    if (reason & STATE_CHANGE_detectorDataSet) > 0:
      update_args[ 'detector_dataset' ] = self.detectorDataSet

    if (reason & STATE_CHANGE_detectorIndex) > 0:
      update_args[ 'detector_index' ] = self.detectorIndex

    if (reason & STATE_CHANGE_pinColRow) > 0:
      update_args[ 'pin_colrow' ] = self.pinColRow

    if (reason & STATE_CHANGE_pinDataSet) > 0:
      update_args[ 'pin_dataset' ] = self.pinDataSet

    if (reason & STATE_CHANGE_scalarDataSet) > 0:
      update_args[ 'scalar_dataset' ] = self.scalarDataSet

    if (reason & STATE_CHANGE_stateIndex) > 0:
      update_args[ 'state_index' ] = self.stateIndex

    if (reason & STATE_CHANGE_timeDataSet) > 0:
      update_args[ 'time_dataset' ] = self.timeDataSet

    return  update_args
  #end CreateUpdateArgs


  #----------------------------------------------------------------------
  #	METHOD:		Load()						-
  #----------------------------------------------------------------------
  def Load( self, data_model = None ):
    """
@param  data_model	if None, use the current dataModel
"""
    undefined_ax = ( 0.0, -1, -1 )
    undefined2 = ( -1, -1 )
    undefined3 = ( -1, -1, -1 )
    self.dataModel = data_model

    if data_model != None:
      self.assemblyIndex = data_model.NormalizeAssemblyIndex( undefined3 )
      self.axialValue = data_model.NormalizeAxialValue( undefined_ax )
      self.channelDataSet = data_model.GetFirstDataSet( 'channel' )
      self.detectorDataSet = data_model.GetFirstDataSet( 'detector' )
      self.detectorIndex = data_model.NormalizeDetectorIndex( undefined3 )
      self.pinColRow = data_model.NormalizePinColRow( undefined2 )
      self.pinDataSet = 'pin_powers' \
	  if 'pin_powers' in data_model.GetDataSetNames( 'pin' ) else \
	  data_model.GetFirstDataSet( 'pin' )
      self.scalarDataSet = data_model.GetFirstDataSet( 'scalar' )
      self.stateIndex = data_model.NormalizeStateIndex( -1 )
      self.timeDataSet = 'exposure' \
          if 'exposure' in data_model.GetDataSetNames( 'time' ) else \
	  'state'

    else:
      self.assemblyIndex = undefined3
      self.axialValue = undefined_ax
      self.channelDataSet = None
      self.detectorDataSet = None
      self.detectorIndex = undefined3
      self.pinColRow = undefined2
      self.pinDataSet = None
      self.scalarDataSet = None
      self.stateIndex = -1
      self.timeDataSet = 'state'
  #end Load


  #----------------------------------------------------------------------
  #	METHOD:		ResolveLocks()					-
  #----------------------------------------------------------------------
  def ResolveLocks( self, reason, locks ):
    """
@return		resolved reason
"""
    if reason == None:
      reason = STATE_CHANGE_noop

    else:
      for mask in LOCKABLE_STATES:
        if not locks[ mask ]:
	  reason &= ~mask
      #end for
    #end if-else

    return  reason
  #end ResolveLocks


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		CreateLocks()					-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateLocks():
    """
@return		dict with all True for
		STATE_CHANGE_assemblyIndex,
		STATE_CHANGE_axialValue,
		STATE_CHANGE_channelDataSet,
		STATE_CHANGE_detectorDataSet,
		STATE_CHANGE_detectorIndex,
		STATE_CHANGE_pinColRow,
		STATE_CHANGE_pinDataSet,
		STATE_CHANGE_scalarDataSet,
		STATE_CHANGE_stateIndex
		STATE_CHANGE_timeDataSet
"""
    locks = {}
    for mask in LOCKABLE_STATES:
      locks[ mask ] = True
    return  locks
  #end CreateLocks


  #----------------------------------------------------------------------
  #	METHOD:		GetDataModel()					-
  #----------------------------------------------------------------------
  @staticmethod
  def GetDataModel( state ):
    data_model = None
    if state != None and state.dataModel != None:
      data_model = state.dataModel

    return  data_model
  #end GetDataModel
#end State
