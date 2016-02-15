#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		deriveddata.py					-
#	HISTORY:							-
#		2016-02-10	leerw@ornl.gov				-
#	  Re-engineered for new approach to managing datasets.
#		2016-02-05	leerw@ornl.gov				-
#	  Keeping a DataModel reference instead of separate core,
#	  dataSetNames, and states.
#		2016-02-02	leerw@ornl.gov				-
#		2016-02-01	leerw@ornl.gov				-
#------------------------------------------------------------------------
import copy, h5py, math, os, sys, tempfile, threading
#import cStringIO, h5py, json, math, os, sys, threading, traceback
import numpy as np
import pdb

from averager import *
#from event.event import *


# indexes: 0-piny, 1-pinx, 2-ax, 3-assy
# keyed by dataset label
DERIVED_DEFS = \
  {
  'channel':
    {
    },

  'pin':
    {
    'assembly':
      {
      'label': 'assembly', 'prefix': 'asy',
      'avgshapein': ( 1, 1, 0, 0 ), 'shapemask': ( 2, 3 )
      },
    'axial':
      {
      'label': 'axial', 'prefix': 'axial',
      'avgshapein': ( 1, 1, 0, 1 ), 'shapemask': ( 2, )
      },
    'core':
      {
      'label': 'core', 'prefix': 'core',
      'avgshapein': ( 1, 1, 1, 1 ), 'shapemask': ()
      },
    'radial':
      {
      'label': 'radial', 'prefix': 'radial',
      'avgshapein': ( 0, 0, 1, 0 ), 'shapemask': ( 0, 1, 3 )
      }
    }
  }


#------------------------------------------------------------------------
#	CLASS:		DerivedDataMgr					-
#------------------------------------------------------------------------
class DerivedDataMgr( object ):
  """Encapsulation of the handling of derived datasets.

Properties:
  averager		Averager instance
  channelShape		shape for 'channel' datasets
  data			reference to DataModel
  derivedDefs		tree by category, derived label, dataset name of
			definitions
  derivedNames		tree by category, derived label, dataset name
			where a value beginning with '@' means it's an existing
			dataset that need not be calculated
  derivedStates		list of DerivedState objects
  h5File		h5py.File
  h5FileName		name of temporary file
  lock			threading.RLock instance
  pinShape		shape for 'pin' datasets
  scalarShape		shape for 'scalar' datasets
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.__del__()			-
  #----------------------------------------------------------------------
  def __del__( self ):
    if hasattr( self, 'h5File' ):
      h5_file = getattr( self, 'h5File' )
      if h5_file:
        h5_file.close()
#	if os.path.exists( h5_file.filename ):
#	  os.remove( h5_file.filename )
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, data_model ):
    """
@param  data_model	reference to DataModel instance
"""
    self.data = data_model
    core = data_model.GetCore()

    self.averager = Averager()
    self.channelShape = ( core.npiny + 1, core.npinx + 1, core.nax, core.nass )
    self.derivedNames = {}
    self.derivedStates = []
    self.h5File = None
    #self.h5FileName = None
    self.lock = threading.RLock()
    # this is fast enough to put here
    self.pinFactors = self.averager.CreateCorePinFactors( core )
    self.pinShape = ( core.npiny, core.npinx, core.nax, core.nass )
    self.scalarShape = ( 1, )

    self.derivedDefs = copy.deepcopy( DERIVED_DEFS )
    self._ResolveShapes( self.derivedDefs[ 'channel' ], self.channelShape )
    self._ResolveShapes( self.derivedDefs[ 'pin' ], self.pinShape )

    ds_names = data_model.GetDataSetNames()
    if ds_names is not None and data_model.GetStatesCount() > 0:
      self.derivedNames = \
          self._FindDataSets( data_model.GetState( 0 ).GetGroup(), ds_names )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._AddTreeEntry()			-
  #----------------------------------------------------------------------
  def _AddTreeEntry( self, tree, value, *names ):
    """Generically adds an entry to the dict hierarchy.
