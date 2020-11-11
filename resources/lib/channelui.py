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

from resources.lib.channel import Channel


class ChannelUI(Channel):
    """
    The channel model view class

    Args:
        plugin(MediathekView): the plugin object

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`

        nextdir(str, optional):
    """

    def __init__(self, plugin, sortmethods=None, nextdir='initial'):
        super(ChannelUI, self).__init__()
        self.logger = appContext.MVLOGGER.get_new_logger('ChannelUI')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.nextdir = nextdir
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE]
        self.startTime = 0


    def begin(self):
        """
        Begin a directory containing channels
        """
        self.startTime = time.time()
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)
        xbmcplugin.setContent(self.handle, '')

    def add(self, altname=None):
        """
        Add the current entry to the directory

        Args:
            altname(str, optional): alternative name for the entry
        """
        resultingname = self.channel if self.count == 0 else '%s (%d)' % (
            self.channel, self.count, )
        ##
        if self.plugin.get_kodi_version() > 17:
            list_item = xbmcgui.ListItem(label=resultingname if altname is None else altname, offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=resultingname if altname is None else altname)
        ##
        icon = os.path.join(
            self.plugin.path,
            'resources',
            'icons',
            self.channel.lower() + '-m.png'
        )
        list_item.setArt({
            'thumb': icon,
            'icon': icon
        })

        info_labels = {
            'title': resultingname,
            'sorttitle': resultingname.lower()
        }
        list_item.setInfo(type='video', infoLabels=info_labels)

        xbmcplugin.addDirectoryItem(
            handle=self.handle,
            url=mvutils.build_url({
                'mode': self.nextdir,
                'channel': self.channel
            }),
            listitem=list_item,
            isFolder=True
        )

    def end(self):
        """ Finish a directory containing channels """
        self.logger.info('Listitem generated: {} sec', time.time() - self.startTime)
        xbmcplugin.endOfDirectory(self.handle)
