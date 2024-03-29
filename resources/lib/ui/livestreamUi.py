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
from resources.lib.model.livestream import Livestream


class LivestreamUi(object):
    """
    Show live streams
    """

    def __init__(self, plugin):
        self.logger = appContext.MVLOGGER.get_new_logger('LivestreamUi')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.settings = appContext.MVSETTINGS
        #
        self.startTime = 0

    def generate(self, databaseRs):
        """
        Add the current entry to the directory

        Args:
            databaseRs: database resultset
        """
        #
        # 0 filmui.filmid
        # 1 filmui.title
        # 2 filmui.show,
        # 3 filmui.channel,
        # 4 filmui.description,
        # 5 filmui.seconds,
        # 6 filmui.aired,
        # 7 filmui.url_sub,
        # 8 filmui.url_video,
        # 9 filmui.url_video_sd,
        # 10 filmui.url_video_hd
        #
        self.startTime = time.time()
        #
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, '')
        #
        livestreamModel = Livestream()
        listOfElements = []
        #
        for element in databaseRs:
            livestreamModel.init(element[3], element[1], element[8])
            #
            videourl = livestreamModel.url + self.settings.getUserAgentString()
            #
            info_labels = {
                'title': livestreamModel.name,
                'sorttitle': livestreamModel.name.lower()
            }
            #
            livestreamName = livestreamModel.name.replace(' ', '')
            fanArt = self._findIconName(livestreamModel.channel, livestreamName) + '-f.png'
            icon = self._findIconName(livestreamModel.channel, livestreamName) + '-i.png'
            #
            if self.plugin.get_kodi_version() > 17:
                listitem = xbmcgui.ListItem(label=livestreamModel.name, path=videourl, offscreen=True)
            else:
                listitem = xbmcgui.ListItem(label=livestreamModel.name, path=videourl)
            #
            listitem.setInfo(type='video', infoLabels=info_labels)
            listitem.setProperty('IsPlayable', 'true')
            listitem.setArt({
                'thumb': icon,
                'icon': icon,
                'fanart': fanArt
            })
            #
            listOfElements.append((videourl, listitem, False))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        self.plugin.setViewId(self.plugin.resolveViewId('THUMBNAIL'))
        #
        self.logger.debug('generated: {} sec', time.time() - self.startTime)

    def _findIconName(self, pchannel, pName):
        liveStreamMap = {
                "3SatLivestream": None,
                "ARDLivestream":None,
                "ARDAlphaLivestream":"ardalpha",
                "ARDONELivestream":"one",
                "ARDTagesschauLivestream":"tagesschau24",
                "ARTE.DELivestream":None,
                "ARTE.FRLivestream":None,
                "BRNordLivestream":None,
                "BRSüdLivestream":None,
                "DWLivestream":None,
                "HRLivestream":None,
                "KiKALivestream":None,
                "MDRSachsenLivestream":"mdr-s",
                "MDRSachsen-AnhaltLivestream":"mdr-sa",
                "MDRThüringenLivestream":"mdr-th",
                "NDRHamburg":None,
                "NDRMecklenburg-Vorpommern":None,
                "NDRNiedersachsen":None,
                "NDRSchleswig-Holstein":None,
                "ORF-1Livestream":"orf1",
                "ORF-2Livestream":"orf2",
                "ORF-3Livestream":"orf3",
                "ORF-SportLivestream":"orfsport",
                "PHOENIXLivestream":None,
                "RBBBrandenburgLivestream":None,
                "RBBBerlinLivestream":None,
                "SRLivestream":None,
                "SWRBWLivestream":None,
                "SWRRPLivestream":None,
                "WDRLivestream":None,
                "ZDFLivestream":None,
                "ZDF.infoLivestream":"zdf.info",
                "ZDF.neoLivestream":"zdf.neo",
            }
        altPath = liveStreamMap.get(pName)
        if altPath is not None:
            altPath = os.path.join(
                self.plugin.path,
                'resources',
                'icons',
                'livestream',
                altPath,
            )
        else:
            altPath = os.path.join(
                self.plugin.path,
                'resources',
                'icons',
                'sender',
                pchannel.lower(),
            )
        return altPath
