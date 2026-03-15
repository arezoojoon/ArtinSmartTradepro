'use client'

import { useState } from 'react'
import { Radar, TrendingUp, TrendingDown, Loader2, AlertTriangle, MapPin, BarChart3, ShieldAlert, Zap, ArrowRight } from 'lucide-react'

interface ArbitrageOpportunity {
  product: string
  buy_market: string
  buy_price_usd_per_kg: number
  sell_market: string
  sell_price_usd_per_kg: number
  estimated_margin_pct: number
  estimated_profit_per_ton_usd: number
  demand_level: string
  supply_level: string
  confidence: number
  reasoning: string
  recommended_action: string
  risk_factors: string[]
}

interface ArbitrageResult {
  product: string
  hs_code: string
  markets_scanned: string[]
  opportunities: ArbitrageOpportunity[]
  market_summary: string
  scan_confidence: number
  disclaimer: string
}

const MARKET_OPTIONS = [
  { code: 'AE', name: 'UAE', flag: '🇦🇪' },
  { code: 'OM', name: 'Oman', flag: '🇴🇲' },
  { code: 'QA', name: 'Qatar', flag: '🇶🇦' },
  { code: 'KW', name: 'Kuwait', flag: '🇰🇼' },
  { code: 'BH', name: 'Bahrain', flag: '🇧🇭' },
  { code: 'SA', name: 'Saudi Arabia', flag: '🇸🇦' },
  { code: 'IR', name: 'Iran', flag: '🇮🇷' },
  { code: 'TR', name: 'Turkey', flag: '🇹🇷' },
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'PK', name: 'Pakistan', flag: '🇵🇰' },
  { code: 'IQ', name: 'Iraq', flag: '🇮🇶' },
  { code: 'EG', name: 'Egypt', flag: '🇪🇬' },
  { code: 'AF', name: 'Afghanistan', flag: '🇦🇫' },
  { code: 'CN', name: 'China', flag: '🇨🇳' },
  { code: 'RU', name: 'Russia', flag: '🇷🇺' },
]

const getCountryDisplay = (code: string) => {
  const market = MARKET_OPTIONS.find(m => m.code === code)
  return market ? `${market.flag} ${market.name}` : code
}

const getCountryFlag = (code: string) => {
  const market = MARKET_OPTIONS.find(m => m.code === code)
  return market?.flag || '🌍'
}

const getMarginColor = (margin: number) => {
  if (margin >= 20) return 'text-emerald-400'
  if (margin >= 10) return 'text-green-400'
  if (margin >= 5) return 'text-amber-400'
  return 'text-red-400'
}

const getMarginBg = (margin: number) => {
  if (margin >= 20) return 'bg-emerald-500/20 border-emerald-500/30'
  if (margin >= 10) return 'bg-green-500/20 border-green-500/30'
  if (margin >= 5) return 'bg-amber-500/20 border-amber-500/30'
  return 'bg-red-500/20 border-red-500/30'
}

const getDemandBadge = (level: string) => {
  switch (level) {
    case 'high': return 'bg-green-500/20 text-green-400 border-green-500/30'
    case 'medium': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    case 'low': return 'bg-red-500/20 text-red-400 border-red-500/30'
    default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  }
}

