# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcaddon, xbmcplugin

from de.yeasoft.kodi.KodiUI import KodiUI

# -- Classes ------------------------------------------------
class Notifier( KodiUI ):
	def __init__( self, id ):
		self.language		= xbmcaddon.Addon( id = id ).getLocalizedString

	def ShowDatabaseError( self, err ):
		self.ShowError( self.language( 30951 ), '{}'.format( err ) )