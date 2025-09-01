#!/usr/bin/env python3
"""
MISMO XSD to RDF/RDFS/OWL TTL Transformer

This script transforms MISMO_3.6.0_B367.xsd into RDF/RDFS/OWL in turtle format
following the specified transformation patterns.

Patterns implemented:
- Pattern 001: Simple types with restrictions
- Pattern 002: Enumerations with values
- Pattern 004: Complex types with simple content and attributes
- Pattern 005: Extension patterns (IGNORED - no transformation)
- Pattern 006: Complex types with elements and attributes
- Pattern 007: Collection types (containing multiple instances)
- Pattern 009: Complex types with only attributes

Usage:
    python transform_mismo_xsd.py --input MISMO_3.6.0_B367.xsd --output mismo_ontology.ttl
"""

import xml.etree.ElementTree as ET
import re
import argparse
import sys
import os
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MISMOXSDTransformer:
    """Transforms MISMO XSD to RDF/RDFS/OWL TTL format."""
    
    def __init__(self):
        """Initialize the transformer."""
        self.transformed_types = set()
        self.ttl_statements = []
        # Define XML namespaces
        self.namespaces = {
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        self.collection_element_pairs: Dict[str, List[str]] = {}
        self.pending_hierarchies: List[tuple[str, str]] = []
        self.complex_type_info: Dict[str, Dict[str, Any]] = {}
        self.hierarchy_data: Dict[str, List[Dict[str, str]]] = {}  # {parent_type: [contained_types]}
        
    def add_prefixes(self):
        """Add standard prefixes to TTL output."""
        prefixes = [
            "@prefix mismo: <http://www.mismo.org/residential/2009/schemas#> .",
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            "",
            "# MISMO XSD to RDF/RDFS/OWL Transformation",
            "# Generated from MISMO_3.6.0_B367.xsd",
            ""
        ]
        self.ttl_statements.extend(prefixes)
    
    def analyze_xsd_structure(self):
        """
        Step 1: Traverse the entire XSD and analyze complex types.
        Build comprehensive data about complex elements and their types.
        """
        logger.info("=== Step 1: Analyzing XSD Structure ===")
        
        if not self._xsd_root:
            logger.error("XSD root not available for analysis")
            return False
            
        # Analyze all complex types
        for complex_type in self._xsd_root.findall('.//xsd:complexType', self.namespaces):
            type_name = complex_type.get('name')
            if not type_name:
                continue
                
            # Get documentation
            doc = complex_type.find('.//xsd:documentation', self.namespaces)
            comment = doc.text if doc is not None else f"Complex type: {type_name}"
            
            # All complex types are owl:Class
            self.complex_type_info[type_name] = {
                'is_owl_class': True,
                'comment': comment,
                'element': complex_type
            }
            
            logger.debug(f"  -> Analyzed complex type: {type_name} (owl:Class)")
        
        # Analyze all simple types
        for simple_type in self._xsd_root.findall('.//xsd:simpleType', self.namespaces):
            type_name = simple_type.get('name')
            if not type_name:
                continue
                
            # Get documentation
            doc = simple_type.find('.//xsd:documentation', self.namespaces)
            comment = doc.text if doc is not None else f"Simple type: {type_name}"
            
            # Simple types are rdfs:Datatype
            self.complex_type_info[type_name] = {
                'is_owl_class': False,
                'comment': comment,
                'element': simple_type
            }
            
            logger.debug(f"  -> Analyzed simple type: {type_name} (rdfs:Datatype)")
        
        logger.info(f"  -> Analyzed {len(self.complex_type_info)} types total")
        return True
        
    def build_hierarchy_data(self):
        """
        Step 2: Build data structure showing which complex types contain other complex types.
        This creates the parent-child relationships for hierarchy building.
        """
        logger.info("=== Step 2: Building Hierarchy Data ===")
        
        for type_name, type_info in self.complex_type_info.items():
            if not type_info['is_owl_class']:
                continue  # Skip simple types
                
            complex_type = type_info['element']
            contained_types = []
            
            # Find all element references in this complex type
            sequence = complex_type.find('.//xsd:sequence', self.namespaces)
            if sequence is not None:
                for elem in sequence.findall('.//xsd:element', self.namespaces):
                    elem_name = elem.get('name')
                    elem_type = elem.get('type')
                    
                    if elem_name and elem_type:
                        # Check if the referenced type is a complex type (owl:Class)
                        if elem_type in self.complex_type_info:
                            if self.complex_type_info[elem_type]['is_owl_class']:
                                contained_types.append({
                                    'name': elem_name,
                                    'type': elem_type,
                                    'max_occurs': elem.get('maxOccurs', '1')
                                })
                                logger.debug(f"  -> {type_name} contains {elem_name} (type: {elem_type})")
            
            if contained_types:
                self.hierarchy_data[type_name] = contained_types
                logger.debug(f"  -> {type_name}: {len(contained_types)} contained complex types")
        
        logger.info(f"  -> Built hierarchy data for {len(self.hierarchy_data)} parent types")
        return True
    
    def get_parent_types(self, element_name: str) -> List[str]:
        """
        Find ALL parent types for a given element based on hierarchy data.
        Returns a list of parent type names (supports multiple inheritance).
        """
        parents = []
        for parent_type, contained_types in self.hierarchy_data.items():
            for contained in contained_types:
                if contained['name'] == element_name:
                    if parent_type not in parents:
                        parents.append(parent_type)
        return parents

    def _determine_collection_parents(self, collection_name: str) -> List[str]:
        """
        Dynamically determine ALL parent types for a collection based on hierarchy data.
        This handles multiple inheritance scenarios where a collection appears in multiple contexts.
        """
        parents = []
        
        # Check if this collection is referenced by other complex types
        for parent_type, contained_types in self.hierarchy_data.items():
            for contained in contained_types:
                if contained['name'] == collection_name:
                    # This collection is contained by another type, so that's a parent
                    logger.debug(f"    -> {collection_name}: Found parent {parent_type} from hierarchy data")
                    if parent_type not in parents:
                        parents.append(parent_type)
        
        # If no parents found in hierarchy, check if it's a top-level collection
        # that should inherit from a root container (like MESSAGE)
        if self._is_top_level_collection(collection_name):
            root_container = self._find_root_container()
            if root_container:
                logger.debug(f"    -> {collection_name}: Top-level collection, inheriting from {root_container}")
                if root_container not in parents:
                    parents.append(root_container)
        
        logger.debug(f"    -> {collection_name}: Found {len(parents)} parents: {parents}")
        return parents

    def _is_top_level_collection(self, collection_name: str) -> bool:
        """
        Dynamically determine if a collection is a top-level collection.
        This replaces hardcoded logic with dynamic analysis.
        """
        # A collection is considered top-level if it's not contained by any other type
        # in the hierarchy data, meaning it's referenced at the root level
        for parent_type, contained_types in self.hierarchy_data.items():
            for contained in contained_types:
                if contained['name'] == collection_name:
                    # This collection is contained by another type, so it's NOT top-level
                    return False
        
        # If we reach here, the collection is not contained by any other type
        # This could mean it's truly top-level OR it's not properly connected in the XSD
        logger.debug(f"    -> {collection_name}: Appears to be top-level (not contained by other types)")
        return True

    def _find_root_container(self) -> str:
        """
        Dynamically find the root container type from the hierarchy data.
        This replaces hardcoded MESSAGE fallback with dynamic analysis.
        """
        # Look for a type that contains many other types (root container)
        # Root containers typically contain many different types
        potential_roots = []
        for type_name, contained_types in self.hierarchy_data.items():
            if len(contained_types) > 5:  # Root container typically contains many types
                potential_roots.append((type_name, len(contained_types)))
                logger.debug(f"    -> Found potential root container: {type_name} with {len(contained_types)} contained types")
        
        if potential_roots:
            # Sort by number of contained types (most contained = most likely root)
            potential_roots.sort(key=lambda x: x[1], reverse=True)
            root_container = potential_roots[0][0]
            logger.debug(f"    -> Selected root container: {root_container} with {potential_roots[0][1]} contained types")
            return root_container
        
        # If no clear root container found, return None
        # This will cause collections to inherit from owl:Thing instead of a hardcoded fallback
        logger.debug(f"    -> No clear root container found, collections will inherit from owl:Thing")
        return None

    def _format_type_reference(self, type_name: str) -> str:
        """Format a type reference with proper namespace prefix."""
        if not type_name:
            return type_name
        
        # If it already has a namespace prefix (like xsd:string), return as is
        if ':' in type_name:
            logger.debug(f"      -> Type reference '{type_name}' already has namespace prefix")
            return type_name
        
        # If it's a MISMO type without prefix, add the mismo: prefix
        formatted_type = f"mismo:{type_name}"
        logger.debug(f"      -> Formatting type reference '{type_name}' -> '{formatted_type}'")
        return formatted_type
    
    def _format_comment_for_ttl(self, comment: str) -> str:
        """
        Format a comment string for TTL output, handling quotes and newlines properly.
        
        Args:
            comment: The comment text that may contain quotes and newlines
            
        Returns:
            Formatted comment string suitable for TTL
        """
        if not comment:
            return ""
        
        # Clean up the comment text
        comment = comment.strip()
        
        # Always escape quotes in the content first
        escaped_comment = comment.replace('"', '\\"')
        
        # If comment contains newlines, use triple-quoted string format
        if '\n' in comment:
            return f'"""\n{escaped_comment}\n"""'
        else:
            # Single line comment, use regular quotes with escaped content
            return f'"{escaped_comment}"'
    
    def transform_simple_type(self, element: ET.Element) -> List[str]:
        """
        Transform simple type (Pattern 001).
        
        Args:
            element: XSD simpleType element
            
        Returns:
            List of TTL statements
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Check if it's a restriction
        restriction = element.find('.//xsd:restriction', self.namespaces)
        if restriction is not None:
            base = restriction.get('base')
            if base:
                # Handle string restrictions
                if base == 'xsd:string':
                    max_length = restriction.find('.//xsd:maxLength', self.namespaces)
                    if max_length is not None:
                        max_value = max_length.get('value')
                        statements.append(f"""mismo:{name} a rdfs:Datatype ;
    rdfs:label "{name}" ;
    owl:equivalentClass [ a rdfs:Datatype ;
            owl:onDatatype xsd:string ;
            owl:withRestrictions ( [ xsd:maxLength "{max_value}"^^xsd:nonNegativeInteger ] ) ] .""")
                    else:
                        statements.append(f"""mismo:{name} a rdfs:Datatype ;
    rdfs:label "{name}" ;
    rdfs:subClassOf {self._format_type_reference(base)} .""")
                else:
                    statements.append(f"""mismo:{name} a rdfs:Datatype ;
    rdfs:label "{name}" ;
    rdfs:subClassOf {self._format_type_reference(base)} .""")
        
        return statements
    
    def transform_enumeration(self, element: ET.Element) -> List[str]:
        """
        Transform enumeration type (Pattern 002).
        
        Args:
            element: XSD simpleType element with enumerations
            
        Returns:
            List of TTL statements
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Check if it's a restriction with base
        restriction = element.find('.//xsd:restriction', self.namespaces)
        if restriction is not None:
            base = restriction.get('base')
            if base:
                # Base type
                statements.append(f"""mismo:{name} a rdfs:Datatype ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(f"Base datatype for {name} enumerations")} ;
    rdfs:subClassOf {self._format_type_reference(base)} .""")
                
                # Enumeration values
                for enum in restriction.findall('.//xsd:enumeration', self.namespaces):
                    enum_value = enum.get('value')
                    if enum_value:
                        # Get documentation if available
                        doc = enum.find('.//xsd:documentation', self.namespaces)
                        comment = doc.text if doc is not None else f"Enumeration value: {enum_value}"
                        
                        statements.append(f"""mismo:{enum_value} a rdf:Property ;
    rdfs:label "{enum_value}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subPropertyOf mismo:{name} .""")
        
        return statements
    
    def transform_complex_type_simple_content(self, element: ET.Element) -> List[str]:
        """
        Transform complex type with simple content (Pattern 004).
        
        Args:
            element: XSD complexType element with simpleContent
            
        Returns:
            List of TTL statements
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Get documentation
        doc = element.find('.//xsd:documentation', self.namespaces)
        comment = doc.text if doc is not None else f"Complex type: {name}"
        
        # Find simple content extension
        simple_content = element.find('.//xsd:simpleContent', self.namespaces)
        if simple_content is not None:
            extension = simple_content.find('.//xsd:extension', self.namespaces)
            if extension is not None:
                base = extension.get('base')
                if base:
                    # Base type
                    statements.append(f"""mismo:{name} a rdfs:Datatype ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subClassOf {self._format_type_reference(base)} .""")
                    
                    # Handle all attributes (ignorable ones are filtered out at element level)
                    for attr in extension.findall('.//xsd:attribute', self.namespaces):
                        attr_name = attr.get('name')
                        attr_type = attr.get('type')
                        if attr_name and attr_type:
                            # Convert attribute name to camelCase for property
                            prop_name = self.to_camel_case(attr_name)
                            
                            # Get attribute documentation
                            attr_doc = attr.find('.//xsd:documentation', self.namespaces)
                            attr_comment = attr_doc.text if attr_doc is not None else f"Attribute: {attr_name}"
                            
                            logger.debug(f"    -> Processing attribute: {attr_name} -> {prop_name}")
                            
                            statements.append(f"""mismo:{prop_name} a owl:DatatypeProperty ;
    rdfs:label "{prop_name}" ;
    rdfs:comment {self._format_comment_for_ttl(attr_comment)} ;
    rdfs:domain mismo:{name} ;
    rdfs:range {self._format_type_reference(attr_type)} .""")
        
        return statements
    
    def transform_complex_type_elements(self, element: ET.Element) -> List[str]:
        """
        Transform complex type with elements and attributes (Pattern 006).
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Get documentation
        doc = element.find('.//xsd:documentation', self.namespaces)
        comment = doc.text if doc is not None else f"Complex type: {name}"
        
        # Pattern 006: Complex types with elements and attributes should be owl:Class
        # Use dynamic hierarchy to determine inheritance
        logger.debug(f"      -> Main class {name} follows Pattern 006 -> owl:Class")

        # Find parent types dynamically (supports multiple inheritance)
        parent_types = self.get_parent_types(name)
        if parent_types:
            # Multiple inheritance: create multiple rdfs:subClassOf statements
            statements.append(f"""mismo:{name} a owl:Class ;
            rdfs:label "{name}" ;
            rdfs:comment {self._format_comment_for_ttl(comment)} .""")
            
            # Add each parent as a separate rdfs:subClassOf statement
            for parent_type in parent_types:
                statements.append(f"mismo:{name} rdfs:subClassOf mismo:{parent_type} .")
                logger.debug(f"      -> {name} inherits from {parent_type}")
        else:
            # No parent found, inherit from owl:Thing
            statements.append(f"""mismo:{name} a owl:Class ;
            rdfs:label "{name}" ;
            rdfs:comment {self._format_comment_for_ttl(comment)} ;
            rdfs:subClassOf owl:Thing .""")
            logger.debug(f"      -> {name} inherits from owl:Thing")

        
        # Handle elements (ignore EXTENSION elements as per Pattern 006)
        sequence = element.find('.//xsd:sequence', self.namespaces)
        if sequence is not None:
            for elem in sequence.findall('.//xsd:element', self.namespaces):
                elem_name = elem.get('name')
                elem_type = elem.get('type')
                
                # Pattern 006: Ignore EXTENSION elements
                if self._should_ignore_element_name(elem_name):
                    logger.debug(f"    -> Testing extension element: {elem_name} (type: {elem_type})")
                    continue
                
                if elem_name and elem_type:
                    # Get element documentation
                    elem_doc = elem.find('.//xsd:documentation', self.namespaces)
                    elem_comment = elem_doc.text if elem_doc is not None else f"Element: {elem_name}"
                    
                    logger.debug(f"    -> Processing element: {elem_name} -> {elem_type}")
                    
                    # Pattern 006: All elements within complex types should be owl:DatatypeProperty
                    # This follows the specification where elements are properties of the main class
                    logger.debug(f"      -> Element {elem_name} as owl:DatatypeProperty with domain {name}")
                    statements.append(f"""mismo:{elem_name} a owl:DatatypeProperty ;
    rdfs:label "{elem_name}" ;
    rdfs:comment {self._format_comment_for_ttl(elem_comment)} ;
    rdfs:domain mismo:{name} ;
    rdfs:range {self._format_type_reference(elem_type)} .""")
        
        # Handle attributes
        for attr in element.findall('.//xsd:attribute', self.namespaces):
            attr_name = attr.get('name')
            attr_type = attr.get('type')
            if attr_name and attr_type:
                # Get attribute documentation
                attr_doc = attr.find('.//xsd:documentation', self.namespaces)
                attr_comment = attr_doc.text if attr_doc is not None else f"Attribute: {attr_name}"
                
                # Pattern 006: Attributes should be owl:DatatypeProperty with proper domain and range
                statements.append(f"""mismo:{attr_name} a owl:DatatypeProperty ;
    rdfs:label "{attr_name}" ;
    rdfs:comment {self._format_comment_for_ttl(attr_comment)} ;
    rdfs:domain mismo:{name} ;
    rdfs:range {self._format_type_reference(attr_type)} .""")
        
        return statements
    
    def transform_collection_type(self, element: ET.Element) -> List[str]:
        """
        Transform collection type (Pattern 007) using dynamic hierarchy data.

        Args:
            element: XSD complexType element representing a collection
            
        Returns:
            List of TTL statements
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Get documentation
        doc = element.find('.//xsd:documentation', self.namespaces)
        comment = doc.text if doc is not None else f"Collection type: {name}"

        # Use dynamic hierarchy data to find contained complex types
        if name not in self.hierarchy_data:
            logger.debug(f"    -> {name}: No hierarchy data found, skipping Pattern 007")
            return statements
            
        contained_types = self.hierarchy_data[name]
        has_unbounded_elements = False

        for contained in contained_types:
            elem_name = contained['name']
            elem_type = contained['type']
            max_occurs = contained['max_occurs']
            
            # Check if this is an unbounded element (collection indicator)
            if max_occurs == 'unbounded':
                has_unbounded_elements = True
                
                # Pattern 007: Ignore EXTENSION elements
                if self._should_ignore_element_name(elem_name):
                    logger.debug(f"    -> Skipping extension element: {elem_name} (type: {elem_type})")
                    continue
                
                # Collection class - modeled as owl:Class (Pattern 007 requirement)
                # Use dynamic hierarchy to determine inheritance (supports multiple parents)
                parent_types = self._determine_collection_parents(name)
                if parent_types:
                    # Multiple inheritance: create multiple rdfs:subClassOf statements
                    statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(f"A collection containing multiple {elem_name} instances. {comment}")} .""")
                    
                    # Add each parent as a separate rdfs:subClassOf statement
                    for parent_type in parent_types:
                        statements.append(f"mismo:{name} rdfs:subClassOf mismo:{parent_type} .")
                        logger.debug(f"      -> {name} inherits from {parent_type}")
                else:
                    statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(f"A collection containing multiple {elem_name} instances. {comment}")} ;
    rdfs:subClassOf owl:Thing .""")
                    logger.debug(f"      -> {name} inherits from owl:Thing")
                
                # Contained class - always owl:Class with proper hierarchy (Pattern 007 requirement)
                statements.append(f"""mismo:{elem_name} a owl:Class ;
        rdfs:label "{elem_name}" ;
        rdfs:comment {self._format_comment_for_ttl(f"Individual {elem_name} element contained in {name} collection")} ;
        rdfs:subClassOf mismo:{name} .""")
                
                # Collection relationship property - establishes containment hierarchy
                statements.append(f"""mismo:contains{elem_name} a owl:ObjectProperty ;
        rdfs:label "contains {elem_name}" ;
        rdfs:comment {self._format_comment_for_ttl(f"Relates {name} to individual {elem_name} instances")} ;
        owl:domain mismo:{name} ;
        owl:range mismo:{elem_name} ;
        rdfs:subPropertyOf rdf:member .""")
                
                # Track the collection-element relationship for hierarchy consistency
                self.track_collection_element_relationship(name, elem_name)
                
                break

        # Special case: MESSAGE is a root container that should always be generated
        # even if it doesn't contain maxOccurs="unbounded" elements
        if name == 'MESSAGE' and not has_unbounded_elements:
            logger.debug(f"    -> {name}: Special case - root container without unbounded elements")
            statements.append(f"""mismo:{name} a owl:Class ;
        rdfs:label "{name}" ;
        rdfs:comment {self._format_comment_for_ttl(f"Root container for MISMO message. {comment}")} ;
        rdfs:subClassOf owl:Thing .""")

        # Use dynamic hierarchy to determine if this should be a collection class
        # even if it doesn't contain maxOccurs="unbounded" elements
        elif not has_unbounded_elements:
            # Check if this should be a collection based on dynamic hierarchy
            parent_types = self._determine_collection_parents(name)
            if parent_types:
                # Multiple inheritance: create multiple rdfs:subClassOf statements
                statements.append(f"""mismo:{name} a owl:Class ;
        rdfs:label "{name}" ;
        rdfs:comment {self._format_comment_for_ttl(f"Collection class with multiple inheritance. {comment}")} .""")
                
                # Add each parent as a separate rdfs:subClassOf statement
                for parent_type in parent_types:
                    statements.append(f"mismo:{name} rdfs:subClassOf mismo:{parent_type} .")
                    logger.debug(f"      -> {name} inherits from {parent_type}")
            else:
                logger.debug(f"    -> {name}: No parent found, inheriting from owl:Thing")
                statements.append(f"""mismo:{name} a owl:Class ;
        rdfs:label "{name}" ;
        rdfs:comment {self._format_comment_for_ttl(f"Collection class. {comment}")} ;
        rdfs:subClassOf owl:Thing .""")

        return statements

    def transform_complex_type_attributes_only(self, element: ET.Element) -> List[str]:
        """
        Transform complex type with only attributes (Pattern 009).
        
        Args:
            element: XSD complexType element with only attributes
            
        Returns:
            List of TTL statements
        """
        statements = []
        name = element.get('name')
        if not name:
            return statements
            
        # Get documentation
        doc = element.find('.//xsd:documentation', self.namespaces)
        comment = doc.text if doc is not None else f"Complex type: {name}"
        
        # Main class - attributes-only types are typically simple containers
        statements.append(f"""mismo:{name} a owl:Class ;
    rdfs:label "{name}" ;
    rdfs:comment {self._format_comment_for_ttl(comment)} ;
    rdfs:subClassOf owl:Thing .""")
        
        # Handle attributes
        for attr in element.findall('.//xsd:attribute', self.namespaces):
            attr_name = attr.get('name')
            attr_type = attr.get('type')
            if attr_name and attr_type:
                # Get attribute documentation
                attr_doc = attr.find('.//xsd:documentation', self.namespaces)
                attr_comment = attr_doc.text if attr_doc is not None else f"Attribute: {attr_name}"
                
                # Pattern 009: Attributes should be owl:DatatypeProperty with proper domain and range
                statements.append(f"""mismo:{attr_name} a owl:DatatypeProperty ;
    rdfs:label "{attr_name}" ;
    rdfs:comment {self._format_comment_for_ttl(attr_comment)} ;
    rdfs:domain mismo:{name} ;
    rdfs:range {self._format_type_reference(attr_type)} .""")
        
        return statements
    
    def establish_class_hierarchies(self) -> List[str]:
        """
        Establish proper class hierarchies between collection classes and their contained elements.
        This ensures that WebProtégé can properly visualize the class structure.
        
        Returns:
            List of TTL statements establishing hierarchies
        """
        statements = []
        
        # Dynamic collection pattern detection: Look for all processed types that follow collection-element patterns
        # This is more comprehensive than hardcoded patterns and will catch all MISMO entities
        
        # Group processed types by their collection-element relationships
        collection_element_pairs = []
        
        for processed_type in self.transformed_types:
            # Check if this is a collection (ends with 'S')
            if processed_type.endswith('S'):
                # Find the corresponding singular element by removing the 'S'
                potential_element = processed_type[:-1]
                
                # Check if the singular element was also processed
                if potential_element in self.transformed_types:
                    collection_element_pairs.append((processed_type, potential_element))
                    logger.debug(f"      -> Detected collection-element pair: {processed_type} -> {potential_element}")
        
        # Also check for common MISMO patterns that might not follow the simple +S rule
        common_patterns = [
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
        
        for collection_name, element_name in common_patterns:
            if collection_name in self.transformed_types and element_name in self.transformed_types:
                if (collection_name, element_name) not in collection_element_pairs:
                    collection_element_pairs.append((collection_name, element_name))
                    logger.debug(f"      -> Added common pattern: {collection_name} -> {element_name}")
        
        for collection_name, element_name in collection_element_pairs:
            # Note: The hierarchy is already established in Pattern 006 and Pattern 007
            # where elements are defined as subclasses of their collections
            # This method now just adds additional containment relationships
            
            # Create a containment relationship property
            statements.append(f"""mismo:contains{element_name} a owl:ObjectProperty ;
    rdfs:label "contains {element_name}" ;
    rdfs:comment "Relates {collection_name} to individual {element_name} instances" ;
    owl:domain mismo:{collection_name} ;
    owl:range mismo:{element_name} ;
    rdfs:subPropertyOf rdf:member .""")
            
            # Add cardinality constraints to show that collections can contain multiple elements
            statements.append(f"""mismo:{collection_name} rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty mismo:contains{element_name} ;
    owl:minCardinality "0"^^xsd:nonNegativeInteger
] .""")
        
        return statements
    
    def track_collection_element_relationship(self, collection_name: str, element_name: str):
        """
        Track collection-element relationships to ensure proper hierarchy establishment
        regardless of the order they appear in the XSD.
        
        Args:
            collection_name: Name of the collection class
            element_name: Name of the element class
        """
        if collection_name not in self.collection_element_pairs:
            self.collection_element_pairs[collection_name] = []
        self.collection_element_pairs[collection_name].append(element_name)
        
        # Store the relationship for later hierarchy establishment
        self.pending_hierarchies.append((collection_name, element_name))
        logger.debug(f"Tracked collection-element relationship: {collection_name} -> {element_name}")
    
    def ensure_hierarchy_consistency(self) -> List[str]:
        """
        Ensure that all collection-element hierarchies are properly established
        regardless of the order they were processed in the XSD.
        
        Returns:
            List of TTL statements to ensure hierarchy consistency
        """
        statements = []
        
        for collection_name, element_name in self.pending_hierarchies:
            # Ensure the hierarchy is properly established
            # This handles cases where elements are processed before collections
            statements.append(f"""# Ensure hierarchy consistency: {element_name} is subclass of {collection_name}
