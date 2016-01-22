#!/usr/bin/env python
# $Id$
#------------------------------------------------------------------------
#	NAME:		datamodel.py					-
#	HISTORY:							-
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
import cStringIO, h5py, json, math, os, sys, threading, traceback
import numpy as np
import pdb


COL_LABELS = \
  (
    'R', 'P', 'N', 'M', 'L', 'K', 'J', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A'
  )

#{1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}

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
    if h5_group != None:
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

#    if self.axialMesh == None or self.axialMeshCenters == None:
    if self.axialMesh == None:
      missing.append( 'AXIAL_MESH not found' )
#    elif self.axialMesh.shape[ 0 ] != self.nax + 1 or \
#        self.axialMeshCenters.shape[ 0 ] != self.nax:
    elif self.axialMesh.shape[ 0 ] != self.nax + 1:
      missing.append( 'AXIAL_MESH shape is not consistent with NAX' )

    if self.coreMap == None:
      missing.append( 'CORE_MAP not found' )
    elif self.coreMap.shape[ 0 ] != self.nassy or \
        self.coreMap.shape[ 1 ] != self.nassx:
      missing.append( 'CORE_MAP shape is not consistent with NASSX and NASSY' )

    if self.detectorMap != None and self.coreMap != None:
      if self.detectorMap.shape != self.coreMap.shape:
        missing.append( 'DETECTOR_MAP shape inconsistent with CORE_MAP shape' )

    if self.pinVolumes == None:
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
    if self.coreLabels != None and len( self.coreLabels ) >= 2:
      result = '(%s-%s)' % \
          ( self.coreLabels[ 0 ][ col ], self.coreLabels[ 1 ][ row ] )

    return  result
  #end CreateAssyLabel


  #----------------------------------------------------------------------
  #	METHOD:		Core.CreatePinFactors()				-
  #----------------------------------------------------------------------
  def CreatePinFactors( self ):
    """Creates a pin factors np.ndarray for the current config properties:
coreSym, npiny, npinx, nax, and nass.
@return			np.ndarray with shape ( npiny, npinx, nax, nass ) or
			None if any of the properties are 0
@deprecated  Use Averager.CreateCorePinFactors()
"""
    factors = None
    if self.IsNonZero():
      factors = np.ndarray(
          ( self.npiny, self.npinx, self.nax, self.nass ),
	  np.float32
	  )
      factors.fill( 1.0 )
      factors[ 0, :, :, : ] = 1.0 / self.coreSym
      factors[ :, 0, :, : ] = 1.0 / self.coreSym
      factors[ 0, 0, :, : ] /= self.coreSym
    #end if

    return  factors
  #end CreatePinFactors


  #----------------------------------------------------------------------
  #	METHOD:		Core._FindInGroup()				-
  #----------------------------------------------------------------------
  def _FindInGroup( self, name, *groups ):
    match = None
    for g in groups:
      if g != None and name in g:
        match = g[ name ]
	break
    #end for
    return  match
  #end _FindInGroup


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
    if h5_group == None or not isinstance( h5_group, h5py.Group ):
      raise Exception( 'Must have valid HDF5 file' )

    core_group = h5_group[ 'CORE' ]
    input_group = h5_group[ 'INPUT' ] if 'INPUT' in h5_group else None

#		-- Assert on CORE or INPUT group
#		--
#    if core_group == None and input_group == None:
#      raise Exception( 'Could not find "CORE" or "INPUT" group' )
    if core_group == None:
      raise Exception( 'Could not find "CORE"' )

    self._ReadImpl( core_group, input_group )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		Core._ReadImpl()				-
  #----------------------------------------------------------------------
  def _ReadImpl( self, core_group, input_group ):
    in_core_group = None
    if input_group != None:
      in_core_group = input_group.get( 'CASEID/CORE' )

#		-- Assert on must have 'core_map'
#		--
    item = self._FindInGroup( 'core_map', core_group, in_core_group )
    if item == None:
      raise Exception( '"core_map" dataset not found' )

#		-- No exception, plow on
#		--
    self.coreMap = item.value
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
    if item != None:
      self.apitch = item.value.item() if len( item.shape ) > 0 else item.value
