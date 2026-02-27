"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertTriangle, Bell, Brain, Check, CheckCircle2, Clock,
  Eye, Loader2, MessageSquare, Package, RefreshCw, Ship,
  ShieldCheck, Sparkles, TrendingUp, X, Zap, Camera,
  Mic, FileText, ArrowRight, CircleDot, Users, Handshake,
} from "lucide-react";
import api from "@/lib/api";

interface Alert {
  id: string;
  type: string;
  severity: string;
  title_fa: string;
  title_en: string;
  description_fa: string;
  description_en: string;
  entity_id?: string;
  entity_type?: string;
  suggested_action?: string;
  action_label_fa?: string;
  action_label_en?: string;
  action_payload?: Record<string, any>;
  ai_confidence?: number;
  created_at?: string;
}

interface KPI {
  active_shipments: number;
  pending_approvals: number;
  active_deals: number;
  total_contacts: number;
  last_updated: string;
}

interface ApprovalItem {
  id: string;
  category: string;
  title: string;
  description?: string;
  ai_payload?: Record<string, any>;
  ai_confidence: number;
  ai_reasoning?: string;
  source_type?: string;
  source_preview?: string;
  status: string;
  priority: string;
  created_at?: string;
  expires_at?: string;
}

const severityConfig: Record<string, { bg: string; border: string; icon: any; pulse: boolean }> = {
  critical: { bg: "bg-red-500/10", border: "border-red-500/30", icon: AlertTriangle, pulse: true },
  warning: { bg: "bg-amber-500/10", border: "border-amber-500/30", icon: Bell, pulse: false },
  opportunity: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", icon: TrendingUp, pulse: false },
  info: { bg: "bg-blue-500/10", border: "border-blue-500/30", icon: Eye, pulse: false },
};

const categoryIcons: Record<string, any> = {
  outbound_message: MessageSquare,
  price_quote: FileText,
  proforma_invoice: FileText,
  lead_contact: Users,
  shipment_update: Ship,
  crm_update: Handshake,
  voice_command: Mic,
  document_routing: FileText,
};

