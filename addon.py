# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import sys,urlparse,datetime
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

from de.yeasoft.kodi.KodiAddon import KodiPlugin

from classes.store import Store
from classes.notifier import Notifier
from classes.settings import Settings
from classes.filmui import FilmUI
from classes.channelui import ChannelUI
from classes.initialui import InitialUI
from classes.showui import ShowUI
from classes.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------
class MediathekView( KodiPlugin ):

	def __init__( self ):
		super( MediathekView, self ).__init__()
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.db			= Store( self.getNewLogger( 'Store' ), self.notifier, self.settings )

	def __del__( self ):
		del self.db

	def showMainMenu( self ):
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
		# Database Information
		self.addFolderItem( 30907, { 'mode': "main-dbinfo" } )
		xbmcplugin.endOfDirectory( self.addon_handle )

	def showSearch( self ):
		# searchText = unicode( self.notifier.GetEnteredText( '', self.language( 30901 ) ).decode( 'UTF-8' ) )
		searchText = self.notifier.GetEnteredText( '', self.language( 30901 ) )
		if len( searchText ) > 2:
			self.db.Search( searchText, FilmUI( self.addon_handle ) )
		else:
			self.showMainMenu()

	def showSearchAll( self ):
		# searchText = unicode( self.notifier.GetEnteredText( '', self.language( 30902 ) ).decode( 'UTF-8' ) )
		searchText = self.notifier.GetEnteredText( '', self.language( 30902 ) )
		if len( searchText ) > 2:
			self.db.SearchFull( searchText, FilmUI( self.addon_handle ) )
		else:
			self.showMainMenu()

	def showDbInfo( self ):
		info = self.db.GetStatus()
		heading = self.language( 30907 )
		infostr = self.language( {
			'NONE': 30941,
			'UNINIT': 30942,
			'IDLE': 30943,
			'UPDATING': 30944,
			'ABORTED': 30945
		}.get( info['status'], 30941 ) )
		infostr = self.language( 30965 ) % infostr
		totinfo = self.language( 30971 ) % (
			info['tot_chn'],
			info['tot_shw'],
			info['tot_mov']
		)
		updatetype = self.language( 30972 if info['fullupdate'] > 0 else 30973 )
		if info['status'] == 'UPDATING' and info['filmupdate'] > 0:
			updinfo = self.language( 30967 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['status'] == 'UPDATING':
			updinfo = self.language( 30968 ) % (
				updatetype,
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['lastupdate'] > 0 and info['filmupdate'] > 0:
			updinfo = self.language( 30969 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		elif info['lastupdate'] > 0:
			updinfo = self.language( 30970 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		else:
			updinfo = self.language( 30966 )

		xbmcgui.Dialog().textviewer(
			heading,
			infostr + '\n\n' +
			totinfo + '\n\n' +
			updinfo
		)
		self.showMainMenu()

	def Init( self ):
		self.args = urlparse.parse_qs( sys.argv[2][1:] )
		self.db.Init()
		if self.settings.HandleFirstRun():
			xbmcgui.Dialog().textviewer(
				self.language( 30961 ),
				self.language( 30962 )
			)
		if MediathekViewUpdater( self.getNewLogger( 'Updater' ), self.notifier, self.settings ).PrerequisitesMissing():
			self.setSetting( 'updenabled', 'false' )
			self.settings.Reload()
			xbmcgui.Dialog().textviewer(
				self.language( 30963 ),
				self.language( 30964 )
			)

	def Do( self ):
		mode = self.args.get( 'mode', None )
		if mode is None:
			self.showMainMenu()
		elif mode[0] == 'main-search':
			self.showSearch()
		elif mode[0] == 'main-searchall':
			self.showSearchAll()
		elif mode[0] == 'main-livestreams':
			self.db.GetLiveStreams( FilmUI( self.addon_handle, [ xbmcplugin.SORT_METHOD_LABEL ] ) )
		elif mode[0] == 'main-recent':
			self.db.GetRecents( FilmUI( self.addon_handle ) )
		elif mode[0] == 'main-channels':
			self.db.GetChannels( ChannelUI( self.addon_handle ) )
		elif mode[0] == 'main-dbinfo':
			self.showDbInfo()
		elif mode[0] == 'channel':
			channel = self.args.get( 'channel', [0] )
			self.db.GetInitials( channel[0], InitialUI( self.addon_handle ) )
		elif mode[0] == 'channel-initial':
			channel = self.args.get( 'channel', [0] )
			initial = self.args.get( 'initial', [None] )
			self.db.GetShows( channel[0], initial[0], ShowUI( self.addon_handle ) )
		elif mode[0] == 'show':
			show = self.args.get( 'show', [0] )
			self.db.GetFilms( show[0], FilmUI( self.addon_handle ) )

	def Exit( self ):
		self.db.Exit()

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	addon = MediathekView()
	addon.Init()
	addon.Do()
	addon.Exit()
	del addon
