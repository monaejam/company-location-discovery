"""
Enhanced LangGraph Multi-Agent Workflow with Fixed URL Handling
Fixes URL processing issues and adds better debugging
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


# ===== STATE DEFINITION =====
class DiscoveryState(TypedDict):
    """Complete state for discovery workflow"""
    # Input
    company_name: str
    company_url: str
    
    # Agent outputs
    google_maps_results: List[Dict]
    web_scraper_results: List[Dict]
    tavily_search_results: List[Dict]
    sec_filing_results: List[Dict]
    
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
    
    # Convert to string and strip
    url = str(url).strip()
    
    # Handle pandas NaN values and common invalid values
    if url.lower() in ['nan', 'none', 'null', '', 'n/a', 'na']:
        return ""
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if parsed.netloc and parsed.scheme:
            return url
    except Exception as e:
        logger.warning(f"URL validation failed for {url}: {e}")
    
    return ""


# ===== AGENT NODES =====

class EnhancedGoogleMapsAgentNode:
    """Google Maps agent with detailed location extraction"""
    
    def __init__(self, api_key: str = None):
        import googlemaps
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if self.api_key:
            self.client = googlemaps.Client(key=self.api_key)
            logger.info("Enhanced Google Maps Agent Node initialized")
        else:
            self.client = None
            logger.warning("Google Maps API key not found - agent will be disabled")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Execute Google Maps search"""
        if state.get('google_maps_results') is not None:
            return state
        
        if not self.client:
            logger.warning("Google Maps client not available")
            state['google_maps_results'] = []
            return state
        
        logger.info(f"Google Maps: Searching for {state['company_name']}")
        
        try:
            places_result = self.client.places(
                query=state['company_name'],
                type=None
            )
            
            locations = []
            for place in places_result.get('results', [])[:20]:
                place_id = place.get('place_id')
                
                # Try to get detailed info
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
                locations.append(location)
            
            state['google_maps_results'] = locations
            state['messages'].append(
                AIMessage(content=f"Google Maps found {len(locations)} locations")
            )
            logger.info(f"Google Maps: Found {len(locations)} locations")
            
        except Exception as e:
            logger.error(f"Google Maps error: {e}")
            state['google_maps_results'] = []
        
        return state
    
    def _extract_city(self, address: str) -> str:
        parts = address.split(',')
        if len(parts) >= 3:
            return parts[-3].strip()
        return ''


