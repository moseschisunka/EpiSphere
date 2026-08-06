'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import {
  Globe, Brain, BarChart3, Upload, Bell, TrendingUp,
  Shield, Zap, Database, ArrowRight, Activity, Users,
  Heart, Microscope, ChevronRight, ExternalLink
} from 'lucide-react'

function AnimatedCounter({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const duration = 2000
    const steps = 60
    const increment = target / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        setCount(target)
        clearInterval(timer)
      } else {
        setCount(Math.floor(current))
      }
    }, duration / steps)
    return () => clearInterval(timer)
  }, [target])

  return <span>{count.toLocaleString()}{suffix}</span>
}

const features = [
  {
    icon: Globe,
    title: 'Global Surveillance',
    description: 'Monitor disease cases across 150+ countries with real-time interactive maps and geospatial analytics.',
    color: 'from-blue-500 to-cyan-500',
    bgLight: 'bg-blue-50 dark:bg-blue-950/30',
  },
  {
    icon: Brain,
    title: 'AI Outbreak Detection',
    description: 'Multi-layer ML engine using CUSUM, EWMA, Isolation Forest, and Farrington algorithms for early signal detection.',
    color: 'from-violet-500 to-purple-500',
    bgLight: 'bg-violet-50 dark:bg-violet-950/30',
  },
  {
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Deep epidemiological dashboards with time-series forecasting, syndromic surveillance, and trend analysis.',
    color: 'from-emerald-500 to-teal-500',
    bgLight: 'bg-emerald-50 dark:bg-emerald-950/30',
  },
  {
    icon: Upload,
    title: 'Data Ingestion',
    description: 'Upload surveillance data via CSV, Excel, or API with automated quality validation and lineage tracking.',
    color: 'from-amber-500 to-orange-500',
    bgLight: 'bg-amber-50 dark:bg-amber-950/30',
  },
  {
    icon: Bell,
    title: 'Automated Alerts',
    description: 'Severity-graded outbreak alerts with probability scores, investigation workflows, and resolution tracking.',
    color: 'from-rose-500 to-red-500',
    bgLight: 'bg-rose-50 dark:bg-rose-950/30',
  },
  {
    icon: TrendingUp,
    title: 'Forecasting Engine',
    description: 'Short-term forecasts using ARIMA, Prophet, and seasonal models with auto-selection and backtesting.',
    color: 'from-sky-500 to-indigo-500',
    bgLight: 'bg-sky-50 dark:bg-sky-950/30',
  },
]

const capabilities = [
  { icon: Shield, label: 'HIPAA Compliant' },
  { icon: Zap, label: 'Real-time Processing' },
  { icon: Database, label: 'DHIS2 Integration' },
  { icon: Users, label: 'Role-based Access' },
  { icon: Heart, label: 'Clinical EHR' },
  { icon: Microscope, label: 'Lab Integration' },
]

