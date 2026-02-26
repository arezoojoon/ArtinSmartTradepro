"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CalendarClock, Wand2, Send, Loader2 } from "lucide-react";
import { BASE_URL } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function SmartFollowUpPage() {
    const router = useRouter();
    const params = useParams();
    const contactId = (params as any)?.id as string;

    const [objective, setObjective] = useState("first_contact");
    const [contextNote, setContextNote] = useState("");

    const [draftLoading, setDraftLoading] = useState(false);
    const [draftError, setDraftError] = useState<string | null>(null);
    const [language, setLanguage] = useState<string>("en");
    const [messageText, setMessageText] = useState<string>("");

    const [scheduledAt, setScheduledAt] = useState<string>("");
    const [scheduleLoading, setScheduleLoading] = useState(false);
    const [scheduleError, setScheduleError] = useState<string | null>(null);
    const [scheduleDone, setScheduleDone] = useState(false);

    const minDateTimeLocal = useMemo(() => {
        const d = new Date();
        d.setMinutes(d.getMinutes() + 1);
        const pad = (n: number) => String(n).padStart(2, "0");
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }, []);

    useEffect(() => {
        setDraftError(null);
        setScheduleError(null);
        setScheduleDone(false);
    }, [contactId]);

    const fetchDraft = async () => {
        if (!contactId) return;
        setDraftLoading(true);
        setDraftError(null);
        setScheduleDone(false);

        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${BASE_URL}/followups/draft`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    contact_id: contactId,
                    objective,
                    context_note: contextNote || undefined,
                }),
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.detail || data?.error?.message || "Failed to generate draft");
            }

            setLanguage(data.language || "en");
            setMessageText(data.message_text || "");
        } catch (e: any) {
            setDraftError(e?.message || "Failed to generate draft");
        } finally {
            setDraftLoading(false);
        }
    };

    const schedule = async () => {
        if (!contactId) return;
        if (!messageText.trim()) {
            setScheduleError("Message text is required");
            return;
        }
        if (!scheduledAt) {
            setScheduleError("Scheduled time is required");
            return;
        }

        setScheduleLoading(true);
        setScheduleError(null);

        try {
            const token = localStorage.getItem("token");
            const iso = new Date(scheduledAt).toISOString();

            const res = await fetch(`${BASE_URL}/followups/schedule`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    contact_id: contactId,
                    scheduled_at: iso,
                    message_text: messageText,
                }),
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data?.detail || data?.error?.message || "Failed to schedule follow-up");
            }

            setScheduleDone(true);
        } catch (e: any) {
            setScheduleError(e?.message || "Failed to schedule follow-up");
        } finally {
            setScheduleLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={() => router.back()} className="gap-2">
                    <ArrowLeft className="h-4 w-4" />
                    Back
                </Button>
                <div className="ml-auto text-xs text-slate-500">Language: {language}</div>
            </div>

            <Card className="bg-white border-slate-200">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-slate-900">
                        <Wand2 className="h-5 w-5 text-indigo-600" />
                        Smart Follow-up
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-5">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <div className="text-xs font-semibold text-slate-600 mb-2">Objective</div>
                            <Input
                                value={objective}
                                onChange={(e) => setObjective(e.target.value)}
                                placeholder="first_contact"
                            />
                        </div>
                        <div>
                            <div className="text-xs font-semibold text-slate-600 mb-2">Send at</div>
                            <div className="flex items-center gap-2">
                                <CalendarClock className="h-4 w-4 text-slate-400" />
                                <input
                                    type="datetime-local"
                                    min={minDateTimeLocal}
                                    value={scheduledAt}
                                    onChange={(e) => setScheduledAt(e.target.value)}
                                    className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <div className="text-xs font-semibold text-slate-600 mb-2">Optional context note</div>
                        <Input
                            value={contextNote}
                            onChange={(e) => setContextNote(e.target.value)}
                            placeholder="e.g. Met at Gulfood, interested in cocoa powder"
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Button onClick={fetchDraft} disabled={draftLoading} className="bg-indigo-600 hover:bg-indigo-700 text-white">
                            {draftLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Wand2 className="h-4 w-4 mr-2" />}
                            Generate Draft
                        </Button>
                        {draftError && <div className="text-sm text-rose-600">{draftError}</div>}
                    </div>

                    <div>
                        <div className="text-xs font-semibold text-slate-600 mb-2">Message (editable)</div>
                        <Textarea
                            value={messageText}
                            onChange={(e) => setMessageText(e.target.value)}
                            rows={6}
                            className="font-mono"
                            placeholder="Click 'Generate Draft' or write your own message."
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        <Button onClick={schedule} disabled={scheduleLoading} className="bg-emerald-600 hover:bg-emerald-700 text-white">
                            {scheduleLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
                            Schedule
                        </Button>
                        {scheduleDone && <div className="text-sm text-emerald-700">Scheduled successfully.</div>}
                        {scheduleError && <div className="text-sm text-rose-600">{scheduleError}</div>}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
