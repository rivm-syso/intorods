"""
Created on Mon May  6 14:28:12 2019
@author: Erwin van Wieringen
Purpose: abstract filesystem base class
"""

import fnmatch
import hashlib
import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime

BUF_SIZE = 1024 * 1024 * 4

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class fsFactory():
    _fscreators = {}

    def __init__(self):
        self._fscreators = {}
        self._optiontext = {}

    def register(self, name, creator, optionText):
        self._fscreators[name] = creator
        self._optiontext[name] = optionText

    def createfs(self, name, **params):
        creator = self._fscreators[name]
        return creator(**params)

    def listfs(self):
        print('Filesystem   Options\n===============================================')
        for i in self._fscreators:
            print("%-10s %-40s" % (i, self._optiontext[i]))


factory = fsFactory()


# class fsbuilder():
#    def __init__(self):
#        self._instance = None
#
#    def options(self):
#        return '-'


class fsobject_base(ABC):
    def __init__(self, fso, path):
        self.fso = fso
        self.path = path
        self._checksum = None

    @abstractmethod
    def isdir(self):
        pass

    @abstractmethod
    def isfile(self):
        pass

    def accessible(self):
        # Test if object is accessible for reading
        # can be reimplemented in derived classes
        try:
            _ = self.open('r')
        except:
            return False
        return True

    def calculate_checksum(self):
        #        logger.debug('Expensive checksum calc for %s' % self.path)
        sha256 = hashlib.sha256()
        with fopen(self, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    @property
    def checksum(self):
        if self._checksum is None:
            self._checksum = self.calculate_checksum()
        return self._checksum

    @checksum.setter
    def checksum(self, cs):
        self._checksum = cs

    def compareto(self, other, compareChecksums=True):
        if compareChecksums:
            if self.checksum == other.checksum:
                return True
                # fixes an issue where files are registered with correct hash in ICAT, but not copied correctly
                if self.filesize() == other.filesize():
                    if self.utc_mtime() == other.utc_mtime():
                        return True
        else:
            if self.filesize() == other.filesize():
                if self.utc_mtime() == other.utc_mtime():
                    return True
        return False

    def copyto(self, dest_fs, dest_path):
        source_fp = self.open('rb')
        dest_fp = dest_fs.createfile(dest_path)
        shutil.copyfileobj(source_fp, dest_fp, BUF_SIZE)
        source_fp.close()
        dest_fp.close()
        dest_fs.invalidate_cache_entry(dest_path)

    @abstractmethod
    def filesize(self):
        pass

    def open(self, mode):
        raise 'fsobject_base.open not implemented'

    def shortname(self):
        return self.path.split('/')[-1]

    @abstractmethod
    def utc_mtime(self):
        pass


class fopen():
    def __init__(self, ff, mode):
        self.objf = ff
        self.mode = mode
        self.fp = None

    def __enter__(self):
        self.fp = self.objf.open(self.mode)
        return self.fp

    def __exit__(self, ftype, value, traceback):
        self.fp.close()


class fs_base(ABC):
    @abstractmethod
    def __init__(self, supportsopen=False):
        self.supportsopen = supportsopen
        self.files = {}

    def refresh(self):
        # Can be used to reconnect in the case of filesystems that are
        # connection-based (smb, irods, ftp)
        pass

    def cleanup(self):
        pass

    def invalidate_cache(self):
        self.files = {}

    def invalidate_cache_entry(self, path):
        if path in self.files:
            del self.files[path]

    @abstractmethod
    def ls(self, path):
        pass

    def lsdirnames(self, path):
        result = [a.shortname() for a in self.ls(path) if a.isdir()]
        return result

    def lsfilenames(self, path):
        result = [a.shortname() for a in self.ls(path) if not a.isdir()]
        return result

    def lsdirs(self, path, skip_inaccessible=False):
        if skip_inaccessible:
            result = [a for a in self.ls(
                path, skip_inaccessible=True) if a.isdir() and a.accessible()]
        else:
            result = [a for a in self.ls(path) if a.isdir()]
        return result

    def _pathsplit(self, path):
        spath = path.split('/')
        base = '/' + '/'.join(spath[1:-1])
        return base, spath[-1]

    @abstractmethod
    def fileexists(self, path):
        pass

    def glob(self, path):
        result = []
        head, tail = os.path.split(path)
        for filename in self.lsfilenames(head):
            if fnmatch.fnmatch(filename, tail):
                result.append(os.path.join(head, filename))
        return result

    def foldermtime(self, path):
        mtime = 0
        pathListing = self.ls(path)
        for entry in pathListing:
            if entry.isdir() and entry.shortname() != '.' and entry.shortname() != '..':
                mtime = max(mtime, self.foldermtime(entry.path))
            else:
                mtime = max(mtime, entry.utc_mtime())
        return mtime

    @abstractmethod
    def folderexists(self, path):
        pass

    @abstractmethod
    def _getfile(self, path):
        pass
        # return fsobject_base(self, path)

    def getfile(self, path):
        if path not in self.files:
            self.files[path] = self._getfile(path)
        return self.files[path]

    def getfolder(self, path):
        return self.getfile(path)

    @abstractmethod
    def mkdir(self, path, parents=False):
        pass

    def createfile(self, path):
        logger.error('%s :createfile not implemented in ' % self.__class__)
        exit(2)

    def deletefile(self, path):
        logger.error('%s :deletefile not implemented in ' % self.__class__)
        exit(2)

    def syncfolderto(self, sourcepath, destfs, destpath):
        logger.debug("sync_folder %s to %s" % (sourcepath, destpath))

        copyCounter = 0

        if not destfs.folderexists(destpath):
            destfs.mkdir(destpath)

        for entry in self.ls(sourcepath):
            destfile = os.path.join(destpath, entry.shortname())
            if entry.isdir():
                if not entry.shortname() in ['.', '..']:
                    self.syncfolderto(entry.path, destfs, destfile)
            else:
                bcopy = False
                if not destfs.fileexists(destfile):
                    logger.debug('Destination not found')
                    bcopy = True
                elif not entry.compareto(destfs.getfile(destfile)):
                    logger.debug('Comparison failed')
                    bcopy = True
                if bcopy:
                    logger.debug('Copy %s to %s' % (entry.path, destfile))
                    copyCounter += 1
                    if destfs.supportsopen:
                        entry.copyto(destfs, destfile)
                    elif self.supportsopen():
                        with entry.open("rb") as fp_source:
                            destfs.copyfrom(fp_source, destfile)
                    else:
                        logger.error('Error: cannot copy %s to %s' %
                                     (entry.shortname(), destfile))
                        exit(2)

                    destfs.getfile(destfile).set_mtime(entry.utc_mtime())

        return copyCounter
