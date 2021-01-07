"""
Management of recent searches

Copyright (c) 2018, Leo Moll
SPDX-License-Identifier: MIT
"""

import os
import json
import time
import resources.lib.appContext as appContext

from contextlib import closing
from operator import itemgetter
from codecs import open
# pylint: disable=import-error
import xbmcplugin
from mailcap import show
from optparse import TitledHelpFormatter


class ExtendedSearchModel(object):
    """
    """

    def __init__(self, pName):
        self.logger = appContext.MVLOGGER.get_new_logger('ExtendedSearchModel')
        self.settings = appContext.MVSETTINGS
        self.id = int(time.time())
        self.name = pName
        self.channel = []
        self.title = []
        self.show = [pName]
        self.description = []
        self.excludeTitle = []
        self.minLength = self.settings.getMinLength()
        self.ignoreTrailer = 1 if self.settings.getNoFutur() else 0
        self.when = self.id
        ##
        ##
        """
        self.recents = [
                { 
                    "id" : 1, 
                    "name" : "",
                    "channel" : [ "ARD" , "WDR" ],
                    "title" : ["something"],
                    "show" : ["something"],
                    "description" : ["bla" ],
                    "excludeTitle" : ["bla"],
                    "minLength" : 60,
                    "ignoreTrailer" : 1,
                    "when" : 1312312
                }
            ]
        """

    ################
    ## RESET
    ################
    def reset(self):
        self.name = ''
        self.channel = []
        self.title = []
        self.show = []
        self.description = []
        self.excludeTitle = []
        self.minLength = 0
        self.ignoreTrailer = False

    ################
    ## GET
    ################
    
    def getId(self):
        return self.id;
    
    def getName(self):
        return self.name;

    def getChannel(self):
        return self.channel
    
    def getShow(self):
        return self.show
    
    def getTitle(self):
        return self.title
    
    def getDescription(self):
        return self.description
    
    def getExcludeTitle(self):
        return self.excludeTitle
    
    def getMinLength(self):
        return self.minLength
    
    def isIgnoreTrailer(self):
        return self.ignoreTrailer == 1

    ################
    ## GET
    ################
    
    def getIdAsString(self):
        return self.id;
    
    def getNameAsString(self):
        return self.name;

    def getChannelAsString(self):
        return ', '.join(self.channel)
    
    def getShowAsString(self):
        return '|'.join(self.show)
    
    def getTitleAsString(self):
        return '|'.join(self.title)
    
    def getDescriptionAsString(self):
        return '|'.join(self.description)
    
    def getExcludeTitleAsString(self):
        return '|'.join(self.excludeTitle)
    
    def getMinLengthAsString(self):
        return str((self.minLength/60))
    
    def getIgnoreTrailerAsString(self):
        return str(self.ignoreTrailer)


    ################
    ## SET
    ################
    def setId(self, pValue):
        self.id = pValue

    def setName(self, pValue):
        self.name = pValue;

    def setChannel(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.channel = pValue
    
    def setShow(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.show = pValue
    
    def setTitle(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.title = pValue
    
    def setDescription(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.description = pValue
    
    def setExcludeTitle(self, pValue):
        if pValue is None or pValue == "":
            pValue = []
        else:
            pValue = pValue.split('|')
        self.excludeTitle = pValue
    
    def setMinLength(self, pValue):
        if pValue is None or pValue == '' or not pValue.isnumeric():
            pValue = '0'
        self.minLength = int(pValue)*60
    
    def setIgnoreTrailer(self, pValue):
        self.ignoreTrailer = pValue
    
    ##
    def toDict(self):
        return {
            "id" : self.id,
            "name" : self.name,
            "channel" : self.channel,
            "title" : self.title,
            "show" : self.show,
            "description" : self.description,
            "excludeTitle" : self.excludeTitle,
            "minLength" : self.minLength,
            "ignoreTrailer" : self.ignoreTrailer,
            "when" : self.when
            }
    
    def fromDict(self, aObject):
        self.id = aObject["id"]
        self.name = aObject["name"]
        self.channel = aObject["channel"]
        self.title = aObject["title"]
        self.show = aObject["show"]
        self.description = aObject["description"]
        self.excludeTitle = aObject["excludeTitle"]
        self.minLength = aObject["minLength"]
        self.ignoreTrailer = aObject["ignoreTrailer"]
        self.when = aObject["when"]
        return self
