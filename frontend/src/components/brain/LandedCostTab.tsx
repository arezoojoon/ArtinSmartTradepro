'use client'

import { useState } from 'react'
import { Calculator, Ship, Shield, Warehouse, FileText, DollarSign, TrendingUp, TrendingDown, Loader2, AlertTriangle } from 'lucide-react'

interface CostLineItem {
  category: string
  description: string
  amount_usd: number
  percentage_of_total: number
  source: string
  notes?: string
}

interface LandedCostResult {
  product_name: string
  hs_code: string
  origin_country: string
  destination_country: string
  quantity_kg: number
  unit_price_usd: number
  product_cost_usd: number
  cost_items: CostLineItem[]
  total_additional_costs_usd: number
  total_landed_cost_usd: number
  landed_cost_per_kg_usd: number
  suggested_sell_price_per_kg: number
  estimated_profit_usd: number
  estimated_margin_pct: number
  confidence: number
  assumptions: string[]
  ai_notes: string
}

const COUNTRY_OPTIONS = [
  { code: 'CN', name: 'China 🇨🇳' },
  { code: 'AE', name: 'UAE 🇦🇪' },
  { code: 'IR', name: 'Iran 🇮🇷' },
  { code: 'TR', name: 'Turkey 🇹🇷' },
  { code: 'IN', name: 'India 🇮🇳' },
  { code: 'SA', name: 'Saudi Arabia 🇸🇦' },
  { code: 'OM', name: 'Oman 🇴🇲' },
  { code: 'QA', name: 'Qatar 🇶🇦' },
  { code: 'KW', name: 'Kuwait 🇰🇼' },
  { code: 'BH', name: 'Bahrain 🇧🇭' },
  { code: 'PK', name: 'Pakistan 🇵🇰' },
  { code: 'DE', name: 'Germany 🇩🇪' },
  { code: 'IT', name: 'Italy 🇮🇹' },
  { code: 'US', name: 'USA 🇺🇸' },
  { code: 'BR', name: 'Brazil 🇧🇷' },
  { code: 'RU', name: 'Russia 🇷🇺' },
  { code: 'KR', name: 'South Korea 🇰🇷' },
  { code: 'JP', name: 'Japan 🇯🇵' },
  { code: 'TH', name: 'Thailand 🇹🇭' },
  { code: 'VN', name: 'Vietnam 🇻🇳' },
  { code: 'MY', name: 'Malaysia 🇲🇾' },
  { code: 'ID', name: 'Indonesia 🇮🇩' },
  { code: 'EG', name: 'Egypt 🇪🇬' },
  { code: 'IQ', name: 'Iraq 🇮🇶' },
  { code: 'AF', name: 'Afghanistan 🇦🇫' },
]

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CNY', 'AED', 'IRR', 'TRY', 'SAR', 'INR']

const getCategoryIcon = (category: string) => {
  if (category.includes('Freight')) return <Ship className="w-4 h-4" />
  if (category.includes('Customs')) return <FileText className="w-4 h-4" />
  if (category.includes('Insurance')) return <Shield className="w-4 h-4" />
  if (category.includes('Warehousing')) return <Warehouse className="w-4 h-4" />
  return <DollarSign className="w-4 h-4" />
}

const getCategoryColor = (category: string) => {
  if (category.includes('Freight')) return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
  if (category.includes('Customs')) return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  if (category.includes('Insurance')) return 'bg-green-500/20 text-green-400 border-green-500/30'
  if (category.includes('Port')) return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
  if (category.includes('Warehousing')) return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
  if (category.includes('Documentation')) return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  if (category.includes('Tax')) return 'bg-red-500/20 text-red-400 border-red-500/30'
  return 'bg-slate-500/20 text-slate-400 border-slate-500/30'
}

const getBarColor = (category: string) => {
  if (category.includes('Freight')) return 'bg-blue-500'
  if (category.includes('Customs')) return 'bg-amber-500'
  if (category.includes('Insurance')) return 'bg-green-500'
  if (category.includes('Port')) return 'bg-cyan-500'
  if (category.includes('Warehousing')) return 'bg-purple-500'
  if (category.includes('Documentation')) return 'bg-gray-500'
  if (category.includes('Tax')) return 'bg-red-500'
  return 'bg-slate-500'
}

