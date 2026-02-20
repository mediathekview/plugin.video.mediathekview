# -*- coding: utf-8 -*-
"""
The channel model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Livestream(object):
    """ The livestream model class """

    def __init__(self):
        self.channel = ''
        self.name = ''

    def init(self, pChannel, pName):
        """ init the object with new values """
        self.channel = pChannel
        self.name = pName

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "channel": self.channel,
            "name": self.name
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.channel = data.get('channel', '')
        self.name = data.get('name', '')
