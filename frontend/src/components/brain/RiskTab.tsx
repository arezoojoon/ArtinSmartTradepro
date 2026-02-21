'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle, Play, Eye } from 'lucide-react'
import { ExplainableCard } from './ExplainableCard'

interface RiskInput {
  product_key: string
  origin_country: string
  destination_country: string
  hs_code?: string
  incoterms: string
  payment_terms: 'LC' | 'TT' | 'OA'
  supplier_id?: string
  buyer_country?: string
  route_tags?: string[]
}

interface RiskOutput {
  status: string
  risk_register: Array<{
    type: string
    severity: 'low' | 'medium' | 'high'
    reason: string
    mitigation_steps: string[]
  }>
  overall_risk_level?: 'low' | 'medium' | 'high'
  explainability: {
    data_used: Array<{
      source_name: string
      dataset: string
      collected_at: string
      coverage: string
      confidence?: number
    }>
    assumptions: string[]
    confidence: number
    confidence_rationale: string
    action_plan: string[]
    limitations: string[]
    computation_method: string
    missing_fields: string[]
  }
}

export function RiskTab() {
  const [input, setInput] = useState<RiskInput>({
    product_key: '',
    origin_country: '',
    destination_country: '',
    incoterms: 'FOB',
    payment_terms: 'LC'
  })
  const [result, setResult] = useState<RiskOutput | null>(null)
  const [loading, setLoading] = useState(false)
  const [showExplainability, setShowExplainability] = useState(false)

  const handleRun = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/brain/risk/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input)
      })

      if (response.ok) {
        const data = await response.json()
        setResult(data)
      } else {
        const error = await response.json()
        setResult({
          status: 'failed',
          risk_register: [],
          explainability: {
            data_used: [],
            assumptions: ['API call failed'],
            confidence: 0,
            confidence_rationale: 'Error occurred',
            action_plan: ['Check input and try again'],
            limitations: ['API error'],
            computation_method: 'none',
            missing_fields: []
          }
        })
      }
    } catch (error) {
      console.error('Error running risk analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof RiskInput, value: any) => {
    setInput(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const addRouteTag = () => {
    const newTag = prompt('Enter route tag (e.g., RedSea, Suez_Canal):')
    if (newTag) {
      setInput(prev => ({
        ...prev,
        route_tags: [...(prev.route_tags || []), newTag]
      }))
    }
  }

  const removeRouteTag = (index: number) => {
    setInput(prev => ({
      ...prev,
      route_tags: prev.route_tags?.filter((_, i) => i !== index) || []
    }))
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'low':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getOverallRiskColor = (level?: string) => {
    if (!level) return 'bg-gray-100 text-gray-800'
    return getSeverityColor(level)
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Analysis</CardTitle>
          <CardDescription>
            Evaluate political, payment, supplier, and route risks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="product_key">Product Key *</Label>
              <Input
                id="product_key"
                value={input.product_key}
                onChange={(e) => handleInputChange('product_key', e.target.value)}
                placeholder="HS code or internal product ID"
              />
            </div>
            
            <div>
              <Label htmlFor="origin_country">Origin Country *</Label>
              <Input
                id="origin_country"
                value={input.origin_country}
                onChange={(e) => handleInputChange('origin_country', e.target.value)}
                placeholder="Country code"
              />
            </div>
            
            <div>
              <Label htmlFor="destination_country">Destination Country *</Label>
              <Input
                id="destination_country"
                value={input.destination_country}
                onChange={(e) => handleInputChange('destination_country', e.target.value)}
                placeholder="Country code"
              />
            </div>
            
            <div>
              <Label htmlFor="incoterms">Incoterms *</Label>
              <Select value={input.incoterms} onValueChange={(value) => handleInputChange('incoterms', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FOB">FOB</SelectItem>
                  <SelectItem value="CIF">CIF</SelectItem>
                  <SelectItem value="EXW">EXW</SelectItem>
                  <SelectItem value="DDP">DDP</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="payment_terms">Payment Terms *</Label>
              <Select value={input.payment_terms} onValueChange={(value) => handleInputChange('payment_terms', value as 'LC' | 'TT' | 'OA')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LC">Letter of Credit</SelectItem>
                  <SelectItem value="TT">Telegraphic Transfer</SelectItem>
                  <SelectItem value="OA">Open Account</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Optional Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="hs_code">HS Code</Label>
              <Input
                id="hs_code"
                value={input.hs_code || ''}
                onChange={(e) => handleInputChange('hs_code', e.target.value)}
                placeholder="HS code (optional)"
              />
            </div>
            
            <div>
              <Label htmlFor="supplier_id">Supplier ID</Label>
              <Input
                id="supplier_id"
                value={input.supplier_id || ''}
                onChange={(e) => handleInputChange('supplier_id', e.target.value)}
                placeholder="Supplier identifier (optional)"
              />
            </div>
            
            <div>
              <Label htmlFor="buyer_country">Buyer Country</Label>
              <Input
                id="buyer_country"
                value={input.buyer_country || ''}
                onChange={(e) => handleInputChange('buyer_country', e.target.value)}
                placeholder="Buyer country (optional)"
              />
            </div>
          </div>
          
          {/* Route Tags */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <Label>Route Tags (Optional)</Label>
              <Button type="button" variant="outline" size="sm" onClick={addRouteTag}>
                Add Tag
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {input.route_tags?.map((tag, index) => (
                <Badge key={index} variant="secondary" className="cursor-pointer">
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeRouteTag(index)}
                    className="ml-2 text-gray-500 hover:text-red-500"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          </div>
          
          <Button onClick={handleRun} disabled={loading} className="w-full">
            {loading ? (
              <>
                <AlertTriangle className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Analysis
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {result.status === 'insufficient_data' ? (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Insufficient Data</p>
                  <p>Please provide the following required information:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {result.explainability.missing_fields.map((field, index) => (
                      <li key={index}>{field}</li>
                    ))}
                  </ul>
                </div>
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {/* Overall Risk Level */}
              {result.overall_risk_level && (
                <Card>
                  <CardHeader>
                    <CardTitle>Overall Risk Assessment</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-medium">Risk Level:</span>
                      <Badge className={getOverallRiskColor(result.overall_risk_level)}>
                        {result.overall_risk_level.toUpperCase()}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Risk Register */}
              {result.risk_register.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Risk Register</CardTitle>
                    <CardDescription>
                      {result.risk_register.length} identified risks
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {result.risk_register.map((risk, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge className={getSeverityColor(risk.severity)}>
                                {risk.type}
                              </Badge>
                              <Badge className={getSeverityColor(risk.severity)}>
                                {risk.severity.toUpperCase()}
                              </Badge>
                            </div>
                          </div>
                          <p className="font-medium text-gray-900">{risk.reason}</p>
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-2">Mitigation Steps:</p>
                            <ul className="list-disc list-inside space-y-1 text-sm">
                              {risk.mitigation_steps.map((step, stepIndex) => (
                                <li key={stepIndex}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Explainability */}
              <ExplainableCard
                explainability={result.explainability}
                onToggleExplainability={() => setShowExplainability(!showExplainability)}
              />
            </>
          )}
        </div>
      )}
    </div>
  )
}
