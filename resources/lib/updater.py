# -*- coding: utf-8 -*-
"""
The database updater module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
import os
import time
from datetime import datetime
import resources.lib.appContext as appContext
import resources.lib.mvutils as mvutils
from resources.lib.storeMySql import StoreMySQL
from resources.lib.storeSqlite import StoreSQLite
from resources.lib.storeSqliteSetup import StoreSQLiteSetup
from resources.lib.storeMySqlSetup import StoreMySQLSetup
from resources.lib.updateFileDownload import UpdateFileDownload
from resources.lib.updateFileImport import UpdateFileImport



# -- Classes ------------------------------------------------
# pylint: disable=bad-whitespace


class MediathekViewUpdater(object):
    """ The database updator class """

    def __init__(self):
        self.logger = appContext.MVLOGGER.get_new_logger('MediathekViewUpdater')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        self.database = None
        self.error = 0
        self.count = 0
        self.insertCount = 0
        self.updateCount = 0
        self.film = {}

    def init(self):
        """ Initializes the updater """
        if self.database is not None:
            self.exit()
        if self.settings.getDatabaseType() == 0:
            self.logger.info('Database driver: Internal (sqlite)')
            self.database = StoreSQLite()
        elif self.settings.getDatabaseType() == 1:
            self.logger.info('Database driver: External (mysql)')
            self.database = StoreMySQL()
        else:
            self.logger.warn('Unknown Database driver selected')
            self.database = None

    def exit(self):
        """ Resets the updater """
        if self.database is not None:
            self.database.exit()
            del self.database
            self.database = None

    def doUpdate(self):
        """ "Disabled" / "Manual" / "On Start" / "Automatic" / "continuous" """
        databaseStatus = self.database.getDatabaseStatus()
        updateConfig = self.settings.getDatabaseUpateMode()
        tsnow = int(time.time())
        currentDate = datetime.now()
        lastUpdateDatetime = datetime.fromtimestamp(databaseStatus['lastUpdate'])
        ##
        outdated = ((databaseStatus['lastUpdate'] + self.settings.getDatabaseUpdateInvterval()) < tsnow)
        sameDay = (currentDate.day == lastUpdateDatetime.day and 
            currentDate.month == lastUpdateDatetime.month and 
            currentDate.year == lastUpdateDatetime.year)
        ##
        self.logger.info('Last Update {}',datetime.fromtimestamp(databaseStatus['lastUpdate']))
        self.logger.info('Last Full Update {}',datetime.fromtimestamp(databaseStatus['lastFullUpdate']))
        self.logger.info('version {}',databaseStatus['version'])
        self.logger.info('status {}',databaseStatus['status'])
        ##
        updateConfigName = {0:"Disabled", 1:"Manual", 2:"On Start", 3:"Automatic", 4:"continuous"}
        self.logger.info('Update Mode "{}"',updateConfigName.get(updateConfig))
        ##
        doSomething = 0
        if (int(databaseStatus['version']) != 3 or databaseStatus['status'] == 'UNINIT'):
            self.logger.info('Version update or not initialized')
            doSomething = -1
            ###
            if self.settings.getDatabaseType() == 0:
                StoreSQLiteSetup(self.database).setupDatabase()
            else:
                StoreMySQLSetup(self.database).setupDatabase()
            ##
            self.database.set_status(pStatus='IDLE', pLastupdate=0, pLastFullUpdate=0, pFilmupdate=0, pVersion='3')
            databaseStatus = self.database.getDatabaseStatus()
            ###
        elif updateConfig == 1 and self.settings.is_update_triggered():
            self.logger.info('Manual update')
            doSomething = 1
        elif updateConfig == 2 and self.settings.is_update_triggered():
            self.logger.info('On Start update - was triggered manual')
            doSomething = 1
        elif updateConfig == 2 and not(sameDay) and self.settings.is_user_alive():
            self.logger.info('On Start update and no update today')
            doSomething = 1
        elif updateConfig == 3 and self.settings.is_user_alive() and outdated:
            self.logger.info('auto update')
            doSomething = 1
        elif updateConfig == 4 and outdated:
            self.logger.info('continuous update')
            doSomething = 1
        elif updateConfig == 9:
            self.logger.info('mvupdate --full')
            doSomething = -1
        ##
        if (doSomething == 0):
            self.logger.info('nothing to do')
            return
        ##
        lastFullUpdate = datetime.fromtimestamp(databaseStatus['lastFullUpdate'])
        ##
        ufd = UpdateFileDownload()
        ##
        if doSomething == -1 or (not (currentDate.day == lastFullUpdate.day and 
            currentDate.month == lastFullUpdate.month and 
            currentDate.year == lastFullUpdate.year) and
            currentDate.hour > 5
        ):
            if self.settings.getDatabaseType() == 0 and self.settings.getDatabaseUpdateNative():
                ## replace the sqlite DB by downloaded version
                self.logger.info('sqlite update')
                ufd.downloadSqliteDb()
                self.database.exit()
                ufd.updateSqliteDb()
                ufd.removeDownloads()
                ## check database is alive
                check = self.database.get_status()
                if check['mov'] > 0:
                    self.database.set_status('IDLE', pLastupdate = int(time.time()), pLastFullUpdate = int(time.time()))
                else:
                    self.database.set_status('UNINIT')
                #
                self.settings.set_update_triggered('false')
            else:
                ## download full filmlist and do a full update
                self.logger.info('full update')
                ufd.downloadFullUpdateFile()
                UpdateFileImport(ufd.getTargetFilename(), self.database).updateFull()
                ufd.removeDownloads()
                ##
                self.database.set_status('IDLE', pLastupdate = int(time.time()), pLastFullUpdate = int(time.time()))
                ##
                self.settings.set_update_triggered('false')
        else:
            ## download incremental filmlist and do the update
            self.logger.info('incremental update')
            ufd.downloadIncrementalUpdateFile()
            UpdateFileImport(ufd.getTargetFilename(), self.database).updateIncremental()
            ufd.removeDownloads()
            self.database.set_status('IDLE', pLastupdate=int(time.time()))
            self.settings.set_update_triggered('false')
            
        






