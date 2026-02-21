'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { format } from 'date-fns'

interface BrainEngineRun {
  id: string
  engine_type: string
  status: string
  created_at: string
  input_payload: any
  output_payload: any
  explainability: any
}

export default function BrainRunDetailPage() {
  const params = useParams()
  const runId = params.id as string
  const [run, setRun] = useState<BrainEngineRun | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchRun = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/brain/runs/${runId}`)
      if (response.ok) {
        const data = await response.json()
        setRun(data)
      } else {
        console.error('Error fetching run details:', response.status)
      }
    } catch (error) {
      console.error('Error fetching run details:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800'
      case 'insufficient_data':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getEngineLabel = (engineType: string) => {
    switch (engineType) {
      case 'arbitrage':
        return 'Arbitrage'
      case 'risk':
        return 'Risk'
      case 'demand':
        return 'Demand'
      case 'cultural':
        return 'Cultural'
      default:
        return 'Unknown'
    }
  }

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'PPP')
  }

  useEffect(() => {
    fetchRun()
  }, [runId])

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
          <p className="text-gray-500 mt-2">Loading run details...</p>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12">
          <p className="text-gray-500">Run not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/brain/history">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to History
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Run Details</h1>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              Run ID: {run.id.substring(0, 8)}...
            </span>
            <Badge className={getStatusColor(run.status)}>
              {run.status.replace('_', ' ')}
            </Badge>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run Overview</CardTitle>
          <CardDescription>
            Complete details of the brain engine execution
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Engine Type</p>
              <p className="font-medium">{getEngineLabel(run.engine_type)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <Badge className={getStatusColor(run.status)}>
                {run.status.replace('_', ' ')}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p className="font-medium">{formatDate(run.created_at)}</p>
            </div>
          </div>
          
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium">Input Summary</h4>
            <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
              {JSON.stringify(run.input_payload, null, 2)}
            </pre>
          </div>
          
          {run.output_payload && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium">Output Summary</h4>
              <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                {JSON.stringify(run.output_payload, null, 2)}
              </pre>
            </div>
          )}
          
          {run.explainability && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium">Explainability</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Data Sources:</span>
                  <span className="font-medium">{run.explainability.data_used?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Assumptions:</span>
                  <span className="font-medium">{run.explainability.assumptions?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Confidence:</span>
                  <span className="font-medium">{Math.round((run.explainability.confidence || 0) * 100)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Method:</span>
                  <span className="font-mono text-xs">{run.explainability.computation_method}</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
