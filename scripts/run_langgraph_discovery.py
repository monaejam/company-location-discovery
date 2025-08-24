"""
FIXED VERSION of your main script
The bug was in how you're reading the CSV or passing data to the workflow
"""
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from pathlib import Path
import argparse
from tqdm import tqdm
import json
from datetime import datetime
from loguru import logger

def load_companies(csv_file: str) -> pd.DataFrame:
    """Load companies from CSV with proper URL handling"""
    
    # FIXED: Read CSV with proper settings to preserve URLs
    df = pd.read_csv(csv_file, dtype=str, keep_default_na=False)
    
    logger.info(f"Loaded {len(df)} companies from {csv_file}")
    
    # DEBUG: Check what we actually loaded
    logger.info(f"CSV columns: {list(df.columns)}")
    
    # Clean the data
    if 'company_name' in df.columns:
        df['company_name'] = df['company_name'].str.strip()
    
    if 'company_url' in df.columns:
        df['company_url'] = df['company_url'].str.strip()
        non_empty_urls = (df['company_url'] != '').sum()
        logger.info(f"Found {non_empty_urls} non-empty URLs out of {len(df)} companies")
        
        # DEBUG: Show first few entries
        for i in range(min(3, len(df))):
            company = df.iloc[i]['company_name']
            url = df.iloc[i]['company_url']
            logger.debug(f"Row {i}: '{company}' -> '{url}' (len: {len(url)})")
    else:
        logger.warning("No 'company_url' column found! Adding empty column.")
        df['company_url'] = ''
    
    return df

def run_batch_discovery(companies_df: pd.DataFrame, limit: int = None, output_dir: str = "data/output/langgraph"):
    """Run discovery for multiple companies"""
    
    # Import your workflow - CORRECT PATH
    import sys
    import os
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    
    from src.workflows.master_discovery_workflow import EnhancedDiscoveryWorkflow
    
    # Initialize workflow
    workflow = EnhancedDiscoveryWorkflow(output_dir)
    logger.info("✅ LangGraph workflow initialized")
    
    # Limit companies if specified
    if limit:
        companies_df = companies_df.head(limit)
    
    results = []
    success_count = 0
    error_count = 0
    
    print(f"📊 Processing {len(companies_df)} companies with LangGraph")
    
    # Process each company
    progress_bar = tqdm(companies_df.iterrows(), total=len(companies_df), desc="Processing")
    
    for index, row in progress_bar:
        company_name = row['company_name']
        company_url = row['company_url']  # This was probably missing or wrong in your original script
        
        # DEBUG: Log what we're about to process
        logger.debug(f"Processing row {index}: '{company_name}' with URL '{company_url}' (len: {len(company_url)})")
        
        progress_bar.set_description(f"Processing: {company_name[:30]}...")
        
        try:
            # FIXED: Make sure we pass BOTH parameters correctly
            result = workflow.discover(company_name, company_url)
            
            locations_count = len(result.get('locations', []))
            results.append(result)
            
            if result.get('errors'):
                logger.warning(f"Completed with errors: {company_name} - {result['errors']}")
                error_count += 1
            else:
                success_count += 1
            
            progress_bar.set_postfix({
                'Locations': locations_count,
                'Success': success_count,
                'Errors': error_count
            })
            
        except Exception as e:
            logger.error(f"Failed to process {company_name}: {e}")
            results.append({
                'company': company_name,
                'url': company_url,
                'locations': [],
                'summary': {'error': str(e)},
                'messages': [],
                'errors': [str(e)]
            })
            error_count += 1
    
    progress_bar.close()
    
    return results, success_count, error_count

def save_batch_summary(results: list, output_dir: str):
    """Save batch processing summary"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_path / f"batch_summary_{timestamp}.json"
    
    # Create summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_companies': len(results),
        'successful': sum(1 for r in results if not r.get('errors')),
        'errors': sum(1 for r in results if r.get('errors')),
        'total_locations': sum(len(r.get('locations', [])) for r in results),
        'results': results
    }
    
    # Save summary
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    return summary_file

def main():
    parser = argparse.ArgumentParser(description='Run LangGraph Multi-Agent Discovery')
    parser.add_argument('--batch', type=str, help='CSV file with companies')
    parser.add_argument('--single', type=str, help='Single company name')
    parser.add_argument('--url', type=str, help='Company URL (for single mode)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--output', type=str, default='data/output/langgraph', 
                       help='Output directory')
    
    args = parser.parse_args()
    
    print("🚀 LangGraph Multi-Agent Company Discovery")
    print("=" * 60)
    
    logger.info("Initializing LangGraph multi-agent workflow...")
    
    if args.batch:
        # Batch processing
        if not Path(args.batch).exists():
            print(f"❌ CSV file not found: {args.batch}")
            return
        
        # Load companies with fixed CSV reading
        companies_df = load_companies(args.batch)
        
        # Run batch discovery
        results, success_count, error_count = run_batch_discovery(
            companies_df, 
            limit=args.limit, 
            output_dir=args.output
        )
        
        # Save summary
        summary_file = save_batch_summary(results, args.output)
        
        # Print results
        print("\n" + "=" * 60)
        print("Batch Processing Complete")
        print("=" * 60)
        print(f"✅ Successfully processed: {success_count} companies")
        print(f"❌ Errors: {error_count} companies")
        
        # Show top companies by locations
        if results:
            sorted_results = sorted(results, key=lambda x: len(x.get('locations', [])), reverse=True)
            print(f"\n📊 Top companies by locations found:")
            for result in sorted_results[:5]:
                locations_count = len(result.get('locations', []))
                if locations_count > 0:
                    print(f"  - {result['company']}: {locations_count} locations")
        
        print(f"\n📊 Batch summary saved to: {summary_file}")
        
    elif args.single:
        # Single company processing - CORRECT PATH
        import sys
        import os
        
        # Add project root to Python path
        project_root = os.path.dirname(os.path.dirname(__file__))
        sys.path.insert(0, project_root)
        
        from src.workflows.master_discovery_workflow import EnhancedDiscoveryWorkflow
        
        workflow = EnhancedDiscoveryWorkflow(args.output)
        
        print(f"🔍 Processing single company: {args.single}")
        if args.url:
            print(f"🌐 URL: {args.url}")
        
        result = workflow.discover(args.single, args.url)
        
        locations_count = len(result.get('locations', []))
        print(f"✅ Found {locations_count} locations")
        
        if result.get('errors'):
            print(f"⚠️ Errors: {result['errors']}")
        
    else:
        print("❌ Please specify either --batch <csv_file> or --single <company_name>")
        parser.print_help()

if __name__ == "__main__":
    main()