# VirtuOSO Turtle File Upload & Viewing Tutorial

## Prerequisites
- Docker and Docker Compose installed
- A Turtle (.ttl) file ready for upload

---

## Step 1: Start VirtuOSO

```bash
# Navigate to your project directory
cd /path/to/your/virtuoso/project

# Start VirtuOSO using docker-compose
docker-compose up -d

# Verify it's running
docker-compose ps
```

**Expected Output:**
```
Name       Command   State   Ports
virtuoso   ...       Up      0.0.0.0:1111->1111/tcp, 0.0.0.0:8890->8890/tcp
```

---

## Step 2: Upload Your Turtle File

### Method A: Using the Shell Script (Recommended for beginners)

```bash
# Make the script executable
chmod +x upload-pipeline.sh

# Upload your Turtle file
./upload-pipeline.sh your_file.ttl

# Upload with custom graph URI
./upload-pipeline.sh your_file.ttl http://example.org/my-ontology

# Upload using specific method
./upload-pipeline.sh your_file.ttl http://example.org/my-ontology isql
```

### Method B: Using the Python Script

```bash
# Install dependencies
pip install -r requirements.txt

# Upload with verbose output
python upload_pipeline.py your_file.ttl --graph-uri "http://example.org/my-ontology" --verbose
```

### Method C: Manual Upload via Web Interface

1. Open browser: **http://localhost:8890/conductor**
2. Login: username `dba`, password `mysecret`
3. Navigate: **Linked Data** → **Quad Store Upload**
4. Select **"File"** option
5. Click **"Choose File"** and select your .ttl file
6. Set **"Named Graph IRI"** to your desired URI
7. Click **"Upload"**

---

## Step 3: Verify Upload Success

### Check Upload Status
```bash
# View VirtuOSO logs
docker-compose logs virtuoso

# Check if container is healthy
docker-compose ps
```

---

## Step 4: View Your Uploaded Data

### Option A: Web Interface (Easiest)

1. **Open SPARQL Endpoint:** http://localhost:8890/sparql

2. **List All Graphs:**
```sparql
SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }
```

3. **Count Triples in Your Graph:**
```sparql
SELECT COUNT(*) WHERE {
  GRAPH <http://example.org/my-ontology> {
    ?s ?p ?o
  }
}
```

4. **View Sample Data:**
```sparql
SELECT ?s ?p ?o WHERE {
  GRAPH <http://example.org/my-ontology> {
    ?s ?p ?o
  }
} LIMIT 10
```

5. **Find Classes in Your Ontology:**
```sparql
SELECT DISTINCT ?class WHERE {
  GRAPH <http://example.org/my-ontology> {
    ?class a <http://www.w3.org/2002/07/owl#Class>
  }
}
```

### Option B: ISQL Command Line

```bash
# Connect to ISQL
docker exec -it virtuoso isql 1111 dba mysecret
```

**In ISQL, use these commands:**

```sql
-- List all graphs
SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } };

-- Count triples in your graph
SPARQL SELECT COUNT(*) FROM <http://example.org/my-ontology> WHERE { ?s ?p ?o };

-- View sample data
SPARQL SELECT ?s ?p ?o FROM <http://example.org/my-ontology> WHERE { ?s ?p ?o } LIMIT 10;

-- Exit ISQL
EXIT;
```

### Option C: Conductor Web Interface

1. Go to: **http://localhost:8890/conductor**
2. Navigate: **Linked Data** → **Graphs**
3. View all loaded graphs and their sizes

---

## Step 5: Common SPARQL Queries for Ontology Exploration

### Basic Queries:
```sparql
-- Count all triples
SELECT COUNT(*) WHERE { ?s ?p ?o }

-- Find all classes
SELECT DISTINCT ?class WHERE { ?class a <http://www.w3.org/2002/07/owl#Class> }

-- Find all properties
SELECT DISTINCT ?prop WHERE { ?prop a <http://www.w3.org/2002/07/owl#ObjectProperty> }

-- Find all individuals
SELECT DISTINCT ?ind WHERE { ?ind a ?class }

-- Find class hierarchy
SELECT ?class ?superclass WHERE {
  ?class rdfs:subClassOf ?superclass
}
```

### Advanced Queries:
```sparql
-- Find classes with their labels
SELECT ?class ?label WHERE {
  ?class a <http://www.w3.org/2002/07/owl#Class> .
  ?class rdfs:label ?label
}

-- Find properties with domains and ranges
SELECT ?prop ?domain ?range WHERE {
  ?prop a <http://www.w3.org/2002/07/owl#ObjectProperty> .
  OPTIONAL { ?prop rdfs:domain ?domain }
  OPTIONAL { ?prop rdfs:range ?range }
}
```

---

## Step 6: Troubleshooting

### Common Issues:

1. **Upload Fails:**
```bash
# Check VirtuOSO logs
docker-compose logs virtuoso

# Restart VirtuOSO
docker-compose restart virtuoso
```

2. **Can't Find Graph:**
```sparql
-- Check what graphs actually exist
SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }
```

3. **Permission Errors:**
```bash
# Make scripts executable
chmod +x upload-pipeline.sh
chmod +x upload_pipeline.py
```

4. **File Not Found:**
- Ensure your .ttl file exists in the current directory
- Check file path is correct

5. **ISQL Syntax Error:**
- Remember to prefix SPARQL queries with `SPARQL` in ISQL
- Use `SPARQL SELECT ...` not just `SELECT ...`

6. **Graph Not Found Error:**
- Verify the exact graph URI used during upload
- Check for trailing `#` in the URI
- Re-upload with verbose logging to see what happened

---

## Step 7: Clean Up

```bash
# Stop VirtuOSO
docker-compose down

# Remove volumes (optional - this deletes all data)
docker-compose down -v
```

---

## Quick Reference Commands

```bash
# Start
docker-compose up -d

# Upload
./upload-pipeline.sh my_ontology.ttl http://example.org/ontology

# View in browser
open http://localhost:8890/sparql

# Stop
docker-compose down
```

---

## Access Points Summary

| Service | URL/Command | Purpose |
|---------|-------------|---------|
| **Conductor** | http://localhost:8890/conductor | Web management interface |
| **SPARQL Endpoint** | http://localhost:8890/sparql | Query your data |
| **ISQL** | `docker exec -it virtuoso isql 1111 dba mysecret` | Command line interface |

---

## Default Credentials

- **Username:** `dba`
- **Password:** `mysecret`

---

This tutorial covers the complete workflow from upload to viewing your Turtle file data in VirtuOSO! 