RDL-Utils
=========

This repository contains a set of useful Python scripts for working on RDL XML. The primary tool, **rdl-xml-splitter**, is used to split individual address maps from RDL base (not Word) xml files:

* **rdl-xml-splitter**: generates a flattened xml file per address map contained in xml (not Word or CRIF) based RDL files

A set of helper tools are also provided:

* **find-empty-fields/regs**: statistics scripts to determine if there are registers/fields with missing descriptions.
* **rdl-xml-diff**: a smart diff for rdl -> compares one release of RDL XML to another and shows which files are different intelligently.


Notes
-----

If you have any issues with **rdl-xml-splitter**, take a look at the **linecache-xml-split** tool in the Archive folder. It splits RDL XML with multiple addrmaps into files with singe RDL container addrmaps, but requires multiple iterations and some hand text editor work to flatten the files. Also in the Archive folder are FingerText snippets for Notepad++, **RDL-XML-FingerText-Snippets.ftd**, which can be used to manually add BAR reference metadata.