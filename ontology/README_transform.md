# MISMO XSD to RDF/RDFS/OWL TTL Transformer

This tool transforms the MISMO_3.6.0_B367.xsd file into RDF/RDFS/OWL in turtle format following the specified transformation patterns.

## Overview

The transformer implements the transformation patterns specified in the prompt to convert MISMO XSD schema definitions into semantic web ontology format. It handles various XSD patterns including simple types, complex types, enumerations, and collections.

## Transformation Patterns Implemented

### Pattern 001: Simple Types with Restrictions
**XSD Pattern:**
```xml
<xsd:simpleType name="MISMOEnum_Base">
    <xsd:restriction base="xsd:string">
        <xsd:maxLength value="80"/>
    </xsd:restriction>
</xsd:simpleType>
```

**TTL Output:**
```ttl
mismo:MISMOEnum_Base a rdfs:Datatype ;
    rdfs:label "MISMOEnum_Base" ;
    owl:equivalentClass [ a rdfs:Datatype ;
            owl:onDatatype xsd:string ;
            owl:withRestrictions ( [ xsd:maxLength "80"^^xsd:nonNegativeInteger ] ) ] .
```

### Pattern 002: Enumerations with Values
**XSD Pattern:**
```xml
<xsd:simpleType name="DataNotSuppliedReasonBase">
    <xsd:restriction base="MISMOEnum_Base">
        <xsd:enumeration value="NotCollected">
            <xsd:documentation>The creator of the MISMO message does not collect the data point.</xsd:documentation>
        </xsd:enumeration>
    </xsd:restriction>
</xsd:simpleType>
```

**TTL Output:**
```ttl
mismo:DataNotSuppliedReasonBase a rdfs:Datatype ;
    rdfs:label "DataNotSuppliedReasonBase" ;
    rdfs:comment "Base datatype for DataNotSuppliedReasonBase enumerations" ;
    rdfs:subClassOf mismo:MISMOEnum_Base .

mismo:NotCollected a rdf:Property ;
    rdfs:label "NotCollected" ;
    rdfs:comment "The creator of the MISMO message does not collect the data point." ;
    rdfs:subPropertyOf mismo:DataNotSuppliedReasonBase .
```

### Pattern 004: Complex Types with Simple Content and Attributes
**XSD Pattern:**
```xml
<xsd:complexType name="MISMOIdentifier">
    <xsd:simpleContent>
        <xsd:extension base="MISMOIdentifier_Base">
            <xsd:attribute name="IdentifierOwnerURI" type="MISMOURI_Base"/>
        </xsd:extension>
    </xsd:simpleContent>
</xsd:complexType>
```

**TTL Output:**
```ttl
mismo:MISMOIdentifier a rdfs:Datatype ;
    rdfs:label "MISMOIdentifier" ;
    rdfs:comment "Complex type: MISMOIdentifier" ;
    rdfs:subClassOf mismo:MISMOIdentifier_Base .

mismo:identifierOwnerURI a owl:DatatypeProperty ;
    rdfs:label "identifierOwnerURI" ;
    rdfs:comment "Attribute: IdentifierOwnerURI" ;
    rdfs:domain mismo:MISMOIdentifier ;
    rdfs:range mismo:MISMOURI_Base .
```

### Pattern 006: Complex Types with Elements and Attributes
**XSD Pattern:**
```xml
<xsd:complexType name="ABOUT_VERSION">
    <xsd:sequence>
        <xsd:element name="AboutVersionIdentifier" type="MISMOIdentifier"/>
    </xsd:sequence>
    <xsd:attribute name="SequenceNumber" type="MISMOSequenceNumber_Base"/>
</xsd:complexType>
```

**TTL Output:**
```ttl
mismo:ABOUT_VERSION a rdfs:Class ;
    rdfs:label "ABOUT_VERSION" ;
    rdfs:comment "Complex type: ABOUT_VERSION" .

mismo:AboutVersionIdentifier a rdfs:Datatype ;
    rdfs:label "AboutVersionIdentifier" ;
    rdfs:comment "Element: AboutVersionIdentifier" ;
    rdfs:subClassOf mismo:MISMOIdentifier .

mismo:SequenceNumber a rdfs:Datatype ;
    rdfs:label "SequenceNumber" ;
    rdfs:comment "Attribute: SequenceNumber" ;
    rdfs:subClassOf mismo:MISMOSequenceNumber_Base .
```

### Pattern 007: Collection Types (Containing Multiple Instances)
**XSD Pattern:**
```xml
<xsd:complexType name="ABOUT_VERSIONS">
    <xsd:sequence>
        <xsd:element name="ABOUT_VERSION" type="ABOUT_VERSION" maxOccurs="unbounded"/>
    </xsd:sequence>
</xsd:complexType>
```

