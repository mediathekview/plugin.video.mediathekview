Kodi MediathekView Addon
========================

English Version: Please see below
Versione Italiana: Il testo italiano si trova più in basso

Über dieses Addon
-----------------

Und schon wieder ein Kodi-Addon für deutsche Mediatheken... Wozu das ganze?

Weil der Ansatz dieses Addons ein anderer ist, als der der bereits verfügbaren
Addons: dieses Addon benutzt die Datenbank des großartigen Projektes
"MediathekView", welche stündlich aktualisiert wird über 200.000 Einträge aus
allen deutschen Mediatheken enthält. Dieser Ansatz hat einige entscheidende
Vorteile gegenüber den anderen Addons, die hingegen versuchen die Mediatheken
in Echtzeit zu scannen:

* Hohe Geschwindigkeit beim Durchsuchen und Navigieren
* Unabhängigkeit von allen Änderungen des Seitenlayouts der Mediatheken
* Hohe Zuverlässigkeit

Dies alles wird ermöglicht durch den unermüdlichen Einsatz des MediathekView-
Teams ohne den ein solches Addon nicht möglich wäre.

Dieses Addon ist allerdings *nicht* offizieller Bestandteil des MediathekView-
Projektes, sondern eine unabhängige Entwicklung.

Sollten Probleme bei der Benutzung dieses Addons auftreten, so können diese
unter https://github.com/YeaSoft/plugin.video.mediathekview/issues gemeldet
werden.

Sollte dieses Addon nützlich sein, wäre es sinnvoll dem MediathekView-Team
eine Spende zukommen zu lassen, da ohne deren Datenbank dieses Addon nicht
funktionieren würde. Eine entsprechende Möglichkeit befindet sich auf der
Homepage https://mediathekview.de/ des Projektes.

Wichtigste Features
-------------------
* Hintergrundaktualisierung der Datenbank
* Blitzschnelle Navigation
* Herunterlladen von Filmen mit automatischer Erzeugung von NFO Dateien und
  eventueller Untertitel
* Lokale interne Datenbank oder geteilte MySQL Datenbank
* Benutzeroberfläche verfügbar in Deutsch, Englisch und Italienisch

Funktionsweise
--------------

Das Addon lädt die Datenbank von MediathekView herunter und importiert diese
entweder in einer lokalen SQLite Datenbank, oder wahlweise in einer lokalen
oder entfernten MySQL Datenbank (zur Benutzung durch mehrere Kodi-Clients).
Während der Laufzeit von Kodi werden in einem konfigurierbaren Intervall
(Standard: 2 Stunden) die Differenzdateien von MediathekView heruntergeladen
und in die Datenbank integriert. Spätestens beim nächsten Kalendertag nach
dem letzten Update wird die Aktualisierung wieder mittels des vollständigen
Updates von Mediathekview ausgeführt.

Systemvoraussetzungen
---------------------

Die Systemvoraussetzungen für das Addon unterscheiden sich je nach
Konfiguration. Nach der Installation startet das Addon im lokalen Modus:
dies bedeutet, dass eine lokale SQLite-Datenbank benutzt wird, die auch
durch das Kodi-System lokal aktualisiert wird. Dies dürfte auch das
üblichste Szenario sein.

Dieses Szenario birgt zwei Voraussetzungen die erfüllt sein sollten:
* ein einigermaßen performantes Dateisystem für die Datenbank. Ein Raspberry
  mit seiner langsamen SD-Karte ist in diesem Fall sicherlich nicht die
  allerbeste Wahl. Das vollständige Update der Datenbank dauert hier um die
  15-20 Minuten. Da dies aber im Hintergrund passiert, kann man unter Umständen
  gut damit leben.
* der Entpacker 'xz' auf dem Kodi-System. Um den Datenbank-Aktualisierer zu
  benutzen, muss dieses Programm auf dem System in einem der Standard-
  Verzeichnisse (/bin, /usr/bin, /usr/local/bin) installiert werden.
  Unter Windows bzw. falls das Programm in einem anderen Verzeichnis
  installiert ist, muss der Pfad zum Programm in den Addon-Einstellungen
  angegeben werden. Sollte der Entpacker nicht vorhanden sein, so gibt
  das Addon eine Meldung aus und deaktiviert den Aktualisierungsprozess.

Das Addon wurde auf verschiedenen Plattformen unter Linux, MacOS und LibreELEC
bzw. OpenELEC getestet. Dort war auch der entsprechende Entpacker verfügbar.
Unter Windows muss der Entpacker nachträglich installiert werden und dessen
Pfad in den Addon-Einstellungen angegeben werden. Mangels Testsystem konnte
dies jedoch zum jetzigen Zeitpunkt noch nicht getestet werden.

Alternativ-Konfigurationen
--------------------------

Ist das Kodi-System zu langsam um eine eigene Datenbank zu verwalten
(z.B. Raspberry PI mit sehr langsamer SD-Karte) oder fehlt das Programm
'xz', so besteht die Möglichkeit das Addon auch mit einer externen
Datenbank (MySQL) zu nutzen.

Da viele Kodi-Nutzer über ein eigenes NAS-System verfügen um ihre Medien
dem Media-Center zur Verfügung zu stellen, eignet sich dieses in der Regel
auch als MySQL Datenbank-Server da nahezu alle NAS-Betriebssysteme die
Installation eines solchen anbieten.