class TavilySearchAgentNode:
    """Tavily search for web-based location discovery"""
    
    def __init__(self, tavily_api_key: str = None):
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        if self.api_key:
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults
                self.search = TavilySearchResults(api_key=self.api_key, max_results=5)
            except ImportError:
                logger.warning("Install langchain-community for Tavily support")
                self.search = None
        else:
            self.search = None
        
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("Tavily Search Agent Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Search for locations using Tavily"""
        if state.get('tavily_search_results') is not None:
            return state
        
        if not self.search:
            logger.warning("Tavily search not available")
            state['tavily_search_results'] = []
            return state
        
        logger.info(f"Tavily: Searching for {state['company_name']}")
        
        try:
            locations = []
            query = f"{state['company_name']} office locations addresses"
            
            results = self.search.invoke(query)
            
            for result in results[:3]:  # Process first 3 results
                content = result.get('content', '')[:2000]
                
                prompt = f"""Extract locations for {state['company_name']} from:
                {content}
                
                Return JSON array with: name, city, country, address.
                Only JSON array, no text."""
                
                response = self.llm.invoke([HumanMessage(content=prompt)])
                
                import re
                json_match = re.search(r'\[.*?\]', response.content, re.DOTALL)
                if json_match:
                    try:
                        locs = json.loads(json_match.group())
                        for loc in locs:
                            if loc.get('city'):
                                loc['source'] = 'tavily'
                                loc['confidence'] = 0.75
                                locations.append(loc)
                    except:
                        pass
            
            state['tavily_search_results'] = locations
            state['messages'].append(
                AIMessage(content=f"Tavily found {len(locations)} locations")
            )
            logger.info(f"Tavily: Found {len(locations)} locations")
            
        except Exception as e:
            logger.error(f"Tavily error: {e}")
            state['tavily_search_results'] = []
        
        return state


class ImprovedWebScraperAgentNode:
    """Enhanced web scraping agent with better URL handling"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        logger.info("Improved Web Scraper Agent Node initialized")
  
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Scrape company website for locations - FIXED WITH DEBUG"""
        if state.get('web_scraper_results') is not None:
            return state
        
        # DEBUG: Let's see what's in the state
        logger.info(f"Web Scraper DEBUG: Full state keys: {list(state.keys())}")
        logger.info(f"Web Scraper DEBUG: company_name = '{state.get('company_name', 'MISSING')}'")
        logger.info(f"Web Scraper DEBUG: company_url in state = {'company_url' in state}")
        
        # Get and clean URL
        raw_url = state.get('company_url', '')
        
        # DEBUG: Show exactly what we got
        logger.info(f"Web Scraper DEBUG: raw_url = '{raw_url}' (type: {type(raw_url)}, len: {len(str(raw_url))})")
        
        company_url = clean_and_validate_url(raw_url)
        
        logger.info(f"Web Scraper: Raw URL: '{raw_url}' -> Cleaned URL: '{company_url}'")
        
        if not company_url:
            logger.warning(f"No valid URL for {state['company_name']} (raw: '{raw_url}')")
            state['web_scraper_results'] = []
            state['messages'].append(
                AIMessage(content=f"Web scraper skipped - no valid URL provided (got: '{raw_url}')")
            )
            return state
        
        logger.info(f"Web Scraper: Processing {company_url} for {state['company_name']}")
        
        try:
            all_locations = []
            
            # Step 1: Find location-related pages
            location_urls = self._find_location_pages(company_url)
            logger.info(f"Found {len(location_urls)} potential location pages")
            
            # Step 2: Scrape each page
            for url in location_urls[:5]:  # Limit to 5 pages
                try:
                    logger.info(f"Scraping: {url}")
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Remove scripts and styles
                        for element in soup(['script', 'style', 'meta', 'noscript']):
                            element.decompose()
                        
                        # Get text
                        text = soup.get_text(separator=' ', strip=True)
                        
                        # Focus on sections with location keywords
                        relevant_text = self._extract_relevant_sections(text, soup)
                        
                        if len(relevant_text) > 100:  # Only process if we have enough text
                            # Use LLM to extract locations
                            locations = self._extract_locations_with_llm(
                                relevant_text[:8000],  # Limit text size
                                state['company_name']
                            )
                            
                            for loc in locations:
                                loc['source_url'] = url
                                all_locations.append(loc)
                    else:
                        logger.warning(f"HTTP {response.status_code} for {url}")
                    
                    time.sleep(0.5)  # Be polite
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    continue
            
            # If no locations found on subpages, try the main URL
            if not all_locations and company_url:
                logger.info("No locations on subpages, trying main URL")
                try:
                    response = self.session.get(company_url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        for element in soup(['script', 'style', 'meta', 'noscript']):
                            element.decompose()
                        
                        text = soup.get_text(separator=' ', strip=True)
                        
                        # Look for any location mentions
                        locations_from_main = self._extract_locations_with_llm(
                            text[:8000],
                            state['company_name']
                        )
                        
                        for loc in locations_from_main:
                            loc['source_url'] = company_url
                            all_locations.append(loc)
                            
                    else:
                        logger.warning(f"HTTP {response.status_code} for main URL {company_url}")
                        
                except Exception as e:
                    logger.error(f"Error with main URL {company_url}: {e}")
            
            state['web_scraper_results'] = all_locations
            state['messages'].append(
                AIMessage(content=f"Web scraper found {len(all_locations)} locations from {company_url}")
            )
            logger.info(f"Web Scraper: Found {len(all_locations)} locations")
            
        except Exception as e:
            logger.error(f"Web scraper error for {company_url}: {e}")
            state['web_scraper_results'] = []
            state['errors'].append(f"Web scraper error: {str(e)}")
        
        return state
   
    
    def _find_location_pages(self, base_url: str) -> List[str]:
        """Find pages likely to contain location information"""
        location_urls = [base_url]
        
        try:
            logger.debug(f"Looking for location pages on {base_url}")
            response = self.session.get(base_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Keywords that indicate location pages
                location_keywords = [
                    'location', 'office', 'contact', 'about', 'global',
                    'branch', 'store', 'address', 'where', 'find-us',
                    'presence', 'worldwide', 'regional', 'facilities',
                    'locations', 'offices', 'contacts', 'branches'
                ]
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text().lower().strip()
                    
                    # Check if link might contain locations
                    if any(keyword in href.lower() or keyword in text for keyword in location_keywords):
                        # Build full URL
                        if href.startswith('http'):
                            full_url = href
                        elif href.startswith('/'):
                            full_url = urljoin(base_url, href)
                        else:
                            continue
                        
                        # Check if same domain
                        try:
                            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                                if full_url not in location_urls:
                                    location_urls.append(full_url)
                                    logger.debug(f"Found potential location page: {full_url}")
                        except:
                            continue
            else:
                logger.warning(f"HTTP {response.status_code} when looking for location pages on {base_url}")
        
        except Exception as e:
            logger.error(f"Error finding location pages: {e}")
        
        return location_urls[:10]  # Limit to 10 URLs
    
    def _extract_relevant_sections(self, text: str, soup: BeautifulSoup) -> str:
        """Extract sections of text likely to contain location information"""
        relevant_text = []
        
        # Look for specific patterns in the HTML
        # Check for address-like elements
        for element in soup.find_all(['div', 'section', 'article', 'p', 'li']):
            element_text = element.get_text(separator=' ', strip=True)
            
            # Check if this element might contain location info
            location_indicators = [
                'office', 'location', 'address', 'headquarters', 'hq',
                'branch', 'store', 'facility', 'campus', 'center', 'centre',
                'suite', 'floor', 'street', 'avenue', 'road', 'drive',
                'boulevard', 'plaza', 'building', 'phone', 'tel'
            ]
            
            if any(indicator in element_text.lower() for indicator in location_indicators):
                relevant_text.append(element_text)
        
        # Also include the full text if nothing specific found
        if not relevant_text:
            relevant_text = [text]
        
        return ' '.join(relevant_text)[:10000]  # Limit size
    
    def _extract_locations_with_llm(self, text: str, company_name: str) -> List[Dict]:
        """Use LLM to extract location information from text"""
        locations = []
        
        prompt = f"""Extract ALL office locations, addresses, and facilities for {company_name} from this website text.
        
        Look for:
        - Office addresses (street, city, state/province, country, postal code)
        - Headquarters locations
        - Branch offices
        - Store locations
        - Any physical addresses mentioned
        
        Text:
        {text}
        
        Return a JSON array of locations with these fields:
        - name: Location name or office name
        - address: Full street address if available
        - city: City name
        - state: State or province (if mentioned)
        - country: Country name
        - postal_code: Postal/ZIP code if available
        - phone: Phone number if available
        
        Include ALL locations you find. If you find addresses like "20807 Biscayne Blvd, Suite 203, Miami, FL 33180", 
        extract all parts properly.
        
        Return ONLY the JSON array, no other text. If no locations found, return empty array [].
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse response
            import re
            # Try to find JSON array in response
            json_match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if json_match:
                try:
                    locs = json.loads(json_match.group())
                    for loc in locs:
                        if loc.get('city'):  # Must have at least a city
                            # Ensure all fields exist
                            location = {
                                'name': loc.get('name', f"{company_name} - {loc.get('city', 'Unknown')}"),
                                'address': loc.get('address', ''),
                                'city': loc.get('city', ''),
                                'state': loc.get('state', ''),
                                'country': loc.get('country', ''),
                                'postal_code': loc.get('postal_code', ''),
                                'phone': loc.get('phone', ''),
                                'source': 'website',
                                'confidence': 0.8
                            }
                            locations.append(location)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
        
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
        
        return locations
    
class SECFilingAgentNode:
    """SEC filing agent for subsidiary information"""
    
    def __init__(self):
        logger.info("SEC Filing Agent Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Extract from SEC filings (mock for now)"""
        if state.get('sec_filing_results') is not None:
            return state
        
        # Mock implementation - replace with real SEC API later
        locations = [
            {
                'name': f"{state['company_name']} Subsidiary",
                'city': 'Delaware',
                'country': 'USA',
                'source': 'sec_filing',
                'confidence': 0.9
            }
        ]
        
        state['sec_filing_results'] = locations
        state['messages'].append(
            AIMessage(content=f"SEC filings found {len(locations)} subsidiaries")
        )
        
        return state


class AggregatorNode:
    """Aggregate results from all agents"""
    
    def __init__(self):
        logger.info("Aggregator Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Combine all locations"""
        if state.get('all_locations') is not None:
            return state
        
        all_locations = []
        
        for source in ['google_maps_results', 'tavily_search_results', 
                      'web_scraper_results', 'sec_filing_results']:
            locations = state.get(source, [])
            all_locations.extend(locations)
        
        state['all_locations'] = all_locations
        state['messages'].append(
            AIMessage(content=f"Aggregated {len(all_locations)} total locations")
        )
        logger.info(f"Aggregated {len(all_locations)} locations")
        
        return state


class DeduplicationNode:
    """Remove duplicate locations"""
    
    def __init__(self):
        logger.info("Deduplication Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Deduplicate locations"""
        if state.get('deduplicated_locations') is not None:
            return state
        
        seen = set()
        unique = []
        
        for loc in state.get('all_locations', []):
            key = (
                loc.get('city', '').lower(),
                loc.get('name', '').lower()[:30]
            )
            if key not in seen and key[0]:
                seen.add(key)
                unique.append(loc)
        
        state['deduplicated_locations'] = unique
        state['messages'].append(
            AIMessage(content=f"Deduplicated to {len(unique)} unique locations")
        )
        
        return state


class LocationEnrichmentNode:
    """Enrich locations with complete details"""
    
    def __init__(self):
        logger.info("Location Enrichment Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Add missing fields to locations"""
        if state.get('enriched_locations') is not None:
            return state
        
        locations = state.get('deduplicated_locations', [])
        enriched = []
        
        for loc in locations:
            enriched_loc = {
                'name': loc.get('name', f"{state['company_name']} - {loc.get('city', 'Unknown')}"),
                'address': loc.get('address', ''),
                'city': loc.get('city', ''),
                'country': loc.get('country', ''),
                'phone': loc.get('phone', ''),
                'website': loc.get('website', ''),
                'lat': loc.get('lat', 0),
                'lng': loc.get('lng', 0),
                'confidence': loc.get('confidence', 0.5),
                'source': loc.get('source', 'unknown')
            }
            enriched.append(enriched_loc)
        
        state['enriched_locations'] = enriched
        state['final_locations'] = enriched
        state['messages'].append(
            AIMessage(content=f"Enriched {len(enriched)} locations")
        )
        
        return state


class EnhancedExportNode:
    """Enhanced export with better Excel formatting and source tracking"""
    
    def __init__(self, output_dir: str = "data/output/langgraph"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Enhanced Export Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Export to multiple formats with enhanced Excel output"""
        if state.get('export_files'):
            return state
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_slug = state['company_name'].lower().replace(' ', '_').replace('-', '_')[:30]
        
        locations = state.get('final_locations', [])
        
        # Create comprehensive DataFrame with source tracking
        df = self._create_enhanced_dataframe(locations, state)
        
        export_files = []
        
        # 1. Enhanced Excel file with multiple sheets and formatting
        excel_file = self._create_enhanced_excel(df, state, company_slug, timestamp)
        export_files.append(str(excel_file))
        
        # 2. Clean CSV for general use
        csv_file = self._create_clean_csv(df, company_slug, timestamp)
        export_files.append(str(csv_file))
        
        # 3. Detailed JSON for developers
        json_file = self._create_detailed_json(locations, state, company_slug, timestamp)
        export_files.append(str(json_file))
        
        # 4. Summary report
        summary_file = self._create_summary_report(df, state, company_slug, timestamp)
        export_files.append(str(summary_file))
        
        state['export_files'] = export_files
        state['messages'].append(
            AIMessage(content=f"Enhanced export completed: {len(export_files)} files created")
        )
        
        logger.info(f"Enhanced export completed: {len(locations)} locations in {len(export_files)} formats")
        return state
    
    def _create_enhanced_dataframe(self, locations, state):
        """Create a comprehensive DataFrame with all location data and metadata"""
        
        enhanced_data = []
        
        for i, loc in enumerate(locations, 1):
            # Core location data
            row = {
                'Location_ID': f"LOC_{i:03d}",
                'Company_Name': state['company_name'],
                'Location_Name': loc.get('name', ''),
                'Street_Address': loc.get('address', ''),
                'City': loc.get('city', ''),
                'State_Province': loc.get('state', ''),
                'Country': loc.get('country', ''),
                'Postal_Code': loc.get('postal_code', ''),
                'Phone': loc.get('phone', ''),
                'Website': loc.get('website', ''),
                
                # Geographic data
                'Latitude': loc.get('lat', ''),
                'Longitude': loc.get('lng', ''),
                
                # Source and quality data
                'Data_Source': self._format_source_name(loc.get('source', 'unknown')),
                'Source_Confidence': loc.get('confidence', ''),
                'Source_URL': loc.get('source_url', ''),
                
                # Metadata
                'Discovery_Date': datetime.now().strftime('%Y-%m-%d'),
                'Discovery_Time': datetime.now().strftime('%H:%M:%S'),
                'Company_Website': state.get('company_url', ''),
            }
            
            # Add any additional fields that might be present
            for key, value in loc.items():
                if key not in ['name', 'address', 'city', 'state', 'country', 'postal_code', 
                              'phone', 'website', 'lat', 'lng', 'source', 'confidence', 'source_url']:
                    row[f'Extra_{key}'] = value
            
            enhanced_data.append(row)
        
        return pd.DataFrame(enhanced_data)
    
    def _format_source_name(self, source):
        """Format source names for better readability"""
        source_map = {
            'google_maps': 'Google Maps',
            'tavily': 'Tavily Search',
            'website': 'Company Website',
            'sec_filing': 'SEC Filings',
            'unknown': 'Unknown'
        }
        return source_map.get(source.lower(), source.title())
    
    def _create_enhanced_excel(self, df, state, company_slug, timestamp):
        """Create an enhanced Excel file with multiple sheets and formatting"""
        
        excel_file = self.output_dir / f"{company_slug}_{timestamp}_LOCATIONS_REPORT.xlsx"
        
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                
                # Sheet 1: Main Locations Data
                df.to_excel(writer, sheet_name='Locations', index=False)
                
                # Sheet 2: Summary by Source
                source_summary = self._create_source_summary(df, state)
                source_summary.to_excel(writer, sheet_name='Summary by Source', index=False)
                
                # Sheet 3: Geographic Distribution
                geo_summary = self._create_geographic_summary(df)
                geo_summary.to_excel(writer, sheet_name='Geographic Summary', index=False)
                
                # Sheet 4: Data Quality Report
                quality_report = self._create_quality_report(df, state)
                quality_report.to_excel(writer, sheet_name='Data Quality', index=False)
                
                # Format the main sheet
                self._format_excel_sheet(writer, 'Locations', df)
                
            logger.info(f"Enhanced Excel created: {excel_file.name}")
            
        except Exception as e:
            logger.error(f"Error creating enhanced Excel: {e}")
            # Fallback to basic Excel
            excel_file = self.output_dir / f"{company_slug}_{timestamp}_locations_basic.xlsx"
            df.to_excel(excel_file, index=False)
        
        return excel_file
    
    def _create_source_summary(self, df, state):
        """Create summary by data source"""
        
        if df.empty:
            return pd.DataFrame({'Message': ['No locations found']})
        
        summary_data = []
        
        # Group by source
        source_groups = df.groupby('Data_Source')
        
        for source, group in source_groups:
            summary_data.append({
                'Data_Source': source,
                'Locations_Found': len(group),
                'Countries': group['Country'].nunique(),
                'Cities': group['City'].nunique(),
                'Has_Address': (group['Street_Address'] != '').sum(),
                'Has_Phone': (group['Phone'] != '').sum(),
                'Has_Coordinates': ((group['Latitude'] != '') & (group['Longitude'] != '')).sum(),
                'Avg_Confidence': group['Source_Confidence'].replace('', 0).astype(float).mean() if 'Source_Confidence' in group else 0
            })
        
        # Add totals row
        summary_data.append({
            'Data_Source': '🎯 TOTAL',
            'Locations_Found': len(df),
            'Countries': df['Country'].nunique(),
            'Cities': df['City'].nunique(),
            'Has_Address': (df['Street_Address'] != '').sum(),
            'Has_Phone': (df['Phone'] != '').sum(),
            'Has_Coordinates': ((df['Latitude'] != '') & (df['Longitude'] != '')).sum(),
            'Avg_Confidence': df['Source_Confidence'].replace('', 0).astype(float).mean() if not df.empty else 0
        })
        
        return pd.DataFrame(summary_data)
    
    def _create_geographic_summary(self, df):
        """Create geographic distribution summary"""
        
        if df.empty:
            return pd.DataFrame({'Message': ['No locations found']})
        
        geo_data = []
        
        # By Country
        country_counts = df['Country'].value_counts()
        for country, count in country_counts.items():
            if country:  # Skip empty countries
                cities_in_country = df[df['Country'] == country]['City'].nunique()
                geo_data.append({
                    'Type': 'Country',
                    'Location': country,
                    'Total_Locations': count,
                    'Unique_Cities': cities_in_country,
                    'Percentage': f"{(count/len(df)*100):.1f}%"
                })
        
        # By City (top 10)
        city_counts = df['City'].value_counts().head(10)
        for city, count in city_counts.items():
            if city:  # Skip empty cities
                geo_data.append({
                    'Type': 'City',
                    'Location': city,
                    'Total_Locations': count,
                    'Unique_Cities': 1,
                    'Percentage': f"{(count/len(df)*100):.1f}%"
                })
        
        return pd.DataFrame(geo_data)
    
    def _create_quality_report(self, df, state):
        """Create data quality assessment"""
        
        quality_data = []
        
        if df.empty:
            return pd.DataFrame({'Message': ['No locations found']})
        
        total_locations = len(df)
        
        # Field completeness
        fields_to_check = [
            ('Street_Address', 'Street Address'),
            ('City', 'City'),
            ('Country', 'Country'),
            ('Phone', 'Phone Number'),
            ('Website', 'Website'),
            ('Postal_Code', 'Postal Code'),
            ('Latitude', 'Geographic Coordinates'),
        ]
        
        for field, display_name in fields_to_check:
            if field in df.columns:
                complete_count = (df[field] != '').sum()
                quality_data.append({
                    'Data_Field': display_name,
                    'Complete_Records': complete_count,
                    'Missing_Records': total_locations - complete_count,
                    'Completeness_Rate': f"{(complete_count/total_locations*100):.1f}%",
                    'Quality_Score': '🟢 Excellent' if complete_count/total_locations > 0.8 
                                   else '🟡 Good' if complete_count/total_locations > 0.5 
                                   else '🔴 Needs Improvement'
                })
        
        # Add overall assessment
        avg_completeness = sum((df[field] != '').sum() for field, _ in fields_to_check if field in df.columns) / (len(fields_to_check) * total_locations)
        
        quality_data.append({
            'Data_Field': '📊 OVERALL QUALITY',
            'Complete_Records': f"{avg_completeness:.1%}",
            'Missing_Records': f"{1-avg_completeness:.1%}",
            'Completeness_Rate': f"{avg_completeness*100:.1f}%",
            'Quality_Score': '🟢 Excellent' if avg_completeness > 0.8 
                           else '🟡 Good' if avg_completeness > 0.5 
                           else '🔴 Needs Improvement'
        })
        
        return pd.DataFrame(quality_data)
    
    def _format_excel_sheet(self, writer, sheet_name, df):
        """Apply formatting to Excel sheet"""
        try:
            from openpyxl.styles import Font, PatternFill, Alignment
            
            worksheet = writer.sheets[sheet_name]
            
            # Header formatting
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            
            # Format header row
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
        except ImportError:
            logger.warning("openpyxl not available for Excel formatting")
        except Exception as e:
            logger.warning(f"Excel formatting failed: {e}")
    
    def _create_clean_csv(self, df, company_slug, timestamp):
        """Create a clean CSV file"""
        csv_file = self.output_dir / f"{company_slug}_{timestamp}_locations_clean.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # UTF-8 with BOM for Excel compatibility
        return csv_file
    
    def _create_detailed_json(self, locations, state, company_slug, timestamp):
        """Create detailed JSON for developers"""
        json_file = self.output_dir / f"{company_slug}_{timestamp}_detailed.json"
        
        detailed_data = {
            'company': state['company_name'],
            'company_url': state.get('company_url', ''),
            'discovery_timestamp': datetime.now().isoformat(),
            'total_locations': len(locations),
            'sources_used': {
                'google_maps': len(state.get('google_maps_results', [])),
                'tavily': len(state.get('tavily_search_results', [])),
                'website': len(state.get('web_scraper_results', [])),
                'sec': len(state.get('sec_filing_results', []))
            },
            'locations': locations,
            'debug_info': {
                'messages': [msg.content if hasattr(msg, 'content') else str(msg) 
                           for msg in state.get('messages', [])],
                'errors': state.get('errors', [])
            }
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, default=str, ensure_ascii=False)
        
        return json_file
    
    def _create_summary_report(self, df, state, company_slug, timestamp):
        """Create a human-readable summary report"""
        
        summary_file = self.output_dir / f"{company_slug}_{timestamp}_SUMMARY_REPORT.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write(f"LOCATION DISCOVERY REPORT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Company: {state['company_name']}\n")
            f.write(f"Company Website: {state.get('company_url', 'Not provided')}\n")
            f.write(f"Discovery Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("="*40 + "\n")
            f.write("SUMMARY\n")
            f.write("="*40 + "\n")
            f.write(f"Total Locations Found: {len(df)}\n")
            
            if not df.empty:
                f.write(f"Countries Covered: {df['Country'].nunique()}\n")
                f.write(f"Cities Covered: {df['City'].nunique()}\n\n")
                
                f.write("Locations by Source:\n")
                source_counts = df['Data_Source'].value_counts()
                for source, count in source_counts.items():
                    f.write(f"  • {source}: {count} locations\n")
                
                f.write(f"\nTop Countries:\n")
                country_counts = df['Country'].value_counts().head(5)
                for country, count in country_counts.items():
                    if country:
                        f.write(f"  • {country}: {count} locations\n")
            
            f.write(f"\n" + "="*40 + "\n")
            f.write("FILES GENERATED\n")
            f.write("="*40 + "\n")
            f.write(f"📊 Excel Report: {company_slug}_{timestamp}_LOCATIONS_REPORT.xlsx\n")
            f.write(f"📋 CSV Data: {company_slug}_{timestamp}_locations_clean.csv\n")
            f.write(f"💻 JSON Data: {company_slug}_{timestamp}_detailed.json\n")
            f.write(f"📄 This Summary: {company_slug}_{timestamp}_SUMMARY_REPORT.txt\n")
        
        return summary_file


class SummaryNode:
    """Create final summary"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("Summary Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Generate summary"""
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
                'sec': len(state.get('sec_filing_results', []))
            },
            'url_processed': bool(clean_and_validate_url(state.get('company_url', '')))
        }
        
        state['summary'] = summary
        state['status'] = 'completed'
        
        # Generate natural language summary
        url_status = "with URL" if summary['url_processed'] else "without valid URL"
        prompt = f"""Summarize discovery for {state['company_name']} ({url_status}):
        Found {summary['total_locations']} locations total.
        Sources: Google Maps ({summary['sources_used']['google_maps']}), 
        Tavily ({summary['sources_used']['tavily']}),
        Website ({summary['sources_used']['website']}),
        SEC ({summary['sources_used']['sec']}).
        Brief 2-sentence summary."""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            state['messages'].append(AIMessage(content=response.content))
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            state['messages'].append(AIMessage(content=f"Discovery completed for {state['company_name']} - found {summary['total_locations']} locations"))
        
        return state


class EnhancedSupervisorNode:
    """Orchestrate the workflow"""
    
    def __init__(self):
        logger.info("Enhanced Supervisor Node initialized")
    
    def run(self, state: DiscoveryState) -> DiscoveryState:
        """Route to next agent"""
        
        # Check completion status
        has_google = state.get('google_maps_results') is not None
        has_tavily = state.get('tavily_search_results') is not None
        has_web = state.get('web_scraper_results') is not None
        has_sec = state.get('sec_filing_results') is not None
        has_aggregated = state.get('all_locations') is not None
        has_deduped = state.get('deduplicated_locations') is not None
        has_enriched = state.get('enriched_locations') is not None
        has_exported = state.get('export_files') is not None
        has_summary = state.get('summary') is not None
        
        # Determine next step
        if not has_google:
            state['next_agent'] = 'google_maps'
        elif not has_tavily:
            state['next_agent'] = 'tavily_search'
        elif not has_web:
            state['next_agent'] = 'web_scraper'
        elif not has_sec:
            state['next_agent'] = 'sec_filing'
        elif not has_aggregated:
            state['next_agent'] = 'aggregator'
        elif not has_deduped:
            state['next_agent'] = 'deduplication'
        elif not has_enriched:
            state['next_agent'] = 'enricher'
        elif not has_exported:
            state['next_agent'] = 'exporter'
        elif not has_summary:
            state['next_agent'] = 'summary'
        else:
            state['next_agent'] = 'end'
        
        logger.info(f"Supervisor: Next agent is {state['next_agent']}")
        return state


# ===== MAIN WORKFLOW CLASS =====

class EnhancedDiscoveryWorkflow:
    """Complete multi-agent discovery workflow with better URL handling"""
    
    def __init__(self, output_dir: str = "data/output/langgraph"):
        # Initialize all nodes
        self.google_maps_node = EnhancedGoogleMapsAgentNode()
        self.tavily_node = TavilySearchAgentNode()
        self.web_scraper_node = ImprovedWebScraperAgentNode()
        self.sec_filing_node = SECFilingAgentNode()
        self.aggregator_node = AggregatorNode()
        self.deduplication_node = DeduplicationNode()
        self.enrichment_node = LocationEnrichmentNode()
        self.export_node = EnhancedExportNode(output_dir)
        self.summary_node = SummaryNode()
        self.supervisor_node = EnhancedSupervisorNode()
        
        # Build the graph
        self.graph = self._build_graph()
        logger.info("Enhanced Discovery Workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph"""
        workflow = StateGraph(DiscoveryState)
        
        # Add all nodes
        workflow.add_node("supervisor", self.supervisor_node.run)
        workflow.add_node("google_maps", self.google_maps_node.run)
        workflow.add_node("tavily_search", self.tavily_node.run)
        workflow.add_node("web_scraper", self.web_scraper_node.run)
        workflow.add_node("sec_filing", self.sec_filing_node.run)
        workflow.add_node("aggregator", self.aggregator_node.run)
        workflow.add_node("deduplication", self.deduplication_node.run)
        workflow.add_node("enricher", self.enrichment_node.run)
        workflow.add_node("exporter", self.export_node.run)
        workflow.add_node("summary", self.summary_node.run)
        
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
                "sec_filing": "sec_filing",
                "aggregator": "aggregator",
                "deduplication": "deduplication",
                "enricher": "enricher",
                "exporter": "exporter",
                "summary": "summary",
                "end": END
            }
        )
        
        # All nodes return to supervisor
        for node in ["google_maps", "tavily_search", "web_scraper", 
                    "sec_filing", "aggregator", "deduplication",
                    "enricher", "exporter", "summary"]:
            workflow.add_edge(node, "supervisor")
        
        return workflow.compile()
    
    def discover(self, company_name: str, company_url: str = None) -> Dict:
        """Run discovery for a company with better URL handling"""
        logger.info(f"Starting discovery for {company_name}")
        
        # Clean and validate the URL
        cleaned_url = clean_and_validate_url(company_url) if company_url else ""
        logger.info(f"URL processing: '{company_url}' -> '{cleaned_url}'")
        
        initial_state = {
            'company_name': company_name,
            'company_url': cleaned_url,
            'messages': [HumanMessage(content=f"Discover locations for {company_name} (URL: {cleaned_url})")],
            'errors': []
        }
        
        try:
            result = self.graph.invoke(
                initial_state,
                config={"recursion_limit": 50}
            )
            
            return {
                'company': company_name,
                'url': cleaned_url,
                'locations': result.get('final_locations', []),
                'summary': result.get('summary', {}),
                'messages': [msg.content if hasattr(msg, 'content') else str(msg) 
                           for msg in result.get('messages', [])],
                'errors': result.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return {
                'company': company_name,
                'url': cleaned_url,
                'locations': [],
                'summary': {'error': str(e)},
                'messages': [],
                'errors': [str(e)]
            }


# Alias for compatibility
CompanyDiscoveryWorkflow = EnhancedDiscoveryWorkflow




   # Add the test 
if __name__ == "__main__":
    workflow = EnhancedDiscoveryWorkflow()
    result = workflow.discover("ADP GROUP", "https://adp.com")
    print(f"Result: {len(result['locations'])} locations")