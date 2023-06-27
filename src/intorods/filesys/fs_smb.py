# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 09:12:30 2020
SMB class for the filesys library
@author: Erwin van Wieringen
"""
import logging
import socket
import tempfile
import os

from smb.SMBConnection import SMBConnection
from smb import smb_constants

from intorods.filesys.fs_base import factory, fs_base, fsobject_base

logger = logging.getLogger(__name__)


def myshortname():
    return socket.gethostname().split('.')[0]


def uxtowin(path):
    return '\\'.join(path.split('/'))


def wintoux(path):
    return '/'.join(path.split('\\'))


class file_smb(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self.attr = fso.smb_conn.getAttributes(
            self.fso.share, uxtowin(self.path))

    def copyto(self, dest_fs, dest_path):
        with dest_fs.createfile(dest_path) as destfile:
            self.fso.smb_conn.retrieveFile(
                self.fso.share, uxtowin(self.path), destfile)

    def close(self):
        self.file_obj.close()

    def open(self, mode):
        self.file_obj = tempfile.NamedTemporaryFile()
        self.fso.smb_conn.retrieveFile(
            self.fso.share, uxtowin(self.path), self.file_obj)
        self.file_obj.seek(0)
        return self.file_obj

    def filesize(self):
        return self.attr.file_size

    def isdir(self):
        return self.attr.file_attributes & smb_constants.ATTR_DIRECTORY > 0

    def isfile(self):
        return not self.isdir()

    def utc_mtime(self):
        return int(self.attr.last_write_time//1)

# TODO
    def local_mtime(self):
        return 0

# TODO
    def set_mtime(self, mtime):
        pass


class fs_smb(fs_base):
    def __init__(self, server='', share='', nbserver='', username='',
                 domain='', password=''):
        super().__init__(supportsopen=False)
        self.server = server
        if not nbserver:
            nbserver = server.split('.')[0].upper()
        self.nbserver = nbserver
        self.username = username
        self.password = password
        self.domain = domain
        self.smb_conn = None
        self.connect()
        self.share = share

    def connect(self):
        client_machine_name = myshortname()
        if self.smb_conn:
            self.smb_conn.close()
        self.smb_conn = SMBConnection(self.username, self.password, client_machine_name,
                                      self.nbserver, domain=self.domain, is_direct_tcp=True)
        if not self.smb_conn.connect(self.server, 445):
            logger.error('Connection to %s failed' % self.server)
            exit(2)

    def refresh(self):
        self.connect()

    def copyfrom(self, source, path):
        self.smb_conn.storeFile(self.share, uxtowin(path), source)

    @staticmethod
    def factory(**kwargs):
        return fs_smb(**kwargs)

    def fileexists(self, path):
        try:
            _ = self.smb_conn.getAttributes(self.share, uxtowin(path))
            return True
        except:
            return False

    def folderexists(self, path):
        path_exists = self.exists(path)
        if path_exists:
            dirobject = self.getfile(path)
            return dirobject.isdir()
        return False

    def _getfile(self, path):
        return file_smb(self, path)

    def lsdirs(self, path, skip_inaccessible=False):
        result = []
        for entry in self.smb_conn.listPath(self.share, uxtowin(path),
                                            search=smb_constants.SMB_FILE_ATTRIBUTE_DIRECTORY):
            if not entry.filename in ['.', '..']:
                fullpath = path + '/' + entry.filename
                try:
                    fileobject = self.getfile(fullpath)
                    result.append(fileobject)
                except:
                    pass
        return result

    def lsdirnames(self, path):
        result = []
        for entry in self.smb_conn.listPath(self.share, uxtowin(path),
                                            search=smb_constants.SMB_FILE_ATTRIBUTE_DIRECTORY):
            if not entry.filename in ['.', '..']:
                result.append(entry.filename)
        return result

    def lsfilenames(self, path):
        result = []
        SEARCH_MASK = smb_constants.SMB_FILE_ATTRIBUTE_HIDDEN | \
            smb_constants.SMB_FILE_ATTRIBUTE_SYSTEM | \
            smb_constants.SMB_FILE_ATTRIBUTE_ARCHIVE | \
            smb_constants.SMB_FILE_ATTRIBUTE_INCL_NORMAL
        for entry in self.smb_conn.listPath(self.share, uxtowin(path),
                                            search=SEARCH_MASK):
            result.append(entry.filename)
        return result

    def mkdir(self, path, parents=False):
        if parents:
            parentdir, dir = os.path.split(path)
            if not self.folderexists(parentdir):
                self.mkdir(parentdir, parents=True)
        self.smb_conn.createDirectory(self.share, uxtowin(path))

# TODO
    def open(self, path, mode):
        return None

    def ls(self, path):
        result = []
        for entry in self.smb_conn.listPath(self.share, uxtowin(path)):
            fullpath = path + '/' + entry.filename
            fileobject = self.getfile(fullpath)
            result.append(fileobject)
        return result


factory.register('smb', fs_smb.factory,
                 'server=<server>, share=<sharename>, \
                 nbserver=<netbios servername>, username=<user>, \
                 domain=<domain>, password=<password>')
