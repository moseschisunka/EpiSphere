'use client'

/* eslint-disable @next/next/no-img-element */

import React, { useState, useEffect } from 'react'
import Navbar from '../../components/Navbar'
import { publicApi } from '../../lib/api'
import Link from 'next/link'

interface NewsArticle {
    id: number;
    title: string;
    summary: string;
    content: string;
    source: string;
    image_url: string;
    published_at: string;
}

export default function BrowsePage() {
    const [articles, setArticles] = useState<NewsArticle[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null)

    useEffect(() => {
        publicApi.getNews().then(setArticles).catch(console.error).finally(() => setLoading(false))
    }, [])

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />

            <main className="container mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">Health News & Trends</h1>
                    <div className="text-sm text-gray-500">Curated by EpiSphere</div>
                </div>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                        <p className="mt-2 text-gray-500">Loading latest updates...</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {articles.map(article => (
                            <div key={article.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 flex flex-col">
                                <div className="h-48 bg-gray-200 relative overflow-hidden">
                                    {/* Placeholder for real images if implementation allows external images */}
                                    <div className="absolute inset-0 bg-blue-100 flex items-center justify-center text-blue-300">
                                        <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
                                    </div>
                                    {article.image_url && (
                                        <img src={article.image_url} alt={article.title} className="w-full h-full object-cover absolute inset-0" onError={(e) => e.currentTarget.style.display = 'none'} />
                                    )}
                                </div>
                                <div className="p-6 flex-1 flex flex-col">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded">{article.source || 'General'}</span>
                                        <span className="text-xs text-gray-400">{new Date(article.published_at).toLocaleDateString()}</span>
                                    </div>
                                    <h2 className="text-xl font-bold text-gray-900 mb-2">{article.title}</h2>
                                    <p className="text-gray-600 mb-4 flex-1 line-clamp-3">{article.summary}</p>
                                    <button
                                        onClick={() => setSelectedArticle(article)}
                                        className="text-blue-600 font-medium hover:text-blue-800 self-start mt-auto"
                                    >
                                        Read Full Story &rarr;
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </main>

            {/* Reading Modal */}
            {selectedArticle && (
                <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={() => setSelectedArticle(null)}>
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="p-6">
                            <div className="flex justify-between items-start mb-4">
                                <h2 className="text-2xl font-bold text-gray-900">{selectedArticle.title}</h2>
                                <button onClick={() => setSelectedArticle(null)} className="text-gray-400 hover:text-gray-600">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500 mb-6 border-b pb-4">
                                <span>{selectedArticle.source}</span>
                                <span>â€¢</span>
                                <span>{new Date(selectedArticle.published_at).toLocaleDateString()}</span>
                            </div>
                            <div className="prose max-w-none text-gray-700">
                                <p className="whitespace-pre-wrap">{selectedArticle.content}</p>
                            </div>
                            <div className="mt-8 pt-4 border-t flex justify-end">
                                <button
                                    onClick={() => setSelectedArticle(null)}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}


