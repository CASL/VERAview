#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
#		2016-08-19	leerw@ornl.gov				-
#		2016-08-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, copy, cStringIO, h5py, json, math, os, sys, \
    tempfile, threading, traceback, uuid
import numpy as np
import pdb

from data.datamodel import *
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
    self.dataModelIds = []
    self.dataModels = {}
    self.dataSetNamesVersion = 0
    self.maxAxialValue = 0.0
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    #for id, dm in self.dataModels.iteritems():
    for dm in self.dataModels.values():
      self.dataModelIds.remove( name )
      dm.Close()
  #end Close


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CloseModel()			-
  #----------------------------------------------------------------------
  def CloseModel( self, param ):
    """Opens the HDF5 file or filename.
@param  param		either a DataModel instance or an ID string
@return			True if removed, False if not found
"""
    result = False
    if isinstance( param, DataModel ):
      id = param.GetId()
    else:
      id = str( param )

    if id in self.dataModels:
      dm = self.dataModels[ id ]
      dm.RemoveListeners( self )
      dm.Close()

      del self.dataModels[ id ]
      self.dataModelIds.remove( id )

      self._UpdateMaxAxialValue()
      self.dataSetNamesVersion += 1

      result = True

    return  result
  #end CloseModel


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
  #	METHOD:		DataModelMgr.GetDataModels()			-
  #----------------------------------------------------------------------
  def GetDataModels( self ):
    """Accessor for the 'dataModels' property.
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
  #	METHOD:		DataModelMgr.GetMaxAxialValue()			-
  #----------------------------------------------------------------------
  def GetMaxAxialValue( self ):
    """Accessor for the 'maxAxialValue' property.
@return			maximum axial value in cm
"""
    return  self.maxAxialValue
  #end GetMaxAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetModelCount()			-
  #----------------------------------------------------------------------
  def GetModelCount( self ):
    return  len( self.dataModels )
  #end GetModelCount


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasData()				-
  #----------------------------------------------------------------------
  def HasData( self ):
    return  len( self.dataModels ) > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.OnDataSetsChanged()		-
  #----------------------------------------------------------------------
  def OnDataSetsChanged( self, model ):
    """Callback for model dataset changes.
"""
    self.dataSetNamesVersion += 1
  #end OnDataSetsChanged


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.OpenModel()			-
  #----------------------------------------------------------------------
  def OpenModel( self, h5f_param ):
    """Opens the HDF5 file or filename.
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
@return			new DataModel object or None if not opened
"""
    try:
#		-- Open
      id = str( uuid.uuid4() )
      dm = DataModel( h5f_param, id )

#		-- Assert on data
      if not dm.HasData():
        raise  Exception( 'Required VERA data not found' )

      dm.AddListeners( self )
      self.dataModels[ id ] = dm
      self._UpdateMaxAxialValue()
      self.dataSetNamesVersion += 1

      return  dm

    except Exception, ex:
      raise  IOError( 'Error reading "%s": %s' % ( h5f_param, ex.message ) )
  #end OpenModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateMaxAxialValue()		-
  #----------------------------------------------------------------------
  def _UpdateMaxAxialValue( self ):
    """Calculates the maximum axial value across all models and sets the
'maxAxialValue' property
@return			new maximum axial value in cm
"""
    result = -1.0
    for dm in self.dataModels.values():
      core = dm.GetCore()
      if core.axialMeshCenters is not None:
        result = max( result, core.axialMeshCenters[ -1 ] )
      if core.detectorMesh is not None:
        result = max( result, core.detectorMesh[ -1 ] )
      if core.fixedDetectorMeshCenters is not None:
        result = max( result, core.fixedDetectorMeshCenters[ -1 ] )
    #end for
    self.maxAxialValue = result
    return  result
  #end _UpdateMaxAxialValue


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
if __name__ == '__main__':
  DataModelMgr.main()
