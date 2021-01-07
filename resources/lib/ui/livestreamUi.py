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
        

    def begin(self):
        """
        Begin a directory containing films
        """
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, 'movies')
        

    def add(self, databaseRs):
        """
        Add the current entry to the directory

        Args:
            databaseRs: database resultset
        """
        listOfElements = []
        ##
        for element in databaseRs:
            (videourl, listitem, isFolder, ) = self.generateLivestream(element)
            listOfElements.append((videourl, listitem, isFolder))
        ##
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )



    def end(self):
        """ Finish a directory containing films """
        self.logger.info('Listitem generated: {} sec', time.time() - self.startTime)
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)


    def generateLivestream(self, rsRow):
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

        videourl = rsRow[9] + self.settings.userAgentString()

        info_labels = {
            'title': rsRow[1],
            'sorttitle': rsRow[1].lower()
        }

        iconFile = rsRow[1].replace(' ','') + '.png'

        icon = os.path.join(
            self.plugin.path,
            'resources',
            'icons',
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
            'icon': icon
        })
        return (videourl, listitem, False)
