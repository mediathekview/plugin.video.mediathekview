# -*- coding: utf-8 -*-
"""
The standalone update application environment module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
Licensed under MIT License
"""

# -- Imports ------------------------------------------------
import os
import sys
import argparse
import datetime
import defusedxml.ElementTree as ET

from resources.lib.base.Logger import Logger
from resources.lib.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------


class Settings(object):
    """ Standalone implementation of the settings class """

    def __init__(self, args):
        self.datapath = args.path if args.dbtype == 'sqlite' else './'
        self.type = {'sqlite': 0, 'mysql': 1}.get(args.dbtype, 0)
        if self.type == 1:
            self.host = args.host
            self.port = int(args.port)
            self.user = args.user
            self.password = args.password
            self.database = args.database
        self.autosub = False
        self.nofuture = True
        self.minlength = 0
        self.maxage = 86400
        self.recentmode = 0
        self.groupshows = False
        self.updmode = 3
        self.updinterval = args.intervall

    @staticmethod
    def reload():
        """
        Reloads the configuration of the addon and returns
        `True` if the database type has changed
        """
        return False

    @staticmethod
    def is_update_triggered():
        """
        Returns `True` if a database update has been triggered
        by another part of the addon
        """
        return True

    @staticmethod
    def is_user_alive():
        """ Returns `True` if there was recent user activity """
        return True

    @staticmethod
    def trigger_update():
        """ Triggers an asynchronous database update """
        return True

    @staticmethod
    def reset_user_activity():
        """ Signals that a user activity has occurred """
        pass


class AppLogger(Logger):
    """ Standalone implementation of the logger class """

    def __init__(self, name, version, topic=None, verbosity=0):
        super(AppLogger, self).__init__(name, version, topic)
        self.verbosity = verbosity

    def getNewLogger(self, topic=None):
        """
        Generates a new logger instance with a specific topic

        Args:
            topic(str, optional): the topic of the new logger.
                Default is the same topic of `self`
        """
        return AppLogger(self.name, self.version, topic, self.verbosity)

    def debug(self, message, *args):
        """ Outputs a debug message """
        self._log(2, message, *args)

    def info(self, message, *args):
        """ Outputs an info message """
        self._log(1, message, *args)

    def warn(self, message, *args):
        """ Outputs a warning message """
        self._log(0, message, *args)

    def error(self, message, *args):
        """ Outputs an error message """
        self._log(-1, message, *args)

    def _log(self, level, message, *args):
        parts = []
        for arg in args:
            part = arg
            if isinstance(arg, basestring):
                part = arg  # arg.decode('utf-8')
            parts.append(part)
        output = '{} {} {}{}'.format(
            datetime.datetime.now(),
            {-1: 'ERROR', 0: 'WARNING', 1: 'NOTICE', 2: 'DEBUG'}.get(level, 2),
            self.prefix,
            message.format(*parts)
        )

        if level < 0:
            # error
            sys.stderr.write(output + '\n')
            sys.stderr.flush()
        elif self.verbosity >= level:
            # other message
            # pylint: disable=superfluous-parens
            print(output)


class Notifier(object):
    """ Standalone implementation of the notifier class """

    def __init__(self):
        pass

    def GetEnteredText(self, deftext='', heading='', hidden=False):
        pass

    def ShowNotification(self, heading, message, icon=None, time=5000, sound=True):
        pass

    def ShowWarning(self, heading, message, time=5000, sound=True):
        pass

    def ShowError(self, heading, message, time=5000, sound=True):
        pass

    def ShowBGDialog(self, heading=None, message=None):
        pass

    def UpdateBGDialog(self, percent, heading=None, message=None):
        pass

    def CloseBGDialog(self):
        pass

    def show_database_error(self, err):
        """ Displays UI for a database error """
        pass

    def show_download_error(self, name, err):
        """ Displays UI for a download error """
        pass

    def show_missing_extractor_error(self):
        """ Disaplys UI for a missing extractor error """
        pass

    def show_limit_results(self, maxresults):
        """ Display UI for search result limited by configuration """
        pass

    def show_outdated_unknown(self):
        """ Display UI for never updated database """
        pass

    def show_outdated_known(self, status):
        """ Display UI for an outdated database """
        pass

    def show_download_progress(self):
        """ Display UI for a download in progress """
        pass

    def update_download_progress(self, percent, message=None):
        """ Update UI odometer for a download in progress """
        pass

    def hook_download_progress(self, blockcount, blocksize, totalsize):
        """ UI Report hook for functions like `url_retrieve` """
        pass

    def close_download_progress(self):
        """ Hides the UI for a download in progress """
        pass

    def show_update_progress(self):
        """ Display UI for a database update in progress """
        pass

    def update_update_progress(self, percent, count, channels, shows, movies):
        """ Update UI odometer for a database update in progress """
        pass

    def close_update_progress(self):
        """ Hides the UI for a database update in progress """
        pass

    def show_updating_scheme(self):
        """ SHow UI that the database schema is about to be updated """
        pass

    def show_update_scheme_progress(self):
        """ Display UI for a database schema update in progress """
        pass

    def update_update_scheme_progress(self, percent):
        """ Update UI odometer for a database schema update in progress """
        pass

    def close_update_scheme_progress(self):
        """ Hides the UI for a database schema update in progress """
        pass


