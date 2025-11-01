-- Flight Safety Incident Tracker Database Schema
-- MariaDB with Vector Extension

CREATE DATABASE IF NOT EXISTS flight_safety;
USE flight_safety;

-- Create application user
CREATE USER IF NOT EXISTS 'app'@'%' IDENTIFIED BY 'apppass';
GRANT ALL PRIVILEGES ON flight_safety.* TO 'app'@'%';
FLUSH PRIVILEGES;

-- Airlines table (OpenFlights data)
CREATE TABLE airlines (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(255),
    iata VARCHAR(3),
    icao VARCHAR(4),
    callsign VARCHAR(255),
    country VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    INDEX idx_iata (iata),
    INDEX idx_icao (icao)
);

-- Airports table (OpenFlights data)
CREATE TABLE airports (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    country VARCHAR(255),
    iata VARCHAR(3),
    icao VARCHAR(4),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    altitude INT,
    timezone_offset DECIMAL(3, 1),
    dst CHAR(1),
    timezone VARCHAR(255),
    type VARCHAR(50),
    source VARCHAR(50),
    INDEX idx_iata (iata),
    INDEX idx_icao (icao),
    INDEX idx_country (country),
    SPATIAL INDEX idx_coordinates (POINT(latitude, longitude))
);

-- Routes table (OpenFlights data)
CREATE TABLE routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    airline_id INT,
    airline_iata VARCHAR(3),
    source_airport_id INT,
    source_airport_iata VARCHAR(3),
    dest_airport_id INT,
    dest_airport_iata VARCHAR(3),
    codeshare BOOLEAN,
    stops INT,
    equipment TEXT,
    INDEX idx_airline (airline_id),
    INDEX idx_source_airport (source_airport_id),
    INDEX idx_dest_airport (dest_airport_id),
    FOREIGN KEY (airline_id) REFERENCES airlines(id) ON DELETE SET NULL,
    FOREIGN KEY (source_airport_id) REFERENCES airports(id) ON DELETE SET NULL,
    FOREIGN KEY (dest_airport_id) REFERENCES airports(id) ON DELETE SET NULL
);

-- Incidents table with Vector embeddings
CREATE TABLE incidents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    title VARCHAR(500),
    description TEXT NOT NULL,
    route_id INT,
    source_airport_iata VARCHAR(3),
    dest_airport_iata VARCHAR(3),
    airline_iata VARCHAR(3),
    aircraft_type VARCHAR(100),
    severity ENUM('low', 'medium', 'high') DEFAULT 'medium',
    category VARCHAR(100),
    location_description TEXT,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Vector embedding for semantic search (384 dimensions for all-MiniLM-L6-v2)
    vector_embedding VECTOR(384),
    INDEX idx_date (date),
    INDEX idx_route (route_id),
    INDEX idx_source_airport (source_airport_iata),
    INDEX idx_dest_airport (dest_airport_iata),
    INDEX idx_airline (airline_iata),
    INDEX idx_severity (severity),
    INDEX idx_category (category),
    -- Vector index for similarity search
    INDEX idx_vector (vector_embedding),
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE SET NULL
);

-- Create views for common queries
CREATE VIEW incident_details AS
SELECT 
    i.id,
    i.date,
    i.title,
    i.description,
    i.severity,
    i.category,
    i.aircraft_type,
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
    al.name as airline_name,
    i.source_url,
    i.created_at
FROM incidents i
LEFT JOIN airports sa ON i.source_airport_iata = sa.iata
LEFT JOIN airports da ON i.dest_airport_iata = da.iata
LEFT JOIN airlines al ON i.airline_iata = al.iata;

-- Insert sample data for testing
-- Sample airlines
INSERT INTO airlines (id, name, alias, iata, icao, callsign, country, active) VALUES
(1, 'American Airlines', 'American', 'AA', 'AAL', 'AMERICAN', 'United States', TRUE),
(2, 'Delta Air Lines', 'Delta', 'DL', 'DAL', 'DELTA', 'United States', TRUE),
(3, 'United Airlines', 'United', 'UA', 'UAL', 'UNITED', 'United States', TRUE),
(4, 'British Airways', 'British Airways', 'BA', 'BAW', 'SPEEDBIRD', 'United Kingdom', TRUE),
(5, 'Lufthansa', 'Lufthansa', 'LH', 'DLH', 'LUFTHANSA', 'Germany', TRUE);

-- Sample airports
INSERT INTO airports (id, name, city, country, iata, icao, latitude, longitude, altitude, timezone_offset, dst, timezone, type, source) VALUES
(1, 'John F Kennedy International Airport', 'New York', 'United States', 'JFK', 'KJFK', 40.639751, -73.778925, 13, -5, 'A', 'America/New_York', 'airport', 'OurAirports'),
(2, 'Los Angeles International Airport', 'Los Angeles', 'United States', 'LAX', 'KLAX', 33.942536, -118.408075, 125, -8, 'A', 'America/Los_Angeles', 'airport', 'OurAirports'),
(3, 'London Heathrow Airport', 'London', 'United Kingdom', 'LHR', 'EGLL', 51.4706, -0.461941, 25, 0, 'E', 'Europe/London', 'airport', 'OurAirports'),
(4, 'Tokyo Haneda Airport', 'Tokyo', 'Japan', 'HND', 'RJTT', 35.5494, 139.7798, 21, 9, 'U', 'Asia/Tokyo', 'airport', 'OurAirports'),
(5, 'Sydney Kingsford Smith Airport', 'Sydney', 'Australia', 'SYD', 'YSSY', -33.9399, 151.1753, 21, 10, 'O', 'Australia/Sydney', 'airport', 'OurAirports');

-- Sample routes
INSERT INTO routes (airline_id, airline_iata, source_airport_id, source_airport_iata, dest_airport_id, dest_airport_iata, codeshare, stops, equipment) VALUES
(1, 'AA', 1, 'JFK', 2, 'LAX', FALSE, 0, 'A321'),
(2, 'DL', 1, 'JFK', 2, 'LAX', FALSE, 0, 'A330'),
(4, 'BA', 1, 'JFK', 3, 'LHR', FALSE, 0, 'B777'),
(3, 'UA', 4, 'HND', 5, 'SYD', FALSE, 0, 'B787');

-- Note: Vector embeddings will be populated by the data loader script