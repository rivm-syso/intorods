import logging
import math
import multiprocessing as mp
import os
import queue
import re
import time

from intorods.filesys.fs_base import factory
from intorods.filesys.yml_filter import PathFilter

# The sync_worker tries to copy each object max MAX_RETRIES times,
# if comparison fails. After that, the object is added to the error_queue,
# and sync_worker continues with the next object
MAX_RETRIES = 2
# After trying to copy all objects, copying is retried (again) for objects in the
# error queue. This happens at most MAX_ERRQUEUE_RETRIES times
MAX_ERRQUEUE_RETRIES = 2
# MONITOR_INTERVAL determines the frequency at which stats are reported
# and at which the state of worker processes is checked
MONITOR_INTERVAL = 5
# The worker process terminates after MAX_OBJECTS_PER_PROCESS. This
# prevents nemory exhaust on the irods server. The monitor process will
# automatically start a new sync worker if there are still objects to copy
# in the queue
MAX_OBJECTS_PER_PROCESS = 2000

logger = logging.getLogger(__name__)


def sync_worker(process_id, q, sq, error_queue, sfs_name, sfs_opts, dfs_name, dfs_opts, compare, minimum_age):
    """The sync worker syncs items from the queue q
    sfs_name, sfs_opts, dfs_name and dfs_opts contain the source and destination
    filesystem name and connect parameters.
    Items that fail to copy/sync are added to the error queue.
    On succesfull sync, the size of the synced object is added to the 
    statistics queue sq
    """

    def copyobj(entry, dfs, dfile):
        try:
            entry.copyto(dfs, dfile)
            dfs.getfile(dfile).set_mtime(entry.utc_mtime())
        except Exception as ex:
            logger.error('T{}: ERROR COPYING {}. Exception code: {}'.format(
                process_id, entry.path, ex.code if hasattr(ex, "code") else "None"))
            return False
        return True

    source_fs = factory.createfs(sfs_name, **sfs_opts)
    destfs = factory.createfs(dfs_name, **dfs_opts)
    objects_copied = 0
    # Start the copy loop
    while objects_copied < MAX_OBJECTS_PER_PROCESS:
        try:
            # Fetch an item to copy from the queue
            item = q.get(True, 2)
        except queue.Empty:
            logger.debug('T{}: Empty queue: exit'.format(process_id))
            break
        if item is None:
            logger.debug('T{}: Empty queue item: exit'.format(process_id))
            break
        sourcefile, destfile, compareChecksums, checksum = item

        # Get source file object
        try:
            entry = source_fs.getfile(sourcefile)
            if minimum_age:
                now = math.floor(time.time())
                if entry.utc_mtime() >= (now - minimum_age):
                    logger.debug('T{}: File {} is omitted since it was modified shortly.'.format(
                        process_id, sourcefile))
                    break
        except:
            logger.debug('T{}: Error getting source file {}.'.format(
                process_id, sourcefile))
            error_queue.put(item)
            continue

        # Assign checksum from checksum file
        if checksum:
            entry.checksum = checksum

        # Try copying the object MAX_RETRIES times
        retry_counter = 0
        equal = False
        while retry_counter < MAX_RETRIES:
            # Check for existing destination and continue if equal
            try:
                dest_exists = destfs.fileexists(destfile)
            except:
                logger.error('T{}: error querying dest filesystem for {}'.format(
                    process_id, destfile))
                break
            if dest_exists:
                if compare:
                    try:
                        dfile = destfs.getfile(destfile)
                    except:
                        logger.error('T{}: error getting destfile object {}'.format(
                            process_id, destfile))
                        break
                    try:
                        equal = entry.compareto(
                            dfile, compareChecksums=compareChecksums)
                    except Exception as ex:
                        logger.error('T{}: error comparing {} to {}. Exception: {}'.format(
                            process_id, entry.path, destfile, ex))
                        equal = False
                else:
                    # No file comparison required, existence of dest object is enough
                    equal = True

                if equal:
                    sq.put(entry.filesize())
                    break
                else:
                    logger.debug('T{}: objects {} and {} are not equal'.format(
                        process_id, entry.path, destfile))
                    try:
                        destfs.deletefile(destfile)
                    except:
                        logger.error('T{}: error deleting {}'.format(
                            process_id, destfile))

            # Here the actual copy is done.
            # objects_copied is only used to terminate the thread after a certain number of copy actions
            objects_copied += 1
            if not copyobj(entry, destfs, destfile):
                logger.error('T{}: copying {} failed'.format(
                    process_id, entry.path))

            retry_counter += 1

        if not equal:
            logger.error('T{}: copying of {} to {} failed'.format(
                process_id, entry.path, destfile))
            # This is a potential deadlock in case of lots of errors
            # https://stackoverflow.com/questions/59951832/python-multiprocessing-queue-makes-code-hang-with-large-data
            error_queue.put(item)

    # Destroy FS objects
    source_fs.cleanup()
    destfs.cleanup()

    logger.debug('T{}: Finish'.format(process_id))


