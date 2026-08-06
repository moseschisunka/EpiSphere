'use client'

import { useEffect, useRef, useState } from 'react'
import * as echarts from 'echarts/core'
import {
  LineChart,
  LineSeriesOption
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  DataZoomComponent,
  LegendComponent,
  DataZoomComponentOption,
  TitleComponentOption,
  TooltipComponentOption,
  GridComponentOption,
  LegendComponentOption
} from 'echarts/components'
import { LabelLayout, UniversalTransition } from 'echarts/features'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  DataZoomComponent,
  LegendComponent,
  LineChart,
  LabelLayout,
  UniversalTransition,
  CanvasRenderer
])

type ECOption = echarts.ComposeOption<
  | LineSeriesOption
  | TitleComponentOption
  | TooltipComponentOption
  | GridComponentOption
  | DataZoomComponentOption
  | LegendComponentOption
>

interface TimeSeriesChartProps {
  data: Array<{
    date: string
    new_cases: number
    new_deaths?: number
  }>
}

export default function TimeSeriesChart({ data }: TimeSeriesChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const checkDarkMode = () => {
      setIsDark(document.documentElement.classList.contains('dark') || 
                window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    
    checkDarkMode()
    
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          checkDarkMode()
        }
      })
    })
    
    observer.observe(document.documentElement, { attributes: true })
    
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return

    if (chartInstance.current) {
      chartInstance.current.dispose()
    }

    const textColor = isDark ? '#94a3b8' : '#64748b'
    const splitLineColor = isDark ? '#334155' : '#e2e8f0'

    chartInstance.current = echarts.init(chartRef.current)
    
    const dates = data.map(d => d.date)
    const cases = data.map(d => d.new_cases)
    const deaths = data.map(d => d.new_deaths || 0)

    const hasDeaths = deaths.some(d => d > 0)

    const series: LineSeriesOption[] = [
      {
        name: 'Daily Cases',
        type: 'line',
        data: cases,
        smooth: true,
        showSymbol: false,
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.5)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
          ])
        }
      }
    ]

    if (hasDeaths) {
      series.push({
        name: 'Daily Deaths',
        type: 'line',
        data: deaths,
        smooth: true,
        showSymbol: false,
        itemStyle: { color: '#ef4444' }
      })
    }

    const option: ECOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        textStyle: { color: isDark ? '#f8fafc' : '#0f172a' },
        valueFormatter: (value: any) => Number(value).toLocaleString()
      },
      legend: {
        data: hasDeaths ? ['Daily Cases', 'Daily Deaths'] : ['Daily Cases'],
        textStyle: { color: textColor },
        top: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          start: 0,
          end: 100,
          textStyle: { color: textColor },
          borderColor: splitLineColor,
          fillerColor: isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.1)'
        }
      ],
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: { color: textColor },
        axisLine: { lineStyle: { color: splitLineColor } }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: textColor,
          formatter: (value: number) => {
            if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
            if (value >= 1000) return (value / 1000).toFixed(1) + 'K'
            return value.toString()
          }
        },
        splitLine: { lineStyle: { color: splitLineColor, type: 'dashed' } }
      },
      series: series
    }

    chartInstance.current.setOption(option)

    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize()
    })
    
    resizeObserver.observe(chartRef.current)

    return () => {
      resizeObserver.disconnect()
      if (chartInstance.current) {
        chartInstance.current.dispose()
      }
    }
  }, [data, isDark])

  return (
    <div className="w-full h-80">
      <div ref={chartRef} className="w-full h-full" />
    </div>
  )
}
