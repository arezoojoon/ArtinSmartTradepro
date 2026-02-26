"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save, Clock, AlertTriangle } from "lucide-react";
import { BASE_URL } from "@/lib/api";

export default function NewFollowUpRulePage() {
    const [name, setName] = useState("");
    const [delay, setDelay] = useState(24); // hours
    const [template, setTemplate] = useState("Hi {{first_name}}, just checking in on this? Let me know if you are still interested.");
    const [trigger, setTrigger] = useState("no_reply");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleCreate = async () => {
        if (!name || !template) return;
        setLoading(true);

        try {
            const token = localStorage.getItem("token");
            const payload = {
                name,
                template_body: template,
                delay_minutes: delay * 60,
                trigger_event: trigger,
                max_attempts: 1 // Default to 1 for MVP
            };

            const res = await fetch(`${BASE_URL}/crm/followups/rules`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                router.push("/crm/followups");
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-4 mb-8">
                <button onClick={() => router.back()} className="text-navy-400 hover:text-white">
                    <ArrowLeft className="h-6 w-6" />
                </button>
                <h1 className="text-2xl font-bold text-white">Create Automation Rule</h1>
            </div>

            <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-8 space-y-8">

                {/* Step 1: Trigger */}
                <div className="space-y-4">
                    <div className="flex items-center gap-3 text-[#f5a623] font-semibold border-b border-[#1e3a5f] pb-2">
                        <div className="bg-navy-800 h-6 w-6 rounded-full flex items-center justify-center text-sm">1</div>
                        Trigger
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => setTrigger("no_reply")}
                            className={`p-4 rounded-lg border text-left transition-all ${trigger === 'no_reply' ? 'bg-gold-500/10 border-gold-500 text-[#f5a623]' : 'bg-navy-950 border-[#1e3a5f] text-navy-400 hover:border-navy-600'}`}
                        >
                            <div className="font-bold mb-1">No Reply</div>
                            <div className="text-xs opacity-70">Trigger when a contact doesn't reply to a message within a set time.</div>
                        </button>
                        <button
                            disabled
                            className="p-4 rounded-lg border bg-navy-950 border-[#1e3a5f] text-navy-600 cursor-not-allowed opacity-50"
                        >
                            <div className="font-bold mb-1">Deal Stage Change</div>
                            <div className="text-xs opacity-70">Under development</div>
                        </button>
                    </div>
                </div>

                {/* Step 2: Timing */}
                <div className="space-y-4">
                    <div className="flex items-center gap-3 text-[#f5a623] font-semibold border-b border-[#1e3a5f] pb-2">
                        <div className="bg-navy-800 h-6 w-6 rounded-full flex items-center justify-center text-sm">2</div>
                        Timing
                    </div>

                    <div className="bg-navy-950 p-6 rounded-lg border border-[#1e3a5f]">
                        <label className="block text-sm font-medium text-navy-300 mb-4">Wait for</label>
                        <div className="flex items-center gap-4">
                            <div className="relative flex-1">
                                <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-navy-400" />
                                <input
                                    type="number"
                                    value={delay}
                                    onChange={(e) => setDelay(parseInt(e.target.value) || 0)}
                                    className="w-full pl-10 pr-4 py-3 bg-[#0e1e33] border border-navy-700 rounded-lg text-white focus:border-gold-400 focus:outline-none"
                                />
                            </div>
                            <span className="text-white font-medium">Hours</span>
                        </div>
                        <p className="text-xs text-navy-400 mt-2 flex items-center gap-2">
                            <AlertTriangle className="h-3 w-3 text-yellow-500" />
                            System will only send if the user has NOT replied during this window.
                        </p>
                    </div>
                </div>

                {/* Step 3: Action */}
                <div className="space-y-4">
                    <div className="flex items-center gap-3 text-[#f5a623] font-semibold border-b border-[#1e3a5f] pb-2">
                        <div className="bg-navy-800 h-6 w-6 rounded-full flex items-center justify-center text-sm">3</div>
                        Action (WhatsApp Message)
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-navy-300 mb-2">Rule Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="e.g. 24h Cold Lead Reviver"
                                className="w-full px-4 py-2.5 bg-navy-950 border border-[#1e3a5f] rounded-lg text-white focus:border-gold-400 focus:outline-none"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-navy-300 mb-2">Message Content</label>
                            <textarea
                                value={template}
                                onChange={(e) => setTemplate(e.target.value)}
                                rows={5}
                                className="w-full px-4 py-3 bg-navy-950 border border-[#1e3a5f] rounded-lg text-white font-mono text-sm focus:border-gold-400 focus:outline-none"
                            />
                            <p className="text-xs text-navy-400 mt-2">Use {'{{first_name}}'} for personalization.</p>
                        </div>
                    </div>
                </div>

                <div className="pt-6 border-t border-[#1e3a5f] flex justify-end">
                    <button
                        onClick={handleCreate}
                        disabled={loading || !name}
                        className="flex items-center gap-2 px-8 py-3 bg-[#f5a623] text-navy-950 rounded-lg font-bold hover:bg-gold-500 transition-colors disabled:opacity-50"
                    >
                        <Save className="h-5 w-5" />
                        {loading ? "Saving..." : "Save & Activate Rule"}
                    </button>
                </div>

            </div>
        </div>
    );
}
