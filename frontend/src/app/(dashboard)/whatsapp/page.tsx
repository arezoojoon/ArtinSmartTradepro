"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { Send, MessageSquare } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

export default function WhatsAppPage() {
    const [recipient, setRecipient] = useState("");
    const [message, setMessage] = useState("");
    const [template, setTemplate] = useState("hello_world"); // Default template
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();

    const handleSend = async () => {
        if (!recipient || !message) return;
        setLoading(true);

        try {
            // MVP: Direct send via API
            await api.post("/whatsapp/send", {
                recipient_phone: recipient,
                content: message,
                template_name: template
            });
            toast({ title: "Message Sent", description: "WhatsApp message queued successfully." });
            setMessage("");
        } catch (error: any) {
            toast({
                title: "Failed to Send",
                description: error.response?.data?.detail || "Insufficient credits or invalid number.",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 p-6 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">
                <MessageSquare className="h-8 w-8 text-green-500" /> WhatsApp Engine
            </h1>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-[#0e1e33] border-[#1e3a5f] text-white">
                    <CardHeader>
                        <CardTitle>Send Message</CardTitle>
                        <CardDescription>Cost: 0.5 Credits per message</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="phone">Recipient Number</Label>
                            <Input
                                id="phone"
                                placeholder="e.g. 971501234567"
                                value={recipient}
                                onChange={(e) => setRecipient(e.target.value)}
                                className="bg-navy-800 border-navy-700"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="template">Template</Label>
                            <select
                                id="template"
                                className="w-full rounded-md border border-navy-700 bg-navy-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-gold-500"
                                value={template}
                                onChange={(e) => setTemplate(e.target.value)}
                            >
                                <option value="hello_world">Intro (Generic)</option>
                                <option value="trade_inquiry">Trade Inquiry</option>
                                <option value="meeting_request">Meeting Request</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="message">Message Body</Label>
                            <Textarea
                                id="message"
                                placeholder="Type your message..."
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                className="bg-navy-800 border-navy-700 min-h-[150px]"
                            />
                        </div>

                        <Button
                            className="w-full bg-green-600 text-white font-bold hover:bg-green-700"
                            disabled={loading}
                            onClick={handleSend}
                        >
                            <Send className="mr-2 h-4 w-4" />
                            {loading ? "Sending..." : "Send via WhatsApp API"}
                        </Button>
                    </CardContent>
                </Card>

                <Card className="bg-navy-800 border-navy-700 text-white">
                    <CardHeader>
                        <CardTitle>Preview</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="bg-[#e5ddd5] p-4 rounded-lg min-h-[300px] text-black bg-opacity-90 relative">
                            {/* Mock WhatsApp Bubble */}
                            <div className="bg-white keep-white p-3 rounded-lg rounded-tl-none shadow-sm max-w-[80%] mb-2">
                                <p className="text-sm">Hi! This is the template header.</p>
                            </div>
                            {message && (
                                <div className="bg-[#dcf8c6] p-3 rounded-lg rounded-tr-none shadow-sm max-w-[80%] ml-auto">
                                    <p className="text-sm">{message}</p>
                                    <span className="text-[10px] text-gray-500 block text-right">12:00 PM</span>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
