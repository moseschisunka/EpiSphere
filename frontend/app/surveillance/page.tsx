'use client'

import SyndromicDashboard from '../../components/surveillance/SyndromicDashboard'
import dynamic from 'next/dynamic'
const FacilityHeatmap = dynamic(() => import('../../components/surveillance/FacilityHeatmap'), { ssr: false })
import IntegrationStatus from '../../components/surveillance/IntegrationStatus'

export default function SurveillancePage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <main className="container mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-6">National Surveillance Operations</h1>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <div className="space-y-6">
                        <section>
                            <h2 className="text-xl font-semibold mb-3 text-gray-800">Syndromic Signals</h2>
                            <SyndromicDashboard />
                        </section>
                        <section>
                            <h2 className="text-xl font-semibold mb-3 text-gray-800">Interoperability</h2>
                            <IntegrationStatus />
                        </section>
                    </div>

                    <section>
                        <h2 className="text-xl font-semibold mb-3 text-gray-800">Outbreak Heatmap</h2>
                        <FacilityHeatmap />
                        <div className="mt-4 bg-blue-50 p-4 rounded border border-blue-100">
                            <h3 className="font-semibold text-blue-800 mb-2">Operational Status</h3>
                            <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
                                <li>Syndromic Engine: <strong>Active</strong></li>
                                <li>DHIS2 Link: <strong>Connected</strong></li>
                                <li>Reporting Completeness: <strong>94%</strong></li>
                            </ul>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    )
}
