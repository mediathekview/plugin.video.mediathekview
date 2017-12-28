# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import os, stat, string, sqlite3, time
import xbmc

# -- Classes ------------------------------------------------
class StoreSQLite( object ):
	def __init__( self, id, logger, notifier, settings ):
		self.conn		= None
		self.logger		= logger
		self.dbfile		= os.path.join( xbmc.translatePath( "special://masterprofile" ), 'addon_data', id, 'filmliste01.db' )

	def Init( self, reset = False ):
		self.logger.info( 'Using SQLite version {}, pathon library sqlite3 version {}', sqlite3.sqlite_version, sqlite3.version )
		if reset == True:
			self.logger.info( '===== RESET: Database will be deleted and regenerated =====' )
			self._file_remove( self.dbfile )
			self.conn = sqlite3.connect( self.dbfile )
			self.Reset()
		else:
			self.conn = sqlite3.connect( self.dbfile )

	def Exit( self ):
		if self.conn is not None:
			self.conn.close()
			self.conn	= None

	def ftInit( self ):
		self.ft_channel = None
		self.ft_channelid = None
		self.ft_show = None
		self.ft_showid = None

	def ftInsertFilm( self, film ):
		cursor = self.conn.cursor()
		newchn = False
		inschn = 0
		insshw = 0
		insmov = 0

		# handle channel
		if self.ft_channel != film['channel']:
			# process changed channel
			newchn = True
			cursor.execute( 'SELECT `id`,`touched` FROM `channel` WHERE channel.channel=?', ( film['channel'], ) )
			r = cursor.fetchall()
			if len( r ) > 0:
				# get the channel data
				self.ft_channel = film['channel']
				self.ft_channelid = r[0][0]
				if r[0][1] == 0:
					# updated touched
					cursor.execute( 'UPDATE `channel` SET `touched`=1 WHERE ( channel.id=? )', ( self.ft_channelid, ) )
					self.conn.commit()
			else:
				# insert the new channel
				inschn = 1
				cursor.execute( 'INSERT INTO `channel` ( `dtCreated`,`channel` ) VALUES ( ?,? )', ( int( time.time() ), film['channel'] ) )
				self.ft_channel = film['channel']
				self.ft_channelid = cursor.lastrowid
				self.conn.commit()

		# handle show
		if newchn or self.ft_show != film['show']:
			# process changes show
			cursor.execute( 'SELECT `id`,`touched` FROM `show` WHERE ( show.channelid=? ) AND ( show.show=? )', ( self.ft_channelid, film['show'] ) )
			r = cursor.fetchall()
			if len( r ) > 0:
				# get the show data
				self.ft_show = film['show']
				self.ft_showid = r[0][0]
				if r[0][1] == 0:
					# updated touched
					cursor.execute( 'UPDATE `show` SET `touched`=1 WHERE ( show.id=? )', ( self.ft_showid, ) )
					self.conn.commit()
			else:
				# insert the new show
				insshw = 1
				cursor.execute(
					"""
					INSERT INTO `show` (
						`dtCreated`,
						`channelid`,
						`show`,
						`search`
					)
					VALUES (
						?,
						?,
						?,
						?
					)
					""", (
						int( time.time() ),
						self.ft_channelid, film['show'],
						self._make_search( film['show'] )
					)
				)
				self.ft_show = film['show']
				self.ft_showid = cursor.lastrowid
				self.conn.commit()

		# check if the movie is there
		cursor.execute( """
			SELECT		`id`,
						`touched`
			FROM		`film`
			WHERE		( film.channelid = ? )
						AND
						( film.showid = ? )
						AND
						( film.url_video = ? )
		""", ( self.ft_channelid, self.ft_showid, film['url_video'] ) )
		r = cursor.fetchall()
		if len( r ) > 0:
			# film found
			filmid = r[0][0]
			if r[0][1] == 0:
				# update touched
				cursor.execute( 'UPDATE `film` SET `touched`=1 WHERE ( film.id=? )', ( filmid, ) )
				self.conn.commit()
		else:
			# insert the new film
			insmov = 1
			cursor.execute(
				"""
				INSERT INTO `film` (
					`dtCreated`,
					`channelid`,
					`showid`,
					`title`,
					`search`,
					`aired`,
					`duration`,
					`size`,
					`description`,
					`website`,
					`url_sub`,
					`url_video`,
					`url_video_sd`,
					`url_video_hd`
				)
				VALUES (
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?,
					?
				)
				""", (
					int( time.time() ),
					self.ft_channelid,
					self.ft_showid,
					film['title'],
					self._make_search( film['title'] ),
					film['airedepoch'],
					self._make_duration( film['duration'] ),
					film['size'],
					film['description'],
					film['website'],
					film['url_sub'],
					film['url_video'],
					film['url_video_sd'],
					film['url_video_hd']
				)
			)
			filmid = cursor.lastrowid
			self.conn.commit()
		cursor.close()
		return ( filmid, inschn, insshw, insmov )

	def ftUpdateStart( self ):
		cursor = self.conn.cursor()
		cursor.executescript( """
			UPDATE	`channel`
			SET		`touched` = 0;

			UPDATE	`show`
			SET		`touched` = 0;

			UPDATE	`film`
			SET		`touched` = 0;
		""" )
		cursor.close()
		self.conn.commit()

	def ftUpdateEnd( self ):
		cursor = self.conn.cursor()
		cursor.execute( 'SELECT COUNT(*) FROM `channel` WHERE ( touched = 0 )' )
		r1 = cursor.fetchone()
		cursor.execute( 'SELECT COUNT(*) FROM `show` WHERE ( touched = 0 )' )
		r2 = cursor.fetchone()
		cursor.execute( 'SELECT COUNT(*) FROM `film` WHERE ( touched = 0 )' )
		r3 = cursor.fetchone()
		cursor.execute( 'DELETE FROM `show` WHERE ( show.touched = 0 ) AND ( ( SELECT SUM( film.touched ) FROM `film` WHERE film.showid = show.id ) = 0 )' )
		cursor.execute( 'DELETE FROM `film` WHERE ( touched = 0 )' )
		cursor.close()
		self.conn.commit()
		return ( r1[0], r2[0], r3[0], )

	def Reset( self ):
		self.conn.executescript( """
/*
 Navicat Premium Data Transfer

 Source Server         : Kodi MediathekView
 Source Server Type    : SQLite
 Source Server Version : 3012001
 Source Database       : main

 Target Server Type    : SQLite
 Target Server Version : 3012001
 File Encoding         : utf-8

 Date: 12/27/2017 23:56:51 PM
*/

PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for channel
-- ----------------------------
DROP TABLE IF EXISTS "channel";
CREATE TABLE "channel" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channel" TEXT(255,0) NOT NULL
);

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film";
CREATE TABLE "film" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL,
	 "showid" INTEGER(11,0) NOT NULL,
	 "title" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	 "aired" integer(11,0),
	 "duration" integer(11,0),
	 "size" integer(11,0),
	 "description" TEXT(2048,0),
	 "website" TEXT(384,0),
	 "url_sub" TEXT(384,0),
	 "url_video" TEXT(384,0),
	 "url_video_sd" TEXT(384,0),
	 "url_video_hd" TEXT(384,0),
	CONSTRAINT "FK_FilmShow" FOREIGN KEY ("showid") REFERENCES "show" ("id") ON DELETE CASCADE,
	CONSTRAINT "FK_FilmChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Table structure for show
-- ----------------------------
DROP TABLE IF EXISTS "show";
CREATE TABLE "show" (
	 "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	 "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
	 "touched" integer(1,0) NOT NULL DEFAULT 1,
	 "channelid" INTEGER(11,0) NOT NULL DEFAULT 0,
	 "show" TEXT(255,0) NOT NULL,
	 "search" TEXT(255,0) NOT NULL,
	CONSTRAINT "FK_ShowChannel" FOREIGN KEY ("channelid") REFERENCES "channel" ("id") ON DELETE CASCADE
);

-- ----------------------------
--  Indexes structure for table film
-- ----------------------------
CREATE INDEX "dupecheck" ON film ("channelid", "showid", "url_video");
CREATE INDEX "index_1" ON film ("channelid", "title" COLLATE NOCASE);
CREATE INDEX "index_2" ON film ("showid", "title" COLLATE NOCASE);

-- ----------------------------
--  Indexes structure for table show
-- ----------------------------
CREATE INDEX "category" ON show ("category");
CREATE INDEX "search" ON show ("search");
CREATE INDEX "combined_1" ON show ("channelid", "search");
CREATE INDEX "combined_2" ON show ("channelid", "show");

PRAGMA foreign_keys = true;
		""" )

	def _make_search( self, val ):
		cset = string.letters + string.digits + ' _-#'
		search = ''.join( [ c for c in val if c in cset ] )
		return search.upper().strip()

	def _make_duration( self, val ):
		if val == "00:00:00":
			return None
		elif val is None:
			return None
		x = val.split( ':' )
		if len( x ) != 3:
			return None
		return int( x[0] ) * 3600 + int( x[1] ) * 60 + int( x[2] )

	def _file_exists( self, name ):
		try:
			s = os.stat( name )
			return stat.S_ISREG( s.st_mode )
		except OSError as err:
			return False

	def _file_remove( self, name ):
		if self._file_exists( name ):
			try:
				os.remove( name )
				return True
			except OSError as err:
				self.logger.error( 'Failed to remove {}: error {}', name, err )
		return False

