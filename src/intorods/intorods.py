#!/usr/bin/env python3

"""
Created on Mon May  6 14:28:12 2019
@author: Erwin van Wieringen

"""

import argparse
import hashlib
import json
import logging
import logging.config
import os
import re
import sys
import time

import irods.exception as ex
import yaml
from jsonschema import ValidationError, validate

import intorods.filesys.fs_ftp
import intorods.filesys.fs_irods
import intorods.filesys.fs_local
import intorods.filesys.fs_scp
import intorods.filesys.fs_sftp

from .filesys.fs_base import factory
from .filesys.fs_smb import wintoux
from .filesys.loghandlers import log_to_stdout, log_to_syslog
from .filesys.sync import sync

logger = logging.getLogger(None)
for _ in ("irods.connection", "irods.manager.metadata_manager", "irods.message", "irods.pool", 
          "irods.session", "paramiko.transport.sftp", "SMB.SMBConnection"):
    logging.getLogger(_).disabled = True
logger.setLevel(logging.WARNING)

FILE_FORMAT_TEXT = 'text'

#the baseclear format
FILE_FORMAT_BASECLEAR = 'baseclear'
BASECLEAR_SCHEMA_FILE = 'schemas/baseclear_checksum_file_schema.json'

FILE_FORMAT_GENERIC_JSON = 'generic'
GENERIC_JSON_SCHEMA_FILE = 'schemas/pipeline_output_schema.json'

METADATA_TEMPLATE = {
    '%sf': lambda s, d: os.path.basename(s),
    '%sp': lambda s, d: s,
    '%df': lambda s, d: os.path.basename(d),
    '%dp': lambda s, d: d,
    '%t': lambda s, d: str(time.time())
}