Hierfür muss lediglich die entsprechende Datenbank im MySQL Server mit
dem SQL-Skript `resources/sql/filmliste-mysql-v1.sql` erzeugt werden.

Die Verbindung zur Datenbank kann in den Addon-Einstellungen im Abschnitt
_"Datenbank Einstellungen"_ vorgenommen werden.

Ist mindestens eines der angeschlossenen Kodi-Systeme in der Lage das Update
der Datenbank durchzuführen, so ist für das Update gesorgt. Sollte dies nicht
der Fall sein, so besteht auch die Möglichkeit, den Update-Prozess auf einem
anderen System (z.B. das NAS, den Datenbankserver oder eine andere Maschine)
laufen zu lassen.

Standalone Datenbank Update Prozess
-----------------------------------

Dieser ist noch nicht vollständig implementiert und dokumentiert, wird aber in
eine der nächsten Versionen nachgeliefert.



English Version
===============

About this Addon
----------------

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


Highlights
----------
* Background updating of the database
* Amazing fast navigation and search
* Download with subtitles and automatic NFO file generation
* Internal standalone or shared MySQL database support
* UI localised to German, English and Italian


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



Versione Italiana
=================

Un altro addon Kodi per la navigazione nelle piattaforme video operate dalle
emittenti pubbliche tedesche... Perchè?

Perché l'approccio di questo addon è diverso da quello degli altri addon
disponibili: questo addon utilizza il database del grande progetto
_"MediathekView"_, che viene aggiornato ogni ora e contiene oltre 200.000 voci
da tutte le piattaforme video tedesche. Questo approccio presenta alcuni
vantaggi significativi rispetto agli altri addon, che cercano di scansionare
i siti delle piattaforme video in tempo reale:

* Navigazione nella libreria ad alta velocità
* Indipendenza da qualsiasi modifica al layout di pagina delle librerie multimediali
* Alta affidabilità

Tutto questo è reso possibile dall'assiduo impegno del team di MediathekView
senza il quale un tale addon non sarebbe possibile.

Tuttavia questo addon *non* è una parte ufficiale del progetto MediathekView,
ma uno sviluppo indipendente.

Se si riscontrano problemi nell'uso di questo addon, si prega di segnalarli
all'indirizzo https://github.com/YeaSoft/plugin.video.mediathekview/issues

Se questo addon è utile, sarebbe utile fare una donazione al team
MediathekView, perché senza il loro database questo addon non funzionerebbe.
Una possibilità corrispondente si trova sulla homepage del progetto
https://mediathekview.de/


Highlights
----------
* Attualizzazione della banca dati in background
* Navigazione e ricerca velocissima
* Scaricamento video con generazione automatica die file NFO e scaricamento
  sottotitoli
* Banca dati interna o banca dati condivisa a base MySQL
* Interfaccia disponibile in Italiano, Inglese e Tedesco


Come funziona
-------------

L'addon scarica il database da MediathekView e lo importa in un database SQLite
locale o, in alternativa, in un database MySQL locale o remoto (per l'uso da
parte di più client Kodi).
Durante il runtime di Kodi, i file differenziali vengono scaricati da
MediathekView in un intervallo configurabile (predefinito: 2 ore) ed importati
nel database. Al più tardi entro il giorno successivo all'ultimo aggiornamento,
l'aggiornamento sarà nuovamente effettuato tramite l'aggiornamento completo
di Mediathekview.

* Un file system con prestazioni accettabili per il database. Un Raspberry con
  la sua lenta scheda SD non è certamente la miglior scelta ma sempre ancora
  accettabile. La durata di un aggiornamento completo in questo caso sarà
  intorno ai 15-20 minuti. Ma poiché questo accade in background, l'impatto
  sarà essere accetabile.
* Il decompressore 'xz' sul sistema Kodi. Per utilizzare il programma di
  aggiornamento del database, questo programma deve essere installato sul
  sistema in una delle directory standard (/bin, /usr/bin, /usr/local/bin). In
  Windows o se il programma è installato in una directory diversa, il percorso
  del programma deve essere specificato nelle impostazioni dell'addon. Se il
  decompressore non è disponibile per il sistema, l'addon mostra un messaggio
  e disabilita il processo di aggiornamento.


Configurazioni alternative
--------------------------

Se il sistema Kodi è troppo lento per gestire il proprio database (ad es.
Raspberry PI con una scheda SD molto lenta) o se manca il programma 'xz',
è anche possibile utilizzare l'addon con un database esterno (MySQL).

Dal momento che molti utenti Kodi hanno il proprio sistema NAS per rendere i
loro contenuti mediali disponibili al media center, questo è di solito anche
adatto come server di database MySQL, dal momento che quasi tutti i sistemi
operativi NAS offrono l'installazione di un tale database.

Dopodiche sarà sufficiente creare la banca dati mediante lo script SQL
disponibile in `resources/sql/filmliste-mysql-v1.sql`.

Il collegamento al database può essere effettuato nelle impostazioni 
dell'addon nella sezione "Impostazioni Banca Dati".

Se almeno uno dei sistemi Kodi collegati è in grado di aggiornare il database,
l'addon funzionerà su tutti i sistemi Kodi. In caso contrario, è anche
possibile eseguire il processo di aggiornamento su un altro sistema (ad es. il
NAS, il server di database o un altro sistema).


Processo esterno di aggiornamento del database
----------------------------------------------

Questo non è ancora completamente implementato e documentato, ma sarà
dispüonibile in una delle prossime versioni.