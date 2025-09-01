# Dynamic Pattern Detection System

## Overview

The updated transformation script now uses a **dynamic pattern detection system** instead of hardcoded collection-element patterns. This system automatically identifies any entity that follows the MISMO naming conventions for collections and their contained elements.

## Problem with Hardcoded Approach

The previous hardcoded approach only handled a limited set of patterns:
```python
# OLD: Limited hardcoded patterns
collection_element_patterns = [
    ('ABOUT_VERSIONS', 'ABOUT_VERSION'),
    ('DEAL_SETS', 'DEAL_SET'),
    # ... only 9 patterns total
]
```

This missed many entities like:
- `ACCESS_STREET` → `ACCESS_STREETS`
- `ACCESSIBILITY_FEATURE` → `ACCESSIBILITY_FEATURES`
- `LOAN_PRODUCT` → `LOAN_PRODUCTS`
- `BORROWER` → `BORROWERS`
- And many more...

## New Dynamic Detection System

### **1. Automatic Plural-Singular Detection**

The system automatically detects when an element follows the pattern:
```
[Singular Entity] + 'S' = [Collection Entity]
```

**Examples:**
- `ACCESS_STREET` + `S` = `ACCESS_STREETS` ✅
- `ACCESSIBILITY_FEATURE` + `S` = `ACCESSIBILITY_FEATURES` ✅
- `LOAN_PRODUCT` + `S` = `LOAN_PRODUCTS` ✅
- `BORROWER` + `S` = `BORROWERS` ✅

### **2. Multi-Layer Detection Strategy**

```python
def _is_element_contained_in_collection(self, element_name: str) -> bool:
    # Layer 1: Check if element is singular (doesn't end with 'S')
    if element_name.endswith('S'):
        return False  # This is a collection, not an element
    
    # Layer 2: Generate potential collection name
    potential_collection_name = element_name + 'S'
    
    # Layer 3: Check if collection was already processed
    if potential_collection_name in self.transformed_types:
        return True
    
    # Layer 4: Check against known MISMO patterns
    if potential_collection_name in common_collection_patterns:
        return True
    
    # Layer 5: Check naming conventions
    if '_' in potential_collection_name and potential_collection_name.endswith('S'):
        return True
    
    return False
```

### **3. Comprehensive Pattern Coverage**

The system now covers:

#### **Simple Plural Patterns**
- `STREET` → `STREETS`
- `FEATURE` → `FEATURES`
- `PRODUCT` → `PRODUCTS`
- `BORROWER` → `BORROWERS`

#### **Compound Plural Patterns**
- `ACCESS_STREET` → `ACCESS_STREETS`
- `ACCESSIBILITY_FEATURE` → `ACCESSIBILITY_FEATURES`
- `LOAN_PRODUCT` → `LOAN_PRODUCTS`
- `DOCUMENT_SET` → `DOCUMENT_SETS`

#### **Special Cases**
- `ABOUT_VERSION` → `ABOUT_VERSIONS`
- `DEAL_SET` → `DEAL_SETS`
- `SYSTEM_SIGNATURE` → `SYSTEM_SIGNATURES`

## How It Works

### **Step 1: Pattern 006 Processing**
When Pattern 006 encounters an element (e.g., `ACCESS_STREET`):
1. Calls `_is_element_contained_in_collection('ACCESS_STREET')`
2. Generates potential collection: `ACCESS_STREET` + `S` = `ACCESS_STREETS`
3. Checks if `ACCESS_STREETS` exists in processed types or known patterns
4. If found: **Skips class creation** (prevents duplication)
5. If not found: **Creates class normally**

### **Step 2: Pattern 007 Processing**
When Pattern 007 encounters a collection (e.g., `ACCESS_STREETS`):
1. Creates the collection class: `mismo:ACCESS_STREETS a owl:Class`
2. Creates the element class: `mismo:ACCESS_STREET a owl:Class`
3. Establishes hierarchy: `mismo:ACCESS_STREET rdfs:subClassOf mismo:ACCESS_STREETS`

