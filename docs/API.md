# API Documentation

## Database Operations

### Database Manager (`database.py`)

The `DatabaseManager` class handles all database interactions with MariaDB.

#### Key Methods:

```python
# Initialize connection
db_manager = DatabaseManager()

# Test connection
is_connected = db_manager.test_connection()

# Insert incident with vector embedding
incident_id = db_manager.insert_incident(incident_data, vector_embedding)

# Vector similarity search
results = db_manager.search_incidents_by_vector(
    query_vector=query_embedding,
    limit=5,
    threshold=0.7
)

# Get summary statistics
stats = db_manager.get_incidents_summary()
```

### Semantic Search (`semantic_search.py`)

The `SemanticSearchEngine` class handles text encoding and vector search.

#### Key Methods:

```python
# Initialize search engine
search_engine = SemanticSearchEngine()

# Encode single text
embedding = search_engine.encode_text("Bird strike during takeoff")

# Encode multiple texts (batch)
embeddings = search_engine.encode_batch(["query1", "query2", "query3"])

# Perform semantic search
results = search_engine.search(
    query="engine failure incidents",
    max_results=5,
    similarity_threshold=0.7
)

# Search with filters
filtered_results = search_engine.search_with_filters(
    query="turbulence incidents",
    filters={"severity": "high", "airline_iata": "AA"}
)
```

### RAG Pipeline (`rag_pipeline.py`)

The `RAGPipeline` class generates natural language answers from search results.

#### Key Methods:

```python
# Initialize RAG pipeline
rag = RAGPipeline()

# Generate summary from search results
summary = rag.generate_summary(incidents, user_query)

# Extract key insights
insights = rag.extract_key_information(incidents)

# Classify incident severity (bonus feature)
severity = rag.classify_incident_severity(description)
```

## Data Models

### Incident Model
```python
{
    "id": int,
    "date": "YYYY-MM-DD",
    "title": str,
    "description": str,
    "route_id": int,
    "source_airport_iata": str,
    "dest_airport_iata": str,
    "airline_iata": str,
    "aircraft_type": str,
    "severity": "low|medium|high",
    "category": str,
    "location_description": str,
    "source_url": str,
    "vector_embedding": List[float],  # 384 dimensions
    "similarity_score": float  # Added during search
}
```

### Search Results Model
```python
{
    "id": int,
    "similarity_score": float,
    "source_airport_name": str,
    "source_city": str,
    "source_country": str,
    "source_lat": float,
    "source_lon": float,
    "dest_airport_name": str,
    "dest_city": str, 
    "dest_country": str,
    "dest_lat": float,
    "dest_lon": float,
    "airline_name": str,
    # ... other incident fields
}
```

## Configuration

### Environment Variables

Required variables:
- `DB_HOST`: Database hostname
- `DB_PORT`: Database port (default: 3306)
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

Optional variables:
- `EMBEDDING_MODEL`: Sentence transformer model name
- `LLM_MODEL`: Question-answering model name
- `MAX_SEARCH_RESULTS`: Maximum results per query
- `SIMILARITY_THRESHOLD`: Minimum similarity score
- `DEBUG`: Enable debug logging
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING)

## Error Handling

### Common Error Cases

1. **Database Connection Errors**
   - Check MariaDB is running
   - Verify connection parameters
   - Ensure database exists

2. **Model Loading Errors**
   - Check internet connection for model downloads
   - Verify sufficient disk space
   - Check model names are correct

3. **Vector Search Errors**
   - Ensure embeddings are generated
   - Check vector dimensions match (384)
   - Verify COSINE_SIMILARITY function is available

4. **Memory Issues**
   - Reduce batch sizes
   - Limit search results
   - Use smaller models

## Performance Optimization

### Batch Processing
```python
# Process embeddings in batches
batch_size = 32
for i in range(0, len(texts), batch_size):
    batch = texts[i:i + batch_size]
    embeddings = search_engine.encode_batch(batch)
```

### Caching
- Model weights are cached after first load
- Database connections are pooled
- Query results can be cached in production

### Indexing
```sql
-- Ensure proper database indexes
CREATE INDEX idx_vector ON incidents(vector_embedding);
CREATE INDEX idx_date ON incidents(date);
CREATE INDEX idx_severity ON incidents(severity);
```