#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		deriveddata.py					-
#	HISTORY:							-
#		2016-02-01	leerw@ornl.gov				-
#------------------------------------------------------------------------
import copy, h5py, math, os, sys, tempfile, threading
#import cStringIO, h5py, json, math, os, sys, threading, traceback
import numpy as np
import pdb

from averager import *


# indexes: 0-piny, 1-pinx, 2-ax, 3-assy
# keyed by dataset label
DERIVED_DEFS = \
  {
  'channel':
    [
    ],

  'pin':
    [
      { 'label': 'assembly', 'prefix': 'asy',
        'avgshape': ( 1, 1, 0, 0 ), 'shapemask': ( 2, 3 ) },
      { 'label': 'axial', 'prefix': 'axial',
	'avgshape': ( 1, 1, 0, 1 ), 'shapemask': ( 2, ) },
      { 'label': 'core', 'prefix': 'core',
	'avgshape': ( 1, 1, 1, 1 ), 'shapemask': () },
      { 'label': 'radial', 'prefix': 'radial',
	'avgshape': ( 0, 0, 1, 0 ), 'shapemask': ( 0, 1, 3 ) }
    ]
  }


#------------------------------------------------------------------------
#	CLASS:		DerivedDataMgr					-
#------------------------------------------------------------------------
class DerivedDataMgr( object ):
  """Encapsulation of the handling of derived datasets.

Properties:
  averager		Averager instance
  channelShape		shape for 'channel' datasets
  core			reference to DataModel.core (properties npinx, npiny, nax, nass)
  dataSetNames		reference to DataModel.dataSetNames
  #derivedData		dict by 'category:derivetype:dataset' of h5py.Dataset
			or name of 
#xxx make this [ category ][ derive_label ][ dataset ] = name
  derivedNames		dict by 'category:derivetype:dataset' of dataset names
			where a value beginning with '@' means it's an existing
			dataset that need not be calculated
  h5File		h5py.File
  h5FileName		name of temporary file
  lock			threading.RLock instance
  pinShape		shape for 'pin' datasets
  scalarShape		shape for 'scalar' datasets
  states		reference to DataModel.states
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.__del__()			-
  #----------------------------------------------------------------------
  def __del__( self ):
    if self.h5File:
      self.h5File.close()
#    if self.h5FileName and os.path.exists( self.h5FileName ):
#      os.remove( self.h5FileName )
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, core, states, ds_names ):
    """
@param  core		Core reference
@param  states		reference to State list
@param  ds_names	dict of dataset names by category
"""
    self.averager = Averager()
    self.core = core
    self.states = states
    self.dataSetNames = ds_names

    self.channelShape = ( core.npiny + 1, core.npinx + 1, core.nax, core.nass )
    self.derivedData = {}
    self.derivedNames = {}
    self.h5File = None
    self.h5FileName = None
    self.lock = threading.RLock()
    # this is fast enough to put here
    self.pinFactors = self.averager.CreateCorePinFactors( core )
    self.pinShape = ( core.npiny, core.npinx, core.nax, core.nass )
    self.scalarShape = ( 1, )

    self.derivedDefs = copy.deepcopy( DERIVED_DEFS )
    self._ResolveShapes( self.derivedDefs[ 'channel' ], self.channelShape )
    self._ResolveShapes( self.derivedDefs[ 'pin' ], self.pinShape )

    if ds_names != None and states != None and len( states ) > 0:
      self.derivedNames = self.FindDataSets( states[ 0 ].GetGroup(), ds_names )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.CreateDataSet()			-
  #----------------------------------------------------------------------
  def CreateDataSet( self, category, derived_label, ds_name ):
    """Creates, if necessary calculating, the derived dataset.
