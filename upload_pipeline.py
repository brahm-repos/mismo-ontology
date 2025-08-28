#!/usr/bin/env python3
"""
VirtuOSO Turtle File Upload Pipeline
A Python-based pipeline for uploading Turtle (.ttl) files to VirtuOSO
"""

import argparse
import requests
import subprocess
import time
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VirtuosoUploader:
    def __init__(self, host: str = "localhost", http_port: int = 8890, 
                 isql_port: int = 1111, username: str = "dba", 
                 password: str = "mysecret", container_name: str = "virtuoso"):
        self.host = host
        self.http_port = http_port
        self.isql_port = isql_port
        self.username = username
        self.password = password
        self.container_name = container_name
        self.base_url = f"http://{host}:{http_port}"
        
    def check_virtuoso_running(self) -> bool:
        """Check if VirtuOSO container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.container_name}"],
                capture_output=True, text=True, check=True
            )
            return self.container_name in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def wait_for_virtuoso(self, timeout: int = 60) -> bool:
        """Wait for VirtuOSO to be ready"""
        logger.info("Waiting for VirtuOSO to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/conductor", timeout=5)
                if response.status_code == 200:
                    logger.info("VirtuOSO is ready!")
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
            print(".", end="", flush=True)
        
        logger.error("VirtuOSO did not become ready within expected time")
        return False
    
    def upload_via_isql(self, ttl_file: str, graph_uri: str) -> bool:
        """Upload Turtle file via ISQL command line"""
        logger.info(f"Uploading {ttl_file} via ISQL...")
        
        try:
            # Copy file to container
            subprocess.run([
                "docker", "cp", ttl_file, f"{self.container_name}:/data/"
            ], check=True)
            
            filename = Path(ttl_file).name
            
            # Create ISQL script
            isql_script = f"""
-- Upload Turtle file to VirtuOSO
ld_dir('/data', '{filename}', '{graph_uri}');
rdf_loader_run();
checkpoint;
"""
            
            # Execute ISQL script
            result = subprocess.run([
                "docker", "exec", "-i", self.container_name, "isql",
                f"{self.host}:{self.isql_port}", self.username, self.password
            ], input=isql_script, text=True, capture_output=True, check=True)
            
            logger.info("Upload completed via ISQL")
            logger.debug(f"ISQL output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ISQL upload failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
    
    def upload_via_sparql(self, ttl_file: str, graph_uri: str) -> bool:
        """Upload Turtle file via SPARQL HTTP endpoint"""
        logger.info(f"Uploading {ttl_file} via SPARQL HTTP endpoint...")
        
        try:
            with open(ttl_file, 'rb') as f:
                response = requests.post(
                    f"{self.base_url}/sparql-graph-crud-auth",
                    params={
                        "graph-uri": graph_uri,
                        "username": self.username,
                        "password": self.password
                    },
                    headers={"Content-Type": "application/x-turtle"},
                    data=f.read(),
                    timeout=30
                )
            
            if response.status_code in [200, 201]:
                logger.info("Upload successful via SPARQL endpoint")
                return True
            else:
                logger.error(f"Upload failed. HTTP code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SPARQL upload failed: {e}")
            return False
    
    def upload_via_bulk_loader(self, ttl_file: str, graph_uri: str) -> bool:
        """Upload Turtle file via VirtuOSO bulk loader"""
        logger.info(f"Uploading {ttl_file} via VirtuOSO bulk loader...")
        
        try:
            # Copy file to container
            subprocess.run([
                "docker", "cp", ttl_file, f"{self.container_name}:/data/"
            ], check=True)
            
            filename = Path(ttl_file).name
            
            # Create bulk loader script
            bulk_script = f"""
