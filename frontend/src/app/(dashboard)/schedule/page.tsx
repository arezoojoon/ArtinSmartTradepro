"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Calendar, Plus, Clock, User, Video, MapPin, X, Loader2, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/lib/api";

interface Appointment {
    id: string;
    guest_name: string;
    guest_email?: string;
    start_time: string;
    end_time: string;
    meeting_type: string;
    location?: string;
    notes?: string;
    status: string;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function SchedulePage() {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [currentMonth, setCurrentMonth] = useState(new Date());
    const [form, setForm] = useState({ guest_name: "", guest_email: "", start_time: "", end_time: "", meeting_type: "online", location: "", notes: "" });
    const [saving, setSaving] = useState(false);

    const fetchAppointments = async () => {
        try {
            const res = await api.get("/scheduling/appointments/me");
            setAppointments(Array.isArray(res.data) ? res.data : []);
        } catch { setAppointments([]); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchAppointments(); }, []);

    const handleCreate = async () => {
        if (!form.guest_name || !form.start_time || !form.end_time) return;
        setSaving(true);
        try {
            await api.post("/scheduling/appointments", {
                host_id: "me",
                guest_name: form.guest_name,
                guest_email: form.guest_email || undefined,
                start_time: form.start_time,
                end_time: form.end_time,
                meeting_type: form.meeting_type,
                location: form.location || undefined,
                notes: form.notes || undefined,
            });
            setShowModal(false);
            setForm({ guest_name: "", guest_email: "", start_time: "", end_time: "", meeting_type: "online", location: "", notes: "" });
            fetchAppointments();
        } catch (e) { console.error("Failed to create appointment", e); }
        finally { setSaving(false); }
    };

    const handleCancel = async (id: string) => {
        try {
            await api.patch(`/scheduling/appointments/${id}/cancel`);
            fetchAppointments();
        } catch (e) { console.error("Cancel failed", e); }
    };

    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear(), month = date.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const offset = firstDay === 0 ? 6 : firstDay - 1;
        return { daysInMonth, offset };
    };

