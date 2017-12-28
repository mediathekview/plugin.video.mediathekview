# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcgui

# -- Classes ------------------------------------------------
class KodiUI( object ):

	def __init__( self ):
		self.bgdialog		= None

	def ShowNotification( self, heading, message, icon = xbmcgui.NOTIFICATION_INFO, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, icon, time, sound )

	def ShowWarning( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_WARNING, time, sound )

	def ShowError( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_ERROR, time, sound )

	def ShowBGDialog( self, heading = None, message = None ):
		if self.bgdialog is None:
			self.bgdialog = xbmcgui.DialogProgressBG()
			self.bgdialog.create( heading, message )
		else:
			self.bgdialog.update( 0, heading, message )

	def UpdateBGDialog( self, percent, heading = None, message = None ):
		if self.bgdialog is not None:
			self.bgdialog.update( percent, heading, message )

	def CloseBGDialog( self ):
		if self.bgdialog is not None:
			self.bgdialog.close()
			del self.bgdialog
			self.bgdialog = None
