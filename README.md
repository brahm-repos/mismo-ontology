# VirtuOSO Turtle File Upload Pipeline

This repository provides a comprehensive data pipeline for uploading Turtle (.ttl) ontology files to VirtuOSO using Docker.

## Quick Start

### 1. Start VirtuOSO

```bash
# Start VirtuOSO using docker-compose
docker-compose up -d

# Check if it's running
docker-compose ps
```

### 2. Upload Your Turtle File

#### Using the Shell Script (Recommended for simple uploads):
```bash
# Make the script executable
chmod +x upload-pipeline.sh

# Upload a Turtle file
./upload-pipeline.sh my_ontology.ttl

# Upload with custom graph URI
./upload-pipeline.sh my_ontology.ttl http://example.org/my-ontology

# Upload using SPARQL method
./upload-pipeline.sh my_ontology.ttl http://example.org/my-ontology sparql
```

#### Using the Python Script (Recommended for advanced usage):
```bash
# Install dependencies
pip install -r requirements.txt

# Upload a Turtle file
python upload_pipeline.py my_ontology.ttl

# Upload with custom options
python upload_pipeline.py my_ontology.ttl \
  --graph-uri http://example.org/my-ontology \
  --method sparql \
  --verbose
```

## Upload Methods

### 1. ISQL Method (Default)
- **Pros**: Most reliable, handles large files well
- **Cons**: Requires file copy to container
- **Use case**: Large ontology files, production environments

### 2. SPARQL HTTP Method
- **Pros**: Direct HTTP upload, no file copying needed
- **Cons**: Limited by HTTP timeout for very large files
- **Use case**: Small to medium files, API integration

### 3. Bulk Loader Method
- **Pros**: Optimized for large datasets, better error handling
- **Cons**: More complex setup
- **Use case**: Very large ontologies, batch processing

### 4. Web UI Method (Manual)
- **Pros**: Visual interface, good for exploration
- **Cons**: Manual process, not suitable for automation, interface may vary by version
- **Use case**: One-time uploads, testing
- **Note**: Navigate to "Linked Data > Quad Store Upload" in the Conductor interface

## Configuration

### Environment Variables

You can customize the VirtuOSO connection by modifying these variables in the scripts:

```bash
VIRTUOSO_HOST=localhost
VIRTUOSO_HTTP_PORT=8890
VIRTUOSO_ISQL_PORT=1111
DBA_USER=dba
DBA_PASSWORD=mysecret
VIRTUOSO_CONTAINER=virtuoso
```

### Docker Compose Configuration

The `docker-compose.yml` file includes:
- Persistent data volumes
- Health checks
- Automatic restart policy
- Proper port mapping

## Access Points

Once VirtuOSO is running, you can access:

- **Web Interface**: http://localhost:8890/conductor
- **SPARQL Endpoint**: http://localhost:8890/sparql
- **ISQL Command Line**: `docker exec -it virtuoso isql 1111 dba mysecret`

## Usage Examples

### Upload MIMO Ontology

```bash
# Assuming you have the MIMO ontology in Turtle format
./upload-pipeline.sh mimo_ontology.ttl http://purl.obolibrary.org/obo/mimo.owl
```

### Batch Upload Multiple Files

```bash
#!/bin/bash
# batch_upload.sh
for file in *.ttl; do
    echo "Uploading $file..."
    ./upload-pipeline.sh "$file" "http://example.org/ontologies/$(basename "$file" .ttl)"
done
```

### Python Script with Custom Configuration

```python
from upload_pipeline import VirtuosoUploader

# Create uploader with custom configuration
uploader = VirtuosoUploader(
    host="localhost",
    http_port=8890,
    username="dba",
    password="mysecret"
)

# Upload ontology
success = uploader.upload(
    ttl_file="mimo_ontology.ttl",
    graph_uri="http://purl.obolibrary.org/obo/mimo.owl",
    method="isql",
    verify=True
)

if success:
    print("Upload successful!")
else:
    print("Upload failed!")
```

## Troubleshooting

### Common Issues

1. **VirtuOSO not starting**
   ```bash
   # Check logs
   docker-compose logs virtuoso
   
   # Restart container
   docker-compose restart virtuoso
   ```

2. **Upload timeout**
   - Use ISQL method for large files
   - Increase timeout in Python script
   - Check available memory

3. **Permission denied**
   ```bash
   # Make scripts executable
   chmod +x upload-pipeline.sh
   chmod +x upload_pipeline.py
   ```

4. **File not found**
   - Ensure the Turtle file exists
   - Check file path is correct
   - Verify file has .ttl or .turtle extension

### Verification

After upload, verify your data:

```bash
# Count triples in your graph
curl -X POST \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  --data "SELECT COUNT(*) WHERE { GRAPH <http://example.org/ontology> { ?s ?p ?o } }" \
  http://localhost:8890/sparql
```

## File Structure

```
virtuoso/
├── docker-compose.yml          # VirtuOSO container configuration
├── upload-pipeline.sh          # Shell script for uploads
├── upload_pipeline.py          # Python script for uploads
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Dependencies

- Docker and Docker Compose
- Bash (for shell script)
- Python 3.6+ (for Python script)
- curl (for health checks)

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests! 