#      self.apitch = item.value[ 0 ]

    item = self._FindInGroup( 'axial_mesh', core_group, in_core_group )
    if item != None:
      self.axialMesh = item.value
      self.nax = self.axialMesh.shape[ 0 ] - 1
#			-- Numpy magic
      t = np.copy( item.value )
      t2 = np.r_[ t, np.roll( t, -1 ) ]
      self.axialMeshCenters = np.mean( t2.reshape( 2, -1 ), axis = 0 )[ : -1 ]

    item = self._FindInGroup( 'core_sym', core_group, in_core_group )
    if item != None:
      self.coreSym = item.value.item() if len( item.shape ) > 0 else item.value
      #self.coreSym = item.value[ 0 ]

    self.pinVolumesSum = 0
    item = self._FindInGroup( 'pin_volumes', core_group, in_core_group )
    if item != None:
      self.pinVolumes = item.value
      self.pinVolumesSum = np.sum( item.value )
      self.npin = self.pinVolumes.shape[ 0 ]  # and [ 1 ]
      self.npiny = self.pinVolumes.shape[ 0 ]
      self.npinx = self.pinVolumes.shape[ 1 ]
      if self.nax == 0:
        self.nax = self.pinVolumes.shape[ 2 ]
      self.nass = self.pinVolumes.shape[ 3 ]

    item = self._FindInGroup( 'rated_flow', core_group, in_core_group )
    if item != None:
      self.ratedFlow = item.value.item() if len( item.shape ) > 0 else item.value
      #self.ratedFlow = item.value[ 0 ]

    item = self._FindInGroup( 'rated_power', core_group, in_core_group )
    if item != None:
      self.ratedPower = item.value.item() if len( item.shape ) > 0 else item.value
      #self.ratedPower = item.value[ 0 ]

#		-- Optional detector_map
#		--
    item = self._FindInGroup( 'detector_map', core_group, in_core_group )
    #if item != None and item.value.shape == self.coreMap.shape:
    if item != None:
      self.detectorMap = item.value
      self.ndet = np.amax( item.value )

#			-- Optional detector_mesh
#			--
      item = self._FindInGroup( 'detector_mesh', core_group )
      if item != None:
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

    if self.npin == 0 and input_group != None:
      num_pins_ds = input_group.get( 'CASEID/ASSEMBLIES/Assembly_1/num_pins' )
      if num_pins_ds != None:
        self.npin = num_pins_ds.value.item() if len( num_pins_ds.shape ) > 0 else num_pins_ds.value
	self.npinx = self.npin
	self.npiny = self.npin
        #self.npin = num_pins_ds.value[ 0 ]
    #end if

#		-- Assert NAX match b/w axial_mesh and pin_volumes
#		--
    if self.nax > 0 and self.pinVolumes != None and \
        self.pinVolumes.shape[ 2 ] != self.nax:
      raise Exception( 'NAX dimension mismatch between "axial_mesh" and "pin_volumes"' )

