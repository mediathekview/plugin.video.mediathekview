# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
from classes.storemysql  import StoreMySQL
from classes.storesqlite import StoreSQLite


# -- Classes ------------------------------------------------
class Store( object ):
	def __init__( self, id, logger, notifier, settings ):
		self.logger = logger
		self.notifier = notifier
		self.settings = settings
		# load storage engine
		if settings.type == '0':
			self.logger.info( 'Database driver: Internal (sqlite)' )
			self.sql = StoreSQLite( id, logger.getNewLogger( 'StoreMySQL' ), notifier, self.settings )
		elif settings.type == '1':
			self.logger.info( 'Database driver: External (mysql)' )
			self.sql = StoreSQLite( id, logger.getNewLogger( 'StoreMySQL' ), notifier, self.settings )
		else:
			self.logger.warn( 'Unknown Database driver selected' )
			self.sql = None

	def __del__( self ):
		if self.sql is not None:
			del self.sql
			self.sql = None

	def Init( self, reset = False ):
		if self.sql is not None:
			self.sql.Init( reset )

	def Exit( self ):
		if self.sql is not None:
			self.sql.Exit()

	def Search( self, search, filmui ):
		if self.sql is not None:
			self.sql.Search( search, filmui )

	def SearchFull( self, search, filmui ):
		if self.sql is not None:
			self.sql.SearchFull( search, filmui )

	def GetRecents( self, filmui ):
		if self.sql is not None:
			self.sql.GetRecents( filmui )

	def GetLiveStreams( self, filmui ):
		if self.sql is not None:
			self.sql.GetLiveStreams( filmui )

	def GetChannels( self, channelui ):
		if self.sql is not None:
			self.sql.GetChannels( channelui )

	def GetInitials( self, channelid, initialui ):
		if self.sql is not None:
			self.sql.GetInitials( channelid, initialui )

	def GetShows( self, channelid, initial, showui ):
		if self.sql is not None:
			self.sql.GetShows( channelid, initial, showui )

	def GetFilms( self, showid, filmui ):
		if self.sql is not None:
			self.sql.GetFilms( showid, filmui )

"""
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
		self.sql. if self.sql is not None
"""