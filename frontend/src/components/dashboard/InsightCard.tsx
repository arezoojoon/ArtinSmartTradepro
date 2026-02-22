import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { AlertCircle, CheckCircle2, Info, Clock, ExternalLink } from "lucide-react";

export interface InsightData {
    title: string;
    source: string;
    timestamp: string; // ISO string
    confidence: number; // 0-100
    actionLabel?: string;
    onAction?: () => void;
    isInsufficientData?: boolean;
}

interface InsightCardProps extends InsightData {
    children?: React.ReactNode;
    className?: string;
}

export function InsightCard({
    title,
    source,
    timestamp,
    confidence,
    actionLabel,
    onAction,
    isInsufficientData,
    children,
    className = "",
}: InsightCardProps) {
    // Confidence Color Logic
    const getConfidenceColor = (conf: number) => {
        if (conf >= 85) return "text-emerald-600 bg-emerald-50 border-emerald-200";
        if (conf >= 60) return "text-amber-600 bg-amber-50 border-amber-200";
        return "text-rose-600 bg-rose-50 border-rose-200";
    };

    const getConfidenceIcon = (conf: number) => {
        if (conf >= 85) return <CheckCircle2 className="h-3 w-3 mr-1" />;
        if (conf >= 60) return <Info className="h-3 w-3 mr-1" />;
        return <AlertCircle className="h-3 w-3 mr-1" />;
    };

    if (isInsufficientData) {
        return (
            <Card className={`border-dashed border-slate-300 bg-slate-50/50 ${className}`}>
                <CardContent className="p-4 flex flex-col items-center justify-center text-center space-y-2">
                    <AlertCircle className="h-8 w-8 text-slate-400" />
                    <h3 className="font-semibold text-slate-700">{title}</h3>
                    <p className="text-sm text-slate-500 max-w-[250px]">
                        Insufficient data to generate this insight.
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs text-slate-400">
                            Source: {source}
                        </Badge>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className={`border-slate-200 shadow-sm overflow-hidden ${className}`}>
            <CardContent className="p-0">
                <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-slate-900 leading-tight">{title}</h3>
                        {confidence !== undefined && (
                            <Badge variant="outline" className={`flex items-center text-[10px] uppercase font-bold px-2 py-0.5 ${getConfidenceColor(confidence)}`}>
                                {getConfidenceIcon(confidence)}
                                {confidence}% Conf.
                            </Badge>
                        )}
                    </div>

                    <div className="my-3">
                        {children}
                    </div>
                </div>

                {/* Footer: Traceability & Action */}
                <div className="bg-slate-50 px-4 py-2.5 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex flex-col gap-0.5">
                        <div className="text-[10px] font-medium text-slate-500 uppercase tracking-widest flex items-center gap-1">
                            <ExternalLink className="h-3 w-3" />
                            Source: <span className="text-slate-700 font-semibold">{source}</span>
                        </div>
                        <div className="text-[10px] text-slate-400 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {timestamp ? formatDistanceToNow(new Date(timestamp), { addSuffix: true }) : "Unknown time"}
                        </div>
                    </div>

                    {actionLabel && (
                        <button
                            onClick={onAction}
                            className="text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-md transition-colors"
                        >
                            {actionLabel}
                        </button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