@param  category	dataset category
@param  derived_label	derived type label
@param  ds_name		source dataset name
@return			h5py.Dataset or None if dataset not found
"""
    dset = None
"""
Record the name of the calculated dataset, replacing any existing '@'name

    ddef = DerivedDataMgr.\
        FindItem( self.derivedDefs[ category ], 'label', derived_label )

    if ddef != None:
      if self.h5File == None:
        self._CreateH5File()

      name = self.derivedNames.get( key )
      if name != None:

    #end if ddef

    if name != None:

    if ddef != None:

      if name.startswith( '@' ):
        source_ds_name = name[ 1 : ]

      elif:
	n = 1
	for st in self.states:
	  if st.GetGroup() != None:
	    from_group = st.GetGroup()
	    st_name = from_group.name.replace( '/', '' )
	    to_group = self.h5File[ st_name ]

	    from_data = from_group[ ds_name ].value
	    avg_dset = averager.CalcGeneralAverage(
	        from_data, ddef[ 'avgshape' ], self.pinFactors
		)
	      exp_ds = to_group.create_dataset(
	          'exposure',
		  data = from_group[ 'exposure' ].value
		  )
	#end for
    #end if name
"""

    return  dset
  #end CreateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._CreateH5File()			-
  #----------------------------------------------------------------------
  def _CreateH5File( self ):
    """Creates and initializes a "derived" HDF5 file.  The state points
are initialized.
@return			new h5py.File object (h5File property)
"""
#		-- Delete existing if requexted
#		--
#    if truncate_flag and self.h5ExtraFile != None:
#      self.h5ExtraFile.close()
#      if os.path.exists( self.h5ExtraFilePath ):
#        os.remove( self.h5ExtraFilePath )
#      self.h5ExtraFile = None
#    #end if


#		-- Create if it does not exist
#		--
    if self.h5File == None:
      fd, name = tempfile.mkstemp( '.h5' )
      os.close( fd )

      self.h5FileName = name
      self.h5File = h5py.File( name, 'w' )

#			-- Add states with exposure values
#			--
      if self.states != None:
        for st in self.states:
	  if st.GetGroup() != None:
	    from_group = st.GetGroup()
	    to_group = self.h5File.\
	        create_group( from_group.name.replace( '/', '' ) )
	    if 'exposure' in from_group:
	      exp_ds = to_group.create_dataset(
	          'exposure',
		  data = from_group[ 'exposure' ].value
		  )
	  #end if state h5py group exists
	#end for
      #end if states exist

      self.h5File.flush()
    #end if file doesn't exist

    return  self.h5File
  #end _CreateH5File


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.FindDataSets()			-
  #----------------------------------------------------------------------
  def FindDataSets( self, state_group, ds_names ):
    """Searches for already-computed derived datasets
@param  state_group	h5py.Group for a state point
@param  ds_names	dict of existing dataset names by 'channel', 'pin'
@return			dict of derived names keyed by
			'category:derivetype:dataset'
"""
#		-- Build list of primary datasets
#		--
    all_ds_names = set( [] )
    for k, items in ds_names.iteritems():
      all_ds_names = all_ds_names.union( items )
    #end k

#		-- Search state point datasets
#		--
    for k in state_group:
      skip_it = isinstance( state_group[ k ], h5py.Group ) or k in all_ds_names
      if not skip_it:
        k_shape = state_group[ k ].shape

	from_dataset = None
	for category, defs in self.derivedDefs.iteritems():
	  if category in ds_names:
	    for ddef in defs:
	      from_dataset = self.Match(
	          ddef, category, ds_names[ category ],
		  k, k_shape
		  )
	      if from_dataset:
		self.lock.acquire()
		try:
	          #key = category + ':' + ddef[ 'label' ] + ':' + from_dataset
		  key = DerivedDataMgr.\
		      CreateKey( category, ddef[ 'label' ], from_dataset )
	          self.derivedNames[ key ] = '@' + k

# do this after creating dataset
#		  #if 2 in ddef[ 'shapemask' ]:
#		  if ddef[ 'avgshape' ][ 2 ] == 0:
#	            key = 'axial:' + key
#	            self.derivedNames[ key ] = '@' + k
		finally:
		  self.lock.release()

	        break
	      #end if matched
	    #end for ddef
	  #end if category in ds_names

	  if from_dataset:  break
	#end for category
      #end if not a subgroup or base dataset
    #end for k

    return  self.derivedNames
  #end FindDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetDataSet()			-
  #----------------------------------------------------------------------
  def GetDataSet( self ):
    """Retrieves the named dataset.
