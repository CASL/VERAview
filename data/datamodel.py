#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel.py					-
#	HISTORY:							-
#		2016-04-16	leerw@ornl.gov				-
#	  Added per-statept dataset ranges, rangesByStatePt.
#		2016-03-17	leerw@ornl.gov				-
#	  Calling Close() from DataModel.__del__().
#		2016-03-16	leerw@ornl.gov				-
#	  Moved FindMax() methods from RasterWidget to here, where it
#	  belongs.
#		2016-03-14	leerw@ornl.gov				-
#		2016-02-12	leerw@ornl.gov				-
#		2016-02-10	leerw@ornl.gov				-
#	  Fixed bug where core.npinx and core.npiny were not being assigned
#	  when core.npin was set from pin_powers length.
#		2016-02-09	leerw@ornl.gov				-
#	  Fixed logic bug in GetStateDataSet() when the copy dataset
#	  already exists.
#		2016-02-08	leerw@ornl.gov				-
#	  New scheme for defining datasets.				-
#		2016-02-05	leerw@ornl.gov				-
#	  Added DataModel dataSetNamesVersion property and
#	  AddDataSetName() method.
#		2016-02-03	leerw@ornl.gov				-
#	  Added IsValidForShape().
#		2016-02-01	leerw@ornl.gov				-
#	  Starting derived datasets.
#		2016-01-22	leerw@ornl.gov				-
#	  Added DataModel.ToCSV().
#		2016-01-09	leerw@ornl.gov				-
#	  Added IsExtra().
#		2016-01-06	leerw@ornl.gov				-
#	  Added DataModel.createAssemblyIndex().
#		2015-11-28	leerw@ornl.gov				-
#	  Added DataModel.IsNoDataValue().
#		2015-11-23	leerw@ornl.gov				-
#	  Fixed bug where ExtraDataSet.ReadAll() must be called in
#	  _CreateExtraH5File().
#		2015-11-18	leerw@ornl.gov				-
#	  Added 'other' dataset category.
#		2015-11-14	leerw@ornl.gov				-
#	  Added more convenience methods to State and DataModel.
#	  Added support for storing "core" as well as state-point-based
#	  extra datasets.
#		2015-11-12	leerw@ornl.gov				-
# 	  Renamed 'avg' category to 'extra' to support imports as well
#	  as calculated datasets.
#		2015-10-26	leerw@ornl.gov				-
#	  Added 'avg' as a category type with storage in a separate HDF5
#	  file.
#		2015-10-05	leerw@ornl.gov				-
#	  Setting core.npinx and core.npiny to be generally ready to
#	  accept non-square pin arrays.
#		2015-10-02	leerw@ornl.gov				-
#	  Added GetAssyIndex() and GetPinIndex() static methods.
#		2015-05-11	leerw@ornl.gov				-
#	  Changed State.axialLevel to axialValue.
#	  Added "axial" dataset type.
#		2015-05-06	leerw@ornl.gov				-
#	  Added DataModel.GetScalarValue().
#		2015-05-05	leerw@ornl.gov				-
#	  Allowing shapeless datasets.
#		2015-05-01	leerw@ornl.gov				-
#	  Working Andrew's latest feedback specifying detector_mesh and
#	  detector_operable datasets.
#		2015-04-27	leerw@ornl.gov				-
#	  Looking for state_nnnn/detector_response, added "detector"
#	  dataset category.
#		2015-04-22	leerw@ornl.gov				-
#	  Handling case of assembly index being a tuple in IsValid().
#		2015-04-13	leerw@ornl.gov				-
#	  Added Check() and CheckAll() methods.
#		2015-04-11	leerw@ornl.gov				-
#	  Added DataModel.IsValid().
#		2015-03-31	leerw@ornl.gov				-
#	  Fixed State.ReadAll() to allow skips in state number/names.
#		2015-03-25	leerw@ornl.gov				-
#	  Renamed "arrays" dataset category to "pin" to distinguish
#	  from "channel" in the future.
#	  Added DataModel.GetRange() and _ReadDataSetRange().
#	  Added rangesLock field to DataModel.
#		2015-03-19	leerw@ornl.gov				-
# 	  Moved arrays and scalars search to State.FindDataSets()
#		2015-03-13	leerw@ornl.gov				-
#	  Added Scalar arrays and scalars properties.
#		2015-02-07	leerw@ornl.gov				-
#	  Added Core.pinVolumesSum.
#		2015-01-19	leerw@ornl.gov				-
# 	  Added DataModel.HasData().
#		2015-01-06	leerw@ornl.gov				-
#	  Modified DataModel.ExtractSymmetryExtent().
#		2014-12-28	leerw@ornl.gov				-
#		2014-10-22	leerw@ornl.gov				-
#------------------------------------------------------------------------
import copy, cStringIO, h5py, json, math, os, sys, tempfile, threading, traceback
import numpy as np
import pdb

#from deriveddata import *
from event.event import *


COL_LABELS = \
  (
    'R', 'P', 'N', 'M', 'L', 'K', 'J', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A'
  )

#{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}


DATASET_DEFS = \
  {
  'channel':
    {
    'label': 'channel',
    'shape_expr': '( core.npiny + 1, core.npinx + 1, core.nax, core.nass )',
    'type': 'channel'
    },

  'detector':
    {
    'label': 'detector',
    'shape_expr': '( core.ndetax, core.ndet )',
    'type': 'detector'
    },

  'pin':
    {
    'category': 'pin',
    'label': 'pin',
    'shape_expr': '( core.npiny, core.npinx, core.nax, core.nass )',
    'type': 'pin'
    },

  'pin:assembly':
    {
#    'avg_method': 'avg.calc_pin_assembly_avg( core, data )',
    'avg_method': 'calc_pin_assembly_avg',
    'copy_expr': '[ 0, 0, :, : ]',
    'copy_shape_expr': '( 1, 1, core.nax, core.nass )',
    'ds_prefix': 'asy',
    'label': 'assembly',
    'shape_expr': '( core.nax, core.nass )',
    'type': 'pin:assembly'
    },

  'pin:axial':
    {
    'avg_method': 'calc_pin_axial_avg',
    'copy_expr': '[ 0, 0, :, 0 ]',
    'copy_shape_expr': '( 1, 1, core.nax, 1 )',
    'ds_prefix': 'axial',
    'label': 'axial',
    'shape_expr': '( core.nax, )',
    'type': 'pin:axial'
    },

  'pin:core':
    {
    'avg_method': 'calc_pin_core_avg',
    'ds_prefix': 'core',
    'label': 'core',
    'shape': ( 1, ),
    'type': 'pin:core'
    },

  'pin:radial':
    {
    'avg_method': 'calc_pin_radial_avg',
    'copy_expr': '[ :, :, 0, : ]',
    'copy_shape_expr': '( core.npiny, core.npinx, 1, core.nass )',
    'ds_prefix': 'radial',
    'label': 'radial',
    'shape_expr': '( core.npiny, core.npinx, core.nass )',
    'type': 'pin:radial'
    },

  'scalar':
    {
    'label': 'scalar',
    'shape': ( 1, ),
    'type': 'scalar'
    }
  }

#DERIVED_CALCULATOR_CLASS = 'data.averages.Averager'
DERIVED_CALCULATOR_CLASS = 'data.pin_averages.Averages'


TIME_DS_NAMES = set([ 'exposure', 'exposure_efpd', 'hours' ])


#------------------------------------------------------------------------
#	CLASS:		Core						-
#------------------------------------------------------------------------
class Core( object ):
  """Data/model bean encapsulating depletion 'CORE' data.  Underlying
data are stored in a numpy array, but this detail should be hidden and
abstracted by this class.  This is a work in progress that will be updated
as needed.

Core datasets have shape ( npin, npin, nax, nass ) and are indexed by
  0-based indexes [ pin_row, pin_col, axial_level, assy_ndx ]

Properties:
  apitch		assembly pitch in cm
  axialMesh		np.ndarray of mesh values
  axialMeshCenters	np.ndarray of center-of-mesh values
  coreLabels		( col_labels, row_labels )
  coreMap		np.ndarray of assembly indexes, row-major,
			origin top,left (row, col)
  coreSym		symmetry value
  detectorMap		np.ndarray of assembly indexes (row, col)
  detectorMeshCenters	np.ndarray of center-of-mesh values
  group			HDF5 group
  nass			number of full core assemblies
  nassx			number of core assembly columns
  nassy			number of core assembly rows
  ndet			number of detectors
  ndetax		number of detector axial levels
  nax			number of axial levels
  npin			number of pins in each assembly
  pinVolumes		np.ndarray, row-major, origin top,left
  pinVolumesSum		sum of all pin volumes
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Core.__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, h5_group = None ):
    """
@param  h5_group	top level group in the file
"""
    self.Clear()
    if h5_group is not None:
      self.Read( h5_group )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		Core.__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    return  json.dumps( self.ToJson() )
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		Core.Check()					-
  #----------------------------------------------------------------------
  def Check( self ):
    """
@return			list of error messages
"""
    missing = []

#    if self.axialMesh is None or self.axialMeshCenters is None:
# Redundant, caught with exception in Read()
    if self.axialMesh is None:
      missing.append( 'AXIAL_MESH not found' )
#    elif self.axialMesh.shape[ 0 ] != self.nax + 1 or \
#        self.axialMeshCenters.shape[ 0 ] != self.nax:
    elif self.axialMesh.shape[ 0 ] != self.nax + 1:
      missing.append( 'AXIAL_MESH shape is not consistent with NAX' )

# Redundant, caught with exception in Read()
    if self.coreMap is None:
      missing.append( 'CORE_MAP not found' )
    elif self.coreMap.shape[ 0 ] != self.nassy or \
        self.coreMap.shape[ 1 ] != self.nassx:
      missing.append( 'CORE_MAP shape is not consistent with NASSX and NASSY' )

    if self.detectorMap is not None and self.coreMap is not None:
      if self.detectorMap.shape != self.coreMap.shape:
        missing.append( 'DETECTOR_MAP shape inconsistent with CORE_MAP shape' )

    if self.pinVolumes is None:
      pass
#      missing.append( 'PIN_VOLUMES not found' )
    elif self.pinVolumes.shape[ 0 ] != self.npin or \
        self.pinVolumes.shape[ 1 ] != self.npin or \
        self.pinVolumes.shape[ 2 ] != self.nax or \
        self.pinVolumes.shape[ 3 ] != self.nass:
      missing.append( 'PIN_VOLUMES shape is not consistent with NPIN, NAX, and NASS' )

    return  missing
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		Core.Clear()					-
  #----------------------------------------------------------------------
  def Clear( self ):
    self.apitch = 0
    self.axialMesh = None
    self.axialMeshCenters = None
    self.coreLabels = None
    self.coreMap = None
    self.coreSym = 0
    self.detectorMap = None
    self.detectorMeshCenters = None
    self.group = None
    self.nass = 0
    self.nassx = 0
    self.nassy = 0
    self.nax = 0
    self.ndet = 0
    self.ndetax = 0
    self.npin = 0
    self.npinx = 0
    self.npiny = 0
    self.pinVolumes = None
    self.pinVolumesSum = 0.0
    self.ratedFlow = 0
    self.ratedPower = 0
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		Core.CreateAssyLabel()				-
  #----------------------------------------------------------------------
  def CreateAssyLabel( self, col, row ):
    result = '(?)'
    if self.coreLabels is not None and len( self.coreLabels ) >= 2:
      result = '(%s-%s)' % \
          ( self.coreLabels[ 0 ][ col ], self.coreLabels[ 1 ][ row ] )

    return  result
  #end CreateAssyLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core._FindInGroup()				-
  #----------------------------------------------------------------------
  def _FindInGroup( self, name, *groups ):
    match = None
    for g in groups:
      if g is not None and name in g:
        match = g[ name ]
	break
    #end for
    return  match
  #end _FindInGroup


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetAssemblyPitch()				-
  #----------------------------------------------------------------------
  def GetAssemblyPitch( self ):
    """Returns a value for the assembly pitch.
