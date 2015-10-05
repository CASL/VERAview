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
    self.npinx = npin
    self.npiny = npin
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
  #	METHOD:		TestAverager.test_Calc2DAssyAverage1()		-
  #----------------------------------------------------------------------
  def test_Calc2DAssyAverage1( self ):
    data = self._readArray( 'one.data' )
    results = self._readArray( 'one.2dassy.1.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DAssyAverage( core, data )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DAssyAverage_( core, data )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DAssyAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc2DAssyAverage2()		-
  #----------------------------------------------------------------------
  def test_Calc2DAssyAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    results = self._readArray( 'one.2dassy.2.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DAssyAverage( core, data, factors )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DAssyAverage_( core, data, factors )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DAssyAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc2DAssyAverage3()		-
  #----------------------------------------------------------------------
  def test_Calc2DAssyAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    results = self._readArray( 'one.2dassy.3.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DAssyAverage( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DAssyAverage_( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DAssyAverage3


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc2DPinAverage1()		-
  #----------------------------------------------------------------------
  def test_Calc2DPinAverage1( self ):
    data = self._readArray( 'one.data' )
    results = self._readArray( 'one.2dpin.1.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DPinAverage( core, data )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DPinAverage_( core, data )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DPinAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc2DPinAverage2()		-
  #----------------------------------------------------------------------
  def test_Calc2DPinAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    results = self._readArray( 'one.2dpin.2.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DPinAverage( core, data, factors )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DPinAverage_( core, data, factors )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DPinAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc2DPinAverage3()		-
  #----------------------------------------------------------------------
  def test_Calc2DPinAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    results = self._readArray( 'one.2dpin.3.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc2DPinAverage( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc2DPinAverage_( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc2DPinAverage3


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc3DAssyAverage1()		-
  #----------------------------------------------------------------------
  def test_Calc3DAssyAverage1( self ):
    data = self._readArray( 'one.data' )
    results = self._readArray( 'one.3dassy.1.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc3DAssyAverage( core, data )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc3DAssyAverage_( core, data )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc3DAssyAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc3DAssyAverage2()		-
  #----------------------------------------------------------------------
  def test_Calc3DAssyAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    results = self._readArray( 'one.3dassy.2.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc3DAssyAverage( core, data, factors )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc3DAssyAverage_( core, data, factors )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc3DAssyAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc3DAssyAverage3()		-
  #----------------------------------------------------------------------
  def test_Calc3DAssyAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    results = self._readArray( 'one.3dassy.3.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc3DAssyAverage( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc3DAssyAverage_( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc3DAssyAverage3


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcScalarAverage1()		-
  #----------------------------------------------------------------------
  def test_CalcScalarAverage1( self ):
    data = self._readArray( 'one.data' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.CalcScalarAverage( core, data )
    #0.555499999999
    self.assertEqual( avg, 0.5555, 'calc vs baseline' )
    self.assertEqual(
        avg, obj.CalcScalarAverage_( core, data ),
	'calc methods comparison'
	)
  #end test_CalcScalarAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcScalarAverage2()		-
  #----------------------------------------------------------------------
  def test_CalcScalarAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.CalcScalarAverage( core, data, factors )
    #1.0100909090909092
    self.assertAlmostEqual(
        avg, 1.010090909,
	msg = 'calc vs baseline', places = 9
	)
    self.assertEqual(
        avg,
	obj.CalcScalarAverage_( core, data, factors ),
	'calc methods comparison'
	)
  #end test_CalcScalarAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcScalarAverage3()		-
  #----------------------------------------------------------------------
  def test_CalcScalarAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.CalcScalarAverage( core, data, factors, weights )
    #1.0555049950499504
    self.assertAlmostEqual(
        avg, 1.055504995,
	msg = 'calc vs baseline', places = 9
	)
    self.assertAlmostEqual(
        avg,
	obj.CalcScalarAverage_( core, data, factors, weights ),
	msg = 'calc methods comparison', places = 9
	)
  #end test_CalcScalarAverage3


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
