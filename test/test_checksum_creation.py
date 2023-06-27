import mock
import json
import os
import unittest
import shutil
import argparse

from intorods.uxhash.hash import create_hash, hash_dict_to_txt, hash_dict_to_json
from intorods.uxhash.hash import main as hash_main

TEST_OUTPUT_FOLDER = "./test/output_for_tests/"
TEST_INPUT_FOLDER = "./test/input/"


class TestCreateChecksumFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_FOLDER)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_OUTPUT_FOLDER)

    def test_create_hash(self):
        """
        Test the creation of the hashes.
        """
        result = create_hash(TEST_INPUT_FOLDER)
        self.assertEqual(
            result["file1"],
            "9ee1e60c4cf9c254453b240c04a3c563380ff503485a620c55659cdb40aae43c",
        )
        self.assertEqual(
            result["file2"],
            "0f218d4f5147fec04ca763fa4a58e8288b070951e6aa462c691d52bb90671dd9",
        )

    def test_hash_dict_to_txt(self):
        hashdict = {
            "file1": "123123123123",
            "file2": "456456456456",
        }
        result = hash_dict_to_txt(hashdict)
        expected = [
            "123123123123  file1\n456456456456  file2\n",
            "456456456456  file2\n123123123123  file1\n",
        ]
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
                {"path": "file2", "checksum": "456456456456", "type": "dataobject"},
                {"path": "file1", "checksum": "123123123123", "type": "dataobject"},
            ],
        }
        self.assertCountEqual(result_json["objects"], expected["objects"])

    @mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            sourcedir=TEST_INPUT_FOLDER,
            output=os.path.join(TEST_OUTPUT_FOLDER, "output_file.json"),
            debuglevel=1,
            procs=1,
            json=True,
            coll="",
        ),
    )
    def test_main(self, mockargs):
        hash_main()
        self.assertTrue(os.path.join(TEST_OUTPUT_FOLDER, "output_file.json"))


if __name__ == "__main__":
    unittest.main()
