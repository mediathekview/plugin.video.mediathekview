# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""
# pylint: disable=too-many-lines,line-too-long

import os
import json
import time
import sqlite3
import hashlib

from contextlib import closing
from codecs import open

import resources.lib.mvutils as mvutils

from resources.lib.film import Film
from resources.lib.exceptions import DatabaseCorrupted

# -- Constants ----------------------------------------------
# DATABASE_URL = 'https://mvupdate.yeasoft.com/filmliste-v2.db.xz'
DATABASE_URL = 'https://liste.mediathekview.de/filmliste-v2.db.xz'
DATABASE_AKT = 'filmliste-v2.db.update'


class StoreSQLite(object):
    """
    The local SQlite database class

    Args:
        logger(KodiLogger): a valid `KodiLogger` instance

        notifier(Notifier): a valid `Notifier` instance

        settings(Settings): a valid `Settings` instance
    """

    def __init__(self, logger, notifier, settings):
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        # internals
        self.conn = None
        self.dbfile = os.path.join(self.settings.datapath, 'filmliste-v3.db')
        # useful query fragments
        self.sql_query_films = "SELECT idhash as id, title, show, channel, description, duration, size, datetime(aired, 'unixepoch', 'localtime'), url_sub, url_video, url_video_sd, url_video_hd FROM film"
        self.sql_cond_recent = "( ( UNIX_TIMESTAMP() - {} ) <= {} )".format(
            "aired" if settings.recentmode == 0 else "dtCreated",
            settings.maxage
        )
        self.sql_cond_nofuture = " AND ( aired < UNIX_TIMESTAMP() )" if settings.nofuture else ""
        self.sql_cond_minlength = " AND ( duration >= %d )" % settings.minlength if settings.minlength > 0 else ""
        # update helper
        self.ft_channel = None
        self.ft_channelid = None
        self.ft_show = None
        self.ft_showid = None

    def init(self, reset=False, convert=False, failedCount = 0):
        """
        Startup of the database system

        Args:
            reset(bool, optional): if `True` the database
                will be cleaned up and recreated. Default
                is `False`

            convert(bool, optional): if `True` the database
                will be converted in case it is older than
                the supported version. If `False` a UI message
                will be displayed to the user informing that
                the database will be converted. Default is
                `False`
        """
        self.logger.info(
            'Using SQLite version {}, python library sqlite3 version {}',
            sqlite3.sqlite_version,
            sqlite3.version
        )
        if not mvutils.dir_exists(self.settings.datapath):
            os.mkdir(self.settings.datapath)

        # remove old versions
        mvutils.file_remove(os.path.join(
            self.settings.datapath,
            'filmliste-v1.db'
        ))
        # remove old versions
        mvutils.file_remove(os.path.join(
            self.settings.datapath,
            'filmliste-v2.db'
        ))
        
        if reset is True or not mvutils.file_exists(self.dbfile):
            self.logger.info(
                '===== RESET: Database will be deleted and regenerated =====')
            self.exit()
            mvutils.file_remove(self.dbfile)
            if self._handle_update_substitution():
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            else:
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
                self._handle_database_initialization()
        else:
            try:
                if self._handle_update_substitution():
                    self._handle_not_update_to_date_dbfile()
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            except sqlite3.DatabaseError as err:
                self.logger.error(
                    'Error while opening database: {}. trying to fully reset the Database...', err)
                return self.init(reset=True, convert=convert)
        try:

            # 3x speed-up, check mode 'WAL'
            self.conn.execute('pragma journal_mode=off')
            # check if DB is ready or broken
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM `status` LIMIT 1')
            rs = cursor.fetchall()
            ##
            self.logger.info('Current DB Status Last modified {} ({})', time.ctime(rs[0][0]), rs[0][0])
            self.logger.info('Current DB Status Last lastupdate {} ({})', time.ctime(rs[0][2]), rs[0][2])
            self.logger.info('Current DB Status Last filmupdate {} ({})', time.ctime(rs[0][3]), rs[0][3])
            self.logger.info('Current DB Status Last fullupdate {}', rs[0][4])
            ##
            cursor.close()
        except sqlite3.DatabaseError as err:
            failedCount += 1
            if (failedCount > 3):
                self.logger.error('Failed to restore database, please uninstall plugin, delete user profile and reinstall')
                raise err
            self.logger.error('Error on first query: {}. trying to fully reset the Database...trying {} times', err, failedCount)
            return self.init(reset=True, convert=convert, failedCount=failedCount)
        # that is a bit dangerous :-) but faaaast
        self.conn.execute('pragma synchronous=off')
        self.conn.create_function('UNIX_TIMESTAMP', 0, get_unix_timestamp)
        self.conn.create_aggregate('GROUP_CONCAT', 1, GroupConcatClass)
        return True

    def exit(self):
        """ Shutdown of the database system """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

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
        self.logger.info('search')
        searchmask = '%' + search + '%'
        searchcond = '( ( title LIKE ? ) OR ( show LIKE ? ) OR ( description LIKE ? ) )' if extendedsearch is True else '( ( title LIKE ? ) OR ( show LIKE ? ) )'
        searchparm = (searchmask, searchmask, searchmask) if extendedsearch is True else (
            searchmask, searchmask, )
        return self._search_condition(
            condition=searchcond,
            params=searchparm,
            filmui=filmui,
            showshows=True,
            showchannels=True,
            maxresults=self.settings.maxresults,
            order='film.aired desc')

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
        self.logger.info('get_recents')
        if channelid != "":
            return self._search_condition(
                condition=self.sql_cond_recent + ' AND ( channel=? )',
                params=(channelid, ),
                filmui=filmui,
                showshows=True,
                showchannels=False,
                maxresults=self.settings.maxresults,
                order='aired desc'
            )

        return self._search_condition(
            condition=self.sql_cond_recent,
            params=(),
            filmui=filmui,
            showshows=True,
            showchannels=False,
            maxresults=self.settings.maxresults,
            order='aired desc'
        )

    def get_live_streams(self, filmui):
        """
        Populates the current UI directory with the live
        streams

        Args:
            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        self.logger.info('get_live_streams')
        return self._search_condition(
            condition='( show="LIVESTREAM" )',
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=False,
            maxresults=0,
            limiting=False
        )

    def get_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of available channels

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        self._search_channels_condition(None, channelui)

    def get_recent_channels(self, channelui):
        """
        Populates the current UI directory with the list
        of channels having recent film additions based on
        the configured interval.

        Args:
            channelui(ChannelUI): an instance of a channel model
                view used for populating the directory
        """
        self._search_channels_condition(self.sql_cond_recent, channelui)

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
        self.logger.info('get_initials')
        if self.conn is None:
            return
        try:
            channelid = channelid
            cursor = self.conn.cursor()
            if channelid != "":
                self.logger.info(
                    """
                    SELECT      SUBSTR(show,1,1),COUNT(*)
                    FROM        film
                    WHERE       ( channel={} ) and SUBSTR(show,1,1) between 'A' and 'Z'
                    GROUP BY    SUBSTR(show,1,1)
                    """,
                    channelid
                )
                cursor.execute("""
                    SELECT      SUBSTR(show,1,1),COUNT(*)
                    FROM        film
                    WHERE       ( channel=? ) and SUBSTR(show,1,1) between 'A' and 'Z'
                    GROUP BY    SUBSTR(show,1,1)
                """, (channelid, ))
            else:
                self.logger.info(
                    'SQlite Query: SELECT SUBSTR(show,1,1),COUNT(*) FROM film GROUP BY SUBSTR(show,1,1)'
                )
                cursor.execute("""
                    SELECT      SUBSTR(show,1,1),COUNT(*)
                    FROM        film
                    WHERE SUBSTR(show,1,1) between 'A' and 'Z'
                    GROUP BY    SUBSTR(show,1,1)
                """)
            initialui.begin(channelid)
            for (initialui.initial, initialui.count) in cursor:
                initialui.add()
            initialui.end()
            cursor.close()
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def get_shows(self, channelid, initial, showui, caching=True):
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
        self.logger.info('get_shows')
        if self.conn is None:
            return

        if caching and self.settings.caching:
            if channelid == "" and self.settings.groupshows:
                cache_condition = "SHOW:1:" + initial
            elif channelid == "":
                cache_condition = "SHOW:2:" + initial
            elif initial:
                cache_condition = "SHOW:3:" + channelid + ':' + initial
            else:
                cache_condition = "SHOW:3:" + channelid
            cached_data = self._load_cache('get_shows', cache_condition)
            if cached_data is not None:
                showui.begin(channelid)
                for show_data in cached_data:
                    showui.set_from_dict(show_data)
                    showui.add()
                showui.end()
                return

        try:
            channelid = channelid
            cached_data = []
            cursor = self.conn.cursor()
            if channelid == "" and self.settings.groupshows:
                sqlstmt = """
                    SELECT      GROUP_CONCAT(showid),
                                GROUP_CONCAT(channel),
                                show,
                                GROUP_CONCAT(channel)
                    FROM        film
                    WHERE       ( show LIKE ? )
                    GROUP BY    show
                """
                cursor.execute(sqlstmt, (initial + '%', ))
            elif channelid == "":
                sqlstmt = """
                    SELECT      showid,
                                channel,
                                show,
                                channel
                    FROM        film
                    WHERE       ( show LIKE ? )
                    GROUP BY showid, channel, show, channel
                """
                cursor.execute(sqlstmt, (initial + '%', ))
            elif initial:
                sqlstmt = """
                    SELECT      showid,
                                channel,
                                show,
                                channel
                    FROM        film
                    WHERE
                                ( channel=? )
                                    AND
                                    ( show LIKE ? )
                    GROUP BY showid, channel, show, channel
                """
                cursor.execute(sqlstmt, (channelid, initial + '%', ))
            else:
                sqlstmt ="""
                    SELECT      showid,
                                channel,
                                show,
                                channel
                    FROM        film
                    WHERE       ( channel=? )
                    GROUP BY showid, channel, show, channel
                """
                cursor.execute(sqlstmt, (channelid, ))
            ##
            self.logger.info(sqlstmt);
            ##
            showui.begin(channelid)
            for (showui.showid, showui.channelid, showui.show, showui.channel) in cursor:
                showui.add()
                if caching and self.settings.caching:
                    cached_data.append(showui.get_as_dict())
            showui.end()
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('get_shows', cache_condition, cached_data)
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def get_films(self, showid, filmui):
        """
        Populates the current UI directory with a list
        of films of a specific show.

        Args:
            showid(id): database id of the selected show.

            filmui(FilmUI): an instance of a film model view
                used for populating the directory
        """
        self.logger.info('get_films')
        if self.conn is None:
            return
        if showid.find(',') == -1:
            # only one channel id
            self.logger.info('get_films for one show')
            return self._search_condition(
                condition='( showid=? )',
                params=(showid,),
                filmui=filmui,
                showshows=False,
                showchannels=False,
                maxresults=10000,
                order='film.aired desc'
            )

        # multiple channel ids
        self.logger.info('get_films for one show')
        self.logger.info(showid)
        parts = showid.split(',')
        sql_list = ','.join("'{0}'".format(w) for w in parts)
        return self._search_condition(
            condition='( showid IN ( {} ) )'.format(sql_list),
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=True,
            maxresults=10000,
            order='film.aired desc'
        )

    def _search_channels_condition(self, condition, channelui, caching=True):
        if self.conn is None:
            return
        if caching and self.settings.caching:
            cached_data = self._load_cache('search_channels', condition)
            if cached_data is not None:
                channelui.begin()
                for channel_data in cached_data:
                    channelui.set_from_dict(channel_data)
                    channelui.add()
                channelui.end()
                return

        try:
            if condition is None:
                query = 'SELECT channel,channel,0 AS `count` FROM film group by channel'
                qtail = ''
            else:
                query = 'SELECT channel AS `id`,channel,COUNT(*) AS `count` FROM film'
                qtail = ' WHERE ' + condition + ' GROUP BY channel'
            self.logger.info('SQLite Query: {}', query + qtail)
            cached_data = []
            cursor = self.conn.cursor()
            cursor.execute(query + qtail)
            channelui.begin()
            for (channelui.channelid, channelui.channel, channelui.count) in cursor:
                channelui.add()
                if caching and self.settings.caching:
                    cached_data.append(channelui.get_as_dict())
            channelui.end()
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('search_channels', condition, cached_data)
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)

    def _search_condition(self, condition, params, filmui, showshows, showchannels, maxresults, limiting=True, caching=True, order=None):
        if self.conn is None:
            return 0

        maxresults = int(maxresults)
        if limiting:
            sql_cond_limit = self.sql_cond_nofuture + self.sql_cond_minlength
        else:
            sql_cond_limit = ''

        if caching and self.settings.caching:
            cache_condition = condition + sql_cond_limit + \
                (' LIMIT {}'.format(maxresults + 1)
                 if maxresults else '') + ':{}'.format(params)
            start = time.time()
            cached_data = self._load_cache('search_films', cache_condition)
            self.logger.info('LOAD_CACHE:{}', time.time() - start)
            if cached_data is not None:
                results = len(cached_data)
                filmui.begin(showshows, showchannels)
                start = time.time()
                for film_data in cached_data:
                    filmui.set_from_dict(film_data)
                    filmui.add(total_items=results)
                filmui.end()
                self.logger.info('FILL_KODI_LIST:{}', time.time() - start)
                return results

        try:
            cached_data = []
            order = (' ORDER BY ' + order) if order is not None else ''
            self.logger.info(
                'SQLite Query: {}',
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order
            )
            start = time.time()
            cursor = self.conn.cursor()
            cursor.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            self.logger.info('QUERY_TIME:{}', time.time() - start)
            start = time.time()
            resultCount = 0
            for (filmui.filmid, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd) in cursor:
                resultCount += 1
                if maxresults and resultCount > maxresults:
                    break;
                cached_data.append(filmui.get_as_dict()) #write data to dict anyway because we want the total number of rows to be passed to add function
            ###
            results = len(cached_data)
            filmui.begin(showshows, showchannels)
            for film_data in cached_data:
                filmui.set_from_dict(film_data)
                filmui.add(total_items=results)
            filmui.end()
            if maxresults and resultCount > maxresults:
                self.notifier.show_limit_results(maxresults)        
            filmui.end()
            self.logger.info('FILL_KODI_LIST:{}', time.time() - start)
            cursor.close()
            if caching and self.settings.caching:
                self._save_cache('search_films', cache_condition, cached_data)
            return results
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            return 0

    def retrieve_film_info(self, filmid):
        """
        Retrieves the spcified film information
        from the database

        Args:
            filmid(id): database id of the requested film
        """
        if self.conn is None:
            return None
        try:
            condition = '( film.idhash={} )'.format(filmid)
            self.logger.info(
                'SQLite Query: {}',
                self.sql_query_films +
                ' WHERE ' +
                condition
            )
            cursor = self.conn.cursor()
            cursor.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition
            )
            film = Film()
            for (film.filmid, film.title, film.show, film.channel, film.description, film.seconds, film.size, film.aired, film.url_sub, film.url_video, film.url_video_sd, film.url_video_hd) in cursor:
                cursor.close()
                return film
            cursor.close()
        except sqlite3.Error as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
        return None

    def get_version(self):
        vversion = 0;
        try :
            statusRs = get_status()
            vversion = int(status['version']);
        except Exception as err:
            self.logger.error('Failed to load version from status: {}', err)
        return vvserion;
        
    def get_status(self):
        """ Retrieves the database status information """
        status = {
            'modified': int(time.time()),
            'status': '',
            'lastupdate': 0,
            'filmupdate': 0,
            'fullupdate': 0,
            'add_chn': 0,
            'add_shw': 0,
            'add_mov': 0,
            'del_chn': 0,
            'del_shw': 0,
            'del_mov': 0,
            'tot_chn': 0,
            'tot_shw': 0,
            'tot_mov': 0,
            'version': 0
        }
        if self.conn is None:
            status['status'] = "UNINIT"
            return status
        self.conn.commit()
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM `status` LIMIT 1')
        result = cursor.fetchall()
        cursor.close()
        if not result:
            status['status'] = "NONE"
            return status
        status['modified'] = result[0][0]
        status['status'] = result[0][1]
        status['lastupdate'] = result[0][2]
        status['filmupdate'] = result[0][3]
        status['fullupdate'] = result[0][4]
        status['add_chn'] = result[0][5]
        status['add_shw'] = result[0][6]
        status['add_mov'] = result[0][7]
        status['del_chn'] = result[0][8]
        status['del_shw'] = result[0][9]
        status['del_mov'] = result[0][10]
        status['tot_chn'] = result[0][11]
        status['tot_shw'] = result[0][12]
        status['tot_mov'] = result[0][13]
        if (len(result[0]) > 13):
            status['version'] = result[0][14]
        return status

    def update_status(self, status=None, lastupdate=None, filmupdate=None, fullupdate=None, add_chn=None, add_shw=None, add_mov=None, del_chn=None, del_shw=None, del_mov=None, tot_chn=None, tot_shw=None, tot_mov=None):
        """
        Updates the database status. Only supplied information
        will be updated.

        Args:
            status(status, optional): Status of the database. Can be:
                `NONE`, `UNINIT`, `IDLE`, `UPDATING`, `ABORTED`

            lastupdate(int, optional): Last update timestamp as UNIX epoch

            filmupdate(int, optional): Timestamp of the update list as UNIX epoch

            fullupdate(int, optional): Last full update timestamp as UNIX epoch

            add_chn(int, optional): Added channels during last update

            add_shw(int, optional): Added shows during last update

            add_mov(int, optional): Added films during last update

            del_chn(int, optional): Deleted channels during last update

            del_shw(int, optional): Deleted shows during last update

            del_mov(int, optional): Deleted films during last update

            tot_chn(int, optional): Total channels in database

            tot_shw(int, optional): Total shows in database

            tot_mov(int, optional): Total films in database
        """
        if self.conn is None:
            return
        new = self.get_status()
        old = new['status']
        if status is not None:
            new['status'] = status
        if lastupdate is not None:
            new['lastupdate'] = lastupdate
        if filmupdate is not None:
            new['filmupdate'] = filmupdate
        if fullupdate is not None:
            new['fullupdate'] = fullupdate
        if add_chn is not None:
            new['add_chn'] = add_chn
        if add_shw is not None:
            new['add_shw'] = add_shw
        if add_mov is not None:
            new['add_mov'] = add_mov
        if del_chn is not None:
            new['del_chn'] = del_chn
        if del_shw is not None:
            new['del_shw'] = del_shw
        if del_mov is not None:
            new['del_mov'] = del_mov
        if tot_chn is not None:
            new['tot_chn'] = tot_chn
        if tot_shw is not None:
            new['tot_shw'] = tot_shw
        if tot_mov is not None:
            new['tot_mov'] = tot_mov
        new['modified'] = int(time.time())
        cursor = self.conn.cursor()
        if old == "NONE":
            # insert status
            cursor.execute(
                """
                INSERT INTO `status` (
                    `modified`,
                    `status`,
                    `lastupdate`,
                    `filmupdate`,
                    `fullupdate`,
                    `add_chn`,
                    `add_shw`,
                    `add_mov`,
                    `del_chm`,
                    `del_shw`,
                    `del_mov`,
                    `tot_chn`,
                    `tot_shw`,
                    `tot_mov`,
                    `version`
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    4
                )
                """, (
                    new['modified'],
                    new['status'],
                    new['lastupdate'],
                    new['filmupdate'],
                    new['fullupdate'],
                    new['add_chn'],
                    new['add_shw'],
                    new['add_mov'],
                    new['del_chn'],
                    new['del_shw'],
                    new['del_mov'],
                    new['tot_chn'],
                    new['tot_shw'],
                    new['tot_mov'],
                )
            )
        else:
            # update status
            cursor.execute(
                """
                UPDATE `status`
                SET     `modified`      = ?,
                        `status`        = ?,
                        `lastupdate`    = ?,
                        `filmupdate`    = ?,
                        `fullupdate`    = ?,
                        `add_chn`       = ?,
                        `add_shw`       = ?,
                        `add_mov`       = ?,
                        `del_chm`       = ?,
                        `del_shw`       = ?,
                        `del_mov`       = ?,
                        `tot_chn`       = ?,
                        `tot_shw`       = ?,
                        `tot_mov`       = ?
                """, (
                    new['modified'],
                    new['status'],
                    new['lastupdate'],
                    new['filmupdate'],
                    new['fullupdate'],
                    new['add_chn'],
                    new['add_shw'],
                    new['add_mov'],
                    new['del_chn'],
                    new['del_shw'],
                    new['del_mov'],
                    new['tot_chn'],
                    new['tot_shw'],
                    new['tot_mov'],
                )
            )
        cursor.close()
        self.conn.commit()

    @staticmethod
    def supports_update():
        """
        Returns `True` if the selected database driver supports
        updating a local copy
        """
        return True

    def supports_native_update(self, full):
        """
        Returns `True` if the selected database driver supports
        updating a local copy with native functions and files

        Args:
            full(bool): if `True` a full update is requested
        """
        return full and self.settings.updnative

    def get_native_info(self, full):
        """
        Returns a tuple containing:
        - The URL of the requested update type dispatcher
        - the base name of the downloadable file

        Args:
            full(bool): if `True` a full update is requested
        """
        if full and self.settings.updnative:
            return (DATABASE_URL, DATABASE_AKT)
        return None

    def native_update(self, full):
        """
        Performs a native update of the database.

        Args:
            full(bool): if `True` a full update is started
        """
        if full:
            self.exit()
            self.init()
        return full

    def ft_init(self):
        """
        Initializes local database for updating
        """
        try:
            # prevent concurrent updating
            self.conn.commit()
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE  `status`
                SET     `modified`      = ?,
                        `status`        = 'UPDATING'
                WHERE   ( `status` != 'UPDATING' )
                        OR
                        ( `modified` < ? )
                """, (
                    int(time.time()),
                    int(time.time()) - 86400
                )
            )
            retval = cursor.rowcount > 0
            self.conn.commit()
            cursor.close()
            self.ft_channel = None
            self.ft_channelid = None
            self.ft_show = None
            self.ft_showid = None
            return retval
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_update_start(self, full):
        """
        Begins a local update procedure

        Args:
            full(bool): if `True` a full update is started
        """
        try:
            cursor = self.conn.cursor()
            if full:
                cursor.executescript("""
                    UPDATE  `film`
                    SET     `touched` = 0;
                """)
            cursor.execute('SELECT COUNT(*) FROM `film`')
            result3 = cursor.fetchone()
            cursor.close()
            self.conn.commit()
            return (0, 0, result3[0], )
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_update_end(self, delete):
        """
        Finishes a local update procedure

        Args:
            delete(bool): if `True` all records not updated
                will be deleted
        """
        try:
            del_chn=0
            del_shw=0
            del_mov=0
            cnt_chn=0
            cnt_shw=0
            cnt_mov=0
            ##
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM `film` WHERE ( touched = 0 )')
            (del_mov, ) = cursor.fetchone()
            if delete:
                cursor.execute('DELETE FROM `film` WHERE ( touched = 0 )')
            else:
                del_chn = 0
                del_shw = 0
                del_mov = 0
            cursor.execute('SELECT COUNT(*) FROM `film`')
            (cnt_mov, ) = cursor.fetchone()
            cursor.close()
            self.conn.commit()
            return (del_chn, del_shw, del_mov, cnt_chn, cnt_shw, cnt_mov, )
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))

    def ft_insert_film(self, filmArray, commit=True):
        #
        pStmtInsert = """
                    INSERT INTO `film` (
                        `idhash`,
                        `dtCreated`,
                        `channel`,
                        `showid`,
                        `show`,
                        `title`,
                        `aired`,
                        `duration`,
                        `size`,
                        `description`,
                        `url_sub`,
                        `url_video`,
                        `url_video_sd`,
                        `url_video_hd`
                    )
                    VALUES (
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )"""
        pStmtUpdate = """UPDATE `film` SET touched = 1 WHERE idhash = ?"""
        try:
            cursor = self.conn.cursor()
            insertArray = []
            updateCnt = 0
            insertCnt = 0
            for f in filmArray:
                cursor.execute(pStmtUpdate,(f[0],))
                if cursor.rowcount == 0:
                    insertArray.append(f)
                    insertCnt +=1
                else:
                    updateCnt +=1
            #
            cursor.executemany(pStmtInsert,insertArray)
            #
            return (updateCnt,insertCnt)
        except sqlite3.DatabaseError as err:
            self._handle_database_corruption(err)
            raise DatabaseCorrupted(
                'Database error during critical operation: {} - Database will be rebuilt from scratch.'.format(err))   
    

    def _load_cache(self, reqtype, condition):
        filename = os.path.join(self.settings.datapath, reqtype + '.cache')
        dbLastUpdate = self.get_status()['modified']
        try:
            with closing(open(filename, encoding='utf-8')) as json_file:
                data = json.load(json_file)
                if isinstance(data, dict):
                    if data.get('type', '') != reqtype:
                        return None
                    if data.get('condition') != condition:
                        return None
                    if int(dbLastUpdate) != data.get('time', 0):
                        return None
                    data = data.get('data', [])
                    if isinstance(data, list):
                        return data
                    return None
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to load cache file {}: {}', filename, err)
        return None

    def _save_cache(self, reqtype, condition, data):
        if not isinstance(data, list):
            return False
        filename = os.path.join(self.settings.datapath, reqtype + '.cache')
        dbLastUpdate = self.get_status()['modified']
        cache = {
            "type": reqtype,
            "time": int(dbLastUpdate),
            "condition": condition,
            "data": data
        }
        try:
            with closing(open(filename, 'w', encoding='utf-8')) as json_file:
                json.dump(cache, json_file)
            return True
        # pylint: disable=broad-except
        except Exception as err:
            self.logger.error(
                'Failed to write cache file {}: {}', filename, err)
            return False

    def _handle_update_substitution(self):
        updfile = os.path.join(self.settings.datapath, DATABASE_AKT)
        sqlfile = os.path.join(self.settings.datapath, 'filmliste-v3.db')
        if mvutils.file_exists(updfile):
            self.logger.info('Native update file found. Updating database...')
            return mvutils.file_rename(updfile, sqlfile)
        return False

    def _handle_database_corruption(self, err):
        self.logger.error(
            'Database error during critical operation: {} - Database will be rebuilt from scratch.', err)
        self.notifier.show_database_error(err)
        self.exit()
        self.init(reset=True, convert=False)

    def _handle_not_update_to_date_dbfile(self):
        ###
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.dbfile, timeout=60)
            cursor = self.conn.cursor()
            cursor.execute('SELECT modified FROM `status` LIMIT 1')
            rs = cursor.fetchall()
            modified = rs[0][0]
            current_time = int(time.time())
            target_time = modified + 8 * 60 * 60;
            if (target_time < current_time):
                self.logger.info("Outdated DB after full refresh! DB modified time is {} ({}) which is less than allowed {} ({})",time.ctime(modified),modified,time.ctime(target_time),target_time)
                cursor = self.conn.cursor()
                cursor.execute('UPDATE status SET modified = ?,lastupdate = ?, filmupdate = ?', (int(time.time()),int(time.time()),int(time.time())))
                cursor.close()
                self.conn.commit()
                return True
            self.conn.close()
            self.conn = None
        except sqlite3.DatabaseError as err:
            self.logger.error('HUST: {}', err)     
        return False

    def _handle_database_initialization(self):
        self.conn.executescript("""
PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film";
CREATE TABLE "film" (
     "idhash" TEXT(32,0) NOT NULL PRIMARY KEY,
     "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
     "touched" integer(1,0) NOT NULL DEFAULT 1,
     "channel" TEXT(32,0) NOT NULL COLLATE NOCASE,
     "showid" TEXT(8,0) NOT NULL,
     "show" TEXT(128,0) NOT NULL COLLATE NOCASE,
     "title" TEXT(128,0) NOT NULL COLLATE NOCASE,
     "aired" integer(11,0),
     "duration" integer(11,0),
     "size" integer(11,0),
     "description" TEXT(2048,0) COLLATE NOCASE,
     "url_sub" TEXT(384,0),
     "url_video" TEXT(384,0),
     "url_video_sd" TEXT(384,0),
     "url_video_hd" TEXT(384,0)
);
                        
-- ----------------------------
--  Table structure for status
-- ----------------------------
DROP TABLE IF EXISTS "status";
CREATE TABLE "status" (
     "modified" integer(11,0),
     "status" TEXT(32,0),
     "lastupdate" integer(11,0),
     "filmupdate" integer(11,0),
     "fullupdate" integer(1,0),
     "add_chn" integer(11,0),
     "add_shw" integer(11,0),
     "add_mov" integer(11,0),
     "del_chm" integer(11,0),
     "del_shw" integer(11,0),
     "del_mov" integer(11,0),
     "tot_chn" integer(11,0),
     "tot_shw" integer(11,0),
     "tot_mov" integer(11,0),
     "version" integer(11,0)
);

PRAGMA foreign_keys = true;
        """)
        self.update_status('IDLE')


class GroupConcatClass(object):
    """ Aggregate class for SQLite """

    def __init__(self):
        self.value = ''

    def step(self, value):
        """
        Accumulates the values to aggregate

        Args:
            value(any): Value to aggregate
        """
        if value is not None:
            if self.value == '':
                self.value = '{0}'.format(value)
            else:
                self.value = '{0},{1}'.format(self.value, value)

    def finalize(self):
        """ Returns the aggregated value """
        return self.value


def get_unix_timestamp():
    """ User defined function for SQLite """
    return int(time.time())
