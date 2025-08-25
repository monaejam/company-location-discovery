#!/usr/bin/env python3
"""
Quick debug test to see why agents are returning 0 locations
"""
import os
import sys
sys.path.append('api')

from master_discovery_workflow import EnhancedDiscoveryWorkflow
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality without API keys"""
    
    print("🔍 Testing basic workflow functionality...")
    print("=" * 50)
    
    # Test with no API keys first (should still work for web scraper)
    workflow = EnhancedDiscoveryWorkflow(
        output_dir="/tmp/output",
        api_keys=None
    )
    
    # Test with a well-known company
    company_name = "Microsoft"
    company_url = "https://www.microsoft.com"
    
    print(f"Testing company: {company_name}")
    print(f"Testing URL: {company_url}")
    print()
    
    try:
        result = workflow.discover(
            company_name=company_name,
            company_url=company_url
        )
        
        print("📊 RESULTS:")
        print("-" * 30)
        print(f"Total locations: {len(result.get('locations', []))}")
        
        summary = result.get('summary', {})
        sources = summary.get('sources_used', {})
        
        print(f"Google Maps: {sources.get('google_maps', 0)}")
        print(f"Tavily: {sources.get('tavily', 0)}")  
        print(f"Website: {sources.get('website', 0)}")
        print(f"Directory: {sources.get('directory', 0)}")
        print()
        
        print("📝 MESSAGES:")
        for msg in result.get('messages', []):
            if hasattr(msg, 'content'):
                print(f"  • {msg.content}")
            else:
                print(f"  • {msg}")
        print()
        
        print("❌ ERRORS:")
        for error in result.get('errors', []):
            print(f"  • {error}")
        print()
        
        if result.get('locations'):
            print("📍 SAMPLE LOCATIONS:")
            for i, loc in enumerate(result.get('locations', [])[:3]):
                print(f"  {i+1}. {loc.get('name', 'Unknown')} - {loc.get('city', 'No city')} ({loc.get('source', 'unknown')})")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def check_environment():
    """Check environment and API keys"""
    print("🔧 Environment Check:")
    print("=" * 50)
    
    # Check API keys
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GOOGLE_MAPS_API_KEY': os.getenv('GOOGLE_MAPS_API_KEY'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY')
    }
    
    for key, value in api_keys.items():
        status = "✅ SET" if value else "❌ MISSING"
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else "None"
        print(f"{key}: {status} ({masked_value})")
    
    print()
    
    # Check required packages
    packages = ['requests', 'beautifulsoup4', 'openai', 'langchain']
    print("📦 Package Check:")
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} - NOT INSTALLED")
    
    print()

if __name__ == "__main__":
    check_environment()
    test_basic_functionality()
