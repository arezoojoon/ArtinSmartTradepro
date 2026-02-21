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
import { TrendingUp, AlertCircle, Play, Eye } from 'lucide-react'
import { ExplainableCard } from './ExplainableCard'

interface ArbitrageInput {
  product_key: string
  buy_market: string
  sell_market: string
  buy_price: number
  buy_currency: string
  sell_price: number
  sell_currency: string
  freight_cost?: number
  fx_rates?: Record<string, number>
  fees?: Array<{ amount: number; currency: string }>
  target_margin_pct?: number
}

interface ArbitrageOutput {
  status: string
  opportunity_card?: {
    estimated_margin_pct: number
    key_drivers: string[]
    next_actions: string[]
    risk_factors: string[]
  }
  similar_deals: Array<{
    id: string
    product_key: string
    buy_market: string
    sell_market: string
    estimated_margin_pct?: number
    realized_margin_pct?: number
    outcome: string
    created_at: string
  }>
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

export function ArbitrageTab() {
  const [input, setInput] = useState<ArbitrageInput>({
    product_key: '',
    buy_market: '',
    sell_market: '',
    buy_price: 0,
    buy_currency: 'USD',
    sell_price: 0,
    sell_currency: 'USD'
  })
  const [result, setResult] = useState<ArbitrageOutput | null>(null)
  const [loading, setLoading] = useState(false)
  const [showExplainability, setShowExplainability] = useState(false)

  const handleRun = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/brain/arbitrage/run', {
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
      console.error('Error running arbitrage analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof ArbitrageInput, value: any) => {
    setInput(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const addFee = () => {
    setInput(prev => ({
      ...prev,
      fees: [...(prev.fees || []), { amount: 0, currency: 'USD' }]
    }))
  }

  const updateFee = (index: number, field: 'amount' | 'currency', value: any) => {
    setInput(prev => ({
      ...prev,
      fees: prev.fees?.map((fee, i) => 
        i === index ? { ...fee, [field]: value } : fee
      ) || []
    }))
  }

  const removeFee = (index: number) => {
    setInput(prev => ({
      ...prev,
      fees: prev.fees?.filter((_, i) => i !== index) || []
    }))
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Arbitrage Analysis</CardTitle>
          <CardDescription>
            Calculate margins and find similar past deals
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
              <Label htmlFor="buy_market">Buy Market *</Label>
              <Input
                id="buy_market"
                value={input.buy_market}
                onChange={(e) => handleInputChange('buy_market', e.target.value)}
                placeholder="Country or port"
              />
            </div>
            
            <div>
              <Label htmlFor="sell_market">Sell Market *</Label>
              <Input
                id="sell_market"
                value={input.sell_market}
                onChange={(e) => handleInputChange('sell_market', e.target.value)}
                placeholder="Country or port"
              />
            </div>
            
            <div>
              <Label htmlFor="buy_price">Buy Price *</Label>
              <Input
                id="buy_price"
                type="number"
                step="0.01"
                value={input.buy_price}
                onChange={(e) => handleInputChange('buy_price', parseFloat(e.target.value) || 0)}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <Label htmlFor="buy_currency">Buy Currency *</Label>
              <Select value={input.buy_currency} onValueChange={(value) => handleInputChange('buy_currency', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                  <SelectItem value="JPY">JPY</SelectItem>
                  <SelectItem value="CNY">CNY</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="sell_price">Sell Price *</Label>
              <Input
                id="sell_price"
                type="number"
                step="0.01"
                value={input.sell_price}
                onChange={(e) => handleInputChange('sell_price', parseFloat(e.target.value) || 0)}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <Label htmlFor="sell_currency">Sell Currency *</Label>
              <Select value={input.sell_currency} onValueChange={(value) => handleInputChange('sell_currency', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                  <SelectItem value="JPY">JPY</SelectItem>
                  <SelectItem value="CNY">CNY</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Optional Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="freight_cost">Freight Cost</Label>
              <Input
                id="freight_cost"
                type="number"
                step="0.01"
                value={input.freight_cost || ''}
                onChange={(e) => handleInputChange('freight_cost', parseFloat(e.target.value) || undefined)}
                placeholder="0.00"
              />
            </div>
            
            <div>
              <Label htmlFor="target_margin_pct">Target Margin %</Label>
              <Input
                id="target_margin_pct"
                type="number"
                step="0.1"
                value={input.target_margin_pct || ''}
                onChange={(e) => handleInputChange('target_margin_pct', parseFloat(e.target.value) || undefined)}
                placeholder="15.0"
              />
            </div>
          </div>
          
          {/* FX Rates */}
          <div>
            <Label>FX Rates (Optional)</Label>
            <Textarea
              placeholder='{"EUR_USD": 1.1, "GBP_USD": 1.25}'
              value={input.fx_rates ? JSON.stringify(input.fx_rates, null, 2) : ''}
              onChange={(e) => {
                try {
                  const fxRates = e.target.value ? JSON.parse(e.target.value) : undefined
                  handleInputChange('fx_rates', fxRates)
                } catch (error) {
                  // Invalid JSON, ignore
                }
              }}
              rows={2}
            />
          </div>
          
          {/* Fees */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <Label>Additional Fees (Optional)</Label>
              <Button type="button" variant="outline" size="sm" onClick={addFee}>
                Add Fee
              </Button>
            </div>
            <div className="space-y-2">
              {input.fees?.map((fee, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    type="number"
                    step="0.01"
                    value={fee.amount}
                    onChange={(e) => updateFee(index, 'amount', parseFloat(e.target.value) || 0)}
                    placeholder="Amount"
                  />
                  <Select value={fee.currency} onValueChange={(value) => updateFee(index, 'currency', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                      <SelectItem value="GBP">GBP</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button type="button" variant="outline" size="sm" onClick={() => removeFee(index)}>
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          </div>
          
          <Button onClick={handleRun} disabled={loading} className="w-full">
            {loading ? (
              <>
                <TrendingUp className="w-4 h-4 mr-2 animate-spin" />
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
              <AlertCircle className="h-4 w-4" />
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
              {/* Opportunity Card */}
              {result.opportunity_card && (
                <Card>
                  <CardHeader>
                    <CardTitle>Opportunity Analysis</CardTitle>
                    <CardDescription>
                      Margin: {result.opportunity_card.estimated_margin_pct.toFixed(2)}%
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium">Key Drivers</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {result.opportunity_card.key_drivers.map((driver, index) => (
                            <li key={index}>{driver}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="font-medium">Next Actions</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {result.opportunity_card.next_actions.map((action, index) => (
                            <li key={index}>{action}</li>
                          ))}
                        </ul>
                      </div>
                      
                      {result.opportunity_card.risk_factors.length > 0 && (
                        <div>
                          <h4 className="font-medium text-red-600">Risk Factors</h4>
                          <ul className="list-disc list-inside space-y-1 text-sm text-red-600">
                            {result.opportunity_card.risk_factors.map((risk, index) => (
                              <li key={index}>{risk}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Similar Deals */}
              {result.similar_deals.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Similar Past Deals</CardTitle>
                    <CardDescription>
                      {result.similar_deals.length} comparable transactions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {result.similar_deals.map((deal, index) => (
                        <div key={index} className="flex justify-between items-center p-3 border rounded">
                          <div>
                            <p className="font-medium">{deal.product_key}</p>
                            <p className="text-sm text-gray-500">
                              {deal.buy_market} → {deal.sell_market}
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(deal.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <Badge className={
                              deal.outcome === 'won' ? 'bg-green-100 text-green-800' :
                              deal.outcome === 'lost' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }>
                              {deal.outcome}
                            </Badge>
                            {deal.realized_margin_pct && (
                              <p className="text-sm mt-1">
                                Realized: {deal.realized_margin_pct.toFixed(1)}%
                              </p>
                            )}
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