export default function ControlTowerPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [kpi, setKpi] = useState<KPI | null>(null);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"alerts" | "approvals">("alerts");
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setFetchError(null);
      const [alertsRes, kpiRes, approvalsRes] = await Promise.all([
        api.get<Alert[]>("/control-tower/alerts"),
        api.get<KPI>("/control-tower/kpi"),
        api.get<ApprovalItem[]>("/control-tower/approvals?status=pending"),
      ]);
      setAlerts(alertsRes.data || []);
      setKpi(kpiRes.data || null);
      setApprovals(approvalsRes.data || []);
    } catch (e: any) {
      console.error("Control Tower fetch failed:", e);
      if (e?.status === 401 || e?.status === 403) {
        setFetchError("لطفاً دوباره وارد شوید / Please log in again");
      } else {
        setFetchError("خطا در دریافت اطلاعات / Failed to load data");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleApproval = async (id: string, action: "approve" | "reject") => {
    setActionLoading(id);
    try {
      await api.post(`/control-tower/approvals/${id}/review`, { action });
      setApprovals((prev) => prev.filter((a) => a.id !== id));
      if (kpi) setKpi({ ...kpi, pending_approvals: Math.max(0, kpi.pending_approvals - 1) });
    } catch (e) {
      console.error("Approval action failed:", e);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050A15] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="relative">
            <div className="w-20 h-20 rounded-full border-2 border-[#D4AF37]/30 flex items-center justify-center mx-auto">
              <Brain className="w-10 h-10 text-[#D4AF37] animate-pulse" />
            </div>
            <div className="absolute inset-0 w-20 h-20 rounded-full border-t-2 border-[#D4AF37] animate-spin mx-auto" />
          </div>
          <p className="text-slate-400 text-sm">Loading Control Tower...</p>
        </div>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="min-h-screen bg-[#050A15] flex items-center justify-center">
        <div className="text-center space-y-4 max-w-sm">
          <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
          <p className="text-white font-medium">{fetchError}</p>
          <div className="flex gap-3 justify-center">
            <Button
              onClick={() => { window.location.href = '/login'; }}
              className="bg-[#D4AF37] text-black hover:bg-[#E5C048]"
            >
              Login
            </Button>
            <Button
              variant="outline"
              onClick={() => { setLoading(true); fetchData(); }}
              className="border-slate-700 text-slate-400"
            >
              <RefreshCw className="w-4 h-4 mr-2" /> Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-6 space-y-6 selection:bg-[#D4AF37] selection:text-black">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B8860B] flex items-center justify-center">
              <Zap className="w-5 h-5 text-black" />
            </div>
            Control Tower
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Your AI-powered command center — actionable alerts, not boring charts
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => { setLoading(true); fetchData(); }}
          className="border-slate-700 text-slate-400 hover:text-white hover:border-[#D4AF37]/50"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* KPI Cards */}
      {kpi && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            icon={Ship}
            label="Active Shipments"
            labelFa="محموله‌های فعال"
            value={kpi.active_shipments}
            color="blue"
          />
          <KPICard
            icon={ShieldCheck}
            label="Pending Approvals"
            labelFa="تایید مورد نیاز"
            value={kpi.pending_approvals}
            color={kpi.pending_approvals > 0 ? "amber" : "green"}
            pulse={kpi.pending_approvals > 0}
          />
          <KPICard
            icon={Handshake}
            label="Active Deals"
            labelFa="معاملات فعال"
            value={kpi.active_deals}
            color="emerald"
          />
          <KPICard
            icon={Users}
            label="Total Contacts"
            labelFa="کل مخاطبین"
            value={kpi.total_contacts}
            color="purple"
          />
        </div>
      )}

      {/* Quick Actions Bar */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        <QuickAction icon={Camera} label="Scan Document" labelFa="اسکن سند" href="/documents" />
        <QuickAction icon={Mic} label="Voice Command" labelFa="دستور صوتی" href="/whatsapp" />
        <QuickAction icon={Package} label="Track Shipment" labelFa="رهگیری محموله" href="/shipments" />
        <QuickAction icon={Handshake} label="New Deal" labelFa="معامله جدید" href="/deals" />
      </div>

      {/* Tab Selector */}
      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("alerts")}
          className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
            activeTab === "alerts"
              ? "bg-[#D4AF37]/10 text-[#D4AF37] border-b-2 border-[#D4AF37]"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          <Zap className="w-4 h-4 inline mr-2" />
          Alerts ({alerts.length})
        </button>
        <button
          onClick={() => setActiveTab("approvals")}
          className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
            activeTab === "approvals"
              ? "bg-[#D4AF37]/10 text-[#D4AF37] border-b-2 border-[#D4AF37]"
              : "text-slate-500 hover:text-slate-300"
          }`}
        >
          <ShieldCheck className="w-4 h-4 inline mr-2" />
          Approvals ({approvals.length})
          {approvals.length > 0 && (
            <span className="ml-2 w-2 h-2 bg-amber-500 rounded-full inline-block animate-pulse" />
          )}
        </button>
      </div>

      {/* Alert Feed */}
      {activeTab === "alerts" && (
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                <p className="text-slate-400">All clear! No active alerts.</p>
                <p className="text-slate-600 text-sm mt-1">Your AI assistant is monitoring everything.</p>
              </CardContent>
            </Card>
          ) : (
            alerts.map((alert) => <AlertCard key={alert.id} alert={alert} />)
          )}
        </div>
      )}

      {/* Approval Queue */}
      {activeTab === "approvals" && (
        <div className="space-y-3">
          {approvals.length === 0 ? (
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                <p className="text-slate-400">No pending approvals.</p>
                <p className="text-slate-600 text-sm mt-1">AI actions are up to date.</p>
              </CardContent>
            </Card>
          ) : (
            approvals.map((item) => (
              <ApprovalCard
                key={item.id}
                item={item}
                onApprove={() => handleApproval(item.id, "approve")}
                onReject={() => handleApproval(item.id, "reject")}
                loading={actionLoading === item.id}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

/* === Sub-Components === */

function KPICard({
  icon: Icon,
  label,
  labelFa,
  value,
  color,
  pulse = false,
}: {
  icon: any;
  label: string;
  labelFa: string;
  value: number;
  color: string;
  pulse?: boolean;
}) {
  const colors: Record<string, string> = {
    blue: "from-blue-500/20 to-blue-600/5 border-blue-500/20 text-blue-400",
    amber: "from-amber-500/20 to-amber-600/5 border-amber-500/20 text-amber-400",
    green: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20 text-emerald-400",
    emerald: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20 text-emerald-400",
    purple: "from-purple-500/20 to-purple-600/5 border-purple-500/20 text-purple-400",
  };

  return (
    <Card className={`bg-gradient-to-br ${colors[color] || colors.blue} border relative overflow-hidden`}>
      {pulse && <div className="absolute top-2 right-2 w-2 h-2 bg-amber-500 rounded-full animate-pulse" />}
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <Icon className="w-5 h-5 opacity-70" />
          <span className="text-2xl font-bold text-white">{value}</span>
        </div>
        <p className="text-xs mt-2 opacity-70">{label}</p>
        <p className="text-xs opacity-50" dir="rtl">{labelFa}</p>
      </CardContent>
    </Card>
  );
}

function QuickAction({
  icon: Icon,
  label,
  labelFa,
  href,
}: {
  icon: any;
  label: string;
  labelFa: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/50 border border-slate-700/50 hover:border-[#D4AF37]/30 hover:bg-slate-800 transition-all group cursor-pointer"
    >
      <Icon className="w-4 h-4 text-[#D4AF37] group-hover:scale-110 transition-transform" />
      <div>
        <p className="text-xs text-white font-medium">{label}</p>
        <p className="text-[10px] text-slate-500" dir="rtl">{labelFa}</p>
      </div>
    </a>
  );
}

function AlertCard({ alert }: { alert: Alert }) {
  const config = severityConfig[alert.severity] || severityConfig.info;
  const Icon = config.icon;

  return (
    <Card className={`${config.bg} border ${config.border} relative overflow-hidden`}>
      {config.pulse && (
        <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-red-500 via-red-400 to-transparent animate-pulse" />
      )}
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
            alert.severity === "critical" ? "bg-red-500/20" :
            alert.severity === "warning" ? "bg-amber-500/20" :
            alert.severity === "opportunity" ? "bg-emerald-500/20" : "bg-blue-500/20"
          }`}>
            <Icon className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">{alert.title_en}</p>
            <p className="text-xs text-slate-500 mt-0.5" dir="rtl">{alert.title_fa}</p>
            {alert.description_en && (
              <p className="text-xs text-slate-400 mt-1">{alert.description_en}</p>
            )}
            {alert.ai_confidence !== undefined && alert.ai_confidence > 0 && (
              <div className="flex items-center gap-1 mt-2">
                <Brain className="w-3 h-3 text-[#D4AF37]" />
                <span className="text-[10px] text-[#D4AF37]">
                  AI Confidence: {Math.round(alert.ai_confidence * 100)}%
                </span>
              </div>
            )}
          </div>
          {alert.action_label_en && (
            <Button
              size="sm"
              className="bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30 hover:bg-[#D4AF37]/20 text-xs flex-shrink-0"
            >
              {alert.action_label_en}
              <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ApprovalCard({
  item,
  onApprove,
  onReject,
  loading,
}: {
  item: ApprovalItem;
  onApprove: () => void;
  onReject: () => void;
  loading: boolean;
}) {
  const CategoryIcon = categoryIcons[item.category] || FileText;

  return (
    <Card className="bg-slate-900/50 border border-slate-700/50 hover:border-[#D4AF37]/20 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#D4AF37]/10 flex items-center justify-center flex-shrink-0">
            <CategoryIcon className="w-4 h-4 text-[#D4AF37]" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium text-white">{item.title}</p>
              <Badge
                variant="outline"
                className={`text-[10px] ${
                  item.priority === "high" ? "border-red-500/50 text-red-400" :
                  item.priority === "critical" ? "border-red-500/50 text-red-400" :
                  "border-slate-600 text-slate-400"
                }`}
              >
                {item.priority}
              </Badge>
            </div>
            {item.source_preview && (
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                {item.source_preview}
              </p>
            )}
            {item.ai_reasoning && (
              <p className="text-xs text-slate-500 mt-1 italic">
                AI: {item.ai_reasoning}
              </p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <Brain className="w-3 h-3 text-[#D4AF37]" />
              <span className="text-[10px] text-[#D4AF37]">
                Confidence: {Math.round(item.ai_confidence * 100)}%
              </span>
              {item.source_type && (
                <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-500">
                  {item.source_type}
                </Badge>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-2 flex-shrink-0">
            <Button
              size="sm"
              onClick={onApprove}
              disabled={loading}
              className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 text-xs"
            >
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-1" />}
              Approve
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onReject}
              disabled={loading}
              className="border-red-500/30 text-red-400 hover:bg-red-500/10 text-xs"
            >
              <X className="w-3 h-3 mr-1" />
              Reject
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
