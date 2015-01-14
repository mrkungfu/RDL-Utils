#!/bin/python
import os.path as path
import os
from lxml import etree
import sys #for main only
# Takes an xml file representing hw registers and splits and flattens them into more managable xml files.
# Also trys to add additional details needed for locating BAR's (*not* full proof, so read the output log!),
# and more. Vs. the old tool, this one supports flattening of address maps (even in deeply nested files),
# and semi-intelligent BAR location mapping. BAR queries are also cached when processing. This can save a
# significant amount of time when BAR names are similar between files.
#
# Notes:
# Requires lxml, a powerfull lib for xml parsing, to run - https://pypi.python.org/pypi/lxml/3.4.1
# See documentation on System RDL for additional details.


def splitAddressMapsFromDirectoryOfFiles(directory):
    """find all xml files in directory and run 'parse_rdl_file' on each one"""
    directory = path.expandvars(path.expanduser(path.abspath(directory)))
    print directory
    files = os.listdir(directory)
    files = filter(is_xml_file, files) #returns list of .xml files in 'directory'
    print "File(s) to process:", files
    files = [path.join(path.abspath(directory), path.basename(afile)) for afile in files]
    map(parse_rdl_file, files) #parse files: open, parse, create new files per leaf addrmap

def parse_rdl_file(fullfilepath):
    """ <parse_rdl_file(fullfilepath)>
    Create folder to contain the output folders
    Parse the xml based RDL file
    Write xml file per addrmap parsed
    """
    rdl_handler = None
    print '[Opening] {0}'.format(fullfilepath)
    outputdir = create_folder_from_filename(fullfilepath)
    if outputdir:
        print '  [Loading XML..] {0}'.format(fullfilepath)
        rdl_handler = RDLFileHandler(fullfilepath, outputdir)
        rdl_handler.create_files_from_reg_containers()
    print '[Closed]'

def create_folder_from_filename(fullfilepath):
    """
    Pull out the xml file name, strip extension and create a folder from the filename (if not already found).
    Returns string path of directory created, or False if directory wasn't created
    """
    foldername, dummy = path.splitext(path.basename(fullfilepath))
    filePathName, fileExtension = path.splitext(path.join(path.dirname(path.abspath(fullfilepath)), foldername, path.basename(fullfilepath)))
    adir = path.join(path.dirname(path.abspath(fullfilepath)), foldername)
    if not os.path.exists(adir):
        os.makedirs(adir)
        print '  [Created Folder] {0}'.format(adir)
    else:
        print ' ![Skipping] Directory "{0}" already exists. Delete to re-generate.'.format(foldername)
        raw_input("Press 'enter' to continue...")
        return False
    return adir





class RDLFileHandler(object):
    """docstring for RDLFileHandler"""
    def __init__(self, filename, destdir):
        super(RDLFileHandler, self).__init__()
        #
        self.filename = filename
        self.outputfolder = destdir
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True)
        self.rdl_etree = etree.parse(filename, parser)
        self.reg_containers = []
        #
        self.find_and_parse_reg_containers()
        self.process_overrides()
        #self.create_files_from_reg_containers() #hold off for now
    def find_and_parse_reg_containers(self):
        """Find all addrmap containers with reg elements and add them to the 'reg_containers' list"""
        elements = self.rdl_etree.findall(".//addrmap")
        for element in elements:
            if elementhasregs(element) and is_container_element(element):
                #create a "RDLContainer" that parses and summurizes data about the container ET element; returns on object with the element fully parsed
                self.reg_containers.append(RDLContainer(element, tree=self.rdl_etree))
            #print self.reg_containers
    def create_files_from_reg_containers(self):
        #remove root addrmaps
        root_containers = self.rdl_etree.findall("./addrmap")
        for container in root_containers:
            container.getparent().remove(container)
        #create strings of containers
        for container in self.reg_containers:
            self.rdl_etree.find('.').append(container.element)
            shortfilename, extension = path.splitext(path.basename(self.filename))
            destinationfile = self.outputfolder + "/" + shortfilename + container.path + extension
            copyStringToFile(etree.tostring(self.rdl_etree, pretty_print=True), destinationfile, mode="w")
            container.element.getparent().remove(container.element)
            string = "  [Created] {0} (Space:{1})".format(shortfilename + container.path + extension, get_container_space(container.element))
            if container.bar['elem'] is not None:
                string += " | '{0}' @ {1}[{2}] + 0x{3:X} (size: {4})".format(container.bar['name'], get_container_space(container.bar['elem']), get_container_baseaddress(container.bar['elem'].getparent()), get_local_address(container.bar['elem']), get_reg_size(container.bar['elem']))
            #TODO: Figure out which BAR's are missing... prolly down in the container parser?
            #if not container.bar['found'] and container.bar['name'] != None:
            #    string += " | Bar not found!"
            print string
    def process_overrides(self):
        pass



