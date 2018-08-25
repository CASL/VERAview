#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel_mgr.py				-
#	HISTORY:							-
#		2018-07-26	leerw@ornl.gov				-
#	  Renaming non-derived dataset category/type from 'axial' to
#	  'axials' to disambiguate from ':axial' displayed name.
#		2018-06-01	leerw@ornl.gov				-
#	  Checking for offset 'pin' axial mesh in _UpdateMeshValues().
#		2018-05-29	leerw@ornl.gov				-
#	  Bug fix: can't use capitalize() b/c it lowers all but first char.
#		2017-08-18	leerw@ornl.gov				-
#	  Using AxialValue class.
#		2017-07-18	leerw@ornl.gov				-
#	  Replacing ignore range with threshold and using RangeExpression.
#	  Added {Load,Save}DataSetThresholds().
#		2017-07-17	leerw@ornl.gov				-
#	  Adding by qds_name ignore ranges.
#		2017-06-05	leerw@ornl.gov				-
#	  Adapting to axial mesh changes.
#		2017-04-21	leerw@ornl.gov				-
#	  Added HtmlMessage, using for CheckDataModelIsCompatible().
#		2017-04-13	leerw@ornl.gov				-
#	  Renamed _CheckDataModelIsCompatible() to
#	  CheckDataModelIsCompatible() since called from FileManagerBean.
#		2017-03-27	leerw@ornl.gov				-
#	  Dealing with tally mesh.
#		2017-03-25	leerw@ornl.gov				-
#	  Added GetRangeAll().
#		2017-02-15	leerw@ornl.gov				-
#	  Not considering detectorMap in _CheckDataModelIsCompatible().
#		2017-02-06	leerw@ornl.gov				-
#	  Fixed bug in ExtractSymmetryExtent() with even number of
#	  assemblies.
#		2017-01-14	leerw@ornl.gov				-
#	  Starting CreateDiffDataSet().
#		2017-01-12	leerw@ornl.gov				-
#	  Added IsChannelType().
#		2016-12-27	leerw@ornl.gov				-
#	  Added GetDetectorMeshIndex and GetFixedDetectorMeshCentersIndex().
#		2016-12-26	leerw@ornl.gov				-
#	  Added check for core_map and detector_map equality in
#	  _CheckDataModelIsCompatible().
#	  Added IsDetectorOperable().
#		2016-12-22	leerw@ornl.gov				-
#	  Modified the GetXxxMeshXxx() methods to accept a model_name
#	  param.
#		2016-12-13	leerw@ornl.gov				-
#	  Added GetDataSetDisplayName().
#		2016-12-09	leerw@ornl.gov				-
#		2016-12-08	leerw@ornl.gov				-
#	  Adding support methods or widgets.
#		2016-12-02	leerw@ornl.gov				-
#	  Added GetFirstDataModel().
#		2016-12-01	leerw@ornl.gov				-
#	  Moved {Assemble,Parse}QDataSetName() to datamodel.DataSetNamer
#	  class.
#		2016-11-30	leerw@ornl.gov				-
#		2016-11-29	leerw@ornl.gov				-
#	  Review and clean-up.
#		2016-08-19	leerw@ornl.gov				-
#		2016-08-18	leerw@ornl.gov				-
#------------------------------------------------------------------------
import bisect, cStringIO, functools, h5py, \
    logging, json, math, os, sys, \
    tempfile, threading, traceback
import numpy as np
import pdb

from data.datamodel import *
from data.differences import *
from data.utils import *
from event.event import *


#------------------------------------------------------------------------
#	CLASS:		HtmlException					-
#------------------------------------------------------------------------
class HtmlException( Exception ):
  """Extends Exception with an 'htmlMessage' property.  Note the
htmlMessage content is a body snippet.  Call the WrapDocument()
or WrapBody() method to add HTML trappings.
"""


  #----------------------------------------------------------------------
  #	METHOD:		HtmlException.__init__()			-
  #----------------------------------------------------------------------
  def __init__( self, message, html_message ):
    """
"""
    super( HtmlException, self ).__init__( message )
    self.htmlMessage = html_message
  #end __init__

#end HtmlException


#------------------------------------------------------------------------
#	CLASS:		DataModelMgr					-
#------------------------------------------------------------------------
class DataModelMgr( object ):
  """Data/model bean encapsulation.  For now we read the
'CORE' group as the 'core' property, and all the states as the 'states'
property.

Events:
  dataSetAdded		OnDataSetAdded( self, model, ds_display_name )
			callable( self, model, ds_display_name )
  modelAdded		OnModelAdded( self, model_name )
			callable( self, model_name )
  modelRemoved		OnModelRemoved( self, model_name )
			callable( self, model_name )

Properties:
  dataModelNames	list of model names in order added
  dataModels		dict of DataModel objects keyed by name
  #dataSetNamesVersion	counter to indicate changes
  maxAxialValue		maximum axial value (cm) across all DataModels
"""


#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.__del__()				-
  #----------------------------------------------------------------------
  def __del__( self ):
    self.Close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self ):
    """
"""
#    self.allMesh = \
#    self.allMeshCenters = \
#    self.axialMesh = \
#    self.axialMeshCenters = None
    self.axialMeshCentersDict = {}
    self.axialMeshDict = {}
    self.core = None
    self.dataModelNames = []
    self.dataModels = {}
    #self.dataSetNamesVersion = 0
    self.detectorMap = None
#    self.detectorMesh = \
#    self.fixedDetectorMesh = \
#    self.fixedDetectorMeshCenters = None
    self.listeners = \
        { 'dataSetAdded': [], 'modelAdded': [], 'modelRemoved': [] }
    self.logger = logging.getLogger( 'data' )
    self.maxAxialValue = 0.0
