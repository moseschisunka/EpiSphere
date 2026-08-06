'use client'

import { Activity, Skull, Bell, Globe, TrendingUp, TrendingDown } from 'lucide-react'

interface StatsCardsProps {
  stats: any
  alerts: any
}

export default function StatsCards({ stats, alerts }: StatsCardsProps) {
  const cards = [
    {
      title: 'Total Cases',
      value: stats?.total_cases?.toLocaleString() || '0',
      icon: Activity,
      color: 'bg-blue-500',
      borderColor: 'border-l-blue-500',
      delta: '+5.2%',
      isPositive: false
    },
    {
      title: 'Total Deaths',
      value: stats?.total_deaths?.toLocaleString() || '0',
      icon: Skull,
      color: 'bg-red-500',
      borderColor: 'border-l-red-500',
      delta: '+1.1%',
      isPositive: false
    },
    {
      title: 'Active Alerts',
      value: alerts?.length?.toLocaleString() || '0',
      icon: Bell,
      color: 'bg-amber-500',
      borderColor: 'border-l-amber-500',
      delta: '-2.4%',
      isPositive: true
    },
    {
      title: 'Affected Countries',
      value: stats?.affected_countries?.toLocaleString() || '0',
      icon: Globe,
      color: 'bg-indigo-500',
      borderColor: 'border-l-indigo-500',
      delta: '0%',
      isPositive: true
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, idx) => (
        <div 
          key={idx} 
          className={`bg-white dark:bg-slate-900 rounded-xl shadow-sm border-l-4 ${card.borderColor} border-y border-r border-slate-200 dark:border-slate-800 p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg`}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-slate-500 dark:text-slate-400 font-medium text-sm">{card.title}</h3>
            <div className={`p-2 rounded-lg ${card.color} bg-opacity-10 dark:bg-opacity-20`}>
              <card.icon className={`w-5 h-5 ${card.color.replace('bg-', 'text-')}`} />
            </div>
          </div>
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {card.value}
            </div>
            <div className={`flex items-center text-sm font-medium ${card.isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
              {card.isPositive ? <TrendingDown className="w-4 h-4 mr-1" /> : <TrendingUp className="w-4 h-4 mr-1" />}
              {card.delta}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
