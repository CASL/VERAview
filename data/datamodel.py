#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel.py					-
#	HISTORY:							-
#		2018-07-26	leerw@ornl.gov				-
#	  Renaming non-derived dataset category/type from 'axial' to
#	  'axials' to disambiguate from ':axial' displayed name.
#		2018-07-18	leerw@ornl.gov				-
#	  Modified _ReadDataSetRange() to account for negative values
#	  when range_min == range_max.
#		2018-05-29	leerw@ornl.gov				-
#	  Bug fix: can't use capitalize() b/c it lowers all but first char.
#		2018-05-25	leerw@ornl.gov				-
#	  Fixed GetFirstDataSet() to accept a CORE group dataset if there
#	  are no others.
#	  Fixed _InferCoreLabelsSimply() to handle weird shapes exhibited
#	  in p10.h5.
#		2018-05-21	leerw@ornl.gov				-
#	  Added GetDerivableFuncsAndTypes() and derivableFuncsAndTypes
#	  property.
#		2018-03-15	leerw@ornl.gov				-
#	  Checking for negative values in 'log' scale_type in
#	  DataModel._ReadDataSetRange(), setting negatives to np.nan.
#		2018-03-08	leerw@ornl.gov				-
#	  Added dataSetScaleTypes property to DataModel.
#		2018-02-15	leerw@ornl.gov				-
#	  Fixed bug in DataModel.GetStateDataSet() determining if the
#	  dataset to be copied is scalar, cannot be based on size property.
#		2018-02-06	leerw@ornl.gov				-
#	  Fixed CORE group dataset processing for datasets that require
#	  a copy.
#		2018-02-03	leerw@ornl.gov				-
#	  Adding processing of CORE group datasets.
#		2018-01-19	leerw@ornl.gov				-
#	  Converting to google doc guidelines.
#		2018-01-10	leerw@ornl.gov				-
#	  Ensuring core.npin is assigned in Core._ReadImpl().
#		2017-12-15	leerw@ornl.gov				-
#	  Expanding FindMinMaxValueAddr() with assy_def param.
#		2017-12-14	leerw@ornl.gov				-
#	  Added DataModel.FixDuplicates(), called from
#	  ReadDataSetTimeValues().
#		2017-12-01	leerw@ornl.gov				-
#	  Added TallyAddress.Equals().
#		2017-10-31	leerw@ornl.gov				-
#	  Added special core.netdet != core.nass check for "radial_detector"
#	  datasets in DataModel._ResolveDataSets().
#		2017-09-26	leerw@ornl.gov				-
#	  First cut at FindTallyMinMaxValue{Addr}().
#		2017-09-25	leerw@ornl.gov				-
#	  Adding FindTallyMinMaxValue().
#	  Changed TallyAddress to store thetaIndex and add radiusIndex.
#		2017-09-23	leerw@ornl.gov				-
#	  Added TallyAddress class.
#		2017-08-16	leerw@ornl.gov				-
#	  Began AxialValue class.
#		2017-07-20	leerw@ornl.gov				-
#	  Checking for 'threshold' dataset attribute in STATE_0001.
#	  Added DataModel.readMessages property to record warning messages
#	  during Read().
#		2017-07-18	leerw@ornl.gov				-
#	  Replacing ignore range with threshold and using RangeExpression.
#		2017-07-17	leerw@ornl.gov				-
#	  Adding by ds_name ignore ranges.
#	  Modified _ReadDataSetRange() to check for a specified
#	  invalid range.  Calls DataUtils.ApplyIgnoreExpression().
#		2017-06-16	leerw@ornl.gov				-
#	  Fixed _ReadDataSetRange.
#		2017-06-05	leerw@ornl.gov				-
#	  Just keeping dicts of per-dataset mesh and mesh center values.
# 	  Moved axialMeshCentersDict and axialMeshDict properties to
#	  DataModel from Core.
#		2017-06-02	leerw@ornl.gov				-
#	  Adding support for per-dataset axial meshes.
#		2017-05-31	leerw@ornl.gov				-
#	  Added subpin_r and subpin_theta types.
#		2017-04-25	leerw@ornl.gov				-
#	  Added VesselGeometry.Read() and Core property vesselGeom.
#	  Moved ExtractSymmetryExtent() implementation to Core.
#		2017-04-03	leerw@ornl.gov				-
#	  Added VesselGeometry.
#	  Skipping non-numeric scalars in _ResolveDataSets().
#		2017-03-27	leerw@ornl.gov				-
#	  Fixing VesselTallyMesh, adding 'tally' dataset defs as a one-off.
#	  Renaming VesselTallyMesh to VesselTallyDef.
#		2017-03-25	leerw@ornl.gov				-
#	  Added DataSetName.GetShortName() and shortName property.
#		2017-03-16	leerw@ornl.gov				-
#	  Added TIME_DS_NAMES_LIST.  Copying all time datasets in
#	  DataModel._CreateDerivedH5File().
#		2017-03-07	leerw@ornl.gov				-
#	  Modified DataModel.GetFactors() to look for 'factors' attribute.
#		2017-03-04	leerw@ornl.gov				-
#	  Added __ge__(), __gt__(), __le__(), and __lt__() to DataSetName.
#		2017-02-25	leerw@ornl.gov				-
#	  Added Core.FindBottomRightAssemblyAddr(), VesselTallyMesh class,
#	  Core vesselTallyMesh property.
#		2016-12-28	leerw@ornl.gov				-
#	  Added HasDetectorData().
#		2016-12-12	leerw@ornl.gov				-
#	  Moved IsValidRange(), ToAddrString() to DataUtils.
#		2016-12-07	leerw@ornl.gov				-
#	  Fixed _FireEvent() call in AddDataSetName() to not pass self
#	  as self is added to the params list by _FireEvent().
#		2016-12-01	leerw@ornl.gov				-
#	  Added DataSetName class to use instead of DataSetNamer.
#	  Added DataSetNamer and DATASET_NAMER singleton.
#	  Removed id property from DataModel, added SetName().
#		2016-11-30	leerw@ornl.gov				-
#	  Moved FindListIndex to DataUtils.
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
#		2016-08-19	leerw@ornl.gov				-
#	  Added "id" property.
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
"""Classes representing a single VERAOutput HDF5 file.

This module provides classes for reading and processing data in a single
VERAOutput HDF5 file.
"""
import bisect, copy, cStringIO, h5py, logging, json
import math, os, re, six, sys, tempfile, threading, traceback
import numpy as np
import pdb

from data.range_expr import *
from data.utils import *
from event.event import *


#------------------------------------------------------------------------
#	CONST:		AGGREGATION_FUNCS				-
#------------------------------------------------------------------------
AGGREGATION_FUNCS = [ 'avg', 'max', 'min' ]
"""list(str): List of available aggregation functions.
"""


#------------------------------------------------------------------------
#	CONST:		AUTO_DERIVED_SCALAR_DEFS			-
#------------------------------------------------------------------------
AUTO_DERIVED_SCALAR_DEFS = \
  {
  'axial_offset':
    {
    'averager': 'pin',
    'datasets': 'pin_powers',
    'method': 'calc_axial_offset'
    }
  }
"""dict(str,dict): Dictionary of scalars to automatically derive keyed by
dataset name.  If the scalar dataset is not present, it is calculated.  Whether
or not the dataset can be derived (if not already present) is determined by the
existence of the ``averager`` and input ``datasets``, in which case
the ``method`` is called to create the scalar dataset.
"""


#------------------------------------------------------------------------
#	CONST:		AVERAGER_DEFS					-
#------------------------------------------------------------------------
AVERAGER_DEFS = \
  {
  'channel': 'data.channel_averages.Averages',
  'pin': 'data.pin_averages.Averages'
  }
"""dict(str,str): Dictionary of averager implementations keyed by dataset
type.  In theory there should be an entry here for every ``avg_method``
key in a DATASET_DEFS entry below, but we use ``pin`` for a default.
"""


#------------------------------------------------------------------------
#	CONST:		COL_LABELS					-
#------------------------------------------------------------------------
COL_LABELS = \
  (
    'R', 'P', 'N', 'M', 'L', 'K', 'J', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A'
  )
"""tuple(str): In-order labels for core columns."""


#------------------------------------------------------------------------
#	CONST:		CORE_SKIP_DS_NAMES
#------------------------------------------------------------------------
CORE_SKIP_DS_NAMES = set([
    "apitch", "axial_mesh", "core_map", "coresym", "core_sym",
    "detector", "detector_map", "detector_mesh", "detector_response",
    "fixed_detector", "fixed_detector_mesh", "fixed_detector_response",
    "label_format",
    "nass", "nax", "npin", "npinx", "npiny", "nsubr", "nsubtheta",
    "subpin_axial_mesh", "subpin_r", "subpin_theta",
    "xlabel", "ylabel"
    ])
"""set(str): Names of datasets in CORE that will never be processed as
datasets."""


#------------------------------------------------------------------------
#	CONST:		DATASET_DEFS					-
#------------------------------------------------------------------------
DATASET_DEFS = \
  {
  'channel':
    {
    'assy_axis': 3,
    'axial_axis': 2,
    'label': 'channel',
    'shape_expr': '( core.npiny + 1, core.npinx + 1, core.nax, core.nass )',
    'type': 'channel'
    },

  'detector':
    {
    'assy_axis': 1,
    'axial_axis': 0,
    'label': 'detector',
    'shape_expr': '( core.ndetax, core.ndet )',
    'type': 'detector'
    },

  'fixed_detector':
    {
    'assy_axis': 1,
    'axial_axis': 0,
    'label': 'fixed_detector',
    'shape_expr': '( core.nfdetax, core.ndet )',
    'type': 'fixed_detector'
    },

#  ':det_radial':
#    {
#    'axial_axis': 0,
#    'copy_expr': '[ 0, : ]',
#    'copy_shape_expr': '( 1, core.ndet )',
#    'ds_prefix': ( 'det_radial', ),
#    'label': 'det_radial',
#    'shape_expr': '( core.ndet, )',
#    'type': 'det_radial'
#    },

  'pin':
    {
    'assy_axis': 3,
    'axial_axis': 2,
    'label': 'pin',
    'shape_expr': '( core.npiny, core.npinx, core.nax, core.nass )',
    'type': 'pin'
    },

  'radial_detector':  # force to detector by copying
    {
    'assy_axis': -1,
    'axial_axis': -1,
    'label': 'radial_detector',
    'shape_expr': '( core.ndet, )',
    'type': 'radial_detector'
    },

  ':assembly':
    {
    'assy_axis': 3,
    'avg_method':
      {
      'channel': 'calc_channel_assembly_avg',
      'pin': 'calc_pin_assembly_avg'
      },
    'axial_axis': 2,
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
    'assy_axis': -1,
    'avg_method':
      {
      'channel': 'calc_channel_axial_avg',
      'pin': 'calc_pin_axial_avg'
      },
    'axial_axis': 2,
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
    'assy_axis': 3,
    #'avg_method': 'calc_channel_radial_avg',
    'avg_method': { 'channel': 'calc_channel_radial_avg' },
    'axial_axis': -1,
    'copy_expr': '[ :, :, 0, : ]',
    'copy_shape_expr': '( core.npiny + 1, core.npinx + 1, 1, core.nass )',
    'ds_prefix': ( 'radial', 'ch_radial' ),
    'label': 'chan_radial',  # '2D pin'
    'shape_expr': '( core.npiny + 1, core.npinx + 1, core.nass )',
    'type': ':chan_radial'
    },

  ':core':
    {
    'assy_axis': -1,
    'avg_method':
      {
      'channel': 'calc_channel_core_avg',
      'pin': 'calc_pin_core_avg'
      },
    'axial_axis': -1,
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
    'assy_axis': 3,
    'avg_method':
      {
      'pin': 'calc_pin_node_avg'
      },
    'axial_axis': 2,
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
    'assy_axis': 3,
    'avg_method':
      {
      'pin': 'calc_pin_radial_avg'
      },
    'axial_axis': -1,
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
    'assy_axis': 3,
    'avg_method':
      {
      'pin': 'calc_pin_radial_assembly_avg'
      },
    'axial_axis': -1,
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
    'assy_axis': 3,
    'avg_method':
      {
      'pin': 'calc_pin_radial_node_avg'
      },
    'axial_axis': -1,
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
    'assy_axis': -1,
    'axial_axis': -1,
    'label': 'scalar',
    'shape_expr': '( 1, )',
    'type': 'scalar'
    },

#  ':scalar':
#    {
#    'assy_axis': -1,
#    'axial_axis': -1,
#    'datasets':
#      {
#      'axial_offset':
#        {
#	'input': 'pin_powers',
#	'factors': 'pinWeights',
#	'method': { 'pin': 'calc_axial_offset' }
#	}
#      },
#    'label': 'scalar',
#    'shape_expr': '( 1, )',
#    'type': ':scalar'
#    },

  'subpin':
    {
    'assy_axis': 5,
    'axial_axis': 4,
    'label': 'subpin_theta',
    'shape_expr': '( core.nsubtheta, core.nsubr, core.npiny, core.npinx, core.nsubax, core.nass )',
    'type': 'subpin'
    },

  #?
  'subpin_cc':
    {
    'assy_axis': 5,
    'axial_axis': 4,
    'label': 'subpin_theta',
    'shape_expr': '( 2, core.nsubtheta, core.npiny, core.npinx, core.nsubax, core.nass )',
    'type': 'subpin_cc'
    },

  'subpin_r':
    {
    'assy_axis': 4,
    'axial_axis': 3,
    'label': 'subpin_r',
    'shape_expr': '( core.nsubr, core.npiny, core.npinx, core.nsubax, core.nass )',
    'type': 'subpin_r'
    },

  'subpin_theta':
    {
    'assy_axis': 4,
    'axial_axis': 3,
    'label': 'subpin_theta',
    'shape_expr': '( core.nsubtheta, core.npiny, core.npinx, core.nsubax, core.nass )',
    'type': 'subpin_theta'
    },

  'tally':
    {
    'assy_axis': -1,
    'axial_axis': 0,
    'group': 'vessel_tally',
    'label': 'tally',
    'shape_expr': '( core.tally.nz, core.tally.ntheta, core.tally.nr, core.tally.nmultipliers, core.tally.nstat )',
    'type': 'tally'
    },
  }
"""dict(str,dict): Dictionary of dataset category/type definitions
keyed by type name.  The naming scheme for derived types is now just a
':' prefix.  Whether or not a type can be derived from a dataset is determined
by the keys in the ``avg_method`` value.

All types have keys:
  (group)	- optional to define group in which to look for matching
		  datasets
  assy_axis	- dataset axis for the assembly index, index of "core.nass"
		  or "core.ndet" in 'copy_shape_expr' or 'shape_expr'
  axial_axis	- dataset axis for the axial mesh, index of "core.nax",
		  "core.ndetax", "core.nfdetax", "core.nsubax", or
		  "core.tally.nz" in 'copy_shape_expr' or 'shape_expr'
  label		- name used in displays
  shape_expr    - shape expression used to match datasets against to determine
		  if they are of the type, where 'core' references the Core
		  instance
  type		- echo of the type name key

Derived types have keys:
  avg_method    - dictionary keyed by category/type of averager methods, where
		  '*' is default
  copy_expr     - lhs expression for numpy array assignment (should be all ':'
		  and '0' entries)
  copy_shape_expr - tuple defining 4D shape of copy, with '1' in flattened
		  dimensions
  ds_prefix     - tuple of prefix names to use in matching datasets read from
		  the VERAOutput file

Some day we should convert these to objects with properties.
"""


#------------------------------------------------------------------------
#	CONST:		TIME_DS_NAMES					-
#------------------------------------------------------------------------
# List is preference order for the default
TIME_DS_NAMES_LIST = [
    'msecs', 'exposure', 'exposure_efpd', 'exposure_efpy',
    'hours', 'transient_time'
    ]
"""list(str): Dataset names we recognize as "time" datasets.  The statepoint
index (``state``) is always added as a time alternative.
"""

TIME_DS_NAMES = set( TIME_DS_NAMES_LIST )
"""set(str): Set of dataset names recognized as "time" datasets."""


#------------------------------------------------------------------------
#	CLASS:		AxialValue					-
#------------------------------------------------------------------------
class AxialValue( dict ):
  """Encapsulates an axial value and all possible axial meshes.
  
New mesh feature.  Each dataset can have a "mesh:xxx" attribute which is an
ndarray of shape (1,) whose values are comma-delimited strings specifying 3
(piny, pinx, assy), 2 (piny, pinx), or 1 (assy) index value tuples, either
3-tuples (piny, pinx, assy), 2-tuples (piny, pinx) or scalar assy, specifying
the pins and/or assemblies to which "mesh:xxx" applies.  Further "mesh:xxx" is
a dataset in CORE.

Modify DataModel.GetAxialMesh() to look this up and also consider (piny, pinx,
assy).
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__eq__()				-
  #----------------------------------------------------------------------
  def __eq__( self, that ):
    """Equivalence operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if that is an ``AxialValue`` instance and has the same
            ``cm`` property value as self.
"""
    return  isinstance( that, AxialValue ) and self.cm == that.cm
  #end __eq__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__ge__()				-
  #----------------------------------------------------------------------
  def __ge__( self, that ):
    """Greater-than-or-equal operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if that is an ``AxialValue`` instance, and self.cm is
            ge that.cm.
"""
    return  self.cm >= that.cm  if isinstance( that, AxialValue ) else False
  #end __ge__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__getitem__()			-
  #----------------------------------------------------------------------
  def __getitem__( self, ndx ):
    """Item index operator.

    Args:
        ndx (int): 0-based index

    Returns:
        int or float: property value by index or -1 if ``ndx`` is out of range.

        ======= =======================
        ``ndx`` Property
        ------- -----------------------
              0 ``cm``
	      1 ``pinIndex``
	      2 ``detectorIndex``
	      3 ``fixedDetectorIndex``
	      4 ``tallyIndex``
	      5 ``subPinIndex``
        ======= =======================
"""
    result = None
    if isinstance( ndx, int ):
      result = \
	  self.GetCm()  if ndx == 0 else \
	  self.GetPinIndex()  if ndx == 1 else \
	  self.GetDetectorIndex()  if ndx == 2 else \
	  self.GetFixedDetectorIndex()  if ndx == 3 else \
	  self.GetTallyIndex()  if ndx == 4 else \
	  self.GetSubPinIndex()  if ndx == 5 else \
	  -1
    else:
      result = super( AxialValue, self ).__getitem__( ndx )
    return  result
  #end __getitem__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__gt__()				-
  #----------------------------------------------------------------------
  def __gt__( self, that ):
    """Greater-than operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if that is an ``AxialValue`` instance, and self.cm is
            gt that.cm.
"""
    return  self.cm > that.cm  if isinstance( that, AxialValue ) else False
  #end __gt__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__hash__()				-
  #----------------------------------------------------------------------
  def __hash__( self ):
    """Hash function.

    Returns:
        int: has based on self.cm
"""
    return  int( self.cm * 1.e4 )
  #end __hash__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """Constructs an instance in the same manner as any ``dict``.
    
    Basically, there are two forms of valid initialization.  The first
    provides a series of property params and values.  The second provides
    another dict from which to initialize.
    Forms of valid initialization:

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
            ``cm``: ``cm`` property value
	    ``detector``: ``detectorIndex`` property value
	    ``fixed_detector``: ``fixedDetectorIndex`` property value
	    ``pin``: ``pinIndex`` property value
	    ``subpin``: ``subPinIndex`` property value
	    ``tally``: ``tallyIndex`` property value
    Other Parameter:
    Keyword Args:
        cm (float): ``cm`` property value
	detector (int): 0-based ``detectorIndex`` property
	fixed_detector (int): 0-based ``fixedDetectorIndex`` property
	pin (int): 0-based ``pinIndex`` property
	subpin (int): 0-based ``subPinIndex`` property
	tally (int): 0-based ``tallyIndex`` property
