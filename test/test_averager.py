#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		test_averager.py				-
#	HISTORY:							-
#		2015-10-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import h5py, os, sys, traceback, unittest
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )

from data.averager import *
from data.datamodel import *


#------------------------------------------------------------------------
#	CLASS:		FakeCore					-
#------------------------------------------------------------------------
class FakeCore( object ):
  def __init__( self, nass, nax, npin ):
    self.nass = nass
    self.nax = nax
    self.npin = npin
  #end __init__
#end  FakeCore


#------------------------------------------------------------------------
#	CLASS:		TestAverager					-
#------------------------------------------------------------------------
class TestAverager( unittest.TestCase ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager._readArray()			-
  #----------------------------------------------------------------------
  def _readArray( self, fname ):
    fp = file( os.path.join( 'data', fname ) )
    try:
      content = fp.read( -1 )
    finally:
      fp.close()

    return  np.array( list( eval( content ) ), np.float64 )
  #end _readArray


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.setUp()				-
  #----------------------------------------------------------------------
#  def setUp( self ):
#  #end setUp


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.tearDown()				-
  #----------------------------------------------------------------------
#  def tearDown( self ):
#  #end tearDown


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcScalarAverage1()		-
  #----------------------------------------------------------------------
  def test_CalcScalarAverage1( self ):
    data = self._readArray( 'one.data' )
    core = FakeCore( 2, 2, 2 )
    avg = Averager().CalcScalarAverage( core, data )
    self.assertEqual( avg, 0.5555 )
  #end test_CalcScalarAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcScalarAverage2()		-
  #----------------------------------------------------------------------
  def test_CalcScalarAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    core = FakeCore( 2, 2, 2 )
    avg = Averager().CalcScalarAverage( core, data, factors )
    self.assertAlmostEqual( avg, 1.010090909, places = 9 )
  #end test_CalcScalarAverage2


#		-- Static Methods
#		--

#end TestAverager


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()
  suite = unittest.TestLoader().loadTestsFromTestCase( TestAverager )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
