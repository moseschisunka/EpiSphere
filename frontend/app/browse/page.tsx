'use client'

/* eslint-disable @next/next/no-img-element */

import React, { useState, useEffect } from 'react'
import { publicApi } from '../../lib/api'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Newspaper, Loader2, ArrowRight, X } from 'lucide-react'

interface NewsArticle {
  id: number
  title: string
  summary: string
  content: string
  source: string
  image_url: string
  published_at: string
}

export default function BrowsePage() {
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null)

  useEffect(() => {
    publicApi.getNews()
      .then(setArticles)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-foreground">Health News & Trends</h1>
            <p className="text-muted-foreground mt-2">Curated global health intelligence and outbreak updates</p>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="animate-pulse overflow-hidden h-[400px]">
                <div className="h-48 bg-muted"></div>
                <CardContent className="p-6 mt-4">
                  <div className="h-6 bg-muted rounded w-3/4 mb-4"></div>
                  <div className="h-4 bg-muted rounded w-full mb-2"></div>
                  <div className="h-4 bg-muted rounded w-5/6"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {articles.map(article => (
              <Card 
                key={article.id} 
                variant="elevated" 
                className="overflow-hidden flex flex-col hover:border-accent/50 transition-all duration-300 group cursor-pointer"
                onClick={() => setSelectedArticle(article)}
              >
                <div className="h-48 bg-muted relative overflow-hidden">
                  <div className="absolute inset-0 bg-blue-500/10 flex items-center justify-center text-blue-500/40">
                    <Newspaper className="w-12 h-12" />
                  </div>
                  {article.image_url && (
                    <img 
                      src={article.image_url} 
                      alt={article.title} 
                      className="w-full h-full object-cover absolute inset-0 group-hover:scale-105 transition-transform duration-500" 
                      onError={(e) => (e.currentTarget.style.display = 'none')} 
                    />
                  )}
                  <div className="absolute top-4 left-4">
                    <Badge variant="info" className="shadow-lg backdrop-blur-md bg-background/90 text-foreground">
                      {article.source || 'Intelligence'}
                    </Badge>
                  </div>
                </div>
                <div className="p-6 flex-1 flex flex-col bg-card">
                  <div className="text-xs text-muted-foreground mb-3 font-medium">
                    {new Date(article.published_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                  <h2 className="text-xl font-bold text-foreground mb-3 line-clamp-2 leading-tight group-hover:text-blue-500 transition-colors">
                    {article.title}
                  </h2>
                  <p className="text-muted-foreground mb-4 flex-1 line-clamp-3 text-sm leading-relaxed">
                    {article.summary}
                  </p>
                  <div className="text-blue-500 font-semibold text-sm flex items-center gap-1 mt-auto">
                    Read Full Story <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Reading Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div 
            className="bg-card rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-white/10 animate-in slide-in-from-bottom-8 duration-300"
            onClick={e => e.stopPropagation()}
          >
            {selectedArticle.image_url && (
              <div className="h-64 relative shrink-0">
                <img 
                  src={selectedArticle.image_url} 
                  alt={selectedArticle.title} 
                  className="w-full h-full object-cover" 
                  onError={(e) => (e.currentTarget.style.display = 'none')} 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
                <button 
                  onClick={() => setSelectedArticle(null)} 
                  className="absolute top-4 right-4 p-2 bg-black/40 hover:bg-black/60 rounded-full text-white backdrop-blur-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            )}
            
            <div className="p-8 overflow-y-auto">
              {!selectedArticle.image_url && (
                <div className="flex justify-end mb-4">
                  <button onClick={() => setSelectedArticle(null)} className="text-muted-foreground hover:text-foreground">
                    <X className="w-6 h-6" />
                  </button>
                </div>
              )}
              
              <div className="flex items-center gap-3 text-sm text-blue-500 font-semibold mb-4">
                <Badge variant="info" className="border-blue-500/30 text-blue-500 bg-blue-500/10">
                  {selectedArticle.source}
                </Badge>
                <span className="text-muted-foreground font-normal">
                  {new Date(selectedArticle.published_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </span>
              </div>
              
              <h2 className="text-3xl font-black text-foreground mb-6 leading-tight">
                {selectedArticle.title}
              </h2>
              
              <div className="prose prose-slate dark:prose-invert max-w-none prose-p:leading-relaxed prose-p:text-muted-foreground">
                <p className="whitespace-pre-wrap">{selectedArticle.content}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
