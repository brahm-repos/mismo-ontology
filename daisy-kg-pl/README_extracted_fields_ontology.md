# Extracted Fields Ontology

## Overview

The **Extracted Fields Ontology** is an OWL ontology that extends the MISMO 3.6 standard to support the representation of data fields extracted from loan documents. This ontology bridges the gap between the MISMO business domain model and the need to represent extracted data fields with their metadata.

## Purpose

This ontology addresses the requirement to model:
- **Loans** that contain multiple **Documents**
- **Documents** that belong to specific **Document Types**
- **Extracted Fields** that represent data points extracted from documents
- **Field Types** that classify the nature of extracted data (string, date, numeric, etc.)
- **Metadata** about the extraction process (confidence, date, position)

## Key Features

### 1. **MISMO 3.6 Integration**
- Extends existing MISMO 3.6 ontology classes
- Reuses `mismo:Loan`, `mismo:Document`, and `mismo:DocumentClassification`
- Maintains compatibility with MISMO standards

### 2. **New Classes for Extracted Fields**
- `extracted:ExtractedField` - Core class for representing extracted data fields
- `extracted:FieldType` - Classification system for field data types
- Specific field type instances: String, Date, Numeric, Alphanumeric, Currency

### 3. **Comprehensive Relationships**
- **Loan → Document** (via `hasDocument`)
- **Document → Document Type** (via `hasDocumentType`)
- **Document → Extracted Fields** (via `hasExtractedField`)
- **Field → Field Type** (via `hasFieldType`)

### 4. **Rich Metadata Support**
- Field names and values
- Extraction confidence scores
- Extraction timestamps
- Field position information
- Inverse relationships for navigation

### 5. **Data Integrity Constraints**
- Cardinality constraints ensuring proper relationships
- Disjoint field types preventing classification conflicts
- Domain and range specifications for all properties

## Ontology Structure

### **Classes**

#### **Core Classes**
- `extracted:ExtractedField` - Data fields extracted from documents
- `extracted:FieldType` - Classification of field data types

#### **Field Type Instances**
- `extracted:StringField` - Text/string data
- `extracted:DateField` - Date/time data
- `extracted:NumericField` - Numeric data
- `extracted:AlphanumericField` - Mixed alphanumeric data
- `extracted:CurrencyField` - Monetary/currency data

### **Object Properties**

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `hasDocument` | `mismo:Loan` | `mismo:Document` | Links loans to documents |
| `hasDocumentType` | `mismo:Document` | `mismo:DocumentClassification` | Links documents to types |
| `hasExtractedField` | `mismo:Document` | `extracted:ExtractedField` | Links documents to fields |
| `belongsToDocument` | `extracted:ExtractedField` | `mismo:Document` | Links fields to documents |
| `hasFieldType` | `extracted:ExtractedField` | `extracted:FieldType` | Links fields to types |
| `belongsToLoan` | `extracted:ExtractedField` | `mismo:Loan` | Links fields to loans |

### **Data Properties**

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `fieldName` | `extracted:ExtractedField` | `xsd:string` | Field identifier |
| `fieldValue` | `extracted:ExtractedField` | `xsd:string` | Extracted value |
| `extractionConfidence` | `extracted:ExtractedField` | `xsd:decimal` | Confidence score (0.0-1.0) |
| `extractionDate` | `extracted:ExtractedField` | `xsd:dateTime` | Extraction timestamp |
| `fieldPosition` | `extracted:ExtractedField` | `xsd:string` | Position in document |

## Usage Examples

### **1. Creating a Loan with Documents and Extracted Fields**

```turtle
# Define a loan
:Loan_001 a mismo:Loan ;
    rdfs:label "Sample Loan 001" .

# Define a document
:Document_001 a mismo:Document ;
    rdfs:label "Promissory Note" ;
    extracted:hasDocumentType :DocumentType_PromissoryNote .

# Link loan to document
:Loan_001 extracted:hasDocument :Document_001 .

# Define document type
:DocumentType_PromissoryNote a mismo:DocumentClassification ;
    rdfs:label "Promissory Note" .

# Create extracted fields
:Field_001 a extracted:ExtractedField ;
    rdfs:label "Borrower Name Field" ;
    extracted:fieldName "borrower_name" ;
    extracted:fieldValue "John Doe" ;
    extracted:hasFieldType extracted:StringField ;
    extracted:extractionConfidence "0.95"^^xsd:decimal ;
    extracted:extractionDate "2024-01-15T10:30:00Z"^^xsd:dateTime ;
    extracted:fieldPosition "Page 1, Top Left" ;
    extracted:belongsToDocument :Document_001 .

:Field_002 a extracted:ExtractedField ;
    rdfs:label "Loan Amount Field" ;
    extracted:fieldName "loan_amount" ;
    extracted:fieldValue "250000" ;
    extracted:hasFieldType extracted:CurrencyField ;
    extracted:extractionConfidence "0.98"^^xsd:decimal ;
    extracted:extractionDate "2024-01-15T10:30:00Z"^^xsd:dateTime ;
    extracted:fieldPosition "Page 1, Center" ;
    extracted:belongsToDocument :Document_001 .
```

### **2. Querying Extracted Fields**

**SPARQL Query: Find all fields extracted from a specific document**
```sparql
PREFIX extracted: <http://www.mismo.org/extracted-fields#>
PREFIX mismo: <http://www.mismo.org/residential/2009/schemas#>

SELECT ?fieldName ?fieldValue ?fieldType ?confidence
WHERE {
    ?document a mismo:Document ;
        rdfs:label "Promissory Note" .
    
    ?field extracted:belongsToDocument ?document ;
        extracted:fieldName ?fieldName ;
        extracted:fieldValue ?fieldValue ;
        extracted:hasFieldType ?fieldType ;
        extracted:extractionConfidence ?confidence .
}
```

**SPARQL Query: Find all currency fields with high confidence**
```sparql
PREFIX extracted: <http://www.mismo.org/extracted-fields#>

SELECT ?fieldName ?fieldValue ?document
WHERE {
    ?field a extracted:ExtractedField ;
        extracted:hasFieldType extracted:CurrencyField ;
        extracted:fieldName ?fieldName ;
        extracted:fieldValue ?fieldValue ;
        extracted:extractionConfidence ?confidence ;
        extracted:belongsToDocument ?document .
    
    FILTER(?confidence > 0.9)
}
```

## File Structure

```
daisy-kg-pl/
├── extracted_fields_ontology.ttl          # Main ontology file
├── README_extracted_fields_ontology.md    # This README file
└── mismo-3.6.ttl                         # MISMO 3.6 ontology (referenced)
```

## Dependencies

- **MISMO 3.6 Ontology** - Required for base classes and document structure
- **OWL 2** - For ontology language features
- **RDF Schema** - For basic modeling constructs
- **XML Schema Datatypes** - For data type definitions

## Validation

The ontology can be validated using:
- **Protégé** - Stanford's ontology editor
- **OWL Validators** - Online and command-line tools
- **SPARQL Endpoints** - For query testing

## Extensibility

The ontology is designed to be extensible:
- **New Field Types** can be added as subclasses of `extracted:FieldType`
- **Additional Metadata** can be added as new data properties
- **Custom Relationships** can be defined for specific use cases

## Contributing

To extend or modify this ontology:
1. Ensure compatibility with MISMO 3.6 standards
2. Follow OWL best practices
3. Add appropriate documentation and examples
4. Validate changes with ontology tools

## License

This ontology extends the MISMO 3.6 standard and follows the same licensing terms.

## Contact

For questions or contributions related to this ontology, please refer to the MISMO standards documentation and community guidelines.
