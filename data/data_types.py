#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		data_types.py					-
#	HISTORY:							-
#		2019-01-16	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, copy, logging, math, os, re, sys
import numpy as np
import pdb

from .utils import *


#------------------------------------------------------------------------
#	CLASS:          BaseDataSetType                               -
#------------------------------------------------------------------------
class BaseDataSetType( object ):
  """Note that eventually all of the DATASET_DEFS handling in DataModel
should be encapsulated here.  With the simplifcation of 'fluence' shapes,
we don't really need this any more, but it's a good placeholder for
the future.
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #	METHOD:		BaseDataSetType.__init__()                      -
  #----------------------------------------------------------------------
  def __init__( self ):
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		BaseDataSetType.match()                         -
  #----------------------------------------------------------------------
  def match( self, dset, core ):
    """
    Args:
        dset (h5py.Dataset): dataset to match
        core (data.datamodel.Core): core instance
"""
    return  True
  #end match


  #----------------------------------------------------------------------
  #	METHOD:		BaseDataSetType.resolve()                       -
  #----------------------------------------------------------------------
  def resolve( self, dset, core, group, copy_name ):
    """
    Args:
        dset (h5py.Dataset): dataset to resolve
        core (data.datamodel.Core): core instance
        group (h5py.Group): group in which to create copy datasets
        copy_name (str): name for copied dataset
    Returns:
        list: list of ( name, dset ) tuples
"""
    return  dset
  #end resolve

#end BaseDataSetType


#------------------------------------------------------------------------
#	CLASS:          FluenceType                                     -
#------------------------------------------------------------------------
class FluenceType( BaseDataSetType ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #	METHOD:		FluenceType.__init__()                          -
  #----------------------------------------------------------------------
  def __init__( self ):
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		FluenceType.match()                             -
  #----------------------------------------------------------------------
  def match( self, dset, core ):
    """
    Args:
        dset (h5py.Dataset): dataset to match
        core (data.datamodel.Core): core instance
"""
    fm = core.fluenceMesh
    return \
        len( dset.shape ) >= 3 and \
        dset.shape[ 0 : 3 ] == ( fm.nz, fm.ntheta, fm.nr )
  #end match


  #----------------------------------------------------------------------
  #	METHOD:		FluenceType.resolve()                           -
  #----------------------------------------------------------------------
  def resolve( self, dset, core, group, copy_name ):
    """
    Args:
        dset (h5py.Dataset): dataset to process
        core (data.datamodel.Core): core instance
        group (h5py.Group): group in which to create copy datasets
    Returns:
        h5py.Dataset: either ``dset`` or a new dataset created in ``group``
"""
    ds_name = dset.name[ dset.name.rfind( '/' ) + 1 : ]

    if len( dset.shape ) == 4:
      copy_data = dset[ 0, :, :, : ]
      copy_dset = group.create_dataset( copy_name, data = copy_data )
      dset = copy_dset

    elif len( dset.shape ) == 5:
      copy_data = dset[ 0, :, :, :, 0 ]
      copy_dset = group.create_dataset( copy_name, data = copy_data )
      dset = copy_dset

    return  dset
  #end resolve

#end FluenceType


#------------------------------------------------------------------------
#	CLASS:          IntraPinEditsType                               -
#------------------------------------------------------------------------
class IntraPinEditsType( BaseDataSetType ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsType.__init__()                    -
  #----------------------------------------------------------------------
  def __init__( self ):
    pass
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		IntraPinEditsType.match()                       -
  #----------------------------------------------------------------------
  def match( self, dset, core ):
    """
    Args:
        dset (h5py.Dataset): dataset to match
        core (data.datamodel.Core): core instance
"""
    return \
        len( dset.shape ) > 0 and dset.shape[ 0 ] > 0 and \
	'PinFirstRegionIndexArray' in dset.attrs and \
	DataUtils.ToString( dset.attrs[ 'PinFirstRegionIndexArray' ] ) in \
            dset.parent and \
	'PinNumRegionsArray' in dset.attrs and \
	DataUtils.ToString( dset.attrs[ 'PinNumRegionsArray' ] ) in dset.parent
  #end match

#end IntraPinEditsType
