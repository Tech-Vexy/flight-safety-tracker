"""
RAG (Retrieval-Augmented Generation) pipeline for generating answers
"""

import os
import logging
from typing import List, Dict, Any
from transformers import pipeline, AutoTokenizer, AutoModelForQuestionAnswering

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Handles answer generation using retrieved context"""
    
    def __init__(self):
        self.model_name = os.getenv('LLM_MODEL', 'distilbert-base-cased-distilled-squad')
        
        # Initialize the question-answering pipeline
        try:
            self.qa_pipeline = pipeline(
                "question-answering",
                model=self.model_name,
                tokenizer=self.model_name,
                return_confidence_score=True
            )
            logger.info(f"Initialized RAG pipeline with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load {self.model_name}, using fallback")
            # Fallback to a smaller, more reliable model
            self.qa_pipeline = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                return_confidence_score=True
            )
    
    def generate_summary(self, incidents: List[Dict[str, Any]], query: str) -> str:
        """
        Generate a natural language summary of retrieved incidents
        
        Args:
            incidents: List of incident dictionaries from semantic search
            query: Original user query
            
        Returns:
            Generated summary text
        """
        if not incidents:
            return "No relevant incidents found for your query."
        
        try:
            # Create context from incidents
            context = self._create_context_from_incidents(incidents)
            
            # Generate answer using QA model
            if len(context) > 512:  # Truncate if too long
                context = context[:512]
            
            result = self.qa_pipeline(question=query, context=context)
            
            # If confidence is too low, create a rule-based summary
            if result['score'] < 0.3:
                return self._create_rule_based_summary(incidents, query)
            
            # Enhance the answer with incident count and severity info
            enhanced_answer = self._enhance_answer(result['answer'], incidents)
            
            return enhanced_answer
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return self._create_rule_based_summary(incidents, query)
    
    def _create_context_from_incidents(self, incidents: List[Dict[str, Any]]) -> str:
        """Create a coherent context string from incident data"""
        context_parts = []
        
        for i, incident in enumerate(incidents[:3], 1):  # Use top 3 incidents
            # Format incident information
            date = incident.get('date', 'Unknown date')
            description = incident.get('description', '')
            severity = incident.get('severity', 'unknown')
            airline = incident.get('airline_name', incident.get('airline_iata', 'Unknown airline'))
            aircraft = incident.get('aircraft_type', 'Unknown aircraft')
            
            source_airport = incident.get('source_airport_name') or incident.get('source_airport_iata', '')
            dest_airport = incident.get('dest_airport_name') or incident.get('dest_airport_iata', '')
            
            route_info = ""
            if source_airport and dest_airport:
                route_info = f" on route from {source_airport} to {dest_airport}"
            elif source_airport:
                route_info = f" near {source_airport}"
            
            incident_text = (
                f"Incident {i}: On {date}, {airline} {aircraft} experienced "
                f"a {severity} severity incident{route_info}. "
                f"Details: {description[:200]}{'...' if len(description) > 200 else ''}"
            )
            
            context_parts.append(incident_text)
        
        return " ".join(context_parts)
    
    def _create_rule_based_summary(self, incidents: List[Dict[str, Any]], query: str) -> str:
        """Create a rule-based summary when QA model confidence is low"""
        num_incidents = len(incidents)
        
        if num_incidents == 0:
            return "No incidents found matching your query."
        
        # Extract key information
        severities = [inc.get('severity') for inc in incidents if inc.get('severity')]
        airlines = [inc.get('airline_name') or inc.get('airline_iata') 
                   for inc in incidents if inc.get('airline_name') or inc.get('airline_iata')]
        years = [str(inc.get('date', ''))[:4] for inc in incidents if inc.get('date')]
        
        # Count occurrences
        severity_counts = {}
        for sev in severities:
            if sev:
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        # Build summary
        summary_parts = []
        
        # Basic count
        summary_parts.append(f"Found {num_incidents} relevant incident{'s' if num_incidents != 1 else ''}")
        
        # Severity breakdown
        if severity_counts:
            sev_strs = [f"{count} {sev}" for sev, count in severity_counts.items()]
            if len(sev_strs) <= 2:
                summary_parts.append(f"({' and '.join(sev_strs)} severity)")
            else:
                summary_parts.append(f"(including {', '.join(sev_strs[:-1])}, and {sev_strs[-1]} severity)")
        
        # Time period
        if years:
            unique_years = list(set([y for y in years if y and len(y) == 4]))
            if len(unique_years) == 1:
                summary_parts.append(f"from {unique_years[0]}")
            elif len(unique_years) > 1:
                summary_parts.append(f"spanning {min(unique_years)} to {max(unique_years)}")
        
        # Most recent incident detail
        if incidents:
            most_recent = max(incidents, key=lambda x: x.get('date', '1900-01-01'))
            desc = most_recent.get('description', '')
            if desc:
                summary_parts.append(f"Most recent: {desc[:100]}{'...' if len(desc) > 100 else ''}")
        
        return ". ".join(summary_parts) + "."
    
    def _enhance_answer(self, answer: str, incidents: List[Dict[str, Any]]) -> str:
        """Enhance the QA model answer with additional context"""
        if not answer or len(answer.strip()) < 10:
            return self._create_rule_based_summary(incidents, "")
        
        # Add incident count if not mentioned
        if not any(word in answer.lower() for word in ['incident', 'found', 'report']):
            count = len(incidents)
            enhanced = f"Found {count} relevant incident{'s' if count != 1 else ''}. {answer}"
        else:
            enhanced = answer
        
        # Ensure it's not too long
        if len(enhanced) > 300:
            enhanced = enhanced[:297] + "..."
        
        return enhanced
    
    def classify_incident_severity(self, description: str) -> str:
        """
        Classify incident severity based on description
        (Bonus feature)
        """
        description_lower = description.lower()
        
        # High severity keywords
        high_severity_keywords = [
            'fatal', 'death', 'killed', 'crash', 'collision', 'fire', 'explosion',
            'emergency landing', 'evacuation', 'serious injury', 'destroyed'
        ]
        
        # Medium severity keywords
        medium_severity_keywords = [
            'injury', 'injured', 'medical', 'diversion', 'abort', 'malfunction',
            'failure', 'turbulence', 'weather', 'delay', 'precautionary'
        ]
        
        # Check for high severity
        for keyword in high_severity_keywords:
            if keyword in description_lower:
                return 'high'
        
        # Check for medium severity
        for keyword in medium_severity_keywords:
            if keyword in description_lower:
                return 'medium'
        
        # Default to low
        return 'low'
    
    def extract_key_information(self, incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract key statistics and information from incidents
        
        Returns:
            Dictionary with key insights
        """
        if not incidents:
            return {}
        
        insights = {
            'total_incidents': len(incidents),
            'severity_distribution': {},
            'common_aircraft': {},
            'common_airlines': {},
            'time_range': {},
            'locations': []
        }
        
        # Process each incident
        dates = []
        for incident in incidents:
            # Severity
            severity = incident.get('severity')
            if severity:
                insights['severity_distribution'][severity] = \
                    insights['severity_distribution'].get(severity, 0) + 1
            
            # Aircraft type
            aircraft = incident.get('aircraft_type')
            if aircraft:
                insights['common_aircraft'][aircraft] = \
                    insights['common_aircraft'].get(aircraft, 0) + 1
            
            # Airline
            airline = incident.get('airline_name') or incident.get('airline_iata')
            if airline:
                insights['common_airlines'][airline] = \
                    insights['common_airlines'].get(airline, 0) + 1
            
            # Date
            date = incident.get('date')
            if date:
                dates.append(str(date))
            
            # Locations
            source_airport = incident.get('source_airport_name')
            dest_airport = incident.get('dest_airport_name')
            if source_airport:
                insights['locations'].append(source_airport)
            if dest_airport:
                insights['locations'].append(dest_airport)
        
        # Time range
        if dates:
            insights['time_range'] = {
                'earliest': min(dates),
                'latest': max(dates)
            }
        
        return insights