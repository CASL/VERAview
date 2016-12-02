#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr_itest.py				-
#	HISTORY:							-
#		2016-11-30	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, logging.config, os, re, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.datamodel import *
from data.datamodel_mgr import *


PATTERN_ws = re.compile( '[\s,]+' )


#------------------------------------------------------------------------
#	CLASS:		DataModelMgrITest				-
#------------------------------------------------------------------------
class DataModelMgrITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, *fnames ):
    self.fMgr = DataModelMgr()
    self.fMgr.AddListener( 'modelAdded', self.OnModelAdded )
    self.fMgr.AddListener( 'modelRemoved', self.OnModelRemoved )

    if fnames:
      for fname in fnames:
        print '[DataModelMgrITest] adding file "%s"' % fname
        self.fMgr.OpenModel( fname )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.CheckMeshIndexes()		-
  #----------------------------------------------------------------------
  def CheckMeshIndexes( self, *mesh_values ):
    if mesh_values:
      print '\n[DataModelMgrITest] mesh value indexes:'
      for mesh_value in mesh_values:
	print '[mesh=%f]' % mesh_value
        for name in self.fMgr.GetDataModelNames():
	  axial_value = \
	      self.fMgr.GetDataModel( name ).CreateAxialValue( cm = mesh_value )
          print '  %s=%s' % ( name, str( axial_value ) )

	axial_value = self.fMgr.GetAxialValue( cm = mesh_value )
        print '  ALL=%s' % str( axial_value )
      #end for mesh_value
    #end if mesh_values
  #end CheckMeshIndexes


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.CheckMeshValues()		-
  #----------------------------------------------------------------------
  def CheckMeshValues( self, *mesh_ndxs ):
    if mesh_ndxs:
      print '\n[DataModelMgrITest] mesh index values:'
      for ndx in mesh_ndxs:
	print '[core_ndx=%d]' % ndx
	axial_value = self.fMgr.GetAxialValue( core_ndx = ndx )
        print '  ALL=%s' % str( axial_value )

	axial_cm = axial_value[ 0 ]
        for name in self.fMgr.GetDataModelNames():
	  dm = self.fMgr.GetDataModel( name )
	  axial_value = dm.CreateAxialValue( cm = axial_cm )
          print '  %s=%s (%f)' % (
	      name, str( axial_value ),
	      dm.GetCore().GetAxialMeshCenters()[ axial_value[ 1 ] ]
	      )
      #end for mesh_value
    #end if mesh_ndxs
  #end CheckMeshValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.CheckTimeIndexes()		-
  #----------------------------------------------------------------------
  def CheckTimeIndexes( self, *time_values ):
    if time_values:
      print '\n[DataModelMgrITest] time value indexes:'
      for time_value in time_values:
	print '[time=%f]' % time_value
        for name in self.fMgr.GetDataModelNames():
	  ndx = self.fMgr.GetTimeValueIndex( time_value, name )
          print '  %s=%d (%f)' % \
	      ( name, ndx, self.fMgr.GetTimeValues( name )[ ndx ] )
	ndx = self.fMgr.GetTimeValueIndex( time_value )
        print '  ALL=%d (%f)' % \
	    ( ndx, self.fMgr.GetTimeValues()[ ndx ] )
      #end for time_value
    #end if time_values
  #end CheckTimeIndexes


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.CheckTimeIndexes_stdin()	-
  #----------------------------------------------------------------------
  def CheckTimeIndexes_stdin( self ):
    print '[DataModelMgrITest] enter time values:'

    time_value = 0.0
    while time_value >= 0.0:
      sys.stdout.write( '> ' )
      sys.stdout.flush()
      line = sys.stdin.readline()
      if line:
        line = line.lstrip( '\t ,' ).rstrip( '\r\n' )
      try:
        time_value = float( line )
      except:
        time_value = -1.0

      if time_value >= 0.0:
        for name in self.fMgr.GetDataModelNames():
	  ndx = self.fMgr.GetTimeValueIndex( time_value, name )
          print '  %s=%d (%f)' % \
	      ( name, ndx, self.fMgr.GetTimeValues( name )[ ndx ] )
	ndx = self.fMgr.GetTimeValueIndex( time_value )
        print '  ALL=%d (%f)' % \
	    ( ndx, self.fMgr.GetTimeValues()[ ndx ] )
      #end if
    #end while
  #end CheckTimeIndexes_stdin


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.ChooseTimeDataSet()		-
  #----------------------------------------------------------------------
  def ChooseTimeDataSet( self, choice ):
    time_ds_names = self.fMgr.ResolveAvailableTimeDataSets()
    msg = '[DataModelMgrITest] choose time dataset %s:> ' % str( time_ds_names )
    sys.stdout.write( msg )
    sys.stdout.flush()
    choice = sys.stdin.readline()
    if choice:
      choice = choice.lstrip( '\t ,' ).rstrip( '\t\r\n ' )
      if choice not in time_ds_names:
        choice = 'state'
    
    self.fMgr.SetTimeDataSet( choice if choice else 'state' )
  #end ChooseTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.OnModelAdded()		-
  #----------------------------------------------------------------------
  def OnModelAdded( self, model_name ):
    print '[DataModelMgrITest] added model "%s"' % model_name
  #end OnModelAdded


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.OnModelRemoved()		-
  #----------------------------------------------------------------------
  def OnModelRemoved( self, model_name ):
    print '[DataModelMgrITest] removed model "%s"' % model_name
  #end OnModelRemoved


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.PrintSummary()		-
  #----------------------------------------------------------------------
  def PrintSummary( self ):