const flowSteps = [
  { step: '01', title: 'Data Ingestion', desc: 'CSV, Excel, API, DHIS2, Clinical EHR' },
  { step: '02', title: 'Quality Engine', desc: 'Validation, deduplication, lineage tracking' },
  { step: '03', title: 'AI Analytics', desc: 'Outbreak detection, forecasting, syndromics' },
  { step: '04', title: 'Intelligence', desc: 'Alerts, dashboards, reports, public portal' },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-gray-900 via-blue-950 to-indigo-950 text-white">
        {/* Animated background grid */}
        <div className="absolute inset-0 opacity-[0.07]" style={{
          backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }} />
        
        {/* Gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-10 right-20 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-40 right-40 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />

        <div className="relative container mx-auto px-4 py-24 lg:py-32">
          <div className="max-w-4xl mx-auto text-center">
            {/* Status badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-sm font-medium mb-8 backdrop-blur-sm">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
              </span>
              Platform Operational — Monitoring Active
            </div>

            <h1 className="text-5xl lg:text-7xl font-black tracking-tight mb-6 leading-[1.1]">
              <span className="bg-gradient-to-r from-white via-blue-100 to-blue-200 bg-clip-text text-transparent">
                EpiSphere
              </span>
              <span className="text-blue-400"> AI</span>
            </h1>
            
            <p className="text-lg lg:text-xl text-blue-100/80 mb-10 max-w-2xl mx-auto leading-relaxed">
              AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform.
              Protecting populations through real-time epidemic intelligence.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/dashboard/global"
                className="group inline-flex items-center justify-center gap-2 bg-white text-gray-900 px-8 py-3.5 rounded-xl font-semibold hover:bg-blue-50 transition-all shadow-lg shadow-white/10 hover:shadow-white/20"
              >
                <Activity className="w-5 h-5" />
                View Dashboard
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="/auth/register"
                className="group inline-flex items-center justify-center gap-2 bg-white/10 border border-white/20 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-white/20 transition-all backdrop-blur-sm"
              >
                Get Started
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Stats ticker */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
            {[
              { value: 150, suffix: '+', label: 'Countries Monitored' },
              { value: 7, suffix: '+', label: 'Diseases Tracked' },
              { value: 6, suffix: '', label: 'Detection Algorithms' },
              { value: 24, suffix: '/7', label: 'Surveillance' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl lg:text-4xl font-black text-white">
                  <AnimatedCounter target={stat.value} suffix={stat.suffix} />
                </div>
                <div className="text-sm text-blue-200/70 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom wave */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 60" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path d="M0 60V30C240 10 480 0 720 10C960 20 1200 40 1440 30V60H0Z" className="fill-white dark:fill-gray-950" />
          </svg>
        </div>
      </section>

      {/* Capabilities bar */}
      <section className="bg-white dark:bg-gray-950 py-8 border-b border-gray-100 dark:border-gray-800">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-6 md:gap-10">
            {capabilities.map((cap, i) => (
              <div key={i} className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <cap.icon className="w-4 h-4" />
                <span className="text-sm font-medium">{cap.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 lg:py-28 bg-white dark:bg-gray-950">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 text-sm font-semibold mb-4">
              Platform Capabilities
            </span>
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Intelligence at Every Layer
            </h2>
            <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto">
              From data ingestion to outbreak response — a complete epidemiological intelligence pipeline.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <div
                key={i}
                className={`group relative p-8 rounded-2xl ${feature.bgLight} border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg`}
              >
                <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.color} shadow-lg mb-5`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Flow Section */}
      <section className="py-20 bg-gray-50 dark:bg-gray-900/50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <span className="inline-block px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 text-sm font-semibold mb-4">
              Architecture
            </span>
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              End-to-End Pipeline
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-4 max-w-5xl mx-auto">
            {flowSteps.map((step, i) => (
              <div key={i} className="relative">
                <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-100 dark:border-gray-700 text-center hover:shadow-md transition-shadow">
                  <div className="text-4xl font-black text-gray-100 dark:text-gray-700 mb-2">{step.step}</div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">{step.title}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{step.desc}</p>
                </div>
                {i < flowSteps.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
                    <ChevronRight className="w-5 h-5 text-gray-300 dark:text-gray-600" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold mb-4">
            Ready to Protect Populations?
          </h2>
          <p className="text-lg text-blue-100/80 mb-8 max-w-xl mx-auto">
            Join the global network of health professionals using AI-powered disease surveillance.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/register"
              className="inline-flex items-center justify-center gap-2 bg-white text-blue-700 px-8 py-3.5 rounded-xl font-semibold hover:bg-blue-50 transition-all shadow-lg"
            >
              Create Free Account
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/browse"
              className="inline-flex items-center justify-center gap-2 border border-white/30 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-white/10 transition-all"
            >
              Explore Public Data
              <ExternalLink className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 dark:bg-gray-950 text-gray-400 py-16 border-t border-gray-800">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-10 mb-12">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-blue-600 text-white rounded-lg px-2 py-0.5 text-lg font-bold">E</span>
                <span className="text-white font-bold text-lg">EpiSphere <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 border border-blue-800">AI</span></span>
              </div>
              <p className="text-sm text-gray-500 leading-relaxed">
                AI-powered global disease surveillance and outbreak intelligence platform.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Platform</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/dashboard/global" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/alerts" className="hover:text-white transition-colors">Alerts</Link></li>
                <li><Link href="/browse" className="hover:text-white transition-colors">Browse Data</Link></li>
                <li><Link href="/surveillance" className="hover:text-white transition-colors">Surveillance</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">Operations</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/clinical" className="hover:text-white transition-colors">Clinical Desk</Link></li>
                <li><Link href="/pharmacy" className="hover:text-white transition-colors">Pharmacy</Link></li>
                <li><Link href="/upload" className="hover:text-white transition-colors">Upload Data</Link></li>
                <li><Link href="/facility" className="hover:text-white transition-colors">Facilities</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm uppercase tracking-wider">System</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                  </span>
                  All Systems Operational
                </li>
                <li>API v1.0.0</li>
                <li>FastAPI + Next.js</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center text-sm">
            <p>&copy; {new Date().getFullYear()} EpiSphere AI. All rights reserved.</p>
            <p className="mt-2 md:mt-0">Built for Global Health Intelligence</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