export function LandedCostTab() {
  const [form, setForm] = useState({
    product_name: '',
    hs_code: '',
    origin_country: 'CN',
    destination_country: 'AE',
    unit_price: '',
    quantity_kg: '',
    currency: 'USD',
    sell_price_per_kg: '',
  })
  const [result, setResult] = useState<LandedCostResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCalculate = async () => {
    if (!form.product_name || !form.unit_price || !form.quantity_kg) {
      setError('Please fill in Product Name, Unit Price, and Quantity.')
      return
    }
    setError('')
    setLoading(true)
    setResult(null)

    try {
      const token = localStorage.getItem('token')
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'

      const res = await fetch(`${BASE_URL}/brain/landed-cost`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          product_name: form.product_name,
          hs_code: form.hs_code,
          origin_country: form.origin_country,
          destination_country: form.destination_country,
          unit_price: parseFloat(form.unit_price),
          quantity_kg: parseFloat(form.quantity_kg),
          currency: form.currency,
          sell_price_per_kg: form.sell_price_per_kg ? parseFloat(form.sell_price_per_kg) : null,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `API Error ${res.status}`)
      }

      const data = await res.json()
      setResult(data.result)
    } catch (e: any) {
      setError(e.message || 'Calculation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
            <Calculator className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Landed Cost Calculator</h2>
            <p className="text-xs text-gray-400">Calculate the full cost of importing/exporting goods with AI-powered estimation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Product Name */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Product Name *</label>
            <input
              type="text"
              value={form.product_name}
              onChange={e => setForm(f => ({ ...f, product_name: e.target.value }))}
              placeholder="e.g. Chocolate, Steel Pipes"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          {/* HS Code */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">HS Code</label>
            <input
              type="text"
              value={form.hs_code}
              onChange={e => setForm(f => ({ ...f, hs_code: e.target.value }))}
              placeholder="e.g. 1806, 7304"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          {/* Currency */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Currency</label>
            <select
              value={form.currency}
              onChange={e => setForm(f => ({ ...f, currency: e.target.value }))}
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            >
              {CURRENCIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Origin */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Origin Country *</label>
            <select
              value={form.origin_country}
              onChange={e => setForm(f => ({ ...f, origin_country: e.target.value }))}
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            >
              {COUNTRY_OPTIONS.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>

          {/* Destination */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Destination Country *</label>
            <select
              value={form.destination_country}
              onChange={e => setForm(f => ({ ...f, destination_country: e.target.value }))}
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            >
              {COUNTRY_OPTIONS.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Quantity (kg) *</label>
            <input
              type="number"
              value={form.quantity_kg}
              onChange={e => setForm(f => ({ ...f, quantity_kg: e.target.value }))}
              placeholder="20000"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          {/* Unit Price */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Buy Price ($/kg) *</label>
            <input
              type="number"
              step="0.01"
              value={form.unit_price}
              onChange={e => setForm(f => ({ ...f, unit_price: e.target.value }))}
              placeholder="8.50"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          {/* Sell Price */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Target Sell Price ($/kg)</label>
            <input
              type="number"
              step="0.01"
              value={form.sell_price_per_kg}
              onChange={e => setForm(f => ({ ...f, sell_price_per_kg: e.target.value }))}
              placeholder="Auto-estimated if empty"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="mt-6 w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-900/30"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Calculating with AI...</>
          ) : (
            <><Calculator className="w-5 h-5" /> Calculate Landed Cost</>
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">

          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-4 text-center">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Product Cost</p>
              <p className="text-lg font-bold text-white">${result.product_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
            </div>
            <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-4 text-center">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Additional Costs</p>
              <p className="text-lg font-bold text-amber-400">+${result.total_additional_costs_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
            </div>
            <div className="bg-[#0c1829] border border-emerald-500/30 rounded-xl p-4 text-center">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Total Landed Cost</p>
              <p className="text-lg font-bold text-emerald-400">${result.total_landed_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
              <p className="text-[10px] text-gray-500">${result.landed_cost_per_kg_usd.toFixed(2)}/kg</p>
            </div>
            <div className={`bg-[#0c1829] border rounded-xl p-4 text-center ${result.estimated_margin_pct >= 0 ? 'border-green-500/30' : 'border-red-500/30'}`}>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Est. Margin</p>
              <div className="flex items-center justify-center gap-1">
                {result.estimated_margin_pct >= 0
                  ? <TrendingUp className="w-4 h-4 text-green-400" />
                  : <TrendingDown className="w-4 h-4 text-red-400" />}
                <p className={`text-lg font-bold ${result.estimated_margin_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {result.estimated_margin_pct.toFixed(1)}%
                </p>
              </div>
              <p className={`text-[10px] ${result.estimated_profit_usd >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {result.estimated_profit_usd >= 0 ? '+' : ''}${result.estimated_profit_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </p>
            </div>
          </div>

          {/* Cost Breakdown Waterfall */}
          <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-6">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">📊 Cost Breakdown</h3>

            {/* Product Cost Bar */}
            <div className="mb-3 p-3 bg-[#0a1526] rounded-lg border border-[#1e3a5f]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-white" />
                  <span className="text-sm font-medium text-white">Product Cost ({result.quantity_kg.toLocaleString()} kg × ${result.unit_price_usd}/kg)</span>
                </div>
                <span className="text-sm font-bold text-white">${result.product_cost_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
              </div>
              <div className="w-full bg-[#1a2b45] rounded-full h-2.5">
                <div className="bg-white/30 h-2.5 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>

            {/* Individual Cost Items */}
            <div className="space-y-2.5">
              {result.cost_items.filter(i => i.amount_usd > 0).map((item, idx) => (
                <div key={idx} className={`p-3 rounded-lg border ${getCategoryColor(item.category)}`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(item.category)}
                      <span className="text-sm font-medium">{item.category}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-sm font-bold">${item.amount_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                      <span className="text-[10px] ml-1.5 opacity-70">({item.percentage_of_total.toFixed(1)}%)</span>
                    </div>
                  </div>
                  <p className="text-[11px] opacity-70 mb-1.5">{item.description}</p>
                  {item.notes && <p className="text-[10px] opacity-50 italic">{item.notes}</p>}

                  {/* Bar */}
                  <div className="w-full bg-black/20 rounded-full h-1.5 mt-2">
                    <div className={`${getBarColor(item.category)} h-1.5 rounded-full transition-all duration-700`} style={{ width: `${Math.min(item.percentage_of_total * 3, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Confidence & AI Notes */}
          <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">🤖 AI Confidence</h3>
              <span className={`text-sm font-bold px-2.5 py-1 rounded-full ${
                result.confidence >= 0.7 ? 'bg-green-500/20 text-green-400' :
                result.confidence >= 0.4 ? 'bg-amber-500/20 text-amber-400' :
                'bg-red-500/20 text-red-400'
              }`}>{(result.confidence * 100).toFixed(0)}%</span>
            </div>
            <p className="text-sm text-gray-300 mb-3">{result.ai_notes}</p>
            <div className="space-y-1">
              {result.assumptions.map((a, i) => (
                <p key={i} className="text-[11px] text-gray-500">• {a}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
