# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""
# pylint: disable=too-many-lines,line-too-long
import time
import resources.lib.appContext as appContext
import resources.lib.mvutils as mvutils
from resources.lib.storeCache import StoreCache
from resources.lib.film import Film

class StoreQuery(object):

    def __init__(self):
        self.logger = appContext.MVLOGGER.get_new_logger('StoreQuery')
        self.notifier = appContext.MVNOTIFIER
        self.settings = appContext.MVSETTINGS
        self._cache = StoreCache()
        self.sql_query_films = "SELECT idhash, title, showname, channel, description, duration, size, aired, url_sub, url_video, url_video_sd, url_video_hd FROM film"
        self.sql_cond_recent = "( ( UNIX_TIMESTAMP() - {} ) <= {} )".format(
            "aired" if self.settings.getRecentMode() == 0 else "dtCreated",
            self.settings.getMaxAge()
        )
        self.sql_cond_nofuture = " AND ( aired < UNIX_TIMESTAMP() )" if self.settings.getNoFutur() else ""
        self.sql_cond_minlength = " AND ( duration >= %d )" % self.settings.getMinLength() if self.settings.getMinLength() > 0 else ""

    
    ## ABSTRACT
    def getConnection(self):
        return None

    ## ABSTRACT
    def exit(self):
        pass

    ## ABSTRACT
    def getDatabaseStatus(self):
        return self.get_status()
    
    def execute(self, aStmt, aParams = None):
        start = time.time()
        self.logger.info('query: {} params {}', aStmt, aParams)
        cursor = self.getConnection().cursor()
        if aParams is None:
            cursor.execute(aStmt)
        else:
            cursor.execute(aStmt, aParams)
        rs = cursor.fetchall()
        cursor.close()
        self.exit()
        self.logger.info('execute: {} rows in {} sec', len(rs), time.time() - start)
        return rs
    
    def executeUpdate(self, aStmt, aParams):
        cursor = self.getConnection().cursor()
        cursor.execute(aStmt, aParams)
        rs = cursor.rowcount
        #self.logger.info(" rowcount executeUpdate {}" , rs )
        cursor.close()
        return rs

    def executemany(self, aStmt, aParams = None):
        cursor = self.getConnection().cursor()
        cursor.executemany(aStmt, aParams)
        rs = cursor.rowcount
        #self.logger.info(" rowcount executemany {}" , rs )
        cursor.close()
        self.getConnection().commit()
        return rs
    
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
        searchcond = '( ( title LIKE ? ) OR ( showname LIKE ? ) OR ( description LIKE ? ) )' if extendedsearch is True else '( ( title LIKE ? ) OR ( showname LIKE ? ) )'
        searchparm = (searchmask, searchmask, searchmask) if extendedsearch is True else (
            searchmask, searchmask, )
        return self._search_condition(
            condition=searchcond,
            params=searchparm,
            filmui=filmui,
            showshows=True,
            showchannels=True,
            maxresults=self.settings.getMaxResults(),
            order='aired desc')

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
                condition=self.sql_cond_recent + " AND ( channel = ? )",
                params=(channelid, ),
                filmui=filmui,
                showshows=True,
                showchannels=False,
                maxresults=self.settings.getMaxResults(),
                order='aired desc'
            )

        return self._search_condition(
            condition=self.sql_cond_recent,
            params=(),
            filmui=filmui,
            showshows=True,
            showchannels=False,
            maxresults=self.settings.getMaxResults(),
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
            condition="( showname='LIVESTREAM' )",
            params=(),
            filmui=filmui,
            showshows=False,
            showchannels=False,
            maxresults=self.settings.getMaxResults(),
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
        cached_data = self._cache.load_cache('get_initials', channelid)
        if cached_data is not None:
            initialui.begin(channelid)
            for initial_data in cached_data:
                initialui.set_from_dict(initial_data)
                initialui.add()
            initialui.end()
            return
        cached_data = []
        if channelid != "":
            sqlStmt = """
                SELECT      UPPER(SUBSTR(showname,1,1)),COUNT(*)
                FROM        film
                WHERE       ( channel=? ) and (SUBSTR(showname,1,1) between 'A' and 'Z')
            """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                GROUP BY    UPPER(SUBSTR(showname,1,1))
            """
            rs = self.execute(sqlStmt, (channelid, ))
        else:
            sqlStmt = """
                SELECT      UPPER(SUBSTR(showname,1,1)),COUNT(*)
                FROM        film
                WHERE SUBSTR(showname,1,1) between 'A' and 'Z'
            """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                GROUP BY    UPPER(SUBSTR(showname,1,1))
            """
            rs = self.execute(sqlStmt)
        initialui.begin(channelid)
        for (initialui.initial, initialui.count) in rs:
            initialui.add()
            cached_data.append(initialui.get_as_dict())
        initialui.end()
        self._cache.save_cache('get_initials', channelid, cached_data)

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
        ##
        if channelid == "" and self.settings.getGroupShow():
            cache_condition = "SHOW:1:" + initial
        elif channelid == "":
            cache_condition = "SHOW:2:" + initial
        elif initial:
            cache_condition = "SHOW:3:" + channelid + ':' + initial
        else:
            cache_condition = "SHOW:3:" + channelid
        cached_data = self._cache.load_cache('get_shows', cache_condition)
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
            if channelid == "" and self.settings.getGroupShow():
                sqlstmt = """
                    SELECT      GROUP_CONCAT(DISTINCT(showid)),
                                GROUP_CONCAT(DISTINCT(channel)),
                                showname,
                                GROUP_CONCAT(DISTINCT(channel))
                    FROM        film
                    WHERE       ( showname LIKE ? )
                """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                    GROUP BY    showname
                """
                rs = self.execute(sqlstmt, (initial + '%', ))
            elif channelid == "":
                sqlstmt = """
                    SELECT      showid,
                                channel,
                                showname,
                                channel
                    FROM        film
                    WHERE       ( showname LIKE ? )
                """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                    GROUP BY showid, channel, showname, channel
                """
                rs = self.execute(sqlstmt, (initial + '%', ))
            elif initial:
                sqlstmt = """
                    SELECT      showid,
                                channel,
                                showname,
                                channel
                    FROM        film
                    WHERE
                                ( channel=? ) AND ( showname LIKE ? )
                    """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                    GROUP BY showid, channel, showname, channel
                """
                rs = self.execute(sqlstmt, (channelid, initial + '%', ))
            else:
                sqlstmt ="""
                    SELECT      showid,
                                channel,
                                showname,
                                channel
                    FROM        film
                    WHERE       ( channel=? )
                """ + self.sql_cond_nofuture + self.sql_cond_minlength + """
                    GROUP BY showid, channel, showname, channel
                """
                rs = self.execute(sqlstmt, (channelid, ))
            ##
            ##
            showui.begin(channelid)
            for (showui.showid, showui.channelid, showui.show, showui.channel) in rs:
                showui.add()
                if caching and self.settings.getCaching():
                    cached_data.append(showui.get_as_dict())
            showui.end()
            self._cache.save_cache('get_shows', cache_condition, cached_data)
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise

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
        if showid.find(',') == -1:
            # only one channel id
            self.logger.info('get_films for one show')
            return self._search_condition(
                condition="( showid = ? )",
                params=(showid,),
                filmui=filmui,
                showshows=False,
                showchannels=False,
                maxresults=self.settings.getMaxResults(),
                order='aired desc'
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
            maxresults=self.settings.getMaxResults(),
            order='aired desc'
        )

    def _search_channels_condition(self, condition, channelui, caching=True):
        cached_data = self._cache.load_cache('search_channels', condition)
        if cached_data is not None:
            channelui.begin()
            for channel_data in cached_data:
                channelui.set_from_dict(channel_data)
                channelui.add()
            channelui.end()
            return

        try:
            if condition is None:
                query = 'SELECT channel, channel, 0 as c FROM film group by channel'
                qtail = ''
            else:
                query = 'SELECT channel, channel, COUNT(*) as c FROM film'
                qtail = ' WHERE ' + condition + self.sql_cond_nofuture + self.sql_cond_minlength + ' GROUP BY channel'
            cached_data = []
            rs = self.execute(query + qtail)
            channelui.begin()
            for (channelui.channelid, channelui.channel, channelui.count) in rs:
                channelui.add()
                if caching and self.settings.getCaching():
                    cached_data.append(channelui.get_as_dict())
            channelui.end()
            self._cache.save_cache('search_channels', condition, cached_data)
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise

    def _search_condition(self, condition, params, filmui, showshows, showchannels, maxresults, limiting=True, caching=True, order=None):
        maxresults = int(maxresults)
        if limiting:
            sql_cond_limit = self.sql_cond_nofuture + self.sql_cond_minlength
        else:
            sql_cond_limit = ''

        cache_condition = condition + sql_cond_limit + \
            (' LIMIT {}'.format(maxresults + 1)
             if maxresults else '') + ':{}'.format(params)
        cached_data = self._cache.load_cache('search_films', cache_condition)
        if cached_data is not None:
            results = len(cached_data)
            filmui.begin(showshows, showchannels)
            for film_data in cached_data:
                filmui.set_from_dict(film_data)
                filmui.add(total_items=results)
            ##
            if len(cached_data) >= self.settings.getMaxResults():
                self.notifier.show_limit_results(maxresults)
            ##
            filmui.end()
            return results

        try:
            cached_data = []
            order = (' ORDER BY ' + order) if order is not None else ''
            rs = self.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition +
                sql_cond_limit +
                order +
                (' LIMIT {}'.format(maxresults + 1) if maxresults else ''),
                params
            )
            resultCount = 0
            for (filmui.filmid, filmui.title, filmui.show, filmui.channel, filmui.description, filmui.seconds, filmui.size, filmui.aired, filmui.url_sub, filmui.url_video, filmui.url_video_sd, filmui.url_video_hd) in rs:
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
            if resultCount >= maxresults:
                self.notifier.show_limit_results(maxresults)        
            self._cache.save_cache('search_films', cache_condition, cached_data)
            return results
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise

    def retrieve_film_info(self, filmid):
        """
        Retrieves the spcified film information
        from the database

        Args:
            filmid(id): database id of the requested film
        """
        try:
            condition = "( idhash='{}' )".format(filmid)
            rs = self.execute(
                self.sql_query_films +
                ' WHERE ' +
                condition
            )
            film = Film()
            for (film.filmid, film.title, film.show, film.channel, film.description, film.seconds, film.size, film.aired, film.url_sub, film.url_video, film.url_video_sd, film.url_video_hd) in rs:
                return film
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        return None

    def get_status(self):
        """ Retrieves the database status information """
        status = {
            'status': 'UNINIT',
            'lastUpdate': 0,
            'lastFullUpdate': 0,
            'filmUpdate': 0,
            'version': 0,
            'chn':0,
            'shw':0,
            'mov':0
        }
        try:
            result = self.execute('SELECT status, lastupdate, lastFullUpdate, filmupdate, version FROM status')
            status['status'] = result[0][0]
            status['lastUpdate'] = result[0][1]
            status['lastFullUpdate'] = result[0][2]
            status['filmUpdate'] = result[0][3]
            status['version'] = result[0][4]
            ##
            result = self.execute('SELECT count(distinct(channel)),count(distinct(showid)),count(*) FROM film')
            status['chn'] = result[0][0]
            status['shw'] = result[0][1]
            status['mov'] = result[0][2]
            ##
            self.settings.setDatabaseStatus(status['status'])
            self.settings.setLastUpdate(status['lastUpdate'])
            self.settings.setLastFullUpdate(status['lastFullUpdate'])
            self.settings.setDatabaseVersion(status['version'])
            
            ##
        except Exception as err:
            self.logger.error('getStatus {}', err)
            #self.settings.setDatabaseStatus('UNINIT')
        return status

    def set_status(self, pStatus = None, pLastupdate = None, pLastFullUpdate = None, pFilmupdate = None, pVersion = None):
        ## status in settings
        if pStatus is not None:
            self.settings.setDatabaseStatus(pStatus)
        if pLastupdate is not None:
            self.settings.setLastUpdate(pLastupdate)
        if pLastFullUpdate is not None:
            self.settings.setLastFullUpdate(pLastFullUpdate)
        if pVersion is not None:
            self.settings.setDatabaseVersion(pVersion)
        ## DB status table
        try:
            sqlStmt = 'UPDATE status SET status = COALESCE(?,status), lastupdate = COALESCE(?,lastupdate), lastFullUpdate = COALESCE(?,lastFullUpdate), filmupdate = COALESCE(?,filmupdate), version = COALESCE(?,version)'
            #cursor.execute(sqlStmt, (pStatus, pLastupdate, pLastFullUpdate, pFilmupdate, pVersion))
            rs = self.executeUpdate(sqlStmt, (pStatus, pLastupdate, pLastFullUpdate, pFilmupdate, pVersion))
            self.getConnection().commit()
            self.logger.info('Update Status {} lastupdate: {} lastFullUpdate: {} filmupdate: {} version: {}', pStatus, pLastupdate, pLastFullUpdate, pFilmupdate, pVersion)
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        ###
   
    def import_begin(self):
        try:
            cursor = self.getConnection().cursor()
            cursor.execute("update film set touched = 0")
            cursor.close()
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise

    def import_end(self):
        try:
            cursor = self.getConnection().cursor()
            cursor.execute("delete from film where touched = 0")
            cursor.close()
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
    
    def import_films(self, filmArray):
        #
        pStmtInsert = """
                    INSERT INTO `film` (
                        `idhash`,
                        `dtCreated`,
                        `channel`,
                        `showid`,
                        `showname`,
                        `title`,
                        `aired`,
                        `duration`,
                        `size`,
                        `description`,
                        `url_sub`,
                        `url_video`,
                        `url_video_sd`,
                        `url_video_hd`,
                        touched
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
                        1
                    )"""
        pStmtUpdate = """UPDATE film SET touched = touched+1 WHERE idhash = ?"""
        try:
            #cursor = self.getConnection().cursor()
            insertArray = []
            updateCnt = 0
            insertCnt = 0
            for f in filmArray:
                #cursor.execute(pStmtUpdate,(f[0],))
                rs = self.executeUpdate(pStmtUpdate, (f[0],))
                #self.logger.info('executeUpdate rs {} for {}', rs , f[0] )
                #if cursor.rowcount == 0:
                if rs == 0:
                    insertArray.append(f)
                    insertCnt +=1
                else:
                    updateCnt +=1
            #
            #cursor.executemany(pStmtInsert,insertArray)
            self.executemany(pStmtInsert, insertArray)
            
            #
            return (insertCnt, updateCnt)
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise 
