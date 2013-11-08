"""
Summary
=======

This script splits Nebulon RDL XML files with multiple addrmap's into 
individual XML files. One file for each address map included.

This script should be called from the command line directly. It calls:

    splitAddressMapsFromDirectoryOfFiles(directory)

Where directory is assumed to be current directory, or where directory is the 
first and only argument when called from the CLI. Only XML files are processed 
from this directory. All xml files in the directory are assumed to contain RDL 
content output from Nebulon.



Details:
========

When run (from CLI), this script will seperate RDL files of the following 
simplified format:

    <rdl>
      <addrmap name="addrmap1">
      </addrmap>
      ... <!-- zero or more additional addrmap's -->
    </rdl>

...into individual files for each address map:

    File 1:
      <rdl>
        <addrmap name="addrmap1">
        </addrmap> <!-- end of addrmap1 -->
      </rdl>
    File 2:
      <rdl>
        <addrmap name="addrmap2">
        </addrmap> <!-- end of addrmap2 -->
      </rdl>
    Etc..

These output files are placed in a directory. The directory name defaults to 
the name of the XLM file (minus extension), so when processing the xml file 
"pcu_b0_d31_f3.xml", all address map files will be placed into the folder 
titled "pcu_b0_d31_f3". For example, assuming "pcu_b0_d31_f3.xml" contains 
three address maps:

1. SMBUS_IO
2. SMBUS_MEM
3. SMBUS_CFG

This script would create the folder "pcu_b0_d31_f3" with the three addrmap xml 
files into it (addrmaps with the same name will be overwritten [TODO]):

    ./pcu_b0_d31_f3/
      |-> pcu_b0_d31_f3-SMBUS_IO.xml
      |-> pcu_b0_d31_f3-SMBUS_MEM.xml
      `-> pcu_b0_d31_f3-SMBUS_CFG.xml

However, the folder names can be overriden via the global "fileToPrettyName". 
This dictionary maps file names to folder names. See example in the code for 
details.


"""
import re
import linecache
import os
import os.path as path
import sys #for main only

fileToPrettyName = {} #dictionary with key: filename, value: pretty-folder-name


#this is a shared global dictionary. Its structure is shown below and created via 'mapFile'
addressMaps = {}

#Example:
# addressMaps = {
#           1: 
#           {
#               'start-line': 23, 
#               'name': 'addrmap1',
#               'end-line': 100
#           },
#           2: 
#           { 
#               'start-line': 101, 
#               'name': 'addrmap2',
#               'end-line': 136
#           },
#
#           ...
#
#           'last-sequence': 27,
#           'total-lines': 65414
#       }

def splitAddressMapsFromDirectoryOfFiles(directory):
    """docstring for splitAddressMapsFromDirectoryOfFiles"""
    directory = path.expandvars( path.expanduser( path.abspath(directory) ) )
    for fullfilepath in os.listdir(directory):
        if isXMLFile(fullfilepath):
            outputdir = createFolderForXMLFile(fullfilepath)
            if outputdir:
                print '[Opening File] {0}'.format(fullfilepath)
                if splitAddressMapsFromFile(fullfilepath, outputdir):
                    print '[Processed]'
    pass


#outputfolder should already exist
#Example call: splitAddressMapsFromFile('pcu_b0_d31_f3_top.xml', './PCU')
def splitAddressMapsFromFile(filename, outputfolder, listofaddrmaps=[]):
    linecache.clearcache()
    if mapFile(filename):
        #print addressMaps
        for sequenceNumber in range(1, addressMaps['last-sequence'] + 1):
            print '  [Creating Address Map] {0}'.format(addressMaps[sequenceNumber]['name'])
            shortfilename, extension = path.splitext(path.basename(filename))
            destinationfile = outputfolder + "/" + shortfilename + "-" + addressMaps[sequenceNumber]['name'] + extension
            start, end = getHeaderRange()
            copyLinesToFile(filename, destinationfile, start, end)
            copyLinesToFile(filename, destinationfile, addressMaps[sequenceNumber]['start-line'], addressMaps[sequenceNumber]['end-line'])
            start, end = getFooterRange()
            copyLinesToFile(filename, destinationfile, start, end)
        return True
    else:
        return False
    pass


#mapFile('1vlv_pcu_b0_d31_f3_top.xml')
def mapFile(filename):
    global addressMaps
    addressMaps = {}
    currentLineNumber = 1
    mapSequence = 1
    while linecache.getline(filename, currentLineNumber) is not '':
        #map all address maps in file
        currentLineNumber = findChildAddrmap(filename, currentLineNumber)
        if currentLineNumber:
            addressMaps[mapSequence] = {}
            addressMaps[mapSequence]['name'] = lineIsAddressMapStart(linecache.getline(filename, currentLineNumber))
            addressMaps[mapSequence]['start-line'] = currentLineNumber
            currentLineNumber = findEndOfChildAddrmap(filename, currentLineNumber+1)
            if not currentLineNumber:
                print '[ERROR] Malformed XML'
                return False
            addressMaps[mapSequence]['end-line'] = currentLineNumber
            mapSequence += 1
            currentLineNumber += 1
        #print currentLineNumber
    addressMaps['total-lines'] = lineCount(filename)
    addressMaps['last-sequence'] = mapSequence-1
    #print addressMaps
    return True


