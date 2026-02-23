import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronRight } from "lucide-react";

// Dummy data
const leads = [
    { id: 1, name: "Ahmed Al-Mansouri", company: "Al Maya Group", status: "New Lead", source: "Gulfood 2026", confidence: 85 },
    { id: 2, name: "Sarah Johnson", company: "Waitrose UAE", status: "Negotiating", source: "LinkedIn", confidence: 92 },
    { id: 3, name: "Rahul Gupta", company: "Choithrams", status: "Closed", source: "Website", confidence: 98 },
    { id: 4, name: "Elena Petrova", company: "Spinneys", status: "Warm Lead", source: "Smart Scanner", confidence: 75 },
];

interface RecentLeadsProps {
    className?: string;
}

const RecentLeads = ({ className }: RecentLeadsProps) => {
    return (
        <Card className={`col-span-3 border-[#1e3a5f] bg-[#0e1e33] text-white ${className || ''}`}>
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg font-medium text-white">Recent Leads</CardTitle>
                <Button variant="ghost" size="sm" className="text-[#f5a623] hover:text-gold-300">
                    View All <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {leads.map((lead) => (
                        <div key={lead.id} className="flex items-center justify-between border-b border-[#1e3a5f] pb-4 last:border-0 last:pb-0">
                            <div>
                                <p className="font-medium text-white">{lead.name}</p>
                                <p className="text-sm text-gray-400">{lead.company}</p>
                            </div>
                            <div className="flex items-center space-x-4">
                                <span className={`text-xs px-2 py-1 rounded-full ${lead.status === "New Lead" ? "bg-blue-500/10 text-blue-400" :
                                        lead.status === "Negotiating" ? "bg-gold-500/10 text-[#f5a623]" :
                                            lead.status === "Closed" ? "bg-green-500/10 text-green-400" :
                                                "bg-gray-500/10 text-gray-400"
                                    }`}>
                                    {lead.status}
                                </span>
                                <div className="text-right">
                                    <p className="text-xs text-gray-400">Confidence</p>
                                    <div className="h-1.5 w-16 bg-navy-800 rounded-full mt-1">
                                        <div className="h-1.5 bg-[#f5a623] rounded-full" style={{ width: `${lead.confidence}%` }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};

export default RecentLeads;
