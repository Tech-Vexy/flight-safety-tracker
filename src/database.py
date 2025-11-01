"""
Database connection and operations for Flight Safety Tracker
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine for MariaDB"""
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '3306')
        db_name = os.getenv('DB_NAME', 'flight_safety')
        db_user = os.getenv('DB_USER', 'app')
        db_password = os.getenv('DB_PASSWORD', 'apppass')
        
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        return engine
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def execute_sql_file(self, sql_file_path: str) -> bool:
        """Execute SQL file"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # Split by semicolon and execute each statement
            statements = sql_content.split(';')
            
            with self.engine.connect() as conn:
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                        conn.commit()
            
            logger.info(f"Successfully executed SQL file: {sql_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute SQL file {sql_file_path}: {e}")
            return False
    
    def insert_incident(self, incident_data: Dict[str, Any], vector_embedding: List[float]) -> int:
        """Insert a new incident with vector embedding"""
        try:
            with self.engine.connect() as conn:
                # Convert vector to string format for MariaDB
                vector_str = '[' + ','.join(map(str, vector_embedding)) + ']'
                
                sql = text("""
                    INSERT INTO incidents (
                        date, title, description, route_id, source_airport_iata, 
                        dest_airport_iata, airline_iata, aircraft_type, severity, 
                        category, location_description, source_url, vector_embedding
                    ) VALUES (
                        :date, :title, :description, :route_id, :source_airport_iata,
                        :dest_airport_iata, :airline_iata, :aircraft_type, :severity,
                        :category, :location_description, :source_url, :vector_embedding
                    )
                """)
                
                result = conn.execute(sql, {
                    **incident_data,
                    'vector_embedding': vector_str
                })
                conn.commit()
                
                return result.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to insert incident: {e}")
            raise
    
    def search_incidents_by_vector(
        self, 
        query_vector: List[float], 
        limit: int = 5, 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search incidents using vector similarity"""
        try:
            vector_str = '[' + ','.join(map(str, query_vector)) + ']'
            
            sql = text("""
                SELECT 
                    i.*,
                    COSINE_SIMILARITY(i.vector_embedding, :query_vector) AS similarity_score,
                    sa.name as source_airport_name,
                    sa.city as source_city,
                    sa.country as source_country,
                    sa.latitude as source_lat,
                    sa.longitude as source_lon,
                    da.name as dest_airport_name,
                    da.city as dest_city,
                    da.country as dest_country,
                    da.latitude as dest_lat,
                    da.longitude as dest_lon,
                    al.name as airline_name
                FROM incidents i
                LEFT JOIN airports sa ON i.source_airport_iata = sa.iata
                LEFT JOIN airports da ON i.dest_airport_iata = da.iata
                LEFT JOIN airlines al ON i.airline_iata = al.iata
                WHERE COSINE_SIMILARITY(i.vector_embedding, :query_vector) > :threshold
                ORDER BY similarity_score DESC
                LIMIT :limit
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(sql, {
                    'query_vector': vector_str,
                    'threshold': threshold,
                    'limit': limit
                })
                
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def get_airports(self) -> pd.DataFrame:
        """Get all airports data"""
        sql = "SELECT * FROM airports"
        return pd.read_sql(sql, self.engine)
    
    def get_airlines(self) -> pd.DataFrame:
        """Get all airlines data"""
        sql = "SELECT * FROM airlines"
        return pd.read_sql(sql, self.engine)
    
    def get_routes(self) -> pd.DataFrame:
        """Get all routes data"""
        sql = "SELECT * FROM routes"
        return pd.read_sql(sql, self.engine)
    
    def get_incidents_summary(self) -> Dict[str, Any]:
        """Get summary statistics of incidents"""
        try:
            with self.engine.connect() as conn:
                # Total incidents
                total_result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
                total_incidents = total_result.fetchone()[0]
                
                # By severity
                severity_result = conn.execute(text("""
                    SELECT severity, COUNT(*) as count 
                    FROM incidents 
                    GROUP BY severity
                """))
                severity_counts = dict(severity_result.fetchall())
                
                # By year
                year_result = conn.execute(text("""
                    SELECT YEAR(date) as year, COUNT(*) as count 
                    FROM incidents 
                    GROUP BY YEAR(date)
                    ORDER BY year DESC
                    LIMIT 5
                """))
                year_counts = dict(year_result.fetchall())
                
                return {
                    'total_incidents': total_incidents,
                    'by_severity': severity_counts,
                    'by_year': year_counts
                }
                
        except Exception as e:
            logger.error(f"Failed to get incident summary: {e}")
            return {'total_incidents': 0, 'by_severity': {}, 'by_year': {}}