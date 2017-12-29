# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcaddon

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.mediathekview'

# -- Classes ------------------------------------------------
class Settings( object ):
	def __init__( self ):
		addon = xbmcaddon.Addon()
		self.preferhd		= addon.getSetting( 'quality' ) == 'true'
		self.nofuture		= addon.getSetting( 'nofuture' ) == 'true'
		self.minlength		= int( float( addon.getSetting( 'minlength' ) ) ) * 60
		self.groupshows		= addon.getSetting( 'groupshows' ) == 'true'
		self.type			= addon.getSetting( 'dbtype' )
		self.host			= addon.getSetting( 'dbhost' )
		self.user			= addon.getSetting( 'dbuser' )
		self.password		= addon.getSetting( 'dbpass' )
		self.database		= addon.getSetting( 'dbdata' )
		self.updinterval	= int( float( addon.getSetting( 'updinterval' ) ) ) * 3600
