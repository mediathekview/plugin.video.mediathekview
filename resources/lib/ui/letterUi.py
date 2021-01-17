# -*- coding: utf-8 -*-
"""
The show model UI module

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


class LetterUi(object):
    """
    The show model view class

    Args:
        plugin(MediathekView): the plugin object
    """

    def __init__(self, plugin):
        self.logger = appContext.MVLOGGER.get_new_logger('ShowUI')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.startTime = 0

    def generate(self, databaseRs):
        #
        # 0 - letter
        # 1 - cnt
        #
        self.startTime = time.time()
        #
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, '')
        #
        listOfElements = []
        for element in databaseRs:
            #
            nameLabel = element[0] + " (" + str(element[1]) + ")" ;
            #
            if self.plugin.get_kodi_version() > 17:
                list_item = xbmcgui.ListItem(label=nameLabel, offscreen=True)
            else:
                list_item = xbmcgui.ListItem(label=nameLabel)
            #
            info_labels = {
                'title': nameLabel,
                'sorttitle': nameLabel.lower()
            }
            list_item.setInfo(type='video', infoLabels=info_labels)
            #
            targetUrl = mvutils.build_url({
                'mode': 'shows',
                'initial': element[0]
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
