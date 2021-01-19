# -*- coding: utf-8 -*-
"""
The film model UI module

Copyright 2021, Mediathekview.de
SPDX-License-Identifier: MIT
"""
import time
import os
from datetime import datetime
from datetime import timedelta
# pylint: disable=import-error
import xbmcgui
import xbmcplugin
import resources.lib.appContext as appContext


class LivestreamUi(object):
    """
    Show live streams
    """

    def __init__(self, plugin):
        self.logger = appContext.MVLOGGER.get_new_logger('LivestreamUi')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.settings = appContext.MVSETTINGS
        ##
        self.startTime = 0
        
    def generate(self, databaseRs):
        """
        Add the current entry to the directory

        Args:
            databaseRs: database resultset
        """
        ##
        self.startTime = time.time()
        ##
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, 'movies')
        ##
        listOfElements = []
        ##
        for element in databaseRs:
            (videourl, listitem, isFolder, ) = self._generateLivestream(element)
            listOfElements.append((videourl, listitem, isFolder))
        ##
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        ##
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        self.plugin.run_builtin('Container.SetViewMode(500)')
        ##
        self.logger.debug('generated: {} sec', time.time() - self.startTime)

    def _generateLivestream(self, rsRow):
        # 0 filmui.filmid
        # 1 filmui.title
        # 2 filmui.show, 
        # 3 filmui.channel, 
        # 4 filmui.description, 
        # 5 filmui.seconds, 
        # 6 filmui.size, 
        # 7 filmui.aired, 
        # 8 filmui.url_sub, 
        # 9 filmui.url_video, 
        #10 filmui.url_video_sd, 
        #11 filmui.url_video_hd

        videourl = rsRow[9] + self.settings.getUserAgentString()

        info_labels = {
            'title': rsRow[1],
            'sorttitle': rsRow[1].lower()
        }

        iconFile = rsRow[1].replace(' ','') + '.png'

        icon = os.path.join(
            self.plugin.path,
            'resources',
            'icons',
            'livestream',
            iconFile
        )

        ##
        if self.plugin.get_kodi_version() > 17:
            listitem = xbmcgui.ListItem(label=rsRow[1], path=videourl, offscreen=True)
        else:
            listitem = xbmcgui.ListItem(label=rsRow[1], path=videourl)
        ##
        listitem.setInfo(type='video', infoLabels=info_labels)
        listitem.setProperty('IsPlayable', 'true')
        listitem.setArt({
                'thumb': icon,
                'icon': icon,
                'banner': icon,
                'fanart': icon,
                'clearart': icon,
                'clearlogo': icon
        })
        return (videourl, listitem, False)
