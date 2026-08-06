'use client'

import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core';
import { MapChart } from 'echarts/charts';
import { TooltipComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer]);

interface GlobalMapProps {
  countryStats: Array<{
    country_id: number
    country_name: string
    iso_code: string
    total_cases: number
  }>
}

export default function GlobalMap({ countryStats }: GlobalMapProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartRef.current || !countryStats || countryStats.length === 0) return

    const chart = echarts.init(chartRef.current)

    // Prepare data for map
    const mapData = countryStats.map((stat) => ({
      name: stat.country_name,
      value: stat.total_cases,
    }))

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} cases',
      },
      visualMap: {
        min: 0,
        max: Math.max(...countryStats.map((s) => s.total_cases)),
        inRange: {
          color: ['#e0f2fe', '#0284c7'],
        },
        text: ['High', 'Low'],
        calculable: true,
      },
      series: [
        {
          name: 'Cases',
          type: 'map',
          map: 'world',
          data: mapData,
          emphasis: {
            label: {
              show: true,
            },
          },
        },
      ],
    }

    // Note: In production, you would need to register the world map
    // For now, this is a placeholder that would work with proper map registration
    chart.setOption(option)

    return () => {
      chart.dispose()
    }
  }, [countryStats])

  if (!countryStats || countryStats.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>
  }

  return <div ref={chartRef} className="h-64 w-full" />
}
