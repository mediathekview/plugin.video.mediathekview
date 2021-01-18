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
from resources.lib.model.film import Film
import resources.lib.extendedSearchModel as ExtendedSearchModel


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
        ## IMPORT SQL
        self.sql_pStmtInsert = """
            INSERT INTO film (
                idhash, touched, dtCreated, channel, showid, showname, title,
                aired, duration, size, description,
                url_sub, url_video, url_video_sd, url_video_hd
            )
            VALUES (
                ?, 1, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?
            )"""
        self.sql_pStmtUpdate = """UPDATE film SET touched = touched+1 WHERE idhash = ?"""
    
    ## ABSTRACT
    def getConnection(self):
        """ Abstract method to implement the database specific connect """
        return None

    ## ABSTRACT
    def exit(self):
        """ Abstract method to implement the database specific disconnect """
        pass

    ## OVERWRITE
    def getDatabaseStatus(self):
        """ 
        Hook to overwrite the database specific get status function. 
        The output is used in the update trigger to find out needed operations
        """
        return self.get_status()
    
    ## OVERWRITE for mysql
    def execute(self, aStmt, aParams = None):
        """ execute a single sql stmt and return the resultset """
        start = time.time()
        self.logger.info('query: {} params {}', aStmt, aParams)
        cursor = self.getConnection().cursor()
        if aParams is None:
            cursor.execute(aStmt)
        else:
            cursor.execute(aStmt, aParams)
        rs = cursor.fetchall()
        cursor.close()
        self.logger.info('execute: {} rows in {} sec', len(rs), time.time() - start)
        return rs
    
    def executeUpdate(self, aStmt, aParams):
        """ execute a single update stmt and commit """
        cursor = self.getConnection().cursor()
        cursor.execute(aStmt, aParams)
        rs = cursor.rowcount
        #self.logger.info(" rowcount executeUpdate {}" , rs )
        cursor.close()
        self.getConnection().commit()
        return rs

    def executemany(self, aStmt, aParams = None):
        """ execute a bulk prepared Stmt """
        cursor = self.getConnection().cursor()
        cursor.executemany(aStmt, aParams)
        rs = cursor.rowcount
        #self.logger.info(" rowcount executemany {}" , rs )
        cursor.close()
        self.getConnection().commit()
        return rs

    ### All this just because mysql is not compliant to sql standard
    def getImportPreparedStmtInsert(self):
            return self.sql_pStmtInsert

    def getImportPreparedStmtUpdate(self):
            return self.sql_pStmtUpdate

    ###
    def extendedSearchQuery(self, esModel):
        rs = None 
        params = []
        sql = self.sql_query_films
        sql += ' WHERE (1=1)'
        ##
        (mixedSearchCondition, mixedSearchParams) = esModel.generateShowTitleDescription()
        if (mixedSearchCondition != ''):
            sql += ' AND ' + mixedSearchCondition
            params.extend(mixedSearchParams)
        ##
        (excludeCondition, excludeParams) = esModel.generateExclude()
        if (excludeCondition != ''):
            sql += ' AND ' + excludeCondition
            params.extend(excludeParams)
        ##
        (channelCondition, channelParams) = esModel.generateChannel()
        if (channelCondition != ''):
            sql += ' AND ' + channelCondition
            params.extend(channelParams)
        ##
        (showCondition, showParams) = esModel.generateShow()
        if (showCondition != ''):
            sql += ' AND ' + showCondition
            params.extend(showParams)
        ##
        (showIdCondition, showIdParams) = esModel.generateShowId()
        if (showIdCondition != ''):
            sql += ' AND ' + showIdCondition
            params.extend(showIdParams)
        ##
        (showStartLetterCondition, showStartLetterParams) = esModel.generateShowStartLetter()
        if (showStartLetterCondition != ''):
            sql += ' AND ' + showStartLetterCondition
            params.extend(showStartLetterParams)
        ##
        ## from settings
        ##
        minLengthCondition = esModel.generateMinLength()
        if minLengthCondition != '':
            sql += ' AND ' + minLengthCondition
        ## no future
        noTrailerCondition = esModel.generateIgnoreTrailer()
        if noTrailerCondition != '':
            sql += " AND " + noTrailerCondition
        ##
        recentOnlyCondition = esModel.generateRecentCondition()
        if recentOnlyCondition != '':
            sql += " AND " + recentOnlyCondition
        ##
        sql += ' ORDER BY aired DESC '
        ##
        maxRowsCondition = esModel.generateMaxRows()
        if (maxRowsCondition != ''):
             sql += maxRowsCondition
        ##
        ##
        try:
            #
            rs = self.execute(sql, params)
            #
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        return rs
    ###
    ###
    def getQuickSearch(self, searchTerm):
        """
        Retrieve data for quick search
        We will check for search term to be (partially) present in showname or title
         
        Parameters
        ----------
        searchTerm : str, optional
            search term which is contained in showname or title
        Returns
        -------
        Array
            Resultset of the query
        """
        self.logger.info('getQuickSearch')
        #
        cached_data = self._cache.load_cache('quickSearch', searchTerm)
        if cached_data is not None:
            rs = cached_data;
        else:
            esModel = ExtendedSearchModel.ExtendedSearchModel('')
            esModel.setShow(searchTerm)
            esModel.setTitle(searchTerm)
            rs = self.extendedSearchQuery(esModel)
            self._cache.save_cache('quickSearch', searchTerm, rs)
        #
        return rs
    ###
    def getLivestreams(self):
        """
        Retrieve data for livestream screen
        """
        self.logger.info('getLivestreams')
        #
        cached_data = self._cache.load_cache('livestreams', '')
        if cached_data is not None:
            rs = cached_data;
        else:
            esModel = ExtendedSearchModel.ExtendedSearchModel('')
            esModel.reset()
            esModel.setShow('LIVESTREAM')
            esModel.setExactMatchForShow(True)
            rs = self.extendedSearchQuery(esModel)
            self._cache.save_cache('livestreams', '', rs)
        #
        return rs
    ###
    def getRecentFilms(self, channelId = ''):
        """
        Retrieve data for recent films
        """
        self.logger.info('getRecentFilms')
        #
        cached_data = self._cache.load_cache('recentFilms', channelId)
        if cached_data is not None:
            rs = cached_data
        else:
            esModel = ExtendedSearchModel.ExtendedSearchModel('')
            esModel.setRecentOnly(1)
            esModel.setChannel(channelId)
            rs = self.extendedSearchQuery(esModel)
            self._cache.save_cache('recentFilms', channelId, rs)
        #
        if len(rs) >= self.settings.getMaxResults():
            self.notifier.show_limit_results(self.settings.getMaxResults())
        #
        return rs
    ###
    def getFilms(self, channel = '', showIds = ''):
        """
        Retrieve data for recent films
        """
        self.logger.info('getFilms')
        #
        cached_data = self._cache.load_cache('films', showIds + channel)
        if cached_data is not None:
            rs = cached_data
        else:
            esModel = ExtendedSearchModel.ExtendedSearchModel('')
            esModel.setChannel(channel)
            esModel.setShowId(showIds)            
            rs = self.extendedSearchQuery(esModel)
            self._cache.save_cache('films', showIds + channel, rs)
        #
        if len(rs) >= self.settings.getMaxResults():
            self.notifier.show_limit_results(self.settings.getMaxResults())
        #
        return rs
    ###
    def getChannels(self):
        cached_data = self._cache.load_cache('channels', '')
        if cached_data is not None:
            return cached_data

        try:
            sql = "SELECT channel AS channelid, channel FROM film GROUP BY channel ORDER BY channel ASC"
            rs = self.execute(sql)
            self._cache.save_cache('channels', sql, rs)

        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        
        return rs
    ###
    def getChannelList(self):
        allChannel = []
        rs = self.getChannels()
        for row in rs:
            allChannel.append(row[0])
        return allChannel
    ###
    def getChannelsRecent(self):
        cached_data = self._cache.load_cache('channels_recent', '')
        if cached_data is not None:
            return cached_data

        try:
            sql = "SELECT channel channelid, channel || ' (' || count(*) || ')' description FROM film WHERE "
            ## recent
            sql += self.sql_cond_recent
            ## duration filter
            sql += self.sql_cond_nofuture
            ## no future
            sql += self.sql_cond_minlength
            ##
            sql += " GROUP BY channel ORDER BY channel asc"
            ##
            rs = self.execute(sql)
            ##
            self._cache.save_cache('channels_recent', sql, rs)

        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        
        return rs
    ###
    def getShowsByChannnel(self, channelId):
        cached_data = self._cache.load_cache('showsByChannel', channelId)
        if cached_data is not None:
            return cached_data

        try:
            sql = "SELECT showid, channel as channelId, showname, channel from film where (channel=?) "
            ## duration filter
            sql += self.sql_cond_nofuture
            ## no future
            sql += self.sql_cond_minlength
            ##
            sql += " GROUP BY showid, channel, showname ORDER BY showname asc"
            ##
            rs = self.execute(sql, (channelId,))
            ##
            self._cache.save_cache('showsByChannel', channelId, rs)

        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        
        return rs
    ###
    def getShowsByLetter(self, aLetter):
        cached_data = self._cache.load_cache('showsByLetter', aLetter)
        if cached_data is not None:
            return cached_data

        try:
            if self.settings.getGroupShow():
                sql = "SELECT GROUP_CONCAT(DISTINCT(showid)), GROUP_CONCAT(DISTINCT(channel)), showname, GROUP_CONCAT(DISTINCT(channel)) FROM film WHERE (showname like ?) "
            else:
                sql = "SELECT showid, channel as channelId, showname, channel FROM film WHERE (showname like ?) "
            ## duration filter
            sql += self.sql_cond_nofuture
            ## no future
            sql += self.sql_cond_minlength
            ##
            if self.settings.getGroupShow():
                sql += " GROUP BY showname ORDER BY showname asc"
            else:
                sql += " GROUP BY showid, channel, showname ORDER BY showname asc"
            ##
            rs = self.execute(sql, (aLetter+"%",))
            ##
            self._cache.save_cache('showsByLetter', aLetter, rs)
    
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        
        return rs
    ###
    def getStartLettersOfShows(self):
        cached_data = self._cache.load_cache('letters', '')
        if cached_data is not None:
            return cached_data

        try:
            sql = "SELECT UPPER(SUBSTR(showname,1,1)), COUNT(*) FROM film where SUBSTR(showname,1,1) between 'A' and 'Z' "
            ## recent
            sql += " AND " + self.sql_cond_recent
            ## duration filter
            sql += self.sql_cond_nofuture
            ## no future
            sql += self.sql_cond_minlength
            ##
            sql += " GROUP BY UPPER(SUBSTR(showname,1,1)) order by UPPER(SUBSTR(showname,1,1)) asc"
            ##
            rs = self.execute(sql)
            ##
            self._cache.save_cache('letters', '', rs)

        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise
        
        return rs    
    ###

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
            pass
            #self.logger.error('getStatus {}', err)
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
        pStmtInsert = self.getImportPreparedStmtInsert()
        pStmtUpdate = self.getImportPreparedStmtUpdate()
        #
        try:
            ##
            cursor = self.getConnection().cursor()
            ##
            insertArray = []
            updateCnt = 0
            insertCnt = 0
            for f in filmArray:
                cursor.execute(pStmtUpdate, (f[0],))
                rs = cursor.rowcount
                #self.logger.info('executeUpdate rs {} for {}', rs , f[0] )
                if rs == 0:
                    insertArray.append(f)
                    insertCnt +=1
                else:
                    updateCnt +=1
            #
            cursor.close()
            self.executemany(pStmtInsert, insertArray)
            #
            return (insertCnt, updateCnt)
        except Exception as err:
            self.logger.error('Database error: {}', err)
            self.notifier.show_database_error(err)
            raise 
