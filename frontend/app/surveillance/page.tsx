'use client'

import { useState } from 'react'
import SyndromicDashboard from '@/components/surveillance/SyndromicDashboard'
import dynamic from 'next/dynamic'
const FacilityHeatmap = dynamic(() => import('@/components/surveillance/FacilityHeatmap'), { ssr: false })
import IntegrationStatus from '@/components/surveillance/IntegrationStatus'
import AdvancedFilters, { FilterState } from '@/components/surveillance/AdvancedFilters'
import { ShieldCheck, Activity, Share2, MapPin } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

export default function SurveillancePage() {
  const [activeFilters, setActiveFilters] = useState<FilterState>({ dateRange: '30d' })

  const handleFilterChange = (newFilters: FilterState) => {
    setActiveFilters(newFilters)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 mb-1">
              <Activity className="w-4 h-4" /> Real-Time Epidemiological Intelligence
            </div>
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              National Surveillance Operations
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Multi-pathogen monitoring, syndromic signal analysis, and geographic outbreak heatmaps.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="low" className="px-3 py-1.5 text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" /> Surveillance Engine Active
            </Badge>
            <Badge variant="info" className="px-3 py-1.5 text-xs font-semibold">
              <Share2 className="w-3.5 h-3.5 mr-1" /> DHIS2 Linked
            </Badge>
          </div>
        </div>

        {/* Advanced Cascading Filter Component */}
        <AdvancedFilters onFilterChange={handleFilterChange} />

        {/* Main Operational Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column: Syndromic & Interop */}
          <div className="space-y-8">
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-500" /> Syndromic Signals & Early Warning
                </h2>
                <span className="text-xs text-gray-400 font-mono">Horizon: {activeFilters.dateRange.toUpperCase()}</span>
              </div>
              <SyndromicDashboard />
            </section>

            <section className="space-y-3">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Share2 className="w-5 h-5 text-indigo-500" /> Interoperability & Data Exchanges
              </h2>
              <IntegrationStatus />
            </section>
          </div>

          {/* Right Column: Outbreak Heatmap & Operational Status */}
          <div className="space-y-8">
            <section className="space-y-3">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <MapPin className="w-5 h-5 text-emerald-500" /> Geographic Outbreak Heatmap
              </h2>
              <FacilityHeatmap />
              
              <Card variant="glass" className="mt-4 border-blue-200/50 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-950/30">
                <h3 className="font-bold text-blue-900 dark:text-blue-300 text-sm mb-2">Operational Integrity Checklist</h3>
                <ul className="grid grid-cols-2 gap-2 text-xs text-blue-800 dark:text-blue-300">
                  <li className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Syndromic Engine: <strong>Active</strong>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    DHIS2 Gateway: <strong>Operational</strong>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Reporting Completeness: <strong>94.2%</strong>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500" />
                    Data Quality Score: <strong>98.6/100</strong>
                  </li>
                </ul>
              </Card>
            </section>
          </div>

        </div>

      </div>
    </div>
  )
}
