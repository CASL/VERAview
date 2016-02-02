#!/usr/bin/env python
#------------------------------------------------------------------------
#	NAME:		event.py					-
#	HISTORY:							-
#		2016-02-02	leerw@ornl.gov				-
# 	  Copied from
#	  http://www.valuedlessons.com/2008/04/events-in-python.html
#	  and reformatted.
#		2008-04-28	leerw@ornl.gov				-
#------------------------------------------------------------------------


#------------------------------------------------------------------------
#	CLASS:		Event						-
#------------------------------------------------------------------------
class Event ( object ):
  """
Simple event implementation from
http://www.valuedlessons.com/2008/04/events-in-python.html
"""
#		-- Object Methods
#		--


  #----------------------------------------------------------------------
  #	METHOD:		__init__()					-
  #----------------------------------------------------------------------
  def __init__( self, source ):
    self.fListeners = set()
    self.fSource = source
  #end __init__


  #----------------------------------------------------------------------
  #	METHOD:		addListener()					-
  #----------------------------------------------------------------------
  def addListener( self, l ):
    """
@param  l		listener to add
@return			self
"""
    self.fListeners.add( l )
    return  self
  #end addListener


  #----------------------------------------------------------------------
  #	METHOD:		fire()						-
  #----------------------------------------------------------------------
  def fire( self, *args, **kargs ):
    """
"""
    for l in self.fListeners:
      l( self.fSource, *args, **kargs )
  #end fire


  #----------------------------------------------------------------------
  #	METHOD:		getSource()					-
  #----------------------------------------------------------------------
  def getSource( self ):
    return  self.fSource
  #end getSource


  #----------------------------------------------------------------------
  #	METHOD:		getListenerCount()				-
  #----------------------------------------------------------------------
  def getListenerCount( self ):
    return  len( self.fListeners )
  #end getListenerCount


  #----------------------------------------------------------------------
  #	METHOD:		removeListener()				-
  #----------------------------------------------------------------------
  def removeListener( self, l ):
    """
@param  l		listener to remove
@return			self
"""
    if l in self.fListeners:
      self.fListeners.remove( l )
    return  self
  #end removeListener


  #----------------------------------------------------------------------
  #	METHOD REFERENCES						-
  #----------------------------------------------------------------------
  __call__ = fire
  __iadd__ = addListener
  __isub__ = removeListener
  __len__  = getListenerCount

#end Event