@return			'apitch' value or a default of 20.0
"""
    return  21.5  if self.apitch == 0.0 else  self.apitch
  #end GetAssemblyPitch


  #----------------------------------------------------------------------
  #	METHOD:		Core.IsNonZero()				-
  #----------------------------------------------------------------------
  def IsNonZero( self ):
    """
@return			True if npiny, npinx, nax, nass, and coreSym are all
			gt 0
"""
    return  \
        self.npiny > 0 and self.npinx > 0 and \
	self.nax > 0 and self.nass > 0 and self.coreSym > 0
  #end IsNonZero


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetGroup()					-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		Core.Read()					-
  #----------------------------------------------------------------------
  def Read( self, h5_group ):
    self.Clear()

#		-- Assert on valid group
#		--
    if h5_group is None or not isinstance( h5_group, h5py.Group ):
      raise Exception( 'Must have valid HDF5 file' )

#		-- Assert on CORE
#		--
    if 'CORE' not in h5_group:
      raise Exception( 'Could not find "CORE"' )

    core_group = h5_group[ 'CORE' ]
    input_group = h5_group[ 'INPUT' ] if 'INPUT' in h5_group else None

    self._ReadImpl( core_group, input_group )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		Core._ReadImpl()				-
  #----------------------------------------------------------------------
  def _ReadImpl( self, core_group, input_group ):
    self.group = core_group

    in_core_group = None
    if input_group is not None:
      in_core_group = input_group.get( 'CASEID/CORE' )

#		-- Assert on must haves: 'axial_mesh', 'core_map'
#		--
    missing = []
    axial_mesh_item = \
        self._FindInGroup( 'axial_mesh', core_group, in_core_group )
    if axial_mesh_item is None:
      missing.append( '"axial_mesh" dataset not found' )

    core_map_item = self._FindInGroup( 'core_map', core_group, in_core_group )
    if core_map_item is None:
      missing.append( '"core_map" dataset not found' )

    if missing:
      raise Exception( ','.join( missing ) )

#		-- No exception, plow on
#		--
    self.coreMap = core_map_item.value
    self.nassy = self.coreMap.shape[ 0 ]
    self.nassx = self.coreMap.shape[ 1 ]

#		-- Labels
#		--
    col_labels = list( COL_LABELS )
    while self.nassx > len( col_labels ):
      col_labels.insert( 0, chr( ord( col_labels[ 0 ] ) + 1 ) )
    col_labels = col_labels[ -self.nassx : ]
    row_labels = [ '%d' % x for x in range( 1, self.nassy + 1 ) ]
    self.coreLabels = ( col_labels, row_labels )

#		-- Other datasets
#		--
    item = self._FindInGroup( 'apitch', core_group, in_core_group )
    if item is not None:
      self.apitch = item.value.item() if len( item.shape ) > 0 else item.value
#      self.apitch = item.value[ 0 ]

    #item = self._FindInGroup( 'axial_mesh', core_group, in_core_group )
    #if item is not None:
    if True:
      self.axialMesh = axial_mesh_item.value
      self.nax = self.axialMesh.shape[ 0 ] - 1
#			-- Numpy magic
      t = np.copy( axial_mesh_item.value )
      t2 = np.r_[ t, np.roll( t, -1 ) ]
      self.axialMeshCenters = np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]

    item = self._FindInGroup( 'core_sym', core_group, in_core_group )
    if item is None:
      self.coreSym = 1
    else:
      self.coreSym = item.value.item() if len( item.shape ) > 0 else item.value

    self.pinVolumesSum = 0
    item = self._FindInGroup( 'pin_volumes', core_group, in_core_group )
    if item is not None:
      self.pinVolumes = item.value
      self.pinVolumesSum = np.sum( item.value )
      self.npin = self.pinVolumes.shape[ 0 ]  # and [ 1 ]
      self.npiny = self.pinVolumes.shape[ 0 ]
      self.npinx = self.pinVolumes.shape[ 1 ]
      if self.nax == 0:
        self.nax = self.pinVolumes.shape[ 2 ]
      self.nass = self.pinVolumes.shape[ 3 ]

    item = self._FindInGroup( 'rated_flow', core_group, in_core_group )
    if item is not None:
      self.ratedFlow = item.value.item() if len( item.shape ) > 0 else item.value
      #self.ratedFlow = item.value[ 0 ]

    item = self._FindInGroup( 'rated_power', core_group, in_core_group )
    if item is not None:
      self.ratedPower = item.value.item() if len( item.shape ) > 0 else item.value
      #self.ratedPower = item.value[ 0 ]

#		-- Optional detector_map
#		--
    #xxxx if no detector_map, assume each assembly is a detector
    item = self._FindInGroup( 'detector_map', core_group, in_core_group )
    #if item is not None and item.value.shape == self.coreMap.shape:
    if item is not None:
      self.detectorMap = item.value
      self.ndet = np.amax( item.value )

#			-- Optional detector_mesh
#			--
      item = self._FindInGroup( 'detector_mesh', core_group )
      if item is not None:
	self.detectorMeshCenters = item.value
#	self.detectorMeshCentersSorted = \
#	    item.value if item.value[ -1 ] > item.value[ 0 ] else \
#	    item.value[ :: -1 ]
        self.ndetax = item.shape[ 0 ]
      else:
        self.detectorMeshCenters = self.axialMeshCenters
        self.ndetax = self.nax
    #end if detector_map

#		-- Infer missing dimensions
#		--
    if self.nass == 0:
      self.nass = np.amax( self.coreMap )

    if self.npin == 0 and input_group is not None:
      num_pins_ds = input_group.get( 'CASEID/ASSEMBLIES/Assembly_1/num_pins' )
      if num_pins_ds is not None:
        self.npin = num_pins_ds.value.item() if len( num_pins_ds.shape ) > 0 else num_pins_ds.value
	self.npinx = self.npin
	self.npiny = self.npin
        #self.npin = num_pins_ds.value[ 0 ]
    #end if

#		-- Assert NAX match b/w axial_mesh and pin_volumes
#		--
    if self.nax > 0 and self.pinVolumes is not None and \
        self.pinVolumes.shape[ 2 ] != self.nax:
      raise Exception( 'NAX dimension mismatch between "axial_mesh" and "pin_volumes"' )

#		-- Assert on NPIN
#		--
#x No: channel files don't have pin_volumes.
#x    if self.npin == 0:
#x      raise Exception( 'NPIN could not be determined from "num_pins" or "pin_volumes"' )
  #end _ReadImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core.ToJson()					-
  #----------------------------------------------------------------------
  def ToJson( self ):
    obj = {}
    obj[ 'apitch' ] = self.apitch
    if self.axialMesh is not None:
      obj[ 'axialMesh' ] = self.axialMesh.tolist()
    if self.coreMap is not None:
      obj[ 'coreMap' ] = self.coreMap.tolist()
    obj[ 'coreSym' ] = self.coreSym
    if self.detectorMap is not None:
      obj[ 'detectorMap' ] = self.detectorMap.tolist()
    if self.detectorMeshCenters is not None:
      obj[ 'detectorMeshCenters' ] = self.detectorMeshCenters.tolist()
    obj[ 'nass' ] = self.nass
    obj[ 'nassx' ] = self.nassx
    obj[ 'nassy' ] = self.nassy
    obj[ 'nax' ] = self.nax
    obj[ 'ndet' ] = self.ndet
    obj[ 'ndetax' ] = self.ndetax
    obj[ 'npin' ] = self.npin
    if self.pinVolumes is not None:
      obj[ 'pinVolumes' ] = self.pinVolumes.tolist()
    obj[ 'ratedFlow' ] = self.ratedFlow
    obj[ 'ratedPower' ] = self.ratedPower

    return  obj
  #end ToJson
#end Core


#------------------------------------------------------------------------
#	CLASS:		DataModel					-
#------------------------------------------------------------------------
class DataModel( object ):
  """Data/model bean encapsulation.  For now we read the
'CORE' group as the 'core' property, and all the states as the 'states'
property.

Properties:
  averager		reference to object for caculating derived averages
  core			Core
  #dataSetChangeEvent	event.Event object
  dataSetDefs		dict of dataset definitions
  dataSetDefsByName	reverse lookup of dataset definitions by ds_name
  dataSetDefsLock	threading.RLock for dataSetDefs and dataSetDefsByName
  dataSetNames		dict of dataset names by category
			  ( 'channel', 'derived', 'detector',
			     'pin', 'scalar' )
  dataSetNamesVersion	counter to indicate changes
  #derivedDataMgr	DerivedDataMgr instance
  derivedFile		h5py.File for derived data
  derivedStates		list of DerivedState instances
  h5File		h5py.File
  ranges		dict of ranges ( min, max ) by dataset
  rangesByStatePt	list by statept index of dicts by dataset of ranges 
  rangesLock		threading.RLock for ranges dict
  states		list of State instances
"""


#		-- Constants
#		--

  DEFAULT_range = ( sys.float_info.min, sys.float_info.max )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.__del__()				-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.Close()
#    if self.h5File is not None:
#      self.h5File.close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, h5f_param = None ):
    """Constructor with optional HDF5 file or filename.  If neither are
