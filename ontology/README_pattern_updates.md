# Pattern 006 and Pattern 007 Updates

## Overview
This document summarizes the updates made to Pattern 006 and Pattern 007 in the MISMO XSD to TTL transformation script (`transform_mismo_xsd.py`) based on the user's requirements for proper class hierarchy visualization in WebProtégé.

## User Requirements
1. **Hierarchy Structure**: `ABOUT_VERSION` should appear as a subclass of `ABOUT_VERSIONS`, which in turn is a subclass of `owl:Thing`
2. **Class Types**: All classes should use `owl:Class` instead of `rdfs:Class` for full OWL expressiveness
3. **Order Handling**: The transformation should handle cases where `ABOUT_VERSION` comes first in the XSD, then `ABOUT_VERSIONS`

## Changes Made

### Pattern 006 (Complex Types with Elements and Attributes)
**Before:**
```python
# Pattern 006: Complex types with elements and attributes should always be rdfs:Class
statements.append(f"""mismo:{name} a rdfs:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} .""")
```

**After:**
```python
# Pattern 006: Complex types with elements and attributes should be owl:Class
statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subClassOf owl:Thing .""")
```

**Changes:**
- Changed from `rdfs:Class` to `owl:Class`
- Added `rdfs:subClassOf owl:Thing` to establish proper hierarchy

### Pattern 007 (Collection Types)
**Before:**
```python
# Collection class - modeled as container class
statements.append(f"""mismo:{name} a rdfs:Class ;
    rdfs:subClassOf rdf:Bag .""")

# Contained class with complex OWL restrictions
statements.append(f"""mismo:{elem_name} a owl:Class ;
    rdfs:subClassOf owl:Thing .""")

# Complex hierarchy establishment with restrictions
statements.append(f"""mismo:{elem_name} rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty rdf:type ;
    owl:hasValue mismo:{name}
] .""")
```

**After:**
```python
# Collection class - modeled as owl:Class
statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:subClassOf owl:Thing .""")

# Contained class with direct hierarchy
statements.append(f"""mismo:{elem_name} a owl:Class ;
    rdfs:subClassOf mismo:{name} .""")
```

**Changes:**
- Changed collection class from `rdfs:Class` to `owl:Class`
- Changed collection superclass from `rdf:Bag` to `owl:Thing`
- Simplified element hierarchy: `mismo:{elem_name} rdfs:subClassOf mismo:{name}`
- Removed complex OWL restrictions in favor of direct subclass relationships

### Pattern 009 (Complex Types with Attributes Only)
**Before:**
```python
statements.append(f"""mismo:{name} a rdfs:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} .""")
```

**After:**
```python
statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subClassOf owl:Thing .""")
```

**Changes:**
- Changed from `rdfs:Class` to `owl:Class`
- Added `rdfs:subClassOf owl:Thing`

## Hierarchy Structure

### Before (Complex OWL Restrictions)
```
owl:Thing
├── mismo:ABOUT_VERSIONS (rdfs:Class, rdfs:subClassOf rdf:Bag)
└── mismo:ABOUT_VERSION (owl:Class, complex restrictions)
```

### After (Direct Subclass Relationships)
```
owl:Thing
└── mismo:ABOUT_VERSIONS (owl:Class, rdfs:subClassOf owl:Thing)
    └── mismo:ABOUT_VERSION (owl:Class, rdfs:subClassOf mismo:ABOUT_VERSIONS)
```

## Order Handling
To address the user's concern about XSD element order, the following mechanisms were added:

### 1. Relationship Tracking
```python
def track_collection_element_relationship(self, collection_name: str, element_name: str):
    """Track collection-element relationships regardless of processing order"""
    if collection_name not in self.collection_element_pairs:
        self.collection_element_pairs[collection_name] = []
    self.collection_element_pairs[collection_name].append(element_name)
    self.pending_hierarchies.append((collection_name, element_name))
```

### 2. Hierarchy Consistency
```python
def ensure_hierarchy_consistency(self) -> List[str]:
    """Ensure all collection-element hierarchies are properly established"""
    statements = []
    for collection_name, element_name in self.pending_hierarchies:
        statements.append(f"""mismo:{element_name} rdfs:subClassOf mismo:{collection_name} .""")
        statements.append(f"""mismo:{collection_name} rdfs:subClassOf owl:Thing .""")
    return statements
```

### 3. Integration in Main Flow
```python
# After establishing class hierarchies
consistency_statements = self.ensure_hierarchy_consistency()
if consistency_statements:
    self.ttl_statements.append("# Hierarchy Consistency")
    self.ttl_statements.extend(consistency_statements)
```

## Benefits

### 1. **Simplified Hierarchy**
- Direct `rdfs:subClassOf` relationships instead of complex OWL restrictions
- Clear parent-child relationships visible in WebProtégé
- Easier to understand and maintain

### 2. **Full OWL Expressiveness**
- All classes use `owl:Class` instead of `rdfs:Class`
- Better support for OWL reasoning and validation
- Consistent with modern ontology standards

### 3. **Order Independence**
- Hierarchy is established regardless of XSD element order
- `ABOUT_VERSION` can come before `ABOUT_VERSIONS` in XSD
- Consistent output regardless of input structure

### 4. **WebProtégé Compatibility**
- Clean class hierarchy visualization
- Proper nesting of subclasses
- No complex restrictions that might confuse the interface

## Example Output

### Collection Class
```ttl
mismo:ABOUT_VERSIONS a owl:Class ;
    rdfs:label "About Versions Collection" ;
    rdfs:comment "A collection containing multiple ABOUT_VERSION instances" ;
    rdfs:subClassOf owl:Thing .
```

### Element Class
```ttl
mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "About Version" ;
    rdfs:comment "Individual ABOUT_VERSION element contained in ABOUT_VERSIONS collection" ;
    rdfs:subClassOf mismo:ABOUT_VERSIONS .
```

### Object Property
```ttl
mismo:containsABOUT_VERSION a owl:ObjectProperty ;
    rdfs:label "contains ABOUT_VERSION" ;
    rdfs:comment "Relates ABOUT_VERSIONS to individual ABOUT_VERSION instances" ;
    owl:domain mismo:ABOUT_VERSIONS ;
    owl:range mismo:ABOUT_VERSION ;
    rdfs:subPropertyOf rdf:member .
```

## Testing
To test the updated transformation:

```bash
cd ontology
python transform_mismo_xsd.py --input mismo-3.6/MISMO_3.6.0_B367.xsd --output output/mismo_ontology_updated.ttl
```

The generated TTL should now show:
- All classes as `owl:Class`
- Proper hierarchy: `owl:Thing` → `ABOUT_VERSIONS` → `ABOUT_VERSION`
- Clean, readable structure suitable for WebProtégé
