MediathekView Addon for Kodi
============================

Frontend Installation
---------------------

Since the plugin is not distributed via a Kodi Repository, you have to
install the dependencies manually. There are two dependencies:

* The Kodi Python MySQL Connector: http://mirrors.kodi.tv/addons/krypton/script.module.myconnpy/script.module.myconnpy-1.1.7.zip
* The Kodi Python Requests library: http://mirrors.kodi.tv/addons/krypton/script.module.requests/script.module.requests-2.12.4.zip

Download both ZIP Files and install them using the Kodi "Install from ZIP File"
function in the Addon Installation Menu.

After that you can install the Addon by cloning the repository into the Kodi
addon directory (addons).

Remeber to enable the addon in the addon configuration.

Backend Installation
--------------------

In order to use the MediathekView video addon for Kodi, you need to operate a
MySQL Server as a backend.

You can install the database by executing the SQL-script in the `backend/sql`
directory:

´´´´
root@db1:~/plugin.video.mediathekview # mysql -u root -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 227292
Server version: 5.7.20-log MySQL Community Server (GPL)

Copyright (c) 2000, 2017, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> source backend/sql/filmliste-init-0.sql
´´´´

The periodic update of the database is done by executing the script ´updatefl.sh´
in the ´backend´ directory.

In order to run this script, you system needs python 2 and the following libraries
installed via pip:

````
pip install ijson
pip install mysql-connector==2.1.4

````