#		-- Assert on NPIN
#		--
#x    if self.npin == 0:
#x      raise Exception( 'NPIN could not be determined from "num_pins" or "pin_volumes"' )
  #end _ReadImpl


  #----------------------------------------------------------------------
  #	METHOD:		Core.ToJson()					-
  #----------------------------------------------------------------------
  def ToJson( self ):
    obj = {}
    obj[ 'apitch' ] = self.apitch.item()
    if self.axialMesh != None:
      obj[ 'axialMesh' ] = self.axialMesh.tolist()
    if self.coreMap != None:
      obj[ 'coreMap' ] = self.coreMap.tolist()
    obj[ 'coreSym' ] = self.coreSym.item()
    if self.detectorMap != None:
      obj[ 'detectorMap' ] = self.detectorMap.tolist()
    if self.detectorMesh != None:
      obj[ 'detectorMesh' ] = self.detectorMesh.tolist()
    obj[ 'nass' ] = self.nass
    obj[ 'nassx' ] = self.nassx
    obj[ 'nassy' ] = self.nassy
    obj[ 'nax' ] = self.nax
    obj[ 'ndet' ] = self.ndet
    obj[ 'ndetax' ] = self.ndetax
    obj[ 'npin' ] = self.npin
    if self.pinVolumes != None:
      obj[ 'pinVolumes' ] = self.pinVolumes.tolist()
    obj[ 'ratedFlow' ] = self.ratedFlow.item()
    obj[ 'ratedPower' ] = self.ratedPower.item()

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
  core			Core
  dataSetNames		dict of dataset names by category
			  ( 'channel', 'detector', 'extra', 'pin', 'scalar' )
  extraStates		list of ExtraState instances
  h5ExtraFile		extra datasets h5py.File, None until exists or created
  h5ExtraFilePath	path to extra datasets file
  h5File		h5py.File
  pinPowerRange		( min, max ), computed from all states
  ranges		dict of ranges ( min, max ) by dataset
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
    if self.h5ExtraFile != None:
      self.h5ExtraFile.close()

    if self.h5File != None:
      self.h5File.close()
  #end __del__


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, h5f_param = None ):
    """Constructor with optional HDF5 file or filename.  If neither are
passed, the read() method must be called.
@param  h5f_param	either an h5py.File instance or the name of an
			HDF5 file (.h5)
"""
    self.rangesLock = threading.RLock()

    self.Clear()
    if h5f_param != None:
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
    self.dataSetNames = None
    self.extraStates = None
    self.h5ExtraFile = None
    self.h5ExtraFilePath = None
    self.h5File = None
    self.pinPowerRange = None
    self.ranges = None
    self.states = None
  #end Clear


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.Close()				-
  #----------------------------------------------------------------------
  def Close( self ):
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
	if self.core != None else \
	( -1, -1, -1 )
  #end CreateAssemblyIndex


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.CreateAxialValue()			-
  #----------------------------------------------------------------------
  def CreateAxialValue( self, **kwargs ):
    """Create from 'core_ndx' or 'detector_ndx' index values.
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
      core_ndx = max( 0, min( kwargs[ 'core_ndx' ], self.core.nax -1 ) )
      axial_cm = self.core.axialMeshCenters[ core_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMeshCenters, axial_cm )

    elif 'pin_ndx' in kwargs:
      pin_ndx = max( 0, min( kwargs[ 'pin_ndx' ], self.core.nax -1 ) )
      axial_cm = self.core.axialMeshCenters[ pin_ndx ]
      det_ndx = self.FindListIndex( self.core.detectorMeshCenters, axial_cm )

    return  ( axial_cm, core_ndx, det_ndx )
  #end CreateAxialValue


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._CreateExtraH5File()			-
  #----------------------------------------------------------------------
  def _CreateExtraH5File( self, truncate_flag = False ):
    """Creates and initializes the "extras" HDF5 file.  The state points
