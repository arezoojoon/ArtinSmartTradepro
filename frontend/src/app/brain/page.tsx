'use client'

import React, { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Brain, TrendingUp, AlertTriangle, Users, Globe } from 'lucide-react'
import { ArbitrageTab } from '@/components/brain/ArbitrageTab'
import { RiskTab } from '@/components/brain/RiskTab'
import { DemandTab } from '@/components/brain/DemandTab'
import { CulturalTab } from '@/components/brain/CulturalTab'

interface EngineRun {
  id: string
  engine_type: string
  status: string
  created_at: string
  input_payload: any
  output_payload: any
  explainability: any
}

export default function BrainPage() {
  const [activeTab, setActiveTab] = useState('arbitrage')
  const [recentRuns, setRecentRuns] = useState<EngineRun[]>([])

  const fetchRecentRuns = async () => {
    try {
      const response = await fetch('/api/brain/runs?limit=5')
      if (response.ok) {
        const data = await response.json()
        setRecentRuns(data.runs || [])
      }
    } catch (error) {
      console.error('Error fetching recent runs:', error)
    }
  }

  const getEngineIcon = (engineType: string) => {
    switch (engineType) {
      case 'arbitrage':
        return <TrendingUp className="w-4 h-4" />
      case 'risk':
        return <AlertTriangle className="w-4 h-4" />
      case 'demand':
        return <Users className="w-4 h-4" />
      case 'cultural':
        return <Globe className="w-4 h-4" />
      default:
        return <Brain className="w-4 h-4" />
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

  React.useEffect(() => {
    fetchRecentRuns()
  }, [])

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Brain Engines</h1>
          <p className="text-gray-600 mt-1">AI-powered analysis with full explainability</p>
        </div>
        <Button variant="outline" asChild>
          <a href="/brain/history">
            View History
          </a>
        </Button>
      </div>

      {/* Recent Runs */}
      {recentRuns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Runs</CardTitle>
            <CardDescription>Your latest brain engine analyses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentRuns.map((run) => (
                <div key={run.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getEngineIcon(run.engine_type)}
                    <div>
                      <p className="font-medium capitalize">{run.engine_type}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(run.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(run.status)}>
                      {run.status.replace('_', ' ')}
                    </Badge>
                    {run.explainability && (
                      <span className="text-sm text-gray-500">
                        Confidence: {Math.round(run.explainability.confidence * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Engine Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="arbitrage" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Arbitrage
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Risk
          </TabsTrigger>
          <TabsTrigger value="demand" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Demand
          </TabsTrigger>
          <TabsTrigger value="cultural" className="flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Cultural
          </TabsTrigger>
        </TabsList>

        <TabsContent value="arbitrage" className="space-y-4">
          <ArbitrageTab />
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <RiskTab />
        </TabsContent>

        <TabsContent value="demand" className="space-y-4">
          <DemandTab />
        </TabsContent>

        <TabsContent value="cultural" className="space-y-4">
          <CulturalTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
