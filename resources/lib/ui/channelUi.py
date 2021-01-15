# -*- coding: utf-8 -*-
"""
The channel model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import time
import resources.lib.appContext as appContext
import os
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils


class ChannelUi(object):
    """
    The channel model view class

    Args:
        plugin(MediathekView): the plugin object

    """

    def __init__(self, plugin, targetUrl):
        self.logger = appContext.MVLOGGER.get_new_logger('ChannelUi')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.targetUrl = targetUrl
        self.startTime = 0

    def generate(self, databaseRs):
        #
        # 0 - channelid
        # 1 - channel
        # 2 - channel description xxx (#no)
        #
        #
        self.startTime = time.time()
        #
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, '')
        #
        listOfElements = []
        for element in databaseRs:
            #
            nameLabel = element[1];
            #
            if self.plugin.get_kodi_version() > 17:
                list_item = xbmcgui.ListItem(label=nameLabel, offscreen=True)
            else:
                list_item = xbmcgui.ListItem(label=nameLabel)
            #
            icon = os.path.join(
                self.plugin.path,
                'resources',
                'icons',
                'sender',
                element[0].lower() + '-m.png'
            )
            list_item.setArt({
                'thumb': icon,
                'icon': icon
            })
    
            info_labels = {
                'title': element[1],
                'sorttitle': element[1].lower()
            }
            list_item.setInfo(type='video', infoLabels=info_labels)
            #
            targetUrl = mvutils.build_url({
                'mode': self.targetUrl,
                'channel': element[0]
            })
            #
            listOfElements.append((targetUrl, list_item, True))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        #
        self.logger.info('Listitems generated: {} sec', time.time() - self.startTime)

