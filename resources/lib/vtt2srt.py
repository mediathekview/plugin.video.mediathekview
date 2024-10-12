# -*- coding: utf-8 -*-
"""
VTT to SRT conversion module

Thanks to (c) Jansen A. Simanullang for his function taken from vtt-to-srt project
See https://github.com/jansenicus/vtt-to-srt.py

SPDX-License-Identifier: MIT
"""
import re


class vtt2srt(object):

    def convertContent(self, fileContents):

        replacement = re.sub(r'(\d\d:\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', fileContents)
        replacement = re.sub(r'(\d\d:\d\d).(\d\d\d) --> (\d\d:\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
        replacement = re.sub(r'(\d\d).(\d\d\d) --> (\d\d).(\d\d\d)(?:[ \-\w]+:[\w\%\d:]+)*\n', r'\1,\2 --> \3,\4\n', replacement)
        replacement = re.sub(r'WEBVTT\n', '', replacement)
        replacement = re.sub(r'Kind:[ \-\w]+\n', '', replacement)
        replacement = re.sub(r'Language:[ \-\w]+\n', '', replacement)
        # replacement = re.sub(r'^\d+\n', '', replacement)
        # replacement = re.sub(r'\n\d+\n', '\n', replacement)
        replacement = re.sub(r'<c[.\w\d]*>', '', replacement)
        replacement = re.sub(r'</c>', '', replacement)
        replacement = re.sub(r'<\d\d:\d\d:\d\d.\d\d\d>', '', replacement)
        replacement = re.sub(r'::[\-\w]+\([\-.\w\d]+\)[ ]*{[.,:;\(\) \-\w\d]+\n }\n', '', replacement)
        replacement = re.sub(r'Style:\n##\n', '', replacement)

        return replacement
