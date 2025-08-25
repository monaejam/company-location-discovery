"""
FastAPI Backend for Company Location Discovery
Users provide their own API keys - no server-side environment variables needed
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import json
from datetime import datetime
from loguru import logger
import tempfile
import os

# Import the real workflow
from master_discovery_workflow import EnhancedDiscoveryWorkflow

# Initialize FastAPI app
app = FastAPI(
    title="Company Location Discovery API",
    description="Multi-agent AI system for discovering company locations worldwide - users provide their own API keys",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory storage for job status (in production, use Redis or database)
jobs_storage: Dict[str, Dict] = {}

# Pydantic Models
class APIKeys(BaseModel):
    openai_api_key: str = Field(..., description="OpenAI API key (required)")
    google_maps_api_key: Optional[str] = Field(None, description="Google Maps API key (optional)")
    tavily_api_key: Optional[str] = Field(None, description="Tavily API key (optional)")

class CompanyRequest(BaseModel):
    company_name: str = Field(..., description="Company name to search for")
    company_url: Optional[str] = Field(None, description="Company website URL (optional)")
    api_keys: APIKeys = Field(..., description="API keys provided by user")

class BatchRequest(BaseModel):
    companies: List[CompanyRequest] = Field(..., description="List of companies to process")
    api_keys: APIKeys = Field(..., description="API keys for batch processing")

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: int  # 0-100
    message: str
    created_at: str
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    download_urls: Optional[List[str]] = None

# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    """API health check and information"""
    return {
        "message": "Company Location Discovery API",
        "status": "healthy",
        "version": "2.0.0",
        "description": "Multi-agent AI system for discovering company locations worldwide",
        "note": "Users provide their own API keys",
        "features": [
            "Single company discovery",
            "Batch processing (up to 50 companies)",
            "Real-time job status tracking",
            "Multiple export formats (JSON, CSV, Excel)",
            "Global location coverage"
        ],
        "endpoints": {
            "single_discovery": "/discover/single",
            "batch_discovery": "/discover/batch",
            "job_status": "/jobs/{job_id}/status",
            "job_results": "/jobs/{job_id}/results",
            "list_jobs": "/jobs"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True
    }

@app.post("/discover/single", tags=["Discovery"])
async def discover_single_company(
    request: CompanyRequest,
    background_tasks: BackgroundTasks
):
    """
    Discover locations for a single company
    
    Requires user to provide their own API keys:
    - openai_api_key (required)
    - google_maps_api_key (optional, but recommended)
    - tavily_api_key (optional, for enhanced web search)
    """
    
    # Validate required API keys
    if not request.api_keys.openai_api_key.strip():
        raise HTTPException(
            status_code=400, 
            detail="OpenAI API key is required. Please provide your API key."
        )
    
    # Validate company name
    if not request.company_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Company name is required"
        )
    
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs_storage[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message=f"Job queued for processing: {request.company_name}",
        created_at=datetime.now().isoformat()
    ).dict()
    
    # Start background task
    background_tasks.add_task(
        process_single_company,
        job_id,
        request.company_name,
        request.company_url,
        request.api_keys
    )
    
    logger.info(f"Created job {job_id} for company: {request.company_name}")
    
    return {
        "job_id": job_id, 
        "status": "queued",
        "company_name": request.company_name,
        "message": "Job has been queued for processing"
    }

@app.post("/discover/batch", tags=["Discovery"])
async def discover_batch_companies(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Discover locations for multiple companies in batch
    
    Maximum 50 companies per batch to prevent resource exhaustion
    """
    
    # Validate batch size
    if len(request.companies) == 0:
        raise HTTPException(status_code=400, detail="At least one company is required")
    
    if len(request.companies) > 50:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 50 companies per batch. Please split into smaller batches."
        )
    
    # Validate API keys
    if not request.api_keys.openai_api_key.strip():
        raise HTTPException(
            status_code=400, 
            detail="OpenAI API key is required for batch processing"
        )
    
    job_id = str(uuid.uuid4())
    
    jobs_storage[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message=f"Batch job queued - {len(request.companies)} companies",
        created_at=datetime.now().isoformat()
    ).dict()
    
    # Start background task
    background_tasks.add_task(
        process_batch_companies,
        job_id,
        request.companies,
        request.api_keys
    )
    
    logger.info(f"Created batch job {job_id} with {len(request.companies)} companies")
    
    return {
        "job_id": job_id, 
        "status": "queued", 
        "companies_count": len(request.companies),
        "message": f"Batch job queued with {len(request.companies)} companies"
    }