passed, Read() must be called.
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
"""
#		-- Instantiate averager
#		--
    module_path, class_name = DERIVED_CALCULATOR_CLASS.rsplit( '.', 1 )
    try:
      module = __import__( module_path, fromlist = [ class_name ] )
      cls = getattr( module, class_name )
      self.averager = cls()
    except AttributeError:
      raise Exception(
	  'DataModel error: Class "%s" not found in module "%s"' %
	  ( class_name, module_path )
	  )
    except ImportError:
      raise Exception(
	  'DataModel error: Module "%s" could not be imported' % module_path
	  )

#		-- Create locks
#		--
    #self.dataSetChangeEvent = Event( self )
    self.dataSetDefsLock = threading.RLock()
    self.rangesLock = threading.RLock()

    self.Clear()
    if h5f_param is not None:
      self.Read( h5f_param )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.__str__()				-
  #----------------------------------------------------------------------
  def __str__( self ):
    #return  json.dumps( self.ToJson() )
    return  ''
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.AddDataSetName()			-
  #----------------------------------------------------------------------
  def AddDataSetName( self, ds_type, ds_name ):
    """
@param  ds_type		dataset type
@param  ds_name		name of new dataset
"""
    if ds_type in self.dataSetNames:
      type_list = self.dataSetNames[ ds_type ]
    else:
      type_list = []
      self.dataSetNames[ ds_type ] = type_list

    if not ds_name in type_list:
      type_list.append( ds_name )

      ddef = self.dataSetDefs[ ds_type ]
      if ddef:
        self.dataSetDefsByName[ ds_name ] = ddef
	if ddef[ 'shape_expr' ].find( 'core.nax' ) >= 0:
	  self.dataSetNames[ 'axial' ].append( ds_name )

      self.dataSetNamesVersion += 1
    #end if ds_name is new
  #end AddDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Check()				-
  #----------------------------------------------------------------------
  def Check( self ):
    """
@return			list of error messages
"""
    missing = []
    missing += self.core.Check()
    missing += State.CheckAll( self.states, self.core )

    return  missing
    #return  missing if len( missing ) > 0 else None
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Clear()				-
  #----------------------------------------------------------------------
  def Clear( self ):
    self.core = None
    self.dataSetDefs = None
    self.dataSetDefsByName = None
    self.dataSetNames = None
    self.dataSetNamesVersion = 0
    self.derivedFile = None
    self.derivedStates = None
    self.h5File = None
    self.ranges = None
    self.rangesByStatePt = None
    self.states = None
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    if hasattr( self, 'derivedFile' ):
      der_file = getattr( self, 'derivedFile' )
      if der_file:
	fname = der_file.filename
        der_file.close()
        os.remove( fname )
    #end if

    if self.h5File:
      self.h5File.close()
    self.Clear()
  #end Close


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAssemblyIndex()			-
  #----------------------------------------------------------------------
  def CreateAssemblyIndex( self, col, row ):
    """Creates tuple from the column and row indexes.
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( assy_ndx, col, row )
"""
    return \
        ( self.core.coreMap[ row, col ], col, row ) \
	if self.core is not None else \
	( -1, -1, -1 )
  #end CreateAssemblyIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAssemblyIndexFromIndex()	-
  #----------------------------------------------------------------------
  def CreateAssemblyIndexFromIndex( self, assy_ndx ):
    """Creates tuple from the column and row indexes.
@param  assy_ndx	0-based assembly index
@return			0-based ( assy_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    places = np.argwhere( self.core.coreMap == assy_ndx + 1 )
    if len( places ) > 0:
      place = places[ -1 ]
      result = ( assy_ndx, place[ 1 ], place[ 0 ] )
    return  result
  #end CreateAssemblyIndexFromIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAxialValue()			-
  #----------------------------------------------------------------------
  def CreateAxialValue( self, **kwargs ):
    """Create from 'core_ndx', 'detector_ndx', or 'value' index values.
Parameters:
  core_ndx		0-based core axial index
  detector_ndx		0-based detector axial index
  pin_ndx		0-based core axial index, alias for 'core_ndx'
  value			axial value
@return			( axial_cm, core_ndx, detector_ndx )
"""
    core_ndx = -1
    det_ndx = -1
    axial_cm = -1

    if 'value' in kwargs:
      axial_cm = kwargs[ 'value' ]
      core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )
      det_ndx = self.FindListIndex( self.core.detectorMeshCenters, axial_cm )

    elif 'detector_ndx' in kwargs:
      det_ndx = max( 0, min( kwargs[ 'detector_ndx' ], self.core.ndetax - 1 ) )
      axial_cm = self.core.detectorMeshCenters[ det_ndx ]
      core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )

    elif 'core_ndx' in kwargs:
      core_ndx = max( 0, min( kwargs[ 'core_ndx' ], self.core.nax - 1 ) )
      axial_cm = self.core.axialMeshCenters[ core_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMeshCenters, axial_cm )

    elif 'pin_ndx' in kwargs: # huh?
      pin_ndx = max( 0, min( kwargs[ 'pin_ndx' ], self.core.nax - 1 ) )
      axial_cm = self.core.axialMeshCenters[ pin_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMeshCenters, axial_cm )

    return  ( axial_cm, core_ndx, det_ndx )
  #end CreateAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedDataSet()		-
  #----------------------------------------------------------------------
  def _CreateDerivedDataSet( self, ds_category, derived_label, ds_name ):
    """Calculates and adds the specified dataset.
@param  ds_category	dataset category, e.g., 'channel', 'pin'
@param  derived_label	derived label, e.g., 'assembly', 'axial', 'core,
			'radial'
@param  ds_name		dataset name that is in ds_category, e.g.,
			'pin_powers', 'pin_fueltemps'
@return			name of new dataset or None if params are invalid
"""
    derived_name = None
    core = self.core

    if len( self.states ) > 0:
      ddef = None
      der_names = \
          self._CreateDerivedNames( ds_category, derived_label, ds_name )
      if der_names:
        ddef = self.dataSetDefs.get( der_names[ 0 ] )

      if ddef and 'avg_method' in ddef:
	derived_name = der_names[ 1 ]
        avg_method_name = ddef[ 'avg_method' ]

	try:
	  avg_method = getattr( self.averager, avg_method_name )

          for state_ndx in range( len( self.states ) ):
	    st = self.GetState( state_ndx )
	    derived_st = self.GetDerivedState( state_ndx )

	    data = st.GetDataSet( ds_name )
	    if data is None:
	      data = derived_st.GetDataSet( ds_name )

	    if data:
	      #avg_data = avg_method( self.core, data )
	      avg_data = avg_method( data.value )
	      derived_st.CreateDataSet( derived_name, avg_data )
	    #end if data
	  #end for each state

	  self.AddDataSetName( der_names[ 0 ], derived_name )

	except Exception, ex:
	  msg = 'Error calculating derived "%s" dataset for "%s"' % \
	      ( derived_label, ds_name )
	  print >> sys.stderr, '%s\nddef="%s"' % ( msg, str( ddef ) )
	  raise Exception( msg )
      #end if dataset definition found
    #end we have state points

    return  derived_name
  #end _CreateDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedH5File()		-
  #----------------------------------------------------------------------
  def _CreateDerivedH5File( self, states ):
    """Creates and initializes a "derived" HDF5 file.  Derived state points
are initialized.
@return			( h5py.File, [ DerivedState ] )
"""
#		-- Create temp fle
#		--
    fd, name = tempfile.mkstemp( '.h5' )
    os.close( fd )

    derived_file = h5py.File( name, 'w' )
    derived_states = []

    if states and len( states ) > 0:
      n = 0
      for st in states:
        from_group = st.GetGroup()
	if from_group is None:
	  derived_states.append( None )

	else:
	  der_name = from_group.name.replace( '/', '' )
	  der_group = derived_file.create_group( der_name )
	  if 'exposure' in from_group:
	    exp_ds = der_group.create_dataset(
	        'exposure',
		data = from_group[ 'exposure' ].value
		)

	  derived_states.append( DerivedState( n, der_name, der_group ) )
	#end if state h5py group exists

	n += 1
      #end for
    #end if we have states

    derived_file.flush()

    return  ( derived_file, derived_states )
  #end _CreateDerivedH5File


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedNames()			-
  #----------------------------------------------------------------------
  def _CreateDerivedNames( self, ds_category, derived_label, ds_name ):
    """Creates the dataset type name (e.g., pin:radial) and
prefixed (e.g., radial_pin_powers) and replaced (radial_powers) derived names.
@param  ds_category	dataset category, e.g., 'channel', 'pin'
@param  derived_label	derived label, e.g., 'assembly', 'axial', 'core,
			'radial'
@param  ds_name		dataset name that is in ds_category, e.g.,
			'pin_powers', 'pin_fueltemps'
@return			( ds_type, prefix_name, replaced_name )
			or None if invalid params
"""
    result = None
    ds_type = ds_category + ':' + derived_label
    ddef = self.dataSetDefs.get( ds_type )
    if ddef:
      der_prefix = ddef[ 'ds_prefix' ]

      pref_name = der_prefix + '_' + ds_name
      repl_name = pref_name.replace( ds_category + '_', '' )

      result = ( ds_type, pref_name, repl_name )
    #end if ddef

    return  result
  #end _CreateDerivedNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateDetectorIndex()			-
  #----------------------------------------------------------------------
  def CreateDetectorIndex( self, col, row ):
    """Creates tuple from the column and row indexes.
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( det_ndx, col, row )
"""
    return \
        ( self.core.detectorMap[ row, col ], col, row ) \
	if self.core is not None else \
	( -1, -1, -1 )
  #end CreateDetectorIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateDetectorIndexFromIndex()	-
  #----------------------------------------------------------------------
  def CreateDetectorIndexFromIndex( self, det_ndx ):
    """Creates tuple from the column and row indexes.
@param  det_ndx		0-based detector index
@return			0-based ( det_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    places = np.argwhere( self.core.detectorMap == det_ndx + 1 )
    if len( places ) > 0:
      place = places[ -1 ]
      result = ( det_ndx, place[ 1 ], place[ 0 ] )
    return  result
  #end CreateDetectorIndexFromIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ExtractSymmetryExtent()		-
  #----------------------------------------------------------------------
  def ExtractSymmetryExtent( self ):
    """Returns the starting horizontal (left) and ending vertical (top)
assembly 0-based indexes, inclusive, and the right and bottom indexes,
exclusive, followed by the number of assemblies in the horizontal and vertical
dimensions.
@return			None if core is None, otherwise
			( left, top, right+1, bottom+1, dx, dy )
