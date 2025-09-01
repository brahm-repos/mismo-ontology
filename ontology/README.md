# ontology



## Getting started

This repo contains python programs to convert 
- mismo xsd files to ontology
- Generate ontology individuals from the json files

Directory Structure:
mismo-3.6/  - contains the mismo 3.6 files
test-data/  - has smaller verion of mismo3.6 file to test the program
xlink_to_xsd,py - this transform the imports. XSD file xlinkMISMOB367.xsd is imported in main mismo-3.6 XSD file MISMO_3.6.0_B367.xsd

xmlxsd_to_turtle.py - this transform the imports. XSD file xml.xsd is imported in main mismo-3.6 XSD file MISMO_3.6.0_B367.xsd

transform,py - is the main program which takes main XSD file MISMO_3.6.0_B367.xsd and converts to turtle.

run.bat  - Windows bat file to runt the transform.py



## MISMO to Ontology
transform.py - is the python program that takes the mismo xsd file and generates the ontology. 

Usage: python transform.py <xsd_file> [output_ttl_file]

Example: 
python transform.py "./mismo-3.6/MISMO_3.6.0_B367.xsd"
This generate the outfile named mismo-turtle.ttl if you do not pass the <output_ttl_file>


## JSON to Ontology Individuals
DAISY team has generated a json format which has the data fields extracted from 
loan documents. 

json-to-individuals.py is the python program that takes the json and generated the
individuals. 

Note: This work is not completed as of now. but checking the script for the sake of
    backup.
