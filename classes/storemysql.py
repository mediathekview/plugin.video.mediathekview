# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import mysql.connector

# -- Classes ------------------------------------------------
class StoreMySQL( object ):
	def __init__( self, id, logger, notifier, settings ):
		self.conn		= None
		self.logger		= logger
		self.notifier	= notifier
		self.settings	= settings
		# useful query fragments
		self.sql_query_films	= "SELECT title,category,channel,description,TIME_TO_SEC(duration) AS seconds,size,aired,url_video,url_video_sd,url_video_hd FROM film LEFT JOIN category ON category.id=film.categoryid LEFT JOIN channel ON channel.id=film.channelid"
		self.sql_cond_nofuture	= " AND ( ( aired IS NULL ) OR ( TIMESTAMPDIFF(HOUR,aired,CURRENT_TIMESTAMP()) > 0 ) )" if settings.nofuture else ""
		self.sql_cond_minlength	= " AND ( ( duration IS NULL ) OR ( TIME_TO_SEC(duration) >= %d ) )" % settings.minlength if settings.minlength > 0 else ""

	def Init( self ):
		try:
			self.conn		= mysql.connector.connect(
				host		= self.settings.host,
				user		= self.settings.user,
				password	= self.settings.password,
				database	= self.settings.database
			)
		except mysql.connector.Error as err:
			self.conn		= None
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def Exit( self ):
		if self.conn is not None:
			self.conn.close()

	def Search( self, search, filmui ):
		self.SearchCondition( '( title LIKE "%%%s%%")' % search, filmui, True, True )

	def SearchFull( self, search, filmui ):
		self.SearchCondition( '( ( title LIKE "%%%s%%") OR ( description LIKE "%%%s%%") )' % ( search, search ), filmui, True, True )

	def GetRecents( self, filmui ):
		self.SearchCondition( '( TIMESTAMPDIFF(HOUR,aired,CURRENT_TIMESTAMP()) < 24 )', filmui, True, True )

	def GetLiveStreams( self, filmui ):
		self.SearchCondition( '( category.search="LIVESTREAM" )', filmui, False, False )

	def GetChannels( self, channelui ):
		if self.conn is None:
			return
		try:
			self.logger.info( 'MySQL Query: {}', "SELECT id,channel FROM channel" )
			cursor = self.conn.cursor()
			cursor.execute( 'SELECT id,channel FROM channel' )
			channelui.Begin()
			for ( channelui.id, channelui.channel ) in cursor:
				channelui.Add()
			channelui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetInitials( self, channelid, initialui ):
		if self.conn is None:
			return
		try:
			condition = 'WHERE ( channelid=' + str( channelid ) + ' ) ' if channelid != '0' else ''
			self.logger.info( 'MySQL Query: {}', 
				'SELECT LEFT(search,1) AS letter,COUNT(*) AS count FROM category ' +
				condition +
				'GROUP BY LEFT(search,1)'
			)
			cursor = self.conn.cursor()
			cursor.execute(
				'SELECT LEFT(search,1) AS letter,COUNT(*) AS count FROM category ' +
				condition +
				'GROUP BY LEFT(search,1)'
			)
			initialui.Begin( channelid )
			for ( initialui.initial, initialui.count ) in cursor:
				initialui.Add()
			initialui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetShows( self, channelid, initial, showui ):
		if self.conn is None:
			return
		try:
			if channelid == '0' and self.settings.groupshows:
				query = 'SELECT GROUP_CONCAT(category.id),GROUP_CONCAT(channelid),category,GROUP_CONCAT(channel) FROM category LEFT JOIN channel ON channel.id=category.channelid WHERE ( category LIKE "%s%%" ) GROUP BY category' % initial
			elif channelid == '0':
				query = 'SELECT category.id,category.channelid,category.category,channel.channel FROM category LEFT JOIN channel ON channel.id=category.channelid WHERE ( category LIKE "%s%%" )' % initial
			else:
				query = 'SELECT category.id,category.channelid,category.category,channel.channel FROM category LEFT JOIN channel ON channel.id=category.channelid WHERE ( channelid=%s ) AND ( category LIKE "%s%%" )' % ( channelid, initial )
			self.logger.info( 'MySQL Query: {}', query )
			cursor = self.conn.cursor()
			cursor.execute( query )
			showui.Begin( channelid )
			for ( showui.id, showui.channelid, showui.show, showui.channel ) in cursor:
				showui.Add()
			showui.End()
			cursor.close()
		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )

	def GetFilms( self, showid, filmui ):
		if self.conn is None:
			return
		if showid.find( ',' ) == -1:
			# only one channel id
			condition = '( categoryid=%s )' % showid
			showchannels = False
		else:
			# multiple channel ids
			condition = '( categoryid IN ( %s ) )' % showid
			showchannels = True
		self.SearchCondition( condition, filmui, False, showchannels )

	def SearchCondition( self, condition, filmui, showshows, showchannels ):
		if self.conn is None:
			return
		try:
			self.logger.info( 'MySQL Query: {}', 
				self.sql_query_films +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength
			)
			cursor = self.conn.cursor()
			cursor.execute(
				self.sql_query_films +
				' WHERE ' +
				condition +
				self.sql_cond_nofuture +
				self.sql_cond_minlength
			)
			filmui.Begin( showshows, showchannels )
			for ( filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd ) in cursor:
				filmui.Add()
			filmui.End()
			cursor.close()

		except mysql.connector.Error as err:
			self.logger.error( 'Database error: {}', err )
			self.notifier.ShowDatabaseError( err )
