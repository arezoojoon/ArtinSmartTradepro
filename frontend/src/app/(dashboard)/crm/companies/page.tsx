"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Filter, MoreHorizontal, Building2, MapPin, Globe, Linkedin } from "lucide-react";

export default function CompaniesPage() {
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => {
        fetchCompanies();
    }, [search]);

    const fetchCompanies = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            const query = search ? `?search=${search}` : "";
            const res = await fetch(`http://localhost:8000/api/v1/crm/companies${query}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setCompanies(data);
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
                    <h1 className="text-2xl font-bold text-white">Companies</h1>
                    <p className="text-sm text-navy-400">Manage client organizations</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-gold-400 text-navy-950 rounded-lg font-semibold hover:bg-gold-500 transition-colors">
                    <Plus className="h-4 w-4" />
                    Add Company
                </button>
            </div>

            <div className="mb-6 flex gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
                    <input
                        type="text"
                        placeholder="Search companies..."
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
                            <th className="px-6 py-4 font-medium">Company Name</th>
                            <th className="px-6 py-4 font-medium">Industry</th>
                            <th className="px-6 py-4 font-medium">Location</th>
                            <th className="px-6 py-4 font-medium">Website</th>
                            <th className="px-6 py-4 font-medium relative"><span className="sr-only">Actions</span></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-800">
                        {loading ? (
                            <tr><td colSpan={5} className="px-6 py-8 text-center text-navy-500">Loading companies...</td></tr>
                        ) : companies.length === 0 ? (
                            <tr><td colSpan={5} className="px-6 py-8 text-center text-navy-500">No companies found</td></tr>
                        ) : (
                            companies.map((company: any) => (
                                <tr key={company.id} className="hover:bg-navy-800/50 transition-colors group">
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-lg bg-navy-700 flex items-center justify-center text-white">
                                                <Building2 className="h-4 w-4" />
                                            </div>
                                            <div>
                                                <div className="font-medium text-white">{company.name}</div>
                                                <div className="text-xs text-navy-400">{company.size || "Unknown size"}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-navy-300">{company.industry || "-"}</td>
                                    <td className="px-6 py-4 text-navy-300">
                                        {company.country && <div className="flex items-center gap-2"><MapPin className="h-3 w-3" />{company.city ? `${company.city}, ` : ""}{company.country}</div>}
                                    </td>
                                    <td className="px-6 py-4 text-navy-300">
                                        <div className="flex items-center gap-3">
                                            {company.website && <a href={company.website} target="_blank" className="text-navy-400 hover:text-gold-400"><Globe className="h-4 w-4" /></a>}
                                            {company.linkedin_url && <a href={company.linkedin_url} target="_blank" className="text-navy-400 hover:text-blue-400"><Linkedin className="h-4 w-4" /></a>}
                                        </div>
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
