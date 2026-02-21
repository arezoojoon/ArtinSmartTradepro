'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ArrowLeft, Search, Filter, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { Eye } from 'lucide-react'

interface EngineRun {
  id: string
  engine_type: string
  status: string
  created_at: string
  input_payload: any
  output_payload: any
  explainability: any
}

export default function BrainHistoryPage() {
  const [runs, setRuns] = useState<EngineRun[]>([])
  const [filteredRuns, setFilteredRuns] = useState<EngineRun[]>([])
  const [engineTypeFilter, setEngineTypeFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchRuns = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      
      if (engineTypeFilter && engineType !== 'all') {
        params.append('engine_type', engineTypeFilter)
      }
      
      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter)
      }
      
      if (searchQuery) {
        params.append('q', searchQuery)
      }

      const response = await fetch(`/api/brain/runs?${params}`)
      if (response.ok) {
        const data = await response.json()
        setRuns(data.runs || [])
        setFilteredRuns(data.runs || [])
      }
    } catch (error) {
      console.error('Error fetching runs:', error)
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

  const getEngineIcon = (engineType: string) => {
    switch (engineType) {
      case 'arbitrage':
        return '📈'
      case 'risk':
        return '⚠️'
      case 'demand':
        return '👥'
      case 'cultural':
        return '🌍'
      default:
        return '🧠'
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

  useEffect(() => {
    fetchRuns()
  }, [])

  useEffect(() => {
    // Apply filters
    let filtered = runs

    if (engineTypeFilter && engineTypeFilter !== 'all') {
      filtered = filtered.filter(run => run.engine_type === engineTypeFilter)
    }

    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter)
    }

    if (searchQuery) {
      filtered = filtered.filter(run => 
        run.input_payload && 
        JSON.stringify(run.input_payload).toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredRuns(filtered)
  }, [runs, engineTypeFilter, statusFilter, searchQuery])

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/brain">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Brain
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Brain Engine History</h1>
            <p className="text-gray-600">Complete traceability of all brain engine runs</p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchRuns} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              <Input
                placeholder="Search runs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-xs"
              />
            </div>
            
            <Select value={engineTypeFilter} onValueChange={setEngineTypeFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Engines" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Engines</SelectItem>
                <SelectItem value="arbitrage">Arbitrage</SelectItem>
                <SelectItem value="risk">Risk</SelectItem>
                <SelectItem value="demand">Demand</SelectItem>
                <SelectItem value="cultural">Cultural</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="insufficient_data">Insufficient Data</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
      </Card>

      {/* Runs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Engine Runs ({filteredRuns.length})</CardTitle>
          <CardDescription>
            History of all brain engine executions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
              <p className="text-gray-500 mt-2">Loading runs...</p>
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No runs found</p>
              <p className="text-sm text-gray-400">
                {searchQuery || engineTypeFilter !== 'all' || statusFilter !== 'all' 
                  ? 'Try adjusting your filters' 
                  : 'Run some analyses to see history here'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Engine</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span>{getEngineIcon(run.engine_type)}</span>
                        <span className="font-medium">{getEngineLabel(run.engine_type)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(run.status)}>
                        {run.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      {run.explainability && (
                        <span className="text-sm">
                          {Math.round(run.explainability.confidence * 100)}%
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {/* Optional Fields */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="historical_start_date">Historical Start Date (Optional)</Label>
                          <Input
                            id="historical_start_date"
                            type="date"
                            value={input.historical_start_date || ''}
                            onChange={(e) => handleInputChange('historical_start_date', e.target.value)}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="historical_end_date">Historical End Date (Optional)</Label>
                          <Input
                            id="historical_end_date"
                            type="date"
                            value={input.historical_end_date || ''}
                            onChange={(e) => handleInputChange('historical_end_date', e.target.value)}
                          />
                        </div>
                      </div>
                      
                      <Button onClick={handleRun} disabled={loading} className="w-full">
                        {loading ? (
                          <>
                            <Play className="w-4 h-4 mr-2 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Run Analysis
                          </>
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
        </Card>
      )}
    </div>
  )
}
