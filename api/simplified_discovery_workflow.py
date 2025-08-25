"""
Simplified Discovery Workflow - Optimized for Railway Deployment
Removes resource-heavy agents while keeping high-performing core functionality
"""

from typing import Dict, List, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
import operator
from loguru import logger
import json
import os
from datetime import datetime
import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin
import re


# ===== STATE DEFINITION =====
class SimplifiedDiscoveryState(TypedDict):
    """Simplified state for discovery workflow"""
    # Input
    company_name: str
    company_url: str
    
    # Agent outputs (only core agents)
    google_maps_results: List[Dict]
    tavily_search_results: List[Dict]
    web_scraper_results: List[Dict]
    directory_results: List[Dict]
    
    # Processing stages
    all_locations: List[Dict]
    deduplicated_locations: List[Dict]
    enriched_locations: List[Dict]
    
    # Final output
    final_locations: List[Dict]
    summary: Dict
    export_files: List[str]
    
    # Workflow control
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    status: str
    errors: List[str]


# ===== UTILITY FUNCTIONS =====
def clean_and_validate_url(url: str) -> str:
    """Clean and validate URL with better handling"""
    if not url:
        return ""
    
    url = str(url).strip()
    
    if (url or '').lower() in ['nan', 'none', 'null', '', 'n/a', 'na']:
        return ""
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if parsed.netloc and parsed.scheme:
            return url
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {e}")
    
    return ""


# ===== CORE AGENT NODES (SIMPLIFIED) =====

