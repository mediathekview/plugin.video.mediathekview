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
		self.db			= Store( self.addon_id, self.getNewLogger( 'Store' ), Notifier(), self.settings )
		self.monitor	= MediathekViewMonitor( self )

	def __del__( self ):
		del self.monitor
		del self.db

	def Init( self ):
		self.info( 'Startup' )
		self.db.Init()

	def Run( self ):
		while not self.monitor.abortRequested():
			# Sleep/wait for abort for 60 seconds
			if self.db.SupportsUpdate():
				status = self.db.GetStatus()
				if status['status'] != "UNINIT":
					if int( time.time() ) - status['lastupdate'] > self.settings.updinterval:
						updater = MediathekViewUpdater( self.addon_id, self.getNewLogger( 'MediathekViewUpdater' ), Notifier(), self.settings )
						if updater.IsEnabled():
							updater.Update()
						del updater
			if self.monitor.waitForAbort( 60 ):
				# Abort was requested while waiting. We should exit
				break			

	def Exit( self ):
		self.info( 'Shutdown' )
		self.db.Exit()

	def ReloadSettings( self ):
		pass

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	service = MediathekViewService()
	service.Init()
	service.Run()
	service.Exit()
	del service