-- Bulk load Turtle file
DELETE FROM DB.DBA.LOAD_LIST;
ld_dir('/data', '{filename}', '{graph_uri}');
SELECT * FROM DB.DBA.LOAD_LIST;
rdf_loader_run();
checkpoint;
SELECT COUNT(*) FROM DB.DBA.LOAD_LIST;
"""
            
            # Execute bulk loader
            result = subprocess.run([
                "docker", "exec", "-i", self.container_name, "isql",
                f"{self.host}:{self.isql_port}", self.username, self.password
            ], input=bulk_script, text=True, capture_output=True, check=True)
            
            logger.info("Bulk upload completed")
            logger.debug(f"Bulk loader output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Bulk loader upload failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False
    
    def verify_upload(self, graph_uri: str) -> Optional[int]:
        """Verify upload by counting triples in the graph"""
        logger.info("Verifying upload...")
        
        try:
            query = f"""
            SELECT COUNT(*) as triple_count 
            WHERE {{ 
                GRAPH <{graph_uri}> {{ ?s ?p ?o }} 
            }}
            """
            
            response = requests.post(
                f"{self.base_url}/sparql",
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json"
                },
                data=query,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and 'bindings' in result['results']:
                    bindings = result['results']['bindings']
                    if bindings and 'triple_count' in bindings[0]:
                        count = int(bindings[0]['triple_count']['value'])
                        logger.info(f"Upload verified! Found {count} triples in graph: {graph_uri}")
                        return count
            
            logger.warning("Could not verify upload")
            return None
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return None
    
    def get_graph_info(self, graph_uri: str) -> Dict[str, Any]:
        """Get detailed information about a graph"""
        try:
            query = f"""
            SELECT ?s ?p ?o 
            WHERE {{ 
                GRAPH <{graph_uri}> {{ ?s ?p ?o }} 
            }} 
            LIMIT 10
            """
            
            response = requests.post(
                f"{self.base_url}/sparql",
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json"
                },
                data=query,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def upload(self, ttl_file: str, graph_uri: str = "http://example.org/ontology", 
               method: str = "isql", verify: bool = True) -> bool:
        """Main upload method"""
        
        # Check if file exists
        if not os.path.exists(ttl_file):
            logger.error(f"File not found: {ttl_file}")
            return False
        
        # Check VirtuOSO status
        if not self.check_virtuoso_running():
            logger.error("VirtuOSO container is not running. Please start it first with: docker-compose up -d")
            return False
        
        if not self.wait_for_virtuoso():
            return False
        
        # Execute upload based on method
        success = False
        if method == "isql":
            success = self.upload_via_isql(ttl_file, graph_uri)
        elif method == "sparql":
            success = self.upload_via_sparql(ttl_file, graph_uri)
        elif method == "bulk":
            success = self.upload_via_bulk_loader(ttl_file, graph_uri)
        else:
            logger.error(f"Unknown method: {method}")
            return False
        
        # Verify upload if requested
        if success and verify:
            self.verify_upload(graph_uri)
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Upload Turtle files to VirtuOSO")
    parser.add_argument("ttl_file", help="Path to the Turtle file to upload")
    parser.add_argument("--graph-uri", default="http://example.org/ontology", 
                       help="Target graph URI (default: http://example.org/ontology)")
    parser.add_argument("--method", choices=["isql", "sparql", "bulk"], default="isql",
                       help="Upload method (default: isql)")
    parser.add_argument("--host", default="localhost", help="VirtuOSO host (default: localhost)")
    parser.add_argument("--http-port", type=int, default=8890, help="VirtuOSO HTTP port (default: 8890)")
    parser.add_argument("--isql-port", type=int, default=1111, help="VirtuOSO ISQL port (default: 1111)")
    parser.add_argument("--username", default="dba", help="VirtuOSO username (default: dba)")
    parser.add_argument("--password", default="mysecret", help="VirtuOSO password (default: mysecret)")
    parser.add_argument("--container", default="virtuoso", help="Docker container name (default: virtuoso)")
    parser.add_argument("--no-verify", action="store_true", help="Skip upload verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create uploader instance
    uploader = VirtuosoUploader(
        host=args.host,
        http_port=args.http_port,
        isql_port=args.isql_port,
        username=args.username,
        password=args.password,
        container_name=args.container
    )
    
    # Perform upload
    success = uploader.upload(
        ttl_file=args.ttl_file,
        graph_uri=args.graph_uri,
        method=args.method,
        verify=not args.no_verify
    )
    
    if success:
        logger.info("Upload pipeline completed successfully!")
        sys.exit(0)
    else:
        logger.error("Upload pipeline failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 