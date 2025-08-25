export interface APIKeys {
  openai_api_key: string
  google_maps_api_key?: string
  tavily_api_key?: string
}

export interface CompanyRequest {
  company_name: string
  company_url?: string
  api_keys: APIKeys
}

export interface Location {
  location_id?: string
  name: string
  address?: string
  city: string
  state?: string
  country?: string
  postal_code?: string
  phone?: string
  website?: string
  lat?: number | string
  lng?: number | string
  confidence?: number
  source: string
  source_url?: string
  search_query?: string
  search_pattern?: string
  facility_type?: string
  // API format compatibility
  Location_ID?: string
  Company_Name?: string
  Location_Name?: string
  Street_Address?: string
  State_Province?: string
  Postal_Code?: string
  Latitude?: number | string
  Longitude?: number | string
  Data_Source?: string
  Source_Confidence?: number
  Source_URL?: string
  Discovery_Date?: string
  Discovery_Time?: string
  Company_Website?: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  created_at: string
  completed_at?: string
  results?: {
    company: string
    url: string
    locations: Location[]
    summary: {
      sources_used: {
        google_maps: number
        tavily: number
        website: number
        directory: number
        sec_filings: number
        multi_search: number
        industry_specific: number
      }
      total_locations: number
      url_processed: boolean
      enhancement_multiplier?: number
      timestamp?: string
    }
    enhancement_summary?: {
      total_agents_used: number
      enhancement_features: string[]
      pages_crawled: string
      expected_improvement: string
    }
    messages: string[]
    errors: string[]
    export_files?: string[]
  }
  download_urls?: string[]
}

export interface BatchResult {
  batch_id: string
  total_companies: number
  total_locations: number
  companies: JobStatus['results'][]
  summary: {
    completed_at: string
    success_rate: number
  }
}

export interface APIResponse<T = any> {
  job_id: string
  status: string
  companies_count?: number
  message?: string
  data?: T
}