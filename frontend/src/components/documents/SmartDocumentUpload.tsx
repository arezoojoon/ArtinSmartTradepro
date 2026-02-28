"use client";

import React, { useState, useCallback } from 'react';
import { Upload, FileText, Brain, CheckCircle, AlertCircle, Loader2, Eye, ArrowRight } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface DocumentClassification {
  document_type: string;
  target_module: string;
  confidence: number;
  routing_path: string;
  suggested_actions: string[];
}

interface UploadResult {
  success: boolean;
  document_id: string;
  classification: DocumentClassification;
  extracted_data: any;
  message: string;
}

interface SmartDocumentUploadProps {
  onDocumentProcessed?: (result: UploadResult) => void;
  acceptedTypes?: string[];
  maxSize?: number; // in MB
}

const SmartDocumentUpload: React.FC<SmartDocumentUploadProps> = ({
  onDocumentProcessed,
  acceptedTypes = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ],
  maxSize = 10
}) => {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [description, setDescription] = useState('');

  const documentTypeLabels: Record<string, string> = {
    'bill_of_lading': 'Bill of Lading',
    'packing_list': 'Packing List',
    'commercial_invoice': 'Commercial Invoice',
    'purchase_order': 'Purchase Order',
    'delivery_note': 'Delivery Note',
    'receipt': 'Receipt',
    'contract': 'Contract',
    'insurance': 'Insurance Policy',
    'customs_declaration': 'Customs Declaration',
    'quality_certificate': 'Quality Certificate',
    'warehouse_receipt': 'Warehouse Receipt',
    'unknown': 'Unknown'
  };

  const moduleLabels: Record<string, string> = {
    'logistics': 'Logistics',
    'crm': 'CRM',
    'billing': 'Billing',
    'procurement': 'Procurement',
    'compliance': 'Compliance',
    'warehouse': 'Warehouse'
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getModuleIcon = (module: string) => {
    switch (module) {
      case 'logistics': return '🚚';
      case 'crm': return '👥';
      case 'billing': return '💰';
      case 'procurement': return '🛒';
      case 'compliance': return '📋';
      case 'warehouse': return '📦';
      default: return '📄';
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileUpload = async (file: File) => {
    setError(null);
    setResult(null);

    // Validate file size
    if (file.size > maxSize * 1024 * 1024) {
      setError(`File size should not exceed ${maxSize} MB.`);
      return;
    }

    // Validate file type
    if (!acceptedTypes.includes(file.type)) {
      setError('Unsupported file type.');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', description);

      const token = localStorage.getItem('token');
      const response = await apiFetch<UploadResult>('/documents/upload', {
        method: 'POST',
        token: token || undefined,
        body: formData,
        headers: {
          // Don't set Content-Type for FormData - browser sets it with boundary
        },
      });

      setResult(response);
      onDocumentProcessed?.(response);
    } catch (err: any) {
      setError(err.data?.detail || 'Error uploading file.');
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFileUpload(files[0]);
    }
  };

  const resetUpload = () => {
    setResult(null);
    setError(null);
    setDescription('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-navy-900 rounded-xl shadow-[0_4px_24px_rgba(251,191,36,0.1)] border border-[#ffffff10]">
      <div className="flex items-center gap-3 mb-6">
        <Brain className="w-6 h-6 text-gold-400" />
        <h3 className="text-lg font-bold text-white">Smart Document Upload</h3>
      </div>

      {!result ? (
        <div className="space-y-4">
          {/* Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragActive
              ? 'border-gold-500 bg-gold-500/10'
              : 'border-white/20 hover:border-gold-400/50 hover:bg-white/5'
              }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileSelect}
              accept={acceptedTypes.join(',')}
              disabled={uploading}
            />

            <div className="space-y-4">
              <Upload className={`w-12 h-12 mx-auto ${dragActive ? 'text-gold-400' : 'text-slate-400'}`} />
              <div>
                <p className="text-lg font-medium text-slate-200">
                  {uploading ? 'Processing Document...' : 'Drag & Drop Document Here or Click to Browse'}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  Supported formats: PDF, JPG, PNG, DOC, DOCX (Max {maxSize}MB)
                </p>
              </div>
            </div>
          </div>

          {/* Description Field */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-navy-800/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-gold-500 focus:border-gold-500 placeholder-slate-500"
              rows={3}
              placeholder="Add context or notes about this document..."
              disabled={uploading}
            />
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-900/30 border border-red-500/50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {uploading && (
            <div className="flex items-center justify-center gap-3 p-4 bg-navy-800 border border-gold-500/30 rounded-lg">
              <Loader2 className="w-5 h-5 text-gold-400 animate-spin" />
              <span className="text-gold-100 font-medium">Analyzing document with AI Brain...</span>
            </div>
          )}
        </div>
      ) : (
        /* Results Display */
        <div className="space-y-6">
          {/* Success Header */}
          <div className="flex items-center gap-3 p-4 bg-emerald-900/30 border border-emerald-500/50 rounded-lg">
            <CheckCircle className="w-6 h-6 text-emerald-400" />
            <div className="flex-1">
              <p className="font-medium text-emerald-200">Document Processed Successfully</p>
              <p className="text-sm text-emerald-400/80">{result.message}</p>
            </div>
            <button
              onClick={resetUpload}
              className="px-3 py-1.5 text-sm bg-navy-800 text-slate-200 border border-white/10 rounded-lg hover:bg-navy-700 transition-colors"
            >
              Upload Another
            </button>
          </div>

          {/* Classification Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Document Type */}
            <div className="p-4 bg-navy-950/50 border border-white/5 rounded-lg">
              <h4 className="text-sm font-medium text-slate-400 mb-2">Document Type</h4>
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gold-400" />
                <span className="font-medium text-white">
                  {documentTypeLabels[result.classification.document_type] || result.classification.document_type}
                </span>
              </div>
            </div>

            {/* Target Module */}
            <div className="p-4 bg-navy-950/50 border border-white/5 rounded-lg">
              <h4 className="text-sm font-medium text-slate-400 mb-2">Target Module</h4>
              <div className="flex items-center gap-2">
                <span className="text-xl">{getModuleIcon(result.classification.target_module)}</span>
                <span className="font-medium text-white">
                  {moduleLabels[result.classification.target_module] || result.classification.target_module}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div className="p-4 bg-navy-950/50 border border-white/5 rounded-lg">
              <h4 className="text-sm font-medium text-slate-400 mb-2">AI Confidence</h4>
              <div className="flex items-center gap-2">
                <div className={`px-2.5 py-1 rounded-full text-xs font-bold ${result.classification.confidence >= 0.8 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                  result.classification.confidence >= 0.6 ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                    'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}>
                  {(result.classification.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Document ID */}
            <div className="p-4 bg-navy-950/50 border border-white/5 rounded-lg">
              <h4 className="text-sm font-medium text-slate-400 mb-2">Document ID</h4>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-slate-300">{result.document_id.slice(0, 8)}...</span>
              </div>
            </div>
          </div>

          {/* Suggested Actions */}
          {result.classification.suggested_actions.length > 0 && (
            <div className="p-4 bg-navy-800/80 border border-gold-500/30 rounded-lg">
              <h4 className="text-sm font-medium text-gold-400 mb-3 flex items-center gap-2">
                <Brain className="w-4 h-4" /> Recommended AI Actions
              </h4>
              <ul className="space-y-2">
                {result.classification.suggested_actions.map((action, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-slate-200">
                    <ArrowRight className="w-4 h-4 text-gold-500/70" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Extracted Data */}
          {result.extracted_data && Object.keys(result.extracted_data).length > 0 && (
            <div className="p-4 bg-navy-950/80 border border-white/10 rounded-lg">
              <h4 className="text-sm font-medium text-slate-300 mb-3">Extracted Metadata</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                {Object.entries(result.extracted_data).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center py-2 border-b border-white/5 last:border-b-0">
                    <span className="text-sm font-medium text-slate-400 capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-sm text-white font-medium">
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Button */}
          <div className="flex justify-center pt-2">
            <button
              onClick={() => {
                window.location.href = result.classification.routing_path;
              }}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-gold-500 to-gold-600 text-navy-950 font-bold rounded-lg hover:from-gold-400 hover:to-gold-500 transition-all shadow-lg hover:shadow-[0_0_15px_rgba(251,191,36,0.4)]"
            >
              <Eye className="w-5 h-5" />
              View in {moduleLabels[result.classification.target_module]} Module
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartDocumentUpload;
