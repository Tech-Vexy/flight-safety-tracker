"""
Flight Safety Incident Tracker - Streamlit Web Application
"""

import os
import sys
import logging
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from semantic_search import SemanticSearchEngine
from rag_pipeline import RAGPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Flight Safety Incident Tracker",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

@st.cache_resource
def initialize_components():
    """Initialize database and AI components"""
    try:
        db_manager = DatabaseManager()
        search_engine = SemanticSearchEngine()
        rag_pipeline = RAGPipeline()
        return db_manager, search_engine, rag_pipeline
    except Exception as e:
        st.error(f"Failed to initialize components: {e}")
        return None, None, None

def create_incident_map(incidents: List[Dict[str, Any]]) -> folium.Map:
    """Create interactive map with incident markers"""
    
    # Default center (roughly middle of US)
    center_lat, center_lon = 39.8283, -98.5795
    
    # If we have incidents with coordinates, center on them
    valid_coords = []
    for incident in incidents:
        if incident.get('source_lat') and incident.get('source_lon'):
            valid_coords.append((incident['source_lat'], incident['source_lon']))
        if incident.get('dest_lat') and incident.get('dest_lon'):
            valid_coords.append((incident['dest_lat'], incident['dest_lon']))
    
    if valid_coords:
        center_lat = sum(coord[0] for coord in valid_coords) / len(valid_coords)
        center_lon = sum(coord[1] for coord in valid_coords) / len(valid_coords)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add incident markers
    for i, incident in enumerate(incidents):
        # Determine marker color by severity
        color_map = {
            'high': 'red',
            'medium': 'orange', 
            'low': 'green'
        }
        color = color_map.get(incident.get('severity', 'medium'), 'blue')
        
        # Create popup content
        popup_content = f"""
        <div style="width: 300px;">
            <h4>{incident.get('title', 'Incident')}</h4>
            <p><strong>Date:</strong> {incident.get('date', 'Unknown')}</p>
            <p><strong>Severity:</strong> {incident.get('severity', 'Unknown')}</p>
            <p><strong>Airline:</strong> {incident.get('airline_name', incident.get('airline_iata', 'Unknown'))}</p>
            <p><strong>Aircraft:</strong> {incident.get('aircraft_type', 'Unknown')}</p>
            <p><strong>Description:</strong> {incident.get('description', '')[:200]}...</p>
            <p><strong>Similarity:</strong> {incident.get('similarity_score', 0):.3f}</p>
        </div>
        """
        
        # Add marker for source airport
        if incident.get('source_lat') and incident.get('source_lon'):
            folium.Marker(
                location=[incident['source_lat'], incident['source_lon']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"Incident {i+1}: {incident.get('source_airport_name', 'Airport')}",
                icon=folium.Icon(color=color, icon='plane')
            ).add_to(m)
        
        # Add marker for destination airport if different
        if (incident.get('dest_lat') and incident.get('dest_lon') and 
            (incident.get('source_lat') != incident.get('dest_lat') or 
             incident.get('source_lon') != incident.get('dest_lon'))):
            
            folium.Marker(
                location=[incident['dest_lat'], incident['dest_lon']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"Incident {i+1}: {incident.get('dest_airport_name', 'Airport')}",
                icon=folium.Icon(color=color, icon='plane-departure')
            ).add_to(m)
    
    return m

def create_severity_chart(incidents: List[Dict[str, Any]]) -> go.Figure:
    """Create severity distribution chart"""
    
    if not incidents:
        return go.Figure()
    
    severities = [inc.get('severity', 'unknown') for inc in incidents]
    severity_counts = pd.Series(severities).value_counts()
    
    colors = {'high': '#ff4444', 'medium': '#ffaa44', 'low': '#44ff44', 'unknown': '#888888'}
    
    fig = go.Figure(data=[
        go.Bar(
            x=severity_counts.index,
            y=severity_counts.values,
            marker_color=[colors.get(sev, '#888888') for sev in severity_counts.index]
        )
    ])
    
    fig.update_layout(
        title="Incident Severity Distribution",
        xaxis_title="Severity Level",
        yaxis_title="Number of Incidents",
        height=300
    )
    
    return fig

def create_timeline_chart(incidents: List[Dict[str, Any]]) -> go.Figure:
    """Create timeline of incidents"""
    
    if not incidents:
        return go.Figure()
    
    # Extract dates
    dates = []
    for inc in incidents:
        if inc.get('date'):
            try:
                if isinstance(inc['date'], str):
                    date_obj = datetime.strptime(inc['date'], '%Y-%m-%d')
                else:
                    date_obj = inc['date']
                dates.append(date_obj)
            except:
                continue
    
    if not dates:
        return go.Figure()
    
    # Create monthly aggregation
    df = pd.DataFrame({'date': dates})
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_counts = df['year_month'].value_counts().sort_index()
    
    fig = go.Figure(data=[
        go.Scatter(
            x=[str(period) for period in monthly_counts.index],
            y=monthly_counts.values,
            mode='lines+markers',
            line=dict(color='#1f77b4')
        )
    ])
    
    fig.update_layout(
        title="Incidents Over Time",
        xaxis_title="Month",
        yaxis_title="Number of Incidents",
        height=300
    )
    
    return fig

def display_incident_details(incidents: List[Dict[str, Any]]):
    """Display detailed incident information"""
    
    if not incidents:
        st.info("No incidents found for your query.")
        return
    
    for i, incident in enumerate(incidents, 1):
        with st.expander(f"🔍 Incident {i}: {incident.get('title', 'Unknown Title')}", expanded=i==1):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Basic Information:**")
                st.write(f"📅 **Date:** {incident.get('date', 'Unknown')}")
                st.write(f"⚠️ **Severity:** {incident.get('severity', 'Unknown')}")
                st.write(f"📊 **Similarity Score:** {incident.get('similarity_score', 0):.3f}")
            
            with col2:
                st.write("**Flight Details:**")
                airline = incident.get('airline_name', incident.get('airline_iata', 'Unknown'))
                st.write(f"✈️ **Airline:** {airline}")
                st.write(f"🛩️ **Aircraft:** {incident.get('aircraft_type', 'Unknown')}")
                st.write(f"🏷️ **Category:** {incident.get('category', 'Unknown')}")
            
            with col3:
                st.write("**Route Information:**")
                source = incident.get('source_airport_name', incident.get('source_airport_iata', 'Unknown'))
                dest = incident.get('dest_airport_name', incident.get('dest_airport_iata', 'Unknown'))
                st.write(f"🛫 **From:** {source}")
                st.write(f"🛬 **To:** {dest}")
            
            st.write("**Description:**")
            st.write(incident.get('description', 'No description available.'))
            
            if incident.get('source_url'):
                st.write(f"**Source:** [View Report]({incident['source_url']})")

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("✈️ Flight Safety Incident Tracker")
    st.markdown("*Ask in plain English. Fly with confidence.*")
    
    # Initialize components
    with st.spinner("Initializing AI components..."):
        db_manager, search_engine, rag_pipeline = initialize_components()
    
    if not all([db_manager, search_engine, rag_pipeline]):
        st.error("Failed to initialize application components. Please check your database connection.")
        return
    
    # Test database connection
    if not db_manager.test_connection():
        st.error("❌ Cannot connect to database. Please ensure MariaDB is running.")
        return
    
    st.success("✅ Connected to database successfully!")
    
    # Sidebar with statistics and filters
    with st.sidebar:
        st.header("📊 Database Statistics")
        
        with st.spinner("Loading statistics..."):
            stats = db_manager.get_incidents_summary()
        
        st.metric("Total Incidents", stats.get('total_incidents', 0))
        
        if stats.get('by_severity'):
            st.write("**By Severity:**")
            for severity, count in stats['by_severity'].items():
                st.write(f"• {severity.title()}: {count}")
        
        st.header("⚙️ Search Settings")
        
        max_results = st.slider("Max Results", 1, 20, 5)
        similarity_threshold = st.slider("Similarity Threshold", 0.1, 1.0, 0.7, 0.1)
        
        st.header("💡 Example Queries")
        example_queries = [
            "Bird strike incidents near Heathrow",
            "Engine failures on flights from Tokyo to Sydney", 
            "Delta flights safety issues in 2023",
            "Turbulence incidents on transatlantic flights",
            "Emergency landings due to technical problems"
        ]
        
        for query in example_queries:
            if st.button(f"🔍 {query}", key=f"example_{query}", use_container_width=True):
                st.session_state.example_query = query
    
    # Main search interface
    st.header("🔍 Search Flight Safety Incidents")
    
    # Query input
    query_input = st.text_input(
        "Enter your question about flight safety incidents:",
        value=st.session_state.get('example_query', ''),
        placeholder="e.g., 'Show me bird strikes at JFK airport' or 'Any engine problems on Boeing 737?'",
        help="Ask questions in natural language about aviation safety incidents"
    )
    
    # Clear example query after use
    if 'example_query' in st.session_state:
        del st.session_state.example_query
    
    # Search button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_clicked = st.button("🔍 Search Incidents", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Clear Results", use_container_width=True):
            st.session_state.search_results = []
            st.rerun()
    
    with col3:
        if st.button("📝 Query History", use_container_width=True):
            if st.session_state.query_history:
                st.write("**Recent Queries:**")
                for i, query in enumerate(reversed(st.session_state.query_history[-5:])):
                    st.write(f"{i+1}. {query}")
            else:
                st.info("No query history yet.")
    
    # Perform search
    if search_clicked and query_input:
        
        # Add to query history
        if query_input not in st.session_state.query_history:
            st.session_state.query_history.append(query_input)
        
        with st.spinner(f"Searching for incidents related to: '{query_input}'..."):
            
            # Perform semantic search
            results = search_engine.search(
                query=query_input,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            st.session_state.search_results = results
        
        if results:
            st.success(f"Found {len(results)} relevant incidents!")
        else:
            st.warning("No incidents found matching your query. Try adjusting the similarity threshold or rephrasing your question.")
    
    # Display results
    if st.session_state.search_results:
        
        results = st.session_state.search_results
        
        # Generate AI summary
        st.header("🤖 AI Summary")
        
        with st.spinner("Generating AI summary..."):
            summary = rag_pipeline.generate_summary(results, query_input)
        
        st.info(summary)
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map View", "📋 Detailed Results", "📊 Analytics", "📈 Charts"])
        
        with tab1:
            st.header("Incident Locations")
            
            if any(r.get('source_lat') for r in results):
                incident_map = create_incident_map(results)
                st_folium(incident_map, width=700, height=500)
            else:
                st.warning("No location data available for these incidents.")
        
        with tab2:
            st.header("Incident Details")
            display_incident_details(results)
        
        with tab3:
            st.header("Analytics Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Key insights
                insights = rag_pipeline.extract_key_information(results)
                
                st.subheader("📊 Key Insights")
                st.write(f"**Total Incidents:** {insights.get('total_incidents', 0)}")
                
                if insights.get('severity_distribution'):
                    st.write("**Severity Distribution:**")
                    for sev, count in insights['severity_distribution'].items():
                        st.write(f"• {sev.title()}: {count}")
                
                if insights.get('time_range'):
                    st.write(f"**Time Range:** {insights['time_range']['earliest']} to {insights['time_range']['latest']}")
            
            with col2:
                # Common patterns
                if insights.get('common_airlines'):
                    st.subheader("✈️ Airlines Involved")
                    for airline, count in list(insights['common_airlines'].items())[:5]:
                        st.write(f"• {airline}: {count}")
                
                if insights.get('common_aircraft'):
                    st.subheader("🛩️ Aircraft Types")
                    for aircraft, count in list(insights['common_aircraft'].items())[:5]:
                        st.write(f"• {aircraft}: {count}")
        
        with tab4:
            st.header("Visual Analytics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                severity_fig = create_severity_chart(results)
                st.plotly_chart(severity_fig, use_container_width=True)
            
            with col2:
                timeline_fig = create_timeline_chart(results)
                st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Flight Safety Incident Tracker** | "
        "Powered by MariaDB Vector, Sentence Transformers & DistilBERT | "
        "[GitHub Repository](https://github.com/yourname/flight-safety-tracker)"
    )

if __name__ == "__main__":
    main()