mismo:{element_name} rdfs:subClassOf mismo:{collection_name} .""")
            
            # Use dynamic hierarchy to determine parents (supports multiple inheritance)
            parent_types = self._determine_collection_parents(collection_name)
            if parent_types:
                # Multiple inheritance: add each parent as a separate rdfs:subClassOf statement
                for parent_type in parent_types:
                    statements.append(f"""# Ensure collection hierarchy: {collection_name} is subclass of {parent_type}
mismo:{collection_name} rdfs:subClassOf mismo:{parent_type} .""")
            else:
                statements.append(f"""# Ensure collection hierarchy: {collection_name} is subclass of owl:Thing
mismo:{collection_name} rdfs:subClassOf owl:Thing .""")
        
        return statements
    
    def to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        if not name:
            return name
        words = name.split('_')
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def should_ignore_element(self, element: ET.Element) -> bool:
        """Check if element should be ignored based on patterns."""
        name = element.get('name', 'UNNAMED')
        
        # Pattern 005: Check for extension elements (ends with 'EXTENSION')
        if element.tag.endswith('EXTENSION'):
            logger.debug(f"    -> {name}: IGNORED - Pattern 005: ends with 'EXTENSION'")
            return True
        
        # Check for MISMO_BASE type (contains <xsd:any> element)
        if element.find('.//xsd:any', self.namespaces) is not None:
            logger.debug(f"    -> {name}: IGNORED - contains <xsd:any> element")
            return True
        
        # Check for extension patterns in complex types
        if element.tag.endswith('complexType'):
            # Check if it's an extension type (Pattern 005)
            sequence = element.find('.//xsd:sequence', self.namespaces)
            if sequence is not None:
                # Check if all elements are extension-related
                all_extension_elements = True
                for elem in sequence.findall('.//xsd:element', self.namespaces):
                    elem_type = elem.get('type', '')
                    if elem_type and not self._is_extension_type(elem_type):
                        all_extension_elements = False
                        break
                
                if all_extension_elements:
                    logger.debug(f"    -> {name}: IGNORED - Pattern 005: all elements are extension types")
                    return True
            
            # For complex types with simple content, be more selective
            simple_content = element.find('.//xsd:simpleContent', self.namespaces)
            if simple_content is not None:
                extension = simple_content.find('.//xsd:extension', self.namespaces)
                if extension is not None:
                    # Check if there are any non-ignorable attributes
                    non_ignorable_attrs = []
                    for attr in extension.findall('.//xsd:attribute', self.namespaces):
                        attr_name = attr.get('name')
                        if attr_name:  # All attributes are considered non-ignorable for now
                            non_ignorable_attrs.append(attr_name)
                    
                    # If there are non-ignorable attributes, don't ignore the element
                    if non_ignorable_attrs:
                        logger.debug(f"    -> {name}: NOT ignored - has non-ignorable attributes: {non_ignorable_attrs}")
                        return False
        
        # For other cases, check for attribute groups that should be ignored
        # But only ignore if the element has no other useful content
        has_ignorable_groups = False
        for attr_group in element.findall('.//xsd:attributeGroup', self.namespaces):
            ref = attr_group.get('ref')
            if ref and ('xlink:' in ref or 'AttributeExtension' in ref):
                has_ignorable_groups = True
                break
        
        # Only ignore if there are ignorable groups AND no other useful content
        if has_ignorable_groups:
            # Check if there are any elements or attributes
            has_elements = element.find('.//xsd:element', self.namespaces) is not None
            has_attributes = element.find('.//xsd:attribute', self.namespaces) is not None
            has_simple_content = element.find('.//xsd:simpleContent', self.namespaces) is not None
            
            if not has_elements and not has_attributes and not has_simple_content:
                logger.debug(f"    -> {name}: IGNORED - only contains ignorable attribute groups")
                return True
            else:
                logger.debug(f"    -> {name}: NOT ignored - has ignorable groups but also useful content")
                return False
        
        logger.debug(f"    -> {name}: NOT ignored - will be processed")
        return False
    
    def _is_extension_type(self, type_name: str) -> bool:
        """Check if a type name represents an extension type that should be ignored."""
        # Pattern 005: Check for extension-related types
        extension_indicators = [
            'EXTENSION',
            'MISMO_BASE',
            'OTHER_BASE'
        ]
        
        for indicator in extension_indicators:
            if indicator in type_name:
                return True
        
        return False
    
    def _should_ignore_element_name(self, element_name: str) -> bool:
        """Check if an element name should be ignored based on extension patterns."""
        # Pattern 006: Ignore EXTENSION elements
        if element_name == 'EXTENSION':
            return True
        
        # Pattern 005: Ignore elements ending with EXTENSION
        if element_name.endswith('EXTENSION'):
            return True
        
        return False
    
    def _is_extension_pattern(self, element: ET.Element) -> bool:
        """Check if an element follows Pattern 005 (extension pattern)."""
        name = element.get('name', '')
        
        # Pattern 005: Check for elements ending with 'EXTENSION'
        if name.endswith('EXTENSION'):
            return True
        
        # Pattern 005: Check for complex types with only extension-related elements
        if element.tag.endswith('complexType'):
            sequence = element.find('.//xsd:sequence', self.namespaces)
            if sequence is not None:
                # Check if all elements are extension-related
                all_extension_elements = True
                for elem in sequence.findall('.//xsd:element', self.namespaces):
                    elem_type = elem.get('type', '')
                    if elem_type and not self._is_extension_type(elem_type):
                        all_extension_elements = False
                        break
                
                if all_extension_elements:
                    return True
        
        return False
    
    def _is_complex_type_reference(self, type_name: str) -> bool:
        """Check if a type reference represents a complex type that should be owl:Class."""
        # Remove namespace prefix if present
        if ':' in type_name:
            type_name = type_name.split(':', 1)[1]
        
        # Check if this type is already defined as a complex type in our transformed types
        # This is a heuristic - in a full implementation, you might want to check the actual XSD
        # For now, we'll assume types ending with certain patterns are complex types
        complex_type_indicators = [
            'VERSION', 'IDENTIFIER', 'RELATIONSHIP', 'DOCUMENT', 'LOAN', 'BORROWER',
            'ABOUT_VERSION', 'MISMOIdentifier', 'MISMODate', 'MISMODatetime'
        ]
        
        for indicator in complex_type_indicators:
            if indicator in type_name:
                return True
        
        return False
    
    def _is_element_contained_in_collection(self, element_name: str) -> bool:
        """
        Check if an element is meant to be contained within a collection.
        This prevents duplicate class creation between Pattern 006 and Pattern 007.
        
        Args:
            element_name: Name of the element to check
            
        Returns:
            True if the element is contained in a collection, False otherwise
        """
        # Dynamic pattern detection: Look for singular forms that have corresponding plural collections
        # Pattern: If element_name is singular, check if there's a corresponding plural form ending with 'S'
        
        # Check if this element name is singular (doesn't end with 'S')
        if element_name.endswith('S'):
            return False  # This is a collection, not an element
        
        # Generate the potential collection name by adding 'S'
        potential_collection_name = element_name + 'S'
        
        # Check if we've already seen this collection name in our transformed types
        # or if it's a known collection pattern
        if potential_collection_name in self.transformed_types:
            logger.debug(f"      -> Element {element_name} is contained in collection {potential_collection_name} (already processed)")
            return True
        
        # Also check for common MISMO collection patterns that might not be processed yet
        common_collection_patterns = [
            'ABOUT_VERSIONS', 'DEAL_SETS', 'DOCUMENT_SETS', 'SYSTEM_SIGNATURES',
            'RELATIONSHIPS', 'SIGNATURES', 'COLLECTIONS', 'VERSIONS', 'SETS',
            'ACCESS_STREETS', 'ACCESSIBILITY_FEATURES', 'LOAN_PRODUCTS', 'BORROWERS',
            'PROPERTIES', 'ADDRESSES', 'PHONES', 'EMAILS', 'IDENTIFIERS',
            'DOCUMENTS', 'LOANS', 'TRANSACTIONS', 'PAYMENTS', 'ACCOUNTS'
        ]
        
        if potential_collection_name in common_collection_patterns:
            logger.debug(f"      -> Element {element_name} is contained in known collection {potential_collection_name}")
            return True
        
        # Check if the potential collection name follows common MISMO naming conventions
        # Many MISMO collections follow the pattern: [CATEGORY]_[TYPE]S
        if '_' in potential_collection_name and potential_collection_name.endswith('S'):
            logger.debug(f"      -> Element {element_name} likely contained in collection {potential_collection_name} (naming convention)")
            return True
        
        # Check for special cases where elements might be contained in collections that don't follow +S pattern
        # For example, MESSAGE might contain MESSAGE_ITEM elements
        special_collection_patterns = [
            ('MESSAGE', 'MESSAGE_ITEM'),
            ('MESSAGE', 'MESSAGE_HEADER'),
            ('MESSAGE', 'MESSAGE_BODY'),
            ('MESSAGE', 'MESSAGE_FOOTER'),
            ('MESSAGE', 'MESSAGE_ATTACHMENT'),
            ('MESSAGE', 'MESSAGE_SIGNATURE'),
            ('MESSAGE', 'MESSAGE_EXTENSION')
        ]
        
        for collection_name, element_pattern in special_collection_patterns:
            if element_name == element_pattern:
                logger.debug(f"      -> Element {element_name} is contained in special collection {collection_name}")
                return True
        
        return False
    
    def _is_collection_type_reference(self, type_name: str) -> bool:
        """Check if a type reference represents a collection type that should be rdf:Bag."""
        # Remove namespace prefix if present
        if ':' in type_name:
            type_name = type_name.split(':', 1)[1]
        
        # Collection type indicators - these are complex types that represent collections
        collection_type_indicators = [
            'VERSIONS', 'SETS', 'RELATIONSHIPS', 'SIGNATURES', 'COLLECTIONS',
            'ABOUT_VERSIONS', 'DEAL_SETS', 'DOCUMENT_SETS', 'SYSTEM_SIGNATURES'
        ]
        
        for indicator in collection_type_indicators:
            if indicator in type_name:
                return True
        
        return False
    
    def is_collection_type(self, element: ET.Element) -> bool:
        """Check if element is a collection type."""
        name = element.get('name', 'UNNAMED')
        
        # Method 1: Check if this complexType contains elements with maxOccurs="unbounded"
        sequence = element.find('.//xsd:sequence', self.namespaces)
        if sequence is not None:
            for elem in sequence.findall('.//xsd:element', self.namespaces):
                max_occurs = elem.get('maxOccurs')
                if max_occurs == 'unbounded':
                    elem_name = elem.get('name', 'UNKNOWN')
                    logger.debug(f"    -> {name}: COLLECTION TYPE detected - contains element '{elem_name}' with maxOccurs='unbounded'")
                    return True
        
        # Method 2: Check if this complexType is referenced elsewhere as an element with maxOccurs="unbounded"
        # This handles cases like MESSAGE where the complexType itself is referenced as a collection element
        if hasattr(self, '_xsd_root') and self._xsd_root is not None:
            # Search for element references to this complexType with maxOccurs="unbounded"
            for elem_ref in self._xsd_root.findall('.//xsd:element', self.namespaces):
                elem_type = elem_ref.get('type')
                max_occurs = elem_ref.get('maxOccurs')
                if (elem_type == name and max_occurs == 'unbounded'):
                    logger.debug(f"    -> {name}: COLLECTION TYPE detected - referenced as element with maxOccurs='unbounded'")
                    return True
        
        # Method 3: Check naming conventions for collection types
        # Many MISMO collection types follow specific naming patterns
        collection_name_indicators = [
            'MESSAGE', 'MESSAGES', 'VERSIONS', 'SETS', 'RELATIONSHIPS', 'SIGNATURES', 
            'COLLECTIONS', 'ABOUT_VERSIONS', 'DEAL_SETS', 'DOCUMENT_SETS', 
            'SYSTEM_SIGNATURES', 'ACCESS_STREETS', 'ACCESSIBILITY_FEATURES',
            'LOAN_PRODUCTS', 'BORROWERS', 'PROPERTIES', 'ADDRESSES', 'PHONES',
            'EMAILS', 'IDENTIFIERS', 'DOCUMENTS', 'LOANS', 'TRANSACTIONS',
            'PAYMENTS', 'ACCOUNTS'
        ]
        
        if name in collection_name_indicators:
            logger.debug(f"    -> {name}: COLLECTION TYPE detected - matches known collection naming pattern")
            return True
        
        logger.debug(f"    -> {name}: NOT a collection type")
        return False
    

    
    def has_only_attributes(self, element: ET.Element) -> bool:
        """Check if element has only attributes (no elements)."""
        name = element.get('name', 'UNNAMED')
        sequence = element.find('.//xsd:sequence', self.namespaces)
        
        if sequence is not None:
            elements = sequence.findall('.//xsd:element', self.namespaces)
            if elements:
                logger.debug(f"    -> {name}: NOT attributes-only - contains {len(elements)} elements")
                return False
        
        # Check if it has attributes
        attributes = element.findall('.//xsd:attribute', self.namespaces)
        if attributes:
            logger.debug(f"    -> {name}: ATTRIBUTES-ONLY detected - contains {len(attributes)} attributes, no elements")
            return True
        else:
            logger.debug(f"    -> {name}: NO attributes or elements found")
            return False
    
    def transform_element(self, element: ET.Element) -> List[str]:
        """
        Transform a single XSD element based on its pattern.
        
        Args:
            element: XSD element to transform
            
        Returns:
            List of TTL statements
        """
        name = element.get('name', 'UNNAMED')
        tag = element.tag
        
        logger.info(f"=== Processing element: {name} (tag: {tag}) ===")
        
        # Check if element should be ignored (includes Pattern 005: Extension patterns)
        if self.should_ignore_element(element):
            # Check if it's a Pattern 005 case
            if element.tag.endswith('EXTENSION') or self._is_extension_pattern(element):
                logger.info(f"  -> Element {name} is marked for IGNORE - Pattern 005: Extension pattern")
            else:
                logger.info(f"  -> Element {name} is marked for IGNORE (extension/attribute group)")
            return []
        
        logger.info(f"  -> Element {name} will be processed")
        statements = []
        
        # Determine element type and transformation pattern
        # Pattern 006: Complex types with elements and attributes (EXTENSION elements are ignored)
        if tag.endswith('simpleType'):
            logger.info(f"  -> Detected SIMPLE TYPE pattern for {name}")
            
            # Check if it's an enumeration
            if element.find('.//xsd:enumeration', self.namespaces) is not None:
                logger.info(f"    -> Pattern 002: ENUMERATION type detected")
                statements.extend(self.transform_enumeration(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for enumeration")
            else:
                logger.info(f"    -> Pattern 001: SIMPLE TYPE with restrictions detected")
                statements.extend(self.transform_simple_type(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for simple type")
                
        elif tag.endswith('complexType'):
            logger.info(f"  -> Detected COMPLEX TYPE pattern for {name}")
            
            # Check for different complex type patterns
            if element.find('.//xsd:simpleContent', self.namespaces) is not None:
                logger.info(f"    -> Pattern 004: COMPLEX TYPE with SIMPLE CONTENT detected")
                logger.debug(f"      -> Found simpleContent, checking for extension and attributes...")
                statements.extend(self.transform_complex_type_simple_content(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for simple content")
                
            elif self.is_collection_type(element):
                logger.info(f"    -> Pattern 007: COLLECTION TYPE detected")
                logger.debug(f"      -> Found collection with maxOccurs='unbounded', applying collection pattern...")
                statements.extend(self.transform_collection_type(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for collection")
                
            elif self.has_only_attributes(element):
                logger.info(f"    -> Pattern 009: COMPLEX TYPE with ATTRIBUTES ONLY detected")
                statements.extend(self.transform_complex_type_attributes_only(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for attributes only")
                
            else:
                logger.info(f"    -> Pattern 006: COMPLEX TYPE with ELEMENTS and ATTRIBUTES detected")
                logger.debug(f"      -> Found sequence, checking for elements and attributes...")
                statements.extend(self.transform_complex_type_elements(element))
                logger.info(f"    -> Generated {len(statements)} TTL statements for elements and attributes")
        else:
            logger.warning(f"  -> UNKNOWN element type: {tag} for {name}")
            logger.warning(f"     This element will not be transformed")
        
        # Log final results
        if statements:
            logger.info(f"  -> SUCCESS: Element {name} transformed with {len(statements)} TTL statements")
        else:
            logger.warning(f"  -> WARNING: Element {name} generated no TTL statements")
        
        logger.info(f"=== Completed processing element: {name} ===\n")
        return statements
    
    def transform_xsd(self, xsd_file: str) -> bool:
        """
        Transform XSD file to TTL format.
        
        Args:
            xsd_file: Path to XSD file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Reading XSD file: {xsd_file}")
            
            # Parse XSD with namespace handling
            tree = ET.parse(xsd_file)
            root = tree.getroot()
            self._xsd_root = root  # Store root for collection type detection
            
            # Add prefixes
            self.add_prefixes()
            
            # Analyze XSD structure
            self.analyze_xsd_structure()
            self.build_hierarchy_data()  
            
            # Find all transformable elements
            transformable_elements = []
            message_element = None
            
            # Find simple types
            for simple_type in root.findall('.//xsd:simpleType', self.namespaces):
                transformable_elements.append(simple_type)
            
            # Find complex types, but prioritize MESSAGE
            for complex_type in root.findall('.//xsd:complexType', self.namespaces):
                name = complex_type.get('name')
                if name == 'MESSAGE':
                    message_element = complex_type
                else:
                    transformable_elements.append(complex_type)
            
            logger.info(f"Found {len(transformable_elements)} transformable elements")
            
            # Transform MESSAGE first if it exists
            if message_element:
                logger.info("Transforming: MESSAGE (priority)")
                statements = self.transform_element(message_element)
                if statements:
                    self.ttl_statements.extend(statements)
                    self.ttl_statements.append("")  # Add blank line
                    self.transformed_types.add('MESSAGE')
            
            # Transform each remaining element
            for element in transformable_elements:
                name = element.get('name')
                if name and name not in self.transformed_types:
                    logger.info(f"Transforming: {name}")
                    statements = self.transform_element(element)
                    if statements:
                        self.ttl_statements.extend(statements)
                        self.ttl_statements.append("")  # Add blank line
                        self.transformed_types.add(name)
            
            # Establish class hierarchies after all elements are transformed
            logger.info("Establishing class hierarchies...")
            hierarchy_statements = self.establish_class_hierarchies()
            if hierarchy_statements:
                self.ttl_statements.append("")
                self.ttl_statements.append("# Class Hierarchies and Containment Relationships")
                self.ttl_statements.append("")
                self.ttl_statements.extend(hierarchy_statements)
                self.ttl_statements.append("")
                logger.info(f"Added {len(hierarchy_statements)} hierarchy statements")
            
            # Ensure hierarchy consistency after all elements are processed
            logger.info("Ensuring hierarchy consistency...")
            consistency_statements = self.ensure_hierarchy_consistency()
            if consistency_statements:
                self.ttl_statements.append("")
                self.ttl_statements.append("# Hierarchy Consistency")
                self.ttl_statements.append("")
                self.ttl_statements.extend(consistency_statements)
                self.ttl_statements.append("")
                logger.info(f"Added {len(consistency_statements)} consistency statements")
            
            logger.info(f"Successfully transformed {len(self.transformed_types)} types")
            return True
            
        except Exception as e:
            logger.error(f"Error transforming XSD: {str(e)}")
            return False
    
    def write_ttl(self, output_file: str) -> bool:
        """
        Write TTL statements to output file.
        
        Args:
            output_file: Path to output TTL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Writing TTL file: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for statement in self.ttl_statements:
                    f.write(statement + "\n")
            
            logger.info(f"Successfully wrote TTL file with {len(self.ttl_statements)} statements")
            return True
            
        except Exception as e:
            logger.error(f"Error writing TTL file: {str(e)}")
            return False

def main():
    """Main function to handle command line arguments and execute the transformer."""
    parser = argparse.ArgumentParser(
        description="Transform MISMO XSD to RDF/RDFS/OWL TTL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transform_mismo_xsd.py --input MISMO_3.6.0_B367.xsd --output mismo_ontology.ttl
  python transform_mismo_xsd.py -i MISMO.xsd -o output.ttl
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Input XSD file path'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output TTL file path'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Initialize transformer
    transformer = MISMOXSDTransformer()
    
    try:
        # Transform XSD
        if not transformer.transform_xsd(args.input):
            sys.exit(1)
        
        # Write TTL
        if not transformer.write_ttl(args.output):
            sys.exit(1)
        
        logger.info("XSD to TTL transformation completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