"""
    super( AxialValue, self ).__init__( *args, **kwargs )
    self[ '__jsonclass__' ] = 'data.datamodel.AxialValue'
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__le__()				-
  #----------------------------------------------------------------------
  def __le__( self, that ):
    """Less-than-or-equal operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if that is an ``AxialValue`` instance, and self.cm is
            le that.cm.
"""
    return  self.cm <= that.cm  if isinstance( that, AxialValue ) else False
  #end __le__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__lt__()				-
  #----------------------------------------------------------------------
  def __lt__( self, that ):
    """Less-than operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if that is an ``AxialValue`` instance, and self.cm is
            lt that.cm.
"""
    return  self.cm < that.cm  if isinstance( that, AxialValue ) else False
  #end __lt__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__ne__()				-
  #----------------------------------------------------------------------
  def __ne__( self, that ):
    """Non-equivalence operator.

    Args:
        that (obj): comparison object

    Returns:
        bool: True if self ne that.
"""
    return  not self.__eq__( that )
  #end __ne__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__repr__()				-
  #----------------------------------------------------------------------
#  def __repr__( self ):
#    return  'datamodel.AxialValue(%s)' % str( self )
#  #end __repr__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.__str__()				-
  #----------------------------------------------------------------------
#  def __str__( self ):
#    return  self._name
#  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetCm()				-
  #----------------------------------------------------------------------
  def GetCm( self ):
    """float: Current value in cm, alias for the ``value`` property."""
    return  self.get( 'cm', 0.0 )
  #end GetCm


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetDetectorIndex()			-
  #----------------------------------------------------------------------
  def GetDetectorIndex( self ):
    """int: 0-based detector mesh index, where -1 means unknown."""
    return  self.get( 'detector', -1 )
  #end GetDetectorIndex


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetFixedDetectorIndex()		-
  #----------------------------------------------------------------------
  def GetFixedDetectorIndex( self ):
    """int: 0-based fixed detector mesh centers index, where -1 means unknown.
"""
    return  self.get( 'fixed_detector', -1 )
  #end GetFixedDetectorIndex


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetPinIndex()			-
  #----------------------------------------------------------------------
  def GetPinIndex( self ):
    """int: 0-based core/pin mesh centers index, where -1 means unknown."""
    return  self.get( 'pin', -1 )
  #end GetPinIndex


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetSubPinIndex()			-
  #----------------------------------------------------------------------
  def GetSubPinIndex( self ):
    """int: 0-based subpin mesh centers index, where -1 means unknown."""
    return  self.get( 'subpin', -1 )
  #end GetSubPinIndex


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetTallyIndex()			-
  #----------------------------------------------------------------------
  def GetTallyIndex( self ):
    """int: 0-based tally mesh index, where -1 means unknown."""
    return  self.get( 'tally', -1 )
  #end GetTallyIndex


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.GetValue()				-
  #----------------------------------------------------------------------
  def GetValue( self ):
    """float: Current value in cm, alias for the ``cm`` property."""
    return  self.get( 'cm', 0.0 )
  #end GetValue


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.tojson()				-
  #----------------------------------------------------------------------
  def tojson( self ):
    """Serializes to a JSON/dict object.

    Basically a noop for this class.

    Returns:
        dict: self.
"""
    return  self
  #end tojson


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	cm						-
  #----------------------------------------------------------------------
  cm = property( GetCm )


  #----------------------------------------------------------------------
  #	PROPERTY:	detectorIndex					-
  #----------------------------------------------------------------------
  detectorIndex = property( GetDetectorIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	fixedDetectorIndex				-
  #----------------------------------------------------------------------
  fixedDetectorIndex = property( GetFixedDetectorIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	pinIndex					-
  #----------------------------------------------------------------------
  pinIndex = property( GetPinIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	subPinIndex					-
  #----------------------------------------------------------------------
  subPinIndex = property( GetSubPinIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	tallyIndex					-
  #----------------------------------------------------------------------
  tallyIndex = property( GetTallyIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	value						-
  #----------------------------------------------------------------------
  value = property( GetValue )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		AxialValue.fromjson()				-
  #----------------------------------------------------------------------
  @staticmethod
  def fromjson( dict_in ):
    """Deserializes an instance from a JSON/dict object.

    Returns:
        AxialValue: ``AxialValue`` instance constructed from ``dict_in``.
"""
    return  AxialValue( dict_in )
  #end fromjson

#end AxialValue


#------------------------------------------------------------------------
#	CLASS:		Core						-
#------------------------------------------------------------------------
class Core( object ):
  """Data/model bean encapsulating depletion 'CORE' data.
  
  Underlying data are stored in a numpy array, but this detail should be hidden
  and abstracted by this class.  as needed.

  Core datasets have shape ( npin, npin, nax, nass ) and are indexed by
  0-based indexes [ pin_row, pin_col, axial_level, assy_ndx ]

  Attributes:
      apitch (float): Assembly pitch in cm
      axialMesh (np.ndarray): Core/pin mesh values
      axialMeshCenters (np.ndarray): Core/pin mesh center values
      coreLabels (list(list)): ( column_labels, row_labels )
      coreMap (np.ndarray): 1-based assembly indexes in row-major order
          with the origian at the top, left (row, col), the shape is
	  (nassy, nassy)
      coreSym (int): Symmetry value (1-full, 4-quarter)
      detectorMap (np.ndarray): 1-based assembly indexes (row, col), the
          shape is (nassy, nassx)
      detectorMesh (np.ndarray): Detector mesh center values
      fixedDetectorMesh (np.ndarray): Fixed detector mesh values
      fixedDetectorMeshCenters (np.ndarray): Fixed detector mesh center
          values
      group (h5py.Group): CORE group object
      nass (int): number of full core assemblies
      nassx (int): number of core assembly columns
      nassy (int): number of core assembly rows
      nax (int): number of core/pin axial levels
      nchanx (int): number of core channel columns, should be npinx + 1
      nchany (int): number of core channel rows, should be npiny + 1
      ndet (int): number of detectors
      ndetax (int): number of detector axial levels
      nfdetax (int): number of fixed detector axial levels
      npin (int): number of pins in each assembly, max( npinx, npiny )
      npinx (int): number of pin columns in each assembly
      npiny (int): number of pin rows in each assembly
      nsubax (int): number of subpin axial levels
      nsubr (int): number of subpin radii
      nsubtheta (int): number of subpin thetas
      pinVolumes (np.ndarray): pin volumes in row-major order, origin at
          (top, left)
      pinVolumesSum (float): sum of pin volumes (do we still need this?)
      subPinAxialMesh (np.ndarray): Subpin mesh values
      subPinAxialMeshCenters (np.ndarray): Subpin mesh center values
      subPinR (np.ndarray): Subpin radius mesh values
      subPinTheta (np.ndarray): Subpin theta values in rads
      tally (VesselTallyDef): object with vessel tally info, never None
      vesselGeom (VesselGeometry): vessel geometry object, None if not defined
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		Core.__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, h5_group = None ):
    """Constructs a Core instance.

    If ``h5_group`` is not specified, :func:`~data.datamodel.Core.Read`
    must be called.

    Args:
        h5_group (h5py.Group): CORE HDF5 group from which to read
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
    """Performs a validity check.

    Returns:
      list(str): list of error messages strings, empty if all is well.
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
    """Initializes all attributes to default or empty values.
"""
    self.apitch = 21.5
    self.axialMesh = None
    self.axialMeshCenters = None
    self.coreLabels = None
    self.coreMap = None
    self.coreSym = 0
    self.detectorMap = None
    self.detectorMesh = None
    self.detectorMeshIsCopied = False
    self.fixedDetectorMesh = None
    self.fixedDetectorMeshCenters = None
    self.group = None
    self.nass = \
    self.nassx = \
    self.nassy = \
    self.nax = 0
    self.nchanx = self.nchany = 0
    self.ndet = \
    self.ndetax = \
    self.nfdetax = 0
    self.npin = \
    self.npinx = \
    self.npiny = 0
    self.nsubax = \
    self.nsubr = \
    self.nsubtheta = 0
    self.pinVolumes = None
    self.pinVolumesSum = 0.0
    self.ratedFlow = 0
    self.ratedPower = 0
    self.subPinAxialMesh = None
    self.subPinAxialMeshCenters = None
    self.subPinR = None
    self.subPinTheta = None
    self.tally = VesselTallyDef()
    self.vesselGeom = None
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		Core.Clone()					-
  #----------------------------------------------------------------------
  def Clone( self ):
    """Mostly deep copy.

    Returns:
        Core: new instance with the same properties as self.
"""
    new_obj = self.__class__()

#		-- Scalars and references
#		--
    for name in (
	'apitch', 'coreSym', 'group', 'nass', 'nassx', 'nassy', 'nax',
	'nchanx', 'nchany',
        'ndet', 'ndetax', 'nfdetax', 'npin', 'npinx', 'npiny',
	'nsubax', 'nsubr', 'nsubtheta',
        'pinVolumesSum', 'ratedFlow', 'ratedPower'
        ):
      setattr( new_obj, name, getattr( self, name ) )
    #end for name

#		-- Numpy arrays
#		--
    for name in (
        'axialMesh', 'axialMeshCenters', 'coreMap',
	'detectorMap', 'detectorMesh',
        'fixedDetectorMesh', 'fixedDetectorMeshCenters',
	'pinVolumes',
	'subPinAxialMesh', 'subPinAxialMeshCenters',
	'subPinR', 'subPinTheta'
        ):
      value = getattr( self, name )
      if value is None:
        new_value = None
      else:
        new_value = np.copy( value )
      setattr( new_obj, name, new_value )
    #end for name

#		-- Deep copy stuff
#		--
    for name in ( 'coreLabels', ):
      setattr( new_obj, name, copy.deepcopy( getattr( self, name ) ) )
    #end for name

#		-- Explicit clones
#		--
    for name in ( 'tally', 'vesselGeom' ):
      value = getattr( self, name )
      new_value = None
      if value is not None and hasattr( value, 'Clone' ):
        new_value = value.Clone()
      setattr( new_obj, name, new_value )
    #end for name

    return  new_obj
  #end Clone


  #----------------------------------------------------------------------
  #	METHOD:		Core.CreateAssyLabel()				-
  #----------------------------------------------------------------------
  def CreateAssyLabel( self, col, row ):
    """Creates a standard assembly label for a given col, row pair.

    Args:
        col (int): 0-based column index
        row (int): 0-based row index

    Returns:
        str: label string of form "(C-R)" representing the column and row.
"""
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
    """Creates a pin label string with an optional assembly address prefix.

    Args:
        pin_col (int): 0-based pin column index
        pin_row (int): 0-based pin row index
	assy_ndx (int): 0-based assembly index,
	    where -1 means don't show the assembly address
	assy_col (int): 0-based assembly column index,
	    where -1 means don't show the assembly address
	assy_row (int): 0-based assembly row index,
	    where -1 means don't show the assembly address

    Returns:
        str: label string of form "[N(C-R)](c,r)" representing (optionally)
	    the assembly index and column-row and the pin column, row,
	    the latter as 1-based indexes.
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
  #	METHOD:		Core.ExtractSymmetryExtent()			-
  #----------------------------------------------------------------------
  def ExtractSymmetryExtent( self ):
    """Returns the default assembly address extent for the specified symmetry.

    The result is the starting horizontal (left) ending vertical (top)
    assembly 0-based indexes, inclusive, and the right and bottom indexes,
    exclusive, followed by the number of assemblies in the horizontal and
    vertical dimensions.

    Returns:
        tuple(int):  ( left, top, right + 1, bottom + 1, dx, dy )
"""
    result = None

    bottom = self.nassy
    right = self.nassx

    if self.coreSym == 4:
#      left = self.nassx >> 1
#      top = self.nassy >> 1
      left = 0  if self.nassx <= 2 else  self.nassx >> 1
      top = 0  if self.nassy <= 2 else  self.nassy >> 1
    elif self.coreSym == 8:
      left = self.nassx >> 2
      top = self.nassy >> 2
      #if self.nassx % 2 == 0 and left > 0: left -= 1
      #if self.nassy % 2 == 0 and top > 0: top -= 1
    else:
      left = top = 0

    result = ( left, top, right, bottom, right - left, bottom - top )
    return  result
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		Core.FindBottomRightAssemblyCell()		-
  #----------------------------------------------------------------------
  def FindBottomRightAssemblyCell( self, cell_range = None ):
    """Locates the bottom-right assembly over the specified range.

    Args:
        cell_range (tuple): optional ( left, top, right + 1, bottom + 1, ... )

    Returns:
        tuple: 0-based (col, row)
"""
    if cell_range is None:
      cell_range = ( 0, 0, self.nassx, self.nassy )

#		-- Walk the diagonal from the bottom right
#		--
    cur_x, cur_y = cell_range[ 2 ] - 1, cell_range[ 3 ] - 1
    while self.coreMap[ cur_y, cur_x ] <= 0 and \
        cur_x > cell_range[ 0 ] and cur_y > cell_range[ 1 ]:
      cur_x -= 1
      cur_y -= 1

    cell = (
        min( cur_x + 1, cell_range[ 2 ] - 1 ),
	min( cur_y + 1, cell_range[ 3 ] - 1 )
        )
    return  cell
  #end FindBottomRightAssemblyCell


  #----------------------------------------------------------------------
  #	METHOD:		Core.FindCornerAssemblyAddrs()			-
  #----------------------------------------------------------------------
  def FindCornerAssemblyAddrs( self, cell_range = None ):
    """Locates the corner assembly addresses.

    Finds the right-most column on the bottom row and bottom-most row on the
    right column.

    Args:
        cell_range (tuple): optional ( left, top, right + 1, bottom + 1, ... )

    Returns:
        tuple: 0-based (bottom_col, right_row)
"""
    if cell_range is None:
      cell_range = ( 0, 0, self.nassx, self.nassy )

    right_col, bottom_row = cell_range[ 2 ] - 1, cell_range[ 3 ] - 1
    bottom_col, right_row = right_col, bottom_row

#		-- Find bottom column
#		--
    while self.coreMap[ bottom_row, bottom_col ] <= 0 and \
        bottom_col > cell_range[ 0 ]:
      bottom_col -= 1

#		-- Find right row
#		--
    while self.coreMap[ right_row, right_col ] <= 0 and \
        right_row > cell_range[ 1 ]:
      right_row -= 1

    return  bottom_col, right_row
  #end FindCornerAssemblyAddrs


  #----------------------------------------------------------------------
  #	METHOD:		Core.FindCornerRadius()				-
  #----------------------------------------------------------------------
  def FindCornerRadius( self, cell_range = None ):
    """Determines the radius in assemblies of the assembly-less bottom-right
    corner.

    Args:
        cell_range (tuple): optional ( left, top, right + 1, bottom + 1, ... )

    Returns:
        float: radius in units of assemblies
"""
    if cell_range is None:
      cell_range = ( 0, 0, self.nassx, self.nassy )

    match_col = match_row = match_radius = -1
    match_radius = max(
        cell_range[ 2 ] - cell_range[ 0 ],
	cell_range[ 3 ] - cell_range[ 1 ]
	)

    right_col, bottom_row = cell_range[ 2 ] - 1, cell_range[ 3 ] - 1

#		-- By row
#		--
    for cur_row in xrange( bottom_row, -1, -1 ):
      cur_col = right_col
      h = cell_range[ 3 ] - cell_range[ 1 ]
      h2 = h * h
      while self.coreMap[ cur_row, cur_col ] <= 0 and \
          cur_col > cell_range[ 0 ]:
        cur_col -= 1
      if cur_col >= cell_range[ 0 ]:
        w = cur_col - cell_range[ 0 ] + 1
	r = math.sqrt( (w * w) + h2 )
	#print >> sys.stderr, 'Y @=%d,%d, r=%f' % ( cur_col, cur_row, r )
	if r > match_radius:
	  match_col = cur_col
	  match_row = cur_row
	  match_radius = r
    #end for y

#		-- By col
#		--
    for cur_col in xrange( right_col, -1, -1 ):
      cur_row = bottom_row
      w = cell_range[ 2 ] - cell_range[ 0 ]
      w2 = w * w
      while self.coreMap[ cur_row, cur_col ] <= 0 and \
	  cur_row > cell_range[ 1 ]:
        cur_row -= 1
      if cur_row >= cell_range[ 1 ]:
	h = cur_row - cell_range[ 1 ] + 1
	r = math.sqrt( w2 + (h * h) )
	#print >> sys.stderr, 'X @=%d,%d, r=%f' % ( cur_col, cur_row, r )
	if r > match_radius:
	  match_col = cur_col
	  match_row = cur_row
	  match_radius = r
    #end for y

    #print >> sys.stderr, 'match col, row, radius=%d,%d,%f' % ( match_col, match_row, match_radius )

    return  match_radius
  #end FindCornerRadius


  #----------------------------------------------------------------------
  #	METHOD:		Core._FindInGroup()				-
  #----------------------------------------------------------------------
  def _FindInGroup( self, name, *groups ):
    """Finds the dataset or group in one of the specified groups.
    
    Returns the first match or None if not found.

    Args:
        name (str): dataset name
	*groups (list(h5py.Group)): list of h5py.Group instances to search,
	    in order

    Returns:
        None if not found, otherwise the the first h5py.Dataset or h5py.Group
	   found with the given name.
"""
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
    """Getter for the ``apitch`` property.

    Returns:
        float:  assembly pitch value in cm, defaulting to 21.5 cm.
"""
    return  21.5  if self.apitch == 0.0 else  self.apitch
  #end GetAssemblyPitch


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetAxialMesh()				-
  #----------------------------------------------------------------------
  def GetAxialMesh( self ):
    """Getter for the ``axialMesh`` property.

    Returns:
        np.ndarray: core/pin axial mesh
"""
    return  self.axialMesh
  #end GetAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetAxialMeshCenters()			-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self ):
    """Getter for ``axialMeshCenters`` property.

    Returns:
        np.ndarray: core/pin axial mesh centers
"""
    return  self.axialMeshCenters
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetColLabel()				-
  #----------------------------------------------------------------------
  def GetColLabel( self, from_ndx, to_ndx = -1 ):
    """Gets the column label or range of labels.

    Calls :func:`~data.datamodel.Core.GetCoreLabel`.

    Args:
        from_ndx (int): 0-based column index or starting column index
        to_ndx (int): 0-based end column index exclusive, or -1 for a
	    single-column result

    Returns:
        str or list(str): single label if ``to_ndx`` is -1, otherwise a
	    list of label strings for the specified range.
"""
    return  self.GetCoreLabel( 0, from_ndx, to_ndx )
  #end GetColLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetCoreLabel()				-
  #----------------------------------------------------------------------
  def GetCoreLabel( self, col_or_row, from_ndx, to_ndx = -1 ):
    """Gets the label or range of labels.

    Args:
        col_or_row (int): 0 for column labels, 1 for row labels
        from_ndx (int): 0-based column index or starting column index
        to_ndx (int): 0-based end column index exclusive, or -1 for a
	    single-column result

    Returns:
        str or list(str): single label if ``to_ndx`` is -1, otherwise a
	    list of label strings for the specified range.
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
  #	METHOD:		Core.GetDetectorMesh()				-
  #----------------------------------------------------------------------
  def GetDetectorMesh( self ):
    """Getter for the ``detectorMesh`` property.

    Returns:
        np.ndarray: detector mesh
"""
    return  self.detectorMesh
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetFixedDetectorMesh()			-
  #----------------------------------------------------------------------
  def GetFixedDetectorMesh( self ):
    """Getter for the ``fixedDetectorMesh`` property.

    Returns:
        np.ndarray: fixed detector mesh
"""
    return  self.fixedDetectorMesh
  #end GetFixedDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetFixedDetectorMeshCenters()		-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self ):
    """Getter for the ``fixedDetectorMeshCenters`` property.

    Returns:
        np.ndarray: fixed detector mesh centers
"""
    return  self.fixedDetectorMeshCenters
  #end GetFixedDetectorMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetGroup()					-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    """Getter for the ``group`` property.

    Returns:
        h5py.Group: CORE Group object
