#!/usr/bin/env python
import os, sys
import numpy as np

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..' ) )
from data.averager import *
from data.datamodel import *


def create_pin_factors_baseline():
  model = DataModel( 'data/pinfactors1.h5' )
  core = model.core
  avg = Averager()
  factors = avg.CreateCorePinFactors( core )
  print factors.tolist()
#end create_pin_factors_baseline


def create_pin_powers_baselines():
  model = DataModel( 'data/pinpowers1.h5' )
  avg = Averager()
  powers = model.GetStates()[ 0 ].GetDataSet( 'pin_powers' )
  volumes = model.core.pinVolumes
  factors = avg.CreateCorePinFactors( model.core )

#	-- 1DAxial
  #cur_shape = ( 1, 1, powers.shape[ 2 ], 1 )
  #results = avg.CalcGeneralAverage( powers, cur_shape )
  results = avg.Calc1DAxialAverage( model.core, powers )
  fp = file( 'data/pinpowers1.1daxial.1.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors )
  results = avg.Calc1DAxialAverage( model.core, powers, factors )
  fp = file( 'data/pinpowers1.1daxial.2.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors, volumes )
  results = avg.Calc1DAxialAverage( model.core, powers, factors, volumes )
  fp = file( 'data/pinpowers1.1daxial.3.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

#	-- 2DAssy
  #cur_shape = ( 1, 1, 1, powers.shape[ 3 ] )
  #results = avg.CalcGeneralAverage( powers, cur_shape )
  results = avg.Calc2DAssyAverage( model.core, powers )
  fp = file( 'data/pinpowers1.2dassy.1.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors )
  results = avg.Calc2DAssyAverage( model.core, powers, factors )
  fp = file( 'data/pinpowers1.2dassy.2.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors, volumes )
  results = avg.Calc2DAssyAverage( model.core, powers, factors, volumes )
  fp = file( 'data/pinpowers1.2dassy.3.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

#	-- 2DPin
  #cur_shape = ( powers.shape[ 0 ], powers.shape[ 1 ], 1, powers.shape[ 3 ] )
  #results = avg.CalcGeneralAverage( powers, cur_shape )
  results = avg.Calc2DPinAverage( model.core, powers )
  fp = file( 'data/pinpowers1.2dpin.1.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors )
  results = avg.Calc2DPinAverage( model.core, powers, factors )
  fp = file( 'data/pinpowers1.2dpin.2.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors, volumes )
  results = avg.Calc2DPinAverage( model.core, powers, factors, volumes )
  fp = file( 'data/pinpowers1.2dpin.3.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

#	-- 3DAssy
  #cur_shape = ( 1, 1, powers.shape[ 2 ], powers.shape[ 3 ] )
  #results = avg.CalcGeneralAverage( powers, cur_shape )
  results = avg.Calc3DAssyAverage( model.core, powers )
  fp = file( 'data/pinpowers1.3dassy.1.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors )
  results = avg.Calc3DAssyAverage( model.core, powers, factors )
  fp = file( 'data/pinpowers1.3dassy.2.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors, volumes )
  results = avg.Calc3DAssyAverage( model.core, powers, factors, volumes )
  fp = file( 'data/pinpowers1.3dassy.3.out', 'w' )
  print >> fp, results.tolist()
  fp.close()

#	-- Scalar
  #cur_shape = ( 1, 1, 1, 1 )
  #results = avg.CalcGeneralAverage( powers, cur_shape )
  result = avg.CalcScalarAverage( model.core, powers )
  results = [ [ [ [ result ] ] ] ]
  fp = file( 'data/pinpowers1.scalar.1.out', 'w' )
  print >> fp, str( results )
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors )
  result = avg.CalcScalarAverage( model.core, powers, factors )
  results = [ [ [ [ result ] ] ] ]
  fp = file( 'data/pinpowers1.scalar.2.out', 'w' )
  print >> fp, str( results )
  fp.close()

  #results = avg.CalcGeneralAverage( powers, cur_shape, factors, volumes )
  result = avg.CalcScalarAverage( model.core, powers, factors, volumes )
  results = [ [ [ [ result ] ] ] ]
  fp = file( 'data/pinpowers1.scalar.3.out', 'w' )
  print >> fp, str( results )
  fp.close()
#end create_pin_powers_baselines


if __name__ == '__main__':
  #create_pin_factors_baseline()
  create_pin_powers_baselines()