**TTL Output:**
```ttl
mismo:ABOUT_VERSIONS a rdfs:Class ;
    rdfs:label "ABOUT_VERSIONS" ;
    rdfs:comment "A collection containing multiple ABOUT_VERSION instances. Collection type: ABOUT_VERSIONS" .

mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "ABOUT_VERSION" ;
    rdfs:comment "Element contained in ABOUT_VERSIONS collection" .

mismo:containsABOUT_VERSION a rdf:Property ;
    rdfs:label "contains ABOUT_VERSION" ;
    rdfs:comment "Relates ABOUT_VERSIONS to individual ABOUT_VERSION instances" ;
    rdfs:domain mismo:ABOUT_VERSIONS ;
    rdfs:range mismo:ABOUT_VERSION .

mismo:ABOUT_VERSIONS rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty mismo:containsABOUT_VERSION ;
    owl:minCardinality "0"^^xsd:nonNegativeInteger
] .
```

### Pattern 009: Complex Types with Only Attributes
**XSD Pattern:**
```xml
<xsd:complexType name="RELATIONSHIP">
    <xsd:attribute name="SequenceNumber" type="MISMOSequenceNumber_Base"/>
</xsd:complexType>
```

**TTL Output:**
```ttl
mismo:RELATIONSHIP a rdfs:Class ;
    rdfs:label "RELATIONSHIP" ;
    rdfs:comment "Complex type: RELATIONSHIP" .

mismo:SequenceNumber a rdfs:Datatype ;
    rdfs:label "SequenceNumber" ;
    rdfs:comment "Attribute: SequenceNumber" ;
    rdfs:subClassOf mismo:MISMOSequenceNumber_Base .
```

## What Gets Ignored

The transformer automatically ignores the following patterns as specified:

1. **Extension Elements**: Any element with name ending in "EXTENSION"
2. **MISMO_BASE Types**: Complex types containing `<xsd:any>` elements
3. **Attribute Groups**: 
   - `xlink:MISMOresourceLink`
   - `xlink:MISMOarcLink`
   - `AttributeExtension`

## Requirements

- Python 3.6 or higher
- No external dependencies required (uses only built-in Python libraries)

## Usage

### Command Line Interface

```bash
# Transform MISMO XSD to TTL
python transform_mismo_xsd.py --input MISMO_3.6.0_B367.xsd --output mismo_ontology.ttl

# Enable verbose logging
python transform_mismo_xsd.py --input MISMO.xsd --output output.ttl --verbose

# Short form
python transform_mismo_xsd.py -i MISMO.xsd -o output.ttl
```

### Windows Batch File

Use the provided batch file for easy execution on Windows:

```cmd
run_transform.bat
```

This will process the MISMO XSD file and generate the TTL ontology in the `output/` directory.

## Output Format

The transformer generates TTL files with:

- **Standard Prefixes**: RDF, RDFS, OWL, XSD, SKOS, and MISMO namespaces
- **Type Definitions**: All XSD types converted to appropriate RDF/RDFS/OWL constructs
- **Documentation**: Original XSD documentation preserved as comments
- **Relationships**: Proper inheritance and property relationships
- **Constraints**: Cardinality and other constraints where applicable

## File Structure

```
ontology/
├── transform_mismo_xsd.py          # Main transformer script
├── run_transform.bat               # Windows batch file for execution
├── mismo-3.6/
│   └── MISMO_3.6.0_B367.xsd      # Input MISMO XSD file
├── output/                         # Generated output files
└── README_transform.md             # This documentation file
```

## Key Features

### Automatic Pattern Detection
The transformer automatically detects the appropriate transformation pattern based on XSD structure:
- Simple types with restrictions
- Enumerations
- Complex types with simple content
- Complex types with elements
- Collection types
- Complex types with only attributes

### Documentation Preservation
All original XSD documentation is preserved in the TTL output as `rdfs:comment` properties.

### Smart Naming
Attribute names are automatically converted to camelCase for property names (e.g., `IdentifierOwnerURI` → `identifierOwnerURI`).

### Extension Handling
The transformer automatically identifies and ignores extension elements and attribute groups as specified in the patterns.

## Error Handling

The transformer includes comprehensive error handling:
- XSD parsing validation
- File I/O error management
- Detailed logging for debugging
- Graceful failure with informative error messages

## Logging

The transformer provides detailed logging:
- **INFO**: General transformation information
- **DEBUG**: Detailed transformation steps (with --verbose flag)
- **ERROR**: Error conditions and failures

## Extensibility

The transformer is designed to be easily extensible:
- Modular pattern-based architecture
- Configurable transformation rules
- Pluggable pattern detection
- Extensible output formatting

## Troubleshooting

### Common Issues

1. **Python not found**: Ensure Python 3.6+ is installed and in PATH
2. **Input file not found**: Verify the MISMO XSD file path is correct
3. **Permission errors**: Ensure write permissions for output directory
4. **Memory issues**: For very large XSD files, consider processing in smaller sections

### Debug Mode

Use the `--verbose` flag for detailed logging:

```bash
python transform_mismo_xsd.py --input MISMO.xsd --output output.ttl --verbose
```

## Contributing

To extend the transformer:

1. Add new transformation patterns in the `transform_*` methods
2. Extend pattern detection in the `transform_element` method
3. Add new output formatting options
4. Update the pattern documentation

## License

This tool is part of the Virtuoso ontology project and follows the same licensing terms.