@return			h5py.Dataset object
"""
    return  None
  #end GetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetDerivedNames()		-
  #----------------------------------------------------------------------
  def GetDerivedNames( self ):
    """Accessor the 'derivedNames' property, a dict by
'category:derive_label:ds_name' of dataset names.
@return			dict reference
"""
    return  self.derivedNames
  #end GetDerivedNames


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetH5File()			-
  #----------------------------------------------------------------------
  def GetH5File( self ):
    """Accessor for the 'h5File' property.
@return			h5py.File instance or None
"""
    #Lazily create here?
    return  self.h5File
  #end GetH5File


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetStates()			-
  #----------------------------------------------------------------------
#  def GetStates( self ):
#    """Accessor for the 'states' property.
#@return			State list
#"""
#    return  self.states
#  #end GetH5File


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.Match()				-
  #----------------------------------------------------------------------
  def Match( self, derived_def, ds_category, ds_names, name_in, shape_in ):
    """Looks for a match by shape and then name.
@param  derived_def	derived definition dict with 'label', 'prefix',
			and 'shape' keys
@param  ds_category	dataset category name
@param  ds_names	list of dataset names in category
@param  name_in		name to match
@param  shape_in	shape to match
@return			the matched name in ds_names
"""
    match = None

#		-- First match on shape
#		--
    derived_shape = derived_def[ 'shape' ]
    if shape_in == derived_shape or \
        ( len( derived_shape ) == 0 and shape_in == ( 1, ) ):

#			-- Match on names
#			--
      derived_prefix = derived_def[ 'prefix' ]
      for ds_name in ds_names:

#				-- Try pure prefix match
	if name_in == derived_prefix + '_' + ds_name:
	  match = ds_name
        else:
	  cat_prefix = ds_category + '_'
          if ds_name.startswith( cat_prefix ) and \
	      name_in == ds_name.replace( ds_category, derived_prefix ):
            match = ds_name

        if match != None:  break
      #end for ds_name
    #if shapes match

    return  match
  #end Match


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._ResolveShapes()			-
  #----------------------------------------------------------------------
  def _ResolveShapes( self, ddefs, ds_shape ):
    for item in ddefs:
      avg_shape = item[ 'avgshape' ]
      dshape = []
      for i in range( len( avg_shape ) ):
        if avg_shape[ i ] == 0:
	  dshape.append( ds_shape[ i ] )
      item[ 'shape' ] = \
          self.scalarShape  if len( dshape ) == 0 else \
	  tuple( dshape )

#      shape_mask = item[ 'shapemask' ]
#      dshape = []
#      for i in shape_mask:
#        dshape.append( ds_shape[ i ] )
#      item[ 'shape' ] = tuple( dshape )
  #end _ResolveShapes


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.CreateKey()			-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateKey( category, derive_label, ds_name ):
    """
@return		category:derive_label:ds_name
"""
    return  category + ':' + derive_label + ':' + ds_name
  #end CreateKey


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.FindItem()			-
  #----------------------------------------------------------------------
  @staticmethod
  def FindItem( item_list, key, value ):
    match = None
    for item in item_list:
      if key in item and item[ key ] == value:
        match = item
	break
    #end for

    return  match
  #end FindItem


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.ParseKey()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ParseKey( key ):
    """
@return		( category, derive_label, ds_name ) or None
"""
    tokens = key.split( ':' )
    return  tuple( tokens ) if len( tokens ) == 3 else None
  #end ParseKey

#end DataModel