@param  tree		top level dict
@param  value		leaf value to add
@param  names		list of names in hierarchical order
"""
    if len( names ) > 0:
      cur_dict = tree

      for i in range( len( names ) - 1 ):
        name = names[ i ]
        if name in cur_dict:
          cur_dict = cur_dict[ name ]
        else:
          new_dict = {}
	  cur_dict[ name ] = new_dict
	  cur_dict = new_dict
      #end for

      cur_dict[ names[ -1 ] ] = value
    #end if
  #end _AddTreeEntry


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._CalculateDataSet()		-
  #----------------------------------------------------------------------
  def _CalculateDataSet( self, ds_name, avg_shape, avg_ds_name ):
    """Calculates using Averager.
@param  ds_name		source dataset name
@param  avg_shape	average dataset shape
@param  avg_ds_name	average dataset name
@return			count of states to which the dataset was added
"""
    count = 0

    #if self.states is not None and self.derivedStates is not None:
    if self.data.GetStatesCount() > 0 and self.derivedStates is not None:
      for state_ndx in range( len( self.derivedStates ) ):
	#from_st = self.states[ state_ndx ]
	from_st = self.data.GetState( state_ndx )
	der_st = self.derivedStates[ state_ndx ]

	if from_st is not None and der_st is not None:
	  from_group = from_st.GetGroup()
	  if ds_name in from_group:
	    from_data = from_group[ ds_name ].value
	    avg_data = self.averager.\
	        CalcGeneralAverage( from_data, avg_shape, self.pinFactors )

	    der_st.CreateDataSet( avg_ds_name, avg_data )
	    count += 1
	#end if
      #for state_ndx
    #end if states exist

    return  count
  #end _CalculateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._CopyDataSet()			-
  #----------------------------------------------------------------------
  def _CopyDataSet( self, ds_name, avg_shape, avg_ds_name ):
    """Calculates using Averager.
@param  ds_name		source dataset name
@param  avg_shape	average dataset shape
@param  avg_ds_name	average dataset name
@return			count of states to which the dataset was added
"""
    count = 0

    #if self.states is not None and self.derivedStates is not None:
    if self.data.GetStatesCount() > 0 and self.derivedStates is not None:
      for state_ndx in range( len( self.derivedStates ) ):
	#from_st = self.states[ state_ndx ]
	from_st = self.data.GetState( state_ndx )
	der_st = self.derivedStates[ state_ndx ]

	if from_st is not None and der_st is not None:
	  from_group = from_st.GetGroup()
	  if ds_name in from_group:
	    from_data = from_group[ ds_name ].value
	    avg_data = self.averager.CopyGeneralAverage( from_data, avg_shape )

	    der_st.CreateDataSet( avg_ds_name, avg_data )
	    count += 1
	#end if
      #for state_ndx
    #end if states exist

    return  count
  #end _CopyDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.CreateDataSet()			-
  #----------------------------------------------------------------------
  def CreateDataSet( self, category, derived_label, ds_name ):
    """Creates, if necessary calculating, the derived dataset.
@param  category	dataset category
@param  derived_label	derived type label
@param  ds_name		source dataset name
@return			dataset name
"""
#    cat_dict = self.derivedNames.get( category )
#    label_dict = cat_dict.get( derived_label )  if cat_dict is not None  else None
#    der_name = label_dict.get( ds_name )  if label_dict is not None  else None
    new_der_name = None

    ddef = self._FindTreeEntry( self.derivedDefs, category, derived_label )
    if ddef is not None:
      if self.h5File is None:
        self._CreateH5File()

      path = [ category, derived_label, ds_name ]
      der_name = self._FindTreeEntry( self.derivedNames, *path )

#			-- Must calculate?
#			--
      if der_name is None:
        new_der_name = 'derived:' + derived_label + '_' + ds_name
        self._CalculateDataSet( ds_name, ddef[ 'avgshape' ], new_der_name )
	#self._AddTreeEntry( self.derivedNames, new_der_name, *path )
#      avg_data = self.averager.CalcGeneralAverage(
#          from_data, ddef[ 'avgshape' ], self.pinFactors
#	  )

#			-- Must copy from existing?
#			--
      elif not der_name.startswith( 'derived:' ):
        from_name = der_name
        #new_der_name = 'derived:' + derived_label + '_' + ds_name
        new_der_name = 'derived:' + der_name
        self._CopyDataSet( from_name, ddef[ 'avgshape' ], new_der_name )
        #self._AddTreeEntry( self.derivedNames, new_der_name, *path )

#			-- Already calculated?
#			--
      #else:
      #end if-else

      if new_der_name is not None:
        self._AddTreeEntry( self.derivedNames, new_der_name, *path )
	self.data.AddDataSetName( 'derived', new_der_name )
	if ddef[ 'avgshape' ][ 2 ] > 1:
	  self.data.AddDataSetName( 'axial', new_der_name )
	elif len( ddef[ 'shapemask' ] ) == 0:
	  self.data.AddDataSetName( 'scalar', new_der_name )

	#self.data.dataSetChangeEvent.fire()

      else:
        new_der_name = der_name
    #end if ddef found

    return  new_der_name
  #end CreateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._CreateH5File()			-
  #----------------------------------------------------------------------
  def _CreateH5File( self ):
    """Creates and initializes a "derived" HDF5 file.  The state points
