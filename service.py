# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import time
import xbmc

from de.yeasoft.kodi.KodiAddon import KodiService

from classes.store import Store
from classes.notifier import Notifier
from classes.settings import Settings
from classes.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------
class MediathekViewMonitor( xbmc.Monitor ):
	def __init__( self, service ):
		super( MediathekViewMonitor, self ).__init__()
		self.service	= service
		self.logger		= service.getNewLogger( 'Monitor' )
		self.logger.info( 'Startup' )

	def __del__( self ):
		self.logger.info( 'Shutdown' )

	def onSettingsChanged( self ):
		self.service.ReloadSettings()

class MediathekViewService( KodiService ):
	def __init__( self ):
		super( MediathekViewService, self ).__init__()
		self.setTopic( 'Service' )
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.monitor	= MediathekViewMonitor( self )
		self.updater	= MediathekViewUpdater( self.getNewLogger( 'MediathekViewUpdater' ), self.notifier, self.settings, self.monitor )

	def __del__( self ):
		del self.updater
		del self.monitor
		del self.notifier
		del self.settings

	def Init( self ):
		self.info( 'Startup' )
		self.updater.Init()

	def Run( self ):
		self.info( 'Starting up...' )
		while not self.monitor.abortRequested():
			updateop = self.updater.GetCurrentUpdateOperation()
			if updateop == 1:
				# full update
				self.info( 'Initiating full update...' )
				self.updater.Update( True )
			elif updateop == 2:
				# differential update
				self.info( 'Initiating differential update...' )
				self.updater.Update( False )
			# Sleep/wait for abort for 60 seconds
			if self.monitor.waitForAbort( 60 ):
				# Abort was requested while waiting. We should exit
				break			
		self.info( 'Exiting...' )

	def Exit( self ):
		self.info( 'Shutdown' )
		self.updater.Exit()

	def ReloadSettings( self ):
		# TODO: support online reconfiguration
		pass

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	service = MediathekViewService()
	service.Init()
	service.Run()
	service.Exit()
	del service