#    self.tallyMesh = \
#    self.tallyMeshCenters = None
    self.timeDataSet = 'state'
    self.timeValues = []
    self.timeValuesById = {}
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.AddListener()			-
  #----------------------------------------------------------------------
  def AddListener( self, event_name, listener ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener not in self.listeners[ event_name ]:
        self.listeners[ event_name ].append( listener )
    #end if event_name
  #end AddListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CheckDataModelIsCompatible()	-
  #----------------------------------------------------------------------
  def CheckDataModelIsCompatible( self, dm ):
    """Checks dm for a compatible core geometry.
@param  dm		DataModel to check
@throws			HtmlException with message body snippet if incompatible
"""
    if dm:
      if not dm.HasData():
        raise  HtmlException( 'Incompatible', 'Required VERA data not found' )

      msg = ''

      if len( self.dataModelNames ) > 0:
	cur_core = self.core
	dm_core = dm.GetCore()
#			-- Core symmetry
#			--
	if cur_core.coreSym != dm_core.coreSym or \
	    cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_templ = """<ul>
<li>Incompatible core geometry</li>
<p/><table border="1" cellpadding="6" cellspacing="0">
<tr><th>Property</th><th>%(dm.name)s</th><th>Current</th></tr>
<tr><td>coreSym</td><td>%(dm_core.coreSym)d</td><td>%(cur_core.coreSym)d</td></tr>
<tr><td>nass</td><td>%(dm_core.nass)d</td><td>%(cur_core.nass)d</td></tr>
<tr><td>nassx</td><td>%(dm_core.nassx)d</td><td>%(cur_core.nassx)d</td></tr>
<tr><td>nassy</td><td>%(dm_core.nassy)d</td><td>%(cur_core.nassy)d</td></tr>
<tr><td>npinx</td><td>%(dm_core.npinx)d</td><td>%(cur_core.npinx)d</td></tr>
<tr><td>npiny</td><td>%(dm_core.npiny)d</td><td>%(cur_core.npiny)d</td></tr>
</table><p/>
"""
	  values = \
	    {
	    'cur_core.coreSym': cur_core.coreSym,
	    'cur_core.nass': cur_core.nass,
	    'cur_core.nassx': cur_core.nassx,
	    'cur_core.nassy': cur_core.nassy,
	    'cur_core.npinx': cur_core.npinx,
	    'cur_core.npiny': cur_core.npiny,
	    'dm.name': dm.name,
	    'dm_core.coreSym': dm_core.coreSym,
	    'dm_core.nass': dm_core.nass,
	    'dm_core.nassx': dm_core.nassx,
	    'dm_core.nassy': dm_core.nassy,
	    'dm_core.npinx': dm_core.npinx,
	    'dm_core.npiny': dm_core.npiny
	    }
	  msg = msg_templ % values

#			-- Core map
#			--
	if not np.array_equal( cur_core.coreMap, dm_core.coreMap ):
	  if len( msg ) == 0:
	    msg = '<ul>\n'
	  msg += '<li>CORE/core_map differs</li>\n'

#			-- Detector map
#			--
#	if self.detectorMap is not None and dm.HasDetectorData() and \
#	    not np.array_equal( cur_core.detectorMap, dm_core.detectorMap ):
#	  msg += '\n* detector_map differs\n'
      #end if len

      if msg:
	msg += '</ul>\n'
	raise HtmlException( 'Incompatible', msg )
    #end if dm
  #end CheckDataModelIsCompatible


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CheckDataModelIsCompatible_orig()	-
  #----------------------------------------------------------------------
  def CheckDataModelIsCompatible_orig( self, dm ):
    """Checks dm for a compatible core geometry.
@param  dm		DataModel to check
@throws			Exception with message if incompatible
"""
    if dm:
      if not dm.HasData():
        raise  Exception( 'Required VERA data not found' )

      msg = ''

      if len( self.dataModelNames ) > 0:
	cur_core = self.core
	dm_core = dm.GetCore()
#			-- Core symmetry
#			--
	if cur_core.coreSym != dm_core.coreSym or \
	    cur_core.nass != dm_core.nass or \
	    cur_core.nassx != dm_core.nassx or \
	    cur_core.npinx != dm_core.npinx or \
	    cur_core.npiny != dm_core.npiny:
	  msg_fmt = \
	      '\n* Incompatible core geometry:\n' + \
	      '\tcoreSym=%d, nass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d\n' + \
	      'is not compatible with\n' + \
	      '\tcoreSym=%d, nass=%d, nassx=%d, nassy=%d, npinx=%d, npiny=%d'
	  msg = msg_fmt % (
	      dm_core.coreSym, dm_core.nass,
	      dm_core.nassx, dm_core.nassy,
	      dm_core.npinx, dm_core.npiny,
	      cur_core.coreSym, cur_core.nass,
	      cur_core.nassx, cur_core.nassy,
	      cur_core.npinx, cur_core.npiny
	      )

#			-- Core map
#			--
	if not np.array_equal( cur_core.coreMap, dm_core.coreMap ):
	  msg += '\n* core_map differs\n'

#			-- Detector map
#			--
#	if self.detectorMap is not None and dm.HasDetectorData() and \
#	    not np.array_equal( cur_core.detectorMap, dm_core.detectorMap ):
#	  msg += '\n* detector_map differs\n'
      #end if len

      if msg:
        raise  Exception( msg )
    #end if dm
  #end CheckDataModelIsCompatible_orig


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
    names = list( self.dataModelNames )
    for dm_name in names:
      self.CloseModel( dm_name, True )
  #end Close


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CloseModel()			-
  #----------------------------------------------------------------------
  def CloseModel( self, model_param, closing_all = False ):
    """Opens the HDF5 file or filename.
@param  model_param	either a DataModel instance or a model name/ID string
@param  closing_all	if True, no local state updates are performed
@param  update_flag	True to update 
@return			True if removed, False if not found
"""
    result = False
    if isinstance( model_param, DataModel ):
      model_name = model_param.GetName()
    else:
      model_name = str( model_param )

    if model_name in self.dataModels:
      dm = self.dataModels[ model_name ]
      #model_name = dm.GetName()
      dm.RemoveListener( 'newDataSet', self )
      dm.Close()

      del self.dataModels[ model_name ]
      del self.timeValuesById[ model_name ]
      self.dataModelNames.remove( model_name )

      if not closing_all:
        if len( self.dataModelNames ) == 1:
	  #self.core = self.dataModels.get( self.dataModelNames[ 0 ] ).GetCore()
	  first_core = self.dataModels.get( self.dataModelNames[ 0 ] ).GetCore()
	  self.core = first_core.Clone()

        self._UpdateMeshValues()
        self._UpdateTimeValues()
        #self.dataSetNamesVersion += 1
	self._FireEvent( 'modelRemoved', model_name )
      #end if not closing_all

      result = True

    return  result
  #end CloseModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateAssemblyAddr()		-
  #----------------------------------------------------------------------
  def CreateAssemblyAddr( self, col, row ):
    """Creates tuple from the column and row indexes.
@param  col		0-based column index
@param  row		0-based row index
@return			0-based ( assy_ndx, col, row )
"""
    core = self.GetCore()
    if core is not None and \
	col >= 0 and row >= 0 and \
        col < core.coreMap.shape[ 1 ] and row < core.coreMap.shape[ 0 ]:
      result = ( core.coreMap[ row, col ], col, row )
    else:
      result = ( -1, -1, -1 )

    return  result
  #end CreateAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.CreateDiffDataSet()		-
  #----------------------------------------------------------------------
  def CreateDiffDataSet( self,
      ref_qds_name, comp_qds_name, diff_ds_name,
      diff_mode = 'delta', interp_mode = 'linear',
      listener = None
      ):
    """Create new difference dataset to be stored as a derived dataset in
the comp_qds_name model.  Thus, the axial mesh and time
values are from the comp_qds_name model.  The current timeDataSet is used
to resolve times between the datasets.  The ref and comp DataModels can
be the same.
@param  ref_qds_name	reference dataset x in x - y
@param  comp_qds_name	comparison dataset y in x - y
@param  diff_ds_name	name of difference dataset
@param  diff_mode	difference mode, must start with one of 'delta', 'pct'
@param  interp_mode	interpolation mode, one of 'linear', 'quad', 'cubic'
@param  listener	optional callable( message, cur_step, step_count )
@return			difference DataSetName
@exception		if diff_ds_name not created in comp_qds_name.modelName
@deprecated  Just instantiate differences.Differences.
"""
    return \
    Differences( self )(
        ref_qds_name, comp_qds_name, diff_ds_name,
	listener
	)
  #end CreateDiffDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ExtractSymmetryExtent()		-
  #----------------------------------------------------------------------
  def ExtractSymmetryExtent( self ):
    """Returns the starting horizontal (left) and ending vertical (top)
assembly 0-based indexes, inclusive, and the right and bottom indexes,
exclusive, followed by the number of assemblies in the horizontal and vertical
dimensions.
@return			None if core is None, otherwise
			( left, top, right+1, bottom+1, dx, dy )
"""
    result = None

    core = self.GetCore()
    if core is not None:
      bottom = core.nassy
      right = core.nassx

      if core.coreSym == 4:
        left = 0  if core.nassx <= 2 else  core.nassx >> 1
        top = 0  if core.nassy <= 2 else  core.nassy >> 1
      elif core.coreSym == 8:
	left = core.nassx >> 2
	top = core.nassy >> 2
      else:
	left = 0
	top = 0

      result = ( left, top, right, bottom, right - left, bottom - top )
    #end if

    return  result  if result is not None else  ( 0, 0, 0, 0, 0, 0 )
  #end ExtractSymmetryExtent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindChannelMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindChannelMinMaxValue(
      self, mode, qds_name, time_value, assy_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with channel addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'channel' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindChannelMinMaxValue(
	  mode, qds_name.displayName, state_ndx, assy_ndx,
	  cur_obj, use_factors
          )
      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindChannelMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindMultiDataSetMinMaxValue()	-
  #----------------------------------------------------------------------
  def FindMultiDataSetMinMaxValue(
      self, mode, time_value, assy_ndx,
      cur_obj, *qds_names
      ):
    """Creates dict with dataset-type-appropriate addresses for the "first"
(right- and bottom-most) occurence of the maximum value among all the
specified datasets.
@param  mode		'min' or 'max', defaulting to the latter
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  qds_names	dataset names to search, DataSetName instances
@return			dict with possible keys: 'assembly_addr',
			'axial_value', 'state_index', 'sub_addr'
"""
    results = {}
    dm = self.GetDataModel( qds_names[ 0 ] )  if qds_names else  None
    if dm:
      model_name = qds_names[ 0 ].modelName
      ds_names = []
      for q in qds_names:
        ds_names.append( q.displayName )

      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, model_name )

      results = dm.FindMultiDataSetMinMaxValue(
          mode, state_ndx, assy_ndx, cur_obj, *ds_names
	  )
      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], model_name )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm

    return  results
  #end FindMultiDataSetMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindPinMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindPinMinMaxValue(
      self, mode, qds_name, time_value, assy_ndx,
      cur_obj = None, use_factors = False
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
@param  mode		'min' or 'max', defaulting to the latter
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  assy_ndx	0-based assembly index, or -1 for all assemblies
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  use_factors	True to apply pinFactors when determining the min/max
			address
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindPinMinMaxValue(
	  mode, qds_name.displayName, state_ndx, assy_ndx,
	  cur_obj, use_factors
          )

      if 'state_index' in results:
#	results[ 'time_value' ] = self.\
#	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindPinMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.FindTallyMinMaxValue()		-
  #----------------------------------------------------------------------
  def FindTallyMinMaxValue(
      self, mode, tally_addr, time_value,
      cur_obj = None, ds_expr = None, radius_start_ndx = 0
      ):
    """Creates dict with pin addresses for the "first" (right- and
bottom-most) occurence of the maximum value of the dataset, which is assumed
to be a 'pin' dataset.
If time_value is gt 0, only differences with the corresponding state are
returned.
@param  mode		'min' or 'max', defaulting to the latter
@param  tally_addr	TallyAddress instance from which the name, multIndex,
			and statIndex properties are used
@param  time_value	value for the current timeDataSet, or -1 for all
			times/statepoints
@param  cur_obj		optional object with attributes/properties to
			compare against for changes: assemblyAddr, axialValue,
			subAddr, stateIndex
@param  ds_expr		expression to apply to dataset min/max search,
			if None, tally_addr.multIndex and .statIndex will
			be applied in DataModel.FindTallyMinMaxValueAddr()
@param  radius_start_ndx  starting index of radius range of validity
@return			changes dict with possible keys: 'assembly_addr',
			'axial_value', 'sub_addr', 'time_value'
"""
    results = {}
    qds_name = tally_addr.name
    if qds_name:
      dm = self.GetDataModel( qds_name )
    if dm:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      results = dm.FindTallyMinMaxValue(
          mode, tally_addr, state_ndx, cur_obj, ds_expr, radius_start_ndx
	  )

      if 'state_index' in results:
	time_value = self.\
	    GetTimeIndexValue( results[ 'state_index' ], qds_name.modelName )
        skip = cur_obj is not None and \
            hasattr( cur_obj, 'timeValue' ) and \
            getattr( cur_obj, 'timeValue' ) == time_value
        if not skip:
	  results[ 'time_value' ] = time_value
    #end if dm
   
    return  results
  #end FindTallyMinMaxValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._FireEvent()			-
  #----------------------------------------------------------------------
  def _FireEvent( self, event_name, *params ):
    """Calls event_name listeners passing self and the params list.
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  params		event params
"""
    if event_name in self.listeners:
      #method_name = 'On' + event_name.capitalize()
      method_name = 'On' + event_name[ 0 ].upper() + event_name[ 1 : ]
      for listener in self.listeners[ event_name ]:
        if not listener:
	  self._logger.error( 'Listener is dead: %s', str( listener ) )
	elif hasattr( listener, method_name ):
	  getattr( listener, method_name )( self, *params )
	elif hasattr( listener, '__call__' ):
	  listener( self, *params )
      #end for listener
    #end if event_name
  #end _FireEvent


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMesh()			-
  #----------------------------------------------------------------------
  def GetAxialMesh( self, qds_name = None ):
    """Retrieves the axialMesh property for the specified model or
the cross-model global mesh.
@param  qds_name	optional DataSetName instance
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    return  self.GetAxialMesh2( qds_name )
  #end GetAxialMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMesh2()			-
  #----------------------------------------------------------------------
  def GetAxialMesh2( self, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh for the specified dataset or mesh type.
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'tally', or 'all' for the combined mesh
			for all datasets
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    result = None
    if qds_name is not None:
      dm = self.GetDataModel( qds_name )
      if dm:
	result = dm.GetAxialMesh( qds_name.displayName, mesh_type )

    if result is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      result = self.axialMeshDict.get( mesh_type )

    return  result  if result is not None else  self.axialMeshDict.get( 'all' )
  #end GetAxialMesh2


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters( self, model_name = None ):
    """Retrieves the axialMeshCenters property for the specified model or
the cross-model global mesh centers.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh centers for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( model_name )
  #end GetAxialMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCenters2()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCenters2( self, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh centers for the specified dataset and/or
mesh type.
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'fixed_detector', 'pin',
			'subpin', 'tally', or 'all' for the combined mesh
			for all datasets
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    result = None
    if qds_name is not None:
      dm = self.GetDataModel( qds_name )
      if dm:
	result = dm.GetAxialMeshCenters( qds_name.displayName, mesh_type )

    if result is None:
      if mesh_type == 'core':
        mesh_type = 'pin'
      result = self.axialMeshCentersDict.get( mesh_type )

    return  \
        result  if result is not None else \
	self.axialMeshCentersDict.get( 'all' )
  #end GetAxialMeshCenters2


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshCentersIndex()		-
  #----------------------------------------------------------------------
  def GetAxialMeshCentersIndex(
      self, mesh_value,
      qds_name = None, mesh_type = 'pin'
      ):
    """Retrieves the axial mesh for the specified dataset or mesh type.
@param  mesh_value	mesh value in cm
@param  qds_name	optional DataSetName instance
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'tally'
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    ndx = -1
    mesh = self.GetAxialMeshCenters2( qds_name, mesh_type )
    if mesh is not None and len( mesh ) > 1:
      ndx = bisect.bisect_right( mesh, mesh_value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )

    return  ndx
  #end GetAxialMeshCentersIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialMeshIndex()		-
  #----------------------------------------------------------------------
  def GetAxialMeshIndex( self, mesh_value, qds_name = None, mesh_type = 'pin' ):
    """Retrieves the axial mesh for the specified dataset or mesh type.
@param  mesh_value	mesh value in cm
@param  qds_name	optional DataSetName instance, overrides ``mesh_type``
@param  mesh_type	'core', 'detector', 'fixed_detector', 'pin',
			'subpin', 'tally'
@return			mesh for the specified dataset or the
			cross-model global mesh if qds_name is None
			or not found
"""
    ndx = -1
    mesh = self.GetAxialMesh2( qds_name, mesh_type )
    if mesh is not None and len( mesh ) > 1:
      ndx = bisect.bisect_right( mesh, mesh_value ) - 1
      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )

    return  ndx
  #end GetAxialMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetAxialValue()			-
  #----------------------------------------------------------------------
  def GetAxialValue( self, qds_name = None, **kwargs ):
    """Retrieves the axial value tuple ( axial_cm, core_ndx, detector_ndx,
fixed_detector_ndx, tally_ndx, subpin_ndx ) for the specified model.
Otherwise, the
cross-model levels are used and can be applied only with 'cm' and 'core_ndx'
arguments.  Calls CreateAxialValue() on the identified DataModel.
@param  qds_name	optional DataSetName instance
@param  kwargs		arguments
    cm				axial value in cm
    core_ndx			0-based core axial index
    detector_ndx		0-based detector axial index
    fixed_detector_ndx		0-based fixed_detector axial index
    pin_ndx			0-based core axial index, alias for 'core_ndx'
    subpin_ndx			0-based subpin axial index
    tally_ndx          		0-based tally axial index
    value			axial value in cm, alias for 'cm'
@return			AxialValue instance
			( axial_cm, core_ndx, detector_ndx, fixed_detector_ndx,
			  tally_ndx )
"""
    results = self._GetAxialValueRec( qds_name, **kwargs )
    return  AxialValue( results )

#    tup = (
#	results.get( 'cm', 0.0 ),
#	results.get( 'pin', -1 ),
#	results.get( 'detector', -1 ),
#	results.get( 'fixed_detector', -1 ),
#	results.get( 'tally', -1 ),
#	results.get( 'subpin', -1 )
#        )
#    return  tup
  #end GetAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._GetAxialValueRec()		-
  #----------------------------------------------------------------------
  def _GetAxialValueRec( self, qds_name = None, **kwargs ):
    """Creates an axial index dict with keys 'cm', 'detector', 'fixed_detector',
'pin', 'subpin', 'tally'.
@param  qds_name	optional DataSetName instance
Parameters:
  cm			axial value in cm
  core_ndx		0-based core axial index
  detector_ndx		0-based detector axial index
  fixed_detector_ndx	0-based fixed_detector axial index
  pin_ndx		alias for 'core_ndx'
  subpin_ndx		0-based subpin axial index
  tally_ndx          	0-based tally axial index
  value			alias for 'cm'
  xxx_ndx		0-based axial index for mesh type 'xxx'
@return			dictionary of axial index values
"""
    results = {}

    if qds_name:
      dm = self.GetDataModel( qds_name )
      if dm:
	results = dm.CreateAxialValueRec( **kwargs )

    elif self.core is not None:
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
	    ndx = max( 0, min( v, len( mesh ) - 1 ) )
	    results[ name ] = ndx
            results[ 'cm' ] = mesh[ ndx ]
	#end elif _ndx
      #end for n, v

#		-- Resolve predefined indexes
#		--
      for name in predef_names:
        ndx = results.get( name, -1 )
	if ndx < 0 and name in self.axialMeshDict:
	  mesh = self.axialMeshDict.get( name )
	  if len( mesh ) > 0:
	    ndx = DataUtils.FindListIndex( mesh[ : -1 ], results[ 'cm' ] )
	    #ndx = min( ndx, len( mesh ) -1 )
	results[ name ] = ndx
      #end for name

      results[ 'value' ] = results[ 'cm' ]
    #end elif self.core

    return  results
  #end _GetAxialValueRec


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetCore()				-
  #----------------------------------------------------------------------
  def GetCore( self, model_name = None ):
    """Retrieves the core property for the specified model or
the cross-model core.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			Core instance for the specified model or the
			cross-model instance if model_name is None
			or not found
"""
    #return  self.core
    result = self.core
    if model_name is not None:
      dm = self.GetDataModel( model_name )
      if dm:
        result = dm.GetCore()

    return  result
  #end GetCore


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModel()			-
  #----------------------------------------------------------------------
  def GetDataModel( self, model_param ):
    """Retrieves the DataModel by model name.  The param can be a string
model name or a DataSetName instance.
@param  model_param	a DataSetName instance or a model name string
@return			DataModel or None if not found
"""
    dm = None
    if model_param:
      model_name = \
          model_param.modelName \
	  if isinstance( model_param, DataSetName ) else \
	  str( model_param )
      dm = self.dataModels.get( model_name )

    return  dm
  #end GetDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelCount()		-
  #----------------------------------------------------------------------
  def GetDataModelCount( self ):
    return  len( self.dataModels )
  #end GetDataModelCount


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelNames()		-
  #----------------------------------------------------------------------
  def GetDataModelNames( self ):
    """
@return			list of model names
"""
    return  self.dataModelNames
  #end GetDataModelNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModelDataSetNames()		-
  #----------------------------------------------------------------------
  def GetDataModelDataSetNames( self, qds_name, ds_type = None ):
    """Calls GetDataSetNames() on the model specified by qds_name.
    Retrieves the dataset types list for the specified model.