are initialized.
@param  truncate_flag	if True, any exist file is first removed
@return			new h5py.File object (h5ExtraFile property)
"""
#		-- Delete existing if requexted
#		--
    if truncate_flag and self.h5ExtraFile != None:
      self.h5ExtraFile.close()
      if os.path.exists( self.h5ExtraFilePath ):
        os.remove( self.h5ExtraFilePath )
      self.h5ExtraFile = None
    #end if

#		-- Create if it does not exist
#		--
    if self.h5ExtraFile == None:
      self.h5ExtraFile = h5py.File( self.h5ExtraFilePath, 'w' )

#			-- Add states with exposure values
#			--
      if self.GetStates() != None:
        for st in self.GetStates():
	  if st.GetGroup() != None:
	    from_group = st.GetGroup()
	    to_group = self.h5ExtraFile.\
	        create_group( from_group.name.replace( '/', '' ) )
	    if 'exposure' in from_group:
	      exp_ds = to_group.create_dataset(
	          'exposure',
		  data = from_group[ 'exposure' ].value
		  )
	  #end if state h5py group exists
	#end for
      #end if states exist

      self.h5ExtraFile.flush()
    #end if file doesn't exist

    names, self.extraStates = ExtraState.ReadAll( self.h5ExtraFile )

    return  self.h5ExtraFile
  #end _CreateExtraH5File


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

    if self.core != None:
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
  #	METHOD:		DataModel.FindFirstDetector()			-
  #----------------------------------------------------------------------
  def FindFirstDetector( self ):
    result = ( -1, -1, -1 )

    if self.core != None and self.core.detectorMap != None:
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
descending.
@param  values		list of values
@param  value		value to search
@return			0-based index N, values[ N ]
			'a': values[ N ] <= value < values[ N + 1 ]
			'd': values[ N ] >= value > values[ N + 1 ]
"""
    match_ndx = -1

    if values != None and len( values ) > 0:
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
  #	METHOD:		DataModel.GetCore()				-
  #----------------------------------------------------------------------
  def GetCore( self ):
    """Accessor for the 'core' property.
@return			Core instance or None
"""
    return  self.core
  #end GetCore


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetDisplayName()		-
  #----------------------------------------------------------------------
  def GetDataSetDisplayName( self, ds_name ):
    """Removes any 'extra:' prefix.
"""
    return  ds_name[ 6 : ] if ds_name.startswith( 'extra:' ) else ds_name
  #end GetDataSetDisplayName


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetDataSetNames()			-
  #----------------------------------------------------------------------
  def GetDataSetNames( self, category = None ):
    """Accessor for the 'dataSetNames' property.
@param  category	optional category/type
@return			if category != None, list of datasets in that
			category
			if category == None, dict of dataset name lists by
			category
			( 'axial', 'channel', 'detector', 'extra', 'other',
			  'pin', 'scalar' )
"""
    return \
        self.dataSetNames if category == None else \
	self.dataSetNames.get( category, [] )
  #end GetDataSetNames


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetExtra4DDataSets()			-
  #----------------------------------------------------------------------
  def GetExtra4DDataSets( self ):
    """Retrieves extra datasets that have a shape of length 4
@return			list of names, possibly empty
"""
    names = []
    extra_names = self.GetDataSetNames( 'extra' )
    if extra_names != None and len( extra_names ) > 0:
      st = self.GetExtraState()
      if st != None:
        for en in extra_names:
	  dset = st.GetDataSet( en )
	  if len( dset.shape ) == 4:
	    names.append( en )
      #end if st
    #end if extra_names

    return  names
  #end GetExtra4DDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetExtraState()			-
  #----------------------------------------------------------------------
  def GetExtraState( self, ndx = 0 ):
    """Retrieves a specific state point by index.
@param  ndx		0-based index
@return			ExtraState object or None if extraStates not defined
			or ndx out of range
"""
    return  \
	self.extraStates[ ndx ]  \
	if self.extraStates != None and ndx >= 0 and \
	    ndx < len( self.extraStates ) else \
	None
  #end GetExtraState


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetExtraStates()			-
  #----------------------------------------------------------------------
  def GetExtraStates( self ):
    """Accessor for the 'extraStates' property.
@return			list of ExtraState instances or None
"""
    return  self.extraStates
  #end GetExtraStates


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetFirstDataSet()			-
  #----------------------------------------------------------------------
  def GetFirstDataSet( self, category ):
    """Retrieves the first dataset in the specified category
@param  category	category/type
@return			dataset name or None
"""
    names = self.dataSetNames.get( category )
    return  names[ 0 ] if names != None and len( names ) > 0 else None
  #end GetFirstDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetH5ExtraFile()			-
  #----------------------------------------------------------------------
  def GetH5ExtraFile( self ):
    """Accessor for the 'h5ExtraFile' property.
@return			h5py.File instance or None
"""
    return  self.h5ExtraFile
  #end GetH5ExtraFile


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
  #	METHOD:		DataModel.GetPinPowerRange()			-
  #----------------------------------------------------------------------
  def GetPinPowerRange( self ):
    """( min, max )
@return			range or None
"""
    return  self.pinPowerRange
  #end GetPinPowerRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetRange()				-
  #----------------------------------------------------------------------
  def GetRange( self, ds_name ):
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
      if ds_range == None:
        ds_range = self._ReadDataSetRange( ds_name )
        self.ranges[ ds_name ] = ds_range
    finally:
      self.rangesLock.release()

    if ds_range == None:
      ds_range = DataModel.DEFAULT_range

    return  ds_range
  #end GetRanges


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
        None if ds == None else \
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
	if self.states != None and ndx >= 0 and ndx < len( self.states ) else \
	None
  #end GetState


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.GetStateDataSet()			-
  #----------------------------------------------------------------------
  def GetStateDataSet( self, state_ndx, ds_name ):
    """Retrieves a normal or extra dataset.
@param  state_ndx	0-based state point index
@param  ds_name		dataset name, where a prefix of 'extra:' means it's an
			extra dataset
@return			h5py.Dataset object if found or None
"""
    if ds_name == None:
      st = None
    elif ds_name.startswith( 'extra:' ):
      st = self.GetExtraState( state_ndx )
      use_name = ds_name[ 6 : ]
    else:
      st = self.GetState( state_ndx )
      use_name = ds_name

    return  st.GetDataSet( use_name ) if st != None else None
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
    if self.IsValid( state_index = state_ndx ) and ds_name != None:
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
        self.core != None and self.states != None and \
	len( self.states ) > 0 and \
	self.core.nass > 0 and self.core.nax > 0 and self.core.npin > 0
  #end HasData


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.HasDataSetCategory()			-
  #----------------------------------------------------------------------
  def HasDataSetCategory( self, category = None ):
    """Tests existence of datasets in category
@param  category	one of 'axial', 'channel', 'detector', 'extra',
			'other', 'pin', 'scalar'
@return			True if there are datasets, False otherwise
"""
    return  \
        category in self.dataSetNames and \
	len( self.dataSetNames[ category ] ) > 0
  #end HasDataSetCategory


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.HasExtraDataSet()			-
  #----------------------------------------------------------------------
  def HasExtraDataSet( self, full_ds_name ):
    """
"""
    exists = False

    if self.h5ExtraFile != None:
      if full_ds_name.startswith( 'core' ):
	exists = full_ds_name in self.h5ExtraFile

      else:
	st = self.GetExtraState( 0 )
	exists = st != None and st.HasDataSet( full_ds_name )
      #end if core or not
    #end if

    return  exists
  #end HasExtraDataSet


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
    return  value == 0.0
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
        valid = val != None and val[ 0 ] >= 0 and val[ 0 ] < self.core.nass
      else:
        valid = val >= 0 and val < self.core.nass

    if 'axial_level' in kwargs:
      val = kwargs[ 'axial_level' ]
      valid = val >= 0 and val < self.core.nax

    if 'channel_colrow' in kwargs and kwargs[ 'channel_colrow' ] != None:
      col, row = kwargs[ 'channel_colrow' ]
      valid = \
          col >= 0 and col <= self.core.npin and \
	  row >= 0 and row <= self.core.npin

    if 'detector_index' in kwargs:
      val = kwargs[ 'detector_index' ]
      valid = val >= 0 and val < self.core.ndet

    if 'pin_colrow' in kwargs and kwargs[ 'pin_colrow' ] != None:
      col, row = kwargs[ 'pin_colrow' ]
      valid = \
          col >= 0 and col < self.core.npin and \
	  row >= 0 and row < self.core.npin

    if 'state_index' in kwargs:
      val = kwargs[ 'state_index' ]
      valid = val >= 0 and val < len( self.states )
      if valid and 'dataset_name' in kwargs:
        valid = kwargs[ 'dataset_name' ] in self.states[ val ].group
    #end if 'state_index'

    return  valid
  #end IsValid


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.LoadExtraDataSet()			-
  #----------------------------------------------------------------------
  def LoadExtraDataSet( self, ds_name, src_name = 'core', state_ndx = -1 ):
    """Retrieves an extra dataset.
@param  ds_name		name of dataset to load, required
@param  src_name	optional name of source dataset for a time-based
			dataset when combined with state_ndx, otherwise
			defaults to 'core'
@param  state_ndx	optional 0-based state point index when combined with
			src_name
@return			h5py.Dataset object or None if not found

Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
if both 'src_name' and 'state_ndx' are specified, the dataset is searched
using the fully-qualified name in the specified state point (if 'state_ndx'
is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
to be 'core', and the dataset is not associated with a state point.
"""
    dset = None

    if self.h5ExtraFile != None and ds_name != None:
      qname = src_name + '.' + ds_name

      if state_ndx < 0:
        if qname in self.h5ExtraFile:
	  dset = self.h5ExtraFile[ qname ]
      else:
        st = self.GetExtraState( state_ndx )
	if st != None and qname in st.GetGroup():
	  dset = st.GetDataSet( qname )
      #end if-else core or state point
    #end if file exists

    return  dset
  #end LoadExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.LoadExtraDataSet_0()			-
  #----------------------------------------------------------------------
  def LoadExtraDataSet_0( self, *argc, **kwargs ):
    """Retrieves an extra dataset.
@param  kwargs		parameters:
  'ds_name'		name of dataset to store, required
  'src_name'		name of source dataset for a time-based dataset if
			specified with 'state_ndx', otherwise 'core' is assumed
			as the source name
  'state_ndx'		0-based state point index
@return			h5py.Dataset object or None if not found

Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
if both 'src_name' and 'state_ndx' are specified, the dataset is searched
using the fully-qualified name in the specified state point (if 'state_ndx'
is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
to be 'core', and the dataset is not associated with a state point.
"""
    dset = None
    ds_name = kwargs.get( 'ds_name' )

    if self.h5ExtraFile != None and ds_name != None:
      src_name = kwargs.get( 'src_name', 'core' )
      state_ndx = kwargs.get( 'state_ndx', -1 )
      qname = src_name + '.' + ds_name

      if state_ndx < 0:
        if qname in self.h5ExtraFile:
	  dset = self.h5ExtraFile[ qname ]
      else:
        st = self.GetExtraState( state_ndx )
	if st != None and qname in st.GetGroup():
	  dset = st.GetDataSet( qname )
      #end if-else core or state point
    #end if file exists

    return  dset
  #end LoadExtraDataSet_0


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
    self.dataSetNames, self.states = State.ReadAll( self.h5File, self.core )

    self.pinPowerRange = self._ReadDataSetRange( 'pin_powers' )
    self.ranges = { 'pin_powers': self.pinPowerRange }

