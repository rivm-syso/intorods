#!/usr/bin/env python3

import argparse
import logging
import multiprocessing as mp
import os
import ssl
import time
from pathlib import Path

import filesys.fs_irods
import filesys.fs_local
import irods.exception as ex
import yaml
from irods.column import Criterion, In
from irods.meta import iRODSMeta
from irods.models import Collection, DataObject, DataObjectMeta
from irods.session import iRODSSession
from tqdm import tqdm

from intorods.filesys.fs_base import factory

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

META_ATTR_OBJECT_ID = 'sys::object_id'
NUMBER_OF_THREADS = 4
OMIT_PARENT_DIRECTORIES = 4


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def find_files_by_objectid(object_ids):
    """find the objects with the given object-id"""
    # - use natural sql to speed things up
    # - use prepared statements on the database to speed things up even more...
    files = []
    if not object_ids:
        return files

    found_object_ids = []

    begin = time.process_time()
    for id_chunk in chunks(object_ids, 50):
        query = irodsSession.query(Collection.name, DataObject.name, DataObjectMeta.name, DataObjectMeta.value).filter(
            Criterion('=', DataObjectMeta.name, META_ATTR_OBJECT_ID)).filter(
            In(DataObjectMeta.value, id_chunk)
        )
        files += [f"{res[Collection.name]}/{res[DataObject.name]}" for res in query]
        found_object_ids += [f"{res[DataObjectMeta.value]}" for res in query]

    found_object_ids.sort()
    missing_object_ids = [x for x in object_ids if x not in found_object_ids]

    end = time.process_time()
    time_in_sec = end-begin
    logger.debug(
        f"searching for objects took {time_in_sec} sec, searched: {len(object_ids)}, found: {len(files)}")
    for id in missing_object_ids:
        logger.debug(f"WARN: could not find object with object_id: {id}")
    return files


def parse_yaml_file(input_file):
    """load yml file containing objectids
     ---
     object_ids:
       - 123
       - 456
       - 0815
     files:
       - /demoZone/projects/test/test1.txt
       - /demoZone/projects/test/test2.txt
    """
    objectIds = []
    files = []
    with open(input_file, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        objectIds = data.get('object_ids', [])
        files = data.get('path', [])
    return (objectIds, files)


def copyobj(entry, dfs, dfile):
    try:
        if dfs.fileexists(dfile):
            logger.error(
                'ERROR COPYING {}. File already exists: {}'.format(entry.path, dfile))
            return False
        entry.copyto(dfs, dfile)
        dfs.getfile(dfile).set_mtime(entry.utc_mtime())
    except Exception as ex:
        logger.error(
            'ERROR COPYING {}. Exception: {}'.format(entry.path, ex))
        return False
    return True

def download_files(output_dir, object_ids, files_by_path):
    files_by_id = find_files_by_objectid(object_ids)
    files = files_by_id + files_by_path
    logger.debug(f"will download {len(files)} files from irods." )

    fs_source = factory.createfs('irods')
    fs_dest = factory.createfs('local')

    # Create copy processes list
    procs = []

    def new_copy_process(i):
        logger.debug(f'Creating copy process {i}')
        reduced_list = files[i::NUMBER_OF_THREADS]
        p = mp.Process(target=get_files, args=(
            i, reduced_list, output_dir, fs_source, fs_dest))
        p.start()
        return p

    for i in range(0, NUMBER_OF_THREADS):
        procs.append(new_copy_process(i) )

    logger.debug(f"All {NUMBER_OF_THREADS} processes started")
    for i in range(0, NUMBER_OF_THREADS):
        procs[i].join()
    logger.debug(f"All {NUMBER_OF_THREADS} processes ended")


def get_files(i, files, output_dir, fs_source, fs_dest):
    logger.debug(f"T{i} will download {len(files)} files." )
    begin = time.process_time()
    count = 0
    for sourcefile in tqdm(files, position=i, desc=f"T{i}"):
        path, filename = os.path.split(sourcefile )
        #for clarity: +1 is used to always omit the root, the *subpath is nneded to convert the list of
        #path elements into bunch of parameters for the join-call
        subpath = path.split(os.sep)[1+OMIT_PARENT_DIRECTORIES:]
        destpath = os.path.join(os.getcwd(), output_dir, *subpath)
        destfile = os.path.join(destpath, filename)
        if not fs_dest.folderexists(destpath):
            Path(os.path.join(output_dir, *subpath)
                 ).mkdir(parents=True, exist_ok=True)
        entry = fs_source.getfile(sourcefile)
        if copyobj(entry, fs_dest, destfile):
            count += 1
    end = time.process_time()
    time_in_sec = end-begin
    logger.debug(f"T{i}: copying of objects took {time_in_sec} sec, requested: {len(files)}, copied: {count}")

#stolen from jobengine
#TODO: put in a shared helper?

def irodsConnect(irodsfile="", use_ssl=False, **kwargs):
    """Connect to irods iCAT and return iRODSSession object

    Args:
        irodsfile: irods environment file to use.
        use_ssl: use ssl if True
    
    Returns:
        iRODSSession object
    """
    if irodsfile:
        envFile = irodsfile
    else:
        try:
            envFile = os.environ['IRODS_ENVIRONMENT_FILE']
        except KeyError:
            envFile = os.path.expanduser('~/.irods/irods_environment.json')

    if use_ssl:
        context = ssl._create_unverified_context(purpose=ssl.Purpose.SERVER_AUTH,
                                                 cafile=None, capath=None, cadata=None)
        ssl_settings = {'irods_ssl_ca_certificate_file': '/etc/irods/ssl/irods.crt',
                        'ssl_context': context}
        session = iRODSSession(irods_env_file=envFile,
                               **ssl_settings, **kwargs)
    else:
        session = iRODSSession(irods_env_file=envFile, **kwargs)
    return session


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Download multiple files by meta-information')
    parser.add_argument('-f', '--file', help='file containing sys::object_ids to retrieve', type=str,required=False)
    parser.add_argument('-o', '--output', help='target directory', type=str,required=True)
    parser.add_argument('-l', '--ids', nargs='*',
                        help='list of sys::object_id', required=False)
    parser.add_argument('-i', '--irodsfile',
                        help='irods environment file', required=False)
    parser.add_argument('-S', '--ssl', help='Use SSL', action='store_true')
    parser.add_argument('-t', '--copy_threads',
                        help='Number of copy processes', type=int, default=4)
    parser.add_argument('-p', '--omit_directories',
                        help='Number of parent directories omitted when creating subdirectories in target-directory', type=int, default=4)
    args = parser.parse_args()

    irodsSession = irodsConnect(
        irodsfile=args.irodsfile, use_ssl=args.ssl, refresh_time=60)

    # Override default 120 sec connection timeout
    #irodsSession.connection_timeout = 900
    NUMBER_OF_THREADS = args.copy_threads
    OMIT_PARENT_DIRECTORIES = args.omit_directories

    object_ids = []
    if args.ids:
        object_ids = args.ids
    if args.file:
        object_ids, files = parse_yaml_file(args.file )

    download_files(args.output, object_ids, files )
