'use client'

import { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { surveillanceApi } from '../../lib/api'

export default function SyndromicDashboard() {
    const [data, setData] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const trends = await surveillanceApi.getSyndromicTrends()
                setData(trends)
            } catch (e) {
                console.error("Failed to load syndromic data", e)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    if (loading) return <div className="p-4 text-center">Loading syndromic trends...</div>

    const dates = data.map(item => item.date)
    // Assuming keys are consistent
    const series = Object.keys(data[0] || {}).filter(k => k !== 'date').map(syndrome => ({
        name: syndrome,
        type: 'line',
        data: data.map(item => item[syndrome]),
        smooth: true
    }))

    const option = {
        title: { text: 'National Syndromic Trends (7 Days)' },
        tooltip: { trigger: 'axis' },
        legend: { bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: dates },
        yAxis: { type: 'value' },
        series: series
    }

    return (
        <div className="bg-white p-4 rounded-lg shadow-md">
            <ReactECharts option={option} style={{ height: '400px' }} />
            <div className="mt-2 text-sm text-gray-500 bg-yellow-50 p-2 rounded">
                <strong>Note:</strong> These are syndromic signals based on clinical symptoms, not confirmed diagnoses.
            </div>
        </div>
    )
}
