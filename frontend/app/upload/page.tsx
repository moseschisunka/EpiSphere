'use client'

import { useState, useEffect } from 'react'
import { casesApi, countriesApi, diseasesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function UploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [countryId, setCountryId] = useState<number | ''>('')
  const [diseaseId, setDiseaseId] = useState<number | ''>('')
  const [countries, setCountries] = useState<any[]>([])
  const [diseases, setDiseases] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)
  const [commit, setCommit] = useState(true)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    loadCountries()
    loadDiseases()
  }, [])

  const loadCountries = async () => {
    try {
      const data = await countriesApi.list()
      setCountries(data)
    } catch (error) {
      console.error('Error loading countries:', error)
    }
  }

  const loadDiseases = async () => {
    try {
      const data = await diseasesApi.list()
      setDiseases(data)
    } catch (error) {
      console.error('Error loading diseases:', error)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file || !countryId || !diseaseId) {
      alert('Please fill in all fields')
      return
    }

    setUploading(true)
    setResult(null)

    try {
      const response = await casesApi.upload(file, Number(countryId), Number(diseaseId), commit)
      setResult(response)
      
      if (response.success && response.committed) {
        setTimeout(() => {
          router.push('/dashboard/global')
        }, 2000)
      }
    } catch (error: any) {
      setResult({
        success: false,
        message: error.response?.data?.detail || 'Upload failed',
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">Upload Case Data</h1>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <h2 className="text-lg font-semibold mb-4">File Format Requirements</h2>
        <ul className="list-disc list-inside text-gray-700 space-y-2">
          <li>Supported formats: CSV, XLSX, XLS</li>
          <li>Required columns: <code className="bg-gray-100 px-2 py-1 rounded">date</code>, <code className="bg-gray-100 px-2 py-1 rounded">daily_cases</code></li>
          <li>Optional columns: <code className="bg-gray-100 px-2 py-1 rounded">cumulative_cases</code>, <code className="bg-gray-100 px-2 py-1 rounded">daily_deaths</code>, <code className="bg-gray-100 px-2 py-1 rounded">cumulative_deaths</code></li>
          <li>Governance columns: <code className="bg-gray-100 px-2 py-1 rounded">subnational_region</code>, <code className="bg-gray-100 px-2 py-1 rounded">reporting_level</code>, <code className="bg-gray-100 px-2 py-1 rounded">confirmation_status</code>, <code className="bg-gray-100 px-2 py-1 rounded">case_definition</code></li>
          <li>Date format: YYYY-MM-DD or any standard date format</li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Country
            </label>
            <select
              value={countryId}
              onChange={(e) => setCountryId(e.target.value ? parseInt(e.target.value) : '')}
              className="border border-gray-300 rounded-lg px-4 py-2 w-full"
              required
            >
              <option value="">Select a country</option>
              {countries.map((country) => (
                <option key={country.id} value={country.id}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Disease
            </label>
            <select
              value={diseaseId}
              onChange={(e) => setDiseaseId(e.target.value ? parseInt(e.target.value) : '')}
              className="border border-gray-300 rounded-lg px-4 py-2 w-full"
              required
            >
              <option value="">Select a disease</option>
              {diseases.map((disease) => (
                <option key={disease.id} value={disease.id}>
                  {disease.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data File
            </label>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              className="border border-gray-300 rounded-lg px-4 py-2 w-full"
              required
            />
            {file && (
              <p className="text-sm text-gray-600 mt-2">Selected: {file.name}</p>
            )}
          </div>

          <label className="flex items-center gap-3 rounded-lg border border-gray-200 p-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={commit}
              onChange={(e) => setCommit(e.target.checked)}
              className="h-4 w-4"
            />
            Commit valid records after validation
          </label>

          <button
            type="submit"
            disabled={uploading}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {uploading ? 'Processing...' : commit ? 'Validate and Commit' : 'Validate Only'}
          </button>
        </div>
      </form>

      {result && (
        <div className={`mt-6 p-4 rounded-lg ${
          result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          <p className="font-semibold">{result.success ? 'Validation passed' : 'Validation failed'}</p>
          <p>{result.message}</p>
          {result.batch_id && (
            <p className="mt-2 text-sm">Batch #{result.batch_id} - Quality score {result.quality_score ?? 'n/a'} - {result.rows_valid ?? 0}/{result.rows_total ?? 0} valid rows</p>
          )}
          {result.quality_checks && result.quality_checks.length > 0 && (
            <div className="mt-3">
              <p className="font-semibold">Quality checks:</p>
              <ul className="list-disc list-inside">
                {result.quality_checks.map((check: any, idx: number) => (
                  <li key={idx}>{check.check_name}: {check.passed ? 'passed' : 'needs review'}{check.message ? ` - ${check.message}` : ''}</li>
                ))}
              </ul>
            </div>
          )}
          {result.issues && result.issues.length > 0 && (
            <div className="mt-3">
              <p className="font-semibold">Row issues:</p>
              <ul className="list-disc list-inside">
                {result.issues.slice(0, 8).map((issue: any, idx: number) => (
                  <li key={idx}>Row {issue.row_number}: {issue.message}</li>
                ))}
              </ul>
            </div>
          )}
          {result.errors && result.errors.length > 0 && (
            <div className="mt-2">
              <p className="font-semibold">Errors:</p>
              <ul className="list-disc list-inside">
                {result.errors.slice(0, 5).map((error: string, idx: number) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
