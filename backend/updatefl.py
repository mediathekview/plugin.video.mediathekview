# https://res.mediathekview.de/akt.xml

import sys, ijson, urllib, string
import mysql.connector

class filmreader:
	def __init__( self ):
		self.film = {
			"channel": "",
			"category": "",
			"catsearch": "",
			"title": "",
			"search": "",
			"aired": "1980-01-01 00:00:00",
			"duration": "00:00:00",
			"size": 0,
			"description": "",
			"website": "",
			"url_sub": "",
			"url_video": "",
			"url_video_sd": "",
			"url_video_hd": "",
			"airedepoch": 0,
			"geo": "",
			"new": 0
		}
		self.channels = 0
		self.categories = 0
		self.movies = 0
		self.index = 0
		self.count = 0
		self.conn = mysql.connector.connect(
			user = 'filmliste',
			password = 'MediathekView-2017',
			host = '127.0.0.1',
			database = 'filmliste'
		)

	def update_start( self ):
		print "Initialting update..."
		cursor = self.conn.cursor()
		cursor.callproc( 'ftUpdateStart' )
		cursor.close()
		self.conn.commit()

	def update_end( self ):
		print "New: channels:%d, categories:%d, movies:%d ..." % ( self.channels, self.categories, self.movies )
		cursor = self.conn.cursor()
		cursor.callproc( 'ftUpdateEnd' )
		for result in cursor.stored_results():
			for ( cnt_chn, cnt_cat, cnt_mov ) in result:
				print "Deleted: channels:%d, categories:%d, movies:%d" % ( cnt_chn, cnt_cat, cnt_mov )
		cursor.close()
		self.conn.commit()

	def init_record( self ):
		self.index = 0
		self.film["title"] = ""
		self.film["search"] = ""
		self.film["aired"] = "1980-01-01 00:00:00"
		self.film["duration"] = "00:00:00"
		self.film["size"] = 0
		self.film["description"] = ""
		self.film["website"] = ""
		self.film["url_sub"] = ""
		self.film["url_video"] = ""
		self.film["url_video_sd"] = ""
		self.film["url_video_hd"] = ""
		self.film["airedepoch"] = 0
		self.film["geo"] = ""
		self.film["new"] = 0

	def end_record( self ):
		if self.count % 1000 == 0:
			print "In progress (%d): channels:%d, categories:%d, movies:%d ..." % ( self.count, self.channels, self.categories, self.movies )
		self.count = self.count + 1
#		try:
		cursor = self.conn.cursor()
		cursor.callproc( 'ftInsertFilm', (
			self.film["channel"],
			self.film["category"],
			self.film["catsearch"],
			self.film["title"],
			self.film["search"],
			self.film["aired"],
			self.film["duration"],
			self.film["size"],
			self.film["description"],
			self.film["website"],
			self.film["url_sub"],
			self.film["url_video"],
			self.film["url_video_sd"],
			self.film["url_video_hd"],
			self.film["airedepoch"],
			self.film["geo"],
			self.film["new"],
		) )
		for result in cursor.stored_results():
			for ( id, cnt_chn, cnt_cat, cnt_mov ) in result:
				self.channels = self.channels + cnt_chn
				self.categories = self.categories + cnt_cat
				self.movies = self.movies + cnt_mov
#		except mysql.connector.errors.DataError:
#			print self.film["aired"] + ' - ' + self.film["duration"]
#			print self.film
#			exit (1)
		cursor.close()
		self.conn.commit()

	def make_search( self, val ):
		cset = string.letters + string.digits + ' _-#'
		search = ''.join( [ c for c in val if c in cset ] )
		return search.upper().strip()

	def add_value( self, val ):
		if self.index == 0:
			if val != "":
				self.film["channel"] = val
		elif self.index == 1:
			if val != "":
				self.film["category"] = val[:255]
				self.film["catsearch"] = self.make_search( val )[:255]
		elif self.index == 2:
			self.film["title"] = val[:255]
			self.film["search"] = self.make_search( val )[:255]
		elif self.index == 3:
			if len(val) == 10:
				self.film["aired"] = val[6:] + '-' + val[3:5] + '-' + val[:2]
		elif self.index == 4:
			if ( self.film["aired"] != "1980-01-01 00:00:00" ) and ( len(val) == 8 ):
				self.film["aired"] = self.film["aired"] + " " + val
		elif self.index == 5:
			if len(val) == 8:
				self.film["duration"] = val
		elif self.index == 6:
			if val != "":
				self.film["size"] = int(val)
		elif self.index == 7:
			self.film["description"] = val
		elif self.index == 8:
			self.film["url_video"] = val
		elif self.index == 9:
			self.film["website"] = val
		elif self.index == 10:
			self.film["suburl_subtitles"] = val
		elif self.index == 12:
			self.film["url_video_sd"] = self.make_url(val)
		elif self.index == 14:
			self.film["url_video_hd"] = self.make_url(val)
		elif self.index == 16:
			if val != "":
				self.film["airedepoch"] = int(val)
		elif self.index == 18:
			self.film["geo"] = val
		elif self.index == 19:
			if val == "true":
				self.film["new"] = 1
		self.index = self.index + 1

	def make_url( self, val ):
		x = val.split( '|' )
		if len(x) == 2:
			cnt = int(x[0])
			return self.film["url_video"][:cnt] + x[1]
		else:
			return val


	def parse( self, file ):
		parser = ijson.parse( file )
		self.update_start()
		for prefix, event, value in parser:
			if ( prefix, event ) == ( "X", "start_array" ):
				self.init_record()
			elif ( prefix, event ) == ( "X", "end_array" ):
				self.end_record()
			elif ( prefix, event ) == ( "X.item", "string" ):
				if value is not None:
					self.add_value( value.strip().encode('utf-8') )
				else:
					self.add_value( "" )
		self.update_end()


# main program
if len(sys.argv) > 1:
	fl = urllib.urlopen( sys.argv[1] )
	fr = filmreader()
	fr.parse( fl )
else:
	print "USAGE: %s <path to Filmliste-akt>" % sys.argv[0]
	exit(1)
