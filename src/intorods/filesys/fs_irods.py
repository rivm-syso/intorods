#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 12:14:23 2019

@author: Erwin van Wieringen
"""

import base64
import calendar as cal
import logging
import math
import os
import re
import ssl
import time

import irods.keywords as kw
from irods.column import Criterion
from irods.models import Collection, CollectionMeta, DataObject
from irods.session import iRODSSession

from intorods.filesys.fs_base import factory, fs_base, fsobject_base

logger = logging.getLogger(__name__)


def utc2local(utc):
    return time.mktime(time.localtime(utc))


class file_irods(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self.refresh()

    def refresh(self):
        self.irods_object = self.fso.irods_session.data_objects.get(self.path)

    def isdir(self):
        return False

    def calculate_checksum(self):
        cs = self.irods_object.checksum
        if cs is None:
            return super().calculate_checksum()
        else:
            sha2 = cs.split(':')[1]
            return base64.b64decode(sha2).hex()

    def filesize(self):
        return self.irods_object.size

    def isfile(self):
        return True

    def open(self, mode):
        return self.irods_object.open(mode[:1])

    def set_mtime(self, mtime):
        new_time = utc2local(mtime)
        self.irods_object.manager.modDataObjMeta(
            {"objPath": self.path}, {"dataModify": round(new_time)})
        self.refresh()

    def utc_mtime(self):
        mtime = cal.timegm(self.irods_object.modify_time.timetuple())
        return math.floor(mtime)

# TODO
    def local_mtime(self):
        return 0


class folder_irods(fsobject_base):
    def __init__(self, fso, path):
        super().__init__(fso, path)
        self.irods_object = fso.irods_session.collections.get(path)

    def filesize(self):
        return 0

    def isdir(self):
        return True

    def isfile(self):
        return False

    def accessible(self):
        raise NotImplementedError

    def removemeta(self, name):
        for m in self.irods_object.metadata.get_all(name):
            self.irods_object.metadata.remove(m)

    def setmeta(self, name, value, units=''):
        try:
            self.irods_object.metadata.add(name, value, units)
        except:
            pass

    def replaceorsetmeta(self, name, value):
        self.removemeta(name)
        self.setmeta(name, value)

    def getmeta(self, name):
        return self.irods_object.metadata.get_one(name).value

    def getorsetmeta(self, name, default):
        if not self.irods_object.metadata.get_all(name):
            self.setmeta(name, default, '')
        return self.getmeta(name)

    def utc_mtime(self):
        return 0


class fs_irods(fs_base):
    def __init__(self, resource='', use_ssl=False, host=None, user=None,
                 zone=None, password=None, port=1247, timeout=None):
        super().__init__(supportsopen=True)

        if host:
            session_params = {'host': host, 'port': port, 'zone': zone,
                              'user': user, 'password': password}
        else:
            try:
                env_file = os.environ['IRODS_ENVIRONMENT_FILE']
            except KeyError:
                env_file = os.path.expanduser(
                    '~/.irods/irods_environment.json')
            session_params = {'irods_env_file': env_file}

        if use_ssl:
            context = ssl._create_unverified_context(purpose=ssl.Purpose.SERVER_AUTH,
                                                     cafile=None, capath=None, cadata=None)
            ssl_settings = {'irods_ssl_ca_certificate_file': '/etc/irods/ssl/irods.crt',
                            'ssl_context': context}
            self.irods_session = iRODSSession(**session_params, **ssl_settings)
        else:
            self.irods_session = iRODSSession(**session_params)
        if timeout:
            self.irods_session.connection_timeout = int(timeout)
        self.resource = resource

    def cleanup(self):
        if self.irods_session:
            self.irods_session.cleanup()
            self.irods_session = None

    def __del__(self):
        self.cleanup()

    def ls(self, path):
        result = []
        coll = self.irods_session.collections.get(path)
        for subcoll in coll.subcollections:
            result.append(folder_irods(self, subcoll.path))
        for entry in coll.data_objects:
            result.append(self.getfile(entry.path))
        return result

    def lsdirs(self, path, skip_inaccessible=False):
        logger.error("lsdirs not implemented")
        exit(2)

    @staticmethod
    def factory(**kwargs):
        return fs_irods(**kwargs)

    def fileexists(self, path):
        base, file = self._pathsplit(path)
        query = self.irods_session.query(
            Collection.name, DataObject.name).filter(
                Criterion('=', Collection.name, base)).filter(
                    Criterion('=', DataObject.name, file))
        return bool(list(query.get_results()))

    def findfolder(self, name, meta=[]):
        result = []
        query = self.irods_session.query(Collection.name).filter(
            Criterion('like', Collection.name, '%/' + name))
        for m in meta:
            query = query.filter(
                Criterion('=', CollectionMeta.name, m['field'])).filter(
                    Criterion(m['op'], CollectionMeta.value, m['value']))
        for coll in query.get_results():
            collname = coll[Collection.name]
            if not re.match('/[^/]*/trash/.*', collname):
                result.append(folder_irods(self, collname))
        return result

    def folderexists(self, path):
        query = self.irods_session.query(Collection).filter(
            Criterion('=', Collection.name, path))
        return bool(list(query.get_results()))

    def _getfile(self, path):
        return file_irods(self, path)

    def getfolder(self, path):
        return folder_irods(self, path)

    def mkdir(self, path, parents=False):
        if parents:
            parentdir, dir = os.path.split(path)
            if not self.folderexists(parentdir):
                self.mkdir(parentdir, parents=True)
        self.irods_session.collections.create(path)
        return folder_irods(self, path)

# Opening an object with create=True should be used for irods4.3.0
# instead of create and open in two statements.
# Check: https://github.com/irods/irods/issues/6808
    def createfile(self, path):
        options = {kw.DEST_RESC_NAME_KW: self.resource}
        return self.irods_session.data_objects.open(path, 'w', create=True, **options)

    def deletefile(self, path):
        self.irods_session.data_objects.unlink(path, True)
        self.invalidate_cache_entry(path)

    def open(self, path, mode):
        options = {kw.FORCE_FLAG_KW: ''}
        obj = self.irods_session.data_objects.create(path, **options,
                                                     resource=self.resource)
        return obj.open(mode[:1])


factory.register('irods', fs_irods.factory,
                 'resource=<dest resource>,use_ssl=<true|false>,host=<host>,user=<user>,password=<passwd>,zone=<zone>,timeout=<timeout>')
