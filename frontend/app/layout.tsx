import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'
import { ThemeProvider } from '@/components/ThemeProvider'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'EpiSphere AI - Global Disease Surveillance',
  description: 'AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform. Monitor disease outbreaks worldwide with real-time analytics, AI-driven detection, and forecasting.',
  keywords: ['disease surveillance', 'outbreak detection', 'epidemiology', 'public health', 'AI', 'global health'],
  authors: [{ name: 'EpiSphere AI' }],
  openGraph: {
    title: 'EpiSphere AI - Global Disease Surveillance',
    description: 'AI-Powered Global Disease Surveillance and Outbreak Intelligence Platform',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-white focus:text-blue-600 focus:rounded-lg focus:shadow-lg">
            Skip to main content
          </a>
          <Navbar />
          <main id="main-content" className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors duration-300">
            {children}
          </main>
          <Toaster position="top-right" richColors />
        </ThemeProvider>
      </body>
    </html>
  )
}
