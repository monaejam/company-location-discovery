import { CompanyRequest, JobStatus } from './types'

// Get API URL from environment or force Railway backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://company-location-discovery-production.up.railway.app'

// Force the correct URL if still seeing localhost issues
const FORCED_API_URL = 'https://company-location-discovery-production.up.railway.app'
const FINAL_API_URL = API_BASE_URL.includes('localhost') ? FORCED_API_URL : API_BASE_URL

// Debug logging
console.log('🔍 API Debug Info:')
console.log('NEXT_PUBLIC_API_URL env var:', process.env.NEXT_PUBLIC_API_URL)
console.log('Final API_BASE_URL:', API_BASE_URL)


class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${FINAL_API_URL}${endpoint}`
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      mode: 'cors',
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('CORS')) {
      throw new APIError('CORS error: Unable to connect to API. Please check if the API is accessible.', 0)
    }
    throw error
  }
}

export async function discoverSingleCompany(request: CompanyRequest) {
  return fetchAPI('/discover/single', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function discoverBatchCompanies(companies: CompanyRequest[]) {
  return fetchAPI('/discover/batch', {
    method: 'POST',
    body: JSON.stringify(companies),
  })
}

export async function uploadCSV(file: File, apiKeys: {
  openai_api_key: string
  google_maps_api_key?: string
  tavily_api_key?: string
}) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('openai_api_key', apiKeys.openai_api_key)
  if (apiKeys.google_maps_api_key) {
    formData.append('google_maps_api_key', apiKeys.google_maps_api_key)
  }
  if (apiKeys.tavily_api_key) {
    formData.append('tavily_api_key', apiKeys.tavily_api_key)
  }

  const response = await fetch(`${FINAL_API_URL}/discover/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new APIError(
      errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status
    )
  }

  return response.json()
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return fetchAPI(`/jobs/${jobId}/status`)
}

export async function getJobResults(jobId: string) {
  return fetchAPI(`/jobs/${jobId}/results`)
}

export async function downloadResults(jobId: string, fileType: string) {
  const response = await fetch(`${FINAL_API_URL}/jobs/${jobId}/download/${fileType}`)
  
  if (!response.ok) {
    throw new APIError(`Failed to download ${fileType} file`, response.status)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  
  // Get filename from response headers or generate one
  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = `results_${jobId.slice(0, 8)}.${fileType}`
  
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
    if (filenameMatch) {
      filename = filenameMatch[1]
    }
  }
  
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export async function listJobs(limit: number = 10) {
  return fetchAPI(`/jobs?limit=${limit}`)
}