def lineCount(filename):
    currentLineNumber = 1
    while linecache.getline(filename, currentLineNumber) is not '':
        currentLineNumber += 1
    return currentLineNumber
    pass


#findEndOfChildAddrmap('audio.xml', 63)
def findEndOfChildAddrmap(filename, currentLineNumber=1):
    map_level = 0
    endLineNumCandidate = findNextLineOfAddrmapInFile(filename, currentLineNumber)
    line = linecache.getline(filename, endLineNumCandidate)
    while not (lineIsAddressMapEnd(line)) or map_level > 0 and line is not '':
        if lineIsAddressMapEnd(line):
            map_level -= 1
        else:
            map_level += 1
        endLineNumCandidate = findNextLineOfAddrmapInFile(filename, endLineNumCandidate+1)
        line = linecache.getline(filename, endLineNumCandidate)
    if line is '':
        return False
    else:
        return endLineNumCandidate
    pass


def findChildAddrmap(filename, currentLineNumber=1):
    currentLineNumber = findNextLineOfAddrmapInFile(filename, currentLineNumber)
    if lineIsAddressMapStart(linecache.getline(filename, currentLineNumber)):
        return currentLineNumber
    else:
        return False


def findNextLineOfAddrmapInFile(filename, currentLineNumber=1):
    while linecache.getline(filename, currentLineNumber) is not '':
        line = linecache.getline(filename, currentLineNumber)
        if lineIsAddressMapStart(line) or lineIsAddressMapEnd(line):
            return currentLineNumber
        currentLineNumber += 1
    return False


def isXMLFile(filename):
    """docstring for isXMLFile"""
    filePathName, fileExtension = path.splitext(path.expandvars( path.expanduser( path.abspath(filename) ) ))
    return path.isfile(filename) and fileExtension == '.xml'
    pass


def createFolderForXMLFile(fullfilepath):
    prettyName = None
    if path.basename(fullfilepath) in fileToPrettyName:
        prettyName = fileToPrettyName[path.basename(fullfilepath)]
    if not prettyName:
        prettyName, dummy = path.splitext(path.basename(fullfilepath))
    filePathName, fileExtension = path.splitext(path.join(path.dirname(path.abspath(fullfilepath)), prettyName, path.basename(fullfilepath)))
    dir = path.join(path.dirname(path.abspath(fullfilepath)), prettyName)
    if not os.path.exists(dir):
        os.makedirs(dir)
    else:
        print 'Directory Already Exists. Skipping:', prettyName
        return False
    return dir
    pass


def lineIsAddressMapStart(line):
    startRegex = ".*<addrmap.+name=\"(.+)\".+=.*>"
    p = re.compile(startRegex)
    m = p.match(line)
    if m:
        return m.group(1)
    else:
        return None
    pass


def lineIsAddressMapEnd(line):
    endRegex = ".*</addrmap>"
    p = re.compile(endRegex)
    m = p.match(line)
    if m:
        return True
    else:
        return None
    pass


def getHeaderRange():
    start = 1
    end = addressMaps[1]['start-line']-1
    return start, end
    pass


def getFooterRange():
    start = addressMaps[addressMaps['last-sequence']]['end-line']+1
    end = addressMaps['total-lines']
    return start, end
    pass


def copyLinesToFile(srcfile, destfile, startline, endline, mode="a"):
    df = open(destfile, mode)
    for i in range(startline, endline + 1):
        df.write(linecache.getline(srcfile, i))
    df.close()
    return True
    pass


#Linegroups example:
# linegroups = {
#       1: {
#           'start-line': 23, 
#           'end-line': 100
#       },
#       2: { 
#           'start-line': 101, 
#           'end-line': 136
#       },
#       3: { 
#           'start-line': 100100, 
#           'end-line': 136000
#       },
#       'last-sequence': 3,
# }


#copyLineGroupsToFile('source', 'output', linegroups)
def copyLineGroupsToFile(srcfile, destfile, linegroups, mode="a"):
    if path.isfile(destfile):
        print "Warning. File is being appended to!", destfile
    df = open(destfile, mode)
    for sequenceNumber in range(1, linegroups['last-sequence'] + 1):
        for i in range(linegroups[sequenceNumber]['start-line'], linegroups[sequenceNumber]['end-line'] + 1):
            df.write(linecache.getline(srcfile, i))
    df.close()
    return True
    pass


def createFile(filename, linecount=1024, mode="w"):
    f = open(filename, mode)
    for i in range(1, linecount+1):
        f.write(str(i)+'\n')
    f.close()





if __name__ == "__main__":
    directory = "."
    if len(sys.argv) is 2:
        directory = sys.argv[1]
        print "", directory
    splitAddressMapsFromDirectoryOfFiles(directory)
    print "Done!"



    