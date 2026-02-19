"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BASE_URL } from "@/lib/api";
import { Upload, FileDown, CheckCircle } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export default function LeadImportPage() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState<{ imported: number; failed: number } | null>(null);
    const { toast } = useToast();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const token = localStorage.getItem("token"); // Assuming token is stored here, check AuthContext if needed
            const res = await fetch(`${BASE_URL}/leads/import/csv`, {
                method: "POST",
                headers: {
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: formData,
            });

            if (!res.ok) throw new Error("Upload failed");

            const data = await res.json();
            setStats(data);
            toast({ title: "Import Successful", description: `Imported ${data.imported} leads.` });
        } catch (error) {
            toast({ title: "Import Failed", description: "Please check your CSV format.", variant: "destructive" });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 p-6">
            <h1 className="text-3xl font-bold text-white">Import Leads</h1>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-navy-900 border-navy-800 text-white">
                    <CardHeader>
                        <CardTitle>1. Upload CSV</CardTitle>
                        <CardDescription>Upload leads from other sources.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="border-2 border-dashed border-navy-700 rounded-lg p-10 flex flex-col items-center justify-center text-center hover:border-gold-500/50 transition-colors">
                            <Upload className="h-10 w-10 text-gray-500 mb-4" />
                            <Label htmlFor="file-upload" className="cursor-pointer">
                                <span className="text-gold-400 font-semibold hover:underline">Click to upload</span>
                                <span className="text-gray-400"> or drag and drop</span>
                            </Label>
                            <Input id="file-upload" type="file" className="hidden" accept=".csv" onChange={handleFileChange} />
                            {file && <p className="mt-2 text-sm text-green-400">{file.name}</p>}
                        </div>
                        <Button
                            className="w-full bg-gold-500 text-navy-900 font-bold hover:bg-gold-600"
                            disabled={!file || loading}
                            onClick={handleUpload}
                        >
                            {loading ? "Importing..." : "Start Import"}
                        </Button>
                    </CardContent>
                </Card>

                <Card className="bg-navy-800 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle>2. CSV Guidelines</CardTitle>
                        <CardDescription>Follow the format strictly.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4 text-sm text-gray-300">
                        <p>Columns required:</p>
                        <code className="block bg-black/30 p-2 rounded text-xs font-mono text-gold-400">
                            company_name, email, phone, city, country
                        </code>
                        <div className="pt-4">
                            <Button variant="outline" className="w-full border-navy-600 text-gray-300 hover:bg-navy-700">
                                <FileDown className="mr-2 h-4 w-4" />
                                Download Template
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {stats && (
                <Card className="bg-green-900/20 border-green-900 text-white">
                    <CardContent className="flex items-center p-6 space-x-4">
                        <CheckCircle className="h-8 w-8 text-green-500" />
                        <div>
                            <h3 className="text-lg font-bold text-green-400">Import Complete</h3>
                            <p>Successfully imported <strong>{stats.imported}</strong> leads. {stats.failed > 0 && <span className="text-red-400">({stats.failed} failed)</span>}</p>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
