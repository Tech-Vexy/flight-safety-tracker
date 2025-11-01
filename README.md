# Flight Safety Incident Tracker ✈️

**Semantic Insights into Aviation Safety with MariaDB Vector & RAG**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![MariaDB](https://img.shields.io/badge/MariaDB-Vector-orange.svg)](https://mariadb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)](https://streamlit.io/)

An AI-powered tool that enables **natural language querying** of historical flight safety incidents using **MariaDB Vector** for semantic search and a **lightweight RAG pipeline**.

![Demo Screenshot](https://via.placeholder.com/800x400/1f77b4/ffffff?text=Flight+Safety+Tracker+Demo)

## 🚀 Quick Start

### One-Line Setup (Recommended)

**Windows:**
```cmd
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker
setup.bat setup
```

**Linux/macOS:**
```bash
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker
chmod +x setup.sh
./setup.sh setup
```

### Manual Docker Setup

```bash
# Clone the repository
git clone https://github.com/yourname/flight-safety-tracker.git
cd flight-safety-tracker

# Copy environment file
cp .env.example .env

# Start the application
docker-compose up --build

# In another terminal, load data
docker-compose --profile setup run --rm data-loader
```

**🌐 Access the application at: http://localhost:8501**

## 🛠️ Features

- **Natural Language Queries**: Ask questions in plain English about aviation safety
- **Semantic Search**: Powered by MariaDB Vector with sentence transformers
- **RAG Pipeline**: AI-generated summaries using DistilBERT
- **Interactive Maps**: Visualize incident locations with Folium
- **Real Data Integration**: Uses OpenFlights dataset + incident reports

## 📊 Example Queries

```text
"Show me bird strike incidents near Heathrow"
"Any engine failures on flights from Tokyo to Sydney?"
"Safety issues on Delta flights in 2023"
```

## 🏗️ Architecture

- **Database**: MariaDB with Vector extension
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: DistilBERT for answer generation
- **Frontend**: Streamlit with Folium maps
- **Backend**: Python with SQLAlchemy

## 📁 Project Structure

```
flight-safety-tracker/
├── src/
│   ├── app.py                 # Streamlit main application
│   ├── database.py            # Database connection & operations
│   ├── semantic_search.py     # Vector search implementation
│   ├── rag_pipeline.py        # RAG answer generation
│   └── data_loader.py         # Data loading utilities
├── sql/
│   └── setup.sql              # Database schema
├── data/
│   ├── airports.csv           # OpenFlights airports
│   ├── airlines.csv           # OpenFlights airlines
│   └── routes.csv             # OpenFlights routes
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🔧 Development Setup

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run the application
streamlit run src/app.py
```

### Database Setup
```bash
# Start MariaDB container
docker run -d --name mariadb-vector \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=flight_safety \
  -e MYSQL_USER=app \
  -e MYSQL_PASSWORD=apppass \
  -p 3306:3306 \
  mariadb:latest

# Initialize schema
mysql -h localhost -u root -p < sql/setup.sql
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Code formatting
black src/
flake8 src/
```

## 🎯 Demo Queries

Try these example queries to see the system in action:

```text
"Show me bird strike incidents near Heathrow"
"Any engine failures on flights from Tokyo to Sydney?"  
"Safety issues on Delta flights in 2023"
"Turbulence incidents on transatlantic flights"
"Emergency landings due to technical problems"
"What kind of incidents happen during takeoff?"
```

## 🔧 Configuration

Key environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `mariadb` | Database host |
| `DB_NAME` | `flight_safety` | Database name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `LLM_MODEL` | `distilbert-base-cased-distilled-squad` | QA model |
| `MAX_SEARCH_RESULTS` | `5` | Maximum search results |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score |

## 📊 Data Sources

- **OpenFlights Dataset**: Airports, airlines, and routes data
- **Synthetic Incidents**: AI-generated realistic incident reports
- **Future**: Real FAA/NTSB incident feeds (post-MVP)

## 🏗️ Technical Implementation

### Vector Search Pipeline
1. **Text Encoding**: User queries → embeddings via `all-MiniLM-L6-v2`
2. **Similarity Search**: Cosine similarity search in MariaDB Vector
3. **Result Ranking**: Top-K retrieval with configurable threshold

### RAG Pipeline
1. **Context Creation**: Format retrieved incidents
2. **Answer Generation**: DistilBERT Q&A model
3. **Response Enhancement**: Rule-based fallbacks and enrichment

### Database Schema
- **Airports**: OpenFlights airport data with coordinates
- **Airlines**: Carrier information and IATA/ICAO codes
- **Routes**: Flight routes connecting airports
- **Incidents**: Safety incidents with 384-dim vector embeddings

## 🎯 MVP Checklist

- [x] MariaDB schema with Vector extension
- [x] OpenFlights data integration
- [x] Incident reports with embeddings
- [x] Semantic search with cosine similarity
- [x] RAG pipeline for answer generation
- [x] Streamlit web interface
- [x] Interactive Folium maps
- [x] Docker containerization
- [x] Documentation & demo

## 🚀 Future Enhancements

- Real-time FAA/NTSB data feeds
- Incident severity classification
- Multi-language query support
- PDF safety brief export
- Predictive risk scoring
- Mobile application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎬 Demo

[Watch the demo video](https://youtu.be/your-demo-video)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**"Ask in plain English. Fly with confidence."** ✈️