"""
    #bounds = ( -1, -1, -1, -1, 0, 0 )
    #left = -1
    #bottom = -1
    #right = -1
    #top = -1

    result = None

    if self.core is not None:
      bottom = self.core.nassy
      right = self.core.nassx

      if self.core.coreSym == 4:
	left = self.core.nassx >> 1
	top = self.core.nassy >> 1
      elif self.core.coreSym == 8:
	left = self.core.nassx >> 2
	top = self.core.nassy >> 2
      else:
	left = 0
	top = 0

#NO
#      if (self.core.nassx % 2) == 0 and left > 0:
#        left += 1
#      if (self.core.nassy % 2) == 0 and top > 0:
#        top += 1

      result = ( left, top, right, bottom, right - left, bottom - top )
    #end if

    return  result
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindChannelMaxValue()			-
  #----------------------------------------------------------------------
  def FindChannelMaxValue( self, ds_name, state_ndx, cur_obj = None ):
    """Creates a dict with channel addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'channel' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMaxValueAddr().
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyIndex, axialValue,
			channelColRow, stateIndex
@return			dict with possible keys: 'assembly_index',
			'axial_value', 'channel_colrow', 'state_index'
"""
    results = {}

    addr, state_ndx = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    elif cur_obj is None:
      assy_ndx = self.CreateAssemblyIndexFromIndex( addr[ 3 ] )
      if assy_ndx[ 0 ] >= 0:
        results[ 'assembly_index' ] = assy_ndx

      axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
      if axial_value[ 0 ] >= 0.0:
        results[ 'axial_value' ] = axial_value

      results[ 'channel_colrow' ] = ( addr[ 1 ], addr[ 0 ] )
      results[ 'state_index' ] = state_ndx

    else:
      skip = hasattr( cur_obj, 'assemblyIndex' ) and \
          getattr( cur_obj, 'assemblyIndex' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_ndx = self.CreateAssemblyIndexFromIndex( addr[ 3 ] )
	if assy_ndx[ 0 ] >= 0:
          results[ 'assembly_index' ] = assy_ndx

      skip = hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
	if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if hasattr( cur_obj, 'channelColRow' ):
        chan_colrow = getattr( cur_obj, 'channelColRow' )
	skip = chan_colrow[ 1 ] == addr[ 0 ] and chan_colrow[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'channel_colrow' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None

    return  results
  #end FindChannelMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindDetectorMaxValue()		-
  #----------------------------------------------------------------------
  def FindDetectorMaxValue( self, ds_name, state_ndx, cur_obj = None ):
    """Creates dict with detector addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'detector' dataset.
Calls FindMaxValueAddr().
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: axialValue,
			detectorIndex, stateIndex
@return			dict with possible keys: 'axial_value',
			'detector_index', 'state_index'
"""
    results = {}

    addr, state_ndx = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    elif cur_obj is None:
      axial_value = self.CreateAxialValue( detector_ndx = addr[ 0 ] )
      if axial_value[ 0 ] >= 0.0:
        results[ 'axial_value' ] = axial_value

      det_ndx = self.CreateDetectorIndexFromIndex( addr[ 1 ] )
      if det_ndx[ 0 ] >= 0:
        results[ 'detector_index' ] = det_ndx

      results[ 'state_index' ] = state_ndx

    else:
      skip = hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 2 ] == addr[ 0 ]
      if not skip:
	axial_value = self.CreateAxialValue( detector_ndx = addr[ 0 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = hasattr( cur_obj, 'detectorIndex' ) and \
          getattr( cur_obj, 'detectorIndex' )[ 0 ] == addr[ 1 ]
      if not skip:
	det_ndx = self.CreateDetectorIndexFromIndex( addr[ 1 ] )
	if det_ndx[ 0 ] >= 0:
          results[ 'detector_index' ] = det_ndx

      skip = hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None

    return  results
  #end FindDetectorMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindFirstDetector()			-
  #----------------------------------------------------------------------
  def FindFirstDetector( self ):
    result = ( -1, -1, -1 )

    if self.core is not None and self.core.detectorMap is not None:
      nzs = self.core.detectorMap.nonzero()
      row = nzs[ 0 ][ 0 ] if len( nzs[ 0 ] ) > 0 else -1
      col = nzs[ 1 ][ 0 ] if len( nzs[ 1 ] ) > 0 else -1
      det = self.core.detectorMap[ row, col ] if row >= 0 and col >= 0 else -1
      result = [ det, col, row ]

    return  result
  #end FindFirstDetector


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindListIndex()			-
  #----------------------------------------------------------------------
  def FindListIndex( self, values, value ):
    """Values in the list are assumed to be in order, either ascending or
descending.  Note bisect only does ascending.
@param  values		list of values
@param  value		value to search
@return			0-based index N, values[ N ]
			'a': values[ N ] <= value < values[ N + 1 ]
			'd': values[ N ] >= value > values[ N + 1 ]
"""
    match_ndx = -1

    if values is not None and len( values ) > 0:
      if values[ 0 ] > values[ -1 ]:
        if value > values[ 0 ]:
	  match_ndx = 0
	elif value <= values[ -1 ]:
	  match_ndx = len( values ) -1
	else:
	  for i in range( len( values ) ):
	    if values[ i ] < value:
	      match_ndx = i
	      break
	#end if

      else:
	if value < values[ 0 ]:
	  match_ndx = 0
	elif value >= values[ -1 ]:
	  match_ndx = len( values ) -1
	else:
	  for i in range( len( values ) ):
	    if values[ i ] > value:
	      match_ndx = i
	      break
	#end if
    #end if not empty list

    return  match_ndx
  #end FindListIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindMaxValueAddr()			-
  #----------------------------------------------------------------------
  def FindMaxValueAddr( self, ds_name, state_ndx ):
    """Finds the first address of the max value
@param  ds_name		name of dataset to search
@param  state_ndx	0-based state point index, or -1 for all states
@return			( addr indices or None, state_ndx )
"""
    addr = None

    if ds_name is None:
      pass

    elif state_ndx >= 0:
      dset = self.GetStateDataSet( state_ndx, ds_name )
      if dset:
        x = np.nanargmax( dset.value )
	addr = np.unravel_index( x, dset.shape )

    else:
      max_value = -sys.float_info.max
      for st in range( len( self.states ) ):
        dset = self.GetStateDataSet( st, ds_name )
	if dset:
	  x = np.nanargmax( dset.value )
	  cur_addr = np.unravel_index( x, dset.shape )
	  cur_max = dset.value[ cur_addr ]
	  if cur_max > max_value:
	    addr = cur_addr
	    state_ndx = st
	    max_value = cur_max
      #end for
    #end else all states

    return  addr, state_ndx
  #end FindMaxValueAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindPinMaxValue()			-
  #----------------------------------------------------------------------
  def FindPinMaxValue( self, ds_name, state_ndx, cur_obj = None ):
    """Creates dict with detector addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMaxValueAddr().
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyIndex, axialValue,
			pinColRow, stateIndex
@return			dict with possible keys: 'assembly_index',
			'axial_value', 'pin_colrow', 'state_index'
"""
    results = {}

    addr, state_ndx = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    elif cur_obj is None:
      assy_ndx = self.CreateAssemblyIndexFromIndex( addr[ 3 ] )
      if assy_ndx[ 0 ] >= 0:
        results[ 'assembly_index' ] = assy_ndx

      axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
      if axial_value[ 0 ] >= 0.0:
        results[ 'axial_value' ] = axial_value

      results[ 'pin_colrow' ] = ( addr[ 1 ], addr[ 0 ] )
      results[ 'state_index' ] = state_ndx

    else:
      skip = hasattr( cur_obj, 'assemblyIndex' ) and \
          getattr( cur_obj, 'assemblyIndex' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_ndx = self.CreateAssemblyIndexFromIndex( addr[ 3 ] )
	if assy_ndx[ 0 ] >= 0:
          results[ 'assembly_index' ] = assy_ndx

      skip = hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if hasattr( cur_obj, 'pinColRow' ):
        pin_colrow = getattr( cur_obj, 'pinColRow' )
	skip = pin_colrow[ 1 ] == addr[ 0 ] and pin_colrow[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'pin_colrow' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None
   
    return  results
  #end FindPinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetCore()				-
  #----------------------------------------------------------------------
  def GetCore( self ):
    """Accessor for the 'core' property.
@return			Core instance or None
"""
    return  self.core
  #end GetCore


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetChangeEvent()		-
  #----------------------------------------------------------------------
#  def GetDataSetChangeEvent( self ):
#    """Accessor the 'dataSetChangeEvent' property
#@return			reference
#"""
#    return  self.dataSetChangeEvent
#  #end GetDataSetChangeEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetDef()			-
  #----------------------------------------------------------------------
  def GetDataSetDef( self, ds_type = None ):
    """Accessor for the 'dataSetDefs' property.
@param  ds_type		optional type name
@return			if ds_type is not None, the definition for the type
			or None if not found
			if ds_type is None, dict of definitions name by type
"""
    return \
	self.dataSetDefs  if ds_type is None else \
	self.dataSetDefs.get( ds_type )
  #end GetDataSetDef


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetDefByDsName()		-
  #----------------------------------------------------------------------
  def GetDataSetDefByDsName( self, ds_name ):
    """Looks up the dataset definition for the dataset name.
@param  ds_name		dataset name
@return			dataset definition in dataSetDefsByName if found,
			None otherwise
"""
    return  self.dataSetDefsByName.get( ds_name )
  #end GetDataSetDefByDsName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, ds_name ):
    """Removes prefixes.
"""
    return \
	ds_name  if not ds_name else \
        ds_name[ 8 : ]  if ds_name.startswith( 'derived:' ) else \
	ds_name
#        ds_name[ 6 : ]  if ds_name.startswith( 'extra:' ) else
  #end GetDataSetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNames()			-
  #----------------------------------------------------------------------
  def GetDataSetNames( self, ds_type = None ):
    """Accessor for the 'dataSetNames' property.
@param  ds_type		optional type name
@return			if ds_type is not None, list of datasets in that
			ds_type, empty if not found
			if ds_type is None, dict of dataset name lists by
			ds_type
			( 'axial', 'channel', 'detector',
			  'pin', 'scalar', etc. )
"""
    return \
        self.dataSetNames if ds_type is None else \
	self.dataSetNames.get( ds_type, [] )
  #end GetDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNamesVersion()		-
  #----------------------------------------------------------------------
  def GetDataSetNamesVersion( self ):
    return  self.dataSetNamesVersion
  #end GetDataSetNamesVersion


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self, ds_name ):
    """Retrieves the type for the name dataset.
@return			type or None
"""
    ddef = self.dataSetDefsByName.get( ds_name )
    return  ddef[ 'type' ]  if ddef  else None
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedDataMgr()			-
  #----------------------------------------------------------------------
