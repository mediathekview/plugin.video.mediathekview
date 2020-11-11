# -*- coding: utf-8 -*-
"""
The plugin module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# -- Imports ------------------------------------------------
from __future__ import unicode_literals  # ,absolute_import, division
# from future import standard_library
# from builtins import *
# standard_library.install_aliases()
import os
import time
from datetime import datetime

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

from resources.lib.kodi.kodiaddon import KodiPlugin

from resources.lib.storeMySql import StoreMySQL
from resources.lib.storeSqlite import StoreSQLite
from resources.lib.notifierKodi import NotifierKodi
from resources.lib.filmui import FilmUI
from resources.lib.channelui import ChannelUI
from resources.lib.initialui import InitialUI
from resources.lib.showui import ShowUI
from resources.lib.downloader import Downloader
from resources.lib.searches import RecentSearches
import resources.lib.appContext as appContext

# -- Classes ------------------------------------------------


class MediathekViewPlugin(KodiPlugin):
    """ The main plugin class """

    def __init__(self):
        super(MediathekViewPlugin, self).__init__()
        self.settings = appContext.MVSETTINGS
        self.notifier = appContext.MVNOTIFIER
        self.logger = appContext.MVLOGGER.get_new_logger('MediathekViewPlugin')
        if self.settings.getDatabaseType() == 0:
            self.logger.info('Database driver: Internal (sqlite)')
            self.database = StoreSQLite()
        elif self.settings.getDatabaseType() == 1:
            self.logger.info('Database driver: External (mysql)')
            self.database = StoreMySQL()
        else:
            self.logger.warn('Unknown Database driver selected')
            self.database = None
        ##
        ##self.database = Store()

    def show_main_menu(self):
        """ Creates the main menu of the plugin """
        xbmcplugin.setContent(self.addon_handle, '')
        # Search
        self.add_folder_item(
            30901,
            {'mode': "search", 'extendedsearch': False},
            icon=os.path.join(self.path, 'resources', 'icons', 'search-m.png')
        )
        # Search all
        self.add_folder_item(
            30902,
            {'mode': "search", 'extendedsearch': True},
            icon=os.path.join(self.path, 'resources', 'icons', 'search-m.png')
        )
        # Browse livestreams
        self.add_folder_item(
            30903,
            {'mode': "livestreams"},
            icon=os.path.join(self.path, 'resources', 'icons', 'live2-m.png')
        )
        # Browse recently added
        self.add_folder_item(
            30904,
            {'mode': "recent", 'channel': ""},
            icon=os.path.join(self.path, 'resources', 'icons', 'new-m.png')
        )
        # Browse recently added by channel
        self.add_folder_item(
            30905,
            {'mode': "recentchannels"},
            icon=os.path.join(self.path, 'resources', 'icons', 'new-m.png')
        )
        # Browse by Initial->Show
        self.add_folder_item(
            30906,
            {'mode': "initial", 'channel': ""},
            icon=os.path.join(self.path, 'resources', 'icons', 'movie-m.png')
        )
        # Browse by Channel->Initial->Shows
        self.add_folder_item(
            30907,
            {'mode': "channels"},
            icon=os.path.join(self.path, 'resources', 'icons', 'movie-m.png')
        )
        # Database Information
        self.add_action_item(
            30908,
            {'mode': "action-dbinfo"},
            icon=os.path.join(self.path, 'resources', 'icons', 'dbinfo-m.png')
        )
        # Manual database update
        if self.settings.getDatabaseUpateMode() == 1 or self.settings.getDatabaseUpateMode() == 2:
            self.add_action_item(30909, {'mode': "action-dbupdate"})
        self.end_of_directory()
        self._check_outdate()

    def show_searches(self, extendedsearch=False):
        """
        Fill the search screen with "New Search..." and the
        list of recent searches

        Args:
            extendedsearch(bool, optionsl): If `True`, the searches
                are performed both in show title and description.
                Default is `False`
        """
        xbmcplugin.setContent(self.addon_handle, '')
        self.add_folder_item(
            30931,
            {'mode': "newsearch", 'extendedsearch': extendedsearch},
            icon=os.path.join(self.path, 'resources', 'icons', 'search-m.png')
        )
        RecentSearches(self, extendedsearch).load().populate()
        self.end_of_directory()

    def new_search(self, extendedsearch=False):
        """
        Asks the user to enter his search terms and then
        performs the search and displays the results.

        Args:
            extendedsearch(bool, optionsl): If `True`, the searches
                are performed both in show title and description.
                Default is `False`
        """
        settingid = 'lastsearch2' if extendedsearch is True else 'lastsearch1'
        headingid = 30902 if extendedsearch is True else 30901
        # are we returning from playback ?
        search = self.get_setting(settingid)
        if search:
            # restore previous search
            self.database.search(search, FilmUI(self), extendedsearch)
        else:
            # enter search term
            (search, confirmed) = self.notifier.get_entered_text('', headingid)
            if len(search) > 2 and confirmed is True:
                RecentSearches(self, extendedsearch).load().add(search).save()
                if self.database.search(search, FilmUI(self), extendedsearch) > 0:
                    self.set_setting(settingid, search)
            else:
                # pylint: disable=line-too-long
                self.logger.info(
                    'The following ERROR can be ignored. It is caused by the architecture of the Kodi Plugin Engine')
                self.end_of_directory(False, cache_to_disc=True)

    def show_db_info(self):
        """ Displays current information about the database """
        info = self.database.get_status()
        heading = self.language(30908)
        infostr = self.language({
            'NONE': 30941,
            'UNINIT': 30942,
            'IDLE': 30943,
            'UPDATING': 30944,
            'ABORTED': 30945
        }.get(info['status'], 30941))
        infostr = self.language(30965) % infostr
        totinfo = self.language(30971) % (
            info['chn'],
            info['shw'],
            info['mov']
            )
        updinfo = self.language(30970) % (
            datetime.fromtimestamp(info['filmUpdate']).isoformat().replace('T',' '),
            datetime.fromtimestamp(info['lastFullUpdate']).isoformat().replace('T',' '),
            datetime.fromtimestamp(info['lastUpdate']).isoformat().replace('T',' ')
            )
        ##
        xbmcgui.Dialog().textviewer(
            heading,
            infostr + '\n\n' +
            totinfo + '\n\n' +
            updinfo
        )

    def _check_outdate(self, maxage=172800):
        if self.settings.getDatabaseUpateMode() != 1 and self.settings.getDatabaseUpateMode() != 2:
            # no check with update disabled or update automatic
            return
        if self.database is None:
            # should never happen
            self.notifier.show_outdated_unknown()
            return
        status = self.database.get_status()
        if status['status'] == 'NONE' or status['status'] == 'UNINIT':
            # should never happen
            self.notifier.show_outdated_unknown()
            return
        elif status['status'] == 'UPDATING':
            # great... we are updating. nuthin to show
            return
        # lets check how old we are
        tsnow = int(time.time())
        tsold = int(status['lastUpdate'])
        if tsnow - tsold > maxage:
            self.notifier.show_outdated_known(status)

    def init(self):
        """ Initialisation of the plugin """
        pass


    def run(self):
        """ Execution of the plugin """
        start = time.time()
        # save last activity timestamp
        self.settings.user_activity()
        # process operation
        self.logger.info("Plugin invoked with parameters {}", self.args)
        mode = self.get_arg('mode', None)
        if mode is None:
            self.show_main_menu()
        elif mode == 'search':
            extendedsearch = self.get_arg('extendedsearch', 'False') == 'True'
            self.show_searches(extendedsearch)
        elif mode == 'newsearch':
            self.new_search(self.get_arg('extendedsearch', 'False') == 'True')
        elif mode == 'research':
            search = self.get_arg('search', '')
            extendedsearch = self.get_arg('extendedsearch', 'False') == 'True'
            self.database.search(search, FilmUI(self), extendedsearch)
            RecentSearches(self, extendedsearch).load().add(search).save()
        elif mode == 'delsearch':
            search = self.get_arg('search', '')
            extendedsearch = self.get_arg('extendedsearch', 'False') == 'True'
            RecentSearches(self, extendedsearch).load().delete(
                search).save().populate()
            self.run_builtin('Container.Refresh')
        elif mode == 'livestreams':
            self.database.get_live_streams(
                FilmUI(self, [xbmcplugin.SORT_METHOD_LABEL]))
        elif mode == 'recent':
            channel = self.get_arg('channel', "")
            channel == "" if channel == "0" else channel
            self.database.get_recents(channel, FilmUI(self))
        elif mode == 'recentchannels':
            self.database.get_recent_channels(
                ChannelUI(self, nextdir='recent'))
        elif mode == 'channels':
            self.database.get_channels(ChannelUI(self, nextdir='shows'))
        elif mode == 'action-dbinfo':
            self.run_builtin("ActivateWindow(busydialognocancel)")
            self.show_db_info()
            self.run_builtin("Dialog.Close(busydialognocancel)")            
        elif mode == 'action-dbupdate':
            self.settings.set_update_triggered('true')
            self.notifier.show_notification(30963, 30964)
        elif mode == 'initial':
            channel = self.get_arg('channel', "")
            channel == "" if channel == "0" else channel
            self.database.get_initials(channel, InitialUI(self))
        elif mode == 'shows':
            channel = self.get_arg('channel', "")
            channel == "" if channel == "0" else channel
            initial = self.get_arg('initial', "")
            initial == "" if initial == "0" else initial
            self.database.get_shows(channel, initial, ShowUI(self))
        elif mode == 'films':
            show = self.get_arg('show', "")
            show == "" if show == "0" else show
            self.database.get_films(show, FilmUI(self))
        elif mode == 'downloadmv':
            filmid = self.get_arg('id', "")
            quality = self.get_arg('quality', 1)
            Downloader(self).download_movie(filmid, quality)
        elif mode == 'downloadep':
            filmid = self.get_arg('id', "")
            quality = self.get_arg('quality', 1)
            Downloader(self).download_episode(filmid, quality)
        elif mode == 'playwithsrt':
            filmid = self.get_arg('id', "")
            Downloader(self).play_movie_with_subs(filmid)

        # cleanup saved searches
        if mode is None or mode != 'newsearch':
            self.set_setting('lastsearch1', '')
            self.set_setting('lastsearch2', '')
        ##
        self.logger.info('request processed: {} sec', time.time() - start)

    def exit(self):
        """ Shutdown of the application """
        self.database.exit()
