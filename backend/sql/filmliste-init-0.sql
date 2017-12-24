-- MySQL dump 10.13  Distrib 5.7.20, for Linux (x86_64)
--
-- Host: localhost    Database: filmliste
-- ------------------------------------------------------
-- Server version	5.7.20-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `filmliste`
--

/*!40000 DROP DATABASE IF EXISTS `filmliste`*/;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `filmliste` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `filmliste`;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channelid` int(11) NOT NULL,
  `category` varchar(255) NOT NULL,
  `search` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `category` (`category`),
  KEY `search` (`search`),
  KEY `FK_categorychannel_idx` (`channelid`),
  KEY `combined_1` (`channelid`,`search`),
  KEY `combined_2` (`channelid`,`category`),
  CONSTRAINT `FK_categorychannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `channel`
--

DROP TABLE IF EXISTS `channel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `channel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channel` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `channel` (`channel`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `film`
--

DROP TABLE IF EXISTS `film`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `film` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dtCreated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `touched` smallint(1) NOT NULL DEFAULT '1',
  `channelid` int(11) NOT NULL,
  `categoryid` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `search` varchar(255) NOT NULL,
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
  `geo` varchar(45) DEFAULT NULL,
  `new` int(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dupecheck` (`channelid`,`categoryid`,`url_video`),
  KEY `FK_filmcategory_idx` (`categoryid`),
  KEY `index_3` (`categoryid`,`title`),
  KEY `index_1` (`channelid`,`title`),
  CONSTRAINT `FK_filmcategory` FOREIGN KEY (`categoryid`) REFERENCES `category` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `FK_filmchannel` FOREIGN KEY (`channelid`) REFERENCES `channel` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'filmliste'
--

--
-- Dumping routines for database 'filmliste'
--
/*!50003 DROP PROCEDURE IF EXISTS `ftInsertFilm` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `ftInsertFilm`(
	_channel		VARCHAR(255),
	_category		VARCHAR(255),
	_catsearch		VARCHAR(255),
	_title			VARCHAR(255),
	_search			VARCHAR(255),
	_aired			TIMESTAMP,
	_duration		TIME,
	_size			INT(11),
	_description	LONGTEXT,
	_website		VARCHAR(384),
	_url_sub		VARCHAR(384),
	_url_video		VARCHAR(384),
	_url_video_sd	VARCHAR(384),
	_url_video_hd	VARCHAR(384),
	_airedepoch		INT(11),
	_geo			VARCHAR(45),
	_new			INT(1)
)
BEGIN
	DECLARE		id_				INT;
	DECLARE		channelid_		INT;
	DECLARE		categoryid_		INT;
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_cat_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	SELECT		`id`
	INTO		channelid_
	FROM		`channel` AS c
	WHERE		( c.channel = _channel );

	IF ( channelid_ IS NULL ) THEN
		INSERT INTO `channel` (
			`channel`
		)
		VALUES (
			_channel
		);
		SET channelid_	= LAST_INSERT_ID();
		SET cnt_chn_	= 1;
	ELSE
		UPDATE	`channel`
		SET		`touched` = 1
		WHERE	( `id` = channelid_ );
	END IF;

	SELECT		`id`
	INTO		categoryid_
	FROM		`category` AS c
	WHERE		( c.category = _category )
				AND
				( c.channelid = channelid_ );

	IF ( categoryid_ IS NULL ) THEN
		INSERT INTO `category` (
			`channelid`,
			`category`,
			`search`
		)
		VALUES (
			channelid_,
			_category,
			_catsearch
		);
		SET categoryid_	= LAST_INSERT_ID();
		SET cnt_cat_	= 1;
	ELSE
		UPDATE	`category`
		SET		`touched` = 1
		WHERE	( `id` = categoryid_ );
	END IF;

	SELECT		`id`
	INTO		id_
	FROM		`film` AS f
	WHERE		( f.channelid = channelid_ )
				AND
				( f.categoryid = categoryid_ )
				AND
				( f.url_video = _url_video );

	IF ( id_ IS NULL ) THEN
		INSERT INTO `film` (
			`channelid`,
			`categoryid`,
			`title`,
			`search`,
			`aired`,
			`duration`,
			`size`,
			`description`,
			`website`,
			`url_sub`,
			`url_video`,
			`url_video_sd`,
			`url_video_hd`,
			`airedepoch`,
			`geo`,
			`new`
		)
		VALUES (
			channelid_,
			categoryid_,
			_title,
			_search,
			IF(_aired = "1980-01-01 00:00:00", NULL, _aired),
			IF(_duration = "00:00:00", NULL, _duration),
			_size,
			_description,
			_website,
			_url_sub,
			_url_video,
			_url_video_sd,
			_url_video_hd,
			_airedepoch,
			_geo,
			_new
		);
		SET id_			= LAST_INSERT_ID();
		SET cnt_mov_	= 1;
	ELSE
		UPDATE	`film`
		SET		`touched` = 1
		WHERE	( `id` = id_ );
	END IF;
	SELECT	id_			AS `id`,
			cnt_chn_	AS `cnt_chn`,
			cnt_cat_	AS `cnt_cat`,
			cnt_mov_	AS `cnt_mov`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftUpdateEnd` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`10.65.%` PROCEDURE `ftUpdateEnd`()
BEGIN
	DECLARE		cnt_chn_		INT DEFAULT 0;
	DECLARE		cnt_cat_		INT DEFAULT 0;
	DECLARE		cnt_mov_		INT DEFAULT 0;

	SELECT		COUNT(*)
	INTO		cnt_chn_
	FROM		`channel`
	WHERE		( `touched` = 0 );

	SELECT		COUNT(*)
	INTO		cnt_cat_
	FROM		`category`
	WHERE		( `touched` = 0 );

	SELECT		COUNT(*)
	INTO		cnt_mov_
	FROM		`film`
	WHERE		( `touched` = 0 );

	-- delete untouched categories with no touched films
	DELETE FROM	`category`
	WHERE		( category.touched = 0 )
				AND
                ( ( SELECT SUM( film.touched ) FROM `film` WHERE film.categoryid = category.id ) = 0 );

	-- delete untouched films
	DELETE FROM	`film`
	WHERE		( touched = 0 );

	SELECT	
			cnt_chn_	AS `cnt_chn`,
			cnt_cat_	AS `cnt_cat`,
			cnt_mov_	AS `cnt_mov`;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `ftUpdateStart` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`10.65.%` PROCEDURE `ftUpdateStart`()
BEGIN
	UPDATE	`channel`
	SET		`touched` = 0;

	UPDATE	`category`
	SET		`touched` = 0;

	UPDATE	`film`
	SET		`touched` = 0;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-12-24 18:30:15