"""
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetRowLabel()				-
  #----------------------------------------------------------------------
  def GetRowLabel( self, from_ndx, to_ndx = -1 ):
    """Gets the row label or range of labels.

    Calls :func:`~data.datamodel.Core.GetCoreLabel`.

    Args:
        from_ndx (int): 0-based row index or starting row index
        to_ndx (int): 0-based end row index exclusive, or -1 for a
	    single-row result

    Returns:
        str or list(str): single label if ``to_ndx`` is -1, otherwise a
	    list of label strings for the specified range.
"""
    return  self.GetCoreLabel( 1, from_ndx, to_ndx )
  #end GetRowLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetSubPinAxialMesh()			-
  #----------------------------------------------------------------------
  def GetSubPinAxialMesh( self ):
    """Getter for the ``subpinAxialMesh`` property.

    Returns:
        np.ndarray: subpin mesh values
"""
    return  self.subPinAxialMesh
  #end GetSubPinAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetSubPinAxialMeshCenters()		-
  #----------------------------------------------------------------------
  def GetSubPinAxialMeshCenters( self ):
    """Getter for the ``subpinAxialMeshCenters`` property.

    Returns:
        np.ndarray: subpin mesh centers
"""
    return  self.subPinAxialMeshCenters
  #end GetSubPinAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		Core.GetTally()					-
  #----------------------------------------------------------------------
  def GetTally( self ):
    """Getter for the ``tally`` property.

    Returns:
	VesselTallyDef: object instance, never None
"""
    return  self.tally
  #end GetTally


  #----------------------------------------------------------------------
  #	METHOD:		Core._InferCoreLabelsSimply()			-
  #----------------------------------------------------------------------
  def _InferCoreLabelsSimply( self, core_group, in_core_group ):
    """Simple approach to determining core X and Y labels.
    
    Assumes datasets named "xlabel" (or "xlabels") and "ylabel" (or
    "ylabels") provide column and row labels, respectively, if they
    exist.  When such datasets do not exist, default labels are used.

    Args:
        core_group (h5py.Group): CORE group
        in_core_group (h5py.Group): INPUT/CASEID/CORE group

    Returns:
        tuple(list): ( col_labels, row_labels )
"""
    item = self._FindInGroup( 'xlabel', core_group, in_core_group )
    if item is None:
      item = self._FindInGroup( 'xlabels', core_group, in_core_group )
    if item is not None and item.shape[ 0 ] == self.nassx:
      col_labels = [
          (item[ i ][ 0 ] if len( item[ i ].shape ) > 0 else item[ i ]).\
	  replace( ' ', '' ) \
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
    if item is None:
      item = self._FindInGroup( 'ylabels', core_group, in_core_group )
    if item is not None and item.shape[ 0 ] == self.nassy:
      row_labels = [
          (item[ i ][ 0 ] if len( item[ i ].shape ) > 0 else item[ i ]).\
	  replace( ' ', '' ) \
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
    """Smarter approach to determining core X and Y labels.
    
    Assumes datasets named "xlabel" (or "xlabels") and "ylabel" (or
    "ylabels") provide column and row labels, respectively, if they
    exist.  Also, alphabeta and numeric labels are assumed to be
    column and row labels, respectively, and the order is forced such that
    'A' is rightmost and '1' is topmost.

    Args:
        core_group (h5py.Group): CORE group
        in_core_group (h5py.Group): INPUT/CASEID/CORE group

    Returns:
        tuple(list): ( col_labels, row_labels )
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
    """Checks if self has data.

    Returns:
      bool: True if npiny, npinx, nax, nass, and coreSym are all gt 0
"""
    return  \
        self.npiny > 0 and self.npinx > 0 and \
	self.nax > 0 and self.nass > 0 and self.coreSym > 0
  #end IsNonZero


  #----------------------------------------------------------------------
  #	METHOD:		Core.Read()					-
  #----------------------------------------------------------------------
  def Read( self, h5_group ):
    """Reads values for this from the HDF5 file.
    
    Calls :func:`~data.datamodel.Core._ReadImpl`.

    Args:
        h5_group (h5py.Group): File level HDF5 group to read.
"""
    self.Clear()

#		-- Assert on valid group
#		--
#    if h5_group is None or not isinstance( h5_group, h5py.Group ):
#      raise Exception( 'Must have valid HDF5 file' )
    assert isinstance( h5_group, h5py.Group ), 'Must have valid HDF5 group'

#		-- Assert on CORE
#		--
#    if 'CORE' not in h5_group:
#      raise Exception( 'Could not find "CORE"' )
    assert 'CORE' in h5_group, 'Could not find "CORE"'

    core_group = h5_group[ 'CORE' ]
    input_group = h5_group[ 'INPUT' ] if 'INPUT' in h5_group else None

    self._ReadImpl( core_group, input_group )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		Core._ReadImpl()				-
  #----------------------------------------------------------------------
  def _ReadImpl( self, core_group, input_group ):
    """Does the heavy lifting of reading from the HDF5 file.

    Args:
        core_group (h5py.Group): CORE group to read.
        input_group (h5py.Group): CASEID/CORE group to read.
"""
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
      raise Exception( ', '.join( missing ) )

#		-- No exception, plow on
#		--
    #self.coreMap = core_map_item.value
    self.coreMap = np.array( core_map_item )
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
    if item is None:
      item = self._FindInGroup( 'Apitch', core_group, in_core_group )
    if item is not None:
      self.apitch = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
      #self.apitch = item.value.item() if len( item.shape ) > 0 else item.value

#		-- Other datasets: axial_mesh
#		--
#    self.axialMesh = axial_mesh_item.value
    self.axialMesh = np.array( axial_mesh_item )
    self.nax = self.axialMesh.shape[ 0 ] - 1

    self.axialMeshCenters = \
        (self.axialMesh[ 0 : -1 ] + self.axialMesh[ 1 : ]) / 2.0

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

    if self.npin == 0:
      self.npin = max( self.npinx, self.npiny )

#		-- Other datasets: pin_volumes
#		--
    self.pinVolumesSum = 0
    item = self._FindInGroup( 'pin_volumes', core_group, in_core_group )
    if item is not None:
      #self.pinVolumes = item.value
      self.pinVolumes = np.array( item )
      self.pinVolumesSum = np.sum( self.pinVolumes )
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

    item = self._FindInGroup( 'rated_power', core_group, in_core_group )
    if item is not None:
      self.ratedPower = item[ 0 ] if len( item.shape ) > 0 else item[ () ]

#		-- Optional detector_map
#		--
    #xxxx if no detector_map, assume each assembly is a detector
    item = self._FindInGroup( 'detector_map', core_group, in_core_group )
    if item is not None:
      #self.detectorMap = item.value
      self.detectorMap = np.array( item )
      self.ndet = int( np.amax( self.detectorMap ) )
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
      self.detectorMesh = np.copy( item )
      self.ndetax = item.shape[ 0 ]
    else:  # only if ndet == nass
      self.detectorMesh = self.axialMeshCenters
      self.detectorMeshIsCopied = True
      self.ndetax = self.nax
    #end if detector_mesh

#		-- Optional fixedDetector_axial_mesh
#		--
    item = self._FindInGroup( 'fixed_detector_mesh', core_group )
    if item is not None:
      self.fixedDetectorMesh = np.array( item )

      self.fixedDetectorMeshCenters = \
(self.fixedDetectorMesh[ 0 : -1 ] + self.fixedDetectorMesh[ 1 : ]) / 2.0
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

#    if self.npin == 0:
#      self.npin = self.npinx = self.npiny = 1

    self.nchanx = self.npinx + 1
    self.nchany = self.npiny + 1

#		-- SubPin
#		--
    item = self._FindInGroup( 'subpin_axial_mesh', core_group )
    if item is not None:
      self.subPinAxialMesh = np.array( item )
      self.nsubax = self.subPinAxialMesh.shape[ 0 ] - 1

      self.subPinAxialMeshCenters = \
          (self.subPinAxialMesh[ 0 : -1 ] + self.subPinAxialMesh[ 1 : ]) / 2.0
    else:
      self.subPinAxialMesh = self.axialMesh
      self.subPinAxialMeshCenters = self.axialMeshCenters
      self.nsubax = self.nax

    item = self._FindInGroup( 'subpin_r', core_group )
    if item is not None:
      self.subPinR = np.array( item )
      self.nsubr = self.subPinR.shape[ 0 ]
    else:
      item = self._FindInGroup( 'nsubr', core_group )
      if item is not None:
        self.nsubr = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
	n = max( 1, self.npinx, self.npiny )
	#incr = float( self.apitch ) / n
	#self.subPinR = np.arange( 0.0, self.apitch + (incr * 0.5), incr )
	self.subPinR = np.linspace( 0.0, np.pi * 2.0, n, endpoint = False )

    item = self._FindInGroup( 'subpin_theta', core_group )
    if item is not None:
      self.subPinTheta = np.array( item )
      self.nsubtheta = self.subPinTheta.shape[ 0 ]
    else:
      item = self._FindInGroup( 'nsubtheta', core_group )
      if item is not None:
        self.nsubtheta = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
	n = max( 1, self.nsubtheta )
	#self.subPinTheta = np.arange( 0.0, math.pi * 2.0, math.pi * 2.0 / n )
	self.subPinTheta = \
	    np.linspace( 0.0, np.pi * 2.0, self.nsubtheta, endpoint = False )

#		-- Vessel Tally
#		--
    vessel_tally_group = self._FindInGroup( 'vessel_tally', core_group )
    if vessel_tally_group is not None:
      self.tally.Read( vessel_tally_group )

      extent = self.ExtractSymmetryExtent()
      self.vesselGeom = VesselGeometry()
      self.vesselGeom.Read( vessel_tally_group, self.apitch, extent[ -2 : ] )
    #end if vessel_tally_group is not None
  #end _ReadImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core.ToJson()					-
  #----------------------------------------------------------------------
  def ToJson( self ):
    """Placeholder that appears might never be needed.
"""
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
  """Data/model bean encapsulation.
  
Events:
  newDataSet		callable( self, new_ds_name )
			listener.OnNewDataSet( self, new_ds_name )

  Attributes:
      averagers (dict): dict by category of average calculators classes.
      axialMeshCentersDict (dict): dict by mesh type of mesh centers,
          types include "pin", "detector", "fixed_detector", "subpin", and
	  "tally".
      axialMeshDict (dict): dict by mesh type of mesh values.
      channelFactors (np.ndarray): channel weight factors with shape
          (npiny + 1, npinx + 1, nax, nass).
      core (Core): Core instance.
      coreGroupDataSetNames (set): set of names of CORE group datasets
      dataSetAxialMesh (dict): dict(ds_name,np.ndarray) of mesh values.
      dataSetAxialMeshCenters (dict): dict(ds_name,np.ndarray) of mesh centers.
      dataSetDefs (dict): dict(category/type,dict) of dataset definitions.
      dataSetDefsByName (dict): dict(ds_name,dict) reverse lookup of dataset
          definitions by ds_name.
      dataSetDefsLock (threading.RLock): used for ``dataSetDefs`` and
          ``dataSetDefsByName``.
      dataSetScaleTypes (dict): dict(ds_name) of scale type, 'linear' or 'log',
          defaulting to 'linear'
      dataSetThresholds (dict): dict(ds_name,data.range_expr.RangeExpression)
          of ranges by dataset name.
      dataSetNames (dict): dict(category/type,list(str)) of dataset names by
          category ( 'channel', 'derived', 'detector', 'fixed_detector',
	  'pin', 'scalar' ) and special names 'axials', 'core', 'time'
      dataSetNamesVersion (int): counter to indicate changes and need to update
          dataset menus.
      derivableFuncsAndTypesByLabel (dict): cache keyed by aggregation func
          name of maps keyed derived type labels of categories/types that can
	  be the basis for the aggregation function applied for the derived type
      derivableTypesByLabel (dict): cache keyed by derived label of dataset
          categories/types that can be the basis for the derived type.
      derivedCoreGroup (h5py.Group): used to store threshold-ed
          CORE-group datasets
      derivedFile (h5py.File): used to store derived data.
      derivedLabelsByType (dict): cache by dataset category/type of available
          derived type labels.
      derivedStates (list): list of DerivedState instances.
      h5File (h5py.File): file for this model.
      listeners (dict): dict(str,obj) of listeners by event name.
      maxAxialValue (float): maximum axial value (cm).
      name (str): unique display name, the base name of the HDF5 file
          with any necessary disambiguation suffixes.
      nodeFactors (np.ndarray): node weight factors with shape
          ( 1, 4, nax, nass ).
      pinFactors (np.ndarray) pin weight factors with shape
          ( npiny, npinx, nax, nass ).
      ranges (dict): dict of (min, max) values by dataset name.
      rangesByStatePt (list): list by statept index of dicts by dataset name
          of ranges.
      rangesLock (threading.RLock): used for ``ranges`` and
         ``rangesByStatePt``.
      states (list): lazily-populated list of State instances.
XXXXX
"""


#		-- Constants
#		--

  DEFAULT_range = ( -sys.float_info.max, sys.float_info.max )


#		-- Class Attributes
#		--

  #dataSetNamesVersion_ = 0


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
passed, :func:`Read` must be called.

  :param h5f_param:  either an h5py.File or the name of the HDF5 file to read
  :type h5f_param:  h5py.File or str
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

    self.readMessages = []

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
    """Adds the dataset name and type to the current list for this.

  :param ds_type:  dataset type or category
  :type ds_type:  str
  :param ds_name:  dataset name
  :type ds_name:  str
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
	  self.dataSetNames[ 'axials' ].append( ds_name )

      self.dataSetNamesVersion += 1
      self._FireEvent( 'newDataSet', ds_name )
    #end if ds_name is new
  #end AddDataSetName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.AddListener()				-
  #----------------------------------------------------------------------
  def AddListener( self, event_name, listener ):
    """Adds an event listener.

  :param event_name:  event name ('newDataSet' is all we have for now)
  :type event_name:  str
  :param listener:  callable or object with OnNewDataSet() method 
  :type listener:  object
"""
    if event_name in self.listeners:
      if listener not in self.listeners[ event_name ]:
        self.listeners[ event_name ].append( listener )
    #end if event_name
  #end AddListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Check()				-
  #----------------------------------------------------------------------
  def Check( self ):
    """Peforms a validity check on core and all the states

  :returns:  list of error messages, empty if none
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
    """Resets to default or empty values.
"""
    self.axialMeshCentersDict = {}
    self.axialMeshDict = {}
    self.core = None
    self.coreGroupDataSets = set()
    self.dataSetAxialMesh = {}
    self.dataSetAxialMeshCenters = {}
    self.dataSetDefs = {}
    self.dataSetDefsByName = {}
    self.dataSetScaleTypes = {}
    self.dataSetThresholds = {}
    self.dataSetNames = {}
    self.dataSetNamesVersion = 0
    self.derivableFuncsAndTypesByLabel = {}
    self.derivableTypesByLabel = {}
    self.derivedCoreGroup = None
    self.derivedFile = None
    self.derivedLabelsByType = {}
    self.derivedStates = None
    self.h5File = None
    self.listeners = { 'newDataSet': [] }
    self.name = ''
    self.ranges = {}
    self.rangesByStatePt = []
    self.states = []

    #DataModel.dataSetNamesVersion_ += 1
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    """Closes this.
"""
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
    """Creates a 3-tuple from the column and row indexes.

  :param col:  0-based column index
  :type col:  int
  :param row:  0-based row index
  :type row:  int
  :returns:  0-based ( assy_ndx, col, row )
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
    """Creates a 3-tuple from the 0-based assembly index.

  :param assy_ndx:  0-based assembly index
  :type assy_ndx:  int
  :returns:  0-based ( assy_ndx, col, row )
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
    """Creates an AxialValue instance.
Calls :func:`CreateAxialValueObject`.

  :returns:  AxialValue instance
"""
#    results = self.CreateAxialValueRec( **kwargs )
#
#    tup = (
#	results.get( 'cm', 0.0 ),
#	results.get( 'pin', -1 ),
#	results.get( 'detector', -1 ),
#	results.get( 'fixed_detector', -1 ),
#	results.get( 'tally', -1 ),
#	results.get( 'subpin', -1 )
#        )
#    return  tup
    return  self.CreateAxialValueObject( **kwargs )
  #end CreateAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAxialValueObject()		-
  #----------------------------------------------------------------------
  def CreateAxialValueObject( self, **kwargs ):
    """Creates an AxialValue instance.

Kwargs:

  ================== ==================================
  Name               Description
  ------------------ ----------------------------------
  cm                 axial value in cm
  core_ndx           0-based core axial index
  detector_ndx       0-based detector axial index
  fixed_detector_ndx 0-based fixed_detector axial index
  pin_ndx            alias for 'core_ndx'
  subpin_ndx         0-based subpin axial index
  tally_ndx          0-based tally axial index
  value              alias for 'cm'
  ================== ==================================

  :returns:  AxialValue instance
"""
    rec = { 'cm': 0.0 }

    if self.core is not None:
      not_centers_names = set([ 'detector' ])
      predef_names = \
          set([ 'pin', 'detector', 'fixed_detector', 'subpin', 'tally' ])

#		-- Process arguments
#		--
      for n, v in kwargs.iteritems():
	if n == 'cm' or n == 'value':
	  rec[ 'cm' ] = kwargs.get( n )

        elif n.endswith( '_ndx' ):
	  name = n[ 0 : -4 ]
	  if name == 'core':
	    name = 'pin'
	  if name in not_centers_names:
	    mesh = self.axialMeshDict.get( name )
	  else:
	    mesh = self.axialMeshCentersDict.get( name )
	  if mesh is not None:
	    ndx = max( 0, min( v, mesh.shape[ 0 ] - 1 ) )
	    rec[ name ] = ndx
            rec[ 'cm' ] = mesh[ ndx ]
	#end elif _ndx
      #end for n, v

#		-- Resolve missing indexes
#		--
      for name in predef_names:
        ndx = rec.get( name, -1 )
	if ndx < 0 and name in self.axialMeshDict:
	  mesh = self.axialMeshDict.get( name )
	  if len( mesh ) > 0:
	    ndx = DataUtils.FindListIndex( mesh[ : -1 ], rec[ 'cm' ] )
	    #ndx = min( ndx, mesh.shape[ 0 ] -1 )
        rec[ name ] = ndx
      #end for name
    #end if self.core

    rec[ 'value' ] = rec[ 'cm' ]

    return  AxialValue( rec )
  #end CreateAxialValueObject


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAxialValueRec()			-
  #----------------------------------------------------------------------
  def CreateAxialValueRec( self, **kwargs ):
    """Creates a dict with AxialValue values.

Kwargs:

  ================== ==================================
  Name               Description
  ------------------ ----------------------------------
  cm                 axial value in cm
  core_ndx           0-based core axial index
  detector_ndx       0-based detector axial index
  fixed_detector_ndx 0-based fixed_detector axial index
  pin_ndx            alias for 'core_ndx'
  subpin_ndx         0-based subpin axial index
  tally_ndx          0-based tally axial index
  value              alias for 'cm'
  ================== ==================================

  :returns:  dict with named values
"""
    results = { 'cm': 0.0 }

    if self.core is not None:
      not_centers_names = set([ 'detector' ])
      predef_names = \
          set([ 'pin', 'detector', 'fixed_detector', 'subpin', 'tally' ])

#		-- Process arguments
#		--
      for n, v in kwargs.iteritems():
	if n == 'cm' or n == 'value':
	  results[ 'cm' ] = kwargs.get( n )

        elif n.endswith( '_ndx' ):
	  name = n[ 0 : -4 ]
	  if name == 'core':
	    name = 'pin'
	  if name in not_centers_names:
	    mesh = self.axialMeshDict.get( name )
	  else:
	    mesh = self.axialMeshCentersDict.get( name )
	  if mesh is not None:
	    ndx = max( 0, min( v, mesh.shape[ 0 ] - 1 ) )
	    results[ name ] = ndx
            results[ 'cm' ] = mesh[ ndx ]
	#end elif _ndx
      #end for n, v

