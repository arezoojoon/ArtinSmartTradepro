'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Eye, Info } from 'lucide-react'

interface ExplainabilityBundle {
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

interface ExplainableCardProps {
  explainability: ExplainabilityBundle
  onToggleExplainability: () => void
}

export function ExplainableCard({ explainability, onToggleExplainability }: ExplainableCardProps) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800'
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
    if (confidence >= 0.4) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High'
    if (confidence >= 0.6) return 'Medium'
    if (confidence >= 0.4) return 'Low'
    return 'Very Low'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Explainability
          <Button variant="outline" size="sm" onClick={onToggleExplainability}>
            <Eye className="w-4 h-4 mr-2" />
            Why?
          </Button>
        </CardTitle>
        <CardDescription>
          Understanding the analysis behind the results
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Confidence Score */}
          <div className="flex items-center justify-between">
            <span className="font-medium">Confidence</span>
            <div className="flex items-center gap-2">
              <Badge className={getConfidenceColor(explainability.confidence)}>
                {getConfidenceLabel(explainability.confidence)}
              </Badge>
              <span className="text-sm text-gray-500">
                {Math.round(explainability.confidence * 100)}%
              </span>
            </div>
          </div>
          
          {/* Data Sources */}
          <div>
            <h4 className="font-medium mb-2">Data Sources Used</h4>
            <div className="space-y-2">
              {explainability.data_used.map((source, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded text-sm">
                  <div>
                    <p className="font-medium">{source.source_name}</p>
                    <p className="text-gray-500">{source.dataset}</p>
                    <p className="text-xs text-gray-400">{source.coverage}</p>
                  </div>
                  <div className="text-right">
                    {source.confidence && (
                      <Badge variant="outline" className="text-xs">
                        {Math.round(source.confidence * 100)}%
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Key Assumptions */}
          {explainability.assumptions.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Key Assumptions</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {explainability.assumptions.map((assumption, index) => (
                  <li key={index}>{assumption}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Action Plan */}
          {explainability.action_plan.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Recommended Actions</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {explainability.action_plan.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Limitations */}
          {explainability.limitations.length > 0 && (
            <div>
              <h4 className="font-medium mb-2 text-orange-600">Limitations</h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-orange-600">
                {explainability.limitations.map((limitation, index) => (
                  <li key={index}>{limitation}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Computation Method */}
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Method:</span>
              <span className="font-mono text-xs">{explainability.computation_method}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {explainability.confidence_rationale}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
