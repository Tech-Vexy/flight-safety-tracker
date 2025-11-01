"""
Semantic search implementation using sentence transformers and MariaDB Vector
"""

import os
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from database import DatabaseManager

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """Handles semantic search using embeddings and MariaDB Vector"""
    
    def __init__(self):
        self.model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(self.model_name)
        self.db_manager = DatabaseManager()
        
        logger.info(f"Initialized semantic search with model: {self.model_name}")
    
    def encode_text(self, text: str) -> List[float]:
        """Encode text into vector embedding"""
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Ensure it's a numpy array and convert to list
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts efficiently"""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False, batch_size=32)
            
            # Convert to list of lists
            if isinstance(embeddings, np.ndarray):
                return embeddings.tolist()
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        max_results: int = None, 
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search for incidents using semantic similarity
        
        Args:
            query: Natural language query
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score threshold
            
        Returns:
            List of incident dictionaries with similarity scores
        """
        
        # Use environment defaults if not specified
        if max_results is None:
            max_results = int(os.getenv('MAX_SEARCH_RESULTS', 5))
        if similarity_threshold is None:
            similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
        
        try:
            # Encode the query
            query_vector = self.encode_text(query)
            
            # Search in database
            results = self.db_manager.search_incidents_by_vector(
                query_vector=query_vector,
                limit=max_results,
                threshold=similarity_threshold
            )
            
            logger.info(f"Found {len(results)} incidents for query: '{query[:50]}...'")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    def search_with_filters(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        max_results: int = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Search with additional filters (future enhancement)
        
        Args:
            query: Natural language query
            filters: Dictionary of filters (e.g., {'severity': 'high', 'year': 2023})
            max_results: Maximum results
            similarity_threshold: Similarity threshold
            
        Returns:
            Filtered search results
        """
        # For now, just do basic search
        # TODO: Implement SQL-level filtering
        results = self.search(query, max_results, similarity_threshold)
        
        if not filters:
            return results
        
        # Apply filters in Python (could be optimized with SQL)
        filtered_results = []
        for result in results:
            match = True
            
            for key, value in filters.items():
                if key in result and result[key] != value:
                    match = False
                    break
            
            if match:
                filtered_results.append(result)
        
        return filtered_results
    
    def get_similar_incidents(self, incident_id: int, max_results: int = 5) -> List[Dict[str, Any]]:
        """Find incidents similar to a given incident"""
        try:
            # Get the incident
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(
                    text("SELECT description FROM incidents WHERE id = :id"),
                    {'id': incident_id}
                )
                row = result.fetchone()
                
                if not row:
                    return []
                
                description = row[0]
            
            # Search for similar incidents
            results = self.search(description, max_results + 1)  # +1 to exclude self
            
            # Remove the original incident from results
            filtered_results = [r for r in results if r['id'] != incident_id]
            
            return filtered_results[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to find similar incidents for ID {incident_id}: {e}")
            return []
    
    def get_embedding_dimensions(self) -> int:
        """Get the dimension of embeddings from this model"""
        return self.model.get_sentence_embedding_dimension()
    
    def precompute_embeddings_for_incidents(self) -> bool:
        """
        Precompute embeddings for all incidents that don't have them
        (Used during data loading)
        """
        try:
            with self.db_manager.engine.connect() as conn:
                from sqlalchemy import text
                
                # Get incidents without embeddings
                result = conn.execute(text("""
                    SELECT id, description 
                    FROM incidents 
                    WHERE vector_embedding IS NULL
                """))
                
                incidents_to_process = result.fetchall()
                
                if not incidents_to_process:
                    logger.info("All incidents already have embeddings")
                    return True
                
                logger.info(f"Processing embeddings for {len(incidents_to_process)} incidents")
                
                # Process in batches
                batch_size = 32
                for i in range(0, len(incidents_to_process), batch_size):
                    batch = incidents_to_process[i:i + batch_size]
                    
                    # Extract descriptions and IDs
                    descriptions = [incident[1] for incident in batch]
                    incident_ids = [incident[0] for incident in batch]
                    
                    # Generate embeddings
                    embeddings = self.encode_batch(descriptions)
                    
                    # Update database
                    for incident_id, embedding in zip(incident_ids, embeddings):
                        vector_str = '[' + ','.join(map(str, embedding)) + ']'
                        
                        conn.execute(text("""
                            UPDATE incidents 
                            SET vector_embedding = :embedding 
                            WHERE id = :id
                        """), {
                            'embedding': vector_str,
                            'id': incident_id
                        })
                    
                    conn.commit()
                    logger.info(f"Processed batch {i//batch_size + 1}/{(len(incidents_to_process)-1)//batch_size + 1}")
                
                logger.info("Successfully precomputed all embeddings")
                return True
                
        except Exception as e:
            logger.error(f"Failed to precompute embeddings: {e}")
            return False