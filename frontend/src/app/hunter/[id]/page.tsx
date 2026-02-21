'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { 
  ArrowLeft, 
  Brain, 
  Target, 
  CheckCircle, 
  XCircle, 
  Users,
  Globe,
  Mail,
  Phone,
  Building,
  Calendar,
  ExternalLink,
  RefreshCw
} from 'lucide-react'
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
  score_breakdown: any
  created_at: string
  identities: Array<{
    id: string
    type: string
    value: string
    normalized_value: string
    created_at: string
  }>
  evidence_by_field: Record<string, Array<{
    id: string
    field_name: string
    source_name: string
    source_url?: string
    collected_at: string
    confidence: number
    snippet?: string
  }>>
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

const identityIcons = {
  email: Mail,
  phone: Phone,
  domain: Globe,
  linkedin: Users,
  address: Building,
  other: Building
}

export default function HunterLeadDetailPage() {
  const params = useParams()
  const router = useRouter()
  const leadId = params.id as string
  
  const [lead, setLead] = useState<HunterLead | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Fetch lead details
  const fetchLead = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/hunter/leads/${leadId}`)
      if (!response.ok) {
        if (response.status === 404) {
          router.push('/hunter')
          return
        }
        throw new Error('Failed to fetch lead')
      }
      
      const data = await response.json()
      setLead(data)
    } catch (error) {
      console.error('Error fetching lead:', error)
    } finally {
      setLoading(false)
    }
  }

  // Handle actions
  const handleEnrich = async () => {
    if (!lead) return
    
    setActionLoading('enrich')
    try {
      await fetch(`/api/hunter/leads/${lead.id}/enrich`, { method: 'POST' })
      await fetchLead()
    } catch (error) {
      console.error('Error enriching lead:', error)
    } finally {
      setActionLoading(null)
    }
  }

  const handleScore = async () => {
    if (!lead) return
    
    setActionLoading('score')
    try {
      await fetch(`/api/hunter/leads/${lead.id}/score`, { method: 'POST' })
      await fetchLead()
    } catch (error) {
      console.error('Error scoring lead:', error)
    } finally {
      setActionLoading(null)
    }
  }

  const handleQualify = async () => {
    if (!lead) return
    
    setActionLoading('qualify')
    try {
      await fetch(`/api/hunter/leads/${lead.id}/qualify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Manual qualification' })
      })
      await fetchLead()
    } catch (error) {
      console.error('Error qualifying lead:', error)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async () => {
    if (!lead) return
    
    const reason = prompt('Rejection reason:')
    if (!reason) return
    
    setActionLoading('reject')
    try {
      await fetch(`/api/hunter/leads/${lead.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      })
      await fetchLead()
    } catch (error) {
      console.error('Error rejecting lead:', error)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePushToCRM = async () => {
    if (!lead) return
    
    setActionLoading('push')
    try {
      await fetch(`/api/hunter/leads/${lead.id}/push-to-crm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          create_company: true,
          create_contact: true,
          create_task: true,
          task_due_days: 1
        })
      })
      await fetchLead()
    } catch (error) {
      console.error('Error pushing to CRM:', error)
    } finally {
      setActionLoading(null)
    }
  }

  useEffect(() => {
    fetchLead()
  }, [leadId])

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
          <p className="text-gray-500 mt-2">Loading lead details...</p>
        </div>
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-12">
          <p className="text-gray-500">Lead not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/hunter">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Hunter
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{lead.primary_name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={statusColors[lead.status]}>
                {statusLabels[lead.status]}
              </Badge>
              {lead.score_total > 0 && (
                <span className="text-sm text-gray-500">
                  Score: {lead.score_total}/70
                </span>
              )}
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          {lead.status === 'new' && (
            <Button onClick={handleEnrich} disabled={actionLoading === 'enrich'}>
              <Brain className="w-4 h-4 mr-2" />
              {actionLoading === 'enrich' ? 'Enriching...' : 'Enrich'}
            </Button>
          )}
          
          {lead.status === 'enriched' && (
            <>
              <Button onClick={handleScore} disabled={actionLoading === 'score'}>
                <Target className="w-4 h-4 mr-2" />
                {actionLoading === 'score' ? 'Scoring...' : 'Score'}
              </Button>
              <Button variant="outline" onClick={handleQualify} disabled={actionLoading === 'qualify'}>
                <CheckCircle className="w-4 h-4 mr-2" />
                {actionLoading === 'qualify' ? 'Qualifying...' : 'Qualify'}
              </Button>
              <Button variant="outline" onClick={handleReject} disabled={actionLoading === 'reject'}>
                <XCircle className="w-4 h-4 mr-2" />
                {actionLoading === 'reject' ? 'Rejecting...' : 'Reject'}
              </Button>
            </>
          )}
          
          {lead.status === 'qualified' && (
            <Button onClick={handlePushToCRM} disabled={actionLoading === 'push'}>
              <Users className="w-4 h-4 mr-2" />
              {actionLoading === 'push' ? 'Pushing...' : 'Push to CRM'}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Lead Information */}
          <Card>
            <CardHeader>
              <CardTitle>Lead Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Country</label>
                  <p className="text-gray-900">{lead.country}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">City</label>
                  <p className="text-gray-900">{lead.city || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Industry</label>
                  <p className="text-gray-900">{lead.industry || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Created</label>
                  <p className="text-gray-900">
                    {new Date(lead.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              {lead.website && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Website</label>
                  <a
                    href={lead.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <ExternalLink className="w-3 h-3" />
                    {lead.website}
                  </a>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Score Breakdown */}
          {lead.score_total > 0 && lead.score_breakdown && (
            <Card>
              <CardHeader>
                <CardTitle>Score Breakdown</CardTitle>
                <CardDescription>
                  Total: {lead.score_total}/{lead.score_breakdown.total_possible} ({lead.score_breakdown.score_percentage}%)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {lead.score_breakdown.signals.map((signal: any, index: number) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{signal.name}</p>
                        <p className="text-sm text-gray-500">{signal.explanation}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{signal.score}/{signal.max_score}</p>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(signal.score / signal.max_score) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {lead.score_breakdown.risk_flags.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <p className="font-medium text-red-600 mb-2">Risk Flags:</p>
                      <ul className="text-sm text-red-600 space-y-1">
                        {lead.score_breakdown.risk_flags.map((flag: string, index: number) => (
                          <li key={index}>• {flag}</li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Evidence */}
          <Card>
            <CardHeader>
              <CardTitle>Evidence</CardTitle>
              <CardDescription>
                Data sources and confidence scores for each field
              </CardDescription>
            </CardHeader>
            <CardContent>
              {Object.keys(lead.evidence_by_field).length === 0 ? (
                <p className="text-gray-500 text-center py-4">No evidence available</p>
              ) : (
                <div className="space-y-6">
                  {Object.entries(lead.evidence_by_field).map(([fieldName, evidenceList]) => (
                    <div key={fieldName}>
                      <h4 className="font-medium text-gray-900 mb-2 capitalize">{fieldName}</h4>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Source</TableHead>
                            <TableHead>Confidence</TableHead>
                            <TableHead>Snippet</TableHead>
                            <TableHead>Collected</TableHead>
                            <TableHead>URL</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {evidenceList.map((evidence) => (
                            <TableRow key={evidence.id}>
                              <TableCell>
                                <Badge variant="outline">{evidence.source_name}</Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-2">
                                  <div className="w-12 bg-gray-200 rounded-full h-2">
                                    <div
                                      className={`h-2 rounded-full ${
                                        evidence.confidence >= 0.8 ? 'bg-green-600' :
                                        evidence.confidence >= 0.6 ? 'bg-yellow-600' : 'bg-red-600'
                                      }`}
                                      style={{ width: `${evidence.confidence * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-sm">{Math.round(evidence.confidence * 100)}%</span>
                                </div>
                              </TableCell>
                              <TableCell className="max-w-xs truncate">
                                {evidence.snippet || 'N/A'}
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1 text-sm text-gray-500">
                                  <Calendar className="w-3 h-3" />
                                  {new Date(evidence.collected_at).toLocaleDateString()}
                                </div>
                              </TableCell>
                              <TableCell>
                                {evidence.source_url ? (
                                  <a
                                    href={evidence.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                ) : (
                                  <span className="text-gray-400">N/A</span>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Identities */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
            </CardHeader>
            <CardContent>
              {lead.identities.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No contact info</p>
              ) : (
                <div className="space-y-3">
                  {lead.identities.map((identity) => {
                    const Icon = identityIcons[identity.type as keyof typeof identityIcons] || Building
                    return (
                      <div key={identity.id} className="flex items-center gap-3">
                        <Icon className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium">{identity.value}</p>
                          <p className="text-xs text-gray-500 capitalize">{identity.type}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {lead.status === 'new' && (
                <Button onClick={handleEnrich} className="w-full" disabled={actionLoading === 'enrich'}>
                  <Brain className="w-4 h-4 mr-2" />
                  {actionLoading === 'enrich' ? 'Enriching...' : 'Enrich Lead'}
                </Button>
              )}
              
              {lead.status === 'enriched' && (
                <>
                  <Button onClick={handleScore} className="w-full" disabled={actionLoading === 'score'}>
                    <Target className="w-4 h-4 mr-2" />
                    {actionLoading === 'score' ? 'Scoring...' : 'Score Lead'}
                  </Button>
                  <Button onClick={handleQualify} className="w-full" disabled={actionLoading === 'qualify'}>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {actionLoading === 'qualify' ? 'Qualifying...' : 'Qualify Lead'}
                  </Button>
                  <Button variant="outline" onClick={handleReject} className="w-full" disabled={actionLoading === 'reject'}>
                    <XCircle className="w-4 h-4 mr-2" />
                    {actionLoading === 'reject' ? 'Rejecting...' : 'Reject Lead'}
                  </Button>
                </>
              )}
              
              {lead.status === 'qualified' && (
                <Button onClick={handlePushToCRM} className="w-full" disabled={actionLoading === 'push'}>
                  <Users className="w-4 h-4 mr-2" />
                  {actionLoading === 'push' ? 'Pushing...' : 'Push to CRM'}
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