#		-- Resolve missing indexes
#		--
      for name in predef_names:
        ndx = results.get( name, -1 )
	if ndx < 0 and name in self.axialMeshDict:
	  mesh = self.axialMeshDict.get( name )
	  if len( mesh ) > 0:
	    ndx = DataUtils.FindListIndex( mesh[ : -1 ], results[ 'cm' ] )
	    #ndx = min( ndx, mesh.shape[ 0 ] -1 )
        results[ name ] = ndx
      #end for name
    #end if self.core

    results[ 'value' ] = results[ 'cm' ]
    return  results
  #end CreateAxialValueRec


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedDataSet()		-
  #----------------------------------------------------------------------
  def _CreateDerivedDataSet( self,
      ds_category, derived_label, ds_name,
      agg_name = 'avg'
      ):
    """Calculates and adds the specified dataset.
    Args:
        ds_category (str): dataset category, e.g., 'channel', 'pin'
	derived_label (str): derived label, e.g., 'assembly', 'axial', 'core',
	    'radial'
	ds_name (str): dataset name that is in the category/type, e.g.,
	    'pin_powers'
        agg_name (str): name of aggration function, e.g., 'avg', 'max', 'min'
    Returns:
        str:  name of the new dataset or None if the parameters are invalid
"""
    derived_name = None
    #core = self.core

    if len( self.states ) > 0:
#			-- First, find dataset definition
#			--
      ddef = None
      der_names = self.\
          _CreateDerivedNames( ds_category, derived_label, ds_name, agg_name )
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
	if agg_name != 'avg':
	  avg_method_name = avg_method_name.replace( '_avg', '_' + agg_name )

#			-- Third, get average method reference
#			--
      if avg_method_name and hasattr( averager, avg_method_name ):
	derived_name = der_names[ 1 ]

	try:
	  avg_method = getattr( averager, avg_method_name )

#xxxxx will need to make this a separate thread with per-state progress feedback
#x especially for node averages!
          for state_ndx in xrange( len( self.states ) ):
	    st = self.GetState( state_ndx )
	    derived_st = self.GetDerivedState( state_ndx )

	    dset = st.GetDataSet( ds_name )
	    if dset is None:
	      dset = derived_st.GetDataSet( ds_name )

	    if dset is not None:
	      avg_data = avg_method( dset )
	      derived_st.CreateDataSet( derived_name, avg_data )
	    #end if data
	  #end for each state

	  self.AddDataSetName( der_names[ 0 ], derived_name )

	#except Exception, ex:
	except Exception as ex:
	  msg = \
'Error calculating derived "{1:s}" dataset for "{2:s}":{0:s}{3:s}'.\
format( os.linesep, derived_label, ds_name, str( ex ) )
#	  msg = 'Error calculating derived "%s" dataset for "%s"' % \
#	      ( derived_label, ds_name )
	  self.logger.error( msg )
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
and the derived CORE group are initialized.
    Args:
        states (list[State]): list of states for which derived datasets will
	    be created
    Returns:
        tuple: h5py.File, core group (h5py.Group), list(DerivedState)
"""
#		-- Create temp fle
#		--
    fd, name = tempfile.mkstemp( '.h5' )
    os.close( fd )

    derived_file = h5py.File( name, 'w' )
    derived_core = derived_file.create_group( 'CORE' )
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
#	  if 'exposure' in from_group:
#	    exp_value = np.array( from_group[ 'exposure' ] )
#	    exp_ds = der_group.create_dataset( 'exposure', data = exp_value )
	  for t in TIME_DS_NAMES_LIST:
	    if t in from_group:
	      exp_value = np.array( from_group[ t ] )
	      exp_ds = der_group.create_dataset( t, data = exp_value )
	  #end for t

	  derived_states.append( DerivedState( n, der_name, der_group ) )
	#end if state h5py group exists

	n += 1
      #end for
    #end if we have states

    derived_file.flush()

    return  derived_file, derived_core, derived_states
  #end _CreateDerivedH5File


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedNames()			-
  #----------------------------------------------------------------------
  def _CreateDerivedNames( self,
      ds_category, derived_label, ds_name,
      agg_name = 'avg'
      ):
    """Creates the dataset type name (e.g., :radial) and then pairs of
prefixed (e.g., radial_pin_powers) and replaced (radial_powers) derived names
for each prefix defined for derived_label.
    Args:
        ds_category (str): dataset category, e.g., 'channel', 'pin'
	derived_label (str): derived label, e.g., 'assembly', 'axial', 'core',
	    'radial'
	ds_name (str): dataset name that is in the category/type, e.g.,
	    'pin_powers
        agg_name (str): name of aggration function, e.g., 'avg', 'max', 'min'
    Returns:
        tuple(str):  None if invalid params, otherwise
	    ( ds_type, prefix_name, replaced_name,
	      [, prefix_name, replaced_name, ... ] )
"""
    result = None
    #ds_type = ':' + derived_label
    ds_type = DataUtils.CreateDerivedTypeName( derived_label )
    ddef = self.dataSetDefs.get( ds_type )
    if ddef:
      suffix = ''  if agg_name == 'avg' else  '_' + agg_name
      result_list = [ ds_type ]
      #for der_prefix in ddef[ 'ds_prefix' ].split( ',' ):
      for der_prefix in ddef[ 'ds_prefix' ]:
        pref_name = der_prefix + '_' + ds_name + suffix
        repl_name = pref_name.replace( ds_category + '_', '' ) + suffix
	result_list.append( pref_name )
	result_list.append( repl_name )

      result = tuple( result_list )
    #end if ddef

    return  result
  #end _CreateDerivedNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateDerivedScalarDataSet()		-
  #----------------------------------------------------------------------
  def _CreateDerivedScalarDataSet( self,
      derived_name, datasets, averager, method
      ):
    """Calculates and adds the derived scalar dataset defined by ``kwargs``.
    Args:
        derived_name (str): name of scalar dataset to create
	datasets (str or list(str)): name of source dataset(s)
	averager (str): category/type name of averager to use
	method (str): name of averager method to invoke
"""
    if len( self.states ) > 0 and datasets:
      if not hasattr( datasets, '__iter__' ):
        datasets = [ datasets ]

#			-- Assert on averager and method
#			--
      avg_obj = self.averagers.get( averager )
      assert avg_obj is not None, \
	  'Averager "%s" not found' % averager

      assert hasattr( avg_obj, method ), \
	  'Method "%s" not found in "%s" averager' % ( method, averager )
      avg_method = getattr( avg_obj, method )

      try:
#				-- Iterate over states
#				--
        for state_ndx in range( len( self.states ) ):
	  st = self.GetState( state_ndx )
	  derived_st = self.GetDerivedState( state_ndx )

#					-- Skip if derived_name exists
#					--
	  dset = st.GetDataSet( derived_name )
	  if dset is None:
	    dset = derived_st.GetDataSet( derived_name )

	  if dset is None:
#						-- Get input datasets
	    input_dsets = []
	    for ds_name in datasets:
	      dset_in = st.GetDataSet( ds_name )
	      if dset_in is None:
	        dset_in = derived_st.GetDataSet( ds_name )
	      if dset_in is not None:
	        input_dsets.append( dset_in )

	    if len( input_dsets ) == len( datasets ):
	      data = avg_method( *input_dsets )
              derived_st.CreateDataSet( derived_name, data )
	  #end if dset is None
        #end for each state

	self.AddDataSetName( 'scalar', derived_name )

      except Exception as ex:
	  msg = \
'Error calculating derived scalar dataset "{1:s}":{0:s}{2:s}'.\
format( os.linesep, ds_name, str( ex ) )
	  self.logger.error( msg )
	  raise Exception( msg )
    #end if len( self.states ) > 0 and datasets
  #end _CreateDerivedScalarDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateDetectorAddr()			-
  #----------------------------------------------------------------------
  def CreateDetectorAddr( self, col, row ):
    """Creates a 3-tuple from the column and row indexes.

  :param col:  0-based column index
  :type col:  int
  :param row:  0-based row index
  :type row:  int
  :returns:  0-based ( det_ndx, col, row )
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
    """Creates tuple from the 0-based detector index.

  :param det_ndx:  0-based assembly index
  :type det_ndx:  int
  :returns:  0-based ( det_ndx, col, row )
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

  :returns:  None if core is None, otherwise ( left, top, right+1, bottom+1, dx, dy )
"""
    result = \
        self.core.ExtractSymmetryExtent()  if self.core is not None else \
	None
    return  result
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindChannelMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindChannelMinMaxValue(
      self,
      mode, ds_name, state_ndx = -1, assy_ndx = -1,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with channel addresses for the "first" (right- and
bottom-most) occurence of the min/max value of the dataset, which is assumed
to be a 'channel' dataset.
If cur_state is provided, only differences with the current state are
returned.  Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply channelFactors when determining the
			min/max address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
"""
    results = {}

    addr, state_ndx, value = self.FindMinMaxValueAddr(
        mode, ds_name, state_ndx, assy_ndx,
        self.GetFactors( ds_name ) if use_factors else None
	)

    if addr is not None:
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

#      skip = cur_obj is not None and \
#          hasattr( cur_obj, 'stateIndex' ) and \
#          getattr( cur_obj, 'stateIndex' ) == state_ndx
#      if not skip:
      results[ 'state_index' ] = state_ndx
    #end if addr is not None
   
    return  results
  #end FindChannelMinMaxValue


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
    """Calls DataUtils.FindListIndex().
@param  values		list of values
@param  value		value to search
@return			0-based index N, values[ N ]
			'a': values[ N ] <= value < values[ N + 1 ]
			'd': values[ N ] >= value > values[ N + 1 ]
"""
    return  DataUtils.FindListIndex( values, value )
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
  #	METHOD:		DataModel.FindMinMaxValueAddr()			-
  #----------------------------------------------------------------------
  def FindMinMaxValueAddr(
      self, mode, ds_name,
      state_ndx = -1, assy_ndx = -1,
      factors = None
      ):
    """Finds the first address of the min/max value.
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset to search
@param  state_ndx	0-based state point index, or -1 for all states
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  factors		optional factors to apply to the data, where zero
			values indicate places in the data to be ignored
@return			( dataset addr indices or None, state_ndx,
			  minmax_value or None )
"""
    def find_minmax( dset, ds_def, factors, assy_ndx ):
      dset_value = np.array( dset )
      if factors is not None:
        np.place(
	    dset_value, factors == 0.0,
	    -sys.float_info.max if max_flag else sys.float_info.max
	    )

      if assy_ndx >= 0 and ds_def.get( 'assy_axis', -1 ) >= 0:
        assy_axis = ds_def[ 'assy_axis' ]
	ds_expr = 'dset_value' + \
	  DataUtils.CreateDataSetExpr( dset.shape, ( assy_axis, assy_ndx ) )
	eval_str = 'np.{0:s}( {1:s} )'.\
	    format( 'nanargmax' if max_flag else 'nanargmin', ds_expr )
	x = eval( eval_str )

	eval_str = 'np.unravel_index( x, {0:s}.shape )'.format( ds_expr )
	temp_addr = list( eval( eval_str ) )
	temp_addr.insert( assy_axis, assy_ndx )
	addr = tuple( temp_addr )
      else:
        x = \
	    np.nanargmax( dset_value ) if max_flag else \
	    np.nanargmin( dset_value )
        addr = np.unravel_index( x, dset.shape )

      return  addr, dset_value[ addr ]
    #end find_minmax

    max_flag = mode != 'min'
    addr = None
    ds_def = None
    minmax_value = None

#		-- Resolve factors to dataset if necessary
#		--
    if ds_name and factors is not None:
      if isinstance( factors, h5py.Dataset ):
        factors = np.array( factors )
      ds_shape = ds_def = None
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
    if not (ds_name or ds_def):
      pass

#		-- Single state point
#		--
    elif state_ndx >= 0:
      dset = self.GetStateDataSet( state_ndx, ds_name )
      if dset:
        addr, minmax_value = find_minmax( dset, ds_def, factors, assy_ndx )

#		-- Multiple state points
#		--
    else:
      minmax_value = -sys.float_info.max if max_flag else sys.float_info.max
      for st in xrange( len( self.states ) ):
        dset = self.GetStateDataSet( st, ds_name )
	if dset:
	  cur_addr, cur_minmax = find_minmax( dset, ds_def, factors, assy_ndx )
	  new_flag = \
	      cur_minmax > minmax_value if max_flag else \
	      cur_minmax < minmax_value
	  if new_flag:
	    addr = cur_addr
	    state_ndx = st
	    minmax_value = cur_minmax
	#end if dset
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
  #	METHOD:		DataModel.FindMultiDataSetMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindMultiDataSetMinMaxValue(
      self, mode, state_ndx, assy_ndx,
      cur_obj, *ds_names
      ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the min/max value among all the
specified datasets.  Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  state_ndx	0-based state point index, or -1 for all states
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
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
	    self.FindMinMaxValueAddr( mode, ds_name, state_ndx, assy_ndx )
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

#        skip = cur_obj is not None and \
#	    hasattr( cur_obj, 'stateIndex' ) and \
#            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
#        if not skip:
        results[ 'state_index' ] = max_state_ndx

      else:  # scalar
#        skip = cur_obj is not None and \
#	    hasattr( cur_obj, 'stateIndex' ) and \
#            getattr( cur_obj, 'stateIndex' ) == max_state_ndx
#        if not skip:
        results[ 'state_index' ] = max_state_ndx
    #end if

    return  results
  #end FindMultiDataSetMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindPinMinMaxValue()			-
  #----------------------------------------------------------------------
  def FindPinMinMaxValue(
      self,
      mode, ds_name, state_ndx, assy_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the min/max value of the dataset, which is assumed
to be a 'pin' dataset.
If state_ndx is ge 0, only that state is searched.
Calls FindMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  ds_name		name of dataset
@param  state_ndx	0-based state point index, or -1 for all states
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors (or nodeFactors) when
			determining the min/max address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'state_index'
"""
    results = {}

    factors = self.GetFactors( ds_name ) if use_factors  else None

    addr, state_ndx, value = self.\
        FindMinMaxValueAddr( mode, ds_name, state_ndx, assy_ndx, factors )

    if addr is not None:
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

#      skip = cur_obj is not None and \
#          hasattr( cur_obj, 'stateIndex' ) and \
#          getattr( cur_obj, 'stateIndex' ) == state_ndx
#      if not skip:
      results[ 'state_index' ] = state_ndx
    #end if addr is not None
   
    return  results
  #end FindPinMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindTallyMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindTallyMinMaxValue(
      self,
      mode, tally_addr_in, state_ndx,
      cur_obj = None, ds_expr = None, radius_start_ndx = 0
      ):
    """Creates dict with z (axial), theta, and r indexes for the "first"
occurrence of the min/max value of the dataset, which is assumed to
be a 'tally' dataset.
If state_ndx is ge 0, only that state is searched.
Calls FindTallyMinMaxValueAddr().
@param  mode		'min' or 'max', defaulting to the latter
@param  tally_addr_in	TallyAddress instance from which the name, multIndex,
			and statIndex properties are used
@param  state_ndx	0-based state point index, or -1 for all states
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: axialValue (AxialValue
			instance), stateIndex, tallyAddr (TallyAddress
			instance)
@param  ds_expr		expression to apply to dataset min/max search,
			if None, tally_addr.multIndex and .statIndex will
			be applied in FindTallyMinMaxValueAddr()
@param  radius_start_ndx  starting index of radius range of validity
@return			changes dict with possible keys:
			'axial_value', 'state_index', 'tally_addr'
"""
    results = {}

    z_ndx, theta_ndx, radius_ndx, state_ndx, value = \
    self.FindTallyMinMaxValueAddr(
        mode, tally_addr_in, state_ndx, ds_expr, radius_start_ndx
	)

    if z_ndx >= 0 and theta_ndx >= 0 and radius_ndx >= 0:
      axial_value = self.CreateAxialValue( tally_ndx = z_ndx )
      tally_addr = tally_addr_in.copy()
      tally_addr.update( radiusIndex = radius_ndx, thetaIndex = theta_ndx )

      skip = cur_obj is not None and \
          hasattr( cur_obj, 'axialValue' ) and \
	  getattr( cur_obj, 'axialValue' ).tallyIndex == z_ndx
      if not skip:
        results[ 'axial_value' ] = axial_value

      results[ 'state_index' ] = state_ndx

      skip = False
      if cur_obj is not None and hasattr( cur_obj, 'tallyAddr' ):
        obj_tally_addr = getattr( cur_obj, 'tallyAddr' )
	skip = obj_tally_addr.radiusIndex == radius_ndx and \
	    obj_tally_addr.thetaIndex == theta_ndx
      if not skip:
        results[ 'tally_addr' ] = tally_addr
    #end if z_ndx >= 0 and theta_ndx >= 0 and radius_ndx >= 0

    return  results
  #end FindTallyMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FindTallyMinMaxValueAddr()		-
  #----------------------------------------------------------------------
  def FindTallyMinMaxValueAddr(
      self, mode, tally_addr, state_ndx,
      ds_expr = None, radius_start_ndx = 0
      ):
    """Finds the first address of the min/max value.
@param  mode		'min' or 'max', defaulting to the latter
@param  tally_addr	TallyAddress instance
@param  state_ndx	0-based state point index, or -1 for all states
@param  ds_expr		expression to apply to dataset min/max search,
			if None, tally_addr.multIndex and .statIndex will
			be used
@param  radius_start_ndx  starting index of radius range of validity
@return			( z_ndx, theta_ndx, radius_ndx, state_ndx,
			  minmax_value or None )
"""
    max_flag = mode != 'min'
    z_ndx = theta_ndx = radius_ndx = -1
    addr = minmax_value = None

#		-- Must have data
#		--
    if tally_addr.name:
      if ds_expr is None:
        ds_expr = \
'[ :, :, radius_start_ndx :, tally_addr.multIndex, tally_addr.statIndex ]'
      scale_type = self.GetDataSetScaleType( tally_addr.name.displayName )

#			-- Single state point
#			--
      if state_ndx >= 0:
        dset = self.GetStateDataSet( state_ndx, tally_addr.name.displayName )
        if dset:
	  dset_array = eval( 'np.array( dset' + ds_expr + ' )' )
#	  dset_array = np.array(
#	      dset[ :, :, :, tally_addr.multIndex, tally_addr.statIndex ]
#	      )
          x = \
	      np.nanargmax( dset_array ) if max_flag else \
	      np.nanargmin( dset_array )
	  #addr = np.unravel_index( x, dset.shape )[ : -2 ]
	  addr = np.unravel_index( x, dset_array.shape )
	  minmax_value = dset_array[ addr ]

#		-- Multiple state points
#		--
      else:
        minmax_value = -sys.float_info.max if max_flag else sys.float_info.max
        for st in xrange( len( self.states ) ):
          dset = self.GetStateDataSet( st, tally_addr.name.displayName )
	  if dset:
	    dset_array = eval( 'np.array( dset' + ds_expr + ' )' )
	    if scale_type == 'log':
	      dset_array[ dset_array <= 0.0 ] = np.nan
            x = \
	        np.nanargmax( dset_array ) if max_flag else \
	        np.nanargmin( dset_array )
	    #cur_addr = np.unravel_index( x, dset.shape )[ : -2 ]
	    cur_addr = np.unravel_index( x, dset_array.shape )
	    cur_minmax = dset_array[ cur_addr ]
	    new_flag = \
False  if math.isnan( cur_minmax ) or math.isinf( cur_minmax ) else \
cur_minmax > minmax_value  if max_flag else \
cur_minmax < minmax_value
	    if new_flag:
	      addr = cur_addr
	      state_ndx = st
	      minmax_value = cur_minmax
        #end for
      #end else all states
    #end if tally_addr.name

