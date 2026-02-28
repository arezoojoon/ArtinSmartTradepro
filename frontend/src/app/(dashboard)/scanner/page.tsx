"use client";

import { useState, useRef, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Camera, Upload, Check, X, Loader2, FileText, Ship,
  Building2, Receipt, ArrowRight, Brain, Sparkles,
  RotateCcw, CheckCircle2, AlertCircle, ImageIcon,
} from "lucide-react";
import api, { BASE_URL } from "@/lib/api";

interface ScanResult {
  document_type: string;
  confidence: number;
  extracted_data: Record<string, any>;
  target_module: string;
  suggested_actions: string[];
  routing_path: string;
}

const docTypeLabels: Record<string, { en: string; icon: any; color: string }> = {
  bill_of_lading: { en: "Bill of Lading", icon: Ship, color: "blue" },
  packing_list: { en: "Packing List", icon: FileText, color: "emerald" },
  commercial_invoice: { en: "Commercial Invoice", icon: Receipt, color: "amber" },
  purchase_order: { en: "Purchase Order", icon: FileText, color: "purple" },
  delivery_note: { en: "Delivery Note", icon: Check, color: "green" },
  contract: { en: "Contract", icon: FileText, color: "slate" },
  insurance: { en: "Insurance", icon: FileText, color: "cyan" },
  customs_declaration: { en: "Customs Declaration", icon: Building2, color: "orange" },
  quality_certificate: { en: "Quality Certificate", icon: CheckCircle2, color: "teal" },
  warehouse_receipt: { en: "Warehouse Receipt", icon: Building2, color: "indigo" },
  unknown: { en: "Unknown Document", icon: FileText, color: "slate" },
};

type Stage = "capture" | "processing" | "result" | "error";