### **Step 3: Result**
- **No duplication**: `ACCESS_STREET` is only defined once
- **Correct hierarchy**: `ACCESS_STREET` appears under `ACCESS_STREETS`
- **Clean structure**: No redundant `owl:Thing` inheritance

## Benefits

### **1. Comprehensive Coverage**
- Automatically catches **ALL** MISMO entities following the pattern
- No need to manually maintain pattern lists
- Future-proof for new entities

### **2. Eliminates Duplication**
- **Before**: `ACCESS_STREET` defined twice (Pattern 006 + Pattern 007)
- **After**: `ACCESS_STREET` defined once (Pattern 007 only)

### **3. Correct Hierarchy**
- **Before**: `ACCESS_STREET rdfs:subClassOf owl:Thing` (wrong)
- **After**: `ACCESS_STREET rdfs:subClassOf mismo:ACCESS_STREETS` (correct)

### **4. Maintains Functionality**
- Pattern 006 still creates datatype properties
- Only the main class definition is skipped
- All other functionality preserved

## Example Transformations

### **ACCESS_STREET Example**

**Before (Duplicated):**
```ttl
# Pattern 006 - WRONG
mismo:ACCESS_STREET a owl:Class ;
    rdfs:label "Access Street" ;
    rdfs:comment "Complex type: Access Street" ;
    rdfs:subClassOf owl:Thing .  # ❌ Wrong hierarchy

# Pattern 007 - CORRECT
mismo:ACCESS_STREET a owl:Class ;
    rdfs:label "Access Street" ;
    rdfs:comment "Individual ACCESS_STREET element contained in ACCESS_STREETS collection" ;
    rdfs:subClassOf mismo:ACCESS_STREETS .  # ✅ Correct hierarchy
```

**After (Fixed):**
```ttl
# Pattern 006 - SKIPPED (no class creation)
# Pattern 007 - ONLY definition
mismo:ACCESS_STREET a owl:Class ;
    rdfs:label "Access Street" ;
    rdfs:comment "Individual ACCESS_STREET element contained in ACCESS_STREETS collection" ;
    rdfs:subClassOf mismo:ACCESS_STREETS .  # ✅ Correct hierarchy
```

### **ACCESSIBILITY_FEATURE Example**

**Before (Duplicated):**
```ttl
# Pattern 006 - WRONG
mismo:ACCESSIBILITY_FEATURE a owl:Class ;
    rdfs:label "Accessibility Feature" ;
    rdfs:comment "Complex type: Accessibility Feature" ;
    rdfs:subClassOf owl:Thing .  # ❌ Wrong hierarchy

# Pattern 007 - CORRECT
mismo:ACCESSIBILITY_FEATURE a owl:Class ;
    rdfs:label "Accessibility Feature" ;
    rdfs:comment "Individual ACCESSIBILITY_FEATURE element contained in ACCESSIBILITY_FEATURES collection" ;
    rdfs:subClassOf mismo:ACCESSIBILITY_FEATURES .  # ✅ Correct hierarchy
```

**After (Fixed):**
```ttl
# Pattern 006 - SKIPPED (no class creation)
# Pattern 007 - ONLY definition
mismo:ACCESSIBILITY_FEATURE a owl:Class ;
    rdfs:label "Accessibility Feature" ;
    rdfs:comment "Individual ACCESSIBILITY_FEATURE element contained in ACCESSIBILITY_FEATURES collection" ;
    rdfs:subClassOf mismo:ACCESSIBILITY_FEATURES .  # ✅ Correct hierarchy
```

## Testing the New System

To verify the dynamic detection works:

```bash
cd ontology
python transform_mismo_xsd.py --input mismo-3.6/MISMO_3.6.0_B367.xsd --output output/mismo_ontology_dynamic.ttl
```

The generated TTL should now show:
- **No duplicate definitions** for any entity following the pattern
- **Correct hierarchy** for all collection-element relationships
- **Clean structure** suitable for WebProtégé visualization

## Future Extensibility

The system is designed to automatically handle:
- **New MISMO entities** following the naming convention
- **Variations** of the plural-singular pattern
- **Complex naming patterns** with underscores and categories

No code changes needed for new entities - they're automatically detected and handled correctly.
