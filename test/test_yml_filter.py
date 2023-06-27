import unittest

from intorods.filesys.yml_filter import PathFilter


class TestYmlFilter(unittest.TestCase):

    def test_no_filter(self):
        filter = []
        pf = PathFilter( filter )
        f = pf.isFileIncluded( "path/to/file.txt")
        self.assertEqual( f, True, "")
        d = pf.isDirIncluded( "path/to/somewhere" )
        self.assertEqual( d, True, "")

    def test_all_excluded(self):
        filter = [ "- /"]
        pf = PathFilter( filter )
        pf.show()
        f = pf.isFileIncluded( "path/to/file.txt")
        self.assertEqual( f, False, "")
        d = pf.isDirIncluded( "path/to/somewhere" )
        self.assertEqual( d, False, "")

    def test_all_included(self):
        filter = [ "+ /"]
        pf = PathFilter( filter )
        pf.show()
        f = pf.isFileIncluded( "path/to/file.txt")
        self.assertEqual( f, True, "")
        f = pf.isFileIncluded( "file.txt")
        self.assertEqual( f, True, "")
        d = pf.isDirIncluded( "path/to/somewhere" )
        self.assertEqual( d, True, "")

    def test_exclude_dirs(self):
        filter = [ "+ /", "- path/to/"]
        pf = PathFilter( filter )
        pf.show()
        f = pf.isFileIncluded( "path/to/file.txt")
        self.assertEqual( f, False, "")
        d = pf.isDirIncluded( "path/to/somewhere" )
        self.assertEqual( d, False, "")

    def test_include_dirs(self):
        filter = [ "- /", "+ A/B/" ]
        pf = PathFilter( filter )
        pf.show()
        d = pf.isDirIncluded("A/B")
        self.assertEqual(d, True, "")
        d = pf.isDirIncluded("A/B/C")
        self.assertEqual(d, True, "")


    def test_exclude_dirs_include_files(self):
            filter = [ "- /", 
                    "+ A/A2/A3/ .*\.in",
                    "- A/A2/A3/ .*\.ex",
                    "+ B/", 
                    "- B/B2/"]
            pf = PathFilter( filter )
            pf.show()
            f = pf.isFileIncluded( "file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "A/file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "A/A2/file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "A/A2/A3/file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "A/A2/A3/file.in")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "A/A2/A3/file.ex")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "B/file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "B/X/file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "BV/A/file.txt")
            self.assertEqual( f, False, "")


    def test_exclude_dirs_include_files_opposite(self):
            filter = [ "+ /", 
                    "- A/A2/A3/ .*\.in",
                    "+ A/A2/A3/ .*\.ex",
                    "- B/", 
                    "+ B/B2/"]
            pf = PathFilter( filter )
            pf.show()
            f = pf.isFileIncluded( "file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "A/file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "A/A2/file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "A/A2/A3/file.txt")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "A/A2/A3/file.in")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "A/A2/A3/file.ex")
            self.assertEqual( f, True, "")
            f = pf.isFileIncluded( "B/file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "B/X/file.txt")
            self.assertEqual( f, False, "")
            f = pf.isFileIncluded( "B/B2A/file.txt")
            self.assertEqual( f, False, "")

    def test_excl_dir_incl_file(self):
        filter = [ "- /", 
                   "- A/A2/A3/",
                    "+ A/A2/A3/ .*\.in"
                    ]
        pf = PathFilter( filter )
        pf.show()
        f = pf.isFileIncluded( "A/A2/A3/file.txt")
        self.assertEqual( f, False, "")
        f = pf.isFileIncluded( "A/A2/A3/file.in")
        self.assertEqual( f, True, "")
        
    def test_root_files(self):
        filter = [] # TODO fill in the correct filter for this test
        pf = PathFilter( filter )
        pf.show()
        # f = pf.isFileIncluded( "file.txt")
        # self.assertEqual( f, False, "")
        # f = pf.isFileIncluded( "file.in")
        # self.assertEqual( f, True, "")

    def test_absolute_paths(self):
        filter = [ "- /", 
                   "+ /A/"
                 ]
        pf = PathFilter( filter )
        pf.show()
        f = pf.isFileIncluded( "A/file.txt")
        self.assertEqual( f, False, "")
        f = pf.isFileIncluded( "/A/file.in")
        self.assertEqual( f, True, "")

    def test_base_calls(self):
        filter = [ "+ /",
            "- Data/Intensities/BaseCalls/",
            "+ Data/Intensities/BaseCalls/ .*" ]
        pf = PathFilter( filter )
        pf.show()
        d = pf.isDirIncluded( "Data/Intensities/BaseCalls/SubDir")
        self.assertEqual( d, False, "")
        d = pf.isDirIncluded( "Data/Intensities/BaseCalls/Phasing")
        self.assertEqual( d, False, "")
        f = pf.isFileIncluded( "Data/Intensities/BaseCalls/Phasing/test.txt")
        self.assertEqual( f, False, "")
        d = pf.isDirIncluded( "Data/Intensities/BaseCalls/Alignment")
        self.assertEqual( d, False, "")
        f = pf.isFileIncluded( "Data/Intensities/BaseCalls/Alignment/test.txt")
        self.assertEqual( f, False, "")
        f = pf.isFileIncluded( "Data/Intensities/BaseCalls/11_S11_L001_R1_001.fastq.gz")
        self.assertEqual( f, True, "")
        f = pf.isFileIncluded( "Data/Intensities/BaseCalls/12_S12_L001_R1_001.fastq.gz")
        self.assertEqual( f, True, "")

if __name__ == '__main__':
    unittest.main()