export default function ScannerPage() {
  const [stage, setStage] = useState<Stage>("capture");
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }, []);

  const processDocument = async () => {
    if (!selectedFile) return;

    setStage("processing");
    setError("");

    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${BASE_URL}/documents/upload`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || `Classification failed: ${response.status}`);
      }

      const data = await response.json();
      setResult(data.classification || data);
      setStage("result");
    } catch (err: any) {
      console.error("Scan failed:", err);
      setError(err.message || "Failed to process document");
      setStage("error");
    }
  };

  const reset = () => {
    setStage("capture");
    setPreview(null);
    setSelectedFile(null);
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (cameraInputRef.current) cameraInputRef.current.value = "";
  };

  const confirmAndRoute = async () => {
    if (!result) return;
    // Navigate to the target module
    window.location.href = result.routing_path || "/documents";
  };

  return (
    <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#D4AF37] to-[#B8860B] flex items-center justify-center mx-auto">
          <Camera className="w-7 h-7 text-black" />
        </div>
        <h1 className="text-2xl font-bold text-white">Smart Scanner</h1>
        <p className="text-slate-500 text-sm">
          Point your camera at any document — AI does the rest
        </p>
      </div>

      {/* Capture Stage */}
      {stage === "capture" && (
        <div className="space-y-4 max-w-md mx-auto">
          {/* Preview Area */}
          {preview ? (
            <Card className="bg-slate-900/50 border-slate-700 overflow-hidden">
              <CardContent className="p-0 relative">
                <img
                  src={preview}
                  alt="Document preview"
                  className="w-full max-h-[400px] object-contain"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={reset}
                  className="absolute top-3 right-3 bg-black/50 border-slate-600 text-white hover:bg-black/70"
                >
                  <RotateCcw className="w-4 h-4 mr-1" />
                  Retake
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-900/50 border-slate-700 border-dashed border-2">
              <CardContent className="py-16 text-center space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto">
                  <ImageIcon className="w-8 h-8 text-slate-500" />
                </div>
                <p className="text-slate-400 text-sm">
                  Take a photo or upload a document
                </p>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => cameraInputRef.current?.click()}
              className="h-14 bg-gradient-to-r from-[#D4AF37] to-[#B8860B] text-black font-bold hover:from-[#E5C048] hover:to-[#C89710]"
            >
              <Camera className="w-5 h-5 mr-2" />
              <div className="text-left">
                <p className="text-sm">Camera</p>
              </div>
            </Button>
            <Button
              onClick={() => fileInputRef.current?.click()}
              variant="outline"
              className="h-14 border-slate-700 text-slate-300 hover:border-[#D4AF37]/50 hover:text-white"
            >
              <Upload className="w-5 h-5 mr-2" />
              <div className="text-left">
                <p className="text-sm">Upload</p>
              </div>
            </Button>
          </div>

          {/* Process Button */}
          {preview && (
            <Button
              onClick={processDocument}
              className="w-full h-14 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold text-lg hover:from-emerald-400 hover:to-emerald-500"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Classify & Extract
            </Button>
          )}

          {/* Hidden inputs */}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleFileSelect}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf"
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>
      )}

      {/* Processing Stage */}
      {stage === "processing" && (
        <div className="max-w-md mx-auto">
          <Card className="bg-slate-900/50 border-slate-700">
            <CardContent className="py-16 text-center space-y-6">
              <div className="relative w-20 h-20 mx-auto">
                <div className="w-20 h-20 rounded-full border-2 border-[#D4AF37]/30 flex items-center justify-center">
                  <Brain className="w-10 h-10 text-[#D4AF37] animate-pulse" />
                </div>
                <div className="absolute inset-0 w-20 h-20 rounded-full border-t-2 border-[#D4AF37] animate-spin" />
              </div>
              <div>
                <p className="text-white font-medium">AI is analyzing your document...</p>
              </div>
              <div className="space-y-2 text-xs text-slate-500">
                <p className="flex items-center gap-2 justify-center">
                  <Loader2 className="w-3 h-3 animate-spin" /> Detecting document type...
                </p>
                <p className="flex items-center gap-2 justify-center">
                  <Loader2 className="w-3 h-3 animate-spin" /> Extracting data...
                </p>
                <p className="flex items-center gap-2 justify-center">
                  <Loader2 className="w-3 h-3 animate-spin" /> Routing to module...
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Result Stage — One-Tap Confirm */}
      {stage === "result" && result && (
        <div className="max-w-md mx-auto space-y-4">
          {/* Document Type */}
          <Card className="bg-emerald-500/10 border-emerald-500/30">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                  {(() => {
                    const docInfo = docTypeLabels[result.document_type] || docTypeLabels.unknown;
                    const DocIcon = docInfo.icon;
                    return <DocIcon className="w-6 h-6 text-emerald-400" />;
                  })()}
                </div>
                <div className="flex-1">
                  <p className="text-white font-bold text-lg">
                    {docTypeLabels[result.document_type]?.en || result.document_type}
                  </p>
                </div>
                <div className="text-right">
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    {Math.round(result.confidence * 100)}%
                  </Badge>
                  <p className="text-[10px] text-slate-500 mt-1">confidence</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Extracted Data */}
          {result.extracted_data && Object.keys(result.extracted_data).length > 0 && (
            <Card className="bg-slate-900/50 border-slate-700">
              <CardContent className="p-4 space-y-2">
                <p className="text-xs font-medium text-[#D4AF37] flex items-center gap-1">
                  <Brain className="w-3 h-3" /> Extracted Data
                </p>
                {Object.entries(result.extracted_data).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm py-1 border-b border-slate-800 last:border-0">
                    <span className="text-slate-500 capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-white font-medium">{String(value)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Routing Info */}
          <Card className="bg-slate-900/50 border-slate-700">
            <CardContent className="p-4">
              <p className="text-xs text-slate-500 mb-2">Target Module</p>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-[#D4AF37]/30 text-[#D4AF37]">
                  {result.target_module}
                </Badge>
                <ArrowRight className="w-4 h-4 text-slate-600" />
                <span className="text-sm text-slate-400">{result.routing_path}</span>
              </div>
            </CardContent>
          </Card>

          {/* ONE-TAP CONFIRM — The Magic Button */}
          <Button
            onClick={confirmAndRoute}
            className="w-full h-16 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold text-lg hover:from-emerald-400 hover:to-emerald-500 rounded-2xl shadow-lg shadow-emerald-500/20"
          >
            <CheckCircle2 className="w-6 h-6 mr-3" />
            <div className="text-left">
              <p>Confirm &amp; Save</p>
            </div>
          </Button>

          <Button
            onClick={reset}
            variant="outline"
            className="w-full border-slate-700 text-slate-400 hover:text-white"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Scan Another Document
          </Button>
        </div>
      )}

      {/* Error Stage — Friendly Fallback (Pillar 4) */}
      {stage === "error" && (
        <div className="max-w-md mx-auto">
          <Card className="bg-amber-500/10 border-amber-500/30">
            <CardContent className="py-8 text-center space-y-4">
              <AlertCircle className="w-12 h-12 text-amber-400 mx-auto" />
              <div>
                <p className="text-white font-medium">Could not process this document</p>
              </div>
              {error && <p className="text-xs text-slate-500">{error}</p>}
              <p className="text-sm text-slate-400">
                Please try a clearer photo or upload from your files.
              </p>
              <div className="flex gap-3 justify-center">
                <Button
                  onClick={() => { reset(); cameraInputRef.current?.click(); }}
                  className="bg-[#D4AF37] text-black hover:bg-[#E5C048]"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Retake Photo
                </Button>
                <Button onClick={reset} variant="outline" className="border-slate-700 text-slate-400">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Start Over
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
