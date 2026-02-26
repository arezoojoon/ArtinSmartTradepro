"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
    ArrowLeft, Upload, FileSpreadsheet, FileText,
    CheckCircle2, AlertCircle, Loader2, Download
} from "lucide-react";
import { BASE_URL } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface ImportResult {
    created: number;
    skipped: number;
    total_rows: number;
    errors: { row: number; error: string }[];
}

export default function BulkImportPage() {
    const router = useRouter();

    const [file, setFile] = useState<File | null>(null);
    const [eventName, setEventName] = useState("");
    const [note, setNote] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<ImportResult | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0] || null;
        if (f) {
            const ext = f.name.toLowerCase();
            if (!ext.endsWith(".csv") && !ext.endsWith(".xlsx")) {
                setError("Only .csv and .xlsx files are supported.");
                setFile(null);
                return;
            }
        }
        setFile(f);
        setError(null);
        setResult(null);
    };

    const handleImport = async () => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const token = localStorage.getItem("token");
            const formData = new FormData();
            formData.append("file", file);
            if (eventName.trim()) formData.append("event_name", eventName.trim());
            if (note.trim()) formData.append("note", note.trim());

            const res = await fetch(`${BASE_URL}/crm/contacts/bulk-import`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.detail || "Import failed");
            }

            setResult(data);
        } catch (e: any) {
            setError(e?.message || "Import failed");
        } finally {
            setLoading(false);
        }
    };

    const downloadTemplate = () => {
        const csv = "first_name,last_name,email,phone,position,linkedin_url,preferred_language\nJohn,Doe,john@example.com,+971501234567,CEO,,en\n";
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "contacts_template.csv";
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={() => router.push("/crm/contacts")} className="gap-2">
                    <ArrowLeft className="h-4 w-4" />
                    Back to Contacts
                </Button>
            </div>

            <Card className="bg-white/5 border-white/10 shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                        <Upload className="h-5 w-5 text-indigo-600" />
                        Bulk Import Contacts
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Template download */}
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-semibold text-slate-200">Download Template</p>
                            <p className="text-xs text-slate-500 mt-0.5">
                                Required column: <code className="bg-white/10 px-1 rounded text-amber-400">first_name</code>.
                                Optional: last_name, email, phone, position, linkedin_url, preferred_language
                            </p>
                        </div>
                        <Button variant="outline" size="sm" onClick={downloadTemplate} className="gap-1.5">
                            <Download className="h-3.5 w-3.5" />
                            CSV Template
                        </Button>
                    </div>

                    {/* File input */}
                    <div>
                        <div className="text-xs font-semibold text-slate-300 mb-2">Upload File (.csv or .xlsx)</div>
                        <div className="flex items-center gap-3">
                            <label className="flex-1 cursor-pointer">
                                <div className="border-2 border-dashed border-white/20 hover:border-amber-400/50 transition-colors rounded-lg p-6 text-center">
                                    {file ? (
                                        <div className="flex items-center justify-center gap-2">
                                            {file.name.endsWith(".xlsx") ? (
                                                <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
                                            ) : (
                                                <FileText className="h-5 w-5 text-blue-600" />
                                            )}
                                            <span className="text-sm font-medium text-slate-200">{file.name}</span>
                                            <Badge variant="outline" className="text-[10px]">
                                                {(file.size / 1024).toFixed(1)} KB
                                            </Badge>
                                        </div>
                                    ) : (
                                        <div className="text-slate-400">
                                            <Upload className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                            <p className="text-sm">Click to select a file or drag & drop</p>
                                            <p className="text-xs mt-1">Supports CSV and Excel (XLSX)</p>
                                        </div>
                                    )}
                                </div>
                                <input
                                    type="file"
                                    accept=".csv,.xlsx"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                            </label>
                        </div>
                    </div>

                    {/* Event name + Note */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <div className="text-xs font-semibold text-slate-300 mb-2">Event Name (optional)</div>
                            <Input
                                value={eventName}
                                onChange={(e) => setEventName(e.target.value)}
                                placeholder="e.g. Gulfood 2025"
                            />
                            <p className="text-[10px] text-slate-400 mt-1">Creates an &quot;event:...&quot; tag on each contact</p>
                        </div>
                        <div>
                            <div className="text-xs font-semibold text-slate-300 mb-2">Note (optional)</div>
                            <Input
                                value={note}
                                onChange={(e) => setNote(e.target.value)}
                                placeholder="e.g. Collected at booth #42"
                            />
                            <p className="text-[10px] text-slate-400 mt-1">Adds this note to every imported contact</p>
                        </div>
                    </div>

                    {/* Import button */}
                    <div className="flex items-center gap-3">
                        <Button
                            onClick={handleImport}
                            disabled={loading || !file}
                            className="bg-amber-500 hover:bg-amber-600 text-black font-bold"
                        >
                            {loading ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <Upload className="h-4 w-4 mr-2" />
                            )}
                            Import Contacts
                        </Button>
                        {error && (
                            <div className="flex items-center gap-1 text-sm text-rose-600">
                                <AlertCircle className="h-4 w-4" />
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Result */}
                    {result && (
                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4 space-y-2">
                            <div className="flex items-center gap-2 text-emerald-700 font-semibold">
                                <CheckCircle2 className="h-5 w-5" />
                                Import Complete
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-center">
                                <div>
                                    <div className="text-2xl font-bold text-emerald-700">{result.created}</div>
                                    <div className="text-xs text-slate-500">Created</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-amber-600">{result.skipped}</div>
                                    <div className="text-xs text-slate-500">Skipped</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-slate-600">{result.total_rows}</div>
                                    <div className="text-xs text-slate-500">Total Rows</div>
                                </div>
                            </div>
                            {result.errors.length > 0 && (
                                <div className="mt-2">
                                    <p className="text-xs font-semibold text-slate-600 mb-1">Errors:</p>
                                    <div className="max-h-32 overflow-y-auto space-y-1">
                                        {result.errors.map((err, i) => (
                                            <div key={i} className="text-xs text-rose-600 bg-rose-50 px-2 py-1 rounded">
                                                Row {err.row}: {err.error}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            <div className="pt-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => router.push("/crm/contacts")}
                                >
                                    View Contacts
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
