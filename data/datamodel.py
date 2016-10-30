#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel.py					-
#	HISTORY:							-
#		2016-10-30	leerw@ornl.gov				-
#	  Removing dependence on pin_powers.
#		2016-10-26	leerw@ornl.gov				-
#	  Using logging.
#		2016-10-24	leerw@ornl.gov				-
#	  Added NAN constant to save a picosecond or two.
#		2016-10-22	leerw@ornl.gov				-
#	  Added Core._InferCoreLabels{Simply,Smartly}(), calling the
#	  former in Core.ReadImpl().
#		2016-10-20	leerw@ornl.gov				-
#	  Added first attempt at GetFactors().
#		2016-10-18	leerw@ornl.gov				-
#	  Modified ReadDataSetAxialValues() and ReadDataSetValues2() to
#	  accept node_addrs params, no longer gleaning node addresses from
#	  sub_addrs.
#		2016-10-17	leerw@ornl.gov				-
#	  Migrating to new approach where all dataset types, including
#	  derived types, are "primary", meaning they are presented along
#	  with non-derived datasets in menus and such.
#		2016-10-13	leerw@ornl.gov				-
#	  Fixed "ds_prefix" values for channel derived types in
#	  DATASET_DEFS to avoid conflicts with pin derived types.
#		2016-10-06	leerw@ornl.gov				-
#	  Modified _ResolveDataSets() to allow shape clashes and try to
#	  resolve them by the prefix names.
#		2016-10-01	leerw@ornl.gov				-
#	  Added DataModel.GetNodeAddr() and GetSubAddrFromNode().
#		2016-09-30	leerw@ornl.gov				-
#	  Added DataModel.nodeFactors.
#		2016-09-29	leerw@ornl.gov				-
#	  Adding derived channel DATASET_DEFS.
#		2016-09-20	leerw@ornl.gov				-
#	  Made 'ds_prefix' in DATASET_DEFS entries a comma-delimited
#	  list.
#		2016-09-14	leerw@ornl.gov				-
#	  Setting DataModel.pinFactors from averager.
#	  Starting to address channel weights and derived datasets.
#		2016-09-03	leerw@ornl.gov				-
#	  Checking for existence of time datasets in all state points.
#		2016-08-30	leerw@ornl.gov				-
#	  Renamed pin:core data type to pin:radial_assembly, and added
#	  new pin:core.
#		2016-08-20	leerw@ornl.gov				-
#	  Fixed bug in FindMultiDataSetMaxValue() finding axial value for
#	  a fixed_detector dataset and setting 'assembly_addr' in results.
#		2016-08-18	leerw@ornl.gov				-
#	  Redefining axial levels in preparation for multiple files.
#	  Renaming detectorMeshCenters to proper detectorMesh
#		2016-08-15	leerw@ornl.gov				-
#	  State/event refactoring.
#		2016-08-02	leerw@ornl.gov				-
#	  Merging colrow events.
#		2016-07-11	leerw@ornl.gov				-
#	  Fixed bug in DataModel.CreateAxialValue() where the core/pin
#	  was based on axialMesh instead of axialMeshCenters.
#		2016-07-09	leerw@ornl.gov				-
#	  Fixed bug in DataModel.ReadDataSetValues2() where 'state' was
#	  not processed correctly.
#		2016-07-08	leerw@ornl.gov				-
#	  Converting indexes from np.int64 to int.
#	  Fixed bug in DataModel._ResolveDataSets() where detector and
#	  fixed_detector types were not added as axial datasets.
#		2016-07-07	leerw@ornl.gov				-
#	  Renaming "vanadium" to "fixed_detector".
#		2016-07-06	leerw@ornl.gov				-
#	  Fixed bug in DataModel.CreateDetectorIndex().
#		2016-06-16	leerw@ornl.gov				-
#	  Implemented ReadDataSetValues2() for faster performance.
#	  Fixed small bug in ReadDataSetAxialValues().
#		2016-06-07	leerw@ornl.gov				-
#	  Fixed ReadDataSetAxialValues() handling of detector datasets.
#		2016-06-04	leerw@ornl.gov				-
#	  Fixed pin:core data definition.
#	  Added CreatePinLabel().
#		2016-05-31	leerw@ornl.gov				-
#	  Added DataModel.ReadDataSet{Axial}Values().
#		2016-05-25	leerw@ornl.gov				-
#	  Special "vanadium" dataset type.
#	  Fixed handling of "detector_mesh" to get detectorMeshCenters.
#	  Added DataModel.CreateEmptyAxialValue() static method.
#		2016-04-28	leerw@ornl.gov				-
# 	  Added DataModel.ToAddrString().
#		2016-04-25	leerw@ornl.gov				-
#	  Added Normalize{Channel,Pin}ColRows() (for aux lists).
#		2016-04-23	leerw@ornl.gov				-
#	  Added GetDefaultScalarDataSet().
#	  In _ResolveDataSets() added hook to define core.detectorMap as
#	  core.coreMap if it wasn't explicitly provided.
#		2016-04-20	leerw@ornl.gov				-
#	  Added DataModel.derivedLabelsByType to cache results for
#	  GetDerivedLabels().
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
import bisect, copy, cStringIO, h5py, logging, json, math, os, sys, \
    tempfile, threading, traceback
import numpy as np
import pdb

#from deriveddata import *
from event.event import *


#------------------------------------------------------------------------
#	CONST:		AVERAGER_DEFS					-
# Dictionary of averager implementations keyed by dataset type.  In theory
# there should be an entry here for every 'avg_method' key in a DATASET_DEFS
# entry below, but we might hard-code 'pin' as a default.
#------------------------------------------------------------------------
AVERAGER_DEFS = \
  {
  'channel': 'data.channel_averages.Averages',
  'pin': 'data.pin_averages.Averages'
  }


#------------------------------------------------------------------------
#	CONST:		COL_LABELS					-
# In-order labels for core columns.
#------------------------------------------------------------------------
COL_LABELS = \
  (
    'R', 'P', 'N', 'M', 'L', 'K', 'J', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A'
  )

#{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}


#------------------------------------------------------------------------
#	CONST:		DATASET_DEFS					-
# Dictionary of dataset category/type definitions by type name.
# The naming scheme for derived types is now just a ':' prefix for derived
# types.  Whether or not a type can be derived from a dataset is determined
# by the keys in the 'avg_method' value.
#
# All types have keys:
#	label		- name used in displays
#	shape_expr	- shape expression used to match datasets against to
#			  determine if they are of the type, where 'core'
#			  references the Core instance
#	type		- echo of the type name key
#
# Derived types have keys:
#	avg_method	- dictionary keyed by category/type of averager
#			  methods, where '*' is default
#	copy_expr	- lhs expression for numpy array assignment
#			  (should be all ':' and '0' entries)
#	copy_shape_expr	- tuple defining 4D shape of copy, with '1' in
#			  flattened dimensions
#	ds_prefix	- tuple of prefix names to use in matching datasets
#			  read from the VERAOutput file
#------------------------------------------------------------------------
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

  'fixed_detector':
    {
    'label': 'fixed_detector',
    'shape_expr': '( core.nfdetax, core.ndet )',
    'type': 'fixed_detector'
    },

  'pin':
    {
    'label': 'pin',
    'shape_expr': '( core.npiny, core.npinx, core.nax, core.nass )',
    'type': 'pin'
    },

  ':assembly':
    {
    'avg_method':
      {
      'channel': 'calc_channel_assembly_avg',
      'pin': 'calc_pin_assembly_avg'
      },
    'copy_expr': '[ 0, 0, :, : ]',
    'copy_shape_expr': '( 1, 1, core.nax, core.nass )',
    'ds_prefix': ( 'asy', 'assembly' ),
    'factors': 'assemblyWeights',
    'label': 'assembly',  # '3D asy'
    'shape_expr': '( core.nax, core.nass )',
    'type': ':assembly'
    },

  ':axial':
    {
    'avg_method':
      {
      'channel': 'calc_channel_axial_avg',
      'pin': 'calc_pin_axial_avg'
      },
    'copy_expr': '[ 0, 0, :, 0 ]',
    'copy_shape_expr': '( 1, 1, core.nax, 1 )',
    'ds_prefix': ( 'axial', ),
    'factors': 'axialWeights',
    'label': 'axial',
    'shape_expr': '( core.nax, )',
    'type': ':axial'
    },

  ':chan_radial':
    {
    #'avg_method': 'calc_channel_radial_avg',
    'avg_method': { 'channel': 'calc_channel_radial_avg' },
    'copy_expr': '[ :, :, 0, : ]',
    'copy_shape_expr': '( core.npiny + 1, core.npinx + 1, 1, core.nass )',
    'ds_prefix': ( 'radial', 'ch_radial' ),
    'label': 'chan_radial',  # '2D pin'
    'shape_expr': '( core.npiny + 1, core.npinx + 1, core.nass )',
    'type': ':chan_radial'
    },

  ':core':
    {
    'avg_method':
      {
      'channel': 'calc_channel_core_avg',
      'pin': 'calc_pin_core_avg'
      },
    'copy_expr': '[ 0, 0, 0, 0 ]',
    'copy_shape_expr': '( 1, 1, 1, 1 )',
    'ds_prefix': ( 'core', ),
    'factors': 'coreWeights',
    'label': 'core',
    'shape_expr': '( 1, )',
    'type': ':core'
    },

  ':node':
    {
    'avg_method':
      {
      'pin': 'calc_pin_node_avg'
      },
    'copy_expr': '[ 0, :, :, : ]',
    'copy_shape_expr': '( 1, 4, core.nax, core.nass )',
    'ds_prefix': ( 'node', ),
    'factors': 'nodeWeights',
    'label': 'node',
    'shape_expr': '( 4, core.nax, core.nass )',
    'type': ':node'
    },

  ':radial':
    {
    'avg_method':
      {
      'pin': 'calc_pin_radial_avg'
      },
    'copy_expr': '[ :, :, 0, : ]',
    'copy_shape_expr': '( core.npiny, core.npinx, 1, core.nass )',
    'ds_prefix': ( 'radial', ),
    'factors': 'radialWeights',
    'label': 'radial',  # '2D pin'
    'shape_expr': '( core.npiny, core.npinx, core.nass )',
    'type': ':radial'
    },

  ':radial_assembly':
    {
    'avg_method':
      {
      'pin': 'calc_pin_radial_assembly_avg'
      },
    'copy_expr': '[ 0, 0, 0, : ]',
    'copy_shape_expr': '( 1, 1, 1, core.nass )',
    'ds_prefix': ( 'radial_asy', 'radial_assembly' ),
    'factors': 'radialAssemblyWeights',
    'label': 'radial assembly',  # '2D assy'
    'shape_expr': '( core.nass, )',
    'type': ':radial_assembly'
    },

  ':radial_node':
    {
    'avg_method':
      {
      'pin': 'calc_pin_radial_node_avg'
      },
    'copy_expr': '[ 0, :, 0, : ]',
    'copy_shape_expr': '( 1, 4, 1, core.nass )',
    'ds_prefix': ( 'radial_node', ),
    'factors': 'radialNodeWeights',
    'label': 'radial node',
    'shape_expr': '( 4, core.nass )',
    'type': ':radial_node'
    },

  'scalar':
    {
    'label': 'scalar',
    'shape_expr': '( 1, )',
    'type': 'scalar'
    },

#  'vanadium':
#    {
#    'label': 'vanadium',
#    'shape_expr': '( core.nvanax, core.ndet )',
#    'type': 'vanadium'
#    },
  }


#------------------------------------------------------------------------
#	CONST:		NAN						-
# NaN value.
#------------------------------------------------------------------------
NAN = float( 'NaN' )


#------------------------------------------------------------------------
#	CONST:		TIME_DS_NAMES					-
# Set of dataset names we recognize as "time" datasets.  We always add
# 'state', the statepoint index, as a time alternative.
#------------------------------------------------------------------------
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
  detectorMesh		np.ndarray of center-of-mesh values
  group			HDF5 group
  nass			number of full core assemblies
  nassx			number of core assembly columns
  nassy			number of core assembly rows
  nax			number of axial levels
  ndet			number of detectors
  ndetax		number of detector axial levels
  nfdetax		number of fixed_detector axial levels
  npin			number of pins in each assembly
  pinVolumes		np.ndarray, row-major, origin top,left
  pinVolumesSum		sum of all pin volumes
  fixedDetectorMesh		np.ndarray of mesh values
  fixedDetectorMeshCenters	np.ndarray of center-of-mesh values
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
    elif self.pinVolumes.shape[ 0 ] != self.npiny or \
        self.pinVolumes.shape[ 1 ] != self.npinx or \
        self.pinVolumes.shape[ 2 ] != self.nax or \
        self.pinVolumes.shape[ 3 ] != self.nass:
      missing.append( 'PIN_VOLUMES shape is not consistent with NPIN, NAX, and NASS' )

    if self.npin <= 0:
      missing.append( 'NPIN le 0' )
    if self.nass <= 0:
      missing.append( 'NASS le 0' )
    if self.nax <= 0:
      missing.append( 'NAX le 0' )

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
    self.detectorMesh = None
    self.group = None
    self.nass = 0
    self.nassx = 0
    self.nassy = 0
    self.nax = 0
    self.ndet = 0
    self.ndetax = 0
    self.nfdetax = 0
    self.npin = 0
    self.npinx = 0
    self.npiny = 0
    self.pinVolumes = None
    self.pinVolumesSum = 0.0
    self.ratedFlow = 0
    self.ratedPower = 0
    self.fixedDetectorMesh = None
    self.fixedDetectorMeshCenters = None
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
  #	METHOD:		Core.CreatePinLabel()				-
  #----------------------------------------------------------------------
  def CreatePinLabel( self,
      pin_col, pin_row,
      assy_ndx = -1, assy_col = -1, assy_row = -1
      ):
    """Creates a label string.
@param  pin_col		0-based column index
@param  pin_row		0-based row index
@param  assy_ndx	0-based assembly index
@param  assy_col	0-based column index
@param  assy_row	0-based row index
@return			"N(C-R)(c,r)"
"""
    result = '(?)'
    if assy_ndx >= 0 and assy_col >= 0 and assy_row >= 0 and \
        self.coreLabels is not None and len( self.coreLabels ) >= 2:
      result = '%d(%s-%s)' % ( \
          assy_ndx + 1,
          self.coreLabels[ 0 ][ assy_col ], self.coreLabels[ 1 ][ assy_row ]
	  )

    if pin_col >= 0 and pin_row >= 0:
      result += '(%d,%d)' % ( pin_col + 1, pin_row + 1 )

    return  result
  #end CreatePinLabel


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
@return			'apitch' value or a default of 21.5
"""
    return  21.5  if self.apitch == 0.0 else  self.apitch
  #end GetAssemblyPitch


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetColLabel()				-
  #----------------------------------------------------------------------
  def GetColLabel( self, from_ndx, to_ndx = -1 ):
    """Gets the column label or range of labels.
