MediathekView Addon for Kodi
============================

Yet another Kodi-Addon for the german pupblic service video platforms... Why?

Because the approach of this addon is different from the already available
addons: this addon uses the database of the awesome project _"MediathekView"_,
which is updated hourly and contains over 200.000 entries from all German
media libraries. This approach has some significant advantages over the other
addons, which try to scan the libraries in real time:

* High speed browsing and navigation
* Independence from all changes to the page layout of the media libraries
* High reliability

All this is made possible by the endless effort of the MediathekView team
without which such an addon would not be possible.

This addon *is not* an official part of the MediathekView project but an
independent development.

If you encounter any problems using this addon, please report them to
https://github.com/YeaSoft/plugin.video.mediathekview/issues

If you like this addon, consider making a donation to the MediathekView team,
because without their database this addon would not work at all.
You will find the possibility to make a donation on the project's homepage
https://mediathekview.de/


How it Works
------------

The addon downloads the database from MediathekView and imports it either into
a local SQLite database, or alternatively into a local or remote MySQL database
(for use by multiple Kodi clients).
During the runtime of Kodi, only the differential update files are downloaded
from MediathekView in a configurable interval (default: 2 hours) and integrated
into the database. By the next calendar day after the last update at the latest,
the update will be carried out again by importing the full MediathekView
database.


System Requirements
-------------------

The system requirements for the addon vary depending on the configuration.
After installation, the addon starts in local mode: this means that a local
SQLite database is used, which is also updated locally by the Kodi system.
This is probably the most common scenario.

* a file system with a decent performance for the database. A Raspberry with
  its slow SD card is certainly not the very best choice in this case but still
  acceptable. The full update will take in this case about 15-20 Minutes but
  since this happens in the background, you may be able to live with it.
* The unpacker 'xz' on the Kodi system. To use the database updater, this
  program must be installed on the system in one of the standard directories
  (/bin, /usr/bin, /usr/local/bin). Under Windows or if the program is
  installed in a different directory, the path to the program must be specified
  in the addon settings. If the unpacker is not available on the target system,
  the addon issues a message and disables the update process.

The addon has been tested on different platforms under Linux, MacOS and
LibreELEC/OpenELEC. The corresponding unpacker was also available there.
Under Windows, the unpacker must be manually installed and its path must
be specified in the addon settings. Due to the lack of a test system,
however, this could not be tested at the present time.


Alternate Configurations
------------------------

If the Kodi system is too slow to manage its own database (e.g. Raspberry PI
with a very slow SD card) or if the program 'xz' is missing, it is also
possible to use the addon with an external database (MySQL).

Since many Kodi users have their own NAS system to make their media available
to the media center, this is usually also suitable as a MySQL database server
since almost all NAS operating systems offer the installation of MySQL.

When you have a running MySQL server avaible, you have only to create the
database by running the SQL script `resources/sql/filmliste-mysql-v1.sql`.

The connection to the database can be configured in the addon settings in
the "Database Settings" section.

If at least one of the connected Kodi systems is able to update the database,
the data is available to all Kodi systems. If this is not the case, it is
also possible to run the update process on a different system (e.g. the NAS,
the database server or another machine).

Standalone Database Update Process
----------------------------------

This is not yet fully implemented and documented, but will be delivered in one
of the next versions.
