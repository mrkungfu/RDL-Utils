import os
import os.path as path
import xml.etree.ElementTree as ET
import sys #for main only

register_total = 0
empty_total = 0


def old_reg_stats(filename):
    global empty_total
    tree = ET.parse(filename)
    root = tree.getroot()
    names = root.findall(".//reg/name")
    count = 0
    
    for name in names:
        #print name.text
        if name.text is None or name.text is "":
            count+=1
    
    print " REGs:"
    print "   Total = ", len(names)
    print "   Empty = ", count
    empty_total += count
    pass


def reg_stats(filename):
    global empty_total
    global register_total
    tree = ET.parse(filename)
    root = tree.getroot()
    regs = root.findall(".//reg")
    count = 0
    
    for reg in regs:
        name = reg.find("./name")
        if name.text == reg.attrib['type'] or name.text is None or name.text == "":
            count+=1
        #print name.text
    
    print " REGs:"
    print "   Total = ", len(regs)
    print "   Empty = ", count
    register_total += len(regs)
    empty_total += count
    pass

def field_stats(filename):
    global empty_total
    global register_total
    tree = ET.parse(filename)
    root = tree.getroot()
    fields = root.findall(".//field")
    count = 0
    
    for field in fields:
        name = field.find("./name")
        if name.text == field.attrib['fieldname'] or name.text is None or name.text == "":
            count+=1
        #print name.text
    
    print " REGs:"
    print "   Total = ", len(fields)
    print "   Empty = ", count
    register_total += len(fields)
    empty_total += count
    pass


def directory_stats(directory = "."):
    """docstring for splitAddressMapsFromDirectoryOfFiles"""
    global empty_total
    global register_total

    directory = path.expandvars( path.expanduser( path.abspath(directory) ) )
    for fullfilepath in os.listdir(directory):
        if isXMLFile(fullfilepath):
            print '[Opening File] {0}'.format(fullfilepath)
            try:
                reg_stats(fullfilepath)
            except ET.ParseError:
                print " !Oops! That file didn't sit right with me."
            print '[Processed] {0}'.format(fullfilepath)
    print "\nSummary\n=======\n\n Total Regs  = ", register_total
    print " Total Empty = ", empty_total
    pass


def isXMLFile(filename):
    """docstring for isXMLFile"""
    filePathName, fileExtension = path.splitext(path.expandvars( path.expanduser( path.abspath(filename) ) ))
    return path.isfile(filename) and fileExtension == '.xml'
    pass


if __name__ == "__main__":
    directory = "."
    if len(sys.argv) is 2:
        directory = sys.argv[1]
        print "", directory
    directory_stats(directory)
    print "Done!"

