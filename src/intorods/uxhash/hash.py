#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 11:38:22 2020

@author: Erwin van Wieringen
"""

import argparse
import json
import hashlib
import logging
import logging.config
import os
import sys
import time
from datetime import datetime
from multiprocessing import Pool

BUF_SIZE = 1024 * 1024

log_format = 'hash: %(asctime)s|%(name)s %(levelname)s: %(message)s'

def checksum(fileobject):
    logging.debug(f'Hashing {fileobject[1]}')
    file = fileobject[1]
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return (fileobject[0], sha256.hexdigest())

def checksum2(file):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def create_hash(folder, procs=1):
    logging.debug('Generate hash jobs')
    hashjobs = []

    basedir = os.path.normpath(folder)
    for root, dirs, files in os.walk(basedir):
        reldir = root[len(basedir)+1:]
        for file in files:
            hashjobs.append((os.path.join(reldir, file), os.path.join(root, file)))
    logging.info(f'{len(hashjobs)} files to hash')
    logging.info(f'Start {procs} hash workers')
    pool = Pool(processes=procs)
    hashlist = pool.map(checksum, hashjobs)    
    hashes = { item[0]: item[1] for item in hashlist}
    logging.info('Hashing finished')        
    return hashes

def loglevel_convert(level):
    """Convert levels 1..5 to logging constants
    """
    LEVELS = dict(enumerate([logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]))
    return LEVELS.get(level-1, logging.WARNING)

def hash_dict_to_json(hashdict, collection=""):
    objects = []
    for path, hash in hashdict.items():
        file_json = {
            "path": path,
            "checksum": hash,
            "type": "dataobject"
        }
        objects.append(file_json)

    result_json = {
        "collection": collection,
        "checksum_format": "sha256",
        "version": 1,
        "checksum_encoding": "hex",
        "objects": objects
    }
    return json.dumps(result_json, indent=3)

def hash_dict_to_txt(hashdict):
    output = ""
    for path, hash in hashdict.items():
        output += "{}  {}\n".format(hash, path)
    return output

def cmd_parser():
    parser = argparse.ArgumentParser(description='Hash file generator')
    parser.add_argument('sourcedir', help='Source directory')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-j', '--json', help='Output in json format', action='store_true')
    parser.add_argument('-p', '--procs', help='Hash processes', type=int, default=1)
    parser.add_argument('-d', '--debuglevel', help='Debug level (1-5)', type=int, default=logging.CRITICAL)
    parser.add_argument('-C', '--coll', help='destination collection for use in json output', default='')

    return parser.parse_args()

def main():
    """
    Main function shows usage
    """

    args = cmd_parser()

    logging.basicConfig(format=log_format, level=loglevel_convert(args.debuglevel))

    t0 = time.time()

    hashes = create_hash(args.sourcedir, procs=args.procs)

    if args.output is not None:
        hashes.pop(args.output, None)
    
    hashtime = time.time() - t0

    
    output = ""
    if args.json:
        output = hash_dict_to_json(hashes, collection=args.coll)
    else:
        output = hash_dict_to_txt(hashes)

    if args.output:
        hashfile = open(args.output, 'w')
    else:
        hashfile = sys.stdout
    hashfile.write(output)
    hashfile.close

    logging.info(f'Hashed {len(hashes)} files in {hashtime:.2f} seconds')

if __name__ == "__main__":
    main()
    