#!/usr/bin/env python3
"""
Generate Enhanced Knowledge Graph from Extracted Data

This script reads dataextracted_*.json files and generates knowledge graph instances
based on the enhanced_loan_document_ontology.ttl ontology.

The script maps:
- documentType -> Document classification
- MismoContainerName -> MISMO entity instances (with naming transformation)
- fieldName -> Extracted field names
- value -> Field values with appropriate data types
- uuid -> Unique identifiers for fields

Usage:
    python generate_enhanced_kg.py --input <input_json_file> --output <output_ttl_file>
    
Examples:
    python generate_enhanced_kg.py --input dataextracted_333_888_999_123321_v1.json --output enhanced_kg.ttl
    python generate_enhanced_kg.py -i data.json -o output.ttl
"""

import json
import glob
import re
import uuid
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedKnowledgeGraphGenerator:
    """Generates enhanced knowledge graph instances from extracted data JSON files."""
    
    def __init__(self, ontology_file: str = "enhanced_loan_document_ontology.ttl"):
        """Initialize the generator with ontology file path."""
        self.ontology_file = ontology_file
        self.namespace = "http://www.mismo.org/loan-document-ontology#"
        self.mismo_namespace = "http://www.mismo.org/residential/2009/schemas#"
        self.instances = []
        self.loan_counter = 0
        self.document_counter = 0
        self.entity_counter = 0
        self.field_counter = 0
        
    def transform_mismo_container_name(self, container_name: str) -> str:
        """
        Transform MISMO container name according to the specified rules:
        1. Take the value after the separator ":" if exists
        2. Remove spaces and replace with "_"
        3. Make the name uppercase
        
        Args:
            container_name: The original MISMO container name
            
        Returns:
            Transformed container name
        """
        if not container_name:
            return "UNKNOWN_ENTITY"
            
        # Split by ":" and take the part after it if exists
        if ":" in container_name:
            parts = container_name.split(":")
            if len(parts) > 1:
                name_part = parts[1].strip()
            else:
                name_part = container_name
        else:
            name_part = container_name
            
        # Remove spaces and replace with "_", then make uppercase
        transformed = name_part.replace(" ", "_").upper()
        
        # Remove any special characters that might cause issues in TTL
        transformed = re.sub(r'[^A-Z0-9_]', '', transformed)
        
        # Ensure it's not empty
        if not transformed:
            transformed = "UNKNOWN_ENTITY"
            
        return transformed
    
    def detect_field_type(self, value: str, field_type: str = "") -> str:
        """
        Detect the appropriate field type based on the value and field_type.
        
        Args:
            value: The field value as a string
            field_type: The field type from the JSON (if available)
            
        Returns:
            The appropriate XSD data type
        """
        if not value or value.strip() == "":
            return "xsd:string"
            
        value = value.strip()
        
        # If field_type is provided and valid, use it
        if field_type and field_type.strip():
            type_mapping = {
                "string": "xsd:string",
                "integer": "xsd:integer",
                "decimal": "xsd:decimal",
                "boolean": "xsd:boolean",
                "date": "xsd:date",
                "datetime": "xsd:dateTime"
            }
            if field_type.lower() in type_mapping:
                return type_mapping[field_type.lower()]
        
        # Check for currency (contains $ or %)
        if "$" in value or "%" in value:
            return "xsd:decimal"
        
        # Check for date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
            r'\d{4}-\d{2}-\d{2}',        # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return "xsd:date"
        
        # Check for numeric (only digits, decimal points, and commas)
        if re.match(r'^[\d,]+\.?\d*$', value):
            if '.' in value or ',' in value:
                return "xsd:decimal"
            else:
                return "xsd:integer"
        
        # Check for boolean
        if value.lower() in ['true', 'false', 'yes', 'no', '1', '0']:
            return "xsd:boolean"
        
        # Default to string
        return "xsd:string"
    
    def generate_loan_instance(self, loan_id: str) -> str:
        """Generate a loan instance in TTL format."""
        self.loan_counter += 1
        return f"""loandocs:Loan_{loan_id} a mismo:loan ;
    rdfs:label "Loan: {loan_id}" ."""
    
    def generate_document_instance(self, document_type: str, document_id: str) -> str:
        """Generate a document instance in TTL format."""
        self.document_counter += 1
        return f"""loandocs:Document_{document_id} a mismo:Document ;
    rdfs:label "{document_type}" ."""
    
    def generate_document_type_instance(self, document_type: str) -> str:
        """Generate a document type classification instance in TTL format."""
        return f"""loandocs:DocumentType_{self.sanitize_name(document_type)} a mismo:document_Classification ;
    rdfs:label "{document_type}" ."""
    
    def generate_mismo_entity_instance(self, entity_name: str, entity_id: str) -> str:
        """Generate a MISMO entity instance in TTL format."""
        self.entity_counter += 1
        return f"""loandocs:{entity_name}_{entity_id} a owl:Thing ;
    rdfs:label "{entity_name}" ;
    rdfs:comment "MISMO entity representing {entity_name} information, formed from extracted fields" ."""
    
    def generate_field_instance(self, field_name: str, field_value: str, field_type: str, field_uuid: str) -> str:
        """Generate a field instance in TTL format."""
        self.field_counter += 1
        xsd_type = self.detect_field_type(field_value, field_type)
        
        # Handle different data types appropriately
        if xsd_type == "xsd:string":
            value_literal = f'"{field_value}"'
        elif xsd_type == "xsd:integer":
            value_literal = field_value
        elif xsd_type == "xsd:decimal":
            value_literal = field_value
        elif xsd_type == "xsd:boolean":
            value_literal = field_value.lower()
        elif xsd_type == "xsd:date":
            value_literal = f'"{field_value}"^^xsd:date'
        else:
            value_literal = f'"{field_value}"'
        
        return f"""loandocs:Field_{field_uuid} a owl:Thing ;
    rdfs:label "{field_name}" ;
    loandocs:fieldName "{field_name}" ;
    loandocs:fieldValue {value_literal} ;
    loandocs:fieldType "{field_type}" ;
    loandocs:fieldUUID "{field_uuid}" ."""
    
    def sanitize_name(self, name: str) -> str:
        """Sanitize names for use in TTL identifiers."""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    def generate_relationships(self, loan_id: str, document_id: str, document_type: str, 
                             entity_name: str, entity_id: str, fields: List[Dict[str, Any]]) -> List[str]:
        """Generate relationship statements in TTL format."""
        relationships = []
        
        # Loan has document
        relationships.append(f"""loandocs:Loan_{loan_id} loandocs:hasDocument loandocs:Document_{document_id} .""")
        
        # Document has document type
        relationships.append(f"""loandocs:Document_{document_id} loandocs:hasDocumentType loandocs:DocumentType_{self.sanitize_name(document_type)} .""")
        
        # Document has extracted entity
        relationships.append(f"""loandocs:Document_{document_id} loandocs:hasExtractedEntity loandocs:{entity_name}_{entity_id} .""")
        
        # Entity is related to document
        relationships.append(f"""loandocs:{entity_name}_{entity_id} loandocs:isRelatedToDocument loandocs:Document_{document_id} .""")
        
        # Entity has fields
        for field in fields:
            field_uuid = field.get('uuid', str(uuid.uuid4()))
            relationships.append(f"""loandocs:{entity_name}_{entity_id} loandocs:hasField loandocs:Field_{field_uuid} .""")
        
        return relationships
    
    def process_json_data(self, json_data: Dict[str, Any]) -> List[str]:
        """Process JSON data and generate TTL instances."""
        ttl_statements = []
        
        # Add prefixes
        ttl_statements.extend([
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
            "@prefix mismo: <http://www.mismo.org/residential/2009/schemas#> .",
            "@prefix loandocs: <http://www.mismo.org/loan-document-ontology#> .",
            "",
            "# Enhanced Knowledge Graph Instances",
            "# Generated from extracted data",
            f"# Generated on: {datetime.now().isoformat()}",
            ""
        ])
        
        extracted_fields = json_data.get('extractedFields', [])
        
        for field_group in extracted_fields:
            document_type = field_group.get('documentType', 'Unknown Document Type')
            document_fields = field_group.get('documentFields', [])
            
            # Generate document type instance
            ttl_statements.append(self.generate_document_type_instance(document_type))
            ttl_statements.append("")
            
            for doc_field in document_fields:
                mismo_container_name = doc_field.get('MismoContainerName', 'Unknown Entity')
                mismofields = doc_field.get('Mismofields', [])
                
                # Transform MISMO container name
                entity_name = self.transform_mismo_container_name(mismo_container_name)
                entity_id = str(uuid.uuid4())[:8]
                
                # Generate entity instance
                ttl_statements.append(self.generate_mismo_entity_instance(entity_name, entity_id))
                ttl_statements.append("")
                
                # Generate field instances
                for field in mismofields:
                    field_name = field.get('fieldName', 'Unknown Field')
                    field_value = field.get('value', '')
                    field_type = field.get('type', '')
                    field_uuid = field.get('uuid', str(uuid.uuid4()))
                    
                    ttl_statements.append(self.generate_field_instance(field_name, field_value, field_type, field_uuid))
                
                ttl_statements.append("")
                
                # Generate relationships
                loan_id = "DEFAULT_LOAN"  # You might want to extract this from the data
                document_id = str(uuid.uuid4())[:8]
                
                # Generate document instance
                ttl_statements.append(self.generate_document_instance(document_type, document_id))
                ttl_statements.append("")
                
                # Generate loan instance
                ttl_statements.append(self.generate_loan_instance(loan_id))
                ttl_statements.append("")
                
                # Generate relationships
                relationships = self.generate_relationships(loan_id, document_id, document_type, 
                                                        entity_name, entity_id, mismofields)
                ttl_statements.extend(relationships)
                ttl_statements.append("")
        
        return ttl_statements
    
    def generate_kg(self, input_file: str, output_file: str) -> bool:
        """
        Generate knowledge graph from input JSON file.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output TTL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Reading input file: {input_file}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            logger.info("Processing JSON data...")
            ttl_statements = self.process_json_data(json_data)
            
            logger.info(f"Writing output file: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                for statement in ttl_statements:
                    f.write(statement + "\n")
            
            logger.info(f"Successfully generated knowledge graph with:")
            logger.info(f"  - {self.loan_counter} loan instances")
            logger.info(f"  - {self.document_counter} document instances")
            logger.info(f"  - {self.entity_counter} entity instances")
            logger.info(f"  - {self.field_counter} field instances")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating knowledge graph: {str(e)}")
            return False
    
    def process_directory(self, input_dir: str, output_dir: str, pattern: str = "dataextracted_*.json") -> bool:
        """
        Process all JSON files in a directory matching the pattern.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            pattern: File pattern to match
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            json_files = glob.glob(os.path.join(input_dir, pattern))
            
            if not json_files:
                logger.warning(f"No files found matching pattern: {pattern}")
                return False
            
            success_count = 0
            for json_file in json_files:
                filename = os.path.basename(json_file)
                output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_kg.ttl")
                
                logger.info(f"Processing file: {filename}")
                if self.generate_kg(json_file, output_file):
                    success_count += 1
                    logger.info(f"Successfully processed: {filename}")
                else:
                    logger.error(f"Failed to process: {filename}")
            
            logger.info(f"Processed {success_count}/{len(json_files)} files successfully")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error processing directory: {str(e)}")
            return False

