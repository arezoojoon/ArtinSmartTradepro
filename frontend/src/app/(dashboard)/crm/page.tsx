"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
    Briefcase, Target, PhoneCall, AlertCircle, TrendingUp, 
    Send, MessageCircle, Bot, CheckCircle2, Globe, Languages, Zap
} from "lucide-react";

export default function FardFoodstuffCRM() {
    return (
        <div className="min-h-screen bg-[#050A15] text-slate-300 p-4 md:p-8 pt-6 space-y-8">
            
            {/* Header: Personalized for Fard Foodstuff */}
            <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 border-b border-[#1E293B] pb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-[#D4AF37]/10 rounded-md border border-[#D4AF37]/30 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
                            <Target className="h-6 w-6 text-[#D4AF37]" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white uppercase">Sales Execution Hub</h2>
                    </div>
                    <p className="text-[#94A3B8] text-sm">
                        Managing 250+ Gulfood Leads | Active Campaigns: Pistachio & Dates
                    </p>
                </div>
                <div className="flex items-center gap-2 bg-[#0F172A] border border-[#1E293B] p-2 rounded-lg">
                    <Badge className="bg-emerald-500/10 text-emerald-400 border-none font-mono text-[10px]">
                        <Bot className="w-3 h-3 mr-1"/> WAHA AI Agents Active
                    </Badge>
                </div>
            </div>

            {/* Gulfood Campaign Live Feed */}
            <div className="grid lg:grid-cols-12 gap-8">
                
                {/* 1. KANBAN / LEADS SUMMARY */}
                <div className="lg:col-span-7 space-y-6">
                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-[#D4AF37] to-transparent opacity-70"></div>
                        <CardHeader className="pb-4 border-b border-[#1E293B]">
                            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
                                <Briefcase className="h-5 w-5 text-[#D4AF37]" /> Gulfood Expo 2026 Pipeline
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="space-y-4">
                                {/* Lead 1: Russian */}
                                <div className="p-4 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <h4 className="font-bold text-white text-md">ELITE GROUPS (Fayuzulleov)</h4>
                                            <p className="text-xs text-[#94A3B8] flex items-center gap-1 mt-1">
                                                <Globe className="w-3 h-3 text-blue-400"/> Moscow, Russia
                                            </p>
                                        </div>
                                        <Badge className="bg-[#D4AF37]/10 text-[#D4AF37] border border-[#D4AF37]/30">Hot Lead</Badge>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase tracking-widest block">AI Extracted Interest</span>
                                            <span className="font-semibold text-white">Akbari Pistachios, 20ft FCL</span>
                                        </div>
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase tracking-widest block">Action Status</span>
                                            <span className="text-emerald-400 flex items-center gap-1 text-xs font-medium">
                                                <CheckCircle2 className="w-3 h-3"/> Pitch sent in Russian
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Lead 2: India */}
                                <div className="p-4 bg-[#050A15] border border-[#1E293B] rounded-lg hover:border-[#D4AF37]/50 transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <h4 className="font-bold text-white text-md">CHAMAN DRY FRUITS</h4>
                                            <p className="text-xs text-[#94A3B8] flex items-center gap-1 mt-1">
                                                <Globe className="w-3 h-3 text-orange-400"/> Mumbai, India
                                            </p>
                                        </div>
                                        <Badge className="bg-purple-500/10 text-purple-400 border border-purple-500/30">Negotiating</Badge>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase tracking-widest block">AI Extracted Interest</span>
                                            <span className="font-semibold text-white">Mazafati Dates, Saffron</span>
                                        </div>
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase tracking-widest block">Action Status</span>
                                            <span className="text-blue-400 flex items-center gap-1 text-xs font-medium">
                                                <MessageCircle className="w-3 h-3"/> Buyer requested FOB price
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <Button className="w-full mt-6 bg-transparent border border-[#1E293B] text-slate-300 hover:bg-[#1E293B] h-10 text-xs uppercase tracking-widest">
                                View All 250+ Gulfood Leads
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                {/* 2. WAHA AUTOPILOT TERMINAL (RIGHT) */}
                <div className="lg:col-span-5 space-y-6">
                    <Card className="bg-[#0F172A] border-[#1E293B] shadow-2xl h-full relative overflow-hidden">
                        <CardHeader className="pb-4 border-b border-[#1E293B] bg-[#0A0F1C]">
                            <CardTitle className="text-md font-medium text-white flex items-center gap-2">
                                <Bot className="h-5 w-5 text-emerald-400" /> WhatsApp AI Autopilot
                            </CardTitle>
                            <CardDescription className="text-xs text-slate-400 mt-1">
                                AI is currently engaging Cold Leads based on localized playbooks.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-6">
                            
                            {/* Live Simulation of AI Chat */}
                            <div className="space-y-4">
                                <div className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-2 flex items-center gap-2">
                                    <Languages className="w-3 h-3 text-[#D4AF37]"/> Auto-Translation & Pitching
                                </div>
                                
                                <div className="bg-[#050A15] p-4 rounded-lg border border-[#1E293B] relative">
                                    <div className="absolute -left-2 -top-2 bg-blue-500 text-white text-[9px] font-bold px-2 py-1 rounded">TO: ELITE GROUPS (RU)</div>
                                    <p className="text-sm text-slate-300 mt-2 font-serif italic border-l-2 border-[#D4AF37] pl-3">
                                        "Здравствуйте! Мы познакомились на выставке Gulfood. У нас есть свежие фисташки Акбари с поставкой в Москву. Цена FOB Джебель-Али: $9.8/кг. Отправить цифровой каталог?"
                                    </p>
                                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-[#1E293B]">
                                        <span className="text-[10px] text-slate-500">Generated by Sales AI Agent</span>
                                        <Badge className="bg-emerald-500/10 text-emerald-400 border-none text-[10px]"><CheckCircle2 className="w-3 h-3 mr-1"/> Delivered on WA</Badge>
                                    </div>
                                </div>

                                <div className="bg-[#050A15] p-4 rounded-lg border border-[#1E293B] relative">
                                    <div className="absolute -left-2 -top-2 bg-orange-500 text-white text-[9px] font-bold px-2 py-1 rounded">TO: MAXONSNUTS (UAE)</div>
                                    <p className="text-sm text-slate-300 mt-2 font-serif italic border-l-2 border-[#D4AF37] pl-3">
                                        "مرحباً، بناءً على طلبكم في جلفود، نرفق لكم كتالوج المكسرات. التسليم متاح فوراً من مستودعنا في دبي."
                                    </p>
                                    <div className="flex justify-between items-center mt-3 pt-3 border-t border-[#1E293B]">
                                        <span className="text-[10px] text-slate-500">Generated by Sales AI Agent</span>
                                        <Badge className="bg-emerald-500/10 text-emerald-400 border-none text-[10px]"><CheckCircle2 className="w-3 h-3 mr-1"/> Delivered on WA</Badge>
                                    </div>
                                </div>
                            </div>

                            <Button className="w-full h-12 bg-[#D4AF37] text-[#050A15] hover:bg-[#F3E5AB] font-bold uppercase tracking-wider shadow-[0_0_20px_rgba(212,175,55,0.3)]">
                                <Zap className="w-4 h-4 mr-2"/> Start Mass Outreach for 250 Leads
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
