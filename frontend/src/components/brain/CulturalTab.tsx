'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Globe, Play, Eye } from 'lucide-react'
import { ExplainableCard } from './ExplainableCard'

interface CulturalInput {
  destination_country: string
  buyer_type: 'B2B' | 'Distributor' | 'Retail'
  payment_terms_target: 'LC' | 'TT' | 'OA'
  deal_context: string
  language: 'en' | 'ar' | 'fa' | 'ru' | 'hi' | 'ur'
}

interface CulturalOutput {
  status: string
  templates: Array<{
    template_type: string
    content: string
    language: string
    referenced_profile_id: string
  }>
  negotiation_tips: string[]
  objection_handling: string[]
  referenced_profile_ids: string[]
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

export function CulturalTab() {
  const [input, setInput] = useState<CulturalInput>({
    destination_country: '',
    buyer_type: 'B2B',
    payment_terms_target: 'LC',
    deal_context: '',
    language: 'en'
  })
  const [result, setResult] = useState<CulturalOutput | null>(null)
  const [loading, setLoading] = useState(false)
  const [showExplainability, setShowExplainability] = useState(false)

  const handleRun = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/brain/cultural/run', {
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
          templates: [],
          negotiation_tips: [],
          objection_handling: [],
          referenced_profile_ids: [],
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
      console.error('Error running cultural analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof CulturalInput, value: any) => {
    setInput(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const languages = [
    { value: 'en', label: 'English' },
    { value: 'ar', label: 'Arabic' },
    { value: 'fa', label: 'Farsi' },
    { value: 'ru', label: 'Russian' },
    { value: 'hi', label: 'Hindi' },
    { value: 'ur', label: 'Urdu' }
  ]

  const buyerTypes = [
    { value: 'B2B', label: 'B2B' },
    { value: 'Distributor', label: 'Distributor' },
    { value: 'Retail', label: 'Retail' }
  ]

  const paymentTerms = [
    { value: 'LC', label: 'Letter of Credit' },
    { value: 'TT', label: 'Telegraphic Transfer' },
    { value: 'OA', label: 'Open Account' }
  ]

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Cultural Strategy</CardTitle>
          <CardDescription>
            Generate cultural insights and communication templates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              <Label htmlFor="buyer_type">Buyer Type *</Label>
              <Select value={input.buyer_type} onValueChange={(value) => handleInputChange('buyer_type', value as 'B2B' | 'Distributor' | 'Retail')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {buyerTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="payment_terms_target">Target Payment Terms *</Label>
              <Select value={input.payment_terms_target} onValueChange={(value) => handleInputChange('payment_terms_target', value as 'LC' | 'TT' | 'OA')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {paymentTerms.map((term) => (
                    <SelectItem key={term.value} value={term.value}>
                      {term.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="language">Language *</Label>
              <Select value={input.language} onValueChange={(value) => handleInputChange('language', value as 'en' | 'ar' | 'fa' | 'ru' | 'hi' | 'ur')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {languages.map((lang) => (
                    <SelectItem key={lang.value} value={lang.value}>
                      {lang.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div>
            <Label htmlFor="deal_context">Deal Context *</Label>
            <Textarea
              id="deal_context"
              value={input.deal_context}
              onChange={(e) => handleInputChange('deal_context', e.target.value)}
              placeholder="Brief description of the business opportunity (max 500 characters)"
              rows={3}
              maxLength={500}
            />
            <p className="text-xs text-gray-500">
              {input.deal_context.length}/500 characters
            </p>
          </div>
          
          <Button onClick={handleRun} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Globe className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Generate Strategy
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
              <Globe className="h-4 w-4" />
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
              {/* Templates */}
              {result.templates.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Generated Templates</CardTitle>
                    <CardDescription>
                      {result.templates.length} templates in {result.templates[0].language}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {result.templates.map((template, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex justify-between items-center mb-2">
                            <Badge variant="outline">
                              {template.template_type}
                            </Badge>
                            <Badge variant="secondary">
                              {template.language}
                            </Badge>
                          </div>
                          <div className="prose">
                            <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded">
                              {template.content}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Negotiation Tips */}
              {result.negotiation_tips.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Negotiation Tips</CardTitle>
                    <CardDescription>
                      Cultural insights for business negotiations
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc list-inside space-y-2 text-sm">
                      {result.negotiation_tips.map((tip, index) => (
                        <li key={index}>{tip}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
              
              {/* Objection Handling */}
              {result.objection_handling.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Objection Handling</CardTitle>
                    <CardDescription>
                      Strategies for handling common objections
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc list-inside space-y-2 text-sm">
                      {result.objection_handling.map((strategy, index) => (
                        <li key={index}>{strategy}</li>
                      ))}
                    </ul>
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
