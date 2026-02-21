'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Search, Plus, Download, RefreshCw, Eye, Brain, Target, Users } from 'lucide-react'
import Link from 'next/link'

interface HunterLead {
  id: string
  primary_name: string
  country: string
  city?: string
  website?: string
  industry?: string
  status: 'new' | 'enriched' | 'qualified' | 'rejected' | 'pushed_to_crm'
  score_total: number
  created_at: string
  identities: Array<{
    type: string
    value: string
  }>
}

const statusColors = {
  new: 'bg-gray-100 text-gray-800',
  enriched: 'bg-blue-100 text-blue-800',
  qualified: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  pushed_to_crm: 'bg-purple-100 text-purple-800'
}

const statusLabels = {
  new: 'New',
  enriched: 'Enriched',
  qualified: 'Qualified',
  rejected: 'Rejected',
  pushed_to_crm: 'Pushed to CRM'
}

export default function HunterPage() {
  const [leads, setLeads] = useState<HunterLead[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [countryFilter, setCountryFilter] = useState<string>('all')
  const [minScore, setMinScore] = useState<number>(0)
  const [selectedLeads, setSelectedLeads] = useState<string[]>([])

  // Fetch leads
  const fetchLeads = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: '50',
        ...(searchQuery && { q: searchQuery }),
        ...(statusFilter !== 'all' && { status: statusFilter }),
        ...(countryFilter !== 'all' && { country: countryFilter }),
        ...(minScore > 0 && { min_score: minScore.toString() })
      })

      const response = await fetch(`/api/hunter/leads?${params}`)
      if (!response.ok) throw new Error('Failed to fetch leads')
      
      const data = await response.json()
      setLeads(data)
    } catch (error) {
      console.error('Error fetching leads:', error)
    } finally {
      setLoading(false)
    }
  }

  // Handle bulk actions
  const handleBulkEnrich = async () => {
    if (selectedLeads.length === 0) return
    
    try {
      const promises = selectedLeads.map(leadId =>
        fetch(`/api/hunter/leads/${leadId}/enrich`, { method: 'POST' })
      )
      
      await Promise.all(promises)
      await fetchLeads()
      setSelectedLeads([])
    } catch (error) {
      console.error('Error bulk enriching:', error)
    }
  }

  const handleBulkScore = async () => {
    if (selectedLeads.length === 0) return
    
    try {
      const promises = selectedLeads.map(leadId =>
        fetch(`/api/hunter/leads/${leadId}/score`, { method: 'POST' })
      )
      
      await Promise.all(promises)
      await fetchLeads()
      setSelectedLeads([])
    } catch (error) {
      console.error('Error bulk scoring:', error)
    }
  }

  // Handle individual actions
  const handleEnrich = async (leadId: string) => {
    try {
      await fetch(`/api/hunter/leads/${leadId}/enrich`, { method: 'POST' })
      await fetchLeads()
    } catch (error) {
      console.error('Error enriching lead:', error)
    }
  }

  const handleScore = async (leadId: string) => {
    try {
      await fetch(`/api/hunter/leads/${leadId}/score`, { method: 'POST' })
      await fetchLeads()
    } catch (error) {
      console.error('Error scoring lead:', error)
    }
  }

  const handleQualify = async (leadId: string) => {
    try {
      await fetch(`/api/hunter/leads/${leadId}/qualify`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Manual qualification' })
      })
      await fetchLeads()
    } catch (error) {
      console.error('Error qualifying lead:', error)
    }
  }

  const handleReject = async (leadId: string) => {
    const reason = prompt('Rejection reason:')
    if (!reason) return
    
    try {
      await fetch(`/api/hunter/leads/${leadId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      })
      await fetchLeads()
    } catch (error) {
      console.error('Error rejecting lead:', error)
    }
  }

  const handlePushToCRM = async (leadId: string) => {
    try {
      await fetch(`/api/hunter/leads/${leadId}/push-to-crm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          create_company: true,
          create_contact: true,
          create_task: true,
          task_due_days: 1
        })
      })
      await fetchLeads()
    } catch (error) {
      console.error('Error pushing to CRM:', error)
    }
  }

  // Get unique countries for filter
  const countries = Array.from(new Set(leads.map(lead => lead.country))).sort()

  useEffect(() => {
    fetchLeads()
  }, [searchQuery, statusFilter, countryFilter, minScore])

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Hunter Lead Management</h1>
          <p className="text-gray-600 mt-1">Manage and enrich your sales leads</p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link href="/hunter/import">
              <Download className="w-4 h-4 mr-2" />
              Import CSV
            </Link>
          </Button>
          <Button asChild>
            <Link href="/hunter/manual">
              <Plus className="w-4 h-4 mr-2" />
              Add Lead
            </Link>
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search leads..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="enriched">Enriched</SelectItem>
                <SelectItem value="qualified">Qualified</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="pushed_to_crm">Pushed to CRM</SelectItem>
              </SelectContent>
            </Select>

            <Select value={countryFilter} onValueChange={setCountryFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                {countries.map(country => (
                  <SelectItem key={country} value={country}>{country}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div>
              <Input
                type="number"
                placeholder="Min Score"
                value={minScore}
                onChange={(e) => setMinScore(parseInt(e.target.value) || 0)}
                min="0"
                max="100"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedLeads.length > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-800">
                {selectedLeads.length} lead{selectedLeads.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={handleBulkEnrich}>
                  <Brain className="w-4 h-4 mr-2" />
                  Enrich
                </Button>
                <Button size="sm" variant="outline" onClick={handleBulkScore}>
                  <Target className="w-4 h-4 mr-2" />
                  Score
                </Button>
                <Button size="sm" variant="outline" onClick={() => setSelectedLeads([])}>
                  Clear
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leads Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Leads ({leads.length})</CardTitle>
            <CardDescription>Your lead pipeline</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={fetchLeads}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
              <p className="text-gray-500 mt-2">Loading leads...</p>
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-12 h-12 mx-auto text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mt-4">No leads found</h3>
              <p className="text-gray-500 mt-2">
                {searchQuery || statusFilter !== 'all' || countryFilter !== 'all' || minScore > 0
                  ? 'Try adjusting your filters'
                  : 'Import some leads or add them manually to get started'
                }
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={selectedLeads.length === leads.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedLeads(leads.map(lead => lead.id))
                        } else {
                          setSelectedLeads([])
                        }
                      }}
                    />
                  </TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Country</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedLeads.includes(lead.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedLeads([...selectedLeads, lead.id])
                          } else {
                            setSelectedLeads(selectedLeads.filter(id => id !== lead.id))
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <Link href={`/hunter/${lead.id}`} className="font-medium text-blue-600 hover:text-blue-800">
                          {lead.primary_name}
                        </Link>
                        {lead.website && (
                          <a
                            href={lead.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-gray-500 hover:text-gray-700 block"
                          >
                            {lead.website}
                          </a>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{lead.country}</TableCell>
                    <TableCell>
                      <Badge className={statusColors[lead.status]}>
                        {statusLabels[lead.status]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center">
                        <span className="font-medium">{lead.score_total}</span>
                        <span className="text-xs text-gray-500 ml-1">/70</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {lead.identities
                          .filter(identity => identity.type === 'email')
                          .slice(0, 1)
                          .map(identity => identity.value)
                          .join(', ')}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button size="sm" variant="outline" asChild>
                          <Link href={`/hunter/${lead.id}`}>
                            <Eye className="w-3 h-3" />
                          </Link>
                        </Button>
                        
                        {lead.status === 'new' && (
                          <Button size="sm" variant="outline" onClick={() => handleEnrich(lead.id)}>
                            <Brain className="w-3 h-3" />
                          </Button>
                        )}
                        
                        {lead.status === 'enriched' && (
                          <Button size="sm" variant="outline" onClick={() => handleScore(lead.id)}>
                            <Target className="w-3 h-3" />
                          </Button>
                        )}
                        
                        {lead.status === 'enriched' && (
                          <Button size="sm" variant="outline" onClick={() => handleQualify(lead.id)}>
                            ✓
                          </Button>
                        )}
                        
                        {lead.status === 'enriched' && (
                          <Button size="sm" variant="outline" onClick={() => handleReject(lead.id)}>
                            ✗
                          </Button>
                        )}
                        
                        {lead.status === 'qualified' && (
                          <Button size="sm" onClick={() => handlePushToCRM(lead.id)}>
                            Push
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
