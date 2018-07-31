"""
Management of recent searches

Copyright (c) 2018, Leo Moll

Licensed under MIT License
"""

# -- Imports ------------------------------------------------
import os
import json
import time

import xbmcplugin

from contextlib import closing
from operator import itemgetter

from resources.lib.kodi.KodiAddon import KodiPlugin

# -- Classes ------------------------------------------------
class RecentSearches( object ):
	def __init__( self, plugin, extendedsearch, sortmethods = None ):
		self.plugin			= plugin
		self.handle			= plugin.addon_handle
		self.sortmethods	= sortmethods if sortmethods is not None else [ xbmcplugin.SORT_METHOD_TITLE ]
		self.datafile		= os.path.join( self.plugin.settings.datapath, 'recent_ext_searches.json' if extendedsearch else 'recent_std_searches.json' )
		self.extendedsearch	= extendedsearch
		self.recents		= []

	def load( self ):
		try:
			with closing( open( self.datafile ) ) as json_file:
				data = json.load( json_file )
				if isinstance( data, list ):
					self.recents = sorted( data, key = itemgetter( 'when' ), reverse = True )
		except Exception as err:
			self.plugin.error( 'Failed to load last searches file {}: {}'.format( self.datafile, err ) )
		return self

	def save( self ):
		data = sorted( self.recents, key = itemgetter( 'when' ), reverse = True )
		try:
			with closing( open( self.datafile, 'w' ) ) as json_file:
				json.dump( data, json_file )
		except Exception as err:
			self.plugin.error( 'Failed to write last searches file {}: {}'.format( self.datafile, err ) )
		return self

	def add( self, search ):
		slow = search.lower()
		try:
			for entry in self.recents:
				if entry['search'].lower() == slow:
					entry['when'] = int( time.time() )
					return self
		except Exception as err:
			self.plugin.error( 'Recent searches list is broken (error {}) - cleaning up'.format( err ) )
			self.recents = []
		self.recents.append( {
			'search':			search,
			'when':				int( time.time() )
		} )
		return self

	def populate( self ):
		for entry in self.recents:
			self.plugin.addFolderItem(
				entry['search'],
				{
					'mode': "research",
					'search': entry['search'],
					'extendedsearch': self.extendedsearch
				}
			)