#		-- Convert from np.int64 to int
#		--
    if addr:
      z_ndx, theta_ndx, radius_ndx = addr
      radius_ndx += radius_start_ndx

    return  z_ndx, theta_ndx, radius_ndx, state_ndx, minmax_value
  #end FindTallyMinMaxValueAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._FireEvent()				-
  #----------------------------------------------------------------------
  def _FireEvent( self, event_name, *params ):
    """Calls event_name listeners passing self, and the list of params.
@param  event_name	'newDataSet'
@param  params		event params
"""
    if event_name in self.listeners:
      for listener in self.listeners[ event_name ]:
        #method_name = 'On' + event_name.capitalize()
        method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
	if hasattr( listener, method_name ):
	  getattr( listener, method_name )( self, *params )
	elif hasattr( listener, '__call__' ):
	  listener( self, *params )
      #end for listener
    #end if event_name
  #end _FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.FixDuplicates()			-
  #----------------------------------------------------------------------
  def FixDuplicates( self, values, order = 'a' ):
    """Creates a new list with no duplicate values.  Duplicate values in
sequence are changed, either to a higher value if order is 'a' or a lower
value if order is 'd'.  The values are such that order is preserved, and
the changes are as insignificant as feasible.

  :param values: List or iterable of values to read
  :type values: iterable
  :param order: 'a' for ascending, 'd' for descending
  :type order: str
"""
#		-- Assert on iterable
#		--
    assert hasattr( values, '__iter__' ), 'Values must be iterable'

    values_list = values  if isinstance( values, list ) else  list( values )
    result = []

    pivot_ndx = -1
    pivot_value = dedup_value = None
    for i in xrange( len( values_list ) ):
      cur_value = values_list[ i ]

      if pivot_ndx < 0 or cur_value != pivot_value:
        pivot_ndx = i
	pivot_value = dedup_value = cur_value
      else:
        #base_value = dedup_value * 1.000000001
	base_value = \
            0.000000001  if dedup_value == 0.0 else \
	    dedup_value * 1.000000001
	if i < len( values_list ) - 1 and \
	    values_list[ i + 1 ] != pivot_value and \
	    base_value >= values_list[ i + 1 ]:
	  base_value = (dedup_value + values_list[ i + 1 ]) / 2.0
        cur_value = dedup_value = base_value

      result.append( cur_value )
    #end for i

    return  result
  #end FixDuplicates


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetAxialMesh()			-
  #----------------------------------------------------------------------
  def GetAxialMesh( self, ds_name = None, mesh_type = 'pin' ):
    """Retrieves the mesh for the specified dataset or type.
@param  ds_name		name of dataset for which to retrieve the axial mesh
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'tally'
@return			np.ndarray
"""
    mesh = self.dataSetAxialMesh.get( ds_name )
    if mesh is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      mesh = self.axialMeshDict.get( mesh_type )

    return  self.core.axialMesh  if mesh is None else  mesh
  #end GetAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetAxialMeshCenters()			-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self, ds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh centers for the specified dataset, or
core.axialMeshCenters if ds_name is None or not found.
@param  ds_name		name of dataset for which to retrieve the axial mesh
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'tally'
@return			np.ndarray
"""
    mesh = self.dataSetAxialMeshCenters.get( ds_name )
    if mesh is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      mesh = self.axialMeshCentersDict.get( mesh_type )

    return  self.core.axialMeshCenters  if mesh is None else  mesh
  #end GetAxialMeshCenters


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
  #	METHOD:		DataModel.GetCoreGroupDataSets()		-
  #----------------------------------------------------------------------
  def GetCoreGroupDataSets( self ):
    """Accessor for the 'coreGroupDataSets' property.

    Returns:
        set: names of datasets in the CORE group
"""
    return  self.coreGroupDataSets
  #end GetCoreGroupDataSets


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
@deprecated  by DataSetName
"""
    return \
	ds_name  if not ds_name else \
        ds_name[ 5 : ]  if ds_name.startswith( 'copy:' ) else \
        ds_name[ 8 : ]  if ds_name.startswith( 'derived:' ) else \
	ds_name
  #end GetDataSetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetScaleType()			-
  #----------------------------------------------------------------------
  def GetDataSetScaleType( self, ds_name = None ):
    """Looks up the scale types for the dataset name.
    Args:
        ds_name (str): dataset name, or None to return the dict keyed by
            dataset names
    Returns:
        str: scale type name, defaulting to 'linear'
"""
    return \
	self.dataSetScaleTypes  if ds_name is None else \
	self.dataSetScaleTypes.get( ds_name, 'linear' )
  #end GetDataSetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetThreshold()			-
  #----------------------------------------------------------------------
  def GetDataSetThreshold( self, ds_name = None ):
    """Looks up the threshold expression for the dataset name.
@param  ds_name		dataset name, or None to return dict of all names
@return			if ds_name is not None, the RangeExpression instance
			for the dataset or None if not found
			if ds_name is None, dict of RangeExpressions by name
"""
    return \
	self.dataSetThresholds  if ds_name is None else \
	self.dataSetThresholds.get( ds_name )
  #end GetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNames()			-
  #----------------------------------------------------------------------
  def GetDataSetNames( self, ds_type = None ):
    """Retrieve names of dataset for the specified type, or return the
dict by type of dataset names.
    Args:
        ds_type(str): optional dataset type name
    Returns:
        list(str): if `ds_type` is not None, list of datasets of that type
	    or empty list if `ds_type` is not found
	dict(str,list(str)): if `ds_type` is None, copy of dict of dataset
	    name lists by ds_type ('axials', 'channel', 'core', 'detector',
	    'fixed_detector', 'pin', 'scalar', 'time', etc.)
"""
    return \
        list( self.dataSetNames.get( ds_type, [] ) ) if ds_type else \
        dict( self.dataSetNames )
#        dict( self.dataSetNames ) if ds_type is None else \
#	list( self.dataSetNames.get( ds_type, [] ) )
  #end GetDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNames2()			-
  #----------------------------------------------------------------------
  def GetDataSetNames2( self, ds_type = None, no_core = False ):
    """Accessor for the 'dataSetNames' property.
@param  ds_type		optional type name
@return			if ds_type is not None, list of datasets in that
			ds_type, empty if not found
			if ds_type is None, copy of dict of dataset name lists
			by ds_type
			( 'axials', 'channel', 'core', 'detector',
			  'fixed_detector', 'pin', 'scalar', 'time', etc. )
"""
    def cull( name_list ):
      return  [ x for x in name_list if not self.IsCoreGroupDataSet( x ) ]

    if ds_type:
      result = self.dataSetNames.get( ds_type, [] )
      if no_core:
        result = cull( result )
    else:
      result = {}
      for type_name, ds_names in six.iteritems( self.dataSetNames ):
	if ds_names is None: ds_names = []
        result[ type_name ] = cull( ds_names )  if no_core else  ds_names

    return  result
  #end GetDataSetNames2


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNamesVersion()		-
  #----------------------------------------------------------------------
  def GetDataSetNamesVersion( self ):
    """Used to determine the generation of dataset changes for menus and
lists that must be rebuilt when the sets of available datasets change.
"""
    #return  DataModel.dataSetNamesVersion_
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
  #	METHOD:		DataModel.GetDataSetTypeDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetTypeDisplayName( self, ds_type ):
    """Strips any derived prefix.  Best to encapsulate this here.  Note this
must match how _CreateDerivedNames() builds the derived type name.
@param  ds_type		category/type
@return			type name sans any derived marking
"""
    return  DataUtils.GetDataSetTypeDisplayName( ds_type )
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
  #	METHOD:		DataModel.GetDerivableFuncsAndTypes()		-
  #----------------------------------------------------------------------
  def GetDerivableFuncsAndTypes( self, der_label ):
    """For the specified derived label, returns all the types from which
    Args:
        der_label (str): derived type label
    Returns:
        dict: dict keyed by aggregation func name of categories/types that can
	  be the basis for the aggregation function applied for the derived type
"""

    funcs_types_map = self.derivableFuncsAndTypesByLabel.get( der_label )
    if funcs_types_map is None:
      funcs_types_map = {}
      ddef = self.GetDataSetDef( ':' + der_label )
      if ddef and 'avg_method' in ddef:
	for base_type, method_name in six.iteritems( ddef[ 'avg_method' ] ):
	  if base_type in self.averagers:
	    averager = self.averagers[ base_type ]
#	    if 'avg' in funcs_types_map:
#	      funcs_types_map[ 'avg' ].append( base_type )
#	    else:
#	      funcs_types_map[ 'avg' ] = [ base_type ]
	    for agg_name in AGGREGATION_FUNCS:
	      cur_method_name = \
		  method_name  if agg_name == 'avg' else \
	          method_name.replace( '_avg', '_' + agg_name )
	      if hasattr( averager, cur_method_name ) and \
	          hasattr( getattr( averager, cur_method_name ), '__call__' ):
	        if agg_name in funcs_types_map:
	          funcs_types_map[ agg_name ].append( base_type )
	        else:
	          funcs_types_map[ agg_name ] = [ base_type ]
	    #end for agg_name in AGGREGATION_FUNCS
	  #end if base_type in self.averagers
	#end for base_type, method_name in six.iteritems( ddef[ 'avg_method' ] )

	for ds_types in six.itervalues( funcs_types_map ):
	  ds_types.sort()
      #end if ddef and 'avg_method' in ddef

      self.derivableFuncsAndTypesByLabel[ der_label ] = funcs_types_map
    #end if funcs_types_map is None

    return  funcs_types_map
  #end GetDerivableFuncsAndTypes


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
        self.derivableTypesByLabel[ der_label ] = ds_types
      #if avg_method defined

    return  ds_types
  #end GetDerivableTypes


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedCoreGroup()			-
  #----------------------------------------------------------------------
  def GetDerivedCoreGroup( self ):
    """Accessor for the 'derivedCoreGroup' property.
    Returns:
        h5py.Group: self.derivedCoreGroup
"""
    return  self.derivedCoreGroup
  #end GetDerivedCoreGroup


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDerivedLabels()			-
  #----------------------------------------------------------------------
  def GetDerivedLabels( self, ds_category ):
    """For the specified category, returns all the labels for possible
derived datasets.  Lazily created and cached.
@param  ds_category	category/type, key in DATASET_DEFS
@return			sorted list of derived type labels, possibly empty

Shouldn't be used any more.
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

    dset = None
    ddef = self.GetDataSetDefByDsName( ds_name ) if ds_name else None
    if ddef:
      ds_type = ddef[ 'type' ]
      dset = self.GetStateDataSet( 0, ds_name )

    if dset is not None:
#		-- Set default
      result = \
          self.nodeFactors if self.IsNodalType( ds_type ) else self.pinFactors

#		-- Check for 'factor' attribute
      factor_name = None
      if dset.attrs is not None and 'factor' in dset.attrs:
        factor_obj = dset.attrs[ 'factor' ]
        factor_name = \
	    factor_obj[ 0 ] if isinstance( factor_obj, np.ndarray ) else \
	    str( factor_obj )

      if factor_name and self.core is not None and \
          factor_name in self.core.group:
        result = self.core.group.get( factor_name )

      elif ddef[ 'type' ] == 'channel':
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
      #end if dset is not None
    #end if result is None

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
    result = core_result = None
    names = self.dataSetNames.get( category )
    #return  names[ 0 ] if names is not None and len( names ) > 0 else None

#		-- First, try for non-CORE group dataset
    for ds_name in names:
      if not self.IsCoreGroupDataSet( ds_name ):
        result = ds_name
	break
      elif core_result is None:
        core_result = ds_name

    if result is None:
      result = core_result

    return  result
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
  #	METHOD:		DataModel.GetName()				-
  #----------------------------------------------------------------------
  def GetName( self ):
    """Accessor for the 'name' property.
@return			name
"""
    return  self.name
  #end GetName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange( self, ds_name, state_ndx = -1, ds_expr = None ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for the range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
@param  ds_name		dataset name
@param  state_ndx	optional 0-based statept index to use, or -1
			for global range
@param  ds_expr		optional reference expression to apply to the dataset
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

      ds_name_key = ds_name + ds_expr  if ds_expr else  ds_name
      ds_range = range_dict.get( ds_name_key )
      if ds_range is None:
        ds_range = self._ReadDataSetRange( ds_name, state_ndx, ds_expr )
        range_dict[ ds_name ] = ds_range

    finally:
      self.rangesLock.release()

    if ds_range is None:
      ds_range = DataModel.DEFAULT_range

    return  ds_range
  #end GetRange


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
  #	METHOD:		DataModel.GetReadMessages()			-
  #----------------------------------------------------------------------
  def GetReadMessages( self ):
    """Accessor for the 'readMessages' property.
@return			list of warning messages during Read(), empty
			if no warnings
"""
    return  self.readMessages
  #end GetReadMessages


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
	ds[ () ] if len( ds.shape ) == 0 else ds[ 0 ]
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
    """Retrieves a normal or derived dataset,
copying a derived dataset into a 4D array if necessary.

    Args:
        state_ndx (int): 0-based state point index
	ds_name (str): dataset name, normal or derived
    Returns:
        h5py.Dataset: object if found or None
"""
    derived_st = dset = st = None

    if ds_name:
      st = self.GetState( state_ndx )
      derived_st = self.GetDerivedState( state_ndx )

    #if st and derived_st:
    if st is not None:
      self.dataSetDefsLock.acquire()
      try:
	core_flag = False
        if self.IsCoreGroupDataSet( ds_name ):
	  core_flag = True
	  dset = self.core.group[ ds_name ]
	else:
	  dset = st.GetDataSet( ds_name )
	if dset is None and derived_st is not None:
	  dset = derived_st.GetDataSet( ds_name )

#				-- Must copy a derived (not 4D) dataset
#				--
        if dset is not None and len( dset.shape ) < 4 and dset.shape != ( 1, ):
          copy_name = 'copy:' + ds_name
	  #copy_dset = st.GetDataSet( copy_name )
	  if core_flag:
	    copy_dset = self.derivedCoreGroup.get( copy_name )
	  else:
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

	      #if copy_data.size == 1:  This picks up non-scalars of size 1
	      if len( dset.shape ) == 0 or dset.shape == ( 1, ):
	        copy_data[ 0, 0, 0, 0 ] = \
		    dset[ 0 ] if len( dset.shape ) > 0 else dset[ () ]
	        #copy_data[ 0, 0, 0, 0 ] = np.array( dset ).item()
	      else:
	        globals_env = {}
	        locals_env = { 'copy_data': copy_data, 'dset': dset }
	        exec( exec_str, globals_env, locals_env )
		if core_flag:
		  dset = self.derivedCoreGroup.create_dataset(
		      copy_name, data = locals_env[ 'copy_data' ]
		      )
		else:
	          dset = derived_st.\
		      CreateDataSet( copy_name, locals_env[ 'copy_data' ] )
	      #end if-else copy_data.size
	    #end if ds_def is not None
	  #end if-else copy_dset
        #end if must copy

#				-- Threshold for ds_name?
#				--
	range_expr = self.dataSetThresholds.get( ds_name )
	if range_expr and dset is not None and derived_st is not None:
	  thold_ds_name = 'threshold:' + ds_name
	  thold_dset = derived_st.GetDataSet( thold_ds_name )
	  if thold_dset is not None:
	    dset = thold_dset
	  else:
	    thold_arr = range_expr.ApplyThreshold( np.array( dset ) )
	    dset = derived_st.CreateDataSet( thold_ds_name, thold_arr )
	#end if dset

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
  def HasDataSetType( self, ds_type ):
    """Tests existence of datasets in named type
@param  ds_type		one of type names, e.g., 'axials', 'channel', 'derived',
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
  def HasDerivedDataSet( self,
      ds_category, derived_label, ds_name,
      agg_name = 'avg'
      ):
    """Checks to see if the dataset exists.
    Args:
        ds_category (str): dataset category, e.g., 'channel', 'pin'
	derived_label (str): derived label, e.g., 'assembly', 'axial', 'core',
	    'radial'
	ds_name (str): dataset name that is in the category/type, e.g.,
	    'pin_powers
        agg_name (str): name of aggration function, e.g., 'avg', 'max', 'min'
    Returns:
        str:  name under which it exists or None if we don't have it
"""
    match = None
    names = None
    der_names = self.\
        _CreateDerivedNames( ds_category, derived_label, ds_name, agg_name )
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
  #	METHOD:		DataModel.HasDetectorData()			-
  #----------------------------------------------------------------------
  def HasDetectorData( self ):
    """Convenience method to check for existence of 'detector' or
'fixed_detector' dataset types.
@return			True if either 'detector' or 'fixed_detector' datasets
			exist, false otherwise
"""
    return  \
        self.HasDataSetType( 'detector' ) or \
	self.HasDataSetType( 'fixed_detector' )
  #end HasDetectorData


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
  #	METHOD:		DataModel.IsCoreGroupDataSet()			-
  #----------------------------------------------------------------------
  def IsCoreGroupDataSet( self, ds_name ):
    """Checks for a CORE group dataset.
    Args:
        ds_name (str): dataset name
    Returns:
        bool: True if in the CORE group, false otherwise
"""
    return  ds_name and ds_name in self.coreGroupDataSets
  #end IsCoreGroupDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.IsDerivedDataSet()			-
  #----------------------------------------------------------------------
  def IsDerivedDataSet( self, ds_name ):
    """
@param  ds_name		dataset name
@return			True if derived, false otherwise
"""
    derived_st = self.GetDerivedState( 0 )
    dset = derived_st.GetDataSet( ds_name ) if derived_st is not None else None
    return  dset is not None
  #end IsDerivedDataSet


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
		'dataset_name' (requires 'state_index')
		'node_addr'
		'sub_addr'
		'sub_addr_mode'
		  (either 'channel', or 'pin', defaulting to 'pin')
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
    """
@param  axial_value	( cm, core_ndx, det_ndx, fdet_ndx, tally_ndx, subpin_ndx )
@deprecated  by AxialValue
"""
    if self.core is None:
      result = ( -1.0, -1, -1, -1, -1, -1 )
    else:
      result_arr = [
        axial_value[ 0 ],
        max( 0, min( axial_value[ 1 ], self.core.nax -1 ) ),
        max( 0, min( axial_value[ 2 ], self.core.ndetax -1 ) ),
        max( 0, min( axial_value[ 3 ], self.core.nfdetax -1 ) )
        ]
      result_arr.append(
	  max( 0, min( axial_value[ 4 ], self.core.tally.nz - 1 ) )
	  if len( axial_value ) > 4 else -1
          )
      result_arr.append(
	  max( 0, min( axial_value[ 5 ], self.core.nsubax - 1 ) )
	  if len( axial_value ) > 5 else -1
          )
      result = tuple( result_arr )
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
    del self.readMessages[ : ]

    if isinstance( h5f_param, h5py.File ):
      self.h5File = h5f_param
    else:
      self.h5File = h5py.File( str( h5f_param ) )
    self.name = os.path.splitext( os.path.basename( self.h5File.filename ))[ 0 ]

    self.core = Core( self.h5File )
    self.states = State.ReadAll( self.h5File )

#		-- Assert on states
#		--
#    if self.states is None or len( self.states ) == 0:
#      raise  Exception( 'No state points could be read' )
    assert self.states is not None and len( self.states ) > 0, \
        'No state points could be read'

    st_group = self.states[ 0 ].GetGroup()

#		-- Special check for vessel_tally
#		--
    if self.core.tally.z is None and 'vessel_tally' in st_group:
      self.core.tally.Read( st_group[ 'vessel_tally' ] )

