# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import sys,urlparse
import xbmc,xbmcplugin,xbmcgui

from de.yeasoft.kodi.KodiLogger import KodiLogger
from de.yeasoft.kodi.KodiAddon import KodiAddon

from classes.storemysql import StoreMySQL
# from classes.storesqlite import StoreSQLite
from classes.notifier import Notifier
from classes.settings import Settings
from classes.filmui import FilmUI
from classes.channelui import ChannelUI
from classes.initialui import InitialUI
from classes.showui import ShowUI
# from classes.updater import MediathekViewUpdater

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.mediathekview'

# -- Classes ------------------------------------------------
class MediathekView( KodiAddon ):

	def __init__( self, id  ):
		super( MediathekView, self ).__init__( id )
		self.settings	= Settings( int( sys.argv[1] ) )
		self.db			= StoreMySQL( id, self.getNewLogger( 'StoreMySQL' ), Notifier( id ), self.settings )
#		self.dbs		= StoreSQLite( id, self.getNewLogger( 'StoreSQLite' ), Notifier( id ), self.settings )

	def __del__( self ):
#		del self.dbs
		del self.db

	def addChannelList( self ):
		self.db.GetChannels( ChannelUI( self.addon_handle ) )

	def addInitialListInChannel( self, channelid ):
		self.db.GetInitials( channelid, InitialUI( self.addon_handle ) )

	def addFilmlistInChannelAndCategory( self, showid ):
		self.db.GetFilms( showid, FilmUI( self.addon_handle ) )

	def addShowListInChannelAndInitial( self, channelid, initial, count ):
		self.db.GetShows( channelid, initial, ShowUI( self.addon_handle ) )

	def addLiveStreams( self ):
		self.db.GetLiveStreams( FilmUI( self.addon_handle, [ xbmcplugin.SORT_METHOD_LABEL ] ) )

	def addRecentlyAdded( self ):
		self.db.GetRecents( FilmUI( self.addon_handle ) )

	def addSearch( self ):
		keyboard = xbmc.Keyboard( '' )
		keyboard.doModal()
		if keyboard.isConfirmed():
			searchText = unicode( keyboard.getText().decode( 'UTF-8' ) )
			if len( searchText ) > 2:
				self.db.Search( searchText, FilmUI( self.addon_handle ) )
			else:
				xbmc.executebuiltin( "Action(PreviousMenu)" )
		else:
			xbmc.executebuiltin( "Action(PreviousMenu)" )

	def addSearchAll( self ):
		keyboard = xbmc.Keyboard( '' )
		keyboard.doModal()
		if keyboard.isConfirmed():
			searchText = unicode( keyboard.getText().decode( 'UTF-8' ) )
			if len( searchText ) > 2:
				self.db.SearchFull( searchText, FilmUI( self.addon_handle ) )
			else:
				xbmc.executebuiltin( "Action(PreviousMenu)" )
		else:
			xbmc.executebuiltin( "Action(PreviousMenu)" )

	def addFolderItem( self, strid, params ):
		li = xbmcgui.ListItem( self.language( strid ) )
		xbmcplugin.addDirectoryItem(
			handle		= self.addon_handle,
			url			= self.build_url( params ),
			listitem	= li,
			isFolder	= True
		)

	def addMainMenu( self ):
		# search
		self.addFolderItem( 30901, { 'mode': "main-search" } )
		# search all
		self.addFolderItem( 30902, { 'mode': "main-searchall" } )
		# livestreams
		self.addFolderItem( 30903, { 'mode': "main-livestreams" } )
		# recently added
		self.addFolderItem( 30904, { 'mode': "main-recent" } )
		# Browse by Show in all Channels
		self.addFolderItem( 30905, { 'mode': "channel", 'channel': 0 } )
		# Browse Shows by Channel
		self.addFolderItem( 30906, { 'mode': "main-channels" } )
		xbmcplugin.endOfDirectory( self.addon_handle )

	def Init( self ):
		self.args			= urlparse.parse_qs( sys.argv[2][1:] )
		self.db.Init()
#		self.dbs.Init()
#		x = MediathekViewUpdater( ADDON_ID, self.getNewLogger( 'Updater' ), Notifier( ADDON_ID ), self.settings )
#		x.GetNewestList()
#		x.Update()
#		del x

	def Do( self ):
		mode = self.args.get( 'mode', None )
		if mode is None:
			self.addMainMenu()
		elif mode[0] == 'main-search':
			self.addSearch()
		elif mode[0] == 'main-searchall':
			self.addSearchAll()
		elif mode[0] == 'main-livestreams':
			self.addLiveStreams()
		elif mode[0] == 'main-recent':
			self.addRecentlyAdded()
		elif mode[0] == 'main-channels':
			self.addChannelList()
		elif mode[0] == 'channel':
			channel = self.args.get( 'channel', [0] )
			self.addInitialListInChannel( channel[0] )
		elif mode[0] == 'channel-initial':
			channel = self.args.get( 'channel', [0] )
			letter = self.args.get( 'letter', [None] )
			count = self.args.get( 'count', [0] )
			self.addShowListInChannelAndInitial( channel[0], letter[0], count[0] )
		elif mode[0] == 'show':
			show = self.args.get( 'show', [0] )
			self.addFilmlistInChannelAndCategory( show[0] )

	def Exit( self ):
#		self.dbs.Exit()
		self.db.Exit()

# -- Main Code ----------------------------------------------
addon = MediathekView( ADDON_ID )
addon.Init()
addon.Do()
addon.Exit()
del addon