#  def GetDerivedDataMgr( self ):
#    """Accessor for the 'derivedDataMgr' property.
#@return			reference
#"""
#    return  self.derivedDataMgr
#  #end GetDerivedDataMgr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedLabels()			-
  #----------------------------------------------------------------------
  def GetDerivedLabels( self, ds_category ):
    """For the specified category, returns all the labels for possible
derived datasets.
"""
    labels = []

    #xxxx must look up prefix in def
    for def_name, def_item in self.dataSetDefs.iteritems():
      if def_name.startswith( ds_category ):
        ndx = def_name.find( ':' )
	if ndx >= 0:
	  labels.append( def_name[ ndx + 1 : ] )
    #end for

    labels.sort()
    return  labels
  #end GetDerivedLabels


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedState()			-
  #----------------------------------------------------------------------
  def GetDerivedState( self, ndx = 0 ):
    """Retrieves a specific state point by index.
@param  ndx		0-based index
@return			DerivedState object or None if derivedStates not
			defined or ndx out of range
"""
    return  \
	self.derivedStates[ ndx ]  \
	if self.derivedStates is not None and ndx >= 0 and \
	    ndx < len( self.derivedStates ) else \
	None
  #end GetDerivedState


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedStates()			-
  #----------------------------------------------------------------------
  def GetDerivedStates( self ):
    """Accessor for the 'derivedStates' property.
@return			list of DerivedState instances or None
"""
    return  self.derivedStates
  #end GetDerivedStates


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetFirstDataSet()			-
  #----------------------------------------------------------------------
  def GetFirstDataSet( self, category ):
    """Retrieves the first dataset in the specified category
@param  category	category/type
@return			dataset name or None
"""
    names = self.dataSetNames.get( category )
    return  names[ 0 ] if names is not None and len( names ) > 0 else None
  #end GetFirstDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetH5File()				-
  #----------------------------------------------------------------------
  def GetH5File( self ):
    """Accessor for the 'h5File' property.
@return			h5py.File instance or None
"""
    return  self.h5File
  #end GetH5File


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange( self, ds_name, state_ndx = -1 ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
@param  ds_name		dataset name
@param  state_ndx	optional 0-based statept index to use, or -1
			for global range
@return			( min, max ), possible the range of floating point values
"""
    ds_range = None

    self.rangesLock.acquire()
    try:
      if state_ndx < 0:
        range_dict = self.ranges

      elif state_ndx >= self.GetStatesCount():
        raise  Exception( 'State index %d is out of range' % state_ndx )

      else:
        range_dict = self.rangesByStatePt[ state_ndx ]
	if range_dict is None:
	  range_dict = {}
	  self.rangesByStatePt[ state_ndx ] = range_dict
      #end if-else

      ds_range = range_dict.get( ds_name )
      if ds_range is None:
        ds_range = self._ReadDataSetRange( ds_name, state_ndx )
        range_dict[ ds_name ] = ds_range

    finally:
      self.rangesLock.release()

    if ds_range is None:
      ds_range = DataModel.DEFAULT_range

    return  ds_range
  #end GetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetRange_orig()			-
  #----------------------------------------------------------------------
  def GetRange_orig( self, ds_name ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
@param  ds_name		dataset name
@return			( min, max ), possible the range of floating point values
"""
    ds_range = None

    self.rangesLock.acquire()
    try:
      ds_range = self.ranges.get( ds_name )
      if ds_range is None:
        ds_range = self._ReadDataSetRange( ds_name )
        self.ranges[ ds_name ] = ds_range
    finally:
      self.rangesLock.release()

    if ds_range is None:
      ds_range = DataModel.DEFAULT_range

    return  ds_range
  #end GetRange_orig


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetRanges()				-
  #----------------------------------------------------------------------
  def GetRanges( self ):
    """Accessor for the 'ranges' property.
@return			dict of ranges by dataset name
"""
    return  self.ranges
  #end GetRanges


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetScalarValue()			-
  #----------------------------------------------------------------------
  def GetScalarValue( self, ds ):
    """Returns the value for the scalar dataset
@param  ds		dataset
@return			value or None
"""
    return \
        None if ds is None else \
	ds.value if len( ds.shape ) == 0 else \
	ds.value.item()
  #end GetScalarValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetState()				-
  #----------------------------------------------------------------------
  def GetState( self, ndx = 0 ):
    """Retrieves a specific state point by index.
@param  ndx		0-based index
@return			State object or None if states not defined or ndx out
			of range
"""
    return  \
	self.states[ ndx ]  \
	if self.states is not None and ndx >= 0 and ndx < len( self.states ) else \
	None
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetStateDataSet()			-
  #----------------------------------------------------------------------
  def GetStateDataSet( self, state_ndx, ds_name ):
    """Retrieves a normal or derived dataset.
@param  state_ndx	0-based state point index
@param  ds_name		dataset name, normal or derived
@return			h5py.Dataset object if found or None
"""
    dset = None

    st = None
    derived_st = None

    if ds_name is not None:
      st = self.GetState( state_ndx )
      derived_st = self.GetDerivedState( state_ndx )

    #if st and derived_st:
    if st:
      self.dataSetDefsLock.acquire()
      try:
        dset = st.GetDataSet( ds_name )
	if dset is None and derived_st is not None:
	  dset = derived_st.GetDataSet( ds_name )

        if dset is not None and len( dset.shape ) < 4 and dset.shape != ( 1, ):
          copy_name = 'copy:' + ds_name
	  #copy_dset = st.GetDataSet( copy_name )
	  copy_dset = derived_st.GetDataSet( copy_name )

	  if copy_dset is not None:
	    dset = copy_dset
	  else:
            ds_def = self.dataSetDefsByName.get( ds_name )
	    if ds_def is not None and 'copy_expr' in ds_def:
	      copy_data = \
	          np.ndarray( ds_def[ 'copy_shape' ], dtype = np.float64 )
	      copy_data.fill( 0.0 )
	      exec_str = 'copy_data' + ds_def[ 'copy_expr' ] + ' = dset'

	      globals_env = {}
	      locals_env = { 'copy_data': copy_data, 'dset': dset }
	      exec( exec_str, globals_env, locals_env )
	      dset = derived_st.CreateDataSet( copy_name, locals_env[ 'copy_data' ] )
        #end if must use copy
      finally:
        self.dataSetDefsLock.release()
    #end if st and derived_st

    return  dset
  #end GetStateDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetStateDataSet_old()			-
  #----------------------------------------------------------------------
#  def GetStateDataSet_old( self, state_ndx, ds_name ):
#    """Retrieves a normal or extra dataset.
#@param  state_ndx	0-based state point index
#@param  ds_name		dataset name, where a prefix of 'derived:' or 'extra:'
#			means a derived or extra dataset respectively
#@return			h5py.Dataset object if found or None
#"""
#    if ds_name is None:
#      st = None
#    elif ds_name.startswith( 'derived:' ):
#      st = self.derivedDataMgr.GetState( state_ndx )
#      use_name = ds_name
#    elif ds_name.startswith( 'extra:' ):
#      st = self.GetExtraState( state_ndx )
#      use_name = ds_name[ 6 : ]
#    else:
#      st = self.GetState( state_ndx )
#      use_name = ds_name
#
#    return  st.GetDataSet( use_name ) if st is not None else None
#  #end GetStateDataSet_old


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetStates()				-
  #----------------------------------------------------------------------
  def GetStates( self ):
    """Accessor for the 'states' property.
@return			list of State instances or None
"""
    return  self.states
  #end GetStates


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetStatesCount()			-
  #----------------------------------------------------------------------
  def GetStatesCount( self ):
    """
@return			number of State instances, where -1 means not read
"""
    return  -1  if self.states is None else  len( self.states )
  #end GetStatesCount


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetTimeValue()			-
  #----------------------------------------------------------------------
  def GetTimeValue( self, state_ndx, ds_name ):
    """Returns the value for the scalar dataset
@param  state_ndx	0-based state index
@param  ds_name		time dataset name
@return			value or None
"""
    value = 0.0
    #if self.IsValid( state_index = state_ndx ) and ds_name in self.GetDataSetNames( 'time' )
    if self.IsValid( state_index = state_ndx ) and ds_name is not None:
      value = \
          (state_ndx + 1) if ds_name == 'state' else \
          self.GetScalarValue( self.states[ state_ndx ].group[ ds_name ] )

    return  value
  #end GetTimeValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.HasData()				-
  #----------------------------------------------------------------------
  def HasData( self ):
    """Checks for existence of core and states
@return			True if both are non-None, False otherwise
"""
    return \
        self.core is not None and self.states is not None and \
	len( self.states ) > 0 and \
	self.core.nass > 0 and self.core.nax > 0 and self.core.npin > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.HasDataSetType()			-
  #----------------------------------------------------------------------
  def HasDataSetType( self, ds_type = None ):
    """Tests existence of datasets in named type
@param  ds_type		one of type names, e.g., 'axial', 'channel', 'derived',
			'detector', 'pin', 'scalar'
@return			True if there are datasets, False otherwise
"""
    return  \
        ds_type in self.dataSetNames and \
	len( self.dataSetNames[ ds_type ] ) > 0
  #end HasDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.HasDerivedDataSet()			-
  #----------------------------------------------------------------------
  def HasDerivedDataSet( self, ds_category, derived_label, ds_name ):
    """Checks to see if the dataset exists.
@param  ds_category	dataset category, e.g., 'channel', 'pin'
@param  derived_label	derived label, e.g., 'assembly', 'axial', 'core,
			'radial'
@param  ds_name		dataset name that is in ds_category, e.g.,
			'pin_powers', 'pin_fueltemps'
@return			name under which it exists or None if we don't have it
"""
    match = None
    names = None
    der_names = self._CreateDerivedNames( ds_category, derived_label, ds_name )
    if der_names:
      names = self.dataSetNames.get( der_names[ 0 ] )

    if names:
      if der_names[ 1 ] in names:
        match = der_names[ 1 ]
      elif der_names[ 2 ] in names:
        match = der_names[ 2 ]

    return  match

#    name = self.derivedDataMgr.GetDerivedName( category, derived_label, ds_name )
#    return  name is not None and len( name ) > 0
  #end HasDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsNoDataValue()			-
  #----------------------------------------------------------------------
  def IsNoDataValue( self, ds_name, value ):
    """Determine if the value is a "no data" value.  Eventually, this should
be some sort of lookup based on the dataset name, or perhaps a check
for NaN.  For now, we just assume 0.0 is "no data".

@param  ds_name		dataset name
@param  value		value to check
@return			True if "no data", False otherwise
"""
    #return  value <= 0.0 if ds_range[ 0 ] >= 0.0 else math.isnan( value )
    return  value == 0.0 or math.isnan( value )
  #end IsNoDataValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValid()				-
  #----------------------------------------------------------------------
  def IsValid( self, **kwargs ):
    """Checks values for validity w/in ranges available for this dataset
@param  kwargs		named values to check:
			  'assembly_index'
			  'axial_level'
			  'channel_colrow'
			  ('dataset_name' (requires 'state_index'))
			  'detector_index'
			  'pin_colrow'
			  'state_index'
"""
    valid = True

    if 'assembly_index' in kwargs:
      val = kwargs[ 'assembly_index' ]
#      valid = val >= 0 and val < self.core.nass
      if hasattr( val, '__iter__' ):
        valid &= val is not None and val[ 0 ] >= 0 and val[ 0 ] < self.core.nass
      else:
        valid &= val >= 0 and val < self.core.nass

    if 'axial_level' in kwargs:
      val = kwargs[ 'axial_level' ]
      valid &= val >= 0 and val < self.core.nax

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] is not None:
      col, row = kwargs[ 'channel_colrow' ]
      valid &= \
          col >= 0 and col <= self.core.npinx and \
	  row >= 0 and row <= self.core.npiny

    if 'detector_index' in kwargs:
      val = kwargs[ 'detector_index' ]
      valid &= val >= 0 and val < self.core.ndet

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] is not None:
      col, row = kwargs[ 'pin_colrow' ]
      valid &= \
          col >= 0 and col < self.core.npinx and \
	  row >= 0 and row < self.core.npiny

    if 'state_index' in kwargs:
      val = kwargs[ 'state_index' ]
      valid &= val >= 0 and val < len( self.states )
      if valid and 'dataset_name' in kwargs:
        valid &= kwargs[ 'dataset_name' ] in self.states[ val ].group
    #end if 'state_index'

    return  valid
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValidForShape()			-
  #----------------------------------------------------------------------
  def IsValidForShape( self, shape_in, **kwargs ):
    """Checks values for ge 0 and w/in shape range.
@param  shape_in	shape against which to validate
@param  kwargs		named values to check:
    'assembly_index'
    'axial_level'
    'channel_colrow'
    'pin_colrow'
"""
    valid = True

    if 'assembly_index' in kwargs:
      val = kwargs[ 'assembly_index' ]
      if hasattr( val, '__iter__' ):
        valid &= val is not None and val[ 0 ] >= 0 and val[ 0 ] < shape_in[ 3 ]
      else:
        valid &= val >= 0 and val < shape_in[ 3 ]

    if 'axial_level' in kwargs:
      val = kwargs[ 'axial_level' ]
      valid &= val >= 0 and val < shape_in[ 2 ]

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] is not None:
      col, row = kwargs[ 'channel_colrow' ]
      valid &= \
          col >= 0 and col <= shape_in[ 0 ] and \
	  row >= 0 and row <= shape_in[ 1 ]

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] is not None:
      col, row = kwargs[ 'pin_colrow' ]
      valid &= \
          col >= 0 and col < shape_in[ 0 ] and \
	  row >= 0 and row < shape_in[ 1 ]

    return  valid
  #end IsValidForShape


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.LoadExtraDataSet()			-
  #----------------------------------------------------------------------
