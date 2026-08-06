'use client'

import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { TooltipComponent, GridComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([LineChart, TooltipComponent, GridComponent, CanvasRenderer]);

interface TimeSeriesChartProps {
  data: Array<{ date: string; value: number }>
}

export default function TimeSeriesChart({ data }: TimeSeriesChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return

    const chart = echarts.init(chartRef.current)

    const option = {
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        type: 'category',
        data: data.map((d) => d.date),
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          name: 'Daily Cases',
          type: 'line',
          data: data.map((d) => d.value),
          smooth: true,
          areaStyle: {
            opacity: 0.3,
          },
        },
      ],
    }

    chart.setOption(option)

    return () => {
      chart.dispose()
    }
  }, [data])

  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>
  }

  return <div ref={chartRef} className="h-64 w-full" />
}