export function RegionalArbitrageTab() {
  const [form, setForm] = useState({
    product: '',
    hs_code: '',
    min_margin: '5',
  })
  const [selectedMarkets, setSelectedMarkets] = useState<string[]>(['AE', 'OM', 'QA', 'KW', 'BH', 'SA', 'IR', 'TR'])
  const [result, setResult] = useState<ArbitrageResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleMarket = (code: string) => {
    setSelectedMarkets(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    )
  }

  const handleScan = async () => {
    if (!form.product) {
      setError('Please enter a product name.')
      return
    }
    if (selectedMarkets.length < 2) {
      setError('Select at least 2 markets to compare.')
      return
    }
    setError('')
    setLoading(true)
    setResult(null)

    try {
      const token = localStorage.getItem('token')
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'

      const res = await fetch(`${BASE_URL}/brain/regional-arbitrage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          product: form.product,
          hs_code: form.hs_code,
          markets: selectedMarkets,
          min_margin_pct: parseFloat(form.min_margin) || 5,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `API Error ${res.status}`)
      }

      const data = await res.json()
      setResult(data.result)
    } catch (e: any) {
      setError(e.message || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Radar className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Regional Arbitrage Finder</h2>
            <p className="text-xs text-gray-400">AI-powered scanner to detect price gaps across neighboring markets</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          {/* Product */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Product Name *</label>
            <input
              type="text"
              value={form.product}
              onChange={e => setForm(f => ({ ...f, product: e.target.value }))}
              placeholder="e.g. Car Tires, Sunflower Oil"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition"
            />
          </div>

          {/* HS Code */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">HS Code (optional)</label>
            <input
              type="text"
              value={form.hs_code}
              onChange={e => setForm(f => ({ ...f, hs_code: e.target.value }))}
              placeholder="e.g. 4011, 1512"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition"
            />
          </div>

          {/* Min Margin */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Min. Margin %</label>
            <input
              type="number"
              value={form.min_margin}
              onChange={e => setForm(f => ({ ...f, min_margin: e.target.value }))}
              placeholder="5"
              className="w-full bg-[#0a1526] border border-[#1e3a5f] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition"
            />
          </div>
        </div>

        {/* Market Selection */}
        <div className="mb-5">
          <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">Target Markets (select 2+)</label>
          <div className="flex flex-wrap gap-2">
            {MARKET_OPTIONS.map(m => (
              <button
                key={m.code}
                onClick={() => toggleMarket(m.code)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200 ${
                  selectedMarkets.includes(m.code)
                    ? 'bg-violet-500/20 border-violet-500/50 text-violet-300 shadow-md shadow-violet-900/20'
                    : 'bg-[#0a1526] border-[#1e3a5f] text-gray-500 hover:border-violet-500/30 hover:text-gray-300'
                }`}
              >
                {m.flag} {m.name}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </div>
        )}

        <button
          onClick={handleScan}
          disabled={loading}
          className="w-full bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-violet-900/30"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Scanning {selectedMarkets.length} Markets...</>
          ) : (
            <><Radar className="w-5 h-5" /> Scan for Opportunities</>
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">

          {/* Market Summary */}
          <div className="bg-[#0c1829] border border-[#1e3a5f] rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">🌍 Market Intelligence</h3>
              <span className="text-xs text-gray-500">{result.markets_scanned.length} markets scanned</span>
            </div>
            <p className="text-sm text-gray-300 leading-relaxed">{result.market_summary}</p>
          </div>

          {/* Opportunities */}
          {result.opportunities.length === 0 ? (
            <div className="bg-[#0c1829] border border-amber-500/30 rounded-xl p-8 text-center">
              <BarChart3 className="w-12 h-12 text-amber-400/50 mx-auto mb-3" />
              <p className="text-amber-300 font-medium">No opportunities above {form.min_margin}% margin found</p>
              <p className="text-xs text-gray-500 mt-1">Try lowering the minimum margin or changing products</p>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">🎯 Found {result.opportunities.length} Opportunities</h3>

              {result.opportunities.map((opp, idx) => (
                <div
                  key={idx}
                  className={`bg-[#0c1829] border rounded-xl p-5 transition-all duration-300 hover:shadow-lg ${getMarginBg(opp.estimated_margin_pct)}`}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getCountryFlag(opp.buy_market)}</span>
                      <ArrowRight className="w-4 h-4 text-gray-500" />
                      <span className="text-2xl">{getCountryFlag(opp.sell_market)}</span>
                      <div className="ml-2">
                        <p className="text-sm font-bold text-white">
                          {getCountryDisplay(opp.buy_market)} → {getCountryDisplay(opp.sell_market)}
                        </p>
                        <p className="text-xs text-gray-400">Buy at ${opp.buy_price_usd_per_kg.toFixed(2)}/kg → Sell at ${opp.sell_price_usd_per_kg.toFixed(2)}/kg</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getMarginColor(opp.estimated_margin_pct)}`}>
                        {opp.estimated_margin_pct.toFixed(1)}%
                      </p>
                      <p className="text-[10px] text-gray-500 uppercase">margin</p>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="bg-black/20 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-gray-500 uppercase mb-0.5">Profit/Ton</p>
                      <p className="text-sm font-bold text-green-400">${opp.estimated_profit_per_ton_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                    </div>
                    <div className="bg-black/20 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-gray-500 uppercase mb-0.5">Demand</p>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${getDemandBadge(opp.demand_level)}`}>
                        {opp.demand_level}
                      </span>
                    </div>
                    <div className="bg-black/20 rounded-lg p-2.5 text-center">
                      <p className="text-[10px] text-gray-500 uppercase mb-0.5">Confidence</p>
                      <p className="text-sm font-bold text-blue-400">{(opp.confidence * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  {/* Reasoning */}
                  <p className="text-sm text-gray-300 mb-3">💡 {opp.reasoning}</p>

                  {/* Action */}
                  <div className="flex items-start gap-2 p-2.5 bg-violet-500/10 border border-violet-500/20 rounded-lg mb-3">
                    <Zap className="w-4 h-4 text-violet-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-violet-300">{opp.recommended_action}</p>
                  </div>

                  {/* Risks */}
                  {opp.risk_factors.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {opp.risk_factors.map((risk, i) => (
                        <span key={i} className="text-[10px] px-2 py-0.5 bg-red-900/20 border border-red-900/30 text-red-400 rounded-full flex items-center gap-1">
                          <ShieldAlert className="w-2.5 h-2.5" /> {risk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Disclaimer */}
          <p className="text-[10px] text-gray-600 text-center italic">{result.disclaimer}</p>
        </div>
      )}
    </div>
  )
}
