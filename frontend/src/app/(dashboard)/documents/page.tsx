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
    'bill_of_lading': 'بارنامه',
    'packing_list': 'لیست بسته‌بندی',
    'commercial_invoice': 'فاکتور تجاری',
    'purchase_order': 'سفارش خرید',
    'delivery_note': 'یادداشت تحویل',
    'receipt': 'رسید',
    'contract': 'قرارداد',
    'insurance': 'بیمه‌نامه',
    'customs_declaration': 'اعلامیه گمرکی',
    'quality_certificate': 'گواهی کیفیت',
    'warehouse_receipt': 'رسید انبار',
    'unknown': 'ناشناخته'
  };

  const moduleLabels: Record<string, string> = {
    'logistics': 'لجستیک',
    'crm': 'CRM',
    'billing': 'صورت‌حساب',
    'procurement': 'خرید',
    'compliance': 'انطباق',
    'warehouse': 'انبار'
  };

  const statusLabels: Record<string, { label: string; color: string }> = {
    'processed': { label: 'پردازش شده', color: 'bg-green-100 text-green-800' },
    'routed': { label: 'مسیریابی شده', color: 'bg-blue-100 text-blue-800' },
    'reclassified': { label: 'تغییر طبقه‌بندی', color: 'bg-yellow-100 text-yellow-800' },
    'error': { label: 'خطا', color: 'bg-red-100 text-red-800' }
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
      setError(err.data?.detail || 'خطا در دریافت لیست داکیومنت‌ها');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentProcessed = (result: any) => {
    // Refresh the document list
    fetchDocuments();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || doc.document_type === filterType;
    const matchesModule = filterModule === 'all' || doc.target_module === filterModule;
    return matchesSearch && matchesType && matchesModule;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-64 bg-gray-200 rounded-xl"></div>
              <div className="h-64 bg-gray-200 rounded-xl"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-800">مدیریت هوشمند داکیومنت</h1>
          </div>
          <p className="text-gray-600">آپلود و طبقه‌بندی خودکار داکیومنت‌ها در بخش‌های مختلف پلتفرم</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <SmartDocumentUpload onDocumentProcessed={handleDocumentProcessed} />
          </div>

          {/* Documents List */}
          <div className="lg:col-span-2">
            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="جستجوی داکیومنت..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pr-10 pl-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Type Filter */}
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">همه انواع</option>
                  {Object.entries(documentTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>

                {/* Module Filter */}
                <select
                  value={filterModule}
                  onChange={(e) => setFilterModule(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">همه بخش‌ها</option>
                  {Object.entries(moduleLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Documents Grid */}
            {error ? (
              <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-700">{error}</p>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">هیچ داکیومنتی یافت نشد</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredDocuments.map((doc) => (
                  <div key={doc.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <div>
                          <h3 className="font-medium text-gray-800 truncate">{doc.filename}</h3>
                          <p className="text-xs text-gray-500">
                            {new Date(doc.created_at).toLocaleDateString('fa-IR')}
                          </p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusLabels[doc.status]?.color || 'bg-gray-100 text-gray-800'}`}>
                        {statusLabels[doc.status]?.label || doc.status}
                      </span>
                    </div>

                    {/* Classification Info */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">نوع:</span>
                        <span className="text-sm font-medium text-gray-800">
                          {documentTypeLabels[doc.document_type] || doc.document_type}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">بخش:</span>
                        <span className="text-sm font-medium text-gray-800">
                          {moduleLabels[doc.target_module] || doc.target_module}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">دقت:</span>
                        <span className={`text-sm font-medium ${getConfidenceColor(doc.confidence)}`}>
                          {(doc.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-4 pt-4 border-t border-gray-200">
                      <button
                        onClick={() => {
                          // Navigate to document in target module
                          const routingPath = doc.classification_data?.routing_path;
                          if (routingPath) {
                            window.location.href = routingPath;
                          }
                        }}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                        مشاهده
                      </button>
                      
                      <button
                        onClick={() => {
                          // Download document
                          window.open(`/api/documents/download/${doc.id}`);
                        }}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        دانلود
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