#		-- Resolve axial meshes
#		--
    self.axialMeshDict[ 'pin' ] = self.core.axialMesh
    self.axialMeshCentersDict[ 'pin' ] = self.core.axialMeshCenters

    if self.core.detectorMesh is not None:
      self.axialMeshDict[ 'detector' ] = self.core.detectorMesh

    if self.core.fixedDetectorMesh is not None and \
        self.core.fixedDetectorMeshCenters is not None:
      self.axialMeshDict[ 'fixed_detector' ] = self.core.fixedDetectorMesh
      self.axialMeshCentersDict[ 'fixed_detector' ] = \
          self.core.fixedDetectorMeshCenters

    if self.core.subPinAxialMesh is not None and \
        self.core.subPinAxialMeshCenters is not None:
      self.axialMeshDict[ 'subpin' ] = self.core.subPinAxialMesh
      self.axialMeshCentersDict[ 'subpin' ] = self.core.subPinAxialMeshCenters

    if self.core.tally.nz > 0:
      t = np.array( self.core.tally.z )
      #tc = (t[ 0 : -1 ] + t[ 1 : ]) / 2.0
      tc = np.array( self.core.tally.zcenters )
      self.axialMeshDict[ 'tally' ] = t
      self.axialMeshCentersDict[ 'tally' ] = tc

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
    if self.core.npin == 0 and pin_powers_shape is not None:
      self.core.npinx = self.core.npiny = \
      self.core.npin = pin_powers_shape[ 0 ]
      self.core.nchanx = self.core.npinx + 1
      self.core.nchany = self.core.npiny + 1

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
    #self.dataSetDefs, self.dataSetDefsByName, self.dataSetNames =
    self.readMessages += self._ResolveDataSets( self.core, st_group )

#			-- Only use time datasets that appear in all statepts
    #self.dataSetNames[ 'time' ] = State.ResolveTimeDataSets( self.states )
    self.derivableFuncsAndTypesByLabel = {}
    self.derivableTypesByLabel = {}
    self.derivedLabelsByType = {}

    self.ranges = {}
    self.rangesByStatePt = [ dict() for i in xrange( len( self.states ) ) ]

#		-- Create derived file and states
#		--
    self.derivedFile, self.derivedCoreGroup, self.derivedStates = \
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
        #darray = group[ name ].value
        darray = np.array( group[ name ] )
	if darray.shape == pin_factors_shape:
	  pin_factors = darray
	  break
    #end for

#		-- Set up the pin averager
#		--
    if 'pin' in self.averagers:
      avg = self.averagers[ 'pin' ]
      ref_pin_powers = None
      #pin_powers_ds = self.GetStateDataSet( 0, 'pin_powers' )
      pin_powers_ds = self.GetStateDataSet( len( self.states ) >> 1, 'pin_powers' )
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

#		-- Automatically derive scalars
#		--
    for name, ddef in six.iteritems( AUTO_DERIVED_SCALAR_DEFS ):
      try:
        self.logger.info( 'auto deriving ' + name )
        self._CreateDerivedScalarDataSet( name, **ddef )
      except Exception as ex:
        #self.logger.exception( ex )
        self.logger.warning( str( ex ) )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadDataSetAxialValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetAxialValues( self,
      ds_name,
      assembly_index = 0,
      detector_index = 0,
      node_addrs = None,
      state_index = 0,
      sub_addrs = None,
      tally_addr = None
      ):
    """Reads axial values for a dataset for a specified state point.
    Args:
        ds_name (str): dataset name, required
	assembly_index (int): optional 0-based assembly index
	detector_index (int): optional 0-based detector index
	node_addrs (list(int)): optional list of node indexes
	sub_addrs (list(pin_col,pin_row)): optional list of 0-based pin
	   col and row indexes
	state_index (int): optional 0-based state point index
	tally_addr (TallyAddress): optional tally address
    Returns:
        tuple( np.ndarray, dict or np.ndarray ): None if ds_name cannot be found
	    or processed, otherwise mesh_values and results, where the latter
	    is a dict by sub_addr (or node col,row) of np.ndarray for datasets
	    that vary by sub_addr, np.ndarray for other datasets.
"""
    mesh_values = result = None

    state_index = self.NormalizeStateIndex( state_index )
    ds_def = self.GetDataSetDefByDsName( ds_name ) \
	if ds_name in self.GetDataSetNames( 'axials' ) else \
	None
    dset = self.GetStateDataSet( state_index, ds_name ) \
        if ds_def is not None else None

    if dset is not None:
      ds_shape = ds_def[ 'shape' ]
      ds_type = ds_def[ 'type' ]
      dset_value = np.array( dset )

      if sub_addrs is not None and not hasattr( sub_addrs, '__iter__' ):
        sub_addrs = [ sub_addrs ]

      mesh_values = \
	  self.GetAxialMesh( ds_name, 'detector' ) \
	    if ds_type == 'detector' else \
	  self.GetAxialMeshCenters( ds_name, 'fixed_detector' ) \
	    if ds_type == 'fixed_detector' else \
	  self.GetAxialMeshCenters( ds_name, 'tally' ) \
	    if ds_type == 'tally' else \
          self.GetAxialMeshCenters( ds_name )
      if not isinstance( mesh_values, np.ndarray ):
        mesh_values = np.array( mesh_values )

#			-- 'detector', 'fixed_detector'
#			--
      if ds_type == 'detector' or ds_type == 'fixed_detector':
        det_ndx = max( 0, min( detector_index, ds_shape[ 1 ] - 1 ) )
	dset_value = np.array( dset )
	result = dset_value[ :, det_ndx ]

#			-- 'tally'
#			--
      elif ds_type == 'tally':
	if tally_addr is not None:
	  theta_ndx = min( tally_addr.thetaIndex, ds_shape[ 1 ] - 1 )
	  radius_ndx = min( tally_addr.radiusIndex, ds_shape[ 2 ] - 1 )
	  mult_ndx = min( tally_addr.multIndex, ds_shape[ 3 ] - 1 )
	  stat_ndx = min( tally_addr.statIndex, ds_shape[ 4 ] - 1 )
	else:
	  theta_ndx = radius_ndx = mult_ndx = stat_ndx = 0
	result = dset_value[ :, theta_ndx, radius_ndx, mult_ndx, stat_ndx ]

#			-- ':node'
#			--
      elif self.IsNodalType( ds_type ):
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

	  #dset_value = np.array( dset )
	  for node_addr in sorted( node_addr_set ):
	    result[ node_addr ] = dset_value[ 0, node_addr[ 0 ], :, assy_ndx ]
	#end if copy_shape

