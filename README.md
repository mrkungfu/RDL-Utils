RDL-Utils
=========

This repository contains a set of useful Python scripts for working on RDL XML. The primary script is used to split individual address maps from RDL base (not Word) xml files.

* **rdl-xml-splitter**: generates an xml file per address map of input rdl xml

A set of helper tools are also provided:

* **find-empty-fields/regs**: statistics script to determine registers/fields that are missing descriptions.
* **rdl-xml-diff**: compares one release of RDL XML to another and shows which files are different intelligently.
* **RDL-XML-FingerText-Snippets.ftd**: FingerText snippets for Notepad++ are also provided for added BAR reference metadata.

Notes
-----

If you have any issues with **rdl-xml-splitter**, take a look at the **linecache-xml-split** tool in the Archive folder. It splits RDL XML with multiple addrmaps into files with singe RDL container addrmaps, but requires multiple iterations and some hand text editor work to flatten the files.
