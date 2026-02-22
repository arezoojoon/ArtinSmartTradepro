import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, TrendingUp, DollarSign, Users, Activity } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
    return (
        <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                {/* استفاده از text-foreground برای جلوگیری از نامرئی شدن متن */}
                <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                    Control Tower
                </h2>
            </div>

            {/* Mobile Control Tower: 
        فقط ۵ ویجت حیاتی برای تصمیمگیری سریع روی موبایل 
      */}
            <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">

                {/* 1. Today Opportunities */}
                <Card className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border-l-4 border-l-blue-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Opportunities</CardTitle>
                        <TrendingUp className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">3 High Margin</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">UAE to EU • 18% Est. Margin</p>
                        <Link href="/brain" className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-2 inline-block font-semibold">
                            Review in Brain &rarr;
                        </Link>
                    </CardContent>
                </Card>

                {/* 2. Risk Alerts */}
                <Card className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border-l-4 border-l-red-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Risk Alerts</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600 dark:text-red-400">2 Critical</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Port Delays & Customs Flags</p>
                        <Link href="/settings/notifications" className="text-xs text-red-600 dark:text-red-400 hover:underline mt-2 inline-block font-semibold">
                            Take Action &rarr;
                        </Link>
                    </CardContent>
                </Card>

                {/* 3. Cash Flow Status */}
                <Card className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border-l-4 border-l-emerald-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Cash Flow</CardTitle>
                        <DollarSign className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">$124,500</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">In 7 Days (DSO: 42 days)</p>
                        <Link href="/wallet" className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline mt-2 inline-block font-semibold">
                            View Wallet &rarr;
                        </Link>
                    </CardContent>
                </Card>

                {/* 4. New Leads (Hunter) */}
                <Card className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border-l-4 border-l-purple-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">New Leads</CardTitle>
                        <Users className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">12 Qualified</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Hunter Score {'>'} 80</p>
                        <Link href="/crm" className="text-xs text-purple-600 dark:text-purple-400 hover:underline mt-2 inline-block font-semibold">
                            Open CRM &rarr;
                        </Link>
                    </CardContent>
                </Card>

                {/* 5. Market Shocks */}
                <Card className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-md border-l-4 border-l-orange-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Market Shocks</CardTitle>
                        <Activity className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">+2.4% FX</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">AED/USD Volatility Triggered</p>
                        <Link href="/toolbox/fx" className="text-xs text-orange-600 dark:text-orange-400 hover:underline mt-2 inline-block font-semibold">
                            Analyze Impact &rarr;
                        </Link>
                    </CardContent>
                </Card>
            </div>

            {/* Desktop Only: Drill-down & Analytics 
        این بخش در دسکتاپ دیده میشود تا مدیر بتواند ساختار را کامل ببیند 
      */}
            <div className="hidden lg:grid gap-4 grid-cols-7 mt-8">

                {/* Pipeline Summary */}
                <Card className="col-span-4 bg-white dark:bg-slate-900 shadow-md">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white">Pipeline Summary (CRM)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Conversion Rate</span>
                                <span className="text-sm font-bold text-slate-900 dark:text-white">24%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-6 relative overflow-hidden flex">
                                <div className="bg-blue-500 h-6 flex items-center justify-center text-[10px] text-white font-bold" style={{ width: '40%' }}>Leads</div>
                                <div className="bg-purple-500 h-6 flex items-center justify-center text-[10px] text-white font-bold" style={{ width: '30%' }}>Quoted</div>
                                <div className="bg-emerald-500 h-6 flex items-center justify-center text-[10px] text-white font-bold" style={{ width: '30%' }}>Won</div>
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-center mt-4">
                                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border dark:border-slate-700">
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Total Pipeline</p>
                                    <p className="text-lg font-bold text-slate-900 dark:text-white">$850K</p>
                                </div>
                                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border dark:border-slate-700">
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Gross Margin</p>
                                    <p className="text-lg font-bold text-slate-900 dark:text-white">18.5%</p>
                                </div>
                                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded border dark:border-slate-700">
                                    <p className="text-xs text-slate-500 dark:text-slate-400">Active Deals</p>
                                    <p className="text-lg font-bold text-slate-900 dark:text-white">24</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* AI Risk Heatmap */}
                <Card className="col-span-3 bg-white dark:bg-slate-900 shadow-md">
                    <CardHeader>
                        <CardTitle className="text-slate-900 dark:text-white">AI Risk Heatmap</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-950/30 rounded-md border border-red-200 dark:border-red-900/50">
                            <div>
                                <span className="block text-sm font-bold text-red-800 dark:text-red-300">Customs Alert (Turkey)</span>
                                <span className="block text-xs text-red-600 dark:text-red-400">HS Code mismatch detected in recent exports.</span>
                            </div>
                            <span className="text-xs bg-red-600 text-white px-2 py-1 rounded-full font-bold shadow-sm">High</span>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-950/30 rounded-md border border-yellow-200 dark:border-yellow-900/50">
                            <div>
                                <span className="block text-sm font-bold text-yellow-800 dark:text-yellow-300">Supplier Delay (CN)</span>
                                <span className="block text-xs text-yellow-600 dark:text-yellow-400">Reliability score dropped by 4%.</span>
                            </div>
                            <span className="text-xs bg-yellow-500 text-white px-2 py-1 rounded-full font-bold shadow-sm">Medium</span>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-md border border-emerald-200 dark:border-emerald-900/50">
                            <div>
                                <span className="block text-sm font-bold text-emerald-800 dark:text-emerald-300">Buyer Behavior (AE)</span>
                                <span className="block text-xs text-emerald-600 dark:text-emerald-400">Payment on-time rate {'>'} 95%.</span>
                            </div>
                            <span className="text-xs bg-emerald-500 text-white px-2 py-1 rounded-full font-bold shadow-sm">Safe</span>
                        </div>
                        <p className="text-xs text-right text-slate-400 italic">Data confidentially level: 89%</p>
                    </CardContent>
                </Card>

            </div>
        </div>
    );
}
