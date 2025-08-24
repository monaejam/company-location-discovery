"""
Workflow Debugger - Find where URLs are getting lost in your main processing loop
This will help identify where the URL becomes empty between CSV reading and the web scraper
"""

import pandas as pd
from pathlib import Path

def debug_workflow_url_passing(csv_file_path):
    """Debug the workflow to see where URLs get lost"""
    
    print("=" * 60)
    print("WORKFLOW URL DEBUGGER")
    print("=" * 60)
    
    # Step 1: Read CSV (we know this works)
    df = pd.read_csv(csv_file_path)
    print(f"✅ Step 1: Read CSV - {len(df)} companies")
    
    # Find ADP GROUP
    adp_mask = df['company_name'].str.contains('ADP GROUP', na=False)
    if not adp_mask.any():
        print("❌ ADP GROUP not found in CSV")
        return
    
    adp_row = df.loc[adp_mask].iloc[0]
    company_name = adp_row['company_name']
    company_url = adp_row['company_url']
    
    print(f"✅ Step 2: Found ADP GROUP")
    print(f"   company_name: '{company_name}' (type: {type(company_name)})")
    print(f"   company_url: '{company_url}' (type: {type(company_url)})")
    
    # Step 3: Test what happens in your main loop
    print(f"\n🔍 Step 3: Simulating your main processing loop")
    
    # This simulates what your code probably does:
    for index, row in df.iterrows():
        if 'ADP GROUP' in str(row.get('company_name', '')):
            print(f"   Found ADP GROUP at index {index}")
            
            # Check different ways of accessing the data
            method1_name = row['company_name']
            method1_url = row['company_url']
            print(f"   Method 1 - Direct access:")
            print(f"     Name: '{method1_name}'")
            print(f"     URL: '{method1_url}' (len: {len(str(method1_url))})")
            
            method2_name = row.get('company_name', '')
            method2_url = row.get('company_url', '')
            print(f"   Method 2 - .get() access:")
            print(f"     Name: '{method2_name}'")
            print(f"     URL: '{method2_url}' (len: {len(str(method2_url))})")
            
            # Test string operations
            name_stripped = str(method1_name).strip()
            url_stripped = str(method1_url).strip()
            print(f"   After .strip():")
            print(f"     Name: '{name_stripped}'")
            print(f"     URL: '{url_stripped}' (len: {len(url_stripped)})")
            
            break
    
    print(f"\n🔍 Step 4: Test your workflow initialization")
    
    # Try to simulate what your workflow does
    try:
        # This is what your workflow probably receives
        test_state = {
            'company_name': company_name,
            'company_url': company_url,
            'messages': [],
            'errors': []
        }
        
        print(f"   Initial state:")
        print(f"     company_name: '{test_state['company_name']}'")
        print(f"     company_url: '{test_state['company_url']}'")
        
        # Test the URL cleaning (we know this works)
        from enhanced_discovery_workflow import clean_and_validate_url
        cleaned_url = clean_and_validate_url(test_state['company_url'])
        print(f"   After URL cleaning: '{cleaned_url}'")
        
    except ImportError:
        print("   ⚠️ Could not import your workflow - but state looks correct")
    except Exception as e:
        print(f"   ❌ Error in workflow simulation: {e}")

def find_the_bug_in_main_script():
    """Show common places where URLs get lost"""
    
    print(f"\n🐛 COMMON PLACES WHERE URLs GET LOST:")
    print("=" * 50)
    
    print("1. ❌ Wrong column name:")
    print("   # If your code has:")
    print("   company_url = row['url']  # Should be 'company_url'")
    print()
    
    print("2. ❌ Index vs iterrows confusion:")
    print("   # Wrong:")
    print("   for i, row in enumerate(df.values):")
    print("       url = row[1]  # Might be wrong index")
    print("   # Right:")
    print("   for index, row in df.iterrows():")
    print("       url = row['company_url']")
    print()
    
    print("3. ❌ Variable name confusion:")
    print("   # Check if you have:")
    print("   company_name = row['company_name']")
    print("   company_url = row['company_url']  # Make sure this line exists")
    print()
    
    print("4. ❌ State dictionary issues:")
    print("   # Check if your workflow receives:")
    print("   initial_state = {")
    print("       'company_name': company_name,")
    print("       'company_url': company_url,  # Make sure this is here")
    print("   }")
    print()
    
    print("5. ❌ Pandas iteration issues:")
    print("   # Make sure you're using:")
    print("   for index, row in df.iterrows():  # Not df.values")

def create_minimal_test():
    """Create a minimal test to isolate the issue"""
    
    print(f"\n🧪 MINIMAL TEST CASE")
    print("=" * 30)
    
    # Create a simple test case
    test_data = {
        'company_name': ['ADP GROUP'],
        'company_url': ['https://adp.com']
    }
    
    df = pd.DataFrame(test_data)
    print("Created test DataFrame:")
    print(df)
    
    print("\nTesting iteration:")
    for index, row in df.iterrows():
        name = row['company_name']
        url = row['company_url']
        print(f"  Row {index}: '{name}' -> '{url}'")
        
        # Test what happens when we create a state dict
        state = {
            'company_name': name,
            'company_url': url
        }
        print(f"  State: {state}")
        
        # Test accessing from state
        state_url = state.get('company_url', '')
        print(f"  URL from state: '{state_url}' (len: {len(state_url)})")

if __name__ == "__main__":
    csv_path = "data/input/companies.csv"
    
    if Path(csv_path).exists():
        debug_workflow_url_passing(csv_path)
        find_the_bug_in_main_script()
        create_minimal_test()
        
        print(f"\n💡 RECOMMENDATION:")
        print("The CSV reading is PERFECT. The issue is in your main processing loop.")
        print("Look at your main script where you:")
        print("1. Read the CSV")
        print("2. Loop through companies") 
        print("3. Call workflow.discover(company_name, company_url)")
        print("\nThe URL is becoming empty somewhere in steps 2-3!")
        
    else:
        print(f"CSV file not found: {csv_path}")