Calls _GetCoreLabel().
"""
    return  self.GetCoreLabel( 0, from_ndx, to_ndx )
  #end GetColLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetCoreLabel()				-
  #----------------------------------------------------------------------
  def GetCoreLabel( self, col_or_row, from_ndx, to_ndx = -1 ):
    """Gets the label or range of labels.
@param  col_or_row	0 for column labels, 1 for row labels
@param  from_ndx	required 0-based inclusive column index
@param  to_ndx		optional 0-based exclusive index for a range
@return			either a single label string or a list of to_ndx
			is specified and is gt from_ndx
"""
    #col_or_row = min( 1, max( 0, col_or_row ) )
    result = ''
    if from_ndx >= 0 and from_ndx < len( self.coreLabels[ col_or_row ] ):
      if to_ndx > from_ndx:
        to_ndx = min( to_ndx, len( self.coreLabels[ col_or_row ] ) )
	result = [
	    self.coreLabels[ col_or_row ][ i ]
	    for i in xrange( from_ndx, to_ndx )
	    ]
      else:
        result = self.coreLabels[ col_or_row ][ from_ndx ]
    #end if from_ndx is valid

    return  result
  #end GetCoreLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetGroup()					-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetRowLabel()				-
  #----------------------------------------------------------------------
  def GetRowLabel( self, from_ndx, to_ndx = -1 ):
    """Gets the row label or range of labels.
Calls _GetCoreLabel().
"""
    return  self.GetCoreLabel( 1, from_ndx, to_ndx )
  #end GetRowLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core._InferCoreLabelsSimply()			-
  #----------------------------------------------------------------------
  def _InferCoreLabelsSimply( self, core_group, in_core_group ):
    """Assumes 'xlabel' dataset if specified provides column labels
left-to-right, and 'ylabel' if provided gives row labels top-to-bottom.
@param  core_group	CORE h5py.Group
@param  in_core_group	INPUT/CASEID/CORE h5py.Group
@return			core_labels, row_labels
"""
    item = self._FindInGroup( 'xlabel', core_group, in_core_group )
    if item is not None and item.shape[ 0 ] == self.nassx:
      col_labels = [
          item[ i ].replace( ' ', '' )
	  for i in xrange( self.nassx )
	  ]
      # Assume left-to-right
      #col_labels = col_labels[ ::-1 ]
    else:
      col_labels = list( COL_LABELS )
      while self.nassx > len( col_labels ):
        col_labels.insert( 0, chr( ord( col_labels[ 0 ] ) + 1 ) )
      col_labels = col_labels[ -self.nassx : ]

    # Rows
    item = self._FindInGroup( 'ylabel', core_group, in_core_group )
    if item is not None and item.shape[ 0 ] == self.nassy:
      row_labels = [
          item[ i ].replace( ' ', '' )
	  for i in xrange( self.nassy )
	  ]
      # Assume top-to-bottom
    else:
      row_labels = [ '%d' % x for x in xrange( 1, self.nassy + 1 ) ]

    return  col_labels, row_labels
  #end _InferCoreLabelsSimply


  #----------------------------------------------------------------------
  #	METHOD:		Core._InferCoreLabelsSmartly()			-
  #----------------------------------------------------------------------
  def _InferCoreLabelsSmartly( self, core_group, in_core_group ):
    """Assumes 'xlabel' and 'ylabel' datasets, if specified, can provide
column or row labels in any order.  Alphabetic and numeric labels are assumed
to be column and row labels, respectively, and the order is forced such that
'A' is rightmost and '1' is topmost.
@param  core_group	CORE h5py.Group
@param  in_core_group	INPUT/CASEID/CORE h5py.Group
@return			core_labels, row_labels
"""
    col_labels = row_labels = None

#		-- Search in groups
#		--
    for name in ( 'xlabel', 'ylabel' ):
      item = self._FindInGroup( name, core_group, in_core_group )
      if item is not None and item.shape[ 0 ] > 0:
        first_value = item[ 0 ].replace( ' ', '' )

#				-- Column?
	#if first_value.isalpha() and item.shape[ 0 ] == self.nassx:
	if first_value.isalpha():
	  if item.shape[ 0 ] == self.nassx:
	    col_labels = [
	        item[ i ].replace( ' ', '' )
	        for i in xrange( self.nassx )
	        ]
#					-- Reverse if necessary
	    if col_labels[ 0 ] < col_labels[ -1 ]:
	      col_labels = col_labels[ ::-1 ]

#				-- Row?
	else:
	  if item.shape[ 0 ] == self.nassy:
	    row_labels = [
	        item[ i ].replace( ' ', '' )
	        for i in xrange( self.nassy )
	        ]
#					-- Reverse if necessary
	    if row_labels[ 0 ] > row_labels[ -1 ]:
	      row_labels = row_labels[ ::-1 ]
      #if item not empty
    #end for name

#		-- Default col_labels if necessary
#		--
    if col_labels is None:
      col_labels = list( COL_LABELS )
      while self.nassx > len( col_labels ):
        col_labels.insert( 0, chr( ord( col_labels[ 0 ] ) + 1 ) )
      col_labels = col_labels[ -self.nassx : ]
    #end if col_labels is None

#		-- Default row_labels if necessary
#		--
    if row_labels is None:
      row_labels = [ '%d' % x for x in xrange( 1, self.nassy + 1 ) ]

    return  col_labels, row_labels
  #end _InferCoreLabelsSmartly


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
    #elif not isinstance( axial_mesh_item.value, np.ndarray ):
      #missing.append( '"axial_mesh" dataset is not an array' )

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
    self.nass = int( np.amax( self.coreMap ) )

#		-- Core Labels
#		--
    self.coreLabels = self._InferCoreLabelsSimply( core_group, in_core_group )
    #self#.coreLabels = self._InferCoreLabelsSmartly( core_group, in_core_group )

#		-- Other datasets: apitch
#		--
    item = self._FindInGroup( 'apitch', core_group, in_core_group )
    if item is not None:
      self.apitch = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      #self.apitch = item.value.item() if len( item.shape ) > 0 else item.value

#		-- Other datasets: axial_mesh
#		--
    #item = self._FindInGroup( 'axial_mesh', core_group, in_core_group )
    #if item is not None:
    self.axialMesh = axial_mesh_item.value
    self.nax = self.axialMesh.shape[ 0 ] - 1
#			-- Numpy magic
    t = np.copy( axial_mesh_item.value )
    t2 = np.r_[ t, np.roll( t, -1 ) ]
    self.axialMeshCenters = np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]

#		-- Other datasets: core_sym
#		--
    item = self._FindInGroup( 'core_sym', core_group, in_core_group )
    if item is None:
      self.coreSym = 1
    else:
      self.coreSym = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      #self.coreSym = item.value.item() if len( item.shape ) > 0 else item.value

#		-- Other datasets: nass
#		--
    item = self._FindInGroup( 'nass', core_group, in_core_group )
    if item is not None:
      self.nass = item[ 0 ] if len( item.shape ) > 0 else item[ () ]

#		-- Other datasets: nax
#		--
    item = self._FindInGroup( 'nax', core_group, in_core_group )
    if item is not None:
      self.nax = item[ 0 ] if len( item.shape ) > 0 else item[ () ]

#		-- Other datasets: npin{,x,y}
#		--
    item = self._FindInGroup( 'npin', core_group, in_core_group )
    if item is not None:
      self.npin = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      self.npinx = self.npiny = self.npin

    item = self._FindInGroup( 'npinx', core_group, in_core_group )
    if item is not None:
      self.npinx = item[ 0 ] if len( item.shape ) > 0 else item[ () ]

    item = self._FindInGroup( 'npiny', core_group, in_core_group )
    if item is not None:
      self.npiny = item[ 0 ] if len( item.shape ) > 0 else item[ () ]


#		-- Other datasets: pin_volumes
#		--
    self.pinVolumesSum = 0
    item = self._FindInGroup( 'pin_volumes', core_group, in_core_group )
    if item is not None:
      self.pinVolumes = item.value
      self.pinVolumesSum = np.sum( item.value )
      if self.npin == 0:
        self.npin = self.pinVolumes.shape[ 0 ]  # and [ 1 ]
        self.npiny = self.pinVolumes.shape[ 0 ]
        self.npinx = self.pinVolumes.shape[ 1 ]
      if self.nax == 0:
        self.nax = self.pinVolumes.shape[ 2 ]
      if self.nass == 0:
        self.nass = self.pinVolumes.shape[ 3 ]

    item = self._FindInGroup( 'rated_flow', core_group, in_core_group )
    if item is not None:
      self.ratedFlow = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      #self.ratedFlow = item.value.item() if len( item.shape ) > 0 else item.value

    item = self._FindInGroup( 'rated_power', core_group, in_core_group )
    if item is not None:
      self.ratedPower = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      #self.ratedPower = item.value.item() if len( item.shape ) > 0 else item.value

#		-- Optional detector_map
#		--
    #xxxx if no detector_map, assume each assembly is a detector
    item = self._FindInGroup( 'detector_map', core_group, in_core_group )
    #if item is not None and item.value.shape == self.coreMap.shape:
    if item is not None:
      self.detectorMap = item.value
      self.ndet = int( np.amax( item.value ) )
    else:
      self.detectorMap = self.coreMap
      self.ndet = self.nass
    #end if detector_map

#		XXXX Check detector_response first for ndet and ndetax
#		-- Optional detector_mesh
#		-- (was inside detector_map if-block)
#		-- (starts at top)
    item = self._FindInGroup( 'detector_mesh', core_group )
    if item is not None:
#				-- Detector meshes are not centers
      t = np.copy( item.value )
      self.detectorMesh = t
      self.ndetax = item.shape[ 0 ]
    else:
      self.detectorMesh = self.axialMeshCenters
      self.ndetax = self.nax
    #end if detector_mesh

#			-- Optional fixedDetector_axial_mesh
#			--
    #item = self._FindInGroup( 'vanadium_axial_mesh', core_group )
    item = self._FindInGroup( 'fixed_detector_mesh', core_group )
    if item is not None:
      self.fixedDetectorMesh = item.value
#				-- Numpy magic for centers
      t = np.copy( item.value )
      t2 = np.r_[ t, np.roll( t, -1 ) ]
      self.fixedDetectorMeshCenters = \
          np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]
      self.nfdetax = item.shape[ 0 ] - 1
    #end if fixed_detector_mesh

#		-- Infer missing dimensions
#		--
    if self.nass == 0:
      self.nass = int( np.amax( self.coreMap ) )

    if self.npin == 0 and input_group is not None:
      num_pins_ds = input_group.get( 'CASEID/ASSEMBLIES/Assembly_1/num_pins' )
      if num_pins_ds is not None:
        self.npin = num_pins_ds[ 0 ] \
	    if len( num_pins_ds.shape ) > 0 else \
	    num_pins_ds[ () ]
        #self.npin = num_pins_ds.value.item() if len( num_pins_ds.shape ) > 0 else num_pins_ds.value
	self.npinx = self.npin
	self.npiny = self.npin
        #self.npin = num_pins_ds.value[ 0 ]
    #end if

#		-- Assert NAX match b/w axial_mesh and pin_volumes
#		--  Rely on call to Check() after DataModel.Read()
#    if self.nax > 0 and self.pinVolumes is not None and \
#        self.pinVolumes.shape[ 2 ] != self.nax:
#      raise Exception( 'NAX dimension mismatch between "axial_mesh" and "pin_volumes"' )
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
    if self.detectorMesh is not None:
      obj[ 'detectorMesh' ] = self.detectorMesh.tolist()
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

Events:
  newDataSet		callable( new_ds_name )
			listener.OnNewDataSet( new_ds_name )
  newFile		callable( new_file_name )
			listener.OnNewFile( new_file_name )

Properties:
  averagers		dict by category of average calculators
  channelFactors	channel weight factors
  			( npiny + 1, npinx + 1, nax, nass )
  core			Core
  #dataSetChangeEvent	event.Event object
  dataSetDefs		dict of dataset definitions
  dataSetDefsByName	reverse lookup of dataset definitions by ds_name
  dataSetDefsLock	threading.RLock for dataSetDefs and dataSetDefsByName
  dataSetNames		dict of dataset names by category
			  ( 'channel', 'derived', 'detector',
			    'fixed_detector', 'pin', 'scalar' )
  dataSetNamesVersion	counter to indicate changes
  derivableTypesByLabel	map of base types by derived type label,
  derivedFile		h5py.File for derived data
  derivedLabelsByType	map of labels by category, lazily populated
  derivedStates		list of DerivedState instances
  h5File		h5py.File
  listeners		map of listeners by event type
  maxAxialValue		maximum axial value (cm) 
  nodeFactors		node weight factors ( 1, 4, nax, nass )
  pinFactors		pin weight factors ( npiny, npinx, nax, nass )
  ranges		dict of ranges ( min, max ) by dataset
  rangesByStatePt	list by statept index of dicts by dataset of ranges 
  rangesLock		threading.RLock for ranges dict
  states		list of State instances
  			lazily populated
"""


#		-- Constants
#		--

  DEFAULT_range = ( -sys.float_info.max, sys.float_info.max )


