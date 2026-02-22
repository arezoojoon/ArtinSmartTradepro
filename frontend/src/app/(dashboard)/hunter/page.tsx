"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Globe, Loader2, Check, Target, Briefcase, Radar, ShoppingCart, TrendingUp, Scale, Send, Factory, ShieldCheck, Calculator } from "lucide-react";

export default function HunterPage() {
    // Shared State
    const [keyword, setKeyword] = useState("Macaroni / Pasta");
    const [status, setStatus] = useState<"idle" | "processing" | "completed">("idle");
    const [activeTab, setActiveTab] = useState("sourcing");

    // Mock Start Search
    const startHunt = () => {
        setStatus("processing");
        setTimeout(() => setStatus("completed"), 2500);
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-8 pt-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                        Hunter Engine <Radar className="h-6 w-6 text-indigo-500" />
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Role-Based Intelligence & Lead Generation</p>
                </div>

                {/* نمایش دسترسی کاربر بر اساس معماری شما */}
                <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider pl-2">Current Role:</span>
                    <Badge className="bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300 hover:bg-indigo-200">Trade Manager (Full Access)</Badge>
                </div>
            </div>

            {/* Role-Based Tabs */}
            <Tabs defaultValue="sourcing" onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-2 h-14 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
                    <TabsTrigger value="sourcing" className="rounded-lg text-sm md:text-base font-bold data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:text-emerald-600 dark:data-[state=active]:text-emerald-400 data-[state=active]:shadow-sm">
                        <ShoppingCart className="w-5 h-5 mr-2" />
                        Sourcing Mode (من میخواهم بخرم)
                    </TabsTrigger>
                    <TabsTrigger value="sales" className="rounded-lg text-sm md:text-base font-bold data-[state=active]:bg-white dark:data-[state=active]:bg-slate-900 data-[state=active]:text-blue-600 dark:data-[state=active]:text-blue-400 data-[state=active]:shadow-sm">
                        <TrendingUp className="w-5 h-5 mr-2" />
                        Sales Mode (من میخواهم بفروشم)
                    </TabsTrigger>
                </TabsList>

                {/* ========================================== */}
                {/* SOURCING MODE: پیدا کردن تولیدکننده و مقایسه */}
                {/* ========================================== */}
                <TabsContent value="sourcing" className="space-y-6 mt-6">
                    <Card className="bg-white dark:bg-slate-900 shadow-sm border-emerald-100 dark:border-emerald-900/30">
                        <CardContent className="pt-6 grid md:grid-cols-4 gap-4 items-end">
                            <div className="md:col-span-2 space-y-2">
                                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Target Product to Buy</label>
                                <Input value={keyword} onChange={(e) => setKeyword(e.target.value)} className="bg-slate-50 dark:bg-slate-950 dark:border-slate-800" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Quality Standard</label>
                                <Select defaultValue="premium">
                                    <SelectTrigger className="bg-slate-50 dark:bg-slate-950 dark:border-slate-800"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="premium">Premium (Grade A)</SelectItem>
                                        <SelectItem value="standard">Standard Commercial</SelectItem>
                                        <SelectItem value="economic">Economy / Low Cost</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <Button onClick={startHunt} disabled={status === "processing"} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white h-10">
                                {status === "processing" ? <Loader2 className="animate-spin h-5 w-5" /> : <><Scale className="mr-2 h-4 w-4" /> Find & Compare Suppliers</>}
                            </Button>
                        </CardContent>
                    </Card>

                    {status === "completed" && activeTab === "sourcing" && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Calculator className="h-5 w-5 text-emerald-500" /> AI Supplier Comparison (FOB vs CIF Dubai)
                            </h3>
                            <div className="grid md:grid-cols-3 gap-6">
                                {/* Supplier 1 */}
                                <Card className="border-2 border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg">BEST VALUE</div>
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg flex items-center gap-2 text-slate-900 dark:text-white"><Factory className="h-4 w-4 text-emerald-600" /> Ankara Pasta Co.</CardTitle>
                                        <CardDescription className="text-slate-500 flex items-center gap-1"><Globe className="h-3 w-3" /> Turkey (Mersin Port)</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-3 text-sm">
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Quality Score:</span>
                                            <span className="font-bold flex items-center gap-1 text-slate-900 dark:text-white"><ShieldCheck className="h-4 w-4 text-blue-500" /> 8.5/10</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Price (FOB):</span>
                                            <span className="font-bold text-slate-900 dark:text-white">$680 / MT</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Est. Freight to DXB:</span>
                                            <span className="font-bold text-orange-600 dark:text-orange-400">+$45 / MT</span>
                                        </div>
                                        <div className="flex justify-between pt-1">
                                            <span className="font-bold text-slate-900 dark:text-white">Est. Landed (CIF):</span>
                                            <span className="font-bold text-emerald-600 text-lg">$725 / MT</span>
                                        </div>
                                        <Button className="w-full mt-4 bg-emerald-600 hover:bg-emerald-700" size="sm">Create RFQ</Button>
                                    </CardContent>
                                </Card>

                                {/* Supplier 2 */}
                                <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg flex items-center gap-2 text-slate-900 dark:text-white"><Factory className="h-4 w-4 text-slate-400" /> Barilla Export Div.</CardTitle>
                                        <CardDescription className="text-slate-500 flex items-center gap-1"><Globe className="h-3 w-3" /> Italy (Genoa Port)</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-3 text-sm">
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Quality Score:</span>
                                            <span className="font-bold flex items-center gap-1 text-slate-900 dark:text-white"><ShieldCheck className="h-4 w-4 text-blue-500" /> 9.8/10</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Price (FOB):</span>
                                            <span className="font-bold text-slate-900 dark:text-white">$850 / MT</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Est. Freight to DXB:</span>
                                            <span className="font-bold text-orange-600 dark:text-orange-400">+$85 / MT</span>
                                        </div>
                                        <div className="flex justify-between pt-1">
                                            <span className="font-bold text-slate-900 dark:text-white">Est. Landed (CIF):</span>
                                            <span className="font-bold text-slate-900 dark:text-white text-lg">$935 / MT</span>
                                        </div>
                                        <Button variant="outline" className="w-full mt-4 dark:border-slate-700 dark:text-slate-300" size="sm">Create RFQ</Button>
                                    </CardContent>
                                </Card>

                                {/* Supplier 3 */}
                                <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg flex items-center gap-2 text-slate-900 dark:text-white"><Factory className="h-4 w-4 text-slate-400" /> Zar Macaron</CardTitle>
                                        <CardDescription className="text-slate-500 flex items-center gap-1"><Globe className="h-3 w-3" /> Iran (Bandar Abbas)</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-3 text-sm">
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Quality Score:</span>
                                            <span className="font-bold flex items-center gap-1 text-slate-900 dark:text-white"><ShieldCheck className="h-4 w-4 text-yellow-500" /> 7.0/10</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Price (FOB):</span>
                                            <span className="font-bold text-slate-900 dark:text-white">$590 / MT</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                                            <span className="text-slate-600 dark:text-slate-400">Est. Freight to DXB:</span>
                                            <span className="font-bold text-emerald-600 dark:text-emerald-400">+$15 / MT</span>
                                        </div>
                                        <div className="flex justify-between pt-1">
                                            <span className="font-bold text-slate-900 dark:text-white">Est. Landed (CIF):</span>
                                            <span className="font-bold text-slate-900 dark:text-white text-lg">$605 / MT</span>
                                        </div>
                                        <Button variant="outline" className="w-full mt-4 dark:border-slate-700 dark:text-slate-300" size="sm">Create RFQ</Button>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    )}
                </TabsContent>

                {/* ========================================== */}
                {/* SALES MODE: پیدا کردن خریدار و ارسال کمپین */}
                {/* ========================================== */}
                <TabsContent value="sales" className="space-y-6 mt-6">
                    <Card className="bg-white dark:bg-slate-900 shadow-sm border-blue-100 dark:border-blue-900/30">
                        <CardContent className="pt-6 grid md:grid-cols-4 gap-4 items-end">
                            <div className="md:col-span-2 space-y-2">
                                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Product I want to Sell</label>
                                <Input value={keyword} onChange={(e) => setKeyword(e.target.value)} className="bg-slate-50 dark:bg-slate-950 dark:border-slate-800" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Target Buyer Region</label>
                                <Input defaultValue="Middle East & Africa" className="bg-slate-50 dark:bg-slate-950 dark:border-slate-800" />
                            </div>
                            <Button onClick={startHunt} disabled={status === "processing"} className="w-full bg-blue-600 hover:bg-blue-700 text-white h-10">
                                {status === "processing" ? <Loader2 className="animate-spin h-5 w-5" /> : <><Target className="mr-2 h-4 w-4" /> Find Importers / Buyers</>}
                            </Button>
                        </CardContent>
                    </Card>

                    {status === "completed" && activeTab === "sales" && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Briefcase className="h-5 w-5 text-blue-500" /> Qualified Global Buyers Found
                            </h3>
                            <div className="grid gap-4">
                                {/* Buyer 1 */}
                                <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 p-4">
                                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                        <div className="flex gap-4">
                                            <div className="w-12 h-12 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600 flex items-center justify-center font-bold text-xl border border-blue-100 dark:border-blue-800">C</div>
                                            <div>
                                                <h4 className="font-bold text-lg text-slate-900 dark:text-white">Carrefour Distribution (Majid Al Futtaim)</h4>
                                                <p className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-2">
                                                    <Globe className="w-3 h-3" /> UAE & GCC
                                                    <Badge variant="outline" className="text-[10px] dark:border-slate-700">Retail / Supermarket</Badge>
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 w-full md:w-auto">
                                            <div className="text-sm text-right hidden md:block">
                                                <div className="text-slate-500 dark:text-slate-400">Import Volume</div>
                                                <div className="font-bold text-slate-900 dark:text-white">Very High (Tier 1)</div>
                                            </div>
                                            <Button className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 gap-2">
                                                <Send className="w-4 h-4" /> Pitch via WhatsApp
                                            </Button>
                                        </div>
                                    </div>
                                </Card>

                                {/* Buyer 2 */}
                                <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 p-4">
                                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                                        <div className="flex gap-4">
                                            <div className="w-12 h-12 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-xl border border-slate-200 dark:border-slate-700">S</div>
                                            <div>
                                                <h4 className="font-bold text-lg text-slate-900 dark:text-white">Spinneys Hypermarket Suppy Chain</h4>
                                                <p className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-2">
                                                    <Globe className="w-3 h-3" /> Egypt & Lebanon
                                                    <Badge variant="outline" className="text-[10px] dark:border-slate-700">FMCG Distributor</Badge>
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 w-full md:w-auto">
                                            <div className="text-sm text-right hidden md:block">
                                                <div className="text-slate-500 dark:text-slate-400">Import Volume</div>
                                                <div className="font-bold text-slate-900 dark:text-white">High (Tier 2)</div>
                                            </div>
                                            <Button className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 gap-2">
                                                <Send className="w-4 h-4" /> Pitch via WhatsApp
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        </div>
                    )}
                </TabsContent>

            </Tabs>
        </div>
    );
}
