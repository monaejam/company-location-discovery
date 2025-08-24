'use client'

import { useState } from 'react'
import { discoverSingleCompany } from '@/lib/api'

interface CompanyFormProps {
  onJobCreated: (jobId: string) => void
}

export default function CompanyForm({ onJobCreated }: CompanyFormProps) {
  const [companyName, setCompanyName] = useState('')
  const [companyUrl, setCompanyUrl] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [googleMapsKey, setGoogleMapsKey] = useState('')
  const [tavilyKey, setTavilyKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showApiKeys, setShowApiKeys] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!companyName.trim()) {
      setError('Company name is required')
      return
    }

    if (!openaiKey.trim()) {
      setError('OpenAI API key is required')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await discoverSingleCompany({
        company_name: companyName.trim(),
        company_url: companyUrl.trim() || undefined,
        api_keys: {
          openai_api_key: openaiKey.trim(),
          google_maps_api_key: googleMapsKey.trim() || undefined,
          tavily_api_key: tavilyKey.trim() || undefined
        }
      })
      
      onJobCreated(response.job_id)
      
      // Reset form (but keep API keys)
      setCompanyName('')
      setCompanyUrl('')
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start discovery')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* API Keys Section */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
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
        <p className="mt-1 text-sm text-yellow-700">
          You need to provide your own API keys. Your keys are not stored and only used for this request.
        </p>
      </div>

      {/* API Keys Fields */}
      {showApiKeys && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg border">
          <h4 className="font-medium text-gray-900">API Keys</h4>
          
          {/* OpenAI API Key */}
          <div>
            <label htmlFor="openai-key" className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key *
            </label>
            <input
              id="openai-key"
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-proj-..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Get your key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" className="text-blue-600 underline">platform.openai.com</a>
            </p>
          </div>

          {/* Google Maps API Key */}
          <div>
            <label htmlFor="maps-key" className="block text-sm font-medium text-gray-700 mb-2">
              Google Maps API Key (Optional)
            </label>
            <input
              id="maps-key"
              type="password"
              value={googleMapsKey}
              onChange={(e) => setGoogleMapsKey(e.target.value)}
              placeholder="AIza..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Improves location accuracy. Get your key at <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener" className="text-blue-600 underline">Google Cloud Console</a>
            </p>
          </div>

          {/* Tavily API Key */}
          <div>
            <label htmlFor="tavily-key" className="block text-sm font-medium text-gray-700 mb-2">
              Tavily API Key (Optional)
            </label>
            <input
              id="tavily-key"
              type="password"
              value={tavilyKey}
              onChange={(e) => setTavilyKey(e.target.value)}
              placeholder="tvly-..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Improves web search. Get your key at <a href="https://tavily.com" target="_blank" rel="noopener" className="text-blue-600 underline">tavily.com</a>
            </p>
          </div>
        </div>
      )}

      {/* Company Name */}
      <div>
        <label htmlFor="company-name" className="block text-sm font-medium text-gray-700 mb-2">
          Company Name *
        </label>
        <input
          id="company-name"
          type="text"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="e.g., ADP GROUP, Microsoft, Tesla"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
      </div>

      {/* Company URL */}
      <div>
        <label htmlFor="company-url" className="block text-sm font-medium text-gray-700 mb-2">
          Company Website (Optional)
        </label>
        <input
          id="company-url"
          type="url"
          value={companyUrl}
          onChange={(e) => setCompanyUrl(e.target.value)}
          placeholder="https://company.com"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
        <p className="mt-1 text-sm text-gray-500">
          Providing a website URL improves discovery accuracy
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div>
        <button
          type="submit"
          disabled={isLoading || !companyName.trim() || !openaiKey.trim()}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Starting Discovery...
            </>
          ) : (
            <>
              🔍 Start Discovery
            </>
          )}
        </button>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">How it works</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>🗺️ Uses your Google Maps API to find office locations</li>
                <li>🔍 Uses your OpenAI API to analyze and search for location data</li>
                <li>🌐 Scrapes company website for address information</li>
                <li>📊 Exports results in Excel, CSV, and JSON formats</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </form>
  )
}