def main():
    """Main function to handle command line arguments and execute the generator."""
    parser = argparse.ArgumentParser(
        description="Generate Enhanced Knowledge Graph from Extracted Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_enhanced_kg.py -i data.json -o output.ttl
  python generate_enhanced_kg.py --input data.json --output output.ttl
  python generate_enhanced_kg.py --directory test-data --output output/
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-i', '--input',
        help='Input JSON file path'
    )
    group.add_argument(
        '-d', '--directory',
        help='Input directory containing JSON files (will process all dataextracted_*.json files)'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output file or directory path'
    )
    
    parser.add_argument(
        '--ontology',
        default='enhanced_loan_document_ontology.ttl',
        help='Path to ontology file (default: enhanced_loan_document_ontology.ttl)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize generator
    generator = EnhancedKnowledgeGraphGenerator(args.ontology)
    
    try:
        if args.input:
            # Process single file
            if not os.path.exists(args.input):
                logger.error(f"Input file not found: {args.input}")
                sys.exit(1)
            
            success = generator.generate_kg(args.input, args.output)
            if not success:
                sys.exit(1)
                
        elif args.directory:
            # Process directory
            if not os.path.exists(args.directory):
                logger.error(f"Input directory not found: {args.directory}")
                sys.exit(1)
            
            success = generator.process_directory(args.directory, args.output)
            if not success:
                sys.exit(1)
        
        logger.info("Knowledge graph generation completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