def formattime(seconds):
    """
    Creates a readable datetime from a duration in seconds
    """
    days = (seconds // 86400)
    hours = (seconds // 3600) % 24
    minutes = (seconds // 60) % 60
    seconds = seconds % 60
    out = "%2i days %2i:%2i:%2i " % (days, hours, minutes, seconds)
    return out


def parse_extra_options(options):
    """
    Creates a dict from a list of options in the form
    name1=value1,name2=value2
    """
    outp = {}
    if options:
        field = options.split(',')
        for option in field:
            kwval = option.split('=')
            outp[kwval[0]] = kwval[1]
    return outp


def parse_checksum_file(fs_source, folder, checksumfile, file_format, json_schema):
    """
        returns a dictionary, containing complete/path/to/file --> hash-value
        returns None to indicate to caller the checksumfile is missing / invalid, either abort or continue with next folder...
    """
    cslist = {}
    logger.debug('Searching checksums-file %s' % checksumfile)
    checksumfilepattern = os.path.join(folder.path, checksumfile)
    csfile_list = fs_source.glob(checksumfilepattern)
    if not 1 == len(csfile_list):
        logger.debug('No definitive match of checksumfile found. Pattern: {} in folder: {}, matches: {}'.format(
            checksumfile, folder.path, len(csfile_list)))
        return None
    checksumfilepath = csfile_list[0]
    if not fs_source.fileexists(checksumfilepath):
        logger.error('Required checksumfile %s not found' % checksumfile)
        return None
    logger.debug('Adding checksums from file %s' % checksumfilepath)
    csfile = fs_source.getfile(checksumfilepath)
    if not csfile.accessible():
        logger.error('Checksumfile %s is not accessible' % checksumfilepath)
        return None
    #put also the samplesheet itself into the cslist for synchronization
    csf_name = os.path.basename(checksumfilepath)
    cslist[wintoux(csf_name)] = None
    #depending on file format, change behavior....
    if file_format == FILE_FORMAT_TEXT:
        with csfile.open('r') as fh:
            lines = fh.readlines()
            for line in lines:
                if not type(line) is str:
                    line = line.decode('utf-8')
                hashvalue, filename = line.rstrip().split('  ')
                cslist[wintoux(filename)] = hashvalue
        return cslist

    elif file_format == FILE_FORMAT_GENERIC_JSON:
        with csfile.open('r') as fh:
            csf_content = json.load(fh)
            try:
                validate(instance=csf_content, schema=json_schema)
            except ValidationError as ex:
                logger.error("ERROR validating checksumfile '{}' threw: '{}'".format(
                    checksumfilepath, ex.message))
                return None
            #parse content
            for data_object in csf_content['objects']:
                hashvalue = data_object['checksum']
                filepath = wintoux(data_object['path'])
                objtype = data_object['type']
                if objtype != 'dataobject':
                    continue
                if filepath in cslist:
                    logger.error(
                        "ERROR parsing checksumfile '{}' is referenced multiple times".format(filepath))
                    return None
                #further sanity checks?
                cslist[filepath] = hashvalue
        return cslist

    elif file_format == FILE_FORMAT_BASECLEAR:
        #magic string, sub directory the actual seqencer files are contained (within further directory structures)
        #Better would be to define this folder in a field of the json-file
        #TODO: once BaseClear abides by the new format, remove magic strings and use always path-property
        SEQUENCE_FILE_DIR = 'raw_sequences'
        #validate against schema definition
        with csfile.open('r') as fh:
            csf_content = json.load(fh)
            try:
                validate(instance=csf_content, schema=json_schema)
            except ValidationError as ex:
                logger.error("ERROR validating checksumfile '{}' threw: '{}'".format(
                    checksumfilepath, ex.message))
                return None
            #parse content
            for sample in csf_content['samples']:
                flowcellid = sample['flowcellid']
                for pair in sample['pairs']:
                    if 'path' in pair.keys():
                        path = pair['path']
                    else:
                        path = os.path.join(SEQUENCE_FILE_DIR, flowcellid)
                    hashvalue = pair['checksum']
                    filename = pair['filename']
                    filepath = os.path.join(path, filename)
                    ux_filepath = wintoux(filepath)
                    if ux_filepath in cslist:
                        logger.error("ERROR parsing checksumfile '{}', file: '{}' is referenced multiple times".format(
                            checksumfilepath, ux_filepath))
                        return None
                    #further sanity checks?
                    cslist[ux_filepath] = hashvalue
        return cslist
    else:
        logger.error('Unknown file format "%s" for checksum file!' %
                     file_format)
        return None


def resolve_meta_template(value, sourcefolder, destfolder):
    """Replace template variables in metadata:
        %sf  basename of source path
        %sp  full source path
        %df  basename of dest path
        %dp  full dest path
    """

    for template, func in METADATA_TEMPLATE.items():
        value = value.replace(template, func(sourcefolder, destfolder))
    return value


def test_completion_avu(dfolder, completion_avu):
    """Will return true if completion avu is present on dfolder
    """
    completion_attr, completion_value = completion_avu.split('=')
    try:
        value = dfolder.getmeta(completion_attr)
    except KeyError:
        return False

    return completion_value == value


def sync_folder(fs_source, folder, fs_dest, destfolder, objdfolder,
                sfs_name, sfs_opts, dfs_name, dfs_opts,
                compareChecksums,
                cslist,
                metadata,
                copy_procs,
                excludelist,
                compare,
                minimum_age,
                cs_filters,
                scan_filters,
                scan):
    logger.debug('Replicating to irods folder {}'.format(objdfolder.path))
    syncresult = sync(fs_source, folder.path, fs_dest, destfolder,
                      sfs_name, sfs_opts, dfs_name, dfs_opts,
                      compareChecksums=compareChecksums,
                      filelist=cslist, worker_processes=copy_procs,
                      excludelist=excludelist,
                      compare=compare,
                      minimum_age=minimum_age,
                      scan_filters=scan_filters,
                      cs_filters=cs_filters,
                      scan=scan)
    if syncresult:
        logger.info('Folders are EQUAL')
        # Add metadata from metadata list
        for attr, v in metadata.items():
            value = resolve_meta_template(v, folder.path, destfolder)
            objdfolder.replaceorsetmeta(attr, value)
    else:
        logger.error('SYNC FAILED for folder %s' % folder.path)
    return syncresult


def replicate_data_folder(sfs_name, sfs_opts, dfs_name, dfs_opts,
                          sourcepath, destpath,
                          checksumfile='', checksumfileformat='', checksumfileschema='', compareChecksums=True, flagfile='', flag_age=0,
                          minage=0, maxage=999999999, pattern='',
                          metadata={}, skip_subdirs=0,
                          copy_procs=1, excludelist=[],
                          completion_avu=None,
                          mark_complete=False,
                          compare=True,
                          timestamp_list=[],
                          minimum_age=None,
                          cs_filter_file='',
                          scan=False,
                          scan_filter_file=''):
    """Replicate a data folder from source filesystem to destination 
    file system by iterating over the direct subfolders of the given
    sourcepath and syncing them piecewise.

    Args:
        == Source and destination parameters ==
        sfs_name: Source filesystem name.
        sfs_opts: Source filesystem options, as passed to fs_<name> class.
        dfs_name: Destination filesystem name.
        dfs_opts: Dest. filesystem options, as passed to fs_<name> class.
        sourcepath: File path on source system to be replicated.
        destpath: File path on destination system to store replication.

        == Source selection parameters ==
        checksumfile: File path on source with checksums for all files
            under <sourcepath>. Wildcards are allowed.
        checksumfileformat: Format of checksum file, either:
            text: one line per file, consisting of cheksum and filename
            json: structured file following the jsonschema defined.
        checksumfileschema: Only relevant for ckecksumfileformat json: file containing a jsonschema definition 
            the checksumfile will be validated against
        compareChecksums: Flag to check file checksums syncing.
        flagfile: Filename, when non-empty this ignores (sub)folders on 
            source filesystem that do not contain such a file.
        flag_age: minimum age (in seconds) of flag file before starting import
        minage: Filter on minimum age of subfolder.
        maxage: Filter on maximum age of subfolder.
        pattern: Regex filter on path of subfolder.
        exclude: List of regex patterns of files to exclude from sync
        timestamp_list: dict of attr: age pairs. The destination collection must exist. All
            the _attr_ attributes must be present. The value is assumed to be a timestamp. In order to be copied,
            it has to be at least _age_ old. Added especially for adding image data to a collection after 
            processing has finished

        == uniqueid parameters == 
        The script adds uniqueid metadata to the destination folder.
        This is used to determine if a data import has already been started
        or finished earlier, and the destination folder has moved in the meantime.

        == Metadata parameters ==
        metadata: List of AVUs to be set on the destination folder on
            succesful replication. 

        == Misc parameters ==
        skip_subdirs: Integer, descend this number of single-entry 
            directories before starting sync.
        copy_procs: Integer, number of processes to use for parallel file
            transfer.
    """

    # The (optional) schema definition is global, and should be read and parsed only once,
    # checksumfileschema is set by default.
    if checksumfileformat in [FILE_FORMAT_BASECLEAR, FILE_FORMAT_GENERIC_JSON]:
        with open(checksumfileschema) as f:
            JSON_SCHEMA = json.load(f)
    else:
        JSON_SCHEMA = None

    # Check all the remote data folders for first level subfolders
    logger.debug('Replicate %s to %s' % (sourcepath, destpath))

    fs_source = factory.createfs(sfs_name, **sfs_opts)
    fs_dest = factory.createfs(dfs_name, **dfs_opts)

    """
    Skip skip_subdirs subdirs, to handle minion data export
    """
    def folderlist(fs, current_dir, levels=0):
        if levels == 0:
            try:
                dirs = fs.lsdirs(current_dir, skip_inaccessible=True)
            except:
                # Skip inaccessible/special directories
                logger.error("ERROR reading directory %s" % current_dir)
                dirs = []
        else:
            dirs = []
            for subfolder in fs.lsdirs(current_dir, skip_inaccessible=True):
                dirs = dirs + folderlist(fs, subfolder.path, levels-1)
        return dirs

    for folder in folderlist(fs_source, sourcepath, levels=skip_subdirs):
        logger.debug("Process folder %s" % folder.path)
        if pattern:
            rePattern = re.compile(pattern + '$', re.IGNORECASE)
            if not rePattern.match(folder.shortname()):
                logger.debug('Folder %s does not match pattern %s' %
                             (folder.shortname(), pattern))
                continue
        if flagfile:
            # Note: flagfile may contain wildcards!
            # List files matching the 'flagfile' pattern,
            # determine the age of the newest one
            # and check against flag_age
            myflagfile = os.path.join(folder.path, flagfile)
            flagfile_list = fs_source.glob(myflagfile)
            min_age = 1E10
            if not flagfile_list:
                logger.debug('Cannot find flagfile %s' % myflagfile)
                continue
            for ff in flagfile_list:
                age = int(time.time() - fs_source.getfile(ff).utc_mtime())
                min_age = min(min_age, age)
            if min_age < flag_age:
                logger.info('Flag file(s) too new. Age is {}, min age is {}'.format(
                    min_age, flag_age))
                continue

        if minage > 0 or maxage < 999999999:
            logger.debug('Checking folder age {} - {}'.format(minage, maxage))
            folderage = int(time.time()) - fs_source.foldermtime(folder.path)
            logger.debug('Remote folder age is {} s'.format(folderage))
            if minage > 0:
                if folderage < minage:
                    logger.info('Recent changes - skipping folder')
                    continue
            if folderage > maxage:
                logger.info('Folder too old : %s - skipping' %
                            formattime(folderage))
                continue

        cslist = {}
        if checksumfile:
            cslist = parse_checksum_file(
                fs_source, folder, checksumfile, checksumfileformat, JSON_SCHEMA)
            if not cslist:
                continue

        destfolder = os.path.join(destpath, folder.shortname())
        if not fs_dest.folderexists(destfolder):
            fs_dest.mkdir(destfolder)

        objdfolder = fs_dest.getfolder(destfolder)
        sync_this_folder = True

        # Check timestamps on destination folder:
        if timestamp_list:
            logger.debug(
                'Verifying required timestamps on {}'.format(objdfolder.path))
            now = int(time.time())
            for t in timestamp_list:
                try:
                    v_str = objdfolder.getmeta(t)
                    v = float(v_str)
                except KeyError:
                    logger.error('timestamp attr {} missing on folder {}'.format(
                        t, objdfolder.path))
                    sync_this_folder = False
                    break
                except ValueError:
                    logger.error('timestamp attr {} on folder {} has invalid value {}'.format(
                        t, objdfolder.path, v_str))
                    sync_this_folder = False
                    break
                if now < (int(v) + int(timestamp_list[t])):
                    logger.info('timestamp attr {} on folder {} too new. Wait {} seconds'.format(
                        t, objdfolder.path, int(v)+int(timestamp_list[t])-now))
                    sync_this_folder = False
                    break

        # Params completion_avu determines copy selection
        # behaviour:
        # completion_avu == None: no check for completion attribute will be done
        #   when selecting folders to copy
        # completion_avu != None:
        #   only folders where completion_avu is not present will be copied

        if completion_avu and sync_this_folder:
            sync_this_folder = not test_completion_avu(
                objdfolder, completion_avu)
            if not sync_this_folder:
                logger.debug(
                    'Import for folder %s already marked complete' % folder.path)

        # Load the content of the filter files
        cs_filters = []
        if cs_filter_file:
            with open(cs_filter_file, 'r') as f:
                data = yaml.safe_load(f)
                cs_filters = data.get("filter", [])

        scan_filters = []
        if scan_filter_file:
            with open(scan_filter_file, 'r') as f:
                data = yaml.safe_load(f)
                scan_filters = data.get("filter", [])

        logger.info(f"Sync this folder: {folder.path}")

        if sync_this_folder:
            sync_folder(fs_source, folder, fs_dest, destfolder, objdfolder,
                        sfs_name, sfs_opts, dfs_name, dfs_opts,
                        compareChecksums,
                        cslist,
                        metadata,
                        copy_procs,
                        excludelist,
                        compare,
                        minimum_age,
                        cs_filters,
                        scan_filters,
                        scan)
            # SYNC might take a long time:
            # so refresh the connections
            fs_source.refresh()
            fs_dest.refresh()


def replicate_single_folder(sfs_name, sfs_opts, dfs_name, dfs_opts,
                            sourcepath, destpath,
                            compareChecksums=True, checksumfile='', checksumfileformat='', checksumfileschema='',
                            metadata={},
                            copy_procs=1,
                            excludelist=[],
                            completion_avu=None,
                            mark_complete=False,
                            compare=True,
                            timestamp_list=[],
                            minimum_age=None,
                            scan=False,
                            cs_filter_file='',
                            scan_filter_file=''):

    fs_source = factory.createfs(sfs_name, **sfs_opts)
    fs_dest = factory.createfs('irods', **dfs_opts)
    folder = fs_source.getfolder(sourcepath)
    destfolder = destpath
    objdfolder = None
    try:
        objdfolder = fs_dest.getfolder(destfolder)
    except ex.CollectionDoesNotExist:
        objdfolder = fs_dest.mkdir(destfolder)

    if completion_avu:
        if test_completion_avu(objdfolder, completion_avu):
            logger.debug(
                'Import for folder %s already marked complete' % sourcepath)
            return

    if checksumfileformat in [FILE_FORMAT_BASECLEAR, FILE_FORMAT_GENERIC_JSON]:
        with open(checksumfileschema) as f:
            JSON_SCHEMA = json.load(f)
    else:
        JSON_SCHEMA = None

    cslist = {}
    if checksumfile:
        cslist = parse_checksum_file(
            fs_source, folder, checksumfile, checksumfileformat, JSON_SCHEMA)
        if not cslist:
            logger.error('Given checksum file is empty')
            sys.exit(0)

    cs_filters = []
    if cs_filter_file:
        with open(cs_filter_file, 'r') as f:
            data = yaml.safe_load(f)
            cs_filters = data.get("filter", [])

    scan_filters = []
    if scan_filter_file:
        with open(scan_filter_file, 'r') as f:
            data = yaml.safe_load(f)
            scan_filters = data.get("filter", [])
    success = sync_folder(fs_source, folder, fs_dest, destfolder, objdfolder,
                          sfs_name, sfs_opts,
                          'irods', dfs_opts,
                          compareChecksums,
                          cslist,
                          metadata,
                          copy_procs,
                          excludelist,
                          compare,
                          minimum_age,
                          cs_filters,
                          scan_filters,
                          scan)
    if success:
        sys.exit(0)
    sys.exit(1)


def loglevel_convert(level):
    """Convert levels 1..5 to logging constants
    """
    LEVELS = dict(enumerate(
        [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]))
    return LEVELS.get(min(max(1, level), len(LEVELS)) - 1, logging.WARNING)


def main():
    """
    Main function shows usage
    options used: -A -a -C -c -cf -cs -d -F -f -g -G -i -k -l -m -n -O -o -P -p -q -R -S -s -T -t -X -x -z
    """

    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument('-l', '--listfs', required=False,
                     action='store_true', default=False)
    args_pre = pre.parse_known_args()

    if args_pre[0].listfs:
        factory.listfs()
        exit(0)

    parser = argparse.ArgumentParser(description='Data synchronisation between iRODS and '
                                     'other file protocols.')

    parser.add_argument('source_path', help='Source path', type=str)
    parser.add_argument('coll', help='destination collection', type=str)

    # Source options
    parser.add_argument('-s', '--source_fs',
                        help='Source filesystem', default='local')
    parser.add_argument('-o', '--source_options', help='Source options')

    # Destination options
    parser.add_argument('-d', '--irods_options', help='iRods options')
    parser.add_argument('-R', '--resource',
                        help='Destination resource', default='')
    parser.add_argument('-S', '--ssl', help='Use SSL', action="store_true")

    # Source selection
    parser.add_argument('--search', help='Search for directories under this base path',
                        dest='search_directory', default=None)
    parser.add_argument('-n', '--skip_subdirs',
                        help='Skip this number of subdirectories while searching for source directories', type=int, default=0)
    parser.add_argument('-P', '--folder_pattern',
                        help='Pattern to match foldername', default='')
    parser.add_argument('-f', '--flag_filename',
                        help='Flag filename', default='')
    parser.add_argument('-g', '--flag_age',
                        help='Flag filename min age', type=int, default=0)
    parser.add_argument('-c', '--checksum_file',
                        help='Checksum file. Wildcards are allowed.', default='')
    parser.add_argument('-cf', '--checksum_file_format', help='Checksum file format ("%s"/"%s"/"%s")' %
                        (FILE_FORMAT_TEXT, FILE_FORMAT_BASECLEAR, FILE_FORMAT_GENERIC_JSON), default=FILE_FORMAT_TEXT)
    parser.add_argument('-cs', '--checksum_file_schema',
                        help='file containing JSONSCHEMA definition of checksum file format.', default=GENERIC_JSON_SCHEMA_FILE)

    # include the --filter_file alias for backward compatibility
    parser.add_argument('--checksum_filter_file', '--filter_file',
                        help='A yaml-file containing filter rules to include/exclude files/directories in the checksum_file', default='')
    parser.add_argument(
        '--scan', help='Scan (walk) source dir to find files to copy. This defaults to true if -c is not supplied', action='store_true')
    parser.add_argument(
        '--scan_filter_file', help='A yaml-file containing filter rules to include/exclude files/directories found by scanning the source', default='')
    parser.add_argument(
        '-a', '--minage', help='Minimum folder age in seconds', type=int, default=0)
    parser.add_argument(
        '-A', '--maxage', help='Maximum folder age in seconds', type=int, default=999999999)
    parser.add_argument('-X', '--exclude', help='Relative file/dir pattern to exclude',
                        type=str, action="append", default=[])
    parser.add_argument('-T', '--timestamp_age',
                        help='Supply attr=age. Checks for a timestamp attr on dest coll, that is min age old', default=[], action="append")
    parser.add_argument(
        '-w', '--last_write', help='Seconds since last writing access to file (in seconds).', type=int, default=0)

    # Metadata options
    parser.add_argument(
        '-m', '--metadata', help='Metadata to add to destination collection', default=[], action='append')
    parser.add_argument('-O', '--completion_avu',
                        help='Metadata attr=value to check for to skip folders', default=None)

    # Copy options
    parser.add_argument('-x', '--verify_checksums',
                        help='Verify checksums after copy', action="store_true")
    parser.add_argument(
        '-z', '--no_compare', help='Do not compare existing objects by size/date/checksum', action="store_true")
    parser.add_argument('-t', '--copy_procs',
                        help='Number of copy processes', type=int, default=1)

    # Logging options
    parser.add_argument('--data_source_name',
                        help='Name of data source', default='intorods')
    parser.add_argument('--debuglevel', help='Debuglevel (1..5)',
                        type=int, default=4)
    parser.add_argument('--syslog', help='Log to syslog', action='store_true')

    args = parser.parse_args()

    assert args.source_path or args.search_directory, "Source path is required"
    assert args.coll, "Destination collection is required"

    loglevel = loglevel_convert(args.debuglevel)

    log_to_stdout(logger, args.data_source_name, loglevel)
    if args.syslog:
        log_to_syslog(logger, args.data_source_name, loglevel)

    logger.debug('{} startup for data source "{}".'.format(
        __name__, args.data_source_name))

    source_options = parse_extra_options(args.source_options)
    metadata = dict(m.split('=') for m in args.metadata)

    dest_options = parse_extra_options(args.irods_options)
    dest_options.update({'resource': args.resource, 'use_ssl': args.ssl})

    timestamp_list = {opt.split('=')[0]: opt.split('=')[1]
                      for opt in args.timestamp_age}

    # Using scan defaults to True if no filelist is specified.
    # This ensures backward compatibility
    scan = True if not args.checksum_file else args.scan

    if args.search_directory:
        replicate_data_folder(args.source_fs, source_options, 'irods', dest_options,
                              args.search_directory, args.coll,
                              compareChecksums=args.verify_checksums,
                              minage=args.minage, maxage=args.maxage,
                              flagfile=args.flag_filename,
                              flag_age=args.flag_age,
                              checksumfile=args.checksum_file,
                              checksumfileformat=args.checksum_file_format,
                              checksumfileschema=args.checksum_file_schema,
                              pattern=args.folder_pattern,
                              metadata=metadata,
                              skip_subdirs=args.skip_subdirs,
                              copy_procs=args.copy_procs,
                              excludelist=args.exclude,
                              completion_avu=args.completion_avu,
                              compare=not args.no_compare,
                              info=args.info,
                              timestamp_list=timestamp_list,
                              minimum_age=args.last_write,
                              cs_filter_file=args.checksum_filter_file,
                              scan=scan,
                              scan_filter_file=args.scan_filter_file
                              )
    else:
        if args.coll[-1] == '/':
            destination_coll = os.path.join(
                args.coll, os.path.basename(args.source_path))
        else:
            destination_coll = args.coll
        replicate_single_folder(args.source_fs, source_options, 'irods', dest_options,
                                args.source_path, destination_coll,
                                compareChecksums=args.verify_checksums,
                                checksumfile=args.checksum_file,
                                checksumfileformat=args.checksum_file_format,
                                checksumfileschema=args.checksum_file_schema,
                                metadata=metadata,
                                copy_procs=args.copy_procs,
                                excludelist=args.exclude,
                                completion_avu=args.completion_avu,
                                compare=not args.no_compare,
                                minimum_age=args.last_write,
                                scan_filter_file=args.scan_filter_file,
                                cs_filter_file=args.checksum_filter_file,
                                scan=scan
                                )


if __name__ == "__main__":
    main()
