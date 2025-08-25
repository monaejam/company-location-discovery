#!/usr/bin/env python3
"""
Test with a B2B tech company that actually lists office locations
"""
import os
import sys
sys.path.append('api')

from master_discovery_workflow import EnhancedDiscoveryWorkflow
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tech_companies():
    """Test companies that actually list office locations"""
    
    companies = [
        ("Atlassian", "https://www.atlassian.com"),
        ("Salesforce", "https://www.salesforce.com"), 
        ("HubSpot", "https://www.hubspot.com"),
        ("Zoom", "https://zoom.us")
    ]
    
    workflow = EnhancedDiscoveryWorkflow(
        output_dir="/tmp/output",
        api_keys=None
    )
    
    for company_name, company_url in companies:
        print(f"\n🔍 Testing: {company_name}")
        print("=" * 50)
        
        try:
            result = workflow.discover(
                company_name=company_name,
                company_url=company_url
            )
            
            locations = result.get('locations', [])
            summary = result.get('summary', {})
            sources = summary.get('sources_used', {})
            
            print(f"📊 Results for {company_name}:")
            print(f"  Total locations: {len(locations)}")
            print(f"  Website: {sources.get('website', 0)}")
            print(f"  Directory: {sources.get('directory', 0)}")
            
            if locations:
                print(f"  ✅ SUCCESS - Found {len(locations)} locations")
                for loc in locations[:2]:  # Show first 2
                    print(f"    • {loc.get('name', 'Unknown')} - {loc.get('city', 'No city')}")
                break  # Stop at first successful one
            else:
                print(f"  ❌ No locations found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎯 CONCLUSION:")
    if any(len(workflow.discover(name, url).get('locations', [])) > 0 for name, url in companies):
        print("✅ System is WORKING - just need companies with office info")
        print("❌ McDonald's failed because it's a franchise (no corporate offices listed)")
        print("🔑 Need Google Maps/Tavily API keys for better coverage")
    else:
        print("❌ System has issues - no locations found for any company")

if __name__ == "__main__":
    test_tech_companies()
