MediathekView Addon per Kodi
============================

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
disponibile in `resources/sql/filmliste-mysql-v1. sql`.

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