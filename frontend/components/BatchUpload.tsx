'use client'

import { useState } from 'react'
import { discoverBatchCompanies, uploadCSV } from '@/lib/api'
import { CompanyRequest } from '@/lib/types'

interface BatchUploadProps {
  type: 'manual' | 'upload'
  onJobCreated: (jobId: string) => void
}

interface CompanyInput {
  company_name: string
  company_url: string
}

export default function BatchUpload({ type, onJobCreated }: BatchUploadProps) {
  const [companies, setCompanies] = useState<CompanyInput[]>([
    { company_name: '', company_url: '' }
  ])
  const [openaiKey, setOpenaiKey] = useState('')
  const [googleMapsKey, setGoogleMapsKey] = useState('')
  const [tavilyKey, setTavilyKey] = useState('')
  const [showApiKeys, setShowApiKeys] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAddCompany = () => {
    if (companies.length < 50) {
      setCompanies([...companies, { company_name: '', company_url: '' }])
    }
  }

  const handleRemoveCompany = (index: number) => {
    if (companies.length > 1) {
      setCompanies(companies.filter((_, i) => i !== index))
    }
  }

  const handleCompanyChange = (index: number, field: keyof CompanyInput, value: string) => {
    const updated = [...companies]
    updated[index] = { ...updated[index], [field]: value }
    setCompanies(updated)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file')
        return
      }
      if (selectedFile.size > 5 * 1024 * 1024) { // 5MB limit
        setError('File size must be less than 5MB')
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const validateApiKeys = () => {
    if (!openaiKey.trim()) {
      setError('OpenAI API key is required')
      return false
    }
    return true
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateApiKeys()) return
    
    const validCompanies = companies.filter(c => c.company_name.trim())
    
    if (validCompanies.length === 0) {
      setError('Please add at least one company')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Convert to the format expected by the API
      const companiesWithKeys: CompanyRequest[] = validCompanies.map(company => ({
        company_name: company.company_name.trim(),
        company_url: company.company_url.trim() || undefined,
        api_keys: {
          openai_api_key: openaiKey.trim(),
          google_maps_api_key: googleMapsKey.trim() || undefined,
          tavily_api_key: tavilyKey.trim() || undefined
        }
      }))

      const response = await discoverBatchCompanies(companiesWithKeys)
      onJobCreated(response.job_id)
      
      // Reset form (but keep API keys)
      setCompanies([{ company_name: '', company_url: '' }])
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start batch processing')
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateApiKeys()) return
    
    if (!file) {
      setError('Please select a CSV file')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await uploadCSV(file, {
        openai_api_key: openaiKey.trim(),
        google_maps_api_key: googleMapsKey.trim() || undefined,
        tavily_api_key: tavilyKey.trim() || undefined
      })
      onJobCreated(response.job_id)
      
      // Reset form
      setFile(null)
      const fileInput = document.getElementById('csv-file') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload CSV')
    } finally {
      setIsLoading(false)
    }
  }

  // API Keys Section Component
  const ApiKeysSection = () => (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <svg className="h-5 w-5 text-yellow-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          <h3 className="text-sm font-medium text-yellow-800">API Keys Required</h3>
        </div>
        <button
          type="button"
          onClick={() => setShowApiKeys(!showApiKeys)}
          className="text-sm text-yellow-700 hover:text-yellow-600 underline"
        >
          {showApiKeys ? 'Hide' : 'Show'} API Keys
        </button>
      </div>
      <p className="text-sm text-yellow-700 mb-3">
        You need to provide your own API keys for batch processing. Keys are not stored.
      </p>

      {showApiKeys && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg border">
          {/* OpenAI API Key */}
          <div>
            <label htmlFor="batch-openai-key" className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key *
            </label>
            <input
              id="batch-openai-key"
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-proj-..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Google Maps API Key */}
          <div>
            <label htmlFor="batch-maps-key" className="block text-sm font-medium text-gray-700 mb-2">
              Google Maps API Key (Optional)
            </label>
            <input
              id="batch-maps-key"
              type="password"
              value={googleMapsKey}
              onChange={(e) => setGoogleMapsKey(e.target.value)}
              placeholder="AIza..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>

          {/* Tavily API Key */}
          <div>
            <label htmlFor="batch-tavily-key" className="block text-sm font-medium text-gray-700 mb-2">
              Tavily API Key (Optional)
            </label>
            <input
              id="batch-tavily-key"
              type="password"
              value={tavilyKey}
              onChange={(e) => setTavilyKey(e.target.value)}
              placeholder="tvly-..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>
        </div>
      )}
    </div>
  )

  if (type === 'upload') {
    return (
      <div>
        <ApiKeysSection />
        
        <form onSubmit={handleFileSubmit} className="space-y-6">
          {/* CSV Upload */}
          <div>
            <label htmlFor="csv-file" className="block text-sm font-medium text-gray-700 mb-2">
              Upload CSV File
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
              <div className="space-y-1 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="flex text-sm text-gray-600">
                  <label
                    htmlFor="csv-file"
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                  >
                    <span>Upload a file</span>
                    <input
                      id="csv-file"
                      name="csv-file"
                      type="file"
                      accept=".csv"
                      className="sr-only"
                      onChange={handleFileUpload}
                      disabled={isLoading}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">CSV up to 5MB</p>
              </div>
            </div>
            
            {file && (
              <div className="mt-2 text-sm text-green-600">
                ✓ Selected: {file.name} ({Math.round(file.size / 1024)}KB)
              </div>
            )}
          </div>

          {/* CSV Format Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">📋 CSV Format Required:</h4>
            <div className="text-sm text-blue-700">
              <p className="mb-2">Your CSV file should have these columns:</p>
              <div className="bg-white rounded border p-2 font-mono text-xs">
                company_name,company_url<br/>
                "Microsoft","https://microsoft.com"<br/>
                "Apple Inc","https://apple.com"<br/>
                "Tesla","https://tesla.com"
              </div>
              <p className="mt-2 text-xs">
                • <strong>company_name</strong>: Required<br/>
                • <strong>company_url</strong>: Optional but recommended
              </p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !file || !openaiKey.trim()}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing CSV...
              </>
            ) : (
              '📁 Upload & Process CSV'
            )}
          </button>
        </form>
      </div>
    )
  }

  // Manual batch entry
  return (
    <div>
      <ApiKeysSection />
      
      <form onSubmit={handleManualSubmit} className="space-y-6">
        {/* Companies List */}
        <div className="space-y-4">
          {companies.map((company, index) => (
            <div key={index} className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name {index === 0 && '*'}
                </label>
                <input
                  type="text"
                  value={company.company_name}
                  onChange={(e) => handleCompanyChange(index, 'company_name', e.target.value)}
                  placeholder="e.g., Microsoft Corporation"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Website URL
                </label>
                <input
                  type="url"
                  value={company.company_url}
                  onChange={(e) => handleCompanyChange(index, 'company_url', e.target.value)}
                  placeholder="https://company.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
              </div>
              <button
                type="button"
                onClick={() => handleRemoveCompany(index)}
                disabled={companies.length === 1 || isLoading}
                className="px-3 py-2 border border-gray-300 rounded-md text-gray-400 hover:text-red-500 hover:border-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>

        {/* Add Company Button */}
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={handleAddCompany}
            disabled={companies.length >= 50 || isLoading}
            className="inline-flex items-center px-4 py-2 border border-dashed border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ➕ Add Company
          </button>
          <span className="text-sm text-gray-500">
            {companies.length}/50 companies
          </span>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || companies.filter(c => c.company_name.trim()).length === 0 || !openaiKey.trim()}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Starting Batch Processing...
            </>
          ) : (
            `📊 Process ${companies.filter(c => c.company_name.trim()).length} Companies`
          )}
        </button>
      </form>
    </div>
  )
}