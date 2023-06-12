#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  8 10:25:59 2019

@author: Erwin van Wieringen
"""

import glob
import math
import os

from intorods.filesys.fs_base import factory, fs_base, fsobject_base


class file_local(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self.fp = None
        self.__update()

    def __update(self):
        self.stat = os.stat(self.path)

    def filesize(self):
        return self.stat.st_size

    def isdir(self):
        return os.path.isdir(self.path)

    def isfile(self):
        return os.path.isfile(self.path)

    def accessible(self):
        if self.isdir():
            return os.access(self.path, os.X_OK)
        else:
            return os.access(self.path, os.R_OK)

    def close(self):
        self.fp.close()

    def open(self, mode):
        self.fp = open(self.path, mode)
        return self.fp

    def utc_mtime(self):
        return math.floor(self.stat.st_mtime)

    def set_mtime(self, mtime):
        os.utime(self.path, (mtime, mtime))
        self.__update()


class fs_local(fs_base):
    def __init__(self):
        super().__init__(supportsopen=True)

    def createfile(self, path):
        return open(path, 'wb')

    @staticmethod
    def factory(**kwargs):
        return fs_local(**kwargs)

    def fileexists(self, path):
        # Check existence of path. Path may contain glob wildcard characters.
        return len(glob.glob(str(path))) > 0

    def folderexists(self, path):
        return os.path.isdir(path)

    def _getfile(self, path):
        return file_local(self, path)

    def getfolder(self, path):
        return file_local(self, path)

    def ls(self, path, skip_inaccessible=False):
        result = []
        for entry in os.listdir(path):
            fullpath = path + '/' + entry
            try:
                ff = self.getfile(fullpath)
                result.append(ff)
            except Exception as e:
                if not skip_inaccessible:
                    raise e
        return result

    def glob(self, path):
        return glob.glob(str(path))
        pass

    def lsdirnames(self, path):
        result = [f.name for f in os.scandir(path) if f.is_dir()]
        return result

    def lsfilenames(self, path):
        result = [f.name for f in os.scandir(path) if not f.is_dir()]
        return result

    def mkdir(self, path, parents=False):
        if parents:
            os.makedirs(path)
        else:
            os.mkdir(path)

    def open(self, path, mode):
        return open(path, mode)

    def deletefile(self, path):
        os.remove(path)


factory.register('local', fs_local.factory, '')