#    print '\n[DataModelMgrITest] data models:'
#    for name, dm in self.fMgr.GetDataModels().iteritems():
#      print '%s=%s' % ( name, dm.GetName() )

    print '\n[DataModelMgrITest]'
    print 'models=%s' % str( self.fMgr.GetDataModelNames() )
    print 'available time datasets=%s' % \
        str( self.fMgr.ResolveAvailableTimeDataSets() )

    print 'maxAxialValue=%f\ntimeDataSet=%s' % \
        ( self.fMgr.GetMaxAxialValue(), self.fMgr.GetTimeDataSet() )

    print '\n[DataModelMgrITest] axialMeshCenters:'
    for name in self.fMgr.GetDataModelNames():
      dm = self.fMgr.GetDataModel( name )
      values = dm.GetCore().GetAxialMeshCenters() if dm.GetCore() else None
      print '%s=\n%s' % ( name, str( values ) )
    print 'ALL=\n%s' % str( self.fMgr.GetAxialMeshCenters() )

    print '\n[DataModelMgrITest] detectorMesh:'
    for name in self.fMgr.GetDataModelNames():
      dm = self.fMgr.GetDataModel( name )
      values = dm.GetCore().GetDetectorMesh() if dm.GetCore() else None
      print '%s=\n%s' % ( name, str( values ) )
    print 'ALL=\n%s' % str( self.fMgr.GetDetectorMesh() )

    print '\n[DataModelMgrITest] fixedDetectorMeshCenters:'
    for name in self.fMgr.GetDataModelNames():
      dm = self.fMgr.GetDataModel( name )
      values = dm.GetCore().GetFixedDetectorMeshCenters() if dm.GetCore() else None
      print '%s=\n%s' % ( name, str( values ) )
    print 'ALL=\n%s' % str( self.fMgr.GetFixedDetectorMeshCenters() )

    print '\n[DataModelMgrITest] time values:'
    for name in self.fMgr.GetDataModelNames():
      print '%s=%s' % ( name, str( self.fMgr.GetTimeValues( name ) ) )
    print 'ALL=%s' % str( self.fMgr.GetTimeValues() )
  #end PrintSummary


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgrITest.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      log_file = os.path.\
          join( os.path.dirname( __file__ ), '..', 'res', 'logging.conf' )
      logging.config.fileConfig( log_file )

      #parser = argparse.ArgumentParser( description = '', epilog = EPILOG )
      parser = argparse.ArgumentParser()
#      parser.add_argument(
#	  '-d', '--dataset',
#	  default = None, nargs = '+',
#	  help = 'dataset-name derived-label ...'
#          )
      parser.add_argument(
	  'files',
	  default = None,
	  help = 'input HDF5 file',
	  nargs = '+'
          )
      parser.add_argument(
	  '--mesh-indexes',
	  default = [],
	  help = 'mesh core indexes for testing',
	  nargs = '*', type = int
          )
      parser.add_argument(
	  '--mesh-values',
	  default = [],
	  help = 'mesh values for testing',
	  nargs = '*', type = float
          )
      parser.add_argument(
	  '-t', '--time-dataset',
	  default = 'state',
	  help = 'time dataset name'
          )
      parser.add_argument(
	  '--time-values',
	  default = [],
	  help = 'time dataset values for testing',
	  nargs = '*', type = float
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      test = DataModelMgrITest( *args.files )
      #test.ChooseTimeDataSet()
      test.fMgr.SetTimeDataSet( args.time_dataset )
      test.PrintSummary()

      test.CheckTimeIndexes( *args.time_values )
      test.CheckMeshIndexes( *args.mesh_values )
      test.CheckMeshValues( *args.mesh_indexes )

    except Exception, ex:
      print >> sys.stderr, str( ex )
      et, ev, tb = sys.exc_info()
      while tb:
	print >> sys.stderr, \
            'File=' + str( tb.tb_frame.f_code ) + \
            ', Line=' + str( traceback.tb_lineno( tb ) )
        tb = tb.tb_next
      #end while
  #end main

#end DataModelMgrITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataModelMgrITest.main()
