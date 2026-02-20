# -*- coding: utf-8 -*-
"""
The local SQlite database module

Copyright 2017-2019, Leo Moll
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long

import resources.lib.appContext as appContext


class StoreSQLiteSetup(object):

    def __init__(self, dbCon):
        self.logger = appContext.MVLOGGER.get_new_logger('StoreSQLiteSetup')
        self.conn = dbCon
        self._setupScript = """
PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for film
-- ----------------------------
DROP TABLE IF EXISTS "film_meta";
CREATE TABLE "film_meta" (
     "idhash" TEXT(32,0) NOT NULL,
     "dtCreated" integer(11,0) NOT NULL DEFAULT 0,
     "touched" integer(1,0) NOT NULL DEFAULT 1,
     "channel" TEXT(32,0) NOT NULL COLLATE NOCASE,
     "showid" TEXT(8,0) NOT NULL,
     "showname" TEXT(128,0) NOT NULL COLLATE NOCASE,
     "title" TEXT(128,0) NOT NULL COLLATE NOCASE,
     "aired" integer(11,0),
     "duration" integer(11,0),
     "description" TEXT(1024,0) COLLATE NOCASE,
     "url_sub_exists" TEXT(1,0)
);
-- ----------------------------
CREATE INDEX idx_idhash_meta ON film_meta (idhash);
-------------------------------
DROP TABLE IF EXISTS "film_video";
CREATE TABLE "film_video" (
     "idhash" TEXT(32,0) NOT NULL,
     "touched" integer(1,0) NOT NULL DEFAULT 1,
     "url_sub" TEXT(2048,0),
     "url_video" TEXT(2048,0),
     "url_video_sd" TEXT(2048,0),
     "url_video_hd" TEXT(2048,0)
);
--
CREATE INDEX idx_idhash_video ON film_video (idhash);
-- ----------------------------
--  Table structure for status
-- ----------------------------
DROP TABLE IF EXISTS "status";
CREATE TABLE "status" (
     "status" TEXT(32,0),
     "lastupdate" integer(11,0),
     "lastFullUpdate" integer(11,0),
     "filmupdate" integer(11,0),
     "version" integer(11,0)
);

INSERT INTO status (status, lastupdate, lastFullUpdate, filmupdate, version) values ('IDLE', 0, 0, 0, 4);

-- ----------------------------
DROP VIEW IF EXISTS "film";
CREATE VIEW "film" AS
SELECT m.idhash, dtCreated, channel, showid, showname, title, aired, duration, description, url_sub, url_video, url_video_sd, url_video_hd from film_meta m left outer join film_video v on m.idhash = v.idhash;

PRAGMA foreign_keys = true;
        """

    def setupDatabase(self):
        self.logger.debug('Start DB setup')
        self.conn.reset()
        self.conn.getConnection().executescript(self._setupScript)
        self.conn.getConnection().commit()
        self.logger.debug('End DB setup')
    def migration34(self):
        setupScriptMigration34 = """
            UPDATE status SET status = 'MIG';
            INSERT INTO film_meta select idhash, dtCreated, touched, channel, showid, showname, title, aired, duration, description, case when url_sub = '' then '' else '1' end as url_sub_exists FROM film_bk;
            INSERT INTO film_video select idhash, touched, url_sub, url_video, url_video_sd, url_video_hd FROM film_bk;
            DROP TABLE film_bk;
            VACUUM;
            UPDATE status SET status = 'IDLE';
            """
        self.logger.debug('Start DB migration34')
        self.conn.getConnection().executescript("ALTER TABLE film RENAME TO film_bk; DROP TABLE status;")
        self.logger.debug('Start 2 DB migration34')
        self.conn.getConnection().executescript(self._setupScript)
        self.logger.debug('Start 3 DB migration34')
        self.conn.getConnection().executescript(setupScriptMigration34)
        self.logger.debug('Start 4 DB migration34')
        self.conn.getConnection().commit()
        self.logger.debug('End DB migration34')
        

