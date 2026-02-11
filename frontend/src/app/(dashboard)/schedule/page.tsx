"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import {
    CalendarDays, Clock, Video, MapPin, ChevronLeft, ChevronRight,
    Plus, X, User
} from "lucide-react";

// --- Calendar Helpers ---
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

function getDaysInMonth(year: number, month: number) {
    return new Date(year, month + 1, 0).getDate();
}
function getFirstDayOfMonth(year: number, month: number) {
    const day = new Date(year, month, 1).getDay();
    return day === 0 ? 6 : day - 1; // Convert to Mon=0
}

export default function SchedulePage() {
    const today = new Date();
    const [currentMonth, setCurrentMonth] = useState(today.getMonth());
    const [currentYear, setCurrentYear] = useState(today.getFullYear());
    const [selectedDate, setSelectedDate] = useState<Date | null>(today);
    const [slots, setSlots] = useState<any[]>([]);
    const [appointments, setAppointments] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    // Booking Modal
    const [openBook, setOpenBook] = useState(false);
    const [selectedSlot, setSelectedSlot] = useState<any>(null);
    const [bookingForm, setBookingForm] = useState({
        guest_name: "",
        guest_email: "",
        meeting_type: "online",
        location: "",
        notes: ""
    });

    // Mock user ID (replace with auth context in production)
    const MOCK_USER = "00000000-0000-0000-0000-000000000001";

    // Calendar Grid
    const calendarDays = useMemo(() => {
        const daysInMonth = getDaysInMonth(currentYear, currentMonth);
        const firstDay = getFirstDayOfMonth(currentYear, currentMonth);
        const days: (number | null)[] = [];

        for (let i = 0; i < firstDay; i++) days.push(null);
        for (let i = 1; i <= daysInMonth; i++) days.push(i);

        return days;
    }, [currentYear, currentMonth]);

    const prevMonth = () => {
        if (currentMonth === 0) {
            setCurrentMonth(11);
            setCurrentYear(currentYear - 1);
        } else {
            setCurrentMonth(currentMonth - 1);
        }
    };

    const nextMonth = () => {
        if (currentMonth === 11) {
            setCurrentMonth(0);
            setCurrentYear(currentYear + 1);
        } else {
            setCurrentMonth(currentMonth + 1);
        }
    };

    const selectDay = (day: number) => {
        setSelectedDate(new Date(currentYear, currentMonth, day));
    };

    // Fetch Slots when date selected
    useEffect(() => {
        if (!selectedDate) return;
        const dateStr = selectedDate.toISOString().split("T")[0];
        setLoading(true);
        api.get(`/api/v1/scheduling/slots/${MOCK_USER}?date=${dateStr}`)
            .then(res => setSlots(res.data))
            .catch(() => setSlots([]))
            .finally(() => setLoading(false));
    }, [selectedDate]);

    // Fetch Upcoming Appointments
    useEffect(() => {
        api.get(`/api/v1/scheduling/appointments/${MOCK_USER}`)
            .then(res => setAppointments(res.data))
            .catch(() => setAppointments([]));
    }, []);

    const handleBookSlot = (slot: any) => {
        setSelectedSlot(slot);
        setOpenBook(true);
    };

    const confirmBooking = async () => {
        if (!selectedSlot) return;
        try {
            await api.post("/api/v1/scheduling/appointments", {
                host_id: MOCK_USER,
                guest_name: bookingForm.guest_name,
                guest_email: bookingForm.guest_email,
                start_time: selectedSlot.start,
                end_time: selectedSlot.end,
                meeting_type: bookingForm.meeting_type,
                location: bookingForm.location,
                notes: bookingForm.notes
            });
            setOpenBook(false);
            setBookingForm({ guest_name: "", guest_email: "", meeting_type: "online", location: "", notes: "" });
            // Refresh slots + appointments
            if (selectedDate) {
                const dateStr = selectedDate.toISOString().split("T")[0];
                const [slotsRes, apptsRes] = await Promise.all([
                    api.get(`/api/v1/scheduling/slots/${MOCK_USER}?date=${dateStr}`),
                    api.get(`/api/v1/scheduling/appointments/${MOCK_USER}`)
                ]);
                setSlots(slotsRes.data);
                setAppointments(apptsRes.data);
            }
        } catch (e: any) {
            alert(e.response?.data?.detail || "Failed to book");
        }
    };

    const isToday = (day: number) => {
        return day === today.getDate() &&
            currentMonth === today.getMonth() &&
            currentYear === today.getFullYear();
    };

    const isSelected = (day: number) => {
        if (!selectedDate) return false;
        return day === selectedDate.getDate() &&
            currentMonth === selectedDate.getMonth() &&
            currentYear === selectedDate.getFullYear();
    };

    return (
        <div className="p-8 bg-black min-h-screen text-white">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-2">
                        <CalendarDays className="h-8 w-8 text-gold-500" />
                        Scheduling
                    </h1>
                    <p className="text-gray-400">Book online & in-person meetings</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* === Calendar Widget === */}
                <Card className="bg-navy-900 border-navy-800 lg:col-span-1">
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <button onClick={prevMonth} className="p-1 hover:bg-navy-800 rounded">
                                <ChevronLeft className="h-5 w-5 text-gray-400" />
                            </button>
                            <CardTitle className="text-white text-lg">
                                {MONTHS[currentMonth]} {currentYear}
                            </CardTitle>
                            <button onClick={nextMonth} className="p-1 hover:bg-navy-800 rounded">
                                <ChevronRight className="h-5 w-5 text-gray-400" />
                            </button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {/* Day Headers */}
                        <div className="grid grid-cols-7 gap-1 mb-2">
                            {DAYS.map(d => (
                                <div key={d} className="text-center text-xs text-gray-500 font-medium py-1">
                                    {d}
                                </div>
                            ))}
                        </div>
                        {/* Day Grid */}
                        <div className="grid grid-cols-7 gap-1">
                            {calendarDays.map((day, i) => (
                                <div key={i} className="aspect-square flex items-center justify-center">
                                    {day ? (
                                        <button
                                            onClick={() => selectDay(day)}
                                            className={`w-9 h-9 rounded-full flex items-center justify-center text-sm transition-all
                                                ${isToday(day)
                                                    ? "bg-gold-500 text-black font-bold"
                                                    : isSelected(day)
                                                        ? "bg-blue-600 text-white"
                                                        : "text-gray-300 hover:bg-navy-700"
                                                }`}
                                        >
                                            {day}
                                        </button>
                                    ) : null}
                                </div>
                            ))}
                        </div>

                        {/* Available Time Slots */}
                        <div className="mt-6">
                            <h3 className="text-sm font-semibold text-gray-500 mb-3">Available Slots</h3>
                            {loading ? (
                                <p className="text-gray-600 text-sm">Loading...</p>
                            ) : slots.length === 0 ? (
                                <p className="text-gray-600 text-sm">No slots for this date. Set your availability first.</p>
                            ) : (
                                <div className="flex flex-wrap gap-2">
                                    {slots.map((s, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleBookSlot(s)}
                                            className="px-3 py-1.5 rounded-full bg-emerald-900/50 text-emerald-400 
                                                       text-sm font-medium border border-emerald-800 hover:bg-emerald-800 transition"
                                        >
                                            {s.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* === Upcoming Appointments === */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex justify-between items-center">
                        <h2 className="text-xl font-semibold">Upcoming</h2>
                        <span className="text-sm text-gray-500">
                            {appointments.length} appointment{appointments.length !== 1 ? "s" : ""}
                        </span>
                    </div>

                    {appointments.length === 0 ? (
                        <Card className="bg-navy-900 border-navy-800">
                            <CardContent className="py-12 text-center text-gray-500">
                                <CalendarDays className="h-12 w-12 mx-auto mb-4 opacity-30" />
                                No upcoming appointments.
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {appointments.map((appt: any) => (
                                <Card key={appt.id} className="bg-navy-900 border-navy-800">
                                    <CardHeader className="pb-2">
                                        <div className="flex justify-between items-start">
                                            <CardTitle className="text-white text-base flex items-center gap-2">
                                                <User className="h-4 w-4 text-blue-400" />
                                                {appt.guest_name}
                                            </CardTitle>
                                            <Badge
                                                variant={appt.meeting_type === "online" ? "default" : "outline"}
                                                className={appt.meeting_type === "online"
                                                    ? "bg-blue-900/60 text-blue-300"
                                                    : "text-orange-400 border-orange-800"}
                                            >
                                                {appt.meeting_type === "online" ? (
                                                    <><Video className="h-3 w-3 mr-1" />Online</>
                                                ) : (
                                                    <><MapPin className="h-3 w-3 mr-1" />In-Person</>
                                                )}
                                            </Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex items-center gap-2 text-sm text-gray-400">
                                            <Clock className="h-4 w-4" />
                                            {new Date(appt.start_time).toLocaleString()}
                                        </div>
                                        {appt.location && (
                                            <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                                                <MapPin className="h-4 w-4" />
                                                {appt.location}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* === Booking Dialog === */}
            <Dialog open={openBook} onOpenChange={setOpenBook}>
                <DialogContent className="bg-navy-900 border-navy-800 text-white max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <CalendarDays className="h-5 w-5 text-gold-500" />
                            Book Meeting — {selectedSlot?.label}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <Input
                            placeholder="Guest Name *"
                            className="bg-navy-950 border-navy-700"
                            value={bookingForm.guest_name}
                            onChange={(e) => setBookingForm({ ...bookingForm, guest_name: e.target.value })}
                        />
                        <Input
                            placeholder="Guest Email"
                            className="bg-navy-950 border-navy-700"
                            value={bookingForm.guest_email}
                            onChange={(e) => setBookingForm({ ...bookingForm, guest_email: e.target.value })}
                        />

                        {/* Meeting Type Toggle */}
                        <div className="flex gap-2">
                            <button
                                onClick={() => setBookingForm({ ...bookingForm, meeting_type: "online" })}
                                className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition
                                    ${bookingForm.meeting_type === "online"
                                        ? "bg-blue-600 text-white"
                                        : "bg-navy-800 text-gray-400 hover:bg-navy-700"
                                    }`}
                            >
                                <Video className="h-4 w-4" /> Online
                            </button>
                            <button
                                onClick={() => setBookingForm({ ...bookingForm, meeting_type: "in_person" })}
                                className={`flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition
                                    ${bookingForm.meeting_type === "in_person"
                                        ? "bg-orange-600 text-white"
                                        : "bg-navy-800 text-gray-400 hover:bg-navy-700"
                                    }`}
                            >
                                <MapPin className="h-4 w-4" /> In-Person
                            </button>
                        </div>

                        <Input
                            placeholder={bookingForm.meeting_type === "online" ? "Meeting Link (Zoom, Google Meet)" : "Physical Address"}
                            className="bg-navy-950 border-navy-700"
                            value={bookingForm.location}
                            onChange={(e) => setBookingForm({ ...bookingForm, location: e.target.value })}
                        />

                        <Input
                            placeholder="Notes (optional)"
                            className="bg-navy-950 border-navy-700"
                            value={bookingForm.notes}
                            onChange={(e) => setBookingForm({ ...bookingForm, notes: e.target.value })}
                        />

                        <Button
                            onClick={confirmBooking}
                            disabled={!bookingForm.guest_name}
                            className="w-full bg-gold-500 text-black hover:bg-gold-400 font-semibold"
                        >
                            Confirm Booking
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
