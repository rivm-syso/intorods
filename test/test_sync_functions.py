import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))

import filecmp

from intorods.intorods import factory, sync

#
# def sync(sourcefs, sourcepath, destfs, destpath, sfs_name, sfs_opts, dfs_name, dfs_opts,
#         compareChecksums=False, filelist={}, scan=False, worker_processes=1, excludelist=[], 
#         compare=True, minimum_age=0, cs_filters=[], scan_filters=[]):
# 

inputpath = './test/input'


def test_sync_list():
    outputpath = './test/output1'
    fs_source = factory.createfs( 'local' )
    fs_dest = factory.createfs('local')
    if not fs_dest.folderexists(outputpath):
        fs_dest.mkdir(outputpath)
    LIST = { 
        'file1' : '9ee1e60c4cf9c254453b240c04a3c563380ff503485a620c55659cdb40aae43c', 
        'file2': '0f218d4f5147fec04ca763fa4a58e8288b070951e6aa462c691d52bb90671dd9' 
    }
    result = sync(fs_source, inputpath,
            fs_dest, outputpath,
            'local', {}, 
            'local', {},
            compareChecksums=True,
            filelist=LIST, scan=False,
            worker_processes=1, excludelist=[],
            compare=True,
            minimum_age=0, cs_filters=[],
            scan_filters=[]) 
    assert result == True
    assert filecmp.cmp(os.path.join(inputpath, 'file1'), os.path.join(outputpath, 'file1'), shallow=False) == True
    assert filecmp.cmp(os.path.join(inputpath, 'file2'), os.path.join(outputpath, 'file2'), shallow=False) == True

def test_sync_scan():
    outputpath = './test/output2'
    fs_source = factory.createfs( 'local' )
    fs_dest = factory.createfs('local')
    if not fs_dest.folderexists(outputpath):
        fs_dest.mkdir(outputpath)
    result = sync(fs_source, inputpath,
            fs_dest, outputpath,
            'local', {}, 
            'local', {},
            compareChecksums=True,
            scan=True,
            worker_processes=1, excludelist=[],
            compare=True,
            minimum_age=0, cs_filters=[],
            scan_filters=[]) 
    assert result == True
    assert filecmp.cmp(os.path.join(inputpath, 'file1'), os.path.join(outputpath, 'file1'), shallow=False) == True
    assert filecmp.cmp(os.path.join(inputpath, 'file2'), os.path.join(outputpath, 'file2'), shallow=False) == True




