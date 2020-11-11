# -*- coding: utf-8 -*-
"""
The database wrapper module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

import time

from resources.lib.storeMySql import StoreMySQL
from resources.lib.storeSqlite import StoreSQLite
import resources.lib.appContext as appContext

class Store(object):
    """
    The database wrapper class

    """

    def __init__(self):
        self.logger = appContext.MVLOGGER.get_new_logger('Store')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        # load storage engine
        if self.settings.getDatabaseType() == 0:
            self.logger.info('Database driver: Internal (sqlite)')
            self.database = StoreSQLite()
        elif self.settings.getDatabaseType() == 1:
            self.logger.info('Database driver: External (mysql)')
            self.database = StoreMySQL()
        else:
            self.logger.warn('Unknown Database driver selected')
            self.database = None

    def search(self, search, filmui, extendedsearch=False):
        """
        Performs a search for films based on a search term
        and adds the results to the current UI directory

        Args:
            search(str): search term

            filmui(FilmUI): an instance of a film model view used
                for populating the directory

            extendedsearch(bool, optional): if `True` the search is
                performed also on film descriptions. Default is
                `False`
        """
        # pylint: disable=line-too-long
        return self.database.search(search, filmui, extendedsearch) if self.database is not None else 0

    def get_recents(self, channelid, filmui):
        """
        Populates the current UI directory with the recent
        film additions based on the configured interval.

        Args:
            channelid(id): database id of the selected channel.
                If 0, films from all channels are listed

            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        return self.database.get_recents(channelid, filmui) if self.database is not None else 0

    def get_live_streams(self, filmui):
        """
        Populates the current UI directory with the live
        streams

        Args:
            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        return self.database.get_live_streams(filmui) if self.database is not None else 0

    def get_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of available channels

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        if self.database is not None:
            self.database.get_channels(channelui)

    def get_recent_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of channels having recent film additions based on
        the configured interval.

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        if self.database is not None:
            self.database.get_recent_channels(channelui)

    def get_initials(self, channelid, initialui):
        """
        Populates the current UI directory with a list
        of initial grouped entries.

        Args:
            channelid(id): database id of the selected channel.
                If 0, groups from all channels are listed

            initialui(InitialUI): an instance of a grouped entry
                model view used for populating the directory
        """
        if self.database is not None:
            self.database.get_initials(channelid, initialui)

    def get_shows(self, channelid, initial, showui):
        """
        Populates the current UI directory with a list
        of shows limited to a specific channel or not.

        Args:
            channelid(id): database id of the selected channel.
                If 0, shows from all channels are listed

            initial(str): search term for shows

            showui(ShowUI): an instance of a show model view
                used for populating the directory
        """
        if self.database is not None:
            self.database.get_shows(channelid, initial, showui)

    def get_films(self, showid, filmui):
        """
        Populates the current UI directory with a list
        of films of a specific show.

        Args:
            showid(id): database id of the selected show.

            filmui(FilmUI): an instance of a film model view
                used for populating the directory
        """
        return self.database.get_films(showid, filmui) if self.database is not None else 0

    def retrieve_film_info(self, filmid):
        """
        Retrieves the spcified film information
        from the database

        Args:
            filmid(id): database id of the requested film
        """
        if self.database is not None:
            return self.database.retrieve_film_info(filmid)
        else:
            return None

    def get_status(self):
        """ Retrieves the database status information """
        return self.database.get_status()