class RDLContainer(object):
    """
    RDLContainer
    Create a new object with an etree element (an RDL container: 'addrmap' or 'regfile') and then parse
    the element, looking for interesting information, and making it possible to update fields (e.g. address)
    and add metadata (for BAR location, as applicable).
    """
    query_cache = {}
    def __init__(self, element, tree, overrides=[]):
        super(RDLContainer, self).__init__()
        self.overrides = overrides
        self.element = element
        self.bar = {'name': None, 'elem': None, 'isdup': False, 'found': False}
        self.addr = None
        self.path = None #path using dash notation (outer-inner-inside_inner)
        #
        self.find_path_and_flataddr()
        self.bar['name'] = get_container_baseaddress(self.element)
        #shouldn't do the rest automatically, but convenient for now
        self.update_with_flat_address()
        if tree and self.bar['name'] and get_container_space(self.element) != "MSG" and get_container_space(self.element) != "CFG":
            self.find_nearest_bar_in_element(tree)
            self.update_with_bar_metadata()
    def find_nearest_bar_in_element(self, tree):
        #BaseAddress(self.element, tree)
        print "------DEBUG-------" #DEBUG
        print "Container: {0} (Space: {1})".format(getelementpath(self.element), get_container_space(self.element)) #DEBUG
        print "BaseAddress: {0}".format(self.bar['name']) #DEBUG
        BaseAddress(self.element, self.tree)
        #BAR's come in all shapes.. massage for different BaseAddress formats (path based, per SAOLA, etc.), and only take the first BAR when there's a list.
        self.bar['name'] = self.bar['name'].replace("{", "")
        self.bar['name'] = self.bar['name'].replace("}", "")
        self.bar['name'] = self.bar['name'].split(",")[0].split(".")[-1]
        #only check in PCI config space for BAR's [assumption]
        regs = []
        if self.bar['name'] in RDLContainer.query_cache:
            regs = RDLContainer.query_cache[self.bar['name']]
            print "Found in cache!"
        else:
            regs = tree.findall(".//property[@name='Space'][@value='CFG']/../reg[@regname='" + self.bar['name'] + "']")
            RDLContainer.query_cache[self.bar['name']] = regs
        distance = 1024 #set high to allow finding the smallest reg as we go... honestly, if it's this far away, we're prolly screwed =P
        for reg in regs:
            #regdist is the distance from the register to the common node, basedist is the distance from this container to the common node
            regdist, basedist = distancesbetweenelements(reg.getparent(), self.element)
            print "  Candidate reg: {2}; dist(reg: {0}, base: {1})".format(regdist, basedist, getelementpath(reg)) #DEBUG
            if basedist > 0:#if 0, found reg is a subreg, and that shouldn't be picked - not foolproof, but works in the common senarios - TODO: look into a subtree check based on Xpath search
                if max(regdist, basedist) < distance:
                    distance = max(regdist, basedist)
                    self.bar['elem'] = reg
                    self.bar['found'] = True
                    self.bar['isdup'] = False
                elif max(regdist, basedist) == distance:
                    self.bar['isdup'] = True
        if self.bar['found']: #DEBUG
            print "  BAR reg pick: {0}, duplicate?: {1}".format(getelementpath(self.bar['elem']), self.bar['isdup']) #DEBUG
        if self.bar['name'] == '':
            self.bar['name'] = None
    def find_path_and_flataddr(self):
        #calculates the flattened address and saves as an int, and saves the conainter path as a string from this element
        self.addr = 0x0
        self.path = ""
        next_elem = self.element
        while is_container_element(next_elem):
            self.path = "." + next_elem.attrib['name'] + self.path
            self.addr += get_local_address(next_elem)
            #print address, next_elem
            next_elem = next_elem.getparent()
        #print self.path
    def update_with_flat_address(self):
        self.element.attrib['addr'] = "0x{0:X}".format(self.addr)
    def update_with_bar_metadata(self):
        """
        Adds the following properties:
            <property name="BaseAddress" value="BAR"/>
            <property name="referenceBaseAddress" value="0/30/5"/>
            <property name="referenceOffset" value="0x10"/>
            <property name="referenceSpace" value="CFG"/>
            <property name="referenceSize" value="32"/>
        """
        #print self.bar
        if self.bar['elem'] is not None:
            refoffset = get_local_address(self.bar['elem'])
            refspace = get_container_space(self.bar['elem'])
            refsize = get_reg_size(self.bar['elem'])
            refbase = get_container_baseaddress(self.bar['elem'])
            self.element.insert(3, etree.Element("property", {'name':"referenceSize",'value':str(refsize)}))
            self.element.insert(3, etree.Element("property", {'name':"referenceSpace",'value':refspace}))
            self.element.insert(3, etree.Element("property", {'name':"referenceOffset",'value':"0x{0:X}".format(refoffset)}))
            self.element.insert(3, etree.Element("property", {'name':"referenceBaseAddress",'value':refbase}))



