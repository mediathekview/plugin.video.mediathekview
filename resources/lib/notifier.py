# -*- coding: utf-8 -*-
"""
UI Notifier module

Copyright (c) 2017-2018, Leo Moll
Licensed under MIT License
"""

# -- Imports ------------------------------------------------
import datetime

# pylint: disable=import-error
import xbmcaddon

from resources.lib.kodi.KodiUI import KodiUI

# -- Classes ------------------------------------------------


class Notifier(KodiUI):
    """ The UI notifier class """

    def __init__(self):
        super(Notifier, self).__init__()
        self.language = xbmcaddon.Addon().getLocalizedString

    def show_database_error(self, err):
        """ Displays UI for a database error """
        self.ShowError(30951, '{}'.format(err))

    def show_download_error(self, name, err):
        """ Displays UI for a download error """
        self.ShowError(30952, self.language(30953).format(name, err))

    def show_missing_extractor_error(self):
        """ Disaplys UI for a missing extractor error """
        self.ShowError(30952, 30954, time=10000)

    def show_limit_results(self, maxresults):
        """ Display UI for search result limited by configuration """
        self.ShowNotification(30980, self.language(30981).format(maxresults))

    def show_outdated_unknown(self):
        """ Display UI for never updated database """
        self.ShowWarning(30982, 30966)

    def show_outdated_known(self, status):
        """ Display UI for an outdated database """
        updatetype = self.language(
            30972 if status['fullupdate'] > 0 else 30973)
        updatetime = datetime.datetime.fromtimestamp(
            status['lastupdate']).strftime('%Y-%m-%d %H:%M:%S'),
        updinfo = self.language(30983)
        self.ShowWarning(30982, updinfo.format(updatetype, updatetime[0]))

    def show_download_progress(self):
        """ Display UI for a download in progress """
        self.ShowBGDialog(30955)

    def update_download_progress(self, percent, message=None):
        """ Update UI odometer for a download in progress """
        self.UpdateBGDialog(percent, message=message)

    def hook_download_progress(self, blockcount, blocksize, totalsize):
        """ UI Report hook for functions like `url_retrieve` """
        self.HookBGDialog(blockcount, blocksize, totalsize)

    def close_download_progress(self):
        """ Hides the UI for a download in progress """
        self.CloseBGDialog()

    def show_update_progress(self):
        """ Display UI for a database update in progress """
        self.ShowBGDialog(30956)

    def update_update_progress(self, percent, count, channels, shows, movies):
        """ Update UI odometer for a database update in progress """
        message = self.language(30957) % (count, channels, shows, movies)
        self.UpdateBGDialog(percent, message=message)

    def close_update_progress(self):
        """ Hides the UI for a database update in progress """
        self.CloseBGDialog()

    def show_updating_scheme(self):
        """ SHow UI that the database schema is about to be updated """
        self.ShowOkDialog(30984, 30985)

    def show_update_scheme_progress(self):
        """ Display UI for a database schema update in progress """
        self.ShowBGDialog(30984)

    def update_update_scheme_progress(self, percent):
        """ Update UI odometer for a database schema update in progress """
        self.UpdateBGDialog(percent, message='')

    def close_update_scheme_progress(self):
        """ Hides the UI for a database schema update in progress """
        self.CloseBGDialog()
