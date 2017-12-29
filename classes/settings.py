# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcplugin

# -- Classes ------------------------------------------------
class Settings( object ):
	def __init__( self, handle ):
		self.preferhd		= xbmcplugin.getSetting( handle, 'quality' ) == 'true'
		self.nofuture		= xbmcplugin.getSetting( handle, 'nofuture' ) == 'true'
		self.minlength		= int( float( xbmcplugin.getSetting( handle, 'minlength' ) ) ) * 60
		self.groupshows		= xbmcplugin.getSetting( handle, 'groupshows' ) == 'true'
		self.type			= xbmcplugin.getSetting( handle, 'dbtype' )
		self.host			= xbmcplugin.getSetting( handle, 'dbhost' )
		self.user			= xbmcplugin.getSetting( handle, 'dbuser' )
		self.password		= xbmcplugin.getSetting( handle, 'dbpass' )
		self.database		= xbmcplugin.getSetting( handle, 'dbdata' )