#	-- Read extras file if it exists
#	--
    self.h5ExtraFile = None
    base, ext = os.path.splitext( self.h5File.filename )
    self.h5ExtraFilePath = base + '.extra' + ext
    if os.path.exists( self.h5ExtraFilePath ):
      self.h5ExtraFile = h5py.File( self.h5ExtraFilePath, 'r+' )  # 'a': r/w or creates
      self.ReadExtraDataSets()
#      self.dataSetNames[ 'extra' ], self.extraStates = \
#          ExtraState.ReadAll( self.h5ExtraFile )
  #end Read


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ReadExtraDataSets()			-
  #----------------------------------------------------------------------
  def ReadExtraDataSets( self ):
    """
"""
    if self.h5ExtraFile == None:
      self.dataSetNames[ 'extra' ] = []
      self.extraStates = None

    else:
      self.dataSetNames[ 'extra' ], self.extraStates = \
          ExtraState.ReadAll( self.h5ExtraFile )
  #end ReadExtraDataSets


  #----------------------------------------------------------------------
  #	METHOD:		DataModel._ReadDataSetRange()			-
  #----------------------------------------------------------------------
  def _ReadDataSetRange( self, ds_name ):
    """Scans the data for the range.  Could be very time consuming.
@param  ds_name		dataset name, where a prefix of 'extra:' means it's
			an extra dataset
"""
    range_min = sys.float_info.min
    range_max = sys.float_info.max

    if ds_name.startswith( 'extra:' ):
      use_states = self.GetExtraStates()
      use_name = ds_name[ 6 : ]
    else:
      use_states = self.GetStates()
      use_name = ds_name

    if use_states != None:
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
  #end _ReadDataSetRange


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.RemoveExtraDataSet()			-
  #----------------------------------------------------------------------
  def RemoveExtraDataSet( self, full_ds_name ):
    """Removes the named dataset from all extra states.
Note the fully-qualified name of a caculated dataset is 'source.name',
where 'source' is the name of the dataset from which the extra dataset was
calculated.
@param  full_ds_name	fully-qualified dataset name
"""
    if self.HasExtraDataSet( full_ds_name ):
      if full_ds_name.startswith( 'core' ):
        del self.h5ExtraFile[ full_ds_name ]

      else:
        for st in self.GetExtraStates():
	  st.RemoveDataSet( full_ds_name )
	#end for
      #end if-else

      self.h5ExtraFile.flush()
    #end if
  #end RemoveExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.StoreExtraDataSet()			-
  #----------------------------------------------------------------------
  def StoreExtraDataSet( self, ds_name, data, src_name = 'core', state_ndx = -1 ):
    """Adds or replaces an extra dataset.
@param  ds_name		name of dataset to store, required
@param  data		numpy.ndarray containing data to store, required
@param  src_name	optional name of source dataset for a time-based
			dataset when combined with state_ndx, otherwise
			defaults to 'core'
@param  state_ndx	optional 0-based state point index when combined with
			src_name
@return			h5py.Dataset object added

Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
if both 'src_name' and 'state_ndx' are specified, the dataset is stored
using the fully-qualified name in the specified state point (if 'state_ndx'
is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
to be 'core', and the dataset is not associated with a state point.
"""
    dset = None