#		-- Class Attributes
#		--

  dataSetNamesVersion_ = 0


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
    self.averagers = {}
    self.logger = logging.getLogger( 'data' )

#		-- Instantiate averagers
#		--
#    for cat, class_path in (
#	( 'pin', DERIVED_PIN_CALCULATOR_CLASS ),
#	( 'channel', DERIVED_CHANNEL_CALCULATOR_CLASS )
#        ):
    for cat, class_path in AVERAGER_DEFS.iteritems():
      module_path, class_name = class_path.rsplit( '.', 1 )
      try:
        module = __import__( module_path, fromlist = [ class_name ] )
        cls = getattr( module, class_name )
        self.averagers[ cat ] = cls()
      except AttributeError:
        raise Exception(
	    'DataModel error: Class "%s" not found in module "%s"' %
	    ( class_name, module_path )
	    )
      except ImportError:
        raise Exception(
	    'DataModel error: Module "%s" could not be imported' % module_path
	    )
    #end for cat, class_name

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

      #self.dataSetNamesVersion += 1
      DataModel.dataSetNamesVersion_ += 1
      self.FireEvent( 'newDataSet', ds_name )
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
    self.dataSetDefs = {}
    self.dataSetDefsByName = {}
    self.dataSetNames = []
    #self.dataSetNamesVersion = 0
    self.derivableTypesByLabel = {}
    self.derivedFile = None
    self.derivedLabelsByType = {}
    self.derivedStates = None
    self.h5File = None
    self.listeners = { 'newDataSet': [], 'newFile': [] }
    self.ranges = {}
    self.rangesByStatePt = []
    self.states = []

    DataModel.dataSetNamesVersion_ += 1
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.AddListener()				-
  #----------------------------------------------------------------------
  def AddListener( self, event_name, listener ):
    """
@param  event_name	either 'newDataSet' or 'newFile'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener not in self.listeners[ event_name ]:
        self.listeners[ event_name ].append( listener )
    #end if event_name
  #end AddListener


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
  #	METHOD:		DataModel.CreateAssemblyAddr()			-
  #----------------------------------------------------------------------
  def CreateAssemblyAddr( self, col, row ):
    """Creates tuple from the column and row indexes.
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( assy_ndx, col, row )
"""
    return \
        ( self.core.coreMap[ row, col ], col, row ) \
	if self.core is not None else \
	( -1, -1, -1 )
  #end CreateAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAssemblyAddrFromIndex()		-
  #----------------------------------------------------------------------
  def CreateAssemblyAddrFromIndex( self, assy_ndx ):
    """Creates tuple from the column and row indexes.
