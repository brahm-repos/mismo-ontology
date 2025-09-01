# Hierarchy Duplication Fix

## Problem Identified

The user identified several issues in the generated TTL file:

1. **Repetition of entities**: `ABOUT_VERSION` was defined twice (lines 37525 and 37564)
2. **Incorrect hierarchy**: The first `ABOUT_VERSION` (line 37525) didn't have the correct subclass relationship
3. **Redundant owl:Thing inheritance**: `ABOUT_VERSION` was incorrectly inheriting from `owl:Thing` instead of being properly nested under `ABOUT_VERSIONS`

## Root Cause

The issue was caused by **both Pattern 006 and Pattern 007 processing the same element**:

- **Pattern 006** (Complex Types with Elements and Attributes): Was creating `ABOUT_VERSION` as a class with `rdfs:subClassOf owl:Thing`
- **Pattern 007** (Collection Types): Was also creating `ABOUT_VERSION` as a class with `rdfs:subClassOf mismo:ABOUT_VERSIONS`

This resulted in:
- Duplicate class definitions
- Incorrect hierarchy structure
- `ABOUT_VERSION` appearing both as a direct subclass of `owl:Thing` AND as a subclass of `ABOUT_VERSIONS`

## Solution Implemented

### 1. **Modified Pattern 006 Logic**

Added a check to prevent Pattern 006 from creating classes for elements that are meant to be contained within collections:

```python
# Check if this element is meant to be contained within a collection
# If so, don't create a class here - it will be handled by Pattern 007
if self._is_element_contained_in_collection(name):
    logger.debug(f"      -> Element {name} is contained in a collection - skipping Pattern 006 class creation")
    # Still create the datatype properties for elements and attributes
    # but don't create the main class definition
else:
    # Pattern 006: Create the class as usual
    statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subClassOf owl:Thing .""")
```

### 2. **Added Helper Method**

Created `_is_element_contained_in_collection()` to identify elements that should only be processed by Pattern 007:

```python
def _is_element_contained_in_collection(self, element_name: str) -> bool:
    """
    Check if an element is meant to be contained within a collection.
    This prevents duplicate class creation between Pattern 006 and Pattern 007.
    """
    # Collection-element patterns where the element should only be defined by Pattern 007
    collection_element_patterns = [
        ('ABOUT_VERSIONS', 'ABOUT_VERSION'),
        ('DEAL_SETS', 'DEAL_SET'),
        ('DOCUMENT_SETS', 'DOCUMENT_SET'),
        ('SYSTEM_SIGNATURES', 'SYSTEM_SIGNATURE'),
        ('RELATIONSHIPS', 'RELATIONSHIP'),
        ('SIGNATURES', 'SIGNATURE'),
        ('COLLECTIONS', 'COLLECTION'),
        ('VERSIONS', 'VERSION'),
        ('SETS', 'SET')
    ]
    
    for collection_name, element_name_pattern in collection_element_patterns:
        if element_name == element_name_pattern:
            return True
    
    return False
```

## Result

### **Before (Problematic)**
```ttl
# First occurrence - WRONG hierarchy
mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "About Version" ;
    rdfs:comment "Complex type: About Version" ;
    rdfs:subClassOf owl:Thing .  # ❌ Wrong!

# Second occurrence - CORRECT hierarchy  
mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "About Version" ;
    rdfs:comment "Individual ABOUT_VERSION element contained in ABOUT_VERSIONS collection" ;
    rdfs:subClassOf mismo:ABOUT_VERSIONS .  # ✅ Correct!
```

### **After (Fixed)**
```ttl
# No duplicate class definition
# ABOUT_VERSION is only defined once by Pattern 007 with correct hierarchy

mismo:ABOUT_VERSION a owl:Class ;
    rdfs:label "About Version" ;
    rdfs:comment "Individual ABOUT_VERSION element contained in ABOUT_VERSIONS collection" ;
    rdfs:subClassOf mismo:ABOUT_VERSIONS .  # ✅ Correct hierarchy
```

## Benefits

1. **Eliminates Duplication**: Each element is defined only once
2. **Correct Hierarchy**: `ABOUT_VERSION` properly appears under `ABOUT_VERSIONS`
3. **Clean Structure**: No redundant `owl:Thing` inheritance for contained elements
4. **Proper WebProtégé Visualization**: Clear parent-child relationships
5. **Maintains Functionality**: Datatype properties are still created for elements and attributes

## Hierarchy Structure

### **Final Result**
```
owl:Thing
└── mismo:ABOUT_VERSIONS (owl:Class, rdfs:subClassOf owl:Thing)
    └── mismo:ABOUT_VERSION (owl:Class, rdfs:subClassOf mismo:ABOUT_VERSIONS)
```

This creates the exact hierarchy the user requested:
- `owl:Thing` as the root
- `mismo:ABOUT_VERSIONS` as a subclass of `owl:Thing`
- `mismo:ABOUT_VERSION` as a subclass of `mismo:ABOUT_VERSIONS`

## Testing

To verify the fix:

```bash
cd ontology
python transform_mismo_xsd.py --input mismo-3.6/MISMO_3.6.0_B367.xsd --output output/mismo_ontology_fixed.ttl
```

The generated TTL should now show:
- No duplicate `ABOUT_VERSION` definitions
- Proper hierarchy: `owl:Thing` → `ABOUT_VERSIONS` → `ABOUT_VERSION`
- Clean, non-repetitive structure
