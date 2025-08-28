#!/usr/bin/env python3
"""
Generate Ontology Instances from Extracted Data

This script reads dataextracted_*.json files and generates ontology instances
based on the loan-document-ontology.ttl ontology.

The script maps:
- MismoContainerName -> DocumentType
- fieldName -> Field name
- value -> Field value with appropriate data type

Usage:
    python generate_ontology_instances.py --input <input_json_file> --output <output_ttl_file>
    
Examples:
    python generate_ontology_instances.py --input dataextracted_333_888_999_123321_v1.json --output my_instances.ttl
    python generate_ontology_instances.py -i data.json -o output.ttl
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

class OntologyInstanceGenerator:
    """Generates ontology instances from extracted data JSON files."""
    
    def __init__(self, ontology_file: str = "loan-document-ontology.ttl"):
        """Initialize the generator with ontology file path."""
        self.ontology_file = ontology_file
        self.namespace = "http://example.org/loan-document-ontology#"
        self.instances = []
        self.loan_counter = 0
        self.document_counter = 0
        self.field_counter = 0
        self.document_type_counter = 0
        
    def detect_field_type(self, value: str) -> str:
        """
        Detect the appropriate field type based on the value.
        
        Args:
            value: The field value as a string
            
        Returns:
            The appropriate field type from the ontology
        """
        if not value or value.strip() == "":
            return "StringField"
            
        value = value.strip()
        
        # Check for currency (contains $ or %)
        if "$" in value or "%" in value:
            return "CurrencyField"
        
        # Check for date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
            r'\d{4}-\d{2}-\d{2}',        # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return "DateField"
        
        # Check for numeric (only digits, decimal points, and commas)
        if re.match(r'^[\d,]+\.?\d*$', value):
            return "NumericField"
        
        # Check for alphanumeric (contains both letters and numbers)
        if re.search(r'[a-zA-Z]', value) and re.search(r'\d', value):
            return "AlphanumericField"
        
        # Default to string
        return "StringField"
    
    def generate_loan_instance(self, loan_id: str) -> Dict[str, Any]:
        """Generate a loan instance."""
        self.loan_counter += 1
        return {
            "type": "Loan",
            "id": f"Loan_{loan_id}",
            "properties": {
                "loanIdentifier": loan_id
            }
        }
    

    # "id": f"DocType_{self.document_type_counter}_{container_name.replace(' ', '_').replace(':', '_')}",
    def generate_document_type_instance(self, container_name: str) -> Dict[str, Any]:
        """Generate a document type instance."""
        self.document_type_counter += 1
        return {
            "type": "DocumentType",
            "id": f"DocType_{self.document_type_counter}_{container_name.replace(' ', '_').replace(':', '_')}",
            "properties": {
                "documentTypeName": container_name
            }
        }
    
    def generate_document_instance(self, loan_id: str, container_name: str) -> Dict[str, Any]:
        """Generate a document instance."""
        self.document_counter += 1
        return {
            "type": "Document",
            "id": f"Doc_{self.document_counter}_{container_name.replace(' ', '_').replace(':', '_')}",
            "properties": {
                "documentIdentifier": f"DOC_{self.document_counter}",
                "belongsToLoan": f"Loan_{loan_id}",
                "hasDocumentType": f"DocType_{self.document_type_counter}_{container_name.replace(' ', '_').replace(':', '_')}"
            }
        }
    
    def generate_field_instance(self, field_data: Dict[str, Any], document_id: str, loan_id: str) -> Dict[str, Any]:
        """Generate a field instance."""
        self.field_counter += 1
        
        field_name = field_data.get("fieldName", "")
        field_value = field_data.get("value", "")
        field_type = self.detect_field_type(field_value)
        
        # Clean field name for Turtle compatibility - remove/replace invalid characters
        clean_field_name = field_name
        # Replace spaces, parentheses, and other special characters with underscores
        clean_field_name = clean_field_name.replace(' ', '_')
        clean_field_name = clean_field_name.replace('(', '')
        clean_field_name = clean_field_name.replace(')', '')
        clean_field_name = clean_field_name.replace('[', '')
        clean_field_name = clean_field_name.replace(']', '')
        clean_field_name = clean_field_name.replace('{', '')
        clean_field_name = clean_field_name.replace('}', '')
        clean_field_name = clean_field_name.replace('<', '')
        clean_field_name = clean_field_name.replace('>', '')
        clean_field_name = clean_field_name.replace('"', '')
        clean_field_name = clean_field_name.replace("'", '')
        clean_field_name = clean_field_name.replace('\\', '')
        clean_field_name = clean_field_name.replace('/', '_')
        clean_field_name = clean_field_name.replace('\\', '_')
        clean_field_name = clean_field_name.replace('|', '_')
        clean_field_name = clean_field_name.replace('&', '_')
        clean_field_name = clean_field_name.replace(';', '_')
        clean_field_name = clean_field_name.replace(',', '_')
        clean_field_name = clean_field_name.replace('.', '_')
        clean_field_name = clean_field_name.replace(':', '_')
        clean_field_name = clean_field_name.replace('!', '_')
        clean_field_name = clean_field_name.replace('?', '_')
        clean_field_name = clean_field_name.replace('@', '_')
        clean_field_name = clean_field_name.replace('#', '_')
        clean_field_name = clean_field_name.replace('$', '_')
        clean_field_name = clean_field_name.replace('%', '_')
        clean_field_name = clean_field_name.replace('^', '_')
        clean_field_name = clean_field_name.replace('*', '_')
        clean_field_name = clean_field_name.replace('+', '_')
        clean_field_name = clean_field_name.replace('=', '_')
        clean_field_name = clean_field_name.replace('~', '_')
        clean_field_name = clean_field_name.replace('`', '_')
        
        # Remove multiple consecutive underscores
        import re
        clean_field_name = re.sub(r'_+', '_', clean_field_name)
        # Remove leading/trailing underscores
        clean_field_name = clean_field_name.strip('_')
        
        return {
            "type": "Field",
            "id": f"Field_{self.field_counter}_{clean_field_name}",
            "properties": {
                "fieldValue": field_value,
                "extractedFromDocument": document_id,
                "belongsToLoanThroughDocument": f"Loan_{loan_id}",
                "hasFieldType": field_type
            }
        }
    
    def process_json_file(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single JSON file and generate ontology instances.
        
        Args:
            json_file_path: Path to the JSON file
            
        Returns:
            List of generated ontology instances
        """
        logger.info(f"Processing file: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            logger.error(f"Error reading file {json_file_path}: {e}")
            return []
        
        instances = []
        
        # Extract loan ID from filename
        loan_id = self.extract_loan_id_from_filename(json_file_path)
        logger.info(f"\t Loan ID: {loan_id}")
        
        # Generate loan instance
        loan_instance = self.generate_loan_instance(loan_id)
        instances.append(loan_instance)
        
        # Process extracted fields
        extracted_fields = data.get("extractedFields", [])
        logger.info(f"\tExtracted fields length: {len(extracted_fields)}")
        
        for doc_section in extracted_fields:
            document_type = doc_section.get("documentType", "Unknown")
            mismofields = doc_section.get("documentFields", [])
            logger.info(f"\t -- Document type: {document_type}")
            logger.info(f"\t -- Mismo fields length: {len(mismofields)}")
            
            # Generate document type instance
            doc_type_instance = self.generate_document_type_instance(document_type)
            instances.append(doc_type_instance)
            
            # Generate document instance
            document_instance = self.generate_document_instance(loan_id, document_type)
            instances.append(document_instance)
            
            # Process fields within this document
            for field_section in mismofields:
                container_name = field_section.get("MismoContainerName", "")
                mismofields = field_section.get("Mismofields", [])
                logger.info(f"\t ----- Container name: {container_name}")
                logger.info(f"\t ----- Mismo fields length: {len(mismofields)}")
                
                for field_data in mismofields:
                    logger.info(f"\t ----- Field name: {field_data.get('fieldName', '')}")
                    logger.info(f"\t ----- Field value: {field_data.get('value', '')}")
                    logger.info(f"\t ----- Field type: {self.detect_field_type(field_data.get('value', ''))}")
                    
                    field_instance = self.generate_field_instance(
                        field_data, 
                        document_instance["id"], 
                        loan_id
                    )
                    instances.append(field_instance)
        
        logger.info(f"Generated {len(instances)} instances from {json_file_path}")
        return instances
    
    def extract_loan_id_from_filename(self, filepath: str) -> str:
        """Extract loan ID from filename."""
        # Extract the numeric part from filename like "dataextracted_333_888_999_123321_v1"
        match = re.search(r'dataextracted_(\d+_\d+_\d+_\d+)', filepath)
        if match:
            return match.group(1)
        return "unknown_loan"
    
    def generate_turtle_output(self, instances: List[Dict[str, Any]]) -> str:
        """
        Generate Turtle format output for the ontology instances.
        
        Args:
            instances: List of generated instances
            
        Returns:
            Turtle format string
        """
        turtle_lines = [
            "@prefix : <http://example.org/loan-document-ontology#> .",
            "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
            "",
            "# Generated Ontology Instances",
            f"# Generated on: {datetime.now().isoformat()}",
            f"# Total instances: {len(instances)}",
            ""
        ]
        
        for instance in instances:
            instance_id = instance["id"]
            instance_type = instance["type"]
            properties = instance["properties"]
            
            # Add instance declaration
            turtle_lines.append(f":{instance_id} a :{instance_type} ;")
            
            # Add properties
            prop_items = list(properties.items())
            for i, (prop, value) in enumerate(prop_items):
                if i == len(prop_items) - 1:
                    # Last property
                    if isinstance(value, str) and value.startswith("Loan_") or value.startswith("Doc_") or value.startswith("DocType_") or value.startswith("Field_"):
                        turtle_lines.append(f"    :{prop} :{value} .")
                    else:
                        turtle_lines.append(f'    :{prop} "{value}" .')
                else:
                    # Not last property
                    if isinstance(value, str) and value.startswith("Loan_") or value.startswith("Doc_") or value.startswith("DocType_") or value.startswith("Field_"):
                        turtle_lines.append(f"    :{prop} :{value} ;")
                    else:
                        turtle_lines.append(f'    :{prop} "{value}" ;')
            
            turtle_lines.append("")
        
        return "\n".join(turtle_lines)
    
    def process_all_files(self, pattern: str = "dataextracted_*.json") -> List[Dict[str, Any]]:
        """
        Process all matching JSON files and generate ontology instances.
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            List of all generated ontology instances
        """
        all_instances = []
        
        # Find all matching files
        json_files = glob.glob(pattern)
        if not json_files:
            logger.warning(f"No files found matching pattern: {pattern}")
            return []
        
        logger.info(f"Found {len(json_files)} files to process")
        
        for json_file in json_files:
            instances = self.process_json_file(json_file)
            all_instances.extend(instances)
        
        return all_instances
    
    def save_turtle_file(self, instances: List[Dict[str, Any]], output_file: str = "generated_instances.ttl"):
        """
        Save generated instances to a Turtle file.
        
        Args:
            instances: List of generated instances
            output_file: Output file path
        """
        turtle_content = self.generate_turtle_output(instances)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(turtle_content)
            logger.info(f"Turtle file saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving Turtle file: {e}")
    
    def save_json_file(self, instances: List[Dict[str, Any]], output_file: str = "generated_instances.json"):
        """
        Save generated instances to a JSON file.
        
        Args:
            instances: List of generated instances
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(instances, file, indent=2, ensure_ascii=False)
            logger.info(f"JSON file saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")


def main():
    """Main function to run the ontology instance generator."""
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Generate ontology instances from extracted data JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_ontology_instances.py --input dataextracted_333_888_999_123321_v1.json --output my_instances.ttl
  python generate_ontology_instances.py -i data.json -o output.ttl
  python generate_ontology_instances.py --input data.json --output output.ttl --json-output output.json
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input JSON file path (e.g., dataextracted_333_888_999_123321_v1.json)"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output TTL file path (e.g., generated_instances.ttl)"
    )
    
    parser.add_argument(
        "--json-output", "-j",
        help="Output JSON file path (optional, defaults to output filename with .json extension)"
    )
    
    parser.add_argument(
        "--ontology", "-ont",
        default="loan-document-ontology.ttl",
        help="Ontology file path (default: loan-document-ontology.ttl)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Ontology Instance Generation")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output TTL file: {args.output}")
    if args.json_output:
        logger.info(f"Output JSON file: {args.json_output}")
    
    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Initialize the generator with custom ontology file if specified
    generator = OntologyInstanceGenerator(args.ontology)
    
    # Process the specified input file
    instances = generator.process_json_file(args.input)
    
    if not instances:
        logger.error("No instances generated. Exiting.")
        sys.exit(1)
    
    logger.info(f"Successfully generated {len(instances)} ontology instances")
    
    # Determine JSON output filename if not specified
    json_output = args.json_output
    if not json_output:
        # Use the same base name as TTL file but with .json extension
        json_output = args.output.rsplit('.', 1)[0] + '.json'
    
    # Save output files
    generator.save_turtle_file(instances, args.output)
    generator.save_json_file(instances, json_output)
    
    # Print summary
    print("\n" + "="*60)
    print("ONTOLOGY INSTANCE GENERATION SUMMARY")
    print("="*60)
    print(f"Input file: {args.input}")
    print(f"Output TTL file: {args.output}")
    print(f"Output JSON file: {json_output}")
    print(f"Total instances generated: {len(instances)}")
    
    # Count by type
    type_counts = {}
    for instance in instances:
        instance_type = instance["type"]
        type_counts[instance_type] = type_counts.get(instance_type, 0) + 1
    
    for instance_type, count in type_counts.items():
        print(f"{instance_type}: {count}")
    
    print("="*60)


if __name__ == "__main__":
    main()
