# MISMO Ontology Hierarchy Changes

## Overview

This document explains the changes made to establish proper class hierarchies in the MISMO ontology, enabling WebProtégé to properly visualize the class structure.

## Problem Statement

The original transformation patterns created individual classes but didn't establish proper containment hierarchies. For example:
- `ABOUT_VERSIONS` was created as a collection class
- `ABOUT_VERSION` was created as an individual class
- But there was no clear relationship showing that `ABOUT_VERSIONS` contains `ABOUT_VERSION`

## Solution: Enhanced Pattern 007 and Hierarchy Establishment

### Pattern 007 (Collection Types) - Enhanced

**Before:**
```ttl
mismo:ABOUT_VERSIONS a rdfs:Class ;
    rdfs:label "ABOUT_VERSIONS" ;
    rdfs:comment "A collection containing multiple ABOUT_VERSION instances..." ;
    rdfs:subClassOf rdf:Bag .

mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "ABOUT_VERSION" ;
    rdfs:comment "Element contained in ABOUT_VERSIONS collection" .
```

**After:**
```ttl
mismo:ABOUT_VERSIONS a rdfs:Class ;
    rdfs:label "ABOUT_VERSIONS" ;
    rdfs:comment "A collection containing multiple ABOUT_VERSION instances..." ;
    rdfs:subClassOf rdf:Bag .

mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "ABOUT_VERSION" ;
    rdfs:comment "Element contained in ABOUT_VERSIONS collection" ;
    rdfs:subClassOf owl:Thing .

# Establish hierarchy: individual class is contained by collection class
mismo:ABOUT_VERSION rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty rdf:type ;
    owl:hasValue mismo:ABOUT_VERSIONS
] .

# Collection relationship property - establishes containment hierarchy
mismo:containsABOUT_VERSION a owl:ObjectProperty ;
    rdfs:label "contains ABOUT_VERSION" ;
    rdfs:comment "Relates ABOUT_VERSIONS to individual ABOUT_VERSION instances" ;
    owl:domain mismo:ABOUT_VERSIONS ;
    owl:range mismo:ABOUT_VERSION ;
    rdfs:subPropertyOf rdf:member .

# Cardinality constraint and hierarchy establishment
mismo:ABOUT_VERSIONS rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty mismo:containsABOUT_VERSION ;
    owl:minCardinality "0"^^xsd:nonNegativeInteger
] .

# Establish that collection contains this type of elements
mismo:ABOUT_VERSIONS rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty rdf:type ;
    owl:someValuesFrom mismo:ABOUT_VERSION
] .
```

### New Method: establish_class_hierarchies()

This method creates additional TTL statements to ensure proper hierarchies:

```ttl
# Hierarchy: ABOUT_VERSIONS contains ABOUT_VERSION
mismo:ABOUT_VERSIONS rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty rdf:member ;
    owl:someValuesFrom mismo:ABOUT_VERSION
] .

# Establish that element class is a member of collection class
mismo:ABOUT_VERSION rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty rdf:type ;
    owl:hasValue mismo:ABOUT_VERSIONS
] .

# Create a containment relationship
mismo:containsABOUT_VERSION a owl:ObjectProperty ;
    rdfs:label "contains ABOUT_VERSION" ;
    rdfs:comment "Relates ABOUT_VERSIONS to individual ABOUT_VERSION instances" ;
    owl:domain mismo:ABOUT_VERSIONS ;
    owl:range mismo:ABOUT_VERSION ;
    rdfs:subPropertyOf rdf:member .
```

## Supported Hierarchy Patterns

The transformation now supports these collection-element pairs:

| Collection Class | Element Class |
|------------------|---------------|
| `ABOUT_VERSIONS` | `ABOUT_VERSION` |
| `DEAL_SETS` | `DEAL_SET` |
| `DOCUMENT_SETS` | `DOCUMENT_SET` |
| `SYSTEM_SIGNATURES` | `SYSTEM_SIGNATURE` |
| `RELATIONSHIPS` | `RELATIONSHIP` |
| `SIGNATURES` | `SIGNATURE` |
| `COLLECTIONS` | `COLLECTION` |
| `VERSIONS` | `VERSION` |
| `SETS` | `SET` |

## WebProtégé Benefits

With these changes, WebProtégé will now be able to:

1. **Visualize class hierarchies** showing containment relationships
2. **Display proper inheritance** between collection and element classes
3. **Show object properties** that connect collections to their elements
4. **Navigate the ontology** using the established containment relationships

## Usage

Run the updated transformation script:

```bash
python transform_mismo_xsd.py --input mismo-3.6/MISMO_3.6.0_B367.xsd --output output/mismo_ontology_hierarchical.ttl
```

The output TTL file will now include:
- Enhanced Pattern 007 transformations with proper hierarchies
- Additional hierarchy establishment statements
- Clear containment relationships between collections and elements

## Technical Details

### Key Changes Made

1. **Enhanced Pattern 007**: Added hierarchy-establishing restrictions and relationships
2. **New method**: `establish_class_hierarchies()` creates additional TTL statements
3. **Integration**: Hierarchy establishment happens after all elements are transformed
4. **RDF compliance**: Uses standard RDF/RDFS/OWL constructs for hierarchies

### OWL Constructs Used

- `owl:Restriction` with `owl:onProperty` and `owl:hasValue`
- `owl:Restriction` with `owl:onProperty` and `owl:someValuesFrom`
- `rdfs:subPropertyOf` to establish property hierarchies
- `rdf:member` as the base property for containment

This approach ensures that the ontology is both semantically correct and visually meaningful in WebProtégé.
