# -*- coding: utf-8 -*-
"""
The channel model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Channel(object):
    """ The channel model class """

    def __init__(self):
        self.channel = ''
        self.count = 0

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "channel": self.channel,
            "count": self.count
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.channel = data.get('channel', '')
        self.count = data.get('count', 0)
