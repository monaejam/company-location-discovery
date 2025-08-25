#!/usr/bin/env python3
"""
Test McDonald's Corporation specifically to debug the 0 locations issue
"""
import os
import sys
sys.path.append('api')

from master_discovery_workflow import EnhancedDiscoveryWorkflow
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mcdonalds():
    """Test McDonald's Corporation specifically"""
    
    print("🍟 Testing McDonald's Corporation")
    print("=" * 50)
    
    # Test with no API keys (only web scraper and directory will work)
    workflow = EnhancedDiscoveryWorkflow(
        output_dir="/tmp/output",
        api_keys=None
    )
    
    company_name = "McDonald's Corporation"
    company_url = "https://www.mcdonalds.com"
    
    print(f"Company: {company_name}")
    print(f"URL: {company_url}")
    print()
    
    try:
        result = workflow.discover(
            company_name=company_name,
            company_url=company_url
        )
        
        print("📊 RESULTS:")
        print("-" * 30)
        
        locations = result.get('locations', [])
        print(f"Total locations found: {len(locations)}")
        
        # Check each agent's results
        summary = result.get('summary', {})
        sources = summary.get('sources_used', {})
        
        print(f"✅ Google Maps: {sources.get('google_maps', 0)} (expected 0 - no API key)")
        print(f"✅ Tavily: {sources.get('tavily', 0)} (expected 0 - no API key)")
        print(f"🔍 Website: {sources.get('website', 0)} (should find some)")
        print(f"🔍 Directory: {sources.get('directory', 0)} (should find some)")
        print()
        
        print("📝 AGENT MESSAGES:")
        messages = result.get('messages', [])
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"  • {content}")
        print()
        
        if result.get('errors'):
            print("❌ ERRORS:")
            for error in result.get('errors', []):
                print(f"  • {error}")
            print()
        
        if locations:
            print("📍 FOUND LOCATIONS:")
            for i, loc in enumerate(locations):
                name = loc.get('name', 'Unknown')
                city = loc.get('city', 'No city')
                address = loc.get('address', 'No address')
                source = loc.get('source', 'unknown')
                confidence = loc.get('confidence', 0)
                
                print(f"  {i+1}. {name}")
                print(f"     City: {city}")
                print(f"     Address: {address}")
                print(f"     Source: {source} (confidence: {confidence})")
                print()
        else:
            print("❌ NO LOCATIONS FOUND")
            print("This indicates a problem with web scraper or directory agents")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcdonalds()