class BaseAddress(object):
    """docstring for BaseAddress"""
    query_cache = {}#{"regname": [<element_reg>, <element_reg>, ...], "reg2name": [...], ...}
    def __init__(self, container_element, tree):
        super(BaseAddress, self).__init__()
        self.tree = tree
        self.container_element = container_element
        self.barstring = get_container_baseaddress(self.container_element)
        self.bars = []
        #
        self.__update_bars()
        print self.bars
        self.__lookup_bar_candidates()
        self.__sort_bars_by_distance()
    def __update_bars(self):
        bar_list = self.barstring.replace("{", "").replace("}", "").split(",")
        for bar in bar_list:
            self.bars.append({"name": bar, "regs": [], "element": None, "found": False, "isdup": False})
        #self.barstring = self.bar['name'].split(",")[0].split(".")[-1]
    def __lookup_bar_candidates(self):
        for bar in self.bars:
            name = bar['name'].split(".")[-1]
            #lookup in cache
            if name in BaseAddress.query_cache:
                bar['regs'] = BaseAddress.query_cache[name]
            else:
                bar['regs'] = self.tree.findall(".//property[@name='Space'][@value='CFG']/../reg[@regname='" + name + "']")
                BaseAddress.query_cache[name] = bar['regs']
            #bar['element']
    def __sort_bars_by_distance(self):
        for bar in self.bars:
            regs = bar['regs']
            bar_tuples = []
            for reg in regs:
                #regdist is the distance from the register to the common node, basedist is the distance from this container to the common node
                regdist, basedist = distancesbetweenelements(reg.getparent(), self.container_element)
                bar_tuples.append((reg, max(regdist, basedist)))
                print "  Candidate reg: {2}; dist(reg: {0}, base: {1})".format(regdist, basedist, getelementpath(reg)) #DEBUG
            bar_tuples.sort(key=lambda distance: distance[1])
            self.bar['sorted_tuples'] = bar_tuples
            print bar_tuples



def repl():
    import code
    code.interact(local=locals())

def get_local_address(element):
    address = int(element.attrib['addr'],0)
    if element.tag == 'reg': #look for register override
        aliasaddr = element.find("property[@name='AliasAddress']")
        if aliasaddr.attrib['value'] != '':
            address = int(aliasaddr.attrib['value'],0) #typically hex, but 0 base should pick wisely (hopefully!)
    return address

def get_container_space(element):
    temp = element
    if not is_container_element(element):
        temp = element.getparent()
    prop = temp.find("property[@name='Space']")
    return prop.attrib['value']

def get_reg_size(element):
    prop = element.find("property[@name='width']")
    return int(prop.attrib['value'])

def get_container_baseaddress(element):
    temp = element
    if not is_container_element(element):
        temp = element.getparent()
    prop = temp.find("property[@name='BaseAddress']")
    return prop.attrib['value']

def get_element_short_name(element):
    name = ''
    if element.tag == 'reg':
        name = element.attrib['regname']
    elif element.tag == 'field':
        name = element.attrib['fieldname'] 
    else:
        name = element.attrib['name'] 
    return name

def distancesbetweenelements(elementa, elementb):
    #find distance between two xml elements using set theory
    alist = [elementa]
    blist = [elementb]
    #traverse tree to root from each element
    while alist[-1].getparent() is not None:
        alist.append(alist[-1].getparent())
    while blist[-1].getparent() is not None:
        blist.append(blist[-1].getparent())
    aset = set(alist)
    bset = set(blist)
    commonset = aset & bset #set intersection
    aset = aset - commonset
    bset = bset - commonset
    return len(aset), len(bset)

def getelementpath(element):
    #calculates the flattened conainter path as a string from this element and returns it
    path = ""
    next_elem = element
    while next_elem is not None:
        path = "." + get_element_short_name(next_elem) + path
        #print address, next_elem
        next_elem = next_elem.getparent()
    #print path
    return path

def isinpath(element, path):
    element_path = getelementpath(element)
    #TODO: compare paths inteligently...

def getcanonicalbar(barstring):
        temp = barstring.replace("{", "").replace("}", "")
        bars = temp.split(",")
        barnames = []
        for bar in bars:
            if not isnumber(bar):
                barnames.append(bar)
        index = common_prefix_count(barnames[0], barnames[1])

        pass

#String Generic
def common_prefix_count(str0, str1):
    "returns the length of the longest common prefix"
    for i, pair in enumerate(zip(str0, str1)):
        if pair[0] != pair[1]:
            return i
    return i

def elementhasregs(element):
    return len(element.findall("./reg")) > 0 #check 'is_container_element'?

def copyStringToFile(string, destfile, mode="a"):
    df = open(destfile, mode)
    df.write(string)
    df.close()
    return True
    pass

def is_container_element(element):
        return element.tag == 'addrmap' or element.tag == 'regfile' #is regfile the correct name?

def is_xml_file(filename):
    """returns bool"""
    filePathName, fileExtension = path.splitext(path.expandvars(path.expanduser(path.abspath(filename))))
    #print path.isfile(filename), fileExtension
    return path.isfile(filename) and fileExtension == '.xml'



if __name__ == "__main__":
    directory = "."
    if len(sys.argv) is 2:
        directory = sys.argv[1]
        print "", directory
    splitAddressMapsFromDirectoryOfFiles(directory)
    print "Done!"
    print '- Please check all address maps above that are missing a Space "(Space:)"'
    print '- Please check all address maps with (Space:IO) and (Space:MEM) shown, but without a BAR to their right'
    raw_input("Press 'enter' to continue...")
