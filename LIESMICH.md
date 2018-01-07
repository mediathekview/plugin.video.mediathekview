MediathekView Addon für Kodi
============================

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