@app.post("/discover/upload", tags=["Discovery"])
async def upload_csv_companies(
    file: UploadFile = File(...),
    openai_api_key: str = Form(...),
    google_maps_api_key: Optional[str] = Form(None),
    tavily_api_key: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload CSV file and process companies in batch
    
    CSV format: company_name,company_url
    Maximum 100 companies per file
    """
    import csv
    import io
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Validate API keys
    if not openai_api_key.strip():
        raise HTTPException(status_code=400, detail="OpenAI API key is required")
    
    try:
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        companies = []
        
        for row_num, row in enumerate(csv_reader, 1):
            if row_num > 100:  # Limit to 100 companies
                break
                
            company_name = row.get('company_name', '').strip()
            company_url = row.get('company_url', '').strip()
            
            if company_name:
                companies.append(CompanyRequest(
                    company_name=company_name,
                    company_url=company_url if company_url else None,
                    api_keys=APIKeys(
                        openai_api_key=openai_api_key,
                        google_maps_api_key=google_maps_api_key,
                        tavily_api_key=tavily_api_key
                    )
                ))
        
        if not companies:
            raise HTTPException(status_code=400, detail="No valid companies found in CSV")
        
        # Create job
        job_id = str(uuid.uuid4())
        
        jobs_storage[job_id] = JobStatus(
            job_id=job_id,
            status="pending",
            progress=0,
            message=f"CSV uploaded - processing {len(companies)} companies",
            created_at=datetime.now().isoformat()
        ).dict()
        
        # Start background processing
        background_tasks.add_task(
            process_batch_companies,
            job_id,
            companies,
            APIKeys(
                openai_api_key=openai_api_key,
                google_maps_api_key=google_maps_api_key,
                tavily_api_key=tavily_api_key
            )
        )
        
        logger.info(f"CSV upload job {job_id} created with {len(companies)} companies")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "companies_count": len(companies),
            "message": f"CSV processed successfully - {len(companies)} companies queued"
        }
        
    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@app.get("/jobs/{job_id}/status", tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get the current status of a discovery job"""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs_storage[job_id]

@app.get("/jobs/{job_id}/results", tags=["Jobs"])
async def get_job_results(job_id: str):
    """Get the detailed results of a completed job"""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Job not completed yet. Current status: {job['status']}"
        )
    
    if not job.get("results"):
        raise HTTPException(
            status_code=404,
            detail="Job results not found"
        )
    
    return job["results"]

@app.get("/jobs", tags=["Jobs"])
async def list_jobs(limit: int = 10):
    """List recent jobs with their status"""
    
    if limit > 100:
        limit = 100
    
    jobs_list = sorted(
        jobs_storage.values(), 
        key=lambda x: x["created_at"], 
        reverse=True
    )[:limit]
    
    return {
        "jobs": jobs_list, 
        "total": len(jobs_storage),
        "showing": len(jobs_list)
    }

@app.get("/jobs/{job_id}/download/{file_type}", tags=["Jobs"])
async def download_job_results(job_id: str, file_type: str):
    """Download job results in specified format"""
    from fastapi.responses import StreamingResponse
    import io
    import json
    import csv
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not job.get("results"):
        raise HTTPException(status_code=404, detail="Job results not found")
    
    results = job["results"]
    
    if file_type.lower() == "json":
        # Generate JSON file
        json_str = json.dumps(results, indent=2)
        buffer = io.StringIO(json_str)
        
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=results_{job_id[:8]}.json"}
        )
    
    elif file_type.lower() == "csv":
        # Generate CSV file
        output = io.StringIO()
        
        if "locations" in results:
            locations = results["locations"]
            if locations:
                fieldnames = locations[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(locations)
        
        csv_content = output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=results_{job_id[:8]}.csv"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Supported formats: json, csv")

