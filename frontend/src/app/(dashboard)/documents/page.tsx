"use client";

import React, { useState, useEffect } from 'react';
import { FileText, Brain, Clock, CheckCircle, AlertCircle, Search, Filter, Download, Eye } from 'lucide-react';
import SmartDocumentUpload from '@/components/documents/SmartDocumentUpload';
import { apiFetch } from '@/lib/api';

interface DocumentRecord {
  id: string;
  filename: string;
  document_type: string;
  target_module: string;
  confidence: number;
  classification_data: any;
  created_at: string;
  status: string;
}

interface DocumentHistoryResponse {
  documents: DocumentRecord[];
  total: number;
}

const DocumentManagementPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterModule, setFilterModule] = useState('all');

  const documentTypeLabels: Record<string, string> = {
    'bill_of_lading': 'Bill of Lading',
    'packing_list': 'Packing List',
    'commercial_invoice': 'Commercial Invoice',
    'purchase_order': 'Purchase Order',
    'delivery_note': 'Delivery Note',
    'receipt': 'Receipt',
    'contract': 'Contract',
    'insurance': 'Insurance',
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

  const statusLabels: Record<string, { label: string; color: string }> = {
    'processed': { label: 'Processed', color: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' },
    'routed': { label: 'Routed', color: 'bg-blue-500/20 text-blue-400 border border-blue-500/30' },
    'reclassified': { label: 'Reclassified', color: 'bg-amber-500/20 text-amber-400 border border-amber-500/30' },
    'error': { label: 'Error', color: 'bg-red-500/20 text-red-400 border border-red-500/30' }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await apiFetch<DocumentHistoryResponse>('/documents/classification-history', {
        method: 'GET',
        token: token || undefined
      });
      setDocuments(response.documents);
    } catch (err: any) {
      setError(err.data?.detail || 'Error fetching documents list');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentProcessed = (result: any) => {
    // Refresh the document list
    fetchDocuments();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-emerald-400';
    if (confidence >= 0.6) return 'text-amber-400';
    return 'text-red-400';
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || doc.document_type === filterType;
    const matchesModule = filterModule === 'all' || doc.target_module === filterModule;
    return matchesSearch && matchesType && matchesModule;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-950 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-white/10 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-64 bg-white/5 border border-white/10 rounded-xl"></div>
              <div className="h-64 bg-white/5 border border-white/10 rounded-xl"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy-950 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-8 h-8 text-gold-400" />
            <h1 className="text-3xl font-bold text-white">Smart Document Management</h1>
          </div>
          <p className="text-white/60">Upload and automatically classify documents across the platform</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <SmartDocumentUpload onDocumentProcessed={handleDocumentProcessed} />
          </div>

          {/* Documents List */}
          <div className="lg:col-span-2">
            {/* Filters */}
            <div className="bg-navy-900 rounded-xl shadow-sm border border-white/10 p-6 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-navy-950 border border-white/10 text-white rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500 placeholder-white/40"
                  />
                </div>

                {/* Type Filter */}
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full px-4 py-2 bg-navy-950 border border-white/10 text-white rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
                >
                  <option value="all">All Types</option>
                  {Object.entries(documentTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>

                {/* Module Filter */}
                <select
                  value={filterModule}
                  onChange={(e) => setFilterModule(e.target.value)}
                  className="w-full px-4 py-2 bg-navy-950 border border-white/10 text-white rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
                >
                  <option value="all">All Modules</option>
                  {Object.entries(moduleLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Documents Grid */}
            {error ? (
              <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-400">{error}</p>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-12 bg-navy-900 rounded-xl shadow-sm border border-white/10">
                <FileText className="w-12 h-12 text-white/20 mx-auto mb-4" />
                <p className="text-white/60">No documents found</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredDocuments.map((doc) => (
                  <div key={doc.id} className="bg-navy-900 rounded-xl shadow-sm border border-white/10 p-6 hover:shadow-md hover:border-gold-500/50 transition-all">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-gold-400" />
                        <div className="overflow-hidden">
                          <h3 className="font-medium text-white truncate max-w-[140px]" title={doc.filename}>{doc.filename}</h3>
                          <p className="text-xs text-white/40">
                            {new Date(doc.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusLabels[doc.status]?.color || 'bg-white/10 text-white/80'}`}>
                        {statusLabels[doc.status]?.label || doc.status}
                      </span>
                    </div>

                    {/* Classification Info */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-white/60">Type:</span>
                        <span className="text-sm font-medium text-white/90">
                          {documentTypeLabels[doc.document_type] || doc.document_type}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-white/60">Module:</span>
                        <span className="text-sm font-medium text-white/90">
                          {moduleLabels[doc.target_module] || doc.target_module}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-sm text-white/60">Confidence:</span>
                        <span className={`text-sm font-medium ${getConfidenceColor(doc.confidence)}`}>
                          {(doc.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-4 pt-4 border-t border-white/10">
                      <button
                        onClick={() => {
                          // Navigate to document in target module
                          const routingPath = doc.classification_data?.routing_path;
                          if (routingPath) {
                            window.location.href = routingPath;
                          }
                        }}
                        className="flex-1 flex justify-center items-center gap-2 px-3 py-1.5 text-sm bg-gold-500 text-navy-950 font-medium rounded-lg hover:bg-gold-400 transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                        View
                      </button>

                      <button
                        onClick={() => {
                          // Download document
                          window.open(`/api/documents/download/${doc.id}`);
                        }}
                        className="flex-1 flex justify-center items-center gap-2 px-3 py-1.5 text-sm bg-white/5 text-white font-medium border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentManagementPage;