#			-- Require sub_addrs for everything else
      elif sub_addrs is None:
        pass

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

    #return  result
    return \
	( mesh_values, result ) \
	if mesh_values is not None and result is not None else \
	None
  #end ReadDataSetAxialValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange()			-
  #----------------------------------------------------------------------
  def _ReadDataSetRange( self, ds_name, state_ndx = -1, ds_expr = None ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name
@param  state_ndx	optional 0-based statept index in which to search
@param  ds_expr		optional reference expression to apply to the dataset
			(e.g., '[ :, :, :, 0, 0 ]')
"""
    vmin = vmax = NAN

    if ds_name:
      search_range = \
          xrange( self.GetStatesCount() )  if state_ndx < 0 else \
	  xrange( state_ndx, state_ndx + 1 )

#		-- For each state point
#		--
      for i in search_range:
#        st = self.GetState( i )
#	derived_st = self.GetDerivedState( i )
#
#	dset = st.GetDataSet( ds_name )
#	if dset is None:
#	  dset = derived_st.GetDataSet( ds_name )

	dset = self.GetStateDataSet( i, ds_name )

        if dset is not None:
	  if ds_expr:
	    dset_array = eval( 'dset' + ds_expr )
	  else:
	    dset_array = np.array( dset )
	  scale_type = self.GetDataSetScaleType( ds_name )

#			-- Find max and min values
#			--
	  if len( dset_array.shape ) > 0:
	    if scale_type == 'log':
	      dset_array[ dset_array <= 0.0 ] = np.nan
	    cur_max = np.nanmax( dset_array )
	    if not (math.isnan( cur_max ) or math.isinf( cur_max )):
	      if math.isnan( vmax ) or cur_max > vmax:
	        vmax = cur_max

	    cur_nz = dset_array[ np.nonzero( dset_array ) ]
	    if len( cur_nz ) > 0:
	      cur_min = np.nanmin( cur_nz )
	      if not (math.isnan( cur_min ) or math.isinf( cur_min )):
	        if math.isnan( vmin ) or cur_min < vmin:
	          vmin = cur_min
	  else:
	    cur_value = dset_array.item()
	    #if not (math.isnan( cur_value ) or math.isinf( cur_value )):
	    if not (scale_type == 'log' and cur_value <= 0.0) and \
	        not (math.isnan( cur_value ) or math.isinf( cur_value )):
	      if math.isnan( vmax ) or cur_value > vmax:
	        vmax = cur_value
	      if math.isnan( vmin ) or cur_value < vmin:
	        vmin = cur_value
	  #end else not len( dset_array.shape ) > 0
	#end if dset
      #end for states
    #end if ds_name

    vmin_nan = math.isnan( vmin )
    vmax_nan = math.isnan( vmax )
    if vmin_nan and vmax_nan:
      range_min = -10.0
      range_max = 10.0
    elif vmin_nan:
      range_min = range_max = vmax
    elif vmax_nan:
      range_min = range_max = vmin
    else:
      range_min = vmin
      range_max = vmax

    if range_min == range_max:
      #range_max = 1.0  if range_min == 0.0 else  range_min + (range_min / 10.0)
      range_max = \
          1.0  if range_min == 0.0 else \
	  range_min - (range_min / 10.0)  if range_min < 0.0 else \
	  range_min + (range_min / 10.0)

    return  ( range_min, range_max )
  #end _ReadDataSetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange_1()			-
  #----------------------------------------------------------------------
  def _ReadDataSetRange_1( self, ds_name, state_ndx = -1, ds_expr = None ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name
@param  state_ndx	optional 0-based statept index in which to search
@param  ds_expr		optional reference expression to apply to the dataset
			(e.g., '[ :, :, :, 0, 0 ]')
"""
    range_min = -sys.float_info.max
    range_max = sys.float_info.max

    if ds_name:
      vmin = vmax = NAN
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
	  if ds_expr:
	    dset_array = eval( 'dset' + ds_expr )
	  else:
	    dset_array = np.array( dset )

	  if len( dset_array.shape ) > 0:
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

    #return  ( range_min, range_max )
    return \
	( range_min - (range_min / 10.0), range_max ) \
        if range_min == range_max else \
        ( range_min, range_max )
  #end _ReadDataSetRange_1


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadDataSetTimeValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetTimeValues( self, *ds_specs_in ):
    """Reads values for a dataset across all state points, one state point
at a time for better performance.
required.
@param  ds_specs_in	list of dataset specifications with the following keys:
	  assembly_index	0-based assembly index
	  axial_cm		axial value in cm
	  detector_index	0-based detector index for detector datasets
	  ds_name		required dataset name, where a '*' prefix
				means it's not a time-based dataset but
				rather another dataset to be treated as
				the time basis
	  node_addrs		list of node addrs
	  sub_addrs		list of sub_addr pairs
	  tally_addr		tally address
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

        tally_addr = spec.get( 'tally_addr' )

#			-- Scalar
#			--
	if ds_type == 'scalar':
	  if ds_name not in result:
	    result[ ds_name ] = []
	  #value = 0.0  if dset is None else  dset_value.item()
	  value = \
	      0.0 if dset is None else \
	      dset_value[ 0 ] if len( dset_value.shape ) > 0 else \
	      dset_value[ () ]
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

	    #dset_value = np.array( dset )
	    value = dset_value[ axial_ndx, det_ndx ]
	  result[ ds_name ].append( value )

#			-- Tally
#			--
	elif ds_type == 'tally':
	  if ds_name not in result:
	    result[ ds_name ] = []

	  if dset is None:
	    value = 0.0
	  else:
	    ds_shape = ds_def[ 'shape' ]
	    axial_cm = spec.get( 'axial_cm', 0.0 )
            ax_value = self.CreateAxialValue( cm = axial_cm )
            axial_ndx = max( 0, min( ax_value.tallyIndex, ds_shape[ 0 ] - 1 ) )
	    if tally_addr is not None:
	      theta_ndx = min( tally_addr.thetaIndex, ds_shape[ 1 ] - 1 )
	      radius_ndx = min( tally_addr.radiusIndex, ds_shape[ 2 ] - 1 )
	      mult_ndx = min( tally_addr.multIndex, ds_shape[ 3 ] - 1 )
	      stat_ndx = min( tally_addr.statIndex, ds_shape[ 4 ] - 1 )
	    else:
	      theta_ndx = radius_ndx = mult_ndx = stat_ndx = 0
	    value = \
	      dset_value[ axial_ndx, theta_ndx, radius_ndx, mult_ndx, stat_ndx ]
	  result[ ds_name ].append( value )

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
	      assembly_index = spec.get( 'assembly_index', 0 )
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
	      assembly_index = spec.get( 'assembly_index', 0 )
              assy_ndx = max( 0, min( assembly_index, ds_shape[ 3 ] - 1 ) )

	      axial_cm = spec.get( 'axial_cm', 0.0 )
              ax_value = self.CreateAxialValue( cm = axial_cm )
              #axial_ndx = max( 0, min( ax_value[ 1 ], ds_shape[ 2 ] - 1 ) )
              axial_ndx = max( 0, min( ax_value.pinIndex, ds_shape[ 2 ] - 1 ) )

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

#		-- Convert arrays to np.ndarrays, force unique time values
#		--
    for k in result:
      if isinstance( result[ k ], dict ):
	for k2 in result[ k ]:
	  #result[ k ][ k2 ] = np.array( result[ k ][ k2 ], dtype = np.float64 )
	  data_list = result[ k ][ k2 ]
	  if k[ 0 ] != '*':
	    data_list = self.FixDuplicates( data_list )
	  result[ k ][ k2 ] = np.array( data_list, dtype = np.float64 )
      else:
	#result[ k ] = np.array( result[ k ], dtype = np.float64 )
	data_list = result[ k ]
	if k[ 0 ] != '*':
	  data_list = self.FixDuplicates( data_list )
	result[ k ] = np.array( data_list, dtype = np.float64 )
    #end for k, item

    return  result
  #end ReadDataSetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.RemoveListener()			-
  #----------------------------------------------------------------------
  def RemoveListener( self, event_name, listener ):
    """
@param  event_name	'newDataSet'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener in self.listeners[ event_name ]:
        del self.listeners[ event_name ][ listener ]
    #end if event_name
  #end RemoveListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ResolveDataSets()			-
  #----------------------------------------------------------------------
  def _ResolveDataSets( self, core, st_group ):
    """Non thread-safe method to update the following properties:
dataSetDefs		dict of dataset definitions by dataset type
dataSetDefsByName 	dict of dataset definitions by dataset name
dataSetNames		dict of dataset names by dataset type
			'axials', 'scalar', 'time', plus types defined in
			DATASET_DEFS
dataSetAxialMesh	dict of axial meshes by dataset name
dataSetAxialMeshCenters	dict of axial mesh centers by dataset name

    Args:
        core (Core): core object, cannot be None
	st_group (h5py.Group), first statepoint Group, cannot be None
    Returns:
        list(str): list of error messages, empty list if none
"""
    #--------------------------------------------------------------------
    #	FUNC:		process_attrs					-
    #--------------------------------------------------------------------
    def process_attrs( cur_dset, cur_shape, messages ):
      cur_axial_mesh = cur_axial_mesh_centers = None

      if cur_dset.attrs:
#			-- Look for explicit threshold
        if 'threshold' in cur_dset.attrs:
          try:
	    attr_obj = cur_dset.attrs[ 'threshold' ]
	    expr = \
	        attr_obj[ 0 ]  if isinstance( attr_obj, np.ndarray ) else \
	        str( attr_obj )
	    self.SetDataSetThreshold( cur_name, expr )
          except Exception, ex:
	    msg = 'Invalid threshold for dataset {0:s}'.\
	        format( DataSetName( self.name, cur_name ).name )
	    self.logger.exception( msg )
	    messages.append( msg + ': ' + str( ex ) )

#			-- Look for explicit axial_mesh
        if 'axial_mesh' in cur_dset.attrs:
	  attr_obj = cur_dset.attrs[ 'axial_mesh' ]
	  axial_mesh_name = \
	      attr_obj[ 0 ]  if isinstance( attr_obj, np.ndarray ) else \
	      str( attr_obj )
	  if axial_mesh_name not in self.axialMeshDict:
	    if axial_mesh_name in core.group:
	      cur_axial_mesh = np.array( core[ axial_mesh_name ] )
	      cur_axial_mesh_centers = \
	          (cur_axial_mesh[ 0 : -1 ] + cur_axial_mesh[ 1 : ]) / 2.0
	      self.axialMeshDict[ axial_mesh_name ] = cur_axial_mesh
	      self.axialMeshCentersDict[ axial_mesh_name ] = \
	          cur_axial_mesh_centers
	  else:
	    cur_axial_mesh = self.axialMeshDict.get( axial_mesh_name )
	    cur_axial_mesh_centers = \
	        self.axialMeshCentersDict.get( axial_mesh_name )
        #end if cur_dset.attrs and 'axial_mesh' in cur_dset.attrs

#			-- Look for range_scale
        if 'scale_type' in cur_dset.attrs:
	  attr_obj = cur_dset.attrs[ 'scale_type' ]
	  scale_name = \
	      attr_obj[ 0 ]  if isinstance( attr_obj, np.ndarray ) else \
	      str( attr_obj )
	  self.SetDataSetScaleType( cur_name, scale_name )
      #end if cur_dset.attrs

      return  cur_axial_mesh, cur_axial_mesh_centers
    #end process_attrs

    #--------------------------------------------------------------------
    #	FUNC:		process_non_scalar				-
    #--------------------------------------------------------------------
    def process_non_scalar(
        cur_name, cur_shape, ds_defs, ds_defs_by_name, ds_names, scalar_shape,
	group_set = None
	):
      cat_item_maybe = None
      cat_item = None
      for def_name, def_item in ds_defs.iteritems():
        if 'group' in def_item:
          pass

        elif def_name == 'detector' and \
            self.core.nax == self.core.ndetax and \
            self.core.ndet == self.core.nass:
          pass

        elif def_name == 'fixed_detector' and \
            self.core.nax == self.core.nfdetax and \
            self.core.ndet == self.core.nass:
          pass

        elif def_name == 'radial_detector' and \
            self.core.ndet == self.core.nass:
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
          ds_names[ 'axials' ].append( cur_name )

	if group_set is not None:
	  group_set.add( cur_name )
      #if cat_item
    #end process_non_scalar

    #--------------------------------------------------------------------
    #	FUNC:		process_scalar					-
    #--------------------------------------------------------------------
    def process_scalar(
	cur_dset, cur_name, cur_shape,
	ds_defs, ds_defs_by_name, ds_names, scalar_shape,
	group_set = None
	):
      cat_name = None
      if cur_name in TIME_DS_NAMES:
        cat_name = 'time'
      else:
        for def_name, def_item in ds_defs.iteritems():
	  if def_name != 'scalar' and def_item[ 'shape' ] == scalar_shape \
	      and 'ds_prefix' in def_item:
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
	test_value = \
	    cur_dset[ () ]  if len( cur_shape ) == 0 else  cur_dset[ 0 ]
	skip = \
	    isinstance( test_value, np.string_ ) or \
	    isinstance( test_value, np.bool_ )
	if not skip:
	  cat_name = 'scalar'
      #end if cat_name is None

      if cat_name:
        ds_names[ cat_name ].append( cur_name )
	ds_defs_by_name[ cur_name ] = ds_defs.get( cat_name )
	if group_set is not None:
	  group_set.add( cur_name )
    #end process_scalar

#		-- Initialize
#		--
    messages = []
    ds_defs = copy.deepcopy( DATASET_DEFS )
    ds_defs_by_name = {}
    ds_names = { 'axials': [], 'core': [], 'scalar': [], 'time': [ 'state' ] }

    ds_axial_mesh = {}
    ds_axial_mesh_centers = {}

#		-- Resolve dataset defs
#		--
    for def_name, def_item in ds_defs.iteritems():
      ds_names[ def_name ] = []
      if 'shape' not in def_item:
        def_item[ 'shape' ] = eval( def_item[ 'shape_expr' ] )
      if 'copy_shape_expr' in def_item:
        def_item[ 'copy_shape' ] = eval( def_item[ 'copy_shape_expr' ] )
    #end for

#		-- Walk statepoint datasets in st_group
#		--
    scalar_shape = ( 1, )

    for cur_name in st_group:
      if isinstance( st_group[ cur_name ], h5py.Group ):
        if cur_name == 'QOI':
	  qoi_group = st_group[ cur_name ]
	  for qoi_name in qoi_group:
	    cur_dset = qoi_group[ qoi_name ]
            cur_shape = cur_dset.shape
            if len( cur_shape ) == 0 or cur_shape == scalar_shape:
	      cur_path_name = cur_name + '/' + qoi_name
	      if cur_path_name not in ds_defs_by_name:
	        process_scalar(
	            cur_dset, cur_path_name, cur_shape,
	            ds_defs, ds_defs_by_name, ds_names,
	            scalar_shape
	            )
            #end if len( cur_shape ) == 0 or cur_shape == scalar_shape
	  #end for qoi_name
        #end if cur_name == 'QOI'

#      if not (
#          isinstance( st_group[ cur_name ], h5py.Group ) or
#	  cur_name.startswith( 'copy:' )
#	  ):
      elif not cur_name.startswith( 'copy:' ):
	cur_dset = st_group[ cur_name ]
        cur_shape = cur_dset.shape

	cur_axial_mesh, cur_axial_mesh_centers = \
	    process_attrs( cur_dset, cur_shape, messages )

#			-- Scalar is special case
#			--
	#bank_pos, emulate as individual scalars
        if len( cur_shape ) == 0 or cur_shape == scalar_shape:
	  process_scalar(
	      cur_dset, cur_name, cur_shape,
	      ds_defs, ds_defs_by_name, ds_names,
	      scalar_shape
	      )

#			-- Fixed detector is special case
#			--
	elif cur_name == 'fixed_detector_response' and \
	    cur_shape == ds_defs[ 'fixed_detector' ][ 'shape' ] and \
	    (core.fixedDetectorMeshCenters is not None or
	    cur_axial_mesh_centers is not None):
	  ds_names[ 'fixed_detector' ].append( cur_name )
	  ds_names[ 'axials' ].append( cur_name )
	  ds_defs_by_name[ cur_name ] = ds_defs[ 'fixed_detector' ]

#x	  if cur_axial_mesh is None:
#x	    cur_axial_mesh = core.fixedDetectorMesh
#x	    cur_axial_mesh_centers = core.fixedDetectorMeshCenters

#			-- If 'detector' and ':assembly' shapes match must
#			-- disambiguate on name
#			--
##	elif cur_name == 'detector_response':
#	elif cur_name.find( 'response' ) >= 0:
#	  if cur_shape == ds_defs[ 'detector' ][ 'shape' ]:
#	    ds_names[ 'detector' ].append( cur_name )
#	    ds_names[ 'axial' ].append( cur_name )
#	    ds_defs_by_name[ cur_name ] = ds_defs[ 'detector' ]
	elif core.ndetax == core.nax and core.ndet == core.nass and \
	    cur_shape == ds_defs[ 'detector' ][ 'shape' ] and \
	    cur_name.find( 'detector' ) >= 0:
	  ds_names[ 'detector' ].append( cur_name )
	  ds_names[ 'axials' ].append( cur_name )
	  ds_defs_by_name[ cur_name ] = ds_defs[ 'detector' ]

#x	  if cur_axial_mesh is None:
#x	    cur_axial_mesh = core.detectorMesh

#			-- Not a scalar
#			--
	else:
	  process_non_scalar(
	      cur_name, cur_shape, ds_defs, ds_defs_by_name, ds_names,
	      scalar_shape
	      )
        #end if-else on shape

	if cur_axial_mesh is not None:
	  ds_axial_mesh[ cur_name ] = cur_axial_mesh
	if cur_axial_mesh_centers is not None:
	  ds_axial_mesh_centers[ cur_name ] = cur_axial_mesh_centers
      #end if not a copy
    #end for st_group keys

#		-- Now, those in subgroups
#		--
    for def_name, def_item in ds_defs.iteritems():
      sub_group = sub_group_name = None
      if 'group' in def_item and def_item[ 'group' ] in st_group:
	sub_group_name = def_item[ 'group' ]
	if sub_group_name in st_group and \
	    isinstance( st_group[ sub_group_name ], h5py.Group ):
	  sub_group = st_group[ sub_group_name ]

      if sub_group is not None:
	for cur_name in sub_group:
	  if not isinstance( sub_group[ cur_name ], h5py.Group ):
            cur_shape = sub_group[ cur_name ].shape
	    if cur_shape == def_item[ 'shape' ]:
	      cur_path_name = sub_group_name + '/' + cur_name
	      ds_names[ def_item[ 'type' ] ].append( cur_path_name )
	      ds_defs_by_name[ cur_path_name ] = def_item
	      if def_item.get( 'axial_axis', -1 ) >= 0:
                ds_names[ 'axials' ].append( cur_path_name )
	      if sub_group_name == 'vessel_tally' and \
	          cur_name.find( '_error' ) < 0:
	        self.SetDataSetScaleType( cur_path_name, 'log' )
	  #end if not an h5py.Group
	#end for cur_name
      #end if sub_group
    #end for def_name, def_item

#		-- Last, Look at CORE Group
#		--
    for cur_name in core.group:
      cur_name_lc = cur_name.lower()
      if not (
          isinstance( core.group[ cur_name ], h5py.Group ) or
	  cur_name_lc in CORE_SKIP_DS_NAMES or
	  cur_name_lc in ds_defs_by_name
	  ):
	cur_dset = core.group[ cur_name ]
        cur_shape = cur_dset.shape

	cur_axial_mesh, cur_axial_mesh_centers = \
	    process_attrs( cur_dset, cur_shape, messages )

	#bank_pos, emulate as individual scalars
        if len( cur_shape ) == 0 or cur_shape == scalar_shape:
	  process_scalar(
	      cur_dset, cur_name, cur_shape,
	      ds_defs, ds_defs_by_name, ds_names,
	      scalar_shape, self.coreGroupDataSets
	      )
	else:
	  process_non_scalar(
	      cur_name, cur_shape, ds_defs, ds_defs_by_name, ds_names,
	      scalar_shape, self.coreGroupDataSets
	      )

	ds_names[ 'core' ].append( cur_name )
	if cur_axial_mesh is not None:
	  ds_axial_mesh[ cur_name ] = cur_axial_mesh
	if cur_axial_mesh_centers is not None:
	  ds_axial_mesh_centers[ cur_name ] = cur_axial_mesh_centers
      #end if not
    #end for cur_name in core.group:

#		-- Cull names not in all states?
#		--
#    cull_ds_names = []
#    for st_ndx in range( 1, len( self.states ) ):
#      cur_group = self.states[ st_ndx ].group

#		-- Sort names
#		--
    for n in ds_names:
      ds_names[ n ].sort()

#		-- Set property values
    self.dataSetDefs = ds_defs
    self.dataSetDefsByName = ds_defs_by_name
    self.dataSetNames = ds_names
    self.dataSetAxialMesh = ds_axial_mesh
    self.dataSetAxialMeshCenters = ds_axial_mesh_centers

    return  messages
  #end _ResolveDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ResolveDerivedDataSet()		-
  #----------------------------------------------------------------------
  def ResolveDerivedDataSet( self,
      ds_category, derived_label, ds_name,
      agg_name = 'avg'
      ):
    """Checks for prior existence and if necessary creates the derived dataset.
    Args:
        ds_category (str): dataset category, e.g., 'channel', 'pin'
	derived_label (str): derived label, e.g., 'assembly', 'axial', 'core',
	    'radial'
	ds_name (str): dataset name that is in the category/type, e.g.,
	    'pin_powers
        agg_name (str): name of aggration function, e.g., 'avg', 'max', 'min'
    Returns:
        str:  name of the new dataset or None if the parameters are invalid
"""
    match_name = \
        self.HasDerivedDataSet( ds_category, derived_label, ds_name, agg_name )
    if not match_name:
      match_name = self.\
          _CreateDerivedDataSet( ds_category, derived_label, ds_name, agg_name )
    return  match_name
  #end ResolveDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ResolveRangeExpression()		-
  #----------------------------------------------------------------------
  def ResolveRangeExpression( self, *op_value_pairs ):
    """Creates a single expression satisfying the specified expressions.
@param  ds_name		dataset name
@param  op_value_pairs	sequence of op-value pairs, where op is one of
			'=', '<', '<=', '>', '>='
@return			expression on "x"
"""
    above_op = above_value = below_op = below_value = None

    for i in xrange( 0, len( op_value_pairs ) - 1, 2 ):
      op = op_value_pairs[ i ]
      value = op_value_pairs[ i + 1 ]

      if op in ( '<', '<=' ):
        if not below_op or value > below_value:
	  below_op = op
	  below_value = value
        elif value == below_value and below_op == '<' and op == '<=':
	  below_op = op

      elif op in ( '>', '>=' ):
        if not above_op or value < above_value:
	  above_op = op
	  above_value = value
        elif value == above_value and above_op == '>' and op == '>=':
	  above_op = op

      elif op == '=' and not (above_op or below_op):
        above_op = '>='
	below_op = '<='
	above_value = below_value = value
    #end for i

    expr = ''
    if above_op:
      #if expr: expr += ' and '
      expr += 'x ' + above_op + ' ' + '{0:.6g}'.format( above_value )
    if below_op:
      if expr: expr += ' and '
      expr += 'x ' + below_op + ' ' + '{0:.6g}'.format( below_value )

    return  expr
  #end ResolveRangeExpression


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
  #	METHOD:		DataModel.SetDataSetScaleType()			-
  #----------------------------------------------------------------------
  def SetDataSetScaleType( self, ds_name, scale_type = 'linear' ):
    """Associates the scale type with the named dataset.
    Args:
        ds_name (str): dataset name
	scale_type (str): 'linear' or 'log', defaulting to 'linear'
"""
#    if scale_type != 'log':
#      scale_type = 'linear'
    self.dataSetScaleTypes[ ds_name ] = scale_type
  #end SetDataSetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.SetDataSetThreshold()			-
  #----------------------------------------------------------------------
  def SetDataSetThreshold( self, ds_name, range_expr = None ):
    """Adds or replaces the threshold RangeExpression the specified
dataset.
@param  ds_name		dataset name
@param  range_expr	either an expression string, a RangeExpression
			instance, or None to remove the threshold
@exception		on expression parse error
"""
    if ds_name:
      if range_expr:
        if not isinstance( range_expr, RangeExpression ):
          range_expr = RangeExpression( str( range_expr ) )
        self.dataSetThresholds[ ds_name ] = range_expr

      elif ds_name in self.dataSetThresholds:
        del self.dataSetThresholds[ ds_name ]

#		-- Clear any calculated ranges
#		--
      key_list = []
      for key in self.ranges.keys():
        if key.startswith( ds_name ):
	  key_list.append( key )
      for key in key_list:
        del self.ranges[ key ]

      for i in xrange( len( self.rangesByStatePt ) ):
	range_dict = self.rangesByStatePt[ i ]
        key_list = []
	for key in range_dict.keys():
	  if key.startswith( ds_name ):
	    key_list.append( key )
        for key in key_list:
          del range_dict[ key ]
      #end for i

#		-- Clear any threshold datasets
#		--
      threshold_name = 'threshold:' + ds_name
      if self.derivedCoreGroup is not None and \
          threshold_name in self.derivedCoreGroup:
        del self.derivedCoreGroup[ threshold_name ]

      elif self.derivedStates:
        for ndx in xrange( len( self.derivedStates ) ):
          derived_st = self.derivedStates[ ndx ]
	  if derived_st.HasDataSet( threshold_name ):
	    derived_st.RemoveDataSet( threshold_name )
        #end for ndx
      #end if self.derivedStates
    #end if ds_name
  #end SetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.SetName()				-
  #----------------------------------------------------------------------
  def SetName( self, name ):
    """Accessor for the 'name' property.
@param  name		new name
"""
    self.name = name
  #end SetName


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
    #return  ( 0.0, -1, -1, -1 )
    return  self.CreateEmptyAxialValueObject()
  #end CreateEmptyAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateEmptyAxialValueObject()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateEmptyAxialValueObject():
    """
@return			( axial_cm, core_ndx, detector_ndx, fixed_detector_ndx )
			as ( 0.0, -1, -1, -1 )
"""
    return  \
    AxialValue(
        cm = 0.0, pin_ndx = -1, detector_ndx = -1, fixed_detector_ndx = -1,
	tally_ndx = -1, subpin_ndx = -1
	)
  #end CreateEmptyAxialValueObject


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateEmptyTallyAddress()		-
  #----------------------------------------------------------------------
  @staticmethod
  def CreateEmptyTallyAddress():
    """
@return			( name, multIndex, radiusIndex, statIndex, thetaIndex )
			as ( None, 0, 0, 0, 0 )
"""
    #return  TallyAddress( name = None, mult = -1, stat = -1, theta = 0.0 )
    return  \
    TallyAddress(
        name = None,
	multIndex = 0, statIndex = 0, radiusIndex = 0, thetaIndex = 0
	)
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
#	CLASS:		DataSetName					-
#------------------------------------------------------------------------
class DataSetName( object ):
  """Encapsulation of a dataset name.
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__eq__()				-
  #----------------------------------------------------------------------
  def __eq__( self, that ):
    return \
        self._name == that._name  if isinstance( that, DataSetName ) else \
	self._name == str( that )
  #end __eq__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__ge__()				-
  #----------------------------------------------------------------------
  def __ge__( self, that ):
    return \
        self._name >= that._name  if isinstance( that, DataSetName ) else \
	self._name >= str( that )
  #end __ge__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__gt__()				-
  #----------------------------------------------------------------------
  def __gt__( self, that ):
    return \
        self._name > that._name  if isinstance( that, DataSetName ) else \
	self._name > str( that )
  #end __gt__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__hash__()				-
  #----------------------------------------------------------------------
  def __hash__( self ):
    return  hash( self._name )
  #end __hash__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args ):
    """There are three forms of valid initialization:
__init__( qname )
  qname		qualified name, overrides other params

__init__( model_name, display_name )
  model_name	model name
  ds_name	dataset name

__init__( dict_value )
  dict_value	dict
"""
    self._modelName = ''
    self._displayName = ''
    self._name = ''

    if args and len( args ) > 0:
      if len( args ) >= 2:
	self._modelName = str( args[ 0 ] )
	self._displayName = str( args[ 1 ] )
	self._name = \
	    self._modelName + '|' + self._displayName \
	    if self._modelName else \
	    self._displayName

      elif isinstance( args[ 0 ], dict ):
        self._modelName = args[ 0 ].get( '_modelName', '' )
        self._displayName = args[ 0 ].get( '_displayName', '' )
	self._name = \
	    self._modelName + '|' + self._displayName \
	    if self._modelName else \
	    self._displayName

      else:
        self._name = str( args[ 0 ] )
	ndx = self._name.find( '|' )
	if ndx > 0:
          self._modelName = self._name[ 0 : ndx ]
	  self._displayName = self._name[ ndx + 1 : ]
        else:
          self._displayName = self._name
    #end if args

    self.__dict__[ '__jsonclass__' ] = 'data.datamodel.DataSetName'
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__le__()				-
  #----------------------------------------------------------------------
  def __le__( self, that ):
    return \
        self._name <= that._name  if isinstance( that, DataSetName ) else \
	self._name <= str( that )
  #end __le__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__lt__()				-
  #----------------------------------------------------------------------
  def __lt__( self, that ):
    return \
        self._name < that._name  if isinstance( that, DataSetName ) else \
	self._name < str( that )
  #end __lt__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__ne__()				-
  #----------------------------------------------------------------------
  def __ne__( self, that ):
    return  not self.__eq__( that )
  #end __ne__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__repr__()				-
  #----------------------------------------------------------------------
  def __repr__( self ):
    return  'datamodel.DataSetName(%s)' % self._name
#    return  \
#        'datamodel.DataSetName(%s, %s, %s)' % \
#	( self._name, self._modelName, self._displayName )
  #end __repr__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.__str__()				-
  #----------------------------------------------------------------------
  def __str__( self ):
    return  self._name
  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.GetDisplayName()			-
  #----------------------------------------------------------------------
  def GetDisplayName( self ):
    return  self._displayName
  #end GetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.GetModelName()			-
  #----------------------------------------------------------------------
  def GetModelName( self ):
    return  self._modelName
  #end GetModelName


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.GetName()				-
  #----------------------------------------------------------------------
  def GetName( self ):
    return  self._name
  #end GetName


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.GetShortName()			-
  #----------------------------------------------------------------------
  def GetShortName( self ):
    return \
        self._modelName[ : 3 ] + '|' + self._displayName \
	if self._modelName else \
	self._displayName
  #end GetShortName


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.tojson()				-
  #----------------------------------------------------------------------
  def tojson( self ):
    """
@return		self.__dict__
"""
    #return  self.__dict__
    rec = \
      {
      '__jsonclass__': 'data.datamodel.DataSetName',
      'name': self.name
      }
    return  rec
  #end tojson


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	displayName					-
  #----------------------------------------------------------------------
  displayName = property( GetDisplayName )


  #----------------------------------------------------------------------
  #	PROPERTY:	modelName					-
  #----------------------------------------------------------------------
  modelName = property( GetModelName )


  #----------------------------------------------------------------------
  #	PROPERTY:	name						-
  #----------------------------------------------------------------------
  name = property( GetName )


  #----------------------------------------------------------------------
  #	PROPERTY:	shortName					-
  #----------------------------------------------------------------------
  shortName = property( GetShortName )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataSetName.fromjson()				-
  #----------------------------------------------------------------------
  @staticmethod
  def fromjson( json_in ):
#    return  \
#    DataSetName(
#        dict_in.get( '_modelName', '' ),
#	dict_in.get( '_displayName', '' )
#	)
    return  DataSetName( json_in.get( 'name', '' ) )
  #end fromjson

#end DataSetName


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

      if 'keff' in state_group:
	item = state_group[ 'keff' ]
        self.keff = item[ 0 ] if len( item.shape ) > 0 else item[ () ]

      if 'pin_powers' in state_group:
        #self.pinPowers = state_group[ 'pin_powers' ].value
        self.pinPowers = np.array( state_group[ 'pin_powers' ] )
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
    """No longer called from State.Init() in favor of
DataModelMgr.ResolveAvailableTimeDataSets().
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
#	CLASS:		TallyAddress					-
#------------------------------------------------------------------------
class TallyAddress( dict ):
  """Encapsulation of all the addressing related to showing tally results.
Properties:
  name			[0] DataSetName instance
  multIndex		[1] 0-based multiplier index
  statIndex		[2] 0-based stat index
  thetaIndex		[3] 0-based theta index
  radiusIndex		[4] 0-based radius index

Note tally datasets elements are referenced by [ z, th, r, mult, stat ],
but z is stored in an AxialValue instance ("axialValue" property of
widgets).
"""

#  KEY_ALIASES = dict(
#      name = 'name',
#      mult_ndx = 'multIndex', radius_ndx = 'radiusIndex',
#      stat_ndx = 'statIndex', theta_ndx = 'thetaIndex'
#      )


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__eq__()				-
  #----------------------------------------------------------------------
  def __eq__( self, that ):
    return  isinstance( that, TallyAddress ) and self == that
  #end __eq__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__getitem__()			-
  #----------------------------------------------------------------------
  def __getitem__( self, ndx ):
    result = None
    if isinstance( ndx, int ):
      result = \
	  self.GetName()  if ndx == 0 else \
	  self.GetMultIndex()  if ndx == 1 else \
	  self.GetStatIndex()  if ndx == 2 else \
	  self.GetThetaIndex()  if ndx == 3 else \
	  self.GetRadiusIndex()  if ndx == 3 else \
	  -1
    else:
      result = super( TallyAddress, self ).__getitem__( ndx )
    return  result
  #end __getitem__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__hash__()				-
  #----------------------------------------------------------------------
  def __hash__( self ):
    value = hash( self.name ) if self.name else 0
    value *= 11
    value += self.multIndex
    value *= 11
    value += self.statIndex
    value *= 11
    value += self.thetaIndex
    value *= 11
    value += self.radiusIndex
    return  int( value )
  #end __hash__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, *args, **kwargs ):
    """Forms of valid initialization:
__init__( name = value, multIndex = value, ... )

__init__( dict_value )
  dict_value	dict
"""
#    if kwargs:
#      for k, v in TallyAddress.KEY_ALIASES.iteritems():
#        if k in kwargs:
#          kwargs[ v ] = kwargs[ k ]
#	  del kwargs[ k ]
#      #end for k, v

    super( TallyAddress, self ).__init__( *args, **kwargs )

    name = self.name
    if name is not None and not isinstance( name, DataSetName ):
      self[ 'name' ] = DataSetName( name )

    self[ '__jsonclass__' ] = 'data.datamodel.TallyAddress'
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__setitem__()			-
  #----------------------------------------------------------------------
#  def __setitem__( self, ndx, value ):
#    if not isinstance( ndx, int ):
#      if ndx in TallyAddress.KEY_ALIASES:
#        ndx = TallyAddress.KEY_ALIASES[ ndx ]
#
#    super( TallyAddress, self ).__setitem__( ndx, value )
#  #end __setitem__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.__str__()				-
  #----------------------------------------------------------------------
#  def __str__( self ):
#    return  self._name
#  #end __str__


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.Equals()				-
  #----------------------------------------------------------------------
  def Equals( self, tally_addr, *ignores ):
    """Checks for equality on every property except those specified in ignores.
Property names: 'multIndex', 'name', 'radiusIndex', 'statIndex', 'thetaIndex'

  :param ignores: Property names to ignore in comparison
  :type ignore: str, ...
  :param tally_addr: Object to which to compare, cannot be None
  :type tally_addr: TallyAddress
"""
    eq = tally_addr is not None
    if eq and not (ignores and 'name' in ignores):
      this_val = self.get( 'name', '' )
      that_val = tally_addr.get( 'name', '' )
      eq = this_val == that_val

    if eq:
      for p in ( 'multIndex', 'radiusIndex', 'statIndex', 'thetaIndex' ):
	if not (ignores and p in ignores):
          this_val = self.get( p, -1 )
          that_val = tally_addr.get( p, -1 )
	  eq = this_val == that_val
	  if not eq: break
      #end for p
    #end if eq

    return  eq
  #end Equals


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.GetName()				-
  #----------------------------------------------------------------------
  def GetName( self ):
    return  self.get( 'name' )
  #end GetName


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.GetMultIndex()			-
  #----------------------------------------------------------------------
  def GetMultIndex( self ):
    return  self.get( 'multIndex', -1 )
  #end GetMultIndex


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.GetRadiusIndex()			-
  #----------------------------------------------------------------------
  def GetRadiusIndex( self ):
    return  self.get( 'radiusIndex', -1 )
  #end GetRadiusIndex


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.GetStatIndex()			-
  #----------------------------------------------------------------------
  def GetStatIndex( self ):
    return  self.get( 'statIndex', -1 )
  #end GetStatIndex


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.GetThetaIndex()			-
  #----------------------------------------------------------------------
  def GetThetaIndex( self ):
    return  self.get( 'thetaIndex', -1 )
  #end GetThetaIndex


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.SetThetaIndex()			-
  #----------------------------------------------------------------------
  def SetThetaIndex( self, value ):
    self[ 'thetaIndex' ] = value
  #end SetThetaIndex


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.copy()				-
  #----------------------------------------------------------------------
  def copy( self ):
    return  type( self )( self )
  #end copy


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.tojson()				-
  #----------------------------------------------------------------------
  def tojson( self ):
    """
@return		self
"""
    #return  self.__dict__
    return  self
  #end tojson


#		-- Property Definitions
#		--


  #----------------------------------------------------------------------
  #	PROPERTY:	name						-
  #----------------------------------------------------------------------
  name = property( GetName )


  #----------------------------------------------------------------------
  #	PROPERTY:	multIndex					-
  #----------------------------------------------------------------------
  multIndex = property( GetMultIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	radiusIndex					-
  #----------------------------------------------------------------------
  radiusIndex = property( GetRadiusIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	statIndex					-
  #----------------------------------------------------------------------
  statIndex = property( GetStatIndex )


  #----------------------------------------------------------------------
  #	PROPERTY:	thetaIndex					-
  #----------------------------------------------------------------------
  thetaIndex = property( GetThetaIndex, SetThetaIndex )


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		TallyAddress.fromjson()				-
  #----------------------------------------------------------------------
  @staticmethod
  def fromjson( dict_in ):
    """
@return		TallyAddress instance
"""
    return  TallyAddress( dict_in )
  #end fromjson

#end TallyAddress


#------------------------------------------------------------------------
#	CLASS:		VesselGeometry					-
#------------------------------------------------------------------------
class VesselGeometry( object ):
  """
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VesselGeometry.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self,
      assy_pitch = 21.5,
      symmetry_size = ( 8, 8 ),
      baffle_wd = 3.0,
      barrel_inner = 187.96,
      barrel_outer = 193.68,
      liner_inner = 219.15,
      liner_outer = 219.71,
      pad_inner = 194.64,
      pad_outer = 201.63,
      pad_angles = ( 45, ),
      pad_arc = 32,
      vessel_outer = 241.70
      ):
    """Lengths except for pad_arc are in cm.
@param  assy_pitch	assembly pitch
@param  symmetry_size	( cols, rows ) ExtractSymmetryExtent()[ 4 5 ]
@param  baffle_wd	baffle width
@param  barrel_inner	radius of barrel inner ring
@param  barrel_outer	radius of barrel outer ring
@param  liner_inner	radius of liner inner ring
@param  liner_outer	radius of liner outer ring
@param  pad_inner	radius of pad inner ring
@param  pad_outer	radius of pad outer ring
@param  pad_angles	list of angles in degrees
@param  pad_arc		pad arc length in degrees
@param  vessel_outer	radius of vessel outer ringer
"""
    self._Config(
        assy_pitch,
        symmetry_size,
        baffle_wd, barrel_inner, barrel_outer,
        liner_inner, liner_outer,
        pad_inner, pad_outer, pad_angles, pad_arc,
        vessel_outer
        )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VesselGeometry.Clone()				-
  #----------------------------------------------------------------------
  def Clone( self ):
    """Deep copy.
"""
    new_obj = self.__class__()

#		-- Scalars and references
#		--
    #for name in ( '_fluxIndex', '_meanIndex' ):
    for name in (
        'baffleSize',
        'barrelInner', 'barrelInnerOffset',
	'barrelOuter', 'barrelOuterOffset',
        'barrelSize', 'coreRadius',
        'linerInner', 'linerInnerOffset',
        'linerOuter', 'linerOuterOffset', 'linerSize',
	'padAngles', 'padArc', 'padSize',
        'padInner', 'padInnerOffset',
        'padOuter', 'padOuterOffset',
        'vesselOuter', 'vesselOuterOffset'
        ):
      setattr( new_obj, name, getattr( self, name ) )
    #end for name

    return  new_obj
  #end Clone


  #----------------------------------------------------------------------
  #	METHOD:		VesselGeometry._Config()			-
  #----------------------------------------------------------------------
  def _Config( self,
      assy_pitch = 21.5,
      symmetry_size = ( 8, 8 ),
      baffle_wd = 3.0,
      barrel_inner = 187.96,
      barrel_outer = 193.68,
      liner_inner = 219.15,
      liner_outer = 219.71,
      pad_inner = 194.64,
      pad_outer = 201.63,
      pad_angles = ( 45, ),
      pad_arc = 32,
      vessel_outer = 241.70
      ):
    """Lengths except for pad_arc are in cm.
@param  assy_pitch	assembly pitch
@param  symmetry_size	( cols, rows ) ExtractSymmetryExtent()[ 4 5 ]
@param  baffle_wd	baffle width
@param  barrel_inner	radius of barrel inner ring
@param  barrel_outer	radius of barrel outer ring
@param  liner_inner	radius of liner inner ring
@param  liner_outer	radius of liner outer ring
@param  pad_inner	radius of pad inner ring
@param  pad_outer	radius of pad outer ring
@param  pad_angles	list of angles in degrees
@param  pad_arc		pad arc length in degrees
@param  vessel_outer	radius of vessel outer ringer
"""
    self.coreRadius = assy_pitch * max( *symmetry_size )
    self.baffleSize = baffle_wd

    self.barrelInner = barrel_inner
    self.barrelInnerOffset = barrel_inner - self.coreRadius
    self.barrelOuter = barrel_outer
    self.barrelOuterOffset = barrel_outer - self.coreRadius
    self.barrelSize = barrel_outer - barrel_inner

    self.linerInner = liner_inner
    self.linerInnerOffset = liner_inner - self.coreRadius
    self.linerOuter = liner_outer
    self.linerOuterOffset = liner_outer - self.coreRadius
    self.linerSize = liner_outer - liner_inner

    self.padInner = pad_inner
    self.padInnerOffset = pad_inner - self.coreRadius
    self.padOuter = pad_outer
    self.padOuterOffset = pad_outer - self.coreRadius
    self.padSize = pad_outer - pad_inner
    self.padAngles = pad_angles
    self.padArc = pad_arc

    self.vesselOuter = vessel_outer
    self.vesselOuterOffset = vessel_outer - self.coreRadius
  #end _Config


  #----------------------------------------------------------------------
  #	METHOD:		VesselGeometry.Read()				-
  #----------------------------------------------------------------------
  def Read( self, h5_group, assy_pitch = 21.5, symmetry_size = ( 8, 8 ) ):
    """
"""
    kwargs = dict( assy_pitch = assy_pitch, symmetry_size = symmetry_size )

    for ds_name, name in (
	( 'barrel_inner_radius', 'barrel_inner' ),
	( 'barrel_outer_radius', 'barrel_outer' ),
	( 'liner_inner_radius', 'liner_inner' ),
	( 'liner_outer_radius', 'liner_outer' ),
	( 'pad_arc', 'pad_arc' ),
	( 'pad_inner_radius', 'pad_inner' ),
	( 'pad_outer_radius', 'pad_outer' ),
	( 'vessel_outer_radius', 'vessel_outer' ),
        ):
      item = h5_group.get( ds_name )
      if item is not None:
	kwargs[ name ] = item[ 0 ] if len( item.shape ) > 0 else item[ () ]
    #end for

    inner = h5_group.get( 'baffle_inner_radius' )
    outer = h5_group.get( 'baffle_outer_radius' )
    if inner is not None and outer is not None:
      inner_value = inner[ 0 ] if len( inner.shape ) > 0 else inner[ () ]
      outer_value = outer[ 0 ] if len( outer.shape ) > 0 else outer[ () ]
      kwargs[ 'baffle_wd' ] = outer_value - inner_value

    item = h5_group.get( 'pad_angles' )
    if item is not None:
      if len( item.shape ) > 0:
        kwargs[ 'pad_angles' ] = tuple( np.array( item ).tolist() )
      else:
        kwargs[ 'pad_angles' ] = ( item[ () ], )

#		-- Convert angles to degrees if necessary
    pad_arc = kwargs.get( 'pad_arc' )
    if pad_arc and pad_arc < math.pi * 2.0:
      kwargs[ 'pad_arc' ] = pad_arc * 180.0 / math.pi

    pad_angles = kwargs.get( 'pad_angles' )
    if pad_angles:
      convert = True
      for an in pad_angles:
	if an > math.pi * 2.0:
	  convert = False
	  break
      if convert:
        kwargs[ 'pad_angles' ] = [ x * 180.0 / math.pi for x in pad_angles ]
    #end if pad_angles

    self._Config( **kwargs )
  #end Read

#end VesselGeometry


#------------------------------------------------------------------------
#	CLASS:		VesselTallyDef					-
#------------------------------------------------------------------------
class VesselTallyDef( object ):
  """Encapsulates vessel tally grid/mesh information.
Total dataset shape ( z, theta, r, multiplier, stat )
For now, we only process 'mean' stat and 'flux' multiplier.
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, h5_group = None ):
    """
@param  h5_group	optional "CORE/vessel_tally" or
			"STATE_0001/vessel_tally" group, if None must
			call Read()
"""
    self.Clear()
    if h5_group is not None:
      self.Read( h5_group )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.Clear()				-
  #----------------------------------------------------------------------
  def Clear( self ):
    #self._fluxIndex = 0  # multipler_names
    #self._meanIndex = 0  # mesh_stat

    self._nmultipliers = \
    self._nr = \
    self._nstat = \
    self._ntheta = \
    self._nz = 0

    self._multiplierNames = None
    self._r = None
    self._stat = None
    self._theta = None
    self._z = None
    self._zcenters = None
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.Clone()				-
  #----------------------------------------------------------------------
  def Clone( self ):
    """Deep copy.
"""
    new_obj = self.__class__()

#		-- Scalars and references
#		--
    #for name in ( '_fluxIndex', '_meanIndex' ):
    for name in ( '_nmultipliers', '_nr', '_nstat', '_ntheta', '_nz' ):
      setattr( new_obj, name, getattr( self, name ) )
    #end for name

#		-- Numpy arrays
#		--
    for name in ( '_multiplierNames', '_r', '_stat', '_theta', '_z' ):
      value = getattr( self, name )
      if value is None:
        new_value = None
      else:
        new_value = np.copy( value )
      setattr( new_obj, name, new_value )
    #end for name

    return  new_obj
  #end Clone


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetFluxIndex()			-
  #----------------------------------------------------------------------
#  def GetFluxIndex( self ):
#    return  self._fluxIndex
#  #end GetFluxIndex


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetMeanIndex()			-
  #----------------------------------------------------------------------
#  def GetMeanIndex( self ):
#    return  self._meanIndex
#  #end GetMeanIndex


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetMultiplierNames()		-
  #----------------------------------------------------------------------
  def GetMultiplierNames( self ):
    return  self._multiplierNames
  #end GetMultiplierNames


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetNMultipliers()		-
  #----------------------------------------------------------------------
  def GetNMultipliers( self ):
    return  self._nmultipliers
  #end GetNMultipliers


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetNR()				-
  #----------------------------------------------------------------------
  def GetNR( self ):
    return  self._nr
  #end GetNR


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetNStat()			-
  #----------------------------------------------------------------------
  def GetNStat( self ):
    return  self._nstat
  #end GetNStat


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetNTheta()			-
  #----------------------------------------------------------------------
  def GetNTheta( self ):
    return  self._ntheta
  #end GetNTheta


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetNZ()				-
  #----------------------------------------------------------------------
  def GetNZ( self ):
    return  self._nz
  #end GetNZ


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetR()				-
  #----------------------------------------------------------------------
  def GetR( self ):
    return  self._r
  #end GetR


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetStat()			-
  #----------------------------------------------------------------------
  def GetStat( self ):
    return  self._stat
  #end GetStat


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetTheta()			-
  #----------------------------------------------------------------------
  def GetTheta( self ):
    return  self._theta
  #end GetTheta


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetThetaIndex()			-
  #----------------------------------------------------------------------
  def GetThetaIndex( self, theta_rad ):
    """Returns the 0-based index into self.theta for the specified value.
@param  theta_rad	theta in radians
@return			0-based index, or -1 if out of range
"""
    ndx = DataUtils.FindListIndex( self._theta, theta_rad )
    if ndx >= len( self._theta ):
      ndx = -1

    return  ndx
  #end GetThetaIndex


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetThetaRads()			-
  #----------------------------------------------------------------------
  def GetThetaRads( self, theta_ndx, center = True ):
    """Returns the theta center in radians for the specified index.
@param  theta_ndx	0-based index
@return			radians
"""
    result = 0.0
    if self._ntheta > 0:
      if theta_ndx == len( self._theta ) - 1:
        result = self._theta[ -1 ]
      elif theta_ndx >= 0 and theta_ndx < len( self._theta ) - 1:
	if center:
          result = (self._theta[ theta_ndx ] + self._theta[ theta_ndx + 1 ]) / 2.0
	else:
          result = self._theta[ theta_ndx ]

    return  result
  #end GetThetaRads


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetZ()				-
  #----------------------------------------------------------------------
  def GetZ( self ):
    return  self._z
  #end GetZ


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.GetZCenters()			-
  #----------------------------------------------------------------------
  def GetZCenters( self ):
    return  self._zcenters
  #end GetZCenters


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.IsValid()			-
  #----------------------------------------------------------------------
  def IsValid( self ):
    """
@return			True if this is valid, False if invalid or empty
"""
    return \
        self._nmultipliers > 0 and self._nr > 1 and \
	self._nstat > 0 and self._ntheta > 0 and \
	self._nz > 0
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		VesselTallyDef.Read()				-
  #----------------------------------------------------------------------
  def Read( self, h5_group ):
    """
@param  h5_group	"CORE/vessel_tally" or "STATE_0001/vessel_tally" group
"""
    self.Clear()

#		-- Assert on valid group
#		--
#    if h5_group is None or not isinstance( h5_group, h5py.Group ):
#      raise Exception( 'Must have valid HDF5 group' )
    assert isinstance( h5_group, h5py.Group ), 'Must have valid HDF5 group'

#		-- Read mesh arrays
#		--
    missing = []

    for name in ( '_r', '_stat', '_theta', '_z' ):
      ds_name = 'mesh' + name
      if ds_name in h5_group:
	value = np.array( h5_group[ ds_name ] )
        setattr( self, name, value )
	setattr( self, name.replace( '_', '_n' ), len( value ) - 1 )
      else:
	missing.append( ds_name )
        #missing.append( '"%s" not found' % ds_name )
    #end for name

    if self._z is not None and self._nz > 0:
      zarray = np.array( self._z )
      self._zcenters = (zarray[ : -1 ] + zarray[ 1 : ]) / 2.0

    for ds_name, attr_name, n_name in (
        ( 'multiplier_names', '_multiplierNames', '_nmultipliers' ),
        ( 'mesh_stat', '_stat', '_nstat' ),
	):
      if ds_name in h5_group:
        value = np.array( h5_group[ ds_name ] )
	setattr( self, attr_name, value )
	setattr( self, n_name, len( value ) )
      else:
        missing.append( ds_name )
    #end for ds_name, attr_name

#		-- Read index labels
#		--
#    if 'mesh_stat' in h5_group:
#      dset = h5_group[ 'mesh_stat' ]
#      if len( dset.shape ) > 0:
#        for i in xrange( dset.shape[ 0 ] ):
#	  if dset[ i ] == 'mean':
#	    self._meanIndex = i
#	    break
#    else:
#      missing.append( 'mesh_stat' )
#    #end if 'mesh_stat'

#    if 'multiplier_names' in h5_group:
#      dset = h5_group[ 'multiplier_names' ]
#      if len( dset.shape ) > 0:
#        for i in xrange( dset.shape[ 0 ] ):
#	  if dset[ i ] == 'flux':
#	    self._fluxIndex = i
#	    break
#    else:
#      missing.append( 'multiplier_names' )
#    #end if 'multiplier_names'

    if missing:
      raise Exception( 'Not found: ' + ', '.join( missing ) )
  #end Read


#		-- Properties
#		--

  #fluxIndex = property( GetFluxIndex )
  #meanIndex = property( GetMeanIndex )
  multiplierNames = property( GetMultiplierNames )
  nmultipliers = property( GetNMultipliers )
  nr = property( GetNR )
  nstat = property( GetNStat )
  ntheta = property( GetNTheta )
  nz = property( GetNZ )
  r = property( GetR )
  stat = property( GetStat )
  theta = property( GetTheta )
  z = property( GetZ )
  zcenters = property( GetZCenters )

#end VesselTallyDef


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataModel.main()