#  def LoadExtraDataSet( self, ds_name, src_name = 'core', state_ndx = -1 ):
#    """Retrieves an extra dataset.
#@param  ds_name		name of dataset to load, required
#@param  src_name	optional name of source dataset for a time-based
#			dataset when combined with state_ndx, otherwise
#			defaults to 'core'
#@param  state_ndx	optional 0-based state point index when combined with
#			src_name
#@return			h5py.Dataset object or None if not found
#
#Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
#if both 'src_name' and 'state_ndx' are specified, the dataset is searched
#using the fully-qualified name in the specified state point (if 'state_ndx'
#is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
#to be 'core', and the dataset is not associated with a state point.
#"""
#    dset = None
#
#    if self.h5ExtraFile is not None and ds_name is not None:
#      qname = src_name + '.' + ds_name
#
#      if state_ndx < 0:
#        if qname in self.h5ExtraFile:
#	  dset = self.h5ExtraFile[ qname ]
#      else:
#        st = self.GetExtraState( state_ndx )
#	if st is not None and qname in st.GetGroup():
#	  dset = st.GetDataSet( qname )
#      #end if-else core or state point
#    #end if file exists
#
#    return  dset
#  #end LoadExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeAssemblyIndex()		-
  #----------------------------------------------------------------------
  def NormalizeAssemblyIndex( self, assy_ndx ):
    result = \
      (
      max( 0, min( assy_ndx[ 0 ], self.core.nass - 1 ) ),
      max( 0, min( assy_ndx[ 1 ], self.core.nassx - 1 ) ),
      max( 0, min( assy_ndx[ 2 ], self.core.nassy - 1 ) )
      )
    return  result
  #end NormalizeAssemblyIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeAxialLevel()			-
  #----------------------------------------------------------------------
#  def NormalizeAxialLevel( self, axial_level ):
#    return  max( 0, min( axial_level, self.core.nax - 1 ) )
#  #end NormalizeAxialLevel


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeAxialValue()			-
  #----------------------------------------------------------------------
  def NormalizeAxialValue( self, axial_value ):
    result = \
      (
      axial_value[ 0 ],
      max( 0, min( axial_value[ 1 ], self.core.nax -1 ) ),
      max( 0, min( axial_value[ 2 ], self.core.ndetax -1 ) )
      )
    return  result
  #end NormalizeAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeChannelColRow()		-
  #----------------------------------------------------------------------
  def NormalizeChannelColRow( self, chan_rc ):
    result = \
      (
      max( 0, min( chan_rc[ 0 ], self.core.npin ) ),
      max( 0, min( chan_rc[ 1 ], self.core.npin ) )
      )
    return  result
  #end NormalizeChannelColRow


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeDetectorIndex()		-
  #----------------------------------------------------------------------
  def NormalizeDetectorIndex( self, det_ndx ):
    result = \
      (
      max( 0, min( det_ndx[ 0 ], self.core.ndet - 1 ) ),
      max( 0, min( det_ndx[ 1 ], self.core.nassx - 1 ) ),
      max( 0, min( det_ndx[ 2 ], self.core.nassy - 1 ) )
      )
    return  result
  #end NormalizeDetectorIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizePinColRow()			-
  #----------------------------------------------------------------------
  def NormalizePinColRow( self, pin_rc ):
    result = \
      (
      max( 0, min( pin_rc[ 0 ], self.core.npin - 1 ) ),
      max( 0, min( pin_rc[ 1 ], self.core.npin - 1 ) )
      )
    return  result
  #end NormalizePinColRow


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeStateIndex()			-
  #----------------------------------------------------------------------
  def NormalizeStateIndex( self, state_ndx ):
    return  max( 0, min( state_ndx, len( self.states ) - 1 ) )
  #end NormalizeStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Read()				-
  #----------------------------------------------------------------------
  def Read( self, h5f_param ):
    """Populates the 'core' and 'states' properties
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
"""
    if isinstance( h5f_param, h5py.File ):
      self.h5File = h5f_param
    else:
      self.h5File = h5py.File( str( h5f_param ) )

    self.core = Core( self.h5File )
    self.states = State.ReadAll( self.h5File )

#		-- Assert on states
#		--
    if self.states is None or len( self.states ) == 0:
      raise  Exception( 'No state points could be read' )

    st_group = self.states[ 0 ].GetGroup()

#		-- Assert on pin_powers
#		--
    if 'pin_powers' not in st_group:
      raise  Exception( '"pin_powers" dataset not found' )
    pin_powers_shape = st_group[ 'pin_powers' ].shape

#		-- Special check to get core.npin if pin_volumes
#		-- missing from CORE
    #if self.core.npin == 0 and 'pin_powers' in st_group:
    if self.core.npin == 0:
      self.core.npinx = self.core.npiny = \
      self.core.npin = pin_powers_shape[ 0 ]

#		-- Assert on pin_powers shape
#		--
    if pin_powers_shape[ 0 ] != self.core.npin or \
        pin_powers_shape[ 1 ] != self.core.npin or \
        pin_powers_shape[ 2 ] != self.core.nax or \
        pin_powers_shape[ 3 ] != self.core.nass:
      raise  Exception( 'pin_powers shape inconsistent with npin, nax, and nass' )

#		-- Resolve everything
#		--
    self.dataSetDefs, self.dataSetDefsByName, self.dataSetNames = \
        self._ResolveDataSets( self.core, st_group )

    self.ranges = {}
    self.rangesByStatePt = [ {} ] * len( self.states )

#		-- Special check for pin_factors
#		--
    pin_factors = None
    pin_factors_shape = \
        ( self.core.npiny, self.core.npinx, self.core.nax, self.core.nass )
    for name, group in (
	( 'pin_factors', self.core.GetGroup() ),
	#( 'core.pin_factors', self.h5File )
        ):
      if name in group:
        darray = group[ name ].value
	if darray.shape == pin_factors_shape:
	  pin_factors = darray
	  break
    #end for

    #Andrew, look here
#    if pin_factors is not None:
#      self.averager.pinWeights = pin_factors

#		-- Create derived file and states
#		--
    self.derivedFile, self.derivedStates = \
        self._CreateDerivedH5File( self.states )

#		-- Set up the averager
#		--
    self.averager.load( self.core, self.GetStateDataSet( 0, 'pin_powers' ).value )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadExtraDataSets()			-
  #----------------------------------------------------------------------
