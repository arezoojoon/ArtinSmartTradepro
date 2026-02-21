"use client";

import { useState, useEffect } from "react";
import { Plus, CheckCircle2, Clock, Calendar, MoreHorizontal } from "lucide-react";

export default function TasksPage() {
    return (
        <div className="p-6 max-w-7xl mx-auto h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Tasks</h1>
                    <p className="text-sm text-navy-400">Manage your to-dos, follow-ups, and daily activities</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-gold-400 text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    New Task
                </button>
            </div>

            <div className="flex-1 bg-navy-900 border border-navy-800 rounded-xl p-8 flex flex-col items-center justify-center">
                <CheckCircle2 className="h-16 w-16 text-navy-700 mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No tasks yet</h3>
                <p className="text-navy-400 text-center max-w-md mb-6">
                    You're all caught up! Create a task to remind yourself of follow-ups, meetings, or deals to review.
                </p>
                <button className="px-6 py-2 bg-navy-800 hover:bg-navy-700 text-white rounded-lg transition-colors font-medium border border-navy-700">
                    Create your first task
                </button>
            </div>
        </div>
    );
}
