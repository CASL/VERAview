#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		test_averager.py				-
#	HISTORY:							-
#		2015-10-26	leerw@ornl.gov				-
#	  Testing CreateCorePinFactors().
#		2015-10-03	leerw@ornl.gov				-
#------------------------------------------------------------------------
import gzip, h5py, os, sys, traceback, unittest
#import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), os.pardir ) )

from data.averager import *
from data.datamodel import *


#------------------------------------------------------------------------
#	CLASS:		FakeCore					-
#------------------------------------------------------------------------
class FakeCore( Core ):
  def __init__( self, nass, nax, npin, core_sym = 4 ):
    self.coreSym = core_sym
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
    fpath = os.path.join( 'data', fname )
    if fname.endswith( '.gz' ):
      fp = gzip.GzipFile( fpath, 'rb' )
    else:
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
  #	METHOD:		TestAverager.test_Calc1DAxialAverage1()		-
  #----------------------------------------------------------------------
  def test_Calc1DAxialAverage1( self ):
    data = self._readArray( 'one.data' )
    results = self._readArray( 'one.1daxial.1.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc1DAxialAverage( core, data )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc1DAxialAverage_( core, data )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc1DAxialAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc1DAxialAverage2()		-
  #----------------------------------------------------------------------
  def test_Calc1DAxialAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    results = self._readArray( 'one.1daxial.2.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc1DAxialAverage( core, data, factors )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc1DAxialAverage_( core, data, factors )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc1DAxialAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_Calc1DAxialAverage3()		-
  #----------------------------------------------------------------------
  def test_Calc1DAxialAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    results = self._readArray( 'one.1daxial.3.out' )
    core = FakeCore( 2, 2, 2 )
    obj = Averager()

    avg = obj.Calc1DAxialAverage( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)

    avg2 = obj.Calc1DAxialAverage_( core, data, factors, weights )
    self.assertTrue(
        np.allclose( avg, avg2, rtol = 0.0, atol = 1.0e-6 ),
	'calc methods comparison'
	)
  #end test_Calc1DAxialAverage3


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
  #	METHOD:		TestAverager.test_CalcGeneralAverage1()		-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage1( self ):
    data = self._readArray( 'one.data' )
    obj = Averager()

    avg = obj.CalcGeneralAverage( data, ( 1, 1, 2, 2 ) )
    results = self._readArray( 'one.3dassy.1.out' )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)
  #end test_CalcGeneralAverage1


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage2()		-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage2( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    results = self._readArray( 'one.3dassy.2.out' )
    obj = Averager()

    avg = obj.CalcGeneralAverage( data, ( 1, 1, 2, 2 ), factors )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)
  #end test_CalcGeneralAverage2


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage3()		-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage3( self ):
    data = self._readArray( 'one.data' )
    factors = self._readArray( 'one.factors' )
    weights = self._readArray( 'one.weights' )
    results = self._readArray( 'one.3dassy.3.out' )
    obj = Averager()

    avg = obj.CalcGeneralAverage( data, ( 1, 1, 2, 2 ), factors, weights )
    self.assertTrue(
        np.allclose( avg, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline'
	)
  #end test_CalcGeneralAverage3


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage1DAxial()	-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage1DAxial( self ):
    obj = Averager()
    data = DataModel( os.path.join( 'data', 'pinpowers1.h5' ) )
    powers = data.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
    factors = obj.CreateCorePinFactors( data.core )
    volumes = data.core.pinVolumes

    cur_shape = ( 1, 1, powers.shape[ 2 ], 1 )
    averages = obj.CalcGeneralAverage( powers, cur_shape )
    comp = np.array( averages[ 0, 0, :, 0 ] )
    results = self._readArray( 'pinpowers1.1daxial.1.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline no factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors )
    comp = np.array( averages[ 0, 0, :, 0 ] )
    results = self._readArray( 'pinpowers1.1daxial.2.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors, volumes )
    comp = np.array( averages[ 0, 0, :, 0 ] )
    results = self._readArray( 'pinpowers1.1daxial.3.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors with weights'
	)
  #end test_CalcGeneralAverage1DAxial


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage2DAssy()	-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage2DAssy( self ):
    obj = Averager()
    data = DataModel( os.path.join( 'data', 'pinpowers1.h5' ) )
    powers = data.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
    factors = obj.CreateCorePinFactors( data.core )
    volumes = data.core.pinVolumes

    cur_shape = ( 1, 1, 1, powers.shape[ 3 ] )
    averages = obj.CalcGeneralAverage( powers, cur_shape )
    comp = np.array( averages[ 0, 0, 0, : ] )
    results = self._readArray( 'pinpowers1.2dassy.1.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline no factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors )
    comp = np.array( averages[ 0, 0, 0, : ] )
    results = self._readArray( 'pinpowers1.2dassy.2.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors, volumes )
    results = self._readArray( 'pinpowers1.2dassy.3.out' )
    comp = np.array( averages[ 0, 0, 0, : ] )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors with weights'
	)
  #end test_CalcGeneralAverage2DAssy


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage2DPin()	-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage2DPin( self ):
    obj = Averager()
    data = DataModel( os.path.join( 'data', 'pinpowers1.h5' ) )
    powers = data.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
    factors = obj.CreateCorePinFactors( data.core )
    volumes = data.core.pinVolumes

    cur_shape = ( powers.shape[ 0 ], powers.shape[ 1 ], 1, powers.shape[ 3 ] )
    averages = obj.CalcGeneralAverage( powers, cur_shape )
    comp = np.array( averages[ :, :, 0, : ] )
    results = self._readArray( 'pinpowers1.2dpin.1.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline no factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors )
    comp = np.array( averages[ :, :, 0, : ] )
    results = self._readArray( 'pinpowers1.2dpin.2.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors, volumes )
    comp = np.array( averages[ :, :, 0, : ] )
    results = self._readArray( 'pinpowers1.2dpin.3.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors with weights'
	)
  #end test_CalcGeneralAverage2DPin


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverage3DAssy()	-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverage3DAssy( self ):
    obj = Averager()
    data = DataModel( os.path.join( 'data', 'pinpowers1.h5' ) )
    powers = data.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
    factors = obj.CreateCorePinFactors( data.core )
    volumes = data.core.pinVolumes

    cur_shape = ( 1, 1, powers.shape[ 2 ], powers.shape[ 3 ] )
    averages = obj.CalcGeneralAverage( powers, cur_shape )
    comp = np.array( averages[ 0, 0, :, : ] )
    results = self._readArray( 'pinpowers1.3dassy.1.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline no factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors )
    comp = np.array( averages[ 0, 0, :, : ] )
    results = self._readArray( 'pinpowers1.3dassy.2.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors, volumes )
    comp = np.array( averages[ 0, 0, :, : ] )
    results = self._readArray( 'pinpowers1.3dassy.3.out' )
    self.assertTrue(
        np.allclose( comp, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors with weights'
	)
  #end test_CalcGeneralAverage3DAssy


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CalcGeneralAverageScalar()	-
  #----------------------------------------------------------------------
  def test_CalcGeneralAverageScalar( self ):
    obj = Averager()
    data = DataModel( os.path.join( 'data', 'pinpowers1.h5' ) )
    powers = data.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
    factors = obj.CreateCorePinFactors( data.core )
    volumes = data.core.pinVolumes

    cur_shape = ( 1, 1, 1, 1 )
    averages = obj.CalcGeneralAverage( powers, cur_shape )
    results = self._readArray( 'pinpowers1.scalar.1.out' )
    self.assertTrue(
        np.allclose( averages, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline no factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors )
    results = self._readArray( 'pinpowers1.scalar.2.out' )
    self.assertTrue(
        np.allclose( averages, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors no weights'
	)

    averages = obj.CalcGeneralAverage( powers, cur_shape, factors, volumes )
    results = self._readArray( 'pinpowers1.scalar.3.out' )
    self.assertTrue(
        np.allclose( averages, results, rtol = 0.0, atol = 1.0e-6 ),
	'calc vs baseline with factors with weights'
	)
  #end test_CalcGeneralAverageScalar


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


  #----------------------------------------------------------------------
  #	METHOD:		TestAverager.test_CreateCorePinFactors1()	-
  #----------------------------------------------------------------------
  def _test_CreateCorePinFactors1( self ):
    obj = Averager()

    results = self._readArray( 'pinfactors1.out.gz' )
    data = DataModel( os.path.join( 'data', 'pinfactors1.h5' ) )
    try:
      factors = obj.CreateCorePinFactors( data.core )
      self.assertTrue(
          np.allclose( factors, results, rtol = 0.0, atol = 1.0e-6 ),
	  'quarter-core pin factors'
	  )
    finally:
      data.Close()
  #end test_CreateCorePinFactors1


#		-- Static Methods
#		--

#end TestAverager


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()

  #suite = unittest.TestSuite()
  #suite.addTest( TestAverager( 'test_CalcGeneralAverage1' ) )

#  tests = [
#      'test_CalcGeneralAverage1DAxial',
#      'test_CalcGeneralAverage2DAssy',
#      'test_CalcGeneralAverage2DPin',
#      'test_CalcGeneralAverage3DAssy',
#      'test_CalcGeneralAverageScalar'
#      ]
#  suite = unittest.TestSuite( map( TestAverager, tests ) )

  suite = unittest.TestLoader().loadTestsFromTestCase( TestAverager )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
