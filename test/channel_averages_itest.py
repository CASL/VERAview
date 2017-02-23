#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		channel_averages_itest.py			-
#	HISTORY:							-
#		2017-02-23	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.datamodel import *
from data.channel_averages import *


#------------------------------------------------------------------------
#	CLASS:		ChannelAveragesITest				-
#------------------------------------------------------------------------
class ChannelAveragesITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAveragesITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, data ):
    self.fAverages = Averages( data.core )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAveragesITest.CalcScalarAverage()	-
  #----------------------------------------------------------------------
  def CalcScalarAverage( self, ds_name ):
    pass
  #end CalcScalarAverage


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ChannelAveragesITest.main()			-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      #parser = argparse.ArgumentParser( description = '', epilog = EPILOG )
      parser = argparse.ArgumentParser()
#      parser.add_argument(
#	  '-d', '--dataset',
#	  default = None, nargs = '+',
#	  help = 'dataset-name derived-label ...'
#          )
      parser.add_argument(
	  '-f', '--file',
	  default = None,
	  help = 'input HDF5 file'
          )
      args = parser.parse_args()

#		-- Check required arguments
#		--
      #if args.dataset is None or args.file is None:
      if args.file is None:
	parser.print_help()

      else:
#			-- Must have valid data
#			--
        data = DataModel( args.file )
	test = ChannelAveragesITest( data )

	vapor_void = data.GetStateDataSet( 0, 'vapor_void' )
	vapor_void_array = np.array( vapor_void )

	print '[vapor_void]'
	print repr( vapor_void_array )

	print '[chan_assembly_avg]'
	print repr( test.fAverages.calc_channel_assembly_avg( vapor_void ) )

	print '[chan_axial_avg]'
	print repr( test.fAverages.calc_channel_axial_avg( vapor_void ) )

	print '[chan_core_avg]'
	print repr( test.fAverages.calc_channel_core_avg( vapor_void ) )

	print '[chan_radial_assembly_avg]'
	print repr( test.fAverages.calc_channel_radial_assembly_avg( vapor_void ) )

	print '[chan_radial_avg]'
	print repr( test.fAverages.calc_channel_radial_avg( vapor_void ) )
      #end required arguments specified

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

#end ChannelAveragesITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  ChannelAveragesITest.main()
