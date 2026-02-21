"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Calendar } from "lucide-react";

export default function SchedulePage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold flex items-center gap-2">
                    <Calendar className="h-8 w-8 text-sky-400" />
                    Schedule
                </h1>
                <p className="text-gray-400 mt-1">Manage tasks, meetings, and follow-up schedules</p>
            </div>
            <Card className="bg-navy-900 border-navy-800">
                <CardContent className="py-16 text-center">
                    <Calendar className="h-16 w-16 mx-auto mb-4 text-gray-700" />
                    <p className="text-gray-500">Scheduler — Coming Soon</p>
                    <p className="text-xs text-gray-600 mt-2">Calendar view with tasks, reminders, and meeting scheduling.</p>
                </CardContent>
            </Card>
        </div>
    );
}
