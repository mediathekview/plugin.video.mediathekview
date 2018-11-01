# -*- coding: utf-8 -*-
"""
The MySQL database support module

Copyright 2017-20180 Leo Moll and Dominik Schlösser
"""
# pylint: disable=too-many-lines,line-too-long

import time
import mysql.connector
import hashlib

import resources.lib.mvutils as mvutils

from resources.lib.film import Film


class StoreMySQL(object):
    """
    The local MySQL database class

    Args:
        logger(KodiLogger): a valid `KodiLogger` instance

        notifier(Notifier): a valid `Notifier` instance

        settings(Settings): a valid `Settings` instance
    """

    def __init__(self, logger, notifier, settings):
        self.sqlInsert = """ insert into film_import 
                        (`idhash`, `channel`, `show`, `showsearch`,
                        `title`, `search`, `aired`, `duration`, `size`, `description`, 
                        `website`, `url_sub`, `url_video`, `url_video_sd`, `url_video_hd`, 
                        `airedepoch`) values 
                        """
        self.blockInsert = ''
        self.blockCursor = None
        self.filmImportColumns = 16
        self.sqlData = []
        self.conn = None
        self.logger = logger
        self.notifier = notifier
        self.settings = settings
        # updater state variables
        self.ft_channel = None
        self.ft_channelid = None
        self.ft_show = None
        self.ft_showid = None
        # useful query fragments
        # pylint: disable=line-too-long
        self.sql_query_films = "SELECT film.id,`title`,`show`,`channel`,`description`,TIME_TO_SEC(`duration`) AS `seconds`,`size`,`aired`,`url_sub`,`url_video`,`url_video_sd`,`url_video_hd` FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
        self.sql_query_filmcnt = "SELECT COUNT(*) FROM `film` LEFT JOIN `show` ON show.id=film.showid LEFT JOIN `channel` ON channel.id=film.channelid"
        self.sql_cond_recent = "( TIMESTAMPDIFF(SECOND,{},CURRENT_TIMESTAMP()) <= {} )".format(
            "aired" if settings.recentmode == 0 else "film.dtCreated", settings.maxage)
        self.sql_cond_nofuture = " AND ( ( `aired` IS NULL ) OR ( TIMESTAMPDIFF(HOUR,`aired`,CURRENT_TIMESTAMP()) > 0 ) )" if settings.nofuture else ""
        self.sql_cond_minlength = " AND ( ( `duration` IS NULL ) OR ( TIME_TO_SEC(`duration`) >= %d ) )" % settings.minlength if settings.minlength > 0 else ""

    def init(self, reset=False, convert=False):
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
        self.clear_insert_data()
        self.logger.info('Using MySQL connector version {}',
                         mysql.connector.__version__)
        if reset:
            self.logger.warn('Reset not supported')
        try:
            self.conn = mysql.connector.connect(
                host=self.settings.host,
                port=self.settings.port,
                user=self.settings.user,
                password=self.settings.password
            )
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT VERSION()')
                (version, ) = cursor.fetchone()
                self.logger.info(
                    'Connected to server {} running {}', self.settings.host, version)
                self.blockInsert = self.build_insert(self.flush_block_size())
                # tests showed that prepared statements provide no speed improvemend
                # as this feature is not implemented
                # in the c clientlib
                self.blockCursor = self.conn.cursor()
            # pylint: disable=broad-except
            except Exception:
                self.logger.info('Connected to server {}', self.settings.host)
            self.conn.database = self.settings.database
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.logger.info(
                    '=== DATABASE {} DOES NOT EXIST. TRYING TO CREATE IT ===', self.settings.database)
                return self._handle_database_initialization()
            self.conn = None
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            return False
        except Exception as err:
            if err.args[0] == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.logger.info('=== DATABASE {} DOES NOT EXIST. TRYING TO CREATE IT ===', self.settings.database)
                return self._handle_database_initialization()
            self.conn = None
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            return False
        # handle schema versioning
        return self._handle_database_update(convert)

    def exit(self):
        """ Shutdown of the database system """
        if self.conn is not None:
            if self.blockCursor is not None:
                self.blockCursor.close()
                self.blockCursor = None
            self.conn.close()
            self.conn = None

    def build_insert(self, rows):
        sqlValues = ''
        for i in xrange(0, rows):
            sqlValues += ' (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),'
        return self.sqlInsert + sqlValues[:-1]

    def flush_block_size(self):
        return 2000;

    def clear_insert_data(self):
        """ clear collected import data from sql variables """
        self.sqlValues = ''
        self.sqlData = []

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
        searchmask = '%' + search.decode('utf-8') + '%'
        searchcond = '( ( `title` LIKE %s ) OR ( `show` LIKE %s ) OR ( `description` LIKE %s ) )' if extendedsearch is True else '( ( `title` LIKE %s ) OR ( `show` LIKE %s ) )'
        searchparm = (searchmask, searchmask, searchmask) if extendedsearch is True else (
            searchmask, searchmask, )
        return self._search_condition(searchcond, searchparm, filmui, True, True, self.settings.maxresults)

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
        if channelid != '0':
            return self._search_condition(
                self.sql_cond_recent + ' AND ( film.channelid=%s )',
                (int(channelid), ),
                filmui,
                True,
                False,
                10000
            )
        return self._search_condition(
            self.sql_cond_recent,
            (),
            filmui,
            True,
            False,
            10000
        )

    def get_live_streams(self, filmui):
        """
        Populates the current UI directory with the live
        streams

        Args:
            filmui(FilmUI): an instance of a film model view used
                for populating the directory
        """
        return self._search_condition(
            '( show.search="LIVESTREAM" )',
            (),
            filmui,
            False,
            False,
            0,
            False
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
        if self.conn is None:
            return
        try:
            channelid = int(channelid)
            cursor = self.conn.cursor()
            if channelid != 0:
                self.logger.info(
                    'MySQL Query: SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` WHERE ( `channelid`={} ) GROUP BY LEFT(search,1)',
                    channelid
                )
                cursor.execute("""
                    SELECT      LEFT(`search`,1)    AS `letter`,
                                COUNT(*)            AS `count`
                    FROM        `show`
                    WHERE       ( `channelid`=%s )
                    GROUP BY    LEFT(`search`,1)
                """, (channelid, ))
            else:
                self.logger.info(
                    'MySQL Query: SELECT LEFT(`search`,1) AS letter,COUNT(*) AS `count` FROM `show` GROUP BY LEFT(search,1)'
                )
                cursor.execute("""
                    SELECT      LEFT(`search`,1)    AS `letter`,
                                COUNT(*)            AS `count`
                    FROM        `show`
                    GROUP BY    LEFT(`search`,1)
                """)
            initialui.begin(channelid)
            for (initialui.initial, initialui.count) in cursor:
                initialui.add()
            initialui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

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
        if self.conn is None:
            return
        try:
            channelid = int(channelid)
            cursor = self.conn.cursor()
            if channelid == 0 and self.settings.groupshows:
                cursor.execute("""
                    SELECT      GROUP_CONCAT(show.id),
                                GROUP_CONCAT(`channelid`),
                                `show`,
                                GROUP_CONCAT(`channel`)
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `show` LIKE %s )
                    GROUP BY    `show`
                """, (initial + '%', ))
            elif channelid == 0:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `show` LIKE %s )
                """, (initial + '%', ))
            elif initial:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       (
                                    ( `channelid` = %s )
                                    AND
                                    ( `show` LIKE %s )
                                )
                """, (channelid, initial + '%', ))
            else:
                cursor.execute("""
                    SELECT      show.id,
                                show.channelid,
                                show.show,
                                channel.channel
                    FROM        `show`
                    LEFT JOIN   `channel`
                        ON      ( channel.id = show.channelid )
                    WHERE       ( `channelid` = %s )
                """, (channelid, ))
            showui.begin(channelid)
            for (showui.showid, showui.channelid, showui.show, showui.channel) in cursor:
                showui.add()
            showui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
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
        if self.conn is None:
            return
        if showid.find(',') == -1:
            # only one channel id
            return self._search_condition(
                '( `showid` = %s )',
                (int(showid), ),
                filmui,
                False,
                False,
                10000
            )
        # multiple channel ids
        return self._search_condition(
            '( `showid` IN ( {} ) )'.format(showid),
            (),
            filmui,
            False,
            True,
            10000
        )

    def _search_channels_condition(self, condition, channelui):
        if self.conn is None:
            return
        try:
            if condition is None:
                query = 'SELECT `id`,`channel`,0 AS `count` FROM `channel`'
                qtail = ''
            else:
                query = 'SELECT channel.id AS `id`,`channel`,COUNT(*) AS `count` FROM `film` LEFT JOIN `channel` ON channel.id=film.channelid'
                qtail = ' WHERE ' + condition + self.sql_cond_nofuture + \
                    self.sql_cond_minlength + ' GROUP BY channel.id'
            self.logger.info('MySQL Query: {}', query + qtail)

            cursor = self.conn.cursor()
            cursor.execute(query + qtail)
            channelui.begin()
            for (channelui.channelid, channelui.channel, channelui.count) in cursor:
                channelui.add()
            channelui.end()
            cursor.close()
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

    def _search_condition(self, condition, params, filmui, showshows, showchannels, maxresults, limiting=True):
        if self.conn is None:
            return 0
        try:
            if limiting:
                sql_cond_limit = self.sql_cond_nofuture + self.sql_cond_minlength
            else:
                sql_cond_limit = ''
            self.logger.info(
                'MySQL Query: {}',
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit
            )
            cursor = self.conn.cursor()
            cursor.execute(
                self.sql_query_filmcnt +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            (results, ) = cursor.fetchone()
            if maxresults and results > maxresults:
                self.notifier.show_limit_results(maxresults)
            cursor.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            filmui.begin(showshows, showchannels)
            for (filmui.filmid, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd) in cursor:
                filmui.add(total_items=results)
            filmui.end()
            cursor.close()
            return results
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
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
            condition = '( film.id={} )'.format(filmid)
            self.logger.info(
                'MySQL Query: {}',
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
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return None

    def get_status(self, reconnect=True):
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
            'tot_mov': 0
        }
        if self.conn is None:
            status['status'] = "UNINIT"
            return status
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM `status` LIMIT 1')
            result = cursor.fetchall()
            cursor.close()
            self.conn.commit()
            if not result:
                status['status'] = "NONE"
                return status
            status['modified'] = result[0][1]
            status['status'] = result[0][2]
            status['lastupdate'] = result[0][3]
            status['filmupdate'] = result[0][4]
            status['fullupdate'] = result[0][5]
            status['add_chn'] = result[0][6]
            status['add_shw'] = result[0][7]
            status['add_mov'] = result[0][8]
            status['del_chn'] = result[0][9]
            status['del_shw'] = result[0][10]
            status['del_mov'] = result[0][11]
            status['tot_chn'] = result[0][12]
            status['tot_shw'] = result[0][13]
            status['tot_mov'] = result[0][14]
            return status
        except mysql.connector.Error as err:
            if err.errno == -1 and reconnect:
                # connection lost. Retry:
                if reconnect:
                    self.logger.warn(
                        'Database connection lost. Trying to reconnect...')
                    if self.reinit():
                        self.logger.info('Reconnection successful')
                        return self.get_status(False)
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            status['status'] = "UNINIT"
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
        if status is None:
            return
        old = self.get_status()
        new = self.get_status()
        if status is not None:
            new['status'] = status
        if lastupdate is not None:
            new['lastupdate'] = lastupdate
        if filmupdate is not None:
            new['filmupdate'] = filmupdate
        if fullupdate is not None:
            new['fullupdate'] = fullupdate

        if (old['status'] == 'NONE'):
            try:
                cursor = self.conn.cursor()
                # insert status
                cursor.execute("""
                    INSERT INTO `status` (
                        `id`, `status`, `lastupdate`, `filmupdate`, `fullupdate`
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                    """, (
                    1, status, lastupdate, filmupdate, fullupdate
                )
                               )
                cursor.close()
                self.conn.commit()
            except mysql.connector.Error as err:
                self.logger.error('Database error: {}, {}', err.errno, err)
                self.notifier.show_database_error(err)
                return
            if (status != 'IDLE'):
                return

        if (status != 'IDLE'):
            try:
                cursor = self.conn.cursor()
                # insert status
                cursor.execute("""
                    UPDATE `status` 
                        set
                            `status` = %s, `lastupdate` = %s, `filmupdate` = %s, `fullupdate` = %s
                        where id=1
                    """, (
                    new['status'],
                    new['lastupdate'],
                    new['filmupdate'],
                    new['fullupdate']
                )
                               )
                cursor.close()
                self.conn.commit()
            except mysql.connector.Error as err:
                self.logger.error('Database error: {}, {}', err.errno, err)
                self.notifier.show_database_error(err)
            return

        if tot_chn is not None:
            new['add_chn'] = max(0, tot_chn - old['tot_chn'])
        if tot_shw is not None:
            new['add_shw'] = max(0, tot_shw - old['tot_shw'])
        if tot_mov is not None:
            new['add_mov'] = max(0, tot_mov - old['tot_mov'])
        if tot_chn is not None:
            new['del_chn'] = max(0, old['tot_chn'] - tot_chn)
        if tot_shw is not None:
            new['del_shw'] = max(0, old['tot_shw'] - tot_shw)
        if tot_mov is not None:
            new['del_mov'] = max(0, old['tot_mov'] - tot_mov)
        if tot_chn is not None:
            new['tot_chn'] = tot_chn
        if tot_shw is not None:
            new['tot_shw'] = tot_shw
        if tot_mov is not None:
            new['tot_mov'] = tot_mov
        # TODO: we should only write, if we have changed something...
        new['modified'] = int(time.time())
        try:
            cursor = self.conn.cursor()
            # insert status
            cursor.execute("""
                UPDATE `status`
                    SET `modified`        = %s,
                        `status`        = %s,
                        `lastupdate`    = %s,
                        `filmupdate`    = %s,
                        `fullupdate`    = %s,
                        `add_chn`        = %s,
                        `add_shw`        = %s,
                        `add_mov`        = %s,
                        `del_chm`        = %s,
                        `del_shw`        = %s,
                        `del_mov`        = %s,
                        `tot_chn`        = %s,
                        `tot_shw`        = %s,
                        `tot_mov`        = %s
                    where id = 1
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
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)

    @staticmethod
    def supports_update():
        """
        Returns `True` if the selected database driver supports
        updating a local copy
        """
        return True

    def reinit(self):
        """ Reinitializes the database connection """
        self.exit()
        return self.init(False, False)

    def ft_init(self):
        """
        Initializes local database for updating
        """
        # prevent concurrent updating
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE  `status`
            SET     `modified`      = %s,
                    `status`        = 'UPDATING'
            WHERE   ( `status` != 'UPDATING' )
                    OR
                    ( `modified` < %s )
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

    def ft_update_start(self, full):
        """
        Begins a local update procedure

        Args:
            full(bool): if `True` a full update is started
        """
        param = (1,) if full else (0,)
        try:
            cursor = self.conn.cursor()
            cursor.execute('truncate film_import')
            status = self.get_status(False)
            return (status['tot_chn'], status['tot_shw'], status['tot_mov'])
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (0, 0, 0,)

    def ft_update_end(self, delete):
        """
        Finishes a local update procedure

        Args:
            delete(bool): if `True` all records not updated
                will be deleted
        """
        try:
            del_chn = 0
            del_shw = 0
            del_mov = 0
            tot_chn = 0
            tot_shw = 0
            tot_mov = 0

            cursor = self.conn.cursor()
            if delete:
                cursor.execute("""
                    delete f1 from film f1
                    left join film_import f2
                    on f1.idhash = f2.idhash
                    where f2.idhash is null
                """)
                del_mov = cursor.rowcount

            cursor.execute("""
                insert into `channel` (channel)
                    select distinct fi.`channel`from film_import fi
                    left join `channel` c on fi.channel=c.channel
                    where c.channel is null
            """)

            cursor.execute("""
                insert into `show` (channelid, `show`, `search`)
                    select distinct c.`id` channelid, fi.`show`, fi.`showsearch`
                    from `channel` c, film_import fi
                    left join `show` s on fi.show=s.show
                    where fi.channel=c.channel
                    and s.show is null
            """)

            cursor.execute("""
                delete c1 from `channel` c1
                    inner join `channel` c2
                    where c1.id > c2.id
                    and c1.channel = c2.channel
            """)
            del_chn = cursor.rowcount

            cursor.execute("""
                delete s1 from `show` s1
                    inner join `show` s2
                    where s1.id > s2.id
                    and s1.search = s2.search
            """)
            del_shw = cursor.rowcount

            cursor.execute("""
                insert into `film` (idhash, channelid, showid, title, `search`,
                    aired, duration, website, url_sub, url_video, url_video_sd,
                    url_video_hd, airedepoch)
                    select distinct fi.idhash, c.`id` channelid, s.`id` showid, fi.title, fi.`search`, fi.aired, fi.duration, fi.website, fi.url_sub, fi.url_video, fi.url_video_sd, fi.url_video_hd, fi.airedepoch
                        from `channel` c, `show` s , film_import fi
                        left join film f on fi.idhash=f.idhash
                        where fi.channel=c.channel
                        and fi.showsearch=s.search
                        and f.idhash is null
            """)

            cursor.execute("""truncate film_import""");

            cursor.close()
            self.conn.commit()

            cursor = self.conn.cursor()
            cursor.execute('SELECT count(*) c FROM `channel`')
            r = cursor.fetchall()
            cursor.close()
            if len(r) == 1:
                tot_chn = r[0][0]

            cursor = self.conn.cursor()
            cursor.execute('SELECT count(*) c FROM `show`')
            r = cursor.fetchall()
            cursor.close()
            if len(r) == 1:
                tot_shw = r[0][0]

            cursor = self.conn.cursor()
            cursor.execute('SELECT count(*) c FROM `film`')
            r = cursor.fetchall()
            cursor.close()
            if len(r) == 1:
                tot_mov = r[0][0]

        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
        return (del_chn, del_shw, del_mov, tot_chn, tot_shw, tot_mov,)

    def ft_insert_film(self, film, commit=True):
        """
        Inserts a film emtry into the database

        Args:
            film(Film): a film entry

            commit(bool, optional): the operation will be
                commited immediately. Default is `True`
        """
        channel = film['channel'][:64]
        show = film['show'][:128]
        title = film['title'][:128]
        hashkey = hashlib.md5((channel + ':' + show + ':' + film["url_video"]).encode('utf-8')).hexdigest()

        try:
            self.sqlValues += """ (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),"""
            self.sqlData += [
                hashkey,
                channel,
                show,
                mvutils.make_search_string(show),
                title,
                mvutils.make_search_string(title),
                film["aired"],
                film["duration"],
                film["size"],
                film["description"],
                film["website"],
                film["url_sub"],
                film["url_video"],
                film["url_video_sd"],
                film["url_video_hd"],
                film["airedepoch"],
            ]

            return (0, 0, 0, 1,)

        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.ShowDatabaseError(err)
        return (0, 0, 0, 0,)

    def ft_flush_insert(self):
        """
        Dump collected data to db using bulk inserts
        """
        rows = len(self.sqlData)
        if rows > 0:
            if rows == self.flush_block_size() * self.filmImportColumns:
                self.blockCursor.execute(self.blockInsert, self.sqlData)
            else:
                cursor = self.conn.cursor()
                sql = self.build_insert(len(self.sqlData) / self.filmImportColumns)
                cursor.execute(sql, self.sqlData)
                cursor.close()
            self.conn.commit()
        self.clear_insert_data()

    def _get_schema_version(self):
        """
        Read current schema version from status record
        """
        if self.conn is None:
            return 0
        cursor = self.conn.cursor()
        try:
            cursor.execute('SELECT `version` FROM `status` LIMIT 1')
            (version, ) = cursor.fetchone()
            del cursor
            return version
        except mysql.connector.errors.ProgrammingError:
            return 1
        except mysql.connector.Error as err:
            self.logger.error('Database error: {}, {}', err.errno, err)
            self.notifier.show_database_error(err)
            return 0

    def _handle_database_update(self, convert, version=None):
        if version is None:
            return self._handle_database_update(convert, self._get_schema_version())
        if version == 0:
            # should never happen - something went wrong...
            self.Exit()
            return False
        elif version == 3:
            # current version
            return True
        elif convert is False:
            # do not convert (Addon threads)
            # self.Exit()
            self.notifier.ShowUpdatingScheme()
            return False
        elif version == 1:
            # convert from 1 to 2
            self.logger.info('Converting database to version 2')
            self.notifier.ShowUpdateSchemeProgress()
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT @@SESSION.sql_mode')
                (sql_mode,) = cursor.fetchone()
                self.logger.info('Current SQL mode is {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = ""')

                self.logger.info('Reducing channel name length...')
                cursor.execute('ALTER TABLE `channel` CHANGE COLUMN `channel` `channel` varchar(64) NOT NULL')
                self.notifier.UpdateUpdateSchemeProgress(5)
                self.logger.info('Reducing show name length...')
                cursor.execute(
                    'ALTER TABLE `show` CHANGE COLUMN `show` `show` varchar(128) NOT NULL, CHANGE COLUMN `search` `search` varchar(128) NOT NULL')
                self.notifier.UpdateUpdateSchemeProgress(10)
                self.logger.info('Reducing film title length...')
                cursor.execute(
                    'ALTER TABLE `film` CHANGE COLUMN `title` `title` varchar(128) NOT NULL, CHANGE COLUMN `search` `search` varchar(128) NOT NULL')
                self.notifier.UpdateUpdateSchemeProgress(65)
                self.logger.info('Deleting old dupecheck index...')
                cursor.execute('ALTER TABLE `film` DROP KEY `dupecheck`')
                self.logger.info('Creating and filling new column idhash...')
                cursor.execute('ALTER TABLE `film` ADD COLUMN `idhash` varchar(32) NULL AFTER `id`')
                self.notifier.UpdateUpdateSchemeProgress(82)
                cursor.execute(
                    'UPDATE `film` SET `idhash`= MD5( CONCAT( `channelid`, ":", `showid`, ":", `url_video` ) )')
                self.notifier.UpdateUpdateSchemeProgress(99)
                self.logger.info('Creating new dupecheck index...')
                cursor.execute('ALTER TABLE `film` ADD KEY `dupecheck` (`idhash`)')
                self.logger.info('Adding version info to status table...')
                cursor.execute('ALTER TABLE `status` ADD COLUMN `version` INT(11) NOT NULL DEFAULT 2')
                self.logger.info('Resetting SQL mode to {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = %s', (sql_mode,))
                self.logger.info('Scheme successfully updated to version 2')
                return self._handle_database_update(convert, self._get_schema_version())
            except mysql.connector.Error as err:
                self.logger.error('=== DATABASE SCHEME UPDATE ERROR: {} ===', err)
                self.Exit()
                self.notifier.CloseUpdateSchemeProgress()
                self.notifier.show_database_error(err)
                return False
        elif version == 2:
            # convert from 2 to 3
            self.logger.info('Converting database to version 3')
            self.notifier.ShowUpdateSchemeProgress()
            try:
                cursor = self.conn.cursor()
                cursor.execute('SELECT @@SESSION.sql_mode')
                (sql_mode,) = cursor.fetchone()
                self.logger.info('Current SQL mode is {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = ""')

                self.logger.info('Dropping touched column on channel...')
                cursor.execute('ALTER TABLE `channel` DROP  `touched`')
                self.notifier.UpdateUpdateSchemeProgress(5)
                self.logger.info('Dropping touched column on show...')
                cursor.execute('ALTER TABLE `show` DROP  `touched`')
                self.notifier.UpdateUpdateSchemeProgress(15)
                self.logger.info('Adding primary key to staus...')
                cursor.execute(
                    "ALTER TABLE `status` ADD `id` INT(4) UNSIGNED NOT NULL DEFAULT '1' FIRST, ADD PRIMARY KEY (`id`)")
                self.notifier.UpdateUpdateSchemeProgress(20)
                self.logger.info('Dropping touched column on film...')
                cursor.execute('ALTER TABLE `film` DROP  `touched`, CHANGE idhash idhash varchar(32) NOT NULL')
                self.notifier.UpdateUpdateSchemeProgress(60)

                self.logger.info('Dropping stored procedure ftInsertChannel...')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftInsertChannel`')
                self.notifier.UpdateUpdateSchemeProgress(65)

                self.logger.info('Dropping stored procedure ftInsertFilm...')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftInsertFilm`')
                self.notifier.UpdateUpdateSchemeProgress(70)

                self.logger.info('Dropping stored procedure ftInsertShow...')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftInsertShow`')
                self.notifier.UpdateUpdateSchemeProgress(75)

                self.logger.info('Dropping stored procedure ftUpdateEnd...')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftUpdateEnd`')
                self.notifier.UpdateUpdateSchemeProgress(80)

                self.logger.info('Dropping stored procedure ftUpdateStart...')
                cursor.execute('DROP PROCEDURE IF EXISTS `ftUpdateStart`')
                self.notifier.UpdateUpdateSchemeProgress(85)

                self.logger.info('Creating tabele film_import...')
                cursor.execute("""CREATE TABLE IF NOT EXISTS `film_import` (
                    `idhash` varchar(32) NOT NULL,
                    `channel` varchar(64) NOT NULL,
                    `show` varchar(128) NOT NULL,
                    `showsearch` varchar(128) NOT NULL,
                    `title` varchar(128) NOT NULL,
                    `search` varchar(128) NOT NULL,
                    `aired` timestamp NULL DEFAULT NULL,
                    `duration` time DEFAULT NULL,
                    `size` int(11) DEFAULT NULL,
                    `description` longtext,
                    `website` varchar(384) DEFAULT NULL,
                    `url_sub` varchar(384) DEFAULT NULL,
                    `url_video` varchar(384) DEFAULT NULL,
                    `url_video_sd` varchar(384) DEFAULT NULL,
                    `url_video_hd` varchar(384) DEFAULT NULL,
                    `airedepoch` int(11) DEFAULT NULL,
                    KEY `idhash` (`idhash`),
                    KEY `channel` (`channel`),
                    KEY `show` (`show`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC
                """)
                self.notifier.UpdateUpdateSchemeProgress(95)
                cursor.execute('UPDATE `status` set `version` = 3')
                self.logger.info('Resetting SQL mode to {}', sql_mode)
                cursor.execute('SET SESSION sql_mode = %s', (sql_mode,))
                self.logger.info('Scheme successfully updated to version 3')
                self.notifier.CloseUpdateSchemeProgress()
            except mysql.connector.Error as err:
                self.logger.error('=== DATABASE SCHEME UPDATE ERROR: {} ===', err)
                self.Exit()
                self.notifier.CloseUpdateSchemeProgress()
                self.notifier.show_database_error(err)
                return False
        return True

    def _handle_database_initialization(self):
        self.logger.info('Database creation started')

        cursor = None
        dbcreated = False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                'CREATE DATABASE IF NOT EXISTS `{}` DEFAULT CHARACTER SET utf8'.format(self.settings.database))
            dbcreated = True
            self.conn.database = self.settings.database
            cursor.execute('SET FOREIGN_KEY_CHECKS=0')
            self.conn.commit()
            cursor.execute("""
                CREATE TABLE `channel` (
                    `id`            int(11)            NOT NULL AUTO_INCREMENT,
                    `dtCreated`        timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `channel`        varchar(64)        NOT NULL,
                    PRIMARY KEY                        (`id`),
                    KEY                `channel`        (`channel`)
                ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()

            cursor.execute("""
                CREATE TABLE `film` (
                    `id`            int(11)            NOT NULL AUTO_INCREMENT,
                    `idhash`        varchar(32)        DEFAULT NULL,
                    `dtCreated`        timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `channelid`        int(11)            NOT NULL,
                    `showid`        int(11)            NOT NULL,
                    `title`            varchar(128)    NOT NULL,
                    `search`        varchar(128)    NOT NULL,
                    `aired`            timestamp        NULL DEFAULT NULL,
                    `duration`        time            DEFAULT NULL,
                    `size`            int(11)            DEFAULT NULL,
                    `description`    longtext,
                    `website`        varchar(384)    DEFAULT NULL,
                    `url_sub`        varchar(384)    DEFAULT NULL,
                    `url_video`        varchar(384)    DEFAULT NULL,
                    `url_video_sd`    varchar(384)    DEFAULT NULL,
                    `url_video_hd`    varchar(384)    DEFAULT NULL,
                    `airedepoch`    int(11)            DEFAULT NULL,
                    PRIMARY KEY                        (`id`),
                    KEY                `index_1`        (`showid`,`title`),
                    KEY                `index_2`        (`channelid`,`title`),
                    KEY                `dupecheck`        (`idhash`),
                    CONSTRAINT `FK_FilmChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
                    CONSTRAINT `FK_FilmShow` FOREIGN KEY (`showid`) REFERENCES `show` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
                ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `film_import` (
                    `idhash` varchar(32) NOT NULL,
                    `channel` varchar(64) NOT NULL,
                    `show` varchar(128) NOT NULL,
                    `showsearch` varchar(128) NOT NULL,
                    `title` varchar(128) NOT NULL,
                    `search` varchar(128) NOT NULL,
                    `aired` timestamp NULL DEFAULT NULL,
                    `duration` time DEFAULT NULL,
                    `size` int(11) DEFAULT NULL,
                    `description` longtext,
                    `website` varchar(384) DEFAULT NULL,
                    `url_sub` varchar(384) DEFAULT NULL,
                    `url_video` varchar(384) DEFAULT NULL,
                    `url_video_sd` varchar(384) DEFAULT NULL,
                    `url_video_hd` varchar(384) DEFAULT NULL,
                    `airedepoch` int(11) DEFAULT NULL,
                    KEY `idhash` (`idhash`),
                    KEY `channel` (`channel`),
                    KEY `show` (`show`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC
            """)
            self.conn.commit()
            cursor.execute("""
                CREATE TABLE `show` (
                    `id`            int(11)            NOT NULL AUTO_INCREMENT,
                    `dtCreated`        timestamp        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    `channelid`        int(11)            NOT NULL,
                    `show`            varchar(128)    NOT NULL,
                    `search`        varchar(128)    NOT NULL,
                    PRIMARY KEY                        (`id`),
                    KEY                `show`            (`show`),
                    KEY                `search`        (`search`),
                    KEY                `combined_1`    (`channelid`,`search`),
                    KEY                `combined_2`    (`channelid`,`show`),
                    CONSTRAINT `FK_ShowChannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
                ) ENGINE=InnoDB ROW_FORMAT=DYNAMIC DEFAULT CHARSET=utf8;
            """)
            self.conn.commit()

            cursor.execute("""
                CREATE TABLE `status` (
                 `id` int(4) unsigned NOT NULL DEFAULT '1',
                 `modified` int(11) NOT NULL,
                 `status` varchar(255) NOT NULL,
                 `lastupdate` int(11) NOT NULL,
                 `filmupdate` int(11) NOT NULL,
                 `fullupdate` int(1) NOT NULL,
                 `add_chn` int(11) NOT NULL,
                 `add_shw` int(11) NOT NULL,
                 `add_mov` int(11) NOT NULL,
                 `del_chm` int(11) NOT NULL,
                 `del_shw` int(11) NOT NULL,
                 `del_mov` int(11) NOT NULL,
                 `tot_chn` int(11) NOT NULL,
                 `tot_shw` int(11) NOT NULL,
                 `tot_mov` int(11) NOT NULL,
                 `version` int(11) NOT NULL DEFAULT '3',
                 PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8 ROW_FORMAT=DYNAMIC
            """)
            self.conn.commit()

            cursor.execute('INSERT INTO `status` VALUES (1, 0,"IDLE",0,0,0,0,0,0,0,0,0,0,0,0,3);')
            self.conn.commit()

            cursor.execute('SET FOREIGN_KEY_CHECKS=1')
            self.conn.commit()

            cursor.close()
            self.logger.info('Database creation successfully completed')
            return True
        except mysql.connector.Error as err:
            self.logger.error('=== DATABASE CREATION ERROR: {} ===', err)
            self.notifier.show_database_error(err)
            try:
                if dbcreated:
                    cursor.execute('DROP DATABASE `{}`'.format(self.settings.database))
                    self.conn.commit()
                if cursor is not None:
                    cursor.close()
                    del cursor
                if self.conn is not None:
                    self.conn.close()
                    self.conn = None
            except mysql.connector.Error as err:
                # should never happen
                self.conn = None
        return False