class MediathekViewMonitor(object):
    @staticmethod
    def abortRequested():
        return False


class UpdateApp(AppLogger):
    """ The standalone updater application class """

    def __init__(self):
        try:
            self.mypath = os.path.dirname(sys.argv[0])
            tree = ET.parse(self.mypath + '/addon.xml')
            version = tree.getroot().attrib['version']
            AppLogger.__init__(self, os.path.basename(sys.argv[0]), version)
            self.args = None
            self.verbosity = 0
            self.notifier = None
            self.monitor = None
            self.updater = None
            self.settings = None
        # pylint: disable=broad-except
        except Exception:
            AppLogger.__init__(self, os.path.basename(sys.argv[0]), '0.0')

    def init(self):
        """ Startup of the application """
        # pylint: disable=line-too-long
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='This is the standalone database updater. It downloads the current database update from mediathekview.de and integrates it in a local database'
        )
        parser.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        subparsers = parser.add_subparsers(
            dest='dbtype',
            help='target database'
        )
        sqliteopts = subparsers.add_parser(
            'sqlite', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        sqliteopts.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        sqliteopts.add_argument(
            '-f', '--force',
            default=False,
            action='store_true',
            help='ignore the minimum interval'
        )
        sqliteopts.add_argument(
            '-i', '--intervall',
            default=3600,
            type=int,
            action='store',
            help='minimum interval between updates'
        )
        sqliteopts.add_argument(
            '-p', '--path',
            dest='path',
            help='alternative path for the sqlite database',
            default='./'
        )
        mysqlopts = subparsers.add_parser(
            'mysql', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        mysqlopts.add_argument(
            '-v', '--verbose',
            default=0,
            action='count',
            help='show progress messages'
        )
        mysqlopts.add_argument(
            '-f', '--force',
            default=False,
            action='store_true',
            help='ignore the minimum interval'
        )
        mysqlopts.add_argument(
            '-i', '--intervall',
            default=3600,
            type=int,
            action='store',
            help='minimum interval between updates'
        )
        mysqlopts.add_argument(
            '-H', '--host',
            dest='host',
            help='hostname or ip address',
            default='localhost'
        )
        mysqlopts.add_argument(
            '-P', '--port',
            dest='port',
            help='connection port',
            default='3306'
        )
        mysqlopts.add_argument(
            '-u', '--user',
            dest='user',
            help='connection username',
            default='mediathekview'
        )
        mysqlopts.add_argument(
            '-p', '--password',
            dest='password',
            help='connection password',
            default=None
        )
        mysqlopts.add_argument(
            '-d', '--database',
            dest='database',
            default='mediathekview',
            help='database name'
        )
        self.args = parser.parse_args()
        self.verbosity = self.args.verbose

        self.info('Startup')
        self.settings = Settings(self.args)
        self.notifier = Notifier()
        self.monitor = MediathekViewMonitor()
        self.updater = MediathekViewUpdater(self.getNewLogger(
            'MediathekViewUpdater'), self.notifier, self.settings, self.monitor)
        return self.updater.init(convert=True)

    def run(self):
        """ Execution of the application """
        self.info('Starting up...')
        updateop = self.updater.get_current_update_operation(self.args.force)
        if updateop == 1:
            # full update
            self.info('Initiating full update...')
            self.updater.update(True)
        elif updateop == 2:
            # differential update
            self.info('Initiating differential update...')
            self.updater.update(False)
        self.info('Exiting...')

    def exit(self):
        """ Shutdown of the application """
        self.updater.exit()
