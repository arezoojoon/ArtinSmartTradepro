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
      setError(`حجم فایل نباید بیشتر از ${maxSize} مگابایت باشد`);
      return;
    }

    // Validate file type
    if (!acceptedTypes.includes(file.type)) {
      setError('نوع فایل پشتیبانی نمی‌شود');
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
      setError(err.data?.detail || 'خطا در آپلود فایل');
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
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="flex items-center gap-3 mb-6">
        <Brain className="w-6 h-6 text-blue-600" />
        <h3 className="text-lg font-bold text-gray-800">آپلود هوشمند داکیومنت</h3>
      </div>

      {!result ? (
        <div className="space-y-4">
          {/* Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
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
              <Upload className={`w-12 h-12 mx-auto ${dragActive ? 'text-blue-500' : 'text-gray-400'}`} />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  {uploading ? 'در حال پردازش...' : 'فاکتور را اینجا بکشید یا کلیک کنید'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  فرمت‌های مجاز: PDF, JPG, PNG, DOC, DOCX (حداکثر {maxSize} مگابایت)
                </p>
              </div>
            </div>
          </div>

          {/* Description Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              توضیحات (اختیاری)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="توضیحات مربوط به داکیومنت..."
              disabled={uploading}
            />
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {uploading && (
            <div className="flex items-center justify-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              <span className="text-blue-700">در حال تحلیل داکیومنت با هوش مصنوعی...</span>
            </div>
          )}
        </div>
      ) : (
        /* Results Display */
        <div className="space-y-6">
          {/* Success Header */}
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <div className="flex-1">
              <p className="font-medium text-green-800">داکیومنت با موفقیت پردازش شد</p>
              <p className="text-sm text-green-600">{result.message}</p>
            </div>
            <button
              onClick={resetUpload}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              آپلود جدید
            </button>
          </div>

          {/* Classification Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Document Type */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-600 mb-2">نوع داکیومنت</h4>
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-gray-800">
                  {documentTypeLabels[result.classification.document_type] || result.classification.document_type}
                </span>
              </div>
            </div>

            {/* Target Module */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-600 mb-2">بخش مقصد</h4>
              <div className="flex items-center gap-2">
                <span className="text-xl">{getModuleIcon(result.classification.target_module)}</span>
                <span className="font-medium text-gray-800">
                  {moduleLabels[result.classification.target_module] || result.classification.target_module}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-600 mb-2">دقت تشخیص</h4>
              <div className="flex items-center gap-2">
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(result.classification.confidence)}`}>
                  {(result.classification.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Document ID */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-600 mb-2">شناسه داکیومنت</h4>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-gray-800">{result.document_id.slice(0, 8)}...</span>
              </div>
            </div>
          </div>

          {/* Suggested Actions */}
          {result.classification.suggested_actions.length > 0 && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-medium text-blue-800 mb-3">اقدامات پیشنهادی</h4>
              <ul className="space-y-2">
                {result.classification.suggested_actions.map((action, index) => (
                  <li key={index} className="flex items-center gap-2 text-sm text-blue-700">
                    <ArrowRight className="w-4 h-4" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Extracted Data */}
          {result.extracted_data && Object.keys(result.extracted_data).length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-3">داده‌های استخراج شده</h4>
              <div className="space-y-2">
                {Object.entries(result.extracted_data).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                    <span className="text-sm font-medium text-gray-600">{key}:</span>
                    <span className="text-sm text-gray-800">
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Navigation Button */}
          <div className="flex justify-center">
            <button
              onClick={() => {
                // Navigate to the target module
                window.location.href = result.classification.routing_path;
              }}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Eye className="w-5 h-5" />
              مشاهده در {moduleLabels[result.classification.target_module]}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartDocumentUpload;