#		-- Create Extra File if Necessary
#		--
    if self.h5ExtraFile == None:
      self._CreateExtraH5File( self )

#		-- Assert on required params
#		--
    if ds_name == None or data == None:
      raise  Exception( 'ds_name and data are required' )

#		-- State point dataset?
#		--
    st = self.GetExtraState( state_ndx )
    if src_name != 'core':
#			-- Assert on index
      if st == None:
        raise  Exception( '"state_ndx" out of range' )

      qname = src_name + '.' + ds_name
      #st = self.GetExtraState( state_ndx )
      st.RemoveDataSet( qname )
      dset = st.CreateDataSet( qname, data )

      if 'extra' not in self.dataSetNames:
        self.dataSetNames[ 'extra' ] = []
      if qname not in self.dataSetNames[ 'extra' ]:
        self.dataSetNames[ 'extra' ].append( qname )
        self.dataSetNames[ 'extra' ].sort()

    else:
      qname = 'core.' + ds_name
      if qname in self.h5ExtraFile:
        del self.h5ExtraFile[ qname ]

      dset = self.h5ExtraFile.create_dataset( qname, data = data )
    #end if-else core or state point

    self.h5ExtraFile.flush()
    return  dset
  #end StoreExtraDataSet


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.StoreExtraDataSet_0()			-
  #----------------------------------------------------------------------
  def StoreExtraDataSet_0( self, *argc, **kwargs ):
    """Adds or replaces an extra dataset.
@param  kwargs		parameters:
  'data'		numpy.ndarray containing data to store, required
  'ds_name'		name of dataset to store, required
  'src_name'		name of source dataset for a time-based dataset if
			specified with 'state_ndx', otherwise 'core' is assumed
			as the source name
  'state_ndx'		0-based state point index
@return			h5py.Dataset object added

Datasets are stored using a fully-qualified in form 'src_name.ds_name'.
if both 'src_name' and 'state_ndx' are specified, the dataset is stored
using the fully-qualified name in the specified state point (if 'state_ndx'
is valid).  If 'src_name' or 'state_ndx' is omitted, the source is assumed
to be 'core', and the dataset is not associated with a state point.
"""
    dset = None

