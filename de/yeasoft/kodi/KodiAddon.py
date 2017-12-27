# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import sys, urllib
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs

from de.yeasoft.kodi.KodiLogger import KodiLogger

# -- Classes ------------------------------------------------
class KodiAddon( KodiLogger ):

	def __init__( self, id ):
		self.addon			= xbmcaddon.Addon( id = id )
		self.base_url		= sys.argv[0]
		self.addon_handle	= int( sys.argv[1] )
		self.addon_id		= self.addon.getAddonInfo( 'id' )
		self.icon			= self.addon.getAddonInfo( 'icon' )
		self.fanart			= self.addon.getAddonInfo( 'fanart' )
		self.version		= self.addon.getAddonInfo( 'version' )
		self.path			= self.addon.getAddonInfo( 'path' )
		self.language		= self.addon.getLocalizedString
		KodiLogger.__init__( self, self.addon_id, self.version )

	def getSetting( self, id ):
		return xbmcplugin.getSetting( self.addon_handle, id )

	def build_url( self, query ):
		return self.base_url + '?' + urllib.urlencode( query )

