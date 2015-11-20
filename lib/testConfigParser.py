#!/usr/bin/python

import os
import time
from ConfigParser import ConfigParser
from cStringIO import StringIO
from ordereddict import OrderedDict


class SpecConfig(object):
    #  sections            name      ordered?
    __sects = OrderedDict((('setup',     False),
                           ('motors',    True),
                           ('detectors', True),
                           ('extra_pvs', True),
                           ('counters',  True)))

    def __init__(self, filename=None, text=None):
        for s in self.__sects:
            setattr(self, s, {})

        self._cp = ConfigParser()
        if filename is None:
            if (os.path.exists(DEF_CONFFILE) and
                os.path.isfile(DEF_CONFFILE)):
                filename = DEF_CONFFILE

        self.filename = filename
        if filename is not None:
            self.Read(filename)

    def Read(self, fname):
        "read config"
        if fname is None:
            return
        ret = self._cp.read(fname)
        if len(ret) == 0:
            time.sleep(0.25)
            ret = self._cp.read(fname)
        self.filename = fname
        # process sections
        for sect, ordered in self.__sects.items():
            if not self._cp.has_section(sect):
                continue
            thissect = {}
            if ordered:
                thissect = OrderedDict()
            for opt in self._cp.options(sect):
                val = self._cp.get(sect, opt)
				#print 'val: ', val
                if '||' in val:
                    words = [i.strip() for i in val.split('||')]
                    label = words.pop(0)
                    #print 'label: ', label
                    #print 'words: ', words
                    if len(words) == 1:
                        words = words[0]
                    else:
                        words = tuple(words)
                    #print 'words: ', words
                    thissect[label] = words
                else:
                    thissect[opt] = val
                setattr(self, sect, thissect)
                #print 'thissect: ', thissec