are initialized.  Populates the 'h5File' and 'derivedStates' properties.
@return			new h5py.File object (h5File property)
"""
#		-- Delete existing if requexted
#		--
#    if truncate_flag and self.h5ExtraFile is not None:
#      self.h5ExtraFile.close()
#      if os.path.exists( self.h5ExtraFilePath ):
#        os.remove( self.h5ExtraFilePath )
#      self.h5ExtraFile = None
#    #end if


#		-- Create only if not already created
#		--
    if self.h5File is None:
      fd, name = tempfile.mkstemp( '.h5' )
      os.close( fd )

      self.h5File = h5py.File( name, 'w' )

#			-- Add states with exposure values
#			--
      if self.data.GetStatesCount() > 0:
	n = 0
        for st in self.data.GetStates():
	  from_group = st.GetGroup()
	  if from_group is None:
	    self.derivedStates.append( None )

	  else:
	    der_name = from_group.name.replace( '/', '' )
	    der_group = self.h5File.create_group( der_name )
	    if 'exposure' in from_group:
	      exp_ds = der_group.create_dataset(
	          'exposure',
		  data = from_group[ 'exposure' ].value
		  )

	    self.derivedStates.append( DerivedState( n, der_group ) )
	  #end if state h5py group exists

	  n += 1
	#end for
      #end if states exist

      self.h5File.flush()
    #end if file doesn't exist

    return  self.h5File
  #end _CreateH5File


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._FindDataSets()			-
  #----------------------------------------------------------------------
  def _FindDataSets( self, state_group, ds_names ):
    """Searches for already-computed derived datasets
@param  state_group	h5py.Group for a state point
@param  ds_names	dict of existing dataset names by 'channel', 'pin'
@return			dict of derived names keyed by
			'category:derivetype:dataset'
"""
    derived_names = {}

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
	for category, defs_dict in self.derivedDefs.iteritems():
	  if category in ds_names:
	    for label, ddef in defs_dict.iteritems():
	      from_dataset = self.Match(
	          ddef, category, ds_names[ category ],
		  k, k_shape
		  )
	      if from_dataset:
		self._AddTreeEntry(
		    derived_names, k,
		    category, label, from_dataset
		    )

	        break
	      #end if matched
	    #end for ddef
	  #end if category in ds_names

	  if from_dataset:  break
	#end for category
      #end if not a subgroup or base dataset
    #end for k

    return  derived_names
  #end _FindDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._FindTreeEntry()			-
  #----------------------------------------------------------------------
  def _FindTreeEntry( self, tree, *names ):
    """Generically adds an entry to the dict hierarchy.
@param  tree		top level dict
@param  names		list of names in hierarchical order
@return			leaf value if found, None otherwise
"""
    value = None

    if len( names ) > 0:
      cur_dict = tree

      for i in range( len( names ) - 1 ):
        name = names[ i ]
        if name in cur_dict:
          cur_dict = cur_dict[ name ]
        else:
	  cur_dict = None
	  break
      #end while

      if cur_dict is not None:
        value = cur_dict.get( names[ -1 ] )
    #end if

    return  value
  #end _FindTreeEntry


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetDerivedLabels()		-
  #----------------------------------------------------------------------
  def GetDerivedLabels( self, ds_category ):
    """Returns the labels for the specified category
@param  category	category ('channel', 'pin')
@return			list of labels, possibly empty
"""
    return \
        sorted( self.derivedDefs[ category ].keys() ) \
	if category in self.derivedDefs else \
	[]
  #end GetDerivedLabels


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetDerivedName()			-
  #----------------------------------------------------------------------
  def GetDerivedName( self, category, derived_label, ds_name ):
    """Looks up the derived dataset name for the tuple.
