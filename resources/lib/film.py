# -*- coding: utf-8 -*-
"""
The film model module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
Licensed under MIT License
"""


class Film(object):
    """ The film model class """

    def __init__(self):
        self.filmid = 0
        self.title = ''
        self.show = ''
        self.channel = ''
        self.description = ''
        self.seconds = 0
        self.size = 0
        self.aired = ''
        self.url_sub = ''
        self.url_video = ''
        self.url_video_sd = ''
        self.url_video_hd = ''
