"""
Data loading utilities for OpenFlights data and incident generation
"""

import os
import csv
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import requests
from tqdm import tqdm
from database import DatabaseManager
from semantic_search import SemanticSearchEngine

logger = logging.getLogger(__name__)

class DataLoader:
    """Handles loading of OpenFlights data and synthetic incident generation"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.search_engine = SemanticSearchEngine()
        
    def download_openflights_data(self, data_dir: str = "data") -> bool:
        """Download OpenFlights dataset"""
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # URLs for OpenFlights data
        urls = {
            'airports.dat': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat',
            'airlines.dat': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat',
            'routes.dat': 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat'
        }
        
        try:
            for filename, url in urls.items():
                file_path = os.path.join(data_dir, filename)
                
                if os.path.exists(file_path):
                    logger.info(f"File {filename} already exists, skipping download")
                    continue
                
                logger.info(f"Downloading {filename} from OpenFlights...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Successfully downloaded {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download OpenFlights data: {e}")
            return False
    
    def load_airports(self, data_dir: str = "data") -> bool:
        """Load airports data into database"""
        file_path = os.path.join(data_dir, "airports.dat")
        
        if not os.path.exists(file_path):
            logger.error(f"Airports file not found: {file_path}")
            return False
        
        try:
            airports_data = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 14:
                        # Parse airport data
                        airport = {
                            'id': int(row[0]) if row[0].isdigit() else None,
                            'name': row[1].replace('"', ''),
                            'city': row[2].replace('"', ''),
                            'country': row[3].replace('"', ''),
                            'iata': row[4].replace('"', '') if row[4] != '\\N' else None,
                            'icao': row[5].replace('"', '') if row[5] != '\\N' else None,
                            'latitude': float(row[6]) if row[6] != '\\N' else None,
                            'longitude': float(row[7]) if row[7] != '\\N' else None,
                            'altitude': int(row[8]) if row[8].isdigit() else None,
                            'timezone_offset': float(row[9]) if row[9] != '\\N' else None,
                            'dst': row[10] if row[10] != '\\N' else None,
                            'timezone': row[11].replace('"', '') if row[11] != '\\N' else None,
                            'type': row[12].replace('"', '') if row[12] != '\\N' else 'airport',
                            'source': row[13].replace('"', '') if row[13] != '\\N' else 'OurAirports'
                        }
                        
                        if airport['id'] and airport['iata']:
                            airports_data.append(airport)
            
            # Insert into database using pandas for efficiency
            df = pd.DataFrame(airports_data)
            df.to_sql('airports', self.db_manager.engine, if_exists='replace', index=False, method='multi')
            
            logger.info(f"Loaded {len(airports_data)} airports into database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load airports: {e}")
            return False
    
    def load_airlines(self, data_dir: str = "data") -> bool:
        """Load airlines data into database"""
        file_path = os.path.join(data_dir, "airlines.dat")
        
        if not os.path.exists(file_path):
            logger.error(f"Airlines file not found: {file_path}")
            return False
        
        try:
            airlines_data = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 8:
                        airline = {
                            'id': int(row[0]) if row[0].isdigit() else None,
                            'name': row[1].replace('"', ''),
                            'alias': row[2].replace('"', '') if row[2] != '\\N' else None,
                            'iata': row[3].replace('"', '') if row[3] != '\\N' else None,
                            'icao': row[4].replace('"', '') if row[4] != '\\N' else None,
                            'callsign': row[5].replace('"', '') if row[5] != '\\N' else None,
                            'country': row[6].replace('"', '') if row[6] != '\\N' else None,
                            'active': row[7] == 'Y' if row[7] in ['Y', 'N'] else True
                        }
                        
                        if airline['id'] and (airline['iata'] or airline['icao']):
                            airlines_data.append(airline)
            
            # Insert into database
            df = pd.DataFrame(airlines_data)
            df.to_sql('airlines', self.db_manager.engine, if_exists='replace', index=False, method='multi')
            
            logger.info(f"Loaded {len(airlines_data)} airlines into database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load airlines: {e}")
            return False
    
    def load_routes(self, data_dir: str = "data") -> bool:
        """Load routes data into database"""
        file_path = os.path.join(data_dir, "routes.dat")
        
        if not os.path.exists(file_path):
            logger.error(f"Routes file not found: {file_path}")
            return False
        
        try:
            routes_data = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 9:
                        route = {
                            'airline_iata': row[0] if row[0] != '\\N' else None,
                            'airline_id': int(row[1]) if row[1].isdigit() else None,
                            'source_airport_iata': row[2] if row[2] != '\\N' else None,
                            'source_airport_id': int(row[3]) if row[3].isdigit() else None,
                            'dest_airport_iata': row[4] if row[4] != '\\N' else None,
                            'dest_airport_id': int(row[5]) if row[5].isdigit() else None,
                            'codeshare': row[6] == 'Y' if row[6] in ['Y', 'N'] else False,
                            'stops': int(row[7]) if row[7].isdigit() else 0,
                            'equipment': row[8] if len(row) > 8 and row[8] != '\\N' else None
                        }
                        
                        if route['source_airport_iata'] and route['dest_airport_iata']:
                            routes_data.append(route)
            
            # Insert into database (limit to reasonable number for demo)
            df = pd.DataFrame(routes_data[:50000])  # Limit for demo
            df.to_sql('routes', self.db_manager.engine, if_exists='replace', index=False, method='multi')
            
            logger.info(f"Loaded {len(df)} routes into database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load routes: {e}")
            return False
    
    def generate_synthetic_incidents(self, num_incidents: int = 100) -> bool:
        """Generate synthetic incident reports"""
        
        try:
            # Get some routes and airports for realistic incidents
            routes_df = pd.read_sql("SELECT * FROM routes LIMIT 500", self.db_manager.engine)
            airports_df = pd.read_sql("SELECT * FROM airports WHERE iata IS NOT NULL LIMIT 200", self.db_manager.engine)
            
            if routes_df.empty or airports_df.empty:
                logger.error("No routes or airports found in database")
                return False
            
            # Incident templates and keywords for generation
            incident_templates = [
                # Bird strikes
                "Bird strike occurred during {phase} at {airport}. Aircraft experienced {impact} to {component}. {outcome}",
                "Multiple bird strikes reported near {airport} during {phase}. {aircraft} sustained damage to {component}. {action_taken}",
                
                # Weather incidents
                "Severe turbulence encountered on flight from {source} to {dest}. {injuries} reported among passengers. {action_taken}",
                "Lightning strike reported on {aircraft} during approach to {airport}. {inspection} required. {outcome}",
                
                # Technical issues
                "Engine malfunction reported on {aircraft} flight {flight_num}. Emergency procedures initiated. {outcome}",
                "Hydraulic system failure on {aircraft} resulted in {action_taken}. {outcome}",
                "Smoke in cabin reported during flight from {source} to {dest}. {action_taken}",
                
                # Ground incidents  
                "Ground collision occurred at {airport} between {aircraft} and ground equipment. {damage} reported.",
                "Runway incursion at {airport} involving {aircraft}. Traffic control intervention prevented collision.",
                
                # Medical emergencies
                "Medical emergency declared on flight from {source} to {dest}. {action_taken}",
                "Passenger medical emergency required diversion to {airport}. Emergency services met aircraft."
            ]
            
            # Variables for template filling
            phases = ["takeoff", "landing", "approach", "departure", "climb", "descent"]
            impacts = ["minor damage", "significant damage", "superficial damage", "no damage"]
            components = ["engine", "windshield", "wing", "nose cone", "landing gear", "fuselage"]
            outcomes = [
                "Flight continued safely", "Aircraft returned to gate", "Emergency landing performed",
                "Aircraft continued to destination", "Maintenance inspection required"
            ]
            actions_taken = [
                "Emergency landing at nearest airport", "Flight diverted", "Precautionary landing",
                "Flight continued normally", "Aircraft met by emergency services"
            ]
            aircraft_types = ["B737", "A320", "B777", "A330", "B787", "A321", "B767", "A319"]
            severities = ["low", "medium", "high"]
            categories = [
                "Bird Strike", "Weather", "Technical Failure", "Ground Operations",
                "Medical Emergency", "Security", "Air Traffic Control"
            ]
            
            incidents_data = []
            
            logger.info(f"Generating {num_incidents} synthetic incidents...")
            
            for i in tqdm(range(num_incidents)):
                # Select random route
                route = routes_df.sample(1).iloc[0]
                
                # Get airport details
                source_airport = airports_df[airports_df['iata'] == route['source_airport_iata']]
                dest_airport = airports_df[airports_df['iata'] == route['dest_airport_iata']]
                
                if source_airport.empty or dest_airport.empty:
                    continue
                
                source_name = source_airport.iloc[0]['name']
                dest_name = dest_airport.iloc[0]['name']
                
                # Generate random date (last 5 years)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5*365)
                random_date = start_date + timedelta(
                    seconds=random.randint(0, int((end_date - start_date).total_seconds()))
                )
                
                # Select template and fill variables
                template = random.choice(incident_templates)
                
                # Fill template variables
                description = template.format(
                    phase=random.choice(phases),
                    airport=random.choice([source_name, dest_name]),
                    impact=random.choice(impacts),
                    component=random.choice(components),
                    outcome=random.choice(outcomes),
                    aircraft=random.choice(aircraft_types),
                    injuries=random.choice(["No injuries", "Minor injuries", "Several injuries"]),
                    action_taken=random.choice(actions_taken),
                    inspection=random.choice(["Thorough inspection", "Visual inspection", "Technical inspection"]),
                    source=source_name,
                    dest=dest_name,
                    flight_num=f"{route['airline_iata']}{random.randint(100, 9999)}",
                    damage=random.choice(["Minor damage", "No damage", "Significant damage"])
                )
                
                # Generate title
                category = random.choice(categories)
                title = f"{category} - {route['airline_iata']} Flight {route['source_airport_iata']} to {route['dest_airport_iata']}"
                
                incident = {
                    'date': random_date.date(),
                    'title': title,
                    'description': description,
                    'route_id': route.name + 1,  # Assuming sequential IDs
                    'source_airport_iata': route['source_airport_iata'],
                    'dest_airport_iata': route['dest_airport_iata'],
                    'airline_iata': route['airline_iata'],
                    'aircraft_type': random.choice(aircraft_types),
                    'severity': random.choice(severities),
                    'category': category,
                    'location_description': f"Near {random.choice([source_name, dest_name])}",
                    'source_url': f"https://aviation-safety.net/incident/{random.randint(100000, 999999)}"
                }
                
                incidents_data.append(incident)
            
            # Insert incidents in batches
            batch_size = 10
            
            for i in range(0, len(incidents_data), batch_size):
                batch = incidents_data[i:i + batch_size]
                
                # Generate embeddings for this batch
                descriptions = [inc['description'] for inc in batch]
                embeddings = self.search_engine.encode_batch(descriptions)
                
                # Insert each incident with its embedding
                for incident, embedding in zip(batch, embeddings):
                    self.db_manager.insert_incident(incident, embedding)
            
            logger.info(f"Successfully generated and loaded {len(incidents_data)} synthetic incidents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate synthetic incidents: {e}")
            return False
    
    def load_all_data(self, data_dir: str = "data", num_incidents: int = 100) -> bool:
        """Load all data: OpenFlights + synthetic incidents"""
        
        logger.info("Starting complete data loading process...")
        
        # Download OpenFlights data
        if not self.download_openflights_data(data_dir):
            return False
        
        # Load airports first (referenced by routes)
        if not self.load_airports(data_dir):
            return False
        
        # Load airlines
        if not self.load_airlines(data_dir):
            return False
        
        # Load routes
        if not self.load_routes(data_dir):
            return False
        
        # Generate synthetic incidents
        if not self.generate_synthetic_incidents(num_incidents):
            return False
        
        logger.info("Data loading completed successfully!")
        return True

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load data
    loader = DataLoader()
    success = loader.load_all_data(num_incidents=150)
    
    if success:
        print("✅ All data loaded successfully!")
    else:
        print("❌ Data loading failed!")