import inspect
import json
import os
import sys
import unittest

from intorods.uxhash.hash import *

class TestCreateChecksumFile(unittest.TestCase):
    def test_create_hash(self):
        """
        Test the creation of the hashes.
        """
        result = create_hash("./test/input/")
        self.assertEqual(result["file1"], "9ee1e60c4cf9c254453b240c04a3c563380ff503485a620c55659cdb40aae43c")
        self.assertEqual(result["file2"], "0f218d4f5147fec04ca763fa4a58e8288b070951e6aa462c691d52bb90671dd9")

    def test_hash_dict_to_txt(self):
        hashdict = {
            "file1": "123123123123",
            "file2": "456456456456",
        }
        result = hash_dict_to_txt(hashdict)
        expected = ["123123123123  file1\n456456456456  file2\n", "456456456456  file2\n123123123123  file1\n"]
        self.assertIn(result, expected)

    def test_hash_dict_to_json(self):
        hashdict = {
            "file1": "123123123123",
            "file2": "456456456456",
        }
        result = hash_dict_to_json(hashdict)
        result_json = json.loads(result)
        expected = {
            "collection": "",
            "checksum_format": "sha256",
            "version": 1,
            "checksum_encoding": "hex",
            "objects": [
                {
                    "path": "file2",
                    "checksum": "456456456456",
                    "type": "dataobject"
                },
                {
                    "path": "file1",
                    "checksum": "123123123123",
                    "type": "dataobject"
                }
            ]
        }
        print(result_json)
        print(expected)
        self.assertCountEqual(result_json["objects"], expected["objects"])



if __name__ == '__main__':
    unittest.main()
