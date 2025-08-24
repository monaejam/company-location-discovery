'use client'

import { useState, useEffect } from 'react'
import { getJobStatus, downloadResults } from '@/lib/api'
import { JobStatus as JobStatusType } from '@/lib/types'

interface JobStatusProps {
  jobId: string
  onComplete: () => void
}

export default function JobStatus({ jobId, onComplete }: JobStatusProps) {
  const [status, setStatus] = useState<JobStatusType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let interval: NodeJS.Timeout

    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId)
        setStatus(jobStatus)

        if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
          clearInterval(interval)
          setTimeout(onComplete, 5000) // Auto-hide after 5 seconds
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status')
        clearInterval(interval)
      }
    }

    // Initial fetch
    pollStatus()

    // Poll every 2 seconds if job is running
    interval = setInterval(() => {
      if (status?.status === 'pending' || status?.status === 'running') {
        pollStatus()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId, onComplete, status?.status])

  const handleDownload = async (fileType: string) => {
    try {
      await downloadResults(jobId, fileType)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="animate-pulse flex space-x-4">
          <div className="rounded-full bg-gray-300 h-10 w-10"></div>
          <div className="flex-1 space-y-2 py-1">
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'pending':
        return '⏳'
      case 'running':
        return '🔄'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '❓'
    }
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200'
      case 'running':
        return 'bg-blue-50 border-blue-200'
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const getProgressBarColor = () => {
    switch (status.status) {
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'running':
        return 'bg-blue-500'
      default:
        return 'bg-gray-300'
    }
  }

  return (
    <div className={`border rounded-lg p-6 ${getStatusColor()}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getStatusIcon()}</span>
          <div>
            <h3 className="text-lg font-semibold capitalize">
              {status.status === 'running' ? 'Processing' : status.status}
            </h3>
            <p className="text-sm text-gray-600">
              Job ID: {jobId.slice(0, 8)}...
            </p>
          </div>
        </div>
        
        {status.status === 'completed' && (
          <div className="text-right">
            <p className="text-sm font-medium text-green-800">
              {status.results?.locations?.length || 0} locations found
            </p>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{status.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor()}`}
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>
      </div>

      {/* Status Message */}
      <p className="text-sm text-gray-700 mb-4">{status.message}</p>

      {/* Results Summary */}
      {status.status === 'completed' && status.results && (
        <div className="mb-4 p-4 bg-white rounded-lg border">
          <h4 className="font-semibold mb-2">📊 Results Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Locations:</span>
              <div className="font-semibold">{status.results.locations?.length || 0}</div>
            </div>
            <div>
              <span className="text-gray-600">Google Maps:</span>
              <div className="font-semibold">{status.results.summary?.sources_used?.google_maps || 0}</div>
            </div>
            <div>
              <span className="text-gray-600">Web Search:</span>
              <div className="font-semibold">{status.results.summary?.sources_used?.tavily || 0}</div>
            </div>
            <div>
              <span className="text-gray-600">Website:</span>
              <div className="font-semibold">{status.results.summary?.sources_used?.website || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Download Options */}
      {status.status === 'completed' && (
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleDownload('csv')}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            📋 Download CSV
          </button>
          <button
            onClick={() => handleDownload('json')}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
          >
            💻 Download JSON
          </button>
        </div>
      )}

      {/* Timestamps */}
      <div className="mt-4 pt-4 border-t text-xs text-gray-500">
        <div className="flex justify-between">
          <span>Started: {new Date(status.created_at).toLocaleString()}</span>
          {status.completed_at && (
            <span>Completed: {new Date(status.completed_at).toLocaleString()}</span>
          )}
        </div>
      </div>
    </div>
  )
}