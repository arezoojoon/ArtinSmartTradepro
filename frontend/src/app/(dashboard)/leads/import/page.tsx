"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, CheckCircle2, AlertTriangle, Loader2, X, Download, Users, FileSpreadsheet } from "lucide-react";
import api from "@/lib/api";

interface ImportResult {
    imported: number;
    skipped: number;
    errors: string[];
    total: number;
}

export default function ImportLeadsPage() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<ImportResult | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    const handleFile = (f: File) => {
        if (f.name.endsWith(".csv") || f.name.endsWith(".xlsx") || f.name.endsWith(".xls")) {
            setFile(f);
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await api.post("/leads/import/csv", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setResult(res.data);
        } catch (e: any) {
            setResult({ imported: 0, skipped: 0, errors: [e?.response?.data?.detail || "Upload failed"], total: 0 });
        }
        finally { setUploading(false); }
    };

    const downloadTemplate = () => {
        const csv = "company_name,contact_name,email,phone,country,source\nAcme Corp,John Doe,john@acme.com,+1234567890,US,Website\n";
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = "leads_template.csv"; a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[900px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Upload className="h-6 w-6 text-purple-400" /> Import Leads
                    </h1>
                    <p className="text-white/50 text-sm">Upload CSV files to bulk-import leads into CRM</p>
                </div>
                <Button onClick={downloadTemplate} variant="outline" className="border-white/20 text-white">
                    <Download className="h-4 w-4 mr-2" /> Download Template
                </Button>
            </div>

            {/* Upload Area */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardContent className="p-6">
                    <div
                        className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${dragOver ? "border-purple-400 bg-purple-400/5" : "border-white/10 hover:border-white/20"}`}
                        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={e => { e.preventDefault(); setDragOver(false); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
                        onClick={() => fileRef.current?.click()}
                    >
                        <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />
                        {file ? (
                            <div className="space-y-3">
                                <FileSpreadsheet className="h-12 w-12 mx-auto text-purple-400" />
                                <div>
                                    <p className="text-white font-medium">{file.name}</p>
                                    <p className="text-white/40 text-xs mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                                <Button size="sm" variant="ghost" className="text-white/40" onClick={e => { e.stopPropagation(); setFile(null); setResult(null); }}>
                                    <X className="h-3 w-3 mr-1" /> Remove
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <Upload className="h-12 w-12 mx-auto text-white/20" />
                                <div>
                                    <p className="text-white/60 font-medium">Drop your CSV file here</p>
                                    <p className="text-white/30 text-xs mt-1">or click to browse · Supports .csv, .xlsx, .xls</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {file && !result && (
                        <Button onClick={handleUpload} disabled={uploading} className="w-full mt-4 bg-purple-600 text-white hover:bg-purple-700">
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Upload className="h-4 w-4 mr-2" />}
                            {uploading ? "Importing..." : "Import Leads"}
                        </Button>
                    )}
                </CardContent>
            </Card>

            {/* Result */}
            {result && (
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            {result.imported > 0 ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <AlertTriangle className="h-5 w-5 text-amber-400" />}
                            Import Results
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="p-3 bg-emerald-500/10 rounded-lg text-center">
                                <p className="text-white/40 text-[10px] uppercase">Imported</p>
                                <p className="text-emerald-400 font-bold text-2xl">{result.imported}</p>
                            </div>
                            <div className="p-3 bg-amber-500/10 rounded-lg text-center">
                                <p className="text-white/40 text-[10px] uppercase">Skipped</p>
                                <p className="text-amber-400 font-bold text-2xl">{result.skipped}</p>
                            </div>
                            <div className="p-3 bg-blue-500/10 rounded-lg text-center">
                                <p className="text-white/40 text-[10px] uppercase">Total Rows</p>
                                <p className="text-blue-400 font-bold text-2xl">{result.total}</p>
                            </div>
                        </div>
                        {result.errors.length > 0 && (
                            <div className="p-3 bg-rose-500/10 rounded-lg border border-rose-500/20">
                                <p className="text-rose-400 text-xs font-medium mb-2">Errors:</p>
                                {result.errors.slice(0, 5).map((err, i) => <p key={i} className="text-white/50 text-xs">• {err}</p>)}
                                {result.errors.length > 5 && <p className="text-white/30 text-xs mt-1">...and {result.errors.length - 5} more</p>}
                            </div>
                        )}
                        <Button onClick={() => { setFile(null); setResult(null); }} className="w-full mt-4 bg-[#f5a623] text-black hover:bg-[#e09000]">
                            Import More
                        </Button>
                    </CardContent>
                </Card>
            )}

            {/* Instructions */}
            <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                <CardHeader><CardTitle className="text-white text-sm">CSV Format</CardTitle></CardHeader>
                <CardContent>
                    <p className="text-white/40 text-xs mb-3">Your CSV should include these columns (first row as headers):</p>
                    <div className="flex flex-wrap gap-2">
                        {["company_name", "contact_name", "email", "phone", "country", "source"].map(col => (
                            <Badge key={col} className="bg-white/5 text-white/60 font-mono text-[10px]">{col}</Badge>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
