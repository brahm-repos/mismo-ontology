# Enhanced Knowledge Graph Generator

This tool generates knowledge graph instances based on the enhanced loan document ontology from extracted JSON data.

## Overview

The Enhanced Knowledge Graph Generator processes JSON files containing extracted document fields and generates RDF/TTL (Turtle) format knowledge graph instances that conform to the `enhanced_loan_document_ontology.ttl` ontology.

## Features

- **MISMO Container Name Transformation**: Automatically transforms MISMO container names according to specified rules:
  - Takes the value after the separator ":" if it exists
  - Removes spaces and replaces them with "_"
  - Converts to uppercase
  - Example: "Loan Adjustments:Rate Or Payment Change Occurrence" → "RATE_OR_PAYMENT_CHANGE_OCCURRENCE"

- **Data Type Detection**: Automatically detects appropriate XSD data types for field values:
  - String, Integer, Decimal, Boolean, Date, DateTime
  - Pattern-based detection for dates, currency, and numeric values

- **Ontology Compliance**: Generates instances that follow the enhanced loan document ontology structure:
  - Loan instances (mismo:loan)
  - Document instances (mismo:Document)
  - Document type classifications (mismo:document_Classification)
  - MISMO entity instances (owl:Thing)
  - Field instances with proper data types
  - Relationship properties between entities

## Requirements

- Python 3.6 or higher
- No external dependencies required (uses only built-in Python libraries)

## Usage

### Command Line Interface

```bash
# Process a single JSON file
python generate_enhanced_kg.py --input <input_json_file> --output <output_ttl_file>

# Process all JSON files in a directory
python generate_enhanced_kg.py --directory <input_directory> --output <output_directory>

# Enable verbose logging
python generate_enhanced_kg.py --input data.json --output output.ttl --verbose

# Specify custom ontology file
python generate_enhanced_kg.py --input data.json --output output.ttl --ontology custom_ontology.ttl
```

### Examples

```bash
# Process the test data file
python generate_enhanced_kg.py --input test-data/dataextracted_333_888_999_123321_v1.json --output output/enhanced_kg.ttl

# Process all dataextracted files in test-data directory
python generate_enhanced_kg.py --directory test-data --output output/

# Process with verbose output
python generate_enhanced_kg.py --input data.json --output output.ttl --verbose
```

### Windows Batch File

Use the provided batch file for easy execution on Windows:

```cmd
run_enhanced_kg.bat
```

This will process the test data and generate the knowledge graph in the `output/` directory.

## Input Data Format

The generator expects JSON files with the following structure:

```json
{
    "extractedFields": [
        {
            "documentType": "Document Type Name",
            "documentFields": [
                {
                    "MismoContainerName": "Entity:Sub Entity Name",
                    "Mismofields": [
                        {
                            "fieldName": "Field Name",
                            "value": "Field Value",
                            "type": "Field Type",
                            "uuid": "Field UUID"
                        }
                    ]
                }
            ]
        }
    ]
}
```

## Output Format

The generator produces TTL (Turtle) format files with:

- **Prefixes**: Standard RDF, RDFS, OWL, XSD, MISMO, and custom loan document namespaces
- **Instances**: Loan, Document, Document Type, Entity, and Field instances
- **Relationships**: Properties linking entities according to the ontology
- **Data Types**: Appropriate XSD data types for field values

### Example Output

```ttl
@prefix loandocs: <http://www.mismo.org/loan-document-ontology#> .
@prefix mismo: <http://www.mismo.org/residential/2009/schemas#> .

loandocs:Loan_DEFAULT_LOAN a mismo:loan ;
    rdfs:label "Loan: DEFAULT_LOAN" .

loandocs:Document_abc12345 a mismo:Document ;
    rdfs:label "Commercial Promissory Note" .

loandocs:RATE_OR_PAYMENT_CHANGE_OCCURRENCE_xyz67890 a owl:Thing ;
    rdfs:label "RATE_OR_PAYMENT_CHANGE_OCCURRENCE" ;
    rdfs:comment "MISMO entity representing RATE_OR_PAYMENT_CHANGE_OCCURRENCE information, formed from extracted fields" .

loandocs:Field_58ac31cd-2b82-4430-a848-057a9ebfd000 a owl:Thing ;
    rdfs:label "Adjustment Change Effective Due Date" ;
    loandocs:fieldName "Adjustment Change Effective Due Date" ;
    loandocs:fieldValue "" ;
    loandocs:fieldType "" ;
    loandocs:fieldUUID "58ac31cd-2b82-4430-a848-057a9ebfd000" .

loandocs:Loan_DEFAULT_LOAN loandocs:hasDocument loandocs:Document_abc12345 .
loandocs:Document_abc12345 loandocs:hasDocumentType loandocs:DocumentType_Commercial_Promissory_Note .
loandocs:Document_abc12345 loandocs:hasExtractedEntity loandocs:RATE_OR_PAYMENT_CHANGE_OCCURRENCE_xyz67890 .
```

## File Structure

```
daisy-kg-pl/
├── generate_enhanced_kg.py          # Main generator script
├── run_enhanced_kg.bat             # Windows batch file for execution
├── prompts/
│   └── enhanced_loan_document_ontology.ttl  # Enhanced ontology file
├── test-data/
│   └── dataextracted_333_888_999_123321_v1.json  # Sample input data
├── output/                          # Generated output files
└── README_enhanced_kg.md           # This documentation file
```

## Key Components

### EnhancedKnowledgeGraphGenerator Class

- **`transform_mismo_container_name()`**: Transforms MISMO container names according to specified rules
- **`detect_field_type()`**: Automatically detects appropriate XSD data types
- **`generate_*_instance()`**: Methods for generating different types of instances
- **`generate_relationships()`**: Creates relationship statements between entities
- **`process_json_data()`**: Main processing method for JSON data

### Data Processing Flow

1. **Input Parsing**: Reads and validates JSON input files
2. **Name Transformation**: Transforms MISMO container names
3. **Instance Generation**: Creates TTL instances for all entities
4. **Relationship Creation**: Establishes connections between entities
5. **Output Generation**: Produces formatted TTL files

## Error Handling

The generator includes comprehensive error handling:

- Input file validation
- JSON parsing error handling
- File I/O error management
- Detailed logging for debugging
- Graceful failure with informative error messages

## Logging

The generator provides detailed logging:

- **INFO**: General processing information
- **DEBUG**: Detailed processing steps (with --verbose flag)
- **ERROR**: Error conditions and failures
- **WARNING**: Non-critical issues

## Extensibility

The generator is designed to be easily extensible:

- Modular class structure
- Configurable ontology file paths
- Customizable output formats
- Pluggable data type detection
- Extensible relationship generation

## Troubleshooting

### Common Issues

1. **Python not found**: Ensure Python 3.6+ is installed and in PATH
2. **Input file not found**: Verify the input file path is correct
3. **Permission errors**: Ensure write permissions for output directory
4. **Memory issues**: For large files, consider processing in smaller batches

### Debug Mode

Use the `--verbose` flag for detailed logging:

```bash
python generate_enhanced_kg.py --input data.json --output output.ttl --verbose
```

## Contributing

To extend the generator:

1. Add new instance types in the `generate_*_instance()` methods
2. Extend data type detection in `detect_field_type()`
3. Add new relationship types in `generate_relationships()`
4. Update the ontology file for new entity types

## License

This tool is part of the Virtuoso ontology project and follows the same licensing terms.
