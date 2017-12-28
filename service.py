# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
import time
import xbmc
 
# -- Main Code ----------------------------------------------
if __name__ == '__main__':
    monitor = xbmc.Monitor()
 
    while not monitor.abortRequested():
        # Sleep/wait for abort for 10 seconds
        if monitor.waitForAbort(10):
            # Abort was requested while waiting. We should exit
            break
        # xbmc.log("hello addon! %s" % time.time(), level=xbmc.LOGNOTICE)