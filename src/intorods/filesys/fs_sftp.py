#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 16:08:06 2019

@author: Erwin van Wieringen
"""

import glob
import hashlib
import os
import re
import stat
import warnings

from cryptography.utils import CryptographyDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=CryptographyDeprecationWarning)
    import paramiko

from intorods.filesys.fs_base import factory, fopen, fs_base, fsobject_base


def esc(mystr):
    return re.sub('([$])', r'\\\1', mystr).strip()


class file_sftp(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self._lstat = self.fso.sftp.lstat(self.path)

    def filesize(self):
        # return self.fso.sftp.lstat(self.path).st_size
        return self._lstat.st_size

    def isfile(self):
        return not stat.S_ISDIR(self._lstat.st_mode)

    def accessible(self):
        if self.isdir():
            try:
                self.fso.sftp.listdir(self.path)
            except:
                return False
            return True
        else:
            try:
                fo = self.fso.sftp.file(self.path, "r")
                if fo:
                    return fo.readable()
            except IOError:
                return False
        return False

    def calculate_checksum(self):
        BUF_SIZE = 1024 * 1024
        sha256 = hashlib.sha256()
        with fopen(self, 'r') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    def open(self, mode):
        return self.fso.sftp.open(self.path, mode)

    def set_mtime(self, mtime):
        self.fso.sftp.utime(self.path, (mtime, mtime))

    def utc_mtime(self):
        return self._lstat.st_mtime

    def isdir(self):
        return stat.S_ISDIR(self._lstat.st_mode)


class fs_sftp(fs_base):
    def __init__(self, hostname='', user='', password=''):
        super().__init__(supportsopen=True)
        self.hostname = hostname
        self.user = user
        port = 22
        self.t = paramiko.Transport((self.hostname, port))
        self.t.connect(username=user, password=password)

#        transport.start_client(event=None, timeout=15)
#        transport.get_remote_server_key()
#        transport.auth_publickey(username, sftp_key, event=None)
#        transport.auth_password(username, password, event=None)
#        sftp = paramiko.SFTPClient.from_transport(transport)
        self.sftp = paramiko.SFTPClient.from_transport(self.t)

    @staticmethod
    def factory(**kwargs):
        return fs_sftp(**kwargs)

    def fileexists(self, path):
        try:
            fileobject = self.getfile(path)
        except:
            return False
        return fileobject.isfile()

    def folderexists(self, path):
        try:
            self.sftp.listdir(path)
        except:
            return False
        return True

    def _getfile(self, path):
        return file_sftp(self, path)

    def ls(self, path):
        result = []
        try:
            for file in self.sftp.listdir(path):
                fullpath = path + '/' + file
                fileobject = self.getfile(fullpath)
                result.append(fileobject)
        except:
            pass
        return result

    def lsfilenames(self, path):
        return self.sftp.listdir(path)

    def mkdir(self, path, parents=False):
        exit(1)

    def open(self, path, mode):
        return self.sftp.open(path, mode)


factory.register('sftp', fs_sftp.factory,
                 'hostname=<hostname>,user=<username>,password=<password>')
