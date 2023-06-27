import inspect
import json
import os
import sys
import unittest

sys.path.insert(1, os.path.join(sys.path[0], ".."))

from intorods.intorods import (BASECLEAR_SCHEMA_FILE, FILE_FORMAT_BASECLEAR,
                               FILE_FORMAT_TEXT, factory, parse_checksum_file)


class TestParseChecksumFile(unittest.TestCase):
    def test_simple_text_format(self):
        """
        Test the parsing of the simple text-format
        """
        fs_source = factory.createfs( "local" )
        result = parse_checksum_file( fs_source,
                                      fs_source.getfile("./test/data"),
                                      "text_checksumfile1",
                                      FILE_FORMAT_TEXT, 
                                      None )
        self.assertIsNotNone( result )
        self.assertEqual( result["file1"], "123" )
        self.assertEqual( result["file2"], "456" )


    def test_json_format(self):
        """
        Test the parsing of the json format with default path per file
        """
        fs_source = factory.createfs( "local" )
        JSON_SCHEMA=None
        with open( BASECLEAR_SCHEMA_FILE) as f:
            JSON_SCHEMA = json.load(f)
        result = parse_checksum_file( fs_source,
                                      fs_source.getfile("./test/data"),
                                      "json_checksumfile1.json",
                                      FILE_FORMAT_BASECLEAR, 
                                      JSON_SCHEMA )
        self.assertIsNotNone( result )
        self.assertEqual( result["raw_sequences/4711/file1"], "1231231231123123123112312312311231231231123123123112312312311231" )
        self.assertEqual( result["raw_sequences/4711/file2"], "4564564564456456456445645645644564564564456456456445645645644564" )


    def test_json_format_with_path(self):
        """
        Test the parsing of the json format with explicit path per file
        """
        fs_source = factory.createfs( "local" )
        JSON_SCHEMA=None
        with open( BASECLEAR_SCHEMA_FILE) as f:
            JSON_SCHEMA = json.load(f)
        result = parse_checksum_file( fs_source,
                                      fs_source.getfile("./test/data"),
                                      "json_checksumfile2.json",
                                      FILE_FORMAT_BASECLEAR, 
                                      JSON_SCHEMA )
        self.assertIsNotNone( result )
        self.assertEqual( result["any/kind/of/path/file1"], "1231231231123123123112312312311231231231123123123112312312311231" )
        self.assertEqual( result["another/path/file2"], "4564564564456456456445645645644564564564456456456445645645644564" )


    def test_missing_json_format_file(self):
        """
        Test no exception happens when checksum file is not found
        """
        fs_source = factory.createfs( "local" )
        JSON_SCHEMA=None
        with open( BASECLEAR_SCHEMA_FILE) as f:
            JSON_SCHEMA = json.load(f)
        result = parse_checksum_file( fs_source,
                                      fs_source.getfile("./test/data"),
                                      "json_checksumfile3.json",
                                      FILE_FORMAT_BASECLEAR, 
                                      JSON_SCHEMA )
        self.assertIsNone( result )


    def test_globbing_for_checksum_file(self):
        """
        Test file globbing works and will parse file if a SINGLE file matches!
        """
        fs_source = factory.createfs( "local" )
        JSON_SCHEMA=None
        with open( BASECLEAR_SCHEMA_FILE) as f:
            JSON_SCHEMA = json.load(f)
        result = parse_checksum_file( fs_source,
                                      fs_source.getfile("./test/data"),
                                      "json_*file2.json",
                                      FILE_FORMAT_BASECLEAR, 
                                      JSON_SCHEMA )
        self.assertIsNotNone( result )
if __name__ == '__main__':
    unittest.main()
