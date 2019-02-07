#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		test_datamodel.py				-
#	HISTORY:							-
#		2016-08-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import os, sys, traceback, unittest
import pdb  # set_trace()

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), os.pardir ) )

from data.datamodel import *


#------------------------------------------------------------------------
#	CLASS:		TestDataModel					-
#------------------------------------------------------------------------
class TestDataModel( unittest.TestCase ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		TestDataModel.setUp()				-
  #----------------------------------------------------------------------
  def setUp( self ):
    path = \
        os.path.join( os.environ[ 'HOME' ], 'study', 'casl', 'andrew', 'c1.h5' )
    self.dataModel = DataModel( path )
  #end setUp


  #----------------------------------------------------------------------
  #	METHOD:		TestDataModel.tearDown()			-
  #----------------------------------------------------------------------
  def tearDown( self ):
    self.dataModel.Close()
  #end tearDown


  #----------------------------------------------------------------------
  #	METHOD:		TestDataModel.test_FindListIndex()		-
  #----------------------------------------------------------------------
  def test_FindListIndex( self ):
    core = self.dataModel.GetCore()

    asc1 = core.axialMeshCenters
    asc2 = core.detectorMesh

    des1 = asc1[ :: -1 ]
    des2 = asc2[ :: -1 ]

    max_value = max( asc1[ -1 ], asc2[ -1 ] ) + 10.0

    x = -5.0
    while x <= max_value:
      a0 = self.dataModel.FindListIndex( asc1, x )
      a1 = self.dataModel.FindListIndex1( asc1, x )
      self.assertEqual( a0, a1, 'ascending list one: %f' % x )

      b0 = self.dataModel.FindListIndex( asc2, x )
      b1 = self.dataModel.FindListIndex1( asc2, x )
      self.assertEqual( b0, b1, 'ascending list two: %f' % x )

      c0 = self.dataModel.FindListIndex( des1, x )
      c1 = self.dataModel.FindListIndex1( des1, x )
      self.assertEqual( c0, c1, 'descending list one: %f' % x )

      d0 = self.dataModel.FindListIndex( des2, x )
      d1 = self.dataModel.FindListIndex1( des2, x )
      self.assertEqual( d0, d1, 'descending list two: %f' % x )

      x += 0.1
    #end while
  #end test_FindListIndex


#		-- Static Methods
#		--

#end TestDataModel


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  #unittest.main()

  #suite = unittest.TestSuite()
  #suite.addTest( TestDataModel( 'test_CalcGeneralAverage1' ) )

#  tests = [
#      'test_CalcGeneralAverage1DAxial',
#      'test_CalcGeneralAverage2DAssy',
#      'test_CalcGeneralAverage2DPin',
#      'test_CalcGeneralAverage3DAssy',
#      'test_CalcGeneralAverageScalar'
#      ]
#  suite = unittest.TestSuite( map( TestAverager, tests ) )

  suite = unittest.TestLoader().loadTestsFromTestCase( TestDataModel )
  unittest.TextTestRunner( verbosity = 2 ).run( suite )
