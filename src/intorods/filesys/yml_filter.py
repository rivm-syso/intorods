import json
import os
import re


# returns number of non-empty path components
def path_length( path ):
    # '/' = 0
    # '/A/' = 1
    parts = path.split(os.sep)
    l=0
    for p in parts:
        if p:
            l += 1
    return l

class PathFilter:

    def __init__(self, filter):
        def addFilterDef( filter ):
            parts = filter.split(' ')
            if len( parts ) not in [2,3]:
                raise f"ERROR: invalid filter: '{filter}'"
            include = parts[0] == '+'
            if os.path.basename( parts[1] ):
                raise f"ERROR: invalid filter: '{parts}'. All filter must end in '/'"
            fpath = os.path.normpath( os.path.dirname( parts[1] ))
            #its a dir filter
            if len( parts ) == 2:
                entry = (include, fpath)
                self._dir_filter.append( entry )
                return
            #its a file filter
            regex = re.compile(parts[2], re.IGNORECASE) 
            entry = (include, fpath, regex)
            if include:
                self._file_filter_include.setdefault( fpath, [] ).append( entry )
            else:
                self._file_filter_exclude.setdefault( fpath, [] ).append( entry )

        #filter rules from yml-file...
        #...regarding directories
        self._dir_filter = []
        #...regarding files
        self._file_filter_include = {}
        self._file_filter_exclude = {}

        for f in filter:
            addFilterDef(f)

    def show( self ):
        print("Filter:")
        for f in self._dir_filter:
            print(f)
        for k in self._file_filter_include.items():
            print(k)
            print(f)
        for k,f in self._file_filter_exclude.items():
            print(k)
            print(f)
        print("------")

    def is_a_subpath( self, cand, path):
        score = None    
        ncand = os.path.normpath( cand )
        if ncand == path:
            #its perfect match
            score = 0
        elif ncand.startswith( '{}/'.format(path) ):
            #its a subpath!
            score = path_length( ncand ) - path_length(path)
        elif path == "/":
            #by default everything is decended of /
            score = path_length( ncand )
        return score


    def get_nearest_directory_filter( self, path ):
        scores = []
        for entry in self._dir_filter:
            include = entry[0]
            score = self.is_a_subpath( path, entry[1])
            if score != None:
                scores.append( (score, entry) )
        #find the rule with highest score:
        if not scores:
            return None
        min_score = min( scores, key=lambda score: score[0])
        return min_score[1]


    # /path/to/directory
    def isDirIncluded( self, path ):
        entry = self.get_nearest_directory_filter( path )
        include=True
        if entry:
            include = entry[0]
        return include

    # /path/to/filename.txt
    def isFileIncluded( self, path_and_file ):
        ncand = os.path.normpath( path_and_file )
        path, filename = os.path.split( path_and_file )
        if not path:
            path = os.sep
        if not filename:
            print( "WARN: path '{path_and_file}' doesn't contain a filename" )
            return False
        
        inFilter = self._file_filter_include.get( path, [] )
        exFilter = self._file_filter_exclude.get( path, [] )

        #if there is any inclusion filter, then by default all files are excluded...
        includeFile = self.isDirIncluded( path )
        matches = 0
        for entry in inFilter:
            if entry[2].match(filename):
                matches += 1
                #print(entry)
                includeFile = True
        for entry in exFilter:
            if entry[2].match(filename):
                matches += 1
                #print(entry)
                includeFile = False
        if matches > 1:
            print( f"WARN: multiple matches for path: '{path_and_file}'")
        return includeFile