class SimplifiedGoogleMapsAgentNode:
    """Simplified Google Maps agent - fewer search patterns"""
    
    def __init__(self, api_key: str = None):
        try:
            import googlemaps
            self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
            if self.api_key:
                self.client = googlemaps.Client(key=self.api_key)
                logger.info("Simplified Google Maps Agent initialized")
            else:
                self.client = None
                logger.warning("Google Maps API key not found - agent disabled")
        except ImportError:
            logger.warning("googlemaps library not installed - Google Maps agent disabled")
            self.client = None
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Execute simplified Google Maps search"""
        if state.get('google_maps_results') is not None:
            return state
        
        if not self.client:
            logger.warning("Google Maps client not available")
            state['google_maps_results'] = []
            return state
        
        company_name = state['company_name']
        logger.info(f"Google Maps: Simplified search for {company_name}")
        
        try:
            all_locations = []
            
            # Only 2 search patterns instead of 5
            search_patterns = [
                company_name,
                f"{company_name} office"
            ]
            
            for pattern in search_patterns:
                try:
                    places_result = self.client.places(query=pattern, type=None)
                    
                    # Limit to 10 results instead of 15
                    for place in places_result.get('results', [])[:10]:
                        place_id = place.get('place_id')
                        
                        # Get basic details only
                        details = {}
                        if place_id:
                            try:
                                details = self.client.place(place_id)['result']
                            except:
                                pass
                        
                        location = {
                            'name': place.get('name', ''),
                            'address': place.get('formatted_address', ''),
                            'city': self._extract_city(place.get('formatted_address', '')),
                            'phone': details.get('formatted_phone_number', ''),
                            'website': details.get('website', ''),
                            'lat': place.get('geometry', {}).get('location', {}).get('lat'),
                            'lng': place.get('geometry', {}).get('location', {}).get('lng'),
                            'confidence': 0.9,
                            'source': 'google_maps'
                        }
                        all_locations.append(location)
                    
                    time.sleep(0.3)  # Shorter delay
                    
                except Exception as e:
                    logger.error(f"Google Maps search error: {e}")
                    continue
            
            # Simple deduplication
            unique_locations = self._deduplicate_results(all_locations)
            
            state['google_maps_results'] = unique_locations
            logger.info(f"Google Maps: Found {len(unique_locations)} locations")
            
        except Exception as e:
            logger.error(f"Google Maps error: {e}")
            state['google_maps_results'] = []
        
        return state
    
    def _extract_city(self, address: str) -> str:
        parts = address.split(',')
        if len(parts) >= 3:
            return (parts[-3] or '').strip()
        return ''
    
    def _deduplicate_results(self, locations: List[Dict]) -> List[Dict]:
        seen_addresses = set()
        unique = []
        
        for loc in locations:
            address_key = (loc.get('address') or '').lower()[:50]
            if address_key and address_key not in seen_addresses:
                seen_addresses.add(address_key)
                unique.append(loc)
        
        return unique


class SimplifiedTavilySearchAgentNode:
    """Simplified Tavily search - fewer queries"""
    
    def __init__(self, tavily_api_key: str = None):
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        
        if self.api_key:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults
                self.search = TavilySearchResults(api_key=self.api_key, max_results=5)  # Reduced
                logger.info("Simplified Tavily search initialized")
            except ImportError as e:
                logger.error(f"langchain-community not installed: {e}")
                self.search = None
            except Exception as e:
                logger.error(f"Failed to initialize Tavily: {e}")
                self.search = None
        else:
            logger.warning("No Tavily API key provided")
            self.search = None
        
        try:
            self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.llm = None
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Simplified Tavily search"""
        if state.get('tavily_search_results') is not None:
            return state
        
        if not self.search or not self.llm:
            logger.warning("Tavily search not available")
            state['tavily_search_results'] = []
            return state
        
        company_name = state['company_name']
        logger.info(f"Tavily: Simplified search for {company_name}")
        
        try:
            all_locations = []
            
            # Only 3 queries instead of 8
            search_queries = [
                f"{company_name} office locations addresses",
                f"{company_name} headquarters contact information",
                f"{company_name} facilities locations"
            ]
            
            for query in search_queries:
                try:
                    logger.info(f"Tavily: Searching '{query}'")
                    results = self.search.invoke(query)
                    
                    # Process only first result
                    for result in results[:1]:
                        content = result.get('content', '')[:2000]  # Reduced content
                        
                        if len(content) > 100:
                            locations = self._extract_locations_with_llm(content, company_name)
                            all_locations.extend(locations)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Tavily search error: {e}")
                    continue
            
            unique_locations = self._deduplicate_results(all_locations)
            
            state['tavily_search_results'] = unique_locations
            logger.info(f"Tavily: Found {len(unique_locations)} locations")
            
        except Exception as e:
            logger.error(f"Tavily error: {e}")
            state['tavily_search_results'] = []
        
        return state
    
    def _extract_locations_with_llm(self, content: str, company_name: str) -> List[Dict]:
        """Simplified LLM extraction"""
        
        prompt = f"""Extract ONLY real, specific locations for {company_name} from this content.

Content: {content}

STRICT REQUIREMENTS:
1. ONLY extract locations explicitly mentioned with real addresses or cities
2. Must have at least a city name from the content
3. NO fake or generic locations

Return JSON array with:
- name: Location name
- address: Full address (if available)
- city: City name (required)
- state: State/province (if available)
- country: Country (if available)

Return [] if no specific locations found.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            json_match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if json_match:
                locs = json.loads(json_match.group())
                validated_locations = []
                
                for loc in locs:
                    if loc and isinstance(loc, dict) and loc.get('city'):
                        city = (loc.get('city') or '').lower()
                        if city in content.lower():  # Validate city appears in content
                            loc['source'] = 'tavily'
                            loc['confidence'] = 0.8
                            validated_locations.append(loc)
                
                return validated_locations
                
        except Exception as e:
            logger.error(f"Tavily LLM extraction error: {e}")
        
        return []
    
    def _deduplicate_results(self, locations: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        
        for loc in locations:
            key = ((loc.get('city') or '').lower(), (loc.get('name') or '')[:20].lower())
            if key not in seen and loc.get('city'):
                seen.add(key)
                unique.append(loc)
        
        return unique


class SimplifiedWebScraperAgentNode:
    """Simplified web scraper - fewer pages"""
    
    def __init__(self):
        try:
            self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.llm = None
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info("Simplified Web Scraper initialized")
  
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Simplified web scraping"""
        if state.get('web_scraper_results') is not None:
            return state
        
        if not self.llm:
            logger.warning("Web scraper disabled - no OpenAI client")
            state['web_scraper_results'] = []
            return state
        
        company_url = clean_and_validate_url(state.get('company_url', ''))
        company_name = state['company_name']
        
        logger.info(f"Web Scraper: Simplified processing for {company_name}")
        
        if not company_url:
            logger.warning(f"No valid URL for {company_name}")
            state['web_scraper_results'] = []
            return state
        
        try:
            all_locations = []
            
            # Only scrape 5 pages instead of 25
            location_urls = self._find_basic_location_pages(company_url)
            logger.info(f"Found {len(location_urls)} pages to scrape")
            
            for url in location_urls[:5]:  # Limit to 5 pages
                try:
                    logger.info(f"Scraping: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        locations = self._extract_locations_from_page(response.text, company_name)
                        all_locations.extend(locations)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
            unique_locations = self._deduplicate_results(all_locations)
            
            state['web_scraper_results'] = unique_locations
            logger.info(f"Web Scraper: Found {len(unique_locations)} locations")
            
        except Exception as e:
            logger.error(f"Web scraper error: {e}")
            state['web_scraper_results'] = []
        
        return state
    
    def _find_basic_location_pages(self, base_url: str) -> List[str]:
        """Find basic location pages - simplified"""
        location_urls = [base_url]
        
        try:
            response = self.session.get(base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Basic keywords only
                location_keywords = [
                    'location', 'office', 'contact', 'about', 'careers'
                ]
                
                for link in soup.find_all('a', href=True)[:20]:  # Limit links
                    href = (link.get('href') or '').lower()
                    text = (link.get_text() or '').lower().strip()
                    
                    if any(keyword in f"{href} {text}" for keyword in location_keywords):
                        full_url = self._build_full_url(link.get('href'), base_url)
                        if full_url and self._is_same_domain(full_url, base_url):
                            location_urls.append(full_url)
        
        except Exception as e:
            logger.error(f"Basic page discovery error: {e}")
        
        return location_urls[:10]  # Return max 10 URLs
    
    def _extract_locations_from_page(self, html_content: str, company_name: str) -> List[Dict]:
        """Simplified location extraction"""
        locations = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove noise
            for element in soup(['script', 'style', 'meta']):
                element.decompose()
            
            text = soup.get_text(separator=' ', strip=True)[:3000]  # Reduced content
            
            if len(text) > 100:
                locations = self._extract_locations_with_llm(text, company_name)
        
        except Exception as e:
            logger.error(f"Page extraction error: {e}")
        
        return locations
    
    def _extract_locations_with_llm(self, content: str, company_name: str) -> List[Dict]:
        """Simplified LLM extraction"""
        
        prompt = f"""Extract office locations for {company_name} from this content.

Content: {content}

REQUIREMENTS:
1. Only extract locations explicitly mentioned
2. Must have at least a city name from the content
3. Include addresses when available

Return JSON array with:
- name: Location name
- address: Street address (if available)
- city: City name (required)
- state: State (if available)
- country: Country (if available)

Return [] if no locations found.
"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            json_match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if json_match:
                locs = json.loads(json_match.group())
                
                validated_locations = []
                for loc in locs:
                    if loc.get('city') and len((loc.get('city') or '').strip()) > 1:
                        city = (loc.get('city') or '').lower()
                        if city in content.lower():
                            loc['source'] = 'company_website'
                            loc['confidence'] = 0.85
                            validated_locations.append(loc)
                
                return validated_locations
        
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
        
        return []
    
    def _build_full_url(self, href: str, base_url: str) -> str:
        try:
            if href.startswith('http'):
                return href
            elif href.startswith('/'):
                return urljoin(base_url, href)
            else:
                return urljoin(base_url + '/', href)
        except:
            return ""
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        try:
            return urlparse(url).netloc == urlparse(base_url).netloc
        except:
            return False
    
    def _deduplicate_results(self, locations: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        
        for loc in locations:
            key = ((loc.get('city') or '').lower(), (loc.get('address') or '')[:30].lower())
            if key not in seen and loc.get('city'):
                seen.add(key)
                unique.append(loc)
        
        return unique


class SimplifiedBusinessDirectoryAgentNode:
    """Simplified business directory search"""
    
    def __init__(self):
        try:
            self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        except:
            self.llm = None
        self.session = requests.Session()
        logger.info("Simplified Business Directory Agent initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Simplified directory search"""
        if state.get('directory_results') is not None:
            return state
        
        if not self.llm:
            logger.warning("Directory agent disabled")
            state['directory_results'] = []
            return state
        
        company_name = state['company_name']
        logger.info(f"Directory: Simplified search for {company_name}")
        
        try:
            # Just return empty for now to speed up processing
            # Directory searches are often not very effective
            locations = []
            
            state['directory_results'] = locations
            logger.info(f"Directory: Found {len(locations)} locations")
            
        except Exception as e:
            logger.error(f"Directory error: {e}")
            state['directory_results'] = []
        
        return state


# ===== PROCESSING NODES (SIMPLIFIED) =====

class SimplifiedAggregatorNode:
    """Simplified aggregator"""
    
    def __init__(self):
        logger.info("Simplified Aggregator initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Combine results from core agents only"""
        if state.get('all_locations') is not None:
            return state
        
        all_locations = []
        
        # Only core sources
        sources = [
            'google_maps_results', 'tavily_search_results', 
            'web_scraper_results', 'directory_results'
        ]
        
        for source in sources:
            locations = state.get(source, [])
            if locations:
                logger.info(f"Aggregating {len(locations)} locations from {source}")
                all_locations.extend(locations)
        
        state['all_locations'] = all_locations
        logger.info(f"Aggregated {len(all_locations)} total locations")
        
        return state


class SimplifiedDeduplicationNode:
    """Simplified deduplication"""
    
    def __init__(self):
        logger.info("Simplified Deduplication initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Basic deduplication"""
        if state.get('deduplicated_locations') is not None:
            return state
        
        all_locations = state.get('all_locations', [])
        logger.info(f"Deduplication: Processing {len(all_locations)} locations")
        
        # Simple deduplication
        unique_locations = self._basic_deduplicate(all_locations)
        
        state['deduplicated_locations'] = unique_locations
        logger.info(f"Deduplication: {len(all_locations)} -> {len(unique_locations)} locations")
        
        return state
    
    def _basic_deduplicate(self, locations: List[Dict]) -> List[Dict]:
        """Basic deduplication by city and name"""
        seen = set()
        unique = []
        
        for loc in locations:
            city = (loc.get('city') or '').lower().strip()
            name = (loc.get('name') or '').lower().strip()
            
            if not city or len(city) < 2:
                continue
            
            key = f"{city}_{name[:20]}"
            
            if key not in seen:
                seen.add(key)
                # Clean up the location data
                cleaned_loc = {
                    'name': (loc.get('name') or '').strip(),
                    'address': (loc.get('address') or '').strip(),
                    'city': city.title(),
                    'state': (loc.get('state') or '').strip(),
                    'country': (loc.get('country') or '').strip(),
                    'phone': (loc.get('phone') or '').strip(),
                    'website': (loc.get('website') or '').strip(),
                    'lat': loc.get('lat', ''),
                    'lng': loc.get('lng', ''),
                    'confidence': loc.get('confidence', 0.5),
                    'source': loc.get('source', 'unknown')
                }
                unique.append(cleaned_loc)
        
        return unique


class SimplifiedEnrichmentNode:
    """Simplified enrichment"""
    
    def __init__(self):
        logger.info("Simplified Enrichment initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Basic enrichment"""
        if state.get('enriched_locations') is not None:
            return state
        
        locations = state.get('deduplicated_locations', [])
        company_name = state['company_name']
        
        # Just add IDs and ensure names
        enriched = []
        for i, loc in enumerate(locations, 1):
            enriched_loc = dict(loc)
            enriched_loc['location_id'] = f"LOC_{i:03d}"
            
            if not enriched_loc.get('name'):
                city = enriched_loc.get('city', 'Unknown')
                enriched_loc['name'] = f"{company_name} - {city}"
            
            enriched.append(enriched_loc)
        
        state['enriched_locations'] = enriched
        state['final_locations'] = enriched
        
        logger.info(f"Enriched {len(enriched)} locations")
        
        return state


class SimplifiedExportNode:
    """Simplified export - just JSON"""
    
    def __init__(self, output_dir: str = "/tmp/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Simplified Export initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Simple JSON export only"""
        if state.get('export_files'):
            return state
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_slug = (state['company_name'] or '').lower().replace(' ', '_')[:30]
        
        locations = state.get('final_locations', [])
        
        # Just create JSON file
        json_file = self.output_dir / f"{company_slug}_{timestamp}_locations.json"
        
        export_data = {
            'company': state['company_name'],
            'company_url': state.get('company_url', ''),
            'discovery_timestamp': datetime.now().isoformat(),
            'total_locations': len(locations),
            'locations': locations
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
        
        state['export_files'] = [str(json_file)]
        logger.info(f"Simple export completed: {len(locations)} locations")
        
        return state


class SimplifiedSummaryNode:
    """Simplified summary"""
    
    def __init__(self):
        logger.info("Simplified Summary initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Generate basic summary"""
        if state.get('summary'):
            return state
        
        summary = {
            'company': state['company_name'],
            'url': state['company_url'],
            'timestamp': datetime.now().isoformat(),
            'total_locations': len(state.get('final_locations', [])),
            'sources_used': {
                'google_maps': len(state.get('google_maps_results', [])),
                'tavily': len(state.get('tavily_search_results', [])),
                'website': len(state.get('web_scraper_results', [])),
                'directory': len(state.get('directory_results', []))
            }
        }
        
        state['summary'] = summary
        state['status'] = 'completed'
        
        return state


class SimplifiedSupervisorNode:
    """Simplified supervisor"""
    
    def __init__(self):
        logger.info("Simplified Supervisor initialized")
    
    def run(self, state: SimplifiedDiscoveryState) -> SimplifiedDiscoveryState:
        """Route to next agent - simplified workflow"""
        
        agents_status = {
            'google_maps': state.get('google_maps_results') is not None,
            'tavily_search': state.get('tavily_search_results') is not None,
            'web_scraper': state.get('web_scraper_results') is not None,
            'directory': state.get('directory_results') is not None,
            'aggregated': state.get('all_locations') is not None,
            'deduplicated': state.get('deduplicated_locations') is not None,
            'enriched': state.get('enriched_locations') is not None,
            'exported': state.get('export_files') is not None,
            'summary': state.get('summary') is not None
        }
        
        # Simplified workflow order
        if not agents_status['google_maps']:
            state['next_agent'] = 'google_maps'
        elif not agents_status['tavily_search']:
            state['next_agent'] = 'tavily_search'
        elif not agents_status['web_scraper']:
            state['next_agent'] = 'web_scraper'
        elif not agents_status['directory']:
            state['next_agent'] = 'directory'
        elif not agents_status['aggregated']:
            state['next_agent'] = 'aggregator'
        elif not agents_status['deduplicated']:
            state['next_agent'] = 'deduplication'
        elif not agents_status['enriched']:
            state['next_agent'] = 'enricher'
        elif not agents_status['exported']:
            state['next_agent'] = 'exporter'
        elif not agents_status['summary']:
            state['next_agent'] = 'summary'
        else:
            state['next_agent'] = 'end'
        
        logger.info(f"Simplified Supervisor: Next agent is {state['next_agent']}")
        return state


# ===== MAIN SIMPLIFIED WORKFLOW CLASS =====

class SimplifiedDiscoveryWorkflow:
    """Simplified multi-agent discovery workflow optimized for Railway deployment"""
    
    def __init__(self, output_dir: str = "temp/output", api_keys: dict = None):
        """Initialize simplified workflow"""
        
        # Store API keys
        self.api_keys = api_keys or {}
        if api_keys:
            if api_keys.get('openai_api_key'):
                os.environ['OPENAI_API_KEY'] = api_keys['openai_api_key']
            if api_keys.get('google_maps_api_key'):
                os.environ['GOOGLE_MAPS_API_KEY'] = api_keys['google_maps_api_key']
            if api_keys.get('tavily_api_key'):
                os.environ['TAVILY_API_KEY'] = api_keys['tavily_api_key']
        
        # Initialize simplified nodes
        self.google_maps_node = SimplifiedGoogleMapsAgentNode(
            api_key=api_keys.get('google_maps_api_key') if api_keys else None
        )
        self.tavily_node = SimplifiedTavilySearchAgentNode(
            tavily_api_key=api_keys.get('tavily_api_key') if api_keys else None
        )
        self.web_scraper_node = SimplifiedWebScraperAgentNode()
        self.directory_node = SimplifiedBusinessDirectoryAgentNode()
        
        # Processing nodes
        self.aggregator_node = SimplifiedAggregatorNode()
        self.deduplication_node = SimplifiedDeduplicationNode()
        self.enrichment_node = SimplifiedEnrichmentNode()
        self.export_node = SimplifiedExportNode(output_dir)
        self.summary_node = SimplifiedSummaryNode()
        self.supervisor_node = SimplifiedSupervisorNode()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info("Simplified Discovery Workflow initialized")
        logger.info("Optimizations: Fewer agents, reduced queries, limited pages, basic export")
    
    def _build_graph(self) -> StateGraph:
        """Build simplified workflow graph"""
        workflow = StateGraph(SimplifiedDiscoveryState)
        
        # Add nodes
        workflow.add_node("supervisor", self.supervisor_node.run)
        workflow.add_node("google_maps", self.google_maps_node.run)
        workflow.add_node("tavily_search", self.tavily_node.run)
        workflow.add_node("web_scraper", self.web_scraper_node.run)
        workflow.add_node("directory", self.directory_node.run)
        workflow.add_node("aggregator", self.aggregator_node.run)
        workflow.add_node("deduplication", self.deduplication_node.run)
        workflow.add_node("enricher", self.enrichment_node.run)
        workflow.add_node("exporter", self.export_node.run)
        workflow.add_node("summary_generator", self.summary_node.run)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Define routing
        def route_next(state):
            return state.get('next_agent', 'end')
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "supervisor",
            route_next,
            {
                "google_maps": "google_maps",
                "tavily_search": "tavily_search", 
                "web_scraper": "web_scraper",
                "directory": "directory",
                "aggregator": "aggregator",
                "deduplication": "deduplication",
                "enricher": "enricher",
                "exporter": "exporter",
                "summary": "summary_generator",
                "end": END
            }
        )
        
        # All nodes return to supervisor
        agent_nodes = [
            "google_maps", "tavily_search", "web_scraper", "directory",
            "aggregator", "deduplication", "enricher", "exporter", "summary_generator"
        ]
        
        for node in agent_nodes:
            workflow.add_edge(node, "supervisor")
        
        return workflow.compile()
    
    def discover(self, company_name: str, company_url: str = None) -> Dict:
        """Run simplified discovery"""
        logger.info(f"Starting SIMPLIFIED discovery for {company_name}")
        
        cleaned_url = clean_and_validate_url(company_url) if company_url else ""
        
        initial_state = {
            'company_name': company_name,
            'company_url': cleaned_url,
            'messages': [
                HumanMessage(content=f"Simplified discovery for {company_name}")
            ],
            'errors': []
        }
        
        try:
            result = self.graph.invoke(
                initial_state,
                config={"recursion_limit": 50}  # Reduced limit
            )
            
            return {
                'company': company_name,
                'url': cleaned_url,
                'locations': result.get('final_locations', []),
                'summary': result.get('summary', {}),
                'enhancement_summary': {
                    'workflow_type': 'simplified',
                    'optimizations': [
                        'Removed resource-heavy agents (SEC, MultiSearch, IndustrySpecific)',
                        'Reduced search queries per agent',
                        'Limited web scraping to 5 pages',
                        'Basic deduplication only',
                        'JSON export only'
                    ],
                    'expected_performance': 'Faster, more reliable, Railway-optimized'
                },
                'export_files': result.get('export_files', []),
                'messages': [msg.content if hasattr(msg, 'content') else str(msg) 
                           for msg in result.get('messages', [])],
                'errors': result.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"Simplified workflow error: {e}")
            return {
                'company': company_name,
                'url': cleaned_url,
                'locations': [],
                'summary': {'error': str(e)},
                'enhancement_summary': {'error': 'Workflow failed'},
                'export_files': [],
                'messages': [],
                'errors': [str(e)]
            }


# ===== ALIASES =====
SuperEnhancedDiscoveryWorkflow = SimplifiedDiscoveryWorkflow
EnhancedDiscoveryWorkflow = SimplifiedDiscoveryWorkflow
CompanyDiscoveryWorkflow = SimplifiedDiscoveryWorkflow


if __name__ == "__main__":
    # Example usage
    api_keys = {
        'openai_api_key': 'your-openai-key-here',
        'google_maps_api_key': 'your-google-maps-key-here', 
        'tavily_api_key': 'your-tavily-key-here'
    }
    
    workflow = SimplifiedDiscoveryWorkflow(
        output_dir="output",
        api_keys=api_keys
    )
    
    result = workflow.discover(
        company_name="Microsoft Corporation",
        company_url="https://microsoft.com"
    )
    
    print("="*60)
    print("SIMPLIFIED LOCATION DISCOVERY RESULTS")
    print("="*60)
    print(f"Company: {result['company']}")
    print(f"Total Locations Found: {len(result['locations'])}")
    print(f"Workflow Type: {result['enhancement_summary']['workflow_type']}")
    print(f"Export Files: {len(result['export_files'])}")