@param  qds_name	DataSetName instance
@param  ds_type		optional type name
@return			empty list if model name found, else
			if ds_type is not None, list of dataset names
			for ds_type or empty if not found, else
			if ds_type is None, copy of dict of dataset name lists
			by ds_type
			( 'axials', 'channel', 'detector', 'fixed_detector',
			  'pin', 'scalar', etc. )
"""
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetNames( ds_type )  if dm else []
  #end GetDataModelDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataModels()			-
  #----------------------------------------------------------------------
  def GetDataModels( self ):
    """Accessor for the dataModels property.
@return			reference
"""
    return  self.dataModels
  #end GetDataModels


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetDefByQName()		-
  #----------------------------------------------------------------------
  def GetDataSetDefByQName( self, qds_name ):
    """Looks up the dataset definition dict for the type of the specified
dataset.
@param  qds_name	DataSetName instance
@return			dataset definition if found, None otherwise
"""
    ddef = None
    dm = self.GetDataModel( qds_name )
    if dm:
      ddef = dm.GetDataSetDefByDsName( qds_name.displayName )
    return  ddef
  #end GetDataSetDefByQName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, qds_name, short = False ):
    """If we have only a single model, we cull the model name for display
purpose.  Otherwise, we need the fully-qualified name.
@param  qds_name	DataSetName instance
@param  short		if true, only the first letter of the model name
			is shown
@return			qds_name.displayName if we have a single model,
			otherwise qds_name.shortName if short else
			qds_name.name
"""
    if isinstance( qds_name, DataSetName ):
      result = \
          qds_name.displayName  if len( self.dataModels ) <= 1 else \
	  qds_name.shortName  if short else \
	  qds_name.name
    else:
      result = str( qds_name )

    return  result
  #end GetDataSetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetHasSubAddr()		-
  #----------------------------------------------------------------------
  def GetDataSetHasSubAddr( self, qds_name ):
    """Looks up the dataset definition for the type of the specified
dataset to determine if it is addressible by sub_addr.
@param  qds_name	DataSetName instance
@return			True if addressible by sub_addr, False otherwise
"""
    result = False
    ddef = None

    dm = self.GetDataModel( qds_name )
    if dm:
      ddef = dm.GetDataSetDefByDsName( qds_name.displayName )

    #if ddef and 'shape' in ddef:
    if ddef:
      ddef_shape = ddef.get( 'shape' )
      result = \
          len( ddef_shape ) == 4 and  \
	  ddef_shape[ 0 ] > 1 and ddef_shape[ 1 ] > 1

    return  result
  #end GetDataSetHasSubAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetScaleType()		-
  #----------------------------------------------------------------------
  def GetDataSetScaleType( self, qds_name ):
    """Looks up the scale types for the dataset name.
    Args:
        qds_name (DataSetName): name, cannot be None
    Returns:
        str: scale type name, defaulting to 'linear'
"""
    result = 'linear'
    if qds_name:
      dm = self.GetDataModel( qds_name )
      if dm:
        result = dm.GetDataSetScaleType( qds_name.displayName )

    return  result
  #end GetDataSetScaleType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetScaleTypeAll()		-
  #----------------------------------------------------------------------
  def GetDataSetScaleTypeAll( self, log_mode = 'all', *qds_names ):
    """Looks up the scale types for the dataset name.
    Args:
	log_mode (str): 'all' or 'any' for log scale if all or any of
	    ``qds_names`` have a log type
        qds_names (list(DataSetName)): names to search
    Returns:
        str: scale type name, defaulting to 'linear'
"""
    result = 'linear'
    if qds_names:
      scale_types = []
      for qds_name in qds_names:
        scale_types.append( self.GetDataSetScaleType( qds_name ) )

      log_count = len( [ x for x in scale_types if x == 'log' ] )
      if log_mode == 'all':
        if log_count == len( scale_types ): result = 'log'
      else:
        if log_count > 0: result = 'log'
    #end if qds_names

    return  result
  #end GetDataSetScaleTypeAll


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetThreshold()		-
  #----------------------------------------------------------------------
  def GetDataSetThreshold( self, qds_name = None ):
    """Returns the range expression for the specified qds_name, or a list
of range expressions for all datasets.
@param  qds_name	DataSetName instance or None for all range expressions
@return			if qds_name specified, the RangeExpression instance
			if found otherwise None
			if qds_name is None list of
			( qds_name, RangeExpression ) pairs
"""
    result = None

    #if isinstance( qds_name, DataSetName ):
    if qds_name:
      dm = self.GetDataModel( qds_name )
      if dm:
        result = dm.GetDataSetThreshold( qds_name.displayName )
    else:
      result = []
      for model_name in sorted( self.dataModelNames ):
        dm = self.dataModels.get( model_name )
	ranges = dm.GetDataSetThreshold()
	for ( ds_name, expr ) in sorted( ranges.iteritems() ):
	  result.append( ( DataSetName( model_name, ds_name ), expr ) )
      #end for model_name
    #end if-else qds_name

    return  result
  #end GetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetQNames()			-
  #----------------------------------------------------------------------
  def GetDataSetQNames( self, model_param, ds_type = None ):
    """Returns the qualified names (DataSetName instances) for ds_type,
for a single DataModel if model_param is specified or across all models.
If ds_type is None or empty, all types are matched.
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for all models
@param  ds_type		optional type name, where None matches all types
@return			empty list if model_param specified and not found,
			list of qualified names (DataSetName instances)
			otherwise
"""
    result = set()
    dm_list = []

    if model_param:
      dm = self.GetDataModel( model_param )
      if dm:
        dm_list.append( dm )
    else:
      dm_list = self.dataModels.values()

    for dm in dm_list:
      if ds_type:
        names = dm.GetDataSetNames( ds_type )
      else:
        names_dict = dm.GetDataSetNames()
	names = []
	for cur_names in names_dict.values():
	  names += cur_names

      for n in names:
        result.add( DataSetName( dm.GetName(), n ) )
    #end for dm

    return  sorted( list( result ) )
  #end GetDataSetQNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetType()			-
  #----------------------------------------------------------------------
  def GetDataSetType( self, qds_name ):
    """Retrieves the type for the name dataset.
@param  qds_name	DataSetName instance
@return			type or None
"""
    dm = self.GetDataModel( qds_name )
    return  dm.GetDataSetType( qds_name.displayName )  if dm else  None
  #end GetDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDataSetTypes()			-
  #----------------------------------------------------------------------
  def GetDataSetTypes( self ):
    """Creates a set of all dataset categories/types across all DataModel
instances.
@return			set of type names
"""
    ds_types = set()
    for dm in self.dataModels.values():
      ds_types |= set( dm.GetDataSetDefs().keys() )

    return  ds_types
  #end GetDataSetTypes


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMesh()			-
  #----------------------------------------------------------------------
  def GetDetectorMesh( self, model_name = None ):
    """Retrieves the detectorMesh property for the specified model or
the cross-model global mesh.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh if model_name is None or is
			not found
"""
    return  self.GetAxialMesh2( model_name, 'detector' )
#    #return  self.detectorMesh
#
#    result = None
#    if model_name is not None:
#      dm = self.GetDataModel( model_name )
#      if dm:
#        result = dm.core.detectorMesh
#
#    if result is None:
#      result = self.axialMeshDict.get( 'detector' )
#
#    return  result
  #end GetDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetDetectorMeshIndex()		-
  #----------------------------------------------------------------------
  def GetDetectorMeshIndex( self, value, model_name = None ):
    """Determines the 0-based index of the value in the mesh list such that
mesh[ ndx ] <= value < mesh[ ndx + 1 ].  If model_name is specified,
only the mesh for the specified model is used.  Otherwise, the global,
cross-model mesh is used.
@param  value		mesh value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshIndex( value, model_name, 'detector' )
#    ndx = -1
#    if isinstance( model_name, DataSetName ):
#      model_name = model_name.modelName
#    mesh = self.GetDetectorMesh( model_name )
#    if mesh is not None:
#      ndx = bisect.bisect_right( mesh, value ) - 1
#      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
#    #end if
#
#    return  ndx
  #end GetDetectorMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFactors()			-
  #----------------------------------------------------------------------
  def GetFactors( self, qds_name ):
    """Determines the factors from the dataset shape.
@param  qds_name	name of dataset, DataSetName instance
@return			factors np.ndarray or None
"""
    dm = self.GetDataModel( qds_name )
    return  dm.GetFactors( qds_name.displayName )  if dm is not None else  None
  #end GetFactors


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFirstDataModel()		-
  #----------------------------------------------------------------------
  def GetFirstDataModel( self ):
    """Retrieves the first DataModel.
@return			DataModel or None if not found
"""
    return \
        self.dataModels.get( self.dataModelNames[ 0 ] ) \
	if len( self.dataModelNames ) > 0 else \
	None
