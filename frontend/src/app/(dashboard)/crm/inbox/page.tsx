"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Send, User, Bot, Check, CheckCheck, Phone, Filter, ShieldAlert } from "lucide-react";
import api from "@/lib/api";

export default function WhatsAppInbox() {
    const [conversations, setConversations] = useState<any[]>([]);
    const [activeConv, setActiveConv] = useState<any>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [replyText, setReplyText] = useState("");
    const [loadingConvs, setLoadingConvs] = useState(true);
    const [loadingMsgs, setLoadingMsgs] = useState(false);
    const [search, setSearch] = useState("");
    const [togglingBot, setTogglingBot] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchConversations();
        const interval = setInterval(fetchConversations, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (activeConv) {
            fetchMessages(activeConv.id);
            const interval = setInterval(() => fetchMessages(activeConv.id), 5000); // Poll msgs
            return () => clearInterval(interval);
        }
    }, [activeConv]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const fetchConversations = async () => {
        try {
            const { data } = await api.get("/whatsapp/conversations");
            setConversations(data);
            if (data.length > 0 && !activeConv) {
                setActiveConv(data[0]);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingConvs(false);
        }
    };

    const fetchMessages = async (convId: string) => {
        try {
            const { data } = await api.get(`/whatsapp/conversations/${convId}/messages`);
            setMessages(data);
        } catch (err) {
            console.error(err);
        }
    };

    const [sendError, setSendError] = useState<string | null>(null);

    const sendMessage = async () => {
        if (!replyText.trim() || !activeConv) return;
        setSendError(null);

        try {
            await api.post("/whatsapp/send", {
                recipient_phone: activeConv.identifier,
                template_name: null,
                components: null,
                text_fallback: replyText
            });
            setReplyText("");
            fetchMessages(activeConv.id);
        } catch (err) {
            setSendError("Connection error. Please try again.");
            setTimeout(() => setSendError(null), 5000);
        }
    };

    const toggleBotMode = async () => {
        if (!activeConv || togglingBot) return;
        setTogglingBot(true);
        try {
            const newStatus = activeConv.status === 'bot_handled' ? 'needs_human' : 'bot_handled';
            await api.patch(`/whatsapp/conversations/${activeConv.id}/status`, { status: newStatus });
            setActiveConv({ ...activeConv, status: newStatus });
            fetchConversations();
        } catch (err) { console.error(err); }
        finally { setTogglingBot(false); }
    };

    const filteredConvs = conversations.filter(c =>
        c.identifier.includes(search) ||
        (c.contact_name && c.contact_name.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <div className="flex flex-col h-[calc(100vh-theme(spacing.20))] max-w-7xl mx-auto p-4 md:p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Phone className="h-6 w-6 text-green-500" />
                        WhatsApp Inbox
                    </h1>
                    <p className="text-sm text-navy-300">Manage conversations and intercept AI flows</p>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden bg-[#0e1e33] border border-navy-700/50 rounded-2xl shadow-xl">
                {/* Sidebar */}
                <div className="w-1/3 flex flex-col border-r border-[#1e3a5f] bg-navy-950/50">
                    <div className="p-4 border-b border-[#1e3a5f]">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
                            <input
                                type="text"
                                placeholder="Search phone or name..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 bg-[#0e1e33] border border-navy-700 rounded-lg text-white text-sm focus:border-green-500 focus:outline-none transition-colors"
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {loadingConvs ? (
                            <div className="p-8 text-center text-navy-500">Loading...</div>
                        ) : filteredConvs.length === 0 ? (
                            <div className="p-8 text-center text-navy-500">No conversations</div>
                        ) : (
                            <div className="divide-y divide-navy-800">
                                {filteredConvs.map(conv => (
                                    <div
                                        key={conv.id}
                                        onClick={() => setActiveConv(conv)}
                                        className={`p-4 cursor-pointer hover:bg-navy-800 transition-colors ${activeConv?.id === conv.id ? 'bg-navy-800 border-l-2 border-green-500' : ''}`}
                                    >
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="font-semibold text-white truncate pr-2">
                                                {conv.contact_name || "+" + conv.identifier}
                                            </span>
                                            <span className="text-xs text-navy-400 whitespace-nowrap">
                                                {new Date(conv.last_message_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        {conv.contact_name && (
                                            <div className="text-xs text-navy-400 mb-1">+{conv.identifier}</div>
                                        )}
                                        <div className="flex items-center gap-2 mt-2">
                                            {conv.status === 'needs_human' && (
                                                <span className="px-2 py-0.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded text-[10px] font-bold flex items-center gap-1">
                                                    <ShieldAlert className="h-3 w-3" /> Needs Human
                                                </span>
                                            )}
                                            {conv.status === 'bot_handled' && (
                                                <span className="px-2 py-0.5 bg-navy-700 rounded text-[10px] text-navy-300 flex items-center gap-1">
                                                    <Bot className="h-3 w-3" /> Bot
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Chat Area */}
                {activeConv ? (
                    <div className="flex-1 flex flex-col bg-[url('/whatsapp-bg.png')] bg-cover relative">
                        <div className="absolute inset-0 bg-[#0e1e33]/90 z-0"></div>

                        {/* Chat Header */}
                        <div className="relative z-10 px-6 py-4 bg-navy-950 border-b border-[#1e3a5f] flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <div className="h-10 w-10 bg-navy-800 rounded-full flex items-center justify-center">
                                    <User className="h-5 w-5 text-navy-400" />
                                </div>
                                <div>
                                    <h2 className="font-bold text-white">{activeConv.contact_name || "+" + activeConv.identifier}</h2>
                                    <p className="text-xs text-navy-400 flex items-center gap-1">
                                        {activeConv.status === 'needs_human' ? <ShieldAlert className="h-3 w-3 text-red-400" /> : <Bot className="h-3 w-3 text-green-400" />}
                                        {activeConv.status === 'needs_human' ? 'Handoff Requested' : 'AI Handled'}
                                    </p>
                                </div>
                            </div>
                            <button onClick={toggleBotMode} disabled={togglingBot} className={`px-3 py-1.5 border rounded-lg text-xs font-semibold transition-colors ${activeConv.status === 'bot_handled' ? 'bg-red-500/20 hover:bg-red-500/30 border-red-500/30 text-red-400' : 'bg-green-500/20 hover:bg-green-500/30 border-green-500/30 text-green-400'}`}>
                                {togglingBot ? "Switching..." : activeConv.status === 'bot_handled' ? "Take Over (Human Mode)" : "Resume Bot Mode"}
                            </button>
                        </div>

                        {/* Messages Area */}
                        <div className="relative z-10 flex-1 overflow-y-auto p-6 space-y-4">
                            {messages.map((msg, idx) => {
                                const isOutbound = msg.direction === 'outbound';
                                return (
                                    <div key={idx} className={`flex ${isOutbound ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[70%] rounded-xl px-4 py-2 relative shadow-sm ${isOutbound
                                                ? 'bg-green-600 text-white rounded-tr-none'
                                                : 'bg-navy-800 text-gray-100 rounded-tl-none border border-navy-700'
                                            }`}>
                                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                                            <div className="flex items-center justify-end gap-1 mt-1 opacity-70">
                                                <span className="text-[10px]">
                                                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                                {isOutbound && (
                                                    msg.status === 'read' ? <CheckCheck className="h-3 w-3 text-blue-300" /> :
                                                        msg.status === 'delivered' ? <CheckCheck className="h-3 w-3" /> :
                                                            <Check className="h-3 w-3" />
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="relative z-10 p-4 bg-navy-950 border-t border-[#1e3a5f]">
                            {sendError && (
                                <div className="mb-3 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center justify-between">
                                    <span className="text-red-400 text-sm">{sendError}</span>
                                    <button onClick={() => setSendError(null)} className="text-red-400 hover:text-red-300 ml-2">&times;</button>
                                </div>
                            )}
                            <form
                                onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
                                className="flex gap-3 max-w-4xl mx-auto"
                            >
                                <input
                                    type="text"
                                    value={replyText}
                                    onChange={(e) => setReplyText(e.target.value)}
                                    placeholder="Type a message..."
                                    className="flex-1 bg-[#0e1e33] border border-navy-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-green-500 transition-colors"
                                />
                                <button
                                    type="submit"
                                    disabled={!replyText.trim()}
                                    className="bg-green-600 hover:bg-green-500 text-white px-5 rounded-xl font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors shadow-lg"
                                >
                                    <Send className="h-5 w-5" />
                                </button>
                            </form>
                            {activeConv.status !== 'needs_human' && (
                                <p className="text-center text-[10px] text-navy-400 mt-2">
                                    Sending a message will automatically lock the AI bot and transition to human mode.
                                </p>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center bg-[#0e1e33] z-10 bg-[url('/whatsapp-bg.png')] bg-cover relative">
                        <div className="absolute inset-0 bg-[#0e1e33]/90 z-0"></div>
                        <div className="relative z-10 text-center">
                            <Phone className="h-20 w-20 text-navy-700 mx-auto mb-4" />
                            <h2 className="text-xl font-bold text-white">No Conversation Selected</h2>
                            <p className="text-navy-400 mt-2">Choose a chat from the sidebar to start messaging</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
