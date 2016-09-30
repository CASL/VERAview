#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		pin_averages_itest.py				-
#	HISTORY:							-
#		2016-09-30	leerw@ornl.gov				-
#		2016-02-15	leerw@ornl.gov				-
#------------------------------------------------------------------------
import argparse, h5py, os, sys, traceback
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.datamodel import *
from data.pin_averages import *


#------------------------------------------------------------------------
#	CLASS:		PinAveragesITest				-
#------------------------------------------------------------------------
class PinAveragesITest( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PinAveragesITest.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, data ):
    self.fAverages = \
        Averages( data.core, data.GetStateDataSet( 0, 'pin_powers' ).value )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		PinAveragesITest.CalcScalarAverage()		-
  #----------------------------------------------------------------------
  def CalcScalarAverage( self, ds_name ):
    pass
  #end CalcScalarAverage


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		PinAveragesITest.main()				-
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
	test = PinAveragesITest( data )
	print '[pinWeights]'
	print repr( test.fAverages.pinWeights )

	pin_powers = data.GetStateDataSet( 0, 'pin_powers' )

	print '[pows]'
	print repr( pin_powers.value )

	print '[ass_wgts]'
	print repr( test.fAverages.assemblyWeights )
	print '[ass_powers]'
	print repr( test.fAverages.calc_pin_assembly_avg( pin_powers ) )

	print '[axial_wgts]'
	print repr( test.fAverages.axialWeights )
	print '[axial_powers]'
	print repr( test.fAverages.calc_pin_axial_avg( pin_powers ) )

	print '[core_wgts]'
	print repr( test.fAverages.coreWeights )
	print '[core_powers]'
	print repr( test.fAverages.calc_pin_core_avg( pin_powers ) )

	print '[nodeWeights]'
	print repr( test.fAverages.nodeWeights )
	print '[node_powers]'
	print repr( test.fAverages.calc_pin_node_avg( pin_powers ) )

	print '[rad_ass_wgts]'
	print repr( test.fAverages.radialAssemblyWeights )
	print '[rad_ass_powers]'
	print repr( test.fAverages.calc_pin_radial_assembly_avg( pin_powers ) )

	print '[rad_wgts]'
	print repr( test.fAverages.radialWeights )
	print '[rad_powers]'
	print repr( test.fAverages.calc_pin_radial_avg( pin_powers ) )
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

#end PinAveragesITest


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  PinAveragesITest.main()
