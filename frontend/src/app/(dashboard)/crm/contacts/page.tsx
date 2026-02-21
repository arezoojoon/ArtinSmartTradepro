"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Filter, MoreHorizontal, User, Mail, Phone, MapPin, Building2 } from "lucide-react";
import { BASE_URL } from "@/lib/api";

export default function ContactsPage() {
    const [contacts, setContacts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => {
        fetchContacts();
    }, [search]);

    const fetchContacts = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            const query = search ? `?search=${search}` : "";
            const res = await fetch(`${BASE_URL}/crm/contacts${query}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setContacts(data.contacts || []);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">Contacts</h1>
                    <p className="text-sm text-navy-400">Manage individual people and connections</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-gold-400 text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    Add Contact
                </button>
            </div>

            <div className="mb-6 flex gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
                    <input
                        type="text"
                        placeholder="Search contacts by name, email, or phone..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-navy-900 border border-navy-700 rounded-lg text-white focus:border-gold-400 focus:outline-none"
                    />
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-navy-800 border border-navy-700 rounded-lg text-navy-300 hover:bg-navy-700">
                    <Filter className="h-4 w-4" />
                    Filters
                </button>
            </div>

            <div className="bg-navy-900 border border-navy-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-navy-950 text-navy-400">
                        <tr>
                            <th className="px-6 py-4 font-medium">Name</th>
                            <th className="px-6 py-4 font-medium">Contact Info</th>
                            <th className="px-6 py-4 font-medium">Position</th>
                            <th className="px-6 py-4 font-medium relative"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-800">
                        {loading ? (
                            <tr><td colSpan={4} className="px-6 py-8 text-center text-navy-500">Loading contacts...</td></tr>
                        ) : contacts.length === 0 ? (
                            <tr><td colSpan={4} className="px-6 py-8 text-center text-navy-500">No contacts found</td></tr>
                        ) : (
                            contacts.map((contact: any) => (
                                <tr key={contact.id} className="hover:bg-navy-800/50 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-navy-700 flex items-center justify-center text-white">
                                                <User className="h-4 w-4" />
                                            </div>
                                            <div>
                                                <div className="font-medium text-white">{contact.first_name} {contact.last_name}</div>
                                                <div className="text-xs text-navy-400 flex items-center gap-1 mt-0.5"><Building2 className="h-3 w-3" /> {contact.company?.name || "No Company"}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="space-y-1">
                                            {contact.email && <div className="flex items-center gap-2 text-navy-300"><Mail className="h-3 w-3" /> {contact.email}</div>}
                                            {contact.phone && <div className="flex items-center gap-2 text-navy-300"><Phone className="h-3 w-3" /> {contact.phone}</div>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-navy-300">
                                        {contact.position ? (
                                            <div className="px-2.5 py-1 rounded-full bg-navy-800 border border-navy-700 text-xs inline-block">
                                                {contact.position}
                                            </div>
                                        ) : "-"}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="p-2 hover:bg-navy-700 rounded-lg text-navy-400 hover:text-white opacity-0 group-hover:opacity-100 transition-all">
                                            <MoreHorizontal className="h-4 w-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}