# -*- coding: utf-8 -*-
"""
The channel model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Channel(object):
    """ The channel model class """

    def __init__(self):
        self.channelId = ''
        self.channelCaption = ''

    def init(self, pId, pName):
        """ init the object with new values """
        self.channelId = pId
        self.channelCaption = pName
        
    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "channelId": self.channelId,
            "channelCaption": self.channelCaption
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.channelId = data.get('channelId', '')
        self.channelCaption = data.get('channelCaption', '')