def sync(sourcefs, sourcepath, destfs, destpath, sfs_name, sfs_opts, dfs_name, dfs_opts,
         compareChecksums=False, filelist={}, scan=False, worker_processes=1, excludelist=[],
         compare=True, minimum_age=0, cs_filters=[], scan_filters=[]):
    # Initialize MP
    job_queue = mp.Queue()
    error_queue = mp.Queue()
    stats_queue = mp.Queue()

    # Create copy processes list
    procs = []

    def new_copy_process(i):
        logger.debug('Creating copy process {}'.format(i))
        p = mp.Process(target=sync_worker, args=(i, job_queue, stats_queue, error_queue,
                                                 sfs_name, sfs_opts, dfs_name, dfs_opts,
                                                 compare, minimum_age))
        p.start()
        return p

    def handle_statistics(ts_start, total_bytes_copied, total_files_copied):
        ts_now = time.time()
        while stats_queue.qsize() > 0:
            bytes_copied = stats_queue.get()
            total_files_copied += 1
            total_bytes_copied += bytes_copied
        byterate = total_bytes_copied/(ts_now-ts_start)
        filerate = total_files_copied/(ts_now-ts_start)
        timeleft = qsize/filerate if filerate > 0 else 0
        avg_size = total_bytes_copied/total_files_copied if total_files_copied > 0 else 0
        logger.info('QUEUE SIZE : {:6d} COPYRATE: {:4.0f}  BYTERATE: {:5.2f} MB/s  AVG SIZE : {:8.2f} kB  TIME: {:.2f} s  ERRORS : {:6d}'.format(
            qsize, filerate, byterate/(1024*1024), avg_size/1024, timeleft, error_queue.qsize()))
        return total_bytes_copied, total_files_copied

    if not destfs.folderexists(destpath):
        destfs.mkdir(destpath)

    ts_start = time.time()

    # Enqueue files to copy
    # copy_jobs is a dict with struct { src_filename : (src_filename, dst_filename, cmp_checksum, checksum_value) }
    # this ensures all source file will be present only once
    copy_jobs = {}

    # Start with scanning the source. since here no cs value will be included
    if scan:
        logger.debug('Queue copy jobs from source fs')
        spf = PathFilter(scan_filters)
        try:
            queue_copyjobs(sourcefs, sourcepath, destfs, destpath, copy_jobs,
                           compareChecksums=compareChecksums, excludelist=excludelist, filter=spf)
        except Exception as ex:
            logger.error(f'ERROR queueing jobs for {sourcepath}: {ex}')
            return False

    if filelist:
        logger.debug('Queue copy jobs from filelist')
        cpf = PathFilter(cs_filters)
        try:
            queue_copyjobs_from_filelist(filelist, sourcepath, destfs, destpath, copy_jobs,
                                         compareChecksums=compareChecksums, excludelist=excludelist, filter=cpf)
        except Exception as ex:
            logger.debug(f'ERROR queueing jobs for {sourcepath}: {ex}')
            return False

    total_files = len(copy_jobs)

    for job in copy_jobs.values():
        job_queue.put(job)

    qsize = job_queue.qsize()
    total_bytes_copied = 0
    total_files_copied = 0

    error_retries = 0
    process_id = 0
    while error_retries < MAX_ERRQUEUE_RETRIES:
        while qsize > 0:
            # Show/handle statistics
            total_bytes_copied, total_files_copied = handle_statistics(
                ts_start, total_bytes_copied, total_files_copied)

            # Handle finished processes
            for p in procs:
                if not p.is_alive():
                    logger.debug('A copy process has ended')
                    p.join()
                    procs.remove(p)
            # Create copy processes if necessary
            desired_processes = min([qsize, worker_processes])
            while len(procs) < desired_processes:
                procs.append(new_copy_process(process_id))
                process_id += 1
            time.sleep(min(MONITOR_INTERVAL, max(qsize//10, 1)))
            qsize = job_queue.qsize()

        while error_queue.qsize() > 0:
            logger.debug('Re-queing {}'.format('x'))
            job_queue.put(error_queue.get())
        qsize = job_queue.qsize()
        error_retries += 1

    logger.debug('Wait for copy jobs to finish')
    errors = 0
    for t in procs:
        # the other side of the deadlock
        # when we reach this point all error_retries have been triggered, anything left in the error_queue is just needed for reporting
        # however the last run is still ongoing, so we can't just join the children,
        # the current implementation polls for a maximum of 100sec per thread, and makes sure the error_queue is regularly read and emptied.
        while True:
            logger.debug(f"waiting to join {t}")
            t.join(100)
            # after timeout check the error queue to prevent deadlock
            while error_queue.qsize() > 0:
                error_queue.get()
                errors += 1
            if not t.is_alive():
                break

    total_bytes_copied, total_files_copied = handle_statistics(
        ts_start, total_bytes_copied, total_files_copied)

    logger.info('Had {} files to sync, handled {}'.format(
        total_files, total_files_copied))
    logger.info('Files with sync error: {}'.format(errors))
    success = (errors == 0) and (total_files_copied == total_files)

    return success


def queue_copyjobs_from_filelist(filelist, sourcepath, destfs, destpath, copy_jobs,
                                 compareChecksums=True, excludelist=[], filter=None):
    dircache = []
    copy_counter = 0

    exclude_relist = [re.compile(exclude, re.IGNORECASE)
                      for exclude in excludelist]

    for filename in filelist:
        if filter and (not filter.isFileIncluded(filename)):
            continue

        # Skip files that match one of the exclude patterns
        match = False
        for exclude_re in exclude_relist:
            if exclude_re.match(filename):
                match = True
        if match:
            continue
        #
        destfile = os.path.join(destpath, filename)
        destdir = os.path.dirname(destfile)
        # Create the destination directory, if non-existing
        if not destdir in dircache:
            if not destfs.folderexists(destdir):
                destfs.mkdir(destdir)
            dircache.append(destdir)
        # Add files to the copy queue
        src_filename = os.path.join(sourcepath, filename)
        copy_jobs[src_filename] = (src_filename, os.path.join(destpath, filename),
                                   compareChecksums, filelist[filename])
        copy_counter += 1
    return copy_counter


def queue_copyjobs(sourcefs, sourcebase, destfs, destbase, copy_jobs,
                   compareChecksums=False, excludelist=[], relpath='', filter=None):

    #
    # PATH variable example
    #
    #  /data/vir-ont/20201204_N2-MIN83-oke/20201204_1704_X1_FAO64587_bf55c64/fast5_pass/FAO64587_pass_0ad68019_3146.fast5
    # |                                sourcebase                           | relpath  |
    # |                                    sourcepath                                  |
    # |                                                                     |           relfilepath                      |
    #                                      |   parentDir                    |
    #
    #  /demoZone/projects/nsglab/minion/20201204_1704_X1_FAO64587_bf55c64/fast5_pass/FAO64587_pass_0ad68019_3146.fast5
    # |                                 destbase                         | relpath  |
    # |                                                                  |           relfilepath                      |
    # |                                        destdir                              |

    dircache = []
    copy_counter = 0

    exclude_relist = [re.compile(exclude, re.IGNORECASE)
                      for exclude in excludelist]

    sourcepath = os.path.join(sourcebase, relpath)

    # I guess only intorods knows what the base directory was sync is called for.
    #parentdir = sourcebase.split(os.sep)[-1]

    for entry in sourcefs.lsdirnames(sourcepath):
        relsubdir = os.path.join(relpath, entry)
        copy_counter += queue_copyjobs(sourcefs, sourcebase, destfs, destbase, copy_jobs,
                                       compareChecksums=compareChecksums, excludelist=excludelist, relpath=relsubdir, filter=filter)

    for entry in sourcefs.lsfilenames(sourcepath):

        relfilepath = os.path.join(relpath, entry)
        # Skip files that match one of the exclude patterns
        if filter and (not filter.isFileIncluded(relfilepath)):
            continue
        match = False
        for exclude_re in exclude_relist:
            if exclude_re.match(relfilepath):
                match = True
        if match:
            continue

        destdir = os.path.join(destbase, relpath).rstrip('/')
        if not destdir in dircache:
            if not destfs.folderexists(destdir):
                destfs.mkdir(destdir, parents=True)
            dircache.append(destdir)

        src_filename = os.path.join(sourcebase, relfilepath)
        copy_jobs[src_filename] = (src_filename, os.path.join(
            destbase, relfilepath), compareChecksums, None)
        copy_counter += 1

    return copy_counter