@param  assy_ndx	0-based assembly index
@return			0-based ( assy_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    if self.core is not None:
      places = np.argwhere( self.core.coreMap == assy_ndx + 1 )
      if len( places ) > 0:
        place = places[ -1 ]
        result = ( assy_ndx, int( place[ 1 ] ), int( place[ 0 ] ) )
    return  result
  #end CreateAssemblyAddrFromIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAxialValue()			-
  #----------------------------------------------------------------------
  def CreateAxialValue( self, **kwargs ):
    """Create from 'core_ndx', 'detector_ndx', 'fixed_detector_ndx', or 'value'
values.
Parameters:
  cm			axial value in cm
  core_ndx		0-based core axial index
  detector_ndx		0-based detector axial index
  fixed_detector_ndx	0-based fixed_detector axial index
  pin_ndx		0-based core axial index, alias for 'core_ndx'
  value			axial value in cm, alias for 'cm'
@return			( axial_cm, core_ndx, detector_ndx,
			  fixed_detector_ndx )
"""
    core_ndx = -1
    det_ndx = -1
    fdet_ndx = -1
    axial_cm = 0.0

    if self.core is None:
      pass

    elif 'cm' in kwargs:
      axial_cm = kwargs[ 'cm' ]
      #core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )
      core_ndx = self.FindListIndex( self.core.axialMeshCenters, axial_cm )
      det_ndx = self.FindListIndex( self.core.detectorMesh, axial_cm )
      fdet_ndx = self.FindListIndex( self.core.fixedDetectorMeshCenters, axial_cm )

    elif 'detector_ndx' in kwargs:
      det_ndx = max( 0, min( kwargs[ 'detector_ndx' ], self.core.ndetax - 1 ) )
      axial_cm = self.core.detectorMesh[ det_ndx ]
      #core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )
      core_ndx = self.FindListIndex( self.core.axialMeshCenters, axial_cm )
      fdet_ndx = self.FindListIndex( self.core.fixedDetectorMeshCenters, axial_cm )

    elif 'core_ndx' in kwargs:
      core_ndx = max( 0, min( kwargs[ 'core_ndx' ], self.core.nax - 1 ) )
      axial_cm = self.core.axialMeshCenters[ core_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMesh, axial_cm )
      fdet_ndx = self.FindListIndex( self.core.fixedDetectorMeshCenters, axial_cm )

    elif 'pin_ndx' in kwargs: # huh?
      core_ndx = max( 0, min( kwargs[ 'pin_ndx' ], self.core.nax - 1 ) )
      axial_cm = self.core.axialMeshCenters[ core_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMesh, axial_cm )
      fdet_ndx = self.FindListIndex( self.core.fixedDetectorMeshCenters, axial_cm )

    elif 'value' in kwargs:
      axial_cm = kwargs[ 'value' ]
      #core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )
      core_ndx = self.FindListIndex( self.core.axialMeshCenters, axial_cm )
      det_ndx = self.FindListIndex( self.core.detectorMesh, axial_cm )
      fdet_ndx = self.FindListIndex( self.core.fixedDetectorMeshCenters, axial_cm )

    elif 'fixed_detector_ndx' in kwargs:
      fdet_ndx = max( 0, min( kwargs[ 'fixed_detector_ndx' ], self.core.nfdetax - 1 ) )
      axial_cm = self.core.fixedDetectorMeshCenters[ fdet_ndx ]
      #core_ndx = self.FindListIndex( self.core.axialMesh, axial_cm )
      core_ndx = self.FindListIndex( self.core.axialMeshCenters, axial_cm )
      det_ndx = self.FindListIndex( self.core.detectorMesh, axial_cm )

    return  ( axial_cm, core_ndx, det_ndx, fdet_ndx )
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
    #core = self.core

    if len( self.states ) > 0:
#			-- First, find dataset definition
#			--
      ddef = None
      der_names = \
          self._CreateDerivedNames( ds_category, derived_label, ds_name )
      if der_names:
	ddef = self.GetDataSetDef( der_names[ 0 ] )
        #ddef = self.dataSetDefs.get( der_names[ 0 ] )

#			-- Second, get averager and find method name
#			--
#      if ds_category in self.averagers and \
#          ddef and 'avg_method' in ddef and \
#	  hasattr( self.averagers[ ds_category ], ddef[ 'avg_method' ] ):
      avg_method_name = None
      averager = self.averagers.get( ds_category )
      if ddef and averager and \
          'avg_method' in ddef and ds_category in ddef[ 'avg_method' ]:
        avg_method_name = ddef[ 'avg_method' ][ ds_category ]

#			-- Third, get average method reference
#			--
      if avg_method_name and hasattr( averager, avg_method_name ):
	derived_name = der_names[ 1 ]

	try:
	  avg_method = getattr( averager, avg_method_name )

#xxxxx will need to make this a separate thread with per-state progress feedback
          for state_ndx in xrange( len( self.states ) ):
	    st = self.GetState( state_ndx )
	    derived_st = self.GetDerivedState( state_ndx )

	    dset = st.GetDataSet( ds_name )
	    if dset is None:
	      dset = derived_st.GetDataSet( ds_name )

	    if dset is not None:
	      avg_data = avg_method( dset )  # was data.value
	      derived_st.CreateDataSet( derived_name, avg_data )
	    #end if data
	  #end for each state

	  self.AddDataSetName( der_names[ 0 ], derived_name )

	except Exception, ex:
#	  msg = 'Error calculating derived "%s" dataset for "%s"' % \
#	      ( derived_label, ds_name )
#	  print >> sys.stderr, '%s\nddef="%s"' % ( msg, str( ddef ) )
	  self.logger.error(
	      'Error calculating derived "%s" dataset for "%s"',
	      derived_label, ds_name
	      )
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
	    exp_value = np.array( from_group[ 'exposure' ] )
	    exp_ds = der_group.create_dataset( 'exposure', data = exp_value )
		#data = from_group[ 'exposure' ].value

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
    """Creates the dataset type name (e.g., :radial) and then pairs of
prefixed (e.g., radial_pin_powers) and replaced (radial_powers) derived names
for each prefix defined for derived_label.
@param  ds_category	dataset category, e.g., 'channel', 'pin'
@param  derived_label	derived label, e.g., 'assembly', 'axial', 'core,
			'radial'
@param  ds_name		dataset name that is in ds_category, e.g.,
			'pin_powers', 'pin_fueltemps'
@return			( ds_type, prefix_name, replaced_name )
			or None if invalid params,
			e.g. ( 'pin:axial', 'axial_pin_powers', 'axial_powers' )
"""
    result = None
    #ds_type = ds_category + ':' + derived_label
    ds_type = ':' + derived_label
    ddef = self.dataSetDefs.get( ds_type )
    if ddef:
      result_list = [ ds_type ]
      #for der_prefix in ddef[ 'ds_prefix' ].split( ',' ):
      for der_prefix in ddef[ 'ds_prefix' ]:
        pref_name = der_prefix + '_' + ds_name
        repl_name = pref_name.replace( ds_category + '_', '' )
	result_list.append( pref_name )
	result_list.append( repl_name )

      result = tuple( result_list )
    #end if ddef

    return  result
  #end _CreateDerivedNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedNames_old()		-
  #----------------------------------------------------------------------
  def _CreateDerivedNames_old( self, ds_category, derived_label, ds_name ):
    """Creates the dataset type name (e.g., pin:radial) and
prefixed (e.g., radial_pin_powers) and replaced (radial_powers) derived names.
@param  ds_category	dataset category, e.g., 'channel', 'pin'
@param  derived_label	derived label, e.g., 'assembly', 'axial', 'core,
			'radial'
@param  ds_name		dataset name that is in ds_category, e.g.,
			'pin_powers', 'pin_fueltemps'
@return			( ds_type, prefix_name, replaced_name )
			or None if invalid params,
			e.g. ( 'pin:axial', 'axial_pin_powers', 'axial_powers' )
"""
    result = None
    ds_type = ds_category + ':' + derived_label
    ddef = self.dataSetDefs.get( ds_type )
    if ddef:
      result_list = [ ds_type ]
      for der_prefix in ddef[ 'ds_prefix' ].split( ',' ):
        pref_name = der_prefix + '_' + ds_name
        repl_name = pref_name.replace( ds_category + '_', '' )
	result_list.append( pref_name )
	result_list.append( repl_name )

      result = tuple( result_list )
    #end if ddef

    return  result
  #end _CreateDerivedNames_old


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateDetectorAddr()			-
  #----------------------------------------------------------------------
  def CreateDetectorAddr( self, col, row ):
    """Creates tuple from the column and row indexes.
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( det_ndx, col, row )
"""
    return \
        ( self.core.detectorMap[ row, col ] - 1, col, row ) \
	if self.core is not None else \
	( -1, -1, -1 )
  #end CreateDetectorAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateDetectorAddrFromIndex()		-
  #----------------------------------------------------------------------
  def CreateDetectorAddrFromIndex( self, det_ndx ):
    """Creates tuple from the column and row indexes.
@param  det_ndx		0-based detector index
@return			0-based ( det_ndx, col, row )
"""
    result = ( -1, -1 -1 )
    if self.core is not None:
      places = np.argwhere( self.core.detectorMap == det_ndx + 1 )
      if len( places ) > 0:
        place = places[ -1 ]
        result = ( det_ndx, int( place[ 1 ] ), int( place[ 0 ] ) )
    return  result
  #end CreateDetectorAddrFromIndex


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

      #xxxxx decrementing on even nassx and nassy
      if self.core.coreSym == 4:
	left = self.core.nassx >> 1
	top = self.core.nassy >> 1
	if self.core.nassx % 2 == 0 and left > 0: left -= 1
	if self.core.nassy % 2 == 0 and top > 0: top -= 1
      elif self.core.coreSym == 8:
	left = self.core.nassx >> 2
	top = self.core.nassy >> 2
	if self.core.nassx % 2 == 0 and left > 0: left -= 1
	if self.core.nassy % 2 == 0 and top > 0: top -= 1
      else:
	left = 0
	top = 0

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
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
@deprecated  use FindChannelMinMaxValue()
"""
    results = {}

    addr, state_ndx, value = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    else:
      skip = cur_obj is not None and \
          hasattr( cur_obj, 'assemblyAddr' ) and \
          getattr( cur_obj, 'assemblyAddr' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_addr = self.CreateAssemblyAddrFromIndex( addr[ 3 ] )
	if assy_addr[ 0 ] >= 0:
          results[ 'assembly_addr' ] = assy_addr

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
	if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
        sub_addr = getattr( cur_obj, 'subAddr' )
	skip = sub_addr[ 1 ] == addr[ 0 ] and sub_addr[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'sub_addr' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None

    return  results
  #end FindChannelMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindChannelMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindChannelMinMaxValue(
      self,
      mode, ds_name, state_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with channel addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'channel' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
"""
    results = {}

    addr, state_ndx, value = self.FindMinMaxValueAddr(
        mode, ds_name, state_ndx,
	self.channelFactors if use_factors else None
	)

    if addr is None:
      pass

    else:
      skip = cur_obj is not None and \
          hasattr( cur_obj, 'assemblyAddr' ) and \
          getattr( cur_obj, 'assemblyAddr' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_addr = self.CreateAssemblyAddrFromIndex( addr[ 3 ] )
	if assy_addr[ 0 ] >= 0:
          results[ 'assembly_addr' ] = assy_addr

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
        sub_addr = getattr( cur_obj, 'subAddr' )
	skip = sub_addr[ 1 ] == addr[ 0 ] and sub_addr[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'sub_addr' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None
   
    return  results
  #end FindChannelMinMaxValue


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
			compare against for changes: assemblyAddr, axialValue,
			stateIndex
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'state_index'
"""
    results = {}

    addr, state_ndx, value = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    else:
      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 2 ] == addr[ 0 ]
      if not skip:
	axial_value = self.CreateAxialValue( detector_ndx = addr[ 0 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'assemblyAddr' ) and \
          getattr( cur_obj, 'assemblyAddr' )[ 0 ] == addr[ 1 ]
      if not skip:
	det_addr = self.CreateDetectorAddrFromIndex( addr[ 1 ] )
	if det_addr[ 0 ] >= 0:
          results[ 'assemblyAddr' ] = det_addr

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'stateIndex' ) and \
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
#			-- Descending
      if values[ 0 ] > values[ -1 ]:
        lo = 0
	hi = len( values )
        while lo < hi:
	  mid = ( lo + hi ) // 2
          if value > values[ mid ]:  hi = mid
          else:  lo = mid + 1
        match_ndx = min( lo, len( values ) - 1 )

#			-- Ascending
      else:
        match_ndx = min(
            bisect.bisect_left( values, value ),
	    len( values ) - 1
	    )
    #end if not empty list

    return  match_ndx
  #end FindListIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindListIndex1()			-
  #----------------------------------------------------------------------
  def FindListIndex1( self, values, value ):
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
#			-- Descending
      if values[ 0 ] > values[ -1 ]:
        if value > values[ 0 ]:
	  match_ndx = 0
	elif value <= values[ -1 ]:
	  match_ndx = len( values ) - 1
	else:
	  for i in xrange( len( values ) ):
	    if values[ i ] < value:
	      match_ndx = i
	      break
	#end if

#			-- Ascending
      else:
	if value < values[ 0 ]:
	  match_ndx = 0
	elif value >= values[ -1 ]:
	  match_ndx = len( values ) -1
	else:
	  for i in xrange( len( values ) ):
	    if values[ i ] > value:
	      match_ndx = i
	      break
	#end if
    #end if not empty list

    return  match_ndx
  #end FindListIndex1


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindMaxValueAddr()			-
  #----------------------------------------------------------------------
  def FindMaxValueAddr( self, ds_name, state_ndx ):
    """Finds the first address of the max value
@param  ds_name		name of dataset to search
@param  state_ndx	0-based state point index, or -1 for all states
@return			( dataset addr indices or None, state_ndx,
			  max_value or None )
@deprecated  Use FindMinMaxValueAddr()
"""
    addr = None
    max_value = None

    if ds_name is None:
      pass

    elif state_ndx >= 0:
      dset = self.GetStateDataSet( state_ndx, ds_name )
      if dset:
        #x = np.nanargmax( dset.value )
	dset_value = np.array( dset )
        x = np.nanargmax( dset_value )
	addr = np.unravel_index( x, dset.shape )
	max_value = dset_value[ addr ]

    else:
      max_value = -sys.float_info.max
      for st in xrange( len( self.states ) ):
        dset = self.GetStateDataSet( st, ds_name )
	if dset:
	  #x = np.nanargmax( dset.value )
	  dset_value = np.array( dset )
	  x = np.nanargmax( dset_value )
	  cur_addr = np.unravel_index( x, dset.shape )
	  cur_max = dset_value[ cur_addr ]
	  if cur_max > max_value:
	    addr = cur_addr
	    state_ndx = st
	    max_value = cur_max
      #end for
    #end else all states

#		-- Convert from np.int64 to int
#		--
    temp_addr = [ int( i ) for i in addr ]
    addr = tuple( temp_addr )

    return  addr, state_ndx, max_value
  #end FindMaxValueAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindMinMaxValueAddr()			-
  #----------------------------------------------------------------------
  def FindMinMaxValueAddr( self, mode, ds_name, state_ndx, factors = None ):
    """Finds the first address of the max value
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset to search
@param  state_ndx	0-based state point index, or -1 for all states
@param  factors		optional factors to apply to the data, where zero
			values indicate places in the data to be ignored
@return			( dataset addr indices or None, state_ndx,
			  minmax_value or None )
"""
    max_flag = mode != 'min'
    addr = None
    minmax_value = None

#		-- Resolve factors to dataset if necessary
#		--
    if ds_name and factors is not None:
      ds_shape = None
      ds_type = self.GetDataSetType( ds_name )
      if ds_type:
        ds_def = self.GetDataSetDef( ds_type )
	if ds_def:
          ds_shape = \
              ds_def[ 'copy_shape' ] if 'copy_shape' in ds_def else \
              ds_def[ 'shape' ]

      if ds_shape is None:
        ds_name = None

      elif factors.shape != ds_shape:
        if 'copy_expr' not in ds_def:
	  factors = None
        else:
	  sum_axis = []
	  for i in xrange( len( ds_shape ) ):
	    if ds_shape[ i ] != factors.shape[ i ] and ds_shape[ i ] == 1:
	      sum_axis.append( i )
	  #end for i

          sum_factors = np.sum( factors, axis = tuple( sum_axis ) )
	  new_factors = np.ndarray( ds_shape, dtype = np.float64 )
	  exec_str = 'new_factors' + ds_def[ 'copy_expr' ] + ' = sum_factors'
	  exec(
	      exec_str, {},
	      { 'new_factors': new_factors, 'sum_factors': sum_factors }
	      )
	  factors = new_factors
        #end if-else copy_expr defined
      #end if-else factors.shape != ds_shape:
    #end if ds_name and factors

#		-- Must have data
#		--
    if not ds_name:
      pass

#		-- Single state point
#		--
    elif state_ndx >= 0:
      dset = self.GetStateDataSet( state_ndx, ds_name )
      if dset:
	dset_value = np.array( dset )
	if factors is not None:
	  np.place(
	      dset_value, factors == 0.0,
	      -sys.float_info.max if max_flag else sys.float_info.max
	      )
        x = \
	    np.nanargmax( dset_value ) if max_flag else \
	    np.nanargmin( dset_value )
	addr = np.unravel_index( x, dset.shape )
	minmax_value = dset_value[ addr ]

#		-- Multiple state points
#		--
    else:
      minmax_value = -sys.float_info.max if max_flag else sys.float_info.max
      for st in xrange( len( self.states ) ):
        dset = self.GetStateDataSet( st, ds_name )
	if dset:
	  dset_value = np.array( dset )
	  if factors is not None:
	    np.place(
		dset_value, factors == 0.0,
	        -sys.float_info.max if max_flag else sys.float_info.max
	        )
          x = \
	      np.nanargmax( dset_value ) if max_flag else \
	      np.nanargmin( dset_value )
	  cur_addr = np.unravel_index( x, dset.shape )
	  cur_minmax = dset_value[ cur_addr ]
	  new_flag = \
	      cur_minmax > minmax_value if max_flag else \
	      cur_minmax < minmax_value
	  if new_flag:
	    addr = cur_addr
	    state_ndx = st
	    minmax_value = cur_minmax
      #end for
    #end else all states

#		-- Convert from np.int64 to int
#		--
    if addr:
      temp_addr = [ int( i ) for i in addr ]
      addr = tuple( temp_addr )

    return  addr, state_ndx, minmax_value
  #end FindMinMaxValueAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindMultiDataSetMaxValue()		-
  #----------------------------------------------------------------------
  def FindMultiDataSetMaxValue( self, state_ndx, cur_obj, *ds_names ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the maximum value among all the
specified datasets.  Calls FindMaxValueAddr().
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  ds_names	dataset names to search
@return			dict with possible keys: 'assembly_addr',
			'axial_value', 'state_index', 'sub_addr'
@deprecated  Use FindMultiDataSetMinMaxValue()
"""
    results = {}
    max_ds_name, max_addr, max_state_ndx, max_value = None, None, None, None

    if ds_names:
      for ds_name in ds_names:
        cur_addr, cur_state_ndx, cur_value = \
	    self.FindMaxValueAddr( ds_name, state_ndx )
        if cur_addr is not None and cur_value is not None:
	  if max_value is None or cur_value > max_value:
	    max_ds_name, max_addr, max_state_ndx, max_value = \
	        ds_name, cur_addr, cur_state_ndx, cur_value
	#end if
      #end for ds_name
    #end if ds_names

    if max_ds_name and max_addr:
      ds_type = self.GetDataSetType( max_ds_name )

      if ds_type == 'channel':
	skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 3 ]
	if not skip:
          assy_addr = self.CreateAssemblyAddrFromIndex( max_addr[ 3 ] )
          if assy_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = assy_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 1 ] == max_addr[ 2 ]
        if not skip:
          axial_value = self.CreateAxialValue( core_ndx = max_addr[ 2 ] )
	  if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = False
	if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
          sub_addr = getattr( cur_obj, 'subAddr' )
	  skip = \
	      sub_addr[ 1 ] == max_addr[ 0 ] and \
	      sub_addr[ 0 ] == max_addr[ 1 ]
        if not skip:
          results[ 'sub_addr' ] = ( max_addr[ 1 ], max_addr[ 0 ] )

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'detector':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 2 ] == max_addr[ 0 ]
        if not skip:
	  axial_value = self.CreateAxialValue( detector_ndx = max_addr[ 0 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 1 ]
        if not skip:
	  det_addr = self.CreateDetectorAddrFromIndex( max_addr[ 1 ] )
	  if det_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = det_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'fixed_detector':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 3 ] == max_addr[ 0 ]
        if not skip:
	  axial_value = self.CreateAxialValue( fixed_detector_ndx = max_addr[ 0 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 1 ]
        if not skip:
	  det_addr = self.CreateDetectorAddrFromIndex( max_addr[ 1 ] )
	  if det_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = det_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'pin':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 3 ]
        if not skip:
	  assy_addr = self.CreateAssemblyAddrFromIndex( max_addr[ 3 ] )
	  if assy_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = assy_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 1 ] == max_addr[ 2 ]
        if not skip:
          axial_value = self.CreateAxialValue( core_ndx = max_addr[ 2 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = False
	if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
          sub_addr = getattr( cur_obj, 'subAddr' )
	  skip = \
	      sub_addr[ 1 ] == max_addr[ 0 ] and \
	      sub_addr[ 0 ] == max_addr[ 1 ]
        if not skip:
          results[ 'sub_addr' ] = ( max_addr[ 1 ], max_addr[ 0 ] )

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      else:  # scalar
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx
    #end if

    return  results
  #end FindMultiDataSetMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindMultiDataSetMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindMultiDataSetMinMaxValue( self, mode, state_ndx, cur_obj, *ds_names ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the maximum value among all the
specified datasets.  Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  ds_names	dataset names to search
@return			dict with possible keys: 'assembly_addr',
			'axial_value', 'state_index', 'sub_addr'
"""
    max_flag = mode != 'min'
    results = {}
    max_ds_name, max_addr, max_state_ndx, max_value = None, None, None, None

    if ds_names:
      for ds_name in ds_names:
        cur_addr, cur_state_ndx, cur_value = \
	    self.FindMinMaxValueAddr( mode, ds_name, state_ndx )
        if cur_addr is not None and cur_value is not None:
	  new_flag = \
	      True if max_value is None else \
	      cur_value > max_value if max_flag else \
	      cur_value < max_value
	  if new_flag:
	    max_ds_name, max_addr, max_state_ndx, max_value = \
	        ds_name, cur_addr, cur_state_ndx, cur_value
	#end if
      #end for ds_name
    #end if ds_names

    if max_ds_name and max_addr:
      ds_type = self.GetDataSetType( max_ds_name )

      if ds_type == 'channel':
	skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 3 ]
	if not skip:
          assy_addr = self.CreateAssemblyAddrFromIndex( max_addr[ 3 ] )
          if assy_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = assy_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 1 ] == max_addr[ 2 ]
        if not skip:
          axial_value = self.CreateAxialValue( core_ndx = max_addr[ 2 ] )
	  if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = False
	if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
          sub_addr = getattr( cur_obj, 'subAddr' )
	  skip = \
	      sub_addr[ 1 ] == max_addr[ 0 ] and \
	      sub_addr[ 0 ] == max_addr[ 1 ]
        if not skip:
          results[ 'sub_addr' ] = ( max_addr[ 1 ], max_addr[ 0 ] )

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'detector':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 2 ] == max_addr[ 0 ]
        if not skip:
	  axial_value = self.CreateAxialValue( detector_ndx = max_addr[ 0 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 1 ]
        if not skip:
	  det_addr = self.CreateDetectorAddrFromIndex( max_addr[ 1 ] )
	  if det_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = det_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'fixed_detector':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 3 ] == max_addr[ 0 ]
        if not skip:
	  axial_value = self.CreateAxialValue( fixed_detector_ndx = max_addr[ 0 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 1 ]
        if not skip:
	  det_addr = self.CreateDetectorAddrFromIndex( max_addr[ 1 ] )
	  if det_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = det_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      elif ds_type == 'pin':
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'assemblyAddr' ) and \
            getattr( cur_obj, 'assemblyAddr' )[ 0 ] == max_addr[ 3 ]
        if not skip:
	  assy_addr = self.CreateAssemblyAddrFromIndex( max_addr[ 3 ] )
	  if assy_addr[ 0 ] >= 0:
            results[ 'assembly_addr' ] = assy_addr

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'axialValue' ) and \
            getattr( cur_obj, 'axialValue' )[ 1 ] == max_addr[ 2 ]
        if not skip:
          axial_value = self.CreateAxialValue( core_ndx = max_addr[ 2 ] )
          if axial_value[ 0 ] >= 0.0:
            results[ 'axial_value' ] = axial_value

        skip = False
	if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
          sub_addr = getattr( cur_obj, 'subAddr' )
	  skip = \
	      sub_addr[ 1 ] == max_addr[ 0 ] and \
	      sub_addr[ 0 ] == max_addr[ 1 ]
        if not skip:
          results[ 'sub_addr' ] = ( max_addr[ 1 ], max_addr[ 0 ] )

        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx

      else:  # scalar
        skip = cur_obj is not None and \
	    hasattr( cur_obj, 'stateIndex' ) and \
            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
        if not skip:
          results[ 'state_index' ] = max_state_ndx
    #end if

    return  results
  #end FindMultiDataSetMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindPinMaxValue()			-
  #----------------------------------------------------------------------
  def FindPinMaxValue( self, ds_name, state_ndx, cur_obj = None ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMaxValueAddr().
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
"""
    results = {}

    addr, state_ndx, value = self.FindMaxValueAddr( ds_name, state_ndx )

    if addr is None:
      pass

    else:
      skip = cur_obj is not None and \
          hasattr( cur_obj, 'assemblyAddr' ) and \
          getattr( cur_obj, 'assemblyAddr' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_addr = self.CreateAssemblyAddrFromIndex( addr[ 3 ] )
	if assy_addr[ 0 ] >= 0:
          results[ 'assembly_addr' ] = assy_addr

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
        sub_addr = getattr( cur_obj, 'subAddr' )
	skip = sub_addr[ 1 ] == addr[ 0 ] and sub_addr[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'sub_addr' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None
   
    return  results
  #end FindPinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindPinMinMaxValue()			-
  #----------------------------------------------------------------------
  def FindPinMinMaxValue(
      self,
      mode, ds_name, state_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors (or nodeFactors) when
			determining the min/max address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
"""
    results = {}

    factors = None
    if use_factors:
      ds_type = self.GetDataSetType( ds_name )
      factors = \
          self.nodeFactors if self.IsNodalType( ds_type ) else self.pinFactors
    #end if use_factors

    addr, state_ndx, value = self.FindMinMaxValueAddr(
        mode, ds_name, state_ndx,
	factors
	#self.pinFactors if use_factors else None
	)

    if addr is None:
      pass

    else:
      skip = cur_obj is not None and \
          hasattr( cur_obj, 'assemblyAddr' ) and \
          getattr( cur_obj, 'assemblyAddr' )[ 0 ] == addr[ 3 ]
      if not skip:
	assy_addr = self.CreateAssemblyAddrFromIndex( addr[ 3 ] )
	if assy_addr[ 0 ] >= 0:
          results[ 'assembly_addr' ] = assy_addr

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
          getattr( cur_obj, 'axialValue' )[ 1 ] == addr[ 2 ]
      if not skip:
        axial_value = self.CreateAxialValue( core_ndx = addr[ 2 ] )
        if axial_value[ 0 ] >= 0.0:
          results[ 'axial_value' ] = axial_value

      skip = False
      if cur_obj is not None and hasattr( cur_obj, 'subAddr' ):
        sub_addr = getattr( cur_obj, 'subAddr' )
	skip = sub_addr[ 1 ] == addr[ 0 ] and sub_addr[ 0 ] == addr[ 1 ]
      if not skip:
        results[ 'sub_addr' ] = ( addr[ 1 ], addr[ 0 ] )

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'stateIndex' ) and \
          getattr( cur_obj, 'stateIndex' ) == state_ndx
      if not skip:
        results[ 'state_index' ] = state_ndx
    #end else cur_obj not None
   
    return  results
  #end FindPinMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FireEvent()				-
  #----------------------------------------------------------------------
  def FireEvent( self, event_name, *params ):
    """
@param  event_name	either 'newDataSet' or 'newFile'
@param  params		event params
"""
    if event_name in self.listeners:
      for listener in self.listeners[ event_name ]:
        method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
	if hasattr( listener, method_name ):
	  getattr( listener, method_name )( *params )
	elif hasattr( listener, '__call__' ):
	  listener( *params )
      #end for listener
    #end if event_name
  #end FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetAverager()				-
  #----------------------------------------------------------------------
  def GetAverager( self, ds_type = None ):
    """
@param  ds_type		optional type/category name ( 'channel', 'pin' )
@return			dict of averager objects if ds_category is None,
			otherwise the named averager if found, otherwise None
@return			if ds_type is not None, averager object for that
			ds_type or None if not found
			if ds_type is None, dict of averager objects by
			ds_type
"""
    return \
	self.averagers.get( ds_type ) if ds_type else \
        self.averagers
  #end GetAverager


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetChannelFactors()			-
  #----------------------------------------------------------------------
  def GetChannelFactors( self ):
    return  self.channelFactors
  #end GetChannelFactors


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
  #	METHOD:		DataModel.GetDataSetDef()			-
  #----------------------------------------------------------------------
  def GetDataSetDef( self, ds_type = None ):
    """Looks up the dataset definition for the category/type.
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
  #	METHOD:		DataModel.GetDataSetDefs()			-
  #----------------------------------------------------------------------
  def GetDataSetDefs( self ):
    """Accessor for the 'dataSetDefs' property.
@return			dictory of dataset definitions
"""
    return  self.dataSetDefs
  #end GetDataSetDefs


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, ds_name ):
    """Removes prefixes.
"""
    return \
	ds_name  if not ds_name else \
        ds_name[ 5 : ]  if ds_name.startswith( 'copy:' ) else \
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
			if ds_type is None, copy of dict of dataset name lists
			by ds_type
			( 'axial', 'channel', 'detector', 'fixed_detector',
			  'pin', 'scalar', etc. )
"""
    return \
        list( self.dataSetNames.get( ds_type, [] ) ) if ds_type else \
        dict( self.dataSetNames )
#        dict( self.dataSetNames ) if ds_type is None else \
#	list( self.dataSetNames.get( ds_type, [] ) )
  #end GetDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNamesVersion()		-
  #----------------------------------------------------------------------
  def GetDataSetNamesVersion( self ):
    """Used to determine the generation of dataset changes for menus and
lists that must be rebuilt when the sets of available datasets change.
"""
    return  DataModel.dataSetNamesVersion_
    #return  self.dataSetNamesVersion
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
  #	METHOD:		DataModel.GetDataSetTypeDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetTypeDisplayName( self, ds_type ):
    """Strips any derived prefix.  Best to encapsulate this here.  Note this
must match how _CreateDerivedNames() builds the derived type name.
@param  ds_type		category/type
@return			type name sans any derived marking
"""
#    if ds_type and ds_type.find( ':' ) == 0:
#      ds_type = ds_type[ 1 : ]
#		-- Safer version
    if ds_type:
      ndx = ds_type.find( ':' )
      if ndx >= 0:
        ds_type = ds_type[ ndx + 1 : ]
    return  ds_type
  #end GetDataSetTypeDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDefaultScalarDataSet()		-
  #----------------------------------------------------------------------
  def GetDefaultScalarDataSet( self ):
    """Tries to find boron, defaulting to the first 'scalar' dataset or
'keff' if none are found.
@return			dataset name
"""
    result = None

    ds_names = self.GetDataSetNames( 'scalar' )
    if 'boron' in ds_names:
      result = 'boron'

    else:
      for name in sorted( ds_names ):
        if name.find( 'boron' ) >= 0:
	  result = name
	  break
    #end if-else

    if not result:
      result = ds_names[ 0 ] if len( ds_names ) > 0 else 'keff'

    return  result
  #end GetDefaultScalarDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivableTypes()			-
  #----------------------------------------------------------------------
  def GetDerivableTypes( self, der_label ):
    """For the specified derived label, returns all the types from which
the derived dataset can be created.  Lazily created and cached.
@param  der_label	derived label
@return			sorted list of base/source types, possibly empty
"""
    ds_types = self.derivableTypesByLabel.get( der_label )
    if ds_types is None:
      ds_types = []
      ddef = self.GetDataSetDef( ':' + der_label )
      if ddef and 'avg_method' in ddef:
        for k in ddef[ 'avg_method' ].keys():
	  ds_types.append( k )
        ds_types.sort()
      #if avg_method defined

    return  ds_types
  #end GetDerivableTypes


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedLabels()			-
  #----------------------------------------------------------------------
  def GetDerivedLabels( self, ds_category ):
    """For the specified category, returns all the labels for possible
derived datasets.  Lazily created and cached.
@param  ds_category	category/type, key in DATASET_DEFS
@return			sorted list of derived type labels, possibly empty
"""
    labels = self.derivedLabelsByType.get( ds_category )
    if labels is None:
      labels = []
      for def_name, ddef in self.dataSetDefs.iteritems():
        if def_name.startswith( ':' ) and 'avg_method' in ddef and \
	    ds_category in ddef[ 'avg_method' ]:
	  labels.append( def_name[ 1 : ] )
      #end for

      labels.sort()
      self.derivedLabelsByType[ ds_category ] = labels
    #end if

    return  labels
  #end GetDerivedLabels


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedLabels_old()		-
  #----------------------------------------------------------------------
  def GetDerivedLabels_old( self, ds_category ):
    """For the specified category, returns all the labels for possible
derived datasets.  Lazily created and cached.
"""
    labels = self.derivedLabelsByType.get( ds_category )
    if labels is None:
      labels = []
      for def_name, def_item in self.dataSetDefs.iteritems():
        if def_name.startswith( ds_category ):
          ndx = def_name.find( ':' )
	  if ndx >= 0:
	    labels.append( def_name[ ndx + 1 : ] )
      #end for

      labels.sort()
      self.derivedLabelsByType[ ds_category ] = labels
    #end if

    return  labels
  #end GetDerivedLabels_old


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
  #	METHOD:		DataModel.GetFactors()				-
  #----------------------------------------------------------------------
  def GetFactors( self, ds_name ):
    """Determines the factors from the dataset shape.
@param  dset		dataset to match
@return			factors np.ndarray or None
"""
    result = None

#		-- Find dataset type
#		--
#    if ds_name and self.GetStatesCount() > 0:
#      dset = self.GetStateDataSet( 0, ds_name )
    ddef = self.GetDataSetDefByDsName( ds_name ) if ds_name else none
    if ddef:
      result = self.pinFactors

      if ddef[ 'type' ] == 'channel':
        result = self.channelFactors

      elif ddef[ 'type' ] == ':chan_radial':
        result = np.ndarray( ddef[ 'copy_shape' ], dtype = np.float64 )
        result.fill( 0.0 )
	factors_sum = np.sum( self.channelFactors, axis = 2 )
	exec_str = 'result' + ddef[ 'copy_expr' ] + ' = factors_sum'
	exec(
	    exec_str, {},
	    { 'factors_sum': factors_sum, 'result': result }
	    )

      elif 'factors' in ddef and 'copy_shape' in ddef and \
          'pin' in self.averagers:
        result = np.ndarray( ddef[ 'copy_shape' ], dtype = np.float64 )
        result.fill( 0.0 )
	exec_str = \
	    'result' + ddef[ 'copy_expr' ] + ' = averager.' + ddef[ 'factors' ]
	exec(
	    exec_str, {},
	    { 'averager': self.averagers[ 'pin' ], 'result': result }
	    )
    #end if ddef

    return  result
  #end GetFactors


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
  #	METHOD:		DataModel.GetNodeAddr()				-
  #----------------------------------------------------------------------
  def GetNodeAddr( self, sub_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  sub_addr	0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
@return			node addr in range [0,3], or -1 if sub_addr is invalid
"""
    node_addr = -1
    if self.core is not None:
      cx = self.core.npinx >> 1
      cy = self.core.npiny >> 1 
      if mode == 'channel':
        cx += 1
	cy += 1

      node_addr = 2 if max( 0, sub_addr[ 1 ] ) >= cy else 0
      if max( 0, sub_addr[ 0 ] ) >= cx:
        node_addr += 1

    return  node_addr
  #end GetNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetNodeAddrs()			-
  #----------------------------------------------------------------------
  def GetNodeAddrs( self, sub_addrs, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  sub_addrs	list of 0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
@return			list of unique node addrs in range [0,3]
"""
    result = []
    for sub_addr in sub_addrs:
      ndx = self.GetNodeAddr( sub_addr, mode )
      if ndx >= 0 and ndx not in result:
        result.append( ndx )

    return  result
  #end GetNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetNodeFactors()			-
  #----------------------------------------------------------------------
  def GetNodeFactors( self ):
    return  self.nodeFactors
  #end GetNodeFactors


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetPinFactors()			-
  #----------------------------------------------------------------------
  def GetPinFactors( self ):
    return  self.pinFactors
  #end GetPinFactors


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
	ds.value[ () ] if len( ds.shape ) == 0 else ds[ 0 ]
#	ds.value if len( ds.shape ) == 0 else \
#	ds.value.item()
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
    """Retrieves a normal or derived dataset, copying a derived dataset into
a 4D array if necessary.
@param  state_ndx	0-based state point index
@param  ds_name		dataset name, normal or derived
@return			h5py.Dataset object if found or None
"""
    dset = None

    st = None
    derived_st = None

    #if ds_name is not None:
    if ds_name:
      st = self.GetState( state_ndx )
      derived_st = self.GetDerivedState( state_ndx )

    #if st and derived_st:
    if st:
      self.dataSetDefsLock.acquire()
      try:
        dset = st.GetDataSet( ds_name )
	if dset is None and derived_st is not None:
	  dset = derived_st.GetDataSet( ds_name )

#				-- Must copy a derived (not 4D) dataset
#				--
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

	      if copy_data.size == 1:
	        copy_data[ 0, 0, 0, 0 ] = \
		    dset[ 0 ] if len( dset.shape ) > 0 else dset[ () ]
	        #copy_data[ 0, 0, 0, 0 ] = np.array( dset ).item()
	      else:
	        globals_env = {}
	        locals_env = { 'copy_data': copy_data, 'dset': dset }
	        exec( exec_str, globals_env, locals_env )
	        dset = derived_st.CreateDataSet(
	            copy_name, locals_env[ 'copy_data' ]
		    )
	      #end if-else copy_data.size
	    #end if ds_def is not None
	  #end if-else copy_dset
        #end if must copy
      finally:
        self.dataSetDefsLock.release()
    #end if st and derived_st

    return  dset
  #end GetStateDataSet


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
  #	METHOD:		DataModel.GetSubAddrFromNode()			-
  #----------------------------------------------------------------------
  def GetSubAddrFromNode( self, node_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  node_addr	0, 1, 2, or 3
@param  mode		'channel' or 'pin', defaulting to the latter
@return			0-based sub_addr ( col, row )
"""
    if self.core is None or node_addr < 0 or node_addr >= 4:
      sub_addr = ( -1, -1 )
    else:
#      cx = self.core.npinx >> 1
#      cy = self.core.npiny >> 1
#      if mode == 'channel':
#        cx += 1
#	cy += 1
#      col = 0 if node_addr in ( 0, 2 ) else cx
#      row = 0 if node_addr in ( 0, 1 ) else cy
      npinx = self.core.npinx
      npiny = self.core.npiny
      if mode == 'channel':
        npinx += 1
        npiny += 1
      col = 0 if node_addr in ( 0, 2 ) else npinx - 1
      row = 0 if node_addr in ( 0, 1 ) else npiny - 1

      sub_addr = ( col, row )

    return  sub_addr
  #end GetSubAddrFromNode


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
			'detector', 'fixed_detector', 'pin', 'scalar'
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
@param  ds_category	(unneeded) dataset category, e.g., 'channel', 'pin'
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
      names = self.GetDataSetNames( der_names[ 0 ] )
      if names:
        for n in der_names[ 1 : ]:
          if n in names:
	    match = n
	    break

    return  match
  #end HasDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Is3DReady()				-
  #----------------------------------------------------------------------
  def Is3DReady( self ):
    """Checks having length gt 1 in all three dimensions.
"""
    valid = \
        self.core is not None and \
	self.core.nax > 1 and \
	(self.core.nassx * self.core.npinx) > 1 and \
	(self.core.nassy * self.core.npiny) > 1

    return  valid
  #end Is3DReady


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsBadValue()				-
  #----------------------------------------------------------------------
  def IsBadValue( self, value ):
    """Checks for nan and inf.
@param  value		value to check
@return			True if nan or inf, False otherwise
"""
    return  value is None or math.isnan( value ) or math.isinf( value )
  #end IsBadValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsDerivedType()			-
  #----------------------------------------------------------------------
  def IsDerivedType( self, ds_type ):
    """
@param  ds_type		category/type
@return			True if derived, false otherwise
"""
    return  ds_type and ds_type.find( ':' ) >= 0
  #end IsDerivedType


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
    return  value == 0.0 or math.isnan( value ) or math.isinf( value )
  #end IsNoDataValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsNodalType()				-
  #----------------------------------------------------------------------
  def IsNodalType( self, ds_type ):
    """Determines if the category/type represents a nodal dataset.
@param  ds_type		dataset category/type
@return			True if nodal, False otherwise
"""
    return  \
        ds_type and \
        (ds_type.find( ':node' ) >= 0 or ds_type.find( ':radial_node' ) >= 0)
  #end IsNodalType


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValid()				-
  #----------------------------------------------------------------------
  def IsValid( self, **kwargs ):
    """Checks values for validity w/in ranges available for this dataset
@param  kwargs		named values to check:
			  'assembly_addr'
			  'assembly_index'
			  'axial_level'
			  'node_addr'
			  'sub_addr'
			  'sub_addr_mode'
			    (either 'channel', or 'pin', defaulting to 'pin')
			  ('dataset_name' (requires 'state_index'))
			  'detector_index'
			  'state_index'
"""
    valid = self.core is not None

    if valid:
      if 'assembly_addr' in kwargs:
        val = kwargs[ 'assembly_addr' ]
        if hasattr( val, '__iter__' ):
          valid &= \
	      val is not None and val[ 0 ] >= 0 and val[ 0 ] < self.core.nass
        else:
          valid &= val >= 0 and val < self.core.nass

      if 'assembly_index' in kwargs:
        val = kwargs[ 'assembly_index' ]
        valid &= val >= 0 and val < self.core.nass

      if 'axial_level' in kwargs:
        val = kwargs[ 'axial_level' ]
        valid &= val >= 0 and val < self.core.nax

#      if 'node_addr' in kwargs:
#        val = kwargs[ 'node_addr' ]
#	valid &= val >= 0 and val < 4

      if 'node_addr' in kwargs and kwargs[ 'node_addr' ] is not None:
        val = kwargs[ 'node_addr' ]
	valid = val >= 0 and val < 4

      if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] is not None:
        col, row = kwargs[ 'sub_addr' ]
        maxx = self.core.npinx
        maxy = self.core.npiny
        if kwargs.get( 'sub_addr_mode', 'pin' ) == 'channel':
          maxx += 1
	  maxy += 1
        valid &= \
            col >= 0 and col < maxx and \
	    row >= 0 and row < maxy

      if 'detector_index' in kwargs:
        val = kwargs[ 'detector_index' ]
        valid &= val >= 0 and val < self.core.ndet

      if 'state_index' in kwargs:
        val = kwargs[ 'state_index' ]
        valid &= val >= 0 and val < len( self.states )
        if valid and 'dataset_name' in kwargs:
          valid &= kwargs[ 'dataset_name' ] in self.states[ val ].group
      #end if 'state_index'
    #end if core exists

    return  valid
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValidForShape()			-
  #----------------------------------------------------------------------
  def IsValidForShape( self, shape_in, **kwargs ):
    """Checks values for ge 0 and w/in shape range.
@param  shape_in	shape against which to validate
@param  kwargs		named values to check:
    'assembly_addr'
    'axial_level'
    'sub_addr'
"""
    valid = True

    if 'assembly_addr' in kwargs:
      val = kwargs[ 'assembly_addr' ]
      if hasattr( val, '__iter__' ):
        valid &= val is not None and val[ 0 ] >= 0 and val[ 0 ] < shape_in[ 3 ]
      else:
        valid &= val >= 0 and val < shape_in[ 3 ]

    if 'axial_level' in kwargs:
      val = kwargs[ 'axial_level' ]
      valid &= val >= 0 and val < shape_in[ 2 ]

    if 'sub_addr' in kwargs and kwargs[ 'sub_addr' ] is not None:
      col, row = kwargs[ 'sub_addr' ]
      valid &= \
          col >= 0 and col <= shape_in[ 0 ] and \
	  row >= 0 and row <= shape_in[ 1 ]

    return  valid
  #end IsValidForShape


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsValidRange()			-
  #----------------------------------------------------------------------
  def IsValidRange( self, min_value, max_value ):
    """Companion to GetDataRange() to check for a valid range as not
[-sys.float_info.max or sys.float_info.max] and min_value ne max_value.
@param  min_value	minimum value in range
@param  max_value	maximum value in range
@return			True if valid, False otherwise
"""
    return  \
        min_value != -sys.float_info.max and \
	max_value != sys.float_info.max and \
	min_value != max_value
  #end IsValidRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeAssemblyAddr()		-
  #----------------------------------------------------------------------
  def NormalizeAssemblyAddr( self, assy_ndx ):
    if self.core is None:
      result = ( -1, -1, -1 )
    else:
      result = \
        (
        max( 0, min( assy_ndx[ 0 ], self.core.nass - 1 ) ),
        max( 0, min( assy_ndx[ 1 ], self.core.nassx - 1 ) ),
        max( 0, min( assy_ndx[ 2 ], self.core.nassy - 1 ) )
        )
    return  result
  #end NormalizeAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeAxialValue()			-
  #----------------------------------------------------------------------
  def NormalizeAxialValue( self, axial_value ):
    if self.core is None:
      result = ( -1.0, -1, -1, -1 )
    else:
      result = \
        (
        axial_value[ 0 ],
        max( 0, min( axial_value[ 1 ], self.core.nax -1 ) ),
        max( 0, min( axial_value[ 2 ], self.core.ndetax -1 ) ),
        max( 0, min( axial_value[ 3 ], self.core.nfdetax -1 ) )
        )
    return  result
  #end NormalizeAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeDetectorIndex()		-
  #----------------------------------------------------------------------
  def NormalizeDetectorIndex( self, det_ndx ):
    if self.core is None:
      result = ( -1, -1, -1 )
    else:
      result = \
        (
        max( 0, min( det_ndx[ 0 ], self.core.ndet - 1 ) ),
        max( 0, min( det_ndx[ 1 ], self.core.nassx - 1 ) ),
        max( 0, min( det_ndx[ 2 ], self.core.nassy - 1 ) )
        )
    return  result
  #end NormalizeDetectorIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeNodeAddr()			-
  #----------------------------------------------------------------------
  def NormalizeNodeAddr( self, ndx ):
    """Here for completeness.
@param  ndx		0-based index
"""
    return  max( 0, min( 3, ndx ) )
  #end NormalizeNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeNodeAddrs()			-
  #----------------------------------------------------------------------
  def NormalizeNodeAddrs( self, addr_list ):
    """Normalizes each index in the list.
@param  addr_list	list of 0-based indexes
"""
    result = []
    for addr in addr_list:
      result.append( max( 0, min( 3, addr ) ) )

    return  list( set( result ) )
  #end NormalizeNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeStateIndex()			-
  #----------------------------------------------------------------------
  def NormalizeStateIndex( self, state_ndx ):
    return  max( 0, min( state_ndx, len( self.states ) - 1 ) )
  #end NormalizeStateIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeSubAddr()			-
  #----------------------------------------------------------------------
  def NormalizeSubAddr( self, addr, mode = 'pin' ):
    """Normalizes the address, accounting for channel shape being one greater
in each dimension.
@param  addr		0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    if self.core is None:
      result = ( -1, -1 )
    else:
      maxx = self.core.npinx - 1
      maxy = self.core.npiny - 1
      if mode == 'channel':
        maxx += 1
        maxy += 1

      result = \
        (
        max( 0, min( addr[ 0 ], maxx ) ),
        max( 0, min( addr[ 1 ], maxy ) )
        )
    return  result
  #end NormalizeSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.NormalizeSubAddrs()			-
  #----------------------------------------------------------------------
  def NormalizeSubAddrs( self, addr_list, mode = 'pin' ):
    """Normalizes each address in the list, accounting for channel shape
being one greater in each dimension.
@param  addr_list	list of 0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    if self.core is None:
      maxx = maxy = -1
    else:
      maxx = self.core.npinx - 1
      maxy = self.core.npiny - 1
      if mode == 'channel':
        maxx += 1
        maxy += 1

    result = []
    for addr in addr_list:
      result.append( (
          max( 0, min( addr[ 0 ], maxx ) ),
          max( 0, min( addr[ 1 ], maxy ) )
	  ) )

    #return  result
    return  list( set( result ) )
  #end NormalizeSubAddrs


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

    #xxxx special read of state_0001 for detector_response
    self.core = Core( self.h5File )
    self.states = State.ReadAll( self.h5File )

#		-- Assert on states
#		--
    if self.states is None or len( self.states ) == 0:
      raise  Exception( 'No state points could be read' )

    st_group = self.states[ 0 ].GetGroup()

#		-- Assert on pin_powers
#		--
#orig
#    if 'pin_powers' not in st_group:
#      raise  Exception( '"pin_powers" dataset not found' )
#    pin_powers_shape = st_group[ 'pin_powers' ].shape
#orig
    pin_powers_shape = None
    if 'pin_powers' in st_group:
      pin_powers_shape = st_group[ 'pin_powers' ].shape

#		-- Special check to get core.npin if pin_volumes
#		-- missing from CORE
    #if self.core.npin == 0 and 'pin_powers' in st_group:
    if self.core.npin == 0 and pin_powers_shape is not None:
      self.core.npinx = self.core.npiny = \
      self.core.npin = pin_powers_shape[ 0 ]

#		-- Assert on pin_powers shape
#		--
    #xxxxx Needed here, since in Core.Check()?
    if pin_powers_shape is None:
      pass
    elif pin_powers_shape[ 0 ] != self.core.npiny or \
        pin_powers_shape[ 1 ] != self.core.npinx or \
        pin_powers_shape[ 2 ] != self.core.nax or \
        pin_powers_shape[ 3 ] != self.core.nass:
      raise  Exception( 'pin_powers shape inconsistent with npin, nax, and nass' )

#		-- Resolve everything
#		--
#xxxxx return messages about datasets ignored due to bad shapes, beavrs.h5
    self.dataSetDefs, self.dataSetDefsByName, self.dataSetNames = \
        self._ResolveDataSets( self.core, st_group )
#			-- Only use time datasets that appear in all statepts
    self.dataSetNames[ 'time' ] = State.ResolveTimeDataSets( self.states )
    self.derivableTypesByLabel = {}
    self.derivedLabelsByType = {}

    self.ranges = {}
    self.rangesByStatePt = [ dict() for i in xrange( len( self.states ) ) ]

#		-- Create derived file and states
#		--
    self.derivedFile, self.derivedStates = \
        self._CreateDerivedH5File( self.states )

#		-- Special check for pin_factors and node_factors
#		--
    node_factors = pin_factors = None
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

#		-- Set up the pin averager
#		--
    if 'pin' in self.averagers:
      avg = self.averagers[ 'pin' ]
      ref_pin_powers = None
      pin_powers_ds = self.GetStateDataSet( 0, 'pin_powers' )
      if pin_powers_ds is not None:
        ref_pin_powers = np.array( pin_powers_ds )
      else:
	pp_shape = \
	    ( self.core.npiny, self.core.npinx, self.core.nax, self.core.nass )
        ref_pin_powers = np.ones( pp_shape )

      avg.load( self.core, ref_pin_powers, pin_factors )
      if pin_factors is None and avg.pinWeights is not None:
        pin_factors = avg.pinWeights
      node_factors = avg.nodeWeights
    #end if

    if node_factors is None:
      self.nodeFactors = \
          np.ones( ( 1, 4, self.core.nax, self.core.nass ), dtype = np.int )
    else:
      self.nodeFactors = np.ndarray(
          ( 1, 4, self.core.nax, self.core.nass ),
	  dtype = np.float64
	  )
      self.nodeFactors[ 0, :, :, : ] = node_factors

    self.pinFactors = \
        pin_factors if pin_factors is not None else \
        np.ones( pin_factors_shape, dtype = np.int )

#		-- Set up the channel averager
#		--
    if 'channel' in self.averagers:
      avg = self.averagers[ 'channel' ]
      avg.load( self.core )
    #end if
    self.channelFactors = np.ones(
        ( self.core.npiny + 1, self.core.npinx + 1,
	  self.core.nax, self.core.nass ),
        dtype = np.int
	)
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadDataSetAxialValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetAxialValues( self,
      ds_name,
      assembly_index = 0,
      node_addrs = None,
      sub_addrs = None,
      detector_index = 0,
      state_index = 0
      ):
    """Reads axial values for a dataset for a specified state point.
@param  ds_name		dataset name
@param  assembly_index	0-based assembly index
@param  detector_index	0-based detector index
@param  node_addrs	list of node indexes
@param  sub_addrs	list of sub_addr pairs
@param  state_index	0-based state point index
@return			None if dataset cannot be found,
			dict by sub_addr of np.ndarray for datasets that vary
			by sub_addr,
			np.ndarray for other datasets
"""
    result = None
    state_index = self.NormalizeStateIndex( state_index )
    ds_def = self.GetDataSetDefByDsName( ds_name ) \
	if ds_name in self.GetDataSetNames( 'axial' ) else \
	None
    dset = self.GetStateDataSet( state_index, ds_name ) \
        if ds_def is not None else None

    if dset is not None:
      ds_shape = ds_def[ 'shape' ]
      ds_type = ds_def[ 'type' ]
      dset_value = np.array( dset )

      if sub_addrs is not None and not hasattr( sub_addrs, '__iter__' ):
        sub_addrs = [ sub_addrs ]

#			-- 'detector', 'fixed_detector'
#			--
      if ds_type == 'detector' or ds_type == 'fixed_detector':
        det_ndx = max( 0, min( detector_index, ds_shape[ 1 ] - 1 ) )
	dset_value = np.array( dset )
	result = dset_value[ :, det_ndx ]

      elif sub_addrs is None:
        pass

#			-- ':node'
#			--
      elif self.IsNodalType( ds_type ):
	#if sub_addrs is not None and 'copy_shape' in ds_def:
	if 'copy_shape' in ds_def:
	  result = {}
          ds_shape = ds_def[ 'copy_shape' ]
          assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )
	  node_addr_set = set()
	  if node_addrs is None:
	    node_addr_set.add( ( 0, -1 ) )
	  else:
	    for node_ndx in node_addrs:
	      cur_pair = ( self.NormalizeNodeAddr( node_ndx ), -1 )
	      node_addr_set.add( cur_pair )
	  #end if-else node_addrs

	  dset_value = np.array( dset )
	  for node_addr in sorted( node_addr_set ):
	    result[ node_addr ] = dset_value[ 0, node_addr[ 0 ], :, assy_ndx ]
	#end if copy_shape

#			-- Everything else
#			--
      else:
        ds_shape = \
              ds_def[ 'copy_shape' ]  if 'copy_shape' in ds_def else \
	      ds_def[ 'shape' ]

        assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )

        if ds_shape[ 0 ] > 1 and ds_shape[ 1 ] > 1:
	  if sub_addrs is not None:
	    result = {}
            sub_addr_set = set()
            for sub_addr in sub_addrs:
	      sub_addr = (
	          min( sub_addr[ 0 ], ds_shape[ 1 ] - 1 ),
	          min( sub_addr[ 1 ], ds_shape[ 0 ] - 1 )
	          )
	      if sub_addr not in sub_addr_set:
	        sub_addr_set.add( sub_addr )
	        result[ sub_addr ] = \
	            dset_value[ sub_addr[ 1 ], sub_addr[ 0 ], :, assy_ndx ]
            #end for sub_addr
	  #end if sub_addrs
	elif dset_value.size == 1:
	  result = dset_value.item()
        else:
	  result = dset_value[ 0, 0, :, assy_ndx ]
        #end if-else ds_shape
      #end if-else ds_type
    #end if dset is not None

    return  result
  #end ReadDataSetAxialValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange()			-
  #----------------------------------------------------------------------
  def _ReadDataSetRange( self, ds_name, state_ndx = -1 ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name, where a prefix of 'extra:' means it's
			an extra dataset
@param  state_ndx	optional 0-based statept index in which to search
"""
    range_min = -sys.float_info.max
    range_max = sys.float_info.max

    if ds_name:
      vmin = vmax = NAN
      #for i in range( len( self.GetStates() ) ):
      search_range = \
          xrange( self.GetStatesCount() )  if state_ndx < 0 else \
	  xrange( state_ndx, state_ndx + 1 )

      for i in search_range:
        st = self.GetState( i )
	derived_st = self.GetDerivedState( i )

	dset = st.GetDataSet( ds_name )
	if dset is None:
	  dset = derived_st.GetDataSet( ds_name )

        if dset:
	  dset_array = dset.value

	  if isinstance( dset_array, np.ndarray ):
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
	  else:
	    cur_value = dset_array.item()
	    if math.isnan( vmax ) or cur_value > vmax:
	      vmax = cur_value
	    if math.isnan( vmin ) or cur_value < vmin:
	      vmin = cur_value
	  #end if-else isinstance
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
  #	METHOD:		DataModel.ReadDataSetValues()			-
  #----------------------------------------------------------------------
  def ReadDataSetValues( self,
      ds_name,
      assembly_index = 0,
      axial_value = 0.0,
      sub_addrs = None,
      detector_index = 0
      ):
    """Reads values for a dataset across all state points.
@param  ds_name		dataset name
@param  assembly_index	0-based assembly index
@param  detector_index	0-based detector index
@param  axial_value	axial value in cm
@param  sub_addrs	single or iterable of sub_addr pairs
@return			None if dataset cannot be found,
			dict by sub_addr of np.ndarray for datasets that vary
			by sub_addr,
			np.ndarray for other datasets
@deprecated  use ReadDataSetValues2()
"""
    result = None
    ds_def = self.GetDataSetDefByDsName( ds_name )

    if sub_addrs is not None and not hasattr( sub_addrs, '__iter__' ):
      sub_addrs = [ sub_addrs ]

#		-- 'state' is special
#		--
    if ds_name == 'state':
      #values = range( 1, len( self.states ) + 1 )
      result = \
          np.array( range( 1, len( self.states ) + 1 ), dtype = np.float64 )

    #elif ds_def is None:
      #pass

#		-- 'scalar'
#		--
    elif ds_def is None or ds_def[ 'type' ] == 'scalar':
      values = []
      #for st in self.states:
        #dset = st.GetDataSet( ds_name )
      for i in xrange( len( self.states ) ):
	dset = self.GetStateDataSet( i, ds_name )
	if dset is not None:
	  dset_value = np.array( dset )
	  values.append( dset_value.item() )
	else:
	  values.append( 0.0 )
      result = np.array( values, dtype = np.float64 )

#		-- 'detector'
#		--
    elif ds_def[ 'type' ] == 'detector':
      values = []
      ds_shape = ds_def[ 'shape' ]
      ax_value = self.CreateAxialValue( value = axial_value )
      axial_level = max( 0, min( ax_value[ 2 ], ds_shape[ 0 ] - 1 ) )
      det_ndx = max( 0, min( detector_index, ds_shape[ 1 ] - 1 ) )
      #for st in self.states:
        #dset = st.GetDataSet( ds_name )
      for i in xrange( len( self.states ) ):
	dset = self.GetStateDataSet( i, ds_name )
	if dset is not None:
	  dset_value = np.array( dset )
	  values.append( dset_value[ axial_level, det_ndx ] )
	else:
	  values.append( 0.0 )
      result = np.array( values, dtype = np.float64 )

#		-- 'fixed_detector'
#		--
    elif ds_def[ 'type' ] == 'fixed_detector':
      values = []
      ds_shape = ds_def[ 'shape' ]
      ax_value = self.CreateAxialValue( value = axial_value )
      axial_level = max( 0, min( ax_value[ 3 ], ds_shape[ 0 ] - 1 ) )
      det_ndx = max( 0, min( detector_index, ds_shape[ 1 ] - 1 ) )
      for i in xrange( len( self.states ) ):
	dset = self.GetStateDataSet( i, ds_name )
	if dset is not None:
	  dset_value = np.array( dset )
	  values.append( dset_value[ axial_level, det_ndx ] )
	else:
	  values.append( 0.0 )
      result = np.array( values, dtype = np.float64 )

#		-- ':node'
#		--
    elif self.IsNodalType( ds_type ):
      if sub_addrs is not None and 'copy_shape' in ds_def:
        result = {}
        ds_shape = ds_def[ 'copy_shape' ]
        assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )
	node_addr_set = set()
        for sub_addr in sub_addrs:
	  node_addr = self.GetNodeAddr( sub_addr )
	  if node_addr not in node_addr_set:
	    node_addr_set.add( node_addr )
	    result[ node_addr ] = []
        node_addrs_sorted = sorted( node_addr_set )

        for i in xrange( len( self.states ) ):
	  dset = self.GetStateDataSet( i, ds_name )
	  if dset is None:
	    for node_addr in node_addrs_sorted:
	      result[ node_addr ].append( 0.0 )
	  else:
	    for node_addr in node_addrs_sorted:
	      value = dset[ 0, node_addr, axial_level, assy_ndx ]
	      result[ sub_addr ].append( value )
        #end for i

	for k in result:
	  result[ k ] = np.array( result[ k ], dtype = np.float64 )
      #end if sub_addrs and copy_shape

#		-- Others
#		--
    else:
      ds_shape = \
          ds_def[ 'copy_shape' ]  if 'copy_shape' in ds_def else \
	  ds_def[ 'shape' ]

      assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )
      ax_value = self.CreateAxialValue( value = axial_value )
      axial_level = max( 0, min( ax_value[ 1 ], ds_shape[ 2 ] - 1 ) )

      if ds_shape[ 0 ] > 1 and ds_shape[ 1 ] > 1 and sub_addrs is not None:
	result = {}
        sub_addr_set = set()
        for sub_addr in sub_addrs:
	  sub_addr = (
	      min( sub_addr[ 0 ], ds_shape[ 1 ] - 1 ),
	      min( sub_addr[ 1 ], ds_shape[ 0 ] - 1 )
	      )
	  sub_addr_set.add( sub_addr )
	  result[ sub_addr ] = []
        sub_addrs_sorted = sorted( sub_addr_set )

        #for st in self.states:
          #dset = st.GetDataSet( ds_name )
        for i in xrange( len( self.states ) ):
	  dset = self.GetStateDataSet( i, ds_name )
	  if dset is None:
	    for sub_addr in sub_addrs_sorted:
	      result[ sub_addr ].append( 0.0 )
	  else:
	    dset_value = np.array( dset )
	    for sub_addr in sub_addrs_sorted:
	      value = dset_value[
	          sub_addr[ 1 ], sub_addr[ 0 ], axial_level, assy_ndx
		  ]
	      result[ sub_addr ].append( value )
        #end for i

	for k in result:
	  result[ k ] = np.array( result[ k ], dtype = np.float64 )

      else:
	values = []
	#for st in self.states:
	#  dset = st.GetDataSet( ds_name )
        for i in xrange( len( self.states ) ):
	  dset = self.GetStateDataSet( i, ds_name )
	  if dset is not None:
	    dset_value = np.array( dset )
	    values.append( dset_value[ 0, 0, axial_level, assy_ndx ] )
	  else:
	    values.append( 0.0 )
	#end for st
        result = np.array( values, dtype = np.float64 )
      #end if-else ds_shape
    #end if-else ds[ 'type' ]

    return  result
  #end ReadDataSetValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadDataSetValues2()			-
  #----------------------------------------------------------------------
  def ReadDataSetValues2( self, *ds_specs_in ):
    """Reads values for a dataset across all state points, one state point
at a time for better performance.
@param  ds_specs_in	list of dataset specifications with the following keys:
	  assembly_addr		0-based assembly index
	  assembly_index	0-based assembly index
	  axial_cm		axial value in cm
	  detector_index	0-based detector index for detector datasets
	  ds_name		required dataset name
	  node_addrs		list of node addrs
	  sub_addrs		list of sub_addr pairs
@return			dict keyed by found ds_name of:
			  dict keyed by sub_addr of np.ndarray for pin-based
			  datasets,
			  np.ndarray for datasets that are not pin-based
"""
    result = {}

#		-- Loop on specs to get valid dataset definitions,
#		--   process 'state'
#		--
    ds_defs = {}
    ds_specs = []
    for spec in ds_specs_in:
      if spec is not None and 'ds_name' in spec:
        ds_name = spec[ 'ds_name' ]
	if ds_name == 'state':
	  result[ ds_name ] = \
	    np.array( range( 1, len( self.states ) + 1 ), dtype = np.float64 )
	elif ds_name not in ds_defs:
	  lookup_ds_name = ds_name[ 1 : ] if ds_name[ 0 ] == '*' else ds_name
	  ds_def = self.GetDataSetDefByDsName( lookup_ds_name )
	  #if ds_def is not None:
	  if ds_def is None:
	    ds_def = DATASET_DEFS[ 'scalar' ]
	  ds_defs[ ds_name ] = ds_def
	  ds_specs.append( spec )
	#end if-else ds_name
      #end if spec
    #end for

#		-- Process by looping on state points
#		--
    for state_ndx in xrange( len( self.states ) ):
      for spec in ds_specs:
        ds_name = spec[ 'ds_name' ]
	lookup_ds_name = ds_name[ 1 : ] if ds_name[ 0 ] == '*' else ds_name
	ds_def = ds_defs.get( ds_name )
        dset = self.GetStateDataSet( state_ndx, lookup_ds_name )
	dset_value = np.array( dset )
	ds_type = ds_def[ 'type' ]

	node_addrs = spec.get( 'node_addrs' )
	if node_addrs is not None and not hasattr( node_addrs, '__iter__' ):
	  node_addrs = [ node_addrs ]

        sub_addrs = spec.get( 'sub_addrs' )
        if sub_addrs is not None and not hasattr( sub_addrs, '__iter__' ):
          sub_addrs = [ sub_addrs ]

#			-- Scalar
#			--
	if ds_type == 'scalar':
	  if ds_name not in result:
	    result[ ds_name ] = []
	  value = 0.0  if dset is None else  dset_value.item()
	  result[ ds_name ].append( value )

#			-- Detector
#			--
	elif ds_type == 'detector' or ds_type == 'fixed_detector':
	  if ds_name not in result:
	    result[ ds_name ] = []

	  if dset is None:
	    value = 0.0
	  else:
            ds_shape = ds_def[ 'shape' ]
	    axial_cm = spec.get( 'axial_cm', 0.0 )
	    ax_ndx = 2 if ds_type == 'detector' else 3
            ax_value = self.CreateAxialValue( cm = axial_cm )
            #axial_ndx = max( 0, min( ax_value[ 2 ], ds_shape[ 0 ] - 1 ) )
            axial_ndx = max( 0, min( ax_value[ ax_ndx ], ds_shape[ 0 ] - 1 ) )

	    detector_ndx = spec.get( 'detector_index', 0 )
            det_ndx = max( 0, min( detector_ndx, ds_shape[ 1 ] - 1 ) )

	    dset_value = np.array( dset )
	    value = dset_value[ axial_ndx, det_ndx ]
	  result[ ds_name ].append( value )

#			-- Fixed detector
#			--
#	elif ds_type == 'fixed_detector':
#	  if ds_name not in result:
#	    result[ ds_name ] = []
#
#	  if dset is None:
#	    value = 0.0
#	  else:
#            ds_shape = ds_def[ 'shape' ]
#	    axial_cm = spec.get( 'axial_cm', 0.0 )
#            ax_value = self.CreateAxialValue( cm = axial_cm )
#            axial_ndx = max( 0, min( ax_value[ 3 ], ds_shape[ 0 ] - 1 ) )
#
#	    detector_ndx = spec.get( 'detector_index', 0 )
#            det_ndx = max( 0, min( detector_ndx, ds_shape[ 1 ] - 1 ) )
#
#	    value = dset.value[ axial_ndx, det_ndx ]
#	  result[ ds_name ].append( value )

#			-- :node
#			--
	elif self.IsNodalType( ds_type ):
          #if sub_addrs is not None and 'copy_shape' in ds_def:
          if 'copy_shape' in ds_def:
	    if ds_name in result:
	      ds_result = result[ ds_name ]
	    else:
	      ds_result = {}
	      result[ ds_name ] = ds_result

	    ds_shape = ds_def[ 'copy_shape' ]
            if dset is not None:
	      assembly_index = spec.get(
	          'assembly_index',
		  spec.get( 'assembly_addr', 0 )
		  )
              assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )

	      axial_cm = spec.get( 'axial_cm', 0.0 )
              ax_value = self.CreateAxialValue( cm = axial_cm )
              axial_ndx = max( 0, min( ax_value[ 1 ], ds_shape[ 2 ] - 1 ) )

	    node_addr_set = set()
	    if node_addrs is None:
	      node_addr_set.add( ( 0, -1 ) )
	    else:
	      for node_ndx in node_addrs:
		cur_pair = ( self.NormalizeNodeAddr( node_ndx ), -1 )
		node_addr_set.add( cur_pair )

	    for node_addr in sorted( node_addr_set ):
	      if node_addr not in ds_result:
	        ds_result[ node_addr ] = []
              value = 0.0
              if dset is not None:
	        dset_value = np.array( dset )
	        value = dset_value[ 0, node_addr[ 0 ], axial_ndx, assy_ndx ]
              ds_result[ node_addr ].append( value )
	    #end if-else node_addrs
	  #end if copy_shape

#			-- Others are pin-based
#			--
	else:
	  #sub_addrs = spec.get( 'sub_addrs' )

#				-- Must have sub_addrs
          if sub_addrs is not None:
            ds_shape = \
                ds_def[ 'copy_shape' ]  if 'copy_shape' in ds_def else \
	        ds_def[ 'shape' ]

            if dset is not None:
	      assembly_index = spec.get(
	          'assembly_index',
		  spec.get( 'assembly_addr', 0 )
		  )
              assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )

	      axial_cm = spec.get( 'axial_cm', 0.0 )
              ax_value = self.CreateAxialValue( cm = axial_cm )
              axial_ndx = max( 0, min( ax_value[ 1 ], ds_shape[ 2 ] - 1 ) )

            if ds_shape[ 0 ] > 1 and ds_shape[ 1 ] > 1:
	      if ds_name in result:
	        ds_result = result[ ds_name ]
	      else:
	        ds_result = {}
	        result[ ds_name ] = ds_result

              sub_addr_set = set()
              for sub_addr in sub_addrs:
	        sub_addr = (
	            min( sub_addr[ 0 ], ds_shape[ 1 ] - 1 ),
	            min( sub_addr[ 1 ], ds_shape[ 0 ] - 1 )
	            )
		if sub_addr not in sub_addr_set:
	          sub_addr_set.add( sub_addr )
		  if sub_addr not in ds_result:
		    ds_result[ sub_addr ] = []
		  value = 0.0
		  if dset is not None:
	            value = dset.\
		      value[ sub_addr[ 1 ], sub_addr[ 0 ], axial_ndx, assy_ndx ]
		  ds_result[ sub_addr ].append( value )
	      #end for sub_addr

	    else:
	      if ds_name not in result:
	        result[ ds_name ] = []

	      value = 0.0
	      if dset is not None:
		dset_value = np.array( dset )
		if dset_value.size == 1:
		  value = dset_value.item()
		else:
	          value = dset_value[ 0, 0, axial_ndx, assy_ndx ]
	      result[ ds_name ].append( value )
            #end if-else ds_shape
	  #end if sub_addrs specified
        #end if-else ds_def[ 'type' ]
      #end for spec
    #end for state_ndx

#		-- Convert arrays to np.ndarrays
#		--
    for k in result:
      if isinstance( result[ k ], dict ):
	for k2 in result[ k ]:
	  result[ k ][ k2 ] = np.array( result[ k ][ k2 ], dtype = np.float64 )
      else:
	result[ k ] = np.array( result[ k ], dtype = np.float64 )
    #end for k, item

    return  result
  #end ReadDataSetValues2


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.RemoveListener()			-
  #----------------------------------------------------------------------
  def RemoveListener( self, event_name, listener ):
    """
@param  event_name	either 'newDataSet' or 'newFile'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      for listener in self.listeners[ event_name ]:
        del self.listeners[ event_name ][ listener ]
    #end if event_name
  #end RemoveListener


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
	      if def_name != 'scalar' and def_item[ 'shape' ] == scalar_shape:
	        #for ds_prefix in def_item[ 'ds_prefix' ].split( ',' ):
	        for ds_prefix in def_item[ 'ds_prefix' ]:
		  if cur_name.startswith( ds_prefix + '_' ):
		    cat_name = def_name
		    break
		if cat_name:
		  break
	      #end if def_name
	    #end for def_name, def_item
	  #end if-else on cur_name

	  if cat_name is None:
	    cat_name = 'scalar'
	  ds_names[ cat_name ].append( cur_name )

	  ds_defs_by_name[ cur_name ] = ds_defs.get( cat_name )

#			-- Detector is special case
#			--
#	elif cur_name == 'detector_response':
	elif cur_name.find( 'response' ) >= 0:
	  if cur_shape == ds_defs[ 'detector' ][ 'shape' ]:
	    ds_names[ 'detector' ].append( cur_name )
	    ds_names[ 'axial' ].append( cur_name )
	    ds_defs_by_name[ cur_name ] = ds_defs[ 'detector' ]

#			-- Fixed detector is special case
#			--
	elif cur_name == 'fixed_detector_response' and \
	    cur_shape == ds_defs[ 'fixed_detector' ][ 'shape' ] and \
	    core.fixedDetectorMeshCenters is not None:
	  ds_names[ 'fixed_detector' ].append( cur_name )
	  ds_names[ 'axial' ].append( cur_name )
	  ds_defs_by_name[ cur_name ] = ds_defs[ 'fixed_detector' ]

#			-- Not a scalar
#			--
	else:
	  cat_item_maybe = None
	  cat_item = None
	  for def_name, def_item in ds_defs.iteritems():
#	    if cur_shape == def_item[ 'shape' ] and \
#	      (def_name != 'fixed_detector' or core.fixedDetectorMeshCenters is None):
	    if def_name in ( 'detector', 'fixed_detector' ):
	      pass
	    elif cur_shape == def_item[ 'shape' ]:
	      if 'ds_prefix' not in def_item:
	        cat_item = def_item
	      else:
	        if cat_item_maybe is None:
	          cat_item_maybe = def_item
	        #for ds_prefix in def_item[ 'ds_prefix' ].split( ',' ):
	        for ds_prefix in def_item[ 'ds_prefix' ]:
	          if cur_name.startswith( ds_prefix + '_' ):
		    cat_item = def_item
		    break
	      #end if-else 'ds_prefix' defined

	      if cat_item:
	        break
	    #end if shape match
	  #end for def_name, def_item

	  if cat_item is None and cat_item_maybe is not None:
	    cat_item = cat_item_maybe
	  if cat_item is not None:
	    ds_names[ cat_item[ 'type' ] ].append( cur_name )
	    ds_defs_by_name[ cur_name ] = cat_item

	    cur_shape_expr = cat_item[ 'shape_expr' ]
	    if cur_shape_expr.find( 'core.nax' ) >= 0 or \
	        cur_shape_expr.find( 'core.ndetax' ) >= 0 or \
		cur_shape_expr.find( 'core.nfdetax' ) >= 0:
	      ds_names[ 'axial' ].append( cur_name )
	  #if cat_item
        #end if-else on shape
      #end if not a copy
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
  #end ResolveDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.RevertIfDerivedDataSet()		-
  #----------------------------------------------------------------------
  def RevertIfDerivedDataSet( self, ds_name ):
    """If ds_name is a derived dataset, return the first dataset of the
base type.  Calls GetFirstDataSet().
Note: We are now hard-coding this to look for ':chan_xxx' for
a derived type, in which case we pass 'channel' to GetFirstDataSet().  For all
other derived types we pass 'pin'.
@param  ds_name		candidate ds_name
@return			ds_name if it is not derived, the first dataset from
			the base category/type if it is derived
"""
    ds_type = self.GetDataSetType( ds_name ) if ds_name else None
    if ds_type:
      ndx = ds_type.find( ':' )
      if ndx >= 0:
        #base_type = ds_type[ 0 : ndx ]
        base_type = 'channel' if ds_type.find( ':chan_' ) == 0 else 'pin'
	ds_name = self.GetFirstDataSet( base_type )
    #end if

    return  ds_name
  #end RevertIfDerivedDataSet


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
  #	METHOD:		DataModel.CreateEmptyAxialValue()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateEmptyAxialValue():
    """
@return			( axial_cm, core_ndx, detector_ndx, fixed_detector_ndx )
			as ( 0.0, -1, -1, -1 )
"""
    return  ( 0.0, -1, -1, -1 )
  #end CreateEmptyAxialValue


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
#  @staticmethod
#  def IsExtra( ds_name ):
#    """Checks for the 'extra:' prefix.
#@return			True if ds_name is an extra dataset, False otherwise
#"""
#    return  ds_name.startswith( 'extra:' )
#  #end IsExtra


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
  #	METHOD:		DataModel.ToAddrString()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ToAddrString( col, row ):
    """Convenience method to convert from 0-based indices to Fortran
1-based indices.
@param  col		0-based column index
@param  row		0-based row index
@return			"( col + 1, row + 1 )"
"""
    #return  '(%d,%d)' % ( col + 1, row + 1 )
    return  \
        '(%d,%d)' % ( col + 1, row + 1 )  if row >= 0 else \
        '(%d)' % (col + 1)
  #end ToAddrString


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
#    if self.pinPowers is None:
#      missing.append( '%s missing PIN_POWERS' % self.name )
#    elif self.pinPowers.shape[ 0 ] != core.npin or \
#        self.pinPowers.shape[ 1 ] != core.npin or \
#        self.pinPowers.shape[ 2 ] != core.nax or \
#        self.pinPowers.shape[ 3 ] != core.nass:
#      missing.append( '%s PIN_POWERS shape is not consistent with NPIN, NAX, and NASS' % self.name )

    if 'detector_operable' in self.group and \
        self.group[ 'detector_operable' ].shape[ 0 ] != core.ndet:
      missing.append( '%s DETECTOR_OPERABLE shape is not consistent with NDET' % self.name )

# Come back to this with beavrs.h5, errors vs warnings where dataset not used
#    if 'detector_response' in self.group and \
#        self.group[ 'detector_response' ].shape != ( core.ndetax, core.ndet ):
#      missing.append( '%s DETECTOR_RESPONSE shape is not consistent with NDETAX and NDET' % self.name )

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
    """Retrieves the dataset from the state point.  Note this method does
NOT process derived datasets as does DataModel.GetStateDataSet().
@param  ds_name		dataset name
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
        self.exposure = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
        #self.exposure = item.value.item() if len( item.shape ) > 0 else item.value

      if 'keff' in state_group:
        #self.keff = state_group[ 'keff' ].value[ 0 ]
	item = state_group[ 'keff' ]
        self.keff = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
        #self.keff = item.value.item() if len( item.shape ) > 0 else item.value

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
      obj[ 'exposure' ] = self.exposure
    if self.keff is not None:
      obj[ 'keff' ] = self.keff

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
  #	METHOD:		State.ResolveTimeDataSets()			-
  #----------------------------------------------------------------------
  @staticmethod
  def ResolveTimeDataSets( states ):
    """
@param  states		list of State objects
@return			list of time datasets, always including 'state'
"""
    time_ds_names = set( TIME_DS_NAMES )
    remove_list = []

    for st in states:
      del remove_list[ : ]
      for name in time_ds_names:
        if not st.HasDataSet( name ):
	  remove_list.append( name )
      #end for

      for name in remove_list:
        time_ds_names.remove( name )

      if len( time_ds_names ) == 0:
        break
    #end for st

    time_ds_names.add( 'state' )

    return  list( time_ds_names )
  #end ResolveTimeDataSets


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
