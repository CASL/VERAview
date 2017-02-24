#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		differences_itest.py				-
#	HISTORY:							-
#		2017-02-24	leerw@ornl.gov				-
#		2017-01-14	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, logging, logging.config, os, re, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.datamodel import *
from data.datamodel_mgr import *
from data.differences import *


PATTERN_ws = re.compile( '[\s,]+' )


#------------------------------------------------------------------------
#	CLASS:		DifferencesITest				-
#------------------------------------------------------------------------
class DifferencesITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DifferencesITest.__del__()			-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.fMgr.Close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DifferencesITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self ):
    self.fMgr = DataModelMgr()
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DifferencesITest.Run()				-
  #----------------------------------------------------------------------
  def Run(
      self,
      ref_fname, ref_ds_name,
      comp_fname, comp_ds_name,
      time_ds_name, result_name
      ):
    ref_dm = self.fMgr.OpenModel( ref_fname )
    comp_dm = self.fMgr.OpenModel( comp_fname )

    time_names = self.fMgr.ResolveAvailableTimeDataSets()
    if time_ds_name not in time_names:
      time_ds_name = time_names[ -1 ]
    self.fMgr.SetTimeDataSet( time_ds_name )

    try:
      ref_qds_name = DataSetName( ref_dm.GetName(), ref_ds_name )
      comp_qds_name = DataSetName( comp_dm.GetName(), comp_ds_name )

      result_qds_name = Differences( self.fMgr )\
          ( ref_qds_name, comp_qds_name, result_name )

      time_values = self.fMgr.GetTimeValues( ref_qds_name )
      for i in xrange( len( time_values ) ):
        dset = self.fMgr.GetH5DataSet( result_qds_name, time_values[ i ] )
	dset_array = np.array( dset )
	print '\n[%.6g]\n%s' % ( time_values[ i ], str( dset_array ) )
      #end for i

      print '\n[MetaData]'
      print 'name=', str( result_qds_name )
      print 'type=', comp_dm.GetDataSetType( result_qds_name.displayName )
      print 'def=', \
          str( comp_dm.GetDataSetDefByDsName( result_qds_name.displayName ) )

    finally:
      self.fMgr.CloseModel( ref_dm.GetName() )
      self.fMgr.CloseModel( comp_dm.GetName() )
  #end Run


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DifferencesITest.main()				-
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
#      parser.add_argument(
#	  'files',
#	  default = None,
#	  help = 'input HDF5 file',
#	  nargs = '+'
#          )
      parser.add_argument(
	  '--comp',
	  default = None,
	  dest = 'comp_pair',
	  help = 'file dataset',
	  nargs = 2
          )
      parser.add_argument(
	  '--ref',
	  default = None,
	  dest = 'ref_pair',
	  help = 'file dataset',
	  nargs = 2
          )
      parser.add_argument(
	  '-r', '--result-name',
	  default = 'diff_data',
	  help = 'name of difference dataset'
          )
      parser.add_argument(
	  '-t', '--time-name',
	  default = 'exposure',
	  help = 'name of time dataset'
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      if args.ref_pair is None or args.comp_pair is None:
        parser.print_help()
      else:
        test = DifferencesITest()
	test.Run(
	    args.ref_pair[ 0 ], args.ref_pair[ 1 ],
	    args.comp_pair[ 0 ], args.comp_pair[ 1 ],
	    args.time_name, args.result_name
	    )

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

#end DifferencesITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DifferencesITest.main()
