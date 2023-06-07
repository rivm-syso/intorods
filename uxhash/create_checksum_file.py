#!/usr/bin/env python3

"""

"""

import argparse
import json
#from jsonschema import validate, ValidationError
import sys


def readHashesAndFilesFromStdin():
    hashesAndFiles = []
    for line in sys.stdin:
        # sys.stdout.write(line)
        hf = line.split(None, 1)
        hashesAndFiles.append((hf[0].strip(), hf[1].strip()))
    return hashesAndFiles


def writeFile(outputFile, collection, hashesAndFiles):
    objects = []
    for hash_file in hashesAndFiles:
        hash = hash_file[0]
        path = hash_file[1]
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
    out_file = open(outputFile, "w")
    json.dump(result_json, out_file, indent=3)
    out_file.close()
    return True


def main():
    """
    Main function shows usage
    """
    parser = argparse.ArgumentParser(
        description='create a valid checksumfile in JSON format')
    parser.add_argument(
        '-C', '--coll', help='destination collection', default='')
    parser.add_argument('-f', '--file', help='output file', default='')

    args = parser.parse_args()

    hashesAndFiles = readHashesAndFilesFromStdin()
    writeFile(args.file, args.coll, hashesAndFiles)


if __name__ == "__main__":
    main()
