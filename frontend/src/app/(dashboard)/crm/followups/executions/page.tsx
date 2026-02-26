"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Clock, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { BASE_URL } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";

export default function ExecutionsPage() {
    const [executions, setExecutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        fetchExecutions();
        const interval = setInterval(fetchExecutions, 10000); // Live poll
        return () => clearInterval(interval);
    }, []);

    const fetchExecutions = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${BASE_URL}/crm/followups/executions`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setExecutions(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'scheduled': return <span className="flex items-center gap-1 text-blue-400 bg-blue-400/10 px-2 py-1 rounded text-xs"><Clock className="h-3 w-3" /> Scheduled</span>;
            case 'sent': return <span className="flex items-center gap-1 text-green-400 bg-green-400/10 px-2 py-1 rounded text-xs"><CheckCircle className="h-3 w-3" /> Sent</span>;
            case 'cancelled': return <span className="flex items-center gap-1 text-gray-400 bg-gray-400/10 px-2 py-1 rounded text-xs"><XCircle className="h-3 w-3" /> Cancelled</span>;
            case 'failed': return <span className="flex items-center gap-1 text-red-400 bg-red-400/10 px-2 py-1 rounded text-xs"><AlertTriangle className="h-3 w-3" /> Failed</span>;
            default: return status;
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex items-center gap-4 mb-6">
                <button onClick={() => router.back()} className="text-navy-400 hover:text-white">
                    <ArrowLeft className="h-6 w-6" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-white">Execution Log</h1>
                    <p className="text-sm text-navy-400">Audit trail of all automated follow-up actions</p>
                </div>
            </div>

            <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-navy-950 text-navy-400 border-b border-[#1e3a5f]">
                        <tr>
                            <th className="px-6 py-4 font-medium">Scheduled / Sent</th>
                            <th className="px-6 py-4 font-medium">Status</th>
                            <th className="px-6 py-4 font-medium">Details</th>
                            <th className="px-6 py-4 font-medium">Attempt</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-800">
                        {loading ? (
                            <tr><td colSpan={4} className="px-6 py-8 text-center text-navy-500">Loading...</td></tr>
                        ) : executions.length === 0 ? (
                            <tr><td colSpan={4} className="px-6 py-8 text-center text-navy-500">No executions found</td></tr>
                        ) : (
                            executions.map((exe: any) => (
                                <tr key={exe.id} className="hover:bg-navy-800/50 transition-colors">
                                    <td className="px-6 py-4 text-white">
                                        <div>{formatDistanceToNow(new Date(exe.scheduled_at), { addSuffix: true })}</div>
                                        {exe.sent_at && <div className="text-xs text-navy-400">Sent: {new Date(exe.sent_at).toLocaleTimeString()}</div>}
                                    </td>
                                    <td className="px-6 py-4">
                                        {getStatusBadge(exe.status)}
                                        {exe.error && <div className="text-xs text-red-400 mt-1">{exe.error}</div>}
                                    </td>
                                    <td className="px-6 py-4 text-navy-300">
                                        <div className="text-xs font-mono opacity-50 mb-1">{exe.id.split('-')[0]}</div>
                                        Contact ID: {exe.contact_id.split('-')[0]}...
                                    </td>
                                    <td className="px-6 py-4 text-white font-mono">
                                        #{exe.attempt}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
