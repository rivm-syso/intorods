#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 25 11:00:00 2023

@author: jansser
"""

import os
import stat
from datetime import datetime

import ftputil

from intorods.filesys.fs_base import factory, fs_base, fsobject_base


class file_ftp(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self._lstat = self.fso.ftp.lstat(self.path)

    def filesize(self):
        return self.fso.ftp.path.getsize(self.path)

    def isfile(self):
        return not stat.S_ISDIR(self._lstat.st_mode)


    def accessible(self):
        if self.isdir():
            try:
                self.fso.ftp.listdir(self.path)
            except:
                return False
            return True
        else:
            try:
                fo = self.fso.ftp.file(self.path, "r")
                if fo:
                    return fo.readable()
            except IOError:
                return False
        return False

    def open(self, mode):
        return self.fso.ftp.open(self.path, mode)

    def set_mtime(self, mtime):
        # not implemented in ftputil, using raw FTP via underlying ftplib 
        # this is not implemented on all FTP servers, or you may lack rights!
        formatted_time = datetime.utcfromtimestamp(mtime).strftime('%Y%m%d%H%M%S')
        self.ftp._session.voidcmd(f"MFMT {self.path} {formatted_time}")

    def utc_mtime(self):
        return self._lstat.st_mtime

    def isdir(self):
        return stat.S_ISDIR(self._lstat.st_mode)

class fs_ftp(fs_base):
    def __init__(self, hostname='', user='anonymous', password='me@domain.com'):
        super().__init__(supportsopen=True)
        self.hostname = hostname
        self.user = user
        self.ftp = ftputil.FTPHost(hostname, user, password)
        # try to correct the difference in timezone. Due to the implementation,
        # this is only possible if you have write access to the ftp server!
        try:
            self.ftp.synchronize_times()
        except:
            pass

    @staticmethod
    def factory(**kwargs):
        return fs_ftp(**kwargs)

    def fileexists(self, path):
        try:
            fileobject = self.getfile(path)
        except:
            return False
        return fileobject.isfile()

    def folderexists(self, path):
        try:
            self.ftp.exists(path)
        except:
            return False
        return True

    def _getfile(self, path):
        return file_ftp(self, path)

    def ls(self, path):
        result = []
        try:
            for file in self.ftp.listdir(path):
                fullpath = os.path.join(path, file)
                fileobject = self.getfile(fullpath)
                result.append(fileobject)
        except:
            pass
        return result

    def mkdir(self, path, parents=False):
        exit(1)

    def open(self, path, mode):
        return self.ftp.open(path, mode)


factory.register('ftp', fs_ftp.factory,
                 'hostname=<hostname>,user=<username>,password=<password>')
