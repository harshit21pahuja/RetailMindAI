import React, { useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AlertCircle,
  AlertTriangle,
  PackagePlus,
  RefreshCw,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  ProductForecastTimeline,
  ProductInventoryStatus,
  ReorderRecommendation,
  StockoutRiskItem,
} from '../types';

interface ForecastTabProps {
  products: ProductInventoryStatus[];
  onRefreshInventory: () => void;
}

export const ForecastTab: React.FC<ForecastTabProps> = ({ products, onRefreshInventory }) => {
  const [selectedSku, setSelectedSku] = useState<string>(products[0]?.sku || 'BEV-COKE-500');
  const [forecastTimeline, setForecastTimeline] = useState<ProductForecastTimeline | null>(null);
  const [stockoutRisks, setStockoutRisks] = useState<StockoutRiskItem[]>([]);
  const [reorders, setReorders] = useState<ReorderRecommendation[]>([]);
  const [isLoadingForecast, setIsLoadingForecast] = useState<boolean>(false);
  const [isGeneratingReorders, setIsGeneratingReorders] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync selected SKU if products load later
  useEffect(() => {
    if (!selectedSku && products.length > 0) {
      setSelectedSku(products[0].sku);
    }
  }, [products, selectedSku]);

  // Fetch forecast for selected SKU
  const loadForecast = async (sku: string) => {
    if (!sku) return;
    setIsLoadingForecast(true);
    setErrorMsg(null);
    try {
      const data = await api.getDemandForecast(sku, 14);
      setForecastTimeline(data);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to load forecast');
    } finally {
      setIsLoadingForecast(false);
    }
  };

  // Fetch stockout risks and reorder recommendations
  const loadRisksAndReorders = async () => {
    try {
      const [risks, recs] = await Promise.all([
        api.getStockoutRisks(),
        api.getReorderRecommendations(),
      ]);
      setStockoutRisks(Array.isArray(risks) ? risks : []);
      setReorders(Array.isArray(recs) ? recs : []);
    } catch (err: any) {
      console.error('Failed to load risks/reorders:', err);
    }
  };

  useEffect(() => {
    if (selectedSku) {
      loadForecast(selectedSku);
    }
    loadRisksAndReorders();
  }, [selectedSku]);

  const handleGenerateReorders = async () => {
    setIsGeneratingReorders(true);
    try {
      await api.generateReorders();
      await loadRisksAndReorders();
      onRefreshInventory();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to generate reorders');
    } finally {
      setIsGeneratingReorders(false);
    }
  };

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    try {
      await api.updateReorderStatus(id, newStatus);
      setReorders((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: newStatus as any } : r))
      );
    } catch {
      setErrorMsg('Failed to update status');
    }
  };

  const chartData = (forecastTimeline?.forecast_points || []).map((pt) => ({
    date: new Date(pt.forecast_date).toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
    }),
    predicted: Math.round(pt.predicted_demand * 10) / 10,
    lower: Math.round(pt.lower_bound * 10) / 10,
    upper: Math.round(pt.upper_bound * 10) / 10,
    confidence: Math.round(pt.confidence_score * 100),
  }));

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            HIGH RISK
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            HEALTHY
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            <span>Demand Forecasting & Dynamic Replenishment</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Hybrid Exponential Smoothing & WMA time series predicting run rates and stockout horizons
          </p>
        </div>

        <button
          id="generate-reorders-btn"
          onClick={handleGenerateReorders}
          disabled={isGeneratingReorders}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-md shadow-emerald-500/20 active:scale-95 disabled:opacity-50"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isGeneratingReorders ? 'animate-spin' : ''}`} />
          <span>{isGeneratingReorders ? 'Computing Reorders...' : 'Run Replenishment Engine'}</span>
        </button>
      </div>

      {errorMsg && (
        <div className="flex items-center space-x-2 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 14-Day Demand Forecast Chart Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
              14-Day Forecast Horizon
            </span>
            <h3 className="text-lg font-bold text-white">
              {forecastTimeline?.product_name || selectedSku}
            </h3>
            <p className="text-xs text-slate-400">
              Daily predicted sales volume with 80% confidence interval bands
            </p>
          </div>

          {/* SKU Picker */}
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5">
            <span className="text-xs text-slate-400 font-medium">Select SKU:</span>
            <select
              value={selectedSku}
              onChange={(e) => setSelectedSku(e.target.value)}
              className="bg-transparent text-xs text-emerald-400 font-bold focus:outline-none cursor-pointer"
            >
              {products.map((p) => (
                <option key={p.sku} value={p.sku} className="bg-slate-900 text-white">
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Forecast KPI bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Current Book Stock</span>
            <p className="text-xl font-bold text-white mt-0.5">
              {forecastTimeline?.current_stock ?? '—'} units
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Daily Run Rate</span>
            <p className="text-xl font-bold text-cyan-400 mt-0.5">
              {forecastTimeline?.daily_run_rate
                ? `${Math.round(forecastTimeline.daily_run_rate * 10) / 10} / day`
                : '—'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Days to Depletion</span>
            <p
              className={`text-xl font-bold mt-0.5 ${
                (forecastTimeline?.days_to_depletion || 0) < 4 ? 'text-rose-400' : 'text-emerald-400'
              }`}
            >
              {forecastTimeline?.days_to_depletion !== undefined
                ? forecastTimeline.days_to_depletion >= 9000
                  ? '> 90 days'
                  : `${Math.round(forecastTimeline.days_to_depletion)} days`
                : '—'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] uppercase text-slate-400 font-semibold">Model Lineage</span>
            <p className="text-xs font-bold text-purple-400 mt-1">Hybrid EMA + WMA</p>
          </div>
        </div>

        {/* Recharts Area Chart */}
        <div className="h-72 w-full pt-4">
          {isLoadingForecast ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              <RefreshCw className="w-5 h-5 animate-spin mr-2 text-cyan-400" />
              <span>Generating demand curve...</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="predictedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="upperGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderColor: '#1e293b',
                    borderRadius: '12px',
                    fontSize: '12px',
                    color: '#f8fafc',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="upper"
                  stroke="#3b82f6"
                  strokeDasharray="4 4"
                  fill="url(#upperGrad)"
                  name="Upper Bound (80%)"
                />
                <Area
                  type="monotone"
                  dataKey="predicted"
                  stroke="#06b6d4"
                  strokeWidth={2.5}
                  fill="url(#predictedGrad)"
                  name="Predicted Demand"
                />
                <Area
                  type="monotone"
                  dataKey="lower"
                  stroke="#64748b"
                  strokeDasharray="4 4"
                  fill="transparent"
                  name="Lower Bound (80%)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Two Column Section: Stockout Risk Radar + Reorder Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Stockout Risks */}
        <div className="lg:col-span-5 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Stockout Risk Ranking</span>
              </h3>
              <p className="text-xs text-slate-400">SKUs sorted by urgency of stock depletion</p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              {Array.isArray(stockoutRisks) ? stockoutRisks.length : 0} SKUs evaluated
            </span>
          </div>

          <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
            {Array.isArray(stockoutRisks) && stockoutRisks.length > 0 ? (
              stockoutRisks.map((risk) => (
                <div
                  key={risk.sku}
                  onClick={() => setSelectedSku(risk.sku)}
                  className={`p-3 rounded-xl border transition cursor-pointer ${
                    selectedSku === risk.sku
                      ? 'bg-slate-900 border-cyan-500/50 shadow-md'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-white">{risk.product_name}</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        Stock: <span className="text-slate-200 font-bold">{risk.current_stock} pcs</span> • Lead Time: {risk.lead_time_days}d
                      </p>
                    </div>
                    {getRiskBadge(risk.stockout_risk)}
                  </div>

                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/80 text-[11px]">
                    <span className="text-slate-400">
                      Runout in:{' '}
                      <strong
                        className={
                          risk.days_to_depletion <= risk.lead_time_days
                            ? 'text-rose-400'
                            : 'text-amber-400'
                        }
                      >
                        {risk.days_to_depletion >= 9000
                          ? '> 90 days'
                          : `${Math.round(risk.days_to_depletion * 10) / 10} days`}
                      </strong>
                    </span>
                    <span className="text-cyan-400 font-semibold">{risk.risk_description}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-500 text-xs">
                Loading stockout risks...
              </div>
            )}
          </div>
        </div>

        {/* Right: Reorder Recommendations */}
        <div className="lg:col-span-7 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <PackagePlus className="w-4 h-4 text-emerald-400" />
                <span>Automated Reorder Recommendations</span>
              </h3>
              <p className="text-xs text-slate-400">
                Purchase orders computed from lead times, daily run rate, and safety stock
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="py-2.5 px-3">SKU</th>
                  <th className="py-2.5 px-3">Stock / ROP</th>
                  <th className="py-2.5 px-3">Order Qty</th>
                  <th className="py-2.5 px-3">Est. Cost</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {Array.isArray(reorders) && reorders.length > 0 ? (
                  reorders.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-900/40 transition">
                      <td className="py-2.5 px-3 font-mono font-bold text-white">{rec.sku}</td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {rec.current_stock} <span className="text-slate-500">/ {rec.reorder_point}</span>
                      </td>
                      <td className="py-2.5 px-3 font-bold text-emerald-400">
                        +{rec.recommended_order_qty}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-200">
                        ₹{Math.round(rec.estimated_cost ?? (rec as any).estimated_reorder_cost ?? 0).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            (rec.priority || (rec as any).reorder_priority) === 'URGENT'
                              ? 'bg-rose-500/20 text-rose-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}
                        >
                          {rec.priority || (rec as any).reorder_priority || 'NORMAL'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            (rec.status || (rec as any).recommendation_status) === 'ORDERED'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : (rec.status || (rec as any).recommendation_status) === 'APPROVED'
                              ? 'bg-blue-500/20 text-blue-300'
                              : (rec.status || (rec as any).recommendation_status) === 'DISMISSED'
                              ? 'bg-slate-800 text-slate-400'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}
                        >
                          {rec.status || (rec as any).recommendation_status || 'PENDING'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right space-x-1">
                        {(rec.status || (rec as any).recommendation_status || 'PENDING') === 'PENDING' && (
                          <>
                            <button
                              onClick={() => handleUpdateStatus(rec.id, 'APPROVED')}
                              className="px-2 py-1 rounded text-[10px] font-bold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 transition"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(rec.id, 'DISMISSED')}
                              className="px-2 py-1 rounded text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-400 transition"
                            >
                              Dismiss
                            </button>
                          </>
                        )}
                        {(rec.status || (rec as any).recommendation_status) === 'APPROVED' && (
                          <button
                            onClick={() => handleUpdateStatus(rec.id, 'ORDERED')}
                            className="px-2 py-1 rounded text-[10px] font-bold bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 transition"
                          >
                            Mark Ordered
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500 text-xs">
                      No active reorders. Click &quot;Run Replenishment Engine&quot; above.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
