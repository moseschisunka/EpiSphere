'use client'

import { useState, useEffect, useRef } from 'react'
import { casesApi, countriesApi, diseasesApi } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Upload, File as FileIcon, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

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
  const [dragActive, setDragActive] = useState(false)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const validateFile = (selectedFile: File) => {
    const validTypes = ['.csv', '.xlsx', '.xls']
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase()
    
    if (!validTypes.includes(ext)) {
      toast.error('Invalid file type. Please upload a CSV or Excel file.')
      return false
    }
    
    if (selectedFile.size > 10 * 1024 * 1024) {
      toast.error('File size exceeds 10MB limit.')
      return false
    }
    
    return true
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      if (validateFile(e.target.files[0])) {
        setFile(e.target.files[0])
      } else {
        if (fileInputRef.current) fileInputRef.current.value = ''
      }
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      if (validateFile(e.dataTransfer.files[0])) {
        setFile(e.dataTransfer.files[0])
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file || !countryId || !diseaseId) {
      toast.error('Please select a file, country, and disease')
      return
    }

    setUploading(true)
    setResult(null)

    try {
      const response = await casesApi.upload(file, Number(countryId), Number(diseaseId), commit)
      setResult(response)
      
      if (response.success && response.committed) {
        toast.success(`Data uploaded successfully! ${response.inserted || 0} cases inserted.`)
        setTimeout(() => {
          router.push('/dashboard/global')
        }, 2000)
      } else {
        toast.info('Validation complete. Review status below.')
      }
    } catch (error: any) {
      const msg = error.response?.data?.detail || 'Upload failed'
      toast.error(msg)
      setResult({
        success: false,
        message: msg,
      })
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">Upload Case Data</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Import epidemiological data into the global registry</p>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-6 rounded-xl shadow-sm mb-6 transition-colors">
        <h2 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center gap-2">
          <FileIcon className="w-5 h-5 text-blue-500" />
          File Format Requirements
        </h2>
        <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <li>Supported formats: <span className="font-medium text-gray-900 dark:text-white">CSV, XLSX, XLS</span> (Max 10MB)</li>
          <li>Required columns: <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700 text-pink-600 dark:text-pink-400">date</code>, <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700 text-pink-600 dark:text-pink-400">daily_cases</code></li>
          <li>Optional columns: <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">cumulative_cases</code>, <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">daily_deaths</code>, <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">cumulative_deaths</code></li>
          <li>Governance columns: <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">subnational_region</code>, <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">reporting_level</code>, <code className="bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-gray-200 dark:border-slate-700">confirmation_status</code></li>
          <li>Date format: YYYY-MM-DD or any standard date format</li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-6 rounded-xl shadow-sm transition-colors">
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Country Location
              </label>
              <select
                value={countryId}
                onChange={(e) => setCountryId(e.target.value ? parseInt(e.target.value) : '')}
                className="border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-white rounded-lg px-4 py-2.5 w-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm"
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
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Disease
              </label>
              <select
                value={diseaseId}
                onChange={(e) => setDiseaseId(e.target.value ? parseInt(e.target.value) : '')}
                className="border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-gray-900 dark:text-white rounded-lg px-4 py-2.5 w-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm"
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
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Data File
            </label>
            
            {!file ? (
              <div 
                className={clsx(
                  "border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer",
                  dragActive 
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10" 
                    : "border-gray-300 dark:border-slate-700 hover:border-gray-400 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/50"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <Upload className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
                <p className="text-gray-700 dark:text-gray-300 font-medium mb-1">
                  Drag & drop files here
                </p>
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">
                  or click to browse
                </p>
                <button type="button" className="px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 shadow-sm">
                  Browse Files
                </button>
              </div>
            ) : (
              <div className="border border-gray-200 dark:border-slate-700 rounded-xl p-4 flex items-center justify-between bg-gray-50 dark:bg-slate-800/50">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="bg-blue-100 dark:bg-blue-900/50 p-2 rounded-lg flex-shrink-0">
                    <FileIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="truncate">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{file.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>

          <label className="flex items-center gap-3 rounded-lg border border-gray-200 dark:border-slate-700 p-4 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-slate-800/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors">
            <input
              type="checkbox"
              checked={commit}
              onChange={(e) => setCommit(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700"
            />
            <span className="font-medium">Commit valid records after validation</span>
          </label>

          <button
            type="submit"
            disabled={uploading || !file || !countryId || !diseaseId}
            className="w-full flex justify-center items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3.5 rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : commit ? (
              'Validate and Commit'
            ) : (
              'Validate Only'
            )}
          </button>
        </div>
      </form>

      {result && (
        <div className={clsx(
          "mt-6 p-6 rounded-xl border animate-in fade-in slide-in-from-bottom-4 duration-300",
          result.success 
            ? "bg-green-50/50 dark:bg-green-900/10 border-green-200 dark:border-green-900/50" 
            : "bg-red-50/50 dark:bg-red-900/10 border-red-200 dark:border-red-900/50"
        )}>
          <div className="flex items-start gap-3">
            {result.success ? (
              <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-500 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className={clsx(
                "font-bold text-lg",
                result.success ? "text-green-800 dark:text-green-400" : "text-red-800 dark:text-red-400"
              )}>
                {result.success ? 'Validation passed' : 'Validation failed'}
              </p>
              <p className="text-gray-700 dark:text-gray-300 mt-1">{result.message}</p>
              
              {result.batch_id && (
                <div className="mt-3 inline-block px-3 py-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-md text-sm text-gray-600 dark:text-gray-400">
                  Batch #{result.batch_id} • Quality score: <span className="font-semibold text-gray-900 dark:text-white">{result.quality_score ?? 'n/a'}</span> • <span className="font-semibold text-gray-900 dark:text-white">{result.rows_valid ?? 0}/{result.rows_total ?? 0}</span> valid rows
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 space-y-6">
            {result.quality_checks && result.quality_checks.length > 0 && (
              <div>
                <p className="font-bold text-sm text-gray-900 dark:text-white uppercase tracking-wider mb-3">Quality Checks</p>
                <div className="space-y-2">
                  {result.quality_checks.map((check: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between text-sm bg-white dark:bg-slate-800 p-3 rounded-lg border border-gray-100 dark:border-slate-700">
                      <span className="font-medium text-gray-700 dark:text-gray-300">{check.check_name}</span>
                      <span className={clsx(
                        "px-2 py-0.5 rounded text-xs font-bold",
                        check.passed ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                      )}>
                        {check.passed ? 'PASSED' : 'NEEDS REVIEW'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {result.issues && result.issues.length > 0 && (
              <div>
                <p className="font-bold text-sm text-gray-900 dark:text-white uppercase tracking-wider mb-3">Row Issues (First 8)</p>
                <ul className="space-y-2">
                  {result.issues.slice(0, 8).map((issue: any, idx: number) => (
                    <li key={idx} className="text-sm text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/10 p-3 rounded-lg border border-amber-200 dark:border-amber-900/50 flex gap-2">
                      <span className="font-bold">Row {issue.row_number}:</span>
                      <span>{issue.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {result.errors && result.errors.length > 0 && (
              <div>
                <p className="font-bold text-sm text-gray-900 dark:text-white uppercase tracking-wider mb-3">Errors</p>
                <ul className="space-y-2">
                  {result.errors.slice(0, 5).map((error: string, idx: number) => (
                    <li key={idx} className="text-sm text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/10 p-3 rounded-lg border border-red-200 dark:border-red-900/50">
                      {error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