@app.delete("/jobs/{job_id}", tags=["Jobs"])
async def delete_job(job_id: str):
    """Delete a job and its results"""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs_storage[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}

# Background Processing Functions
async def process_single_company(
    job_id: str, 
    company_name: str, 
    company_url: Optional[str], 
    api_keys: APIKeys
):
    """Process a single company discovery using the real multi-agent workflow"""
    
    try:
        # Update job status
        jobs_storage[job_id]["status"] = "running"
        jobs_storage[job_id]["progress"] = 10
        jobs_storage[job_id]["message"] = f"Initializing discovery for {company_name}"
        
        logger.info(f"Job {job_id}: Processing {company_name} with real workflow")
        
        # Initialize the real workflow with user's API keys
        workflow_api_keys = {
            'openai_api_key': api_keys.openai_api_key,
            'google_maps_api_key': api_keys.google_maps_api_key,
            'tavily_api_key': api_keys.tavily_api_key
        }
        
        jobs_storage[job_id]["progress"] = 20
        jobs_storage[job_id]["message"] = "Starting multi-agent workflow..."
        
        # Create workflow instance
        workflow = EnhancedDiscoveryWorkflow(
            output_dir="temp/output",
            api_keys=workflow_api_keys
        )
        
        jobs_storage[job_id]["progress"] = 30
        jobs_storage[job_id]["message"] = "Running Google Maps agent..."
        
        # Run the real discovery workflow
        result = workflow.discover(
            company_name=company_name,
            company_url=company_url
        )
        
        jobs_storage[job_id]["progress"] = 90
        jobs_storage[job_id]["message"] = "Processing results..."
        
        # Transform the result to match our API format
        locations = []
        for loc in result.get('locations', []):
            location = {
                "Location_Name": loc.get('name', ''),
                "Street_Address": loc.get('address', ''),
                "City": loc.get('city', ''),
                "State_Province": loc.get('state', ''),
                "Country": loc.get('country', ''),
                "Postal_Code": loc.get('postal_code', ''),
                "Phone": loc.get('phone', ''),
                "Website": loc.get('website', ''),
                "Latitude": loc.get('lat', ''),
                "Longitude": loc.get('lng', ''),
                "Data_Source": loc.get('source', 'unknown'),
                "Source_Confidence": loc.get('confidence', 0.5),
                "Discovery_Date": datetime.now().strftime("%Y-%m-%d"),
                "Discovery_Time": datetime.now().strftime("%H:%M:%S")
            }
            locations.append(location)
        
        # Format the final result
        final_result = {
            "company_name": company_name,
            "company_url": company_url,
            "locations": locations,
            "summary": result.get('summary', {}),
            "messages": result.get('messages', []),
            "errors": result.get('errors', []),
            "export_files": result.get('export_files', [])
        }
        
        # Complete job
        jobs_storage[job_id]["status"] = "completed"
        jobs_storage[job_id]["progress"] = 100
        jobs_storage[job_id]["message"] = f"Discovery completed - found {len(locations)} locations using real agents"
        jobs_storage[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_storage[job_id]["results"] = final_result
        jobs_storage[job_id]["download_urls"] = [
            f"/jobs/{job_id}/download/json",
            f"/jobs/{job_id}/download/csv"
        ]
        
        logger.info(f"Job {job_id}: Completed successfully with {len(locations)} locations using real workflow")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Error - {e}")
        jobs_storage[job_id]["status"] = "failed"
        jobs_storage[job_id]["message"] = f"Error during processing: {str(e)}"
        jobs_storage[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_storage[job_id]["errors"] = [str(e)]

async def process_batch_companies(
    job_id: str, 
    companies: List[CompanyRequest], 
    api_keys: APIKeys
):
    """Process multiple companies using the real multi-agent workflow"""
    
    try:
        total_companies = len(companies)
        all_results = []
        
        jobs_storage[job_id]["status"] = "running"
        jobs_storage[job_id]["message"] = f"Processing batch of {total_companies} companies with real workflow"
        
        # Initialize the real workflow with user's API keys
        workflow_api_keys = {
            'openai_api_key': api_keys.openai_api_key,
            'google_maps_api_key': api_keys.google_maps_api_key,
            'tavily_api_key': api_keys.tavily_api_key
        }
        
        workflow = EnhancedDiscoveryWorkflow(
            output_dir="temp/output",
            api_keys=workflow_api_keys
        )
        
        for i, company in enumerate(companies):
            progress = int((i / total_companies) * 90)  # Reserve 10% for final processing
            jobs_storage[job_id]["progress"] = progress
            jobs_storage[job_id]["message"] = f"Running agents for {company.company_name} ({i+1}/{total_companies})"
            
            logger.info(f"Batch job {job_id}: Processing company {i+1}/{total_companies}: {company.company_name}")
            
            try:
                # Run the real workflow for each company
                result = workflow.discover(
                    company_name=company.company_name,
                    company_url=company.company_url
                )
                
                # Transform locations to match API format
                locations = []
                for loc in result.get('locations', []):
                    location = {
                        "Location_Name": loc.get('name', ''),
                        "Street_Address": loc.get('address', ''),
                        "City": loc.get('city', ''),
                        "State_Province": loc.get('state', ''),
                        "Country": loc.get('country', ''),
                        "Postal_Code": loc.get('postal_code', ''),
                        "Phone": loc.get('phone', ''),
                        "Website": loc.get('website', ''),
                        "Latitude": loc.get('lat', ''),
                        "Longitude": loc.get('lng', ''),
                        "Data_Source": loc.get('source', 'unknown'),
                        "Source_Confidence": loc.get('confidence', 0.5),
                        "Discovery_Date": datetime.now().strftime("%Y-%m-%d"),
                        "Discovery_Time": datetime.now().strftime("%H:%M:%S")
                    }
                    locations.append(location)
                
                company_result = {
                    "company_name": company.company_name,
                    "company_url": company.company_url,
                    "locations": locations,
                    "summary": result.get('summary', {}),
                    "messages": result.get('messages', []),
                    "errors": result.get('errors', [])
                }
                
            except Exception as company_error:
                logger.error(f"Error processing {company.company_name}: {company_error}")
                company_result = {
                    "company_name": company.company_name,
                    "company_url": company.company_url,
                    "locations": [],
                    "summary": {"error": str(company_error)},
                    "messages": [],
                    "errors": [str(company_error)]
                }
            
            all_results.append(company_result)
        
        # Final processing
        jobs_storage[job_id]["progress"] = 95
        jobs_storage[job_id]["message"] = "Finalizing batch results..."
        
        await asyncio.sleep(1)
        
        # Create batch summary
        total_locations = sum(len(r['locations']) for r in all_results)
        success_count = len([r for r in all_results if len(r['errors']) == 0])
        
        batch_result = {
            "batch_id": job_id,
            "total_companies": total_companies,
            "successful_companies": success_count,
            "total_locations": total_locations,
            "companies": all_results,
            "summary": {
                "completed_at": datetime.now().isoformat(),
                "success_rate": (success_count / total_companies) * 100 if total_companies > 0 else 0,
                "processing_time_seconds": 0  # Calculate if needed
            }
        }
        
        # Complete batch job
        jobs_storage[job_id]["status"] = "completed"
        jobs_storage[job_id]["progress"] = 100
        jobs_storage[job_id]["message"] = f"Batch completed using real agents - {success_count}/{total_companies} companies successful, {total_locations} total locations"
        jobs_storage[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_storage[job_id]["results"] = batch_result
        jobs_storage[job_id]["download_urls"] = [
            f"/jobs/{job_id}/download/json",
            f"/jobs/{job_id}/download/csv"
        ]
        
        logger.info(f"Batch job {job_id}: Completed successfully using real workflow")
        
    except Exception as e:
        logger.error(f"Batch job {job_id}: Error - {e}")
        jobs_storage[job_id]["status"] = "failed"
        jobs_storage[job_id]["message"] = f"Batch processing error: {str(e)}"
        jobs_storage[job_id]["completed_at"] = datetime.now().isoformat()

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )