#!/usr/bin/env python3
"""
Test the workflow directly to see what's happening
"""
import os
import sys
import asyncio
from master_discovery_workflow import EnhancedDiscoveryWorkflow

def test_workflow():
    """Test the workflow with a simple company"""
    
    # Set up some test API keys (using None to see what happens without keys)
    test_api_keys = {
        'openai_api_key': None,  # No key - should disable OpenAI features
        'google_maps_api_key': None,  # No key - should disable Google Maps
        'tavily_api_key': None  # No key - should disable Tavily
    }
    
    print("🔍 Testing workflow...")
    print(f"API keys provided: {list(test_api_keys.keys())}")
    
    try:
        # Create workflow
        workflow = EnhancedDiscoveryWorkflow(
            output_dir="temp/output",
            api_keys=test_api_keys
        )
        
        print("✅ Workflow created successfully")
        
        # Test with Microsoft
        print("\n🏢 Testing with Microsoft...")
        result = workflow.discover(
            company_name="Microsoft",
            company_url="https://microsoft.com"
        )
        
        print(f"\n📊 RESULTS:")
        print(f"Company: {result.get('company', 'Unknown')}")
        print(f"URL: {result.get('url', 'None')}")
        print(f"Total locations: {len(result.get('locations', []))}")
        print(f"Summary: {result.get('summary', {})}")
        print(f"Messages: {result.get('messages', [])}")
        print(f"Errors: {result.get('errors', [])}")
        
        print(f"\n📍 LOCATIONS FOUND:")
        for i, loc in enumerate(result.get('locations', []), 1):
            print(f"{i}. {loc.get('name', 'Unknown')} - {loc.get('city', 'Unknown City')} ({loc.get('source', 'Unknown source')})")
        
        if len(result.get('locations', [])) == 0:
            print("❌ NO LOCATIONS FOUND - This is the problem!")
            print("\nLet's check what each agent returned:")
            summary = result.get('summary', {})
            sources = summary.get('sources_used', {})
            for source, count in sources.items():
                print(f"  {source}: {count} locations")
        else:
            print(f"✅ Found {len(result.get('locations', []))} locations - workflow is working!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()
