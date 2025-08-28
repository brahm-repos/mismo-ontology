
# DAISY Knowledge Graph pipline
## updated as of 08/27/2025

DAISY is a product from Mphasis that does the auto-classification, book marking and data extraction.

This pipeline consists of the following.
Step 1: Documents are classified and data is extracted using DAISY
Step 2: Take the output from DAISY 
Step 3: Generate the Knowledge graph of the loan documents and extracted fields.
Step 4: Persist Knowledge in GrapDB


pre-requisites:
1. It is assumed that Mortgage Base Ontology is defined and accessible
2. MISMO base ontology layer provides Loan, Document, Document-Sets, DocumentClassification entities. IT does not provide the entities to handle the data fields extracted from the documents of a given loan.
3. MISMO base ontology is extended to accommidate data extracted from loan documents using extracted_fields_ontology.ttl file. Read the file README_extracted_fields_ontology.md for more details on this ontology file.


# Step 1: Documents are classified and data is extracted using DAISY
This is TBD. This may be outside the scope of the pipeline.

# Step 2: ake the output from DAISY 
Python program is yet to be developed for this step.

Sample file is given in test-data/dataextracted_333_888_999_123321_v1.json 

# Step 3: Generate the Knowledge graph of the loan documents and extracted fields.
Python program named generate_ontology_instances.py with the DAISY file from Step 2.
This will generate the file named output/generated_instances.ttl

   python generate_ontology_instances.py --input your_data.json --output your_output.ttl

   python generate_ontology_instances.py --help

# Step 4: Persist Knowledge
This steps saves the knwoledge in persistent layer.




