# -*- coding: utf-8 -*-
"""
The initial grouping model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils


class Initial(object):
    """
    The initial grouping model view class
    """

    def __init__(self, plugin, sortmethods=None):
        self.channelid = 0
        self.initial = ''
        self.count = 0

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "channelid": self.channelid,
            "initial": self.initial,
            "count": self.count
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.channelid = data.get('channelid', 0)
        self.initial = data.get('initial', '')
        self.count = data.get('count', 0)