#		-- Create Extra File if Necessary
#		--
    if self.h5ExtraFile == None:
      self._CreateExtraH5File( self )

#		-- Assert on required params
#		--
    if 'data' not in kwargs and 'ds_name' not in kwargs:
      raise  Exception( '"data" and "ds_name" are required' )

    data_in = kwargs.get( 'data' )
    ds_name = kwargs.get( 'ds_name' )

    src_name = kwargs.get( 'src_name', 'core' )
    state_ndx = kwargs.get( 'state_ndx', -1 )

#		-- State point dataset?
#		--
    st = self.GetExtraState( state_ndx )
    if src_name != 'core':
#			-- Assert on index
      if st == None:
        raise  Exception( '"state_ndx" out of range' )

      qname = src_name + '.' + ds_name
      #st = self.GetExtraState( state_ndx )
      st.RemoveDataSet( qname )
      dset = st.CreateDataSet( qname, data_in )

      if 'extra' not in self.dataSetNames:
        self.dataSetNames[ 'extra' ] = []
      if qname not in self.dataSetNames[ 'extra' ]:
        self.dataSetNames[ 'extra' ].append( qname )
        self.dataSetNames[ 'extra' ].sort()

    else:
      qname = 'core.' + ds_name
      if qname in self.h5ExtraFile:
        del self.h5ExtraFile[ qname ]

      dset = self.h5ExtraFile.create_dataset( qname, data = data_in )
    #end if-else core or state point

    self.h5ExtraFile.flush()
    return  dset
  #end StoreExtraDataSet_0


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ToJson()				-
  #----------------------------------------------------------------------
  def ToJson( self ):
    obj = {}

    if self.core != None:
      obj[ 'core' ] = self.core.ToJson()
    if self.states != None:
      obj[ 'states' ] = State.ToJsonAll( self.states )
    if self.pinPowerRange != None:
      obj[ 'pinPowerRange' ] = list( self.pinPowerRange )

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
    return  data != None and data.IsValid( **kwargs )
  #end IsValidObj


  #----------------------------------------------------------------------
  #	METHOD:		DataModel.ToCSV()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ToCSV( data ):
    """Retrieves a normal or extra dataset.
@param  data		numpy.ndarray containing data to dump
@return			h5py.Dataset object if found or None
"""
    if data == None:
      cvs_text = None

    else:
      output = cStringIO.StringIO()
      try:
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
      if len( slice_name ) > 0:
        fp.write( '# Slice: %s\n' % slice_name )
      np.savetxt( fp, data, fmt = '%.7g', delimiter = ',' )

    else:
      ndx = 0
      for data_slice in data:
        if len( slice_name ) > 0:
	  slice_name += ','
        slice_name += str( ndx )
        ndx += 1

        DataModel._WriteCSV( fp, data_slice, slice_name )
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
    if name != None and state_group != None:
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

    if self.pinPowers == None:
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
  #	METHOD:		State.GetGroup()				-
  #----------------------------------------------------------------------
  def GetGroup( self ):
    return  self.group
  #end GetGroup


  #----------------------------------------------------------------------
  #	METHOD:		State.GetDataSet()				-
  #----------------------------------------------------------------------
  def GetDataSet( self, ds_name ):
    """
@return			h5py.Dataset object or None if not found
"""
    return \
        self.group[ ds_name ] \
	if ds_name != None and ds_name in self.group else \
	None
  #end GetDataSet


  #----------------------------------------------------------------------
  #	METHOD:		State.HasDataSet()				-
  #----------------------------------------------------------------------
  def HasDataSet( self, ds_name ):
    """
"""
    return  ds_name != None and ds_name in self.group
  #end HasDataSet


  #----------------------------------------------------------------------
  #	METHOD:		State.Read()					-
  #----------------------------------------------------------------------
  def Read( self, index, name, state_group ):
    self.Clear()
    self.group = state_group
    self.index = index
    self.name = name

    if state_group != None and isinstance( state_group, h5py.Group ):
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
    removed = ds_name != None and ds_name in self.group
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
    if self.exposure != None:
      obj[ 'exposure' ] = self.exposure.item()
    if self.keff != None:
      obj[ 'keff' ] = self.keff.item()

    if self.pinPowers != None:
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

    if states == None or len( states ) == 0:
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
  def ReadAll( h5_group, core ):
    """
@return			( dataset_names_dict, states )
"""
    ds_names_dict = {}
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
	if core.npin == 0 and 'pin_powers' in cur_group:
	  core.npin = cur_group[ 'pin_powers'].shape[ 0 ]

	if n == 1:
	  ds_names_dict = State.FindDataSets( h5_group[ name ], core )
      #end if-else
      n += 1
    #end while

    return  ( ds_names_dict, states )
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
#	CLASS:		ExtraState					-
#------------------------------------------------------------------------
class ExtraState( State ):
  """Special State for extra datasets.
  
Fields:
  exposure		exposure time in (?) secs
  group			HDF5 group
  keff			always None
  pinPowers		always None
"""

#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		ExtraState.__init__()				-
  #----------------------------------------------------------------------
  def __init__( self, index, name = None, state_group = None ):
    """
@param  state_group	HDF5 group for this state
"""
    super( ExtraState, self ).__init__( index, name, state_group )
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		ExtraState.Check()				-
  #----------------------------------------------------------------------
  def Check( self, core ):
    """
@return			empty list
"""
    return  []
  #end Check


  #----------------------------------------------------------------------
  #	METHOD:		ExtraState.ReadAll()				-
  #----------------------------------------------------------------------
  @staticmethod
  def ReadAll( h5_group ):
    """
@return			( ds_names, states )
"""
    ds_names = []
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
        states.append( ExtraState( n - 1, name, cur_group ) )

	if n == 1:
	  ds_names = cur_group.keys()
      #end if-else

      n += 1
    #end while

    return  ( ds_names, states )
  #end ReadAll
#end ExtraState


#------------------------------------------------------------------------
#	NAME:		main()						-
#------------------------------------------------------------------------
if __name__ == '__main__':
  DataModel.main()
