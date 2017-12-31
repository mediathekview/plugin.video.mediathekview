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
			self.db = StoreSQLite( id, logger.getNewLogger( 'StoreMySQL' ), notifier, self.settings )
		elif settings.type == '1':
			self.logger.info( 'Database driver: External (mysql)' )
			self.db = StoreSQLite( id, logger.getNewLogger( 'StoreMySQL' ), notifier, self.settings )
		else:
			self.logger.warn( 'Unknown Database driver selected' )
			self.db = None

	def __del__( self ):
		if self.db is not None:
			del self.db
			self.db = None

	def Init( self, reset = False ):
		if self.db is not None:
			self.db.Init( reset )

	def Exit( self ):
		if self.db is not None:
			self.db.Exit()

	def Search( self, search, filmui ):
		if self.db is not None:
			self.db.Search( search, filmui )

	def SearchFull( self, search, filmui ):
		if self.db is not None:
			self.db.SearchFull( search, filmui )

	def GetRecents( self, filmui ):
		if self.db is not None:
			self.db.GetRecents( filmui )

	def GetLiveStreams( self, filmui ):
		if self.db is not None:
			self.db.GetLiveStreams( filmui )

	def GetChannels( self, channelui ):
		if self.db is not None:
			self.db.GetChannels( channelui )

	def GetInitials( self, channelid, initialui ):
		if self.db is not None:
			self.db.GetInitials( channelid, initialui )

	def GetShows( self, channelid, initial, showui ):
		if self.db is not None:
			self.db.GetShows( channelid, initial, showui )

	def GetFilms( self, showid, filmui ):
		if self.db is not None:
			self.db.GetFilms( showid, filmui )

	def SearchCondition( self, condition, filmui, showshows, showchannels ):
		if self.db is not None:
			self.db.SearchCondition( condition, filmui, showshows, showchannels )

	def GetStatus( self ):
		if self.db is not None:
			return self.db.GetStatus()
		else:
			return {
				'modified': int( time.time() ),
				'status': 'UNINIT',
				'lastupdate': 0,
				'add_chn': 0,
				'add_shw': 0,
				'add_mov': 0,
				'del_chn': 0,
				'del_shw': 0,
				'del_mov': 0,
				'tot_chn': 0,
				'tot_shw': 0,
				'tot_mov': 0,
				'description': ''
			}

	def UpdateStatus( self, status = None, description = None, lastupdate = None, add_chn = None, add_shw = None, add_mov = None, del_chn = None, del_shw = None, del_mov = None, tot_chn = None, tot_shw = None, tot_mov = None ):
		if self.db is not None:
			self.db.UpdateStatus( status, description, lastupdate, add_chn, add_shw, add_mov, del_chn, del_shw, del_mov, tot_chn, tot_shw, tot_mov )

	def SupportsUpdate( self ):
		if self.db is not None:
			return self.db.SupportsUpdate()
		return False

	def ftInit( self ):
		if self.db is not None:
			self.db.ftInit()

	def ftUpdateStart( self ):
		if self.db is not None:
			return self.db.ftUpdateStart()
		return ( 0, 0, 0, )

	def ftUpdateEnd( self, aborted ):
		if self.db is not None:
			return self.db.ftUpdateEnd( aborted )
		return ( 0, 0, 0, 0, 0, 0, )

	def ftInsertFilm( self, film ):
		if self.db is not None:
			return self.db.ftInsertFilm( film )
		return ( 0, 0, 0, 0, )
