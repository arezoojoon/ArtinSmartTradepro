"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, CheckCircle2, Clock, Calendar, MoreHorizontal, X, Loader2 } from "lucide-react";
import api from "@/lib/api";

export default function TasksPage() {
    const [tasks, setTasks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [form, setForm] = useState({ title: "", description: "", priority: "medium", due_date: "" });

    const fetchTasks = useCallback(async () => {
        try {
            const res = await api.get("/crm/tasks");
            setTasks(res.data.tasks || res.data || []);
        } catch { setTasks([]); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchTasks(); }, [fetchTasks]);

    const createTask = async () => {
        if (!form.title.trim()) return;
        setSaving(true);
        try {
            await api.post("/crm/tasks", {
                title: form.title,
                description: form.description || undefined,
                priority: form.priority,
                due_date: form.due_date || undefined,
            });
            setShowModal(false);
            setForm({ title: "", description: "", priority: "medium", due_date: "" });
            fetchTasks();
        } catch (e) { console.error("Failed to create task", e); }
        finally { setSaving(false); }
    };

    const openModal = () => { setForm({ title: "", description: "", priority: "medium", due_date: "" }); setShowModal(true); };

    return (
        <div className="p-6 max-w-7xl mx-auto h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Tasks</h1>
                    <p className="text-sm text-navy-400">Manage your to-dos, follow-ups, and daily activities</p>
                </div>
                <button onClick={openModal} className="flex items-center gap-2 px-4 py-2 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    New Task
                </button>
            </div>

            {loading ? (
                <div className="flex-1 flex items-center justify-center text-navy-500"><Loader2 className="h-6 w-6 animate-spin mr-2" /> Loading tasks...</div>
            ) : tasks.length === 0 ? (
                <div className="flex-1 bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-8 flex flex-col items-center justify-center">
                    <CheckCircle2 className="h-16 w-16 text-navy-700 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">No tasks yet</h3>
                    <p className="text-navy-400 text-center max-w-md mb-6">
                        You're all caught up! Create a task to remind yourself of follow-ups, meetings, or deals to review.
                    </p>
                    <button onClick={openModal} className="px-6 py-2 bg-navy-800 hover:bg-navy-700 text-white rounded-lg transition-colors font-medium border border-navy-700">
                        Create your first task
                    </button>
                </div>
            ) : (
                <div className="space-y-3">
                    {tasks.map((task: any) => (
                        <div key={task.id} className="bg-[#0e1e33] border border-[#1e3a5f] rounded-xl p-4 flex items-center justify-between hover:border-navy-600 transition-colors">
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className={`h-5 w-5 ${task.status === "completed" ? "text-emerald-400" : "text-navy-600"}`} />
                                <div>
                                    <p className={`font-medium ${task.status === "completed" ? "text-navy-400 line-through" : "text-white"}`}>{task.title}</p>
                                    {task.description && <p className="text-xs text-navy-500 mt-0.5">{task.description}</p>}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                {task.due_date && <span className="text-xs text-navy-400 flex items-center gap-1"><Calendar className="h-3 w-3" />{new Date(task.due_date).toLocaleDateString()}</span>}
                                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${task.priority === "high" ? "bg-red-500/20 text-red-400" : task.priority === "low" ? "bg-blue-500/20 text-blue-400" : "bg-amber-500/20 text-amber-400"}`}>{task.priority}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create Task Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
                    <div className="bg-[#0e1e33] border border-[#1e3a5f] rounded-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-5">
                            <h3 className="text-lg font-bold text-white">New Task</h3>
                            <button onClick={() => setShowModal(false)} className="text-navy-400 hover:text-white"><X className="h-5 w-5" /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs text-navy-400 mb-1">Title *</label>
                                <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Follow up with supplier" className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none" />
                            </div>
                            <div>
                                <label className="block text-xs text-navy-400 mb-1">Description</label>
                                <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={3} className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none resize-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-xs text-navy-400 mb-1">Priority</label>
                                    <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))} className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none">
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-navy-400 mb-1">Due Date</label>
                                    <input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} className="w-full px-3 py-2 bg-navy-800 border border-navy-600 rounded-lg text-white text-sm focus:border-gold-400 focus:outline-none" />
                                </div>
                            </div>
                        </div>
                        <button onClick={createTask} disabled={saving || !form.title.trim()} className="mt-6 w-full py-2.5 bg-[#f5a623] text-navy-950 rounded-lg font-semibold hover:bg-gold-300 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                            {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Creating...</> : <><Plus className="h-4 w-4" /> Create Task</>}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