@param  category	dataset category ('channel', 'pin')
@param  derived_label	label from derived data definition
@param  ds_name		source dataset name
@return			derived name if found, None otherwise
"""
    return \
      self._FindTreeEntry( self.derivedNames, category, derived_label, ds_name )
  #end GetDerivedName


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._GetDerivedNames()		-
  #----------------------------------------------------------------------
  def _GetDerivedNames( self ):
    """Accessor the 'derivedNames' property, a dict by
'category:derive_label:ds_name' of dataset names.
@return			dict reference
"""
    return  self.derivedNames
  #end _GetDerivedNames


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
  #	METHOD:		DerivedDataMgr.GetState()			-
  #----------------------------------------------------------------------
  def GetState( self, ndx = 0 ):
    """Retrieves a specific state point by index.
@param  ndx		0-based index
@return			DerivedState object or None if states not defined or
			ndx out of range
"""
    return  \
	self.derivedStates[ ndx ] \
	if self.derivedStates is not None and ndx >= 0 and \
	    ndx < len( self.derivedStates ) else \
	None
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr.GetStates()			-
  #----------------------------------------------------------------------
  def GetStates( self ):
    """Accessor for the 'states' property.
@return			State list
"""
    return  self.derivedStates
  #end GetStates


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

        if match is not None:  break
      #end for ds_name
    #if shapes match

    return  match
  #end Match


  #----------------------------------------------------------------------
  #	METHOD:		DerivedDataMgr._ResolveShapes()			-
  #----------------------------------------------------------------------
  def _ResolveShapes( self, defs_dict, ds_shape ):
    """
@param  defs_dict	dictionary of derived definitions by label
@param  ds_shape	reference shape
"""
    for label, item in defs_dict.iteritems():
      avg_shape_in = item[ 'avgshapein' ]
      avg_shape_out = []
      shape_out = []

      for i in range( len( avg_shape_in ) ):
        if avg_shape_in[ i ] == 0:
	  avg_shape_out.append( ds_shape[ i ] )
	  shape_out.append( ds_shape[ i ] )
        else:
	  avg_shape_out.append( 1 )

      item[ 'avgshape' ] = tuple( avg_shape_out )
      item[ 'shape' ] = \
          self.scalarShape  if len( shape_out ) == 0 else \
	  tuple( shape_out )
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

#end DerivedDataMgr


#------------------------------------------------------------------------
#	CLASS:		DerivedState					-
#------------------------------------------------------------------------
class DerivedState( object ):
  """Special State for derived datasets.
  
Fields:
  group			HDF5 group
  index			state point index
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, index, state_group ):
    """
@param  state_group	HDF5 group for this state
"""
    #super( DerivedState, self ).__init__( index, name, state_group )
    self.index = index
    self.group = state_group
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.Check()				-
  #----------------------------------------------------------------------
  def Check( self, core ):
    """
@return			empty list
"""
    return  []
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.CreateDataSet()			-
  #----------------------------------------------------------------------
  def CreateDataSet( self, ds_name, data_in ):
    """
@param  ds_name		dataset name
@param  data_in		numpy.ndarray
@return			h5py.Dataset object
"""
    return  self.group.create_dataset( ds_name, data = data_in )
  #end CreateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.GetDataSet()			-
  #----------------------------------------------------------------------
  def GetDataSet( self, ds_name ):
    """
@return			h5py.Dataset object or None if not found
"""
    return \
        self.group[ ds_name ] \
	if ds_name is not None and ds_name in self.group else \
	None
  #end GetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.GetGroup()				-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.HasDataSet()			-
  #----------------------------------------------------------------------
  def HasDataSet( self, ds_name ):
    """
"""
    return  ds_name is not None and ds_name in self.group
  #end HasDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.RemoveDataSet()			-
  #----------------------------------------------------------------------
  def RemoveDataSet( self, ds_name ):
    """
@return			True if removed, False if ds_name not in this
"""
    removed = ds_name is not None and ds_name in self.group
    if removed:
      del self.group[ ds_name ]

    return  removed
  #end RemoveDataSet

#end DerivedState
