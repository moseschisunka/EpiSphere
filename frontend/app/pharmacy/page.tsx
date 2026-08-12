'use client'

import { useState, useEffect, useCallback } from 'react'
import { pharmacyApi } from '../../lib/api'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Pill, User, Clock, AlertCircle } from 'lucide-react'

interface Prescription {
  id: number
  drug_name: string
  quantity: number
  patient_mrn?: string | null
  clinician_name?: string | null
  created_at?: string
}

export default function PharmacyDesk() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const data = await pharmacyApi.getPending()
      setPrescriptions(data)
      setError(null)
    } catch (e) {
      console.error('Failed to load pharmacy data', e)
      setError('Failed to load pending prescriptions')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleDispense = async (id: number) => {
    try {
      await pharmacyApi.dispense({ prescription_id: id, notes: 'Dispensed via Pharmacy Desk' })
      setPrescriptions(prev => prev.filter(p => p.id !== id))
      toast.success('Medication dispensed successfully')
    } catch (e) {
      console.error('Failed to dispense', e)
      setError('Failed to dispense medication')
      toast.error('Failed to dispense medication')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">Pharmacy Desk</h1>
            <p className="text-muted-foreground mt-1">Manage and dispense pending prescriptions</p>
          </div>
          <Button onClick={loadData} variant="outline" className="gap-2">
            <Clock className="w-4 h-4" /> Refresh Queue
          </Button>
        </div>

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <div className="grid gap-6">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="h-24" />
              </Card>
            ))
          ) : prescriptions.length === 0 ? (
            <Card className="p-12 text-center border-dashed">
              <Pill className="w-12 h-12 text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground">No pending prescriptions</h3>
              <p className="text-muted-foreground mt-1">The pharmacy queue is currently empty.</p>
            </Card>
          ) : (
            prescriptions.map(item => (
              <Card key={item.id} variant="elevated" className="overflow-hidden hover:border-accent/50 transition-colors">
                <div className="flex flex-col md:flex-row">
                  <div className="p-6 flex-1 border-b md:border-b-0 md:border-r border-border bg-card">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-blue-500/10 dark:bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                        <Pill className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-bold text-foreground mb-1">{item.drug_name}</h3>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mt-2">
                          <div className="flex items-center gap-1.5 bg-muted px-2 py-1 rounded-md">
                            <span className="font-semibold text-foreground">Qty: {item.quantity}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <User className="w-4 h-4" /> MRN: {item.patient_mrn || 'N/A'}
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-medium">Dr. {item.clinician_name}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="p-6 bg-muted/30 flex items-center justify-center md:w-48">
                    <Button 
                      onClick={() => handleDispense(item.id)} 
                      className="w-full shadow-lg shadow-blue-500/20"
                    >
                      Dispense
                    </Button>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </main>
    </div>
  )
}
