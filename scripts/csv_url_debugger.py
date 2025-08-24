"""
CSV URL Debugger - Standalone file to debug why URLs are not being read correctly
Run this file to diagnose CSV reading issues without touching your existing code
"""

import pandas as pd
import numpy as np
from pathlib import Path

def debug_csv_urls(csv_file_path):
    """Debug CSV URL reading issues"""
    
    print("=" * 60)
    print("CSV URL DEBUGGER")
    print("=" * 60)
    
    if not Path(csv_file_path).exists():
        print(f"❌ CSV file not found: {csv_file_path}")
        print("Please update the path in this script")
        return
    
    print(f"📁 Reading file: {csv_file_path}")
    
    # Method 1: Default pandas reading (what your code probably does)
    print("\n🔍 METHOD 1: Default pandas reading")
    try:
        df1 = pd.read_csv(csv_file_path)
        print(f"Shape: {df1.shape}")
        print(f"Columns: {list(df1.columns)}")
        
        if 'company_url' in df1.columns:
            print(f"URL column type: {df1['company_url'].dtype}")
            print(f"Null values: {df1['company_url'].isnull().sum()}")
            print(f"Empty strings: {(df1['company_url'] == '').sum()}")
            
            # Check ADP GROUP specifically
            adp_mask = df1['company_name'].str.contains('ADP GROUP', na=False)
            if adp_mask.any():
                adp_url = df1.loc[adp_mask, 'company_url'].iloc[0]
                print(f"🎯 ADP GROUP URL: '{adp_url}' (type: {type(adp_url)})")
                print(f"   Is null: {pd.isna(adp_url)}")
                print(f"   Is empty string: {adp_url == ''}")
            else:
                print("❌ ADP GROUP not found")
                
    except Exception as e:
        print(f"❌ Error with method 1: {e}")
    
    # Method 2: Force string reading
    print("\n🔍 METHOD 2: Force string reading")
    try:
        df2 = pd.read_csv(csv_file_path, dtype=str, keep_default_na=False)
        
        if 'company_url' in df2.columns:
            # Check ADP GROUP
            adp_mask = df2['company_name'].str.contains('ADP GROUP', na=False)
            if adp_mask.any():
                adp_url = df2.loc[adp_mask, 'company_url'].iloc[0]
                print(f"🎯 ADP GROUP URL: '{adp_url}' (type: {type(adp_url)})")
                print(f"   Length: {len(adp_url)}")
                
    except Exception as e:
        print(f"❌ Error with method 2: {e}")
    
    # Method 3: Show raw file content
    print("\n🔍 METHOD 3: Raw file inspection")
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:15]  # First 15 lines
            
        print("Raw file content (first 15 lines):")
        for i, line in enumerate(lines):
            print(f"{i+1:2d}: {line.rstrip()}")
            
        # Look for ADP GROUP line specifically
        print("\n🔍 Searching for ADP GROUP in raw file:")
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if 'ADP GROUP' in line:
                    print(f"Line {i+1}: {line.strip()}")
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        print(f"   Company: '{parts[0]}'")
                        print(f"   URL: '{parts[1]}'")
                    break
                    
    except Exception as e:
        print(f"❌ Error reading raw file: {e}")
    
    # Method 4: Sample data analysis
    print("\n🔍 METHOD 4: Sample data analysis")
    try:
        df = pd.read_csv(csv_file_path, dtype=str, keep_default_na=False)
        
        print("First 10 companies and their URLs:")
        for i in range(min(10, len(df))):
            company = df.iloc[i].get('company_name', 'NO_NAME')
            url = df.iloc[i].get('company_url', 'NO_URL')
            print(f"{i+1:2d}. '{company}' -> '{url}' (len: {len(str(url))})")
            
    except Exception as e:
        print(f"❌ Error with sample analysis: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

def test_url_cleaning_function():
    """Test the URL cleaning function from your code"""
    print("\n🧪 TESTING URL CLEANING FUNCTION")
    
    # Test cases based on what we see in your CSV
    test_urls = [
        "https://adp.com",
        "adp.com",
        "",
        "nan",
        None,
        "https://accutraccapital.com",
        "  https://adp.com  ",  # with spaces
    ]
    
    # Copy the function from your code
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
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme:
                return url
        except Exception as e:
            print(f"URL validation failed for {url}: {e}")
        
        return ""
    
    for test_url in test_urls:
        cleaned = clean_and_validate_url(test_url)
        print(f"'{test_url}' -> '{cleaned}'")

if __name__ == "__main__":
    # UPDATE THIS PATH TO YOUR CSV FILE
    csv_path = "data/input/companies.csv"
    
    # Run the debugging
    debug_csv_urls(csv_path)
    
    # Test URL cleaning
    test_url_cleaning_function()
    
    print("\n💡 NEXT STEPS:")
    print("1. Check the output above to see what's happening with your URLs")
    print("2. If URLs look correct in raw file but wrong in pandas, it's a CSV reading issue")
    print("3. If you need a fix, I can create a separate CSV reader file")