# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcplugin, xbmcgui

from classes.film import Film
from classes.settings import Settings

# -- Classes ------------------------------------------------
class FilmUI( Film ):
	def __init__( self, handle, sortmethods = [ xbmcplugin.SORT_METHOD_TITLE, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_DURATION, xbmcplugin.SORT_METHOD_SIZE ] ):
		self.handle			= handle
		self.settings		= Settings( handle )
		self.sortmethods	= sortmethods
		self.showshows		= False
		self.showchannels	= False

	def Begin( self, showshows, showchannels ):
		self.showshows		= showshows
		self.showchannels	= showchannels
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, alttitle = None ):
		# get the best url
		videourl = self.url_video_hd if ( self.url_video_hd != "" and self.settings.preferhd ) else self.url_video if self.url_video != "" else self.url_video_sd
		videohds = " (HD)" if ( self.url_video_hd != "" and self.settings.preferhd ) else ""
		# exit if no url supplied
		if videourl == "":
			return

		if alttitle is not None:
			resultingtitle = alttitle
		else:
			if self.showshows:
				resultingtitle = self.show + ': ' + self.title
			else:
				resultingtitle = self.title
			if self.showchannels:
				resultingtitle += ' [' + self.channel + ']'

		infoLabels = {
			'title' : resultingtitle + videohds,
			'sorttitle' : resultingtitle,
			'tvshowtitle' : self.show,
			'plot' : self.description
		}

		if self.size > 0:
			infoLabels['size'] = self.size * 1024 * 1024

		if self.seconds > 0:
			infoLabels['duration'] = self.seconds

		if self.aired is not None:
			airedstring = '%s' % self.aired
			infoLabels['date']		= airedstring[8:10] + '-' + airedstring[5:7] + '-' + airedstring[:4]
			infoLabels['aired']		= airedstring
			infoLabels['dateadded']	= airedstring
			
		li = xbmcgui.ListItem( resultingtitle, self.description )
		li.setInfo( type = 'video', infoLabels = infoLabels )
		li.setProperty( 'IsPlayable', 'true' )

		xbmcplugin.addDirectoryItem(
			handle	= self.handle,
			url		= videourl,
			listitem = li,
			isFolder = False
		)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle )
