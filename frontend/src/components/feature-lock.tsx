"use client";

import { Lock, ArrowRight } from "lucide-react";
import Link from "next/link";

interface FeatureLockProps {
    featureName: string;
    requiredPlan?: string;
    children: React.ReactNode;
    isLocked: boolean;
}

/**
 * Wraps any feature component. When locked, displays upgrade prompt instead.
 * Usage:
 *   <FeatureLock featureName="Trade Intelligence" requiredPlan="Enterprise" isLocked={!hasFeature("trade_intelligence")}>
 *     <TradeIntelligencePage />
 *   </FeatureLock>
 */
export function FeatureLock({ featureName, requiredPlan = "Enterprise", children, isLocked }: FeatureLockProps) {
    if (!isLocked) return <>{children}</>;

    return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center max-w-md px-8 py-12 bg-[#0e1e33]/50 border border-navy-700/30 rounded-2xl">
                <div className="mx-auto w-16 h-16 rounded-full bg-navy-800 flex items-center justify-center mb-6">
                    <Lock className="h-8 w-8 text-[#f5a623]" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{featureName}</h3>
                <p className="text-navy-400 text-sm mb-6">
                    This feature is available on the <span className="text-[#f5a623] font-semibold">{requiredPlan}</span> plan and above.
                </p>
                <Link
                    href="/pricing"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-[#f5a623] text-navy-950 rounded-xl font-semibold text-sm hover:bg-gold-300 transition-all"
                >
                    Upgrade Plan <ArrowRight className="h-4 w-4" />
                </Link>
                <p className="text-xs text-navy-600 mt-4">
                    Not sure? Contact sales for a free demo.
                </p>
            </div>
        </div>
    );
}

/**
 * Feature lock button — shows a locked button with tooltip.
 * Usage:
 *   <FeatureLockButton featureName="AI Vision" />
 */
export function FeatureLockButton({ featureName, requiredPlan = "Enterprise" }: { featureName: string; requiredPlan?: string }) {
    return (
        <div className="relative group cursor-not-allowed">
            <button
                disabled
                className="px-4 py-2 rounded-lg bg-navy-800/50 border border-navy-700/30 text-navy-500 flex items-center gap-2 opacity-60"
            >
                <Lock className="h-3.5 w-3.5" />
                {featureName}
            </button>
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-navy-800 border border-navy-600 rounded-lg text-xs text-[#f5a623] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                Requires {requiredPlan} plan
            </div>
        </div>
    );
}
