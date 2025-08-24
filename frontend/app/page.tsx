'use client'

import { useState } from 'react'
import CompanyForm from '@/components/CompanyForm'
import BatchUpload from '@/components/BatchUpload'
import JobStatus from '@/components/JobStatus'

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<'single' | 'batch' | 'upload'>('single')
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  const handleJobCreated = (jobId: string) => {
    setCurrentJobId(jobId)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              🌍 Company Location Discovery
            </h1>
            <p className="mt-2 text-gray-600">
              AI-powered multi-agent system to discover company locations worldwide
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Current Job Status */}
        {currentJobId && (
          <div className="mb-8">
            <JobStatus 
              jobId={currentJobId} 
              onComplete={() => setCurrentJobId(null)}
            />
          </div>
        )}

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-sm border">
          
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('single')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'single'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🏢 Single Company
              </button>
              <button
                onClick={() => setActiveTab('batch')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'batch'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📊 Batch Processing
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'upload'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📁 CSV Upload
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'single' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Discover Single Company</h2>
                <p className="text-gray-600 mb-6">
                  Enter a company name and optional website to discover all their global locations
                </p>
                <CompanyForm onJobCreated={handleJobCreated} />
              </div>
            )}

            {activeTab === 'batch' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Batch Processing</h2>
                <p className="text-gray-600 mb-6">
                  Process multiple companies at once (up to 50 companies)
                </p>
                <BatchUpload type="manual" onJobCreated={handleJobCreated} />
              </div>
            )}

            {activeTab === 'upload' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">CSV Upload</h2>
                <p className="text-gray-600 mb-6">
                  Upload a CSV file with company names and URLs (up to 100 companies)
                </p>
                <BatchUpload type="upload" onJobCreated={handleJobCreated} />
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-4">
              🤖
            </div>
            <h3 className="font-semibold mb-2">Multi-Agent AI</h3>
            <p className="text-gray-600 text-sm">
              Uses Google Maps, web scraping, and search APIs for comprehensive coverage
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-green-100 rounded-full p-3 w-12 h-12 mx-auto mb-4">
              📊
            </div>
            <h3 className="font-semibold mb-2">Rich Export Options</h3>
            <p className="text-gray-600 text-sm">
              Download results as Excel, CSV, or JSON with source attribution
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-purple-100 rounded-full p-3 w-12 h-12 mx-auto mb-4">
              🌍
            </div>
            <h3 className="font-semibold mb-2">Global Coverage</h3>
            <p className="text-gray-600 text-sm">
              Discovers locations worldwide with detailed address information
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}