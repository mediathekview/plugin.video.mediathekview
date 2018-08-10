# -*- coding: utf-8 -*-
"""
The main service module

MIT License

Copyright (c) 2017-2018, Leo Moll

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# -- Imports ------------------------------------------------
from __future__ import unicode_literals

from resources.lib.kodi.kodiaddon import KodiService
from resources.lib.kodi.kodiaddon import KodiInterlockedMonitor

from resources.lib.notifier import Notifier
from resources.lib.settings import Settings
from resources.lib.updater import MediathekViewUpdater


class MediathekViewMonitor(KodiInterlockedMonitor):
    """ Singleton Event Monitor Class """

    def __init__(self, service, setting_id):
        super(MediathekViewMonitor, self).__init__(service, setting_id)
        self.logger = service.get_new_logger('Monitor')

    # pylint: disable=invalid-name
    def onSettingsChanged(self):
        """ Handler method invoked when settings have been changed """
        self.service.reload_settings()


class MediathekViewService(KodiService):
    """ The main service class """

    def __init__(self):
        super(MediathekViewService, self).__init__()
        self.set_topic('Service')
        self.settings = Settings()
        self.notifier = Notifier()
        self.monitor = MediathekViewMonitor(self, 'instanceid')
        self.updater = MediathekViewUpdater(self.get_new_logger(
            'Updater'), self.notifier, self.settings, self.monitor)

    def init(self):
        """ Initialisation of the service """
        self.info('Init (instance id: {})', self.monitor.instance_id)
        self.monitor.register_instance()
        self.updater.init(convert=True)
        self.settings.reset_user_activity()

    def run(self):
        """ Execution of the service """
        self.info('Starting up... (instance id: {})', self.monitor.instance_id)
        while not self.monitor.abort_requested():
            if self.settings.reload() is True:
                # database configuration changed
                self.info(
                    '===== Database Configuration has changed - Reloading the updater =====')
                self.updater.reload()

            updateop = self.updater.get_current_update_operation()
            if updateop == 1:
                # full update
                self.info('Initiating full update...')
                self.settings.save_update_instance(self.monitor.instance_id)
                self.updater.update(True)
            elif updateop == 2:
                # differential update
                self.info('Initiating differential update...')
                self.settings.save_update_instance(self.monitor.instance_id)
                self.updater.update(False)
            # Sleep/wait for abort for 60 seconds
            if self.monitor.wait_for_abort(15):
                # Abort was requested while waiting. We should exit
                break
        self.info('Shutting down... (instance id: {})',
                  self.monitor.instance_id)

    def exit(self):
        """ Shutdown of the service """
        self.info('Exit (instance id: {})', self.monitor.instance_id)
        self.updater.exit()
        self.monitor.unregister_instance()

    def reload_settings(self):
        """ Reload settings and reconfigure service behaviour """
        # self.info("===== RELOAD SETTINGS =====")
        # TODO: support online reconfiguration
        #       currently there is a bug in Kodi: this event is only
        #       triggered if the reconfiguration happen inside the
        #       addon (via setSetting). If teh user changes something
        #       via the settings page, NOTHING WILL HAPPEN!
        pass


# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    SERVICE = MediathekViewService()
    SERVICE.init()
    SERVICE.run()
    SERVICE.exit()
    del SERVICE