    const { daysInMonth, offset } = getDaysInMonth(currentMonth);
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];

    const getAppointmentsForDate = (day: number) => {
        const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        return appointments.filter(a => a.start_time?.startsWith(dateStr));
    };

    const upcomingAppts = appointments
        .filter(a => a.status !== "cancelled" && new Date(a.start_time) >= today)
        .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
        .slice(0, 8);

    return (
        <div className="space-y-6 p-4 md:p-8 max-w-[1400px] mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Calendar className="h-6 w-6 text-[#f5a623]" /> Schedule
                    </h1>
                    <p className="text-white/50 text-sm">Manage appointments and meetings</p>
                </div>
                <Button onClick={() => setShowModal(true)} className="bg-[#f5a623] text-black hover:bg-[#e09000]">
                    <Plus className="h-4 w-4 mr-2" /> New Appointment
                </Button>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                {/* Calendar */}
                <Card className="lg:col-span-2 bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-white text-lg">
                            {currentMonth.toLocaleString("default", { month: "long", year: "numeric" })}
                        </CardTitle>
                        <div className="flex gap-2">
                            <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}>
                                <ChevronLeft className="h-4 w-4 text-white" />
                            </Button>
                            <Button variant="ghost" size="icon" onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}>
                                <ChevronRight className="h-4 w-4 text-white" />
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-7 gap-1 mb-2">
                            {DAYS.map(d => <div key={d} className="text-center text-xs font-bold text-white/40 py-1">{d}</div>)}
                        </div>
                        <div className="grid grid-cols-7 gap-1">
                            {Array.from({ length: offset }).map((_, i) => <div key={`e-${i}`} />)}
                            {Array.from({ length: daysInMonth }).map((_, i) => {
                                const day = i + 1;
                                const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                                const dayAppts = getAppointmentsForDate(day);
                                const isToday = dateStr === todayStr;
                                const isSelected = selectedDate.toISOString().split("T")[0] === dateStr;
                                return (
                                    <button key={day} onClick={() => setSelectedDate(new Date(dateStr))}
                                        className={`p-2 rounded-lg text-sm text-center transition-all min-h-[48px] ${isToday ? "ring-1 ring-[#f5a623]" : ""} ${isSelected ? "bg-[#f5a623]/20 text-[#f5a623]" : "text-white/70 hover:bg-white/5"}`}>
                                        <div className="font-medium">{day}</div>
                                        {dayAppts.length > 0 && <div className="flex justify-center mt-1"><div className="w-1.5 h-1.5 rounded-full bg-[#f5a623]" /></div>}
                                    </button>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>

                {/* Upcoming */}
                <Card className="bg-[#0e1e33] border-[#1e3a5f]">
                    <CardHeader>
                        <CardTitle className="text-white text-lg flex items-center gap-2">
                            <Clock className="h-5 w-5 text-[#f5a623]" /> Upcoming
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {loading ? (
                            <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-white/40" /></div>
                        ) : upcomingAppts.length === 0 ? (
                            <p className="text-white/40 text-sm text-center py-8">No upcoming appointments</p>
                        ) : upcomingAppts.map(appt => (
                            <div key={appt.id} className="p-3 bg-white/5 rounded-lg border border-white/10 group">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <p className="text-white font-medium text-sm">{appt.guest_name}</p>
                                        <p className="text-white/40 text-xs mt-1 flex items-center gap-1">
                                            <Clock className="h-3 w-3" />
                                            {new Date(appt.start_time).toLocaleDateString()} {new Date(appt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Badge className={`text-[10px] ${appt.meeting_type === "online" ? "bg-blue-500/20 text-blue-400" : "bg-emerald-500/20 text-emerald-400"}`}>
                                            {appt.meeting_type === "online" ? <Video className="h-3 w-3 mr-1" /> : <MapPin className="h-3 w-3 mr-1" />}
                                            {appt.meeting_type}
                                        </Badge>
                                        <button onClick={() => handleCancel(appt.id)} className="opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Trash2 className="h-3.5 w-3.5 text-rose-400" />
                                        </button>
                                    </div>
                                </div>
                                {appt.notes && <p className="text-white/30 text-xs mt-2">{appt.notes}</p>}
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center justify-between">
                            <h3 className="text-white font-bold text-lg">New Appointment</h3>
                            <button onClick={() => setShowModal(false)}><X className="h-5 w-5 text-white/40" /></button>
                        </div>
                        <div className="space-y-3">
                            <Input placeholder="Guest Name *" value={form.guest_name} onChange={e => setForm(p => ({ ...p, guest_name: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <Input placeholder="Guest Email" value={form.guest_email} onChange={e => setForm(p => ({ ...p, guest_email: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-white/50 text-xs">Start *</label>
                                    <Input type="datetime-local" value={form.start_time} onChange={e => setForm(p => ({ ...p, start_time: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                                </div>
                                <div>
                                    <label className="text-white/50 text-xs">End *</label>
                                    <Input type="datetime-local" value={form.end_time} onChange={e => setForm(p => ({ ...p, end_time: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button variant={form.meeting_type === "online" ? "default" : "outline"} size="sm" onClick={() => setForm(p => ({ ...p, meeting_type: "online" }))} className={form.meeting_type === "online" ? "bg-blue-600" : "border-white/20 text-white"}>
                                    <Video className="h-3 w-3 mr-1" /> Online
                                </Button>
                                <Button variant={form.meeting_type === "in_person" ? "default" : "outline"} size="sm" onClick={() => setForm(p => ({ ...p, meeting_type: "in_person" }))} className={form.meeting_type === "in_person" ? "bg-emerald-600" : "border-white/20 text-white"}>
                                    <MapPin className="h-3 w-3 mr-1" /> In Person
                                </Button>
                            </div>
                            {form.meeting_type === "in_person" && (
                                <Input placeholder="Location" value={form.location} onChange={e => setForm(p => ({ ...p, location: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                            )}
                            <Input placeholder="Notes (optional)" value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} className="bg-white/5 border-white/10 text-white" />
                        </div>
                        <Button onClick={handleCreate} disabled={saving || !form.guest_name || !form.start_time || !form.end_time} className="w-full bg-[#f5a623] text-black hover:bg-[#e09000]">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                            Book Appointment
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