#    dm = None
#    if len( self.dataModelNames ) > 0:
#      dm = self.dataModels.get( self.dataModelNames[ 0 ] )
#
#    return  dm
  #end GetFirstDataModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFirstDataSet()			-
  #----------------------------------------------------------------------
  def GetFirstDataSet( self, ds_type ):
    """Retrieves the first matching dataset.
@param  ds_type		datset category/type
@return			DataSetName instance or None if not found
"""
    qds_name = None
    if ds_type:
      for model_name in self.dataModelNames:
        dm = self.dataModels.get( model_name )
	ds_name = dm.GetFirstDataSet( ds_type )
	if ds_name:
	  qds_name = DataSetName( model_name, ds_name )
	  break

    return  qds_name
  #end GetFirstDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMesh()		-
  #----------------------------------------------------------------------
  def GetFixedDetectorMesh( self, qds_name = None ):
    """Retrieves the fixedDetectorMesh property for the specified model
or the cross-model global mesh.
@param  qds_name	DataSetName instance
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMesh2( qds_name, 'fixed_detector' )
  #end GetFixedDetectorMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCenters()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCenters( self, qds_name = None ):
    """Retrieves the fixedDetectorMeshCenters property for the specified model
or the cross-model global mesh centers.
@param  qds_name	DataSetName instance
@return			mesh centers for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( qds_name, 'fixed_detector' )
  #end GetFixedDetectorMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetFixedDetectorMeshCentersIndex()	-
  #----------------------------------------------------------------------
  def GetFixedDetectorMeshCentersIndex( self, value, model_name = None ):
    """Determines the 0-based index of the value in the mesh list such that
mesh[ ndx ] <= value < mesh[ ndx + 1 ].  If model_name is specified,
only the mesh for the specified model is used.  Otherwise, the global,
cross-model mesh is used.
@param  value		global time value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshCentersIndex( value, model_name, 'fixed_detector' )
#    ndx = -1
#    if isinstance( model_name, DataSetName ):
#      model_name = model_name.modelName
#    mesh = self.GetFixedDetectorMeshCenters( model_name )
#    if mesh is not None:
#      ndx = bisect.bisect_right( mesh, value ) - 1
#      ndx = max( 0, min( ndx, len( mesh ) - 1 ) )
#    #end if
#
#    return  ndx
  #end GetFixedDetectorMeshCentersIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetH5DataSet()			-
  #----------------------------------------------------------------------
  def GetH5DataSet( self, qds_name, time_value ):
    """Calls GetStateDataSet() on the corresponding DataModel.
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for current timeDataSet
@return			h5py.Dataset object if found or None
"""
    dm = dset = None
    if qds_name is not None and time_value >= 0.0:
      state_ndx = self.GetTimeValueIndex( time_value, qds_name.modelName )
      if state_ndx >= 0:
        dm = self.GetDataModel( qds_name )

    if dm is not None:
      dset = dm.GetStateDataSet( state_ndx, qds_name.displayName )
    return  dset
  #end GetH5DataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetMaxAxialValue()			-
  #----------------------------------------------------------------------
  def GetMaxAxialValue( self ):
    """Accessor for the maxAxialValue property.
@return			maximum axial value in cm
"""
    return  self.maxAxialValue
  #end GetMaxAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetNodeAddr()			-
  #----------------------------------------------------------------------
  def GetNodeAddr( self, sub_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  sub_addr	0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
@return			node addr in range [0,3], or -1 if sub_addr is invalid
"""
    node_addr = -1
    core = self.GetCore()
    if core is not None:
      cx = core.npinx >> 1
      cy = core.npiny >> 1 
      if mode == 'channel':
        cx += 1
	cy += 1

      node_addr = 2 if max( 0, sub_addr[ 1 ] ) >= cy else 0
      if max( 0, sub_addr[ 0 ] ) >= cx:
        node_addr += 1

    return  node_addr
  #end GetNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetNodeAddrs()			-
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
  #	METHOD:		DataModelMgr.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange( self, qds_name, time_value = -1.0, ds_expr = None ):
    """Gets the range for the specified dataset, calculating
if necessary.  Note all requests for range should flow through this method,
although Python doesn't allow us to enforce this.  We'll need to adopt
the properties construct for this class soon.
@param  qds_name	name of dataset, DataSetName instance
@param  time_value	value for the current timeDataSet, or -1
			for global range
@param  ds_expr		optional reference expression to apply to the dataset
@return			( min, max ), possibly the range of floating point
			values or None if qds_name not found
"""
    result = None
    dm = self.GetDataModel( qds_name )
    if dm is not None:
      state_ndx = \
          -1  if time_value < 0.0 else \
	  self.GetTimeValueIndex( time_value, qds_name.modelName )
      result = dm.GetRange( qds_name.displayName, state_ndx, ds_expr )
    #end if dm
   
    return  result
  #end GetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetRangeAll()			-
  #----------------------------------------------------------------------
  def GetRangeAll( self, time_value = -1.0, *qds_names ):
    """Calculates the range across all the specified datasets.
Note all requests for multiple ranges should flow through this method.
@param  time_value	value for the current timeDataSet, or -1
			for global range
@param  qds_names	datasets, DataSetName instances
@return			[ min, max ], possibly the range of floating point
			values or None if none of qds_names exist
"""
    result = None

    if qds_names:
      for qds_name in qds_names:
	cur_range = self.GetRange( qds_name, time_value )
	if cur_range is None:
	  pass
	elif result is None:
	  result = list( cur_range )
        else:
	  result[ 0 ] = min( result[ 0 ], cur_range[ 0 ] )
	  result[ 1 ] = max( result[ 1 ], cur_range[ 1 ] )
      #end for qds_name
    #end if qds_names
   
#    if result is None:
#      result = DataModel.DEFAULT_range
    return  result
  #end GetRangeAll


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetSubAddrFromNode()		-
  #----------------------------------------------------------------------
  def GetSubAddrFromNode( self, node_addr, mode = 'pin' ):
    """Get the node addr corresponding to sub_addr.
@param  node_addr	0, 1, 2, or 3
@param  mode		'channel' or 'pin', defaulting to the latter
@return			0-based sub_addr ( col, row )
"""
    core = self.GetCore()
    if core is None or node_addr < 0 or node_addr >= 4:
      sub_addr = ( -1, -1 )
    else:
      npinx = core.npinx
      npiny = core.npiny
      if mode == 'channel':
        npinx += 1
        npiny += 1
      col = 0 if node_addr in ( 0, 2 ) else npinx - 1
      row = 0 if node_addr in ( 0, 1 ) else npiny - 1

      sub_addr = ( col, row )

    return  sub_addr
  #end GetSubAddrFromNode


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTallyMesh()			-
  #----------------------------------------------------------------------
  def GetTallyMesh( self, model_name = None ):
    """Calls GetAxialMesh2( model_name, 'tally' ).
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMesh2( model_name, 'tally' )
  #end GetTallyMesh


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTallyMeshCenters()		-
  #----------------------------------------------------------------------
  def GetTallyMeshCenters( self, model_name = None ):
    """Calls GetAxialMeshCenters2( model_name, 'tally' ).
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			mesh for the specified model or the
			cross-model global mesh values if model_name is None
			or not found
"""
    return  self.GetAxialMeshCenters2( model_name, 'tally' )
  #end GetTallyMeshCenters


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTallyMeshIndex()		-
  #----------------------------------------------------------------------
  def GetTallyMeshIndex( self, value, model_name = None ):
    """ Calls GetAxialMeshCentersIndex( value_model_name, 'tally' ).
