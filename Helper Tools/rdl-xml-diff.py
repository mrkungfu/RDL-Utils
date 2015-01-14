import re
import linecache
import os
import os.path as path
import sys #for main only

DEBUG = False


def smartdiff(filenameA, filenameB):
    linecache.clearcache()
    linenuminA = linenuminB = 1
    diff = False
    while True:
        while ignoreline( linecache.getline(filenameA, linenuminA) ): #skip ignored lines
            linenuminA += 1
        while ignoreline( linecache.getline(filenameB, linenuminB) ): #skip ignored lines
            linenuminB += 1
        #
        lineinA = linecache.getline(filenameA, linenuminA)
        lineinB = linecache.getline(filenameB, linenuminB)
        if lineinA is '' and lineinB is '': #end of file
            break
        if not (lineinA == lineinB):
            diff = True
            if DEBUG: print "diff @line # in {0}: {1}, in {2}: {3}".format(filenameA, linenuminA, filenameB, linenuminB)
            break
        linenuminA += 1
        linenuminB += 1
    return diff


def ignoreline(line):
    return isComment(line) or isPubDate(line) or isWhitespace(line) and line is not ''
    pass


def isComment(line):
    startRegex = ".*<!--.*-->.*"
    p = re.compile(startRegex)
    m = p.match(line)
    if m:
        return True
    else:
        return False
    pass


def isPubDate(line):
    startRegex = ".*<pubdate>.*"
    p = re.compile(startRegex)
    m = p.match(line)
    if m:
        return True
    else:
        return False
    pass


def isWhitespace(line):
    startRegex = "^\s*$"
    p = re.compile(startRegex)
    m = p.match(line)
    if m:
        return True
    else:
        return False
    pass


def isXMLFile(filename):
    """docstring for isXMLFile"""
    filePathName, fileExtension = path.splitext(path.expandvars( path.expanduser( path.abspath(filename) ) ))
    return path.isfile(filename) and fileExtension == '.xml'
    pass

def folderdiffprint(directoryA, directoryB, commonlist, onlyinA, onlyinB):
    print "Shared Files"
    for file in commonlist: print "  {0}".format(file)
    print "\n--- {0} ---".format(directoryA, directoryB)
    for file in onlyinA: print "- {0}".format(file)
    print "\n+++ {0} +++".format(directoryB)
    for file in onlyinB: print "+ {0}".format(file)
    pass


def directorysmartdiff(directoryA, directoryB):
    """docstring for directorysmartdiff"""
    directoryA = path.expandvars( path.expanduser( path.abspath(directoryA) ) )
    directoryB = path.expandvars( path.expanduser( path.abspath(directoryB) ) )
    dirsetA = set(os.listdir(directoryA))
    dirsetB = set(os.listdir(directoryB))
    #
    commonlist = dirsetA & dirsetB
    onlyinA = dirsetA - dirsetB
    onlyinB = dirsetB - dirsetA
    changedfiles = []
    #
    folderdiffprint(directoryA, directoryB, commonlist, onlyinA, onlyinB)
    print '\n[Comparing Shared Files]'
    #
    for filename in commonlist:
        fullfilepathA = os.path.join(directoryA, filename)
        fullfilepathB = os.path.join(directoryB, filename)
        #if isXMLFile(fullfilepathA):
        if smartdiff(fullfilepathA, fullfilepathB):
            print ' [!"{0}" - Change found!]'.format(filename)
            changedfiles.append(filename)
        else:
            print ' [ "{0}" - No change]'.format(filename)
    # Summary
    print ''
    folderdiffprint(directoryA, directoryB, commonlist, onlyinA, onlyinB)
    print '\n\n[Shared Files w/Differences]'
    for file in changedfiles: print "! {0}".format(file)
    pass


if __name__ == "__main__":
    if len(sys.argv) is 3:
        directoryA = sys.argv[1]
        directoryB = sys.argv[2]
        print ''
        directorysmartdiff(directoryA, directoryB)
        print "\nFinished. Use diff or WinMerge to compare individual files in detail."
    else:
        print "Use:\n {0} <directory a> <directory b>".format(sys.argv[0])
        print "This script needs two XML RDL files to compare. Full paths, or relative. You decide."
