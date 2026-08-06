'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { newsApi, covidIngestApi, interopApi, authApi } from '@/lib/api'
import { toast } from 'sonner'
import {
  ShieldAlert, Newspaper, Database, Share2, Plus, Trash2, Edit3, Eye,
  CheckCircle2, RefreshCw, Server, FileText, ArrowRight, Download, Activity, Globe
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { StatusDot } from '@/components/ui/StatusDot'

interface NewsArticle {
  id: number
  title: string
  summary: string
  content: string
  source?: string
  image_url?: string
  is_public: boolean
  published_at: string
}

export default function AdminPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'news' | 'pipeline' | 'interop'>('news')
  const [loading, setLoading] = useState(true)
  const [isAdmin, setIsAdmin] = useState(false)

  // News state
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingArticle, setEditingArticle] = useState<NewsArticle | null>(null)
  const [newsForm, setNewsForm] = useState({
    title: '',
    summary: '',
    content: '',
    source: 'EpiSphere Health Network',
    image_url: '',
    is_public: true,
  })

  // Ingestion state
  const [ingestStatus, setIngestStatus] = useState<any>(null)
  const [ingestLoading, setIngestLoading] = useState(false)

  // Interop state
  const [interopLogs, setInteropLogs] = useState<any[]>([])
  const [dhis2Dataset, setDhis2Dataset] = useState('COVID19_WEEKLY_AGGREGATE')
  const [dhis2Payload, setDhis2Payload] = useState('{\n  "orgUnit": "GLOBAL_WHO",\n  "period": "2026W31",\n  "dataValues": [\n    {"dataElement": "cases_new", "value": 1420}\n  ]\n}')
  const [syncResult, setSyncResult] = useState<any>(null)

  useEffect(() => {
    checkAdminAuth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const checkAdminAuth = async () => {
    try {
      const user = await authApi.getCurrentUser()
      const userRoles = user.roles || []
      if (!userRoles.includes('admin')) {
        toast.error('Access restricted to administrators')
        router.push('/')
        return
      }
      setIsAdmin(true)
      fetchTabContent('news')
    } catch (err) {
      toast.error('Please sign in as an admin to view this page')
      router.push('/auth/login')
    } finally {
      setLoading(false)
    }
  }

  const fetchTabContent = async (tab: 'news' | 'pipeline' | 'interop') => {
    setActiveTab(tab)
    try {
      if (tab === 'news') {
        const data = await newsApi.list({ public_only: false })
        setArticles(data)
      } else if (tab === 'pipeline') {
        const status = await covidIngestApi.getStatus()
        setIngestStatus(status)
      } else if (tab === 'interop') {
        const logs = await interopApi.getLogs()
        setInteropLogs(logs)
      }
    } catch (err) {
      toast.error('Failed to load data for tab')
    }
  }

  // News Handlers
  const handleSaveNews = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingArticle) {
        await newsApi.update(editingArticle.id, newsForm)
        toast.success('News article updated successfully')
      } else {
        await newsApi.create(newsForm)
        toast.success('News article created successfully')
      }
      setShowCreateModal(false)
      setEditingArticle(null)
      setNewsForm({ title: '', summary: '', content: '', source: 'EpiSphere Health Network', image_url: '', is_public: true })
      fetchTabContent('news')
    } catch (err) {
      toast.error('Error saving news article')
    }
  }

  const handleDeleteNews = async (id: number) => {
    if (!confirm('Are you sure you want to delete this article?')) return
    try {
      await newsApi.delete(id)
      toast.success('Article deleted')
      fetchTabContent('news')
    } catch (err) {
      toast.error('Failed to delete article')
    }
  }

  const handleTogglePublic = async (article: NewsArticle) => {
    try {
      await newsApi.update(article.id, { ...article, is_public: !article.is_public })
      toast.success(`Article ${!article.is_public ? 'published to public' : 'hidden from public'}`)
      fetchTabContent('news')
    } catch (err) {
      toast.error('Failed to update status')
    }
  }

  // Pipeline Handlers
  const handleSeedCountries = async () => {
    setIngestLoading(true)
    try {
      const res = await covidIngestApi.seedCountries()
      toast.success(res.message || 'Seeded country metadata')
      fetchTabContent('pipeline')
    } catch (err) {
      toast.error('Failed to seed countries')
    } finally {
      setIngestLoading(false)
    }
  }

  const handleTriggerIngest = async () => {
    setIngestLoading(true)
    try {
      const res = await covidIngestApi.triggerIngest()
      toast.success(res.message || 'Data ingestion pipeline launched in background')
      fetchTabContent('pipeline')
    } catch (err) {
      toast.error('Failed to start ingestion')
    } finally {
      setIngestLoading(false)
    }
  }

  // Interop Handlers
  const handleTestDHIS2Sync = async (dryRun: boolean) => {
    try {
      const parsed = JSON.parse(dhis2Payload)
      const res = await interopApi.syncDHIS2(dhis2Dataset, parsed, dryRun)
      setSyncResult(res)
      toast.success(dryRun ? 'Dry run completed successfully!' : 'DHIS2 Sync executed!')
      fetchTabContent('interop')
    } catch (err: any) {
      toast.error(err.response?.data?.detail?.message || 'DHIS2 Sync failed')
      setSyncResult(err.response?.data?.detail || { success: false, errors: ['Invalid JSON payload or connection error'] })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-6">
        <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span>Verifying administrator credentials...</span>
        </div>
      </div>
    )
  }

  if (!isAdmin) return null

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold uppercase tracking-wider mb-3">
                <ShieldAlert className="w-3.5 h-3.5" /> Administrator Workspace
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight">System Control & Operations Hub</h1>
              <p className="text-blue-200 mt-1 text-sm max-w-2xl">
                Manage global health news, pipeline data ingestion, and DHIS2 interoperability integrations.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant={activeTab === 'news' ? 'primary' : 'ghost'}
                onClick={() => fetchTabContent('news')}
                className="text-white hover:bg-white/10"
              >
                <Newspaper className="w-4 h-4 mr-2" /> News
              </Button>
              <Button
                variant={activeTab === 'pipeline' ? 'primary' : 'ghost'}
                onClick={() => fetchTabContent('pipeline')}
                className="text-white hover:bg-white/10"
              >
                <Database className="w-4 h-4 mr-2" /> Pipelines
              </Button>
              <Button
                variant={activeTab === 'interop' ? 'primary' : 'ghost'}
                onClick={() => fetchTabContent('interop')}
                className="text-white hover:bg-white/10"
              >
                <Share2 className="w-4 h-4 mr-2" /> Interop
              </Button>
            </div>
          </div>
        </div>

        {/* Tab 1: News Articles */}
        {activeTab === 'news' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Public Health Articles</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">Publish alerts, outbreak notices, and updates visible on the public news desk.</p>
              </div>
              <Button onClick={() => { setEditingArticle(null); setNewsForm({ title: '', summary: '', content: '', source: 'EpiSphere Health Network', image_url: '', is_public: true }); setShowCreateModal(true); }}>
                <Plus className="w-4 h-4 mr-2" /> Create Article
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article) => (
                <Card key={article.id} variant="elevated" className="flex flex-col justify-between hover:shadow-lg transition-all">
                  <div>
                    {article.image_url && (
                      <img src={article.image_url} alt={article.title} className="w-full h-40 object-cover rounded-t-xl -mt-6 -mx-6 mb-4 max-w-[calc(100%+3rem)]" />
                    )}
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant={article.is_public ? 'low' : 'default'}>
                        {article.is_public ? 'Public' : 'Draft / Private'}
                      </Badge>
                      <span className="text-xs text-gray-400">
                        {new Date(article.published_at).toLocaleDateString()}
                      </span>
                    </div>
                    <h3 className="font-bold text-gray-900 dark:text-white text-lg line-clamp-2">{article.title}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-3">{article.summary}</p>
                  </div>

                  <div className="pt-4 mt-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
                    <button
                      onClick={() => handleTogglePublic(article)}
                      className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      {article.is_public ? 'Hide' : 'Publish'}
                    </button>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => {
                          setEditingArticle(article)
                          setNewsForm({
                            title: article.title,
                            summary: article.summary,
                            content: article.content,
                            source: article.source || 'EpiSphere Health Network',
                            image_url: article.image_url || '',
                            is_public: article.is_public,
                          })
                          setShowCreateModal(true)
                        }}
                        className="p-1.5 text-gray-500 hover:text-blue-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteNews(article.id)}
                        className="p-1.5 text-gray-500 hover:text-red-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: Ingestion Pipelines */}
        {activeTab === 'pipeline' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <Card variant="elevated" className="space-y-4">
                <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <Globe className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-lg">1. Seed Country Catalog</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Initialize WHO regions, geographic coordinates, and baseline country metadata.
                  </p>
                </div>
                <Button variant="outline" className="w-full" onClick={handleSeedCountries} disabled={ingestLoading}>
                  <Globe className="w-4 h-4 mr-2" /> Seed Country Data
                </Button>
              </Card>

              <Card variant="elevated" className="space-y-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <RefreshCw className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-lg">2. Fetch OWID COVID-19 Data</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Download latest COVID-19 case, death, and recovery numbers from Our World in Data.
                  </p>
                </div>
                <Button variant="primary" className="w-full" onClick={handleTriggerIngest} disabled={ingestLoading}>
                  <RefreshCw className={`w-4 h-4 mr-2 ${ingestLoading ? 'animate-spin' : ''}`} /> Trigger Data Ingestion
                </Button>
              </Card>

              <Card variant="elevated" className="space-y-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white text-lg">3. Ingestion Health Status</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Current status of automated data pipeline tasks.
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-1 text-sm font-mono">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status:</span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 uppercase">{ingestStatus?.status || 'IDLE'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Processed:</span>
                    <span>{ingestStatus?.records_processed || 0} records</span>
                  </div>
                </div>
              </Card>

            </div>
          </div>
        )}

        {/* Tab 3: Interoperability */}
        {activeTab === 'interop' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* DHIS2 Sync Tester */}
            <Card variant="elevated" className="space-y-6">
              <div>
                <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-semibold text-sm">
                  <Share2 className="w-4 h-4" /> DHIS2 Data Exchange
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mt-1">Sync Payload Tester</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Validate or dispatch mapped epidemiological metrics to DHIS2 instance.</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-1">Dataset Code</label>
                  <Input value={dhis2Dataset} onChange={(e) => setDhis2Dataset(e.target.value)} />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-1">Payload (JSON)</label>
                  <textarea
                    rows={6}
                    value={dhis2Payload}
                    onChange={(e) => setDhis2Payload(e.target.value)}
                    className="w-full font-mono text-sm bg-gray-900 text-emerald-400 p-3 rounded-xl border border-gray-700 focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => handleTestDHIS2Sync(true)}>
                    Dry Run Test
                  </Button>
                  <Button variant="primary" className="flex-1" onClick={() => handleTestDHIS2Sync(false)}>
                    Live Dispatch
                  </Button>
                </div>

                {syncResult && (
                  <div className={`p-4 rounded-xl text-sm font-mono ${syncResult.success ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-300'}`}>
                    <div className="font-bold flex items-center gap-2">
                      <StatusDot status={syncResult.success ? 'active' : 'error'} />
                      {syncResult.message || 'Execution Result'}
                    </div>
                    {syncResult.errors?.length > 0 && (
                      <ul className="mt-2 text-xs list-disc list-inside">
                        {syncResult.errors.map((err: string, i: number) => <li key={i}>{err}</li>)}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            </Card>

            {/* Interop Execution Logs */}
            <Card variant="elevated" className="space-y-6">
              <div>
                <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-semibold text-sm">
                  <FileText className="w-4 h-4" /> Interoperability Ledger
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mt-1">Audit Logs</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Traceable ledger of inbound webhooks and outbound DHIS2 exchanges.</p>
              </div>

              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
                {interopLogs.length === 0 ? (
                  <p className="text-center text-sm text-gray-400 py-8">No interoperability events logged yet.</p>
                ) : (
                  interopLogs.map((log) => (
                    <div key={log.id} className="p-3 bg-gray-50 dark:bg-gray-800/60 rounded-xl text-xs space-y-1.5 border border-gray-100 dark:border-gray-700/50">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-gray-900 dark:text-white uppercase">{log.target_system || 'DHIS2 System'}</span>
                        <Badge variant={log.status === 'success' ? 'low' : 'critical'}>{log.status}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-gray-500">
                        <span>Direction: <strong className="uppercase">{log.direction}</strong></span>
                        <span>{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

          </div>
        )}

        {/* Modal: Create/Edit News Article */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {editingArticle ? 'Edit Article' : 'Create Public Health Article'}
              </h3>

              <form onSubmit={handleSaveNews} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Title</label>
                  <Input required value={newsForm.title} onChange={(e) => setNewsForm({ ...newsForm, title: e.target.value })} placeholder="Outbreak alert title..." />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Summary</label>
                  <Input required value={newsForm.summary} onChange={(e) => setNewsForm({ ...newsForm, summary: e.target.value })} placeholder="Brief 1-2 sentence summary..." />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Content</label>
                  <textarea
                    required
                    rows={4}
                    value={newsForm.content}
                    onChange={(e) => setNewsForm({ ...newsForm, content: e.target.value })}
                    placeholder="Full article body..."
                    className="w-full text-sm bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white p-3 rounded-xl border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Source</label>
                    <Input value={newsForm.source} onChange={(e) => setNewsForm({ ...newsForm, source: e.target.value })} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-1">Image URL (Optional)</label>
                    <Input value={newsForm.image_url} onChange={(e) => setNewsForm({ ...newsForm, image_url: e.target.value })} placeholder="https://..." />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="is_public"
                    checked={newsForm.is_public}
                    onChange={(e) => setNewsForm({ ...newsForm, is_public: e.target.checked })}
                    className="w-4 h-4 rounded text-blue-600"
                  />
                  <label htmlFor="is_public" className="text-sm text-gray-700 dark:text-gray-300">Publish immediately to public news feed</label>
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100 dark:border-gray-700">
                  <Button type="button" variant="ghost" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                  <Button type="submit" variant="primary">Save Article</Button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