@param  value		global time value
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    return  self.GetAxialMeshCentersIndex( value, model_name, 'tally' )
  #end GetTallyMeshIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeDataSet()			-
  #----------------------------------------------------------------------
  def GetTimeDataSet( self ):
    """Accessor for the timeDataSet property.
@return			dataset used for time
"""
    return  self.timeDataSet
  #end GetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeIndexValue()		-
  #----------------------------------------------------------------------
  def GetTimeIndexValue( self, ndx, model_name = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If model_name is specified,
only the list of values for the specified model are used.  Otherwise,
the global, cross-model values are used.
@param  model_name	optional name for the model of interest,
			can be a DataSetName
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    value = -1

    values = None
    if ndx >= 0:
      if isinstance( model_name, DataSetName ):
        model_name = model_name.modelName
      values = self.GetTimeValues( model_name )
      if values:
        ndx = min( ndx, len( values ) -1 )
        value = values[ ndx ]

    return  value
  #end GetTimeIndexValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValueIndex()		-
  #----------------------------------------------------------------------
  def GetTimeValueIndex( self, value, model_param = None ):
    """Determines the 0-based index of the value in the values list such that
values[ ndx ] <= value < values[ ndx + 1 ].  If model_param is specified,
only the list of values for the specified model are used.  Otherwise,
the global, cross-model values are used.
@param  value		global time value
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for global index
@return			0-based index such that
			values[ ndx ] <= value < values[ ndx + 1 ]
"""
    ndx = -1
    if isinstance( model_param, DataSetName ):
      model_param = model_param.modelName
    values = self.GetTimeValues( model_param )
    if values:
      ndx = bisect.bisect_right( values, value ) - 1
      ndx = max( 0, min( ndx, len( values ) - 1 ) )
    #end if

    return  ndx
  #end GetTimeValueIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.GetTimeValues()			-
  #----------------------------------------------------------------------
  def GetTimeValues( self, model_param = None ):
    """Retrieves the time dataset values for the specified model if 'id'
is not None, otherwise retrieves the union of values across all models.
@param  model_param	optional name for the model of interest,
			can be a DataSetName, None for global time values
@return			list of time dataset values for the specified model
			or across all models
"""
    if isinstance( model_param, DataSetName ):
      model_param = model_param.modelName

    return \
	self.timeValuesById[ model_param ] \
	if model_param and model_param in self.timeValuesById else \
	self.timeValues
  #end GetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasData()				-
  #----------------------------------------------------------------------
  def HasData( self ):
    return  len( self.dataModels ) > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.HasDataSetType()			-
  #----------------------------------------------------------------------
  def HasDataSetType( self, ds_type ):
    """Convenience method to call HasDataSetType() on DataModel instances until 
True is returned.
@param  ds_type		one of type names, e.g., 'axials', 'channel', 'derived',
			'detector', 'fixed_detector', 'pin', 'scalar'
@return			True if there are datasets, False otherwise
"""
    found = False
    for dm in self.dataModels.values():
      found = dm.HasDataSetType( ds_type )
      if found:
        break

    return  found
  #end HasDataSetType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.Is3DReady()			-
  #----------------------------------------------------------------------
  def Is3DReady( self ):
    """Checks having length gt 1 in all three dimensions.
"""
    core = self.GetCore()
    valid = \
        core is not None and \
	core.nax > 1 and \
	(core.nassx * core.npinx) > 1 and \
	(core.nassy * core.npiny) > 1

    return  valid
  #end Is3DReady


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsBadValue()			-
  #----------------------------------------------------------------------
  def IsBadValue( self, value ):
    """Checks for nan and inf.
@param  value		value to check
@return			True if nan or inf, False otherwise
"""
    #np.logical_or( np.isnan( value ), np.isinf( value ) )
    return  value is None or math.isnan( value ) or math.isinf( value )
  #end IsBadValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsChannelType()			-
  #----------------------------------------------------------------------
  def IsChannelType( self, qds_name ):
    """Determines if the qds_name represents a channel dataset.
@param  qds_name	DataSetName instance
@return			True if channel, False otherwise
"""
    result = False
    if self.core:
      dset = self.GetH5DataSet( qds_name, 0.0 )
      if dset:
	result = \
	    dset.shape[ 0 ] == self.core.npiny + 1 and \
	    dset.shape[ 1 ] == self.core.npinx + 1

    return  result
  #end IsChannelType


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsDerivedDataSet()			-
  #----------------------------------------------------------------------
  def IsDerivedDataSet( self, qds_name ):
    """
@param  qds_name	name of dataset, DataSetName instance
@return			True if derived, false otherwise
"""
    dm = self.GetDataModel( qds_name )
    return  dm.IsDerivedDataSet( qds_name.displayName )  if dm else  False
  #end IsDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsDetectorOperable()		-
  #----------------------------------------------------------------------
  def IsDetectorOperable( self, det_ndx, time_value, model_name = None ):
    """Determines if there is/are 'detector_operable' datasets that mark
the det_ndx as inoperable.  If model_name is None, then all models must
report inoperability for the result to be False.
@param  det_ndx		0-based detector index
@param  time_value	time value
@param  model_name	optional model name, can be a DataSetName instance
@return			True if det_ndx for model_name or any model is
			operable, False if inoperable for model_name or
			all models
"""
    operable = False

    if model_name:
      model_names = [ model_name ]
    else:
      model_names = self.dataModelNames

    for name in model_names:
      det_operable_dset = None
      dm = self.GetDataModel( name )
      if dm:
        state_ndx = self.GetTimeValueIndex( time_value, name )
	det_operable_dset = dm.GetStateDataSet( state_ndx, 'detector_operable' )

      operable |= \
          (det_operable_dset is None or det_operable_dset[ det_ndx ] == 0)
      if operable:
        break
    #end for name

    return  operable
  #end IsDetectorOperable


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.IsNodalType()			-
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
  #	METHOD:		DataModelMgr.IsValid()				-
  #----------------------------------------------------------------------
  def IsValid( self, qds_name, **kwargs ):
    """Checks values for validity w/in ranges available for the specified
dataset.
@param  qds_name	name of dataset, DataSetName instance
@param  kwargs		named values to check:
		'assembly_addr'
		'assembly_index'
		'axial_level'
		'dataset_name' (requires 'time_value')
		'node_addr'
		'sub_addr'
		'sub_addr_mode'
		  (either 'channel', or 'pin', defaulting to 'pin')
		'detector_index'
		'time_value'
"""
    valid = False
    dm = self.GetDataModel( qds_name )
    if dm:
      if 'dataset_name' in kwargs:
        state_index = self.GetTimeValueIndex( kwargs.get( 'time_value', 0.0 ) )
	if state_index >= 0:
	  kwargs[ 'state_index' ] = state_index
      valid = dm.IsValid( **kwargs )

    return  valid
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.LoadDataSetThresholds()		-
  #----------------------------------------------------------------------
  def LoadDataSetThresholds( self, expr_dict ):
    """Deserializes the names and threshold expressions.
@param  expr_dict	dict of expressions by DataSetName.name
"""
    for ( name_str, expr_str ) in expr_dict.iteritems():
      try:
        qds_name = DataSetName( name_str )
        dm = self.GetDataModel( qds_name )
        if dm:
	  dm.SetDataSetThreshold( qds_name.displayName, expr_str )
      except Exception, ex:
        self.logger.exception( 'qds_name=%s, expr=%s', qds_name.name, expr_str )
    #end for ( name_str, expr_str )
  #end LoadDataSetThresholds


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeAssemblyAddr()		-
  #----------------------------------------------------------------------
  def NormalizeAssemblyAddr( self, assy_ndx ):
    core = self.GetCore()
    if core is None:
      result = ( -1, -1, -1 )
    else:
      result = \
        (
        max( 0, min( assy_ndx[ 0 ], core.nass - 1 ) ),
        max( 0, min( assy_ndx[ 1 ], core.nassx - 1 ) ),
        max( 0, min( assy_ndx[ 2 ], core.nassy - 1 ) )
        )
    return  result
  #end NormalizeAssemblyAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeAxialValue()		-
  #----------------------------------------------------------------------
  def NormalizeAxialValue( self, model_param, axial_value ):
    """Normalizes against meshes specified by model_param or the global
cross-model meshes if model_param is None
@param  model_param	None for cross-model meshes, either a DataModel
			instance or a model name/ID string for
			model-specific meshes
@param  axial_value	( cm, core_ndx, det_ndx, fdet_ndx, tally_ndx, subpin_ndx )
@deprecated by datamodel.AxialValue
"""
    axial_rec = { 'cm': axial_value[ 0 ] }
    i = 1
    for name in ( 'pin', 'detector', 'fixed_detector', 'tally', 'subpin' ):
      if len( axial_value ) > i:
        axial_rec[ name ] = axial_value[ i ]
      i += 1

    result_rec = self.NormalizeAxialValueRec( model_param, axial_rec )
    result = (
	result_rec.get( 'cm', 0.0 ),
	result_rec.get( 'pin', -1 ),
	result_rec.get( 'detector', -1 ),
	result_rec.get( 'fixed_detector', -1 ),
	result_rec.get( 'tally', -1 ),
	result_rec.get( 'subgin', -1 ),
        )
    return  result
  #end NormalizeAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeAxialValueRec()		-
  #----------------------------------------------------------------------
  def NormalizeAxialValueRec( self, qds_name, axial_value ):
    """Normalizes against meshes specified by model_param or the global
cross-model meshes if model_param is None
@param  qds_name	optional DataModel instance
@param  axial_value	dict of axial value and indexes as created by
			_GetAxialValueRec()
@deprecated by datamodel.AxialValue
"""
    result = {}

    if axial_value:
      dm = None
      if qds_name:
        dm = self.GetDataModel( qds_name )

      for mesh_type in ( 'pin', 'fixed_detector', 'tally', 'subpin' ):
        if mesh_type in axial_value:
	  if dm:
	    centers = dm.GetAxialMeshCenters( qds_name.displayName, mesh_type )
	  else:
	    centers = self.GetAxialMeshCenters2( None, mesh_type )

	  ndx = -1
	  if centers is not None and len( centers ) > 1:
	    ndx = min( axial_value.get( mesh_type, 0 ), len( centers ) - 1 )
	    ndx = max( 0, ndx )
	  result[ mesh_type ] = ndx
        #end if mesh_type
      #end for mesh_type

      for mesh_type in ( 'detector', ):
        if mesh_type in axial_value:
	  if dm:
	    centers = dm.GetAxialMesh( qds_name.displayName, mesh_type )
	  else:
	    centers = self.GetAxialMesh2( None, mesh_type )

	  ndx = -1
	  if centers is not None and len( centers ) > 1:
	    ndx = min( axial_value.get( mesh_type, 0 ), len( centers ) - 1 )
	    ndx = max( 0, ndx )
	  result[ mesh_type ] = ndx
        #end if mesh_type
      #end for mesh_type
    #end if axial_value

    return  result
  #end NormalizeAxialValueRec


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeLogRange()		-
  #----------------------------------------------------------------------
  def NormalizeLogRange( self, data_range ):
    """Forces the ranges to be positive.
    Args:
        data_range (list or tuple): range_min, range_max, data_min, data_max
    Returns:
        tuple: range_min, range_max, data_min, data_max
"""
    new_range = list( data_range )
    for i in xrange( 0, 3, 2 ):
      if len( new_range ) >= i + 1 and new_range[ i ] <= 0.0:
	if new_range[ i + 1 ] <= 0.0:
	  new_range[ i ] = 1.0
	  new_range[ i + 1 ] = 10.0
	else:
	  new_range[ i ] = new_range[ i + 1 ] / 100.0
#	  new_range[ i ] = \
#	      new_range[ i + 1 ] / 10.0  if new_range[ i + 1 ] < 1.0 else \
#	      1.0
      #end if len( new_range ) >= i + 1 and new_range[ i ] <= 0.0
    #end for i in xrange( 0, 3, 2 )

    return  tuple( new_range )
  #end NormalizeLogRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeNodeAddr()		-
  #----------------------------------------------------------------------
  def NormalizeNodeAddr( self, ndx ):
    """Here for completeness.
@param  ndx		0-based index
"""
    return  DataUtils.NormalizeNodeAddr( ndx )
  #end NormalizeNodeAddr


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeNodeAddrs()		-
  #----------------------------------------------------------------------
  def NormalizeNodeAddrs( self, addr_list ):
    """Normalizes each index in the list.
@param  addr_list	list of 0-based indexes
"""
    return  DataUtils.NormalizeNodeAddrs( addr_list )
  #end NormalizeNodeAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.NormalizeSubAddr()			-
  #----------------------------------------------------------------------
  def NormalizeSubAddr( self, addr, mode = 'pin' ):
    """Normalizes the address, accounting for channel shape being one greater
in each dimension.
@param  addr		0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    core = self.GetCore()
    if core is None:
      result = ( -1, -1 )
    else:
      maxx = core.npinx - 1
      maxy = core.npiny - 1
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
  #	METHOD:		DataModelMgr.NormalizeSubAddrs()		-
  #----------------------------------------------------------------------
  def NormalizeSubAddrs( self, addr_list, mode = 'pin' ):
    """Normalizes each address in the list, accounting for channel shape
being one greater in each dimension.
@param  addr_list	list of 0-based ( col, row )
@param  mode		'channel' or 'pin', defaulting to the latter
"""
    core = self.GetCore()
    if core is None:
      maxx = maxy = -1
    else:
      maxx = core.npinx - 1
      maxy = core.npiny - 1
      if mode == 'channel':
        maxx += 1
        maxy += 1

    result = []
    for addr in addr_list:
      result.append( (
          max( 0, min( addr[ 0 ], maxx ) ),
          max( 0, min( addr[ 1 ], maxy ) )
	  ) )

    return  list( set( result ) )
  #end NormalizeSubAddrs


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._OnNewDataSet()			-
  #----------------------------------------------------------------------
  def _OnNewDataSet( self, model, ds_name ):
    """Callback for model 'newDataSet' events.
"""
    #self.dataSetNamesVersion += 1
    self._FireEvent( 'dataSetAdded', model, ds_name )
  #end _OnNewDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.OpenModel()			-
  #----------------------------------------------------------------------
  def OpenModel( self, h5f_param ):
    """Opens the HDF5 file or filename.
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
@return			new DataModel object
@throws			Exception with error or incompatibility message
"""
#		-- Assert on file read
#		--
    dm = None
    try:
      #id = str( uuid.uuid4() )
      #dm = DataModel( h5f_param, id )
      dm = DataModel( h5f_param )
    except Exception, ex:
      msg = 'Error reading "%s": %s' % ( h5f_param, ex.message )
      output = cStringIO.StringIO()
      try:
        print >> output, msg
        traceback.print_exc( 10, output )
        self.logger.error( output.getvalue() )
      finally:
        output.close()
      raise  IOError( msg )

#		-- Assert on compatibility
#		--
    self.CheckDataModelIsCompatible( dm )

#		-- Process
#		--
    try:
      #xxxxx check for duplicate path, dm.GetH5File().filename
      model_name = self._ResolveDataModelName( dm )
      dm.AddListener( 'newDataSet', self._OnNewDataSet )
      self.dataModelNames.append( model_name )
      self.dataModels[ model_name ] = dm

      if len( self.dataModelNames ) == 1:
        #self.core = dm.GetCore()
	self.core = dm.GetCore().Clone()

      self._UpdateMeshValues()
      self._UpdateTimeValues()
      #self.dataSetNamesVersion += 1
      self._FireEvent( 'modelAdded', dm.GetName() )

      return  dm

    except Exception, ex:
      msg = 'Error processing "%s": %s' % ( h5f_param, ex.message )
      self.logger.error( msg )
      raise  IOError( msg )
  #end OpenModel


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ReadDataSetAxialValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetAxialValues( self,
      qds_name,
      assembly_index = 0,
      node_addrs = None,
      sub_addrs = None,
      detector_index = 0,
      tally_addr = None,
      time_value = 0.0
      ):
    """Reads axial values for a dataset for a specified time value.  Note the
returned values are over the appropriate mesh (axial mesh centers, detector
mesh, fixed detector mesh centers) for the DataModel.
Calls ReadDataSetAxialValues() on the matching DataModel if found.
    Args:
        qds_name (data.datamodel.DataSetName): dataset name, cannot be none
	assembly_index (int): optional 0-based assembly index
	detector_index (int): optional 0-based detector index
	node_addrs (list(int)): optional list of node indexes
	sub_addrs (list(pin_col,pin_row)): optional list of 0-based pin
	   col and row indexes
	tally_addr (TallyAddress): optional tally address
	time_value (float): timeDataSet value
    Returns:
        tuple( np.ndarray, dict or np.ndarray ): None if ds_name cannot be found
	    or processed, otherwise mesh_values and results, where the latter
	    is a dict by sub_addr (or node col,row) of np.ndarray for datasets
	    that vary by sub_addr, np.ndarray for other datasets.
"""
    result = None
    dm = self.GetDataModel( qds_name )
    if dm:
      state_index = self.GetTimeValueIndex( time_value, qds_name )
      result_pair = dm.ReadDataSetAxialValues(
          qds_name.displayName,
	  assembly_index = assembly_index,
	  detector_index = detector_index,
	  node_addrs = node_addrs,
	  state_index = state_index,
	  sub_addrs = sub_addrs,
	  tally_addr = tally_addr
	  )
      if result_pair is not None:
        result = dict( data = result_pair[ 1 ], mesh = result_pair[ 0 ] )
    #end if dm

    return  result
  #end ReadDataSetAxialValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ReadDataSetTimeValues()		-
  #----------------------------------------------------------------------
  def ReadDataSetTimeValues( self, *ds_specs_in ):
    """Reads values for datasets across time, axial values for a dataset for a specified time value.  Note the

    Reads values for a dataset across all state points, one state point
at a time for better performance.
@param  ds_specs_in	list of dataset specifications with the following keys:
	  assembly_index	0-based assembly index
	  axial_cm		axial value in cm
	  detector_index	0-based detector index for detector datasets
	  qds_name		required DataSetName instance
	  node_addrs		list of node addrs
	  sub_addrs		list of sub_addr pairs
	  tally_addr		tally address
@return			dict keyed by found qds_name of:
			  dict with keys 'data' and 'times', where 'data' value
			  is
			    dict keyed by sub_addr of np.ndarray for pin-based
			    datasets,
			    np.ndarray for datasets that are not pin-based
			  'times' value is np.ndarray
"""
    results = {}

#		-- Collate specs by model name
#		--
    specs_by_model = {}
    for spec in ds_specs_in:
      if spec is not None and 'qds_name' in spec:
	qds_name = spec[ 'qds_name' ]
	model_name = qds_name.modelName
	if model_name in self.dataModels:
          spec_list = specs_by_model.get( model_name )
	  if spec_list is None:
	    spec_list = []
	    specs_by_model[ model_name ] = spec_list
	  spec[ 'ds_name' ] = qds_name.displayName
          spec_list.append( spec )
	#end if model_name
      #end if value spec
    #end for spec

    for model_name, spec_list in specs_by_model.iteritems():
      time_values = np.array( self.timeValuesById.get( model_name ) )
      dm = self.dataModels.get( model_name )
      if dm is not None and time_values is not None:
        model_results = dm.ReadDataSetTimeValues( *spec_list )
	for ds_name, item in model_results.iteritems():
	  qds_name = DataSetName( model_name, ds_name )
	  # this is either a dict or a np.ndarray
	  item = model_results[ ds_name ]
	  results[ qds_name ] = dict( data = item, times = time_values )
	#end for ds_name
    #end for model_name, spec_list

    return  results
  #end ReadDataSetTimeValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.RemoveListener()			-
  #----------------------------------------------------------------------
  def RemoveListener( self, event_name, listener ):
    """
@param  event_name	'dataSetAdded', 'modelAdded', or 'modelRemoved'
@param  listener	listener with OnXxx() method or callable
"""
    if event_name in self.listeners:
      if listener in self.listeners[ event_name ]:
	self.listeners[ event_name ].remove( listener )
    #end if event_name
  #end RemoveListener


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.ResolveAvailableTimeDataSets()	-
  #----------------------------------------------------------------------
  def ResolveAvailableTimeDataSets( self ):
    """Determines which time datasets are available across all models.
The fallback is 'state', meaning state point index.
@return			list of ds names
"""
    time_ds_names = set([ 'state' ])
    for name in TIME_DS_NAMES:
      found = True
      for dm in self.dataModels.values():
        st = dm.GetState()
	if not (st and st.HasDataSet( name )):
	  found = False
	  break
      #end for dm

      if found:
        time_ds_names.add( name )
    #end for name

    return  list( time_ds_names )
  #end ResolveAvailableTimeDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._ResolveDataModelName()		-
  #----------------------------------------------------------------------
  def _ResolveDataModelName( self, dm ):
    """Checks for a name clash, appending to the name as necessary to make it
unique.  Calls dm.SetName() if necessary.
@param  dm		DataModel to check
@return			resulting name for dm
"""
    name = None
    if dm:
      cur_name = dm.GetName()
      ndx = 2
      while cur_name in self.dataModelNames:
        cur_name = '%s_%d' % ( dm.GetName(), ndx )
	ndx += 1
      #end while

      name = cur_name
      if name != dm.GetName():
        dm.SetName( name )

    return  name
  #end _ResolveDataModelName


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.RevertIfDerivedDataSet()		-
  #----------------------------------------------------------------------
  def RevertIfDerivedDataSet( self, qds_name ):
    """If qds_name is a derived dataset, return the first dataset of the
base type.  Calls GetFirstDataSet().
Note: We are now hard-coding this to look for ':chan_xxx' for
a derived type, in which case we pass 'channel' to GetFirstDataSet().  For all
other derived types we pass 'pin'.
@param  qds_name	name of dataset, DataSetName instance
@return			ds_name if it is not derived, the first dataset from
			the base category/type if it is derived
"""
    result = None
    dm = self.GetDataModel( qds_name )
    if dm:
      ds_name = dm.RevertIfDerivedDataSet( qds_name.displayName )
      if ds_name:
        result = DataSetName( qds_name.modelName, ds_name )

    return  result
  #end RevertIfDerivedDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SaveDataSetThresholds()		-
  #----------------------------------------------------------------------
  def SaveDataSetThresholds( self ):
    """Serializes the names and threshold expressions.
@return			dict of expressions by DataSetName
"""
    result = {}
    for ( model_name, dm ) in self.dataModels.iteritems():
      expr_dict = dm.GetDataSetThreshold()
      for ( ds_name, expr ) in expr_dict.iteritems():
        result[ DataSetName( model_name, ds_name ).name ] = expr.displayExpr
      #end for ( ds_name, expr )
    #end for ( model_name, dm )

    return  result
  #end SaveDataSetThresholds


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SetDataSetThreshold()		-
  #----------------------------------------------------------------------
  def SetDataSetThreshold( self, qds_name, range_expr = None ):
    """Adds or replaces the ignore range expressions for the specified
dataset.
@param  qds_name	DataSetName instance
@param  range_expr	either an expression string, a RangeExpression
			instance, or None to remove the threshold
@param  op_value_pairs	sequence of op-value pairs, where op is one of
			'=', '<', '<=', '>', '>='
"""
    dm = self.GetDataModel( qds_name )
    if dm:
      dm.SetDataSetThreshold( qds_name.displayName, range_expr )
  #end SetDataSetThreshold


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.SetTimeDataSet()			-
  #----------------------------------------------------------------------
  def SetTimeDataSet( self, ds_name ):
    """Accessor for the timeDataSet property.
@param  ds_name		cross-model dataset used for time
"""
    self.timeDataSet = ds_name
    self._UpdateTimeValues()
  #end SetTimeDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateMeshValues()		-
  #----------------------------------------------------------------------
  def _UpdateMeshValues( self ):
    """Updates the allMesh, allMeshCenters, axialMesh, axialMeshCenters,
detectorMap, detectorMesh, fixedDetectorMesh, fixedDetectorMeshCenters,
tallyMesh, tallyMeshCenters, and maxAxialValue properties.
@return			maxAxialValue property value
"""
    #--------------------------------------------------------------------
    #	INNER METHOD:	is_offset_mesh()				-
    #--------------------------------------------------------------------
    def is_offset_mesh( global_set, cur_mesh ):
      result = False
      global_mesh = np.array( sorted( global_set ), dtype = np.float64 )
      if global_mesh.shape == cur_mesh.shape:
        global_diffs = global_mesh[ 1 : ] - global_mesh[ 0 : -1 ]
        cur_diffs = cur_mesh[ 1 : ] - cur_mesh[ 0 : -1 ]
	result = np.array_equal( global_diffs, cur_diffs )

      return  result
    #end is_offset_mesh

    #--------------------------------------------------------------------
    #	INNER METHOD:	update_mesh()					-
    #--------------------------------------------------------------------
    def update_mesh( global_meshes, dm, dm_mesh_dict ):
      max_value = -1
      dm_mesh_updates = {}
      for cur_type, cur_mesh in dm_mesh_dict.iteritems():
	if cur_type and len( cur_mesh ) > 0:
	  if cur_type in global_meshes:
	    cur_global = global_meshes[ cur_type ]
	  else:
	    cur_global = set()
	    global_meshes[ cur_type ] = cur_global

	  if cur_type == 'pin' and is_offset_mesh( cur_global, cur_mesh ):
	    dm_mesh_updates[ cur_type ] = np.array( sorted( cur_global ) )
	  else:
	    max_value = max( max_value, cur_mesh[ -1 ] )
	    cur_mesh_set = set( cur_mesh )
	    cur_global.update( cur_mesh_set )
	    if not (cur_type == 'detector' and dm.core.detectorMeshIsCopied):
	      global_meshes[ 'all' ].update( cur_mesh_set )
	  #end else not is_offset_mesh( cur_global, cur_mesh )
	#end if cur_type and len( cur_mesh ) > 0
      #end for cur_name, cur_mesh

      for t, m in dm_mesh_updates.iteritems():
        dm_mesh_dict[ t ] = m

      return  max_value
    #end update_mesh

    self.detectorMap = None
    self.maxAxialValue = -1.0
    global_mesh_centers = { 'all': set() }
    global_meshes = { 'all': set() }

    for dm in self.dataModels.values():
      core = dm.GetCore()
      if core is not None:
	self.maxAxialValue = max(
	    self.maxAxialValue,
	    update_mesh( global_meshes, dm, dm.axialMeshDict )
	    )

        if self.detectorMap is None and dm.HasDetectorData():
          self.detectorMap = np.copy( dm.core.detectorMap )
      #end if core
    #end for dm

    for k, v in global_meshes.iteritems():
      if k != 'detector':
	vdata = np.array( sorted( list( v ) ), dtype = np.float64 )
        global_mesh_centers[ k ] = (vdata[ 0 : -1 ] + vdata[ 1 : ]) / 2.0

#		-- Convert sets to list
#		--
    self.axialMeshDict.clear()
    for n, v in global_meshes.iteritems():
      self.axialMeshDict[ n ] = list( sorted( v ) )

    self.axialMeshCentersDict.clear()
    for n, v in global_mesh_centers.iteritems():
      self.axialMeshCentersDict[ n ] = list( sorted( v ) )

    return  self.maxAxialValue
  #end _UpdateMeshValues


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr._UpdateTimeValues()		-
  #----------------------------------------------------------------------
  def _UpdateTimeValues( self ):
    """Updates the timeValues and timeValuesById properties based on the
open DataModels and the timeDataSet property.
@return			timeValues property value
"""
    result = []

    if self.timeDataSet == 'state':
      cur_count = 0
      for name, dm in self.dataModels.iteritems():
	#self.timeValuesById[ name ] = range( dm.GetStatesCount() )
	self.timeValuesById[ name ] = range( 1, dm.GetStatesCount() + 1 )
        cur_count = max( cur_count, dm.GetStatesCount() )
      #result = range( cur_count )
      result = range( 1, cur_count + 1 )

    elif self.timeDataSet:
      # cannot resolve with sets b/c values repeat
      #cur_set = set()
      spec = dict( ds_name = self.timeDataSet )
      for name, dm in self.dataModels.iteritems():
	cur_values = dm.ReadDataSetTimeValues( spec )
	if cur_values and self.timeDataSet in cur_values:
	  cur_list = cur_values[ self.timeDataSet ].tolist()
	  self.timeValuesById[ name ] = cur_list
	  #cur_set.update( set( cur_list ) )
	  #self._ResolveLists( result, cur_list )
	  result = DataUtils.MergeList( result, *cur_list )
	else:
	  self.timeValuesById[ name ] = []
      #result = list( cur_set )
    #end if-elif

    #result.sort()
    self.timeValues = result
    return  result
  #end _UpdateTimeValues


#		-- Static Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		DataModelMgr.main()				-
  #----------------------------------------------------------------------
#  @staticmethod
#  def main():
#    try:
#      if len( sys.argv ) < 2:
#        print >> sys.stderr, 'Usage: datamodel.py casl-output-fname'
#
#      else:
#        data = DataModel( sys.argv[ 1 ] )
#	print str( data )
#      #end if-else
#
#    except Exception, ex:
#      print >> sys.stderr, str( ex )
#      et, ev, tb = sys.exc_info()
#      while tb:
#	print >> sys.stderr, \
#            'File=' + str( tb.tb_frame.f_code ) + \
#            ', Line=' + str( traceback.tb_lineno( tb ) )
#        tb = tb.tb_next
#      #end while
#  #end main
#end DataModelMgr


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
#if __name__ == '__main__':
  #DataModelMgr.main()
