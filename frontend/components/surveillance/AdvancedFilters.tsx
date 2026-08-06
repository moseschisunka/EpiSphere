'use client'

import { useEffect, useState } from 'react'
import { locationsApi, diseasesApi } from '@/lib/api'
import { Filter, RotateCcw, MapPin, Calendar, Activity, ChevronDown, Check } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

export interface FilterState {
  regionId?: number
  countryId?: number
  province?: string
  district?: string
  facilityId?: number
  diseaseId?: number
  dateRange: '7d' | '30d' | '90d' | '1y' | 'all'
  startDate?: string
  endDate?: string
  ageGroup?: string
  gender?: string
}

interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterState) => void
  className?: string
}

export default function AdvancedFilters({ onFilterChange, className = '' }: AdvancedFiltersProps) {
  const [hierarchy, setHierarchy] = useState<any[]>([])
  const [diseases, setDiseases] = useState<any[]>([])
  const [provinces, setProvinces] = useState<string[]>([])
  const [districts, setDistricts] = useState<string[]>([])
  const [facilities, setFacilities] = useState<any[]>([])
  const [isExpanded, setIsExpanded] = useState(true)

  const [filters, setFilters] = useState<FilterState>({
    dateRange: '30d',
  })

  useEffect(() => {
    loadInitialOptions()
  }, [])

  const loadInitialOptions = async () => {
    try {
      const [hierarchyRes, diseasesRes] = await Promise.all([
        locationsApi.getHierarchy(),
        diseasesApi.list(),
      ])
      setHierarchy(hierarchyRes || [])
      setDiseases(diseasesRes || [])
    } catch (err) {
      console.error('Failed to load filter metadata', err)
    }
  }

  // Cascading Location Logic
  const selectedRegion = hierarchy.find((r) => r.region_id === filters.regionId)
  const availableCountries = selectedRegion ? selectedRegion.countries : hierarchy.flatMap((r) => r.countries || [])

  const handleRegionChange = (regionId?: number) => {
    const updated = { ...filters, regionId, countryId: undefined, province: undefined, district: undefined, facilityId: undefined }
    setFilters(updated)
    setProvinces([])
    setDistricts([])
    setFacilities([])
    onFilterChange(updated)
  }

  const handleCountryChange = async (countryId?: number) => {
    const updated = { ...filters, countryId, province: undefined, district: undefined, facilityId: undefined }
    setFilters(updated)
    setDistricts([])
    setFacilities([])

    if (countryId) {
      const countryObj = availableCountries.find((c: any) => c.id === countryId)
      if (countryObj) {
        setProvinces(countryObj.provinces || [])
        setFacilities(countryObj.facilities || [])
      }
    } else {
      setProvinces([])
      setFacilities([])
    }

    onFilterChange(updated)
  }

  const handleProvinceChange = async (province?: string) => {
    const updated = { ...filters, province, district: undefined, facilityId: undefined }
    setFilters(updated)

    if (filters.countryId && province) {
      try {
        const res = await locationsApi.getDistricts(filters.countryId, province)
        setDistricts(res.districts || [])
        
        const countryObj = availableCountries.find((c: any) => c.id === filters.countryId)
        if (countryObj) {
          setFacilities((countryObj.facilities || []).filter((f: any) => f.province === province))
        }
      } catch (err) {
        setDistricts([])
      }
    } else {
      setDistricts([])
    }

    onFilterChange(updated)
  }

  const handleDistrictChange = (district?: string) => {
    const updated = { ...filters, district, facilityId: undefined }
    setFilters(updated)

    if (filters.countryId) {
      const countryObj = availableCountries.find((c: any) => c.id === filters.countryId)
      if (countryObj) {
        let filtered = countryObj.facilities || []
        if (filters.province) filtered = filtered.filter((f: any) => f.province === filters.province)
        if (district) filtered = filtered.filter((f: any) => f.district === district)
        setFacilities(filtered)
      }
    }

    onFilterChange(updated)
  }

  const handleFacilityChange = (facilityId?: number) => {
    const updated = { ...filters, facilityId }
    setFilters(updated)
    onFilterChange(updated)
  }

  const handleDiseaseChange = (diseaseId?: number) => {
    const updated = { ...filters, diseaseId }
    setFilters(updated)
    onFilterChange(updated)
  }

  const handleDateRangeChange = (dateRange: FilterState['dateRange']) => {
    const updated = { ...filters, dateRange }
    setFilters(updated)
    onFilterChange(updated)
  }

  const handleReset = () => {
    const resetState: FilterState = { dateRange: '30d' }
    setFilters(resetState)
    setProvinces([])
    setDistricts([])
    setFacilities([])
    onFilterChange(resetState)
  }

  const activeCount = [
    filters.regionId, filters.countryId, filters.province, filters.district,
    filters.facilityId, filters.diseaseId, filters.ageGroup, filters.gender
  ].filter(Boolean).length

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-sm overflow-hidden transition-all ${className}`}>
      
      {/* Header Bar */}
      <div className="p-4 bg-gray-50/80 dark:bg-gray-800/80 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Filter className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white text-sm">Surveillance & Geographic Filters</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">Cascading hierarchy: Region → Country → Province → District → Facility</p>
          </div>
          {activeCount > 0 && (
            <Badge variant="info" className="ml-2">
              {activeCount} Active
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <button
              onClick={handleReset}
              className="text-xs text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-1 font-medium px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
          >
            <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Options */}
      {isExpanded && (
        <div className="p-5 space-y-4">
          
          {/* Row 1: Geographic Cascade */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
            
            {/* Region */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-blue-500" /> 1. Region
              </label>
              <select
                value={filters.regionId || ''}
                onChange={(e) => handleRegionChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Regions</option>
                {hierarchy.map((r) => (
                  <option key={r.region_id} value={r.region_id}>{r.region_name}</option>
                ))}
              </select>
            </div>

            {/* Country */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <MapPin className="w-3 h-3 text-indigo-500" /> 2. Country
              </label>
              <select
                value={filters.countryId || ''}
                onChange={(e) => handleCountryChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Countries</option>
                {availableCountries.map((c: any) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Province / State */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                3. Province/State
              </label>
              <select
                disabled={!filters.countryId || provinces.length === 0}
                value={filters.province || ''}
                onChange={(e) => handleProvinceChange(e.target.value || undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <option value="">All Provinces</option>
                {provinces.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            {/* District */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                4. District
              </label>
              <select
                disabled={!filters.province || districts.length === 0}
                value={filters.district || ''}
                onChange={(e) => handleDistrictChange(e.target.value || undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <option value="">All Districts</option>
                {districts.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>

            {/* Facility */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                5. Facility / Hospital
              </label>
              <select
                disabled={!filters.countryId || facilities.length === 0}
                value={filters.facilityId || ''}
                onChange={(e) => handleFacilityChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <option value="">All Facilities</option>
                {facilities.map((f: any) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </div>

          </div>

          {/* Row 2: Disease & Time Period */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-gray-100 dark:border-gray-700/60">
            
            {/* Disease Selector */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Activity className="w-3 h-3 text-red-500" /> Target Pathogen
              </label>
              <select
                value={filters.diseaseId || ''}
                onChange={(e) => handleDiseaseChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Diseases (Multi-Pathogen)</option>
                {diseases.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code || 'ICD-10'})</option>
                ))}
              </select>
            </div>

            {/* Time Window */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-emerald-500" /> Time Horizon
              </label>
              <div className="flex bg-gray-100 dark:bg-gray-900 p-1 rounded-xl">
                {(['7d', '30d', '90d', '1y', 'all'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => handleDateRangeChange(range)}
                    className={`flex-1 text-xs font-semibold py-1.5 rounded-lg transition-colors ${
                      filters.dateRange === range
                        ? 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
                    }`}
                  >
                    {range.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Age Group Triad */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                Age Stratification
              </label>
              <select
                value={filters.ageGroup || ''}
                onChange={(e) => {
                  const updated = { ...filters, ageGroup: e.target.value || undefined }
                  setFilters(updated)
                  onFilterChange(updated)
                }}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Age Groups</option>
                <option value="under_5">Under 5 Years (Pediatric)</option>
                <option value="5_14">5 - 14 Years</option>
                <option value="15_49">15 - 49 Years (Adult)</option>
                <option value="50_plus">50+ Years (Geriatric)</option>
              </select>
            </div>

            {/* Gender Triad */}
            <div>
              <label className="block text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                Gender Demographic
              </label>
              <select
                value={filters.gender || ''}
                onChange={(e) => {
                  const updated = { ...filters, gender: e.target.value || undefined }
                  setFilters(updated)
                  onFilterChange(updated)
                }}
                className="w-full text-xs font-medium bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-xl p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Genders</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

          </div>

        </div>
      )}
    </div>
  )
}
