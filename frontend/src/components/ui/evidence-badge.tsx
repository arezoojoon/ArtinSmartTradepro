"use client";

import React from "react";
import {
    ShieldCheck,
    Info,
    Database,
    Globe,
    Clock,
    AlertCircle,
    ExternalLink
} from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface EvidenceBadgeProps {
    source: string;
    confidence: number; // 0 to 1
    timestamp?: string | Date;
    reasoning?: string | string[];
    sourceUrl?: string;
    className?: string;
    size?: "sm" | "md";
}

export function EvidenceBadge({
    source,
    confidence,
    timestamp,
    reasoning,
    sourceUrl,
    className,
    size = "sm",
}: EvidenceBadgeProps) {
    const pct = Math.round(confidence * 100);

    const getConfidenceConfig = (score: number) => {
        if (score >= 0.8) return {
            color: "text-emerald-700 bg-emerald-50 border-emerald-200",
            icon: ShieldCheck,
            label: "Verified"
        };
        if (score >= 0.5) return {
            color: "text-amber-700 bg-amber-50 border-amber-200",
            icon: Info,
            label: "Probable"
        };
        return {
            color: "text-rose-700 bg-rose-50 border-rose-200",
            icon: AlertCircle,
            label: "Low Certainty"
        };
    };

    const config = getConfidenceConfig(confidence);
    const Icon = config.icon;

    const dateStr = timestamp
        ? new Date(timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
        : null;

    return (
        <TooltipProvider>
            <Tooltip delayDuration={300}>
                <TooltipTrigger asChild>
                    <div className={cn("inline-flex items-center gap-1.5 cursor-help", className)}>
                        <Badge
                            variant="outline"
                            className={cn(
                                "font-bold tracking-tight px-1.5 py-0 h-5 transition-all hover:shadow-sm",
                                config.color,
                                size === "sm" ? "text-[10px]" : "text-[11px]"
                            )}
                        >
                            <Icon className={cn("mr-1", size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3")} />
                            {pct}% Confidence
                        </Badge>
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                            via {source}
                        </span>
                    </div>
                </TooltipTrigger>
                <TooltipContent className="p-3 max-w-[280px] bg-white border-slate-200 shadow-xl rounded-xl">
                    <div className="space-y-2.5">
                        <div className="flex items-center justify-between border-b pb-2 border-slate-100">
                            <div className="flex items-center gap-2">
                                <div className="p-1.5 bg-indigo-50 rounded-lg">
                                    <Database className="h-3.5 w-3.5 text-indigo-600" />
                                </div>
                                <span className="font-bold text-slate-900 text-sm">{source}</span>
                            </div>
                            {dateStr && (
                                <div className="flex items-center gap-1 text-[10px] text-slate-400 font-bold">
                                    <Clock className="h-2.5 w-2.5" />
                                    {dateStr}
                                </div>
                            )}
                        </div>

                        {reasoning && (
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Logic/Evidence</p>
                                <div className="text-xs text-slate-600 leading-relaxed italic">
                                    {Array.isArray(reasoning) ? (
                                        <ul className="list-disc pl-3 space-y-1">
                                            {reasoning.map((r, i) => <li key={i}>{r}</li>)}
                                        </ul>
                                    ) : (
                                        `"${reasoning}"`
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="flex items-center gap-2 pt-1">
                            <Badge className={cn("text-[9px] font-black uppercase", config.color)}>
                                {config.label}
                            </Badge>
                            {sourceUrl && (
                                <a
                                    href={sourceUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[9px] font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-0.5 ml-auto"
                                >
                                    Source URL <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                            )}
                        </div>
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}
