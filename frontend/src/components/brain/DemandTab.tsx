'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Users, Play, Eye } from 'lucide-react'
import { ExplainableCard } from './ExplainableCard'

interface DemandInput {
  product_key: string
  country: string
  forecast_months: number
  historical_start_date?: string
  historical_end_date?: string
}

interface DemandOutput {
  status: string
  forecast_points: Array<{
    date: string
    demand_value: number
    confidence_interval: {
      lower: number
      upper: number
    }
  }>
  peak_windows: Array<{
    start_date: string
    end_date: string
    demand_multiplier: number
  }>
  method_used: string
  data_points_used: number
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

export function DemandTab() {
  const [input, setInput] = useState<DemandInput>({
    product_key: '',
    country: '',
    forecast_months: 6
  })
  const [result, setResult] = useState<DemandOutput | null>(null)
  const [loading, setLoading] = useState(false)
  const [showExplainability, setShowExplainability] = useState(false)

  const handleRun = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/brain/demand/run', {
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
          forecast_points: [],
          peak_windows: [],
          method_used: 'none',
          data_points_used: 0,
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
      console.error('Error running demand forecast:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof DemandInput, value: any) => {
    setInput(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Demand Forecast</CardTitle>
          <CardDescription>
            Predict future demand using historical data and seasonality patterns
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
              <Label htmlFor="country">Country *</Label>
              <Input
                id="country"
                value={input.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                placeholder="Country code"
              />
            </div>
            
            <div>
              <Label htmlFor="forecast_months">Forecast Months</Label>
              <Select value={input.forecast_months.toString()} onValueChange={(value) => handleInputChange('forecast_months', parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3">3 months</SelectItem>
                  <SelectItem value="6">6 months</SelectItem>
                  <SelectItem value="9">9 months</SelectItem>
                  <SelectItem value="12">12 months</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* Optional Date Range */}
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
                <Users className="w-4 h-4 mr-2 animate-spin" />
                Forecasting...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Forecast
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
              <Users className="h-4 w-4" />
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
              {/* Forecast Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Forecast Summary</CardTitle>
                  <CardDescription>
                    Method: {result.method_used} | Data Points: {result.data_points_used}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-gray-500">Forecast Period</p>
                      <p className="text-lg font-semibold">{result.forecast_points.length} months</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Peak Windows</p>
                      <p className="text-lg font-semibold">{result.peak_windows.length} identified</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Data Points Used</p>
                      <p className="text-lg font-semibold">{result.data_points_used}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Forecast Points */}
              {result.forecast_points.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Forecast Points</CardTitle>
                    <CardDescription>
                      Predicted demand values with confidence intervals
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {result.forecast_points.map((point, index) => (
                        <div key={index} className="border rounded-lg p-3">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium">
                              {new Date(point.date).toLocaleDateString()}
                            </span>
                            <Badge variant="outline">
                              {point.demand_value.toFixed(2)} units
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-600">
                            Confidence: {point.confidence_interval.lower.toFixed(1)} - {point.confidence_interval.upper.toFixed(1)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* Peak Windows */}
              {result.peak_windows.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Peak Demand Windows</CardTitle>
                    <CardDescription>
                      Periods with higher than average demand
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {result.peak_windows.map((window, index) => (
                        <div key={index} className="border rounded-lg p-3 bg-green-50">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium">
                              {new Date(window.start_date).toLocaleDateString()} - {new Date(window.end_date).toLocaleDateString()}
                            </span>
                            <Badge className="bg-green-100 text-green-800">
                              {window.demand_multiplier.toFixed(1)}x average
                            </Badge>
                          </div>
                          <p className="text-sm text-green-700">
                            Peak demand period identified
                          </p>
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
