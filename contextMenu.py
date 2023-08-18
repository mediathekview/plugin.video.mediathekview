# -*- coding: utf-8 -*-
"""
Context Menu hook

Copyright (c) 2017-2018, codingPF
SPDX-License-Identifier: MIT

"""

import sys
import xbmc
import resources.lib.mvutils as mvutils
from urllib.parse import urlencode

if __name__ == '__main__':
    params = {"mode":"research", "doNotSave":"true", "search" : sys.listitem.getLabel()}
    utfEnsuredParams = mvutils.dict_to_utf(params)
    cmd = 'ActivateWindow(Videos,plugin://plugin.video.mediathekview?' + urlencode(utfEnsuredParams) + ")"
    #xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.mediathekview?mode=research&doNotSave=true&search={})'.format(sys.listitem.getLabel()))
    xbmc.executebuiltin(cmd)