#  def ReadExtraDataSets( self ):
#    """
#"""
#    if self.h5ExtraFile is None:
#      self.dataSetNames[ 'extra' ] = []
#      self.extraStates = None
#
#    else:
#      self.dataSetNames[ 'extra' ], self.extraStates = \
#          ExtraState.ReadAll( self.h5ExtraFile )
#  #end ReadExtraDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange()			-
  #----------------------------------------------------------------------
  def _ReadDataSetRange( self, ds_name, state_ndx = -1 ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name, where a prefix of 'extra:' means it's
			an extra dataset
@param  state_ndx	optional 0-based statept index in which to search
"""
    range_min = sys.float_info.min
    range_max = sys.float_info.max

    if ds_name:
      vmin = vmax = float( 'nan' )
      #for i in range( len( self.GetStates() ) ):
      search_range = \
          range( self.GetStatesCount() )  if state_ndx < 0 else \
	  range( state_ndx, state_ndx + 1 )

      for i in search_range:
        st = self.GetState( i )
	derived_st = self.GetDerivedState( i )

	dset = st.GetDataSet( ds_name )
	if dset is None:
	  dset = derived_st.GetDataSet( ds_name )

        if dset:
	  dset_array = dset.value

	  #cur_max = np.amax( dset_array )
	  cur_max = np.nanmax( dset_array )
	  if math.isnan( vmax ) or cur_max > vmax:
	    vmax = cur_max

	  cur_nz = dset_array[ np.nonzero( dset_array ) ]
	  if len( cur_nz ) > 0:
	    #cur_min = np.amin( cur_nz )
	    cur_min = np.nanmin( cur_nz )
	    if math.isnan( vmin ) or cur_min < vmin:
	      vmin = cur_min
	#end if dset
      #end for states

      if not math.isnan( vmin ):
        range_min = vmin
      if not math.isnan( vmax ):
        range_max = vmax
    #end if ds_name

    return  ( range_min, range_max )
  #end _ReadDataSetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange_old()		-
  #----------------------------------------------------------------------
  def _ReadDataSetRange_old( self, ds_name ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name, where a prefix of 'extra:' means it's
			an extra dataset
"""
    range_min = sys.float_info.min
    range_max = sys.float_info.max

    if not ds_name:
      use_states = None
#    elif ds_name.startswith( 'derived:' ):
#      use_states = self.derivedDataMgr.GetStates()
#      use_name = ds_name
#    elif ds_name.startswith( 'extra:' ):
#      use_states = self.GetExtraStates()
#      use_name = ds_name[ 6 : ]
    else:
      use_states = self.GetStates()
      use_name = ds_name

    if use_states is not None:
      vmin = vmax = float( 'nan' )
      for st in use_states:
	if st.HasDataSet( use_name ):
	  cur_ds = st.GetDataSet( use_name ).value
	  cur_max = np.amax( cur_ds )
	  if math.isnan( vmax ) or cur_max > vmax:
	    vmax = cur_max

	  cur_ds_nz = cur_ds[ np.nonzero( cur_ds ) ]
	  if len( cur_ds_nz ) > 0:
	    cur_min = np.amin( cur_ds_nz )
	    if math.isnan( vmin ) or cur_min < vmin:
	      vmin = cur_min
	#end if ds_name in st
      #end for states

      if not math.isnan( vmin ):
        range_min = vmin
      if not math.isnan( vmax ):
        range_max = vmax
    #end if

    return  ( range_min, range_max )
  #end _ReadDataSetRange_old


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.RemoveExtraDataSet()			-
  #----------------------------------------------------------------------
#  def RemoveExtraDataSet( self, full_ds_name ):
#    """Removes the named dataset from all extra states.
#Note the fully-qualified name of a caculated dataset is 'source.name',
#where 'source' is the name of the dataset from which the extra dataset was
#calculated.
#@param  full_ds_name	fully-qualified dataset name
#"""
#    if self.HasExtraDataSet( full_ds_name ):
#      if full_ds_name.startswith( 'core' ):
#        del self.h5ExtraFile[ full_ds_name ]
#
#      else:
#        for st in self.GetExtraStates():
#	  st.RemoveDataSet( full_ds_name )
#	#end for
#      #end if-else
#
#      self.h5ExtraFile.flush()
#    #end if
#  #end RemoveExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ResolveDataSets()			-
  #----------------------------------------------------------------------
  def _ResolveDataSets( self, core, st_group ):
    """Thread-safe method to build three dicts:
ds_defs		dataset definitions by dataset type
ds_defs_by_name	dataset definition by dataset name
ds_names	dict of dataset names by dataset type
		'axial', 'scalar', 'time', plus types defined in DATASET_DEFS
@param  core		core object, cannot be None
@param  st_group	h5py.Group for first state group, cannot be None
@return			ds_defs, ds_defs_by_name, ds_names
"""
    ds_defs = copy.deepcopy( DATASET_DEFS )
    ds_defs_by_name = {}
    ds_names = { 'axial': [], 'scalar': [], 'time': [ 'state' ] }

#		-- Resolve dataset defs
#		--
    for def_name, def_item in ds_defs.iteritems():
      ds_names[ def_name ] = []
      if 'shape' not in def_item:
        def_item[ 'shape' ] = eval( def_item[ 'shape_expr' ] )

      if 'copy_shape_expr' in def_item:
        def_item[ 'copy_shape' ] = eval( def_item[ 'copy_shape_expr' ] )
    #end for

#		-- Walk datasets
#		--
    scalar_shape = ( 1, )

    for cur_name in st_group:
      #if not isinstance( st_group[ cur_name ], h5py.Group ):
      if not (
          isinstance( st_group[ cur_name ], h5py.Group ) or
	  cur_name.startswith( 'copy:' )
	  ):
        cur_shape = st_group[ cur_name ].shape

#			-- Scalar is special case
#			--
        if len( cur_shape ) == 0 or cur_shape == scalar_shape:
	  cat_name = None
	  if cur_name in TIME_DS_NAMES:
	    cat_name = 'time'
	  else:
	    for def_name, def_item in ds_defs.iteritems():
	      if def_name != 'scalar' and \
	          def_item[ 'shape' ] == scalar_shape and \
		  cur_name.startswith( def_item[ 'ds_prefix' ] + '_' ):
	        cat_name = def_name
		break
	    #end for
	  #end if-else on cur_name

	  if cat_name is None:
	    cat_name = 'scalar'
	  ds_names[ cat_name ].append( cur_name )

	  ds_defs_by_name[ cur_name ] = ds_defs.get( cat_name )

#			-- Detector is special case
#			--
	elif cur_name == 'detector_response' and \
	    cur_shape == ds_defs[ 'detector' ][ 'shape' ]:
	  ds_names[ 'detector' ].append( cur_name )
	  ds_names[ 'axial' ].append( cur_name )
	  ds_defs_by_name[ cur_name ] = ds_defs[ 'detector' ]

#			-- Not a scalar
#			--
	else:
	  for def_name, def_item in ds_defs.iteritems():
	    if cur_shape == def_item[ 'shape' ]:
	      ds_names[ def_name ].append( cur_name )
	      ds_defs_by_name[ cur_name ] = def_item

	      if def_item[ 'shape_expr' ].find( 'core.nax' ) >= 0:
	        ds_names[ 'axial' ].append( cur_name )
	      break
	  #end for
        #end if-else on shape

#			-- Old 'axial' check
#			--
#        if ( len( cur_shape ) == 4 and cur_shape[ 2 ] == core.nax ) or \
#	    ( len( cur_shape ) == 2 and cur_shape[ 0 ] == core.ndetax ):
#	  ds_names[ 'axial' ].append( cur_name )
    #end for st_group keys

#		-- Sort names
#		--
    for name in ds_names:
      ds_names[ name ].sort()

    return  ds_defs, ds_defs_by_name, ds_names
  #end _ResolveDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ResolveDerivedDataSet()		-
  #----------------------------------------------------------------------
  def ResolveDerivedDataSet( self, ds_category, derived_label, ds_name ):
    match_name = self.HasDerivedDataSet( ds_category, derived_label, ds_name )
    if not match_name:
      match_name = self._CreateDerivedDataSet( ds_category, derived_label, ds_name )
    return  match_name
#    return \
#        self.derivedDataMgr.CreateDataSet( category, derived_label, ds_name )
  #end ResolveDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.StoreExtraDataSet()			-
  #----------------------------------------------------------------------
#  def StoreExtraDataSet( self, ds_name, data, src_name = 'core', state_ndx = -1 ):
#    """Adds or replaces an extra dataset.
#@param  ds_name		name of dataset to store, required
#@param  data		numpy.ndarray containing data to store, required
#@param  src_name	optional name of source dataset for a time-based
#			dataset when combined with state_ndx, otherwise
#			defaults to 'core'
#@param  state_ndx	optional 0-based state point index when combined with
#			src_name
#@return			h5py.Dataset object added
#
#Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
#if both 'src_name' and 'state_ndx' are specified, the dataset is stored
#using the fully-qualified name in the specified state point (if 'state_ndx'
#is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
#to be 'core', and the dataset is not associated with a state point.
#"""
#    dset = None
#
##		-- Create Extra File if Necessary
##		--
#    if self.h5ExtraFile is None:
#      self._CreateExtraH5File( self )
#
##		-- Assert on required params
##		--
#    if ds_name is None or data is None:
#      raise  Exception( 'ds_name and data are required' )
#
##		-- State point dataset?
##		--
#    st = self.GetExtraState( state_ndx )
#    if src_name != 'core':
##			-- Assert on index
#      if st is None:
#        raise  Exception( '"state_ndx" out of range' )
#
#      qname = src_name + '.' + ds_name
#      #st = self.GetExtraState( state_ndx )
#      st.RemoveDataSet( qname )
#      dset = st.CreateDataSet( qname, data )
#
#      if 'extra' not in self.dataSetNames:
#        self.dataSetNames[ 'extra' ] = []
#      if qname not in self.dataSetNames[ 'extra' ]:
#        self.dataSetNames[ 'extra' ].append( qname )
#        self.dataSetNames[ 'extra' ].sort()
#
#    else:
#      qname = 'core.' + ds_name
#      if qname in self.h5ExtraFile:
#        del self.h5ExtraFile[ qname ]
#
#      dset = self.h5ExtraFile.create_dataset( qname, data = data )
#    #end if-else core or state point
#
#    self.h5ExtraFile.flush()
#    return  dset
#  #end StoreExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ToJson()				-
  #----------------------------------------------------------------------
  def ToJson( self ):
    """Placeholder for some day.
"""
    obj = {}

    if self.core is not None:
      obj[ 'core' ] = self.core.ToJson()
    if self.states is not None:
      obj[ 'states' ] = State.ToJsonAll( self.states )

    return  obj
  #end ToJson


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetAssyIndex()			-
  #----------------------------------------------------------------------
  @staticmethod
  def GetAssyIndex( assy_col, assy_row ):
    """Creates the tuple necessary to reference an assembly in a core dataset
@param  assy_col	0-based column index
@param  assy_row	0-based row index
@return			( assy_row, assy_col )
"""
    return  ( assy_row, assy_col )
  #end GetAssyIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetPinIndex()				-
  #----------------------------------------------------------------------
  @staticmethod
  def GetPinIndex( assy_ndx, axial_level, pin_col, pin_row ):
    """Creates the tuple necessary to reference a pin in an assembly dataset
@param  assy_ndx	0-based assembly index
@param  axial_level	0-based axial level index (not value)
@param  pin_col		0-based pin column index
@param  pin_row		0-based pin row index
@return			( pin_row, pin_col, axial_level, assy_ndx )
"""
    return  ( pin_row, pin_col, axial_level, assy_ndx )
  #end GetPinIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsExtra()				-
  #----------------------------------------------------------------------
  @staticmethod
  def IsExtra( ds_name ):
    """Checks for the 'extra:' prefix.
@return			True if ds_name is an extra dataset, False otherwise
"""
    return  ds_name.startswith( 'extra:' )
  #end IsExtra


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValidObj()				-
  #----------------------------------------------------------------------
  @staticmethod
  def IsValidObj( data, **kwargs ):
    """Checks for non-None data and then calls its IsValid() instance method.
"""
    return  data is not None and data.IsValid( **kwargs )
  #end IsValidObj


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ToCSV()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ToCSV( data, title = None ):
    """Retrieves a normal or extra dataset.
@param  data		numpy.ndarray containing data to dump
@param  title		optional title string or iterable of strings
@return			h5py.Dataset object if found or None
"""
    if data is None:
      cvs_text = None

    else:
      output = cStringIO.StringIO()
      try:
	if hasattr( title, '__iter__' ):
	  for t in title:
	    output.write( str( t ) + '\n' )
	    #output.write( '# ' + str( t ) + '\n' )
	elif title is not None:
          output.write( str( title ) + '\n' )
          #output.write( '# ' + str( title ) + '\n' )

        DataModel._WriteCSV( output, np.transpose( data ) )
	csv_text = output.getvalue()
      finally:
        output.close()

    return  csv_text
  #end ToCSV


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._WriteCSV()				-
  #----------------------------------------------------------------------
  @staticmethod
  def _WriteCSV( fp, data, slice_name = '' ):
    """Recursive routine
@param  fp		file
@param  data		numpy.ndarray containing data to dump
"""
    if len( data.shape ) <= 2:
      if len( data.shape ) == 2:
        data = np.transpose( data )

      if len( slice_name ) > 0:
        fp.write( '## Slice: %s\n' % slice_name )
      np.savetxt( fp, data, fmt = '%.7g', delimiter = ',' )

    else:
      ndx = 0
      for data_slice in data:
	if len( slice_name ) > 0:
	  new_slice_name = slice_name + ',' + str( ndx )
	else:
	  new_slice_name = str( ndx )
        ndx += 1

        DataModel._WriteCSV( fp, data_slice, slice_name = new_slice_name )
      #end for
    #end if-else
  #end _WriteCSV


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.main()				-
  #----------------------------------------------------------------------
  @staticmethod
  def main():
    try:
      if len( sys.argv ) < 2:
        print >> sys.stderr, 'Usage: datamodel.py casl-output-fname'

      else:
        data = DataModel( sys.argv[ 1 ] )
	print str( data )
      #end if-else

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
#end DataModel


#------------------------------------------------------------------------
#	CLASS:		State						-
#------------------------------------------------------------------------
class State( object ):
  """Encapsulates a single state.
  
Fields:
  exposure		exposure time in (?) secs
  group			HDF5 group
  keff			value
  pinPowers		np.ndarray[ npin, npin, nax, nass ],
			( pin_row, pin_col, ax, assy )
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		State.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, index, name = None, state_group = None ):
    """
@param  state_group	HDF5 group for this state
"""
    self.Clear()
    if name is not None and state_group is not None:
      self.Read( index, name, state_group )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		State.__str__()					-
  #----------------------------------------------------------------------
  def __str__( self ):
    return  json.dumps( self.ToJson() )
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		State.Clear()					-
  #----------------------------------------------------------------------
  def Clear( self ):
    self.exposure = -1.0
    self.group = None
    self.index = -1
    self.keff = -1.0
    self.name = None
    self.pinPowers = None
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		State.Check()					-
  #----------------------------------------------------------------------
  def Check( self, core ):
    """
@return			list of error messages
"""
    missing = []

#    if self.exposure < 0.0:
#      missing.append( '%s missing EXPOSURE' % self.name )

#    if self.keff < 0.0:
#      missing.append( '%s missing KEFF' % self.name )

# Redundant, caught in DataModel.Read()
    if self.pinPowers is None:
      missing.append( '%s missing PIN_POWERS' % self.name )
    elif self.pinPowers.shape[ 0 ] != core.npin or \
        self.pinPowers.shape[ 1 ] != core.npin or \
        self.pinPowers.shape[ 2 ] != core.nax or \
        self.pinPowers.shape[ 3 ] != core.nass:
      missing.append( '%s PIN_POWERS shape is not consistent with NPIN, NAX, and NASS' % self.name )

    if 'detector_operable' in self.group and \
        self.group[ 'detector_operable' ].shape[ 0 ] != core.ndet:
      missing.append( '%s DETECTOR_OPERABLE shape is not consistent with NDET' % self.name )

    return  missing
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		State.CreateDataSet()				-
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
  #	METHOD:		State.GetDataSet()				-
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
  #	METHOD:		State.GetGroup()				-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		State.HasDataSet()				-
  #----------------------------------------------------------------------
  def HasDataSet( self, ds_name ):
    """
"""
    return  ds_name is not None and ds_name in self.group
  #end HasDataSet


  #----------------------------------------------------------------------
  #	METHOD:		State.Read()					-
  #----------------------------------------------------------------------
  def Read( self, index, name, state_group ):
    self.Clear()
    self.group = state_group
    self.index = index
    self.name = name

    if state_group is not None and isinstance( state_group, h5py.Group ):
#      exposure_shape = ( -1, )
#      powers_shape = ( -1, )

      if 'exposure' in state_group:
        #self.exposure = state_group[ 'exposure' ].value[ 0 ]
	item = state_group[ 'exposure' ]
        self.exposure = item.value.item() if len( item.shape ) > 0 else item.value

      if 'keff' in state_group:
        #self.keff = state_group[ 'keff' ].value[ 0 ]
	item = state_group[ 'keff' ]
        self.keff = item.value.item() if len( item.shape ) > 0 else item.value

      if 'pin_powers' in state_group:
        self.pinPowers = state_group[ 'pin_powers' ].value
#	powers_shape = state_group[ 'pin_powers' ].shape
    #end if

    if self.exposure < 0.0:
      self.exposure = index
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		State.RemoveDataSet()				-
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


  #----------------------------------------------------------------------
  #	METHOD:		State.ToJson()					-
  #----------------------------------------------------------------------
  def ToJson( self ):
#    obj = \
#      {
#      'exposure': self.exposure.item(),
#      'keff': self.keff.item()
#      }
    obj = {}
    if self.exposure is not None:
      obj[ 'exposure' ] = self.exposure.item()
    if self.keff is not None:
      obj[ 'keff' ] = self.keff.item()

    if self.pinPowers is not None:
      obj[ 'pinPowers' ] = self.pinPowers.tolist()

    return  obj
  #end ToJson

#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		State.CheckAll()				-
  #----------------------------------------------------------------------
  @staticmethod
  def CheckAll( states, core ):
    """
@return			list of error messages
"""
    missing = []

    if states is None or len( states ) == 0:
      missing.append( 'No STATE_nnnn groups found' )

    else:
      missing += states[ 0 ].Check( core )
#      for st in states:
#        missing += st.Check( core )
    #end if-else

    return  missing
  #end CheckAll


  #----------------------------------------------------------------------
  #	METHOD:		State.FindDataSets()				-
  #----------------------------------------------------------------------
  @staticmethod
  def FindDataSets( state_group, core ):
    """
@return			dict of dataset name lists with keys
			  'axial', 'channel', 'detector', 'other', 'pin',
			  'scalar', 'time'
@deprecated  This is now handled in DataModel._ResolveDataSets()
"""
    axial_ds_names = []
    channel_ds_names = []
    detector_ds_names = []
    other_ds_names = []
    pin_ds_names = []
    scalar_ds_names = []
    time_ds_names = [ 'state' ]

    channel_shape = ( core.npin + 1, core.npin + 1, core.nax, core.nass )
    detector_shape = ( core.ndetax, core.ndet )
    pin_shape = ( core.npin, core.npin, core.nax, core.nass )
#    if 'pin_powers' in state_group:
#      powers_shape = state_group[ 'pin_powers' ].shape
    scalar_shape = ( 1, )
#    if 'exposure' in state_group:
#      exposure_shape = state_group[ 'exposure' ].shape

#		-- Check each dataset
#		--
    for k in state_group:
#      if k not in ( 'exposure' ) and \
#          not isinstance( state_group[ k ], h5py.Group ):
      if not isinstance( state_group[ k ], h5py.Group ):
        k_shape = state_group[ k ].shape

        if len( k_shape ) == 0 or k_shape == scalar_shape:
	  if k in TIME_DS_NAMES:
	    time_ds_names.append( k )
	  else:
	    scalar_ds_names.append( k )
        elif k_shape == pin_shape:
	  pin_ds_names.append( k )
        elif k_shape == channel_shape:
	  channel_ds_names.append( k )
        elif k_shape == detector_shape:
	  detector_ds_names.append( k )
	###derived manager
	elif len( k_shape ) == 4:
	  other_ds_names.append( k )

#			-- Special axial check
#			--
        if (len( k_shape ) == 4 and k_shape[ 2 ] == core.nax) or \
	    (len( k_shape ) == 2 and k_shape[ 0 ] == core.ndetax):
          axial_ds_names.append( k )
    #end for state_group keys

    axial_ds_names.sort()
    channel_ds_names.sort()
    detector_ds_names.sort()
    pin_ds_names.sort()
    scalar_ds_names.sort()
    time_ds_names.sort()

    result = \
      {
      'axial': axial_ds_names,
      'channel': channel_ds_names,
      'derived': [],
      'detector': detector_ds_names,
      'other': other_ds_names,
      'pin': pin_ds_names,
      'scalar': scalar_ds_names,
      'time': time_ds_names
      }
    return  result
  #end FindDataSets


  #----------------------------------------------------------------------
  #	METHOD:		State.ReadAll()					-
  #----------------------------------------------------------------------
  @staticmethod
  def ReadAll( h5_group ):
    """
@return			( dataset_names_dict, states )
"""
    #ds_names_dict = {}
    states = []

    missing_count = 0
    n = 1
    while True:
      name = 'STATE_%04d' % n
      if name not in h5_group:
	missing_count += 1
	if missing_count > 5:
          break
      else:
	missing_count = 0
	cur_group = h5_group[ name ]
        states.append( State( n - 1, name, cur_group ) )

#				-- Special hook to fix npin
#				--
#	if core.npin == 0 and 'pin_powers' in cur_group:
#	  core.npin = cur_group[ 'pin_powers'].shape[ 0 ]

#	if n == 1:
#	  ds_names_dict = State.FindDataSets( cur_group, core )
      #end if-else
      n += 1
    #end while

    #return  ( ds_names_dict, states )
    return  states
  #end ReadAll


  #----------------------------------------------------------------------
  #	METHOD:		State.ToJsonAll()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ToJsonAll( states ):
    json_arr = []
    for state in states:
      json_arr.append( state.ToJson() )

    return  json_arr
  #end ToJsonAll
#end State


#------------------------------------------------------------------------
#	CLASS:		DerivedState					-
#------------------------------------------------------------------------
class DerivedState( State ):
  """Special State for derived datasets.
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DerivedState.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, index, name, state_group ):
    """
@param  index		0-based state point index
@param  name		name, which can clean from the group
@param  state_group	HDF5 group for this state
"""
    #super( DerivedState, self ).__init__( index, name, state_group )
    self.index = index
    self.name = name
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

#end DerivedState


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataModel.main()
