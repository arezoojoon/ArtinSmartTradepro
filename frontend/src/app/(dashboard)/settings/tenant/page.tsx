"use client";

import { useEffect, useState } from "react";
import { getActiveTenantId, getMyTenants, type Tenant } from "@/lib/tenant";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";
import { CheckCircle2, AlertTriangle } from "lucide-react";

export default function TenantSettingsPage() {
    const [tenant, setTenant] = useState<Tenant | null>(null);
    const [editName, setEditName] = useState("");
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteInput, setDeleteInput] = useState("");
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        const activeId = getActiveTenantId();
        if (activeId) {
            getMyTenants().then(list => {
                const found = list.find(t => t.id === activeId);
                if (found) { setTenant(found); setEditName(found.name); }
            });
        }
    }, []);

    const handleSaveName = async () => {
        if (!tenant || !editName.trim() || editName === tenant.name) return;
        setSaving(true);
        try {
            await api.patch(`/tenants/${tenant.id}`, { name: editName.trim() });
            setTenant({ ...tenant, name: editName.trim() });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (e) { console.error("Failed to update name", e); }
        finally { setSaving(false); }
    };

    const handleDelete = async () => {
        if (!tenant || deleteInput !== tenant.name) return;
        setDeleting(true);
        try {
            await api.delete(`/tenants/${tenant.id}`);
            localStorage.removeItem("active_tenant_id");
            window.location.href = "/";
        } catch (e) { console.error("Failed to delete org", e); setDeleting(false); }
    };

    if (!tenant) return <div className="p-8 text-white">Loading...</div>;

    return (
        <div className="p-4 md:p-8 space-y-8 max-w-2xl text-white">
            <div>
                <h1 className="text-2xl font-bold">Organization Settings</h1>
                <p className="text-white/60">Manage your organization details.</p>
            </div>

            <div className="space-y-6">
                <div className="grid gap-2">
                    <Label>Organization ID</Label>
                    <div className="font-mono text-sm text-white/40 bg-white/5 p-2 rounded">
                        {tenant.id}
                    </div>
                </div>

                <div className="grid gap-2">
                    <Label>Name</Label>
                    <div className="flex gap-2">
                        <Input value={editName} onChange={e => setEditName(e.target.value)} className="bg-white/5 border-white/10" />
                        <Button onClick={handleSaveName} disabled={saving || editName === tenant.name || !editName.trim()} className="bg-[#f5a623] text-navy-950 hover:bg-gold-300 disabled:opacity-40">
                            {saving ? "Saving..." : saved ? "Saved" : "Save"}
                        </Button>
                    </div>
                    {saved && <span className="text-emerald-400 text-xs flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Name updated</span>}
                </div>

                <div className="grid gap-2">
                    <Label>Your Role</Label>
                    <div className="capitalize text-white/80">{tenant.role}</div>
                </div>

                <div className="pt-4 border-t border-white/10">
                    <h3 className="text-lg font-medium mb-2">Danger Zone</h3>
                    <p className="text-sm text-white/40 mb-4">Deleting your organization will permanently remove all data including contacts, deals, and messages.</p>
                    {!showDeleteConfirm ? (
                        <Button variant="destructive" onClick={() => setShowDeleteConfirm(true)} disabled={tenant.role !== "owner"}>
                            {tenant.role !== "owner" ? "Only owners can delete" : "Delete Organization"}
                        </Button>
                    ) : (
                        <div className="bg-red-950/30 border border-red-500/30 rounded-xl p-4 space-y-3">
                            <div className="flex items-center gap-2 text-red-400 text-sm font-semibold">
                                <AlertTriangle className="h-4 w-4" /> This action is irreversible
                            </div>
                            <p className="text-xs text-white/60">Type <strong className="text-white">{tenant.name}</strong> to confirm:</p>
                            <Input value={deleteInput} onChange={e => setDeleteInput(e.target.value)} placeholder={tenant.name} className="bg-red-950/20 border-red-500/30 text-white" />
                            <div className="flex gap-2">
                                <Button variant="destructive" onClick={handleDelete} disabled={deleteInput !== tenant.name || deleting}>
                                    {deleting ? "Deleting..." : "Permanently Delete"}
                                </Button>
                                <Button variant="outline" onClick={() => { setShowDeleteConfirm(false); setDeleteInput(""); }} className="border-white/20 text-white">Cancel</Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
