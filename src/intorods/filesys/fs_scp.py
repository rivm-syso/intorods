#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 16:08:06 2019

@author: Erwin van Wieringen
"""

import os
import re
import stat
import warnings

from cryptography.utils import CryptographyDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=CryptographyDeprecationWarning)
    import paramiko

from intorods.filesys.fs_base import factory, fs_base, fsobject_base


def esc(mystr):
    return re.sub('([$])', r'\\\1', mystr).strip()


class file_scp(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self._lstat = self.fso.sftp.lstat(self.path)

    def calculate_checksum(self):
        myhash = ""
        try:
            I = self.open("r")
            myhash = I.check("sha256")
        except IOError:
            pass
        if myhash == "":
            command = 'sha256sum "' + esc(self.path) + '"  | cut -f 1 -d" " '
            stdin, stdout, stderr = self.fso.ssh.exec_command(command)
            out0 = stdout.read().splitlines()[0]
            myhash = out0.decode().split("'")[0]
        return myhash

    def filesize(self):
        # return self.fso.sftp.lstat(self.path).st_size
        return self._lstat.st_size

    def isfile(self):
        return not stat.S_ISDIR(self._lstat.st_mode)

    def open(self, mode):
        return self.fso.sftp.open(self.path, mode)

    def set_mtime(self, mtime):
        self.fso.sftp.utime(self.path, (mtime, mtime))

    def utc_mtime(self):
        return self._lstat.st_mtime

    def isdir(self):
        return stat.S_ISDIR(self._lstat.st_mode)


class fs_scp(fs_base):
    def __init__(self, hostname='', user='', private_key=None, public_key='', port=22):
        super().__init__(supportsopen=True)
        self.hostname = hostname
        self.user = user if user else os.environ('USER')
        self.port = port

        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.WarningPolicy)
        self.ssh.connect(self.hostname, username=self.user, port=self.port, key_filename=private_key)
        self.sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())


    @staticmethod
    def factory(**kwargs):
        return fs_scp(**kwargs)

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
        return file_scp(self, path)

    def ls(self, path):
        result = []
        for file in self.sftp.listdir(path):
            fullpath = path + '/' + file
            fileobject = self.getfile(fullpath)
            result.append(fileobject)
        return result

    def mkdir(self, path, parents=False):
        exit(1)

    def open(self, path, mode):
        return self.sftp.open(path, mode)


factory.register('scp', fs_scp.factory, 'hostname=<hostname>,user=<username>,private_key=<private key file>')
