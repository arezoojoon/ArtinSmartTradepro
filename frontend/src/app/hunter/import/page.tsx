'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Upload, Download, FileText, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface ImportSummary {
  created: number
  updated: number
  skipped: number
  duplicates: number
  errors: string[]
}

export default function HunterImportPage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [summary, setSummary] = useState<ImportSummary | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile)
      setSummary(null)
    } else {
      alert('Please select a CSV file')
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile)
      setSummary(null)
    } else {
      alert('Please select a CSV file')
    }
  }

  const handleImport = async () => {
    if (!file) return

    setImporting(true)
    setSummary(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/hunter/leads/import/csv', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Import failed')
      }

      const result = await response.json()
      setSummary(result)
    } catch (error) {
      console.error('Import error:', error)
      alert('Import failed. Please check your CSV file and try again.')
    } finally {
      setImporting(false)
    }
  }

  const handleDownloadTemplate = () => {
    const csvContent = `name,country,website,email,phone,city,industry
Example Company,US,https://example.com,contact@example.com,+1-555-123-4567,New York,Technology
Another Company,CA,https://another.ca,hello@another.ca,+1-416-555-9876,Toronto,Manufacturing`

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'hunter_import_template.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container mx-auto py-6 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="sm" asChild>
          <Link href="/hunter">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Hunter
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Import Leads from CSV</h1>
          <p className="text-gray-600">Upload a CSV file to import multiple leads</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>CSV Format Requirements</CardTitle>
            <CardDescription>Your CSV file must include these columns</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Required Columns:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li><code>name</code> - Company name (required)</li>
                  <li><code>country</code> - Country code (required)</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Optional Columns:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li><code>website</code> - Company website</li>
                  <li><code>email</code> - Contact email</li>
                  <li><code>phone</code> - Contact phone</li>
                  <li><code>city</code> - City</li>
                  <li><code>industry</code> - Industry</li>
                </ul>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleDownloadTemplate}>
                  <Download className="w-4 h-4 mr-2" />
                  Download Template
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* File Upload */}
        <Card>
          <CardHeader>
            <CardTitle>Upload CSV File</CardTitle>
            <CardDescription>Drag and drop or click to select your CSV file</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
              />
              
              {file ? (
                <div className="space-y-4">
                  <FileText className="w-12 h-12 mx-auto text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setFile(null)
                      setSummary(null)
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ''
                      }
                    }}
                  >
                    Remove File
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="w-12 h-12 mx-auto text-gray-400" />
                  <div>
                    <p className="text-gray-600">Drag and drop your CSV file here, or</p>
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      Browse Files
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Import Button */}
        {file && (
          <Card>
            <CardContent className="pt-6">
              <Button
                onClick={handleImport}
                disabled={importing}
                className="w-full"
                size="lg"
              >
                {importing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Import Leads
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {summary && (
          <Card>
            <CardHeader>
              <CardTitle>Import Results</CardTitle>
              <CardDescription>
                {summary.errors.length === 0 ? (
                  <span className="flex items-center text-green-600">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Import completed successfully
                  </span>
                ) : (
                  <span className="flex items-center text-yellow-600">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    Import completed with warnings
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{summary.created}</p>
                  <p className="text-sm text-gray-500">Created</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{summary.updated}</p>
                  <p className="text-sm text-gray-500">Updated</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-yellow-600">{summary.duplicates}</p>
                  <p className="text-sm text-gray-500">Duplicates</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">{summary.skipped}</p>
                  <p className="text-sm text-gray-500">Skipped</p>
                </div>
              </div>
              
              {summary.errors.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-600 mb-2">Errors:</h4>
                  <ul className="text-sm text-red-600 space-y-1 max-h-32 overflow-y-auto">
                    {summary.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="flex gap-2 mt-6">
                <Button onClick={() => router.push('/hunter')}>
                  View Leads
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setFile(null)
                    setSummary(null)
                    if (fileInputRef.current) {
                      fileInputRef.current.value = ''
                    }
                  }}
                >
                  Import Another File
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
