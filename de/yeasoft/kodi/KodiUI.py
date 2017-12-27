# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcgui

# -- Classes ------------------------------------------------
class KodiUI( object ):

	def __init__( self ):
		pass

	def ShowNotification( self, heading, message, icon = xbmcgui.NOTIFICATION_INFO, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, icon, time, sound )

	def ShowWarning( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_WARNING, time, sound )

	def ShowError( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_ERROR, time, sound )

