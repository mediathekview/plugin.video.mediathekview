# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import os,sys,urlparse,datetime,string,urllib
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

from de.yeasoft.kodi.KodiAddon import KodiPlugin
from de.yeasoft.kodi.KodiUI import KodiBGDialog

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
			self.db.Search( searchText, FilmUI( self ) )
		else:
			self.showMainMenu()

	def showSearchAll( self ):
		# searchText = unicode( self.notifier.GetEnteredText( '', self.language( 30902 ) ).decode( 'UTF-8' ) )
		searchText = self.notifier.GetEnteredText( '', self.language( 30902 ) )
		if len( searchText ) > 2:
			self.db.SearchFull( searchText, FilmUI( self ) )
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

	def doDownloadFilm( self, filmid ):
		if self.settings.downloadpath:
			film = self.db.RetrieveFilmInfo( filmid )
			if film is None:
				return
			# get the best url
			videourl	= film.url_video_hd if ( film.url_video_hd and self.settings.preferhd ) else film.url_video if film.url_video else film.url_video_sd
			dirname		= self._cleanup_filename( film.show )[:64]
			filestem	= self._cleanup_filename( film.title )[:64]
			extension	= os.path.splitext( videourl )[1]
			if not extension:
				extension = u'.mp4'
			if not filestem:
				filestem = u'Film-{}'.format( film.id )
			if not dirname:
				dirname = filestem

			# this is our download directory
			dirname = os.path.join( self.settings.downloadpath, dirname )
			movname = os.path.join( dirname, filestem ) + extension
			srtname = os.path.join( dirname, filestem ) + u'.srt'
			ttmname = os.path.join( dirname, filestem ) + u'.ttml'
			nfoname = os.path.join( dirname, filestem ) + u'.nfo'

			if os.path.isfile( movname ):
				self.notifier.ShowWarning( self.language( 30977 ), videourl )
				return

			# create dir if it does not exist
			if not os.path.isdir( dirname ):
				try:
					os.mkdir( dirname )
				except OSError as err:
					self.notifier.ShowError( self.language( 30952 ), self.language( 30959 ).format( err ) )
					return

			# download video
			bgd = KodiBGDialog()
			bgd.Create( self.language( 30974 ), filestem + extension )
			try:
				bgd.Update( 0 )
				result = urllib.urlretrieve( videourl, filename = movname, reporthook = bgd.UrlRetrieveHook )
				bgd.Close()
				if result is not None:
					self.notifier.ShowNotification( self.language( 30960 ), self.language( 30976 ).format( videourl ) )
			except IOError as err:
				bgd.Close()
				self.error( 'Failure downloading {}', videourl )
				self.notifier.ShowError( self.language( 30952 ), self.language( 30975 ).format( videourl, err ) )

			# download subtitles
			if film.url_sub:
				bgd = KodiBGDialog()
				bgd.Create( self.language( 30978 ), filestem + u'.ttml' )
				try:
					bgd.Update( 0 )
					result = urllib.urlretrieve( film.url_sub, filename = os.path.join( dirname, filestem ) + extension, reporthook = bgd.UrlRetrieveHook )
					bgd.Close()
					# TODO: Convert substitles to srt format.
				except IOError as err:
					bgd.Close()
					self.error( 'Failure downloading {}', film.url_sub )

			# create NFO files
			try:
				file = open( os.path.join( dirname, 'tvshow.nfo' ), 'w' )
				file.write( '<tvshow>\n' )
				file.write( '\t<title>{}</title>\n'.format( film.show ) )
				file.write( '\t<studio>{}</studio>\n'.format( film.channel ) )
				file.write( '</tvshow>\n' )
				file.close()
			except IOError as err:
				self.error( 'Failure creating show NFO file for {}', videourl )


			try:
				file = open( nfoname, 'w' )
				file.write( '<episodedetails>\n' )
				file.write( '\t<title>{}</title>\n'.format( film.title ) )
				file.write( '\t<showtitle>{}</showtitle>\n'.format( film.show ) )
				file.write( '\t<plot>{}</plot>\n'.format( film.description ) )
				file.write( '\t<aired>{}</aired>\n'.format( film.aired ) )
				if film.seconds > 60:
					file.write( '\t<runtime>{}</runtime>\n'.format( int( film.seconds / 60 ) ) )
				file.write( '\t<studio>{}</studio\n'.format( film.channel ) )
				file.write( '</episodedetails>\n' )
				file.close()
			except IOError as err:
				self.error( 'Failure creating NFO file for {}', videourl )

		else:
			self.notifier.ShowError( self.language( 30952 ), self.language( 30958 ) )

	def doEnqueueFilm( self, filmid ):
		self.info( 'Enqueue {}', filmid )

	def _cleanup_filename( self, val ):
		cset = string.letters + string.digits + u' _-#äöüÄÖÜßáàâéèêíìîóòôúùûÁÀÉÈÍÌÓÒÚÙçÇœ'
		search = ''.join( [ c for c in val if c in cset ] )
		return search.strip()

	def Do( self ):
		mode = self.args.get( 'mode', None )
		if mode is None:
			self.showMainMenu()
		elif mode[0] == 'main-search':
			self.showSearch()
		elif mode[0] == 'main-searchall':
			self.showSearchAll()
		elif mode[0] == 'main-livestreams':
			self.db.GetLiveStreams( FilmUI( self, [ xbmcplugin.SORT_METHOD_LABEL ] ) )
		elif mode[0] == 'main-recent':
			self.db.GetRecents( FilmUI( self ) )
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
			self.db.GetFilms( show[0], FilmUI( self ) )
		elif mode[0] == 'download':
			self.doDownloadFilm( self.args.get( 'id', [0] )[0] )
		elif mode[0] == 'enqueue':
			self.doEnqueueFilm( self.args.get( 'id', [0] )[0] )

	def Exit( self ):
		self.db.Exit()

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	addon = MediathekView()
	addon.Init()
	addon.Do()
	addon.Exit()
	del addon
